"""Comparación real de generación: prompt registrado frente al mismo prompt extendido."""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import importlib.metadata
import json
import os
import re
import time

BASE = Path(__file__).resolve().parent

def ahora():
    return datetime.now(timezone.utc).isoformat()

def bloque(texto):
    n = max([len(s) for s in re.findall(r'`+', texto)] or [0])
    fence = '`' * max(4, n + 1)
    return fence + 'text\n' + texto + '\n' + fence

def cargar_casos():
    historial = BASE / 'resultados'
    if not historial.exists():
        historial = BASE.parent / 'curacion_demo/resultados'
    carpeta = historial / '20261018T030127Z_24cd58'
    eventos = [json.loads(s) for s in (carpeta / 'evidencia.jsonl').read_text(encoding='utf-8').splitlines() if s.strip()]
    casos = []
    for ident, formato in [('DEMO-001', 'linkedin'), ('DEMO-002', 'linkedin'), ('DEMO-003', 'newsletter')]:
        caso = ident + '-directa'
        entrada = next(e['entrada'] for e in eventos if e['tipo_registro'] == 'entrada' and e['caso'] == caso)
        peticion = next(e['solicitud'] for e in eventos if e['tipo_registro'] == 'solicitud_gemini' and e['caso'] == caso and e['metodo'] == 'models.generate_content')
        respuesta = next(e['salida'] for e in eventos if e['tipo_registro'] == 'respuesta_gemini' and e['caso'] == caso and e['metodo'] == 'models.generate_content')
        casos.append({'id': ident, 'formato': formato, 'entrada': entrada['texto'],
                      'prompt_original': peticion['contents'], 'salida_historica': respuesta})
    return casos

def crear_cliente():
    from dotenv import load_dotenv
    from google import genai
    from google.genai import types
    load_dotenv(BASE / '.env', override=False)
    clave = os.environ.get('GEMINI_API_KEY', '').strip()
    if not clave:
        raise ValueError('GEMINI_API_KEY no configurada.')
    return genai.Client(api_key=clave, http_options=types.HttpOptions(timeout=60000))

def construir_prompt(caso, adicional, variante):
    if variante == 'base':
        return caso['prompt_original']
    if variante != 'extendido':
        raise ValueError('Variante no admitida')
    return caso['prompt_original'] + '\n\nCRITERIO COMPLEMENTARIO DE RESPALDO:\n' + adicional

def metricas(texto):
    return {'palabras': len(texto.split()),
            'hashtags': len(re.findall(r'(?<![\w/&])#(?!\d+\b)\w+', texto))}

def guardar_informe(destino, casos, adicional, filas, meta):
    partes = ['# Comparación de prompts mediante Gemini API',
              '## Alcance',
              'Ensayo exploratorio de generación: prompt base registrado frente al mismo prompt con un bloque complementario. Se mantienen mensaje, análisis, ejemplos y configuración por pareja. Se evalúa higiene de afirmaciones causales, magnitudes y cuantificación, conservando tono de marketing. No se prueba el endpoint ni el enrutamiento.',
              '| Configuración | Valor |\n|---|---|\n' + '\n'.join(f'| {k} | {v} |' for k, v in meta.items()),
              'El prompt base procede de las funciones del PR #38 (d62dd02), capturado en la ejecución 20261018T030127Z_24cd58 del PR #39. Las salidas históricas se muestran como referencia separada. Las respuestas base y extendida de este ensayo son llamadas nuevas con la misma configuración; no se confunden con la ejecución histórica.',
              '## Bloque complementario enviado', bloque(adicional),
              '## Estado de ejecución',
              f"Solicitudes registradas: {len(filas)}. Respuestas con texto: {sum(r['estado'] == 'respuesta' for r in filas)}. Errores o respuestas vacías: {sum(r['estado'] != 'respuesta' for r in filas)}.",
              '## Resultados completos por mensaje']
    for caso in casos:
        partes += [f"### {caso['id']} — {caso['formato']}", '**Entrada completa**', bloque(caso['entrada']),
                   '**Prompt base completo**', bloque(caso['prompt_original']),
                   '**Respuesta histórica — referencia, no ejecutada de nuevo para esta sección**', bloque(caso['salida_historica'])]
        for rep in sorted({r['repeticion'] for r in filas if r['id'] == caso['id']}):
            partes += [f'#### Repetición {rep}']
            for variante in ('base', 'extendido'):
                matches = [r for r in filas if r['id'] == caso['id'] and r['repeticion'] == rep and r['variante'] == variante]
                if not matches:
                    partes += [f'**{variante}:** solicitud no ejecutada.']
                    continue
                r = matches[0]
                partes += [f"**{variante} — {r['estado']}**", f"Fecha UTC: {r['fecha_utc']}. Modelo devuelto: {r['modelo_devuelto']}. Duración: {r['segundos']} s.",
                           bloque(r['texto']),
                           f"Palabras: {r['palabras']}. Hashtags: {r['hashtags']}. Finalización: {r['finalizacion']}. Uso registrado: {r['uso']}."]
    partes += ['## Criterios de lectura',
               '- Conservar el hecho principal y un tono publicable; no penalizar por sí sola una reflexión inspiradora.\n- Detectar causalidad o eficacia presentadas como demostradas sin respaldo.\n- Detectar cifras, magnitudes, comparaciones o validación estadística inexistentes.\n- Distinguir percepción atribuida de mejora medida y mantener el alcance del sujeto.\n- Comprobar que no se inventan fuentes o citas.\n- Revisar también posibles pérdidas de naturalidad y regresiones.',
               '## Limitaciones',
               f'{len(casos)} mensajes y dos repeticiones por variante. No son una estimación de precisión ni una prueba estadística de superioridad. La generación puede variar aun con temperatura fija. Los ejemplos incluidos en el prompt y el análisis previo se mantienen constantes: este ensayo aísla el efecto del bloque sobre generación, no evalúa una modificación del analizador. Se requieren criterios humanos para juzgar calidad; palabras y hashtags son controles descriptivos, no una puntuación de veracidad.']
    (destino / 'COMPARACION_GEMINI.md').write_text('\n\n'.join(partes) + '\n', encoding='utf-8')

def ejecutar_comparacion(cliente, casos, adicional, repeticiones=2):
    from google.genai import types
    if repeticiones != 2:
        raise ValueError('Este protocolo define dos repeticiones por variante.')
    modelo = os.environ.get('GEMINI_MODEL', 'gemini-3.5-flash-lite')
    destino = BASE / 'comparacion_api' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    destino.mkdir(parents=True, exist_ok=False)
    (destino / 'BLOQUE_PROBADO.txt').write_text(adicional, encoding='utf-8')
    meta = {'modelo_solicitado': modelo, 'inicio_utc': ahora(), 'temperatura': 0.2,
            'max_output_tokens': 2048, 'repeticiones_por_variante': repeticiones,
            'sdk_google_genai': importlib.metadata.version('google-genai'),
            'version_fuente_prompts': 'd62dd02ce1a358824b72336a6e4150be1ab81262'}
    filas = []
    guardar_informe(destino, casos, adicional, filas, meta)
    # Alternate order on the second repetition; no retry or model fallback.
    for repeticion in range(1, repeticiones + 1):
        for caso in casos:
            orden = ('base', 'extendido') if repeticion == 1 else ('extendido', 'base')
            for variante in orden:
                prompt = construir_prompt(caso, adicional, variante)
                fecha = ahora()
                registro = {'id': caso['id'], 'repeticion': repeticion, 'variante': variante,
                            'fecha_utc': fecha, 'modelo_solicitado': modelo}
                titulo = f"{caso['id']}_r{repeticion}_{variante}"
                (destino / f'{titulo}_solicitud.md').write_text('# Solicitud Gemini\n\n' + f'Modelo: {modelo}. Fecha UTC: {fecha}. Temperatura: 0.2. max_output_tokens: 2048.\n\n' + bloque(prompt) + '\n', encoding='utf-8')
                print(f'\n{titulo} — consultando Gemini...', flush=True)
                start = time.perf_counter()
                try:
                    response = cliente.models.generate_content(model=modelo, contents=prompt,
                        config=types.GenerateContentConfig(temperature=0.2, max_output_tokens=2048))
                    texto = response.text or ''
                    uso = getattr(response, 'usage_metadata', None)
                    uso = uso.model_dump(mode='json', exclude_none=True) if hasattr(uso, 'model_dump') else None
                    finish = str(response.candidates[0].finish_reason) if response.candidates else 'sin candidato'
                    registro.update(estado='respuesta' if texto.strip() else 'respuesta_vacia', texto=texto,
                                    modelo_devuelto=getattr(response, 'model_version', None), uso=uso,
                                    finalizacion=finish, **metricas(texto))
                except Exception as exc:
                    # Provider errors may embed request/auth details: record only class and code.
                    registro.update(estado='error', texto='Error de API: ' + type(exc).__name__,
                                    codigo_error=getattr(exc, 'code', None), modelo_devuelto=None,
                                    uso=None, finalizacion=None, palabras=0, hashtags=0)
                registro['segundos'] = round(time.perf_counter() - start, 3)
                filas.append(registro)
                (destino / f'{titulo}_respuesta.md').write_text('# Respuesta Gemini\n\n' + f"Fecha de solicitud UTC: {fecha}. Estado: {registro['estado']}.\n\n" + bloque(registro['texto']) + '\n', encoding='utf-8')
                guardar_informe(destino, casos, adicional, filas, meta)
                print(registro['texto'], flush=True)
                if registro['estado'] == 'error':
                    print('Ensayo interrumpido; error persistido sin reintentos automáticos.', flush=True)
                    return destino, filas
    return destino, filas

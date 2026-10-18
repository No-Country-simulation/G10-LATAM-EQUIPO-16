"""Evidencia de pruebas; importa el código de Andrea, sin reemplazar sus prompts."""
import csv
import importlib
import importlib.metadata
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

BASE = Path(__file__).resolve().parent

def ahora():
    return datetime.now(timezone.utc).isoformat()

def guardar_json(path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

def validar_lote(payload):
    for campo in ('origen_comunidad', 'periodo_referencia'):
        if not isinstance(payload.get(campo), str) or not payload[campo].strip():
            raise ValueError(f'Falta {campo}')
    filas = payload.get('interacciones')
    if not isinstance(filas, list) or not 1 <= len(filas) <= 10:
        raise ValueError('Cada solicitud debe contener entre 1 y 10 interacciones')
    ids = []
    for fila in filas:
        for campo in ('autor', 'canal', 'tipo', 'texto'):
            if not isinstance(fila.get(campo), str) or not fila[campo].strip():
                raise ValueError(f'Interacción inválida: {campo}')
        if not isinstance(fila.get('id'), str) or not fila['id'].strip():
            raise ValueError('Se requiere id para el endpoint de AI Engine')
        ids.append(fila['id'])
    if len(ids) != len(set(ids)):
        raise ValueError('IDs duplicados en el lote')
    return payload

class Registro:
    def __init__(self, version):
        self.path = BASE / 'resultados' / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '_' + uuid4().hex[:6])
        self.path.mkdir(parents=True)
        self.version = version
        self.filas = []
        guardar_json(self.path / 'version_probada.json', version)

    def anotar(self, tipo, **data):
        fila = {'fecha_utc': ahora(), 'tipo_registro': tipo, **data}
        with (self.path / 'evidencia.jsonl').open('a', encoding='utf-8') as f:
            f.write(json.dumps(fila, ensure_ascii=False) + '\n')
        self.filas.append(fila)
        return fila

    def exportar_revision(self):
        campos = ['fecha_utc', 'nivel_prueba', 'caso', 'activo', 'entrada', 'salida', 'revision_marketing', 'observaciones']
        with (self.path / 'revision_marketing.csv').open('w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=campos)
            writer.writeheader()
            for fila in self.filas:
                if fila['tipo_registro'] == 'activo':
                    writer.writerow({**{k: fila.get(k, '') for k in campos}, 'revision_marketing': 'pendiente'})

def cargar_modulos(engine_dir):
    engine = Path(engine_dir).resolve()
    if not (engine / 'few_shot.py').exists():
        raise FileNotFoundError('La versión seleccionada no incluye few_shot.py; usa PR #38 o una versión que lo integre.')
    for nombre in ('models', 'privacy', 'few_shot', 'generators', 'graph', 'loaders', 'analyzer', 'api'):
        previo = sys.modules.get(nombre)
        if previo and Path(previo.__file__).resolve().parent != engine:
            raise RuntimeError(f'{nombre} ya procede de otra carpeta. Reinicia el kernel.')
    sys.path.insert(0, str(engine))
    nombres = ('models', 'privacy', 'few_shot', 'generators', 'graph', 'analyzer', 'api')
    return SimpleNamespace(**{n: importlib.import_module(n) for n in nombres})

def version_fuente(engine_dir, modelo):
    engine = Path(engine_dir).resolve()
    snapshot = BASE / 'andrea_pr38'
    if engine == snapshot.resolve():
        version = json.loads((snapshot / 'procedencia.json').read_text(encoding='utf-8'))
    else:
        def git(*args):
            return subprocess.check_output(['git', '-C', str(engine), *args], text=True).strip()
        version = {'commit': git('rev-parse', 'HEAD'), 'estado_worktree': git('status', '--short', '--', str(engine)),
                   'origen': 'checkout indicado por ANDREA_ENGINE_DIR'}
        if version['estado_worktree']:
            raise RuntimeError('El checkout tiene cambios locales. Confirma un commit limpio para identificar la versión probada.')
    version.update(modelo=modelo, python=sys.version.split()[0], fecha_inicio_utc=ahora())
    version['dependencias'] = {}
    for nombre in ('google-genai', 'python-dotenv', 'pydantic', 'langgraph', 'fastapi', 'httpx'):
        version['dependencias'][nombre] = importlib.metadata.version(nombre)
    return version

class ClienteRegistrado:
    """Reenvía llamadas reales y guarda prompt/salida; nunca guarda el cliente o su key."""
    def __init__(self, real, registro):
        self.real = real
        self.registro = registro
        self.contexto = ''
        self.models = SimpleNamespace(generate_content=self.generate_content)
        self.interactions = SimpleNamespace(create=self.create)

    def llamada(self, metodo, funcion, texto_salida, kwargs):
        self.registro.anotar('solicitud_gemini', caso=self.contexto, metodo=metodo, solicitud=kwargs)
        try:
            response = funcion(**kwargs)
        except Exception as exc:
            self.registro.anotar('error_gemini', caso=self.contexto, metodo=metodo, clase_error=type(exc).__name__)
            raise
        usage = getattr(response, 'usage_metadata', None) or getattr(response, 'usage', None)
        self.registro.anotar('respuesta_gemini', caso=self.contexto, metodo=metodo,
                             salida=getattr(response, texto_salida, None),
                             uso=usage.model_dump(mode='json') if hasattr(usage, 'model_dump') else None)
        return response

    def generate_content(self, **kwargs):
        return self.llamada('models.generate_content', self.real.models.generate_content, 'text', kwargs)

    def create(self, **kwargs):
        return self.llamada('interactions.create', self.real.interactions.create, 'output_text', kwargs)

def registrar_activos(registro, caso, payload, salida, nivel):
    activos = salida.get('activos_distribucion_generados', {}) if isinstance(salida, dict) else {}
    for clave, valor in activos.items():
        if valor:
            registro.anotar('activo', nivel_prueba=nivel, caso=caso, activo=clave,
                             entrada=payload, salida=valor, revision_marketing='pendiente')
    registro.exportar_revision()

def probar_motor(modulos, cliente, registro, caso, payload):
    """Ejecuta el endpoint real local: análisis Gemini → selección → LangGraph → Gemini."""
    from fastapi.testclient import TestClient
    validar_lote(payload)
    modulos.analyzer.client = cliente
    modulos.api.client = cliente
    cliente.contexto = caso
    registro.anotar('entrada', nivel_prueba='ai_engine_local', caso=caso, entrada=payload)
    try:
        with TestClient(modulos.api.app, raise_server_exceptions=False) as app:
            resp = app.post('/api/v1/analyze-batch', json=payload)
        try:
            salida = resp.json()
        except ValueError:
            salida = {'error': 'Respuesta no JSON; revisar consola del servicio'}
        registro.anotar('resultado', nivel_prueba='ai_engine_local', caso=caso,
                        http_status=resp.status_code, salida=salida)
        if resp.status_code == 200:
            registrar_activos(registro, caso, payload, salida, 'ai_engine_local')
        return resp.status_code, salida
    except Exception as exc:
        registro.anotar('error', nivel_prueba='ai_engine_local', caso=caso, clase_error=type(exc).__name__)
        return None, {'error': type(exc).__name__}

def probar_backend(registro, caso, payload, url, version_backend, token=''):
    """Prueba HTTP al backend real; no supone que use tu key/modelo locales."""
    import httpx
    validar_lote(payload)
    if not version_backend.strip():
        raise ValueError('Falta BACKEND_VERSION: confirmar commit desplegado con el responsable.')
    body = {**payload, 'interacciones': [{k: v for k, v in f.items() if k != 'id'} for f in payload['interacciones']]}
    registro.anotar('entrada', nivel_prueba='backend_integrado', caso=caso, entrada=body,
                    version_backend_declarada=version_backend, endpoint=url.rstrip('/') + '/api/v1/community/process')
    try:
        headers = {'Authorization': 'Bearer ' + token} if token else {}
        resp = httpx.post(url.rstrip('/') + '/api/v1/community/process', json=body, headers=headers, timeout=180)
        try:
            salida = resp.json()
        except ValueError:
            salida = {'error': 'Respuesta no JSON; revisar servicio'}
        registro.anotar('resultado', nivel_prueba='backend_integrado', caso=caso,
                        version_backend_declarada=version_backend, http_status=resp.status_code, salida=salida)
        if resp.status_code == 200:
            registrar_activos(registro, caso, body, salida, 'backend_integrado')
        return resp.status_code, salida
    except httpx.HTTPError as exc:
        registro.anotar('error', nivel_prueba='backend_integrado', caso=caso, clase_error=type(exc).__name__)
        return None, {'error': type(exc).__name__}

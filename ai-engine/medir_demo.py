"""Ejecuta un lote de demostración contra el AI Engine y mide tiempo y tokens.

Qué hace
--------
1. Carga un JSON de interacciones (por defecto, demo_balanceado.json).
2. Llama a /api/v1/analyze-batch en el mismo proceso (sin levantar el servidor),
   así pasa por la misma ruta que usa el backend Java: anonimización, análisis,
   enrutamiento con LangGraph y generación de activos.
3. Registra cada llamada a Gemini (análisis y generación) con su tiempo y sus tokens.
   El endpoint descarta estas métricas, por eso se miden aquí envolviendo las llamadas.
4. Verifica que ningún nombre de autor aparezca en la respuesta.
5. Guarda la respuesta completa, las métricas y un archivo de ejemplos legible.

Uso (desde la carpeta ai-engine/, con GEMINI_API_KEY en el .env):

    python medir_demo.py demo_balanceado.json
    python medir_demo.py demo_balanceado.json --salida resultados_demo

Consume solicitudes reales de Gemini: un lote completo hace 1 llamada de análisis
más 1 de generación por cada tipo de activo (hasta 3).
"""

import argparse
import json
import sys
import time
from pathlib import Path


def _usage_interactions(usage):
    """Tokens de la Interactions API (análisis)."""
    return {
        "entrada": getattr(usage, "total_input_tokens", None),
        "salida": getattr(usage, "total_output_tokens", None),
        "razonamiento": getattr(usage, "total_thought_tokens", None),
        "total": getattr(usage, "total_tokens", None),
    }


def _usage_generate_content(usage):
    """Tokens de generate_content (generación de activos)."""
    return {
        "entrada": getattr(usage, "prompt_token_count", None),
        "salida": getattr(usage, "candidates_token_count", None),
        "razonamiento": getattr(usage, "thoughts_token_count", None),
        "total": getattr(usage, "total_token_count", None),
    }


def _suma(llamadas, campo):
    valores = [c[campo] for c in llamadas if isinstance(c.get(campo), (int, float))]
    return sum(valores) if valores else None


def _fmt(valor, decimales=None):
    if valor is None:
        return "n/d"
    if decimales is not None:
        return f"{valor:.{decimales}f}"
    return str(valor)


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("entrada", nargs="?", default="demo_balanceado.json")
    parser.add_argument("--salida", default="resultados_demo")
    args = parser.parse_args()

    datos = json.loads(Path(args.entrada).read_text(encoding="utf-8"))
    interacciones = datos["interacciones"][:10]

    for i, interaccion in enumerate(interacciones, start=1):
        interaccion.setdefault("id", f"MSG-{i:03d}")

    # Estos imports exigen GEMINI_API_KEY (analyzer.py falla sin ella).
    import analyzer
    from fastapi.testclient import TestClient

    import api

    llamadas = []

    # --- Medición del análisis (Interactions API) ---
    llamada_original = analyzer.call_gemini

    def call_gemini_medido(prompt):
        interaction, segundos = llamada_original(prompt)
        llamadas.append(
            {
                "etapa": "análisis del lote",
                "segundos": segundos,
                **_usage_interactions(getattr(interaction, "usage", None)),
            }
        )
        return interaction, segundos

    analyzer.call_gemini = call_gemini_medido

    # --- Medición de la generación (generate_content) ---
    modelos = analyzer.client.models
    generar_original = modelos.generate_content

    def generate_content_medido(*a, **kw):
        inicio = time.perf_counter()
        respuesta = generar_original(*a, **kw)
        llamadas.append(
            {
                "etapa": "generación de activo",
                "segundos": time.perf_counter() - inicio,
                **_usage_generate_content(
                    getattr(respuesta, "usage_metadata", None)
                ),
            }
        )
        return respuesta

    modelos.generate_content = generate_content_medido

    cuerpo = {
        "origen_comunidad": datos.get("origen_comunidad", "Demo"),
        "periodo_referencia": datos.get("periodo_referencia", "Semana_00"),
        "interacciones": interacciones,
    }

    cliente = TestClient(api.app)
    inicio_total = time.perf_counter()
    respuesta = cliente.post("/api/v1/analyze-batch", json=cuerpo)
    total_segundos = time.perf_counter() - inicio_total

    print(f"\nHTTP {respuesta.status_code} en {total_segundos:.2f} s")
    if respuesta.status_code != 200:
        print(respuesta.text)
        sys.exit(1)

    resultado = respuesta.json()
    texto_respuesta = json.dumps(resultado, ensure_ascii=False)

    # --- Verificación de privacidad ---
    fugas = []
    for interaccion in interacciones:
        autor = interaccion.get("autor", "").strip()
        if autor and autor in texto_respuesta:
            fugas.append(autor)
    if "[AUTOR]" in texto_respuesta:
        fugas.append("[AUTOR]")

    # --- Tabla de métricas ---
    print("\nLlamadas a Gemini")
    print(f"{'etapa':<24}{'seg':>8}{'entrada':>10}{'salida':>9}{'razon.':>9}{'total':>9}")
    for c in llamadas:
        print(
            f"{c['etapa']:<24}{_fmt(c['segundos'], 2):>8}"
            f"{_fmt(c['entrada']):>10}{_fmt(c['salida']):>9}"
            f"{_fmt(c['razonamiento']):>9}{_fmt(c['total']):>9}"
        )
    resumen = {
        "llamadas_a_gemini": len(llamadas),
        "segundos_en_gemini": _suma(llamadas, "segundos"),
        "tokens_entrada": _suma(llamadas, "entrada"),
        "tokens_salida": _suma(llamadas, "salida"),
        "tokens_razonamiento": _suma(llamadas, "razonamiento"),
        "tokens_total": _suma(llamadas, "total"),
        "segundos_extremo_a_extremo": total_segundos,
    }
    print(
        f"\nTotal: {resumen['llamadas_a_gemini']} llamadas, "
        f"{_fmt(resumen['tokens_total'])} tokens, "
        f"{total_segundos:.2f} s extremo a extremo"
    )

    if fugas:
        print(f"\nALERTA de privacidad: aparece en la respuesta -> {fugas}")
    else:
        print("\nPrivacidad: ningún autor ni marcador [AUTOR] aparece en la respuesta.")

    # --- Archivos de salida ---
    carpeta = Path(args.salida)
    carpeta.mkdir(parents=True, exist_ok=True)
    (carpeta / "respuesta.json").write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (carpeta / "metricas.json").write_text(
        json.dumps(
            {"resumen": resumen, "llamadas": llamadas, "fugas_de_privacidad": fugas},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    activos = resultado.get("activos_distribucion_generados", {})
    lineas = [
        "# Ejemplos de transformación",
        "",
        f"Origen: {cuerpo['origen_comunidad']} · Periodo: {cuerpo['periodo_referencia']}",
        "",
        "## Entrada → análisis",
        "",
        "| id | canal | tipo (entrada) | tipo (modelo) | relevancia | tema |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    por_id = {i["id"]: i for i in interacciones}
    for item in resultado.get("interacciones_analizadas", []):
        origen = por_id.get(item["id"], {})
        lineas.append(
            f"| {item['id']} | {origen.get('canal', '')} | {origen.get('tipo', '')} "
            f"| {item['tipo']} | {item['relevancia']} | {item['tema']} |"
        )

    lineas += ["", "## Activos generados", ""]
    for nombre, activo in activos.items():
        lineas.append(f"### {nombre}")
        lineas.append("")
        if not activo:
            lineas.append("_No se generó (ninguna interacción enrutó a este tipo)._")
        else:
            for campo, valor in activo.items():
                lineas.append(f"* **{campo}:** {valor}")
        lineas.append("")
    (carpeta / "ejemplos.md").write_text("\n".join(lineas), encoding="utf-8")

    print(f"\nGuardado en {carpeta}/: respuesta.json, metricas.json, ejemplos.md")


if __name__ == "__main__":
    main()

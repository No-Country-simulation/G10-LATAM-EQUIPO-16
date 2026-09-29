import json
import os
import time

from dotenv import load_dotenv
from google import genai
from pydantic import ValidationError

from models import AnalysisResult, BatchAnalysisResult
from loaders import load_csv
from graph import graph


# ==========================================
# CONFIGURACIÓN
# ==========================================

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError(
        "No se encontró GEMINI_API_KEY en el archivo .env"
    )

client = genai.Client(api_key=api_key)

MODEL_NAME = "gemini-3.5-flash-lite"


# ==========================================
# PROMPT
# ==========================================

def load_prompt() -> str:
    """Carga el prompt de análisis desde un archivo."""

    prompt_path = os.path.join(
        os.path.dirname(__file__),
        "prompts",
        "analysis_prompt.txt",
    )

    with open(prompt_path, "r", encoding="utf-8") as file:
        return file.read()


# ==========================================
# GEMINI
# ==========================================

def call_gemini(prompt: str):
    """Realiza una llamada a Gemini usando Interactions API."""

    start_time = time.perf_counter()

    try:
        interaction = client.interactions.create(
            model=MODEL_NAME,
            input=prompt,
            generation_config={
                "max_output_tokens": 2000,
                "thinking_level": "minimal",
            }
        )

    except Exception as error:
        elapsed_time = time.perf_counter() - start_time
        error_message = str(error).lower()

        if (
            "429" in error_message
            or "quota exceeded" in error_message
            or "too_many_requests" in error_message
        ):
            raise RuntimeError(
                "Gemini alcanzó el límite de solicitudes. "
                "No se realizarán reintentos automáticos."
            ) from error

        if (
            "503" in error_message
            or "unavailable" in error_message
            or "high demand" in error_message
        ):
            raise RuntimeError(
                "Gemini está temporalmente saturado. "
                "Inténtalo nuevamente más tarde."
            ) from error

        raise RuntimeError(
            f"Error al consultar Gemini después de "
            f"{elapsed_time:.2f} segundos."
        ) from error

    elapsed_time = time.perf_counter() - start_time

    return interaction, elapsed_time


# ==========================================
# ANÁLISIS
# ==========================================

def analyze_text(text: str):
    """Analiza texto y devuelve respuesta y métricas."""

    prompt_template = load_prompt()

    prompt = prompt_template.replace(
        "{content}",
        text,
    )

    print(f"🤖 Consultando {MODEL_NAME}...")

    interaction, elapsed_time = call_gemini(prompt)

    usage = getattr(interaction, "usage", None)

    print("\n--- USAGE DEBUG ---")
    print(usage)

    metrics = {
        "time_seconds": elapsed_time,
        "input_tokens": (
            getattr(usage, "total_input_tokens", None)
            if usage
            else None
        ),
        "output_tokens": (
            getattr(usage, "total_output_tokens", None)
            if usage
            else None
        ),
        "thought_tokens": (
            getattr(usage, "total_thought_tokens", None)
            if usage
            else None
        ),
        "total_tokens": (
            getattr(usage, "total_tokens", None)
            if usage
            else None
        ),
    }

    try:
        data = json.loads(interaction.output_text)
        analysis = AnalysisResult(**data)

    except (json.JSONDecodeError, ValidationError) as error:
        raise RuntimeError(
            "Gemini devolvió una respuesta con formato inválido."
        ) from error

    return analysis, metrics

def analyze_batch_texts(interactions: list[dict]):
    """Analiza varias interacciones en una sola llamada a Gemini."""

    batch_data = [
        {
            "id": interaction["id"],
            "texto": interaction["texto"],
        }
        for interaction in interactions
    ]

    prompt = f"""
Analiza las siguientes interacciones de una comunidad digital.

Debes analizar TODAS las interacciones recibidas y conservar exactamente
el mismo ID de cada una.

Para cada interacción devuelve:

- id
- sentimiento: positivo, neutro o negativo
- tema: tema principal de la interacción
- tipo: testimonio, pregunta_tecnica, feedback, logro u otro
- relevancia: alta, media o baja
- insight: conclusión breve y útil sobre la interacción

Devuelve únicamente JSON válido con esta estructura:

{{
  "results": [
    {{
      "id": "MSG-001",
      "sentimiento": "positivo",
      "tema": "tema detectado",
      "tipo": "feedback",
      "relevancia": "alta",
      "insight": "..."
    }}
  ]
}}

INTERACCIONES:

{json.dumps(batch_data, ensure_ascii=False)}
"""

    print(
        f"🤖 Analizando lote de {len(interactions)} "
        f"interacciones con {MODEL_NAME}..."
    )

    response, elapsed_time = call_gemini(prompt)

    usage = getattr(response, "usage", None)

    metrics = {
        "time_seconds": elapsed_time,
        "input_tokens": (
            getattr(usage, "total_input_tokens", None)
            if usage
            else None
        ),
        "output_tokens": (
            getattr(usage, "total_output_tokens", None)
            if usage
            else None
        ),
        "thought_tokens": (
            getattr(usage, "total_thought_tokens", None)
            if usage
            else None
        ),
        "total_tokens": (
            getattr(usage, "total_tokens", None)
            if usage
            else None
        ),
    }

    print("\n--- RESPUESTA RAW GEMINI ---")
    print(repr(response.output_text))
    print("--- FIN RESPUESTA RAW ---\n")

    try:
        raw_text = response.output_text.strip()

        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]

        if raw_text.startswith("```"):
            raw_text = raw_text[3:]

        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]

        raw_text = raw_text.strip()

        data = json.loads(raw_text)
        batch_result = BatchAnalysisResult(**data)

    except (json.JSONDecodeError, ValidationError) as error:
        raise RuntimeError(
            "Gemini devolvió un lote con formato inválido."
        ) from error

    expected_ids = {
        interaction["id"]
        for interaction in interactions
    }

    returned_ids = {
        result.id
        for result in batch_result.results
    }

    if expected_ids != returned_ids:
        raise RuntimeError(
            "Los IDs devueltos por Gemini no coinciden "
            "con los IDs enviados."
        )

    if len(batch_result.results) != len(interactions):
        raise RuntimeError(
            "Gemini no devolvió la misma cantidad "
            "de resultados que recibió."
        )

    return batch_result, metrics

# ==========================================
# PRUEBA
# ==========================================

if __name__ == "__main__":

    try:
        interactions = load_csv("data/messages.csv")

        print(
            f"\n📂 Interacciones cargadas: "
            f"{len(interactions)}"
        )

        for interaction in interactions:

            print("\n" + "=" * 50)
            print(f"👤 Autor: {interaction.autor}")
            print(f"💬 Canal: {interaction.canal}")
            print(f"📝 Texto: {interaction.texto}")

            result, metrics = analyze_text(
                interaction.texto
            )

            graph_result = graph.invoke(
                {
                    "interaction": interaction,
                    "analysis": result,
                    "route": "",
                    "content": "",
                    "client": client,
                    "model": MODEL_NAME
                }
            )

            print("\n--- RESULTADO VALIDADO ---")
            print(
                result.model_dump_json(
                    indent=2
                )
            )

            print("\n--- RUTA LANGGRAPH ---")
            print(
                f"🔀 Ruta seleccionada: "
                f"{graph_result['route']}"
            )

            print("\n--- CONTENIDO GENERADO ---")
            print(graph_result["content"])

            print("\n--- MÉTRICAS ---")
            print(
                f"⏱ Tiempo: "
                f"{metrics['time_seconds']:.2f} segundos"
            )
            print(
                f"🔢 Tokens totales: "
                f"{metrics['total_tokens']}"
            )

    except (
        RuntimeError,
        FileNotFoundError,
        ValueError,
    ) as error:
        print("\n❌ No se pudo completar el análisis.")
        print(f"ℹ️ {error}")
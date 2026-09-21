import json
import os
import time

from dotenv import load_dotenv
from google import genai
from pydantic import ValidationError

from models import AnalysisResult
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
                "max_output_tokens": 400,
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
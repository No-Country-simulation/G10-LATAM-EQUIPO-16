import os

from dotenv import load_dotenv
from google import genai


# Cargar variables desde .env
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("No se encontró GEMINI_API_KEY en el archivo .env")


# Crear cliente de Gemini
client = genai.Client(api_key=api_key)


def analyze_text(text: str) -> str:
    """Analiza un texto utilizando Gemini."""

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=f"""
Analiza el siguiente texto y devuelve un resumen breve
con los puntos más importantes:

{text}
""",
    )

    return response.text


if __name__ == "__main__":
    result = analyze_text(
        "La inteligencia artificial puede ayudar a los equipos "
        "a analizar grandes cantidades de información."
    )

    print(result)
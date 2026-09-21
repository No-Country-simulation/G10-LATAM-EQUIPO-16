from google import genai

from models import AnalysisResult, Interaction


def generate_linkedin(
    client: genai.Client,
    interaction: Interaction,
    analysis: AnalysisResult,
    model: str,
) -> str:
    """Genera una publicación de LinkedIn a partir de una interacción analizada."""

    prompt = f"""
Eres un asistente de marketing para una comunidad educativa de tecnología.

Convierte la siguiente interacción en una publicación breve para LinkedIn.

INTERACCIÓN:
Autor: {interaction.autor}
Canal: {interaction.canal}
Mensaje: {interaction.texto}

ANÁLISIS:
Sentimiento: {analysis.sentimiento}
Tema: {analysis.tema}
Tipo: {analysis.tipo}
Relevancia: {analysis.relevancia}
Insight: {analysis.insight}

INSTRUCCIONES:
- Escribe en español.
- Mantén un tono profesional, positivo y humano.
- No inventes información que no aparezca en la interacción.
- Máximo 100 palabras.
- Devuelve únicamente el texto de la publicación.
"""

    response = client.models.generate_content(
        model=model,
        contents=prompt,
    )

    return response.text.strip()

def generate_faq(
    client: genai.Client,
    interaction: Interaction,
    analysis: AnalysisResult,
    model: str,
) -> str:
    """Genera contenido FAQ a partir de una pregunta técnica analizada."""

    prompt = f"""
Eres un asistente técnico para una comunidad educativa de tecnología.

Convierte la siguiente interacción en una entrada de FAQ clara y útil.

INTERACCIÓN:
Autor: {interaction.autor}
Canal: {interaction.canal}
Mensaje: {interaction.texto}

ANÁLISIS:
Sentimiento: {analysis.sentimiento}
Tema: {analysis.tema}
Tipo: {analysis.tipo}
Relevancia: {analysis.relevancia}
Insight: {analysis.insight}

INSTRUCCIONES:
- Escribe en español.
- Formula una pregunta clara basada en la interacción.
- Responde de forma breve, didáctica y útil.
- No inventes información que no pueda justificarse.
- Si falta información para responder con precisión, indícalo.
- Máximo 150 palabras.
- Usa exactamente este formato:

Pregunta: ...
Respuesta: ...
"""

    response = client.models.generate_content(
        model=model,
        contents=prompt,
    )

    return response.text.strip()
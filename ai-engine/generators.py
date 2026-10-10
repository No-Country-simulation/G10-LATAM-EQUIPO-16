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

def generate_newsletter(
    client: genai.Client,
    interaction: Interaction,
    analysis: AnalysisResult,
    model: str,
) -> str:
    """Genera un destaque breve para newsletter a partir de una interacción analizada."""

    prompt = f"""
Eres un asistente de marketing para una comunidad educativa de tecnología.

Convierte la siguiente interacción en un destaque breve para el newsletter semanal.

INTERACCIÓN:
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
- Resume únicamente los hechos expresados en la interacción.
- Mantén un tono profesional, neutral y humano.
- No inventes información que no aparezca explícitamente en la interacción.
- No afirmes que la organización tomó, está tomando o tomará acciones, medidas o decisiones si eso no aparece explícitamente en la interacción.
- No inventes compromisos, soluciones, mejoras, avances, estados de trabajo ni promesas de la organización.
- No conviertas una sugerencia, queja o dificultad del usuario en una acción confirmada de la organización.
- Puedes reformular el mensaje para hacerlo más claro, pero sin agregar hechos nuevos.
- Máximo 80 palabras.
- Devuelve únicamente el texto del destaque.
"""

    response = client.models.generate_content(
        model=model,
        contents=prompt,
    )

    return response.text.strip()
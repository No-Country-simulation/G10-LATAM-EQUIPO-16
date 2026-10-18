import re

from google import genai

from few_shot import (
    LINKEDIN_EXAMPLES,
    NEWSLETTER_EXAMPLES,
    format_examples,
)
from models import AnalysisResult, Interaction

MAX_HASHTAGS_LINKEDIN = 3

_HASHTAG = re.compile(r"(?<!\S)#\w+")


def limitar_hashtags(texto: str, maximo: int) -> str:
    """Conserva solo los primeros `maximo` hashtags del texto.

    La guía de Marketing fija un máximo de 3 hashtags en LinkedIn. El
    prompt lo pide, pero el modelo no siempre lo cumple, así que se
    garantiza aquí.
    """

    conservados = 0

    def _filtrar(coincidencia: re.Match) -> str:
        nonlocal conservados
        conservados += 1
        return coincidencia.group(0) if conservados <= maximo else ""

    resultado = _HASHTAG.sub(_filtrar, texto)

    return re.sub(r"[ \t]+(\n|$)", r"\1", resultado).strip()


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

EJEMPLOS DE REFERENCIA (muestran la estructura y el tono esperados; no copies sus hechos ni su contenido):
{format_examples(LINKEDIN_EXAMPLES, "Publicación esperada")}

INSTRUCCIONES:
- Escribe en español.
- Usa únicamente los hechos del mensaje de la interacción, nunca los de los ejemplos.
- Mantén un tono profesional, positivo y humano.
- No inventes información que no aparezca en la interacción.
- No agregues apoyo, colaboración, recursos ni otros beneficios de la comunidad que el mensaje no mencione.
- La frase de cierre o reflexión debe derivarse únicamente de lo que dice el mensaje: no afirmes resultados, causas ni beneficios que el mensaje no exprese.
- Termina el texto con exactamente uno de estos llamados a la acción, sin modificarlo: "Únete a nuestra comunidad en Discord.", "Consulta más recursos en la documentación oficial." o "Comparte tus avances en el canal de proyectos."
- Después del llamado a la acción, incluye como máximo 3 hashtags.
- El marcador [AUTOR] representa un nombre anonimizado y nunca debe aparecer en el contenido generado.
- Si aparece [AUTOR] en el mensaje o análisis, reformula la oración de manera natural sin incluir ese marcador ni intentar recuperar el nombre.
- Género de la persona: si el mensaje usa formas femeninas para quien lo escribe (por ejemplo "seleccionada"), respétalas. Si usa formas masculinas o un cargo en masculino (por ejemplo "desarrollador", "contratado"), no copies esa palabra, porque puede ser un masculino genérico: nombra el puesto con un sustantivo neutro ("un puesto de desarrollo backend", "el equipo de desarrollo") y refiérete a la persona como "una persona de la comunidad". Ejemplo: "me contrataron como desarrollador backend" se escribe "una persona de la comunidad se incorporó a un puesto de desarrollo backend". Si el mensaje no marca el género, usa siempre expresiones neutras. Esto aplica a cualquier sustantivo, adjetivo, participio o artículo que describa a la persona, no solo a los ejemplos: no uses una forma masculina para quien escribe a menos que el mensaje lo marque; usa "una persona", "quien" o una construcción impersonal.
- Máximo 100 palabras.
- Devuelve únicamente el texto de la publicación.
"""

    response = client.models.generate_content(
        model=model,
        contents=prompt,
    )

    return limitar_hashtags(response.text.strip(), MAX_HASHTAGS_LINKEDIN)

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
- El marcador [AUTOR] representa un nombre anonimizado y nunca debe aparecer en el contenido generado.
- Si aparece [AUTOR] en el mensaje o análisis, reformula la oración de manera natural sin incluir ese marcador ni intentar recuperar el nombre.
- Género de la persona: si el mensaje usa formas femeninas para quien lo escribe (por ejemplo "seleccionada"), respétalas. Si usa formas masculinas o un cargo en masculino (por ejemplo "desarrollador", "contratado"), no copies esa palabra, porque puede ser un masculino genérico: nombra el puesto con un sustantivo neutro ("un puesto de desarrollo backend", "el equipo de desarrollo") y refiérete a la persona como "una persona de la comunidad". Ejemplo: "me contrataron como desarrollador backend" se escribe "una persona de la comunidad se incorporó a un puesto de desarrollo backend". Si el mensaje no marca el género, usa siempre expresiones neutras. Esto aplica a cualquier sustantivo, adjetivo, participio o artículo que describa a la persona, no solo a los ejemplos: no uses una forma masculina para quien escribe a menos que el mensaje lo marque; usa "una persona", "quien" o una construcción impersonal.
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

EJEMPLOS DE REFERENCIA (muestran la estructura y el tono esperados; no copies sus hechos ni su contenido):
{format_examples(NEWSLETTER_EXAMPLES, "Destaque esperado")}

INSTRUCCIONES:
- Escribe en español.
- Usa únicamente los hechos del mensaje de la interacción, nunca los de los ejemplos.
- Resume únicamente los hechos expresados en la interacción.
- Mantén un tono profesional, neutral y humano.
- No inventes información que no aparezca explícitamente en la interacción.
- No afirmes que la organización tomó, está tomando o tomará acciones, medidas o decisiones si eso no aparece explícitamente en la interacción.
- No inventes compromisos, soluciones, mejoras, avances, estados de trabajo ni promesas de la organización.
- No conviertas una sugerencia, queja o dificultad del usuario en una acción confirmada de la organización.
- Puedes reformular el mensaje para hacerlo más claro, pero sin agregar hechos nuevos.
- El marcador [AUTOR] representa un nombre anonimizado y nunca debe aparecer en el contenido generado.
- Si aparece [AUTOR] en el mensaje o análisis, reformula la oración de manera natural sin incluir ese marcador ni intentar recuperar el nombre.
- Género de la persona: si el mensaje usa formas femeninas para quien lo escribe (por ejemplo "seleccionada"), respétalas. Si usa formas masculinas o un cargo en masculino (por ejemplo "desarrollador", "contratado"), no copies esa palabra, porque puede ser un masculino genérico: nombra el puesto con un sustantivo neutro ("un puesto de desarrollo backend", "el equipo de desarrollo") y refiérete a la persona como "una persona de la comunidad". Ejemplo: "me contrataron como desarrollador backend" se escribe "una persona de la comunidad se incorporó a un puesto de desarrollo backend". Si el mensaje no marca el género, usa siempre expresiones neutras. Esto aplica a cualquier sustantivo, adjetivo, participio o artículo que describa a la persona, no solo a los ejemplos: no uses una forma masculina para quien escribe a menos que el mensaje lo marque; usa "una persona", "quien" o una construcción impersonal.
- Máximo 80 palabras.
- Devuelve únicamente el texto del destaque.
"""

    response = client.models.generate_content(
        model=model,
        contents=prompt,
    )

    return response.text.strip()
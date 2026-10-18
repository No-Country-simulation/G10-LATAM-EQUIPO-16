"""Ejemplos few-shot de Marketing para los prompts de generación.

Fuente: docs/GUIA_TONO_Y_PROMPTS.md (autor: Uziel Green, Marketing).

Adaptaciones respecto de la guía, para respetar las reglas ya vigentes en
los prompts (género neutro y fidelidad al mensaje de origen):

* Se nombra a la persona como "una persona de la comunidad" en lugar de
  "un miembro" o "un integrante" (regla de género, PR #25).
* LinkedIn, ejemplo 2: "un mes" en lugar de "cuatro semanas", y el tercer
  párrafo solo repite lo que dice el mensaje (los apuntes compartidos),
  sin hablar de "apoyo colaborativo" ni de una revisión de recursos. En
  una prueba con Gemini real, ese párrafo hacía que el modelo inventara
  "apoyo" y "colaboración" en otros mensajes.
* LinkedIn 1: "una posición" en lugar de "su primera posición", porque el
  mensaje habla de la primera entrevista, no necesariamente del primer
  empleo (revisión de Gaby, #38).
* Newsletter: "Se lanzó" en lugar de "La comunidad publicó", porque el
  mensaje no identifica a toda la comunidad como autora del lanzamiento
  (revisión de Gaby, #38).
* Newsletter: solo el resumen. El titular y la sección los completa la API
  a partir del análisis, por lo que el ejemplo no repite un titular.

El formato FAQ no usa ejemplos: la guía define "Tip de la Semana" y el
contrato con Backend exige "Pregunta: ... Respuesta: ...".
"""

LINKEDIN_EXAMPLES = [
    {
        "mensaje": (
            "¡Gente, pasé mi primera entrevista técnica y me contrataron "
            "como Trainee Backend! El proyecto de Spring Boot que hicimos "
            "en grupo fue clave."
        ),
        "salida": (
            "¡El esfuerzo enfocado da resultados!\n"
            "\n"
            "Una persona de nuestra comunidad acaba de asegurar una "
            "posición como Trainee Backend. El trabajo colaborativo y la "
            "práctica en proyectos de Spring Boot fueron decisivos para "
            "superar la entrevista técnica.\n"
            "\n"
            "Las oportunidades surgen al combinar constancia con "
            "aprendizaje aplicado. ¡Felicidades por este logro!\n"
            "\n"
            "Únete a nuestra comunidad en Discord.\n"
            "\n"
            "#TalentoTech #ComunidadDev #DesarrolloBackend"
        ),
    },
    {
        "mensaje": (
            "Logré sacar mi certificación de Oracle Cloud Always Free "
            "después de un mes de estudiar. ¡Gracias por los apuntes que "
            "pasaron por el canal!"
        ),
        "salida": (
            "Un mes de preparación y una nueva certificación alcanzada.\n"
            "\n"
            "Celebramos que una persona de la comunidad certificó sus "
            "conocimientos en Oracle Cloud tras un mes de estudio "
            "constante.\n"
            "\n"
            "Los apuntes compartidos en el canal fueron parte de su "
            "preparación para el examen.\n"
            "\n"
            "Consulta más recursos en la documentación oficial.\n"
            "\n"
            "#OracleCloud #TechCommunity #Logros"
        ),
    },
]

NEWSLETTER_EXAMPLES = [
    {
        "mensaje": (
            "Lanzamos la primera versión de la herramienta de testing para "
            "la API. Ya está el repositorio disponible para quien quiera "
            "probarlo."
        ),
        "salida": (
            "Se lanzó la versión inicial de la herramienta de pruebas para "
            "la API. El repositorio ya se encuentra "
            "disponible para revisión y pruebas colaborativas."
        ),
    },
]


def format_examples(examples: list[dict[str, str]], etiqueta_salida: str) -> str:
    """Da formato a los ejemplos para incluirlos en un prompt."""

    bloques = []

    for numero, ejemplo in enumerate(examples, start=1):
        bloques.append(
            f"Ejemplo {numero}\n"
            f"Mensaje: {ejemplo['mensaje']}\n"
            f"{etiqueta_salida}:\n{ejemplo['salida']}"
        )

    return "\n\n".join(bloques)

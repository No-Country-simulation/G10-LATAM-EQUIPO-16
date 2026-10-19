"""Pruebas de los ejemplos few-shot incluidos en los prompts de generación."""

import os
import re
from types import SimpleNamespace
from unittest.mock import MagicMock

os.environ.setdefault("GEMINI_API_KEY", "test-key")

from few_shot import LINKEDIN_EXAMPLES, NEWSLETTER_EXAMPLES  # noqa: E402
from generators import (  # noqa: E402
    generate_faq,
    generate_linkedin,
    generate_newsletter,
)
from models import AnalysisResult, Interaction  # noqa: E402


def _prompt_enviado(generator) -> str:
    interaction = Interaction(
        autor="[AUTOR]",
        canal="#logros",
        tipo="testimonio",
        texto="Terminé mi curso de SQL y ya hago consultas en mi trabajo.",
    )
    analysis = AnalysisResult(
        sentimiento="positivo",
        tema="aprendizaje de SQL",
        tipo="logro",
        relevancia="alta",
        insight="La formación se aplica en el trabajo.",
    )
    client = MagicMock()
    client.models.generate_content.return_value = SimpleNamespace(text="ok")

    generator(
        client=client,
        interaction=interaction,
        analysis=analysis,
        model="modelo-prueba",
    )

    return client.models.generate_content.call_args.kwargs["contents"]


def test_linkedin_incluye_todos_los_ejemplos():
    prompt = _prompt_enviado(generate_linkedin)

    for ejemplo in LINKEDIN_EXAMPLES:
        assert ejemplo["mensaje"] in prompt
        assert ejemplo["salida"] in prompt


def test_newsletter_incluye_todos_los_ejemplos():
    prompt = _prompt_enviado(generate_newsletter)

    for ejemplo in NEWSLETTER_EXAMPLES:
        assert ejemplo["mensaje"] in prompt
        assert ejemplo["salida"] in prompt


def test_faq_no_incluye_ejemplos_de_otros_formatos():
    prompt = _prompt_enviado(generate_faq)

    assert "EJEMPLOS DE REFERENCIA" not in prompt
    assert "Pregunta: ..." in prompt


def test_ejemplos_no_exponen_datos_personales_ni_masculino_generico():
    textos = [
        ejemplo[campo]
        for ejemplo in LINKEDIN_EXAMPLES + NEWSLETTER_EXAMPLES
        for campo in ("mensaje", "salida")
    ]

    for texto in textos:
        assert not re.search(r"\S+@\S+", texto)
        assert "Autor:" not in texto
        assert not re.search(r"\b[Uu]n (miembro|integrante)\b", texto)


def test_ejemplos_de_salida_respetan_el_maximo_de_palabras():
    for ejemplo in LINKEDIN_EXAMPLES:
        assert len(ejemplo["salida"].split()) <= 100

    for ejemplo in NEWSLETTER_EXAMPLES:
        assert len(ejemplo["salida"].split()) <= 80


def test_linkedin_prohibe_agregar_apoyo_no_mencionado():
    prompt = _prompt_enviado(generate_linkedin)

    assert "No agregues apoyo, colaboración" in prompt


def test_ejemplos_linkedin_no_hablan_de_apoyo_colaborativo():
    for ejemplo in LINKEDIN_EXAMPLES:
        assert "apoyo colaborativo" not in ejemplo["salida"]


CTAS_PERMITIDOS = [
    "Únete a nuestra comunidad en Discord.",
    "Consulta más recursos en la documentación oficial.",
    "Comparte tus avances en el canal de proyectos.",
]


def test_linkedin_exige_cta_de_la_lista_cerrada_y_maximo_3_hashtags():
    prompt = _prompt_enviado(generate_linkedin)

    for cta in CTAS_PERMITIDOS:
        assert cta in prompt

    assert "como máximo 3 hashtags" in prompt
    assert "derivarse únicamente de lo que dice el mensaje" in prompt


def test_newsletter_y_faq_no_reciben_las_reglas_de_cta_y_hashtags():
    for generator in (generate_newsletter, generate_faq):
        prompt = _prompt_enviado(generator)

        assert "llamados a la acción" not in prompt
        assert "hashtags" not in prompt


def test_ejemplos_linkedin_usan_cta_permitido_y_maximo_3_hashtags():
    for ejemplo in LINKEDIN_EXAMPLES:
        salida = ejemplo["salida"]

        assert any(cta in salida for cta in CTAS_PERMITIDOS)
        assert len(re.findall(r"(?<!\S)#\w+", salida)) <= 3


def test_ejemplos_no_afirman_lo_que_el_mensaje_no_dice():
    ejemplo_1 = LINKEDIN_EXAMPLES[0]["salida"]
    assert "primera posición" not in ejemplo_1

    assert "La comunidad publicó" not in NEWSLETTER_EXAMPLES[0]["salida"]


def test_limitar_hashtags_conserva_solo_los_primeros_3():
    from generators import limitar_hashtags

    texto = (
        "Un logro.\n\nÚnete a nuestra comunidad en Discord.\n\n"
        "#SQL #ComunidadTech #Datos #Pasantias"
    )

    assert limitar_hashtags(texto, 3) == (
        "Un logro.\n\nÚnete a nuestra comunidad en Discord.\n\n"
        "#SQL #ComunidadTech #Datos"
    )


def test_limitar_hashtags_detecta_hashtags_tras_signos_de_puntuacion():
    from generators import limitar_hashtags

    assert limitar_hashtags("Texto (#Uno) (#Dos) (#Tres) (#Cuatro)", 3) == (
        "Texto (#Uno) (#Dos) (#Tres)"
    )
    assert limitar_hashtags("Fin. #A, #B; #C. #D", 3) == "Fin. #A, #B; #C."


def test_limitar_hashtags_ignora_referencias_numericas_y_no_hashtags():
    from generators import limitar_hashtags

    texto = "Ver el issue #26, C# y https://sitio.com/p#ancla. #A #B #C"

    assert limitar_hashtags(texto, 3) == texto


def test_limitar_hashtags_cuenta_hashtags_que_empiezan_con_numero_y_letras():
    from generators import limitar_hashtags

    assert limitar_hashtags("#A #B #2024Tech #D", 3) == "#A #B #2024Tech"


def test_limitar_hashtags_no_toca_textos_con_3_o_menos():
    from generators import limitar_hashtags

    texto = "Un logro. Lenguaje C# y el issue #26.\n\n#SQL #Datos"

    assert limitar_hashtags(texto, 3) == texto

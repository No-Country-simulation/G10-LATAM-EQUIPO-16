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

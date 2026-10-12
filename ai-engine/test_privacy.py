from types import SimpleNamespace
from unittest.mock import MagicMock

from models import Interaction, AnalysisResult
from privacy import anonymize_interaction
from generators import (
    generate_linkedin,
    generate_faq,
    generate_newsletter,
)


def test_anonymization():
    original = Interaction(
        autor="Mariana Souza",
        canal="#general",
        tipo="testimonio",
        texto="Soy Mariana Souza y conseguí mi primer empleo.",
    )

    safe = anonymize_interaction(original)

    assert safe.autor == "Usuario anónimo"
    assert "Mariana Souza" not in safe.texto
    assert "[AUTOR]" in safe.texto
    assert "conseguí mi primer empleo" in safe.texto

    # El objeto original no debe modificarse.
    assert original.autor == "Mariana Souza"
    assert "Mariana Souza" in original.texto


def test_generator_prompts():
    original = Interaction(
        autor="Mariana Souza",
        canal="#general",
        tipo="testimonio",
        texto="Soy Mariana Souza y terminé un curso de IA.",
    )

    safe = anonymize_interaction(original)

    analysis = AnalysisResult(
        sentimiento="positivo",
        tema="formación en IA",
        tipo="testimonio",
        relevancia="alta",
        insight="La estudiante completó un curso de IA.",
    )

    for generator in (
        generate_linkedin,
        generate_faq,
        generate_newsletter,
    ):
        client = MagicMock()
        client.models.generate_content.return_value = (
            SimpleNamespace(text="Contenido de prueba")
        )

        result = generator(
            client=client,
            interaction=safe,
            analysis=analysis,
            model="modelo-prueba",
        )

        assert result == "Contenido de prueba"

        client.models.generate_content.assert_called_once()

        prompt = client.models.generate_content.call_args.kwargs[
            "contents"
        ]

        assert "Mariana Souza" not in prompt
        assert "Autor:" not in prompt
        assert "[AUTOR]" in prompt


def test_sanitize_generated_content():
    from privacy import sanitize_generated_content

    original = "Celebramos el éxito de [AUTOR]."
    resultado = sanitize_generated_content(original)

    assert "[AUTOR]" not in resultado
    assert "una persona de la comunidad" in resultado


def test_sanitize_analysis():
    from privacy import sanitize_analysis

    original = {
        "tema": "Logro profesional de [AUTOR]",
        "insight": "[AUTOR] consiguió empleo.",
        "sentimiento": "positivo",
    }

    resultado = sanitize_analysis(original)

    assert "[AUTOR]" not in resultado["tema"]
    assert "[AUTOR]" not in resultado["insight"]
    assert resultado["sentimiento"] == "positivo"


if __name__ == "__main__":
    test_anonymization()
    test_generator_prompts()
    test_sanitize_generated_content()
    test_sanitize_analysis()

    print("OK: pruebas de anonimización y sanitización superadas")
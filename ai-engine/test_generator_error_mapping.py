"""Pruebas del manejo compartido de errores de generación."""

from unittest.mock import Mock

import httpx
import pytest
from google.genai import errors

from gemini_resilience import (
    GeminiPermanentError,
    GeminiQuotaError,
    GeminiTransientError,
    generate_content_safely,
)


@pytest.mark.parametrize(
    ("code", "expected_exception"),
    [
        (429, GeminiQuotaError),
        (503, GeminiTransientError),
        (500, GeminiTransientError),
        (400, GeminiPermanentError),
        (403, GeminiPermanentError),
    ],
)
def test_generation_sdk_error_mapping(code, expected_exception):
    client = Mock()
    client.models.generate_content.side_effect = errors.APIError(
        code=code,
        response_json={"error": {"message": "Error simulado"}},
    )

    with pytest.raises(expected_exception):
        generate_content_safely(
            client=client,
            model="modelo-prueba",
            prompt="Contenido de prueba",
        )

    client.models.generate_content.assert_called_once_with(
        model="modelo-prueba",
        contents="Contenido de prueba",
    )


def test_generation_timeout_is_transient():
    client = Mock()
    client.models.generate_content.side_effect = httpx.ReadTimeout(
        "Tiempo agotado"
    )

    with pytest.raises(GeminiTransientError):
        generate_content_safely(
            client=client,
            model="modelo-prueba",
            prompt="Contenido de prueba",
        )


def test_successful_generation_preserves_response():
    client = Mock()
    expected = Mock()
    expected.text = "Contenido generado correctamente"

    client.models.generate_content.return_value = expected

    result = generate_content_safely(
        client=client,
        model="modelo-prueba",
        prompt="Contenido de prueba",
    )

    assert result is expected
    assert result.text == "Contenido generado correctamente"

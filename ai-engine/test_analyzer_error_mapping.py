"""Pruebas de integración entre Gemini SDK y analyzer."""

from unittest.mock import patch

import pytest
from google.genai import errors

from analyzer import (
    PermanentAIError,
    QuotaExceededAIError,
    TransientAIError,
    call_gemini,
)


@pytest.mark.parametrize(
    ("code", "expected_exception"),
    [
        (429, QuotaExceededAIError),
        (503, TransientAIError),
        (500, TransientAIError),
        (400, PermanentAIError),
        (401, PermanentAIError),
        (403, PermanentAIError),
    ],
)
def test_sdk_errors_are_mapped_correctly(code, expected_exception):
    sdk_error = errors.APIError(
        code=code,
        response_json={
            "error": {
                "message": "Error simulado",
            }
        },
    )

    with patch(
        "analyzer.client.interactions.create",
        side_effect=sdk_error,
    ):
        with pytest.raises(expected_exception):
            call_gemini("Prompt de prueba")


def test_unexpected_error_is_permanent():
    with patch(
        "analyzer.client.interactions.create",
        side_effect=ValueError("Error inesperado"),
    ):
        with pytest.raises(PermanentAIError):
            call_gemini("Prompt de prueba")


def test_analysis_timeout_is_transient():
    import httpx

    with patch(
        "analyzer.client.interactions.create",
        side_effect=httpx.ReadTimeout("Tiempo de espera agotado"),
    ):
        with pytest.raises(TransientAIError):
            call_gemini("Prompt de prueba")

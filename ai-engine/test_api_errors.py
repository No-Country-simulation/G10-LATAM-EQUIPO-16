from unittest.mock import patch

from fastapi.testclient import TestClient

from analyzer import PermanentAIError, QuotaExceededAIError, TransientAIError
from api import app

client = TestClient(app)

BATCH = {
    "origen_comunidad": "Discord",
    "periodo_referencia": "2026-10",
    "interacciones": [
        {
            "id": "MSG-001",
            "autor": "Persona de prueba",
            "canal": "#general",
            "tipo": "mensaje",
            "texto": "Texto de prueba.",
        }
    ],
}


def post_batch_failing_with(error):
    with patch("api.analyze_batch_texts", side_effect=error):
        return client.post("/api/v1/analyze-batch", json=BATCH)


def test_quota_exceeded_returns_429_so_backend_does_not_retry():
    response = post_batch_failing_with(QuotaExceededAIError("cuota agotada"))
    assert response.status_code == 429, response.text


def test_transient_error_still_returns_503():
    response = post_batch_failing_with(TransientAIError("Gemini saturado"))
    assert response.status_code == 503, response.text


def test_permanent_error_still_returns_500():
    response = post_batch_failing_with(PermanentAIError("respuesta inválida"))
    assert response.status_code == 500, response.text

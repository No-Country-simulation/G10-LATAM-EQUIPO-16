"""Validación de entradas antes de consultar Gemini."""

from copy import deepcopy
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from api import app


BASE_BATCH = {
    "origen_comunidad": "Comunidad de prueba",
    "periodo_referencia": "2026-10",
    "interacciones": [
        {
            "id": "id-1",
            "autor": "Usuario",
            "canal": "discord",
            "tipo": "pregunta",
            "texto": "¿Cómo funciona el proyecto?",
        }
    ],
}


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("origen_comunidad", ""),
        ("periodo_referencia", "   "),
    ],
)
def test_blank_batch_fields_are_rejected(field, value):
    payload = deepcopy(BASE_BATCH)
    payload[field] = value

    with patch("api.analyze_batch_texts") as mocked:
        response = TestClient(app).post(
            "/api/v1/analyze-batch", json=payload
        )

    assert response.status_code == 422
    mocked.assert_not_called()


@pytest.mark.parametrize(
    "field",
    ["id", "autor", "canal", "tipo", "texto"],
)
def test_blank_interaction_fields_are_rejected(field):
    payload = deepcopy(BASE_BATCH)
    payload["interacciones"][0][field] = "   "

    with patch("api.analyze_batch_texts") as mocked:
        response = TestClient(app).post(
            "/api/v1/analyze-batch", json=payload
        )

    assert response.status_code == 422
    mocked.assert_not_called()


def test_duplicate_interaction_ids_are_rejected():
    payload = deepcopy(BASE_BATCH)
    duplicate = deepcopy(payload["interacciones"][0])
    duplicate["texto"] = "Otra interacción diferente"
    payload["interacciones"].append(duplicate)

    with patch("api.analyze_batch_texts") as mocked:
        response = TestClient(app).post(
            "/api/v1/analyze-batch", json=payload
        )

    assert response.status_code == 422
    mocked.assert_not_called()

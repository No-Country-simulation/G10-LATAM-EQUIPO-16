from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

from api import app


client = TestClient(app)


def test_invalid_faq_preserves_successful_analysis():
    fields = {
        "id": "FAQ-001",
        "sentimiento": "positivo",
        "tema": "Soporte técnico",
        "tipo": "pregunta_tecnica",
        "relevancia": "alta",
        "insight": "La comunidad necesita orientación técnica",
    }

    analysis = SimpleNamespace(
        **fields,
        model_dump=lambda: fields.copy(),
    )

    payload = {
        "origen_comunidad": "Discord",
        "periodo_referencia": "2026-10",
        "interacciones": [
            {
                "id": "FAQ-001",
                "autor": "Persona de prueba",
                "canal": "#soporte",
                "tipo": "pregunta",
                "texto": "¿Cómo puedo resolver este problema?",
            }
        ],
    }

    with (
        patch(
            "api.analyze_batch_texts",
            return_value=(SimpleNamespace(results=[analysis]), {}),
        ),
        patch("api.decide_route", return_value="faq"),
        patch(
            "api.graph.invoke",
            return_value={"content": "Contenido sin formato FAQ válido"},
        ),
    ):
        response = client.post("/api/v1/analyze-batch", json=payload)

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "parcial"
    assert data["resumen_comunidad"]["total_interacciones_procesadas"] == 1
    assert len(data["interacciones_analizadas"]) == 1
    assert data["interacciones_analizadas"][0]["id"] == "FAQ-001"
    assert data["interacciones_fallidas"] == []
    assert data["activos_distribucion_generados"]["sugerencia_contenido_faq"] is None


import pytest


@pytest.mark.parametrize(
    ("route", "asset_key"),
    [
        ("linkedin", "post_linkedin"),
        ("newsletter", "destaque_newsletter_semanal"),
    ],
)
def test_generation_error_preserves_analysis(route, asset_key):
    fields = {
        "id": "GEN-001",
        "sentimiento": "positivo",
        "tema": "Comunidad",
        "tipo": "logro" if route == "linkedin" else "feedback",
        "relevancia": "alta",
        "insight": "Contenido relevante para la comunidad",
    }

    analysis = SimpleNamespace(
        **fields,
        model_dump=lambda: fields.copy(),
    )

    payload = {
        "origen_comunidad": "Discord",
        "periodo_referencia": "2026-10",
        "interacciones": [
            {
                "id": "GEN-001",
                "autor": "Persona de prueba",
                "canal": "#general",
                "tipo": fields["tipo"],
                "texto": "Contenido de prueba",
            }
        ],
    }

    with (
        patch(
            "api.analyze_batch_texts",
            return_value=(SimpleNamespace(results=[analysis]), {}),
        ),
        patch("api.decide_route", return_value=route),
        patch(
            "api.graph.invoke",
            side_effect=ValueError("Error simulado de generación"),
        ),
    ):
        response = client.post("/api/v1/analyze-batch", json=payload)

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "parcial"
    assert data["resumen_comunidad"]["total_interacciones_procesadas"] == 1
    assert len(data["interacciones_analizadas"]) == 1
    assert data["interacciones_analizadas"][0]["id"] == "GEN-001"
    assert data["interacciones_fallidas"] == []
    assert data["activos_distribucion_generados"][asset_key] is None


from gemini_resilience import (
    GeminiQuotaError,
    GeminiTransientError,
)


@pytest.mark.parametrize(
    "generation_error",
    [
        GeminiQuotaError("Cuota agotada"),
        GeminiTransientError("Gemini temporalmente no disponible"),
    ],
)
def test_provider_generation_error_preserves_analysis(generation_error):
    fields = {
        "id": "PROVIDER-001",
        "sentimiento": "positivo",
        "tema": "Logros de la comunidad",
        "tipo": "logro",
        "relevancia": "alta",
        "insight": "Una persona compartió un logro",
    }

    analysis = SimpleNamespace(
        **fields,
        model_dump=lambda: fields.copy(),
    )

    payload = {
        "origen_comunidad": "Discord",
        "periodo_referencia": "2026-10",
        "interacciones": [
            {
                "id": "PROVIDER-001",
                "autor": "Persona de prueba",
                "canal": "#logros",
                "tipo": "logro",
                "texto": "Terminé mi proyecto de inteligencia artificial",
            }
        ],
    }

    with (
        patch(
            "api.analyze_batch_texts",
            return_value=(SimpleNamespace(results=[analysis]), {}),
        ),
        patch("api.decide_route", return_value="linkedin"),
        patch("api.graph.invoke", side_effect=generation_error),
    ):
        response = client.post("/api/v1/analyze-batch", json=payload)

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "parcial"
    assert data["resumen_comunidad"]["total_interacciones_procesadas"] == 1
    assert len(data["interacciones_analizadas"]) == 1
    assert data["interacciones_fallidas"] == []
    assert data["activos_distribucion_generados"]["post_linkedin"] is None


@pytest.mark.parametrize(
    "generation_error",
    [
        GeminiQuotaError(
            "Gemini alcanzó un límite de solicitudes o cuota HTTP 429."
        ),
        GeminiTransientError(
            "Gemini devolvió un error temporal HTTP 503."
        ),
    ],
)
def test_real_provider_error_preserves_analysis(generation_error):
    fields = {
        "id": "REAL-001",
        "sentimiento": "positivo",
        "tema": "Proyecto de inteligencia artificial",
        "tipo": "logro",
        "relevancia": "alta",
        "insight": "Una persona terminó su proyecto",
    }

    analysis = SimpleNamespace(
        **fields,
        model_dump=lambda: fields.copy(),
    )

    payload = {
        "origen_comunidad": "Discord",
        "periodo_referencia": "2026-10",
        "interacciones": [
            {
                "id": "REAL-001",
                "autor": "Persona de prueba",
                "canal": "#logros",
                "tipo": "logro",
                "texto": "Terminé mi proyecto de inteligencia artificial",
            }
        ],
    }

    with (
        patch(
            "api.analyze_batch_texts",
            return_value=(SimpleNamespace(results=[analysis]), {}),
        ),
        patch("api.decide_route", return_value="linkedin"),
        patch("api.graph.invoke", side_effect=generation_error),
    ):
        response = client.post("/api/v1/analyze-batch", json=payload)

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "parcial"
    assert data["resumen_comunidad"]["total_interacciones_procesadas"] == 1
    assert len(data["interacciones_analizadas"]) == 1
    assert data["interacciones_fallidas"] == []
    assert data["activos_distribucion_generados"]["post_linkedin"] is None

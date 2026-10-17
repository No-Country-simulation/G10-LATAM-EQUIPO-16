from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient
from api import app

client = TestClient(app)


def make_analysis(identifier, kind, relevance="alta"):
    fields = {
        "id": identifier,
        "sentimiento": "positivo",
        "tema": "Comunidad",
        "tipo": kind,
        "relevancia": relevance,
        "insight": "Contenido relevante para la comunidad",
    }
    return SimpleNamespace(
        **fields,
        model_dump=lambda: fields.copy(),
    )


def make_interaction(identifier, kind):
    return {
        "id": identifier,
        "autor": "Usuario de prueba",
        "canal": "#general",
        "tipo": kind,
        "texto": "Contenido de prueba para la comunidad",
    }


def test_contract_all_assets_and_failed_interaction():
    analyses = [
        make_analysis("L-001", "logro"),
        make_analysis("N-001", "otro"),
        make_analysis("F-001", "pregunta"),
    ]

    def fake_batch(interactions):
        return SimpleNamespace(results=analyses), {}

    def fake_route(state):
        return {
            "L-001": "linkedin",
            "N-001": "newsletter",
            "F-001": "faq",
        }[state["analysis"].id]

    def fake_graph(state):
        content = {
            "linkedin": "Publicación para LinkedIn",
            "newsletter": "Resumen para newsletter",
            "faq": "Pregunta: ¿Cómo participar?\nRespuesta: Regístrate en la comunidad.",
        }
        return {"content": content[state["route"]]}

    def graph_invoke(state):
        route = fake_route(state)
        return fake_graph({**state, "route": route})

    with (
        patch("api.analyze_batch_texts", side_effect=fake_batch),
        patch("api.decide_route", side_effect=fake_route),
        patch("api.graph.invoke", side_effect=graph_invoke),
    ):
        response = client.post(
            "/api/v1/analyze-batch",
            json={
                "origen_comunidad": "Discord",
                "periodo_referencia": "2026-10",
                "interacciones": [
                    make_interaction("L-001", "logro"),
                    make_interaction("N-001", "otro"),
                    make_interaction("F-001", "pregunta"),
                    make_interaction("X-001", "otro"),
                ],
            },
        )

    assert response.status_code == 200, response.text
    data = response.json()

    assert data["status"] == "parcial"
    assert data["resumen_comunidad"]["total_interacciones_procesadas"] == 3

    assets = data["activos_distribucion_generados"]

    assert assets["post_linkedin"]["interaccion_id"] == "L-001"
    assert assets["destaque_newsletter_semanal"]["interaccion_id"] == "N-001"

    faq = assets["sugerencia_contenido_faq"]
    assert faq["interaccion_id"] == "F-001"
    assert faq["pregunta"] == "¿Cómo participar?"
    assert faq["respuesta"] == "Regístrate en la comunidad."
    assert faq["status"] == "BORRADOR"

    assert len(data["interacciones_analizadas"]) == 3
    assert data["interacciones_fallidas"] == [
        {
            "id": "X-001",
            "motivo": "No se pudo procesar la interacción",
        }
    ]

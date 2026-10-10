from unittest.mock import patch
from types import SimpleNamespace

from fastapi.testclient import TestClient
from api import app

client = TestClient(app)

AUTHOR = "Mariana Souza"


def check_safe_interaction(interaction):
    assert interaction.autor == "Usuario anónimo"
    assert AUTHOR not in interaction.texto
    assert "[AUTOR]" in interaction.texto


def fake_analyze_text(text):
    assert AUTHOR not in text
    assert "[AUTOR]" in text

    return SimpleNamespace(
        sentimiento="positivo",
        tema="empleabilidad",
        tipo="logro",
        relevancia="alta",
        insight="Conseguí mi primer empleo.",
        model_dump=lambda: {
            "sentimiento": "positivo",
            "tema": "empleabilidad",
            "tipo": "logro",
            "relevancia": "alta",
            "insight": "Conseguí mi primer empleo.",
        },
    ), {}


def fake_analyze_batch(interactions):
    assert len(interactions) == 1
    assert interactions[0]["id"] == "MSG-001"
    assert AUTHOR not in interactions[0]["texto"]
    assert "[AUTOR]" in interactions[0]["texto"]

    analysis = SimpleNamespace(
        id="MSG-001",
        sentimiento="positivo",
        tema="empleabilidad",
        tipo="logro",
        relevancia="alta",
        insight="Conseguí mi primer empleo.",
        model_dump=lambda: {
            "sentimiento": "positivo",
            "tema": "empleabilidad",
            "tipo": "logro",
            "relevancia": "alta",
            "insight": "Conseguí mi primer empleo.",
        },
    )

    return SimpleNamespace(results=[analysis]), {}


def fake_graph_invoke(state):
    check_safe_interaction(state["interaction"])

    return {
        "route": "linkedin",
        "content": "Publicación de prueba",
    }


def test_single_endpoint():
    with (
        patch("api.analyze_text", side_effect=fake_analyze_text),
        patch("api.graph.invoke", side_effect=fake_graph_invoke),
    ):
        response = client.post(
            "/analyze",
            json={
                "autor": AUTHOR,
                "canal": "#general",
                "tipo": "testimonio",
                "texto": "Soy Mariana Souza y conseguí empleo.",
            },
        )

    assert response.status_code == 200, response.text
    assert response.json()["route"] == "linkedin"


def test_batch_endpoint():
    with (
        patch("api.analyze_batch_texts", side_effect=fake_analyze_batch),
        patch("api.graph.invoke", side_effect=fake_graph_invoke),
    ):
        response = client.post(
            "/api/v1/analyze-batch",
            json={
                "origen_comunidad": "Discord",
                "periodo_referencia": "2026-10",
                "interacciones": [
                    {
                        "id": "MSG-001",
                        "autor": AUTHOR,
                        "canal": "#general",
                        "tipo": "testimonio",
                        "texto": "Soy Mariana Souza y conseguí empleo.",
                    }
                ],
            },
        )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["status"] == "exito"
    assert data["interacciones_analizadas"][0]["id"] == "MSG-001"
    assert data["activos_distribucion_generados"]["post_linkedin"] is not None


if __name__ == "__main__":
    test_single_endpoint()
    test_batch_endpoint()
    print("OK: privacidad verificada en ambos endpoints")
import json
from pathlib import Path
from unittest.mock import patch
import pytest
from jsonschema import Draft202012Validator
from streamlit.testing.v1 import AppTest
import app

ROOT = Path(__file__).parent
def read(path): return json.loads((ROOT/path).read_text(encoding="utf-8"))

def test_request_contract():
    v=Draft202012Validator(read("contracts/request.schema.json"))
    v.validate(read("contracts/examples/request_valido.json"))
    assert list(v.iter_errors(read("contracts/examples/request_invalido_blanco.json")))

@pytest.mark.parametrize("scenario", list(read("demo_scenarios/manifest.json")))
def test_scenario_contract(scenario):
    payload=read(f"demo_scenarios/{scenario}.json")
    Draft202012Validator(read("contracts/response.schema.json")).validate(payload)
    assert payload["status"] in ("exito", "parcial", "error")
    assert isinstance(payload["interacciones_fallidas"],list)
    assert app._cargar_respuesta_demo(scenario)==payload

def test_unknown_scenario_is_rejected():
    assert app._cargar_respuesta_demo("../app") is None

def test_faq_uses_backend_fields():
    with patch.object(app.st,"text") as output, patch.object(app.st,"caption"):
        app._mostrar_sugerencia_faq({"pregunta":"Pregunta de prueba", "respuesta":"Respuesta de prueba"})
    assert [c.args[0] for c in output.call_args_list]==["Pregunta: Pregunta de prueba", "Respuesta: Respuesta de prueba"]

@pytest.mark.parametrize("scenario", list(read("demo_scenarios/manifest.json")))
def test_demo_screen(scenario,monkeypatch):
    monkeypatch.setenv("COMMUNITYLAB_DEMO","1")
    at=AppTest.from_file(str(ROOT/"app.py"),default_timeout=30).run()
    at.sidebar.selectbox[0].select(scenario).run()
    at.radio[0].set_value("Pegar JSON").run()
    at.text_area[0].input(json.dumps(read("contracts/examples/request_valido.json"))).run()
    with patch("requests.post") as post:
        at.button[0].click().run()
        post.assert_not_called()
    assert not at.exception
    labels=[e.label for e in at.expander]
    assert "Respuesta simulada" in labels
    assert "Solicitud preparada (sin envío)" in labels
    strings=[x.value for x in at.text]
    faq=read(f"demo_scenarios/{scenario}.json")["activos_distribucion_generados"]
    if faq:
        areas = [x.value for x in at.text_area]
        assert any("Q: ¿Dónde configuro" in x for x in areas)
    if scenario=="resultado_parcial":
        assert sum(x.startswith("ID:") for x in strings)==1
        assert any("000000000003" in x for x in strings)
        assert not any("Interacción #" in x for x in strings)
    else:
        assert not any(x.startswith("ID:") for x in strings)
    if scenario=="error_oci":
        assert any("no se guardaron" in x.value for x in at.warning)
    if scenario=="solo_descartadas":
        assert any("descartadas: 3" in x.value for x in at.caption)

def test_partial_without_detail_does_not_invent_failures():
    with patch.object(app.st,"info") as info, patch.object(app.st,"text") as output:
        app._mostrar_interacciones_fallidas({"status":"parcial"})
    info.assert_called_once()
    output.assert_not_called()

"""Pruebas del contrato de aprobación editorial de Aigoraweave."""

import ast
from pathlib import Path


def test_guardar_edicion_invalida_aprobacion_anterior():
    source = Path(__file__).with_name("app.py").read_text(encoding="utf-8")
    module = ast.parse(source)

    function = next(
        node for node in module.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "_guardar_edicion"
    )

    function_source = ast.get_source_segment(source, function)

    assert "texto_anterior != nuevo_texto" in function_source
    assert "CLAVE_FEEDBACK" in function_source
    assert ".pop(llave, None)" in function_source



def test_editar_texto_aprobado_revoca_aprobacion():
    """Ejecuta la función real con un estado Streamlit simulado."""
    from types import SimpleNamespace

    source = Path(__file__).with_name("app.py").read_text(encoding="utf-8")
    module = ast.parse(source)

    function = next(
        node for node in module.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "_guardar_edicion"
    )

    state = {
        "texto_widget": "Publicación modificada",
        "texto_editado": {"lote:linkedin": "Publicación original"},
        "curaduria_feedback": {"lote:linkedin": "aprobado"},
        "edicion_modo": {"lote:linkedin": True},
    }

    namespace = {
        "st": SimpleNamespace(session_state=state),
        "CLAVE_TEXTO_EDITADO": "texto_editado",
        "CLAVE_FEEDBACK": "curaduria_feedback",
        "CLAVE_EDICION": "edicion_modo",
    }

    isolated = ast.Module(body=[function], type_ignores=[])
    exec(compile(isolated, "<guardar_edicion>", "exec"), namespace)

    namespace["_guardar_edicion"](
        "lote:linkedin",
        "texto_widget",
        "Publicación original",
    )

    assert state["texto_editado"]["lote:linkedin"] == "Publicación modificada"
    assert "lote:linkedin" not in state["curaduria_feedback"]
    assert state["edicion_modo"]["lote:linkedin"] is False

import ast
from pathlib import Path

BASE = Path(__file__).resolve().parent
PROMPT = BASE / "prompts" / "analysis_prompt.txt"
ANALYZER = BASE / "analyzer.py"

REGLAS = (
    "Conserva el tono de marketing",
    "efectos causales",
    "percepción personal",
)


def test_prompt_individual_contiene_reglas_precision():
    contenido = PROMPT.read_text(encoding="utf-8")

    for regla in REGLAS:
        assert regla in contenido

    assert (
        "Una persona compartió que sus proyectos prácticos "
        "le ayudaron a conseguir empleo."
    ) in contenido


def test_prompt_batch_contiene_reglas_precision():
    contenido = ANALYZER.read_text(encoding="utf-8")

    for regla in REGLAS:
        assert regla in contenido


def test_sentimientos_coinciden_con_modelo():
    individual = PROMPT.read_text(encoding="utf-8")
    batch = ANALYZER.read_text(encoding="utf-8")

    for sentimiento in ("positivo", "negativo", "neutro", "mixto"):
        assert f"- {sentimiento}" in individual

    assert "- sentimiento: positivo, negativo, neutro o mixto" in batch


def test_se_conservan_marcadores_y_estructura():
    individual = PROMPT.read_text(encoding="utf-8")
    batch = ANALYZER.read_text(encoding="utf-8")

    assert "{content}" in individual
    assert '"insight":' in individual

    arbol = ast.parse(batch)
    assert any(
        isinstance(nodo, ast.FunctionDef)
        and nodo.name == "analyze_batch_texts"
        for nodo in ast.walk(arbol)
    )
    assert '"results": [' in batch
    assert '"id": "MSG-001"' in batch

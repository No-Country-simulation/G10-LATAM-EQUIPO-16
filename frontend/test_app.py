"""Pruebas automatizadas para las funciones de validación y construcción del payload del frontend."""

from unittest.mock import Mock

import pytest

import app


CSV_VALIDO = """autor,canal,tipo,texto
Ana Torres,#logros,feedback,Me encanta el curso y aprendí mucho.
Luis Soto,#dudas,feedback,No entiendo el tema de redes.
"""

CSV_ENCABEZADOS = """ Autor , Canal ,Tipo,Texto
Ana Torres,#logros,feedback,Me encanta el curso.
"""

JSON_OBJETO = {
    "autor": "Ana Torres",
    "canal": "#logros",
    "tipo": "feedback",
    "texto": "Me encanta el curso.",
}

JSON_LISTA = [
    {"autor": "Ana Torres", "canal": "#logros", "tipo": "feedback", "texto": "Me encanta el curso."},
    {"autor": "Luis Soto", "canal": "#dudas", "tipo": "feedback", "texto": "No entiendo."},
]

JSON_ANIDADO = {"interacciones": JSON_LISTA}


# ---------------------------------------------------------------------------
# CSV
# ---------------------------------------------------------------------------

def test_csv_valido_se_normaliza():
    interacciones, avisos = app._interacciones_desde_csv(CSV_VALIDO)
    assert len(interacciones) == 2
    assert avisos == []
    assert interacciones[0]["autor"] == "Ana Torres"
    assert interacciones[0]["canal"] == "#logros"
    assert interacciones[0]["tipo"] == "feedback"
    assert interacciones[0]["texto"] == "Me encanta el curso y aprendí mucho."


def test_csv_encabezados_mayusculas_y_espacios():
    interacciones, avisos = app._interacciones_desde_csv(CSV_ENCABEZADOS)
    assert len(interacciones) == 1
    assert interacciones[0]["autor"] == "Ana Torres"
    assert interacciones[0]["canal"] == "#logros"
    assert interacciones[0]["tipo"] == "feedback"
    assert interacciones[0]["texto"] == "Me encanta el curso."


def test_csv_vacio_o_malformado():
    interacciones, avisos = app._interacciones_desde_csv("")
    assert interacciones == []
    assert len(avisos) > 0

    interacciones, avisos = app._interacciones_desde_csv("esto no es un csv valido {{{")
    assert interacciones == []
    assert len(avisos) > 0


# ---------------------------------------------------------------------------
# JSON
# ---------------------------------------------------------------------------

def test_json_objeto_individual():
    interacciones, avisos = app._interacciones_desde_json(JSON_OBJETO)
    assert len(interacciones) == 1
    assert avisos == []
    assert interacciones[0]["autor"] == "Ana Torres"
    assert interacciones[0]["texto"] == "Me encanta el curso."


def test_json_lista():
    interacciones, avisos = app._interacciones_desde_json(JSON_LISTA)
    assert len(interacciones) == 2
    assert avisos == []


def test_json_anidado():
    interacciones, avisos = app._interacciones_desde_json(JSON_ANIDADO)
    assert len(interacciones) == 2
    assert avisos == []


def test_json_malformado():
    interacciones, avisos = app._interacciones_desde_json_text("{not valid json")
    assert interacciones == []
    assert len(avisos) > 0


# ---------------------------------------------------------------------------
# Filtrado de filas
# ---------------------------------------------------------------------------

def test_filas_sin_texto_se_descartan():
    interacciones, avisos = app._normalizar_interacciones([
        {"autor": "Ana", "canal": "#logros", "tipo": "feedback", "texto": "   "},
        {"autor": "Luis", "canal": "#dudas", "tipo": "feedback", "texto": "Valida"},
    ])
    assert len(interacciones) == 1
    assert interacciones[0]["texto"] == "Valida"
    assert len(avisos) == 1


def test_interaccion_incompleta_se_descarta():
    interacciones, avisos = app._normalizar_interacciones([
        {"autor": "Ana", "canal": "#logros", "texto": "Falta el tipo"},
    ])
    assert interacciones == []
    assert len(avisos) == 1


# ---------------------------------------------------------------------------
# Límite de interacciones y tamaño de archivo
# ---------------------------------------------------------------------------

def test_limite_interacciones_validas():
    interacciones_validas, avisos = app._normalizar_interacciones(JSON_LISTA * 6)
    interacciones, ignoradas = app._aplicar_limite_interacciones(interacciones_validas)
    assert len(interacciones) == 10
    assert ignoradas == 2


def test_validacion_tamanio_archivo():
    assert app._validar_tamanio_archivo(1024 * 1024) is True
    assert app._validar_tamanio_archivo(1024 * 1024 - 1) is True
    assert app._validar_tamanio_archivo(1024 * 1024 + 1) is False
    assert app._validar_tamanio_archivo(0) is True


# ---------------------------------------------------------------------------
# Payload y errores
# ---------------------------------------------------------------------------

def test_payload_claves_exactas():
    interacciones = [{"autor": "a", "canal": "c", "tipo": "t", "texto": "txt"}]
    payload = app._construir_payload("Comunidad X", "Semana_01", interacciones)
    assert set(payload.keys()) == {"origen_comunidad", "periodo_referencia", "interacciones"}
    assert payload["origen_comunidad"] == "Comunidad X"
    assert payload["periodo_referencia"] == "Semana_01"
    assert payload["interacciones"] == interacciones
    assert set(interacciones[0].keys()) == {"autor", "canal", "tipo", "texto"}


def test_mensaje_error_backend_campos_y_mock():
    respuesta = Mock()
    respuesta.status_code = 400
    respuesta.json.return_value = {
        "timestamp": "2026-10-16T15:00:00",
        "status": 400,
        "error": "Solicitud inválida",
        "mensaje": "interacciones: debe tener entre 1 y 10 elementos",
    }
    assert "interacciones" in app._obtener_mensaje_error(respuesta)
    assert "400" in app._generar_mensaje_error_backend(400, respuesta)

    respuesta_503 = Mock()
    respuesta_503.status_code = 503
    respuesta_503.json.return_value = {"error": "Servicio de IA no disponible", "mensaje": "No se pudo procesar el lote."}
    mensaje_503 = app._generar_mensaje_error_backend(503, respuesta_503)
    assert "servicio de ia" in mensaje_503.lower()
    assert "intente" in mensaje_503.lower()

    respuesta_no_json = Mock()
    respuesta_no_json.status_code = 502
    respuesta_no_json.json.side_effect = Exception("no json")
    mensaje_502 = app._generar_mensaje_error_backend(502, respuesta_no_json)
    assert "bad gateway" in mensaje_502.lower()
    assert "502" in app._obtener_mensaje_error(respuesta_no_json)


def test_url_backend_default_y_variable_de_entorno(monkeypatch):
    monkeypatch.delenv("BACKEND_URL", raising=False)
    assert app._obtener_url_backend() == "http://localhost:8080/api/v1/community/process"
    monkeypatch.setenv("BACKEND_URL", "http://backend:8080/api/v1/community/process")
    assert app._obtener_url_backend() == "http://backend:8080/api/v1/community/process"

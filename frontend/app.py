import io
import json
import os

import pandas as pd
import requests
import streamlit as st

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

MAX_INTERACCIONES = 10
TAMANIO_MAXIMO_BYTES = 1 * 1024 * 1024  # 1 MB
TIMEOUT_CONEXION_SEGUNDOS = float(os.environ.get("BACKEND_TIMEOUT_CONEXION", "10"))
# Timeout de respuesta del backend. Con el plan futuro de reintentos automáticos
# (hasta 3 intentos con backoff) el peor caso puede superar 90 s; el ajuste se
# puede realizar mediante la variable de entorno BACKEND_TIMEOUT.
TIMEOUT_RESPUESTA_SEGUNDOS = float(os.environ.get("BACKEND_TIMEOUT", "90"))
URL_BACKEND_DEFAULT = "http://localhost:8080/api/v1/community/process"

CAMPOS_CANONICOS = ("autor", "canal", "tipo", "texto")
CLAVE_INTERACCIONES = "interacciones"
CLAVE_INTERACCIONES_ALTERNATIVAS = ("data", "items", "mensajes")
ALIASES_CAMPOS = {
    "autor": ("autor", "author", "nombre", "usuario", "creador"),
    "canal": ("canal", "channel", "comunidad", "servicio", "plataforma", "fuente"),
    "tipo": ("tipo", "type", "categoria", "category", "tipo_interaccion", "tema_tipo"),
    "texto": ("texto", "text", "mensaje", "content", "contenido", "cuerpo", "body", "interaccion"),
}


def _normalizar_clave(clave: str) -> str:
    """Normaliza el nombre de una columna o alias para comparación."""
    return str(clave).strip().lower()


def _construir_mapa_claves() -> dict:
    mapa: dict = {}
    for campo, alias_lista in ALIASES_CAMPOS.items():
        for alias in alias_lista:
            mapa[_normalizar_clave(alias)] = campo
    return mapa


_MAPA_CLAVE_CANONICA = _construir_mapa_claves()


def _limpiar_texto(valor) -> str:
    """Recorta espacios al inicio/fin y colapsa espacios internos consecutivos."""
    return " ".join(str(valor).split())


def _normalizar_interaccion(raw) -> dict | None:
    """Normaliza una interacción al contrato {autor, canal, tipo, texto}.

    Devuelve None cuando la interacción no es válida (fila vacía o incompleta).
    """
    if not isinstance(raw, dict):
        return None
    valores: dict = {}
    for clave, valor in raw.items():
        if not isinstance(valor, str):
            continue
        campo = _MAPA_CLAVE_CANONICA.get(_normalizar_clave(str(clave)))
        if campo is not None:
            valores[campo] = _limpiar_texto(valor)
    interaccion = {campo: valores.get(campo, "") for campo in CAMPOS_CANONICOS}
    if not all(interaccion[campo] for campo in CAMPOS_CANONICOS):
        return None
    return interaccion


def _normalizar_interacciones(interacciones_raw):
    """Normaliza una lista de interacciones crudas.

    Devuelve una tupla (interacciones_validas, avisos).
    """
    avisos: list = []
    if not isinstance(interacciones_raw, list):
        return [], ["Las interacciones deben ser una lista de objetos."]
    validas: list = []
    for indice, item in enumerate(interacciones_raw):
        interaccion = _normalizar_interaccion(item)
        if interaccion is None:
            avisos.append(
                f"Fila {indice + 1}: se descartó porque falta información obligatoria o está vacía."
            )
        else:
            validas.append(interaccion)
    return validas, avisos


def _interacciones_desde_json(data) -> tuple:
    """Convierte un objeto JSON (individual o lista) a interacciones válidas."""
    if isinstance(data, list):
        return _normalizar_interacciones(data)
    if isinstance(data, dict):
        claves = (CLAVE_INTERACCIONES,) + CLAVE_INTERACCIONES_ALTERNATIVAS
        for clave in claves:
            valor = data.get(clave)
            if isinstance(valor, list):
                return _normalizar_interacciones(valor)
        return _normalizar_interacciones([data])
    return [], ["El JSON proporcionado no tiene un formato válido para interacciones."]


def _interacciones_desde_json_text(texto: str) -> tuple:
    """Parsea el texto JSON y devuelve (interacciones_validas, avisos)."""
    try:
        data = json.loads(texto)
    except Exception:
        return [], ["El JSON proporcionado no es válido. Revise el formato e intente nuevamente."]
    return _interacciones_desde_json(data)


def _interacciones_desde_csv(texto: str) -> tuple:
    """Convierte el contenido CSV a interacciones válidas usando pandas."""
    try:
        df = pd.read_csv(io.StringIO(texto))
    except Exception:
        return [], ["No se pudo leer el archivo CSV: el formato no es válido."]
    df = df.fillna("")
    df.columns = [_normalizar_clave(str(columna)) for columna in df.columns]
    columnas_canonicas: dict = {}
    for columna in df.columns:
        campo = _MAPA_CLAVE_CANONICA.get(columna)
        if campo is not None and campo not in columnas_canonicas.values():
            columnas_canonicas[columna] = campo
    registros: list = []
    for _, fila in df.iterrows():
        registro: dict = {}
        for columna, campo in columnas_canonicas.items():
            valor = fila[columna]
            if valor is None or (isinstance(valor, float) and pd.isna(valor)):
                valor = ""
            registro[campo] = _limpiar_texto(str(valor))
        registros.append(registro)
    if not registros:
        return [], ["El archivo no contiene interacciones para procesar."]
    return _normalizar_interacciones(registros)


def _validar_tamanio_archivo(tamanio_bytes: int) -> bool:
    """Indica si el archivo está dentro del límite de 1 MB."""
    return tamanio_bytes <= TAMANIO_MAXIMO_BYTES


def _aplicar_limite_interacciones(interacciones: list, maximo: int = MAX_INTERACCIONES) -> tuple:
    """Aplica el límite de interacciones por lote.

    Devuelve una tupla (interacciones, ignoradas).
    """
    if len(interacciones) > maximo:
        return interacciones[:maximo], len(interacciones) - maximo
    return interacciones, 0


def _construir_payload(origen_comunidad: str, periodo_referencia: str, interacciones: list) -> dict:
    """Construye el payload con el contrato vigente del backend."""
    return {
        "origen_comunidad": origen_comunidad.strip(),
        "periodo_referencia": periodo_referencia.strip(),
        "interacciones": interacciones,
    }


def _obtener_url_backend() -> str:
    """Devuelve la URL del backend desde variable de entorno o st.secrets."""
    url = os.environ.get("BACKEND_URL") or URL_BACKEND_DEFAULT
    try:
        secreto = st.secrets.get("BACKEND_URL")
        if secreto:
            url = str(secreto)
    except Exception:
        pass
    return url


def _obtener_mensaje_error(respuesta) -> str:
    """Extrae un mensaje legible desde respuesta.error/mensaje/message."""
    try:
        datos = respuesta.json()
    except Exception:
        return f"No se pudo leer la respuesta del backend (código {respuesta.status_code})."
    if isinstance(datos, dict):
        for clave in ("mensaje", "message", "error"):
            valor = datos.get(clave)
            if isinstance(valor, str) and valor.strip():
                return valor.strip()
    return f"No se pudo procesar la solicitud (código {respuesta.status_code})."


def _generar_mensaje_error_backend(status_code: int, respuesta) -> str:
    """Genera el mensaje de error legible para un código HTTP de respuesta."""
    if status_code == 400:
        return f"Solicitud rechazada por el backend (400): {_obtener_mensaje_error(respuesta)}"
    if status_code == 429:
        return "Demasiadas solicitudes al servicio de IA: la cuota está agotada. Intente más tarde."
    if status_code == 502:
        return "El motor de IA respondió con un error temporal (bad gateway). No se realizarán reintentos automáticos."
    if status_code == 503:
        return "El servicio de IA no está disponible en este momento. Intente más tarde."
    return f"Error {status_code} al procesar la solicitud: {_obtener_mensaje_error(respuesta)}"


def _etiquetar_sentimiento(valor) -> str:
    """Devuelve una etiqueta legible del sentimiento; maneja el valor mixto."""
    texto = str(valor or "").strip().lower()
    if texto == "mixto":
        return "Mixto"
    return str(valor or "").strip() or "N/A"


def _formato_temas(temas) -> str:
    """Devuelve los temas principales como texto legible."""
    if not temas:
        return "Sin temas detectados"
    return ", ".join(str(tema) for tema in temas)


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------

st.set_page_config(page_title="CommunityLab", layout="wide")
st.title("CommunityLab - Panel MVP")

url_backend = _obtener_url_backend()
interacciones = None
avisos: list = []

modo = st.radio("¿Cómo desea cargarlas?", ["Subir archivo", "Pegar JSON"])

origen = st.text_input("Origen comunidad", "Discord_Grupo_ONE_G10")
periodo = st.text_input("Periodo", "Semana_01")

if modo == "Subir archivo":
    archivo = st.file_uploader("Archivo CSV o JSON", type=["csv", "json"])
    if archivo is not None:
        if not _validar_tamanio_archivo(archivo.size):
            st.error(
                f"El archivo supera el tamaño máximo permitido de 1 MB "
                f"({archivo.size / (1024 * 1024):.2f} MB)."
            )
            interacciones = None
        elif archivo.name.lower().endswith(".json"):
            try:
                data = json.load(archivo)
                interacciones, avisos = _interacciones_desde_json(data)
            except Exception:
                interacciones = None
                avisos = ["El archivo JSON no es válido."]
        else:
            try:
                texto = archivo.read().decode("utf-8")
            except Exception:
                interacciones = None
                avisos = ["No se pudo leer el contenido del archivo CSV."]
            else:
                interacciones, avisos = _interacciones_desde_csv(texto)

if modo == "Pegar JSON":
    texto = st.text_area("Pegue el JSON aquí", height=200)
    if texto.strip():
        interacciones, avisos = _interacciones_desde_json_text(texto)

for aviso in avisos:
    st.warning(aviso)

if interacciones:
    st.write(f"Se cargaron {len(interacciones)} interacciones")
    st.dataframe(pd.DataFrame(interacciones))

interacciones_a_enviar, interacciones_ignoradas = _aplicar_limite_interacciones(interacciones or [])
if interacciones_ignoradas > 0:
    st.warning(
        f"El backend acepta un máximo de {MAX_INTERACCIONES} interacciones por lote. "
        f"Se ignoraron {interacciones_ignoradas} interacciones adicionales."
    )

st.markdown("### Enviar al backend")
st.caption(f"Enviando a: {url_backend}")

if st.button("Procesar"):
    if not interacciones_a_enviar:
        st.warning("Debe cargar datos antes de procesar")
    else:
        payload = _construir_payload(origen, periodo, interacciones_a_enviar)
        with st.spinner("Procesando interacciones con el motor de IA, esto puede tardar unos segundos..."):
            try:
                respuesta = requests.post(
                    url_backend,
                    json=payload,
                    timeout=(TIMEOUT_CONEXION_SEGUNDOS, TIMEOUT_RESPUESTA_SEGUNDOS),
                )
            except requests.exceptions.Timeout:
                st.error("La solicitud tardó demasiado en responder. Intente nuevamente.")
            except requests.exceptions.ConnectionError:
                st.error("No fue posible conectarse con el backend. Verifique que el servicio esté disponible.")
            except requests.exceptions.RequestException:
                st.error("Ocurrió un error al comunicarse con el backend. Intente nuevamente.")
            else:
                if respuesta.status_code == 400:
                    st.error(_generar_mensaje_error_backend(400, respuesta))
                elif respuesta.status_code == 429:
                    st.error(_generar_mensaje_error_backend(429, respuesta))
                elif respuesta.status_code == 502:
                    st.error(_generar_mensaje_error_backend(502, respuesta))
                elif respuesta.status_code == 503:
                    st.error(_generar_mensaje_error_backend(503, respuesta))
                elif not respuesta.ok:
                    st.error(_generar_mensaje_error_backend(respuesta.status_code, respuesta))
                else:
                    st.markdown("### Resultados del análisis")
                    try:
                        resp = respuesta.json()
                    except Exception:
                        st.error("La respuesta del backend no es JSON válido")
                        resp = None
                    if resp:
                        estado = str(resp.get("status") or "")
                        if estado == "exito":
                            st.success("Análisis procesado exitosamente.")
                        elif estado == "parcial":
                            st.warning("Resultado parcial: algunas interacciones no pudieron procesarse.")
                        elif estado == "error":
                            st.error("El análisis terminó con errores.")

                        # Mostrar resumen de comunidad si existe
                        summary = resp.get("resumen_comunidad")
                        if summary:
                            sentimiento = _etiquetar_sentimiento(summary.get("sentimiento_predominante"))
                            temas = summary.get("temas_principales") or []
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("Sentimiento predominante", sentimiento)
                            with col2:
                                st.metric("Total interacciones procesadas", summary.get("total_interacciones_procesadas") or 0)
                            st.write(f"**Temas principales:** {_formato_temas(temas)}")

                        # Mostrar activos de distribución si existen
                        activos = resp.get("activos_distribucion_generados") or {}
                        if activos:
                            tarjetas = [
                                ("Post LinkedIn", activos.get("post_linkedin"), "linkedin"),
                                ("Destacado Newsletter", activos.get("destaque_newsletter_semanal"), "newsletter"),
                                ("Sugerencia FAQ", activos.get("sugerencia_contenido_faq"), "faq"),
                            ]
                            columnas_activos = st.columns(3)
                            for columna, (titulo, activo, tipo) in zip(columnas_activos, tarjetas):
                                with columna:
                                    st.markdown(f"**{titulo}**")
                                    if not activo:
                                        st.caption("Sin activo generado por el motor.")
                                        continue
                                    if tipo == "linkedin":
                                        st.write(f"Título: {activo.get('titulo')}")
                                        st.write(f"Copy: {activo.get('copy')}")
                                        st.write(f"Canal recomendado: {activo.get('canal_recomendado')}")
                                        st.write(f"Potencial de engagement: {activo.get('potencial_engagement')}")
                                    elif tipo == "newsletter":
                                        st.write(f"Sección: {activo.get('seccion')}")
                                        st.write(f"Titular: {activo.get('titular')}")
                                        st.write(f"Resumen: {activo.get('resumen')}")
                                    else:
                                        st.write(f"Tema: {activo.get('tema')}")
                                        st.write(f"Origen: {activo.get('origen')}")
                                        st.write(f"Estado: {activo.get('status')}")
                            almacenamiento = activos.get("almacenamiento_oci") or {}
                            if almacenamiento:
                                st.caption(f"Almacenamiento OCI: {almacenamiento.get('status')} - {almacenamiento.get('ruta_objeto')}")

                        if not summary:
                            st.info("El backend no devolvió un resumen de comunidad.")
                        if not activos:
                            st.info("El backend no devolvió activos de distribución.")

                        st.info("Nota: El 'relevance score' por mensaje está pendiente de integración con el backend/ML (persistencia de interacciones_analizadas).")

                    with st.expander("Respuesta completa del backend"):
                        try:
                            st.json(resp if resp is not None else respuesta.json())
                        except Exception:
                            st.text("La respuesta del backend no es JSON válida")

with st.expander("Ver el payload enviado"):
    st.json({
        "origen_comunidad": origen.strip(),
        "periodo_referencia": periodo.strip(),
        "interacciones": interacciones_a_enviar or [],
    })

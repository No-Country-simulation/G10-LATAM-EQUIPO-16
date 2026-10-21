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
# Timeout de respuesta del backend. Valor por defecto 200 segundos configurable
# mediante la variable de entorno BACKEND_TIMEOUT.
TIMEOUT_RESPUESTA_SEGUNDOS = float(os.environ.get("BACKEND_TIMEOUT", "200"))
URL_BACKEND_DEFAULT = "http://localhost:8080/api/v1/community/process"
# Modo demo local - archivo de respuesta simulada para demostración sin backend
MODO_DEMO_VAR = "COMMUNITYLAB_DEMO"
DEMO_RESPUESTA_ARCHIVO = os.path.join(os.path.dirname(__file__), "demo_respuesta_simulada.json")

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

    Reglas de validación:
    - Si falta `autor`, se usa "Anónimo".
    - Si falta `canal`, se usa "General".
    - Si falta `tipo`, se usa "otro".
    - Si falta `texto`, está vacío o contiene únicamente espacios, se descarta la fila.
    - Limpia espacios innecesarios y normaliza valores sin alterar contenido legítimo.
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

    # Aplicar valores por defecto para metadatos opcionales
    autor = valores.get("autor", "").strip()
    canal = valores.get("canal", "").strip()
    tipo = valores.get("tipo", "").strip()
    texto = valores.get("texto", "").strip()

    # Validar que el texto sea obligatorio y no esté vacío
    if not texto:
        return None

    # Normalizar con valores por defecto
    interaccion = {
        "autor": autor if autor else "Anónimo",
        "canal": canal if canal else "General",
        "tipo": tipo if tipo else "otro",
        "texto": texto,
    }
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
        # Asegurar que todos los campos canónicos existan en el registro
        for campo in CAMPOS_CANONICOS:
            if campo not in registro:
                registro[campo] = ""
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
        return "El motor de IA no pudo procesar el lote. Intente más tarde."
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


def _mostrar_post_linkedin(activo: dict) -> None:
    """Muestra una publicación de LinkedIn de forma legible."""
    titulo = activo.get("titulo")
    copy = activo.get("copy")
    canal = activo.get("canal_recomendado")
    potencial = activo.get("potencial_engagement")

    if titulo:
        st.write(f"**Título:** {titulo}")
    if copy:
        st.text_area("Copy", value=copy, height=120, disabled=True, label_visibility="collapsed")
    if canal:
        st.write(f"**Canal recomendado:** {canal}")
    if potencial:
        st.write(f"**Potencial de engagement:** {potencial}")


def _mostrar_destaque_newsletter(activo: dict) -> None:
    """Muestra un destacado para newsletter de forma legible."""
    seccion = activo.get("seccion")
    titular = activo.get("titular")
    resumen = activo.get("resumen")

    if seccion:
        st.write(f"**Sección:** {seccion}")
    if titular:
        st.write(f"**Titular:** {titular}")
    if resumen:
        st.text_area("Resumen", value=resumen, height=100, disabled=True, label_visibility="collapsed")


def _mostrar_sugerencia_faq(activo: dict) -> None:
    """Muestra una sugerencia de FAQ de forma legible.

    Contrato del backend (FaqSuggestionDto): tema, origen, status.
    No existen campos 'pregunta' ni 'respuesta' en la respuesta actual.
    """
    st.caption("💡 Tip de la Semana")
    tema = activo.get("tema")
    origen = activo.get("origen")
    status = activo.get("status")

    if tema:
        st.write(f"**Tema:** {tema}")
    if origen:
        st.write(f"**Origen:** {origen}")
    if status:
        st.write(f"**Estado del borrador:** {status}")


def _mostrar_almacenamiento_oci(almacenamiento: dict) -> None:
    """Muestra información de almacenamiento OCI."""
    bucket = almacenamiento.get("bucket")
    ruta = almacenamiento.get("ruta_objeto")
    status = almacenamiento.get("status")

    if bucket or ruta or status:
        st.markdown("**Almacenamiento OCI**")
        if bucket:
            st.write(f"- Bucket: {bucket}")
        if ruta:
            st.write(f"- Ruta del objeto: {ruta}")
        if status:
            st.write(f"- Estado: {status}")
            if status == "error_subida":
                st.warning(
                    "La subida a OCI Object Storage falló. La generación de activos se completó, "
                    "pero los archivos no se guardaron en el almacenamiento."
                )


def _cargar_respuesta_demo() -> dict | None:
    """Carga la respuesta simulada desde el archivo JSON para el modo demo.

    Returns:
        dict con la respuesta simulada o None si no se pudo cargar.
    """
    try:
        with open(DEMO_RESPUESTA_ARCHIVO, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------

st.set_page_config(page_title="CommunityLab", layout="wide")
st.title("CommunityLab - Panel MVP")

# Modo demo local - solo activado explícitamente via variable de entorno
modo_demo = os.environ.get(MODO_DEMO_VAR, "").lower() in ("1", "true", "yes", "on")
if modo_demo:
    st.sidebar.warning("⚠️ MODO DEMO ACTIVO - Datos simulados, sin llamada al backend")

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
if modo_demo:
    st.caption("Modo demo: usando respuesta simulada (sin llamada HTTP)")
else:
    st.caption(f"Enviando a: {url_backend}")

if st.button("Procesar"):
    if not interacciones_a_enviar:
        st.warning("Debe cargar datos antes de procesar")
    else:
        payload = _construir_payload(origen, periodo, interacciones_a_enviar)

        if modo_demo:
            # Modo demo: usar respuesta simulada sin llamar al backend
            with st.spinner("Cargando respuesta simulada..."):
                resp = _cargar_respuesta_demo()
            if resp is None:
                st.error("No se pudo cargar la respuesta simulada. Verifique que existe demo_respuesta_simulada.json")
                resp = None
        else:
            # Modo normal: llamada real al backend
            with st.spinner("Procesando interacciones con el motor de IA, esto puede tardar unos segundos..."):
                try:
                    respuesta = requests.post(
                        url_backend,
                        json=payload,
                        timeout=(TIMEOUT_CONEXION_SEGUNDOS, TIMEOUT_RESPUESTA_SEGUNDOS),
                    )
                except requests.exceptions.Timeout:
                    st.error("La solicitud tardó demasiado en responder. Intente nuevamente.")
                    resp = None
                except requests.exceptions.ConnectionError:
                    st.error("No fue posible conectarse con el backend. Verifique que el servicio esté disponible.")
                    resp = None
                except requests.exceptions.RequestException:
                    st.error("Ocurrió un error al comunicarse con el backend. Intente nuevamente.")
                    resp = None
                else:
                    if respuesta.status_code == 400:
                        st.error(_generar_mensaje_error_backend(400, respuesta))
                        resp = None
                    elif respuesta.status_code == 429:
                        st.error(_generar_mensaje_error_backend(429, respuesta))
                        resp = None
                    elif respuesta.status_code == 502:
                        st.error(_generar_mensaje_error_backend(502, respuesta))
                        resp = None
                    elif respuesta.status_code == 503:
                        st.error(_generar_mensaje_error_backend(503, respuesta))
                        resp = None
                    elif not respuesta.ok:
                        st.error(_generar_mensaje_error_backend(respuesta.status_code, respuesta))
                        resp = None
                    else:
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

                # Mostrar total de interacciones descartadas
                total_descartadas = summary.get("total_descartadas")
                if total_descartadas is None:
                    total_descartadas = resp.get("total_descartadas", 0)
                if total_descartadas:
                    st.caption(f"Interacciones descartadas: {total_descartadas}")

            # Mostrar activos de distribución si existen
            activos = resp.get("activos_distribucion_generados") or {}
            if activos:
                # Leer almacenamiento OCI: primero nivel raíz, luego fallback a activos
                almacenamiento = resp.get("almacenamiento_oci") or activos.get("almacenamiento_oci") or {}

                tarjetas = [
                    ("Publicación LinkedIn", activos.get("post_linkedin"), "linkedin"),
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
                            _mostrar_post_linkedin(activo)
                        elif tipo == "newsletter":
                            _mostrar_destaque_newsletter(activo)
                        else:
                            _mostrar_sugerencia_faq(activo)

                # Mostrar información de almacenamiento OCI
                if almacenamiento:
                    _mostrar_almacenamiento_oci(almacenamiento)

            if not summary:
                st.info("El backend no devolvió un resumen de comunidad.")
            if not activos:
                st.info("El backend no devolvió activos de distribución.")

            # Mostrar interacciones fallidas si el estado es parcial
            if estado == "parcial":
                interacciones_analizadas = resp.get("interacciones_analizadas") or []
                # Obtener IDs de las interacciones enviadas para comparar
                # NOTA: El backend usa UUIDs, el frontend índices 0..N. Correlación aproximada.
                ids_enviados = {str(i) for i in range(len(interacciones_a_enviar))}
                ids_procesados = {str(item.get("id")) for item in interacciones_analizadas if item.get("id")}
                ids_fallidos = ids_enviados - ids_procesados
                if ids_fallidos:
                    with st.expander("Interacciones que fallaron", expanded=False):
                        st.caption("Nota: Los IDs del backend son UUIDs; esta lista usa índices locales como aproximación.")
                        for idx in sorted(ids_fallidos, key=int):
                            st.write(f"- Interacción #{idx}: no se pudo procesar")

            with st.expander("Respuesta completa del backend"):
                try:
                    st.json(resp)
                except Exception:
                    st.text("La respuesta del backend no es JSON válida")

with st.expander("Ver el payload enviado"):
    st.json({
        "origen_comunidad": origen.strip(),
        "periodo_referencia": periodo.strip(),
        "interacciones": interacciones_a_enviar or [],
    })

import base64
import html
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
    """Presenta los campos de FaqSuggestionDto, admitiendo versiones incompletas."""
    st.caption("💡 Tip de la Semana")
    for campo, etiqueta in (("tema", "Tema"), ("origen", "Origen"),
                            ("pregunta", "Pregunta"), ("respuesta", "Respuesta"),
                            ("status", "Estado del borrador")):
        valor = activo.get(campo)
        if valor:
            st.text(f"{etiqueta}: {valor}")


def _mostrar_interacciones_fallidas(resp: dict) -> None:
    """Usa los IDs y motivos declarados por Backend; no infiere filas locales."""
    fallidas = resp.get("interacciones_fallidas") or []
    if fallidas:
        with st.expander("Interacciones que fallaron", expanded=True):
            for item in fallidas:
                st.text(f"ID: {item.get('id') or 'No informado'}")
                st.text(f"Motivo: {item.get('motivo') or 'No informado'}")
    elif resp.get("status") == "parcial":
        st.info("El backend informó un resultado parcial sin detalle de interacciones fallidas.")


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


def _cargar_respuesta_demo(escenario: str | None = None) -> dict | None:
    """Carga la respuesta simulada desde el archivo JSON para el modo demo.

    Returns:
        dict con la respuesta simulada o None si no se pudo cargar.
    """
    try:
        ruta = DEMO_RESPUESTA_ARCHIVO
        if escenario is not None:
            with open(os.path.join(os.path.dirname(__file__), "demo_scenarios", "manifest.json"), encoding="utf-8") as manifest_file:
                permitidos = json.load(manifest_file)
            if escenario not in permitidos:
                return None
            ruta = os.path.join(os.path.dirname(__file__), "demo_scenarios", escenario + ".json")
        with open(ruta, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None



# ---------------------------------------------------------------------------
# Tema visual (CSS)
# ---------------------------------------------------------------------------

# Claves de st.session_state (persisten entre reruns, cambios de pestaña y clics)
CLAVE_RESULTADO = "ultimo_resultado_backend"   # {"resp", "enviadas", "items"} del último HTTP 200
CLAVE_TEXTO_EDITADO = "texto_editado"          # {llave_activo: texto guardado}
CLAVE_EDICION = "edicion_modo"                 # {llave_activo: bool}
CLAVE_FEEDBACK = "curaduria_feedback"          # {llave_activo: "aprobado" | "rechazado"}
CLAVE_PROCESANDO = "cl_procesando"             # True mientras corre la petición
CLAVE_MENSAJE = "cl_mensaje_proceso"           # (nivel, texto) del último intento
CLAVE_MODO = "cl_modo_carga"
CLAVE_JSON = "cl_texto_json"
CLAVE_UPLOADER = "cl_uploader_n"

# Datos de ejemplo (ficticios, DEC-08: autores neutros, sin nombres ni iniciales)
_A1, _A2 = "Un miembro de nuestra comunidad", "Una persona de nuestra comunidad"
DATOS_EJEMPLO = [
    {"autor": _A1, "canal": "Discord", "tipo": "logro", "texto": "Terminé el módulo de Spring Boot y por fin mi API responde. Gracias a quienes me ayudaron en el canal."},
    {"autor": _A2, "canal": "Alura Latam", "tipo": "feedback", "texto": "Las clases de la ruta de IA están muy claras, me ayudaron a armar mi primer proyecto para el portafolio."},
    {"autor": _A1, "canal": "Discord", "tipo": "pregunta", "texto": "¿Alguien sabe cómo conectar un bucket de OCI Object Storage desde Java? Me pierdo con las credenciales."},
    {"autor": _A2, "canal": "WhatsApp", "tipo": "feedback", "texto": "El grupo de estudio de esta semana estuvo genial, aprendí mucho sobre cómo escribir buenos prompts."},
    {"autor": _A1, "canal": "Alura Latam", "tipo": "sugerencia", "texto": "Sería útil tener más ejercicios prácticos al final de cada módulo de IA generativa."},
    {"autor": _A2, "canal": "Discord", "tipo": "logro", "texto": "Conseguí una entrevista para un puesto junior de datos usando lo que practiqué en esta comunidad."},
    {"autor": _A1, "canal": "LinkedIn", "tipo": "feedback", "texto": "Excelente iniciativa, se nota el esfuerzo de la comunidad por ayudar a quienes recién empiezan."},
    {"autor": _A2, "canal": "WhatsApp", "tipo": "otro", "texto": "jajaja ok 👍"},
    {"autor": _A1, "canal": "Alura Latam", "tipo": "duda", "texto": "No me queda claro cuándo conviene usar un agente en lugar de una cadena simple de prompts, ¿hay algún ejemplo?"},
    {"autor": _A2, "canal": "Discord", "tipo": "queja", "texto": "El horario de las mentorías se cruza con mi trabajo, ojalá hubiera grabaciones."},
    {"autor": _A1, "canal": "Discord", "tipo": "pregunta", "texto": "¿Qué certificaciones recomiendan para empezar en la nube sin gastar mucho?"},
    {"autor": _A2, "canal": "Alura Latam", "tipo": "feedback", "texto": "El foro de la ruta de datos me resolvió una duda de pandas en minutos."},
]

CSS_TEMA = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;600;700&family=Inter:wght@400;500;600&display=swap');
/* Oculta menú de 3 puntos, botón Deploy, header, footer y barra decorativa (igual que app_final) */
#MainMenu,footer,.stAppDeployButton,div[data-testid="stDecoration"],header[data-testid="stHeader"]{visibility:hidden!important;display:none!important;}
:root{--navy:#252733;--navy2:#323544;--coral:#F98B72;--mint:#9BE19D;--bg:#E8F4F3;--ink:#252733;--muted:#6b7280;--card:#ffffff;--line:#d6e6e4;}
html,body,.stApp,[data-testid="stAppViewContainer"]{background:var(--bg)!important;font-family:'Inter',system-ui,sans-serif;color:var(--ink);}
header[data-testid="stHeader"]{background:transparent!important;}
.block-container{padding-top:3rem!important;padding-bottom:3rem;max-width:1320px;}
h1,h2,h3,h4{font-family:'Barlow Condensed','Inter',sans-serif!important;letter-spacing:.2px;color:var(--navy);}

/* Sidebar oscura */
[data-testid="stSidebar"]{background:var(--navy)!important;}
[data-testid="stSidebar"] *{color:#d9dce6;}
[data-testid="stSidebar"] label p,[data-testid="stSidebar"] .stCaption,[data-testid="stSidebar"] small{color:#aab0c0!important;}
[data-testid="stSidebar"] input,[data-testid="stSidebar"] [data-baseweb="select"] *{color:#252733!important;}
.cl-side-brand{font-family:'Barlow Condensed',sans-serif;font-size:1.7rem;font-weight:700;color:#fff;margin:.2rem 0 .2rem;}
.cl-side-brand span{color:var(--coral);}
.cl-side-h{font-size:.72rem;text-transform:uppercase;letter-spacing:.12em;color:var(--coral)!important;margin:1.2rem 0 .4rem;font-weight:600;}
.cl-status{display:flex;justify-content:space-between;gap:.5rem;font-size:.82rem;padding:.45rem 0;border-bottom:1px solid #3a3d4e;}
.cl-status b{color:#fff;font-weight:500;text-align:right;word-break:break-all;}
.cl-demo-flag{background:rgba(249,139,114,.15);border:1px solid var(--coral);color:#ffd9d0;border-radius:10px;padding:.6rem .7rem;font-size:.82rem;}

/* Barra superior */
.cl-top{display:flex;align-items:center;gap:1.2rem;background:#fff;border-radius:14px;padding:.7rem 1.2rem;box-shadow:0 1px 3px rgba(37,39,51,.08);margin-bottom:1.1rem;flex-wrap:wrap;}
.cl-top img{height:34px;display:block;}
.cl-brandtxt{font-family:'Barlow Condensed',sans-serif;font-size:1.6rem;font-weight:700;color:var(--navy);}
.cl-brandtxt span{color:var(--coral);}
.cl-crumb{color:var(--muted);font-size:.9rem;flex:1;}
.cl-chip{display:inline-block;padding:.25rem .7rem;border-radius:999px;font-size:.78rem;font-weight:600;margin-left:.4rem;}
.cl-chip.navy{background:var(--navy);color:#fff;}
.cl-chip.coral{background:rgba(249,139,114,.18);color:#b84a33;}
.cl-chip.mint{background:rgba(155,225,157,.35);color:#1f6b2a;}
.cl-chip.grey{background:#eef1f4;color:#4b5563;}

/* Tarjetas (st.container(border=True, key="card_*")) */
div[class*="st-key-card"]{background:var(--card);border:none!important;border-radius:14px;box-shadow:0 1px 3px rgba(37,39,51,.08);padding:.4rem .6rem;}
div[class*="st-key-card"] button{width:100%;border-radius:8px;padding:.3rem .4rem;font-size:.88rem;white-space:nowrap;}
div[class*="st-key-card"] [class*="st-key-cl_edit_"] button{width:auto;min-width:0;padding:.25rem .5rem;font-size:1rem;line-height:1.2;}
/* Texto revisable: legible aunque esté en modo lectura, y sin cursor de "prohibido" */
div[class*="st-key-card"] textarea{font-size:.92rem;line-height:1.5;}
div[class*="st-key-card"] textarea:disabled{color:#252733!important;-webkit-text-fill-color:#252733!important;opacity:1!important;cursor:default!important;}
div[class*="st-key-card"] [data-testid="stTextArea"],div[class*="st-key-card"] [data-baseweb="textarea"],div[class*="st-key-card"] [data-baseweb="base-input"]{opacity:1!important;cursor:default!important;}
div[class*="st-key-card"] button[kind="primary"]{background:var(--coral);border-color:var(--coral);color:#fff;}
.cl-card-h{display:flex;justify-content:space-between;align-items:center;margin-bottom:.3rem;}
.cl-card-t{font-family:'Barlow Condensed',sans-serif;font-size:1.25rem;font-weight:600;color:var(--navy);}
.cl-meta{margin:.2rem 0 .5rem;}

/* KPI */
.cl-kpis{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:1rem;margin:0 0 1.1rem;}
@media(max-width:900px){.cl-kpis{grid-template-columns:repeat(2,minmax(0,1fr));}}
.kpi{background:#fff;border-radius:14px;overflow:hidden;box-shadow:0 1px 3px rgba(37,39,51,.08);}
.kpi-h{background:var(--navy);color:#fff;font-size:.74rem;letter-spacing:.1em;text-transform:uppercase;padding:.5rem .9rem;font-weight:600;}
.kpi-b{display:flex;justify-content:space-between;align-items:center;padding:.8rem .9rem .2rem;}
.kpi-n{font-family:'Barlow Condensed',sans-serif;font-size:2.6rem;font-weight:700;color:var(--navy);line-height:1;}
.kpi-n.txt{font-size:1.9rem;text-transform:capitalize;}
.kpi-i{width:42px;height:42px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:1.3rem;color:#fff;}
.kpi-i.coral{background:var(--coral);}.kpi-i.mint{background:var(--mint);color:#1f4d27;}.kpi-i.navy{background:var(--navy);}
.kpi-d{padding:.1rem .9rem .8rem;font-size:.8rem;color:var(--muted);}

/* Gráficos HTML/CSS */
.cl-panel{background:#fff;border-radius:14px;padding:1rem 1.2rem;box-shadow:0 1px 3px rgba(37,39,51,.08);height:100%;}
.cl-panel.green{background:var(--mint);}
.cl-panel h4{margin:0 0 .8rem;font-size:1.2rem;}
.cl-donut-wrap{display:flex;align-items:center;gap:1.4rem;flex-wrap:wrap;}
.cl-donut{width:150px;height:150px;border-radius:50%;display:flex;align-items:center;justify-content:center;flex:none;}
.cl-donut div{width:96px;height:96px;border-radius:50%;background:#fff;display:flex;flex-direction:column;align-items:center;justify-content:center;font-family:'Barlow Condensed',sans-serif;font-size:1.9rem;font-weight:700;color:var(--navy);line-height:1;}
.cl-donut small{font-family:'Inter',sans-serif;font-size:.65rem;font-weight:500;color:var(--muted);margin-top:.2rem;}
.cl-leg{list-style:none;margin:0;padding:0;font-size:.88rem;}
.cl-leg li{display:flex;align-items:center;gap:.5rem;padding:.2rem 0;}
.cl-dot{width:11px;height:11px;border-radius:50%;display:inline-block;}
.cl-bars{display:flex;align-items:flex-end;gap:.9rem;height:170px;padding-top:.5rem;}
.cl-bar{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:flex-end;height:100%;min-width:0;}
.cl-bar i{display:block;width:100%;max-width:46px;background:var(--navy);border-radius:6px 6px 0 0;}
.cl-bar b{font-size:.85rem;color:var(--navy);margin-bottom:.2rem;}
.cl-bar span{font-size:.72rem;color:#1c3b24;margin-top:.35rem;text-align:center;word-break:break-word;}
.cl-empty{color:var(--muted);font-size:.9rem;padding:1.2rem 0;}
.cl-panel.green .cl-empty{color:#1c3b24;}
.cl-tags{margin-top:.8rem;}
</style>
"""

_PALETA_DONUT = {"procesadas": "#9BE19D", "descartadas": "#F98B72", "fallidas": "#252733"}


def _esc(valor) -> str:
    return html.escape(str(valor if valor is not None else ""))


def _cargar_logo_html() -> str:
    """Logo del repo (docs/assets/logo) embebido; si no existe, usa texto."""
    base = os.path.dirname(os.path.abspath(__file__))
    for ruta in (
        os.path.join(base, "..", "docs", "assets", "logo", "logo-b-matraz.svg"),
        os.path.join(base, "assets", "logo-b-matraz.svg"),
    ):
        try:
            with open(ruta, "rb") as f:
                datos = base64.b64encode(f.read()).decode("ascii")
            return f'<img alt="CommunityLab" src="data:image/svg+xml;base64,{datos}">'
        except OSError:
            continue
    return '<div class="cl-brandtxt">Community<span>Lab</span></div>'


def _kpi(etiqueta: str, valor, icono: str, color: str, detalle: str, texto: bool = False) -> str:
    clase = "kpi-n txt" if texto else "kpi-n"
    return (
        f'<div class="kpi"><div class="kpi-h">{_esc(etiqueta)}</div>'
        f'<div class="kpi-b"><div class="{clase}">{_esc(valor)}</div>'
        f'<div class="kpi-i {color}">{_esc(icono)}</div></div>'
        f'<div class="kpi-d">{_esc(detalle)}</div></div>'
    )


def _icono_sentimiento(valor: str) -> tuple:
    clave = str(valor or "").strip().lower()
    return {
        "positivo": ("+", "mint"),
        "negativo": ("−", "coral"),
        "neutral": ("=", "navy"),
        "mixto": ("~", "navy"),
    }.get(clave, ("?", "navy"))


def _numero(valor) -> int:
    try:
        return int(valor)
    except (TypeError, ValueError):
        return 0


def _info_oci(resp: dict) -> dict:
    """OCI a nivel raíz o anidado en activos_distribucion_generados (DEC-14)."""
    activos = resp.get("activos_distribucion_generados") or {}
    info = resp.get("almacenamiento_oci") or activos.get("almacenamiento_oci") or {}
    return info if isinstance(info, dict) else {}


def _estado_oci(oci: dict) -> tuple:
    """(texto, icono, color, detalle) según el status que informa el backend."""
    status = str(oci.get("status") or "").strip()
    if not status:
        return ("Sin dato", "?", "navy", "el backend no informó almacenamiento")
    mapa = {
        "guardado_con_exito": ("Guardado", "✓", "mint"),
        "simulado": ("Simulado", "~", "navy"),
        "error_subida": ("Error", "!", "coral"),
    }
    texto, icono, color = mapa.get(status, (status, "?", "navy"))
    detalle = str(oci.get("bucket") or "bucket no informado")
    if status == "error_subida":
        detalle = "subida fallida · " + detalle
    return (texto, icono, color, detalle)


def _metricas_resultado(resp: dict, enviadas: int) -> dict:
    """Extrae solo cifras que informa el backend; no inventa valores."""
    resumen = resp.get("resumen_comunidad") or {}
    descartadas = resumen.get("total_descartadas")
    if descartadas is None:
        descartadas = resp.get("total_descartadas", 0)
    return {
        "procesadas": _numero(resumen.get("total_interacciones_procesadas")),
        "descartadas": _numero(descartadas),
        "fallidas": len(resp.get("interacciones_fallidas") or []),
        "sentimiento": _etiquetar_sentimiento(resumen.get("sentimiento_predominante")) if resumen else "N/A",
        "temas": resumen.get("temas_principales") or [],
        "enviadas": enviadas,
        "oci": _info_oci(resp),
    }


def _html_kpis(metricas: dict | None) -> str:
    """Fila de 4 KPIs: sentimiento, procesadas, descartadas/fallidas y estado OCI."""
    if metricas is None:
        tarjetas = [
            _kpi("Sentimiento", "—", "~", "navy", "Aún sin resultados", texto=True),
            _kpi("Procesadas", "—", "✓", "mint", "Aún sin resultados"),
            _kpi("Descartadas / Fallidas", "—", "×", "coral", "Aún sin resultados"),
            _kpi("Estado OCI", "—", "?", "navy", "Aún sin resultados", texto=True),
        ]
    else:
        icono, color = _icono_sentimiento(metricas["sentimiento"])
        oci_txt, oci_icono, oci_color, oci_detalle = _estado_oci(metricas["oci"])
        rechazadas = metricas["descartadas"] + metricas["fallidas"]
        tarjetas = [
            _kpi("Sentimiento", metricas["sentimiento"], icono, color, "predominante en el lote", texto=True),
            _kpi("Procesadas", metricas["procesadas"], "✓", "mint", f"de {metricas['enviadas']} enviadas"),
            _kpi("Descartadas / Fallidas", rechazadas, "×", "coral",
                 f"{metricas['descartadas']} descartadas · {metricas['fallidas']} fallidas"),
            _kpi("Estado OCI", oci_txt, oci_icono, oci_color, oci_detalle, texto=True),
        ]
    return '<div class="cl-kpis">' + "".join(tarjetas) + "</div>"


def _html_donut(metricas: dict | None) -> str:
    if metricas is None:
        return '<div class="cl-panel"><h4>Resultado del lote</h4><div class="cl-empty">Procese un lote para ver la distribución.</div></div>'
    partes = [(k, metricas[k]) for k in ("procesadas", "descartadas", "fallidas")]
    total = sum(v for _, v in partes)
    if total <= 0:
        fondo = "#e5e7eb"
    else:
        acumulado, tramos = 0.0, []
        for clave, valor in partes:
            if valor <= 0:
                continue
            fin = acumulado + valor * 100.0 / total
            tramos.append(f"{_PALETA_DONUT[clave]} {acumulado:.2f}% {fin:.2f}%")
            acumulado = fin
        fondo = "conic-gradient(" + ", ".join(tramos) + ")"
    leyenda = "".join(
        f'<li><span class="cl-dot" style="background:{_PALETA_DONUT[k]}"></span>{k.capitalize()}: <b>{v}</b></li>'
        for k, v in partes
    )
    return (
        '<div class="cl-panel"><h4>Resultado del lote</h4><div class="cl-donut-wrap">'
        f'<div class="cl-donut" style="background:{fondo}"><div>{total}<small>interacciones</small></div></div>'
        f'<ul class="cl-leg">{leyenda}</ul></div></div>'
    )


def _html_barras_canal(interacciones: list) -> str:
    conteo: dict = {}
    for item in interacciones or []:
        canal = item.get("canal") or "General"
        conteo[canal] = conteo.get(canal, 0) + 1
    if not conteo:
        return '<div class="cl-panel green"><h4>Mensajes por canal</h4><div class="cl-empty">Cargue interacciones para ver su distribución.</div></div>'
    top = sorted(conteo.items(), key=lambda par: (-par[1], par[0]))[:6]
    maximo = max(v for _, v in top)
    barras = "".join(
        f'<div class="cl-bar"><b>{v}</b><i style="height:{max(8, int(v * 120 / maximo))}px"></i><span>{_esc(c)}</span></div>'
        for c, v in top
    )
    return f'<div class="cl-panel green"><h4>Mensajes por canal</h4><div class="cl-bars">{barras}</div></div>'


def _html_chips(valores: list, color: str = "grey") -> str:
    return "".join(f'<span class="cl-chip {color}">{_esc(v)}</span>' for v in valores if v)



# ---------------------------------------------------------------------------
# Procesamiento (única llamada HTTP del frontend)
# ---------------------------------------------------------------------------

def _registrar_mensaje(nivel: str, texto: str) -> None:
    """Guarda el aviso del último intento para mostrarlo tras el rerun."""
    st.session_state[CLAVE_MENSAJE] = (nivel, texto)


def _procesar(payload: dict, modo_demo: bool, escenario_demo, url_backend: str):
    """Obtiene la respuesta del backend (o simulada en modo demo); None si falla.

    Los errores se registran en session_state (no se pierden con el rerun).
    """
    if modo_demo:
        with st.spinner("Cargando respuesta simulada..."):
            resp = _cargar_respuesta_demo(escenario_demo)
        if resp is None:
            _registrar_mensaje(
                "error",
                "No se pudo cargar la respuesta simulada. Verifique que existe demo_respuesta_simulada.json",
            )
        return resp

    with st.spinner("Procesando interacciones con el motor de IA, esto puede tardar unos segundos..."):
        try:
            respuesta = requests.post(
                url_backend,
                json=payload,
                timeout=(TIMEOUT_CONEXION_SEGUNDOS, TIMEOUT_RESPUESTA_SEGUNDOS),
            )
        except requests.exceptions.Timeout:
            _registrar_mensaje("error", "La solicitud tardó demasiado en responder. Intente nuevamente.")
            return None
        except requests.exceptions.ConnectionError:
            _registrar_mensaje("error", "No fue posible conectarse con el backend. Verifique que el servicio esté disponible.")
            return None
        except requests.exceptions.RequestException:
            _registrar_mensaje("error", "Ocurrió un error al comunicarse con el backend. Intente nuevamente.")
            return None
    if not respuesta.ok:
        _registrar_mensaje("error", _generar_mensaje_error_backend(respuesta.status_code, respuesta))
        return None
    try:
        return respuesta.json()
    except Exception:
        _registrar_mensaje("error", "La respuesta del backend no es JSON válido")
        return None


# ---------------------------------------------------------------------------
# Callbacks de la interfaz (se ejecutan antes del rerun)
# ---------------------------------------------------------------------------

def _iniciar_proceso() -> None:
    """Anti-spam: marca el proceso en curso para renderizar el botón deshabilitado."""
    st.session_state[CLAVE_PROCESANDO] = True
    st.session_state.pop(CLAVE_MENSAJE, None)


def _vaciar_campo() -> None:
    """Limpia el JSON pegado y el archivo subido."""
    st.session_state[CLAVE_JSON] = ""
    st.session_state[CLAVE_UPLOADER] = st.session_state.get(CLAVE_UPLOADER, 0) + 1


def _cargar_ejemplo() -> None:
    """Carga datos de ejemplo ficticios en el campo JSON."""
    st.session_state[CLAVE_MODO] = "Pegar JSON"
    st.session_state[CLAVE_JSON] = json.dumps({"interacciones": DATOS_EJEMPLO}, ensure_ascii=False, indent=2)


def _alternar(clave_estado: str, llave: str) -> None:
    estado = st.session_state.setdefault(clave_estado, {})
    estado[llave] = not estado.get(llave, False)


def _decidir(llave: str, valor: str) -> None:
    """Registra la decisión de revisión (aprobado / rechazado) del activo."""
    st.session_state.setdefault(CLAVE_FEEDBACK, {})[llave] = valor


def _guardar_edicion(llave: str, clave_widget: str) -> None:
    st.session_state.setdefault(CLAVE_TEXTO_EDITADO, {})[llave] = st.session_state.get(clave_widget, "")
    st.session_state.setdefault(CLAVE_EDICION, {})[llave] = False


# ---------------------------------------------------------------------------
# Revisión de activos: feedback, edición y descarga (estado solo de la sesión)
# ---------------------------------------------------------------------------

def _texto_activo(tipo: str, activo: dict) -> str:
    """Texto revisable del activo. La FAQ se presenta como 'Q: ... / A: ...'."""
    if tipo == "linkedin":
        partes = [activo.get("titulo"), activo.get("copy")]
        return "\n\n".join(str(p) for p in partes if p)
    if tipo == "newsletter":
        partes = [activo.get("titular"), activo.get("resumen")]
        return "\n\n".join(str(p) for p in partes if p)
    lineas = []
    if activo.get("pregunta"):
        lineas.append(f"Q: {activo.get('pregunta')}")
    if activo.get("respuesta"):
        lineas.append(f"A: {activo.get('respuesta')}")
    return "\n".join(lineas)


def _metadatos_activo(tipo: str, activo: dict) -> list:
    if tipo == "linkedin":
        return [activo.get("canal_recomendado"), activo.get("potencial_engagement")]
    if tipo == "newsletter":
        return [activo.get("seccion")]
    return [activo.get("tema"), activo.get("origen"), activo.get("status")]


def _tarjeta_activo(lote: str, clave: str, titulo: str, tipo: str, activo) -> None:
    llave = f"{lote}:{clave}"
    clave_txt = f"cl_txt_{lote}_{clave}"
    editando = bool(st.session_state.get(CLAVE_EDICION, {}).get(llave, False))
    decision = st.session_state.get(CLAVE_FEEDBACK, {}).get(llave, "pendiente")
    if editando:
        etiqueta, color = "Editando", "coral"
    elif decision == "aprobado":
        etiqueta, color = "Aprobado", "mint"
    elif decision == "rechazado":
        etiqueta, color = "Rechazado", "coral"
    else:
        etiqueta, color = "En revisión", "grey"

    with st.container(border=True, key=f"card_{clave}"):
        original = _texto_activo(tipo, activo) if activo else ""
        cab_titulo, cab_editar = st.columns([5, 1])
        cab_titulo.markdown(
            f'<div class="cl-card-h"><span class="cl-card-t">{_esc(titulo)}</span>'
            f'<span class="cl-chip {color}">{etiqueta}</span></div>',
            unsafe_allow_html=True,
        )
        if original:
            if editando:
                cab_editar.button("💾", key=f"cl_edit_{lote}_{clave}", help="Guardar edición",
                                  on_click=_guardar_edicion, args=(llave, clave_txt))
            else:
                cab_editar.button("✏️", key=f"cl_edit_{lote}_{clave}", help="Editar texto",
                                  on_click=_alternar, args=(CLAVE_EDICION, llave))
        if not activo:
            st.caption("Sin activo generado por el motor.")
            return
        if tipo == "faq":
            st.caption("💡 Tip de la Semana")
        meta = _html_chips(_metadatos_activo(tipo, activo))
        if meta:
            st.markdown(f'<div class="cl-meta">{meta}</div>', unsafe_allow_html=True)
        if not original:
            st.caption("El activo no incluye texto para revisar.")
            return

        # El texto vive en el estado del widget; se restaura desde texto_editado si se perdió.
        st.session_state.setdefault(
            clave_txt, st.session_state.get(CLAVE_TEXTO_EDITADO, {}).get(llave, original)
        )
        texto = st.text_area(
            f"Texto de {titulo}", key=clave_txt, height=190,
            disabled=not editando, label_visibility="collapsed",
        )
        if texto != original:
            st.caption("Texto editado respecto al original del motor.")

        c1, c2, c3 = st.columns(3)
        c1.button("Aprobar", key=f"cl_ok_{lote}_{clave}", type="primary",
                  on_click=_decidir, args=(llave, "aprobado"))
        c2.button("Rechazar", key=f"cl_no_{lote}_{clave}",
                  on_click=_decidir, args=(llave, "rechazado"))
        c3.download_button("Descargar", data=texto, file_name=f"{clave}_{lote}.txt",
                           key=f"cl_dl_{lote}_{clave}", disabled=decision != "aprobado")


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------

st.set_page_config(page_title="CommunityLab", layout="wide", initial_sidebar_state="expanded")
st.markdown(CSS_TEMA, unsafe_allow_html=True)

# Modo demo local - solo activado explícitamente via variable de entorno
modo_demo = os.environ.get(MODO_DEMO_VAR, "").lower() in ("1", "true", "yes", "on")
url_backend = _obtener_url_backend()

resultado = st.session_state.get(CLAVE_RESULTADO)
resp_guardada = resultado["resp"] if resultado else None
lote_actual = str((resp_guardada or {}).get("lote_id") or "sin_lote")

# ---- Barra lateral: escenario demo, datos del lote y monitoreo cloud ----
escenario_demo = None
with st.sidebar:
    st.markdown('<div class="cl-side-brand">Community<span>Lab</span></div>', unsafe_allow_html=True)
    if modo_demo:
        with open(os.path.join(os.path.dirname(__file__), "demo_scenarios", "manifest.json"), encoding="utf-8") as manifest_file:
            escenarios_demo = json.load(manifest_file)
        st.markdown('<div class="cl-side-h">Escenario</div>', unsafe_allow_html=True)
        escenario_demo = st.selectbox("Escenario simulado", list(escenarios_demo), format_func=lambda key: escenarios_demo[key])
        st.caption("Respuesta fija de prueba: no depende de los mensajes cargados.")
        st.markdown(
            '<div class="cl-demo-flag">⚠️ MODO DEMO ACTIVO - Datos simulados, sin llamada al backend</div>',
            unsafe_allow_html=True,
        )
    st.markdown('<div class="cl-side-h">Lote</div>', unsafe_allow_html=True)
    origen = st.text_input("Origen comunidad", "Discord_Grupo_ONE_G10")
    periodo = st.text_input("Periodo", "Semana_01")

    st.markdown('<div class="cl-side-h">Sistema</div>', unsafe_allow_html=True)
    oci_actual = _info_oci(resp_guardada) if resp_guardada else {}
    oci_txt = _estado_oci(oci_actual)[0] if oci_actual else "Sin ejecución"
    filas = [("Modo", "Demo (simulado)" if modo_demo else "En vivo")]
    if not modo_demo:
        filas.append(("Backend", url_backend))
    filas += [
        ("Bucket OCI", str(oci_actual.get("bucket") or "—")),
        ("Estado OCI", oci_txt),
        ("Límite por lote", f"{MAX_INTERACCIONES} interacciones"),
        ("Tamaño máx. archivo", "1 MB"),
    ]
    st.markdown(
        "".join(f'<div class="cl-status"><span>{_esc(a)}</span><b>{_esc(b)}</b></div>' for a, b in filas),
        unsafe_allow_html=True,
    )

# ---- Barra superior ----
chips_top = '<span class="cl-chip coral">Modo demo</span>' if modo_demo else '<span class="cl-chip mint">En vivo</span>'
if resp_guardada:
    chips_top += f'<span class="cl-chip navy">Lote {_esc(lote_actual)}</span>'
st.markdown(
    f'<div class="cl-top">{_cargar_logo_html()}'
    f'<div class="cl-crumb">Panel · Del chat de la comunidad a contenido listo para revisar</div>'
    f'<div>{chips_top}</div></div>',
    unsafe_allow_html=True,
)

# ---- Ingesta ----
interacciones = None
avisos: list = []
procesando = bool(st.session_state.get(CLAVE_PROCESANDO, False))

with st.container(border=True, key="card_carga"):
    st.markdown("### Cargar interacciones")
    with st.container():
        modo = st.radio("¿Cómo desea cargarlas?", ["Subir archivo", "Pegar JSON"], horizontal=True, key=CLAVE_MODO)

        if modo == "Subir archivo":
            archivo = st.file_uploader(
                "Archivo CSV o JSON", type=["csv", "json"],
                key=f"cl_archivo_{st.session_state.get(CLAVE_UPLOADER, 0)}",
            )
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
            texto = st.text_area("Pegue el JSON aquí", height=200, key=CLAVE_JSON)
            if texto.strip():
                interacciones, avisos = _interacciones_desde_json_text(texto)

    for aviso in avisos:
        st.warning(aviso)

    interacciones_a_enviar, interacciones_ignoradas = _aplicar_limite_interacciones(interacciones or [])
    if interacciones_ignoradas > 0:
        st.warning(
            f"El backend acepta un máximo de {MAX_INTERACCIONES} interacciones por lote. "
            f"Se ignoraron {interacciones_ignoradas} interacciones adicionales."
        )

    if modo_demo:
        st.caption("Modo demo: usando respuesta simulada (sin llamada HTTP)")
    else:
        st.caption(f"Enviando a: {url_backend}")

    b1, b2, b3 = st.columns(3)
    b1.button("🚀 Procesar Lote", type="primary", disabled=procesando, on_click=_iniciar_proceso)
    b2.button("🧹 Vaciar Campo", disabled=procesando, on_click=_vaciar_campo)
    b3.button("📋 Cargar ejemplo", disabled=procesando, on_click=_cargar_ejemplo)

    mensaje = st.session_state.get(CLAVE_MENSAJE)
    if mensaje:
        getattr(st, mensaje[0])(mensaje[1])

# ---- Procesamiento (se ejecuta en el rerun disparado por el botón) ----
if procesando:
    try:
        if not interacciones_a_enviar:
            _registrar_mensaje("warning", "Debe cargar datos antes de procesar")
        else:
            payload = _construir_payload(origen, periodo, interacciones_a_enviar)
            resp = _procesar(payload, modo_demo, escenario_demo, url_backend)
            # Limpieza atómica: el resultado previo solo se reemplaza si llegó una respuesta válida.
            if resp:
                st.session_state[CLAVE_RESULTADO] = {
                    "resp": resp,
                    "enviadas": len(interacciones_a_enviar),
                    "items": list(interacciones_a_enviar),
                }
    finally:
        # Siempre rehabilita los botones, aun si algo falló arriba.
        st.session_state[CLAVE_PROCESANDO] = False
    st.rerun()

metricas = _metricas_resultado(resp_guardada, resultado["enviadas"]) if resp_guardada else None
items_enviados = resultado["items"] if resultado else []

st.markdown(_html_kpis(metricas), unsafe_allow_html=True)

tab_panel, tab_datos, tab_json = st.tabs(["Panel de resultados", "Datos cargados", "Respuesta y solicitud"])

with tab_panel:
    if not resp_guardada:
        st.info("Cargue interacciones y pulse Procesar Lote para ver aquí el análisis y los activos generados.")
    else:
        estado = str(resp_guardada.get("status") or "")
        if estado == "exito":
            st.success("Análisis procesado exitosamente.")
        elif estado == "parcial":
            st.warning("Resultado parcial: algunas interacciones no pudieron procesarse.")
        elif estado == "error":
            st.error("El análisis terminó con errores.")

        graf1, graf2 = st.columns([1, 1])
        with graf1:
            st.markdown(_html_donut(metricas), unsafe_allow_html=True)
        with graf2:
            st.markdown(_html_barras_canal(items_enviados), unsafe_allow_html=True)

        resumen = resp_guardada.get("resumen_comunidad")
        if resumen:
            st.markdown(f"**Temas principales:** {_formato_temas(metricas['temas'])}")
            if metricas["descartadas"]:
                st.caption(f"Interacciones descartadas: {metricas['descartadas']}")
        else:
            st.info("La respuesta no incluye un resumen de comunidad.")

        activos = resp_guardada.get("activos_distribucion_generados") or {}
        if activos:
            st.markdown("### Activos para revisar")
            st.caption("La aprobación y las ediciones viven solo en esta sesión; no se envían al backend.")
            tarjetas = [
                ("Publicación LinkedIn", "linkedin", "post_linkedin"),
                ("Destacado Newsletter", "newsletter", "destaque_newsletter_semanal"),
                ("Sugerencia FAQ", "faq", "sugerencia_contenido_faq"),
            ]
            for columna, (titulo, tipo, campo) in zip(st.columns(3), tarjetas):
                with columna:
                    _tarjeta_activo(lote_actual, tipo, titulo, tipo, activos.get(campo))
        else:
            st.info("La respuesta no incluye activos de distribución.")

        almacenamiento = _info_oci(resp_guardada)
        if almacenamiento:
            _mostrar_almacenamiento_oci(almacenamiento)

        _mostrar_interacciones_fallidas(resp_guardada)

with tab_datos:
    if interacciones:
        st.write(f"Se cargaron {len(interacciones)} interacciones")
        columna_a, columna_b = st.columns([3, 2])
        with columna_a:
            st.dataframe(pd.DataFrame(interacciones))
        with columna_b:
            st.markdown(_html_barras_canal(interacciones_a_enviar), unsafe_allow_html=True)
    else:
        st.info("Todavía no hay interacciones cargadas.")

with tab_json:
    if resp_guardada:
        with st.expander("Respuesta simulada" if modo_demo else "Respuesta completa del backend"):
            try:
                st.json(resp_guardada)
            except Exception:
                st.text("La respuesta del backend no es JSON válida")
    with st.expander("Solicitud preparada (sin envío)" if modo_demo else "Ver la solicitud preparada"):
        st.json({
            "origen_comunidad": origen.strip(),
            "periodo_referencia": periodo.strip(),
            "interacciones": interacciones_a_enviar or [],
        })

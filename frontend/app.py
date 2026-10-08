import streamlit as st
import requests
import json
import pandas as pd

st.set_page_config(page_title="CommunityLab", layout="wide")
st.title("CommunityLab - Panel MVP")

# Constantes
MAX_INTERACCIONES = 10

url_backend = "http://localhost:8080/api/v1/community/process"

st.markdown("### Cargar interacciones")

modo = st.radio("¿Cómo desea cargarlas?", ["Subir archivo", "Pegar JSON"])

interacciones = None
origen = st.text_input("Origen comunidad", "Discord_Grupo_ONE_G10")
periodo = st.text_input("Periodo", "Semana_01")

if modo == "Subir archivo":
    archivo = st.file_uploader("Archivo CSV o JSON", type=["csv", "json"])
    if archivo:
        if archivo.name.endswith(".json"):
            try:
                data = json.load(archivo)
                if isinstance(data, list):
                    interacciones = data
                elif isinstance(data, dict):
                    for key in ["interacciones", "data", "items", "mensajes"]:
                        if key in data and isinstance(data[key], list):
                            interacciones = data[key]
                            break
                    if interacciones is None:
                        interacciones = [data] if data else []
                else:
                    interacciones = []
            except (json.JSONDecodeError, ValueError):
                st.error("El archivo JSON no es válido")
                interacciones = None
        else:
            try:
                df = pd.read_csv(archivo)
                # Reemplazar NaN por cadenas vacías
                df = df.fillna("")
                interacciones = df.to_dict(orient="records")
            except Exception as e:
                st.error(f"Error al leer CSV: {e}")
                interacciones = None

        if interacciones:
            st.write(f"Se cargaron {len(interacciones)} interacciones")
            st.dataframe(pd.DataFrame(interacciones))
else:
    texto = st.text_area("Pegue el JSON aquí", height=200)
    if texto:
        try:
            data = json.loads(texto)
            if isinstance(data, list):
                interacciones = data
            else:
                # Intentar claves comunes
                if isinstance(data, dict):
                    for key in ["interacciones", "data", "items", "mensajes"]:
                        if key in data and isinstance(data[key], list):
                            interacciones = data[key]
                            break
                    if interacciones is None:
                        # Si es un dict, tal vez sea un solo elemento
                        interacciones = [data] if data else []
                else:
                    interacciones = []
        except (json.JSONDecodeError, ValueError):
            st.error("El JSON proporcionado no es válido. Revise el formato e intente nuevamente.")
            interacciones = None

st.markdown("### Enviar al backend")
st.caption(f"Enviando a: {url_backend}")

if st.button("Procesar"):
    if not interacciones:
        st.warning("Debe cargar datos antes de procesar")
    else:
        payload = {
            "origen_comunidad": origen,
            "periodo_referencia": periodo,
            "interacciones": interacciones
        }

        # Validar límite de interacciones antes de enviar
        if len(interacciones) > MAX_INTERACCIONES:
            st.error(f"El backend acepta máximo {MAX_INTERACCIONES} interacciones por lote. Por favor, reduzca el número de interacciones.")
        else:
            try:
                r = requests.post(url_backend, json=payload, timeout=(10, 90))
                st.write("Código de estado:", r.status_code)
                if not r.ok:
                    try:
                        error_data = r.json()
                        st.error(f"Error {r.status_code}: {error_data.get('mensaje') or error_data.get('error') or 'Error en la solicitud'}")
                    except Exception:
                        st.error(f"Error {r.status_code}: {r.text}")
                else:
                    st.markdown("### Resultados del análisis")
                    try:
                        resp = r.json()
                    except json.JSONDecodeError:
                        st.error("La respuesta del backend no es JSON válido")
                        st.text(r.text)
                        resp = None

                    if resp:
                        # Mostrar resumen de comunidad si existe
                        summary = resp.get("resumen_comunidad")
                        if summary:
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("Sentimiento predominante", summary.get("sentimiento_predominante", "N/A"))
                            with col2:
                                st.metric("Total interacciones procesadas", summary.get("total_interacciones_procesadas", "N/A"))
                            if summary.get("temas_principales"):
                                st.write("**Temas principales:**", ", ".join(summary.get("temas_principales")))

                        # Mostrar activos de distribución si existen
                        assets = resp.get("activos_distribucion_generados")
                        if assets:
                            with st.expander("Activos de distribución generados"):
                                st.json(assets)

                        st.info("Nota: El 'relevance score' por mensaje está pendiente de integración con el backend/ML (persistencia de interacciones_analizadas).")

                    with st.expander("Respuesta completa del backend"):
                        try:
                            st.json(resp if resp is not None else r.json())
                        except ValueError:
                            st.text(r.text)
            except requests.exceptions.Timeout:
                st.error("La solicitud tardó demasiado en responder. Intente nuevamente.")
            except requests.exceptions.ConnectionError:
                st.error("No fue posible conectarse con el backend. Verifique que el servicio esté disponible.")
            except Exception as e:
                st.error(f"Ocurrió un error al procesar la solicitud: {e}")

with st.expander("Ver el payload enviado"):
    st.json({
        "origen_comunidad": origen,
        "periodo_referencia": periodo,
        "interacciones": interacciones or []
    })

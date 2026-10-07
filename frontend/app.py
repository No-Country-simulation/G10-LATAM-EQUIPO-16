import streamlit as st
import requests
import json
import pandas as pd

st.set_page_config(page_title="CommunityLab", layout="wide")
st.title("CommunityLab - Panel MVP")

url_backend = "http://localhost:8080/api/v1/community/process"

st.markdown("### Cargar interacciones")

modo = st.radio("Como quieres cargarlas?", ["Subir archivo", "Pegar JSON"])

interacciones = None
origen = st.text_input("Origen comunidad", "Discord_Grupo_ONE_G10")
periodo = st.text_input("Periodo", "Semana_01")

if modo == "Subir archivo":
    archivo = st.file_uploader("CSV o JSON", type=["csv", "json"])
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
                # Replace NaN with None/empty strings
                df = df.fillna("")
                interacciones = df.to_dict(orient="records")
            except Exception as e:
                st.error(f"Error al leer CSV: {e}")
                interacciones = None

        if interacciones:
            st.write(f"cargadas {len(interacciones)} interacciones")
            st.dataframe(pd.DataFrame(interacciones))
else:
    texto = st.text_area("Pega el JSON aqui", height=200)
    if texto:
        try:
            data = json.loads(texto)
            if isinstance(data, list):
                interacciones = data
            else:
                # Try common keys
                if isinstance(data, dict):
                    for key in ["interacciones", "data", "items", "mensajes"]:
                        if key in data and isinstance(data[key], list):
                            interacciones = data[key]
                            break
                    if interacciones is None:
                        # If it's a dict, maybe it's a single item
                        interacciones = [data] if data else []
                else:
                    interacciones = []
        except (json.JSONDecodeError, ValueError):
            st.error("ese json no sirve, revisalo")
            interacciones = None

st.markdown("### Mandar al backend")
st.caption(f"pegándole a: {url_backend}")

if st.button("Procesar"):
    if not interacciones:
        st.warning("falta cargar algo primero")
    else:
        payload = {
            "origen_comunidad": origen,
            "periodo_referencia": periodo,
            "interacciones": interacciones
        }

        # Validar límite de 10 interacciones antes de enviar
        if len(interacciones) > 10:
            st.error("El backend acepta máximo 10 interacciones por lote. Por favor, reduce el número de interacciones.")
        else:
            try:
                r = requests.post(url_backend, json=payload, timeout=(10, 90))
                st.write("status:", r.status_code)
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
                        st.error("Respuesta del backend no es JSON válido")
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
                        except:
                            st.text(r.text)
            except requests.exceptions.ConnectionError:
                st.error("no conecta al backend, seguro no esta corriendo en local")
            except Exception as e:
                st.error(f"algo se rompió: {e}")

with st.expander("ver el payload que se manda"):
    st.json({
        "origen_comunidad": origen,
        "periodo_referencia": periodo,
        "interacciones": interacciones or []
    })

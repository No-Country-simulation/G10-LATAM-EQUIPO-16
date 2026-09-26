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
            data = json.load(archivo)
            if isinstance(data, list):
                interacciones = data
            else:
                interacciones = data.get("interacciones", [])
        else:
            df = pd.read_csv(archivo)
            interacciones = df.to_dict(orient="records")

        st.write(f"cargadas {len(interacciones)} interacciones")
        st.dataframe(pd.DataFrame(interacciones))
else:
    texto = st.text_area("Pega el JSON aqui", height=200)
    if texto:
        try:
            interacciones = json.loads(texto)
        except:
            st.error("ese json no sirve, revisalo")

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

        try:
            r = requests.post(url_backend, json=payload, timeout=15)
            st.write("status:", r.status_code)
            st.markdown("### esto devolvió el backend")
            try:
                st.json(r.json())
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

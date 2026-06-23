import streamlit as st
import pandas as pd
import requests
import os

st.set_page_config(page_title="Plataforma de Combustibles", layout="wide")

# Truco Profesional: Usa localhost por defecto para pruebas locales, 
# pero permite inyectar el nombre del contenedor en Docker.
API_URL = os.getenv("API_URL", "http://localhost:8000")

st.title("⛽ Análisis de Dispensación y Precios")

st.sidebar.header("Perfil de Usuario")
audiencia = st.sidebar.radio("Vista:", ["Ejecutiva (Estratégica)", "Operativa (Técnica)"])

def fetch_data(endpoint):
    try:
        res = requests.get(f"{API_URL}{endpoint}")
        # Si la API responde con error (ej. falta correr el ETL), lo mostramos
        if "error" in res.json():
            st.warning(f"Aviso de la API: {res.json()['error']}")
            return None
        return res.json()
    except Exception as e:
        # Si la API está apagada, mostramos un error rojo en lugar de una pantalla vacía
        st.error(f"Falla de conexión con el Backend en {API_URL}. Verifica que la API esté encendida.")
        return None

if audiencia == "Ejecutiva (Estratégica)":
    st.markdown("### 📈 Resumen Financiero y de Mercado")
    st.info("Métricas clave para la toma de decisiones gerenciales.")
    
    precios = fetch_data("/api/precios-nacionales")
    if precios and "promedios" in precios:
        c1, c2, c3 = st.columns(3)
        c1.metric("Promedio Nacional 93", f"${precios['promedios'].get('precio_93', 0)}")
        c2.metric("Promedio Nacional 95", f"${precios['promedios'].get('precio_95', 0)}")
        c3.metric("Promedio Diésel", f"${precios['promedios'].get('diesel', 0)}")
    
    st.divider()
    st.markdown("#### Volumen de Ventas por Industria")
    data_ind = fetch_data("/api/consumo-industria")
    if data_ind:
        df_ind = pd.DataFrame(data_ind)
        if not df_ind.empty:
            st.bar_chart(df_ind.set_index("industria")["cantidad"], color="#1f77b4")

else:
    st.markdown("### ⚙️ Telemetría y Desglose Operativo")
    st.info("Registro tabular y distribución volumétrica para mantención de equipos.")
    
    data_hist = fetch_data("/api/historico-combustibles")
    if data_hist:
        df_hist = pd.DataFrame(data_hist)
        if not df_hist.empty:
            col1, col2 = st.columns([1, 2])
            with col1:
                st.markdown("#### Registro Tabular")
                st.dataframe(df_hist, use_container_width=True)
            with col2:
                st.markdown("#### Dispensación por Producto")
                st.bar_chart(df_hist.set_index("nombre_prod")["cantidad"], color="#ff7f0e")
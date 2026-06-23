from fastapi import FastAPI
import pandas as pd
import os

app = FastAPI(title="API Data Pipeline Bencinera - CNE")

@app.get("/")
def index():
    return {"estado": "Operativo", "arquitectura": "ETL + FastAPI Dockerizados", "rol": "Backend"}

@app.get("/api/consumo-industria")
def consumo_por_industria():
    path = "data/transacciones_limpias.csv"
    if not os.path.exists(path):
        return {"error": "Ejecuta el ETL primero para generar la data histórica"}

    df = pd.read_csv(path)
    # Agrupamos por los sectores industriales
    resumen = df.groupby('industria')['cantidad'].sum().reset_index()
    return resumen.to_dict(orient="records")

@app.get("/api/historico-combustibles")
def historico_combustibles():
    path = "data/transacciones_limpias.csv"
    if not os.path.exists(path):
        return {"error": "Dataset no disponible"}

    df = pd.read_csv(path)
    # Filtro avanzado para que Vicente grafique el consumo por tipo de producto
    resumen = df.groupby('nombre_prod')['cantidad'].sum().reset_index()
    return resumen.to_dict(orient="records")

@app.get("/api/precios-nacionales")
def precios_promedio():
    path = "data/precios_cne.csv"
    if not os.path.exists(path):
        return {"error": "Telemetría CNE no sincronizada"}

    df = pd.read_csv(path)
    promedios = {}
    for col in ['precio_93', 'precio_95', 'diesel']:
        if col in df.columns:
            # Calculamos el promedio y lo redondeamos a 2 decimales
            promedios[col] = round(float(df[col].mean()), 2)

    return {"unidad": "CLP", "promedios": promedios}

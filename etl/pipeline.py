import os
import logging
import requests
import pandas as pd
import urllib3

# Desactivamos advertencias de certificados SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

class DataPipeline:
    def __init__(self):
        # 1. Variables de entorno para ocultar las credenciales en Docker
        self.email = os.getenv("CNE_USER", "je.urquiaga@duocuc.cl")
        self.password = os.getenv("CNE_PASSWORD", "Joder123#")

        self.url_login = "https://api.cne.cl/api/login"
        # 2. URL actualizada a la versión 4
        self.cne_url = "https://api.cne.cl/api/v4/estaciones"

        # Asegúrate de que este nombre coincida exactamente con tu archivo físico
        self.csv_path = "df_bencinera_final.csv"
        self.token = None

    def obtener_token(self):
        logging.info("Iniciando Handshake con API CNE (POST)...")
        payload = {"email": self.email, "password": self.password}
        try:
            res = requests.post(self.url_login, data=payload, timeout=10, verify=False)
            res.raise_for_status()
            self.token = res.json().get("token")
            if self.token:
                logging.info("Autenticación exitosa. Token capturado en memoria.")
            else:
                logging.error("Login devolvió 200 OK, pero no se halló el token.")
        except Exception as e:
            logging.error(f"Falla en autenticación: {e}")

    def procesar_csv_local(self):
        logging.info("Procesando histórico de transacciones (CSV)...")
        try:
            df = pd.read_csv(self.csv_path)
            cols = ['id_vehiculo', 'industria', 'nombre_prod', 'cantidad', 'fecha']
            # Validación de columnas antes de filtrar
            columnas_presentes = [c for c in cols if c in df.columns]
            df = df[columnas_presentes].dropna(subset=['cantidad'])
            df['cantidad'] = pd.to_numeric(df['cantidad'], errors='coerce')

            os.makedirs("data", exist_ok=True)
            df.to_csv("data/transacciones_limpias.csv", index=False)
            logging.info("Dataset CSV limpio exportado a /data.")
        except Exception as e:
            logging.error(f"Falla al procesar CSV: {e}")

    def procesar_api_cne(self):
        logging.info("Extrayendo telemetría de precios CNE v4 (GET)...")
        df = pd.DataFrame()

        try:
            if not self.token:
                raise ValueError("Sin token. Abortando extracción en vivo.")

            parametros_url = {"token": self.token}
            res = requests.get(self.cne_url, params=parametros_url, timeout=30, verify=False)
            res.raise_for_status()

            if res.text.strip().startswith("<!DOCTYPE html>"):
                raise ValueError("El servidor retornó HTML. Revisa la documentación de la API.")

            data_json = res.json()
            data = data_json.get("data", data_json) if isinstance(data_json, dict) else data_json

            # 3. Aplicación de json_normalize para aplanar las jerarquías
            if data:
                df = pd.json_normalize(data)
                logging.info("API consumida y JSON aplanado exitosamente.")
            else:
                logging.warning("La API de la CNE respondió, pero la lista de datos está vacía.")

        except Exception as e:
            logging.error(f"Error de red/API externa: {e}. Activando Fallback al CSV local...")
            try:
                # 4. Fallback al archivo CSV actualizado
                df = pd.read_csv("df_datos_estaciones_cne_2.csv")
                logging.info("Respaldo local cargado correctamente.")
            except FileNotFoundError:
                logging.critical("CRÍTICO: No se pudo conectar a la API ni cargar el archivo de respaldo.")
                return

        if not df.empty:
            # 5. Mapeo adaptado a la estructura anidada y separada por puntos
            cols_to_rename = {
                'ubicacion.nombre_comuna': 'comuna',
                'precios.93.precio': 'precio_93',
                'precios.95.precio': 'precio_95',
                'precios.petroleo_diesel.precio': 'diesel'
            }

            # Renombramos solo las columnas que existan en el DataFrame aplanado
            df_fil = df.rename(columns={k: v for k, v in cols_to_rename.items() if k in df.columns})

            # Seleccionamos exclusivamente nuestras columnas objetivo
            columnas_finales = [c for c in ['comuna', 'precio_93', 'precio_95', 'diesel'] if c in df_fil.columns]
            df_fil = df_fil[columnas_finales]

            for col in ['precio_93', 'precio_95', 'diesel']:
                if col in df_fil.columns:
                    df_fil[col] = pd.to_numeric(df_fil[col], errors='coerce')

            os.makedirs("data", exist_ok=True)
            df_fil.to_csv("data/precios_cne.csv", index=False)
            logging.info("Precios CNE estructurados y sincronizados en /data.")

    def ejecutar(self):
        self.obtener_token()
        self.procesar_csv_local()
        self.procesar_api_cne()

if __name__ == "__main__":
    DataPipeline().ejecutar()

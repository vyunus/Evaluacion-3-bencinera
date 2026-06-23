import unittest
import pandas as pd
import os

class TestBencineraPipeline(unittest.TestCase):
    def test_existencia_data_limpia(self):
        """Valida que la fase de carga del ETL guardó físicamente el archivo procesado."""
        self.assertTrue(os.path.exists("data/transacciones_limpias.csv"))

    def test_calidad_esquema(self):
        """Verifica que el dataset procesado no contenga cantidades nulas en las transacciones."""
        # Primero revisamos si el archivo existe para evitar que este test falle por herencia
        if os.path.exists("data/transacciones_limpias.csv"):
            df = pd.read_csv("data/transacciones_limpias.csv")
            self.assertEqual(df['cantidad'].isnull().sum(), 0)
        else:
            self.skipTest("El archivo data/transacciones_limpias.csv no existe todavía.")

if __name__ == '__main__':
    unittest.main()

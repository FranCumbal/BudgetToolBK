# sql_connector.py
import pyodbc
import pandas as pd
from .base_connector import BaseConnector
from config import DB_CONFIG  # Importa la configuración de SQL

class SQLConnector(BaseConnector):
    def __init__(self, config=DB_CONFIG):
        self.conn = None
        self.config = config

    def connect(self):
        try:
            self.conn = pyodbc.connect(
                f"DRIVER={{SQL Server}};SERVER={self.config['server']};"
                f"DATABASE={self.config['database']};UID={self.config['username']};PWD={self.config['password']}"
            )
            print("Conectado a SQL Server exitosamente")
        except Exception as e:
            print(f"Error al conectar a SQL Server: {e}")
            self.conn = None

    def fetch_data(self, query):
        if self.conn:
            try:
                return pd.read_sql(query, self.conn)
            except Exception as e:
                print(f"Error al ejecutar la consulta: {e}")
                return pd.DataFrame()
        else:
            print("No hay conexión activa a SQL Server")
            return pd.DataFrame()

# cdf_connector.py
from .base_connector import BaseConnector
import pandas as pd
from cognite.client import CogniteClient, ClientConfig
from cognite.client.credentials import OAuthClientCredentials
from config import COGNITE_CONFIG  # Importa la configuración desde la raíz

class CDFConnector(BaseConnector):
    def __init__(self, config=COGNITE_CONFIG):
        self.client = None
        self.project = config['project']
        self.base_url = config['base_url']
        self.client_id = config['client_id']
        self.client_secret = config['client_secret']
        self.token_url = config['token_url']

    def connect(self):
        """
        Establece la conexión con Cognite Data Fusion.
        """
        try:
            self.client = self.get_cognite_client_shaya()
            print("Conexión a Cognite establecida exitosamente")
        except Exception as e:
            print(f"Error al conectar a Cognite: {e}")
            self.client = None

    def fetch_data(self, query):
        """
        Recupera datos desde Cognite Data Fusion utilizando parámetros:
          - database (por defecto 'jobs_catalogue')
          - table (por defecto 'jobs_catalogue')
          - limit (opcional)
        """
        if self.client:
            try:
                database = query.get('database', 'jobs_catalogue')
                table = query.get('table', 'jobs_catalogue')
                limit = query.get('limit', None)
                df = self.client.raw.rows.retrieve_dataframe(database, table, limit=limit)
                df['Start'] = pd.to_datetime(df['Start'])
                df.reset_index(inplace=True)
                df.rename(columns={'index': 'ID'}, inplace=True)
                return df
            except Exception as e:
                print(f"Error al obtener datos de Cognite: {e}")
                return pd.DataFrame()
        else:
            print("No hay conexión activa a Cognite")
            return pd.DataFrame()

    def get_cognite_client_shaya(self):
        """
        Configura y retorna un cliente de Cognite Data Fusion utilizando la configuración externalizada.
        """
        creds = OAuthClientCredentials(
            token_url=self.token_url,
            client_id=self.client_id,
            client_secret=self.client_secret,
            scopes=["delfi-sauth-cognitedata-api-audience"]
        )
        cnf = ClientConfig(
            client_name="custom-client-name",
            project=self.project,
            credentials=creds,
            base_url=self.base_url,
        )
        client = CogniteClient(cnf)
        return client

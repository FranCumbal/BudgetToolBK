import pandas as pd
import os
from utils.file_manager import get_capex_config_path

class CapexConfigService:
    """
    Servicio para manejar la lógica de carga y guardado de la configuración
    de los meses CAPEX desde y hacia un archivo CSV.
    """
    def __init__(self):
        self.config_path = get_capex_config_path()
        self.months = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]

    def load_config(self) -> dict:
        """
        Carga la configuración desde el archivo CSV.
        Si el archivo no existe, retorna una configuración por defecto con todos los meses en "No".
        """
        if not os.path.exists(self.config_path):
            return {month: "No" for month in self.months}
        
        try:
            df = pd.read_csv(self.config_path)
            # Convertir el DataFrame a un diccionario {Month: Capex}
            return pd.Series(df.Capex.values, index=df.Month).to_dict()
        except Exception:
            # En caso de error o archivo corrupto, devolver el default
            return {month: "No" for month in self.months}

    def save_config(self, config_data: dict):
        """
        Guarda el diccionario de configuración en el archivo CSV.
        """
        df = pd.DataFrame(list(config_data.items()), columns=["Month", "Capex"])
        df.to_csv(self.config_path, index=False)
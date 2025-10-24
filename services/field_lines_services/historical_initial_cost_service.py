import os
import pandas as pd
from datetime import datetime

from utils.file_manager import get_historical_initial_cost_approved_path

class HistoricalInitialCostService:
    """
    Gestiona un registro histórico del costo inicial aprobado, almacenado por año.

    Esta clase se encarga de leer y escribir en un archivo CSV que persiste
    el "Costo Inicial Aprobado" para diferentes años, facilitando su
    consulta y actualización.
    """
    def __init__(self):
        """
        Inicializa el servicio.

        Establece la ruta del archivo, determina el año actual y carga los datos
        existentes o crea un nuevo registro si es necesario.
        """
        self.file_path = get_historical_initial_cost_approved_path()
        self.year = datetime.now().year
        self.df = self._load_or_create()

    def _load_or_create(self):
        """
        Carga los datos desde el archivo CSV o crea un DataFrame por defecto.

        Si el archivo existe, lo lee. Si el año actual no se encuentra en los
        datos cargados, se añade una nueva fila para él. Si el archivo no existe,
        se crea un DataFrame nuevo con una entrada para el año actual.
        """
        if os.path.exists(self.file_path):
            df = pd.read_csv(self.file_path)
            if self.year not in df['Year'].values:
                df = pd.concat([df, pd.DataFrame({"Year": [self.year], "Initial Cost Approved": [0.0]})], ignore_index=True)
        else:
            df = pd.DataFrame({"Year": [self.year], "Initial Cost Approved": [0.0]})
        return df

    def get_year(self):
        """Devuelve el año operativo actual del servicio."""
        return self.year

    def get_initial_cost(self):
        """
        Obtiene el costo inicial aprobado para el año actual.

        Returns:
            float: El valor del costo inicial aprobado. Devuelve 0.0 si no se
                   encuentra una entrada para el año actual o si el valor no es válido.
        """
        row = self.df[self.df['Year'] == self.year]
        if not row.empty:
            value = row.iloc[0]['Initial Cost Approved']
            try:
                return float(value)
            except Exception:
                return 0.0
        return 0.0

    def set_initial_cost(self, value):
        """
        Establece el costo inicial aprobado para el año actual en memoria.

        El valor se convierte a float. Si la conversión falla, se establece en 0.0.

        Args:
            value: El nuevo valor para el costo inicial aprobado.
        """
        try:
            value = float(value)
        except Exception:
            value = 0.0
        self.df.loc[self.df['Year'] == self.year, 'Initial Cost Approved'] = value

    def save(self):
        """
        Guarda el estado actual del DataFrame en el archivo CSV.
        """
        self.df.to_csv(self.file_path, index=False)

    def get_dataframe(self):
        """
        Retorna el DataFrame con los datos del costo inicial aprobado.
        """
        return self.df

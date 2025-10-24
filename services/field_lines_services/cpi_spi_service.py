import os
import pandas as pd
from calendar import month_name
from utils.file_manager import get_cpi_spi_path, get_all_cpi_spi_files

class CpiSpiService:
    def __init__(self, line_title=None):
        self.line_title = line_title
        self.CSV_PATH = get_cpi_spi_path(line_title) if line_title else None
        self.dataframe = self._load_or_create_csv()

    def _load_or_create_csv(self):
        """Carga o crea un DataFrame con CPI y SPI inicializados"""
        if self.CSV_PATH and os.path.exists(self.CSV_PATH):
            try:
                df = pd.read_csv(self.CSV_PATH)
            except pd.errors.EmptyDataError:
                # Archivo existe pero está vacío, crear DataFrame por defecto
                df = self._create_default_dataframe()
        else:
            df = self._create_default_dataframe()
        return df

    def _create_default_dataframe(self):
        """Crea un DataFrame por defecto con meses, CPI y SPI en 0.0"""
        months = list(month_name)[1:]  # January to December
        return pd.DataFrame({
            "Month": months,
            "CPI": [0.0] * 12,
            "SPI": [0.0] * 12
        })


    def set_line_title(self, line_title):
        """Cambia la línea de campo y carga los datos correspondientes"""
        self.line_title = line_title
        self.CSV_PATH = get_cpi_spi_path(line_title)
        self.dataframe = self._load_or_create_csv()

    def get_available_lines(self):
        """Retorna una lista de todas las líneas disponibles"""
        files = get_all_cpi_spi_files()
        return [line_title for line_title, _ in files]

    def save_to_csv(self):
        """Guarda el DataFrame actual en CSV"""
        if self.CSV_PATH:
            # Crear el directorio si no existe
            os.makedirs(os.path.dirname(self.CSV_PATH), exist_ok=True)
            self.dataframe.to_csv(self.CSV_PATH, index=False)

    def get_data_as_list(self):
        """Retorna los datos como lista de diccionarios"""
        return self.dataframe.to_dict(orient="records")

    def get_columns(self):
        """Retorna las columnas del DataFrame"""
        return list(self.dataframe.columns)
    
    def get_dataframe(self) -> pd.DataFrame:
        """Retorna una copia del DataFrame"""
        return self.dataframe.copy()

    def get_current_and_next_info(self):
        """
        Retorna un dict con el CPI y SPI del mes actual (último con CPI != 0) y el siguiente.
        """
        df = self.get_dataframe()
        if df[df["CPI"] != 0].empty:
            # Si no hay ningún valor distinto de 0, retorna None
            return {
                "current_month": None,
                "next_month": None,
                "cpi_current": None,
                "spi_current": None,
                "cpi_next": None,
                "spi_next": None
            }
        last_valid_idx = df[df["CPI"] != 0].index[-1]
        current_month = df.loc[last_valid_idx, "Month"]
        next_month = df.loc[last_valid_idx + 1, "Month"] if last_valid_idx + 1 < len(df) else None
        cpi_current = df.loc[last_valid_idx, "CPI"]
        spi_current = df.loc[last_valid_idx, "SPI"]
        cpi_next = df.loc[last_valid_idx + 1, "CPI"] if next_month else None
        spi_next = df.loc[last_valid_idx + 1, "SPI"] if next_month else None
        return {
            "current_month": current_month,
            "next_month": next_month,
            "cpi_current": cpi_current,
            "spi_current": spi_current,
            "cpi_next": cpi_next,
            "spi_next": spi_next
        }

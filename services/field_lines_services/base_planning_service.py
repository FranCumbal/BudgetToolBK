from abc import ABC, abstractmethod
import os
import pandas as pd
from calendar import month_name
from datetime import datetime
from utils.file_manager import get_manual_planning_path, get_all_manual_planning_files

class BasePlanningService(ABC):
    """Clase base abstracta para servicios de planificación"""
    
    def __init__(self, line_title=None):
        self.line_title = line_title
        self.CSV_PATH = get_manual_planning_path(line_title) if line_title else None
        self.dataframe = self._load_or_create_csv()

    def _load_or_create_csv(self):
        """Carga el CSV existente o crea uno nuevo con la estructura por defecto"""
        if self.CSV_PATH and os.path.exists(self.CSV_PATH):
            df = pd.read_csv(self.CSV_PATH)
            # Validar que tenga las columnas necesarias
            df = self._validate_and_fix_columns(df)
        else:
            df = self._create_default_dataframe()
        return df

    @abstractmethod
    def _create_default_dataframe(self):
        """Crea el DataFrame por defecto según el tipo de servicio"""
        pass

    @abstractmethod
    def _validate_and_fix_columns(self, df):
        """Valida y corrige las columnas del DataFrame cargado"""
        pass

    @abstractmethod
    def get_editable_columns(self):
        """Retorna las columnas que pueden ser editadas"""
        pass

    @abstractmethod
    def get_columns(self):
        """Retorna todas las columnas del DataFrame"""
        pass

    def set_line_title(self, line_title):
        """Cambia la línea de campo y carga los datos correspondientes"""
        self.line_title = line_title
        self.CSV_PATH = get_manual_planning_path(line_title)
        self.dataframe = self._load_or_create_csv()

    def get_available_lines(self):
        """Retorna una lista de todas las líneas disponibles"""
        files = get_all_manual_planning_files()
        return [line_title for line_title, _ in files]

    def update_row(self, month, column, value):
        """Actualiza un valor específico en el DataFrame"""
        idx = self.dataframe[self.dataframe["Month"] == month].index
        if not idx.empty:
            # La columna debe estar en las columnas editables para ser actualizada
            if column in self.get_editable_columns():
                self.dataframe.at[idx[0], column] = value
                self._post_update_calculations(month)

    @abstractmethod
    def _post_update_calculations(self, month):
        """Realiza cálculos automáticos después de una actualización"""
        pass

    def save_to_csv(self):
        if self.CSV_PATH:
            os.makedirs(os.path.dirname(self.CSV_PATH), exist_ok=True)
            self.dataframe.to_csv(self.CSV_PATH, index=False)

    def get_data_as_list(self):
        return self.dataframe.to_dict(orient="records")

    def get_dataframe(self) -> pd.DataFrame:
        return self.dataframe.copy()

    def get_current_month_index(self):
        """Retorna el índice del mes actual (0-based)"""
        current_month = datetime.now().month - 1  # 0-based
        return current_month

    def is_month_editable(self, month_index):
        """Determina si un mes es editable (mes actual en adelante)"""
        return month_index >= self.get_current_month_index()

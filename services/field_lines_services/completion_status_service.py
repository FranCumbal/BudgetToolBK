# logic/field_lines/field_lines_services/completion_status_service.py
import pandas as pd
import os
from utils.file_manager import get_completion_status_path 

class CompletionStatusService:
    def __init__(self):
        self.csv_path = get_completion_status_path()
        self.dataframe = self._load_or_create()

    def _load_or_create(self):
        try:
            df = pd.read_csv(self.csv_path)
            # Asegurarse de que la columna 'completed' sea de tipo booleano
            if 'completed' in df.columns:
                df['completed'] = df['completed'].astype(bool)
            return df
        except FileNotFoundError:
            # Si no existe, crea un DataFrame vacío y el archivo
            df = pd.DataFrame(columns=["line_name", "completed"])
            df.to_csv(self.csv_path, index=False)
            return df

    def get_status(self, line_name: str) -> bool:
        """Devuelve True si una línea está marcada como completa, False en caso contrario."""
        record = self.dataframe[self.dataframe["line_name"] == line_name]
        if not record.empty:
            return bool(record.iloc[0]["completed"])
        return False

    def set_status(self, line_name: str, is_completed: bool):
        """Establece el estado de completado para una línea y guarda el archivo."""
        self.dataframe = self.dataframe[self.dataframe["line_name"] != line_name]
        new_row = pd.DataFrame([{"line_name": line_name, "completed": is_completed}])
        self.dataframe = pd.concat([self.dataframe, new_row], ignore_index=True)
        self.dataframe.to_csv(self.csv_path, index=False)

    def get_completed_lines(self) -> list:
        """Devuelve una lista con los nombres de todas las líneas completadas."""
        if self.dataframe.empty or "completed" not in self.dataframe.columns:
            return []
        # Filtrar donde la columna 'completed' es explícitamente True
        completed_df = self.dataframe[self.dataframe["completed"] == True]
        return completed_df["line_name"].tolist()
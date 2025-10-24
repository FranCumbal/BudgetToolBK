import os
import pandas as pd
from datetime import datetime
from utils.file_manager import get_field_approved_budget_activities_from_file

COLUMNS = ["idx", "year", "budget", "approved_activities", "line_name"]

class ApprovedBudgetActivitiesService:
    """
    Gestiona los datos de presupuesto y actividades aprobadas en un archivo CSV.

    Esta clase proporciona una interfaz para realizar operaciones CRUD (Crear, Leer,
    Actualizar) sobre un archivo CSV que almacena el presupuesto y el número
    de actividades aprobadas para cada línea de servicio por año.
    """
    def __init__(self):
        """
        Inicializa el servicio.

        Establece la ruta al archivo CSV y carga los datos existentes o crea
        un nuevo archivo con los encabezados correctos si no existe.
        """
        self.csv_path = get_field_approved_budget_activities_from_file()
        self.dataframe = self._load_or_create_csv()

    def _load_or_create_csv(self):
        """
        Carga los datos desde el archivo CSV o crea uno nuevo si no existe.

        Returns:
            pd.DataFrame: Un DataFrame con los datos cargados o un DataFrame
                          vacío con la estructura de columnas definida.
        """
        if not os.path.exists(self.csv_path):
            df = pd.DataFrame(columns=COLUMNS)
            df.to_csv(self.csv_path, index=False)
            return df
        df = pd.read_csv(self.csv_path)
        return df

    def get_data_as_list(self):
        """
        Devuelve los datos del DataFrame como una lista de diccionarios.
        Cada diccionario representa una fila del catálogo.
        """
        return self.dataframe.to_dict(orient="records")

    def get_columns(self):
        """
        Devuelve los nombres de las columnas que son visibles y editables.
        Excluye la columna interna 'idx'.
        """
        return [col for col in COLUMNS if col not in ["idx"]]

    def save_to_csv(self):
        """
        Guarda el estado actual del DataFrame en el archivo CSV.
        Crea el directorio si no existe.
        """
        os.makedirs(os.path.dirname(self.csv_path), exist_ok=True)
        self.dataframe.to_csv(self.csv_path, index=False)

    def add_or_update_record(self, budget, approved_activities, line_name):
        """
        Añade un nuevo registro o actualiza uno existente para una línea y año específicos.

        Busca un registro que coincida con el año actual y el `line_name`.
        Si lo encuentra, actualiza los valores de presupuesto y actividades.
        Si no, crea un nuevo registro con un nuevo índice. Finalmente, guarda los cambios.
        """
        year = datetime.now().year
        mask = (self.dataframe["year"] == year) & (self.dataframe["line_name"] == line_name)
        if mask.any():
            idx = self.dataframe[mask].index[0]
            self.dataframe.at[idx, "budget"] = budget
            self.dataframe.at[idx, "approved_activities"] = approved_activities
        else:
            new_idx = self._get_next_idx()
            new_row = {
                "idx": new_idx,
                "year": year,
                "budget": budget,
                "approved_activities": approved_activities,
                "line_name": line_name
            }
            self.dataframe = pd.concat([self.dataframe, pd.DataFrame([new_row])], ignore_index=True)
        self.save_to_csv()

    def _get_next_idx(self):
        """Calcula el siguiente índice único para un nuevo registro."""
        if self.dataframe.empty:
            return 1
        return int(self.dataframe["idx"].max()) + 1

    def reload(self):
        """Recarga los datos desde el archivo CSV, descartando cambios en memoria."""
        self.dataframe = self._load_or_create_csv()
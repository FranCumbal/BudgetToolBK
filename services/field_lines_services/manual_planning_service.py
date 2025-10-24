import os
import pandas as pd
from calendar import month_name
from utils.file_loader import load_field_reports_from_json
from utils.file_manager import get_manual_planning_path, get_all_manual_planning_files

COLUMNS = ["Month", "Planned Activities"]

class ManualPlanningService:
    """
    Gestiona los datos de planificación manual para una línea de campo específica.

    Esta clase se encarga de leer, crear y modificar un archivo CSV que contiene
    la planificación manual de actividades. Adapta su estructura de columnas
    dependiendo de si la línea es "normal" o "especial" (Varillera, Zona Sur).
    """
    def __init__(self, line_title=None):
        """
        Inicializa el servicio de planificación manual.

        Args:
            line_title (str, optional): El título de la línea de campo a gestionar.
                                        Si es None, se inicializa sin datos.
        """
        self.line_title = line_title
        self.CSV_PATH = get_manual_planning_path(line_title) if line_title else None
        self.dataframe = self._load_or_create_csv()

    def _load_or_create_csv(self):
        """
        Carga el archivo CSV de planificación o crea un DataFrame por defecto.

        Si el archivo CSV para la línea actual existe, lo carga. De lo contrario,
        crea un nuevo DataFrame con 12 meses y valores en cero, asegurando que
        tenga las columnas correctas según el tipo de línea.

        Returns:
            pd.DataFrame: El DataFrame con los datos de planificación.
        """
        if self.CSV_PATH and os.path.exists(self.CSV_PATH):
            df = pd.read_csv(self.CSV_PATH)
            df = self._validate_and_add_missing_columns(df)
        else:
            months = list(month_name)[1:]
            df = pd.DataFrame({
                "Month": months,
                "Planned Activities": [0] * 12
            })
            df = self._validate_and_add_missing_columns(df)
        return df

    def _validate_and_add_missing_columns(self, df):
        """
        Asegura que el DataFrame tenga las columnas correctas según el tipo de línea.

        Para líneas especiales, elimina columnas adicionales. Para líneas normales,
        se asegura de que existan las columnas 'Scheduled Activities' y 'Forecast'.
        """
        if self._is_special_line():
            columns_to_remove = ["Scheduled Activities", "Forecast", "Category 1", "Category 2", "Category 3"]
            for col in columns_to_remove:
                if col in df.columns:
                    df = df.drop(columns=[col])
        else:
            if self.should_have_scheduled_activities() and "Scheduled Activities" not in df.columns:
                df["Scheduled Activities"] = [0.0] * len(df)
            
            if self.should_have_forecast() and "Forecast" not in df.columns:
                df["Forecast"] = [0.0] * len(df)
        
        return df

    def set_line_title(self, line_title):
        """
        Establece una nueva línea de campo y recarga sus datos de planificación.
        """
        self.line_title = line_title
        self.CSV_PATH = get_manual_planning_path(line_title)
        self.dataframe = self._load_or_create_csv()

    def get_available_lines(self):
        """
        Obtiene una lista de todas las líneas que tienen un archivo de planificación manual.
        """
        files = get_all_manual_planning_files()
        return [line_title for line_title, _ in files]

    def update_row(self, month, column, value):
        """
        Actualiza el valor de una celda específica en el DataFrame en memoria.

        Args:
            month (str): El mes de la fila a actualizar.
            column (str): El nombre de la columna a actualizar.
            value: El nuevo valor para la celda.
        """
        idx = self.dataframe[self.dataframe["Month"] == month].index
        if not idx.empty and column in self.get_editable_columns():
            if column == "Scheduled Activities" or column == "Planned Activities":
                self.dataframe.at[idx[0], column] = int(value)
            elif column == "Forecast":
                self.dataframe.at[idx[0], column] = float(value)
            else:
                self.dataframe.at[idx[0], column] = value
            self._post_update_calculations(month)

    def save_to_csv(self):
        """
        Guarda el estado actual del DataFrame en su archivo CSV correspondiente.
        Crea el directorio si no existe.
        """
        if self.CSV_PATH:
            os.makedirs(os.path.dirname(self.CSV_PATH), exist_ok=True)
            self.dataframe.to_csv(self.CSV_PATH, index=False)

    def get_data_as_list(self):
        """
        Devuelve los datos del DataFrame como una lista de diccionarios.
        Excluye columnas internas como 'Forecast_Manual' si existen.
        """
        df = self.dataframe.copy()
        if "Forecast_Manual" in df.columns:
            df = df.drop(columns=["Forecast_Manual"])
        return df.to_dict(orient="records")

    def get_columns(self):
        """
        Devuelve la lista de nombres de columna del DataFrame.
        Excluye columnas internas como 'Forecast_Manual' si existen.
        """
        cols = list(self.dataframe.columns)
        if "Forecast_Manual" in cols:
            cols.remove("Forecast_Manual")
        return cols
    
    def get_editable_columns(self):
        """
        Devuelve una lista de las columnas que deben ser editables en la interfaz.
        """
        editable = ["Planned Activities"]
        
        if self.should_have_scheduled_activities() and "Scheduled Activities" in self.dataframe.columns:
            editable.append("Scheduled Activities")
        if self.should_have_forecast() and "Forecast" in self.dataframe.columns:
            editable.append("Forecast")
        return editable
    
    def _post_update_calculations(self, month):
        """
        Placeholder para cálculos automáticos después de una actualización.
        Actualmente, la lógica de cálculo se maneja en la vista.
        """
        if "Scheduled Activities" in self.dataframe.columns and "Forecast" in self.dataframe.columns:
            pass
    
    def update_forecast(self, month, cpae_value):
        """
        Calcula y actualiza el valor del Forecast para un mes específico.

        El Forecast se calcula como: `Scheduled Activities * cpae_value`.

        Args:
            month (str): El mes para el cual se actualizará el forecast.
            cpae_value (float): El costo por actividad a utilizar en el cálculo.
        """
        if "Forecast" in self.dataframe.columns:
            idx = self.dataframe[self.dataframe["Month"] == month].index
            if not idx.empty:
                row_idx = idx[0]
                if "Scheduled Activities" in self.dataframe.columns:
                    scheduled = self.dataframe.at[row_idx, "Scheduled Activities"]
                    forecast = scheduled * cpae_value
                    self.dataframe.at[row_idx, "Forecast"] = round(forecast, 2)
    
    def should_have_forecast(self):
        """Determina si la línea actual debe tener una columna 'Forecast'."""
        return not self._is_special_line()
    
    def should_have_scheduled_activities(self):
        """Determina si la línea actual debe tener una columna 'Scheduled Activities'."""
        return not self._is_special_line()
    
    def _is_special_line(self):
        """Comprueba si la línea actual es de tipo 'especial' (Varillera o Zona Sur)."""
        return self._is_varillera_or_south_zone()
    
    def _is_varillera_or_south_zone(self):
        """
        Verifica si la línea es Varillera o de Zona Sur mediante múltiples comprobaciones.

        La lógica es:
        1. Comprueba si el título contiene 'varillera' o 'varella'.
        2. Carga la configuración JSON y busca si la zona es 'south' o la clase
           es 'VarilleraReport'.
        3. Como fallback, busca patrones de nombres de línea de la zona sur.
        """
        if not self.line_title:
            return False
        
        line_title_lower = self.line_title.lower()
        
        if "varillera" in line_title_lower or "varella" in line_title_lower:
            return True
        
        try:
            configs = load_field_reports_from_json()
            
            # Buscar la línea en la configuración
            for config in configs:
                config_title = config.get("title", "").lower()
                if config_title == line_title_lower:
                    if config.get("zone", "").lower() == "south":
                        return True
                    if config.get("class") in ["VarilleraReport"]:
                        return True
                    break
        except Exception as e:
            print(f"Error al verificar configuración de línea: {e}")
            south_zone_patterns = ["ctu", "item 66", "item 68", "item 70"]
            if any(pattern in line_title_lower for pattern in south_zone_patterns):
                return True
        
        return False
    
    def _is_varillera(self):
        """Método legacy para compatibilidad. Delega a _is_special_line()"""
        return self._is_special_line()
    
    def get_readonly_columns_before_current_month(self):
        """
        Define qué columnas deben ser de solo lectura para meses anteriores al actual.
        Actualmente, todas las columnas son editables para todos los meses.
        """
        return []
    
    def get_dataframe(self) -> pd.DataFrame:
        """
        Devuelve una copia segura del DataFrame interno para evitar modificaciones externas.
        """
        return self.dataframe.copy()

    def get_line_type(self):
        """
        Devuelve un identificador de tipo de línea ('varillera', 'south_zone', 'normal').
        Útil para depuración y lógica condicional.
        """
        if not self.line_title:
            return "unknown"
        
        line_title_lower = self.line_title.lower()
        
        if "varillera" in line_title_lower or "varella" in line_title_lower:
            return "varillera"
        try:
            configs = load_field_reports_from_json()
            
            for config in configs:
                if config.get("title", "").lower() == line_title_lower:
                    if config.get("zone", "").lower() == "south":
                        return "south_zone"
                    break
        except:
            pass
        
        return "normal"
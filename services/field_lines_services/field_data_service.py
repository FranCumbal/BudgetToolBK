import pandas as pd
from datetime import datetime
from services.read_excel import get_field_approved_budget_activities_from_csv

class FieldDataService:
    """
    Servicio para acceder y procesar los datos de presupuesto y actividades aprobadas.

    Esta clase se encarga de cargar los datos de un origen CSV, filtrarlos por
    línea de servicio y año, y formatearlos para su uso en los reportes.
    """
    @staticmethod
    def get_approved_budget_activities(line_title):
        """
        Obtiene y formatea el DataFrame de actividades y presupuesto aprobados para una línea específica.

        Carga los datos de presupuesto aprobados desde un archivo CSV, filtra las
        filas que corresponden a la `line_title` proporcionada y al año actual.
        Además, renombra y convierte las columnas relevantes a los tipos de datos
        correctos (int para actividades, float para presupuesto).

        Args:
            line_title (str): El título de la línea de servicio para la cual se
                              desean obtener los datos aprobados.

        Returns:
            pd.DataFrame: Un DataFrame con las columnas 'Presupuesto {año_actual}',
                          'Actividades aprobadas' y 'line_name' para la línea especificada.
        """
        df_total_approved_budget_activities = get_field_approved_budget_activities_from_csv()
        actual_year = datetime.now().year
        df_total_approved_budget_activities = pd.DataFrame(df_total_approved_budget_activities)
        df_total_approved_budget_activities = df_total_approved_budget_activities[
            df_total_approved_budget_activities["line_name"].str.strip().str.lower() == line_title.lower()
        ]
        df_total_approved_budget_activities["Actividades aprobadas"] = df_total_approved_budget_activities["approved_activities"].astype(int)
        df_total_approved_budget_activities["Year"] = df_total_approved_budget_activities["year"].astype(int)
        presupuesto_col = f"Presupuesto {actual_year}"
        df_total_approved_budget_activities[presupuesto_col] = df_total_approved_budget_activities["budget"].astype(float)
        return df_total_approved_budget_activities[[presupuesto_col, "Actividades aprobadas", "line_name"]]
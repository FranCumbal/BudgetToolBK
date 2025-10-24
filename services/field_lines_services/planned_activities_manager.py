import pandas as pd
from datetime import datetime
from utils.months_utils import NAME_MONTH_COMPLETE, SORTED_MONTHS, NAME_MONTH_COMPLETE
from services.field_lines_services.planning_service_factory import PlanningServiceFactory
class PlannedActivitiesManager():
    """
    Gestiona y procesa los datos de las actividades planeadas desde un DataFrame.

    Esta clase se encarga de normalizar los datos de entrada (especialmente las fechas),
    y proporciona métodos para calcular proyecciones, presupuestos y conteos de
    actividades planeadas y programadas.
    """
    def __init__(self, data_frame):
        """
        Inicializa el gestor con un DataFrame de actividades planeadas.

        Args:
            data_frame (pd.DataFrame): DataFrame que contiene los datos de planificación.
                                       Debe incluir una columna 'Month'.
        """
        self.df = data_frame
        if 'Month' not in self.df.columns: #OJO AQUI DEBES TENER EN CUENTA COMO LLAMEN A ESAS COLUMNAS EN EL EXCEL DE ELLOS
            raise ValueError("El Excel no tiene la columna 'Month'")
        self._preprocess_df()
        self.meses_ordenados = SORTED_MONTHS
        
    def _preprocess_df(self):
        """
        Pre-procesa el DataFrame para estandarizar la columna 'Month'.

        Detecta si el formato de mes es una fecha completa (ej. '31-ene-25') o un
        nombre de mes (ej. 'January'), y lo normaliza a un nombre de mes en minúsculas.
        """
        # Detectar si el formato es ya tipo 'january', 'february', etc.
        unique_months = self.df['Month'].str.lower().unique()
        if all(m in NAME_MONTH_COMPLETE.values() for m in unique_months):
            # Ya está limpio, normalizar
            self.df['Month'] = self.df['Month'].str.lower()
            return

        # Caso contrario, asumir formato '31-ene-25', '30-sept-25'
        formato_valido = self.df['Month'].str.match(r'^\d{2}-[a-zA-Z]{3,4}-\d{2}$')
        if not formato_valido.all():
            filas_erroneas = self.df[~formato_valido]
            raise ValueError(f"Formato de 'Month' incorrecto en filas: {filas_erroneas.index.tolist()}")

        # Extraer abreviatura del mes
        self.df['Mes_abrev'] = (
            self.df['Month']
            .str.split('-').str[1]
            .str.strip()
            .str.lower()
        )
        # Mapear abreviaturas a nombres completos
        self.df['Month'] = self.df['Mes_abrev'].map(NAME_MONTH_COMPLETE)
        self.df.drop('Mes_abrev', axis=1, inplace=True)
    
    def get_activities_planned_by_month(self, month):
        """
        Obtiene el número de actividades planeadas para un mes específico.
        """
        if month in self.meses_ordenados:
            month = NAME_MONTH_COMPLETE[month]
        filtered = self.df[self.df['Month'] == month.strip().lower()]
        if 'Initial Planned Activities' in filtered.columns:
            filtered.rename(columns={'Initial Planned Activities': 'Planned Activities'}, inplace=True)
        if not filtered.empty:
            return int(filtered['Planned Activities'].values[0])
        else:
            return 0  
        
    def generate_forecast_from_csv(self, service_type, title):
        """
        Genera un DataFrame de forecast utilizando un servicio de planificación específico.
        """
        planning_service = PlanningServiceFactory.create_service(service_type, title)
        df_planning = planning_service.get_dataframe()
        forecast_df = df_planning[["Month", "Forecast"]].copy()
        forecast_df['Month'] = forecast_df['Month'].str.lower()
        return forecast_df
    
    def generate_planned_activities_data_frame(self, months):
        """
        Crea un DataFrame con el acumulado de actividades planeadas mes a mes.
        """
        activities_data = []
        for month in months:
            activity_planned = self.get_activities_planned_by_month(month.lower())
            activities_data.append({"Month": month.lower(), "Planned Activities": activity_planned})
        df_activities_planned = pd.DataFrame(activities_data)
        df_activities_planned['Planned Activities'] = df_activities_planned['Planned Activities'].cumsum()
        return df_activities_planned

    def get_cpae_by_month(self, month, cost_by_activity, line_name, service_type):
        """
        Calcula el costo proyectado (CPAE) para un mes, basado en actividades programadas.
        """
        scheduled_activities = self.get_scheduled_executed_activities_by_month(month, line_name, service_type)
        return round(scheduled_activities * cost_by_activity, 2)  # Si no hay datos, será 0 * costo = 0
    
    def get_cpae_to_budget_by_month(self, month, cost_by_activity):
        """
        Calcula el costo para el presupuesto (CPAE) de un mes, basado en actividades planeadas.
        """
        planned_activities = self.get_activities_planned_by_month(month)
        return round(planned_activities * cost_by_activity, 2)  # Si no hay datos, será 0 * costo = 0
    
    def generate_cpae_data_frame_to_budget(self, months, cost_by_activity):
        """
        Genera un DataFrame con los costos mensuales para el presupuesto (CPAE).
        """
        data_to_cpae = []
        for month in months:
            cpae = self.get_cpae_to_budget_by_month(month.lower(), cost_by_activity)
            data_to_cpae.append({"Month": month.lower(), "CPAE": cpae})
        df_cpae = pd.DataFrame(data_to_cpae)
        return df_cpae
    
    def get_scheduled_executed_activities_by_month(self, month, line_name, service_type):
        """
        Obtiene el número de actividades programadas/ejecutadas para un mes específico.
        """
        df_scheduled_executed_activities = self.get_df_scheduled_executed_activities(line_name, service_type)
        month = month.strip().lower()
        for _, row in df_scheduled_executed_activities.iterrows():
            if row['Month'] == month:
                return row['Scheduled Activities']
        raise ValueError(f"Mes no encontrado en el DataFrame: {month}")

    def get_budget_by_month(self, month: str, df_budget) -> float:
        """
        Obtiene el valor del presupuesto para un mes desde un DataFrame de presupuesto.
        """
        month = month.strip().lower()
        if "Budget" not in df_budget.columns:
            raise ValueError("El DataFrame no contiene la columna 'Budget'.")
        if month not in df_budget["Month"].values:
            raise ValueError(f"Mes no encontrado en el DataFrame: {month}")
        return round(df_budget.loc[df_budget["Month"] == month.lower(), "Budget"].values[0], 2)
    
    def generate_cpae_data_frame(self, months, cost_by_activity, line_name, service_type):
        """
        Genera un DataFrame con los costos proyectados (CPAE) para cada mes.
        """
        data_to_cpae = []
        for month in months:
            cpae = self.get_cpae_by_month(month.lower(), cost_by_activity, line_name, service_type)
            data_to_cpae.append({"Month": month.lower(), "CPAE": cpae})
        df_cpae = pd.DataFrame(data_to_cpae)
        return df_cpae
    
    def generate_budget_data_frame(self, df_cpae):
        """
        Calcula el presupuesto acumulado a partir de un DataFrame de costos mensuales (CPAE).
        """
        df_cpae["Budget"] = df_cpae["CPAE"].cumsum()
        return df_cpae[["Month", "Budget"]]

    def get_df_scheduled_executed_activities_accumulated(self, title, service_type, last_value, last_index_month):
        """
        Genera el acumulado de actividades proyectadas (ejecutadas + programadas).

        Combina el último valor de actividades ejecutadas (`last_value`) con las
        actividades programadas a partir del mes siguiente al último ejecutado
        (`last_index_month`), creando una proyección acumulada para el resto del año.
        """
        planning_service = PlanningServiceFactory.create_service(service_type, title)
        df_planning = planning_service.get_dataframe()
        months = ['january', 'february', 'march', 'april', 'may', 'june', 
                 'july', 'august', 'september', 'october', 'november', 'december']
        # Determinar el índice del mes posterior al de las actividades ejecutadas (desde ahi se va a empezar a colocar el schduled)
        next_month_idx = last_index_month + 1
        scheduled_data = []
        for idx, month in enumerate(months):
            if idx < next_month_idx:
                scheduled_data.append(0)
            else:
                month_data = df_planning[df_planning['Month'] == month.title()]
                if not month_data.empty:
                    scheduled_activities = int(float(month_data.iloc[0].get('Scheduled Activities', 0)))
                else:
                    scheduled_activities = 0
                scheduled_data.append(scheduled_activities)
        # Lógica: mantener last_value hasta que haya un valor real, luego acumular, solo desde el mes actual
        result = []
        acumulado = 0
        for idx, val in enumerate(scheduled_data):
            if idx < next_month_idx:
                result.append(0)
            else:
                if val == 0:
                    result.append(last_value if acumulado == 0 else acumulado)
                else:
                    acumulado = (acumulado if acumulado != 0 else last_value) + val
                    result.append(acumulado)
        df_result = pd.DataFrame({
            'Month': months,
            'Scheduled Activities': result
        })
        return df_result
    
    def get_df_scheduled_executed_activities_accumulated_varillera(self, df_scheduled_executed_activities, last_value, last_index_month):
        """
        Genera el acumulado de actividades proyectadas, específico para 'Varillera'.

        Aplica la misma lógica de acumulación que el método general, pero utiliza un
        DataFrame de actividades programadas ya procesado, en lugar de generarlo
        a través de la `PlanningServiceFactory`.
        """
        months = ['january', 'february', 'march', 'april', 'may', 'june', 
                 'july', 'august', 'september', 'october', 'november', 'december']
        current_month_idx = last_index_month + 1
        scheduled_data = []
        for idx, month in enumerate(months):
            if idx < current_month_idx:
                scheduled_data.append(0)
            else:
                month_data = df_scheduled_executed_activities[df_scheduled_executed_activities['Month'].str.lower() == month]
                if not month_data.empty:
                    scheduled_activities = int(float(month_data.iloc[0].get('Scheduled Activities', 0)))
                else:
                    scheduled_activities = 0
                scheduled_data.append(scheduled_activities)
        # Lógica: mantener last_value hasta que haya un valor real, luego acumular, solo desde el mes actual
        result = []
        acumulado = 0
        for idx, val in enumerate(scheduled_data):
            if idx < current_month_idx:
                result.append(0)
            else:
                if val == 0:
                    result.append(last_value if acumulado == 0 else acumulado)
                else:
                    acumulado = (acumulado if acumulado != 0 else last_value) + val
                    result.append(acumulado)
        df_result = pd.DataFrame({
            'Month': months,
            'Scheduled Activities': result
        })
        return df_result
    
    def get_df_scheduled_executed_activities(self, title, service_type):
        """
        Genera un DataFrame con el conteo mensual de actividades programadas.

        Obtiene las actividades programadas desde el mes actual en adelante,
        dejando los meses pasados en cero.
        """
        planning_service = PlanningServiceFactory.create_service(service_type, title)
        df_planning = planning_service.get_dataframe()
        months = ['january', 'february', 'march', 'april', 'may', 'june', 
                 'july', 'august', 'september', 'october', 'november', 'december']
        # Determinar el índice del mes actual 
        current_month_idx = datetime.now().month - 1
        scheduled_data = []
        for idx, month in enumerate(months):
            if idx < current_month_idx:
                scheduled_data.append(0)
            else:
                month_data = df_planning[df_planning['Month'] == month.title()]
                if not month_data.empty:
                    scheduled_activities = int(float(month_data.iloc[0].get('Scheduled Activities', 0)))
                else:
                    scheduled_activities = 0
                scheduled_data.append(scheduled_activities)
        df_result = pd.DataFrame({
            'Month': months,
            'Scheduled Activities': scheduled_data
        })
        return df_result
from calendar import month_name
from datetime import datetime
from functools import cached_property
from typing import Any, Dict, Optional
import pandas as pd
from services.field_lines_services.executed_activities_manager import ExecutedActivitiesManager
from services.field_lines_services.field_activities_coordinator import FieldActivitiesCoordinator
from services.field_lines_services.anual_pta_loader import AnnualPTALoader
from services.field_lines_services.field_data_service import FieldDataService
from services.field_lines_services.manual_planning_service import ManualPlanningService
from services.field_lines_services.planned_activities_manager import PlannedActivitiesManager
from services.field_lines_services.field_graph_generator_service import FieldGraphGeneratorService
from services.field_lines_services.cpi_spi_service import CpiSpiService
from services.read_excel import get_plan_df_by_line
from utils.file_loader import load_months_from_file

class FieldReport:
    """
    Clase que encapsula la lógica para generar un reporte completo de una línea de campo.

    Esta clase centraliza el acceso y la manipulación de datos relacionados con
    actividades planeadas, ejecutadas, presupuestos y proyecciones, actuando como
    una fachada para diversos servicios y gestores de datos.
    """
    def __init__(self, title: str, service_type: str, zone: str, line_type: str, field_graph_service: Optional[FieldGraphGeneratorService] = None, planned_activities_manager: Optional[PlannedActivitiesManager] = None, executed_activities_manager: Optional[ExecutedActivitiesManager] = None, manual_planning_service: Optional[ManualPlanningService] = None, field_data_service: Optional[FieldDataService] = None, field_activities_coordinator: Optional[FieldActivitiesCoordinator] = None):
        """
        Inicializa una instancia de FieldReport.

        Args:
            title (str): Título o nombre de la línea.
            service_type (str): Tipo de servicio.
            zone (str): Zona geográfica.
            line_type (str): Tipo de línea.
            field_graph_service (Optional[FieldGraphGeneratorService]): Servicio para generar gráficos.
            planned_activities_manager (Optional[PlannedActivitiesManager]): Gestor de actividades planeadas.
            executed_activities_manager (Optional[ExecutedActivitiesManager]): Gestor de actividades ejecutadas.
            manual_planning_service (Optional[ManualPlanningService]): Servicio de planificación manual.
            field_data_service (Optional[FieldDataService]): Servicio de datos de campo.
            field_activities_coordinator (Optional[FieldActivitiesCoordinator]): Coordinador de actividades de campo.
        """
        self.title = title
        self.service_type = service_type
        self.zone = zone
        self.line_type = line_type
        self._field_graph_service = field_graph_service
        self._planned_activities_manager = planned_activities_manager
        self._executed_activities_manager = executed_activities_manager
        self._manual_planning_service = manual_planning_service
        self._field_data_service = field_data_service
        self._field_activities_coordinator = field_activities_coordinator
        self._approved_budget_activities_cache = None
        self._cost_by_activity_cache = None
        self._year = None

    @property
    def manual_planning_service(self) -> ManualPlanningService:
        """Inicializa y devuelve de forma perezosa el servicio de planificación manual."""
        if self._manual_planning_service is None:
            self._manual_planning_service = ManualPlanningService(line_title=self.title)
        return self._manual_planning_service

    @property
    def executed_activities_manager(self) -> ExecutedActivitiesManager:
        """Inicializa y devuelve de forma perezosa el gestor de actividades ejecutadas."""
        if self._executed_activities_manager is None:
            self._executed_activities_manager = ExecutedActivitiesManager()
        return self._executed_activities_manager
    
    @property
    def planned_activities_manager(self) -> PlannedActivitiesManager:
        """Inicializa y devuelve de forma perezosa el gestor de actividades planeadas."""
        if self._planned_activities_manager is None:
            self._planned_activities_manager = PlannedActivitiesManager(get_plan_df_by_line(self.title))
        return self._planned_activities_manager
    
    @property
    def field_graph_service(self) -> FieldGraphGeneratorService:
        """Inicializa y devuelve de forma perezosa el servicio de generación de gráficos."""
        if self._field_graph_service is None:
            self._field_graph_service = FieldGraphGeneratorService()
        return self._field_graph_service

    @property
    def field_activities_coordinator(self) -> FieldActivitiesCoordinator:
        """Inicializa y devuelve de forma perezosa el coordinador de actividades de campo."""
        if self._field_activities_coordinator is None:
            self._field_activities_coordinator = FieldActivitiesCoordinator(self.planned_activities_manager, self.executed_activities_manager)
        return self._field_activities_coordinator

    @property
    def field_data_service(self) -> FieldDataService:
        """Inicializa y devuelve de forma perezosa el servicio de datos de campo."""
        if self._field_data_service is None:
            self._field_data_service = FieldDataService()
        return self._field_data_service
    
    @cached_property
    def anual_initial_planned_loader(self) -> AnnualPTALoader:
        """Carga y devuelve de forma perezosa el cargador de PTA anual inicial."""
        return AnnualPTALoader(self.get_approved_budget_activities())
    
    @property
    def cost_by_activity(self) -> float:
        """Calcula y cachea el costo por actividad (CPAE) para el año del reporte."""
        if self._cost_by_activity_cache is None:
            self._cost_by_activity_cache = self.anual_initial_planned_loader.get_cpae_value(self.get_year())
        return self._cost_by_activity_cache
    
    @property
    def year(self) -> int:
        """Determina y devuelve el año fiscal del reporte, ajustando si el mes actual es enero."""
        if self._year is None:
            if datetime.now().month == 1: #Si es enero
                self._year = datetime.now().year - 1 # El anio es el anio anterior al actual
            else:
                self._year = datetime.now().year #sino, es el anio actual
        return self._year
    
    def get_approved_budget_activities(self) -> pd.DataFrame:
        """Obtiene y cachea el DataFrame de actividades y presupuesto aprobados para la línea."""
        if self._approved_budget_activities_cache is None:
            self._approved_budget_activities_cache = self.field_data_service.get_approved_budget_activities(self.title)
        return self._approved_budget_activities_cache
    
    def get_cost_by_activity(self):
        """Devuelve el costo por actividad (CPAE) cacheado."""
        return self.cost_by_activity
    
    def get_year(self) -> int:
        """Devuelve el año del reporte."""
        return self.year
    
    def _get_months_data(self) -> list:
        """Carga la lista de meses desde un archivo de configuración."""
        return load_months_from_file()
    
    def generate_budget(self):
        """Genera el DataFrame del presupuesto mensual basado en las actividades planeadas y el CPAE."""
        df_budget = self.planned_activities_manager.generate_budget_data_frame(self.generate_cpae_data_frame_to_budget())
        return df_budget

    def generate_forecast(self):
        """Genera el DataFrame del forecast (proyección) de costos."""
        df_forecast = self.field_activities_coordinator.get_projected_adjusted_data_frame(self.title, self.service_type)
        return df_forecast
    
    def generate_graph(self):
        """Genera el gráfico de forecast de la línea utilizando todas las fuentes de datos."""
        return self.field_graph_service.generate_field_forecast_graph(self.title, **self.get_data_sources())
    
    def generate_deviations(self):
        """Genera un DataFrame con las desviaciones (actualmente es un placeholder)."""
        return pd.DataFrame()
    
    def generate_summary_data_frame(self):
        """Crea un DataFrame resumen con los principales indicadores de la línea."""
        summary_df = pd.DataFrame()
        year = self.get_year()
        last_valid_month = self.executed_activities_manager.get_last_index_month_in_excel()
        real_cost_accumulated_df = self.generate_accumulated_real_cost_data_frame()
        forecast_df = self.generate_forecast()
        approved_budget_df = self.get_approved_budget_activities()
        forecast_activities_accumulated_df = self.generate_scheduled_executed_activities_accumulated_data_frame()
        activities_balance, cost_balance = self.get_balances(forecast_activities_accumulated_df.iloc[-1]['Scheduled Activities'], approved_budget_df["Actividades aprobadas"], forecast_df.iloc[-1]['Forecast'], approved_budget_df[f"Presupuesto {year}"])
        summary_df["contractual activity"] = approved_budget_df["line_name"] #bien
        summary_df["approved budget"] = approved_budget_df[f"Presupuesto {year}"] #Budget Aprobado bien
        summary_df["approved activities"] = approved_budget_df["Actividades aprobadas"] #PTA 2025 APROBADO actividades bien
        summary_df["executed activities"] = self.get_total_executed_activities() #Actividades ejecutadas hasta la fecha bien 
        summary_df["last valid real cost"] = round(real_cost_accumulated_df.iloc[last_valid_month]['TotalAccumulatedCost'], 3)
        summary_df["last valid month"] = real_cost_accumulated_df.iloc[last_valid_month]['Month']
        summary_df["last valid forecast activities"] = forecast_activities_accumulated_df.iloc[-1]['Scheduled Activities']
        summary_df["last valid forecast cost"] = forecast_df.iloc[-1]['Forecast']
        summary_df["activities balance"] = activities_balance
        summary_df["cost balance"] = cost_balance
        return summary_df
        
    def generate_executed_activities_and_cost_data_frame_by_month(self):
        """Crea un DataFrame que combina actividades ejecutadas y costos reales por mes."""
        df_executed_activities = self.generate_executed_activities_data_frame_by_month()
        df_executed_cost = self.executed_activities_manager.generate_real_cost_data_frame(self.title)
        df_merged = df_executed_activities.merge(df_executed_cost, on="Month", how="left")
        return df_merged

    def get_balances(self, forecast_activities_accumulated, approved_activities, last_forecast_cost, approved_budget):
        """Calcula los balances de actividades y costos entre lo aprobado y lo proyectado."""
        activities_balance = approved_activities - forecast_activities_accumulated
        cost_balance = approved_budget - last_forecast_cost
        return activities_balance, cost_balance

    def generate_planned_activities_data_frame_by_month(self):
        """Genera un DataFrame con el número de actividades planeadas manualmente por mes."""
        df = self.manual_planning_service.get_dataframe()
        planned_activities_df = df
        planned_activities_df["Month"] = planned_activities_df["Month"].str.lower()
        planned_activities_df["Planned Activities"] = planned_activities_df["Planned Activities"].astype(int)
        return planned_activities_df[["Month", "Planned Activities"]]

    def generate_accumulated_planned_activities_data_frame(self):
        """Genera un DataFrame con el acumulado de actividades planeadas mes a mes."""
        planned_activities_accumulated_df = self.generate_planned_activities_data_frame_by_month()
        planned_activities_accumulated_df["Planned Activities"] = planned_activities_accumulated_df["Planned Activities"].cumsum()
        return planned_activities_accumulated_df
    
    def generate_executed_activities_data_frame_by_month(self):
        """Genera un DataFrame con el número de actividades ejecutadas por mes."""
        meses = self._get_months_data()
        df_executed_activities_by_month = self.executed_activities_manager.generate_executed_activities_data_frame(meses, self.title)
        return df_executed_activities_by_month
    
    def get_executed_activities_data_frame_by_month(self):
        """
        Devuelve el DataFrame de actividades ejecutadas por mes.
        """
        meses = self._get_months_data()
        df_executed_activities_by_month = self.executed_activities_manager.get_executed_activities_data_frame_by_month(meses, self.title)
        return df_executed_activities_by_month
    
    def generate_accumulated_executed_activities_data_frame(self):
        """Genera un DataFrame con el acumulado de actividades ejecutadas mes a mes."""
        executed_activities_accumulated_df = self.generate_executed_activities_data_frame_by_month()
        executed_activities_accumulated_df["Executed Activities"] = executed_activities_accumulated_df["Executed Activities"].cumsum()

        return executed_activities_accumulated_df
    
    def generate_accumulated_real_cost_data_frame(self):
        """Genera un DataFrame con el costo real acumulado mes a mes."""
        accumulated_real_cost_df = self.executed_activities_manager.generate_accumulated_real_cost_data_frame(self.title)
        return accumulated_real_cost_df
    
    def generate_scheduled_executed_activities_accumulated_data_frame(self):
        """Genera un DataFrame con el acumulado de actividades proyectadas (ejecutadas + planeadas)."""
        accumulated_executed_activities_df = self.generate_accumulated_executed_activities_data_frame()
        last_valid_month = self.executed_activities_manager.get_last_index_month_in_excel()
        last_value = accumulated_executed_activities_df[accumulated_executed_activities_df['Executed Activities'] != 0]['Executed Activities'].iloc[-1] if not accumulated_executed_activities_df[accumulated_executed_activities_df['Executed Activities'] != 0].empty else 0
        scheduled_activities_accumulated_df = self.planned_activities_manager.get_df_scheduled_executed_activities_accumulated(self.title, self.service_type, last_value, last_valid_month)
        return scheduled_activities_accumulated_df

    def generate_scheduled_executed_activities_by_month(self):
        """Genera un DataFrame con las actividades proyectadas (ejecutadas + planeadas) por mes."""
        scheduled_executed_activities_df = self.planned_activities_manager.get_df_scheduled_executed_activities(self.title, self.service_type)
        return scheduled_executed_activities_df
    
    def generate_cpae_data_frame_to_budget(self):
        """Genera un DataFrame del costo por actividad (CPAE) por mes para el presupuesto."""
        meses = self._get_months_data()
        return self.planned_activities_manager.generate_cpae_data_frame_to_budget(meses, self.cost_by_activity)
    
    def generate_cpi_dataframe(self):
        """Genera un DataFrame con el Índice de Desempeño de Costos (CPI) mensual."""
        df_cpi = self.generate_budget().merge(self.generate_accumulated_real_cost_data_frame(), on="Month", how="left")
        df_cpi["CPI"] = df_cpi.apply(
            lambda row: round(row["Budget"] / row["TotalAccumulatedCost"],2) if row["TotalAccumulatedCost"] != 0 else 0, axis=1
        )
        return df_cpi[["Month", "CPI"]]
    
    def generate_spi_dataframe(self):
        """Genera DataFrame de SPI basado en actividades planeadas y ejecutadas acumuladas"""
        df_spi = self.generate_accumulated_planned_activities_data_frame().merge(self.generate_accumulated_executed_activities_data_frame(), on="Month", how="left")
        df_spi["SPI"] = df_spi.apply(
            lambda row: round(row["Executed Activities"] / row["Planned Activities"], 2)  if row["Planned Activities"] != 0 else 0, axis=1
        )
        return df_spi[["Month", "SPI"]]
    
    def generate_combined_cpi_spi_dataframe(self): 
        """Genera un DataFrame combinado con CPI y SPI"""
        df_combined = self.generate_cpi_dataframe().merge(self.generate_spi_dataframe(), on="Month", how="left")
        df_combined["Month"] = df_combined["Month"].str.strip().str.lower().str.title()
        return df_combined
    
    def get_cpi_spi_info(self):
        """Obtiene la información de CPI y SPI para el mes actual y el siguiente."""
        cpi_spi_service = CpiSpiService(self.title)
        return cpi_spi_service.get_current_and_next_info()
    
    def get_total_executed_activities(self) -> int: 
        """
        Obtiene el total de actividades ejecutadas.
        """
        df_executed = self.generate_accumulated_executed_activities_data_frame()
        if not df_executed.empty:
            return df_executed['Executed Activities'].iloc[-1]
        return 0

    def get_automatic_distribution(self):
        """
        Distribuye automáticamente las actividades aprobadas.
        """
        return self.anual_initial_planned_loader.automatic_distribution()
    def reload_planned_activities_manager(self):
        """Recarga el gestor de actividades planeadas para reflejar los datos más recientes."""
        self._planned_activities_manager = PlannedActivitiesManager(get_plan_df_by_line(self.title))

    def reload_manual_planning_service(self):
        """Recarga el servicio de planificación manual desde el archivo CSV."""
        self._manual_planning_service = ManualPlanningService(line_title=self.title)
        
    def reload_approved_budget_data(self):
        """
        Limpia el caché interno de datos de presupuesto y CPAE
        """
        self._approved_budget_activities_cache = None
        self._cost_by_activity_cache = None
        if 'anual_initial_planned_loader' in self.__dict__:
            del self.__dict__['anual_initial_planned_loader']

    def reload_executed_activities_manager(self):
        """
        Recarga del gestor de actividades ejecutadas, creando una nueva instancia que leerá los datos más recientes del archivo Excel de origen.
        """
        self._executed_activities_manager = ExecutedActivitiesManager()

    def get_monthly_summary_dataframe(self) -> pd.DataFrame:
        """
        Crea y devuelve un DataFrame con el resumen mensual de todos los datos clave.
        Esta es la base para la agregación del Reporte Líder.
        """
        # Forzar recarga de todos los datos para asegurar que estén frescos
        self.reload_approved_budget_data()
        self.reload_manual_planning_service()
        self.reload_executed_activities_manager()
        self.reload_planned_activities_manager()
        
        # Generar todo lo necesario
        forecast_df = self.generate_forecast()
        budget_df = self.generate_budget()
        real_cost_accumulated_df = self.generate_accumulated_real_cost_data_frame()
        executed_activities_df = self.generate_accumulated_executed_activities_data_frame()
        executed_activities_monthly_df = self.generate_executed_activities_data_frame_by_month()
        planned_activities_df = self.generate_accumulated_planned_activities_data_frame()
        planned_activities_monthly_df = self.generate_planned_activities_data_frame_by_month()
        scheduled_executed_activities_accumulated_df = self.generate_scheduled_executed_activities_accumulated_data_frame()
        scheduled_executed_activities_monthly_df = self.generate_scheduled_executed_activities_by_month()

        # hacer merge en la columna Month de todo
        merged_df = pd.merge(forecast_df, budget_df, on="Month", how="outer")
        merged_df = pd.merge(merged_df, real_cost_accumulated_df, on="Month", how="outer")
        merged_df = pd.merge(merged_df, executed_activities_df, on="Month", how="outer")
        merged_df = pd.merge(merged_df, executed_activities_monthly_df, on="Month", how="outer")
        merged_df = pd.merge(merged_df, planned_activities_df, on="Month", how="outer")
        merged_df = pd.merge(merged_df, planned_activities_monthly_df, on="Month", how="outer")
        merged_df = pd.merge(merged_df, scheduled_executed_activities_accumulated_df, on="Month", how="outer")
        merged_df = pd.merge(merged_df, scheduled_executed_activities_monthly_df, on="Month", how="outer")
        month_order = [m.lower() for m in month_name[1:]]
        merged_df['Month'] = pd.Categorical(merged_df['Month'].str.lower(), categories=month_order, ordered=True)
        merged_df = merged_df.sort_values('Month').reset_index(drop=True)
        return merged_df

    def get_data_sources(self) -> Dict[str, Any]:
        """Recopila y devuelve un diccionario con todos los DataFrames necesarios para el reporte."""
        return {
            "forecast": self.generate_forecast(),
            "budget": self.generate_budget(),
            "real_cost_accumulated": self.generate_accumulated_real_cost_data_frame(),
            "executed_activities": self.generate_accumulated_executed_activities_data_frame(),
            "executed_activities_monthly": self.generate_executed_activities_data_frame_by_month(),
            "planned_activities": self.generate_accumulated_planned_activities_data_frame(),
            "planned_activities_monthly": self.generate_planned_activities_data_frame_by_month(),
            "scheduled_executed_activities": self.generate_scheduled_executed_activities_accumulated_data_frame(),
            "scheduled_executed_activities_monthly": self.generate_scheduled_executed_activities_by_month(),
            "cpi_spi_info": self.get_cpi_spi_info(),
        } 
    
    
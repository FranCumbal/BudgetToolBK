import pandas as pd
from logic.field_lines.reports.field_report import FieldReport
from services.read_excel import get_data_from_csv
from utils.file_loader import load_field_reports_from_json, load_months_from_file
from utils.file_manager import get_specific_schedule_activities_path, get_varillera_schedule_activities_path

class VarilleraReport(FieldReport):
    """
    Reporte especializado para la línea de servicio 'Varillera'.

    Hereda de FieldReport pero sobrescribe la lógica de generación de proyecciones (forecast)
    para basarse en un archivo CSV de actividades programadas y validadas, en lugar
    de la planificación manual estándar.
    """
    def __init__(self, title: str, service_type: str, zone: str):
        """
        Inicializa una instancia del reporte para Varillera.

        Args:
            title (str): Título o nombre de la línea.
            service_type (str): Tipo de servicio.
            zone (str): Zona geográfica.
        """
        super().__init__(title, service_type, zone, line_type="Varillera")

    def get_data_sources(self) -> dict:
        """
        Sobrescribe el método base para añadir fuentes de datos específicas de Varillera.

        Añade el 'initial_approved_cost' (costo aprobado inicial) solo si el reporte
        corresponde al "ITEM 104 Varillera", manteniendo la flexibilidad para otras líneas.
        """
        sources = super().get_data_sources()
        if self.title == "ITEM 104 Varillera": # Solo varillera tiene eso
            sources["initial_approved_cost"] = self.anual_initial_planned_loader.get_initial_approved_cost_df_to_static_line()
        return sources
    
    # Sobrescribe el método de FieldReport porque es distinta la logica del forecast
    def generate_forecast(self):
        """
        Genera el DataFrame del forecast (proyección) usando la lógica específica de Varillera.

        Sobrescribe el método base para utilizar un cálculo de proyección que combina
        costos reales con costos de actividades programadas desde un archivo CSV.
        """
        return self.get_projected_adjusted_data_frame(self.title)

    def get_projected_adjusted_data_frame(self, line_name):
        """
        Orquesta la generación del forecast y aplica los ajustes finales.

        Primero, genera el DataFrame de costos proyectados y luego utiliza el coordinador
        de actividades para aplicar la lógica de ajuste (reemplazar con costos reales).
        """
        df_projected_cost = self.generate_projected_data_frame(line_name)
        return self.field_activities_coordinator.apply_projected_adjustment_logic(df_projected_cost, line_name)
    
    def get_projected_adjusted_by_month(self, month, line_name):
        """
        Obtiene el valor del forecast ajustado para un mes y línea específicos.
        """
        df_projected_adjusted_cost = self.get_projected_adjusted_data_frame(line_name)
        month = month.lower()
        if month not in df_projected_adjusted_cost["Month"].values:
            raise ValueError(f"Mes '{month}' no encontrado en el DataFrame proyectado.")
        return df_projected_adjusted_cost.loc[df_projected_adjusted_cost["Month"] == month, "Forecast"].values[0]
    
    def generate_projected_data_frame(self, line_name):
        """
        Crea el DataFrame de costos proyectados iniciales mes a mes.

        Para cada mes, combina el costo total de las actividades programadas y validadas
        (desde el CSV) con el costo real ejecutado hasta la fecha.
        """
        months = load_months_from_file()
        real_cost_df = self.generate_real_cost_data_frame(line_name)
        projected_data = []
        for month in months:
            total = self.get_total_scheduled_executed_activities_cost_by_month(month)
            total_real_cost = real_cost_df[real_cost_df["Month"].str.lower() == month.lower()]["TotalRealCost"].values
            projected_data.append({
                "Month": month.lower(),
                "Projected": round(total, 2),
                "TotalRealCost": round(total_real_cost[0], 2) if total_real_cost.size > 0 else 0.0
            })
        df_projected_cost = pd.DataFrame(projected_data)
        return df_projected_cost
    
    def get_total_scheduled_executed_activities_cost_by_month(self, month):
        """
        Calcula el costo total de las actividades programadas y validadas para un mes.

        Suma la columna 'Net Total (USD)' del DataFrame de actividades validadas.
        """
        df_validated = self.get_df_scheduled_executed_activities_validated(month)
        if df_validated.empty:
            return 0.0
        return df_validated['Net Total (USD)'].sum() if 'Net Total (USD)' in df_validated.columns else 0.0
    
    def generate_real_cost_data_frame(self, line_name):
        """
        Obtiene el DataFrame de costos reales por mes.

        Delega la llamada al gestor de actividades ejecutadas.
        """
        return self.executed_activities_manager.generate_real_cost_data_frame(line_name)
    
    def generate_scheduled_executed_activities_accumulated_data_frame(self):
        """
        Genera el DataFrame acumulado de actividades proyectadas (ejecutadas + programadas).

        Sobrescribe el método base para usar una función de acumulación específica
        de Varillera que considera las actividades del archivo CSV.
        """
        df_accumulated_executed_activities = self.generate_accumulated_executed_activities_data_frame()
        last_value = df_accumulated_executed_activities[df_accumulated_executed_activities['Executed Activities'] != 0]['Executed Activities'].iloc[-1] if not df_accumulated_executed_activities[df_accumulated_executed_activities['Executed Activities'] != 0].empty else 0
        last_valid_month = self.executed_activities_manager.get_last_index_month_in_excel()
        df_scheduled_executed_activities = self.get_df_scheduled_executed_activities()
        return self.planned_activities_manager.get_df_scheduled_executed_activities_accumulated_varillera(df_scheduled_executed_activities, last_value, last_valid_month)
    
    def get_df_scheduled_executed_activities(self):
        """
        Genera un DataFrame con el conteo mensual de actividades programadas y validadas.

        Itera sobre cada mes, obtiene las actividades validadas del CSV y cuenta cuántas hay.
        """
        meses = load_months_from_file()
        scheduled_data = []
        for month in meses:
            df = self.get_df_scheduled_executed_activities_validated(month)
            count = len(df)
            scheduled_data.append({
                "Month": month.lower(),
                "Scheduled Activities": count
            })
        scheduled_activities_df = pd.DataFrame(scheduled_data)
        return scheduled_activities_df
    
    def get_df_scheduled_executed_activities_validated(self, month):
        """
        Lee y filtra las actividades programadas desde un archivo CSV para un mes específico.

        Busca el archivo CSV correspondiente a la línea, lo lee, y filtra las filas
        que corresponden al mes solicitado y tienen una validación de 'yes'.
        Maneja de forma segura el caso en que el archivo no exista.
        """
        path = get_specific_schedule_activities_path(self.title)
        df = get_data_from_csv(path)
        #print(f"Reading scheduled activities from: {path}")
        # Si la función de lectura devolvió None o un DataFrame vacío (porque el archivo no existe o está vacío)
        if df is None or df.empty:
            # Devolvemos un DataFrame vacío con la estructura esperada para que el resto del código no falle.
            return pd.DataFrame(columns=['Well', 'Net Total (USD)', 'Validation'])
        df['Scheduled Execution Month'] = df['Scheduled Execution Month'].str.strip().str.lower()
        df['UWI/API'] = df['UWI/API'].astype(str).str.strip()
        df['Validation'] = df['Validation'].str.strip().str.lower()
        filtered_df = df[
            (df['Scheduled Execution Month'] == month.lower()) &
            (df['Validation'] == 'yes')
        ].copy()
        filtered_df['Well'] = filtered_df['UWI/API']
        result_df = filtered_df[['Well', 'Net Total (USD)', 'Validation']]
        return result_df
    
    def generate_scheduled_executed_activities_by_month(self):
        """
        Genera un DataFrame con el conteo mensual de actividades programadas y validadas.

        Sobrescribe el método base para obtener el conteo de actividades desde el CSV.
        """
        meses = load_months_from_file()
        scheduled_data = []
        for month in meses:
            df = self.get_df_scheduled_executed_activities_validated(month)
            count = len(df)
            scheduled_data.append({
                "Month": month.lower(),
                "Scheduled Activities": count
            })
        scheduled_activities_df = pd.DataFrame(scheduled_data)
        return scheduled_activities_df
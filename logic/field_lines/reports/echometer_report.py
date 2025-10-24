import pandas as pd

from logic.field_lines.reports.field_report import FieldReport


class EchometerReport(FieldReport):
    """
    Reporte especializado para la línea de servicio 'Echometer'.

    Hereda de FieldReport y fija el tipo de línea, permitiendo generar
    reportes y análisis de datos específicos para mediciones con Echometer.
    """
    def get_data_sources(self) -> dict:
        """
        Sobrescribe el método base para proporcionar fuentes de datos específicas de Echometer.

        Reemplaza los DataFrames de actividades ejecutadas (mensuales y acumuladas)
        con versiones que leen los datos de una columna específica del Excel,
        adaptándose a la forma en que se registran las actividades de Echometer.
        """
        sources = super().get_data_sources()
        sources["executed_activities"] = self.get_executed_activities_accumulated_df_by_column_from_excel()
        sources["executed_activities_monthly"] = self.get_executed_activities_df_by_column_from_excel_monthly_distributed()
        return sources

    def get_executed_activities_df_by_column_from_excel_monthly_distributed(self) -> pd.DataFrame:
        """
        Obtiene las actividades ejecutadas distribuidas mensualmente desde Excel.

        Utiliza el gestor de actividades ejecutadas para leer los datos de una
        columna específica del archivo Excel y los distribuye por mes.
        """
        meses = self._get_months_data()
        return self.executed_activities_manager.get_executed_activities_df_by_column_from_excel_monthly_distributed(meses, self.title)
    
    def get_executed_activities_accumulated_df_by_column_from_excel(self) -> pd.DataFrame:
        """
        Obtiene el acumulado de actividades ejecutadas desde una columna de Excel.

        Calcula el acumulado mes a mes de las actividades ejecutadas que se
        obtienen de una columna específica del archivo Excel.
        """
        meses = self._get_months_data()
        return self.executed_activities_manager.get_executed_activities_accumulated_df_by_column_from_excel(meses, self.title)
    
    def generate_executed_activities_data_frame_by_month(self):
        """
        Genera el DataFrame de actividades ejecutadas por mes sumando los valores.

        Sobrescribe el método base para utilizar una lógica de suma específica
        para las actividades de Echometer, obteniendo el total mensual.
        """
        meses = self._get_months_data()
        return self.executed_activities_manager._get_executed_activities_sum_by_month(meses, self.title)
    
    def generate_scheduled_executed_activities_accumulated_data_frame(self):
        """
        Genera el DataFrame de actividades proyectadas (ejecutadas + planeadas) acumuladas.

        Sobrescribe el método base para usar el cálculo de actividades ejecutadas
        específico de Echometer como punto de partida para la proyección futura.
        """
        executed_activities_df = self.get_executed_activities_accumulated_df_by_column_from_excel()
        last_value = executed_activities_df[executed_activities_df['Executed Activities'] != 0]['Executed Activities'].iloc[-1] if not executed_activities_df[executed_activities_df['Executed Activities'] != 0].empty else 0
        last_valid_month = self.executed_activities_manager.get_last_index_month_in_excel()
        scheduled_activities_accumulated_df = self.planned_activities_manager.get_df_scheduled_executed_activities_accumulated(self.title, self.service_type, last_value, last_valid_month)
        return scheduled_activities_accumulated_df

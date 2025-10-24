import pandas as pd
from calendar import month_name
from services.field_lines_services.planning_service_factory import PlanningServiceFactory

class LeaderLineService:
    """
    Servicio dedicado a agregar datos de múltiples reportes de campo
    para generar el DataFrame consolidado de la "Línea Líder".
    """
    def __init__(self, all_report_instances: list, completion_service):
        """
        Inicializa el servicio de la Línea Líder.

        Args:
            all_report_instances (list): Una lista que contiene instancias de todos
                                         los reportes de campo disponibles (subclases de FieldReport).
            completion_service: Un objeto de servicio que proporciona la lista de
                                títulos de línea marcados como 'completados' y listos para la agregación.
        """
        self.all_report_instances = all_report_instances
        self.completion_service = completion_service

    def generate_aggregated_dataframe(self) -> pd.DataFrame:
        """
        Agrega los resúmenes mensuales de todos los reportes de campo completados en un único DataFrame.

        Esta es la lógica de negocio principal del servicio. Realiza los siguientes pasos:
        1. Obtiene la lista de títulos de línea 'completados' desde el servicio de completitud.
        2. Filtra las instancias de reporte para incluir solo aquellas que están completadas.
        3. Para cada reporte completado, genera un DataFrame de resumen mensual detallado.
        4. Concatena todos los DataFrames de resumen individuales en un único DataFrame grande.
        5. Agrupa los datos combinados por 'Month' y calcula la suma para todas las columnas numéricas,
           creando así los datos agregados de la línea líder.
        6. Ordena el DataFrame final cronológicamente por mes.

        Returns:
            pd.DataFrame: Un DataFrame que contiene los datos mensuales agregados para la línea líder.
                          Devuelve un DataFrame vacío si no hay líneas completadas o si no se generan resúmenes.
        """
        completed_lines = self.completion_service.get_completed_lines()
        if not completed_lines:
            return pd.DataFrame()
        reports_to_aggregate = [
            report for report in self.all_report_instances
            if report.title in completed_lines
        ]

        all_summaries = []
        for report in reports_to_aggregate:
            summary_df = report.get_monthly_summary_dataframe()
            all_summaries.append(summary_df)

        if not all_summaries:
            return pd.DataFrame()

        combined_df = pd.concat(all_summaries, ignore_index=True)
        aggregated_df = combined_df.groupby("Month", as_index=False).sum(numeric_only=True)

        month_order = [m.lower() for m in month_name[1:]]
        aggregated_df['Month'] = pd.Categorical(aggregated_df['Month'].str.lower(), categories=month_order, ordered=True)
        aggregated_df = aggregated_df.sort_values('Month').reset_index(drop=True)

        return aggregated_df
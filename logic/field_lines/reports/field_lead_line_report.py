import pandas as pd
from services.field_lines_services.field_graph_generator_service import FieldGraphGeneratorService
from calendar import month_name

class FieldLeadLineReport:
    """
    Reporte para la Línea Líder que prepara los datos agregados y genera
    un único gráfico combinado, idéntico a los reportes individuales.
    """
    def __init__(self, aggregated_df: pd.DataFrame, title="Field Leader Line Report"):
        self.title = title
        self.aggregated_df = aggregated_df
        self.graph_service = FieldGraphGeneratorService()

    def get_data_sources(self) -> dict:
        """
        Transforma el DataFrame agregado en el diccionario exacto que el
        servicio de gráficos espera, creando series mensuales y acumuladas.
        """
        df = self.aggregated_df.copy()
        # Asegurarnos de que todas las columnas necesarias existan
        required_cols = [
            "Month", "Planned Activities", "Executed Activities", 
            "Scheduled Activities", "Forecast", "Budget", "RealCost"
        ]
        for col in required_cols:
            if col not in df.columns:
                df[col] = 0
        month_order = [m.lower() for m in month_name[1:]]
        df['Month'] = pd.Categorical(df['Month'].str.lower(), categories=month_order, ordered=True)
        df = df.sort_values('Month')
        return {
            "forecast": df[["Month", "Forecast", "RealCost"]],
            "budget": df[["Month", "Budget"]],
            "real_cost_accumulated": df[["Month", "TotalAccumulatedCost"]],
            "executed_activities": df[["Month", "Executed Activities_x"]].rename(columns={"Executed Activities_x": "Executed Activities"}),
            "executed_activities_monthly": df[["Month", "Executed Activities_y"]].rename(columns={"Executed Activities_y": "Executed Activities"}),
            "planned_activities": df[["Month", "Planned Activities_x"]].rename(columns={"Planned Activities_x": "Planned Activities"}),
            "planned_activities_monthly": df[['Month', 'Planned Activities_y', 'Scheduled Activities', 'Forecast']].rename(columns={"Planned Activities_y": "Planned Activities"}),
            "scheduled_executed_activities": df[["Month", "Scheduled Activities_x"]].rename(columns={"Scheduled Activities_x": "Scheduled Activities"}),
            "scheduled_executed_activities_monthly": df[["Month", "Scheduled Activities_y"]].rename(columns={"Scheduled Activities_y": "Scheduled Activities"}),
        }

    def generate_graph(self):
        """Genera el gráfico combinado a partir de los datos agregados."""
        if self.aggregated_df.empty:
            return None
        return self.graph_service.generate_field_forecast_graph(
            self.title,
            **self.get_data_sources()
        )

    def generate_deviations(self):
        """Para este reporte consolidado, no se calculan desviaciones."""
        return pd.DataFrame()
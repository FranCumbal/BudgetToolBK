import pandas as pd
from calendar import month_name
from .base_planning_service import BasePlanningService

class ScheduleWithoutCategorizerService(BasePlanningService):
    """Servicio para líneas de tipo schedule_without_categorizer"""
    
    def _create_default_dataframe(self):
        """Crea DataFrame con columnas: Month, Planned Activities, Scheduled Activities, Forecast"""
        months = list(month_name)[1:]  # January to December
        return pd.DataFrame({
            "Month": months,
            "Planned Activities": [0] * 12,
            "Scheduled Activities": [0] * 12,  # Enteros para Scheduled Activities
            "Forecast": [0.0] * 12
        })

    def _validate_and_fix_columns(self, df):
        """Valida y agrega columnas faltantes"""
        required_columns = ["Month", "Planned Activities", "Scheduled Activities", "Forecast"]
        
        for col in required_columns:
            if col not in df.columns:
                if col == "Month":
                    df[col] = list(month_name)[1:][:len(df)]
                elif col == "Forecast":
                    df[col] = 0.0
                elif col == "Scheduled Activities":
                    df[col] = 0.0  # Flotante para Scheduled Activities
                else:
                    df[col] = 0
        
        # Reordenar columnas
        df = df[required_columns]
        return df

    def get_editable_columns(self):
        """Planned Activities y Scheduled Activities son editables desde el mes actual"""
        return ["Planned Activities", "Scheduled Activities", "Forecast"]

    def get_columns(self):
        return ["Month", "Planned Activities", "Scheduled Activities", "Forecast"]

    def _post_update_calculations(self, month):
        """Actualiza el Forecast basado en Scheduled Activities y CPAE"""
        pass  # Se calculará desde la vista

    def update_forecast(self, month, cpae_value):
        """Actualiza el forecast para un mes específico"""
        idx = self.dataframe[self.dataframe["Month"] == month].index
        if not idx.empty:
            row_idx = idx[0]
            scheduled = self.dataframe.at[row_idx, "Scheduled Activities"]
            forecast = scheduled * cpae_value
            self.dataframe.at[row_idx, "Forecast"] = round(forecast, 2)

    def get_readonly_columns_before_current_month(self):
        """Retorna columnas que son readonly antes del mes actual"""
        return ["Scheduled Activities"]  # Solo Scheduled Activities y Forecast tienen restricción de mes

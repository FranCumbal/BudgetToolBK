import pandas as pd
from calendar import month_name
from .base_planning_service import BasePlanningService

class ScheduleWithCategorizerService(BasePlanningService):
    """Servicio para líneas de tipo schedule_with_categorizer"""
    
    def _create_default_dataframe(self):
        """Crea DataFrame con columnas: Month, Planned Activities, Scheduled Activities, Category 1, Category 2, Category 3, Forecast"""
        months = list(month_name)[1:]  # January to December
        return pd.DataFrame({
            "Month": months,
            "Planned Activities": [0] * 12,
            "Scheduled Activities": [0] * 12,
            "Category 1": [0] * 12,
            "Category 2": [0] * 12,
            "Category 3": [0] * 12,
            "Forecast": [0.0] * 12
        })

    def _validate_and_fix_columns(self, df):
        """Valida y agrega columnas faltantes"""
        required_columns = ["Month", "Planned Activities", "Scheduled Activities", 
                          "Category 1", "Category 2", "Category 3", "Forecast"]
        
        for col in required_columns:
            if col not in df.columns:
                if col == "Month":
                    df[col] = list(month_name)[1:][:len(df)]
                elif col == "Forecast":
                    df[col] = 0.0
                else:
                    df[col] = 0
        
        # Reordenar columnas
        df = df[required_columns]
        return df

    def get_editable_columns(self):
        """Planned Activities, las categorías y Forecast son editables desde el mes actual"""
        return ["Planned Activities", "Category 1", "Category 2", "Category 3", "Forecast"]

    def get_columns(self):
        return ["Month", "Planned Activities", "Scheduled Activities", 
                "Category 1", "Category 2", "Category 3", "Forecast"]

    def _post_update_calculations(self, month):
        """Calcula automáticamente Scheduled Activities como suma de categorías."""
        idx = self.dataframe[self.dataframe["Month"] == month].index
        if not idx.empty:
            row_idx = idx[0]
            
            try:
                cat1 = int(self.dataframe.at[row_idx, "Category 1"])
                cat2 = int(self.dataframe.at[row_idx, "Category 2"])
                cat3 = int(self.dataframe.at[row_idx, "Category 3"])
            except (ValueError, TypeError):
                print("ERROR")
                cat1, cat2, cat3 = 0, 0, 0

            scheduled_total = cat1 + cat2 + cat3
            self.dataframe.at[row_idx, "Scheduled Activities"] = scheduled_total

    
    def update_forecast(self, month, cat1_value, cat2_value, cat3_value):
        """Actualiza el forecast para un mes específico usando los valores de cada categoría."""
        idx = self.dataframe[self.dataframe["Month"] == month].index
        if not idx.empty:
            row_idx = idx[0]
            
            # --- LÓGICA CORREGIDA ---
            # Nos aseguramos de que las cantidades leídas del DataFrame sean números
            try:
                cat1_qty = int(float(self.dataframe.at[row_idx, "Category 1"]))
                cat2_qty = int(float(self.dataframe.at[row_idx, "Category 2"]))
                cat3_qty = int(float(self.dataframe.at[row_idx, "Category 3"]))
            except (ValueError, TypeError):
                print("ERROR ACA")
                # Si algún valor no es un número, asumimos 0 para evitar errores
                cat1_qty, cat2_qty, cat3_qty = 0, 0, 0

            # Ahora la operación es puramente matemática
            forecast = (cat1_qty * cat1_value) + (cat2_qty * cat2_value) + (cat3_qty * cat3_value)
            self.dataframe.at[row_idx, "Forecast"] = round(forecast, 2)

    def get_readonly_columns_before_current_month(self):
        """Retorna columnas que son readonly antes del mes actual"""
        return ["Category 1", "Category 2", "Category 3"]  # Solo las categorías tienen restricción de mes

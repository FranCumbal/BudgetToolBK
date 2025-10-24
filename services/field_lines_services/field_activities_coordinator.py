from services.field_lines_services.field_graph_generator_service import FieldGraphGeneratorService
import pandas as pd

class FieldActivitiesCoordinator():
    """
    Coordina los datos de actividades planeadas y ejecutadas para generar proyecciones.

    Esta clase actúa como un intermediario entre el `PlannedActivitiesManager` y el
    `ExecutedActivitiesManager` para crear un DataFrame de 'Forecast' que combina
    los costos reales ya incurridos con los costos proyectados para el futuro.
    """
    def __init__(self, planned_activities_manager, executed_activities_manager):
        """
        Inicializa el coordinador.

        Args:
            planned_activities_manager: Gestor de actividades planeadas.
            executed_activities_manager: Gestor de actividades ejecutadas.
        """
        self.planned_activities_manager = planned_activities_manager
        self.executed_activities_manager = executed_activities_manager
        self.graph_service = FieldGraphGeneratorService()
        self.meses_ordenados = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sept', 'oct', 'nov', 'dic']
        self.meses_ingles = ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december']

    def get_projected_adjusted_data_frame(self, line_name, service_type):
        """
        Orquesta la generación del DataFrame de forecast ajustado.

        Primero genera una proyección inicial y luego le aplica la lógica de ajuste
        con los costos reales acumulados.
        """
        df_projected_cost = self.generate_projected_data_frame(line_name, service_type)
        return self.apply_projected_adjustment_logic(df_projected_cost, line_name)

    def apply_projected_adjustment_logic(self, df_projected_cost, line_name):
        """
        Aplica la lógica de ajuste para crear el forecast final acumulado.

        Reemplaza los valores proyectados de los meses pasados con el costo real
        acumulado. Para los meses futuros, continúa la acumulación a partir del
        último costo real, sumando los costos proyectados de cada mes.
        """
        df_real_accumulated_cost = self.executed_activities_manager.generate_accumulated_real_cost_data_frame(line_name)
        df_projected_adjusted_cost = pd.DataFrame({
            "Month": df_projected_cost["Month"],
            "Projected": df_projected_cost["Projected"],
            "RealCost": df_projected_cost["TotalRealCost"]
        })
        df_projected_adjusted_cost["Forecast"] = df_projected_adjusted_cost["Projected"]
        condition = df_projected_adjusted_cost["Projected"] == 0
        df_projected_adjusted_cost.loc[condition, "Forecast"] = df_projected_adjusted_cost.loc[condition, "RealCost"]
        df_projected_adjusted_cost["Forecast ANTERIOR"] = df_projected_adjusted_cost["Forecast"].copy()
        non_zero_accumulated = df_real_accumulated_cost[df_real_accumulated_cost["TotalAccumulatedCost"] != 0]
        
        if len(non_zero_accumulated) > 0:
            last_accumulated_idx = non_zero_accumulated.index[-1]
            for i in range(last_accumulated_idx + 1):
                if df_real_accumulated_cost.iloc[i]["TotalAccumulatedCost"] != 0:
                    df_projected_adjusted_cost.loc[i, "Forecast"] = df_real_accumulated_cost.iloc[i]["TotalAccumulatedCost"]
            last_real_value = df_real_accumulated_cost.iloc[last_accumulated_idx]["TotalAccumulatedCost"]
            
            for i in range(last_accumulated_idx + 1, len(df_projected_adjusted_cost)):
                if df_projected_adjusted_cost.iloc[i]["Projected"] == 0:
                    df_projected_adjusted_cost.loc[i, "Forecast"] = last_real_value
                else:
                    last_real_value += df_projected_adjusted_cost.iloc[i]["Projected"]
                    df_projected_adjusted_cost.loc[i, "Forecast"] = last_real_value
        else:
            df_projected_adjusted_cost["Forecast"] = df_projected_adjusted_cost["Forecast"].cumsum()
        return df_projected_adjusted_cost
    
    def generate_projected_data_frame(self, line_name, service_type):
        """
        Genera un DataFrame de proyección inicial combinando costos reales y planeados.

        Crea una serie de costos mensuales ("Projected") donde:
        - Para los meses con costos reales, se usa el costo real.
        - Para los meses futuros (sin costo real), se usa el forecast inicial
          obtenido del `planned_activities_manager`.
        """
        df_real = self.executed_activities_manager.generate_real_cost_data_frame(line_name)
        df_initial_forecast = self.planned_activities_manager.generate_forecast_from_csv(service_type, line_name)
        df_merged = pd.merge(
            df_real,
            df_initial_forecast,
            on="Month",
            how="left"
        ).fillna(0)  

        non_zero_indices = df_merged[df_merged["TotalRealCost"] != 0].index
        if len(non_zero_indices) > 0:
            last_real_idx = non_zero_indices[-1]
        else:
            last_real_idx = -1  

        projected = []
        for i, row in df_merged.iterrows():
            if i <= last_real_idx:
                projected.append(row["TotalRealCost"])
            else:
                projected.append(row["TotalRealCost"] if row["TotalRealCost"] != 0 else row["Forecast"])
        df_merged["Projected"] = projected
        df_merged["Month"] = pd.Categorical(
            df_merged["Month"], 
            categories=self.meses_ingles, 
            ordered=True
        )
        df_merged = df_merged.sort_values("Month")
        return df_merged
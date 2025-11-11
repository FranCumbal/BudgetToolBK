#tubulars_report

import os
import pandas as pd
from logic.reports.base_report import LineReport
from utils.file_manager import get_catalog_path, get_forecasted_plan_path, get_tubulars_config_path
from services.graph_generator import create_budget_forecast_graph

class TubularsReport(LineReport):
    """
    Reporte para la línea 1.09 Tubulars.

    Características:
    - Usa el plan anual para obtener el número de actividades por mes.
    - Carga un catálogo de costos por actividad y por pie de tubería.
    - Carga un archivo de configuración con pies de tubería usados por mes.
    - Calcula el costo base y el costo variable por pie, y proyecta el forecast mensual.
    - Integra el presupuesto real y exporta los resultados.
    """

    def __init__(self, data_loader, year, operative_capacity, opex_manager, plan_actividades):
        super().__init__(data_loader)
        self.year = year
        self.operative_capacity = pd.DataFrame(operative_capacity)
        self.plan_actividades = plan_actividades
        self.opex_manager = opex_manager
        self.matched_data = None

    def load_catalog(self):
        """Carga el catálogo de costos para Tubulars."""
        catalog_df = self.data_loader.load_catalog_data(get_catalog_path(), sheet_name="Tubulars")
        return catalog_df[catalog_df["line"] == "Tubulars"].copy()

    def load_tubulars_config(self):
        """Carga el archivo de configuración con pies de tubería por mes y tipo."""
        config_path = get_tubulars_config_path()
        if os.path.exists(config_path):
            df = pd.read_excel(config_path)
        else:
            df = pd.DataFrame(columns=["Month", "PipeDesc", "Feet"])

        for col in ["Month", "PipeDesc", "Feet"]:
            if col not in df.columns:
                df[col] = ""
        df["Feet"] = df["Feet"].fillna(0)
        return df

    def generate_forecast(self):
        """
        Genera el forecast mensual para Tubulars:
        - Carga costos fijos por actividad (PER_ACTIVITY) y variables por pie (PER_FT).
        - Calcula el costo total por mes según el plan de actividades y la configuración de pies.
        - Combina con el presupuesto real y exporta el resultado.
        """
        cat_df = self.load_catalog()
        df_services = cat_df[cat_df["cost_type"] == "PER_ACTIVITY"].copy()
        df_tubing = cat_df[cat_df["cost_type"] == "PER_FT"].copy()
        cost_base_services = df_services["cost_value"].sum()

        tuby_config = self.load_tubulars_config()

        def sum_pipe_costs(group):
            total = 0.0
            for _, row in group.iterrows():
                pipe_desc = row["PipeDesc"]
                feet = row["Feet"]
                match = df_tubing[df_tubing["description"] == pipe_desc]
                cost_per_ft = float(match["cost_value"].iloc[0]) if not match.empty else 0.0
                total += cost_per_ft * feet
            return total

        pipe_cost_by_month = tuby_config.groupby("Month").apply(sum_pipe_costs).to_dict()
        sheet_name = f"ForecastedPlan{self.year}"
        forecasted_plan_path = get_forecasted_plan_path(self.year)
        planned_activities_complete_df = self.plan_actividades.data_loader.load_plan_actividades_from_excel(
                forecasted_plan_path,
                sheet_name
        )

        columnas_meses = [c for c in planned_activities_complete_df.columns if c not in ['No.', 'Tipo de Actividad', 'Total']]

        list_provisional = []
        if not planned_activities_complete_df.empty:
            # Renombrar columna 'Total' a 'PLANNED_ACTIVITIES' si existe
            if 'Total' in planned_activities_complete_df.columns:
                planned_activities_complete_df = planned_activities_complete_df.rename(columns={'Total': 'PLANNED_ACTIVITIES'})
            # Sumar actividades por mes (todas las filas) para obtener un df de 12 filas (una por mes)
            meses = [col for col in planned_activities_complete_df.columns if col not in ['No.', 'Tipo de Actividad', 'PLANNED_ACTIVITIES']]
            monthly_totals = {mes: planned_activities_complete_df[mes].sum() for mes in meses}
            forecast_df = pd.DataFrame({
                'MONTH': list(monthly_totals.keys()),
                'PLANNED_ACTIVITIES': list(monthly_totals.values())
            })
            list_provisional = list(monthly_totals.values())
        
        total_por_mes = list_provisional

        forecast_df = pd.DataFrame({"MONTH": columnas_meses})
        forecast_df["PLANNED_ACTIVITIES"] = total_por_mes
        forecast_df["BASE_COST"] = cost_base_services
        forecast_df["PIPE_COST"] = forecast_df["MONTH"].map(pipe_cost_by_month).fillna(0)
        forecast_df["FORECAST_COST"] = (forecast_df["BASE_COST"] * forecast_df["PLANNED_ACTIVITIES"]) + forecast_df["PIPE_COST"]

        budget_df = self.generate_budget().rename(columns={"Budget": "ACTUAL_COST"})
        final_df = forecast_df.merge(budget_df, on="MONTH", how="left")

        final_df["BUDGET"] = final_df["FORECAST_COST"]
        final_df.loc[final_df["ACTUAL_COST"].notna(), "BUDGET"] = final_df["ACTUAL_COST"]
        final_df["CUMULATIVE_FORECAST"] = final_df["BUDGET"].cumsum()

        print("\n=== TUBULARS FORECAST SUMMARY ===")
        print(final_df[[
            "MONTH", "PLANNED_ACTIVITIES", "BASE_COST", "PIPE_COST", "FORECAST_COST",
            "ACTUAL_COST", "BUDGET", "CUMULATIVE_FORECAST"
        ]].to_string(index=False))

        #final_df.to_excel(r"summary/tubulars/tubulars_forecast.xlsx", index=False)
        return final_df

    def generate_budget(self):
        """Carga el presupuesto real para Tubulars."""
        return self.data_loader.load_budget_for_line(self.year, "1.09 Tubulars")

    def generate_deviations(self):
        return pd.DataFrame()

    def generate_plan_data(self, opex_budget: float) -> pd.DataFrame:
        """Distribuye el OPEX en partes iguales a lo largo de los 12 meses."""
        from utils.dates import get_all_months
        months = get_all_months()
        monthly_value = opex_budget / 12
        return pd.DataFrame({"MONTH": months, "PLANNED_COST": [monthly_value] * 12})

    def generate_graph(self, forecast, budget, activities_data):
        """Genera el gráfico para el reporte de Tubulars, incluyendo OPEX plan y capacidad operativa."""
        from utils.dates import get_all_months

        opex_budget = self.opex_manager.get_opex_for_line("1.09 Tubulars")
        plan_data = self.generate_plan_data(opex_budget)

        # 🟢 CAMBIO: Crea las barras de "Forecasted" dinámicamente desde el forecast.
        # Usa la columna 'PLANNED_ACTIVITIES' que en este contexto contiene el forecast.
        capacity_df = forecast[['MONTH', 'PLANNED_ACTIVITIES']].copy()
        capacity_df.rename(columns={'PLANNED_ACTIVITIES': 'FORECASTED_OPEX_ACT'}, inplace=True)

        return create_budget_forecast_graph(
            forecast=forecast,
            budget_data=budget,
            plan_data=plan_data,
            activities_data=activities_data,
            title="1.09 Tubulars",
            capacity_data=capacity_df
        )
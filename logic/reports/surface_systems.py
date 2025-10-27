
import calendar
import pandas as pd
from logic.plan_actividades1 import PlanAnualActividades1
from datetime import datetime

from logic.reports.base_report import LineReport
from utils.dates import get_all_months, get_month_number, normalize_month_names
from logic.activity_mapping import map_services_and_costs
from utils.file_manager import get_catalog_path, get_template_path, get_forecasted_plan_path

class SurfaceSystemsReport(LineReport):
    """
    Reporte para la línea 1.05 Surface Systems (CSUR).

    Genera el forecast mensual basado en:
    - Plan anual de actividades.
    - Mapeo de actividades a servicios usando plantilla y catálogo.
    - Costos por servicio.
    """

    def __init__(self, data_loader, year, operative_capacity, opex_manager, plan_actividades):
        super().__init__(data_loader)
        self.year = year
        self.operative_capacity = operative_capacity
        self.opex_manager = opex_manager
        self.plan_actividades = plan_actividades
        self.line_name = "Surface Systems"

    def generate_forecast(self):
        """Genera el forecast con costos proyectados y reales para Surface Systems."""
        plan_path = get_forecasted_plan_path(self.year)
        plan_provider = PlanAnualActividades1(self.data_loader, plan_path)
        distribucion_df = plan_provider.calcular_distribucion_por_tipo(year=self.year)
        distribucion_df.columns = [
            normalize_month_names(pd.Series([col.strip()])).iloc[0]
            if col.strip() not in ['No.', 'Tipo de Actividad', 'Total'] else col.strip()
            for col in distribucion_df.columns
        ]
        month_names = [m for m in distribucion_df.columns if m not in ['No.', 'Tipo de Actividad', 'Total']]
        month_nums = [get_month_number(m) for m in month_names]

        jobs_expandidos = []
        for _, row in distribucion_df.iterrows():
            tipo = row['No.']
            for month in month_names:
                cantidad = int(row[month]) if pd.notna(row[month]) else 0
                for _ in range(cantidad):
                    jobs_expandidos.append({"activity_type": tipo, "MONTH": month})

        jobs_df = pd.DataFrame(jobs_expandidos)
        if jobs_df.empty:
            print("⚠️ No hay actividades para procesar en Surface Systems")
            return pd.DataFrame()


        # Cargar plantilla y catálogo
        template_df = self.data_loader.load_activities_template(get_template_path())
        catalog_df = self.data_loader.load_catalog_data(get_catalog_path(), self.line_name)
        line_template = template_df[template_df['line'] == self.line_name].copy()
        mapped_df = map_services_and_costs(jobs_df, line_template, catalog_df)

        # Calcular costos por mes
        monthly_df = mapped_df.groupby('MONTH')['CostByService'].sum().reset_index()

        monthly_df.rename(columns={"CostByService": "FORECAST_COST"}, inplace=True)
        monthly_df['month_num'] = monthly_df['MONTH'].apply(get_month_number)

        # Merge con base de meses y budget real
        forecast_df = pd.DataFrame({"MONTH": get_all_months(), "month_num": list(range(1, 13))})
        budget_df = self.generate_budget()
        forecast_df = forecast_df.merge(budget_df, on="MONTH", how="left")
        forecast_df = forecast_df.merge(monthly_df, on="MONTH", how="left")

        forecast_df["FORECAST_COST"] = forecast_df["FORECAST_COST"].fillna(0.0)
        forecast_df.rename(columns={"Budget": "ACTUAL_COST"}, inplace=True)

        forecast_df["BUDGET"] = forecast_df["FORECAST_COST"]
        forecast_df.loc[forecast_df["ACTUAL_COST"].notna(), "BUDGET"] = forecast_df["ACTUAL_COST"]
        forecast_df["CUMULATIVE_FORECAST"] = forecast_df["BUDGET"].cumsum()

        #forecast_df.to_excel("summary/surface_systems/forecast_surface_systems.xlsx", index=False)

        print("\n📊 RESUMEN FORECAST SURFACE SYSTEMS:")
        print(forecast_df[["MONTH", "FORECAST_COST", "ACTUAL_COST", "BUDGET", "CUMULATIVE_FORECAST"]])

        return forecast_df

    def generate_budget(self):
        """Carga el presupuesto real para Surface Systems."""
        return self.data_loader.load_budget_for_line(self.year, "1.5 Surface Systems (CSUR)")

    def generate_plan_data(self, opex_budget: float) -> pd.DataFrame:
        """Distribuye el OPEX uniformemente en 12 meses."""
        months = get_all_months()
        monthly_value = opex_budget / 12
        return pd.DataFrame({"MONTH": months, "PLANNED_COST": [monthly_value] * 12})

    def generate_graph(self, forecast, budget, activities_data):
        """Genera el gráfico forecast vs real vs plan para Surface Systems."""
        from services.graph_generator import create_budget_forecast_graph
        opex_budget = self.opex_manager.get_opex_for_line("1.05 Surface Systems (CSUR)")
        print(f"⚠️ OPEX Budget: {opex_budget}")
        plan_data = self.generate_plan_data(opex_budget)

        cap_df = self.operative_capacity[["Mes", "Numero tentativo de pozos OPEX"]].copy()
        month_map = {i + 1: m for i, m in enumerate(get_all_months())}
        cap_df["MONTH"] = cap_df["Mes"].map(month_map)
        cap_df.rename(columns={"Numero tentativo de pozos OPEX": "FORECASTED_OPEX_ACT"}, inplace=True)
        capacity_df = cap_df[["MONTH", "FORECASTED_OPEX_ACT"]]

        return create_budget_forecast_graph(
            forecast=forecast,
            budget_data=budget,
            plan_data=plan_data,
            activities_data=activities_data,
            title="1.05 Surface Systems (CSUR)",
            capacity_data=capacity_df
        )

    def generate_deviations(self):
        """No se generan desviaciones para este reporte."""
        return pd.DataFrame()

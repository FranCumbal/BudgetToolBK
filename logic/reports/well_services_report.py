import os
import calendar
from datetime import datetime
import pandas as pd

from logic.reports.base_report import LineReport
from utils.dates import normalize_month_names, get_all_months, get_month_number
from logic.activity_mapping import map_services_and_costs
from logic.forecasting import calculate_monthly_costs
from utils.file_manager import get_catalog_path, get_template_path

class WellServicesReport(LineReport):
    """
    Reporte para la línea 1.7 Well Services (WS).

    - Usa el plan anual de actividades.
    - Aplica el catálogo y plantilla para obtener el costo por servicio.
    - Aplica una regla del 70% para "Llenado/Circulación".
    - Retorna DataFrame con columnas estándar para el graficador.
    """

    def __init__(self, data_loader, year, operative_capacity, opex_manager, plan_actividades):
        super().__init__(data_loader)
        self.year = year
        self.operative_capacity = operative_capacity
        self.opex_manager = opex_manager
        self.plan_actividades = plan_actividades
        self.line_filter = "Well Services"

    def generate_forecast(self):
        # 1️⃣ Obtener plan anual distribuido
        distribucion_df = self.plan_actividades.calcular_distribucion_por_tipo(year=self.year)

        # 2️⃣ Normalizar columnas de mes
        distribucion_df.columns = [
            normalize_month_names(pd.Series([col.strip()])).iloc[0]
            if col.strip() not in ['No.', 'Tipo de Actividad', 'Total'] else col.strip()
            for col in distribucion_df.columns
        ]

        # 3️⃣ Verificar columnas válidas de mes
        month_names = [m for m in distribucion_df.columns if m not in ['No.', 'Tipo de Actividad', 'Total']]
        invalids = [m for m in month_names if get_month_number(m) == "Invalid month name"]
        if invalids:
            raise ValueError(f"❌ Nombres de mes no válidos detectados: {invalids}")

        # 4️⃣ Cargar catálogo y plantilla desde utilidades
        template_df = self.data_loader.load_activities_template(get_template_path())
        catalog_df = self.data_loader.load_catalog_data(get_catalog_path(), sheet_name="Well Services")

        # 5️⃣ Filtrar plantilla por línea
        line_template = template_df[template_df['line'] == self.line_filter].copy()

        # 6️⃣ Convertir plan a formato jobs_df
        jobs = []
        for _, row in distribucion_df.iterrows():
            tipo = row['No.']
            for month in month_names:
                count = int(row[month])
                for _ in range(count):
                    jobs.append({"activity_type": tipo, "MONTH": month})

        jobs_df = pd.DataFrame(jobs)
        if jobs_df.empty:
            print("⚠️ No hay actividades planeadas para Well Services.")
            return pd.DataFrame()

        # 7️⃣ Aplicar mapeo de costos por servicio
        mapped_df = map_services_and_costs(jobs_df, line_template, catalog_df)

        # 💡 Regla específica: reducir al 70% el costo del servicio 'Llenado/Circulación'
        mapped_df.loc[
            mapped_df["type"].str.contains("A", case=False, na=False),
            "CostByService"
        ] *= 0.7

        #mapped_df.to_excel("summary/well_services/well_services_activities.xlsx", index=False)

        # 8️⃣ Calcular forecast por mes
        forecast_jobs = calculate_monthly_costs(mapped_df, job_id_col="Job ID")
        forecast_jobs.rename(columns={'Month': 'MONTH', 'budget': 'FORECAST_COST'}, inplace=True)

        # 9️⃣ Crear estructura mensual
        df = pd.DataFrame({
            "MONTH": get_all_months(),
            "month_num": list(range(1, 13))
        })

        df = df.merge(forecast_jobs, on="MONTH", how="left")
        df["FORECAST_COST"] = df["FORECAST_COST"].fillna(0.0)

        # 🔟 Agregar presupuesto real
        budget_df = self.generate_budget()
        df = df.merge(budget_df, on="MONTH", how="left")
        df.rename(columns={"Budget": "ACTUAL_COST"}, inplace=True)

        # 🔁 Sustituir forecast por real si existe
        df["BUDGET"] = df["FORECAST_COST"]
        df.loc[df["ACTUAL_COST"].notna(), "BUDGET"] = df.loc[df["ACTUAL_COST"].notna(), "ACTUAL_COST"]

        df["CUMULATIVE_FORECAST"] = df["BUDGET"].cumsum()

        #df.to_excel("summary/well_services/well_services_forecast.xlsx", index=False)

        print("\n📊 RESUMEN FORECAST WELL SERVICES:")
        print(df[["MONTH", "FORECAST_COST", "ACTUAL_COST", "BUDGET", "CUMULATIVE_FORECAST"]])

        return df

    def generate_budget(self):
        return self.data_loader.load_budget_for_line(self.year, "1.7 Well Services (WS)")

    def generate_plan_data(self, opex_budget: float) -> pd.DataFrame:
        months = get_all_months()
        monthly_value = opex_budget / 12
        return pd.DataFrame({"MONTH": months, "PLANNED_COST": [monthly_value] * 12})

    def generate_graph(self, forecast, budget, activities_data):
        from services.graph_generator import create_budget_forecast_graph
        opex_budget = self.opex_manager.get_opex_for_line("1.07 Well Services (WS)")
        print(f"⚠️ OPEX Budget: {opex_budget}")
        plan_data = self.generate_plan_data(opex_budget)

        # Procesar capacidad operativa
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
            title="1.7 Well Services (WS)",
            capacity_data=capacity_df
        )

    def generate_deviations(self):
        return pd.DataFrame()
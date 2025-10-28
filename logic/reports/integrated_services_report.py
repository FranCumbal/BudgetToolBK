import pandas as pd

from logic.reports.base_report import LineReport
from utils.dates import get_all_months
from utils.file_manager import get_catalog_path, get_forecasted_plan_path

class IntegratedServicesReport(LineReport):
    """
    Reporte para la línea 1.14 Integrated Services Management.

    Calcula el forecast mensual combinando:
    - Costo por día OPEX multiplicado por Total Días OPEX (Service).
    - Costo por día logístico multiplicado por días del mes (Logistics).
    - Usa costos desde el catálogo.
    """

    def __init__(self, data_loader, year, operative_capacity, opex_manager, plan_actividades):
        super().__init__(data_loader)
        self.year = year
        self.operative_capacity = operative_capacity
        self.opex_manager = opex_manager
        self.actual_budget_data = None
        self.service_rate = None
        self.logistics_rate = None
        self.plan_actividades = plan_actividades

    def load_catalog(self):
        """
        Carga las tarifas de SERVICE_RATE y LOGISTICS_RATE desde el catálogo.
        Lanza un error si no se encuentran.
        """
        catalog_df = self.data_loader.load_catalog_data(get_catalog_path(), sheet_name="Integrated Services")
        catalog_df.columns = [col.strip() for col in catalog_df.columns]

        try:
            self.service_rate = catalog_df.loc[catalog_df["Tipo"] == "SERVICE_RATE", "Valor"].values[0]
            self.logistics_rate = catalog_df.loc[catalog_df["Tipo"] == "LOGISTICS_RATE", "Valor"].values[0]
        except IndexError:
            raise ValueError("❌ No se encontraron las tarifas SERVICE_RATE o LOGISTICS_RATE en el catálogo.")

    def generate_forecast(self):
        """
        Genera el forecast mensual para Integrated Services:
        - Calcula costos desde operative_capacity con las tarifas.
        - Ajusta con costos reales si existen.
        - Exporta el resultado a Excel.
        """
        if self.service_rate is None or self.logistics_rate is None:
            self.load_catalog()

        cap_df = pd.DataFrame(self.operative_capacity)
        month_map = {i + 1: m for i, m in enumerate(get_all_months())}
        cap_df["MONTH"] = cap_df["Mes"].map(month_map)

        cap_df["SERVICE_COST"] = cap_df["Total Días OPEX"] * self.service_rate
        cap_df["LOGISTICS_COST"] = cap_df["DíasMes"] * self.logistics_rate
        cap_df["FORECAST_COST"] = cap_df["SERVICE_COST"] + cap_df["LOGISTICS_COST"]

        print("\n📊 RESUMEN FORECAST INTEGRATED SERVICES:")
        print(cap_df[["MONTH", "SERVICE_COST", "LOGISTICS_COST", "FORECAST_COST"]].to_string(index=False))

        df = pd.DataFrame({"MONTH": get_all_months()})
        df = df.merge(cap_df[["MONTH", "FORECAST_COST"]], on="MONTH", how="left")

        budget_df = self.generate_budget().rename(columns={"Budget": "ACTUAL_COST"})
        df = df.merge(budget_df, on="MONTH", how="left")

        df["BUDGET"] = df["FORECAST_COST"]
        df.loc[df["ACTUAL_COST"].notna(), "BUDGET"] = df["ACTUAL_COST"]
        df["CUMULATIVE_FORECAST"] = df["BUDGET"].cumsum()

        #df.to_excel("summary/integrated_services/integrated_services_forecast.xlsx", index=False)
        return df

    def generate_budget(self):
        """Carga el budget real para Integrated Services."""
        return self.data_loader.load_budget_for_line(self.year, "1.14 Integrated Services Management")

    def generate_plan_data(self, opex_budget: float) -> pd.DataFrame:
        """Distribuye el OPEX uniformemente en 12 meses."""
        months = get_all_months()
        monthly_value = opex_budget / 12
        return pd.DataFrame({"MONTH": months, "PLANNED_COST": [monthly_value] * 12})

    def get_total_activities(self):
        sheet_name = f"ForecastedPlan{self.year}"
        forecasted_plan_path = get_forecasted_plan_path(self.year)
        planned_activities_complete_df = self.plan_actividades.data_loader.load_plan_actividades_from_excel(
                forecasted_plan_path,
                sheet_name
        )
        list_provisional = []
        if not planned_activities_complete_df.empty:
            planned_activities_complete_df = planned_activities_complete_df.rename(columns={'Total': 'PLANNED_ACTIVITIES'})
            # Sumar actividades por mes (todas las filas) para obtener un df de 12 filas (una por mes)
            meses = [col for col in planned_activities_complete_df.columns if col not in ['No.', 'Tipo de Actividad', 'PLANNED_ACTIVITIES']]
            monthly_totals = {mes: planned_activities_complete_df[mes].sum() for mes in meses}
            
            list_provisional = list(monthly_totals.values())
        month_names = [m for m in planned_activities_complete_df.columns if m not in ['No.', 'Tipo de Actividad', 'PLANNED_ACTIVITIES']]
        total_activities_by_month = list_provisional if list_provisional else [0] * len(month_names)
        df_activities = pd.DataFrame({
            "MONTH": month_names,
            "TOTAL_ACTIVITIES": total_activities_by_month,
        })
        return df_activities

    def generate_graph(self, forecast, budget, activities_data):
        """
        Genera el gráfico forecast vs real vs plan para Integrated Services.
        Incluye presupuesto, forecast, plan y capacidad operativa.
        """
        from services.graph_generator import create_budget_forecast_graph

        opex_budget = self.opex_manager.get_opex_for_line("1.14 Integrated Services Management")
        print(f"⚠️ OPEX Budget: {opex_budget}")
        plan_data = self.generate_plan_data(opex_budget)

        capacity_df = self.get_total_activities()
        capacity_df.rename(columns={'TOTAL_ACTIVITIES': 'FORECASTED_OPEX_ACT'}, inplace=True)

        return create_budget_forecast_graph(
            forecast=forecast,
            budget_data=budget,
            plan_data=plan_data,
            activities_data=activities_data,
            title="1.14 Integrated Services Management",
            capacity_data=capacity_df
        )

    def generate_deviations(self):
        """No se generan desviaciones para este reporte."""
        return pd.DataFrame()

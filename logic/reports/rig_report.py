import pandas as pd
from logic.reports.base_report import LineReport
from utils.dates import  get_all_months
from utils.file_manager import get_forecasted_plan_path

class RigReport(LineReport):
    """
    Reporte para la línea 1.01 WI RIG.
    Calcula el forecast de costos por mes utilizando tarifas promedio y capacidad operativa.
    """

    def __init__(self, data_loader, year, merged_opex_data, operative_capacity, opex_manager, plan_actividades):
        super().__init__(data_loader)
        self.year = year
        self.merged_opex_data = merged_opex_data
        self.operative_capacity = operative_capacity
        self.opex_manager = opex_manager
        self.actual_budget_data = None
        self.plan_actividades = plan_actividades

    def generate_forecast(self):
        """
        Genera el forecast mensual basado en las tarifas promedio de rigs y los días OPEX.
        """
        df_rates = self.data_loader.load_rig_rates()
        df_avg = df_rates.mean(numeric_only=True)

        daily_operating_rate = df_avg["daily_operating_rate_hr"]
        standby_rate_crew = df_avg["standby_rate_crew_hr"]
        rig_move_10_20km = df_avg["rig_move_10_20km"]
        extras_per_job = df_avg["extras_per_job"]

        rig = pd.DataFrame(self.operative_capacity)
        month_map = {i + 1: m for i, m in enumerate(get_all_months())}
        rig["MONTH"] = rig["Mes"].map(month_map)

        rig["DiasOPEX"] = rig["Total Días OPEX"]
        rig["Movilizaciones"] = rig["DiasOPEX"] / 8.9

        rig["COST_STANDBY"] = rig["Movilizaciones"] * 12 * standby_rate_crew
        rig["COST_OPER"] = (
            (daily_operating_rate * 24) * (rig["DiasOPEX"] - (rig["Movilizaciones"] * 1.5)) +
            (extras_per_job * rig["Movilizaciones"]) +
            (rig["DiasOPEX"] * 1045) +
            (3000 * rig["Movilizaciones"]) +
            (60 * rig["DiasOPEX"])
        )
        rig["COST_MOB"] = rig["Movilizaciones"] * rig_move_10_20km

        rig["FORECAST_COST"] = rig["COST_STANDBY"] + rig["COST_OPER"] + rig["COST_MOB"]

        summary_cols = [
            "MONTH", "DiasOPEX", "Movilizaciones",
            "COST_STANDBY", "COST_OPER", "COST_MOB", "FORECAST_COST"
        ]
        summary_df = rig[summary_cols].copy()
        print("\n=== RIG FORECAST SUMMARY ===")
        print(summary_df.to_string(index=False))

        month_order = get_all_months()
        all_months_df = pd.DataFrame({"MONTH": month_order})
        forecast_df = all_months_df.merge(
            rig[["MONTH", "FORECAST_COST"]], on="MONTH", how="left"
        )
        forecast_df["FORECAST_COST"] = forecast_df["FORECAST_COST"].fillna(0)

        budget_df = self.generate_budget().rename(columns={"MONTH": "MONTH", "Budget": "ACTUAL_COST"})
        final_df = forecast_df.merge(budget_df, on="MONTH", how="left")

        final_df["BUDGET"] = final_df.apply(
            lambda row: row["ACTUAL_COST"] if pd.notna(row["ACTUAL_COST"]) else row["FORECAST_COST"], axis=1
        )
        final_df["CUMULATIVE_FORECAST"] = final_df["BUDGET"].cumsum()

        print("\n=== RIG FORECAST FINAL ===")
        print(final_df.to_string(index=False))

        return final_df

    def generate_plan_data(self, opex_budget: float) -> pd.DataFrame:
        """
        Genera un DataFrame con el costo mensual uniforme basado en el OPEX anual.
        """
        months = get_all_months()
        monthly_value = opex_budget / 12
        return pd.DataFrame({"MONTH": months, "PLANNED_COST": [monthly_value] * 12})

    def load_and_match_data(self):
        """
        Carga el presupuesto real para la línea '1.1 WI Rig' si aún no está cacheado.
        """
        if self.actual_budget_data is None:
            self.actual_budget_data = self.data_loader.load_budget_for_line(self.year, "1.1 WI Rig")
        self.actual_budget_data = self.actual_budget_data.rename(columns={"MONTH": "MONTH", "Budget": "ACTUAL_COST"})
        return self.actual_budget_data

    def generate_budget(self):
        """
        Carga los costos reales registrados para la línea.
        """
        return self.data_loader.load_budget_for_line(self.year, "1.1 WI RIG")

    def generate_deviations(self):
        return pd.DataFrame()

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
        Genera el gráfico comparativo Forecast vs Real vs Plan.
        """
        from services.graph_generator import create_budget_forecast_graph
        opex_budget = self.opex_manager.get_opex_for_line("1.01 WI RIG")
        print(f"⚠️ OPEX Budget: {opex_budget}")
        plan_data = self.generate_plan_data(opex_budget)

        capacity_df = self.get_total_activities()
        capacity_df.rename(columns={'TOTAL_ACTIVITIES': 'FORECASTED_OPEX_ACT'}, inplace=True)

        return create_budget_forecast_graph(
            forecast=forecast,
            budget_data=budget,
            plan_data=plan_data,
            activities_data=activities_data,
            title="1.01 WI Rig",
            capacity_data=capacity_df
        )

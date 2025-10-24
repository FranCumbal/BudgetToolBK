import pandas as pd
from logic.reports.base_report import LineReport
from utils.dates import  get_all_months

class RigReport(LineReport):
    """
    Reporte para la línea 1.01 WI RIG.
    Calcula el forecast de costos por mes utilizando tarifas promedio y capacidad operativa.
    """

    def __init__(self, data_loader, year, merged_opex_data, operative_capacity, opex_manager):
        super().__init__(data_loader)
        self.year = year
        self.merged_opex_data = merged_opex_data
        self.operative_capacity = operative_capacity
        self.opex_manager = opex_manager
        self.actual_budget_data = None

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

    def generate_graph(self, forecast, budget, activities_data):
        """
        Genera el gráfico comparativo Forecast vs Real vs Plan.
        """
        from services.graph_generator import create_budget_forecast_graph
        opex_budget = self.opex_manager.get_opex_for_line("1.01 WI RIG")
        print(f"⚠️ OPEX Budget: {opex_budget}")
        plan_data = self.generate_plan_data(opex_budget)

        capacity_df = self.operative_capacity[["Mes", "Numero tentativo de pozos OPEX"]].copy()
        month_map = {i + 1: m for i, m in enumerate(get_all_months())}
        capacity_df["MONTH"] = capacity_df["Mes"].map(month_map)
        capacity_df.rename(columns={"Numero tentativo de pozos OPEX": "FORECASTED_OPEX_ACT"}, inplace=True)
        capacity_df = capacity_df[["MONTH", "FORECASTED_OPEX_ACT"]]

        return create_budget_forecast_graph(
            forecast=forecast,
            budget_data=budget,
            plan_data=plan_data,
            activities_data=activities_data,
            title="1.01 WI Rig",
            capacity_data=capacity_df
        )

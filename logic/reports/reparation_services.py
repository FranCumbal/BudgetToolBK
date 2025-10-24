from pandas import pd
from logic.reports.base_report import LineReport
from utils.dates import normalize_month_names, get_month_number, get_all_months


class ReparationServicesReport(LineReport):
    def __init__(self, data_loader, year, operative_capacity, opex_manager, plan_actividades, file_manager):
        super().__init__(data_loader)
        self.year = year
        self.operative_capacity = operative_capacity
        self.catalog = None
        self.opex_manager = opex_manager
        self.plan_actividades = plan_actividades
        self.file_manager = file_manager
    
    def generate_forecast(self):
        """
        Genera el forecast mensual basado en el plan anual y las reglas del catálogo.
        """
        plan_df = self.plan_actividades.calcular_distribucion_por_tipo(year=self.year)
        

        pass

    def get_activities_executed_by_month_data(self):
        df = self.file_manager.get_reparation_services_path()
        df['Month'] = df['Month'].str.strip()
        conteo_mensual = df.groupby('Month')['ITEM 104 Std. Valve'].count()
        df_act_executed = df_act_executed.rename(columns={"ITEM 104 Std. Valve": "ACTIVITIES_EXECUTED"})
        df_act_executed = conteo_mensual.to_frame().T
        return df_act_executed
    
    def generate_budget(self):
        """
        Carga los costos reales desde los datos del plan anual.
        """
        return self.data_loader.load_budget_for_line(self.year, "1.6 Wireline")

    def generate_graph(self, forecast, budget, activities_data):
        """
        Genera el gráfico de comparación Forecast vs Real vs Plan.
        """
        from services.graph_generator import create_budget_forecast_graph
        opex_budget = self.opex_manager.get_opex_for_line("1.06 Wireline")
        print(f"⚠️ OPEX Budget: {opex_budget}")
        plan_data = self.generate_plan_data(opex_budget)

        capacity_df = self.operative_capacity[["Mes", "Numero tentativo de pozos OPEX"]].copy()
        from utils.dates import get_all_months
        month_map = {i + 1: m for i, m in enumerate(get_all_months())}
        capacity_df["MONTH"] = capacity_df["Mes"].map(month_map)
        capacity_df.rename(columns={"Numero tentativo de pozos OPEX": "FORECASTED_OPEX_ACT"}, inplace=True)
        capacity_df = capacity_df[["MONTH", "FORECASTED_OPEX_ACT"]]

        return create_budget_forecast_graph(
            forecast=forecast,
            budget_data=budget,
            plan_data=plan_data,
            activities_data=activities_data,
            title="1.6 Wireline",
            capacity_data=capacity_df
        )
    

    
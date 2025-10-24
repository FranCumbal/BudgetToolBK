
import pandas as pd
from logic.avg_activity_gestor import AvgActivityGestor
from logic.reports.base_report import LineReport
from utils.dates import get_all_months
import os

from utils.file_manager import get_forecasted_plan_path, get_planning_cost_by_line_path

class TanksAndTrunksReport(LineReport):
    """
    Reporte para la línea 1.15 Tanks and Trunks.

    Genera el forecast mensual:
    - Usa el número total de actividades del plan.
    - Asume un costo promedio por actividad.
    - Sobrescribe con presupuesto real si existe.
    - Renombra columnas para graficador.
    """

    DEFAULT_CAPEX_VALUE = 33000  # Valor promedio por actividad
    avg_activity_gestor = AvgActivityGestor()

    def __init__(self, data_loader, year, operative_capacity, opex_manager, plan_actividades):
        super().__init__(data_loader)
        self.year = year
        self.operative_capacity = operative_capacity
        self.opex_manager = opex_manager
        self.plan_actividades = plan_actividades
        self.line_name = "1.15 Tanks and Trunks"

    def generate_forecast(self):
        """
        Genera el forecast mensual para Tanks and Trunks:
        - Recupera meses con actividades CAPEX desde Cognite (vía fetch_capex_activities_for_year).
        - No distribuye actividades en esos meses.
        - Distribuye el total del plan solo en meses libres.
        - Calcula el costo proyectado, sobrescribe con real si existe, y acumula el presupuesto.
        """
        sheet_name = f"ForecastedPlan{self.year}"
        forecasted_plan_path = get_forecasted_plan_path(self.year)
        planned_activities_by_month_df = self.plan_actividades.data_loader.get_total_activities_by_month_df_from_plan(forecasted_plan_path, sheet_name)
        planned_activities_by_month_df["month_num"] = list(range(1, 13)) 
        print("LO QUE TRAIGO")
        print(planned_activities_by_month_df)
        cpae_avg = self.avg_activity_gestor.get_avrg_by_type_and_range(min_value=1, max_value=2000, line_name=self.line_name)
        print("Promedio filtrado:")
        print(cpae_avg)

        # 1️⃣ Obtener actividades CAPEX desde CDF y extraer meses | Esto que hizo Nardy, queda despreciado con lo que me dijo Luis Toledo que queria colocar lo Capex
        '''df_capex = self.data_loader.fetch_capex_activities_for_year(self.year)
        if not df_capex.empty:
            meses_capex = df_capex['End'].dt.month.unique().tolist()
            print(f"🛑 Meses con actividades CAPEX desde CDF: {meses_capex}")
        else:
            meses_capex = []
        
        meses_capex.append(10)'''
        meses_capex= self.data_loader.get_capex_yes_month_indices()

        # Calcular los costos a traves de la logica de Luis con las actividades capex
        planned_activities_by_month_df.rename(columns={"PLANNED_ACTIVITIES": "FORECASTED_ACTIVITIES"}, inplace=True) # Son forecasteadas, no planificadas

        planned_activities_by_month_df["FORECAST_COST"] = (
            planned_activities_by_month_df["FORECASTED_ACTIVITIES"] * cpae_avg +
            planned_activities_by_month_df["month_num"].apply(lambda m: self.DEFAULT_CAPEX_VALUE if m not in meses_capex else 0)
        )
        print("Costos pronosticados:")
        print(planned_activities_by_month_df[["MONTH", "FORECAST_COST"]])

        budget_df = self.generate_budget()
        planned_activities_by_month_df = planned_activities_by_month_df.merge(budget_df, on="MONTH", how="left")
        planned_activities_by_month_df.rename(columns={"Budget": "ACTUAL_COST"}, inplace=True)

        planned_activities_by_month_df["BUDGET"] = planned_activities_by_month_df["FORECAST_COST"]
        planned_activities_by_month_df.loc[planned_activities_by_month_df["ACTUAL_COST"].notna(), "BUDGET"] = planned_activities_by_month_df["ACTUAL_COST"]
        planned_activities_by_month_df["CUMULATIVE_FORECAST"] = planned_activities_by_month_df["BUDGET"].cumsum()

        print("\n📊 RESUMEN FORECAST TANKS & TRUNKS:")
        print(planned_activities_by_month_df[["MONTH", "FORECASTED_ACTIVITIES", "FORECAST_COST", "ACTUAL_COST", "BUDGET", "CUMULATIVE_FORECAST"]])

        return planned_activities_by_month_df


    def generate_budget(self):
        """Carga el presupuesto real para Tanks and Trunks."""
        return self.data_loader.load_budget_for_line(self.year, "1.15 Tanks and Trunks")
    
    def generate_plan_cost_logic(self):
        activities_by_month_df = self.data_loader.get_total_activities_by_month_df_from_plan(
            self.plan_actividades.plan_path,
            self.plan_actividades.sheet_name
        )
        activities_by_month_df["month_num"] = list(range(1, 13))

        cpae_avg = self.avg_activity_gestor.get_avrg_by_type_and_range(min_value=1, max_value=2000, line_name=self.line_name)
        # MESES CAPEX
        meses_capex= self.data_loader.get_capex_yes_month_indices()
        # Si un mes es actividad CAPEX se le coloca 33000, sino, se multiplica las PLANNED_ACTIVITIES * cpae_avg
        activities_by_month_df["PLANNED_COST"] = activities_by_month_df.apply(
            lambda row: 33000 if row["month_num"] in meses_capex else row["PLANNED_ACTIVITIES"] * cpae_avg,
            axis=1
        )
        return activities_by_month_df[["MONTH", "PLANNED_COST"]]


    def generate_plan_data(self, opex_budget: float) -> pd.DataFrame:
        planificacion_manual = get_planning_cost_by_line_path(self.line_name, self.year)
        manual_planning_df = pd.read_excel(planificacion_manual)
        manual_planning_df.rename(columns={"Costo de Plan": "PLANNED_COST"}, inplace=True)
        manual_planning_df.rename(columns={"Mes": "MONTH"}, inplace=True)
        if manual_planning_df.empty: 
            return self.generate_plan_cost_logic()
        return manual_planning_df[["MONTH", "PLANNED_COST"]]

    def generate_graph(self, forecast, budget, activities_data):
        """Genera el gráfico para Tanks and Trunks."""
        from services.graph_generator import create_budget_forecast_graph
        opex_budget = self.opex_manager.get_opex_for_line("1.15 Tanks and Trunks")
        plan_data = self.generate_plan_data(opex_budget)

        # 🟢 CAMBIO: Crea las barras de "Forecasted" dinámicamente desde el forecast.
        # La columna 'FORECASTED_ACTIVITIES' ya contiene los datos que necesitamos.
        capacity_df = forecast[['MONTH', 'FORECASTED_ACTIVITIES']].copy()
        capacity_df.rename(columns={"FORECASTED_ACTIVITIES": "FORECASTED_OPEX_ACT"}, inplace=True)

        return create_budget_forecast_graph(
            forecast=forecast,
            budget_data=budget,
            plan_data=plan_data,
            activities_data=activities_data,
            title="1.15 Tanks and Trunks",
            capacity_data=capacity_df
        )

    def generate_deviations(self):
        """No se calculan desviaciones para este reporte."""
        return pd.DataFrame()

import os
import calendar
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from logic.avg_activity_gestor import AvgActivityGestor
from logic.reports.base_report import LineReport
from utils.dates import get_all_months, normalize_month_names
from logic.budget_analysis import group_by_month
from utils.file_manager import get_forecasted_plan_path, get_planning_cost_by_line_path


class TestingFluidAnalysisReport(LineReport):
    """
    Reporte para la línea 1.8 Testing & Fluid Analysis.

    Características principales:
    - Se calcula el forecast basado en actividades TCP (C1.3) y normales.
    - Se evita asignar costos en meses con actividades CAPEX.
    - Integra presupuesto real para consolidar el presupuesto final.
    """

    def __init__(self, data_loader, year, operative_capacity, opex_manager, plan_actividades):
        super().__init__(data_loader)
        self.year = year
        self.operative_capacity = operative_capacity
        self.opex_manager = opex_manager
        self.plan_actividades = plan_actividades
        self.line_name = '1.8 Testing & Fluid Analysis'

    def generate_forecast(self):
        """Genera el forecast mensual para Testing & Fluid Analysis."""
        # Obtener meses donde hay actividades CAPEX
        avg_normal, avg_tcp = self.get_average_costs()
        # Preparar DataFrame inicial de forecast
        meses = get_all_months()
        forecast_df = pd.DataFrame({"MONTH": meses, "FORECAST_COST": 0.0})
        # Contar actividades TCP y normales desde el plan de forecast
        tcp_counts, normal_counts = self.count_activities_from_forecast_plan()
        total_activities = {m: tcp_counts.get(m, 0) + normal_counts.get(m, 0) for m in meses}
        
        tcp_counts_df = pd.DataFrame(list(tcp_counts.items()), columns=["MONTH", "TCP_ACTIVITIES"])
        total_activities_df = pd.DataFrame(list(total_activities.items()), columns=["MONTH", "TOTAL_ACTIVITIES"]) # Crea un DF para el total
        
        forecast_df = forecast_df.merge(tcp_counts_df, on="MONTH", how="left")
        forecast_df = forecast_df.merge(total_activities_df, on="MONTH", how="left") # Une el total al DF principal
        
        forecast_df["FORECAST_COST"] = forecast_df["TCP_ACTIVITIES"] * avg_tcp

        # Cargar presupuesto real y combinar
        budget_df = self.generate_budget()
        forecast_df = forecast_df.merge(budget_df, on="MONTH", how="left").rename(columns={"Budget": "ACTUAL_COST"})

        # Definir BUDGET final
        forecast_df["BUDGET"] = forecast_df["FORECAST_COST"]
        forecast_df.loc[forecast_df["ACTUAL_COST"].notna(), "BUDGET"] = forecast_df["ACTUAL_COST"]
        forecast_df["CUMULATIVE_FORECAST"] = forecast_df["BUDGET"].cumsum()

        print("\n📊 RESUMEN FORECAST TESTING & FLUID ANALYSIS:")
        print(forecast_df[["MONTH", "FORECAST_COST", "ACTUAL_COST", "BUDGET", "CUMULATIVE_FORECAST"]])
        return forecast_df

    def get_capex_months(self): #Con lo que me dijo Luis, esto queda despreciable
        """Obtiene los meses donde hay actividades CAPEX."""
        capex_df = self.data_loader.fetch_capex_activities_for_year(self.year)
        return set(capex_df['End'].dt.month.unique()) if not capex_df.empty else set()

    def get_average_costs(self):
        """Calcula el costo promedio histórico de actividades normales y TCP."""
        avg_gestor = AvgActivityGestor()
        df_all = avg_gestor.generate_report_execution_dataframe_by_line(self.line_name)
        if self.line_name not in df_all.columns:
            return 0, 0

        df_normal = df_all[~df_all['TYPE'].str.contains("TCP", case=False, na=False)].copy()
        df_normal = df_normal[df_normal[self.line_name] < 20000] # el 20000 es el valor maximo para la estadistica, segun Luis.
        df_tcp = df_all[df_all['TYPE'].str.contains("TCP", case=False, na=False)].copy()

        avg_normal = df_normal[self.line_name].mean() or 0
        avg_tcp = df_tcp[self.line_name].mean() or 0

        return avg_normal, avg_tcp

    def count_activities_from_forecast_plan(self):
        """Cuenta actividades TCP y normales a partir del plan anual."""
        sheet_name = f"ForecastedPlan{self.year}"
        forecasted_plan_path = get_forecasted_plan_path(self.year)
        planned_activities_complete_df = self.plan_actividades.data_loader.load_plan_actividades_from_excel(
                forecasted_plan_path,
                sheet_name
        )
        planned_activities_complete_df.columns = [normalize_month_names(pd.Series([c])).iloc[0] if c not in ["No.", "Tipo de Actividad", "Total"] else c for c in planned_activities_complete_df.columns]
        month_names = [m for m in planned_activities_complete_df.columns if m not in ['No.', 'Tipo de Actividad', 'Total']]

        tcp_counts = {m: 0 for m in get_all_months()}
        normal_counts = {m: 0 for m in get_all_months()}

        for _, row in planned_activities_complete_df.iterrows():
            tipo = row['No.']
            for mes in month_names:
                cantidad = int(row[mes]) if pd.notna(row[mes]) else 0
                if tipo == "C1.3":
                    tcp_counts[mes] += cantidad
                else:
                    normal_counts[mes] += cantidad
        return tcp_counts, normal_counts
    
    def count_activities_from_plan(self):
        planned_activities_complete_df = self.plan_actividades.data_loader.load_plan_actividades_from_excel(
                self.plan_actividades.plan_path,
                self.plan_actividades.sheet_name
        )
        planned_activities_complete_df.columns = [normalize_month_names(pd.Series([c])).iloc[0] if c not in ["No.", "Tipo de Actividad", "Total"] else c for c in planned_activities_complete_df.columns]
        month_names = [m for m in planned_activities_complete_df.columns if m not in ['No.', 'Tipo de Actividad', 'Total']]

        tcp_counts = {m: 0 for m in get_all_months()}
        normal_counts = {m: 0 for m in get_all_months()}

        for _, row in planned_activities_complete_df.iterrows():
            tipo = row['No.']
            for mes in month_names:
                cantidad = int(row[mes]) if pd.notna(row[mes]) else 0
                if tipo == "C1.3":
                    tcp_counts[mes] += cantidad
                else:
                    normal_counts[mes] += cantidad
        return tcp_counts, normal_counts

    def generate_budget(self):
        """Carga el presupuesto real de Testing & Fluid Analysis."""
        return self.data_loader.load_budget_for_line(self.year, "1.8 Testing & Fluid Analysis")


    def generate_plan_cost_logic(self):
        tcp_counts, normal_counts = self.count_activities_from_plan()
        tcp_counts_df = pd.DataFrame(list(tcp_counts.items()), columns=["MONTH", "TCP_ACTIVITIES"])
        # Recupero las actividades planificadas
        activities_by_month_df = self.data_loader.get_total_activities_by_month_df_from_plan(
            self.plan_actividades.plan_path,
            self.plan_actividades.sheet_name
        )
        activities_by_month_df["month_num"] = list(range(1, 13))
        #recupero los promedios 
        avg_normal, avg_tcp = self.get_average_costs()
        # Aplicamos la logica que sigue Luis (Si hay actividades TCP se multiplica las actividades planeadas en ese mes por el avg_normal y se le suma el avg_tcp)
        planned_cost_df = pd.DataFrame()
        planned_cost_df = activities_by_month_df.merge(tcp_counts_df, on="MONTH", how="left")
        planned_cost_df["TCP_ACTIVITIES"].fillna(0, inplace=True)
        planned_cost_df["PLANNED_COST"] = np.where(
            planned_cost_df["TCP_ACTIVITIES"] > 0,
            planned_cost_df["PLANNED_ACTIVITIES"] * avg_normal + avg_tcp,
            planned_cost_df["PLANNED_ACTIVITIES"] * avg_normal
        )
        return planned_cost_df[["MONTH", "PLANNED_COST"]]

    def generate_plan_data(self, opex_budget: float) -> pd.DataFrame:
        # Recupero los meses que tuvieron TCP
        planificacion_manual = get_planning_cost_by_line_path("1.08 Testing and Fluid Analysis", self.year) #correccion ya que mapearon mal los nombres, sin estadares aplicados
        manual_planning_df = pd.read_excel(planificacion_manual)
        manual_planning_df.rename(columns={"Costo de Plan": "PLANNED_COST"}, inplace=True)
        manual_planning_df.rename(columns={"Mes": "MONTH"}, inplace=True)
        if manual_planning_df.empty: # Esto es para mantener lo que se tenia anteriormente, por si algo falla (genera una linea lineal en la grafica)
            return self.generate_plan_cost_logic()
        return manual_planning_df[["MONTH", "PLANNED_COST"]]
        

    def generate_graph(self, forecast, budget, activities_data):
        """Genera el gráfico Forecast vs Real vs Plan para Testing & Fluid Analysis."""
        from services.graph_generator import create_budget_forecast_graph

        opex_budget = self.opex_manager.get_opex_for_line("1.08 Testing & Fluid Analysis")
        plan_data = self.generate_plan_data(opex_budget)

        # 🟢 CAMBIO: Crea las barras de "Forecasted" dinámicamente desde el forecast.
        capacity_df = forecast[['MONTH', 'TOTAL_ACTIVITIES']].copy()
        capacity_df.rename(columns={'TOTAL_ACTIVITIES': 'FORECASTED_OPEX_ACT'}, inplace=True)

        return create_budget_forecast_graph(
            forecast=forecast,
            budget_data=budget,
            plan_data=plan_data,
            activities_data=activities_data,
            title="1.08 Testing & Fluid Analysis",
            capacity_data=capacity_df
        )

    def generate_deviations(self):
        """Este reporte no calcula desviaciones."""
        return pd.DataFrame()

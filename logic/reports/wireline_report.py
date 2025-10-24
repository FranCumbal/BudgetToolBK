
import calendar
import pandas as pd
import json
import os

from logic.avg_activity_gestor import AvgActivityGestor
from logic.reports.base_report import LineReport
from utils.dates import normalize_month_names, get_month_number, get_all_months
from utils.file_manager import get_catalog_path, get_forecasted_plan_path, get_planning_cost_by_line_path

class WirelineReport(LineReport):
    """
    Reporte para la línea 1.6 Wireline.

    Genera el forecast mensual basado en el plan anual de actividades y
    el catálogo de costos promedio por tipo de actividad.
    """

    def __init__(self, data_loader, year, operative_capacity, opex_manager, plan_actividades):
        super().__init__(data_loader)
        self.year = year
        self.operative_capacity = operative_capacity
        self.catalog = None
        self.opex_manager = opex_manager
        self.plan_actividades = plan_actividades
        self.line_name = '1.6 Wireline'

    def load_catalog(self):
        """
        Carga el catálogo de costos promedio para Wireline.
        """
        catalog_df = self.data_loader.load_catalog_data(
            get_catalog_path(), sheet_name="Wireline"
        )

        self.catalog = [
            {
                "name": row["Actividad"],
                "cost": row["Costo Promedio ($)"],
                "rule_type": row.get("rule_type", ""),
                "activity_type": row.get("activity_type"),
                "ratio": row.get("ratio"),
                "multiplier": row.get("multiplier")
            }
            for _, row in catalog_df.iterrows()
        ]
        return self.catalog

    def generate_forecast(self):
        """
        Genera el forecast mensual basado en el plan anual y las reglas del catálogo.
        """
        sheet_name = f"ForecastedPlan{self.year}"
        forecasted_plan_path = get_forecasted_plan_path(self.year)
        planned_activities_complete_df = self.plan_actividades.data_loader.load_plan_actividades_from_excel(
                forecasted_plan_path,
                sheet_name
        )

        month_names = [m for m in planned_activities_complete_df.columns if m not in ['No.', 'Tipo de Actividad', 'Total']]
        forecast_by_month = self.calculate_monthly_forecast_or_plan(planned_activities_complete_df, self.get_all_avrg_activities_cost())
        month_numbers = [get_month_number(m) for m in month_names]
        forecast_by_month["month_num"] = month_numbers

        # 🟢 CAMBIO: Calcula y añade el total de actividades al DataFrame.
        total_activities_by_month = planned_activities_complete_df[month_names].sum(axis=0)
        total_activities_df = total_activities_by_month.reset_index()
        total_activities_df.columns = ['MONTH', 'TOTAL_ACTIVITIES']
        forecast_by_month = forecast_by_month.merge(total_activities_df, on='MONTH', how='left')
        
        if not self.catalog:
            self.load_catalog()
        
        real_cost_df = self.generate_budget().rename(columns={"Budget": "ACTUAL_COST"})
        final_df = forecast_by_month.merge(real_cost_df, on="MONTH", how="left")
        final_df = final_df.rename(columns={"FORECAST": "FORECAST_COST"})
        
        final_df["BUDGET"] = final_df["FORECAST_COST"]
        final_df.loc[final_df["ACTUAL_COST"].notna(), "BUDGET"] = final_df["ACTUAL_COST"]
        final_df["CUMULATIVE_FORECAST"] = final_df["BUDGET"].cumsum()
        final_df = final_df.sort_values("month_num").reset_index(drop=True)

        print("\n📊 RESUMEN FORECAST WIRELINE:")
        print(final_df[[
            "MONTH", "TOTAL_ACTIVITIES", "FORECAST_COST", "ACTUAL_COST", "BUDGET", "CUMULATIVE_FORECAST"
        ]])
        return final_df

    def get_all_avrg_activities_cost(self):
        avg_activity_gestor = AvgActivityGestor()
        config_path = os.path.join(os.path.dirname(__file__), 'activity_config.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            activity_config = json.load(f)
        df_avrg_costs = pd.DataFrame()
        for key, params in activity_config.items():
            types = params["types"]
            min_value = params["min"]
            max_value = params.get("max")
            avg = avg_activity_gestor.get_avrg_by_type_and_range(types, min_value, max_value, self.line_name)
            df_avrg_costs[key] = [avg]
        return df_avrg_costs
    
    def calculate_monthly_forecast_or_plan(self, activities_df, avg_costs_df):
        """
        Calcula el forecast mensual multiplicando la cantidad de actividades por su costo promedio.
        activities_df: DataFrame de actividades
        avg_costs_df: DataFrame de costos promedio (output de get_all_avrg_activities_cost)
        Devuelve un DataFrame con columnas Month y FORECAST.
        """
        # Obtener lista de meses presentes en el DataFrame de actividades
        months = [col for col in activities_df.columns if col not in ['No.', 'Tipo de Actividad', 'PLANNED_ACTIVITIES', 'Total']]
        # Tomar la fila 0 de avg_costs_df como serie para fácil acceso
        avg_costs = avg_costs_df.iloc[0]
        forecast_per_month = []
        for month in months:
            total = 0
            for idx, row in activities_df.iterrows():
                code = row['No.']
                count = row[month]
                cost = avg_costs.get(code, 0)
                total += count * cost
            forecast_per_month.append(total)
        result_df = pd.DataFrame({'MONTH': months, 'FORECAST': forecast_per_month})
        return result_df

    def compute_activity_count(self, row, activity_rule):
        """
        Calcula el número de actividades según la regla definida en el catálogo.
        """
        rule_type = activity_rule.get("rule_type", "")
        ratio = activity_rule.get("ratio", 0)
        multiplier = activity_rule.get("multiplier", 1)
        activity_type = activity_rule.get("activity_type", "")

        if rule_type == "ratio_total":
            return ratio * row["total_interv"]
        elif rule_type == "by_type":
            return row.get({
                "C1.2": "wl_interv",
                "C1.3": "tcp_interv",
                "C1.5": "fishing_interv"
            }.get(activity_type, ""), 0)
        elif rule_type == "by_type_multiple":
            if activity_type == "C1.5":
                return multiplier * row.get("fishing_interv", 0)
        elif rule_type == "skip":
            return 0

        return 0

    def generate_budget(self):
        """
        Carga los costos reales desde los datos del plan anual.
        """
        return self.data_loader.load_budget_for_line(self.year, "1.6 Wireline")
    
    def generate_plan_cost_logic(self):
        planned_activities_complete_df = self.plan_actividades.data_loader.load_plan_actividades_from_excel(
                self.plan_actividades.plan_path,
                self.plan_actividades.sheet_name
        )

        month_names = [m for m in planned_activities_complete_df.columns if m not in ['No.', 'Tipo de Actividad', 'Total']]
        planned_cost_by_month_df = self.calculate_monthly_forecast_or_plan(planned_activities_complete_df, self.get_all_avrg_activities_cost())
        print("\n📊 RESUMEN PLAN WIRELINE:")
        print(self.get_all_avrg_activities_cost())
        print(planned_cost_by_month_df)
        month_numbers = [get_month_number(m) for m in month_names]
        planned_cost_by_month_df["month_num"] = month_numbers
        planned_cost_by_month_df.rename(columns={"FORECAST": "PLANNED_COST"}, inplace=True)
        return planned_cost_by_month_df

    def generate_plan_data(self, opex_budget: float) -> pd.DataFrame:
        """
        Genera un dataframe de plan uniforme mensual usando el OPEX total.
        """
        planificacion_manual = get_planning_cost_by_line_path("1.06 Wireline Report", self.year)
        manual_planning_df = pd.read_excel(planificacion_manual)
        manual_planning_df.rename(columns={"Costo de Plan": "PLANNED_COST"}, inplace=True)
        manual_planning_df.rename(columns={"Mes": "MONTH"}, inplace=True)
        if manual_planning_df.empty: # Esto es para mantener lo que se tenia anteriormente, por si algo falla (genera una linea lineal en la grafica)
            return self.generate_plan_cost_logic()
        return manual_planning_df[["MONTH", "PLANNED_COST"]]
    
    def generate_graph(self, forecast, budget, activities_data):
        """
        Genera el gráfico de comparación Forecast vs Real vs Plan.
        """
        from services.graph_generator import create_budget_forecast_graph
        opex_budget = self.opex_manager.get_opex_for_line("1.06 Wireline")
        plan_data = self.generate_plan_data(opex_budget)
        
        # 🟢 CAMBIO: Crea las barras de "Forecasted" dinámicamente desde el forecast.
        capacity_df = forecast[['MONTH', 'TOTAL_ACTIVITIES']].copy()
        capacity_df.rename(columns={'TOTAL_ACTIVITIES': 'FORECASTED_OPEX_ACT'}, inplace=True)

        return create_budget_forecast_graph(
            forecast=forecast,
            budget_data=budget,
            plan_data=plan_data,
            activities_data=activities_data,
            title="1.6 Wireline",
            capacity_data=capacity_df
        )

    def generate_deviations(self):
        """
        Wireline no calcula desviaciones personalizadas.
        """
        return pd.DataFrame()

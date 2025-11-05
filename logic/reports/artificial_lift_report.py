from logic.reports.base_report import LineReport

import numpy as np

import datetime
from logic.budget_analysis import (
    group_by_month,
    match_jobs_with_budget,
    BUDGET_GROUP_MAPPING,
    COTIZACION_GROUP_MAPPING
)
from logic.deviation_analysis import calculate_deviations
from services.graph_generator import generate_budget_graph_als
from utils.dates import normalize_month_names, get_all_months
from utils.file_manager import (
    get_single_excel_file_path,
    get_cotizacion_path,
    get_budget_als_dir,
    get_forecasted_plan_path
)
import pandas as pd


class ArtificialLiftReport(LineReport):
    """
    Reporte para la línea 1.13 Artificial LifT
    """
    def __init__(self, data_loader, year, operative_capacity, opex_manager, plan_actividades):
        super().__init__(data_loader)
        self.year = year
        self.operative_capacity = pd.DataFrame(operative_capacity)
        self.opex_manager = opex_manager
        self.matched_data = None
        self.plan_actividades = plan_actividades

    def load_and_match_data(self):
        """
        Carga y cruza los datos de cotización y presupuesto usando mapeos predefinidos.
        El resultado se cachea para evitar cargas repetidas.
        """
        if self.matched_data is None:
            cotizacion_path = get_cotizacion_path(self.year)
            print("###cotizacion")
            print(cotizacion_path)
            budget_path = get_single_excel_file_path(get_budget_als_dir())
            print("########################path")
            print(budget_path)
            cotizacion_df = self.data_loader.load_cotizacion_data(cotizacion_path)
            budget_df = self.data_loader.load_budget_data_from_excel(
                budget_path, "Detalle de pulling", year=self.year
            )
            print("budget df")
            print(budget_df)
            self.matched_data = match_jobs_with_budget(
                cotizacion_df, budget_df, BUDGET_GROUP_MAPPING, COTIZACION_GROUP_MAPPING
            )
        return self.matched_data

    def generate_forecast(self):
        """
        Genera el forecast mensual basado en la capacidad operativa y datos reales.
        Si hay datos reales disponibles, se priorizan sobre las estimaciones.
        """
        print("=== Generación de Forecast para Artificial Lift ===")
        matched_data = self.load_and_match_data()
        
        matched_data['Numero_Mes']=0
        matched_data["Numero_Mes"] = matched_data["MONTH"].case_when(
        [
            (matched_data["MONTH"] == "Jan", 1),
            (matched_data["MONTH"] == "Feb", 2),
            (matched_data["MONTH"] == "Mar", 3),
            (matched_data["MONTH"] == "Apr", 4),
            (matched_data["MONTH"] == "May", 5),
            (matched_data["MONTH"] == "Jun", 6),
            (matched_data["MONTH"] == "Jul", 7),
            (matched_data["MONTH"] == "Aug", 8),
            (matched_data["MONTH"] == "Sep", 9),
            (matched_data["MONTH"] == "Oct", 10),
            (matched_data["MONTH"] == "Nov", 11),
            (matched_data["MONTH"] == "Dec", 12)
        ]
        )
        print("=== RESUMEN FINAL DEL FORECAST === ALS")
        #print(matched_data)
        ###print(type(matched_data['Numero_Mes'] ))
        mes_actual = datetime.datetime.now().month   
        print(matched_data)
        matched_data['Numero_Mes'] = matched_data['Numero_Mes'].astype(int)
        matched_data = matched_data[~((matched_data['Numero_Mes'] >= mes_actual))]
        matched_data.to_excel("als-salida.xlsx")
        # Calcular costo real por pozo
        actual_cols = [col for col in matched_data.columns if col.endswith("_Actual")]
        matched_data["RealCost"] = matched_data[actual_cols].sum(axis=1, skipna=True)
        matched_data["N_POZOS"] = 1.0
        matched_data = matched_data[matched_data["RealCost"] > 0]
        matched_data["MONTH"] = normalize_month_names(matched_data["MONTH"])
        matched_data.to_excel("summary/als/real_costs_als.xlsx", index=False)

        # Agrupar datos reales por mes
        real_group = matched_data.groupby("MONTH").agg({
            "RealCost": "sum",
            "N_POZOS": "sum"
        }).reset_index()

        # Calcular promedios y ratio por capacidad
        total_real_cost = real_group["RealCost"].sum()
        total_real_pozos = real_group["N_POZOS"].sum()
        avg_cost_per_activity = total_real_cost / total_real_pozos if total_real_pozos > 0 else 0

        

        cap_df = self.operative_capacity.copy()
        cap_df["MONTH"] = cap_df["Mes"].map({i+1: m for i, m in enumerate(get_all_months())})
        cap_df["Total Días OPEX"] = cap_df.get("Total Días OPEX", 0)

        #merged = real_group.merge(cap_df[["MONTH", "Total Días OPEX"]], on="MONTH", how="inner")
        #sum_days = merged["Total Días OPEX"].sum()
        
        #sum_pozos = merged["N_POZOS"].sum()
        #pozos_ratio = sum_pozos / sum_days if sum_days > 0 else 0

        # Construir DataFrame de forecast
        all_months = get_all_months()
        forecast_df = pd.DataFrame({"MONTH": all_months})
        print("TABLAS FORECAST Y CAP_DF")
        print(forecast_df)
        print(cap_df)
        forecast_df = forecast_df.merge(cap_df[["MONTH", "Numero tentativo de pozos OPEX"]], on="MONTH", how="left")
        forecast_df = forecast_df.merge(real_group[["MONTH", "RealCost"]], on="MONTH", how="left")
        forecast_df.fillna({"Numero tentativo de pozos OPEX": 0, "RealCost": 0}, inplace=True)
        forecast_df["PlannedActivities"] = forecast_df["Numero tentativo de pozos OPEX"]
        print("PlannedActivities")
        print(forecast_df)
        forecast_df["Forecast"] = forecast_df.apply(
            lambda row: row["RealCost"] if row["RealCost"] > 0 else row["PlannedActivities"] * avg_cost_per_activity,
            axis=1
        )


        forecast_df["MONTH"] = pd.Categorical(forecast_df["MONTH"], categories=all_months, ordered=True)
        forecast_df.sort_values("MONTH", inplace=True)
        #forecast_df.to_excel("summary/als/final_summary_als.xlsx", index=False)

        #print("=== RESUMEN FINAL DEL FORECAST ===")
        
        #forecast_df.replace(0, np.nan, inplace=True)

        #print(forecast_df[["MONTH", "Total Días OPEX", "PlannedActivities", "RealCost", "Forecast"]])
        print(forecast_df)

        return forecast_df

    def generate_budget(self):
        """Agrupa y resume el presupuesto real por mes para Artificial Lift."""
        matched_data = self.load_and_match_data()

        matched_data['Numero_Mes']=0
        matched_data["Numero_Mes"] = matched_data["MONTH"].case_when(
        [
            (matched_data["MONTH"] == "Jan", 1),
            (matched_data["MONTH"] == "Feb", 2),
            (matched_data["MONTH"] == "Mar", 3),
            (matched_data["MONTH"] == "Apr", 4),
            (matched_data["MONTH"] == "May", 5),
            (matched_data["MONTH"] == "Jun", 6),
            (matched_data["MONTH"] == "Jul", 7),
            (matched_data["MONTH"] == "Aug", 8),
            (matched_data["MONTH"] == "Sep", 9),
            (matched_data["MONTH"] == "Oct", 10),
            (matched_data["MONTH"] == "Nov", 11),
            (matched_data["MONTH"] == "Dec", 12)
        ]
        )
        print("=== RESUMEN FINAL DEL FORECAST === ALS")
        #print(matched_data)
        ###print(type(matched_data['Numero_Mes'] ))
        mes_actual = datetime.datetime.now().month      
        matched_data['Numero_Mes'] = matched_data['Numero_Mes'].astype(int)
        matched_data = matched_data[~((matched_data['Numero_Mes'] >= mes_actual))]

        actual_cols = [col for col in matched_data.columns if col.endswith('_Actual')]

        matched_data['Actual Cost'] = matched_data[actual_cols].sum(axis=1, skipna=True)
        matched_data['MONTH'] = normalize_month_names(matched_data['MONTH'])

        monthly_data = group_by_month(matched_data)
        monthly_data['MONTH'] = pd.Categorical(
            monthly_data['MONTH'], categories=get_all_months(), ordered=True
        )
        monthly_data.sort_values('MONTH', inplace=True)
        # monthly_data.to_excel("summary/als/monthly_data_als.xlsx")
        return monthly_data

    def generate_deviations(self):
        """Calcula las desviaciones por componente con base en cotización vs presupuesto."""
        matched_data = self.load_and_match_data()
        deviations = calculate_deviations(
            data=matched_data,
            group_mapping=BUDGET_GROUP_MAPPING,
            threshold=20000
        )
        deviations.to_excel("summary/als/deviations.xlsx")
        return deviations
    
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
            "month": month_names,
            "total_activities": total_activities_by_month,
        })
        return df_activities

    def generate_graph(self, forecast_df, budget, activities_data, failures=None):
        """Genera el gráfico comparativo para Artificial Lift."""
        capacity_df = self.get_total_activities()
        opex_budget = self.opex_manager.get_opex_for_line("1.13 Artificial Lift")
        
        print(f"⚠️ OPEX Budget: {opex_budget}")
        return generate_budget_graph_als(forecast_df, budget, activities_data, capacity_df, opex_budget=opex_budget)

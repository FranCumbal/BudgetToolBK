import os
import math
import calendar
import pandas as pd
import numpy as np
from logic.plan_actividades1 import PlanAnualActividades1
from datetime import datetime

from logic.reports.base_report import LineReport
from utils.dates import normalize_month_names, get_month_number, get_all_months
from logic.activity_mapping import map_services_and_costs
from utils.file_manager import get_catalog_path, get_template_path, get_forecasted_plan_path

class BitsDrillingTRemedialReport(LineReport):
    """
    Reporte para la línea 1.4 Bits, Drilling Tools and Remedial.

    Genera un forecast mensual basado en el mapeo de actividades
    y aplica un factor de 60% al costo unitario.
    """

    def __init__(self, data_loader, year, operative_capacity, opex_manager, plan_actividades):
        super().__init__(data_loader)
        self.year = year
        self.operative_capacity = operative_capacity
        self.opex_manager = opex_manager
        self.plan_actividades = plan_actividades
        print("EN ESTA CLASE")
        print(self.plan_actividades)
        print(self.plan_actividades.plan_path, "AQUI BRO")
        self.line_filter = "Bits, Drilling Tools and Remedial"

    def load_catalog(self):
        """Carga el catálogo de costos unitarios para Bits y Herramientas."""
        return self.data_loader.load_catalog_data(
            get_catalog_path(), sheet_name="Bits, Drilling Tools"
        )

    def load_template(self):
        """Carga la plantilla de actividades para la línea correspondiente."""
        template_df = self.data_loader.load_activities_template(get_template_path())
        return template_df[template_df['line'] == self.line_filter].copy()
    def generate_forecast(self):
        """
        Genera el forecast mensual para la línea 1.4 Bits, Drilling Tools and Remedial.

        El cálculo se basa en el plan anual de actividades, que se transforma en trabajos individuales.
        Luego, se mapean estos trabajos al catálogo de costos unitarios.

        A diferencia de versiones previas, el factor del 60% se aplica al total mensual,
        no al costo por fila. El resultado se exporta a un archivo Excel para revisión.
        
        Columnas del resultado:
            - FORECAST_COST: Costo proyectado mensual (60% del total original)
            - ACTUAL_COST: Costo real (si existe)
            - BUDGET: Costo final usado (forecast si no hay real)
            - CUMULATIVE_FORECAST: Acumulado del presupuesto proyectado
        """
        plan_path = get_forecasted_plan_path(self.year)
        plan_provider = PlanAnualActividades1(self.data_loader, plan_path)
        distribucion_df = plan_provider.calcular_distribucion_por_tipo(year=self.year)

        # Normalizar nombres de columnas
        distribucion_df.columns = [
            normalize_month_names(pd.Series([col.strip()])).iloc[0]
            if col.strip() not in ['No.', 'Tipo de Actividad', 'Total'] else col.strip()
            for col in distribucion_df.columns
        ]

        month_names = [m for m in distribucion_df.columns if m not in ['No.', 'Tipo de Actividad', 'Total']]
        invalids = [m for m in month_names if get_month_number(m) == "Invalid month name"]
        if invalids:
            raise ValueError(f"❌ Invalid month names: {invalids}")

        # Expandir las actividades por cantidad
        jobs = []
        for _, row in distribucion_df.iterrows():
            tipo = row['No.']
            for mes in month_names:
                cantidad = int(row[mes])
                for _ in range(cantidad):
                    jobs.append({"activity_type": tipo, "MONTH": mes})

        jobs_df = pd.DataFrame(jobs)
        if jobs_df.empty:
            return pd.DataFrame()

        template_df = self.load_template()
        catalog_df = self.load_catalog()
        mapped_df = map_services_and_costs(jobs_df, template_df, catalog_df)

        # Agrupar costo original por mes
        monthly_costs = mapped_df.groupby('MONTH')['CostByService'].sum().reset_index()

        # Aplicar el factor de 60% al total mensual (aquí está el cambio)
        monthly_costs['FORECAST_COST'] = monthly_costs['CostByService'] 
        monthly_costs.drop(columns=['CostByService'], inplace=True)

        # Combinar con todos los meses (asegurar formato uniforme)
        df = pd.DataFrame({"MONTH": get_all_months()})
        df = df.merge(monthly_costs, on="MONTH", how="left")

        # Cargar datos reales del presupuesto
        budget_df = self.generate_budget()
        df = df.merge(budget_df, on="MONTH", how="left")
        df.rename(columns={"Budget": "ACTUAL_COST"}, inplace=True)

        # BUDGET: forecast por defecto, pero si hay real, se usa ese
        df["BUDGET"] = df["FORECAST_COST"].fillna(0)
        df.loc[df["ACTUAL_COST"].notna(), "BUDGET"] = df["ACTUAL_COST"]
        df["CUMULATIVE_FORECAST"] = df["BUDGET"].cumsum()

        # Exportar a Excel
        #export_path = "summary/bits_drilling_tool/forecast_data_bits_drilling.xlsx"
        #os.makedirs(os.path.dirname(export_path), exist_ok=True)
        #df.to_excel(export_path, index=False)

        print("\n📊 RESUMEN FORECAST BITS DRILLING:")
        print(df[["MONTH", "FORECAST_COST", "ACTUAL_COST", "BUDGET", "CUMULATIVE_FORECAST"]])

        return df


    def generate_budget(self):
        """Carga datos del presupuesto real."""
        return self.data_loader.load_budget_for_line(self.year, "1.4 Bits, Drilling Tools & Remedial (B,D &R)")

    def generate_plan_data(self, opex_budget: float) -> pd.DataFrame:
        """Distribuye el OPEX uniformemente entre los 12 meses."""
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
        Genera el gráfico comparativo forecast vs real vs plan.
        Incluye las actividades planeadas, ejecutadas y pozos estimados.
        """
        from services.graph_generator import create_budget_forecast_graph

        opex_budget = self.opex_manager.get_opex_for_line("1.04 Bits, Drilling Tools & Remedial (B,D &R)")
        print(f"⚠️ OPEX Budget: {opex_budget}")
        plan_data = self.generate_plan_data(opex_budget)

        # Formatear capacity_df con pozos OPEX
        capacity_df = self.get_total_activities()
        capacity_df.rename(columns={'TOTAL_ACTIVITIES': 'FORECASTED_OPEX_ACT'}, inplace=True)

        return create_budget_forecast_graph(
            forecast=forecast,
            budget_data=budget,
            plan_data=plan_data,
            activities_data=activities_data,
            title="1.4 Bits, Drilling Tools and Remedial",
            capacity_data=capacity_df
        )

    def generate_deviations(self):
        """No aplica cálculo de desviaciones para este reporte."""
        return pd.DataFrame()
    
    
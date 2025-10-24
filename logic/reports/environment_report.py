import os
import calendar
import pandas as pd
from datetime import datetime
from logic.reports.base_report import LineReport
from utils.dates import normalize_month_names, get_month_number, get_all_months
from utils.file_manager import get_catalog_path, get_forecasted_plan_path

class EnvironmentReport(LineReport):
    """
    Reporte para la línea 1.11 Environment.

    Características:
    - Genera el forecast mensual con base en el plan anual de actividades.
    - Aplica los costos unitarios por tipo de actividad desde un catálogo.
    - Combina los resultados con los costos reales si están disponibles.
    - Exporta un resumen mensual con costos proyectados, reales y acumulados.
    """

    def __init__(self, data_loader, year, operative_capacity, opex_manager, plan_actividades):
        """
        Inicializa el reporte.

        :param data_loader: Fuente de datos históricos y configuraciones.
        :param year: Año del forecast.
        :param operative_capacity: DataFrame con la capacidad operativa por mes.
        :param opex_manager: Manejador del presupuesto OPEX asignado.
        :param plan_actividades: Plan anual de actividades.
        """
        super().__init__(data_loader)
        self.year = year
        self.operative_capacity = pd.DataFrame(operative_capacity)
        self.opex_manager = opex_manager
        self.plan_actividades = plan_actividades
        self.catalog = None

    def load_catalog(self):
        """
        Carga el catálogo de costos por tipo de actividad desde la hoja "Environment".
        El catálogo debe contener las columnas: No., Tipo de Actividad, Costo / actividad.

        :return: Lista de diccionarios con códigos, descripciones y costos unitarios.
        """
        catalog_df = self.data_loader.load_catalog_data(get_catalog_path(), sheet_name="Environment")
        self.catalog = [
            {
                "activity_code": str(row["No."]).strip(),
                "description": row["Tipo de Actividad"],
                "cost": float(row["Costo / actividad"])
            }
            for _, row in catalog_df.iterrows()
        ]
        return self.catalog

    def generate_forecast(self):
        """
        Genera el forecast mensual:
        - Aplica los costos por tipo de actividad del catálogo.
        - Multiplica la cantidad de actividades mensuales por su costo unitario.
        - Combina con datos reales cuando existen.

        :return: DataFrame con columnas: MONTH, TOTAL_ACTIVITIES, FORECAST_COST, ACTUAL_COST, BUDGET, CUMULATIVE_FORECAST.
        """
        sheet_name = f"ForecastedPlan{self.year}"
        forecasted_plan_path = get_forecasted_plan_path(self.year)
        planned_activities_complete_df = self.plan_actividades.data_loader.load_plan_actividades_from_excel(
                forecasted_plan_path,
                sheet_name
        )
        planned_activities_complete_df.columns = [
            normalize_month_names(pd.Series([col.strip()])).iloc[0]
            if col.strip() not in ['No.', 'Tipo de Actividad', 'Total'] else col.strip()
            for col in planned_activities_complete_df.columns
        ]
        month_names = [m for m in planned_activities_complete_df.columns if m not in ['No.', 'Tipo de Actividad', 'Total']] #De aqui solo saca los meses en ingles y mayuscula
        month_nums = [get_month_number(m) for m in month_names]

        if not self.catalog:
            self.load_catalog()

        # Inicializar estructura de salida
        data = {
            "month_num": month_nums,
            "MONTH": [calendar.month_name[num] for num in month_nums],
            "TOTAL_ACTIVITIES": [0] * 12,
            "FORECAST_COST": [0.0] * 12
        }
        
        for act in self.catalog:
            code = act["activity_code"]
            data[f"{code}_COUNT"] = [0] * 12
            data[f"{code}_COST"] = [0.0] * 12
        # Procesar distribución de actividades
        for _, row in planned_activities_complete_df.iterrows():
            code = str(row["No."]).strip()
            catalog_entry = next((c for c in self.catalog if c["activity_code"] == code), None)
            if not catalog_entry:
                continue

            cost_unit = catalog_entry["cost"]

            for i, month in enumerate(month_names):
                try:
                    count = int(row[month])
                except ValueError:
                    count = 0

                data[f"{code}_COUNT"][i] += count
                data[f"{code}_COST"][i] += count * cost_unit
                data["TOTAL_ACTIVITIES"][i] += count
                data["FORECAST_COST"][i] += count * cost_unit

        forecast_df = pd.DataFrame(data)
        # Cargar presupuesto real y combinar
        budget_df = self.generate_budget().rename(columns={"Budget": "ACTUAL_COST"})
        final_df = forecast_df.merge(budget_df, on="MONTH", how="left")

        final_df["BUDGET"] = final_df["FORECAST_COST"]
        final_df.loc[final_df["ACTUAL_COST"].notna(), "BUDGET"] = final_df["ACTUAL_COST"]
        final_df["CUMULATIVE_FORECAST"] = final_df["BUDGET"].cumsum()
        final_df = final_df.sort_values("month_num").reset_index(drop=True)

        print("\n📊 RESUMEN FORECAST ENVIRONMENT:")
        print(final_df[["MONTH", "TOTAL_ACTIVITIES", "FORECAST_COST", "ACTUAL_COST", "BUDGET", "CUMULATIVE_FORECAST"]])

        return final_df

    def generate_budget(self):
        """Carga los datos reales ejecutados para la línea 1.11 Environment."""
        return self.data_loader.load_budget_for_line(self.year, "1.11 Environment")

    def generate_plan_data(self, opex_budget: float) -> pd.DataFrame:
        """Distribuye uniformemente el OPEX anual en los 12 meses."""
        months = get_all_months()
        monthly_value = opex_budget / 12
        return pd.DataFrame({"MONTH": months, "PLANNED_COST": [monthly_value] * 12})

    def generate_graph(self, forecast, budget, activities_data):
        """Genera gráfico Forecast vs Real vs Plan para Environment."""
        from services.graph_generator import create_budget_forecast_graph

        opex_budget = self.opex_manager.get_opex_for_line("1.11 Environment")
        plan_data = self.generate_plan_data(opex_budget)

        capacity_df = forecast[['MONTH', 'TOTAL_ACTIVITIES']].copy()
        capacity_df.rename(columns={'TOTAL_ACTIVITIES': 'FORECASTED_OPEX_ACT'}, inplace=True)

        return create_budget_forecast_graph(
            forecast=forecast,
            budget_data=budget,
            plan_data=plan_data,
            activities_data=activities_data,
            title="1.11 Environment",
            capacity_data=capacity_df
        )

    def generate_deviations(self):
        """No se calculan desviaciones específicas para Environment."""
        return pd.DataFrame()
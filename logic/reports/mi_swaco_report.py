import pandas as pd
import calendar
from logic.plan_actividades1 import PlanAnualActividades1
from logic.reports.base_report import LineReport
from utils.dates import get_all_months, get_month_number, normalize_month_names
from utils.file_manager import get_catalog_path, get_forecasted_plan_path


class MISwacoReport(LineReport):
    """
    Reporte para la línea 1.2 M-I Swaco.

    Calcula el forecast mensual utilizando el número de actividades planificadas
    desde el plan anual y el costo promedio por actividad cargado desde el catálogo.
    """

    # 🔴 CAMBIO: Eliminamos plan_actividades y lo reemplazamos por data_loader
    # El data_loader ya lo hereda de LineReport, así que no es necesario volver a declararlo
    def __init__(self, data_loader, year, operative_capacity, opex_manager, plan_actividades):
        super().__init__(data_loader)
        self.year = year
        self.operative_capacity = operative_capacity
        self.opex_manager = opex_manager
        # 🔴 CAMBIO: Eliminamos la dependencia directa de plan_actividades
        # self.plan_actividades = plan_actividades
        self.average_cost_per_activity = None
        self.plan_actividades = plan_actividades

    def load_catalog(self):
        """
        Carga el costo promedio desde un catálogo con columnas 'Descripción' y 'Valor'.
        """
        catalog_df = self.data_loader.load_catalog_data(get_catalog_path(), sheet_name="MI SWACO")

        # Filtrar por la fila que tenga la descripción 'Costo promedio'
        row = catalog_df[catalog_df['Descripción'].str.strip().str.lower() == 'costo promedio']

        if row.empty:
            raise ValueError("No se encontró una fila con 'Costo promedio' en la columna 'Descripción'.")

        self.average_cost_per_activity = float(row['Valor'].values[0])

        print(f"📚 Costo promedio cargado correctamente: {self.average_cost_per_activity}")

    def generate_forecast(self):
        """
        Genera el forecast mensual:
        - Usa la distribución mensual de actividades planificadas desde el plan anual.
        - Multiplica por el costo promedio por actividad desde el catálogo.
        - Integra los costos reales si existen.
        - Calcula el presupuesto final y acumulado.
        """
        # 🟢 CAMBIO: Se crea una instancia de PlanAnualActividades para asegurar
        # que se cargue el plan correcto (CDFPlan) desde el disco.
        plan_path = get_forecasted_plan_path(self.year)
        plan_provider = PlanAnualActividades1(self.data_loader, plan_path)
        distribucion_df = plan_provider.calcular_distribucion_por_tipo(year=self.year)

        distribucion_df.columns = [
            normalize_month_names(pd.Series([col.strip()])).iloc[0]
            if col.strip() not in ['No.', 'Tipo de Actividad', 'Total'] else col.strip()
            for col in distribucion_df.columns
        ]

        month_names = [m for m in distribucion_df.columns if m not in ['No.', 'Tipo de Actividad', 'Total']]
        month_nums = [get_month_number(m) for m in month_names]

        # 2. Cargar el costo promedio desde el catálogo
        if self.average_cost_per_activity is None:
            self.load_catalog()

        # 3. Construir forecast mensual
        data = {
            "month_num": month_nums,
            "MONTH": [calendar.month_name[num] for num in month_nums],
            "TOTAL_ACTIVITIES": [0] * 12,
            "FORECAST_COST": [0.0] * 12
        }

        for idx, mes in enumerate(month_names):
            actividades_mes = distribucion_df[mes].sum()
            data["TOTAL_ACTIVITIES"][idx] = actividades_mes
            data["FORECAST_COST"][idx] = actividades_mes * self.average_cost_per_activity

        forecast_df = pd.DataFrame(data)

        # 4. Cargar presupuesto real
        budget_df = self.generate_budget().rename(columns={"Budget": "ACTUAL_COST"})
        forecast_df = forecast_df.merge(budget_df, on="MONTH", how="left")

        # 5. Determinar presupuesto final
        forecast_df["BUDGET"] = forecast_df["FORECAST_COST"]
        forecast_df.loc[forecast_df["ACTUAL_COST"].notna(), "BUDGET"] = forecast_df["ACTUAL_COST"]

        # 6. Calcular acumulado
        forecast_df["CUMULATIVE_FORECAST"] = forecast_df["BUDGET"].cumsum()

        # 7. Guardar resultados
        #forecast_df.to_excel(r"summary/mi_swaco/forecast_data_mi_swaco.xlsx", index=False)

        print("\n📊 RESUMEN FORECAST MI SWACO:")
        print(forecast_df[["MONTH", "TOTAL_ACTIVITIES", "FORECAST_COST", "ACTUAL_COST", "BUDGET", "CUMULATIVE_FORECAST"]])

        return forecast_df

    def generate_budget(self):
        """Carga el presupuesto real para M-I Swaco."""
        return self.data_loader.load_budget_for_line(self.year, "1.2 M-I Swaco")

    def generate_plan_data(self, opex_budget: float) -> pd.DataFrame:
        """Distribuye el OPEX uniformemente en los 12 meses para fines de comparación visual."""
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
        Genera el gráfico comparativo forecast vs real vs plan para M-I Swaco.
        """
        from services.graph_generator import create_budget_forecast_graph
        opex_budget = self.opex_manager.get_opex_for_line("1.02 M-I Swaco")
        print(f"⚠️ OPEX Budget: {opex_budget}")
        plan_data = self.generate_plan_data(opex_budget)

        capacity_df = self.get_total_activities()
        capacity_df.rename(columns={'TOTAL_ACTIVITIES': 'FORECASTED_OPEX_ACT'}, inplace=True)

        return create_budget_forecast_graph(
            forecast=forecast,
            budget_data=budget,
            plan_data=plan_data,
            activities_data=activities_data,
            title="1.02 M-I Swaco",
            capacity_data=capacity_df
        )

    def generate_deviations(self):
        """No se generan desviaciones para este reporte."""
        return pd.DataFrame()
import pandas as pd
import calendar
from logic.reports.base_report import LineReport
from utils.dates import get_all_months, get_month_number, normalize_month_names
from utils.file_manager import get_catalog_path, get_forecasted_plan_path

class CompletionsReport(LineReport):
    """
    Reporte para la línea 1.03 Completions.

    Calcula el forecast mensual:
    - Usa actividades planificadas del plan anual.
    - Multiplica por un costo promedio cargado desde catálogo.
    - Aplica un costo adicional único si corresponde.
    """

    def __init__(self, data_loader, year, operative_capacity, opex_manager, plan_actividades):
        super().__init__(data_loader)
        self.year = year
        self.operative_capacity = pd.DataFrame(operative_capacity)
        self.opex_manager = opex_manager
        self.plan_actividades = plan_actividades
        self.average_cost_per_activity = None
        self.extra_cost = 0
        self.extra_cost_month = None
        self.warnings = []

    def load_catalog(self):
        """
        Carga el catálogo para Completions:
        - Costo promedio por actividad.
        - Costo adicional y el mes de aplicación (opcional).

        El mes ahora se espera como número (1-12).
        """
        self.warnings = []

        catalog_df = self.data_loader.load_catalog_data(get_catalog_path(), sheet_name="COMPLETIONS")

        for _, row in catalog_df.iterrows():
            descripcion = str(row.get("Descripción", "")).strip().lower()
            valor = row.get("Valor", 0)
            mes = row.get("Mes", None)  # Ahora esperamos que Mes sea un número

            if descripcion == "costo promedio":
                try:
                    self.average_cost_per_activity = float(valor)
                except (TypeError, ValueError):
                    raise ValueError("Error crítico: El valor de 'Costo promedio' no es un número válido.")

            elif descripcion == "costo adicional":
                try:
                    self.extra_cost = float(valor)
                    # Validar que el mes sea un número entre 1 y 12
                    if not (isinstance(mes, (int, float)) and 1 <= int(mes) <= 12):
                        self.warnings.append(f"El número de mes '{mes}' no es válido. El costo adicional no se aplicará.")
                        self.extra_cost = 0
                        self.extra_cost_month = None
                    else:
                        self.extra_cost_month = calendar.month_name[int(mes)]  # Convertimos el número en nombre de mes
                except (TypeError, ValueError):
                    self.warnings.append("El valor de 'Costo adicional' o 'Mes' no es válido. No se aplicará el costo adicional.")

        if not self.average_cost_per_activity:
            raise ValueError("Error crítico: No se encontró 'Costo promedio' válido en el catálogo.")

    def generate_forecast(self):
        """
        Genera el forecast mensual:
        - Usa actividades planificadas del plan anual.
        - Multiplica por el costo promedio cargado.
        - Integra los costos reales si existen.
        - Aplica costo adicional sólo si no hay ejecución en el mes configurado.
        """
        if self.average_cost_per_activity is None:
            self.load_catalog()
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
            forecast_df = pd.DataFrame({
                'MONTH': list(monthly_totals.keys()),
                'PLANNED_ACTIVITIES': list(monthly_totals.values())
            })
            list_provisional = list(monthly_totals.values())
        else:
            months = [calendar.month_name[i] for i in range(1, 13)]
            forecast_df = pd.DataFrame({'MONTH': months, 'PLANNED_ACTIVITIES': [0]*12})
        print("Como termian")
        print(forecast_df)

        # obtener los meses 
        month_names = [m for m in planned_activities_complete_df.columns if m not in ['No.', 'Tipo de Actividad', 'PLANNED_ACTIVITIES']]
        total_activities_by_month = list_provisional if list_provisional else [0] * len(month_names)
        

        df = pd.DataFrame({
            "month_num": [get_month_number(m) for m in month_names],
            "MONTH": month_names,
            "TOTAL_ACTIVITIES": total_activities_by_month,
            "FORECAST_COST": [a * self.average_cost_per_activity for a in total_activities_by_month]
        })

        budget_df = self.generate_budget().rename(columns={"Budget": "ACTUAL_COST"})
        df = df.merge(budget_df, on="MONTH", how="left")

        df["BUDGET"] = df["FORECAST_COST"]
        df.loc[df["ACTUAL_COST"].notna(), "BUDGET"] = df["ACTUAL_COST"]

        # Aplicar costo adicional
        if self.extra_cost and self.extra_cost_month:
            idx = df[df["MONTH"].str.lower() == self.extra_cost_month.lower()].index
            if not idx.empty:
                row_idx = idx[0]
                if pd.isna(df.at[row_idx, "ACTUAL_COST"]) or df.at[row_idx, "ACTUAL_COST"] == 0:
                    df.at[row_idx, "BUDGET"] += self.extra_cost
                    print(f"✅ Se aplicó el costo adicional de {self.extra_cost} en {self.extra_cost_month}")
                else:
                    self.warnings.append(
                        f"No se aplicó el costo adicional en {self.extra_cost_month} porque ya existe ejecución real."
                    )

        df["CUMULATIVE_FORECAST"] = df["BUDGET"].cumsum()

        #df.to_excel("summary/completions/forecast_data_completions.xlsx", index=False)

        print("\n📊 RESUMEN FORECAST COMPLETIONS:")
        print(df[["MONTH", "TOTAL_ACTIVITIES", "FORECAST_COST", "ACTUAL_COST", "BUDGET", "CUMULATIVE_FORECAST"]])

        return df

    def generate_budget(self):
        """Carga el presupuesto real para Completions."""
        return self.data_loader.load_budget_for_line(self.year, "1.03 Completions")

    def generate_plan_data(self, opex_budget: float) -> pd.DataFrame:
        """Distribuye el OPEX uniformemente en los 12 meses para fines comparativos."""
        months = get_all_months()
        monthly_value = opex_budget / 12
        return pd.DataFrame({"MONTH": months, "PLANNED_COST": [monthly_value] * 12})

    def generate_graph(self, forecast, budget, activities_data):
        """
        Genera el gráfico forecast vs real vs plan para Completions.
        """
        from services.graph_generator import create_budget_forecast_graph
        opex_budget = self.opex_manager.get_opex_for_line("1.03 Completions")
        plan_data = self.generate_plan_data(opex_budget)

        # 🟢 CAMBIO: En lugar de leer la capacidad operativa estática, vamos a
        # construir dinámicamente los datos para las barras "Forecasted" a partir
        # del archivo que acabas de editar.

        # 1. Tomamos los datos del forecast (que vienen del ForecastedPlan.xlsx).
        #    La columna 'TOTAL_ACTIVITIES' contiene los valores que necesitas visualizar.
        capacity_df = forecast[['MONTH', 'TOTAL_ACTIVITIES']].copy()
        
        # 2. Renombramos la columna para que la función de la gráfica la reconozca
        #    y la use para dibujar las barras de "Forecasted Opex Act".
        capacity_df.rename(columns={'TOTAL_ACTIVITIES': 'FORECASTED_OPEX_ACT'}, inplace=True)

        # 3. Llamamos a la función de la gráfica pasando:
        #    - 'activities_data' sin modificar (para las barras "Planned Activities").
        #    - El nuevo 'capacity_df' (para las barras "Forecasted Opex Act").
        return create_budget_forecast_graph(
            forecast=forecast,
            budget_data=budget,
            plan_data=plan_data,
            activities_data=activities_data,
            title="1.03 Completions",
            capacity_data=capacity_df
        )

    def generate_deviations(self):
        """No se generan desviaciones para este reporte."""
        return pd.DataFrame()
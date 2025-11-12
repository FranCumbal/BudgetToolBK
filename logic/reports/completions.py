#completions

import pandas as pd
import calendar
import os
from logic.reports.base_report import LineReport
from utils.dates import get_all_months, get_month_number, normalize_month_names
from utils.file_manager import get_catalog_path, get_forecasted_plan_path, get_completions_config_path
from logic.plan_actividades1 import PlanAnualActividades1

pd.set_option('display.max_columns', None)

class CompletionsReport(LineReport):
    """
    Reporte para la línea 1.03 Completions.

    Lógica Híbrida:
    - Carga el plan de actividades automático.
    - Carga el plan manual de "ofensores".
    - Calcula el costo de actividades normales.
    - Suma el costo específico.
    - Aplica un "costo adicional" de catálogo si existe.
    """

    def __init__(self, data_loader, year, operative_capacity, opex_manager, plan_actividades):
        super().__init__(data_loader)
        self.year = year
        self.operative_capacity = pd.DataFrame(operative_capacity)
        self.opex_manager = opex_manager
        self.plan_actividades = plan_actividades
        
        # Valores que cargará load_catalog
        self.average_cost_per_activity = None
        self.extra_cost = 0
        self.extra_cost_month = None
        self.warnings = []

        # Cargamos el catálogo (costo normal y costo adicional)
        if self.average_cost_per_activity is None:
            self.load_catalog()
            
        # Cargamos y procesamos el config de ofensores
        self.df_config_ofensor = self.load_completions_config()
        
        # Procesamos el config para tenerlo listo (agrupado por MONTH)
        self.ofensor_cost_by_month = self.df_config_ofensor.groupby('MONTH')['AVG_QUANTITY'].sum().to_dict()
        self.ofensor_count_by_month = self.df_config_ofensor.groupby('MONTH').size().to_dict()
        
        print(f"Completions Ofensor: Costos por mes cargados: {self.ofensor_cost_by_month}")
        print(f"Completions Ofensor: Conteo por mes cargado: {self.ofensor_count_by_month}")

    def load_catalog(self):
        """
        Carga el catálogo para Completions:
        - Costo promedio por actividad (NORMAL).
        - Costo adicional y el mes de aplicación (opcional).
        """
        self.warnings = []
        catalog_df = self.data_loader.load_catalog_data(get_catalog_path(), sheet_name="COMPLETIONS")

        # Limpiamos los nombres de columna
        catalog_df.columns = catalog_df.columns.str.strip()

        for _, row in catalog_df.iterrows():
            descripcion = str(row.get("Descripción", "")).strip().lower()
            valor = row.get("Valor", 0)
            mes = row.get("Mes", None) 

            if descripcion == "costo promedio":
                try:
                    self.average_cost_per_activity = float(valor)
                except (TypeError, ValueError):
                    raise ValueError("Error crítico: El valor de 'Costo promedio' no es un número válido.")

            elif descripcion == "costo adicional":
                try:
                    self.extra_cost = float(valor)
                    if not (isinstance(mes, (int, float)) and 1 <= int(mes) <= 12):
                        self.warnings.append(f"El número de mes '{mes}' no es válido. El costo adicional no se aplicará.")
                        self.extra_cost = 0
                        self.extra_cost_month = None
                    else:
                        self.extra_cost_month = calendar.month_name[int(mes)] 
                except (TypeError, ValueError):
                    self.warnings.append("El valor de 'Costo adicional' o 'Mes' no es válido. No se aplicará el costo adicional.")

        if self.average_cost_per_activity is None:
            raise ValueError("Error crítico: No se encontró 'Costo promedio' válido en el catálogo de COMPLETIONS.")
        
        print(f"📚 Completions: Costo promedio NORMAL cargado: {self.average_cost_per_activity}")
        if self.extra_cost > 0:
            print(f"📚 Completions: Costo ADICIONAL cargado: {self.extra_cost} para el mes {self.extra_cost_month}")

    def load_completions_config(self):
        """
        Carga el archivo de configuración manual de Completions (Ofensores).
        """
        config_path = get_completions_config_path()
        if not os.path.exists(config_path):
            print("Advertencia: No se encontró 'completions_config.xlsx'. Se usará un forecast 100% automático.")
            return pd.DataFrame(columns=["MONTH", "TYPE", "ACTIVITIES", "AVG_QUANTITY"])
        
        try:
            df = pd.read_excel(config_path)
            
            # --- Compatibilidad con nombres viejos y nuevos ---
            if "AVG_QUANTITY" not in df.columns:
                if "AVG POR ACTIVIDAD" in df.columns:
                    df.rename(columns={"AVG POR ACTIVIDAD": "AVG_QUANTITY"}, inplace=True)
                elif "avg_quantity" in df.columns: # (por si acaso)
                    df.rename(columns={"avg_quantity": "AVG_QUANTITY"}, inplace=True)
                elif "Cantidad" in df.columns: # (formato súper-viejo)
                    df.rename(columns={"Cantidad": "AVG_QUANTITY"}, inplace=True)

            if "MONTH" not in df.columns:
                if "Month" in df.columns:
                    df.rename(columns={"Month": "MONTH"}, inplace=True)
                elif "month" in df.columns:
                    df.rename(columns={"month": "MONTH"}, inplace=True)

            if "MONTH" not in df.columns or "AVG_QUANTITY" not in df.columns:
                 print(f"ADVERTENCIA: 'completions_config.xlsx' no tiene las columnas 'MONTH' o 'AVG_QUANTITY'. No se cargarán datos de ofensor.")
                 return pd.DataFrame(columns=["MONTH", "TYPE", "ACTIVITIES", "AVG_QUANTITY"])

            df["MONTH"] = normalize_month_names(df["MONTH"])
            df["AVG_QUANTITY"] = pd.to_numeric(df["AVG_QUANTITY"], errors='coerce').fillna(0)
            
            print(f"✅ Cargado 'completions_config.xlsx' con {len(df)} actividades ofensor.")
            return df[["MONTH", "AVG_QUANTITY"]]
            
        except Exception as e:
            print(f"ERROR: No se pudo leer 'completions_config.xlsx'. Se usará un forecast 100% automático. Error: {e}")
            return pd.DataFrame(columns=["MONTH", "TYPE", "ACTIVITIES", "AVG_QUANTITY"])

    # --- 5. generate_forecast ---
    def generate_forecast(self):
        """
        Genera el forecast mensual aplicando la lógica híbrida de sustitución.
        """
        
        # 1. Cargar el Plan Automático
        plan_path = get_forecasted_plan_path(self.year)
        plan_provider = PlanAnualActividades1(self.data_loader, plan_path)
        distribucion_df = plan_provider.calcular_distribucion_hibrida(
            year=self.year, 
            saved_excel_path=plan_path, 
            saved_sheet_name=plan_provider.sheet_name
        )

        # Normalizar nombres de meses del plan
        distribucion_df.columns = [
            normalize_month_names(pd.Series([col.strip()])).iloc[0]
            if col.strip() not in ['No.', 'Tipo de Actividad', 'Total'] else col.strip()
            for col in distribucion_df.columns
        ]

        month_names = [m for m in distribucion_df.columns if m not in ['No.', 'Tipo de Actividad', 'Total']]
        month_nums = [get_month_number(m) for m in month_names]

        # 2. El costo promedio normal ya se cargó en __init__
        if self.average_cost_per_activity is None:
             self.load_catalog() 

        # 3. Construir DataFrame de forecast vacío
        data = {
            "month_num": month_nums,
            "MONTH": [calendar.month_name[num] for num in month_nums],
            "TOTAL_ACTIVITIES": [0] * 12, # Actividades Totales (Normal + Ofensor)
            "FORECAST_COST": [0.0] * 12
        }

        # 4. Aplicar la Lógica Híbrida mes a mes
        for idx, mes in enumerate(month_names):
            
            # a. Obtener total automático
            actividades_automaticas = distribucion_df[mes].sum()
            
            # b. Obtener datos del plan ofensor (cargados en __init__)
            num_actividades_ofensor = self.ofensor_count_by_month.get(mes, 0)
            costo_total_ofensor = self.ofensor_cost_by_month.get(mes, 0.0)
            
            # c. Calcular actividades normales
            actividades_normales = actividades_automaticas - num_actividades_ofensor
            
            if actividades_normales < 0:
                print(f"Advertencia en {mes}: Hay {num_actividades_ofensor} actividades ofensor pero solo {actividades_automaticas} en el plan. Se asumirán 0 actividades normales.")
                actividades_normales = 0
            
            # d. Calcular costo normal
            costo_normal = actividades_normales * self.average_cost_per_activity
            
            # e. Costo total del mes (sin costo adicional todavía)
            costo_forecast_mes = costo_normal + costo_total_ofensor
            
            data["TOTAL_ACTIVITIES"][idx] = actividades_automaticas
            data["FORECAST_COST"][idx] = costo_forecast_mes

        forecast_df = pd.DataFrame(data)

        # 5. Cargar presupuesto real
        budget_df = self.generate_budget().rename(columns={"Budget": "ACTUAL_COST"})
        forecast_df = forecast_df.merge(budget_df, on="MONTH", how="left")

        # 6. Determinar presupuesto final
        forecast_df["BUDGET"] = forecast_df["FORECAST_COST"]
        forecast_df.loc[forecast_df["ACTUAL_COST"].notna(), "BUDGET"] = forecast_df["ACTUAL_COST"]

        # --- 7. RE-INTEGRAR LÓGICA DE COSTO ADICIONAL ---
        if self.extra_cost and self.extra_cost_month:
            # (El mes ya está en Inglés gracias a load_catalog)
            idx = forecast_df[forecast_df["MONTH"] == self.extra_cost_month].index
            if not idx.empty:
                row_idx = idx[0]
                # Solo aplicar si no hay ejecución real en ese mes
                if pd.isna(forecast_df.at[row_idx, "ACTUAL_COST"]) or forecast_df.at[row_idx, "ACTUAL_COST"] == 0:
                    forecast_df.at[row_idx, "BUDGET"] += self.extra_cost
                    print(f"✅ Se aplicó el costo adicional de {self.extra_cost} en {self.extra_cost_month}")
                else:
                    self.warnings.append(
                        f"No se aplicó el costo adicional en {self.extra_cost_month} porque ya existe ejecución real."
                    )

        # 8. Calcular acumulado
        forecast_df["CUMULATIVE_FORECAST"] = forecast_df["BUDGET"].cumsum()

        # 9. Guardar resultados
        #forecast_df.to_excel("summary/completions/forecast_data_completions.xlsx", index=False)

        print("\n📊 RESUMEN FORECAST COMPLETIONS (Híbrido):")
        print(forecast_df[["MONTH", "TOTAL_ACTIVITIES", "FORECAST_COST", "ACTUAL_COST", "BUDGET", "CUMULATIVE_FORECAST"]])
        
        for warning in self.warnings:
            print(f"⚠️ {warning}")

        return forecast_df

    def generate_budget(self):
        """Carga el presupuesto real para Completions."""
        return self.data_loader.load_budget_for_line(self.year, "1.03 Completions")

    def generate_plan_data(self, opex_budget: float) -> pd.DataFrame:
        """Distribuye el OPEX uniformemente en los 12 meses para fines comparativos."""
        months = get_all_months()
        monthly_value = opex_budget / 12
        return pd.DataFrame({"MONTH": months, "PLANNED_COST": [monthly_value] * 12})

    # --- 6. NUEVA FUNCIÓN DE AYUDA  ---
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
        
        # Corrección: asegurar que month_names se defina incluso si el df está vacío
        if 'meses' not in locals():
             month_names = [calendar.month_name[i] for i in range(1, 13)]
        else:
             month_names = meses

        total_activities_by_month = list_provisional if list_provisional else [0] * len(month_names)
        df_activities = pd.DataFrame({
            "MONTH": month_names,
            "TOTAL_ACTIVITIES": total_activities_by_month,
        })
        return df_activities

    def generate_graph(self, forecast, budget, activities_data):
        """
        Genera el gráfico forecast vs real vs plan para Completions.
        """
        from services.graph_generator import create_budget_forecast_graph
        opex_budget = self.opex_manager.get_opex_for_line("1.03 Completions")
        plan_data = self.generate_plan_data(opex_budget)

        # Usamos la nueva función get_total_activities
        capacity_df = self.get_total_activities()
        capacity_df.rename(columns={'TOTAL_ACTIVITIES': 'FORECASTED_OPEX_ACT'}, inplace=True)

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
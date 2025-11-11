import pandas as pd
import calendar
import os
from logic.plan_actividades1 import PlanAnualActividades1
from logic.reports.base_report import LineReport
from utils.dates import get_all_months, get_month_number, normalize_month_names
from utils.file_manager import get_catalog_path, get_forecasted_plan_path, get_mi_swaco_config_path

class MISwacoReport(LineReport):
    """
    Reporte para la línea 1.2 M-I Swaco.
    
    Lógica Híbrida:
    - Carga el plan de actividades automático.
    - Carga el plan manual de "ofensores".
    - Calcula el costo de (9-2) actividades normales.
    - Suma el costo específico de las 2 actividades ofensor.
    """

    # --- 3. __init__ ---
    def __init__(self, data_loader, year, operative_capacity, opex_manager, plan_actividades):
        super().__init__(data_loader)
        self.year = year
        self.operative_capacity = operative_capacity
        self.opex_manager = opex_manager
        self.plan_actividades = plan_actividades
        self.average_cost_per_activity = None
        
        # Cargamos el catálogo de costo normal al inicio
        if self.average_cost_per_activity is None:
            self.load_catalog()
            
        # Cargamos y procesamos el config de ofensores
        self.df_config_ofensor = self.load_mi_swaco_config()
        
        # Procesamos el config para tenerlo listo (agrupado por MONTH)
        self.ofensor_cost_by_month = self.df_config_ofensor.groupby('MONTH')['AVG_QUANTITY'].sum().to_dict()
        self.ofensor_count_by_month = self.df_config_ofensor.groupby('MONTH').size().to_dict()
        
        print(f"MI Swaco Ofensor: Costos por mes cargados: {self.ofensor_cost_by_month}")
        print(f"MI Swaco Ofensor: Conteo por mes cargado: {self.ofensor_count_by_month}")

    def load_catalog(self):
        """
        Carga el costo promedio (NORMAL) desde el catálogo.
        """
        catalog_df = self.data_loader.load_catalog_data(get_catalog_path(), sheet_name="MI SWACO")

        # Filtra por la fila que tenga la descripción 'Costo promedio'
        # Usamos .str.contains para ser más robustos
        row = catalog_df[catalog_df['Descripción'].fillna('').str.strip().str.lower() == 'costo promedio']

        if row.empty:
            raise ValueError("No se encontró una fila con 'Costo promedio' en la columna 'Descripción' del catálogo MI SWACO.")

        self.average_cost_per_activity = float(row['Valor'].values[0])
        print(f"📚 MI Swaco: Costo promedio NORMAL cargado: {self.average_cost_per_activity}")

    # --- 4. NUEVA FUNCIÓN (Patrón de Tubulars) ---
    def load_mi_swaco_config(self):
        """
        Carga el archivo de configuración manual de MI Swaco (Ofensores).
        """
        config_path = get_mi_swaco_config_path()
        if not os.path.exists(config_path):
            print("Advertencia: No se encontró 'mi_swaco_config.xlsx'. Se usará un forecast 100% automático.")
            # Retorna un DF vacío con las columnas que esperamos
            return pd.DataFrame(columns=["MONTH", "TYPE", "ACTIVITIES", "AVG_QUANTITY"])
        
        try:
            df = pd.read_excel(config_path)
            
            # --- Compatibilidad con nombres viejos y nuevos ---
            # (El config puede tener nombres en Español/minúscula o Inglés/MAYÚSCULA)
            
            if "AVG_QUANTITY" not in df.columns:
                if "AVG POR ACTIVIDAD" in df.columns:
                    df.rename(columns={"AVG POR ACTIVIDAD": "AVG_QUANTITY"}, inplace=True)
                elif "avg_quantity" in df.columns:
                    df.rename(columns={"avg_quantity": "AVG_QUANTITY"}, inplace=True)

            if "MONTH" not in df.columns:
                if "Month" in df.columns:
                    df.rename(columns={"Month": "MONTH"}, inplace=True)
                elif "month" in df.columns:
                    df.rename(columns={"month": "MONTH"}, inplace=True)

            # Asegurarse de que las columnas clave existan
            if "MONTH" not in df.columns or "AVG_QUANTITY" not in df.columns:
                 print(f"ADVERTENCIA: 'mi_swaco_config.xlsx' no tiene las columnas 'MONTH' o 'AVG_QUANTITY'. No se cargarán datos de ofensor.")
                 return pd.DataFrame(columns=["MONTH", "TYPE", "ACTIVITIES", "AVG_QUANTITY"])

            # Convertir nombres de mes a estándar (Enero -> January)
            df["MONTH"] = normalize_month_names(df["MONTH"])
            df["AVG_QUANTITY"] = pd.to_numeric(df["AVG_QUANTITY"], errors='coerce').fillna(0)
            
            print(f"✅ Cargado 'mi_swaco_config.xlsx' con {len(df)} actividades ofensor.")
            # Filtramos solo las columnas que necesitamos
            return df[["MONTH", "AVG_QUANTITY"]]
            
        except Exception as e:
            print(f"ERROR: No se pudo leer 'mi_swaco_config.xlsx'. Se usará un forecast 100% automático. Error: {e}")
            return pd.DataFrame(columns=["MONTH", "TYPE", "ACTIVITIES", "AVG_QUANTITY"])

    # --- 5. generate_forecast  ---
    def generate_forecast(self):
        """
        Genera el forecast mensual aplicando la lógica híbrida de sustitución.
        """
        
        # 1. Cargar el Plan Automático
        plan_path = get_forecasted_plan_path(self.year)
        # Asegúrate de que PlanAnualActividades1 es el correcto, tu archivo lo usa.
        plan_provider = PlanAnualActividades1(self.data_loader, plan_path) 
        distribucion_df = plan_provider.calcular_distribucion_por_tipo(year=self.year)

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
             # Esto no debería pasar si __init__ funcionó
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
            # (mes está en Inglés, ej. "January")
            
            # a. Obtener total automático
            actividades_automaticas = distribucion_df[mes].sum()
            
            # b. Obtener datos del plan ofensor (cargados en __init__)
            num_actividades_ofensor = self.ofensor_count_by_month.get(mes, 0)
            costo_total_ofensor = self.ofensor_cost_by_month.get(mes, 0.0)
            
            # c. Calcular actividades normales
            actividades_normales = actividades_automaticas - num_actividades_ofensor
            
            # (Seguridad: si el config tiene más actividades que el plan, no restar)
            if actividades_normales < 0:
                print(f"Advertencia en {mes}: Hay {num_actividades_ofensor} actividades ofensor pero solo {actividades_automaticas} en el plan. Se asumirán 0 actividades normales.")
                actividades_normales = 0
            
            # d. Calcular costo normal
            costo_normal = actividades_normales * self.average_cost_per_activity
            
            # e. Costo total del mes
            costo_forecast_mes = costo_normal + costo_total_ofensor
            
            # Guardar datos
            data["TOTAL_ACTIVITIES"][idx] = actividades_automaticas # Reportamos el total (9)
            data["FORECAST_COST"][idx] = costo_forecast_mes

        forecast_df = pd.DataFrame(data)

        # 5. Cargar presupuesto real
        budget_df = self.generate_budget().rename(columns={"Budget": "ACTUAL_COST"})
        forecast_df = forecast_df.merge(budget_df, on="MONTH", how="left")

        # 6. Determinar presupuesto final
        forecast_df["BUDGET"] = forecast_df["FORECAST_COST"]
        forecast_df.loc[forecast_df["ACTUAL_COST"].notna(), "BUDGET"] = forecast_df["ACTUAL_COST"]

        # 7. Calcular acumulado
        forecast_df["CUMULATIVE_FORECAST"] = forecast_df["BUDGET"].cumsum()

        # 8. Guardar resultados
        #forecast_df.to_excel(r"summary/mi_swaco/forecast_data_mi_swaco.xlsx", index=False)

        print("\n📊 RESUMEN FORECAST MI SWACO (Híbrido):")
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
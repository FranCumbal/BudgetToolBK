import os
import pandas as pd
import re
from datetime import datetime, timedelta
import calendar

from logic.activity_data import build_activities_dataframe
from logic.reports.base_report import LineReport
from utils.dates import normalize_month_names, get_month_number, get_all_months, calculate_duration
from utils.file_manager import get_forecast_services_path_file, get_selected_services_wells_path


class ServicesReport(LineReport):

  
    """
    Reporte para la línea 1.10 Services.

    Este reporte permite calcular el forecast mensual combinando:
    - Actividades ejecutadas en meses actuales (desde CDF).
    - Actividades planeadas del año (desde el plan anual).
    - Costos históricos por pozo (basado en pozos seleccionados manualmente).

    También considera la duración estimada por pozo para calcular el costo mensual
    proyectado por actividad planificada.
    """

    def __init__(self, data_loader, year, operative_capacity, plan_actividades, opex_manager):
        """
        Inicializa el reporte para la línea 1.10 Services.

        :param data_loader: Objeto que permite acceder a los datos históricos y de configuración.
        :param year: Año del forecast.
        :param operative_capacity: DataFrame con la capacidad operativa mensual.
        :param plan_actividades: Objeto con el plan anual de actividades.
        :param opex_manager: Objeto que contiene el OPEX asignado por línea.
        """
        super().__init__(data_loader)
        self.year = year
        self.operative_capacity = pd.DataFrame(operative_capacity)
        self.plan_actividades = plan_actividades
        self.selected_wells = set()
        self.custom_duration = None
        self.target_cost = None
        self.opex_manager = opex_manager
        self.validated_paths = []

    def load_available_wells(self):
        """Carga los datos de pozos con costos históricos para la línea 1.10 Services."""
        df = self.data_loader.load_budget_data_per_year(self.year)
        cols = [c for c in ["YEAR", "MONTH", "WELL", "1.10 Services"] if c in df.columns]
        df = df[cols].dropna(subset=["1.10 Services", "WELL"])
        df["WELL"] = df["WELL"].astype(str)
        return df
    
    def _load_validated_paths_from_csv(self):
        """
        Lee el archivo CSV de configuración, extrae las rutas validadas (costo y días)
        y las devuelve en una lista de IDs internos.
        """
        try:
            df = pd.read_csv(get_forecast_services_path_file())
            # Mapeo de los nombres en el CSV a los IDs internos que usas en tu lógica
            NAME_TO_ID_MAPPING = {
                "Costo Target": "costo_target",
                "Costo Promedio": "costo_promedio",
                "Costo Total": "costo_total",
                "Dias Target": "dias_target",
                "Dias Promedio": "dias_promedio"
            }
            validated = []
            # Buscar el costo validado
            costo_validado_row = df[df['Validacion Costos'] == True]
            if not costo_validado_row.empty:
                costo_name = costo_validado_row.iloc[0]['Ruta Costos']
                if costo_name in NAME_TO_ID_MAPPING:
                    validated.append(NAME_TO_ID_MAPPING[costo_name])
            # Buscar los días validados
            dias_validados_row = df[df['Validacion Dias'] == True]
            if not dias_validados_row.empty:
                dias_name = dias_validados_row.iloc[0]['Ruta Dias']
                if dias_name in NAME_TO_ID_MAPPING:
                    validated.append(NAME_TO_ID_MAPPING[dias_name])
            return validated
        except FileNotFoundError:
            Exception("⚠️ Archivo de rutas de forecast no encontrado. Se usarán valores por defecto.")
            return []
        except Exception as e:
            Exception(f"❌ Error leyendo el CSV de rutas: {e}")
            return []

    def load_well_durations(self):
        """Carga la duración histórica en días de cada pozo."""
        return self.data_loader.calcular_duracion_promedio()

    def load_selected_wells(self, file_path):
        """Carga desde un archivo Excel la lista de pozos seleccionados manualmente por el usuario."""
        if os.path.exists(file_path):
            df = pd.read_excel(file_path)
            self.set_selected_wells(df["WELL"].tolist())

    def set_selected_wells(self, wells: list[str]):
        """Define manualmente la lista de pozos a considerar para el cálculo de costos promedio."""
        self.selected_wells = set(wells)

    def set_manual_duration(self, duration_days: float):
        """Establece una duración promedio manual (en días) por pozo."""
        self.custom_duration = duration_days

    def set_manual_input_target_cost(self, target_cost: float):
        """Establece un costo objetivo manual para el cálculo del forecast."""
        self.target_cost = target_cost

    def get_target_cost(self):
        """Devuelve el costo objetivo manual establecido."""
        return self.target_cost
    
    def get_custom_duration(self):
        """Devuelve la duración promedio manual establecida."""
        return self.custom_duration

    def calculate_average_cost_per_day(self, df_budget, df_durations):
        """
        Calcula el costo promedio por día para los pozos seleccionados.

        :param df_budget: DataFrame con costos históricos por pozo.
        :param df_durations: DataFrame con duración histórica por pozo.
        :return: Costo promedio diario.
        """
        df = df_budget[df_budget["WELL"].isin(self.selected_wells)].copy()
        df = df.merge(df_durations, left_on="WELL", right_on="ITEM_NAME", how="left")
        df["cost_per_day"] = df["1.10 Services"] / df["DURACION_DIAS"]
        df = df[df["cost_per_day"] > 0]
        return df["cost_per_day"].mean()
    
    def calculate_average_days_duration(self, df_budget, df_durations):
        """
        Calcula la duración promedio en días para los pozos seleccionados.

        :param df_budget: DataFrame con costos históricos por pozo.
        :param df_durations: DataFrame con duración histórica por pozo.
        :return: Duración promedio en días.
        """
        df = df_budget[df_budget["WELL"].isin(self.selected_wells)].copy()
        df = df.merge(df_durations, left_on="WELL", right_on="ITEM_NAME", how="left")
        return df["DURACION_DIAS"].mean()

    def get_activity_distribution(self):
        """
        Construye la distribución mensual de actividades:
        - Usa CDF para los meses actual y siguiente.
        - Usa el plan anual para el resto de meses.
        :return: Lista de 12 enteros representando el número de actividades por mes.
        """
        mes_actual = datetime.today().month
        mes_siguiente = (datetime.today().replace(day=28) + timedelta(days=4)).month

        cdf = self.data_loader.load_from_cognite()
        cdf = calculate_duration(cdf)
        cdf = cdf[cdf["End"].dt.year == self.year]
        cdf = cdf[cdf["activity_type"].isin([f"C1.{i}" for i in range(1, 17)])]

        actividades_mes = [0] * 12
        actividades_mes[mes_actual - 1] = cdf[cdf["End"].dt.month == mes_actual].shape[0]
        actividades_mes[mes_siguiente - 1] = cdf[cdf["End"].dt.month == mes_siguiente].shape[0]
        print("CDF")
        print(actividades_mes)

        distribucion_df = self.plan_actividades.calcular_distribucion_por_tipo(year=self.year)
        distribucion_df.columns = [
            normalize_month_names(pd.Series([c.strip()])).iloc[0]
            if c.strip() not in ["No.", "Tipo de Actividad", "Total"] else c.strip()
            for c in distribucion_df.columns
        ]
        columnas_mes = [c for c in distribucion_df.columns if c not in ["No.", "Tipo de Actividad", "Total"]]
        for col in columnas_mes:
            num_mes = get_month_number(col)
            if num_mes not in [mes_actual, mes_siguiente] and num_mes != "Invalid month name":
                actividades_mes[num_mes - 1] = int(distribucion_df[col].sum())
        
        return actividades_mes

    def get_costos_y_duracion(self, df_budget, df_durations):
        """
        Devuelve estadísticas de referencia para los pozos:
        - Promedio general de costo por día.
        - Promedio por pozos seleccionados.
        - Duración promedio histórica.
        """
        df = df_budget.merge(df_durations, left_on="WELL", right_on="ITEM_NAME", how="left")
        df["cost_per_day"] = df["1.10 Services"] / df["DURACION_DIAS"]

        promedio_total = df["cost_per_day"].dropna().mean()
        df_sel = df[df["WELL"].isin(self.selected_wells)]
        promedio_sel = df_sel["cost_per_day"].dropna().mean()
        duracion_prom = df["DURACION_DIAS"].dropna().mean()

        return promedio_sel, promedio_total, duracion_prom

    def set_validated_paths(self, registros_validados):
        """
        Recibe una lista de rutas validadas y las imprime (para pruebas).
        """
        self.validated_paths = registros_validados
        print("[ServicesReport] Rutas validadas recibidas:")
        print(self.validated_paths)

    def get_conditioned_paths(self):
        """
        Devuelve el valor de costo y días según el id validado seleccionado.
        """
        if not self.validated_paths:
            self.validated_paths = self._load_validated_paths_from_csv()
        # Buscar directamente los IDs específicos de costo
        cost_patterns = [r"costo_target", r"costo_promedio", r"costo_total"]
        cost_id = next((id_ for id_ in self.validated_paths if any(re.search(pattern, id_) for pattern in cost_patterns)), None)
        days_id = next((id_ for id_ in self.validated_paths if self.is_input_days(id_)), None)

        # Costo - Verificar los 3 tipos posibles
        if cost_id == "costo_target":
            cost_selected = self.get_target_cost()
        elif cost_id == "costo_promedio":
            cost_selected = self.get_cost_per_day_automatically()
        elif cost_id == "costo_total":
            cost_selected = self.get_total_avg_cost()
        else:
            cost_selected = self.get_cost_per_day_automatically()
            
        # Días
        if days_id == "dias_target":
            days_selected = self.get_custom_duration() if self.get_custom_duration() > 0 else 1
        elif days_id == "dias_promedio":
            days_selected = self.get_avg_day_duration_automatically() if self.get_avg_day_duration_automatically() > 0 else 1
        else:
            days_selected = self.get_avg_day_duration_automatically()
        print("GENERAL A VER")
        print(cost_selected, " | ",days_selected)
        return cost_selected, days_selected

    def get_services_variables_from_csv(self):
        """
        Lee el CSV y devuelve los valores de costo y días seleccionados.
        """
        df = pd.read_csv(get_forecast_services_path_file())
        print("ACA EL DF DEL CSV")
        print(df)
        
    def get_cost_per_day_automatically(self):
        df_budget = self.load_available_wells()
        df_durations = self.load_well_durations()
        df_budget["WELL"] = df_budget["WELL"].str.strip().str.upper()
        df_durations["ITEM_NAME"] = df_durations["ITEM_NAME"].str.strip().str.upper()
        cost_per_day = self.calculate_average_cost_per_day(df_budget, df_durations)     
        return cost_per_day
    
    def get_avg_day_duration_automatically(self):
        df_budget = self.load_available_wells()
        df_durations = self.load_well_durations()
        df_budget["WELL"] = df_budget["WELL"].str.strip().str.upper()
        df_durations["ITEM_NAME"] = df_durations["ITEM_NAME"].str.strip().str.upper()
        avarage_days_duration = self.calculate_average_days_duration(df_budget, df_durations)
        return avarage_days_duration
    
    def get_total_avg_cost(self):
        df_budget = self.load_available_wells()
        df_durations = self.load_well_durations()
        duracion_total_promedio_dataframe = self.load_well_durations()
        # Renombrar columna de servicios
        df_budget = df_budget.rename(columns={"WELL": "ITEM_NAME"})
        
        # Asegurar que el valor monetario esté como float
        df_budget["1.10 Services"] = df_budget["1.10 Services"].astype(float)
        print("ACA EL BUDGET")
        print(df_budget)
        print("ACA EL DF DE DURACION")
        print(duracion_total_promedio_dataframe)

        # Realizar merge usando la columna 'ITEM_NAME' como clave
        df_merged = df_budget.merge(
            duracion_total_promedio_dataframe,
            on="ITEM_NAME",
            how="inner"
        )

        # Calcular el costo promedio por pozo
        df_merged["COSTO_PROMEDIO_POR_POZO"] = df_merged["1.10 Services"] / df_merged["DURACION_DIAS"]

        print("COSTO PROMEDIO POR POZO")
        print(df_merged[["ITEM_NAME", "1.10 Services", "DURACION_DIAS", "COSTO_PROMEDIO_POR_POZO"]])

        # Calcular el promedio total
        avrg_total_cost = df_merged["COSTO_PROMEDIO_POR_POZO"].mean()

        print("COSTO PROMEDIO TOTAL POR POZO")
        print(avrg_total_cost)

        return avrg_total_cost


    def is_input_days(self, id_):
        # Verifica si el ID corresponde a un input de días.
        if re.search(r"dias_target_input", id_):
            return True
        return False

    def generate_forecast(self):
        """
        Genera el forecast mensual para la línea 1.10 Services usando el forecast plan CSV.
        """
        df_budget = self.load_available_wells()
        df_durations = self.load_well_durations()

        df_budget["WELL"] = df_budget["WELL"].str.strip().str.upper()
        df_durations["ITEM_NAME"] = df_durations["ITEM_NAME"].str.strip().str.upper()

        selected_path = get_selected_services_wells_path()
        self.load_selected_wells(selected_path)

        # Cálculo de promedios para el resumen
        promedio_sel, promedio_total, duracion_prom = self.get_costos_y_duracion(df_budget, df_durations)
        costo_dia, duracion = self.get_conditioned_paths()
        
        # Asegurarse de que costo_dia y duracion no sean None
        costo_dia = costo_dia or 0
        duracion = duracion or 0

        actividades_mes = self.get_activity_distribution()
        months = [calendar.month_name[i] for i in range(1, 13)]
        forecast_df = pd.DataFrame({"MONTH": months, "PLANNED_ACTIVITIES": actividades_mes})
        forecast_df['FORECAST_COST'] = forecast_df['PLANNED_ACTIVITIES'] * duracion * costo_dia
        budget_df = self.generate_budget()
        final_df = forecast_df.merge(budget_df, on="MONTH", how="left")
        final_df.rename(columns={"Budget": "ACTUAL_COST"}, inplace=True)
        final_df["BUDGET"] = final_df["FORECAST_COST"]
        final_df.loc[final_df["ACTUAL_COST"].notna(), "BUDGET"] = final_df["ACTUAL_COST"]
        final_df["CUMULATIVE_FORECAST"] = final_df["BUDGET"].cumsum()

        # 🔹 Resumen de cálculo
        print("\n--- Resumen de Forecast para 1.10 Services ---")
        print(f"➤ Costo promedio por día (todos los pozos): ${promedio_total:,.2f}")
        print(f"➤ Costo promedio por día (pozos seleccionados): ${promedio_sel:,.2f}")
        print(f"➤ Duración promedio histórica: {duracion_prom:.2f} días")
        print(f"➤ Duración usada para forecast: {duracion:.2f} días")
        print(f"➤ Costo diario final utilizado: ${costo_dia:,.2f}")
        print("\n➤ Actividades planificadas por mes:")
        for _, row in forecast_df.iterrows():
            print(f"   {row['MONTH']}: {row['PLANNED_ACTIVITIES']} actividades")
        print(f"\n➤ Costo total estimado (forecast): ${final_df['FORECAST_COST'].sum():,.2f}")
        print("--------------------------------------------\n")

        return final_df


    def generate_budget(self):
        """Carga el presupuesto real para la línea 1.10 Services."""
        return self.data_loader.load_budget_for_line(self.year, "1.10 Services")

    def generate_deviations(self):
        return pd.DataFrame()

    def generate_plan_data(self, opex_budget: float) -> pd.DataFrame:
        """Distribuye el OPEX total en los 12 meses del año."""
        months = get_all_months()
        monthly_value = opex_budget / 12
        return pd.DataFrame({"MONTH": months, "PLANNED_COST": [monthly_value] * 12})
    
    def generate_forecast_by_path(self, cost_avarage, day_avarage_override):
        """
        Genera el forecast mensual para la línea 1.10 Services, usando SIEMPRE los valores enviados
        """
        validated = []
        validated.append(cost_avarage)
        validated.append(day_avarage_override)
        self.set_validated_paths(validated)

        # Llama al método estándar
        df = self.generate_forecast()
        executed_activities_df = self.get_executed_activities_dataframe()

        information_df = df.merge(executed_activities_df, on="MONTH", how="left")

        # Selecciona solo las columnas que te interesan
        columnas = ["MONTH", "PLANNED_ACTIVITIES", "EXECUTED_ACTIVITIES", "FORECAST_COST", "CUMULATIVE_FORECAST"] 
        return information_df[columnas]

    def get_executed_activities_dataframe(self):
        # Esta logica se deberia implementar en la clase, no en el controlador o en un archivo de gestion a parte cuando la responsabilidad 
        # es de la propia clase/clases que lo necesiten. En todo caso, generar un servicio, no un archivo .py sin sentido.
        activities_data_dataframe = build_activities_dataframe(self.data_loader, self.plan_actividades, year=datetime.now().year)
        return activities_data_dataframe[["MONTH", "EXECUTED_ACTIVITIES"]]
         
    def generate_graph(self, forecast, budget, activities_data):
        """Genera el gráfico comparativo Forecast vs Real vs Plan."""
        from services.graph_generator import create_budget_forecast_graph

        opex_budget = self.opex_manager.get_opex_for_line("1.10 Services")
        plan_data = self.generate_plan_data(opex_budget)

        cap_df = self.operative_capacity[["Mes", "Numero tentativo de pozos OPEX"]].copy()
        month_map = {i + 1: m for i, m in enumerate(get_all_months())}
        cap_df["MONTH"] = cap_df["Mes"].map(month_map)
        cap_df.rename(columns={"Numero tentativo de pozos OPEX": "FORECASTED_OPEX_ACT"}, inplace=True)
        capacity_df = cap_df[["MONTH", "FORECASTED_OPEX_ACT"]]

        return create_budget_forecast_graph(
            forecast=forecast,
            budget_data=budget,
            plan_data=plan_data,
            activities_data=activities_data,
            title="1.10 Services",
            capacity_data=capacity_df
        )

from services.field_lines_services.executed_plan import ExecutedActivitiesPlan
from utils.months_utils import MONTH_ES_TO_MONTH_EN, SORTED_MONTHS
import pandas as pd
from datetime import datetime

class ExecutedActivitiesManager:
    """
    Gestiona el acceso y procesamiento de los datos de actividades ejecutadas.

    Esta clase carga los datos desde un plan de Excel, los pre-procesa y ofrece
    métodos para consultar costos reales, conteo de actividades y otros datos
    filtrados por mes y línea de servicio.
    """
    def __init__(self):
        """
        Inicializa el gestor, carga los datos de actividades ejecutadas y los pre-procesa.
        """
        self.df = ExecutedActivitiesPlan().get_executed_data_from_excel()
        self.meses_ordenados = SORTED_MONTHS
        self.meses_ingles = ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december']
        if self.df is not None and not self.df.empty:
            self._preprocess_df()
        else:
            self.df = pd.DataFrame()
        
    def convert_columns_to_numeric(self, column_names):
        """
        Convierte de forma segura una lista de columnas del DataFrame a tipo numérico.
        Los valores que no se puedan convertir se transformarán en NaN.
        """
        for col in column_names:
            if col in self.df.columns:
                self.df[col] = pd.to_numeric(self.df[col], errors='coerce')

    def _preprocess_df(self):
        """
        Pre-procesa el DataFrame interno para estandarizar los datos.

        Limpia y normaliza la columna 'Month', traduciéndola a inglés y
        estableciendo un orden categórico para asegurar la correcta ordenación.
        """
        self.df['Month'] = self.df['Month'].str.strip().str.lower()
        self.df['Month'] = self.df['Month'].replace(MONTH_ES_TO_MONTH_EN)
        self.df['Month'] = self.df['Month'].str.lower()
        self.df['Month'] = pd.Categorical(self.df['Month'], categories=self.meses_ingles, ordered=True)
        self.df = self.df.sort_values('Month').reset_index(drop=True)

    def get_executed_activities_data_frame_by_month(self, month, line_name):
        """Filtra y devuelve un DataFrame con el detalle de actividades para un mes y línea."""
        month = month.strip().lower()
        servicios_col = f'{line_name}_Servicios'
        productos_col = f'{line_name}_Productos'
        b_and_h_col = f'{line_name}_B&H'
        self.convert_columns_to_numeric([servicios_col, productos_col, b_and_h_col])
        conditions = self.get_conditions_to_check_services_and_product(line_name, self.df, month)
        filtered_df = self.df[conditions]
        columnas = ['WELL', 'STATUS', 'Month', servicios_col]
        if productos_col in filtered_df.columns:
            columnas.append(productos_col)
        if b_and_h_col in filtered_df.columns:
            columnas.append(b_and_h_col)
        return filtered_df[columnas]
    
    def get_last_index_month_in_excel(self):
        """
        Obtiene el índice numérico (0-11) del último mes con datos en el Excel.
        """
        valid_months_df = self.df[self.df['Month'].notna()] 
        last_valid_month = valid_months_df['Month'].iloc[-1]
        month_indices = self.df['Month'].dropna().unique().tolist()
        last_index_month = month_indices.index(last_valid_month)
        return last_index_month
    
    def get_executed_activities_data_frame_by_month_to_draw(self, month, line_name):
        """
        Obtiene el detalle de actividades para un mes, excluyendo las 'adicionales'.

        Este método está pensado para generar gráficos que solo deben mostrar
        las actividades planificadas y ejecutadas, no las adicionales.
        """
        month = month.strip().lower()
        servicios_col = f'{line_name}_Servicios'
        productos_col = f'{line_name}_Productos'
        # ✅ Conversión segura a numérico
        self.convert_columns_to_numeric([servicios_col, productos_col])
        conditions = self.get_conditions_to_check_services_and_product_to_draw(line_name, self.df, month)
        filtered_df = self.df[conditions]
        columnas = ['WELL', 'Month', servicios_col]
        if productos_col in filtered_df.columns:
            columnas.append(productos_col)
        return filtered_df[columnas]

    def get_executed_activities_accumulated_df_by_column_from_excel(self, meses, line_name):
        """
        Obtiene el acumulado de actividades desde una columna de resumen en Excel.

        Es usado por reportes como Echometer, que tienen una columna específica
        con el total de actividades ejecutadas.
        """
        df_mes = self._get_executed_activities_sum_by_month(meses, line_name, status_filter=['final', 'pend.'])
        df_mes['Executed Activities'] = df_mes['Executed Activities'].cumsum()
        return df_mes
    
    def get_executed_activities_df_by_column_from_excel_monthly_distributed(self, meses, line_name):
        """
        Obtiene el total mensual de actividades desde una columna de resumen en Excel.
        """
        df_mes = self._get_executed_activities_sum_by_month(meses, line_name, status_filter=['final', 'pend.'])
        return df_mes
    
    def get_echometer_executed_activities_monthly(self, meses, line_name):
        """
        Método específico para obtener las actividades mensuales acumuladas de Echometer.
        """
        return self.get_executed_activities_accumulated_df_by_column_from_excel(meses, line_name)

    def _get_executed_activities_sum_by_month(self, meses, line_name, status_filter=None):
        """
        Helper privado para sumar actividades de una columna específica por mes.

        Busca una columna como '{line_name}_Act. Ejecutadas' y suma sus valores
        para cada mes, aplicando un filtro de estado opcional.
        """
        act_ejecutadas_col = f'{line_name}_Act. Ejecutadas'
        if act_ejecutadas_col not in self.df.columns:
            self.df[act_ejecutadas_col] = 0
        df = self.df[['Month', act_ejecutadas_col, 'STATUS']].copy() if 'STATUS' in self.df.columns else self.df[['Month', act_ejecutadas_col]].copy()
        df['Month'] = df['Month'].str.strip().str.lower().replace(MONTH_ES_TO_MONTH_EN).str.lower()
        df[act_ejecutadas_col] = pd.to_numeric(df[act_ejecutadas_col], errors='coerce').fillna(0).astype(int)
        if status_filter and 'STATUS' in df.columns:
            if isinstance(status_filter, (list, tuple, set)):
                status_filter_set = set([s.strip().lower() for s in status_filter])
                df = df[df['STATUS'].str.strip().str.lower().isin(status_filter_set)]
            else:
                df = df[df['STATUS'].str.strip().str.lower() == status_filter.strip().lower()]
        meses_lower = [m.lower() for m in meses]
        activities_data = []
        for month in meses_lower:
            total = df.loc[df['Month'] == month, act_ejecutadas_col].sum() if month in df['Month'].values else 0
            activities_data.append({"Month": month, "Executed Activities": int(total)})
        df_result = pd.DataFrame(activities_data)
        return df_result
    
    def generate_executed_activities_data_frame(self, months, line_name):
        """
        Genera un DataFrame con el conteo de actividades ejecutadas para cada mes.
        """
        activities_data = []
        for month in months:
            executed_activities = self.get_executed_activities_by_month_to_draw(month.lower(), line_name)
            activities_data.append({"Month": month.lower(), "Executed Activities": executed_activities})
        df_executed_activities = pd.DataFrame(activities_data)
        df_executed_activities['Executed Activities'] = df_executed_activities['Executed Activities']
        return df_executed_activities
    
    def generate_executed_activities_data_frame_to_draw(self, months, line_name):
        """
        Genera un DataFrame con el conteo de actividades para graficar.

        Excluye actividades 'adicionales' para no distorsionar los gráficos.
        """
        activities_data = []
        for month in months:
            executed_activities = self.get_executed_activities_by_month_to_draw(month.lower(), line_name)
            activities_data.append({"Month": month.lower(), "Executed Activities": executed_activities})
        df_executed_activities = pd.DataFrame(activities_data)
        df_executed_activities['Executed Activities'] = df_executed_activities['Executed Activities']
        return df_executed_activities

    def get_executed_activities_by_month(self, month, line_name):
        """
        Devuelve el número (conteo) de actividades ejecutadas para un mes y línea.
        """
        if month not in self.meses_ingles:
            raise ValueError(f"Mes '{month}' no está en la lista de meses válidos.")
        filtered = self.get_executed_activities_data_frame_by_month(month, line_name)
        return filtered.shape[0]
    
    def get_executed_activities_by_month_to_draw(self, month, line_name):
        """
        Devuelve el conteo de actividades para graficar (excluye 'adicionales').
        """
        if month not in self.meses_ingles:
            raise ValueError(f"Mes '{month}' no está en la lista de meses válidos.")
        filtered = self.get_executed_activities_data_frame_by_month_to_draw(month, line_name)
        return filtered.shape[0]

    def get_total_real_cost_by_month(self, month, line_name):
        """
        Calcula el costo real total para un mes sumando servicios y productos.
        """
        try:
            df_total = self.get_executed_activities_data_frame_by_month(month, line_name)
        except ValueError:
            return 0.0
        servicios_col = f'{line_name}_Servicios'
        productos_col = f'{line_name}_Productos'
        servicios_sum = df_total[servicios_col].sum() if servicios_col in df_total.columns else 0.0
        productos_sum = df_total[productos_col].sum() if productos_col in df_total.columns else 0.0

        return servicios_sum + productos_sum

    def generate_real_cost_data_frame(self, line_name):
        """
        Genera un DataFrame con el costo real total para cada mes del año.
        """
        full_english_months = self.meses_ingles
        data_to_real_cost = []
        for month in full_english_months:
            total = self.get_total_real_cost_by_month(month, line_name)
            data_to_real_cost.append({"Month": month, "TotalRealCost": total})
        return pd.DataFrame(data_to_real_cost)

    def generate_accumulated_real_cost_data_frame(self, line_name):
        """
        Genera un DataFrame con el costo real acumulado mes a mes.

        La acumulación se detiene y se mantiene constante después del último mes
        que contiene datos en el archivo de origen.
        """
        df_acummulated_cost = self.generate_real_cost_data_frame(line_name)
        accumulated = []
        prev_accumulated = 0
        self.df['Month'] = self.df['Month'].str.strip().str.lower()
        self.df['Month'] = self.df['Month'].replace(MONTH_ES_TO_MONTH_EN)
        last_month_in_df = self.df["Month"].dropna().iloc[-1].strip().lower()
        for index, row in df_acummulated_cost.iterrows():
            month_name = row["Month"].strip().lower()
            current_real_cost = row["TotalRealCost"]

            if self.meses_ingles.index(month_name) <= self.meses_ingles.index(last_month_in_df):
                current_accumulated = current_real_cost + prev_accumulated
            else:
                current_accumulated = 0 

            accumulated.append(current_accumulated)
            prev_accumulated = current_accumulated

        df_acummulated_cost["TotalAccumulatedCost"] = accumulated
        return df_acummulated_cost[["Month", "TotalAccumulatedCost"]]

    def get_conditions_to_check_services_and_product(self, line_name, df, month):
        """
        Construye y devuelve las condiciones para filtrar actividades ejecutadas.

        Considera una actividad como ejecutada si su estado es 'final', 'pend.' o
        'adicional' y tiene un costo asociado (en servicios, productos o B&H).
        """
        servicios_col = f'{line_name}_Servicios'
        productos_col = f'{line_name}_Productos'
        b_and_h_col = f'{line_name}_B&H'
        self.convert_columns_to_numeric([servicios_col, productos_col, b_and_h_col])
        has_productos = productos_col in df.columns
        has_b_and_h = b_and_h_col in df.columns
        is_final = df['STATUS'].str.strip().str.lower() == 'final' 
        is_aditional = df['STATUS'].str.strip().str.lower() == 'adicional' 
        is_pending = df['STATUS'].str.strip().str.lower() == 'pend.' 
        is_correct_month = df['Month'] == month
        valid_servicios = df[servicios_col].notna() & (df[servicios_col] > 0)
        if has_productos and has_b_and_h:
            valid_productos = (
                (df[productos_col].notna() & (df[productos_col] > 0)) |
                (df[b_and_h_col].notna() & (df[b_and_h_col] > 0))
            )
        elif has_productos:
            valid_productos = df[productos_col].notna() & (df[productos_col] > 0)
        elif has_b_and_h:
            valid_productos = df[b_and_h_col].notna() & (df[b_and_h_col] > 0)
        else:
            valid_productos = False
        conditions = (is_final | is_pending | is_aditional) & is_correct_month & (valid_servicios | valid_productos)
        return conditions
    
    def get_conditions_to_check_services_and_product_to_draw(self, line_name, df, month):
        """
        Construye las condiciones para filtrar actividades para gráficos.

        Es similar al otro método de condiciones, pero excluye explícitamente
        las actividades con estado 'adicional'.
        """
        servicios_col = f'{line_name}_Servicios'
        productos_col = f'{line_name}_Productos'
        self.convert_columns_to_numeric([servicios_col, productos_col])
        has_productos = productos_col in df.columns
        is_final = df['STATUS'].str.strip().str.lower() == 'final'
        is_pending = df['STATUS'].str.strip().str.lower() == 'pend.' 
        is_correct_month = df['Month'] == month
        valid_servicios = df[servicios_col].notna() & (df[servicios_col] > 0)
        valid_productos = (
            df[productos_col].notna() & (df[productos_col] > 0)
            if has_productos else False
        )
        conditions = (is_final | is_pending) & is_correct_month & (valid_servicios | valid_productos)
        return conditions
    
    def get_total_executed_activities_data_frame(self, months, line_name):
        """
        Consolida todas las actividades ejecutadas de varios meses en un solo DataFrame.

        Añade columnas calculadas para el costo total con y sin B&H (Burning &
        Handling).
        """
        servicios_col = f'{line_name}_Servicios'
        productos_col = f'{line_name}_Productos'
        b_and_h_col = f'{line_name}_B&H'
        dfs = []
        for month in months:
            df_month = self.get_executed_activities_data_frame_by_month(month, line_name)
            for col in df_month.columns:
                if pd.api.types.is_numeric_dtype(df_month[col]):
                    df_month[col] = df_month[col].fillna(0)
            df_month['Total sin B&H'] = df_month[servicios_col] + df_month.get(productos_col, 0)
            if b_and_h_col in df_month.columns:
                df_month['Total con B&H'] = df_month[servicios_col] + df_month.get(productos_col, 0) + df_month.get(b_and_h_col, 0)
            else:
                df_month['Total con B&H'] = df_month['Total sin B&H']
            dfs.append(df_month)
        if dfs:
            return pd.concat(dfs, ignore_index=True)
        else:
            return pd.DataFrame()
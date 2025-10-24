from datetime import datetime
import pandas as pd
from calendar import month_name

from services.field_lines_services.historical_initial_cost_service import HistoricalInitialCostService

class AnnualPTALoader:
    """
    Carga y procesa los datos del Plan de Trabajo Anual (PTA).

    Esta clase toma un DataFrame con los datos anuales aprobados (presupuesto y
    actividades) y proporciona métodos para distribuirlos a lo largo del año
    o para calcular métricas clave como el Costo Por Actividad (CPAE).
    """
    def __init__(self, df: pd.DataFrame):
        """
        Inicializa el cargador con los datos del PTA.

        Args:
            df (pd.DataFrame): Un DataFrame que contiene los datos anuales aprobados.
                               Debe incluir columnas para presupuesto y actividades.
        """
        self.df = None
        self._raw_df = df.copy()
        if "Actividades aprobadas" in self._raw_df.columns:
            self._raw_df.rename(columns={"Actividades aprobadas": "Planned Activities"}, inplace=True)
        self.TOTAL_MONTHS_NUMBER = 12

    def get_raw_df(self):
        """Devuelve el DataFrame original sin procesar."""
        return self._raw_df

    def automatic_distribution(self):
        """
        Distribuye el total de actividades planeadas uniformemente a lo largo de los 12 meses.

        Calcula una distribución base y asigna el resto de manera equitativa.

        Returns:
            pd.DataFrame: Un DataFrame con las actividades distribuidas por mes.
        """
        try:
            actual_year = datetime.now().year
            presupuesto_col = f"Presupuesto {actual_year}"
            if self._raw_df is None or "Planned Activities" not in self._raw_df.columns or presupuesto_col not in self._raw_df.columns:
                raise ValueError(f"❌ DataFrame inválido o sin columnas requeridas ('Planned Activities', '{presupuesto_col}').")
            planned_activities = int(self._raw_df["Planned Activities"].iloc[0])
            presupuesto_value = float(self._raw_df[presupuesto_col].iloc[0])
        except Exception as e:
            print(f"❌ Error procesando planificación anual: {e}")
            return pd.DataFrame()

        months = [month.lower() for month in month_name[1:]]
        base = planned_activities // 12
        remainder = planned_activities % 12
        distribution = [base + 1 if i < remainder else base for i in range(12)]

        df_auto = pd.DataFrame({
            "Month": months,
            "Planned Activities": distribution,
            presupuesto_col: [presupuesto_value] * 12
        })
        return df_auto
    
    def get_initial_approved_cost_df(self) -> pd.DataFrame:
        """
        Crea un DataFrame para representar el costo inicial aprobado como una línea estática.

        Extrae el valor del presupuesto total del año y crea un DataFrame donde
        cada mes tiene este mismo valor, útil para graficar una línea de referencia.
        """
        months = [month.lower() for month in month_name[1:]]
        actual_year = datetime.now().year
        presupuesto_col = f"Presupuesto {actual_year}"
        try:
            initial_planned_cost = float(self._raw_df[presupuesto_col].iloc[0])
        except (ValueError, TypeError, KeyError) as e:
            print(f"❌ Error al convertir '{presupuesto_col}' a float: {e}")
            initial_planned_cost = 0.0

        df_initial_planned_cost = pd.DataFrame({
            "Month": months,
            "VALUE": [0] * 12
        })
        df_initial_planned_cost['VALUE'] = initial_planned_cost
        return df_initial_planned_cost
    
    def get_initial_approved_cost_df_to_static_line(self) -> pd.DataFrame:
        """
        Obtiene el costo inicial aprobado desde el servicio histórico para líneas estáticas.

        Utiliza `HistoricalInitialCostService` para obtener un costo que no depende
        del PTA actual, sino de un valor guardado, y lo formatea en un DataFrame
        mensual para su visualización.
        """
        historical_initial_cost = HistoricalInitialCostService()
        df_historical_initial_cost = historical_initial_cost.get_dataframe()

        months = [month.lower() for month in month_name[1:]]
        actual_year = datetime.now().year
        try:
            row = df_historical_initial_cost[df_historical_initial_cost['Year'] == actual_year]
            if not row.empty:
                initial_planned_cost = float(row['Initial Cost Approved'].iloc[0])
            else:
                initial_planned_cost = 0.0
        except (ValueError, TypeError, KeyError, IndexError) as e:
            print(f"❌ Error al convertir valor de Initial Cost Approved a float: {e}")
            initial_planned_cost = 0.0

        df_initial_planned_cost = pd.DataFrame({
            "Month": months,
            "VALUE": [initial_planned_cost] * 12
        })
        return df_initial_planned_cost
    
    def get_budget_value_evently_distributed_by_year(self, year):
        """
        Calcula el valor del presupuesto distribuido uniformemente por mes para un año dado.
        """
        presupuesto_col = f"Presupuesto {year}"
        if self._raw_df is None or self._raw_df.empty:
            return 0
        value = self._raw_df[presupuesto_col].iloc[0] / self.TOTAL_MONTHS_NUMBER
        return round(value, 4)
    
    def get_cpae_value(self, year):
        '''
        Calcula el Costo Por Actividad (CPAE) para un año dado.

        Divide el presupuesto total del año entre el número total de actividades planeadas.
        Maneja el caso de división por cero si no hay actividades planeadas.
        '''
        presupuesto_col = f"Presupuesto {year}"
        if self._raw_df is None or self._raw_df.empty:
            return 0
        if self._raw_df["Planned Activities"].sum() == 0:
            return 1
        cpae_value = self._raw_df[presupuesto_col].iloc[0] / self._raw_df["Planned Activities"].sum() if self._raw_df["Planned Activities"].sum() != 0 else 0
        return round(cpae_value, 4)
    
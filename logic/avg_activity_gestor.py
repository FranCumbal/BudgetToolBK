
import datetime

import pandas as pd
from data.data_loader import DataLoader


class AvgActivityGestor():
    def __init__(self):
        """
        Gestor para calcular el promedio de actividades.
        """
        self.data_loader = DataLoader()
        self.year = datetime.datetime.now().year

    def generate_report_execution_dataframe_by_line(self, line_name):
        """
        Filtra el DataFrame de budget para los años 2023 y 2024 y actividad 'WO OPEX',
        devolviendo solo las columnas YEAR, ACTIVITY, TYPE, y '1.6 Wireline'.
        """
        df = self.data_loader.load_budget_data_all_years().copy()
        # Filtrar por años 2023 y 2024 (es variable si cambiamos de anio), siempre los dos anios anteriores al actual
        old_year = self.year - 2
        top_year = self.year - 1
        df = df[df['YEAR'].isin([old_year, top_year])]
        # Filtrar por actividad 'WO OPEX'
        df = df[df['ACTIVITY'] == 'WO OPEX']
        # Seleccionar columnas
        columns = ['YEAR', 'ACTIVITY', 'TYPE', line_name]
        filtered_df = df[columns].reset_index(drop=True)
        return filtered_df

    def get_avrg_by_type_and_range(self, types=None, min_value=None, max_value=None, line_name=None):
        """
        Calcula el promedio de cualquier linea para los tipos y rango dados. Si max_value es None, solo filtra por min_value.
        """
        df_complete = self.generate_report_execution_dataframe_by_line(line_name)
        if max_value is not None:
            df_complete = df_complete[(df_complete[line_name] >= min_value) & (df_complete[line_name] <= max_value)]
        else:
            df_complete = df_complete[df_complete[line_name] >= min_value]
        filtered_df = df_complete[df_complete['TYPE'].isin(types)] if types else df_complete
        avg = filtered_df[line_name].mean() if not filtered_df.empty else 0
        return avg


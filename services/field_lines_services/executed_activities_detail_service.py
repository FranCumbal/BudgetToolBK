import pandas as pd
from services.field_lines_services.executed_activities_manager import ExecutedActivitiesManager
from utils.file_loader import load_months_from_file

class ExecutedActivitiesDetailService:
    def __init__(self, line_name):
        self.line_name = line_name
        self.executed_manager = ExecutedActivitiesManager()
 
    def get_detail_dataframe(self):
        months = load_months_from_file()
        df = self.executed_manager.get_total_executed_activities_data_frame(months, self.line_name)
        # Renombrar columnas para la vista
        rename_dict = {
            f'{self.line_name}_Servicios': 'Costo Servicio',
            f'{self.line_name}_Productos': 'Costo Producto',
            f'{self.line_name}_B&H': 'Costo B&H',
            'WELL': 'Pozo',
            'STATUS': 'Estado',
            'Month': 'Mes',
            'Total sin B&H': 'Total sin B&H',
            'Total con B&H': 'Total con B&H',
        }
        # Solo dejar las columnas relevantes y renombrar
        columns = ['WELL', 'STATUS', 'Month', f'{self.line_name}_Servicios', f'{self.line_name}_Productos', f'{self.line_name}_B&H', 'Total sin B&H', 'Total con B&H']
        df = df[columns].rename(columns=rename_dict)
        # Normalizar nombres de mes
        df['Mes'] = df['Mes'].str.title()
        # Agregar fila "Total {mes}" después de cada cambio de mes, sumando los totales del mes
        if not df.empty:
            new_rows = []
            mes_rows = []
            for idx, row in df.iterrows():
                new_rows.append(row.to_dict())
                mes_rows.append(row)
                current_mes = row['Mes']
                next_mes = df['Mes'][idx+1] if idx+1 < len(df) else None
                if current_mes != next_mes:
                    # Sumar los totales del mes
                    total_sin_bh = pd.to_numeric([r['Total sin B&H'] for r in mes_rows], errors='coerce').sum()
                    total_con_bh = pd.to_numeric([r['Total con B&H'] for r in mes_rows], errors='coerce').sum()
                    empty_row = {col: '' for col in df.columns}
                    empty_row['Mes'] = f'Total {current_mes}'
                    empty_row['Total sin B&H'] = f'{total_sin_bh:,.2f}'
                    empty_row['Total con B&H'] = f'{total_con_bh:,.2f}'
                    new_rows.append(empty_row)
                    mes_rows = []
            df = pd.DataFrame(new_rows, columns=df.columns).reset_index(drop=True)
        # Formatear todos los valores numéricos a dos decimales con separador de miles
        if not df.empty:
            for col in df.columns:
                if col not in ['Mes', 'Pozo', 'Estado']:
                    def safe_format(x):
                        try:
                            return f"{float(str(x).replace(',', '')):,.2f}"
                        except Exception:
                            return x
                    df[col] = df[col].apply(safe_format)
        return df
    
    def get_executed_accumulated_activities_number(self):
        # cuenta el numero de registros de la columna "Pozo" que sea no none
        df = self.get_detail_dataframe()
        if df.empty:
            return 0
        return df['Pozo'].notna().sum()
    
    def get_total_without_b_and_h(self):
        df = self.get_detail_dataframe()
        if df.empty:
            return 0
        # Filtrar solo filas donde 'Mes' comienza con 'Total '
        df_total = df[df['Mes'].str.lower().str.startswith('total ')]
        total = df_total['Total sin B&H'].replace('', 0).replace(',', '', regex=True).astype(float).sum()
        return total
    
    def get_total_with_b_and_h(self):
        df = self.get_detail_dataframe()
        if df.empty:
            return 0
        df_total = df[df['Mes'].str.lower().str.startswith('total ')]
        total = df_total['Total con B&H'].replace('', 0).replace(',', '', regex=True).astype(float).sum()
        return total
    
    def get_avarage_by_activity_with_b_and_h(self):
        df = self.get_detail_dataframe()
        if df.empty:
            return 0
        df_total = df[df['Mes'].str.lower().str.startswith('total ')]
        total = df_total['Total con B&H'].replace('', 0).replace(',', '', regex=True).astype(float).sum()
        count = len(df_total)
        if count == 0:
            return 0
        return total / count
    
    def get_avarage_by_activity_without_b_and_h(self):
        df = self.get_detail_dataframe()
        if df.empty:
            return 0
        df_total = df[df['Mes'].str.lower().str.startswith('total ')]
        total = df_total['Total sin B&H'].replace('', 0).replace(',', '', regex=True).astype(float).sum()
        count = len(df_total)
        if count == 0:
            return 0
        return total / count

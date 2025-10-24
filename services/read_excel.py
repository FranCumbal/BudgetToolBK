import pandas as pd
from services.field_lines_services.anual_pta_loader import AnnualPTALoader
from services.field_lines_services.manual_planning_service import ManualPlanningService
from utils.file_manager import get_field_approved_budget_activities_from_file, get_planned_activities_catalog_path

def get_data_from_excel(file_path, sheet_name):
    try:
        df = pd.read_excel(file_path, sheet_name= sheet_name, engine='openpyxl', dtype=str)
        if 'Initial Planned Activities' in df.columns:
            df['Initial Planned Activities'] = pd.to_numeric(df['Planned Activities'], errors='coerce')
        if 'Planned Activities' in df.columns:
            df['Planned Activities'] = pd.to_numeric(df['Planned Activities'], errors='coerce')
        return df
    except Exception as e:
        print(f"Error al leer el archivo: {e}")
        return None
    
def get_data_from_csv(file_path):
    try:
        df = pd.read_csv(file_path, encoding='utf-8')
        if 'Net Total (USD)' in df.columns:
            df['Net Total (USD)'] = (
                df['Net Total (USD)']
                .astype(str)
                .str.replace(',', '', regex=False)
                .astype(float)
            )
        return df
    except Exception as e:
        print(f"Error al leer el archivo CSV: {e}")
        return None

def get_plan_df_by_line(line_name):
    """
    Obtiene el DataFrame de actividades planeadas para una línea específica
    usando ManualPlanningService para un acceso unificado a los archivos.
    
    Args:
        line_name (str): Nombre de la línea de campo
        
    Returns:
        pd.DataFrame: DataFrame con las actividades planeadas de la línea
    """
    service = ManualPlanningService(line_title=line_name)
    return service.get_dataframe()  # Devuelve un DataFrame con la distribución de actividades planeadas
    
def get_field_approved_budget_activities_from_csv():
    return pd.read_csv(get_field_approved_budget_activities_from_file(), encoding='utf-8')

def get_rig_catalog_from_data_frame_from_csv():
    df = pd.read_csv(get_planned_activities_catalog_path(), encoding='utf-8')
    return df

# Función para leer un archivo Excel y devolver un DataFrame con columnas personalizadas por el problema de las actividades ejecutadas del excel base
def get_data_aplanado_custom(file_path, sheet_name):
    try:
        # Leer las dos primeras filas como encabezados
        df = pd.read_excel(file_path, header=[1, 2], sheet_name=sheet_name, dtype=str)

        # Ignorar la primera columna (por posición)
        df.drop(df.columns[0], axis=1, inplace=True)

        # Construir nuevos nombres de columnas personalizados
        cleaned_columns = []
        for col1, col2 in df.columns:
            col1_str = str(col1).strip()
            col2_str = str(col2).strip()

            # Verificar si col1 es válido (no 'Unnamed', no vacío)
            if col1_str.lower().startswith("unnamed") or col1_str == "":
                cleaned_columns.append(col2_str)  # usar solo subcolumna
            else:
                cleaned_columns.append(f"{col1_str}_{col2_str}")

        # Reasignar nombres limpios
        df.columns = cleaned_columns
        # Opcional: eliminar primera columna si sigue vacía
        if df.columns[0].lower().startswith("unnamed") or df.iloc[:, 0].isna().all():
            df.drop(df.columns[0], axis=1, inplace=True)
        df.rename(columns={'Month': 'Month'}, inplace=True)

        # Si 'Mes' no existe pero 'DATE' sí, creamos la columna 'Mes' desde 'DATE'
        if 'Mes' not in df.columns and 'DATE' in df.columns:
            df['DATE'] = pd.to_datetime(df['DATE'], errors='coerce')
            # Diccionario para abreviaturas en español
            meses_es = {
                1: 'ene', 2: 'feb', 3: 'mar', 4: 'abr',
                5: 'may', 6: 'jun', 7: 'jul', 8: 'ago',
                9: 'sept', 10: 'oct', 11: 'nov', 12: 'dic'
            }
            df['DATE'] = df['DATE'].apply(
                lambda x: f"{x.day:02d}-{meses_es.get(x.month, '???')}-{x.strftime('%y')}" if pd.notnull(x) else ''
            )
        df.rename(columns={'DATE': 'Mes'}, inplace=True)
        df = df[df['Month'].notna()]
        return df

    except Exception as e:
        print(f"Error al leer el archivo: {e}")
        return None
    
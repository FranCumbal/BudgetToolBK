import pandas as pd
from datetime import datetime, timedelta
import re

def calculate_duration(jobs_data):
        
    # Asegurarse de que las columnas 'Start' y 'duration' existan y convertir 'Start' a datetime
    if 'Start' in jobs_data.columns and 'duration' in jobs_data.columns:
        jobs_data['Start'] = pd.to_datetime(jobs_data['Start'])
    else:
        raise KeyError("Las columnas 'Start' o 'duration' no existen en el DataFrame")
    
    # Convertir la duración de horas a días y sumar 2 días
    jobs_data['duration_days'] = (jobs_data['duration'] / 24) + 2
    
    # Calcular la fecha de finalización
    jobs_data['End'] = jobs_data['Start'] + pd.to_timedelta(jobs_data['duration_days'], unit='d')
    
    jobs_data.to_excel('forecast_activities_rig.xlsx', index=False)
    
    return jobs_data

def calculate_forecast(jobs_data):
    # Calcular la duración
    jobs_data = calculate_duration(jobs_data)
    
    # Obtener la fecha actual
    current_date = datetime.now()
    # current_date = datetime.strptime('2024-03-05', '%Y-%m-%d')
    
    # Agregar una columna con el mes de la fecha de finalización
    jobs_data['Month'] = jobs_data['End'].dt.strftime('%B')
    
    # Pronóstico para los siguientes 3 meses
    forecast_months = [(current_date + timedelta(days=30*i)).strftime('%B') for i in range(1, 4)]
    forecast_data = jobs_data[(jobs_data['End'] > current_date) & 
                              (jobs_data['End'] <= current_date + timedelta(days=90))] \
        .groupby('Month')['Job Cost (USD)'].sum() \
        .reindex(forecast_months, fill_value=0)
    
    # Convertir la Serie a DataFrame
    forecast_df = forecast_data.reset_index()
    return forecast_df

import pandas as pd

def calculate_forecast_with_mapping(mapped_df: pd.DataFrame,
                       job_id_col: str = "Pending") -> pd.DataFrame:
    """
    Recibe el DataFrame resultante de 'map_services_and_costs' y:
      1) Agrupa por job_id_col para sumar CostByService.
      2) Asigna el mes de finalización a cada job.
      3) Agrupa por mes para obtener el costo total y el acumulado.
    """
    if 'End' not in mapped_df.columns:
        raise KeyError("No existe la columna 'End' en el DataFrame mapeado.")

    # Obtener el mes
    mapped_df['Month'] = mapped_df['End'].dt.strftime('%B')

    # Sumar costo total por job
    cost_by_job = mapped_df.groupby(job_id_col, as_index=False)['CostByService'].sum()
    cost_by_job.rename(columns={'CostByService': 'JobTotalCost'}, inplace=True)

    # Vincular con Month
    job_month = mapped_df[[job_id_col, 'Month']].drop_duplicates()
    cost_by_job = pd.merge(cost_by_job, job_month, on=job_id_col, how='left')

    # Agrupar por mes
    forecast_by_month = cost_by_job.groupby('Month', as_index=False)['JobTotalCost'].sum()

    # Ordenar meses
    month_order = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]
    forecast_by_month['Month'] = pd.Categorical(forecast_by_month['Month'], categories=month_order, ordered=True)
    forecast_by_month.sort_values('Month', inplace=True)

    # Acumulado
    forecast_by_month['Cumulative'] = forecast_by_month['JobTotalCost'].cumsum()
    return forecast_by_month

# logic/forecast_calculator.py
import pandas as pd

def calculate_monthly_costs(mapped_df: pd.DataFrame,
                            job_id_col: str = "Job ID") -> pd.DataFrame:
    """
    1) Asigna la columna 'Month' según 'End'.
    2) Agrupa por [Month] y suma 'CostByService'.
       (Si deseas separar por 'linea', también agrupa por 'linea'.)
    3) Retorna un DataFrame con [Month, TotalCost] (y luego puedes calcular Cumulative).
    """
    if 'MONTH' not in mapped_df.columns:
        raise KeyError("No existe la columna 'MONTH' en mapped_df")


    # Agrupar por 'MONTH' directamente
    monthly = mapped_df.groupby('MONTH', as_index=False)['CostByService'].sum()
    monthly.rename(columns={'CostByService': 'budget'}, inplace=True)

    # Ordenar meses
    month_order = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]
    monthly['MONTH'] = pd.Categorical(monthly['MONTH'], categories=month_order, ordered=True)
    monthly.sort_values('MONTH', inplace=True)


    return monthly






def calculate_deviations(df):
    """
    Filtra las filas con:
    1. Distancia > 30 km desde la columna 'Estimated distance (km)'.
    2. Pozos con duración > 15 días.
    
    Parámetros:
        df (pd.DataFrame): DataFrame con columnas 'Estimated distance (km)' y 'duration'.
        
    Retorna:
        pd.DataFrame: DataFrame filtrado.
    """
    def extract_distance(value):
        """Extraer la distancia numérica usando una expresión regular."""
        match = re.search(r'(\d+(\.\d+)?)', str(value))
        return float(match.group(0)) if match else None
    
    # Extraer las distancias
    df['Distance'] = df['Estimated distance (km)'].apply(extract_distance)
    
    # Filtrar: distancia > 30 y duración > 15 días
    filtered_df = df[(df['Distance'] > 80)]
    
    return filtered_df


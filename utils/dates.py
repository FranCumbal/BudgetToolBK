from datetime import datetime
import pandas as pd

def get_days_in_months(year: int) -> dict:
    """
    Devuelve un diccionario con la cantidad de días de cada mes para un año dado.

    Args:
        year (int): Año del cual se desean obtener los días por mes.

    Returns:
        dict: Diccionario con el número de mes como clave y número de días como valor.
    """
    return {
        month: (datetime(year, month + 1, 1) - datetime(year, month, 1)).days if month < 12 else 31
        for month in range(1, 13)
    }

def get_month_number(month: str):
    """
    Convierte el nombre completo de un mes a su número correspondiente.

    Args:
        month (str): Nombre completo del mes (e.g., 'January').

    Returns:
        int | str: Número del mes (1-12) o 'Invalid month name' si no coincide.
    """
    months = {
        "January": 1, "February": 2, "March": 3, "April": 4,
        "May": 5, "June": 6, "July": 7, "August": 8,
        "September": 9, "October": 10, "November": 11, "December": 12
    }
    return months.get(month, "Invalid month name")

def get_month_name(mes_num: int) -> str:
    """
    Retorna el nombre del mes correspondiente a un número.

    Args:
        mes_num (int): Número del mes (1-12).

    Returns:
        str: Nombre del mes en inglés.
    """
    return datetime(2000, mes_num, 1).strftime("%B")

def normalize_month_names(month_column: pd.Series) -> pd.Series:
    """
    Normaliza una columna de nombres de meses abreviados a nombres completos.

    Args:
        month_column (pd.Series): Serie de pandas con nombres de meses.

    Returns:
        pd.Series: Serie con nombres de meses normalizados en formato completo.
    """
    month_mapping = {
        "Jan": "January", "Feb": "February", "Mar": "March", "Apr": "April",
        "May": "May", "Jun": "June", "Jul": "July", "Aug": "August",
        "Sep": "September", "Oct": "October", "Nov": "November", "Dec": "December"
    }
    return month_column.replace(month_mapping)
def get_all_months():
    """
    Retorna la lista estándar de meses en inglés.
    """
    return [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]
    
def calculate_duration(jobs_data: pd.DataFrame) -> pd.DataFrame:
    if 'Start' not in jobs_data.columns or 'duration' not in jobs_data.columns:
        raise KeyError("Faltan columnas 'Start' o 'duration' en jobs_data")

    jobs_data['Start'] = pd.to_datetime(jobs_data['Start'])
    jobs_data['duration_days'] = (jobs_data['duration'] / 24) + 2
    jobs_data['End'] = jobs_data['Start'] + pd.to_timedelta(jobs_data['duration_days'], unit='d')
    return jobs_data
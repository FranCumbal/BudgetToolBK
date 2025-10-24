import pandas as pd

def format_failures(df):
    # Convertir 'MENSUAL' a datetime
    df['MENSUAL'] = pd.to_datetime(df['MENSUAL'])

    # Extraer los nombres de los meses
    df['Month'] = df['MENSUAL'].dt.strftime('%B')
    return df


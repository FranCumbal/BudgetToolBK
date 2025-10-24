
import pandas as pd

from utils.file_manager import get_field_file_cost


class ExecutedActivitiesPlan:
    """
    Clase responsable de leer y procesar el archivo Excel de costos de campo.

    Su principal función es manejar la estructura de encabezado de múltiples niveles
    del archivo de origen, limpiar los nombres de las columnas y preparar un
    DataFrame estandarizado para su uso en el resto de la aplicación.
    """
    @staticmethod
    def get_executed_data_from_excel():
        """
        Lee el archivo Excel de costos de campo y lo transforma en un DataFrame limpio.

        Este método realiza varias operaciones clave:
        1. Lee el archivo Excel utilizando un encabezado de dos niveles.
        2. Ignora la primera columna, que suele estar vacía o ser un índice.
        3. Combina los dos niveles del encabezado para crear nombres de columna únicos
           (ej. 'LINEA_Servicios'), manejando columnas sin nombre.
        4. Si una columna 'DATE' existe pero 'Mes' no, la convierte para generar
           la columna 'Mes' en formato 'dd-mes-aa'.
        5. Filtra las filas que no tienen un valor válido en la columna 'Month'.
        6. Maneja errores de lectura de archivos, devolviendo None en caso de fallo.

        Returns:
            pd.DataFrame or None: Un DataFrame con los datos procesados, o None si ocurre un error.
        """
        try:
            df = pd.read_excel(get_field_file_cost(), header=[1, 2], sheet_name="Sheet1", dtype=str)

            df.drop(df.columns[0], axis=1, inplace=True)

            cleaned_columns = []
            for col1, col2 in df.columns:
                col1_str = str(col1).strip()
                col2_str = str(col2).strip()

                if col1_str.lower().startswith("unnamed") or col1_str == "":
                    cleaned_columns.append(col2_str)
                else:
                    cleaned_columns.append(f"{col1_str}_{col2_str}")

            df.columns = cleaned_columns
            if df.columns[0].lower().startswith("unnamed") or df.iloc[:, 0].isna().all():
                df.drop(df.columns[0], axis=1, inplace=True)
            df.rename(columns={'Month': 'Month'}, inplace=True)

            if 'Mes' not in df.columns and 'DATE' in df.columns:
                df['DATE'] = pd.to_datetime(df['DATE'], errors='coerce')
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
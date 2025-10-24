import os
import pandas as pd
from datetime import datetime
from utils.file_manager import get_categorizer_executed_catalog_path_by_line_name

class CategorizerExecutedCatalogService:
    """
    Gestiona un catálogo persistente de actividades ejecutadas y categorizadas.

    Esta clase se encarga de guardar en un archivo CSV los detalles de las
    actividades ejecutadas (pozo, costo, categoría) para una línea y mes
    específicos, y permite recuperar estos registros posteriormente.
    """
    def __init__(self):
        """
        Inicializa el servicio del catálogo de actividades categorizadas.
        """
        self.columns = ["month", "year", "Well", "Cost by Activity", "Category"]
        self.dataframe = None
        self.line_title = None
        self.month = None
        self.csv_path = None  

    def set_line_title(self, line_title):
        """
        Establece la línea de servicio para la cual se gestionará el catálogo.

        Determina la ruta del archivo CSV correspondiente y lo crea con los
        encabezados necesarios si no existe.
        """
        self.line_title = line_title
        self.csv_path = self.get_categorizer_executed_catalog_path_by_line_name(line_title)

        if not os.path.exists(self.csv_path):
            pd.DataFrame(columns=self.columns).to_csv(self.csv_path, index=False)

    def set_month(self, month):
        """Establece el mes para el cual se guardarán o consultarán los datos."""
        self.month = month

    def save_to_csv(self):
        """
        Guarda el DataFrame de actividades en el archivo CSV del catálogo.

        Procesa el DataFrame en memoria, extrae los datos relevantes, y los guarda
        en el archivo CSV. Si ya existen registros para el mismo mes y año,
        los reemplaza con los nuevos datos para evitar duplicados.
        """
        if self.dataframe is None or self.dataframe.empty:
            print("No hay datos para guardar")
            return

        year = datetime.now().year
        servicios_col = f'{self.line_title}_Servicios'
        productos_col = f'{self.line_title}_Productos'

        has_serv = servicios_col in self.dataframe.columns
        has_prod = productos_col in self.dataframe.columns

        records = []
        for _, row in self.dataframe.iterrows():
            sum_serv = row.get(servicios_col, 0) if has_serv else 0
            sum_prod = row.get(productos_col, 0) if has_prod else 0
            cost_value = sum_serv + sum_prod

            records.append({
                "month": self.month,
                "year": year,
                "Well": row.get("WELL", ""),
                "Cost by Activity": cost_value,
                "Category": row.get("Categoria_Total", "")
            })

        if os.path.exists(self.csv_path):
            existing_df = pd.read_csv(self.csv_path)

            mask = ~((existing_df["month"] == self.month) & 
                    (existing_df["year"] == year))
            existing_df = existing_df[mask]
        else:
            existing_df = pd.DataFrame(columns=self.columns)

        new_df = pd.DataFrame(records, columns=self.columns)
        final_df = pd.concat([existing_df, new_df], ignore_index=True)

        final_df.to_csv(self.csv_path, index=False)
        print(f"Guardados {len(records)} registros para {self.line_title} - {self.month}/{year}")


    def get_records_by_month_and_line(self, month, line_title=None):
        """
        Obtiene los registros del catálogo filtrados por mes y año.

        Args:
            month (str): El mes para el cual se desean obtener los registros.
            line_title (str, optional): El título de la línea. Aunque se recibe,
                                        el filtro se basa en el archivo CSV ya
                                        específico de la línea.

        Returns:
            pd.DataFrame: Un DataFrame con los registros encontrados.
        """
        if not os.path.exists(self.csv_path):
            return pd.DataFrame(columns=self.columns)
        
        df = pd.read_csv(self.csv_path)
        year = datetime.now().year
        
        filtered_df = df[(df["month"] == month) & (df["year"] == year)]
        
        return filtered_df
    
    def get_categorizer_executed_catalog_path_by_line_name(self, line_name):
        """
        Obtiene la ruta del archivo CSV para el catálogo de una línea específica.
        """
        return get_categorizer_executed_catalog_path_by_line_name(line_name)

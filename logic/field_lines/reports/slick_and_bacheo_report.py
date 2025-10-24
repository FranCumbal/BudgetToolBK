import pandas as pd
from logic.field_lines.reports.field_report import FieldReport


class SlickAndBacheoReport(FieldReport):
    """
    Reporte especializado para las líneas de servicio 'Slickline' y 'Bacheo'.

    Hereda de FieldReport y añade lógica para calcular el presupuesto con un
    CPAE estático y para categorizar las actividades ejecutadas según su costo.
    """
    def __init__(self, title: str, service_type: str, zone: str, line_type: str, categoria_1: float, categoria_2: float, categoria_3: float):
        """
        Inicializa una instancia del reporte para Slick and Bacheo.

        Args:
            title (str): Título o nombre de la línea.
            service_type (str): Tipo de servicio.
            zone (str): Zona geográfica.
            line_type (str): Tipo de línea.
            categoria_1 (float): Límite superior de costo para la categoría 1.
            categoria_2 (float): Límite superior de costo para la categoría 2.
            categoria_3 (float): Límite superior de costo para la categoría 3.
        """
        super().__init__(title=title, service_type=service_type, zone=zone, line_type=line_type)
        self.type = service_type
        self.CATEGORIA_1 = categoria_1
        self.CATEGORIA_2 = categoria_2
        self.CATEGORIA_3 = categoria_3

    def get_data_sources(self) -> dict:
        """
        Sobrescribe el método base para usar un presupuesto con CPAE estático.

        Reemplaza la fuente de datos 'budget' por una versión calculada con un
        costo por actividad (CPAE) distribuido uniformemente a lo largo del año.
        """
        sources = super().get_data_sources()
        sources["budget"] = self.generate_budget_with_static_cpae(self.static_cpae_value())
        return sources
    
    def static_cpae_value(self) -> float:
        """
        Calcula un valor de CPAE estático y distribuido uniformemente.

        Obtiene el presupuesto total anual y lo divide entre los 12 meses para
        obtener un costo mensual constante.
        """
        return self.anual_initial_planned_loader.get_budget_value_evently_distributed_by_year(self.year)
    
    def generate_budget_with_static_cpae(self, cpae_value):
        """
        Genera un DataFrame de presupuesto con el mismo valor CPAE para cada mes.
        """
        months = [m.lower() for m in self._get_months_data()]
        static_cpae_dataframe = pd.DataFrame({"Month": months, "CPAE": [cpae_value]*len(months)})
        budget_df = static_cpae_dataframe.copy()
        budget_df["Budget"] = budget_df["CPAE"].cumsum()
        return budget_df[["Month", "Budget"]]

    def get_executed_activities_data_frame_by_month(self, month, line_name):
        """
        Obtiene el DataFrame de actividades ejecutadas para un mes y línea específicos.

        Delega la llamada al gestor de actividades ejecutadas.
        """
        return self.executed_activities_manager.get_executed_activities_data_frame_by_month(month, line_name)
    
    def get_categorizer_executed_activities_by_month(self, month):
        """
        Obtiene y categoriza las actividades ejecutadas para un mes dado.

        Distingue entre 'Slickline' (usa solo costos de servicios) y 'Bacheo'
        (suma costos de servicios y productos). Luego, clasifica el costo total
        en categorías predefinidas.
        """
        month = month.strip().lower().title()
        df = self.get_executed_activities_data_frame_by_month(month, self.title)
        servicios_col = f'{self.title}_Servicios'
        productos_col = f'{self.title}_Productos'

        if servicios_col not in df.columns:
            raise ValueError(f'Columna {servicios_col} no encontrada')
        productos_exists = productos_col in df.columns
        # Si es Slickline, solo usar servicios_col
        if self.title.strip().lower() == "item 49 slick line":
            df["Categoria_Total"] = df[servicios_col].apply(self.clasificar_valor_servicio)
            return df
        # Si es Bacheo, sumar servicios y productos si existen
        def calcular_total(row):
            servicio = row.get(servicios_col, 0) or 0
            producto = row.get(productos_col, None) if productos_exists else None
            if pd.notnull(producto):
                return servicio + producto
            else:
                return servicio
        df[servicios_col] = df[servicios_col].fillna(0)
        if productos_exists:
            df[productos_col] = df[productos_col].fillna(0)
        df["Costo_Total"] = df.apply(calcular_total, axis=1)
        df["Categoria_Total"] = df["Costo_Total"].apply(self.clasificar_valor_servicio)
        return df

    def clasificar_valor_servicio(self, valor):
        """
        Clasifica un valor de costo en una categoría numérica.

        Utiliza los umbrales (CATEGORIA_1, CATEGORIA_2, CATEGORIA_3) definidos
        en la inicialización para asignar un número de categoría (1 a 4) a un
        costo dado. Devuelve 0 si el valor es nulo o cero.
        """
        if pd.isna(valor) or valor == 0:
            return 0
        elif valor <= self.CATEGORIA_1:
            return 1
        elif valor <= self.CATEGORIA_2:
            return 2
        elif valor <= self.CATEGORIA_3:
            return 3
        else:
            return 4
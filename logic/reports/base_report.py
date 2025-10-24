# logic/base_report.py
from abc import ABC, abstractmethod

class LineReport(ABC):
    def __init__(self, data_loader):
        self.data_loader = data_loader

    @abstractmethod
    def generate_forecast(self):
        pass

    @abstractmethod
    def generate_budget(self):
        pass

    @abstractmethod
    def generate_deviations(self):
        pass

    @abstractmethod
    def generate_graph(self, forecast, budget, activities_data):
        pass

    def get_data_sources(self) -> dict:
        """
        Método opcional que devuelve los dataframes necesarios para el gráfico.
        Por defecto, devuelve un dict vacío. Las subclases pueden sobrescribirlo.
        """
        return {}

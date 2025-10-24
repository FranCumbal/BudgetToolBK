from abc import ABC, abstractmethod

class BaseConnector(ABC):
    """
    Clase base para todas las conexiones a fuentes de datos.
    """

    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def fetch_data(self, query):
        pass

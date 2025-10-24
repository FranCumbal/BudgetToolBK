import csv
import os
from PyQt5.QtWidgets import QComboBox

class PlannedActivitiesCatalogService:
    """
    Gestiona un catálogo de actividades planeadas almacenado en un archivo CSV.

    Esta clase proporciona una interfaz para realizar operaciones CRUD (Crear, Leer,
    Actualizar, Borrar) sobre un archivo CSV que contiene un catálogo de
    actividades. También incluye un método para sincronizar los datos desde
    un QTableWidget de PyQt5.
    """
    def __init__(self, csv_file):
        """
        Inicializa el servicio del catálogo.

        Args:
            csv_file (str): La ruta al archivo CSV que se va a gestionar.
        """
        self.csv_file = csv_file
        self.data = []
        self.load_data()

    def load_data(self):
        """
        Carga los datos desde el archivo CSV a la memoria.

        Si el archivo existe, lee su contenido y lo almacena en `self.data`
        como una lista de diccionarios, donde cada diccionario representa una fila.
        """
        self.data = []
        if os.path.exists(self.csv_file):
            with open(self.csv_file, newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.data.append(row)

    def save_data(self):
        """
        Guarda los datos actualmente en memoria de vuelta al archivo CSV.

        Sobrescribe el archivo CSV con el contenido de `self.data`.
        """
        with open(self.csv_file, mode='w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=self.get_headers())
            writer.writeheader()
            writer.writerows(self.data)

    def get_headers(self):
        """Devuelve la lista de encabezados esperados para el archivo CSV."""
        return ["Activity Type", "Line Name", "Year", "Activity Description", "Historical Avarage", "Cost", "Planned Activities"]


    def add_entry(self, entry):
        """
        Añade una nueva entrada al catálogo si no existe un duplicado.

        Verifica la unicidad basada en la tupla ('Activity Type', 'Line Name', 'Year').
        Si es única, la añade y guarda los datos.

        Returns:
            bool: True si la entrada fue añadida, False si se encontró un duplicado.
        """
        key = (entry["Activity Type"], entry["Line Name"], entry["Year"])
        for row in self.data:
            if (row["Activity Type"], row["Line Name"], row["Year"]) == key:
                return False  # Duplicate found
        self.data.append(entry)
        self.save_data()
        return True

    def delete_entry(self, activity_type, line_name, year):
        """
        Elimina una entrada del catálogo que coincida con los parámetros.

        Busca una entrada por 'Activity Type', 'Line Name' y 'Year' y la elimina.
        Guarda los cambios si se realizó una eliminación.

        Returns:
            bool: True si una entrada fue eliminada, False en caso contrario.
        """
        initial_length = len(self.data)
        self.data = [
            row for row in self.data
            if not (
                row["Activity Type"] == activity_type and
                row["Line Name"] == line_name and
                row["Year"] == year
            )
        ]
        if len(self.data) < initial_length:
            self.save_data()
            return True
        return False

    def update_data_from_table(self, table):
        """
        Actualiza el catálogo completo con los datos de un QTableWidget.

        Lee todas las filas de la tabla, reconstruye la lista de datos y la guarda
        en el archivo CSV. Realiza una validación para evitar duplicados.

        Args:
            table (QTableWidget): La tabla de la interfaz de usuario con los datos.

        Returns:
            bool: True si la actualización fue exitosa, False si se detectaron duplicados.
        """
        new_data = []
        headers = self.get_headers()
        seen_keys = set()

        for row in range(table.rowCount()):
            row_data = {}
            for col, header in enumerate(headers):
                if header == "Activity Type":
                    widget = table.cellWidget(row, col)
                    if isinstance(widget, QComboBox):
                        row_data[header] = widget.currentText()
                else:
                    item = table.item(row, col)
                    row_data[header] = item.text() if item else ""

            # Cambiar la clave para incluir el año (consistente con el servicio)
            key = (row_data["Activity Type"], row_data["Line Name"], row_data["Year"])
            if key in seen_keys:
                return False  # Duplicado detectado
            seen_keys.add(key)
            new_data.append(row_data)

        self.data = new_data
        self.save_data()
        return True
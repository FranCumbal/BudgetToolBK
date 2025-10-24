import pandas as pd
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QComboBox,
    QPushButton, QHeaderView, QMessageBox
)
from PyQt5.QtCore import Qt

class CapexConfigDialog(QDialog):
    """
    Diálogo para configurar qué meses se consideran para CAPEX.
    Muestra una tabla con cada mes y un ComboBox con opciones "Yes" o "No".
    """
    def __init__(self, config_data: dict, parent=None):
        super().__init__(parent)
        self.config_data = config_data
        self.months = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]
        self.comboboxes = {}
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Configuración de los meses Capex")
        self.setMinimumSize(350, 500)
        layout = QVBoxLayout(self)

        # Crear y configurar la tabla
        self.table = QTableWidget(len(self.months), 2)
        self.table.setHorizontalHeaderLabels(["Month", "Capex"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)

        # Poblar la tabla con los meses y ComboBoxes
        for i, month in enumerate(self.months):
            month_item = QTableWidgetItem(month)
            month_item.setFlags(month_item.flags() & ~Qt.ItemIsEditable)

            combo = QComboBox()
            combo.addItems(["No", "Yes"])
            
            # Establecer el valor actual desde la configuración cargada
            current_value = self.config_data.get(month, "No")
            combo.setCurrentText(current_value)

            self.table.setItem(i, 0, month_item)
            self.table.setCellWidget(i, 1, combo)
            self.comboboxes[month] = combo

        layout.addWidget(self.table)

        # Botón para guardar la configuración
        save_button = QPushButton("Guardar Configuración")
        save_button.clicked.connect(self.accept) # Cierra el diálogo con estado Aceptado
        layout.addWidget(save_button)

    def get_updated_config(self) -> dict:
        """
        Recupera los valores seleccionados en cada ComboBox y los retorna
        como un diccionario.
        """
        updated_config = {}
        for month, combo in self.comboboxes.items():
            updated_config[month] = combo.currentText()
        return updated_config
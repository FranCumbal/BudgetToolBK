from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from PyQt5.QtCore import Qt
from services.field_lines_services.historical_initial_cost_service import HistoricalInitialCostService
from datetime import datetime

class HistoricalInitialCostView(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Varillera's Initial Approved Cost")
        self.setMinimumWidth(400)
        self.setMinimumHeight(150)
        self.service = HistoricalInitialCostService()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        year = self.service.get_year()
        initial_cost = self.service.get_initial_cost()

        # Fila de año (no editable)
        year_layout = QHBoxLayout()
        year_label = QLabel("Year:")
        self.year_value = QLabel(str(year))
        year_layout.addWidget(year_label)
        year_layout.addWidget(self.year_value)
        layout.addLayout(year_layout)

        # Fila de Initial Cost Approved (editable)
        cost_layout = QHBoxLayout()
        cost_label = QLabel("Initial Cost Approved:")
        self.cost_edit = QLineEdit(str(initial_cost))
        cost_layout.addWidget(cost_label)
        cost_layout.addWidget(self.cost_edit)
        layout.addLayout(cost_layout)

        # Botón guardar
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save)
        layout.addWidget(save_button)

        self.setLayout(layout)

    def save(self):
        try:
            value = float(self.cost_edit.text())
            self.service.set_initial_cost(value)
            self.service.save()
            QMessageBox.information(self, "Saved", "✅ Initial Approved Cost saved successfully.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error while saving: {e}")

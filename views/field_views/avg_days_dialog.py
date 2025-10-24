from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from PyQt5.QtCore import Qt

class AvgDaysDialog(QDialog):
    def __init__(self, controller=None):
        super().__init__()
        self.controller = controller
        self.setWindowTitle("Promedio de días")
        self.setMinimumWidth(300)
        self.setMinimumHeight(120)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        self.label = QLabel("Coloca el número de días promedio")
        self.label.setAlignment(Qt.AlignCenter)
        self.input = QLineEdit()
        self.input.setPlaceholderText("Ejemplo: 7")
        self.input.setAlignment(Qt.AlignCenter)
        self.save_button = QPushButton("Guardar")
        self.save_button.clicked.connect(self._on_save)
        layout.addWidget(self.label)
        layout.addWidget(self.input)
        layout.addWidget(self.save_button)

    def _on_save(self):
        value = self.input.text().strip().replace(',', '.')
        try:
            avg_days = float(value)
            if avg_days <= 0:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Valor inválido", "Por favor ingresa un número válido.")
            return
        # Aquí puedes guardar el valor usando el controller si lo necesitas
        if self.controller and hasattr(self.controller, "set_avg_days"):
            self.controller.set_avg_days(avg_days)
        QMessageBox.information(self, "Guardado", f"Días promedio guardados: {avg_days}")
        self.accept()

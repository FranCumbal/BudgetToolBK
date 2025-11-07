# views/completions_config_view.py
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt

class CompletionsConfigDialog(QDialog):
    """
    Diálogo de configuración para el catálogo de Completions.
    (Versión inicial)
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuración Catálogo 1.03 - Completions")
        self.setWindowModality(Qt.ApplicationModal)
        self.setMinimumSize(400, 200)

        # Layout principal
        layout = QVBoxLayout(self)

        # Mensaje temporal
        label = QLabel("Ventana de configuración de Completions.\n\nFuncionalidad próximamente.")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)

        self.setLayout(layout)
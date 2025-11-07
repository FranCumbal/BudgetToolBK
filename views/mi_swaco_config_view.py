# views/mi_swaco_config_view.py
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt

class MISwacoConfigDialog(QDialog):
    """
    Diálogo de configuración para el catálogo de MI Swaco.
    (Versión inicial)
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuración Catálogo 1.02 - MI Swaco")
        self.setWindowModality(Qt.ApplicationModal)
        self.setMinimumSize(400, 200)

        # Layout principal
        layout = QVBoxLayout(self)

        # Mensaje temporal
        label = QLabel("Ventana de configuración de MI Swaco.\n\nFuncionalidad próximamente.")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)

        self.setLayout(layout)
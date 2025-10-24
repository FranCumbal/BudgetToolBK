from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGroupBox, QFormLayout, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt


class ServicesResumenDialog(QDialog):
    def __init__(self, costo_target, costo_seleccion, costo_total, duracion_target, duracion_promedio, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Resumen de Costo y Duración - Services")
        self.setMinimumWidth(500)

        layout = QVBoxLayout(self)

        # 🔹 Grupo 1: Costos
        costos_group = QGroupBox("Costo por día")
        costos_layout = QFormLayout()
        costos_layout.addRow("🎯 Costo objetivo:", QLabel(f"{costo_target:,.2f} USD"))
        costos_layout.addRow("✅ Costo seleccionado:", QLabel(f"{costo_seleccion:,.2f} USD"))
        costos_layout.addRow("📊 Costo general:", QLabel(f"{costo_total:,.2f} USD"))
        costos_group.setLayout(costos_layout)
        layout.addWidget(costos_group)

        # 🔹 Grupo 2: Duraciones
        duracion_group = QGroupBox("Duración estimada")
        duracion_layout = QFormLayout()
        duracion_layout.addRow("🕒 Duración objetivo:", QLabel(f"{duracion_target:.1f} días"))
        duracion_layout.addRow("📉 Duración promedio:", QLabel(f"{duracion_promedio:.1f} días"))
        duracion_group.setLayout(duracion_layout)
        layout.addWidget(duracion_group)

        # 🔹 Notas
        notas = QLabel(
            "📌 Los valores se basan en los pozos seleccionados y el historial del presupuesto.\n"
            "🔧 El costo objetivo fue definido manualmente desde el catálogo."
        )
        notas.setWordWrap(True)
        layout.addWidget(notas)

        layout.addSpacerItem(QSpacerItem(10, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # 🔘 Botón cerrar
        cerrar_btn = QPushButton("Cerrar")
        cerrar_btn.setFixedWidth(120)
        cerrar_btn.clicked.connect(self.accept)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(cerrar_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)
        self.adjustSize()


from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt

class ServicesValuesInfoView(QDialog):
    def __init__(self, values_dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Valores de cada variable")
        self.resize(500, 300)
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)


        # Agrupar variables por tipo
        costos_keys = [k for k in values_dict.keys() if "Costo" in k]
        dias_keys = [k for k in values_dict.keys() if "Día" in k or "Dias" in k]

        # Grupo de Costos
        from PyQt5.QtWidgets import QGroupBox, QFormLayout
        costos_group = QGroupBox("💵 Costos")
        costos_layout = QFormLayout()
        for key in costos_keys:
            value = values_dict[key]
            try:
                value_fmt = f"{float(value):,.2f} USD"
            except (ValueError, TypeError):
                value_fmt = str(value)
            costos_layout.addRow(key + ":", QLabel(value_fmt))
        costos_group.setLayout(costos_layout)
        main_layout.addWidget(costos_group)

        # Grupo de Días
        dias_group = QGroupBox("☀️ Días")
        dias_layout = QFormLayout()
        for key in dias_keys:
            value = values_dict[key]
            try:
                value_fmt = f"{float(value):.2f} días"
            except (ValueError, TypeError):
                value_fmt = str(value)
            dias_layout.addRow(key + ":", QLabel(value_fmt))
        dias_group.setLayout(dias_layout)
        main_layout.addWidget(dias_group)

        # Botón cerrar
        close_btn = QPushButton("Cerrar")
        close_btn.clicked.connect(self.accept)
        main_layout.addWidget(close_btn)

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QMessageBox, QWidget, QHBoxLayout, QCheckBox
)
from PyQt5.QtCore import Qt
import pandas as pd
import os


class WellSelectorDialog(QDialog):
    def __init__(self, wells_df, save_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Selector de Pozos - Services")
        self.resize(700, 400)

        self.wells_df = wells_df.copy()
        self.save_path = save_path
        self.selected = set()

        if os.path.exists(self.save_path):
            try:
                prev_df = pd.read_excel(self.save_path)
                self.selected = set(str(p).strip().upper() for p in prev_df["WELL"])
            except Exception as e:
                print(f"No se pudo cargar pozos seleccionados: {e}")

        self.checkbox_list = []  # Lista para acceder a todos los QCheckBox
        layout = QVBoxLayout(self)

        # Tabla
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["", "Pozo", "Costo Services"])
        self.table.setRowCount(len(self.wells_df))
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)

        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(2, 120)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.verticalHeader().setDefaultSectionSize(28)

        for row, (_, data) in enumerate(self.wells_df.iterrows()):
            pozo_val = str(data["WELL"]).strip().upper()
            costo_val = float(data["1.10 Services"])

            # Columna 0: CheckBox centrado
            check_widget, checkbox = self.create_checkbox_cell(pozo_val in self.selected)
            self.table.setCellWidget(row, 0, check_widget)
            self.checkbox_list.append(checkbox)

            # Columna 1: Pozo
            pozo_item = QTableWidgetItem(pozo_val)
            pozo_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 1, pozo_item)

            # Columna 2: Costo
            costo_item = QTableWidgetItem(f"{costo_val:.2f}")
            costo_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 2, costo_item)

        layout.addWidget(self.table)

        # Botones
        self.toggle_btn = QPushButton("Seleccionar todos")
        self.toggle_btn.clicked.connect(self.toggle_all_checkboxes)
        layout.addWidget(self.toggle_btn)

        guardar_btn = QPushButton("Guardar selección")
        guardar_btn.clicked.connect(self.guardar_seleccion)
        layout.addWidget(guardar_btn)

        self.setLayout(layout)

    def create_checkbox_cell(self, checked):
        widget = QWidget()
        checkbox = QCheckBox()
        checkbox.setChecked(checked)

        layout = QHBoxLayout()
        layout.addWidget(checkbox)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        widget.setLayout(layout)

        return widget, checkbox

    def toggle_all_checkboxes(self):
        todos_seleccionados = all(cb.isChecked() for cb in self.checkbox_list)
        nuevo_estado = not todos_seleccionados

        for cb in self.checkbox_list:
            cb.setChecked(nuevo_estado)

        self.toggle_btn.setText("Deseleccionar todos" if nuevo_estado else "Seleccionar todos")

    def guardar_seleccion(self):
        seleccionados = []
        for row in range(self.table.rowCount()):
            checkbox_widget = self.table.cellWidget(row, 0)
            checkbox = checkbox_widget.findChild(QCheckBox)
            if checkbox and checkbox.isChecked():
                pozo = self.table.item(row, 1).text()
                costo = float(self.table.item(row, 2).text())
                seleccionados.append({"WELL": pozo, "1.10 Services": costo})

        if not seleccionados:
            QMessageBox.warning(self, "Advertencia", "No se ha seleccionado ningún pozo.")
            return

        df_selected = pd.DataFrame(seleccionados)
        try:
            df_selected.to_excel(self.save_path, index=False)
            QMessageBox.information(self, "Éxito", f"Pozos guardados correctamente en:\n{self.save_path}")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo guardar el archivo: {e}")

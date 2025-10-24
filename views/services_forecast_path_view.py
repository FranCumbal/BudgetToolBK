from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QHeaderView, QPushButton, QTableWidget, QTableWidgetItem, QHBoxLayout, QCheckBox, QFileDialog, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from views.services_forecast_result_view import ServicesForecastResultView
import pandas as pd
import os

class ServicesForecastPathView(QDialog):
    paths_saved = pyqtSignal(list)

    def __init__(self, csv_path, parent=None, controller=None):
        super().__init__(parent)
        self.setWindowTitle("Forecast para la linea 1.10. Services")
        self.resize(1200, 600)  # Tamaño más grande para mostrar nombres completos
        self.csv_path = csv_path
        self.controller = controller

        self.result_windows = []

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Mapeo de posiciones de tabla a IDs únicos
        self.record_ids = {
            (0, 0): "costo_target",        # Fila 0, Columna 0 (Costos)
            (0, 2): "dias_target",         # Fila 0, Columna 2 (Días)
            (1, 0): "costo_promedio",  # Fila 1, Columna 0 (Costos)
            (1, 2): "dias_promedio",   # Fila 1, Columna 2 (Días)
            (2, 0): "costo_total",               # Fila 2, Columna 0 (Costos)
        }

        # Tabla principal
        self.table = QTableWidget(3, 4)
        self.table.setHorizontalHeaderLabels(["Ruta Costos", "Validacion", "Ruta Días", "Validacion"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.layout.addWidget(self.table)

        # Tag herramientas con menú
        tools_layout = QHBoxLayout()
        tools_label = QLabel("Herramientas:")
        tools_layout.addWidget(tools_label)
        self.visualize_btn = QPushButton("Visualiza tu forecast")
        self.visualize_btn.clicked.connect(self.on_visualize_forecast)
        self.visualize_values_btn = QPushButton("Mira los valores de cada variable")
        self.visualize_values_btn.clicked.connect(self.on_values_chosen)
        tools_layout.addWidget(self.visualize_btn)
        tools_layout.addWidget(self.visualize_values_btn)
        self.layout.addLayout(tools_layout)

        # Botón Guardar
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Guardar")
        btn_layout.addWidget(self.save_btn)
        self.layout.addLayout(btn_layout)
        self.save_btn.clicked.connect(self.on_save_clicked)

        # Poblar la tabla
        self.populate_table()

        self.load_from_csv()


    def on_save_clicked(self):
        self.save_to_csv()
        validados = self.get_validated_records()
        self.paths_saved.emit(validados)

    def on_values_chosen(self):
        """
        Abre una interfaz informativa con los valores de cada variable.
        """
        from views.services_values_info_view import ServicesValuesInfoView
        values_dict = self.controller.get_all_values_to_show()
        self.info_view = ServicesValuesInfoView(values_dict)
        self.info_view.show()

    def on_visualize_forecast(self):
        """
        Abre la vista de visualización de forecast con los pares de IDs seleccionados.
        """
        
        # Recupera los pares de IDs validados
        validados = self.get_validated_records()
        
        # Genera los pares posibles (costos y días)
        ids_costos = [id for id in validados if "costo" in id]
        ids_dias = [id for id in validados if "dias" in id]
        
        # Si no hay pares válidos, muestra advertencia
        if not ids_costos or not ids_dias:
            QMessageBox.warning(self, "Advertencia", "Debes seleccionar al menos un ID de costo y uno de días.")
            return
        
        # Genera todos los pares posibles
        pares = []
        for id_costo in ids_costos:
            for id_dia in ids_dias:
                pares.append((id_costo, id_dia))
        
        # Abre la vista de resultados
        self.result_view = ServicesForecastResultView(self.controller, pares)
        self.result_view.show()
        self.result_windows.append(self.result_view)

    def populate_table(self):
        # Fila 0: Costo Target Input | | Dias Target Input | 
        item0_0 = QTableWidgetItem("Costo Target")
        item0_0.setFlags(item0_0.flags() & ~Qt.ItemIsEditable)
        self.table.setItem(0, 0, item0_0)
        chk0_1 = QCheckBox()
        chk0_1.toggled.connect(lambda checked, row=0, col=1: self.on_checkbox_toggled(checked, row, col))
        self.table.setCellWidget(0, 1, chk0_1)
        item0_2 = QTableWidgetItem("Dias Target")
        item0_2.setFlags(item0_2.flags() & ~Qt.ItemIsEditable)
        self.table.setItem(0, 2, item0_2)
        chk0_3 = QCheckBox()
        chk0_3.toggled.connect(lambda checked, row=0, col=3: self.on_checkbox_toggled(checked, row, col))
        self.table.setCellWidget(0, 3, chk0_3)

        # Fila 1: Costo Promedio Calculado | | Dias Promedio Calculado | 
        item1_0 = QTableWidgetItem("Costo Promedio")
        item1_0.setFlags(item1_0.flags() & ~Qt.ItemIsEditable)
        self.table.setItem(1, 0, item1_0)
        chk1_1 = QCheckBox()
        chk1_1.toggled.connect(lambda checked, row=1, col=1: self.on_checkbox_toggled(checked, row, col))
        self.table.setCellWidget(1, 1, chk1_1)
        item1_2 = QTableWidgetItem("Dias Promedio")
        item1_2.setFlags(item1_2.flags() & ~Qt.ItemIsEditable)
        self.table.setItem(1, 2, item1_2)
        chk1_3 = QCheckBox()
        chk1_3.toggled.connect(lambda checked, row=1, col=3: self.on_checkbox_toggled(checked, row, col))
        self.table.setCellWidget(1, 3, chk1_3)

        # Fila 2: Costo Total | | | 
        item2_0 = QTableWidgetItem("Costo Total")
        item2_0.setFlags(item2_0.flags() & ~Qt.ItemIsEditable)
        self.table.setItem(2, 0, item2_0)
        chk2_1 = QCheckBox()
        chk2_1.toggled.connect(lambda checked, row=2, col=1: self.on_checkbox_toggled(checked, row, col))
        self.table.setCellWidget(2, 1, chk2_1)
        item2_2 = QTableWidgetItem("")
        item2_2.setFlags(item2_2.flags() & ~Qt.ItemIsEditable)
        self.table.setItem(2, 2, item2_2)
        # No hay checkbox en columna 3 de la fila 2

    def on_checkbox_toggled(self, checked, current_row, current_col):
        """
        Maneja la selección exclusiva de checkboxes por columna.
        Solo un checkbox puede estar seleccionado por columna de validación.
        """
        if checked:
            # Si se selecciona este checkbox, deseleccionar los otros de la misma columna
            for row in range(self.table.rowCount()):
                if row != current_row:
                    chk = self.table.cellWidget(row, current_col)
                    if chk:
                        chk.blockSignals(True)  # Evitar recursión
                        chk.setChecked(False)
                        chk.blockSignals(False)


    def save_to_csv(self):
        data = []
        for row in range(self.table.rowCount()):
            ruta_costos_item = self.table.item(row, 0)
            ruta_costos = ruta_costos_item.text() if ruta_costos_item else ""
            chk_costos = self.table.cellWidget(row, 1)
            validacion_costos = chk_costos.isChecked() if chk_costos else False
            ruta_dias_item = self.table.item(row, 2)
            ruta_dias = ruta_dias_item.text() if ruta_dias_item else ""
            chk_dias = self.table.cellWidget(row, 3)
            validacion_dias = chk_dias.isChecked() if chk_dias else False
            data.append({
                "Ruta Costos": ruta_costos,
                "Validacion Costos": validacion_costos,
                "Ruta Dias": ruta_dias,
                "Validacion Dias": validacion_dias
            })
        df = pd.DataFrame(data)
        try:
            df.to_csv(self.csv_path, index=False)
            QMessageBox.information(self, "Guardado", f"Archivo guardado en: {self.csv_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo guardar el archivo: {e}")

    def load_from_csv(self):
        if os.path.exists(self.csv_path):
            try:
                df = pd.read_csv(self.csv_path)
                # Solo actualiza las filas existentes (3 filas fijas)
                for row_idx in range(3):
                    if row_idx < len(df):
                        row = df.iloc[row_idx]
                        # Actualiza texto de columnas no editables
                        if self.table.item(row_idx, 0):
                            ruta_costos_val = row.get("Ruta Costos", "")
                            if pd.isna(ruta_costos_val):
                                ruta_costos_val = ""
                            self.table.item(row_idx, 0).setText(str(ruta_costos_val))
                        chk_costos = self.table.cellWidget(row_idx, 1)
                        if chk_costos:
                            chk_costos.blockSignals(True)
                            chk_costos.setChecked(bool(row.get("Validacion Costos", False)))
                            chk_costos.blockSignals(False)
                        if self.table.item(row_idx, 2):
                            ruta_dias_val = row.get("Ruta Dias", "")
                            if pd.isna(ruta_dias_val):
                                ruta_dias_val = ""
                            self.table.item(row_idx, 2).setText(str(ruta_dias_val))
                        # Solo actualiza el checkbox de columna 3 si existe (no existe en fila 2)
                        chk_dias = self.table.cellWidget(row_idx, 3)
                        if chk_dias:
                            chk_dias.blockSignals(True)
                            chk_dias.setChecked(bool(row.get("Validacion Dias", False)))
                            chk_dias.blockSignals(False)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"No se pudo cargar el archivo: {e}")

    def get_validated_records(self):
        """
        Devuelve una lista con los IDs de los registros validados (costos o días).
        Ejemplo: ["costo_target_input", "dias_promedio_calculado"]
        """
        validados = []
        for row in range(self.table.rowCount()):
            chk_costos = self.table.cellWidget(row, 1)
            chk_dias = self.table.cellWidget(row, 3)
            
            # Verificar checkbox de costos (columna 1)
            if chk_costos and chk_costos.isChecked():
                record_id = self.record_ids.get((row, 0))  # Columna 0 para costos
                if record_id:
                    validados.append(record_id)
            
            # Verificar checkbox de días (columna 3) - no existe en fila 2
            if chk_dias and chk_dias.isChecked():
                record_id = self.record_ids.get((row, 2))  # Columna 2 para días
                if record_id:
                    validados.append(record_id)
        
        return validados

    def closeEvent(self, event):
        """
            Este método se activa justo antes de que la ventana se cierre.         
            Nos aseguramos de cerrar todas las ventanas de resultados hijas que se abrieron.
        """
        # Itera sobre la lista de ventanas de resultados y cierra cada una
        for window in self.result_windows:
            window.close()
        if hasattr(self, 'info_view') and self.info_view is not None:
            self.info_view.close()
        # Llama al método original para que la ventana principal se cierre correctamente
        super().closeEvent(event)

from PyQt5.QtWidgets import (
    QHeaderView, QDialog, QPushButton, QLabel, QVBoxLayout,
    QFileDialog, QMessageBox, QTableWidget, QTableWidgetItem,
    QComboBox, QHBoxLayout, QCheckBox
)
from PyQt5.QtGui import QFontMetrics
from PyQt5.QtCore import Qt, pyqtSignal
from services.field_lines_services.quote_extractor_service import QuoteExtractorService, MONTHS, VALIDATIONS
from datetime import datetime
import random

from views.field_views.total_widget import TotalsWidget


class QuoteExtractorView(QDialog):
    data_changed = pyqtSignal()
    completion_status_changed = pyqtSignal(bool)
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Varillera's Scheduled Activities Path")
        self.setGeometry(200, 200, 1200, 700)

        self.service = QuoteExtractorService()
        self.columnas = self.service.get_columns()
        self.completed_checkbox = QCheckBox("Completed")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(len(self.columnas))
        self.tabla.setHorizontalHeaderLabels(self.columnas)
        header = self.tabla.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setSectionResizeMode(self.tabla.columnCount() - 1, QHeaderView.Stretch)
        layout.addWidget(self.tabla)

        self.totals_widget = TotalsWidget()
        layout.addWidget(self.totals_widget)

        boton_cargar_pdf = QPushButton("Load PDFs")
        boton_cargar_pdf.clicked.connect(self.load_pdfs)
        boton_cargar_pdf.setSizePolicy(QPushButton().sizePolicy().Expanding, QPushButton().sizePolicy().Fixed)
        layout.addWidget(boton_cargar_pdf)
        botones_layout = QHBoxLayout()
        boton_eliminar = QPushButton("Delete Selected Row")
        boton_eliminar.clicked.connect(self.delete_row)
        boton_agregar_nuevo = QPushButton("Add New")
        boton_agregar_nuevo.clicked.connect(self.add_new_row)
        boton_save = QPushButton("Save")
        boton_save.clicked.connect(self.save_csv)
        botones_layout.addWidget(boton_eliminar)
        botones_layout.addWidget(boton_agregar_nuevo)
        botones_layout.addWidget(boton_save)
        botones_layout.addWidget(self.completed_checkbox)
        layout.addLayout(botones_layout)
        self.completed_checkbox.stateChanged.connect(self.on_completion_changed)
        self.setLayout(layout)

    def on_completion_changed(self, state):
        self.completion_status_changed.emit(state == Qt.Checked)

    def set_completion_status(self, is_completed: bool):
        self.completed_checkbox.blockSignals(True)
        self.completed_checkbox.setChecked(is_completed)
        self.completed_checkbox.blockSignals(False)
        
    def update_totals(self, data: dict):
        if hasattr(self, 'totals_widget'):
            self.totals_widget.update_data(data)

    def load_pdfs(self):
        rutas, _ = QFileDialog.getOpenFileNames(self, "Select PDF of Quote", "", "PDF Files (*.pdf)")
        for ruta in rutas:
            datos = self.service.extract_data_from_pdf(ruta)
            quote_number = datos.get("Quote Number")

            if not quote_number:
                QMessageBox.warning(self, "Invalid PDF", f"The file '{ruta}' does not have the 'Quote Number' column'. It will be ommited.")
                continue

            if any(
                self.tabla.item(row, 0) and self.tabla.item(row, 0).text() == quote_number
                for row in range(self.tabla.rowCount())
            ):
                continue

            if quote_number in self.service.dataframe["Quote Number"].astype(str).values:
                continue

            self.add_row_to_table(datos)

        self.sort_table_by_date()
        self.data_changed.emit() # Notificar al final
    
    def get_validated_quote_sum(self):
        """
        Lee la tabla, maneja comas en los números, y devuelve la suma
        de 'Net Total (USD)' solo para las filas con validación "Yes".
        """
        total = 0.0
        for row in range(self.tabla.rowCount()):
            try:
                validation_widget = self.tabla.cellWidget(row, self.columnas.index("Validation"))
                if validation_widget and validation_widget.currentText().lower() == 'yes':
                    cost_item = self.tabla.item(row, self.columnas.index("Net Total (USD)"))
                    # Elimina comas para una conversión segura a float
                    cost_text = cost_item.text().replace(',', '')
                    total += float(cost_text)
            except (ValueError, AttributeError, IndexError, TypeError):
                # Ignorar filas con datos incompletos o formato incorrecto
                continue
        return total

    def add_row_to_table(self, datos):
        fila = self.tabla.rowCount()
        self.tabla.insertRow(fila)

        for col, campo in enumerate(self.columnas):
            campo_limpio = campo.strip()
            if campo_limpio == "Scheduled Execution Month":
                combo = QComboBox()
                combo.addItems(MONTHS)
                combo.setCurrentText(str(datos.get(campo, "")))
                self.tabla.setCellWidget(fila, col, combo)
            elif campo_limpio == "Validation":
                combo = QComboBox()
                combo.addItems(VALIDATIONS)
                combo.setCurrentText(str(datos.get(campo, "Pending")))
                self.tabla.setCellWidget(fila, col, combo)
            else:
                item = QTableWidgetItem(str(datos.get(campo, "")))
                # Hacer ineditables los campos específicos
                if campo_limpio in ["Quote Number", "Quote Effective Date", "Year"]:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.tabla.setItem(fila, col, item)
        if "Validation" in self.columnas:
            col = self.columnas.index("Validation")
            widget = self.tabla.cellWidget(fila, col)
            if isinstance(widget, QComboBox):
                widget.currentTextChanged.connect(self.data_changed.emit)

    def delete_row(self):
        filas = sorted(set(index.row() for index in self.tabla.selectedIndexes()), reverse=True)
        quote_numbers_a_eliminar = []

        for fila in filas:
            item = self.tabla.item(fila, 0)
            if item:
                quote_numbers_a_eliminar.append(item.text())
            self.tabla.removeRow(fila)

        self.service.dataframe = self.service.dataframe[
            ~self.service.dataframe["Quote Number"].astype(str).isin(quote_numbers_a_eliminar)
        ].reset_index(drop=True)
        self.data_changed.emit() # Notificar al final

    def save_csv(self):
        registros = []
        for fila in range(self.tabla.rowCount()):
            registro = {}
            for col, campo in enumerate(self.columnas):
                campo_limpio = campo.strip()
                if campo_limpio in ["Scheduled Execution Month", "Validation"]:
                    widget = self.tabla.cellWidget(fila, col)
                    if isinstance(widget, QComboBox):
                        registro[campo] = widget.currentText()
                else:
                    item = self.tabla.item(fila, col)
                    registro[campo] = item.text() if item else None  # Asignar None si el campo está vacío

            # Verificar si algún valor en el registro es None
            if any(valor is None or valor == "" for valor in registro.values()):
                QMessageBox.critical(
                    self,
                    "Error al guardar",
                    f"Unable to save due to empty or 'None' fields in row {fila + 1}. Please, check the data."
                )
                return  # Detener el guardado si hay valores inválidos

            registros.append(registro)

        try:
            registros.sort(key=lambda x: datetime.strptime(x.get("Quote Effective Date", ""), "%d-%b-%Y"))
        except Exception as e:
            print("[WARN] No se pudo ordenar registros para guardar:", e)

        for reg in registros:
            self.service.add_or_update_entry(reg)

        try:
            # Guardar como texto, no como datetime
            df = self.service.dataframe.copy()
            if "Quote Effective Date" in df.columns:
                df["Quote Effective Date"] = df["Quote Effective Date"].astype(str)
            df.to_csv(self.service.CSV_PATH, index=False)
            QMessageBox.information(self, "Saved", "Path saved succesfully.")
        except PermissionError:
            QMessageBox.critical(self, "Access Error", "You must close any cotitation file before do any action.")
        self.data_changed.emit() # Notificar al final

    def add_new_row(self):
        # Generar un Quote Number único
        while True:
            quote_number = f"QR.{random.randint(10000000, 99999999)}"
            if not any(
                self.tabla.item(row, 0) and self.tabla.item(row, 0).text() == quote_number
                for row in range(self.tabla.rowCount())
            ):
                break

        # Obtener la fecha y el año actuales
        current_date = datetime.now().strftime("%d-%b-%Y")
        current_year = datetime.now().year

        # Crear un nuevo registro con valores predeterminados
        nuevo_registro = {
            "Quote Number": quote_number,
            "Quote Effective Date": current_date,
            "Year": current_year,
            "UWI/API": "",
            "Net Total (USD)": "",
            "Scheduled Execution Month": "",
            "Validation": "Pending"
        }

        # Insertar el nuevo registro en la tabla
        self.add_row_to_table(nuevo_registro)
        self.data_changed.emit() # Notificar al final

    def load_data_from_csv(self):
        registros = self.service.get_data_as_list()

        try:
            registros.sort(key=lambda x: datetime.strptime(x.get("Quote Effective Date", ""), "%d-%b-%Y"))
        except Exception as e:
            print("[WARN] No se pudo ordenar registros para mostrar:", e)

        for registro in registros:
            self.add_row_to_table(registro)
        self.data_changed.emit() # Notificar al final

    def sort_table_by_date(self):
        filas = []
        for row in range(self.tabla.rowCount()):
            fila_dict = {}
            for col, campo in enumerate(self.columnas):
                campo_limpio = campo.strip()
                if campo_limpio in ["Scheduled Execution Month", "Validation"]:
                    widget = self.tabla.cellWidget(row, col)
                    fila_dict[campo] = widget.currentText() if widget else ""
                else:
                    item = self.tabla.item(row, col)
                    fila_dict[campo] = item.text() if item else ""
            filas.append(fila_dict)

        try:
            filas.sort(key=lambda x: datetime.strptime(x.get("Quote Effective Date", ""), "%d-%b-%Y"))
        except Exception as e:
            print("[WARN] No se pudo ordenar visualmente la tabla:", e)

        self.tabla.setRowCount(0)
        for fila in filas:
            self.add_row_to_table(fila)

    def closeEvent(self, event):
        """
        Sobrescribe el evento de cierre de la ventana para validar los datos y guardar automáticamente.
        """
        # Validar si hay valores vacíos o 'None' en la tabla
        for fila in range(self.tabla.rowCount()):
            for col, campo in enumerate(self.columnas):
                campo_limpio = campo.strip()
                if campo_limpio in ["Scheduled Execution Month", "Validation"]:
                    widget = self.tabla.cellWidget(fila, col)
                    if isinstance(widget, QComboBox) and not widget.currentText():
                        QMessageBox.critical(
                            self,
                            "Error while closing",
                            f"Cannot close the window because there are empty fields in row {fila + 1}. Please review the data."
                        )
                        event.ignore()  # Evita que la ventana se cierre
                        return
                else:
                    item = self.tabla.item(fila, col)
                    if not item or not item.text().strip():
                        QMessageBox.critical(
                            self,
                            "Error while closing",
                            f"Cannot close the window because there are empty fields in row {fila + 1}. Please review the data."
                        )
                        event.ignore()  # Evita que la ventana se cierre
                        return
        event.accept()  # Permite que la ventana se cierre

    def get_validated_quote_count(self):
        """
        Cuenta el número de filas en la tabla que tienen la validación "Yes".
        """
        count = 0
        for row in range(self.tabla.rowCount()):
            try:
                validation_widget = self.tabla.cellWidget(row, self.columnas.index("Validation"))
                if validation_widget and validation_widget.currentText().lower() == 'yes':
                    count += 1
            except (ValueError, AttributeError, IndexError):
                continue
        return count

    def get_costs_from_ui(self, last_valid_month_index: int):
        """
        Lee la tabla y calcula los costos, usando el último mes con actividad
        real como el punto de corte entre "real" y "forecast".
        """
        real_cost = 0.0
        forecast_cost = 0.0

        for row in range(self.tabla.rowCount()):
            try:
                validation_widget = self.tabla.cellWidget(row, self.columnas.index("Validation"))
                if not validation_widget or validation_widget.currentText().lower() != 'yes':
                    continue

                month_widget = self.tabla.cellWidget(row, self.columnas.index("Scheduled Execution Month"))
                month_name = month_widget.currentText().title()
                # Convertimos el nombre del mes a un índice 0-based (Enero=0)
                month_index = MONTHS.index(month_name)

                cost_item = self.tabla.item(row, self.columnas.index("Net Total (USD)"))
                cost_text = cost_item.text().replace(',', '')
                cost = float(cost_text)
                if month_index <= last_valid_month_index:
                    real_cost += cost
                else:
                    forecast_cost += cost
            
            except (ValueError, AttributeError, IndexError, TypeError):
                continue
        
        return real_cost, forecast_cost
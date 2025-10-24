
import pandas as pd
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QComboBox, QHBoxLayout, QMessageBox
)
from PyQt5.QtCore import Qt
from utils.file_manager import get_catalog_path

class CatalogViewerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Catálogo de Costos")
        self.resize(800, 600)

        self.fixed_catalog_path = get_catalog_path()
        self.sheet_map = {
            "1.04 Bits, Drilling Tools & Remedial (B,D &R)": "Bits, Drilling Tools",
            "1.05 Surface Systems (CSUR)": "Surface Systems",
            "1.06 Wireline (WL)": "Wireline",
            "1.07 Well Services (WS)": "Well Services",
            "1.09 Tubulars (TUB)": "Tubulars",
            "1.10 Services": "Services",
            "1.11 Environment": "Environment",
            "1.14 Integrated Services Management": "Integrated Services"
        }

        layout = QVBoxLayout(self)

        self.label_line = QLabel("Selecciona la línea:")
        layout.addWidget(self.label_line)

        self.line_combo = QComboBox()
        self.line_combo.addItems(self.sheet_map.keys())
        layout.addWidget(self.line_combo)

        button_layout = QHBoxLayout()
        self.load_button = QPushButton("Cargar Catálogo")
        self.load_button.clicked.connect(self.load_catalog)
        button_layout.addWidget(self.load_button)

        self.save_button = QPushButton("Guardar Cambios")
        self.save_button.clicked.connect(self.save_changes)
        button_layout.addWidget(self.save_button)

        self.add_row_button = QPushButton("Agregar Fila")
        self.add_row_button.clicked.connect(self.add_row)
        button_layout.addWidget(self.add_row_button)

        self.remove_row_button = QPushButton("Eliminar Fila")
        self.remove_row_button.clicked.connect(self.remove_selected_row)
        button_layout.addWidget(self.remove_row_button)

        layout.addLayout(button_layout)

        self.table_widget = QTableWidget()
        layout.addWidget(self.table_widget)

        self.df = pd.DataFrame()
        self.current_sheet = None

    def load_catalog(self):
        selected_line = self.line_combo.currentText()
        self.current_sheet = self.sheet_map.get(selected_line, None)
        if not self.current_sheet:
            return

        try:
            df = pd.read_excel(self.fixed_catalog_path, sheet_name=self.current_sheet)

            if self.current_sheet == "Services":
                if not ((df['line'] == '__INPUT__') & (df['TIPO'] == 'duration')).any():
                    df = pd.concat([df, pd.DataFrame([{
                        'line': '__INPUT__', 'TIPO': 'duration', 'valor': ''
                    }])], ignore_index=True)

                if not ((df['line'] == '__INPUT__') & (df['TIPO'] == 'target_cost')).any():
                    df = pd.concat([df, pd.DataFrame([{
                        'line': '__INPUT__', 'TIPO': 'target_cost','valor': ''
                    }])], ignore_index=True)

            self.df = df
            self.populate_table(df)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar el catálogo: {e}")

    def populate_table(self, df):
        self.table_widget.setRowCount(len(df))
        self.table_widget.setColumnCount(len(df.columns))
        self.table_widget.setHorizontalHeaderLabels([col.upper() for col in df.columns])

        for i in range(len(df)):
            for j in range(len(df.columns)):
                header = df.columns[j].strip().lower()

                # Si estamos en la hoja COMPLETIONS y es la columna 'Mes' y fila 'Costo adicional'
                if (self.current_sheet == "COMPLETIONS" and
                    header == "mes" and
                    str(df.iloc[i]["Descripción"]).strip().lower() == "costo adicional"):
                    
                    combo = QComboBox()
                    combo.addItems([
                        "January", "February", "March", "April", "May", "June",
                        "July", "August", "September", "October", "November", "December"
                    ])
                    
                    # Si ya existe un valor de mes, seleccionarlo
                    current_value = str(df.iat[i, j]).strip()
                    if current_value in combo.model().stringList():
                        combo.setCurrentText(current_value)

                    self.table_widget.setCellWidget(i, j, combo)

                else:
                    # Celda normal editable
                    item = QTableWidgetItem(str(df.iat[i, j]))
                    item.setFlags(item.flags() | Qt.ItemIsEditable)
                    self.table_widget.setItem(i, j, item)


    def save_changes(self):
        try:
            new_data = []
            for row in range(self.table_widget.rowCount()):
                row_data = []
                for col in range(self.table_widget.columnCount()):
                    widget = self.table_widget.cellWidget(row, col)
                    if widget and isinstance(widget, QComboBox):
                        row_data.append(widget.currentText())
                    else:
                        item = self.table_widget.item(row, col)
                        row_data.append(item.text() if item else '')
                new_data.append(row_data)

            new_df = pd.DataFrame(new_data, columns=self.df.columns)

            # Validar inputs solo para la hoja Services
            if self.current_sheet == "Services":
                valid, error_msg = self.validar_inputs_de_services(new_df)
                if not valid:
                    QMessageBox.warning(self, "Error de Validación", error_msg)
                    return

            with pd.ExcelWriter(self.fixed_catalog_path, mode='a', if_sheet_exists='replace', engine='openpyxl') as writer:
                new_df.to_excel(writer, sheet_name=self.current_sheet, index=False)

            QMessageBox.information(self, "Éxito", "Cambios guardados correctamente.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudieron guardar los cambios: {e}")


    def validar_inputs_de_services(self, df):
        try:
            dur_row = df[(df["line"] == "__INPUT__") & (df["TIPO"] == "duration")]
            cost_row = df[(df["line"] == "__INPUT__") & (df["TIPO"] == "target_cost")]

            if dur_row.empty or cost_row.empty:
                return False, "Faltan las filas de duración o costo esperado."

            dur_val = float(dur_row["valor"].values[0])
            cost_val = float(cost_row["valor"].values[0])

            if dur_val <= 0 or cost_val <= 0:
                return False, "Los valores deben ser mayores que cero."

            return True, ""
        except Exception:
            return False, "Los valores de duración y costo deben ser numéricos válidos."

    def add_row(self):
        current_row_count = self.table_widget.rowCount()
        self.table_widget.insertRow(current_row_count)
        for col in range(self.table_widget.columnCount()):
            self.table_widget.setItem(current_row_count, col, QTableWidgetItem(""))

    def remove_selected_row(self):
        selected_row = self.table_widget.currentRow()
        if selected_row >= 0:
            self.table_widget.removeRow(selected_row)


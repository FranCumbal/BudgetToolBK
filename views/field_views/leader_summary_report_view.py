import pandas as pd
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton,
    QFileDialog, QMessageBox, QHeaderView, QHBoxLayout, QApplication
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont

class LeaderSummaryReportView(QDialog):
    def __init__(self, data_df: pd.DataFrame, controller, parent=None):
        super().__init__(parent)
        self.data_df = data_df
        self.controller = controller
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Leader Line Summary Report")
        # La ventana se mostrará maximizada desde el controlador para asegurar que el contenido se expanda correctamente.
        layout = QVBoxLayout(self)

        self.table_widget = QTableWidget()
        self.populate_table()
        layout.addWidget(self.table_widget)

        # Layout para botones
        button_layout = QHBoxLayout()

        refresh_button = QPushButton("Refresh Data")
        refresh_button.clicked.connect(self.handle_refresh)
        button_layout.addWidget(refresh_button)

        export_button = QPushButton("Export to Excel")
        export_button.clicked.connect(self.export_to_excel)
        button_layout.addWidget(export_button)
        layout.addLayout(button_layout)

    def populate_table(self):
        if self.data_df.empty:
            return
        # --- 1. Preparar el DataFrame para la visualización ---
        # Crear una copia para no modificar el original
        display_df = pd.DataFrame()
        # Mapeo de columnas y nombres nuevos con saltos de línea
        display_df["Resource\nName"] = self.data_df["contractual activity"]
        display_df["Planned\nActivities"] = self.data_df["approved activities"]
        display_df["Approved\nBudget"] = self.data_df["approved budget"]
        # Columnas con nombre de mes dinámico
        # Tomamos el mes de la primera fila como referencia para el encabezado
        month = self.data_df['last valid month'].iloc[0].capitalize()
        display_df[f"Accumulated\nExecuted Act. ({month})"] = self.data_df["executed activities"]
        display_df[f"Accumulated\nExecuted Cost ({month})"] = self.data_df["last valid real cost"]
        display_df["Forecast\nActivities (December)"] = self.data_df["last valid forecast activities"]
        display_df["Forecast\nCost (December)"] = self.data_df["last valid forecast cost"]
        display_df["Activities\nBalance"] = self.data_df["activities balance"]
        display_df["Cost\nBalance"] = self.data_df["cost balance"]
        # --- 2. Calcular la fila de totales ---
        # Seleccionar solo columnas numéricas para la suma
        numeric_cols = display_df.select_dtypes(include=['number']).columns
        totals = display_df[numeric_cols].sum()
        totals["Resource\nName"] = "Total Rigless" # Etiqueta para la fila de totales
        # --- 3. Configurar la tabla ---
        num_rows = display_df.shape[0]
        self.table_widget.setRowCount(num_rows + 1) # +1 para la fila de totales
        self.table_widget.setColumnCount(display_df.shape[1])
        self.table_widget.setHorizontalHeaderLabels(display_df.columns)
        # Estilo para la cabecera (azul, texto blanco y negrita)
        header_style = """
            QHeaderView::section {
                background-color: #2874A6; /* QColor(40, 116, 166) */
                color: white;
                padding: 4px;
                border: 1px solid #6c757d;
                font-weight: bold;
            }
        """
        self.table_widget.horizontalHeader().setStyleSheet(header_style)
        # --- 4. Llenar la tabla con los datos ---
        money_columns = ["Approved\nBudget", f"Accumulated\nExecuted Cost ({month})", "Forecast\nCost (December)", "Cost\nBalance"]
        
        for i in range(num_rows):
            for j, col in enumerate(display_df.columns):
                value = display_df.iat[i, j]
                item_text = ""
                if isinstance(value, (int, float)):
                    # Formato con comas y 2 decimales
                    item_text = f"{value:,.2f}"
                    # Añadir símbolo de dólar si es una columna de dinero
                    if col in money_columns:
                        item_text = f"${item_text}"
                else:
                    item_text = str(value)
                
                item = QTableWidgetItem(item_text)

                # Estilo para la primera columna (azul, texto blanco y negrita)
                if j == 0:
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
                    item.setBackground(QColor(40, 116, 166))  # Azul oscuro
                    item.setForeground(Qt.white)
                # Estilo para valores negativos (rojo suave)
                elif pd.api.types.is_number(value) and value < 0:
                    item.setForeground(QColor(204, 41, 54))  # Rojo suave

                self.table_widget.setItem(i, j, item)

        # --- 5. Llenar la fila de totales ---
        
        total_row_index = num_rows

        # Calcular porcentajes para los balances
        total_planned_activities = totals.get("Planned\nActivities", 0)
        total_approved_budget = totals.get("Approved\nBudget", 0)
        total_activities_balance = totals.get("Activities\nBalance", 0)
        total_cost_balance = totals.get("Cost\nBalance", 0)

        activities_balance_percentage = 0
        if total_planned_activities != 0:
            activities_balance_percentage = (total_activities_balance / total_planned_activities) * 100

        cost_balance_percentage = 0
        if total_approved_budget != 0:
            cost_balance_percentage = (total_cost_balance / total_approved_budget) * 100

        for j, col in enumerate(display_df.columns):
            item_text = ""
            if col in totals:
                value = totals[col]
                if col == "Resource\nName":
                    item_text = str(value)
                else:
                    # Formato con comas y 2 decimales
                    item_text = f"{value:,.2f}"
                    # Añadir símbolo de dólar si es una columna de dinero
                    if col in money_columns:
                        item_text = f"${item_text}"

            # Añadir el porcentaje a las celdas de balance
            if col == "Activities\nBalance":
                item_text += f" ({activities_balance_percentage:.2f}%)"
            elif col == "Cost\nBalance":
                item_text += f" ({cost_balance_percentage:.2f}%)"

            item = QTableWidgetItem(item_text)
            
            # Estilo para la fila de totales (verde, texto en negrita)
            font = item.font()
            font.setBold(True)
            item.setFont(font)
            item.setBackground(QColor(212, 239, 223)) # Verde claro

            # Estilo para valores negativos en la fila de totales
            if col in totals and pd.api.types.is_number(totals[col]) and totals[col] < 0:
                item.setForeground(QColor(204, 41, 54)) # Rojo suave

            self.table_widget.setItem(total_row_index, j, item)

        # Ajustar el tamaño de las columnas para que se estiren y el texto se divida en dos líneas.
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_widget.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_widget.resizeRowsToContents()

    def export_to_excel(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save File", "", "Excel Files (*.xlsx)"
        )
        if file_path:
            try:
                # Obtener encabezados de la tabla
                column_headers = []
                for j in range(self.table_widget.columnCount()):
                    header_text = self.table_widget.horizontalHeaderItem(j).text()
                    # Reemplazar saltos de línea para nombres de columna más limpios en Excel
                    column_headers.append(header_text.replace('\n', ' '))

                # Extraer datos de la tabla, incluyendo la fila de totales
                data = []
                for i in range(self.table_widget.rowCount()):
                    row_data = []
                    for j in range(self.table_widget.columnCount()):
                        item = self.table_widget.item(i, j)
                        row_data.append(item.text() if item else '')
                    data.append(row_data)

                # Crear un DataFrame con los datos visualizados
                df_to_export = pd.DataFrame(data, columns=column_headers)

                # Limpiar y convertir columnas a tipo numérico para que sean útiles en Excel
                # La primera columna ("Resource Name") se omite de la conversión.
                for col in df_to_export.columns[1:]:
                    # Eliminar '$', comas y el texto de porcentaje ' (xx.xx%)'
                    cleaned_series = df_to_export[col].str.replace('$', '', regex=False)
                    cleaned_series = cleaned_series.str.replace(',', '', regex=False)
                    cleaned_series = cleaned_series.str.split('(').str[0].str.strip()
                    # Convertir a numérico, los errores se convierten en celdas vacías (NaN)
                    df_to_export[col] = pd.to_numeric(cleaned_series, errors='coerce')

                # Exportar el DataFrame procesado
                df_to_export.to_excel(file_path, index=False)
                QMessageBox.information(
                    self, "Success", f"Data successfully exported to {file_path}"
                )
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not export to Excel: {e}")

    def handle_refresh(self):
        """
        Manejador para el botón de refresco. Llama al controlador para
        obtener datos nuevos y luego actualiza la tabla.
        """
        reply = QMessageBox.question(self, "Confirm Refresh", 
                                     "This will recalculate all data from the source files. This may take a moment. Are you sure you want to continue?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.table_widget.setEnabled(False) # Deshabilitar tabla mientras carga
            QApplication.setOverrideCursor(Qt.WaitCursor)
            
            new_df = self.controller.refresh_leader_summary_data()
            self.data_df = new_df
            self.populate_table() # Redibuja la tabla con los nuevos datos
            
            QApplication.restoreOverrideCursor()
            self.table_widget.setEnabled(True)
            QMessageBox.information(self, "Success", "Report data has been refreshed.")

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor
from calendar import month_name

import pandas as pd

class PlanningTableWidget(QWidget):
    # Señal que se emitirá cuando el usuario edite una celda
    item_edited = pyqtSignal(int, int, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # El widget principal es la tabla
        self.table = QTableWidget()
        
        # --- Configuración inicial de la tabla ---
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Layout interno
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.table)
        
        # Conectar la señal interna de la tabla a un método nuestro
        self.table.itemChanged.connect(self._on_item_changed)

    def update_view(self, view_data: dict):
        """
        Método principal para redibujar toda la tabla con nuevos datos y configuración.
        """
        # Bloqueamos las señales para evitar que 'itemChanged' se dispare mientras llenamos la tabla
        self.table.blockSignals(True)
        
        # --- Llenado de datos (antes en _setup_table) ---
        data = view_data.get("data_list", [])
        columns = view_data.get("columns", [])
        
        self.table.setColumnCount(len(columns))
        self.table.setRowCount(len(data))
        self.table.setHorizontalHeaderLabels(columns)

        for row_idx, row_data in enumerate(data):
            for col_idx, col_name in enumerate(columns):
                value = row_data.get(col_name, 0)
                if col_name == "Scheduled Activities":
                    try:
                        value = int(float(value))
                    except (ValueError, TypeError):
                        value = 0
                item = QTableWidgetItem(str(value)) # Ahora 'value' ya es un entero
                if col_name != "Month":
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row_idx, col_idx, item)

        self._apply_real_data(view_data)

        self._configure_all_cells(view_data)

        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()
        header_height = self.table.horizontalHeader().height()
        row_height = self.table.rowHeight(0) if self.table.rowCount() > 0 else 20
        total_height = header_height + (row_height * self.table.rowCount()) + 4
        self.setMinimumHeight(total_height)
        
        # Desbloqueamos las señales
        self.table.blockSignals(False)

    def get_column_totals(self, last_month_index: int):
        """
        Calcula los totales. Suma 'Planned Activities' de todas las filas,
        pero 'Scheduled Activities' solo de las filas futuras (editables).
        """
        planned_total = 0
        scheduled_total = 0
        
        columns = [self.table.horizontalHeaderItem(i).text() for i in range(self.table.columnCount())]
        
        for row in range(self.table.rowCount()):
            try:
                # Planned Activities siempre se suma
                if "Planned Activities" in columns:
                    planned_idx = columns.index("Planned Activities")
                    item = self.table.item(row, planned_idx)
                    if item and item.text():
                        planned_total += int(float(item.text()))
                
                # Scheduled Activities solo se suma para meses futuros
                if "Scheduled Activities" in columns:
                    # --- LÓGICA CORREGIDA ---
                    if row > last_month_index:
                        scheduled_idx = columns.index("Scheduled Activities")
                        item = self.table.item(row, scheduled_idx)
                        if item and item.text():
                            scheduled_total += float(item.text())
            except (ValueError, AttributeError):
                continue
                
        return planned_total, int(scheduled_total)

    def get_column_sum(self, column_name: str) -> float:
        """Suma todos los valores numéricos de una columna específica."""
        total = 0.0
        
        try:
            columns = [self.table.horizontalHeaderItem(i).text() for i in range(self.table.columnCount())]
            if column_name not in columns:
                return total

            col_idx = columns.index(column_name)
            for row in range(self.table.rowCount()):
                item = self.table.item(row, col_idx)
                if item and item.text():
                    total += float(item.text())
        except (ValueError, TypeError):
            # Ignorar si un valor no es numérico
            pass
            
        return total

    def _apply_real_data(self, view_data: dict):
        """Aplica los datos históricos a las columnas de Forecast y Scheduled."""
        last_month_index = view_data.get("last_month_index", -1)
        if last_month_index == -1:
            return

        columns = view_data.get("columns", [])
        
        # Aplicar costos reales a Forecast
        if "Forecast" in columns:
            real_costs = view_data.get("real_costs", pd.Series(dtype=float))
            col_idx = columns.index("Forecast")
            for i in range(last_month_index + 1):
                if i < len(real_costs):
                    item = self.table.item(i, col_idx)
                    # Accedemos directamente a la Serie por su índice
                    item.setText(str(round(real_costs.iloc[i], 2)))

        # Aplicar actividades ejecutadas a Scheduled Activities
        if "Scheduled Activities" in columns:
            executed_activities_df = view_data.get("executed_activities", pd.DataFrame())
            col_idx = columns.index("Scheduled Activities")
            # --- LÓGICA CORREGIDA ---
            for i in range(last_month_index + 1):
                if i < len(executed_activities_df):
                    item = self.table.item(i, col_idx)
                    # Primero accedemos a la columna (que es una Serie) y luego al índice de la fila
                    activity_value = executed_activities_df['Executed Activities'].iloc[i]
                    item.setText(str(activity_value))

    def _configure_all_cells(self, view_data):
        """Recorre todas las celdas y aplica las reglas de edicion y color."""
        last_month_index = view_data.get("last_month_index", -1)
        editable_columns = view_data.get("editable_columns", [])
        
        for row_idx in range(self.table.rowCount()):
            for col_idx in range(self.table.columnCount()):
                item = self.table.item(row_idx, col_idx)
                col_name = self.table.horizontalHeaderItem(col_idx).text()
                
                # Lógica de configuración
                if col_name == "Month":
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    item.setBackground(QColor(240, 240, 240))
                elif col_name in ["Forecast", "Scheduled Activities"]:
                    if row_idx > last_month_index:
                        pass 
                    else:
                        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                        color = QColor(230, 255, 230)
                        item.setBackground(color)
                elif col_name in editable_columns:
                    pass # Editable
                else:
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    item.setBackground(QColor(240, 240, 240))

    def _on_item_changed(self, item):
        """Captura la señal interna y emite nuestra propia señal más limpia."""
        self.item_edited.emit(item.row(), item.column(), item.text())
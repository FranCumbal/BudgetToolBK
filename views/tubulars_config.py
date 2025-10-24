import sys
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem,
                             QComboBox, QPushButton, QHBoxLayout, QLabel)
from PyQt5.QtCore import Qt
import pandas as pd

class TubularsConfigDialog(QDialog):
    def __init__(self, df_config, pipe_catalog, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configurar Tubería Nueva (1.09 Tubulars)")
        self.df_config = df_config.copy()
        self.pipe_catalog = pipe_catalog

        self.layout = QVBoxLayout(self)

        self.table = QTableWidget(self)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Month","PipeDesc","Feet", "TotalCost"])
        self.layout.addWidget(self.table)

        # Botones
        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("Add Row")
        self.btn_remove = QPushButton("Remove Row")
        self.btn_ok = QPushButton("OK")
        self.btn_cancel = QPushButton("Cancel")

        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_remove)
        btn_layout.addWidget(self.btn_ok)
        btn_layout.addWidget(self.btn_cancel)
        self.layout.addLayout(btn_layout)

        self.btn_add.clicked.connect(self.add_row)
        self.btn_remove.clicked.connect(self.remove_row)
        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)

        self.populate_table()

        # Conectar cambios
        self.table.cellChanged.connect(self.handle_cell_change)

    def populate_table(self):
        self.table.setRowCount(len(self.df_config))
        for row_idx in range(len(self.df_config)):
            month = str(self.df_config.iloc[row_idx]["Month"])
            pipe_desc = str(self.df_config.iloc[row_idx]["PipeDesc"])
            feet_val = self.df_config.iloc[row_idx]["Feet"]

            # Month combo
            combo_month = QComboBox()
            months_list = ["January","February","March","April","May","June",
                           "July","August","September","October","November","December"]
            combo_month.addItems(months_list)
            idx_m = combo_month.findText(month)
            combo_month.setCurrentIndex(max(0, idx_m))
            self.table.setCellWidget(row_idx, 0, combo_month)

            # PipeDesc combo
            combo_pipe = QComboBox()
            combo_pipe.addItem("")
            for k in self.pipe_catalog.keys():
                combo_pipe.addItem(k)
            idx_p = combo_pipe.findText(pipe_desc)
            combo_pipe.setCurrentIndex(max(0, idx_p))
            self.table.setCellWidget(row_idx, 1, combo_pipe)

            # Feet
            item_feet = QTableWidgetItem(str(feet_val))
            self.table.setItem(row_idx, 2, item_feet)

            # Total cost
            cost = self.compute_cost(pipe_desc, feet_val)
            item_total = QTableWidgetItem(f"{cost:.2f}")
            item_total.setFlags(Qt.ItemIsEnabled)  # Read-only
            self.table.setItem(row_idx, 3, item_total)
            self.table.resizeColumnsToContents()
            self.table.resizeRowsToContents()
            self.adjust_dialog_size()


    def compute_cost(self, pipe_desc, feet):
        try:
            cost_per_ft = self.pipe_catalog.get(pipe_desc, 0.0)
            return float(feet) * cost_per_ft
        except:
            return 0.0

    def update_total_cost(self, row_idx):
        try:
            pipe_widget = self.table.cellWidget(row_idx, 1)
            pipe_desc = pipe_widget.currentText()
            feet_item = self.table.item(row_idx, 2)
            feet_val = float(feet_item.text()) if feet_item else 0.0
            cost = self.compute_cost(pipe_desc, feet_val)
            item_total = QTableWidgetItem(f"{cost:.2f}")
            item_total.setFlags(Qt.ItemIsEnabled)
            self.table.setItem(row_idx, 3, item_total)
        except Exception as e:
            print(f"Error actualizando total en fila {row_idx}: {e}")

    def handle_cell_change(self, row, column):
        if column == 2:  # Feet column
            self.update_total_cost(row)

    def add_row(self):
        current_rows = self.table.rowCount()
        self.table.insertRow(current_rows)

        combo_month = QComboBox()
        months_list = ["January","February","March","April","May","June",
                       "July","August","September","October","November","December"]
        combo_month.addItems(months_list)
        self.table.setCellWidget(current_rows, 0, combo_month)

        combo_pipe = QComboBox()
        combo_pipe.addItem("")
        for k in self.pipe_catalog.keys():
            combo_pipe.addItem(k)
        self.table.setCellWidget(current_rows, 1, combo_pipe)

        item_feet = QTableWidgetItem("0")
        self.table.setItem(current_rows, 2, item_feet)

        item_total = QTableWidgetItem("0.00")
        item_total.setFlags(Qt.ItemIsEnabled)
        self.table.setItem(current_rows, 3, item_total)

    def remove_row(self):
        row = self.table.currentRow()
        if row >= 0:
            self.table.removeRow(row)

    def accept(self):
        new_data = []
        rows = self.table.rowCount()
        for r in range(rows):
            combo_m = self.table.cellWidget(r, 0)
            month_val = combo_m.currentText()
            combo_p = self.table.cellWidget(r, 1)
            pipe_val = combo_p.currentText()
            item_feet = self.table.item(r, 2)
            try:
                feet_val = float(item_feet.text())
            except:
                feet_val = 0.0

            if not month_val and not pipe_val and feet_val == 0:
                continue

            new_data.append({
                "Month": month_val,
                "PipeDesc": pipe_val,
                "Feet": feet_val
            })

        self.df_config = pd.DataFrame(new_data)
        super().accept()

    def get_updated_df(self):
        return self.df_config
    
    def adjust_dialog_size(self):
        width = self.table.verticalHeader().width()
        for col in range(self.table.columnCount()):
            width += self.table.columnWidth(col)
        width += 60  # padding

        height = self.table.horizontalHeader().height()
        for row in range(self.table.rowCount()):
            height += self.table.rowHeight(row)
        height += 150  # botones y padding

        screen = self.screen().availableGeometry()
        max_width = screen.width() * 0.9
        max_height = screen.height() * 0.9

        self.setMinimumSize(min(width, max_width), min(height, max_height))
        self.resize(min(width, max_width), min(height, max_height))

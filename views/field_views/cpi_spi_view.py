from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QMessageBox, QComboBox, QLabel
)
from PyQt5.QtCore import Qt

class CpiSpiView(QDialog):
    def __init__(self, service, available_line_titles=None, on_calculate_and_save=None):
        super().__init__()
        self.service = service
        self.available_line_titles = available_line_titles or []
        self.on_calculate_and_save = on_calculate_and_save
        self.setWindowTitle("CPI & SPI by Field Line")
        self.setMinimumWidth(700)
        self.setMinimumHeight(650)

        self.line_combo = QComboBox()
        self.table = QTableWidget()

        self.line_combo.addItems(self.available_line_titles)
        self.line_combo.currentTextChanged.connect(self.on_line_changed)

        layout = QVBoxLayout()
        combo_layout = QHBoxLayout()
        combo_layout.addWidget(QLabel("Choose your field line:"))
        combo_layout.addWidget(self.line_combo)
        combo_layout.addStretch()
        layout.addLayout(combo_layout)
        layout.addWidget(self.table)
        self.setLayout(layout)

        if self.available_line_titles:
            self.line_combo.setCurrentIndex(0)
            self.on_line_changed(self.line_combo.currentText())

    def on_line_changed(self, line_title):
        if line_title:
            if self.on_calculate_and_save:
                result = self.on_calculate_and_save(line_title)
                if isinstance(result, str):
                    QMessageBox.critical(self, "Error de Cálculo", result)
                    self.table.setRowCount(0) 
                    return
            
            self.service.set_line_title(line_title)
            df = self.service.get_dataframe()
            if df.empty:
                QMessageBox.critical(self, "Error", "No se pudieron cargar los datos para esta línea.")
                self.table.setRowCount(0) 
                return
                
            self.refresh_table()

    def refresh_table(self):
        data = self.service.get_data_as_list()
        columns = self.service.get_columns()
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        self.table.setRowCount(len(data))
        for row_index, row in enumerate(data):
            for col_index, col in enumerate(columns):
                item = QTableWidgetItem(str(row[col]))
                item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row_index, col_index, item)

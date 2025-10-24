from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QComboBox, QMessageBox, QHeaderView
)
from PyQt5.QtCore import Qt
from datetime import datetime

class ApprovedBudgetActivitiesView(QDialog):
    def __init__(self, service, available_line_titles=None):
        super().__init__()
        self.service = service
        self.available_line_titles = available_line_titles or []
        self.setWindowTitle("Budget and Approbed Activities by Field Line")
        self.setMinimumWidth(700)
        self.setMinimumHeight(500)

        self.table = QTableWidget()
        self.add_button = QPushButton("Add/Update Data")
        self.budget_input = QLineEdit()
        self.activities_input = QLineEdit()
        self.line_combo = QComboBox()
        self.line_combo.addItem("")  # Opción vacía por defecto
        self.line_combo.addItems(self.available_line_titles)
        self.year_label = QLabel(str(datetime.now().year))

        # Layout para inputs
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("Year:"))
        input_layout.addWidget(self.year_label)
        input_layout.addWidget(QLabel("Field Line:"))
        input_layout.addWidget(self.line_combo)

        # Layout para los campos de presupuesto y actividades aprobadas
        fields_layout = QHBoxLayout()
        fields_layout.addWidget(QLabel("Budget:"))
        fields_layout.addWidget(self.budget_input)
        fields_layout.addWidget(QLabel("Approved Activities:"))
        fields_layout.addWidget(self.activities_input)
        fields_layout.addWidget(self.add_button)

        layout = QVBoxLayout()
        layout.addLayout(input_layout)
        layout.addLayout(fields_layout)
        layout.addWidget(self.table)
        self.setLayout(layout)

        self.add_button.clicked.connect(self.handle_add_or_update)
        self.refresh_table()

    def refresh_table(self):
        self.service.reload()
        data = self.service.get_data_as_list()
        columns = self.service.get_columns()
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(["Year", "Budget", "Approved Activities", "Line"])
        self.table.setRowCount(len(data))
        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.Stretch)
        for row_index, row in enumerate(data):
            for col_index, col in enumerate(columns):
                item = QTableWidgetItem(str(row[col]))
                item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row_index, col_index, item)
        self.table.resizeRowsToContents()
        self.table.resizeColumnsToContents()
        header.setMinimumSectionSize(150)
        self.table.setSizeAdjustPolicy(QTableWidget.AdjustToContents)
        self.table.setMinimumWidth(600)
        self.table.setMinimumHeight(350)
        self.table.setSizePolicy(self.sizePolicy().Expanding, self.sizePolicy().Expanding)

    def handle_add_or_update(self):
        line_name = self.line_combo.currentText()
        budget = self.budget_input.text()
        approved_activities = self.activities_input.text()
        if not line_name.strip():
            QMessageBox.warning(self, "Warning", "You must select a field line before add or update.")
            return
        if not budget or not approved_activities:
            QMessageBox.warning(self, "Data requeried", "You must complete all fields before add or update.")
            return
        try:
            budget = float(budget)
            approved_activities = int(approved_activities)
        except ValueError:
            QMessageBox.warning(self, "Invalid Data", "Budget must be a number and the activities an integer.")
            return
        # Verificar si es actualización
        year = int(self.year_label.text())
        existing = self.service.dataframe
        mask = (existing["year"] == year) & (existing["line_name"] == line_name)
        if mask.any():
            reply = QMessageBox.question(
                self,
                "Updating...",
                f"Do you want to update this line: {line_name}?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return
        self.service.add_or_update_record(budget, approved_activities, line_name)
        self.refresh_table()
        self.budget_input.clear()
        self.activities_input.clear()
        QMessageBox.information(self, "Success", "Data added or updated successfully.")

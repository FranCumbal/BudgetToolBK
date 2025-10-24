from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QMessageBox, QComboBox, QLabel
)
from PyQt5.QtCore import Qt


class ManualPlanningView(QDialog):
    def __init__(self, service, approved_service, available_line_titles=None):
        super().__init__()
        self.service = service
        self.approved_service = approved_service  # Guardar referencia al servicio de aprobados
        self.available_line_titles = available_line_titles or []
        self.setWindowTitle("Manual Planning")
        self.setMinimumWidth(700)
        self.setMinimumHeight(650)

        # Widgets principales
        self.line_combo = QComboBox()
        self.table = QTableWidget()
        self.save_button = QPushButton("Save Data")
        self.total_label = QLabel()
        self.approved_label = QLabel()  # NUEVO: Label para mostrar actividades aprobadas
        self.total_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.total_label.setStyleSheet("font-weight: bold; font-size: 14px; margin: 8px;")
        self.approved_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.approved_label.setStyleSheet("font-weight: bold; font-size: 14px; margin: 8px;")
        
        # Conectar señales
        self.line_combo.currentTextChanged.connect(self.on_line_changed)
        self.save_button.clicked.connect(self.save_changes)
        self.table.itemChanged.connect(self.update_total_label)
        
        # Configurar UI
        layout = QVBoxLayout(self)
        layout.addWidget(self.line_combo)
        layout.addWidget(self.table)
        layout.addWidget(self.approved_label)  # Mostrar actividades aprobadas
        layout.addWidget(self.total_label)
        layout.addWidget(self.save_button)

        self.setup_combo()
        self.setup_table()
        self.update_total_label()

    def get_approved_activities(self, line_title):
        """Obtiene el número de actividades aprobadas para la línea y año actual"""
        from datetime import datetime
        year = datetime.now().year
        df = self.approved_service.dataframe
        filtered = df[(df['year'] == year) & (df['line_name'] == line_title)]
        if not filtered.empty:
            return int(filtered.iloc[-1]['approved_activities'])
        return None

    def setup_combo(self):
        """Configura el combobox con las líneas de campo disponibles"""
        self.line_combo.clear()
        self.line_combo.addItems(self.available_line_titles)
        
        # Si hay líneas disponibles, seleccionar la primera
        if self.available_line_titles:
            # Si el service ya tiene una línea configurada, seleccionarla
            if self.service.line_title and self.service.line_title in self.available_line_titles:
                self.line_combo.setCurrentText(self.service.line_title)
            else:
                self.line_combo.setCurrentIndex(0)
                self.on_line_changed(self.line_combo.currentText())
        self.update_total_label()  # Actualizar total al cambiar línea

    def on_line_changed(self, line_title):
        """Se ejecuta cuando se cambia la selección del combobox"""
        if line_title:
            self.service.set_line_title(line_title)
            self.setup_table()
            self.update_total_label()

    def setup_table(self):
        data = self.service.get_data_as_list()
        columns = self.service.get_columns()

        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        self.table.setRowCount(len(data))

        for row_index, row in enumerate(data):
            # Month (read-only)
            month_item = QTableWidgetItem(row["Month"])
            month_item.setFlags(month_item.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row_index, 0, month_item)

            # Planned Activities (editable)
            activity_item = QTableWidgetItem(str(row["Planned Activities"]))
            activity_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row_index, 1, activity_item)
        self.update_total_label()

    def update_total_label(self):
        """Actualiza el label con la suma total de Planned Activities en tiempo real"""
        total = 0
        for row in range(self.table.rowCount()):
            try:
                value = int(self.table.item(row, 1).text())
            except (ValueError, AttributeError):
                value = 0
            total += value
        line_title = self.line_combo.currentText()
        approved = self.get_approved_activities(line_title)
        if approved is not None:
            self.approved_label.setText(f"Approved Activities: {approved}")
            if total > approved:
                self.total_label.setStyleSheet("font-weight: bold; font-size: 14px; color: red; margin: 8px;")
            else:
                self.total_label.setStyleSheet("font-weight: bold; font-size: 14px; color: green; margin: 8px;")
        else:
            self.approved_label.setText("Actividades Aprobadas: -")
            self.total_label.setStyleSheet("font-weight: bold; font-size: 14px; margin: 8px;")
        self.total_label.setText(f"Total Planned Activities: {total}")

    def save_changes(self):
        current_line = self.line_combo.currentText()
        if not current_line:
            QMessageBox.warning(self, "No Selection", "Please select a field line first.")
            return
        total = 0
        for row in range(self.table.rowCount()):
            try:
                value = int(self.table.item(row, 1).text())
            except (ValueError, AttributeError):
                value = 0
            total += value
        approved = self.get_approved_activities(current_line)
        if approved is not None and total > approved:
            QMessageBox.warning(self, "Warning", f" The total of planned activities({total}) exceeds the approved activities({approved}).")
            return
        for row in range(self.table.rowCount()):
            month = self.table.item(row, 0).text()
            try:
                value = int(self.table.item(row, 1).text())
            except ValueError:
                QMessageBox.warning(self, "Invalid Input", f"Value in row {row + 1} must be an integer.")
                return
            self.service.update_row(month, value)
        self.service.save_to_csv()
        QMessageBox.information(self, "Success", f"Manual planning data saved successfully for {current_line}.")

    def closeEvent(self, event):
        """Sobrescribe el evento de cierre para validar antes de cerrar"""
        current_line = self.line_combo.currentText()
        if current_line:
            # Validar que todos los valores sean enteros válidos
            for row in range(self.table.rowCount()):
                try:
                    int(self.table.item(row, 1).text())
                except (ValueError, AttributeError):
                    reply = QMessageBox.question(
                        self, 
                        "Unsaved Changes", 
                        "There are invalid values in the table. Do you want to close without saving?",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No
                    )
                    if reply == QMessageBox.No:
                        event.ignore()
                        return
                    break
        
        event.accept()

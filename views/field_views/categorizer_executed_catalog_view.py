from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QComboBox, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
)
from PyQt5.QtCore import Qt
from datetime import datetime


class CategorizerExecutedCatalogView(QDialog):
    def __init__(self, service, available_line_titles=None, on_calculate_and_save=None):
        super().__init__()
        self.service = service
        self.on_calculate_and_save = on_calculate_and_save
        self.fixed_line_title = available_line_titles[0]
        self.months = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle(f"Executed Activities Catalog - {self.fixed_line_title}")
        self.setModal(True)
        self.resize(800, 600)
        
        layout = QVBoxLayout(self)
        
        # Sección de controles - Solo selector de mes
        controls_layout = QHBoxLayout()
        
        # Selector de mes
        controls_layout.addWidget(QLabel("Month:"))
        self.month_combo = QComboBox()
        self.month_combo.addItems(self.months)
        # Establecer mes actual por defecto
        current_month = datetime.now().strftime("%B").lower()
        if current_month in self.months:
            self.month_combo.setCurrentText(current_month)
        controls_layout.addWidget(self.month_combo)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
          # Tabla para mostrar los datos
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Mes", "Año", "Pozo", "Costo por Actividad", "Categoría"])
        
        # Configurar tabla para que se ajuste al contenido
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        # Permitir que la última columna se estire si hay espacio extra
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        
        layout.addWidget(self.table)
        
        # Botón cerrar
        close_layout = QHBoxLayout()
        close_layout.addStretch()
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        close_layout.addWidget(close_button)
        layout.addLayout(close_layout)
        
        # Conectar cambio de mes para calcular automáticamente
        self.month_combo.currentTextChanged.connect(self.on_month_changed)
          # Cargar datos iniciales
        self.on_month_changed(self.month_combo.currentText())

    def on_month_changed(self, month):
        """Se ejecuta automáticamente cuando cambia el mes"""
        if not month:
            self.table.setRowCount(0)
            return
        
        try:
            # Primero, calcular y guardar nuevos datos
            if self.on_calculate_and_save:
                self.on_calculate_and_save(self.fixed_line_title, month)
            
            # Luego, cargar y mostrar los datos
            df = self.service.get_records_by_month_and_line(month, self.fixed_line_title)
            self.show_dataframe_in_table(df)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al procesar datos: {str(e)}")
            print(f"Error al procesar datos: {str(e)}")
            self.table.setRowCount(0)

    def show_dataframe_in_table(self, df):
        """Muestra un DataFrame en la tabla"""
        if df.empty:
            self.table.setRowCount(0)
            return
        
        # Calcular totales por categoría
        category_counts = df['Category'].value_counts().sort_index()
        
        # Establecer filas: datos + 1 fila de resumen
        self.table.setRowCount(len(df) + 1)
        
        # Mostrar datos normales
        for row_idx, (_, row) in enumerate(df.iterrows()):
            for col_idx, col_name in enumerate(["month", "year", "Well", "Cost by Activity", "Category"]):
                value = str(row.get(col_name, ""))
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # Solo lectura
                self.table.setItem(row_idx, col_idx, item)
        
        # Agregar fila de resumen
        summary_row_idx = len(df)
        
        # Columna "Mes" - mostrar "RESUMEN"
        summary_item = QTableWidgetItem("Summary")
        summary_item.setFlags(summary_item.flags() & ~Qt.ItemIsEditable)
        from PyQt5.QtGui import QFont, QColor
        font = QFont()
        font.setBold(True)
        summary_item.setFont(font)
        summary_item.setBackground(QColor(220, 220, 220))  # Fondo gris claro
        self.table.setItem(summary_row_idx, 0, summary_item)
        
        # Columna "Año" - mostrar totales por categoría
        totals_text = []
        for category in [1, 2, 3, 4]:
            count = category_counts.get(category, 0)
            if count > 0:
                totals_text.append(f"Cat.{category} -> {count}")
        
        totals_summary = " | ".join(totals_text) if totals_text else "Empty Data"
        totals_item = QTableWidgetItem(totals_summary)
        totals_item.setFlags(totals_item.flags() & ~Qt.ItemIsEditable)
        totals_item.setFont(font)
        totals_item.setBackground(QColor(220, 220, 220))
        self.table.setItem(summary_row_idx, 1, totals_item)
          # Columnas restantes - vacías pero con el mismo formato
        for col_idx in range(2, 5):
            empty_item = QTableWidgetItem("")
            empty_item.setFlags(empty_item.flags() & ~Qt.ItemIsEditable)
            empty_item.setBackground(QColor(220, 220, 220))
            self.table.setItem(summary_row_idx, col_idx, empty_item)
        
        # Ajustar el ancho de las columnas para que se vea todo el contenido
        self.table.resizeColumnsToContents()
        # Asegurar que la columna de resumen tenga espacio suficiente
        self.table.setColumnWidth(1, max(200, self.table.columnWidth(1)))

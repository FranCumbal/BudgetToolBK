from PyQt5.QtWidgets import QLabel, QComboBox, QHBoxLayout, QMessageBox, QCheckBox
from PyQt5.QtCore import Qt

from services.field_lines_services.quote_extractor_service import SouthZoneQuoteExtractorService
from views.field_views.quote_extractor_view import QuoteExtractorView


class SouthZoneQuoteExtractorView(QuoteExtractorView):
    """Vista para la zona sur que hereda toda la funcionalidad de QuoteExtractorView"""
    
    def __init__(self, available_line_titles):
        self.available_line_titles = available_line_titles
        self.current_line = None
        self.init_base_without_service()

        if self.available_line_titles:
            self.current_line = self.available_line_titles[0]
            self.service = SouthZoneQuoteExtractorService(self.current_line)
            self.columnas = self.service.get_columns()
        self.completed_checkbox = QCheckBox("Completed")
        self.init_ui()
    
    def init_base_without_service(self):
        """Inicializa los atributos básicos sin crear el servicio"""
        super(QuoteExtractorView, self).__init__()  # Solo inicializa QDialog
        self.setWindowTitle("CTU - Scheduled Activities Path")
        self.setGeometry(200, 200, 1200, 700)
    
    def init_ui(self):
        """Sobrescribe init_ui para agregar el selector de línea"""
        layout = self.create_base_layout()
        
        # Agregar selector de línea al inicio
        line_selector_layout = QHBoxLayout()
        line_selector_label = QLabel("Select Line:")
        self.line_selector = QComboBox()
        self.line_selector.addItems(self.available_line_titles)
        self.line_selector.setCurrentText(self.current_line or "")
        self.line_selector.currentTextChanged.connect(self.on_line_changed)
        
        line_selector_layout.addWidget(line_selector_label)
        line_selector_layout.addWidget(self.line_selector)
        line_selector_layout.addStretch()
        
        # Insertar el selector al inicio del layout
        main_layout = self.layout()
        if main_layout:
            main_layout.insertLayout(0, line_selector_layout)
        else:
            # Si no hay layout previo, crear uno nuevo
            from PyQt5.QtWidgets import QVBoxLayout
            new_layout = QVBoxLayout()
            new_layout.addLayout(line_selector_layout)
            new_layout.addLayout(layout)
            self.setLayout(new_layout)
    
    def create_base_layout(self):
        """Crea el layout base usando la lógica de la clase padre"""
        # Llamar al init_ui original pero devolver el layout en lugar de asignarlo
        super().init_ui()
        return self.layout()
    
    def on_line_changed(self):
        """Cambia el servicio y recarga datos cuando se cambia la línea"""
        selected_line = self.line_selector.currentText()
        if not selected_line or selected_line == self.current_line:
            return
            
        self.current_line = selected_line
        
        # Crear nuevo servicio para la línea seleccionada
        self.service = SouthZoneQuoteExtractorService(selected_line)
        self.columnas = self.service.get_columns()
        
        # Limpiar y reconfigurar tabla
        self.tabla.setRowCount(0)
        self.tabla.setColumnCount(len(self.columnas))
        self.tabla.setHorizontalHeaderLabels(self.columnas)
        
        # Reconfigurar header
        from PyQt5.QtWidgets import QHeaderView
        header = self.tabla.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setSectionResizeMode(self.tabla.columnCount() - 1, QHeaderView.Stretch)
        
        # Cargar datos de la línea seleccionada
        self.load_data_from_csv()
    
    def load_pdfs(self):
        """Sobrescribe load_pdfs para agregar validación de línea seleccionada"""
        if not self.service or not self.current_line:
            QMessageBox.warning(self, "No Line Selected", "Please select a line first.")
            return
        
        # Llamar al método original de la clase padre
        super().load_pdfs()
    
    def save_csv(self):
        """Sobrescribe save_csv para mostrar el nombre de la línea en el mensaje"""
        if not self.service or not self.current_line:
            QMessageBox.warning(self, "No Line Selected", "Please select a line first.")
            return
        
        # Usar la lógica original pero personalizar el mensaje de éxito
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
                    registro[campo] = item.text() if item else None

            # Verificar si algún valor en el registro es None
            if any(valor is None or valor == "" for valor in registro.values()):
                QMessageBox.critical(
                    self,
                    "Error while saving",
                    f"Unable to save due to empty or 'None' fields in row {fila + 1}. Please, check the data."
                )
                return

            registros.append(registro)

        try:
            from datetime import datetime
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
            QMessageBox.information(self, "Saved", f"Path for {self.current_line} saved successfully.")
        except PermissionError:
            QMessageBox.critical(self, "Access Error", "You must close any quotation file before do any action.")
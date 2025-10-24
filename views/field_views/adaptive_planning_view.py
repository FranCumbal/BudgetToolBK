from calendar import month_name
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QPushButton, QMessageBox, QComboBox, QLabel, QCheckBox, QHBoxLayout)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor
from datetime import datetime
from utils.file_loader import load_field_reports_from_json
from views.field_views.planning_table_widget import PlanningTableWidget
from views.field_views.total_widget import TotalsWidget

class AdaptivePlanningView(QDialog):
    save_requested = pyqtSignal()
    line_changed = pyqtSignal(str) # Para notificar cuando cambia la línea
    item_edited = pyqtSignal(int, str, str) # row_index, column_name, new_value
    calculation_requested = pyqtSignal()
    completion_status_changed = pyqtSignal(bool)
    
    def __init__(self, approved_service, available_line_titles=None, field_line_reports=None):
        super().__init__()
        self.service = None 
        self.approved_service = approved_service
        self.available_line_titles = available_line_titles or []
        self.field_line_reports = field_line_reports or []
        self.current_month_index = datetime.now().month - 1
        self.field_report = self.field_line_reports[0] if self.field_line_reports else None
        self.setWindowTitle("Field Activity Planning")
        self.setMinimumWidth(900)
        self.line_combo = QComboBox()
        self.save_button = QPushButton("Save changes")
        self.calculate_button = QPushButton("Calculate automatically")
        self.completed_checkbox = QCheckBox("Completed")
        self.info_label = QLabel()
        self.cpae_label = QLabel()
        self.category_values_label = QLabel()
        self.totals_widget = TotalsWidget()
        self.table_widget = PlanningTableWidget()
        self.month_map = {name.lower(): i for i, name in enumerate(month_name[1:])}
        self.month_map_reverse = {i: name for i, name in enumerate(month_name[1:])}
        self._setup_ui() # Cambié el nombre de _setup_labels a _setup_ui para mayor claridad
        self._connect_signals()
        self._setup_combo()

    def _setup_ui(self):
        """
        Configura los estilos de las etiquetas y CONSTRUYE el layout de la ventana.
        """
        # --- Configuración de estilos (sin cambios) ---
        self.cpae_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cpae_label.setStyleSheet("font-weight: bold; font-size: 12px; margin: 8px; background-color: #f0f0f0; padding: 5px; border: 1px solid #ccc;")
        
        self.info_label.setStyleSheet("font-size: 12px; color: #666; margin: 8px;")
        
        self.category_values_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.category_values_label.setStyleSheet("font-size: 12px; color: #333; margin: 8px; background-color: #f9f9f9; padding: 5px; border: 1px solid #eee;")
        
        self.line_combo.setStyleSheet("QComboBox { font-size: 14px; padding: 5px; }")
        self.calculate_button.setMinimumHeight(40) # Establece una altura mínima de 40 píxeles
        # --- Layout principal (Vertical) ---
        layout = QVBoxLayout(self)
        layout.addWidget(self.line_combo)
        layout.addWidget(self.info_label)
        layout.addWidget(self.cpae_label)
        layout.addWidget(self.category_values_label)
        layout.addWidget(self.table_widget)
        layout.addWidget(self.totals_widget)
        layout.addWidget(self.save_button)

        bottom_actions_layout = QHBoxLayout()
        bottom_actions_layout.addWidget(self.calculate_button)
        bottom_actions_layout.addStretch() 
        bottom_actions_layout.addWidget(self.completed_checkbox)
        
        layout.addLayout(bottom_actions_layout)

    def _connect_signals(self):
        """Conecta las señales de los widgets a los manejadores de esta clase."""
        self.line_combo.currentTextChanged.connect(self.on_line_changed)
        self.table_widget.item_edited.connect(self.on_item_changed)
        self.save_button.clicked.connect(self.save_changes)
        self.calculate_button.clicked.connect(self.on_calculate_button_clicked)
        self.completed_checkbox.stateChanged.connect(self.on_completion_changed)

    
    def on_calculate_button_clicked(self):
        """Notifica al controlador que se solicitó un cálculo automático."""
        self.calculation_requested.emit()
    
    def on_completion_changed(self, state):
        self.completion_status_changed.emit(state == Qt.Checked)
    
    def set_completion_status(self, is_completed: bool):
        self.completed_checkbox.blockSignals(True)
        self.completed_checkbox.setChecked(is_completed)
        self.completed_checkbox.blockSignals(False)

    def update_info_labels(self, info_text, category_text, are_categories_visible):
        """Actualiza las etiquetas de información y categorías."""
        self.info_label.setText(info_text)
        self.category_values_label.setText(category_text)
        self.category_values_label.setTextFormat(Qt.TextFormat.RichText)
        self.category_values_label.setVisible(are_categories_visible)

    def on_item_changed(self, row, col, text):
        """Obtiene el nombre de la columna y emite la señal item_edited."""
        # Obtenemos el nombre de la columna a partir de su índice
        column_name = self.table_widget.table.horizontalHeaderItem(col).text()
        self.item_edited.emit(row, column_name, text)
    
    def _setup_combo(self):
        """Configura el combobox con las líneas disponibles."""
        self.line_combo.blockSignals(True)
        self.line_combo.clear()
        self.line_combo.addItems(self.available_line_titles)
        self.line_combo.blockSignals(False)

    def on_line_changed(self, line_title):
        """Notifica al controlador que la línea ha cambiado."""
        for report in self.field_line_reports:
            if hasattr(report, 'title') and report.title == line_title:
                self.field_report = report
                break
        self.line_changed.emit(line_title)

    def _setup_table(self):
        """
        Este método ahora solo dispara la carga inicial de datos
        a través del método on_line_changed, que notificará al controlador.
        """
        self.on_line_changed(self.line_combo.currentText())

    def update_calculations(self):
        """Este método ahora es solo un alias para notificar un cambio de datos."""
        self.data_changed.emit()
    def update_totals(self, totals_data: dict):
        """Pasa los datos de totales al widget de totales."""
        self.totals_widget.update_data(totals_data)

    def update_cpae_label(self, title, cpae_value, budget_value):
        """Actualiza la etiqueta CPAE con datos recibidos del controlador."""
        cpae_text = f"<span style='color:darkblue;'>CPAE Value: ${cpae_value:,.2f}</span>"
        budget_text = f"<span style='color:#008FF6;'>Approved Budget: ${budget_value:,.2f}</span>"
        self.cpae_label.setText(f"<b>{title}</b><br>{cpae_text} | {budget_text}")
        self.cpae_label.setTextFormat(Qt.TextFormat.RichText)

    def update_table(self, table_data: dict):
        """Pasa los datos de la tabla al widget de la tabla."""
        self.table_widget.update_view(table_data)

    def save_changes(self):
        """Notifica al controlador que se ha solicitado guardar los cambios."""
        self.save_requested.emit()
    
    def closeEvent(self, event):
        """Maneja el evento de cierre"""
        event.accept() 

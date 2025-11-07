import sys
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QScrollArea, QAction, QMenu, QMenuBar,
    QDialog, QTableWidget, QTableWidgetItem,
    QFileDialog, QMessageBox, QTableWidget, QAbstractScrollArea, QGroupBox
)
from PyQt5.QtCore import Qt
from views.catalog_viewer import CatalogViewerDialog

class MainWindow(QMainWindow):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.comments_by_title = {}  # Para guardar comentarios por título

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Pronóstico de Presupuesto")
        screen = self.screen().availableGeometry()
        self.resize(int(screen.width() * 0.5), int(screen.height() * 0.5))

        self.setup_menu()

        central_widget = QWidget()
        central_layout = QVBoxLayout(central_widget)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        scroll_area.setWidget(self.scroll_widget)
        central_layout.addWidget(scroll_area)

        # Área de botones agrupada
        button_group = QGroupBox("Acciones disponibles")
        button_layout = QHBoxLayout()

        # --- Botón Generar Reportes (Oficina) ---
        generate_button = QPushButton("Generar reportes")
        generate_button.setMinimumHeight(40)
        generate_button.clicked.connect(self.on_generate_reports_clicked) # Conexión NUEVA
        button_layout.addWidget(generate_button)

        # --- Botón Generar Reportes de Campo ---
        generate_field_button = QPushButton("Generate Field Reports")
        generate_field_button.setMinimumHeight(40)
        generate_field_button.clicked.connect(self.on_generate_field_reports_clicked) # Conexión NUEVA
        button_layout.addWidget(generate_field_button)

        # --- Botón Generar Reporte Líder de Línea ---
        generate_lead_field_button = QPushButton("Generate Lead Field Report")
        generate_lead_field_button.setMinimumHeight(40)
        generate_lead_field_button.clicked.connect(self.on_generate_leader_line_report_clicked) # Conexión NUEVA
        button_layout.addWidget(generate_lead_field_button)

        # --- Otros botones (conexiones originales) ---
        open_table_button = QPushButton("Abrir tabla de capacidad operativa")
        open_table_button.setMinimumHeight(40)
        open_table_button.clicked.connect(self.controller.open_table_popup)
        button_layout.addWidget(open_table_button)

        update_capex_button = QPushButton("Actualizar CAPEX desde CDF")
        update_capex_button.setMinimumHeight(40)
        update_capex_button.clicked.connect(self.controller.update_capex_from_cdf)
        button_layout.addWidget(update_capex_button)

        export_all_button = QPushButton("Exportar todos los slides")
        export_all_button.setMinimumHeight(40)
        export_all_button.clicked.connect(self.controller.generate_all_slides)
        button_layout.addWidget(export_all_button)

        button_layout.addStretch()

        button_group.setLayout(button_layout)
        self.scroll_layout.addWidget(button_group)

        self.plot_frame = QWidget()
        self.plot_layout = QVBoxLayout(self.plot_frame)
        self.plot_layout.setContentsMargins(10, 10, 10, 10)
        self.plot_layout.setSpacing(10)
        # 🔽 Ocultar inicialmente
        self.plot_frame.setVisible(False)
        self.scroll_layout.addWidget(self.plot_frame)

        self.setCentralWidget(central_widget)

    def setup_menu(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("Archivo")
        exit_action = QAction("Salir", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        tools_menu = menubar.addMenu("Herramientas")

        open_table_action = QAction("Abrir tabla de capacidad operativa", self)
        open_table_action.triggered.connect(self.controller.open_table_popup)
        tools_menu.addAction(open_table_action)

        # --- SE AÑADE LA OPCION DE ACCEDER A LOS 2 NUEVOS CATALOGOS ---
        mi_swaco_config_action = QAction("Line 1.02 - Configurar MI Swaco", self)
        mi_swaco_config_action.triggered.connect(self.controller.open_mi_swaco_config)
        tools_menu.addAction(mi_swaco_config_action)

        completions_config_action = QAction("Line 1.03 - Configurar Completions", self)
        completions_config_action.triggered.connect(self.controller.open_completions_config)
        tools_menu.addAction(completions_config_action)

        tubulars_config_action = QAction("Line 1.09 - Configurar Tuberías", self)
        tubulars_config_action.triggered.connect(self.controller.open_tubulars_config)
        tools_menu.addAction(tubulars_config_action)

        services_tools = QMenu("Line 1.10. - Services Tools", self)
        tools_menu.addMenu(services_tools)
        
        well_selector_action = QAction("Seleccionar pozos", self)
        well_selector_action.triggered.connect(self.controller.open_well_selector_dialog)
        services_tools.addAction(well_selector_action)
        
        services_summary_action = QAction("Abrir resumen de Services", self)
        services_summary_action.triggered.connect(self.controller.open_services_summary)
        services_tools.addAction(services_summary_action)

        services_forecast_path = QAction("Abrir ruta para forecast", self)
        services_forecast_path.triggered.connect(self.controller.open_services_forecast_path)
        services_tools.addAction(services_forecast_path)

        wireline_tanks_testing_tools = QMenu("Planificación Wireline, Tanks y Testing", self)
        tools_menu.addMenu(wireline_tanks_testing_tools)

        wireline_activities_plan = QAction("Ajustar Planificación", self)
        wireline_activities_plan.triggered.connect(self.controller.open_office_activities_plan)
        wireline_tanks_testing_tools.addAction(wireline_activities_plan)

        avg_days_action = QAction("Colocar dias promedio", self)
        avg_days_action.triggered.connect(self.controller.open_avg_days_dialog)
        tools_menu.addAction(avg_days_action)

        catalog_action = QAction("Editar catálogos", self)
        catalog_action.triggered.connect(self.open_catalog_viewer)
        tools_menu.addAction(catalog_action)

        opex_action = QAction("Editar presupuesto OPEX", self)
        opex_action.triggered.connect(self.controller.show_opex_editor)
        tools_menu.addAction(opex_action)

        plan_action = QAction("Visualizar plan de actividades", self)
        plan_action.triggered.connect(self.controller.open_activity_plan_viewer)
        tools_menu.addAction(plan_action)

        forecast_plan_action = QAction("Editar plan de actividades forecasteadas", self)
        forecast_plan_action.triggered.connect(self.controller.open_forecasted_activity_plan_editor)
        tools_menu.addAction(forecast_plan_action)

        # Nuevo menú Herramientas - Campo
        field_tools_menu = menubar.addMenu("Field Tools")

        initial_activities_plan = QAction("Field - Field Activity Planning", self)
        initial_activities_plan.triggered.connect(self.controller.open_initial_activities_plan)
        field_tools_menu.addAction(initial_activities_plan)

        approved_budget_and_activities = QAction("Field - Budget and Approved Activities", self)
        approved_budget_and_activities.triggered.connect(self.controller.open_approved_budget_and_activities)
        field_tools_menu.addAction(approved_budget_and_activities)

        south_zone_tools = QMenu("Field - CTU Tools", self)
        field_tools_menu.addMenu(south_zone_tools)

        south_zone_forecast_path_action = QAction("CTU - Scheduled Activities Path", self) 
        south_zone_forecast_path_action.triggered.connect(self.controller.open_south_zone_quote_extractor_view)
        south_zone_tools.addAction(south_zone_forecast_path_action)

        varillera_tools_submenu = QMenu("Field - Varillera Tools", self)
        field_tools_menu.addMenu(varillera_tools_submenu)

        load_pdf_action = QAction("Varillera - Scheduled Activities Path", self) 
        load_pdf_action.triggered.connect(self.controller.open_quote_extractor_view)
        varillera_tools_submenu.addAction(load_pdf_action)

        #categorizer_activities_catalog_varillera_action = QAction("Varillera - Categorized Activites Catalog", self)
        #categorizer_activities_catalog_varillera_action.triggered.connect(self.controller.open_categorizer_planned_activities_catalog_varillera)
        #varillera_tools_submenu.addAction(categorizer_activities_catalog_varillera_action)

        initial_cost_action = QAction("Varillera - Register Initial Approved Cost", self)
        initial_cost_action.triggered.connect(self.controller.open_historical_initial_cost_view)
        varillera_tools_submenu.addAction(initial_cost_action)

        total_executed_activities = QAction("Varillera - Executed Activities Detail", self)
        total_executed_activities.triggered.connect(
            lambda: self.controller.open_total_executed_activities_view("ITEM 104 Varillera")
            )
        varillera_tools_submenu.addAction(total_executed_activities)

        catalogo_actividades_submenu = QMenu("Field - Categorized Activities", self)
        field_tools_menu.addMenu(catalogo_actividades_submenu)
        # Slickline
        categorizer_slickline_action = QAction("Slickline - Categorized Activities Catalog", self)
        categorizer_slickline_action.triggered.connect(
            lambda: self.controller.open_categorizer_executed_activities_catalog("ITEM 49 Slick Line")
        )
        catalogo_actividades_submenu.addAction(categorizer_slickline_action)

        # Bacheo Anular
        categorizer_bacheo_action = QAction("Bacheo Anular - Categorized Activities Catalog", self)
        categorizer_bacheo_action.triggered.connect(
            lambda: self.controller.open_categorizer_executed_activities_catalog("ITEM 65 Bacheo Anular")
        )
        catalogo_actividades_submenu.addAction(categorizer_bacheo_action)

        cpi_and_spi_action = QAction("Field - CPI and SPI by line", self)
        cpi_and_spi_action.triggered.connect(self.controller.open_cpi_spi_by_line)
        field_tools_menu.addAction(cpi_and_spi_action)

        lead_summary_report_action = QAction("Field - Leader Line Summary Report", self)
        lead_summary_report_action.triggered.connect(self.controller.open_leader_summary_report)
        field_tools_menu.addAction(lead_summary_report_action)

    def show_plot_view(self, graph, deviations, title="Plot View", deviation_type="default"):
        from views.plot_view import PlotView
        container = QWidget()
        layout = QVBoxLayout(container)
        plot_view = PlotView(container, graph, deviations, self.controller,
                             title=title, deviation_type=deviation_type)
        layout.addWidget(plot_view)
        # 👇 Mostrar el plot_frame si está oculto
        self.plot_frame.setVisible(True)
        self.plot_layout.addWidget(container)
        plot_view.comments_edit.textChanged.connect(
            lambda: self.comments_by_title.update({title: plot_view.comments_edit.toPlainText()})
        )

    def get_comments_for_title(self, title):
        return self.comments_by_title.get(title, "")

    def show_table(self, data):
        table_dialog = TableDialog(data, self.controller, self)
        table_dialog.exec_()

    def open_catalog_viewer(self):
        catalog_dialog = CatalogViewerDialog(self)
        catalog_dialog.exec_()

    def on_generate_reports_clicked(self):
        """Limpia la UI y luego genera los reportes de oficina."""
        print("Limpiando gráficos anteriores (Oficina)...")
        self.clear_layout(self.plot_layout)
        self.plot_frame.setVisible(False)
        self.comments_by_title.clear()
        self.controller.generate_reports()

    def on_generate_field_reports_clicked(self):
        """Limpia la UI y luego genera los reportes de campo."""
        print("Limpiando gráficos anteriores (Campo)...")
        self.clear_layout(self.plot_layout)
        self.plot_frame.setVisible(False)
        self.comments_by_title.clear()
        self.controller.generate_field_reports()

    def on_generate_leader_line_report_clicked(self):
        """Limpia la UI y luego genera el reporte de líder de línea."""
        print("Limpiando gráficos anteriores (Líder)...")
        self.clear_layout(self.plot_layout)
        self.plot_frame.setVisible(False)
        self.comments_by_title.clear()
        self.controller.generate_leader_line_report()

    def clear_layout(self, layout):
        """
        Limpia un layout (QLayout) de todos sus widgets, 
        eliminándolos de forma segura.
        """
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    # Elimina el widget de forma segura
                    widget.deleteLater()
                else:
                    # Maneja el caso de que sea un layout anidado
                    nested_layout = item.layout()
                    if nested_layout is not None:
                        self.clear_layout(nested_layout)

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton,
    QFileDialog, QMessageBox, QAbstractScrollArea
)

class TableDialog(QDialog):
    def __init__(self, data, controller, parent=None):
        super().__init__(parent)
        self.data = data
        self.controller = controller
        self.total_row_idx = len(self.data)
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Tabla de Capacidad Operativa")
        layout = QVBoxLayout(self)

        if not self.data.empty:
            self.col_names = list(self.data.columns)
        else:
            self.col_names = []

        self.table_widget = QTableWidget(len(self.data) + 1, len(self.col_names))
        self.table_widget.setHorizontalHeaderLabels(self.col_names)
        self.table_widget.setAlternatingRowColors(True)
        self.table_widget.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)

        # Mostrar datos y definir celdas editables
        for row_idx, row_data in self.data.iterrows():
            for col_idx, col_name in enumerate(self.col_names):
                item_value = str(row_data[col_name])
                item = QTableWidgetItem(item_value)

                # Entradas manuales (resaltadas)
                if col_name in ["Taladros", "Días CAPEX", "Días Certificación", "Días OPEX 4to Rig", "Días CAPEX 4to Rig"]:
                    item.setFlags(item.flags() | Qt.ItemIsEditable)
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    item.setBackground(QColor(218, 232, 252))  # Azul claro
                # Calculadas (sombreado gris)
                else:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    item.setTextAlignment(Qt.AlignCenter)
                    item.setBackground(QColor(245, 245, 245))  # Gris suave


                self.table_widget.setItem(row_idx, col_idx, item)

        # Fila de totales
        self.insert_total_row()

        # Conexión al cambio de valores
        self.table_widget.itemChanged.connect(self.handle_item_changed)

        self.table_widget.resizeColumnsToContents()
        self.table_widget.resizeRowsToContents()
        layout.addWidget(self.table_widget)

        # Botón para exportar como copia
        save_button = QPushButton("Guardar como archivo nuevo...")
        save_button.clicked.connect(self.save_to_excel_as)
        layout.addWidget(save_button)

        self.setMinimumSize(800, 400)
        self.setMaximumSize(1600, 800)
        self.setLayout(layout)
        self.adjustSize()

    def insert_total_row(self):
        """
        Inserta la última fila como totales.
        """
        totales = self.data.sum(numeric_only=True)
        for col_idx, col_name in enumerate(self.col_names):
            if col_name in [
                "Días Operativos",
                "Total Días OPEX",
                "Numero tentativo de pozos OPEX",
                "Días OPEX 4to Rig",
                "Días CAPEX 4to Rig"
            ]:
                total_value = f"{totales.get(col_name, 0):.0f}"
            elif col_name == "Mes":
                total_value = "Totales"
            else:
                total_value = ""

            item = QTableWidgetItem(total_value)
            item.setFlags(Qt.ItemIsEnabled)
            item.setTextAlignment(Qt.AlignCenter)

            # Estilo visual
            font = QFont()
            font.setBold(True)
            item.setFont(font)
            item.setBackground(QColor(220, 220, 220))  # Gris claro

            self.table_widget.setItem(self.total_row_idx, col_idx, item)

    def handle_item_changed(self, item):
        row = item.row()
        col = item.column()

        # Evitar edición en la fila de totales
        if row == self.total_row_idx:
            return

        col_name = self.col_names[col]
        value = item.text()

        try:
            value_float = float(value)
        except ValueError:
            QMessageBox.warning(self, "Valor inválido", f"El valor '{value}' no es válido para la columna '{col_name}'.")
            return

        self.controller.update_capacity_value(row, col_name, value_float)
        self.controller.save_operative_capacity()
        self.data = self.controller.capacity_manager.df
        self.refresh_table()
        QMessageBox.information(self, "Guardado automático", "✅ Los cambios se guardaron en el archivo original.")

    def refresh_table(self):
        """
        Refresca toda la tabla visual con el nuevo DataFrame y la fila de totales.
        """
        self.table_widget.blockSignals(True)
        self.col_names = list(self.data.columns)

        # Recargar valores del DataFrame
        for row_idx, row_data in self.data.iterrows():
            for col_idx, col_name in enumerate(self.col_names):
                item = self.table_widget.item(row_idx, col_idx)
                new_value = str(row_data[col_name])
                if item is not None:
                    item.setText(new_value)

        # Actualizar fila de totales
        self.insert_total_row()

        self.table_widget.blockSignals(False)

    def save_to_excel_as(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar tabla como...",
            "",
            "Excel Files (*.xlsx)"
        )
        if file_path:
            self.controller.save_table_data_to_excel(file_path)
            QMessageBox.information(self, "Guardado", f"Tabla guardada en:\n{file_path}")

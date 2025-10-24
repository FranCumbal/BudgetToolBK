from calendar import month_name
from datetime import datetime
import getpass
import inspect
from PyQt5.QtCore import QObject, Qt
from PyQt5.QtWidgets import QMessageBox
import pandas as pd
from controllers.field_planning_controller import FieldPlanningController
from services.field_lines_services.approved_budget_activities_service import ApprovedBudgetActivitiesService
from services.field_lines_services.categorizer_executed_catalog_service import CategorizerExecutedCatalogService
from services.field_lines_services.completion_status_service import CompletionStatusService
from services.field_lines_services.cpi_spi_service import CpiSpiService
from services.field_lines_services.executed_activities_detail_service import ExecutedActivitiesDetailService
from services.field_lines_services.leader_line_service import LeaderLineService
from services.field_lines_services.planned_activities_catalog_service import PlannedActivitiesCatalogService
from logic.field_lines.reports.echometer_report import EchometerReport
from logic.field_lines.reports.field_lead_line_report import FieldLeadLineReport
from logic.field_lines.reports.field_report import FieldReport
from logic.field_lines.reports.slick_and_bacheo_report import SlickAndBacheoReport
from logic.field_lines.reports.varillera_report import VarilleraReport
from utils.comments import load_field_line_comments, save_field_line_comment
from utils.file_loader import load_field_reports_from_json
from utils.file_manager import get_planned_activities_catalog_path
from views.field_views.approved_budget_activities_view import ApprovedBudgetActivitiesView
from views.field_views.categorizer_executed_catalog_view import CategorizerExecutedCatalogView
from views.field_views.cpi_spi_view import CpiSpiView
from views.field_views.executed_activities_detail_view import ExecutedActivitiesDetailView
from views.field_views.historical_initial_cost_view import HistoricalInitialCostView
from views.field_views.quote_extractor_view import QuoteExtractorView
from views.field_views.south_zone_quote_extractor_view import SouthZoneQuoteExtractorView
from views.field_views.leader_summary_report_view import LeaderSummaryReportView

class FieldController(QObject):
    FIELD_REPORT_CLASSES = { 
        "VarilleraReport": VarilleraReport,
        "SlickAndBacheoReport": SlickAndBacheoReport,
        "EchometerReport": EchometerReport,
        "default": FieldReport
    }

    def __init__(self, parent_view=None):
        super().__init__()
        self.parent_view = parent_view
        self.approved_service = ApprovedBudgetActivitiesService()
        self.field_comments_df = load_field_line_comments() 
        self.categorizer_activities_catalog_path_varillera = get_planned_activities_catalog_path()
        self.field_line_report_instances = []
        self.year = 0
        self.load_field_instances()
        self.summary_report_cache = None
        self.month_map = {name.lower(): i for i, name in enumerate(month_name[1:])}
        self.set_year()
        self.completion_service = CompletionStatusService()

    def load_field_instances(self):
        configs = load_field_reports_from_json()
        for cfg in configs:
            class_name = cfg.get("class", "default")
            if class_name == "FieldLeadLineReport": # No es un FieldReport comun, por eso lo paso
                continue
            report_class = self.FIELD_REPORT_CLASSES.get(class_name, FieldReport)
            valid_params = inspect.signature(report_class.__init__).parameters
            kwargs = {k: v for k, v in cfg.items() if k in valid_params and k != 'self'}
            try:
                instance = report_class(**kwargs)
                self.field_line_report_instances.append(instance)
            except Exception as e:
                print(f"Error instanciando {class_name} con {kwargs}: {e}")

    def set_year(self):
        if datetime.now().month == 1:
            self.year = datetime.now().year - 1
        else: 
            self.year = datetime.now().year 

    def is_field_report(self, title_to_check: str) -> bool:
        """
        Verifica si un título corresponde a CUALQUIER tipo de reporte de campo,
        ya sea una línea individual o un reporte consolidado.
        """
        configs = load_field_reports_from_json()
        for config in configs:
            if config.get("title") == title_to_check and config.get("line_type") == "field":
                return True
        return False
    
    def get_comments_for_title(self, title):
        """Obtiene los comentarios específicos para una línea de campo."""
        mes_actual = datetime.now().strftime("%Y-%m")
        df = self.field_comments_df
        
        if df is None or df.empty:
            return ""
        comentarios = df[(df["Report Title"] == title) & (df["Mes"] == mes_actual)]
        if comentarios.empty:
            return ""
            
        return "\n".join(f" {row['Comentario']}" for _, row in comentarios.iterrows())
    
    def save_new_comment(self, title, comentario):
        """Guarda un comentario para una línea de campo."""
        now = datetime.now()
        mes_actual = now.strftime("%Y-%m")
        nuevo = pd.DataFrame([{
            "Report Title": title,
            "Mes": mes_actual,
            "Fecha": now.strftime("%Y-%m-%d %H:%M:%S"),
            "Usuario": getpass.getuser(),
            "Comentario": comentario
        }])

        df = self.field_comments_df
        if df is not None and not df.empty:
            df = df[~((df["Report Title"] == title) & (df["Mes"] == mes_actual))]
            self.field_comments_df = pd.concat([df, nuevo], ignore_index=True)
        else:
            self.field_comments_df = nuevo
        
        save_field_line_comment(self.field_comments_df)

    def generate_field_reports(self):
        for field_report_instance in self.field_line_report_instances:
            try:
                graph = field_report_instance.generate_graph()
                deviations = field_report_instance.generate_deviations()
                self.parent_view.show_plot_view(
                    graph,
                    deviations,
                    title=field_report_instance.title,
                    deviation_type="default"
                )
            except PermissionError:
                QMessageBox.critical(
                    self.parent_view, 
                    "File Access Error", 
                    "The cost source file is currently open and cannot be read.\n\nPlease close the 'Control de costos.xlsx' file and try again."
                )
                return None, None, "default"
            except FileNotFoundError as e:
                QMessageBox.warning(
                    self.parent_view,
                    "File Not Found",
                    "You must create the file first." + str(e)
                )
    
    def _create_leader_line_report_object(self):
        """
        Método ayudante que centraliza la creación del DataFrame agregado
        y el objeto FieldLeadLineReport.
        """
        leader_service = LeaderLineService(self.field_line_report_instances, self.completion_service)
        aggregated_df = leader_service.generate_aggregated_dataframe()

        if aggregated_df.empty:
            return None 

        if "RealCost" in aggregated_df.columns:
            aggregated_df.rename(columns={"RealCost": "TotalRealCost"}, inplace=True)
            
        leader_report = FieldLeadLineReport(aggregated_df, title="Field Leader Line (Consolidated)")
        return leader_report
    
    def generate_summary_to_lead_report(self):
        summary_df = pd.DataFrame()
        for report in self.field_line_report_instances:
            report_summary = report.generate_summary_data_frame()
            summary_df = pd.concat([summary_df, report_summary], ignore_index=True)
        return summary_df

    def open_leader_summary_report(self):
        # --- Lógica de Caché ---
        if self.summary_report_cache is None:
            # Si no hay caché, genera los datos (la primera vez o después de refrescar)
            QMessageBox.information(self.parent_view, "Loading Data", "The report is being generated for the first time. This may take a moment...")
            self.summary_report_cache = self.generate_summary_to_lead_report()
        
        summary_df = self.summary_report_cache
        # --- Fin Lógica de Caché ---

        if summary_df.empty:
            QMessageBox.information(self.parent_view, "No Data", "No summary data available to generate the report.")
            return
        
        # Pasamos el controlador a la vista para la comunicación de refresco
        self.summary_report_view = LeaderSummaryReportView(summary_df, self, self.parent_view)
        self.summary_report_view.showMaximized() 
        self.summary_report_view.setWindowModality(Qt.ApplicationModal)
        self.summary_report_view.exec_()
    
    def refresh_leader_summary_data(self):
        """Regenera los datos para el reporte resumen y los devuelve."""
        new_summary_df = self.generate_summary_to_lead_report()
        self.summary_report_cache = new_summary_df  # Actualiza el caché
        return new_summary_df

    def regenerar_reporte_linea_campo(self, title):
        """
        Regenera los datos de un solo reporte de línea de campo y retorna:
        gráfico, desviaciones, tipo.
        """
        report_instance = next((r for r in self.field_line_report_instances if r.title == title), None)
        if report_instance is not None:
            try:
                if hasattr(report_instance, 'reload_approved_budget_data'):
                    report_instance.reload_approved_budget_data()
                if hasattr(report_instance, 'reload_planned_activities_manager'):
                    report_instance.reload_planned_activities_manager()
                if hasattr(report_instance, 'reload_manual_planning_service'):
                    report_instance.reload_manual_planning_service()
                if hasattr(report_instance, 'reload_executed_activities_manager'):
                    report_instance.reload_executed_activities_manager()
                graph = report_instance.generate_graph()
                deviations = report_instance.generate_deviations()
                tipo = getattr(report_instance, 'type', 'default')
                return graph, deviations, tipo
            except PermissionError:
                QMessageBox.critical(
                    self.parent_view, 
                    "File Access Error", 
                    "The cost source file is currently open and cannot be read.\n\nPlease close the 'Control de costos.xlsx' file and try again."
                )
                return None, None, "default"
            except FileNotFoundError as e:
                QMessageBox.warning(self.parent_view, "File Not Found", "You must create the file first." + str(e))
                return None, None, "default"
        return None, None, "default"

    def regenerate_report_and_get_data(self, title):
        """
        Regenera un reporte de campo y retorna todos sus datos asociados.
        """
        configs = load_field_reports_from_json()
        report_config = next((cfg for cfg in configs if cfg.get("title") == title), {})
        if report_config.get("is_consolidated"):
            return self.regenerate_leader_line_report()
        else:
            graph, deviations, tipo = self.regenerar_reporte_linea_campo(title)
            comentario = self.get_comments_for_title(title)
            return graph, deviations, comentario, tipo
    
    def open_approved_budget_and_activities(self):
        available_line_titles = [report.title for report in self.field_line_report_instances]
        try:
            self.approved_budget_activities_service = ApprovedBudgetActivitiesService()
            self.approved_budget_activities_view = ApprovedBudgetActivitiesView(
                self.approved_budget_activities_service,
                available_line_titles=available_line_titles
            )
            self.approved_budget_activities_view.setWindowModality(Qt.ApplicationModal)
            self.approved_budget_activities_view.exec_()
        except FileNotFoundError as e:
            QMessageBox.warning(
                self.parent_view,
                "File Not Found",
                "You must create the file first." + str(e)
            )
    
    def open_cpi_spi_by_line(self):
        available_line_titles = [report.title for report in self.field_line_report_instances]
        self.cpi_spi_service = CpiSpiService()
        self.cpi_spi_view = CpiSpiView(
            self.cpi_spi_service,
            available_line_titles=available_line_titles,
            on_calculate_and_save=self.calculate_and_save_cpi_spi
        )
        self.cpi_spi_view.setWindowModality(Qt.ApplicationModal)
        self.cpi_spi_view.exec_()

    def calculate_and_save_cpi_spi(self, line_title):
        report_instance = next((r for r in self.field_line_report_instances if r.title == line_title), None)
        if report_instance is not None:
            try:
                if hasattr(report_instance, 'reload_planned_activities_manager'):
                    report_instance.reload_planned_activities_manager()
                
                if hasattr(report_instance, 'reload_manual_planning_service'):
                    report_instance.reload_manual_planning_service()

                df = report_instance.generate_combined_cpi_spi_dataframe() if hasattr(report_instance, 'generate_combined_cpi_spi_dataframe') else None
                if df is not None:
                    self.cpi_spi_service.set_line_title(line_title)
                    self.cpi_spi_service.dataframe = df
                    self.cpi_spi_service.save_to_csv()
                return None
            except RuntimeError as e:
                return str(e)

    def open_categorizer_executed_activities_catalog(self, selected_line_title):
        available_line_titles = [report.title for report in self.field_line_report_instances]
        if selected_line_title not in available_line_titles:
            print(f"Línea no reconocida: {selected_line_title}")
            return
        self.categorizer_executed_activities_catalog_service = CategorizerExecutedCatalogService()
        self.categorizer_executed_activities_catalog_service.set_line_title(selected_line_title) 
        self.categorizer_executed_activities_catalog_view = CategorizerExecutedCatalogView(
            self.categorizer_executed_activities_catalog_service,
            available_line_titles=[selected_line_title],
            on_calculate_and_save=self.calculate_and_save_categorizer_executed_activities
        )

        self.categorizer_executed_activities_catalog_view.setWindowModality(Qt.ApplicationModal)
        self.categorizer_executed_activities_catalog_view.exec_()

    def calculate_and_save_categorizer_executed_activities(self, line_title, month):
        report_instance = next((r for r in self.field_line_report_instances if r.title == line_title), None)
        if report_instance and hasattr(report_instance, 'get_categorizer_executed_activities_by_month'):
            df = report_instance.get_categorizer_executed_activities_by_month(month)
            if df is not None:
                self.categorizer_executed_activities_catalog_service.set_line_title(line_title)
                self.categorizer_executed_activities_catalog_service.set_month(month)
                self.categorizer_executed_activities_catalog_service.dataframe = df
                self.categorizer_executed_activities_catalog_service.save_to_csv()
    
    def open_total_executed_activities_view(self, selected_line_title):
        service = ExecutedActivitiesDetailService(selected_line_title)
        self.executed_activities_detail_view = ExecutedActivitiesDetailView(service)
        self.executed_activities_detail_view.setWindowModality(Qt.ApplicationModal)
        self.executed_activities_detail_view.exec_()

    def open_quote_extractor_view(self):
        self.quote_view = QuoteExtractorView()
        self.quote_view.data_changed.connect(lambda: self._refresh_quote_view_totals(self.quote_view, "ITEM 104 Varillera"))
        self.quote_view.completion_status_changed.connect(
            lambda checked: self.handle_quote_view_completion_changed(checked, "ITEM 104 Varillera")
        )
        self.quote_view.load_data_from_csv()
        self.quote_view.setWindowModality(Qt.ApplicationModal)
        self.quote_view.exec_()

    def open_south_zone_quote_extractor_view(self):
        configs = load_field_reports_from_json()
        south_zone_lines = [cfg["title"] for cfg in configs if cfg.get("zone", "") == "south"]
        self.south_zone_quote_view = SouthZoneQuoteExtractorView(available_line_titles=south_zone_lines)
        self.south_zone_quote_view.data_changed.connect(lambda: self._refresh_quote_view_totals(self.south_zone_quote_view, self.south_zone_quote_view.current_line))
        self.south_zone_quote_view.completion_status_changed.connect(
            lambda checked: self.handle_quote_view_completion_changed(checked, self.south_zone_quote_view.current_line)
        )
        self.south_zone_quote_view.load_data_from_csv()
        self.south_zone_quote_view.setWindowModality(Qt.ApplicationModal)
        self.south_zone_quote_view.exec_()

    def handle_quote_view_completion_changed(self, is_completed, line_title):
        if line_title:
            self.completion_service.set_status(line_title, is_completed)

    def open_historical_initial_cost_view(self):
        """Abre la vista de costo inicial aprobado"""
        try:
            self.historical_initial_cost_view = HistoricalInitialCostView()
            self.historical_initial_cost_view.setWindowModality(Qt.ApplicationModal)
            self.historical_initial_cost_view.exec_()
        except FileNotFoundError as e:
            QMessageBox.warning(
                self.parent_view,
                "File Not Found",
                "You must create the file first." + str(e)
            )

    def _refresh_quote_view_totals(self, view, line_title):
        if not view or not line_title:
            return
        report = next((r for r in self.field_line_report_instances if r.title == line_title), None)
        if not report:
            return
        if hasattr(report, 'reload_approved_budget_data'):
            report.reload_approved_budget_data()
        if hasattr(report, 'reload_manual_planning_service'):
            report.reload_manual_planning_service()
            
        df_approved = report.get_approved_budget_activities()
        approved_budget = float(df_approved[f'Presupuesto {self.year}'].iloc[0]) if not df_approved.empty else 0.0
        approved_activities = int(df_approved['Actividades aprobadas'].iloc[0]) if not df_approved.empty else 0

        df_real_cost_accumulated = report.generate_accumulated_real_cost_data_frame()
        non_zero_costs = df_real_cost_accumulated[df_real_cost_accumulated["TotalAccumulatedCost"] != 0]
        real_cost = float(non_zero_costs['TotalAccumulatedCost'].iloc[-1]) if not non_zero_costs.empty else 0.0
        
        last_valid_month_name = non_zero_costs.iloc[-1]['Month'] if not non_zero_costs.empty else None
        last_valid_month_index = self.month_map.get(last_valid_month_name.lower(), -1) if last_valid_month_name else -1
        _, validated_forecast_cost = view.get_costs_from_ui(last_valid_month_index)
        total_forecast_cost = real_cost + validated_forecast_cost
        remaining_budget = approved_budget - total_forecast_cost

        data = {
            "planned_total": approved_activities, 
            "executed_total": report.get_total_executed_activities(),
            "scheduled_total": view.get_validated_quote_count(),
            "approved_budget": approved_budget,
            "approved_activities": approved_activities,
            "executed_cost": real_cost, 
            "forecast_cost": total_forecast_cost,
            "remaining_budget": remaining_budget,
            "cpae_value": report.get_cost_by_activity()
        }
        is_completed = self.completion_service.get_status(line_title)
        view.set_completion_status(is_completed)
        view.update_totals(data)

    def open_adaptive_planning(self):
        """
        Crea y ejecuta el controlador especializado en la planificación de campo.
        """
        self.planning_controller = FieldPlanningController(
            field_reports=self.field_line_report_instances,
            approved_service=self.approved_service,
            completion_service=self.completion_service,
            parent_view=self.parent_view
        )
        self.planning_controller.run() 

    def generate_leader_line_report(self):
        """
        Obtiene el reporte líder usando el método ayudante y lo muestra.
        """
        leader_report = self._create_leader_line_report_object()
        if leader_report is None:
            QMessageBox.information(self.parent_view, "No Data", "No 'Completed' lines found to generate the report.")
            return
        graph = leader_report.generate_graph()
        if graph:
            self.parent_view.show_plot_view(
                graph,
                leader_report.generate_deviations(),
                title=leader_report.title
            )

    def regenerate_leader_line_report(self):
        """
        Regenera el reporte líder y DEVUELVE los componentes del gráfico
        para que la vista existente se actualice.
        """
        leader_report = self._create_leader_line_report_object()
        if leader_report is None:
            return None, pd.DataFrame(), "", "default"
        graph = leader_report.generate_graph()
        deviations = leader_report.generate_deviations()
        comments = self.get_comments_for_title(leader_report.title)
        return graph, deviations, comments, "default"
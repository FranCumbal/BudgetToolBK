from PyQt5.QtCore import QObject, Qt
from PyQt5.QtWidgets import QMessageBox
from services.field_lines_services.approved_budget_activities_service import ApprovedBudgetActivitiesService
from services.field_lines_services.planning_service_factory import PlanningServiceFactory
from services.field_lines_services.schedule_with_categorizer_service import ScheduleWithCategorizerService
from views.field_views.adaptive_planning_view import AdaptivePlanningView

class FieldPlanningController(QObject):
    def __init__(self, field_reports, approved_service, completion_service, parent_view=None):
        super().__init__()
        self.field_line_report_instances = field_reports
        self.approved_service = approved_service
        self.completion_service = completion_service
        self.parent_view = parent_view
        self.view = None 

    def run(self):
        """
        Crea, conecta y muestra la vista de planificación adaptativa.
        """
        try:
            available_line_titles = [report.title for report in self.field_line_report_instances]
            
            # La referencia a la vista ahora es self.view
            self.view = AdaptivePlanningView(
                approved_service=self.approved_service,
                available_line_titles=available_line_titles,
                field_line_reports=self.field_line_report_instances
            )
            
            # --- Las conexiones ahora usan self.view ---
            self.view.save_requested.connect(self.handle_save_field_plan_changes)
            self.view.line_changed.connect(self.on_adaptive_view_line_changed)
            self.view.item_edited.connect(self.handle_view_item_edited)
            self.view.calculation_requested.connect(self.handle_calculation_requested)
            self.view.completion_status_changed.connect(self.handle_completion_status_changed)

            # Carga inicial de datos
            if available_line_titles:
                self.on_adaptive_view_line_changed(self.view.line_combo.currentText())
            
            self.view.setWindowModality(Qt.ApplicationModal)
            self.view.exec_()
        except Exception as e:
            QMessageBox.critical(self.parent_view, "Error", f"No se pudo abrir la vista de planificación: {e}")


    def open_initial_field_activities_plan(self):
        """Abre la vista adaptativa, conecta las señales e inicia la carga de datos."""
        try:
            available_line_titles = [report.title for report in self.field_line_report_instances]
            approved_service = ApprovedBudgetActivitiesService()
            self.view = AdaptivePlanningView(
                approved_service=approved_service,
                available_line_titles=available_line_titles,
                field_line_reports=self.field_line_report_instances)
            self.view.save_requested.connect(self.handle_save_field_plan_changes)
            self.view.line_changed.connect(self.on_adaptive_view_line_changed)
            self.view.item_edited.connect(self.handle_view_item_edited)
            self.view.calculation_requested.connect(self.handle_calculation_requested)

            if available_line_titles:
                self.on_adaptive_view_line_changed(self.view.line_combo.currentText())
            
            self.view.setWindowModality(Qt.ApplicationModal)
            self.view.exec_()
        except Exception as e:
            parent_view = getattr(self, 'view', None)
            QMessageBox.critical(parent_view, "Error", f"No se pudo abrir la vista de planificación: {e}")

    # controllers/field_planning_controller.py

    def handle_view_item_edited(self, row_index, column_name, new_value):
        """
        Recibe un dato editado, VALIDA, actualiza el modelo, ejecuta cálculos
        dependientes y LUEGO refresca la vista.
        """
        view = self.view
        service = view.service
        report = view.field_report
        numeric_columns = [
            "Planned Activities", "Scheduled Activities", "Forecast",
            "Category 1", "Category 2", "Category 3"
        ]

        if column_name in numeric_columns:
            try:
                if new_value.strip() == '':
                    new_value = '0'
                float(new_value) 
            except (ValueError, TypeError):
                QMessageBox.warning(view, "Invalid Input", "You can only put numbers in this column.")
                self.refresh_adaptive_view() 

                return 
        month = view.month_map_reverse.get(row_index, None)
        if not month or not service:
            return

        service.update_row(month, column_name, new_value)

        # Solo calculamos automáticamente Scheduled Activities (suma de categorías)
        # pero NO el Forecast, que solo se calcula cuando el usuario lo solicita
        if isinstance(service, ScheduleWithCategorizerService):
            # Solo recalculamos Scheduled Activities si se editó una categoría
            if column_name in ["Category 1", "Category 2", "Category 3"]:
                service._post_update_calculations(month)

        self.refresh_adaptive_view()

    def handle_calculation_requested(self):
        """
        Maneja la lógica del cálculo automático de Forecast.
        """
        view = self.view
        service = view.service
        report = view.field_report
        table = view.table_widget.table 

        try:
            columns = service.get_columns()
            df_real_cost_accumulated = report.generate_accumulated_real_cost_data_frame()
            non_zero_costs = df_real_cost_accumulated[df_real_cost_accumulated["TotalAccumulatedCost"] != 0]
            last_valid_month_name = non_zero_costs.iloc[-1]['Month'] if not non_zero_costs.empty else None
            last_month_index = view.month_map.get(last_valid_month_name.lower(), -1) if last_valid_month_name else -1
            start_row = last_month_index + 1

            if isinstance(service, ScheduleWithCategorizerService):
                # Para líneas with_categorizer, calculamos Forecast basado en categorías
                if hasattr(report, "CATEGORIA_1"):
                    for row in range(start_row, table.rowCount()):
                        month = table.item(row, 0).text()
                        service.update_forecast(
                            month,
                            report.CATEGORIA_1,
                            report.CATEGORIA_2,
                            report.CATEGORIA_3
                        )
            else:
                # Para otras líneas, usamos CPAE * Scheduled Activities
                cpae_value = report.get_cost_by_activity() or 0
                scheduled_index = columns.index("Scheduled Activities")
                forecast_index = columns.index("Forecast")

                for row in range(start_row, table.rowCount()):
                    month = table.item(row, 0).text()
                    scheduled_text = table.item(row, scheduled_index).text() or "0"
                    scheduled = int(float(scheduled_text))
                    forecast = round(scheduled * cpae_value, 2)
                    service.update_row(month, "Forecast", forecast)
                    
            self.refresh_adaptive_view()
            QMessageBox.information(view, "Success", "Forecast calculated for future months.")
        except Exception as e:
            QMessageBox.critical(view, "Error", f"An error occurred during automatic calculation:\n{e}")

    def on_adaptive_view_line_changed(self, line_title):
        """
        Maneja el cambio de línea, crea el nuevo servicio y refresca la vista.
        """
        view = self.view
        if not view: return
        service_type = PlanningServiceFactory.get_service_type_from_line_reports(
            line_title, self.field_line_report_instances
        )
        new_service = PlanningServiceFactory.create_service(service_type, line_title)
        view.service = new_service
        is_completed = self.completion_service.get_status(line_title)
        self.view.set_completion_status(is_completed)
        self.refresh_adaptive_view()

    def handle_completion_status_changed(self, is_completed: bool):
        line_title = self.view.line_combo.currentText()
        if line_title:
            self.completion_service.set_status(line_title, is_completed)

    def handle_save_field_plan_changes(self):
        """Maneja la lógica de guardado, incluyendo la validación de datos."""
        view = self.view
        service = view.service
        approved_service = view.approved_service
        report = view.field_report
        line_title = view.line_combo.currentText()

        df_real_cost_accumulated = report.generate_accumulated_real_cost_data_frame()
        non_zero_costs = df_real_cost_accumulated[df_real_cost_accumulated["TotalAccumulatedCost"] != 0]
        last_valid_month_name = non_zero_costs.iloc[-1]['Month'] if not non_zero_costs.empty else None
        last_month_index = view.month_map.get(last_valid_month_name.lower(), -1) if last_valid_month_name else -1

        planned_total, _ = view.table_widget.get_column_totals(last_month_index)

        df_approved = approved_service.dataframe
        line_approved_data = df_approved[df_approved['line_name'] == line_title]
        approved_activities = int(line_approved_data.iloc[-1]['approved_activities']) if not line_approved_data.empty else None

        if approved_activities is not None and planned_total > approved_activities:
            QMessageBox.warning(view, "Validation Error",
                                f"The total Planned Activities ({planned_total}) exceeds the Approved Activities ({approved_activities}).\n\n"
                                "Please adjust the values before saving.")
            return

        service.save_to_csv()
        QMessageBox.information(view, "Success", f"Data saved successfully for {line_title}.")

    def refresh_adaptive_view(self):
        """
        Recolecta TODOS los datos del modelo y actualiza la vista. 
        """
        view = self.view
        if not view or not hasattr(view, 'service') or not view.service:
            return
        self.approved_service.reload()
        report = view.field_report
        if hasattr(report, 'reload_approved_budget_data'): #para arreglar problemas de cache
            report.reload_approved_budget_data()
        service = view.service
        approved_service = view.approved_service
        line_title = view.line_combo.currentText()

        df_real_cost_accumulated = report.generate_accumulated_real_cost_data_frame()
        non_zero_costs = df_real_cost_accumulated[df_real_cost_accumulated["TotalAccumulatedCost"] != 0]
        last_valid_month_name = non_zero_costs.iloc[-1]['Month'] if not non_zero_costs.empty else None
        last_month_index = view.month_map.get(last_valid_month_name.lower(), -1) if last_valid_month_name else -1

        df_approved = approved_service.dataframe
        line_approved_data = df_approved[df_approved['line_name'] == line_title]
        approved_activities = int(line_approved_data.iloc[-1]['approved_activities']) if not line_approved_data.empty else 0
        approved_budget = float(line_approved_data.iloc[-1]['budget']) if not line_approved_data.empty else 0.0
        cpae_value = report.get_cost_by_activity()

        forecast_df = report.generate_forecast()
        executed_activities_df = report.generate_executed_activities_data_frame_by_month()

        table_data = {
            "data_list": service.get_data_as_list(),
            "columns": service.get_columns(),
            "editable_columns": service.get_editable_columns(),
            "last_month_index": last_month_index,
            "real_costs": forecast_df["RealCost"],
            "executed_activities": executed_activities_df
        }
        view.update_table(table_data)

        planned_total, scheduled_total = view.table_widget.get_column_totals(last_month_index)
        
        forecast_cost = view.table_widget.get_column_sum("Forecast")

        executed_cost = non_zero_costs.iloc[-1]["TotalAccumulatedCost"] if not non_zero_costs.empty else 0.0

        totals_data = {
            "approved_activities": approved_activities,
            "planned_total": planned_total,
            "scheduled_total": scheduled_total,
            "executed_total": report.get_total_executed_activities(),
            "executed_cost": executed_cost,
            "forecast_cost": forecast_cost,
            "remaining_budget": approved_budget - forecast_cost,
            "approved_budget": approved_budget,
            "cpae_value": cpae_value 
        }

        if hasattr(report, 'service_type'):
            if report.service_type == "schedule_with_categorizer":
                info_text = "Planned Activities, Categories and Forecast are editable. Use 'Calculate automatically' button to auto-calculate Forecast."
            elif report.service_type == "schedule_without_categorizer":
                info_text = "Planned/Scheduled Activities are editable from the current month onwards."
            else:
                info_text = "Planned Activities are editable all year."
        else:
            info_text = "Planned Activities are editable all year."

        if hasattr(report, "CATEGORIA_1"):
            cat1 = report.CATEGORIA_1
            cat2 = report.CATEGORIA_2
            cat3 = report.CATEGORIA_3
            category_text = f"<b>Category values:</b> Cat 1: <span style='color:blue;'>{cat1}</span> | Cat 2: <span style='color:green;'>{cat2}</span> | Cat 3: <span style='color:orange;'>{cat3}</span>"
            are_categories_visible = True
        else:
            category_text = ""
            are_categories_visible = False

        view.update_totals(totals_data)
        view.update_cpae_label(line_title, cpae_value, approved_budget)
        view.update_info_labels(info_text, category_text, are_categories_visible)
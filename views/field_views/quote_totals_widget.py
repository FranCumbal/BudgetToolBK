# views/field_views/quote_totals_widget.py

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt5.QtCore import Qt

class QuoteTotalsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.activities_label = QLabel("Loading...") # Izquierda: Planned/Executed
        self.schedule_label = QLabel("Loading...")   # Centro: Scheduled
        self.budget_label = QLabel("Loading...")     # Derecha: Costs/Budget
        
        self._setup_ui()

    def _setup_ui(self):
        """Configura la apariencia interna de este widget."""
        label_style = "font-weight: bold; font-size: 14px; margin: 8px;"
        
        self.activities_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.activities_label.setStyleSheet(label_style)
        
        self.schedule_label.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        self.schedule_label.setStyleSheet(label_style)
        
        self.budget_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.budget_label.setStyleSheet(label_style)


        main_layout = QHBoxLayout(self)
        main_layout.addWidget(self.activities_label)
        main_layout.addStretch()
        main_layout.addWidget(self.schedule_label)
        main_layout.addStretch()
        main_layout.addWidget(self.budget_label)

    def update_data(self, data: dict):
        """Recibe los datos calculados y actualiza las tres secciones."""
        
        # --- Sección Izquierda: Actividades Planeadas y Ejecutadas ---
        planned_total = data.get("planned_total", 0)
        executed_total = data.get("executed_total", 0)
        
        activities_text = (f"<span style='color:black;'>Planned Activities Total: {planned_total}</span><br>"
                           f"<span style='color:green;'>Executed Activities Total: {executed_total}</span>")
        self.activities_label.setText(activities_text)
        self.activities_label.setTextFormat(Qt.TextFormat.RichText)

        # --- Sección Central: Actividades Programadas ---
        scheduled_total = data.get("scheduled_total", 0)
        to_be_scheduled = planned_total - executed_total
        to_be_scheduled = max(0, to_be_scheduled)

        color = "red" if scheduled_total > to_be_scheduled else "black"
        schedule_text = (f"<span style='color:purple;'>Activities to be scheduled: {to_be_scheduled}</span><br>"
                         f"<span style='color:{color};'>Scheduled Activities Total: {scheduled_total}</span>")
        self.schedule_label.setText(schedule_text)
        self.schedule_label.setTextFormat(Qt.TextFormat.RichText)

        # --- Sección Derecha: Costos y Presupuesto ---
        approved_budget = data.get("approved_budget", 0.0)
        real_cost = data.get("real_cost", 0.0)
        forecast_cost = data.get("forecast_cost", 0.0)
        remaining_budget = data.get("remaining_budget", 0.0)
        
        budget_color = "red" if remaining_budget < 0 else "darkblue"
        budget_text = (f"<span style='color:blue;'>Approved Budget: ${approved_budget:,.2f}</span><br>"
                       f"<span style='color:green;'>Total Real Cost: ${real_cost:,.2f}</span><br>"
                       f"<span style='color:purple;'>Total Forecast Cost: ${forecast_cost:,.2f}</span><br>"
                       f"<span style='color:{budget_color};'>Remaining Budget: ${remaining_budget:,.2f}</span>")
        self.budget_label.setText(budget_text)
        self.budget_label.setTextFormat(Qt.TextFormat.RichText)
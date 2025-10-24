from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt

class TotalsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.planned_label = QLabel("Loading...")
        self.scheduled_label = QLabel("Loading...")
        self.cost_label = QLabel("Loading...")
        
        self._setup_ui()

    def _setup_ui(self):
        """Configura la apariencia interna de este widget."""
        label_style = "font-weight: bold; font-size: 15px; margin: 8px;"
        
        self.planned_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.planned_label.setStyleSheet(label_style)
        
        self.scheduled_label.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        self.scheduled_label.setStyleSheet(label_style)
        
        self.cost_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.cost_label.setStyleSheet(label_style)

        main_layout = QHBoxLayout(self)
        main_layout.addWidget(self.planned_label)
        main_layout.addStretch()
        main_layout.addWidget(self.scheduled_label)
        main_layout.addStretch()
        main_layout.addWidget(self.cost_label)

    def update_data(self, data: dict):
        """
        Método público para recibir datos y actualizar las etiquetas con lógica de color mejorada.
        """
        approved_activities = data.get("approved_activities", 0)
        planned_total = data.get("planned_total", 0)
        executed_total = data.get("executed_total", 0)
        cpae_value = data.get("cpae_value", 0.0)
        approved_budget = data.get("approved_budget", 0.0) # Dato necesario para la nueva lógica

        if approved_activities is not None and planned_total > approved_activities:
            planned_color = "red"
        elif approved_activities is not None and planned_total == approved_activities:
            planned_color = "#008FF6"  
        else:
            planned_color = "black"
        planned_label_text = (f"<span style='color:#008FF6'>Approved Activities: {approved_activities}</span><br>"
                            f"<span style='color:{planned_color}'>Planned Activities Total: {planned_total}</span>")

        manual_budget_cost = planned_total * cpae_value
        if approved_budget > 0 and int(manual_budget_cost) == int(approved_budget):
            manual_budget_color = "#008FF6" 
        elif approved_budget > 0 and manual_budget_cost > approved_budget:
            manual_budget_color = "red" 
        else:
            manual_budget_color = "black" 

        manual_budget_str = f"<span style='color:{manual_budget_color};'>Manual Budget Cost: ${manual_budget_cost:,.2f}</span>"
        
        self.planned_label.setText(f"{planned_label_text}<br>{manual_budget_str}")
        self.planned_label.setTextFormat(Qt.TextFormat.RichText)

        scheduled_total = data.get("scheduled_total", 0.0)
        to_be_scheduled = planned_total - executed_total
        to_be_scheduled = max(0, to_be_scheduled)
        
        if scheduled_total > to_be_scheduled:
            scheduled_color = "red"
        elif scheduled_total == to_be_scheduled and scheduled_total > 0:
            scheduled_color = "purple" 
        else:
            scheduled_color = "black"

        executed_total_str = f"<span style='color:green'>Executed Activities Total: {executed_total}</span>"
        to_be_scheduled_str = f"<span style='color:purple'>Activities to be scheduled: {to_be_scheduled}</span>"
        scheduled_str = f"<span style='color:{scheduled_color}'>Scheduled Activities Total: {int(scheduled_total)}</span>"
        
        self.scheduled_label.setText(f"{executed_total_str}<br>{to_be_scheduled_str}<br>{scheduled_str}")
        self.scheduled_label.setTextFormat(Qt.TextFormat.RichText)

        executed_cost = data.get("executed_cost", 0.0)
        forecast_cost = data.get("forecast_cost", 0.0)
        remaining_budget = data.get("remaining_budget", 0.0)
        
        cost_label_text = (f"<span style='color:green;'>Total Real Cost: ${executed_cost:,.2f}</span><br>"
                        f"<span style='color:purple;'>Total Forecasted Cost: ${forecast_cost:,.2f}</span><br>"
                        f"<span style='color:darkblue;'>Remaining Budget: ${remaining_budget:,.2f}</span>")
        self.cost_label.setText(cost_label_text)
        self.cost_label.setTextFormat(Qt.TextFormat.RichText)
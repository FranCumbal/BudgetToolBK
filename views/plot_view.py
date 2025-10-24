from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QPushButton,
    QTextEdit, QSizePolicy, QMessageBox, QListWidgetItem
)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from utils.dates import normalize_month_names
import pandas as pd

class PlotView(QWidget):
    def __init__(self, parent, graph, deviations, controller, title="Plot", deviation_type="default"):
        super().__init__(parent)
        self.graph = graph
        self.deviations = deviations
        self.controller = controller
        self.title_text = title
        self.deviation_type = deviation_type
        self.filtered_deviations = deviations.copy()

        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout(self)

        # Sección gráfica
        graph_layout = QVBoxLayout()
        title_label = QLabel(self.title_text)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        graph_layout.addWidget(title_label)

        self.graph.set_size_inches(6, 4)
        self.graph.set_dpi(100)
        self.graph.tight_layout()

        canvas = FigureCanvas(self.graph)
        canvas.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        canvas.setFixedSize(1000, 800)

        graph_layout.addWidget(canvas)
        main_layout.addLayout(graph_layout, 2)

        # Sección de detalles
        details_layout = QVBoxLayout()

        # Filtro por mes
        filter_label = QLabel("Filter by month:")
        details_layout.addWidget(filter_label)

        self.month_filter = QListWidget()
        self.month_filter.setSelectionMode(QListWidget.MultiSelection)
        months = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]
        for month in months:
            self.month_filter.addItem(month)

        details_layout.addWidget(self.month_filter)

        filter_button = QPushButton("Apply Filter")
        filter_button.clicked.connect(self.apply_month_filter)
        details_layout.addWidget(filter_button)

        # Lista de desviaciones
        deviation_label = QLabel("Deviations:")
        details_layout.addWidget(deviation_label)

        self.deviation_list = QListWidget()
        details_layout.addWidget(self.deviation_list)

        self.populate_deviation_list(self.filtered_deviations)

        # Sección de comentarios
        comments_label = QLabel("Add Comments:")
        details_layout.addWidget(comments_label)
        

        self.comments_edit = QTextEdit()
        details_layout.addWidget(self.comments_edit)
        comentarios_existentes = self.controller.get_comments_for_title(self.title_text)
        self.comments_edit.setPlainText(comentarios_existentes)

        # Botones

        save_comment_button = QPushButton("Save Comments")
        save_comment_button.clicked.connect(self.guardar_comentario)
        details_layout.addWidget(save_comment_button)

        regenerate_button = QPushButton("Regenerate Report")
        regenerate_button.clicked.connect(self.regenerar_reporte)
        details_layout.addWidget(regenerate_button)

        main_layout.addLayout(details_layout, 1)

    def populate_deviation_list(self, deviations=None):
        self.deviation_list.clear()

        if deviations is None or deviations.empty:
            self.deviation_list.addItem("No deviations found.")
            return

        if self.deviation_type == "artificial_lift":
            self._populate_artificial_lift_deviations(deviations)
        else:
            for _, row in deviations.iterrows():
                msg = f"Month: {row.get('MONTH', '-')}, Deviation: {row.get('Desviaciones', 0)}"
                self.deviation_list.addItem(msg)

    def _populate_artificial_lift_deviations(self, deviations):
        deviations = deviations.copy()
        deviations["MONTH"] = normalize_month_names(deviations["MONTH"])

        deviation_groups = [
            'Servicio_Deviation', 'Equipo_Deviation', 'Protectores de Cable_Deviation',
            'Capilar_Deviation', 'Equipo Superficie_Deviation', 'Desarenador_Deviation',
            'Cable Nuevo_Deviation', 'B&H_Deviation'
        ]

        threshold = 20000

        month_order = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]
        deviations['MONTH'] = pd.Categorical(deviations['MONTH'], categories=month_order, ordered=True)
        sorted_deviations = deviations.sort_values(by=['MONTH', 'WELL'])

        for _, row in sorted_deviations.iterrows():
            deviation_text = f"{row['WELL']} ({row['MONTH']} {int(row['YEAR'])}): "
            for group in deviation_groups:
                if abs(row.get(group, 0)) > threshold:
                    deviation_text += f"{group.replace('_Deviation', '')}: {row[group]:+,.2f} $ | "
            deviation_text = deviation_text.rstrip(" | ")
            if not deviation_text.endswith(":"):
                self.deviation_list.addItem(deviation_text)

    def apply_month_filter(self):
        selected_months = [item.text() for item in self.month_filter.selectedItems()]
        if "MONTH" not in self.deviations.columns:
            QMessageBox.warning(self, "Sin columna 'MONTH'", "Este reporte no contiene columna 'MONTH'.")
            return

        df = self.deviations.copy()
        df["MONTH"] = normalize_month_names(df["MONTH"])

        if selected_months:
            df = df[df["MONTH"].isin(selected_months)]

        self.filtered_deviations = df
        self.populate_deviation_list(df)

    def guardar_comentario(self):
        comentario = self.comments_edit.toPlainText().strip()
        if comentario:
            self.controller.save_new_comment(self.title_text, comentario)
            QMessageBox.information(self, "Comment Save", "✅ The comment has been saved succesfully.")
        else:
            QMessageBox.warning(self, "Empty Comment", "Please, write a comment first.")

    def regenerar_reporte(self):

        # Obtener nuevos datos desde el controlador
        graph, deviations, comentario, deviation_type = self.controller.regenerar_reporte_y_retorna_datos(self.title_text)

        if graph is None:
            QMessageBox.warning(self, "Error", "The report could not be regenerated.")
            return

        # ✅ Actualizar atributos
        self.graph = graph
        self.deviations = deviations
        self.filtered_deviations = deviations.copy()
        self.deviation_type = deviation_type

        # ✅ Reemplazar canvas
        self.graph.set_size_inches(6, 4)
        self.graph.set_dpi(100)
        self.graph.tight_layout()

        canvas = FigureCanvas(self.graph)
        canvas.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        canvas.setFixedSize(1000, 800)

        # Reemplazar widget gráfico
        layout = self.layout()
        graph_layout = layout.itemAt(0).layout()
        old_canvas = graph_layout.itemAt(1).widget()
        graph_layout.replaceWidget(old_canvas, canvas)
        old_canvas.deleteLater()

        # ✅ Actualizar lista de desviaciones y comentario
        self.populate_deviation_list(deviations)
        self.comments_edit.setPlainText(comentario)

        QMessageBox.information(self, "Updated", "✅ Report Regenerated.")


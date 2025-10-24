from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor

class ExecutedActivitiesDetailView(QDialog):
    def __init__(self, service, parent=None):
        super().__init__(parent)
        self.service = service
        self.setWindowTitle("Executed Activities Detail")
        self.resize(900, 850)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        # Tabla
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Pozo", "Estado", "Mes", "Costo Servicio", "Costo Producto", "Costo B&H", "Total sin B&H", "Total con B&H"
        ])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.Stretch)
        layout.addWidget(self.table)

        # Cambiar color de la fila de encabezado
        self.set_header_row_color(QColor(180, 220, 255))

        # Cargar datos
        self.load_data()

        # Agregar resumen de costos y promedios al final con mejor estilo y en dos columnas
        summary_layout = QVBoxLayout()
        title_label = QLabel("<b>Summary</b>")
        title_label.setAlignment(Qt.AlignHCenter)
        title_label.setStyleSheet("font-size: 15px; color: #000000; margin-bottom: 8px; margin-top: 10px;")
        summary_layout.addWidget(title_label)
        content_layout = QHBoxLayout()
        left_col = QVBoxLayout()
        right_col = QVBoxLayout()
        label_style_without_b_and_h = (
            "font-size: 13px; padding: 6px 12px; border-radius: 6px; color: #0077b6"
        )
        label_style_with_b_and_h = (
            "font-size: 13px; padding: 6px 12px; border-radius: 6px; color: #218838"
        )
        total_sin_bh = self.service.get_total_without_b_and_h()
        total_con_bh = self.service.get_total_with_b_and_h()
        avg_sin_bh = self.service.get_avarage_by_activity_without_b_and_h()
        avg_con_bh = self.service.get_avarage_by_activity_with_b_and_h()
        total_sin_bh_label = QLabel(f"<b>Total Cost without B&H:</b> {total_sin_bh:,.2f}")
        total_sin_bh_label.setStyleSheet(label_style_without_b_and_h)
        total_con_bh_label = QLabel(f"<b>Total Cost with B&H:</b> {total_con_bh:,.2f}")
        total_con_bh_label.setStyleSheet(label_style_with_b_and_h)
        avg_sin_bh_label = QLabel(f"<b>Avarage Cost by Activity without B&H:</b> {avg_sin_bh:,.2f}")
        avg_sin_bh_label.setStyleSheet(label_style_without_b_and_h)
        avg_con_bh_label = QLabel(f"<b>Avarage Cost by Activity with B&H:</b> {avg_con_bh:,.2f}")
        avg_con_bh_label.setStyleSheet(label_style_with_b_and_h)
        left_col.addWidget(total_sin_bh_label)
        left_col.addWidget(avg_sin_bh_label)
        right_col.addWidget(total_con_bh_label)
        right_col.addWidget(avg_con_bh_label)
        content_layout.addLayout(left_col)
        content_layout.addLayout(right_col)
        summary_layout.addLayout(content_layout)
        layout.addLayout(summary_layout)

    def set_header_row_color(self, color):
        # Aplica color de fondo a los encabezados visuales usando QSS
        self.table.setStyleSheet(f"QHeaderView::section {{ background-color: rgb({color.red()}, {color.green()}, {color.blue()}); }}")

    def load_data(self):
        df = self.service.get_detail_dataframe()
        self.table.setRowCount(len(df))
        font = QFont()
        font.setBold(True)
        for row_idx, row in df.iterrows():
            is_total_row = str(row.get("Mes", "")).lower().startswith("total ")
            for col_idx, col_name in enumerate(["Pozo", "Estado", "Mes", "Costo Servicio", "Costo Producto", "Costo B&H", "Total sin B&H", "Total con B&H"]):
                value = str(row.get(col_name, ""))
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                if is_total_row:
                    item.setFont(font)
                    item.setBackground(QColor(180, 220, 255))
                self.table.setItem(row_idx, col_idx, item)
        self.table.resizeColumnsToContents()
        self.table.setColumnWidth(6, max(200, self.table.columnWidth(6)))

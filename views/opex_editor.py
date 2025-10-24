from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QHeaderView, QMessageBox
from PyQt5.QtCore import Qt
import pandas as pd

class OpexEditorWindow(QWidget):
    def __init__(self, opex_df: pd.DataFrame, on_save_callback):
        super().__init__()
        self.setWindowTitle("Editor de OPEX por Línea")
        self.on_save_callback = on_save_callback

        self.opex_df = opex_df.copy()
        total_row = pd.DataFrame([{
            "LINE": "Total WO OPEX",
            "OPEX_BUDGET": self.opex_df["OPEX_BUDGET"].sum()
        }])
        self.opex_df = pd.concat([self.opex_df, total_row], ignore_index=True)

        layout = QVBoxLayout()
        self.table = QTableWidget()
        self.populate_table()

        self.save_button = QPushButton("Guardar cambios")
        self.save_button.clicked.connect(self.guardar_cambios)

        layout.addWidget(self.table)
        layout.addWidget(self.save_button)
        self.setLayout(layout)

        self.table.cellChanged.connect(self.actualizar_total)
        self.table.cellChanged.connect(self.validar_valor_en_celda)
        self.adjustSize()
        self.autosize_window()

    def populate_table(self):
        self.table.setRowCount(len(self.opex_df))
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["LINE", "OPEX_BUDGET"])

        for row_idx, (_, row) in enumerate(self.opex_df.iterrows()):
            item_name = QTableWidgetItem(str(row["LINE"]))
            if row["LINE"] == "Total WO OPEX":
                item_name.setFlags(Qt.ItemIsEnabled)
            else:
                item_name.setFlags(item_name.flags() & ~Qt.ItemIsEditable)

            item_val = QTableWidgetItem(f"{row['OPEX_BUDGET']:,.2f}")
            if row["LINE"] == "Total WO OPEX":
                item_val.setFlags(Qt.ItemIsEnabled)
            else:
                item_val.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)

            self.table.setItem(row_idx, 0, item_name)
            self.table.setItem(row_idx, 1, item_val)

        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def validar_valor_en_celda(self, row, column):
        if column != 1 or self.table.item(row, 0).text() == "Total WO OPEX":
            return

        item = self.table.item(row, column)
        texto = item.text().replace(",", "").strip()

        try:
            float(texto)
            item.setBackground(Qt.white)
            item.setToolTip("")
        except ValueError:
            item.setBackground(Qt.red)
            item.setToolTip("Valor inválido. Ingrese un número como 2,500,000.00.")

    def actualizar_total(self, row, column):
        if column != 1:
            return
        if self.table.item(row, 0).text() == "Total WO OPEX":
            return

        total = 0
        for i in range(self.table.rowCount() - 1):
            try:
                val_text = self.table.item(i, 1).text().replace(",", "").strip()
                total += float(val_text)
            except:
                continue

        self.table.blockSignals(True)
        self.table.item(self.table.rowCount() - 1, 1).setText(f"{total:,.2f}")
        self.table.blockSignals(False)

    def guardar_cambios(self):
        updated_data = []
        errores = []
        for row_idx in range(self.table.rowCount() - 1):  # Ignorar total
            name = self.table.item(row_idx, 0).text()
            value_text = self.table.item(row_idx, 1).text()
            try:
                value = float(value_text.replace(",", ""))
                if value <= 0:
                    raise ValueError()
                updated_data.append({"LINE": name, "OPEX_BUDGET": value})
            except:
                errores.append(f"Línea: {name} ➤ Valor inválido: '{value_text}'")

        if errores:
            QMessageBox.warning(self, "Errores encontrados", "⚠️ No se puede guardar:\n" + "\n".join(errores))
            return

        updated_df = pd.DataFrame(updated_data)
        self.on_save_callback(updated_df)
        self.close()

    def autosize_window(self):
        """
        Ajusta el tamaño de la ventana según el contenido de la tabla.
        """
        width = self.table.verticalHeader().width()
        for col in range(self.table.columnCount()):
            width += self.table.columnWidth(col)
        width += 60  # margen extra para el layout

        height = self.table.horizontalHeader().height()
        for row in range(self.table.rowCount()):
            height += self.table.rowHeight(row)
        height += 100  # espacio para botón y padding

        max_width = 1000
        max_height = 700
        self.setMinimumSize(min(width, max_width), min(height, max_height))
        self.resize(min(width, max_width), min(height, max_height))

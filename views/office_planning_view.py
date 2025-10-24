from datetime import datetime
from PyQt5.QtWidgets import QHBoxLayout, QSizePolicy, QDialog, QVBoxLayout, QComboBox, QTableWidget, QTableWidgetItem, QPushButton, QMessageBox, QLabel
from PyQt5.QtCore import Qt
import pandas as pd
import ast
import operator as op
import os


class OfficePlanningView(QDialog):
    def __init__(self, available_line_titles, data_loader, plan_actividades, save_path, controller):
        super().__init__()
        self.available_line_titles = available_line_titles
        self.data_loader = data_loader
        self.plan_actividades = plan_actividades
        self.save_path = save_path
        self.controller = controller
        self.setWindowTitle("Office Activity Planning")
        self.setMinimumWidth(600)
        self.setMinimumHeight(700)

        self.line_combo = QComboBox()
        self.line_combo.addItems(self.available_line_titles)
        self.table = QTableWidget()
        self.save_button = QPushButton("Save changes")
        self.auto_calc_button = QPushButton("Calcular automáticamente")
        self.label_total_cost = QLabel()

        layout = QVBoxLayout(self)
        layout.addWidget(self.line_combo)
        layout.addWidget(self.table)
        layout.addWidget(self.label_total_cost)
        layout.addWidget(self.save_button)

        # Crear un layout horizontal para el botón de calcular automáticamenteE 
        h_layout = QHBoxLayout()
        self.auto_calc_button.setFixedWidth(220)
        self.auto_calc_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        h_layout.addWidget(self.auto_calc_button)
        h_layout.addStretch(1)
        layout.addLayout(h_layout)

        self.line_combo.currentTextChanged.connect(self.load_data_for_line)
        self.save_button.clicked.connect(self.save_to_xlsx)
        self.auto_calc_button.clicked.connect(self.auto_calculate_cost)

        # Conectar evento de edición de celda para evaluar expresiones matemáticas
        self.table.cellChanged.connect(self.on_cost_cell_changed)

        self.load_data_for_line(self.line_combo.currentText())

    def load_data_for_line(self, line_title):
        file_name = f"{line_title}_Planning_Cost.xlsx"
        file_path = os.path.join(self.save_path, file_name)

        # 1. Siempre obtener meses y actividades planificadas del método universal
        df_base = self.data_loader.get_total_activities_by_month_df_from_plan(
            self.plan_actividades.plan_path,
            self.plan_actividades.sheet_name
        )
        df_view = pd.DataFrame({
            "Mes": df_base["MONTH"],
            "Actividades Planificadas": df_base["PLANNED_ACTIVITIES"].astype(int),
            "Costo de Plan": [0.0 for _ in range(len(df_base))]
        })

        # 2. Si existe el archivo, solo recuperar el costo de plan por mes
        if os.path.exists(file_path):
            try:
                df_file = pd.read_excel(file_path)
                df_file = df_file.fillna("")
                # Hacer merge solo de la columna "Costo de Plan" por "Mes"
                if "Mes" in df_file.columns and "Costo de Plan" in df_file.columns:
                    df_view = df_view.merge(
                        df_file[["Mes", "Costo de Plan"]],
                        on="Mes",
                        how="left",
                        suffixes=("", "_file")
                    )
                    # Si hay valores en la columna mergeada, reemplazar
                    df_view["Costo de Plan"] = df_view["Costo de Plan_file"].combine_first(df_view["Costo de Plan"])
                    df_view = df_view.drop(columns=["Costo de Plan_file"])
            except Exception as e:
                QMessageBox.information(self, "Error", f"Al leer el archivo de costos: {e}")

        self.table.setRowCount(len(df_view))
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Mes", "Actividades Planificadas", "Costo de Plan"])
        for row_idx, row in df_view.iterrows():
            for col_idx, col in enumerate(["Mes", "Actividades Planificadas", "Costo de Plan"]):
                item = QTableWidgetItem(str(row[col]) if col in row else "")
                if col == "Mes":
                    item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                self.table.setItem(row_idx, col_idx, item)

        # Calcular y mostrar el costo total planificado
        try:
            total_cost = pd.to_numeric(df_view["Costo de Plan"], errors="coerce").fillna(0).sum()
        except Exception:
            total_cost = 0
        self.label_total_cost.setText(f"Costo Planificado Total: <b>{total_cost:,.2f}</b>")

    def safe_eval(self, expr):
        """
        Evalúa una expresión matemática de forma segura.
        Permite +, -, *, /, paréntesis y decimales. Valida división por cero.
        """
        # Operadores permitidos
        allowed_operators = {
            ast.Add: op.add,
            ast.Sub: op.sub,
            ast.Mult: op.mul,
            ast.Div: op.truediv,
            ast.USub: op.neg
        }
        def eval_(node):
            if isinstance(node, ast.Num):
                return node.n
            elif isinstance(node, ast.BinOp):
                left = eval_(node.left)
                right = eval_(node.right)
                if isinstance(node.op, ast.Div) and right == 0:
                    raise ZeroDivisionError("División por cero")
                return allowed_operators[type(node.op)](left, right)
            elif isinstance(node, ast.UnaryOp):
                return allowed_operators[type(node.op)](eval_(node.operand))
            else:
                raise ValueError("Operación no permitida")
        try:
            node = ast.parse(expr, mode='eval').body
            return eval_(node)
        except Exception:
            return expr  # Si no es válido, retorna el texto original
    def on_cost_cell_changed(self, row, column):
        # Solo aplicar en la columna 'Costo de Plan' (índice 2)
        if column == 2:
            item = self.table.item(row, column)
            if item is not None:
                expr = item.text().replace(',', '.')
                result = self.safe_eval(expr)
                if isinstance(result, (int, float)):
                    item.setText(f"{result:.2f}")
                elif isinstance(result, str) and result != expr:
                    item.setText(str(result))

    def auto_calculate_cost(self):
        line_title = self.line_combo.currentText()
        if line_title == "1.15 Tanks and Trunks":
            df_cost = self.controller.calcular_plan_costo_automatico_tanks_and_trunks(
                self.plan_actividades.year if hasattr(self.plan_actividades, 'year') else datetime.now().year,
                self.plan_actividades
            )
        elif line_title == "1.08 Testing and Fluid Analysis":
            df_cost = self.controller.calcular_plan_costo_automatico_testing(
                self.plan_actividades.year if hasattr(self.plan_actividades, 'year') else datetime.now().year,
                self.plan_actividades
            )
        elif line_title == "1.06 Wireline Report":
            df_cost = self.controller.calcular_plan_costo_automatico_wireline(
                self.plan_actividades.year if hasattr(self.plan_actividades, 'year') else datetime.now().year,
                self.plan_actividades
            )
        else:
            QMessageBox.information(self, "Solo Tanks, Testing y Wireline", "El cálculo automático solo está disponible para '1.15 Tanks and Trunks', '1.08 Testing and Fluid Analysis' y '1.6 Wireline'.")
            return

        # df_cost tiene columnas MONTH y PLANNED_COST
        # Actualizar la columna "Costo de Plan" en la tabla
        for row in range(self.table.rowCount()):
            mes_item = self.table.item(row, 0)
            if mes_item is not None:
                mes = mes_item.text()
                costo_row = df_cost[df_cost["MONTH"] == mes]
                if not costo_row.empty:
                    costo = float(costo_row["PLANNED_COST"].values[0])
                    costo_item = QTableWidgetItem(f"{costo:.2f}")
                    self.table.setItem(row, 2, costo_item)

    def save_to_xlsx(self):
        import os
        line_title = self.line_combo.currentText()
        df = pd.DataFrame([
            {
                "Mes": self.table.item(row, 0).text() if self.table.item(row, 0) else "",
                "Actividades Planificadas": self.table.item(row, 1).text() if self.table.item(row, 1) else "",
                "Costo de Plan": self.table.item(row, 2).text() if self.table.item(row, 2) else ""
            }
            for row in range(self.table.rowCount())
        ])
        # Construir el nombre de archivo
        file_name = f"{line_title}_Planning_Cost.xlsx"
        save_path_xlsx = os.path.join(self.save_path, file_name)
        df.to_excel(save_path_xlsx, index=False)
        QMessageBox.information(self, "Éxito", f"Datos guardados en {save_path_xlsx}")



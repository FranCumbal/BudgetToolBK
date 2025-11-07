from PyQt5.QtCore import QAbstractTableModel, Qt
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtWidgets import QMessageBox, QMenuBar, QAction
import pandas as pd
from datetime import datetime


class PandasForecastedModel(QAbstractTableModel):
    def __init__(self, df: pd.DataFrame):
        super().__init__()
        self._df = df
        self.current_month, self.next_month = self.get_current_and_next_months()
        self.invalid_cells = set()

    def rowCount(self, parent=None): return self._df.shape[0]
    def columnCount(self, parent=None): return self._df.shape[1]

    def data(self, index, role=Qt.DisplayRole):
        value = self._df.iloc[index.row(), index.column()]
        col_name = self._df.columns[index.column()]
        row_tipo = self._df.iloc[index.row(), self._df.columns.get_loc("Tipo de Actividad")]

        if role in (Qt.DisplayRole, Qt.EditRole):
            if isinstance(value, float) and value.is_integer():
                return str(int(value))
            return str(value)

        if role == Qt.ToolTipRole and self.is_editable(index):
            restante = self.get_restante(index.row(), exclude_col=col_name)
            return f"Actividades restantes: {restante}"

        if role == Qt.BackgroundRole:
            if (index.row(), index.column()) in self.invalid_cells:
                return QColor("#f2dede")
            if self.is_editable(index):
                return QColor("#dff0d8")
            if row_tipo == "TOTAL":
                return QColor("#e0e0e0")

        if role == Qt.FontRole and row_tipo == "TOTAL":
            font = QFont()
            font.setBold(True)
            return font

        return None
    def setData(self, index, value, role):
        if role == Qt.EditRole:
            try:
                col_name = self._df.columns[index.column()]
                row_idx = index.row()
                row_tipo = self._df.iloc[row_idx, self._df.columns.get_loc("Tipo de Actividad")]
                if row_tipo == "TOTAL":
                    return False

                # ⚠️ Validación: solo enteros válidos
                try:
                    nuevo_valor = int(float(value))
                except ValueError:
                    self.show_warning("Solo se permiten números enteros.")
                    return False

                plan_total = int(self._df.at[row_idx, "Total"])

                if col_name in [self.current_month, self.next_month]:
                    columnas_meses = [col for col in self._df.columns if col not in ['No.', 'Tipo de Actividad', 'Total']]
                    mes_limite = self.get_month_number(self.next_month)

                    suma_previos = sum(
                        int(self._df.at[row_idx, col]) for col in columnas_meses
                        if col != col_name and self.get_month_number(col) <= mes_limite
                    )   
                    max_permitido = plan_total - suma_previos

                    """if nuevo_valor > max_permitido:
                        self.invalid_cells.add((row_idx, index.column()))
                        self.show_warning(f"No puedes asignar más de {max_permitido} actividades en este mes.")
                        self.dataChanged.emit(index, index)
                        return False"""

                    self._df.at[row_idx, col_name] = nuevo_valor
                    self.invalid_cells.discard((row_idx, index.column()))
                    self.redistribuir_restantes(row_idx)
                    self.recalcular_fila_total()
                    self.dataChanged.emit(index, index)
                    return True

                elif col_name == "Total":
                    nuevo_valor = int(float(value))
                    columnas_meses = [col for col in self._df.columns if col not in ['No.', 'Tipo de Actividad', 'Total']]
                    mes_limite = self.get_month_number(self.current_month)

                    ya_realizado = sum(
                        int(self._df.at[row_idx, col]) for col in columnas_meses
                        if self.get_month_number(col) <= mes_limite
                    )


                    if nuevo_valor < ya_realizado:
                        self.invalid_cells.add((row_idx, index.column()))
                        self.show_warning(f"No puedes asignar menos de {ya_realizado} actividades ya realizadas.")
                        self.dataChanged.emit(index, index)
                        return False

                    self._df.at[row_idx, "Total"] = nuevo_valor
                    self.redistribuir_futuros(row_idx, nuevo_valor)
                    self.recalcular_fila_total()
                    self.dataChanged.emit(index, index)
                    return True

            except Exception as e:
                print(f"Error al editar celda: {e}")
                self.show_warning(f"Ocurrió un error: {e}")
                return False
        return False

    def redistribuir_futuros(self, row_idx, nuevo_total):
        columnas_meses = [col for col in self._df.columns if col not in ['No.', 'Tipo de Actividad', 'Total']]
        mes_limite = self.get_month_number(self.current_month)
        
        ya_definidos = sum(
            int(self._df.at[row_idx, col]) for col in columnas_meses
            if self.get_month_number(col) <= mes_limite
        )
        faltante = max(nuevo_total - ya_definidos, 0)
        meses_futuros = [m for m in columnas_meses if self.get_month_number(m) > mes_limite]
        n = len(meses_futuros)
        if n == 0:
            return

        base = faltante // n
        extra = faltante % n
        for i, mes in enumerate(meses_futuros):
            self._df.at[row_idx, mes] = base + (1 if i < extra else 0)

    def flags(self, index):
        if self.is_editable(index):
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled

    def is_editable(self, index):
        col_name = self._df.columns[index.column()]
        row_tipo = self._df.iloc[index.row(), self._df.columns.get_loc("Tipo de Actividad")]
        if row_tipo == "TOTAL":
            return False
        month_names = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]
        now = datetime.now()
        current_month_idx = now.month - 1
        if col_name in month_names and month_names.index(col_name) > current_month_idx:
            return True

        return col_name == "Total"

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            return self._df.columns[section] if orientation == Qt.Horizontal else str(self._df.index[section])
        return None

    def get_dataframe(self):
        return self._df

    def get_current_and_next_months(self):
        month_names = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]
        now = datetime.now()
        current_idx = now.month - 1
        next_idx = (current_idx + 1) % 12
        return month_names[current_idx], month_names[next_idx]

    def get_month_number(self, name):
        try:
            return datetime.strptime(name, "%B").month
        except:
            return 0

    def get_restante(self, row_idx, exclude_col=None):
        columnas_meses = [col for col in self._df.columns if col not in ['No.', 'Tipo de Actividad', 'Total']]

        total = int(self._df.at[row_idx, "Total"])
        suma = 0
        for col in columnas_meses:
            if col == exclude_col:
                continue
            if self.get_month_number(col) <= self.get_month_number(self.next_month):
                try:
                    suma += int(self._df.at[row_idx, col])
                except:
                    pass
        return max(total - suma, 0)

    def redistribuir_restantes(self, row_idx):
        columnas_meses = [col for col in self._df.columns if col not in ['No.', 'Tipo de Actividad', 'Total']]
        mes_limite = self.get_month_number(self.next_month)

        definidos = sum(
            int(self._df.at[row_idx, col]) for col in columnas_meses
            if self.get_month_number(col) <= mes_limite
        )
        total = int(self._df.at[row_idx, "Total"])
        faltante = max(total - definidos, 0)

        meses_futuros = [col for col in columnas_meses if self.get_month_number(col) > mes_limite]
        if not meses_futuros:
            return

        base = faltante // len(meses_futuros)
        extra = faltante % len(meses_futuros)

        for i, col in enumerate(meses_futuros):
            self._df.at[row_idx, col] = base + (1 if i < extra else 0)

    def redistribuir_row(self, row_idx, nuevo_total):
        columnas_meses = [col for col in self._df.columns if col not in ['No.', 'Tipo de Actividad', 'Total']]
        mes_limite = self.get_month_number(self.next_month)

        ya_definidos = sum(
            self._df.at[row_idx, col] for col in columnas_meses
            if self.get_month_number(col) <= mes_limite
        )
        faltante = max(nuevo_total - ya_definidos, 0)
        meses_disponibles = [m for m in columnas_meses if self.get_month_number(m) > mes_limite]
        n = len(meses_disponibles)
        if n == 0:
            return

        base = faltante // n
        extra = faltante % n

        for i, mes in enumerate(meses_disponibles):
            self._df.at[row_idx, mes] = base + (1 if i < extra else 0)

    def recalcular_total(self, row_idx):
        columnas_meses = [col for col in self._df.columns if col not in ['No.', 'Tipo de Actividad', 'Total']]
        return sum(float(self._df.at[row_idx, col]) for col in columnas_meses)

    def recalcular_fila_total(self):
        columnas_meses = [col for col in self._df.columns if col not in ['No.', 'Tipo de Actividad', 'Total']]
        total_row_idx = self._df.shape[0] - 1


        for col in columnas_meses:
            suma = 0
            for row in range(total_row_idx):
                try:
                    valor = float(self._df.at[row, col])
                    suma += valor
                except:
                    pass
            self._df.at[total_row_idx, col] = int(suma)

        for row in range(total_row_idx):
            self._df.at[row, "Total"] = int(self.recalcular_total(row))

        # Recalcular el total sumando solo las columnas de meses y solo en filas anteriores al total
        self._df.at[total_row_idx, "Total"] = int(
            self._df.loc[:total_row_idx - 1, columnas_meses].sum(axis=1).sum()
        )

        self.layoutChanged.emit()

    def show_warning(self, msg):
        QMessageBox.warning(None, "Advertencia", msg)


from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QTableView, QMessageBox, QLabel
)
from PyQt5.QtCore import Qt
from views.forecasted_plan_editor import PandasForecastedModel  
import pandas as pd


class ForecastedPlanEditorWindow(QWidget):
    def __init__(self, df: pd.DataFrame, excel_path: str, pozos_sugeridos, controller):
        super().__init__()
        self.setWindowTitle("Editor de Plan Anual de Actividades Forecasteadas")
        self.df = df
        self.excel_path = excel_path
        self.pozos_sugeridos = pozos_sugeridos
        self.controller = controller 
        layout = QVBoxLayout()
        self.setLayout(layout) 

        self.setup_menu()

       # Crear label de actividades totales basado en el valor pasado al constructor
        self.label_actividades = QLabel(f"Actividades totales a planificar: <b>{self.pozos_sugeridos:.2f}</b>")
        self.label_actividades.setAlignment(Qt.AlignCenter)
        self.label_actividades.setStyleSheet("font-size: 22px; font-weight: bold; margin: 12px 0;")
        layout.addWidget(self.label_actividades)


        # Crear tabla
        self.table = QTableView()
        df_with_total = self.agregar_fila_total(self.df)
        self.model = PandasForecastedModel(df_with_total)
        self.table.setModel(self.model)
        layout.addWidget(self.table)

        # Conectar la actualización del label cuando cambia la tabla
        #self.model.layoutChanged.connect(self.update_label_actividades)

        # Botón guardar
        guardar_btn = QPushButton("Guardar cambios")
        guardar_btn.clicked.connect(self.guardar_excel)
        layout.addWidget(guardar_btn)

        self.resize(1300, 600)
        self.adjust_table_size()

    def update_label_actividades(self):
        """Actualiza el label con la suma de la columna Total excluyendo la fila TOTAL"""
        print("Se guardo Exitosamente")


    def setup_menu(self):
        """ Crea y configura la barra de menú para esta ventana.
            Esto servira unicamente para Wireline, Tanks and Trunks y Testing. No se si esa logica apliquen las demas lineas
        """
        menu_bar = QMenuBar(self)
        self.layout().setMenuBar(menu_bar)

        config_menu = menu_bar.addMenu("Configuración")

        capex_action = QAction("Configuración Capex", self)
        # Conectar la acción al método del controlador
        capex_action.triggered.connect(self.controller.open_capex_config_editor)
        config_menu.addAction(capex_action)
    
    def agregar_fila_total(self, df):
        df_copy = df.copy()
        columnas_meses = [c for c in df.columns if c not in ['No.', 'Tipo de Actividad', 'Total']]

        total_row = {
            'No.': '',
            'Tipo de Actividad': 'TOTAL'
        }

        for col in columnas_meses:
            total_row[col] = df_copy[col].sum()
        
        total_row['Total'] = df_copy['Total'].sum()

        total_df = pd.DataFrame([total_row])
        return pd.concat([df_copy, total_df], ignore_index=True)


    def guardar_excel(self):
        try:
            df_to_save = self.model.get_dataframe().copy()
            df_to_save = df_to_save[df_to_save["Tipo de Actividad"] != "TOTAL"]

            # Guardar toda la distribución mensual, no solo los totales
            with pd.ExcelWriter(self.excel_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                df_to_save.to_excel(writer, sheet_name="ForecastedPlan"+str(datetime.now().year), index=False)

            # Refrescar la vista de la tabla (sin recargar desde archivo)
            self.model.layoutChanged.emit()
            self.adjust_table_size()

            QMessageBox.information(self, "Éxito", "Plan completo guardado y la tabla actualizada.")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al guardar la hoja: {e}")


    def adjust_table_size(self):
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()

        width = self.table.verticalHeader().width()
        for col in range(self.table.model().columnCount()):
            width += self.table.columnWidth(col)
        width += 80

        height = self.table.horizontalHeader().height()
        for row in range(self.table.model().rowCount()):
            height += self.table.rowHeight(row)
        height += 100

        max_width = 1300
        max_height = 800
        self.setMinimumSize(min(width, max_width), min(height, max_height))
        self.resize(min(width, max_width), min(height, max_height))
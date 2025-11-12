#completions_config_view

import sys
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem,
                             QComboBox, QPushButton, QHBoxLayout, QLabel, QHeaderView, QMessageBox)
from PyQt5.QtCore import Qt
import pandas as pd

# --- 1. Nombre de Clase Cambiado ---
class CompletionsConfigDialog(QDialog):
    """
    Diálogo de configuración para el plan manual de Completions (1.03).
    Lógica de "Ofensor": Carga AVG_QUANTITY automáticamente.
    """
    
    # Constantes (idénticas a MI Swaco)
    COL_MONTH = "MONTH"
    COL_TIPO = "TYPE"
    COL_ACTIVIDAD = "ACTIVITIES"
    COL_AVG = "AVG_QUANTITY"

    SRC_COL_LINE = "line"
    SRC_COL_TIPO = "TIPO"
    SRC_COL_ACTIVIDAD = "ACTIVIDADES"
    SRC_COL_AVG = "AVG POR ACTIVIDAD" 
    
    def __init__(self, df_config, df_catalog, parent=None):
        super().__init__(parent)
        # --- 2. Título Cambiado ---
        self.setWindowTitle("Configurar Plan Manual (1.03 Completions)")
        self.setWindowModality(Qt.ApplicationModal)
        
        self.df_config = df_config.copy()
        self.df_catalog = df_catalog.copy()

        if not self.df_catalog.empty:
            self.df_catalog.columns = self.df_catalog.columns.str.strip()

        self.setup_catalog_maps()
        self.init_ui()
        self.populate_table()

    def setup_catalog_maps(self):
        """
        Procesa el df_catalog para crear:
        1. self.catalog_map: Un dict para los dropdowns (TYPE -> [ACTIVITIES])
        2. self.avg_map: Un dict para buscar AVG_QUANTITY ((TYPE, ACTIVITY) -> AVG)
        """
        self.catalog_map = {}
        self.avg_map = {}
        
        if self.df_catalog.empty:
            print("Advertencia: Catálogo Completions está vacío.")
            return

        try:
            # --- LÓGICA DE FILTRO CORREGIDA (Línea 1101) ---
            # Filtramos por la columna TIPO (SRC_COL_TIPO) buscando 'ofensor'
            df_ofensor = self.df_catalog[
                self.df_catalog[self.SRC_COL_TIPO].fillna('').str.lower().str.contains('ofensor', na=False)
            ].copy()
            
            if df_ofensor.empty:
                print("Advertencia: No se encontraron ítems de 'tipo ofensor' en el catálogo COMPLETIONS.")
                QMessageBox.warning(self, "Catálogo Vacío", 
                    "No se encontraron ítems cuyo 'TIPO' contenga la palabra 'ofensor' en el catálogo COMPLETIONS.")
                return

            # --- Construir mapas usando solo el catálogo filtrado ---
            for tipo in df_ofensor[self.SRC_COL_TIPO].unique():
                
                if pd.isna(tipo):
                    continue
                    
                actividades = df_ofensor[df_ofensor[self.SRC_COL_TIPO] == tipo][self.SRC_COL_ACTIVIDAD].unique().tolist()
                self.catalog_map[tipo] = actividades
                
                for act in actividades:
                    avg_val_row = df_ofensor[
                        (df_ofensor[self.SRC_COL_TIPO] == tipo) &
                        (df_ofensor[self.SRC_COL_ACTIVIDAD] == act)
                    ][self.SRC_COL_AVG]
                    
                    if not avg_val_row.empty:
                        avg_val = avg_val_row.values[0]
                        self.avg_map[(tipo, act)] = float(avg_val) if pd.notna(avg_val) else 0.0
                    else:
                        self.avg_map[(tipo, act)] = 0.0
                        
        except KeyError as e:
            QMessageBox.critical(self, "Error de Catálogo",
                f"No se encontró la columna requerida '{e}' en la hoja 'COMPLETIONS'.\n\n"
                f"Se requieren: {self.SRC_COL_TIPO}, {self.SRC_COL_ACTIVIDAD}, {self.SRC_COL_AVG}")
            return

        self.tipo_list = sorted(list(self.catalog_map.keys()))
        self.months_list = ["January", "February", "March", "April", "May", "June",
                            "July", "August", "September", "October", "November", "December"]

    def init_ui(self):
        """Inicializa los componentes de la interfaz gráfica."""
        self.layout = QVBoxLayout(self)
        self.setMinimumSize(900, 500)
        self.table_widget = QTableWidget(self)
        
        self.table_cols = [self.COL_MONTH, self.COL_TIPO, self.COL_ACTIVIDAD, self.COL_AVG]
        self.table_widget.setColumnCount(len(self.table_cols))
        self.table_widget.setHorizontalHeaderLabels(self.table_cols)
        
        self.table_widget.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table_widget.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table_widget.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table_widget.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)

        self.layout.addWidget(self.table_widget)

        # Botones
        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("Add Row")
        self.btn_remove = QPushButton("Remove Row")
        self.btn_ok = QPushButton("OK")
        self.btn_cancel = QPushButton("Cancel")
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_remove)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_ok)
        btn_layout.addWidget(self.btn_cancel)
        self.layout.addLayout(btn_layout)

        # Conexiones
        self.btn_add.clicked.connect(self.add_row)
        self.btn_remove.clicked.connect(self.remove_row)
        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)

    def populate_table(self):
        """Llena la tabla con los datos del df_config (el plan guardado)."""
        self.table_widget.setRowCount(len(self.df_config))
        
        for row_idx in range(len(self.df_config)):
            month_val = str(self.df_config.iloc[row_idx].get(self.COL_MONTH, 
                              self.df_config.iloc[row_idx].get("Month", "")))
            
            tipo_val = str(self.df_config.iloc[row_idx].get(self.COL_TIPO, 
                             self.df_config.iloc[row_idx].get("Descripción", ""))) 
            
            act_val = str(self.df_config.iloc[row_idx].get(self.COL_ACTIVIDAD, ""))
            
            avg_val = self.df_config.iloc[row_idx].get(self.COL_AVG, 
                             self.df_config.iloc[row_idx].get("Cantidad", None))
            
            if avg_val is None:
                avg_val = self.avg_map.get((tipo_val, act_val), 0.0)

            self.insert_row_widgets(row_idx, month_val, tipo_val, act_val, float(avg_val))
        
        self.table_widget.resizeColumnsToContents()
        self.table_widget.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)

    def insert_row_widgets(self, row_idx, month_val, tipo_val, act_val, avg_val):
        """Helper para insertar todos los widgets en una fila (nueva o existente)."""
        
        combo_month = QComboBox()
        combo_month.addItems(self.months_list)
        idx_m = combo_month.findText(month_val)
        combo_month.setCurrentIndex(max(0, idx_m))
        self.table_widget.setCellWidget(row_idx, 0, combo_month)

        if tipo_val and tipo_val in self.tipo_list:
            tipo_fijo = tipo_val
        else:
            tipo_fijo = self.tipo_list[0] if self.tipo_list else ""

        item_tipo = QTableWidgetItem(tipo_fijo)
        item_tipo.setFlags(Qt.ItemIsEnabled)  
        item_tipo.setTextAlignment(Qt.AlignCenter) 
        self.table_widget.setItem(row_idx, 1, item_tipo)
        
        current_selected_tipo = tipo_fijo

        combo_act = QComboBox()

        current_act_list = [""] + self.catalog_map.get(current_selected_tipo, [])
        combo_act.addItems(current_act_list)
        
        idx_a = combo_act.findText(act_val) 
        if idx_a == -1:
             idx_a = 0
             act_val = "" 
             
        combo_act.setCurrentIndex(idx_a)
        self.table_widget.setCellWidget(row_idx, 2, combo_act)

        current_avg_val = self.avg_map.get((current_selected_tipo, act_val), 0.0)
        
        item_avg = QTableWidgetItem(str(current_avg_val))
        item_avg.setFlags(Qt.ItemIsEnabled)
        self.table_widget.setItem(row_idx, 3, item_avg) 
        
        combo_act.currentTextChanged.connect(lambda text, r=row_idx: self.handle_activity_change(text, r))

    def handle_tipo_change(self, tipo_text, row):
        """Actualiza el combo de ACTIVIDADES cuando TIPO cambia."""
        try:
            combo_act = self.table_widget.cellWidget(row, 2)
            if not combo_act: 
                return
            combo_act.blockSignals(True)
            combo_act.clear()
            new_act_list = [""] + self.catalog_map.get(tipo_text, [])
            combo_act.addItems(new_act_list)
            combo_act.setCurrentIndex(0)
            combo_act.blockSignals(False)
            self.table_widget.item(row, 3).setText("0.0")
        except Exception as e:
            print(f"Error actualizando combo de actividades en fila {row}: {e}")

    def handle_activity_change(self, activity_text, row):
        """Actualiza el AVG_QUANTITY cuando ACTIVITIES cambia."""
        try:
            tipo_item = self.table_widget.item(row, 1) 
            tipo_val = tipo_item.text() if tipo_item else ""
            avg_item = self.table_widget.item(row, 3)
            avg_val = self.avg_map.get((tipo_val, activity_text), 0.0)
            avg_item.setText(str(avg_val))
        except Exception as e:
            print(f"Error actualizando AVG_QUANTITY en fila {row}: {e}")

    def add_row(self):
        """Añade una fila vacía a la tabla."""
        current_rows = self.table_widget.rowCount()
        self.table_widget.insertRow(current_rows)
        self.insert_row_widgets(current_rows, self.months_list[0], "", "", 0.0)
        self.table_widget.resizeColumnsToContents()
        self.table_widget.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)

    def remove_row(self):
        """Elimina la fila seleccionada actualmente."""
        row = self.table_widget.currentRow()
        if row >= 0:
            self.table_widget.removeRow(row)

    def accept(self):
        """Lee todos los datos de la tabla y actualiza el df_config."""
        new_data = []
        rows = self.table_widget.rowCount()
        
        for r in range(rows):
            month_val = self.table_widget.cellWidget(r, 0).currentText()
            tipo_item = self.table_widget.item(r, 1)
            tipo_val = tipo_item.text() if tipo_item else ""
            act_val = self.table_widget.cellWidget(r, 2).currentText()
            try:
                avg_val = float(self.table_widget.item(r, 3).text())
            except (ValueError, AttributeError):
                avg_val = 0.0

            if not tipo_val and not act_val and avg_val == 0:
                continue

            new_data.append({
                self.COL_MONTH: month_val,
                self.COL_TIPO: tipo_val,
                self.COL_ACTIVIDAD: act_val,
                self.COL_AVG: avg_val
            })

        self.df_config = pd.DataFrame(new_data, columns=[self.COL_MONTH, self.COL_TIPO, self.COL_ACTIVIDAD, self.COL_AVG])
        super().accept()

    def get_updated_df(self):
        """Retorna el DataFrame actualizado al controlador."""
        return self.df_config
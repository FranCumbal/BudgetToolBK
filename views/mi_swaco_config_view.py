#mi_swaco_config_view

import sys
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem,
                             QComboBox, QPushButton, QHBoxLayout, QLabel, QHeaderView, QMessageBox)
from PyQt5.QtCore import Qt
import pandas as pd

class MISwacoConfigDialog(QDialog):
    """
    Diálogo de configuración para el plan manual de MI Swaco (1.02).
    Lógica de "Ofensor": Carga AVG_QUANTITY automáticamente.
    """
    
    # --- 1. Constantes actualizadas ---
    
    # Nombres de columna para MOSTRAR en la tabla y GUARDAR en el config
    COL_MONTH = "MONTH"
    COL_TIPO = "TYPE"
    COL_ACTIVIDAD = "ACTIVITIES"
    COL_AVG = "AVG_QUANTITY"
    # COL_COST eliminado

    # Nombres de las columnas en el archivo 'catalogo_solo_valores.xlsx' (MAESTRO)
    SRC_COL_LINE = "line"
    SRC_COL_TIPO = "TIPO"
    SRC_COL_ACTIVIDAD = "ACTIVIDADES"
    SRC_COL_AVG = "AVG POR ACTIVIDAD" 
    # (Asegúrate que 'AVG POR ACTIVIDAD' es el nombre correcto en tu Excel)
    
    # --- Fin Constantes ---

    def __init__(self, df_config, df_catalog, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configurar Plan Manual (1.02 MI Swaco)")
        self.setWindowModality(Qt.ApplicationModal)
        
        self.df_config = df_config.copy()
        self.df_catalog = df_catalog.copy()

        # Limpiar nombres de columnas del catálogo por si acaso
        if not self.df_catalog.empty:
            self.df_catalog.columns = self.df_catalog.columns.str.strip()

        # 1. Procesar el catálogo para un uso fácil
        self.setup_catalog_maps()

        # 2. Configurar la UI
        self.init_ui()

        # 3. Llenar la tabla con los datos
        self.populate_table()

    def setup_catalog_maps(self):
        """
        Procesa el df_catalog para crear:
        1. self.catalog_map: Un dict para los dropdowns (TYPE -> [ACTIVITIES])
        2. self.avg_map: Un dict para buscar AVG_QUANTITY ((TYPE, ACTIVITY) -> AVG)
        """
        self.catalog_map = {}
        self.avg_map = {} # Nuevo mapa para el AVG
        
        if self.df_catalog.empty:
            print("Advertencia: Catálogo MI Swaco está vacío.")
            return

        try:
            # --- LÓGICA DE FILTRO CORREGIDA (Línea 77) ---
            # Filtramos por la columna TIPO (SRC_COL_TIPO) buscando 'ofensor'
            df_ofensor = self.df_catalog[
                self.df_catalog[self.SRC_COL_TIPO].fillna('').str.lower().str.contains('ofensor', na=False)
            ].copy()
            
            if df_ofensor.empty:
                print("Advertencia: No se encontraron ítems de 'tipo ofensor' en el catálogo MI SWACO.")
                QMessageBox.warning(self, "Catálogo Vacío", 
                    "No se encontraron ítems cuyo 'TIPO' contenga la palabra 'ofensor' en el catálogo MI SWACO.")
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
                f"No se encontró la columna requerida '{e}' en la hoja 'MI SWACO'.\n\n"
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
        
        # --- 4. Formato de 4 Columnas ---
        self.table_cols = [self.COL_MONTH, self.COL_TIPO, self.COL_ACTIVIDAD, self.COL_AVG]
        self.table_widget.setColumnCount(len(self.table_cols))
        self.table_widget.setHorizontalHeaderLabels(self.table_cols)
        
        # Estirar la columna 'ACTIVITIES' (índice 2)
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
        
        # Ya no se editan celdas, se quita handle_cell_change
        # self.table_widget.cellChanged.connect(self.handle_cell_change)

    def populate_table(self):
        """Llena la tabla con los datos del df_config (el plan guardado)."""
        self.table_widget.setRowCount(len(self.df_config))
        
        for row_idx in range(len(self.df_config)):
            
            # Lógica de carga compatible (NUEVO vs VIEJO)
            month_val = str(self.df_config.iloc[row_idx].get(self.COL_MONTH, 
                              self.df_config.iloc[row_idx].get("Month", "")))
            
            tipo_val = str(self.df_config.iloc[row_idx].get(self.COL_TIPO, 
                             self.df_config.iloc[row_idx].get("TIPO", ""))) 
            
            act_val = str(self.df_config.iloc[row_idx].get(self.COL_ACTIVIDAD,
                             self.df_config.iloc[row_idx].get("ACTIVIDADES", "")))
            
            # --- 5. Lógica de carga para AVG ---
            # Si el archivo guardado tiene el AVG, úsalo. Si no, búscalo.
            avg_val = self.df_config.iloc[row_idx].get(self.COL_AVG, 
                             self.df_config.iloc[row_idx].get("AVG POR ACTIVIDAD", None))
            
            if avg_val is None: # Si no estaba en el archivo, buscarlo en el mapa
                avg_val = self.avg_map.get((tipo_val, act_val), 0.0)
            # --- Fin Lógica AVG ---

            self.insert_row_widgets(row_idx, month_val, tipo_val, act_val, avg_val)
        
        self.table_widget.resizeColumnsToContents()
        self.table_widget.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)

    def insert_row_widgets(self, row_idx, month_val, tipo_val, act_val, avg_val):
        """Helper para insertar todos los widgets en una fila (nueva o existente)."""
        
        # --- Col 0: MONTH ---
        combo_month = QComboBox()
        combo_month.addItems(self.months_list)
        idx_m = combo_month.findText(month_val)
        combo_month.setCurrentIndex(max(0, idx_m))
        self.table_widget.setCellWidget(row_idx, 0, combo_month)

        combo_tipo = QComboBox()
        combo_tipo.addItems(self.tipo_list) # Ya no tiene la opción ""
        idx_t = combo_tipo.findText(tipo_val)
        # Si no se encuentra (idx_t = -1), max(0, -1) será 0.
        # Esto selecciona el PRIMER tipo ofensor por defecto.
        combo_tipo.setCurrentIndex(max(0, idx_t)) 
        self.table_widget.setCellWidget(row_idx, 1, combo_tipo)
        
        # --- LÓGICA DE SINCRONIZACIÓN ---
        # Obtenemos el TIPO que *realmente* quedó seleccionado
        current_selected_tipo = combo_tipo.currentText()

        # --- Col 2: ACTIVITIES ---
        combo_act = QComboBox()
        # Construimos la lista de actividades basándonos en el TIPO ya seleccionado
        current_act_list = [""] + self.catalog_map.get(current_selected_tipo, [])
        combo_act.addItems(current_act_list)
        
        # Si la actividad guardada (act_val) no existe en la lista (porque el TIPO cambió),
        # reseteamos al índice 0 (la opción en blanco "").
        idx_a = combo_act.findText(act_val) 
        if idx_a == -1:
             idx_a = 0
             act_val = "" # Reseteamos el valor
             
        combo_act.setCurrentIndex(idx_a)
        self.table_widget.setCellWidget(row_idx, 2, combo_act)

        # --- Col 3: AVG_QUANTITY (Read-Only) ---
        # Recalculamos el AVG basado en el TIPO y ACTIVIDAD que quedaron seleccionados
        current_avg_val = self.avg_map.get((current_selected_tipo, act_val), 0.0)
        
        item_avg = QTableWidgetItem(str(current_avg_val))
        item_avg.setFlags(Qt.ItemIsEnabled)  # Read-only
        self.table_widget.setItem(row_idx, 3, item_avg) # Columna 3
        
        # --- Conectar señales ---
        combo_tipo.currentTextChanged.connect(lambda text, r=row_idx: self.handle_tipo_change(text, r))
        combo_act.currentTextChanged.connect(lambda text, r=row_idx: self.handle_activity_change(text, r))

    def handle_tipo_change(self, tipo_text, row):
        """Actualiza el combo de ACTIVIDADES cuando TIPO cambia."""
        try:
            combo_act = self.table_widget.cellWidget(row, 2) # Col 2 = ACTIVITIES
            if not combo_act: 
                return

            combo_act.blockSignals(True)
            combo_act.clear()
            
            new_act_list = [""] + self.catalog_map.get(tipo_text, [])
            combo_act.addItems(new_act_list)
            
            combo_act.setCurrentIndex(0) # Poner en ""
            combo_act.blockSignals(False)
            
            # Limpiar también el AVG
            self.table_widget.item(row, 3).setText("0.0") # Col 3 = AVG_QUANTITY

        except Exception as e:
            print(f"Error actualizando combo de actividades en fila {row}: {e}")

    def handle_activity_change(self, activity_text, row):
        """Actualiza el AVG_QUANTITY cuando ACTIVITIES cambia."""
        try:
            tipo_val = self.table_widget.cellWidget(row, 1).currentText() # Col 1 = TYPE
            avg_item = self.table_widget.item(row, 3) # Col 3 = AVG_QUANTITY
            
            # Buscar el AVG en el mapa
            avg_val = self.avg_map.get((tipo_val, activity_text), 0.0)
            
            # Poner el valor en la celda (es read-only)
            avg_item.setText(str(avg_val))
            
        except Exception as e:
            print(f"Error actualizando AVG_QUANTITY en fila {row}: {e}")

    def add_row(self):
        """Añade una fila vacía a la tabla."""
        current_rows = self.table_widget.rowCount()
        self.table_widget.insertRow(current_rows)
        # Insertar widgets con valores por defecto
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
            tipo_val = self.table_widget.cellWidget(r, 1).currentText()
            act_val = self.table_widget.cellWidget(r, 2).currentText()
            
            try:
                # Leemos el valor de la celda (que es read-only)
                avg_val = float(self.table_widget.item(r, 3).text())
            except (ValueError, AttributeError):
                avg_val = 0.0

            # No guardar filas vacías
            if not tipo_val and not act_val and avg_val == 0:
                continue

            # --- 7. Guardar en el nuevo formato ---
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
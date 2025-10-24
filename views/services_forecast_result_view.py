from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QHeaderView, QPushButton, QTableWidget, 
    QTableWidgetItem, QHBoxLayout, QMessageBox, QProgressBar
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import pandas as pd


class ForecastCalculationThread(QThread):
    """
    Hilo para calcular el forecast en segundo plano sin bloquear la UI.
    """
    result_ready = pyqtSignal(pd.DataFrame)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, controller, pares_ids):
        super().__init__()
        self.controller = controller
        self.pares_ids = pares_ids
        
    def run(self):
        try:
            dfs = []
            for id_costo, id_dia in self.pares_ids:
                # Llama al método del controlador
                df = None
                if hasattr(self.controller, "generate_forecast_by_path"):
                    df = self.controller.generate_forecast_by_path(id_costo, id_dia)
                elif hasattr(self.controller, "services_report"):
                    df = self.controller.services_report.generate_forecast_by_path(id_costo, id_dia)
                
                if df is not None:
                    df = df.copy()
                    df["ID_COSTO"] = id_costo
                    df["ID_DIA"] = id_dia
                    dfs.append(df)
            
            if dfs:
                df_final = pd.concat(dfs, ignore_index=True)
                self.result_ready.emit(df_final)
            else:
                self.error_occurred.emit("No se pudo generar el forecast para los pares seleccionados.")
                
        except Exception as e:
            self.error_occurred.emit(f"Error al calcular el forecast: {str(e)}")


class ServicesForecastResultView(QDialog):
    """
    Vista para mostrar el resultado del forecast personalizado.
    
    Esta vista toma los pares de IDs (costo, día) seleccionados en la vista principal,
    llama automáticamente al método generate_forecast_by_path del controlador,
    y muestra los resultados en una tabla.
    """
    
    def __init__(self, controller, pares_ids, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Resultado de tu forecast personalizado")
        self.resize(1050, 600)
        self.controller = controller
        self.pares_ids = pares_ids
        self.setup_ui()
        self.calculate_forecast()
    
    def setup_ui(self):
        """Configura la interfaz de usuario."""
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        
        # Título informativo
        title_label = QLabel(f"Calculando forecast para {len(self.pares_ids)} combinación(es) de parámetros...")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px; margin: 10px;")
        self.layout.addWidget(title_label)
        
        # Barra de progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Modo indeterminado
        self.layout.addWidget(self.progress_bar)
        
        # Tabla para mostrar resultados
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.layout.addWidget(self.table)
        
        # Etiqueta para mostrar el total de FORECAST_COST
        self.total_label = QLabel("")
        self.total_label.setStyleSheet("font-weight: bold; font-size: 14px; margin: 10px; color: #2E8B57;")
        self.layout.addWidget(self.total_label)

        # Nueva etiqueta para mostrar las anotaciones (cost_value y day_value)
        self.notes_label = QLabel("")
        self.notes_label.setStyleSheet("font-style: italic; font-size: 12px; margin: 5px 10px; color: #555;")
        self.layout.addWidget(self.notes_label)

        # Botones
        button_layout = QHBoxLayout()
        
        self.close_btn = QPushButton("Cerrar")
        self.close_btn.clicked.connect(self.close)
        button_layout.addWidget(self.close_btn)
        
        self.layout.addLayout(button_layout)
    
    def calculate_forecast(self):
        """Inicia el cálculo del forecast en un hilo separado."""
        self.calculation_thread = ForecastCalculationThread(self.controller, self.pares_ids)
        self.calculation_thread.result_ready.connect(self.on_calculation_complete)
        self.calculation_thread.error_occurred.connect(self.on_calculation_error)
        self.calculation_thread.start()
    
    def on_calculation_complete(self, df_result):
        """Maneja la finalización exitosa del cálculo."""
        self.progress_bar.hide()
        self.df_result = df_result
        self.show_dataframe(df_result)
        # Actualizar título
        title_label = self.layout.itemAt(0).widget()
        title_label.setText(f"Forecast calculado: {len(df_result)} filas de datos")
    
    def on_calculation_error(self, error_message):
        """Maneja errores durante el cálculo."""
        self.progress_bar.hide()
        QMessageBox.critical(self, "Error", error_message)
        
        # Actualizar título
        title_label = self.layout.itemAt(0).widget()
        title_label.setText("Error al calcular el forecast")
    
    def show_dataframe(self, df):
        """Muestra el DataFrame en la tabla."""
        # Filtrar columnas para excluir las columnas de ID
        columns_to_show = [col for col in df.columns if col not in ["ID_COSTO", "ID_DIA"]]
        df_display = df[columns_to_show]
        
        self.table.setRowCount(len(df_display))
        self.table.setColumnCount(len(df_display.columns))
        self.table.setHorizontalHeaderLabels([str(col) for col in df_display.columns])
        
        # Llenar la tabla con los datos
        for i, row in df_display.iterrows():
            for j, col in enumerate(df_display.columns):
                value = row[col]
                
                # Formatear números para mejor legibilidad
                if isinstance(value, (int, float)) and col in ["FORECAST_COST"]:
                    item_text = f"${value:,.2f}"
                elif isinstance(value, (int, float)) and col in ["PLANNED_ACTIVITIES"]:
                    item_text = f"{int(value)}"
                elif isinstance(value, (int, float)) and col in ["EXECUTED_ACTIVITIES"]:
                    item_text = f"{int(value)}"
                elif isinstance(value, (int, float)) and col in ["CUMULATIVE_FORECAST"]:
                    item_text = f"${value:,.2f}"
                elif isinstance(value, (int, float)):
                    item_text = f"{value:.2f}"
                else:
                    item_text = str(value)
                
                item = QTableWidgetItem(item_text)
                
                # Resaltar columnas importantes
                if col in ["FORECAST_COST"]:
                    item.setBackground(Qt.lightGray)
                
                self.table.setItem(i, j, item)
        
        # Ajustar el ancho de las columnas
        self.table.resizeColumnsToContents()
        
        # Calcular y mostrar el total de FORECAST_COST
        if "CUMULATIVE_FORECAST" in df_display.columns:
            total_commulative_forecast = df_display["CUMULATIVE_FORECAST"].iloc[-1]
            self.total_label.setText(f"Total w/ Forecast: ${total_commulative_forecast:,.2f}")
        else:
            self.total_label.setText("")
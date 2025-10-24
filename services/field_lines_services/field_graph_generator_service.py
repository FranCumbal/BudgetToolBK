from matplotlib.widgets import Button
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
from matplotlib.patches import FancyBboxPatch

class FieldGraphGeneratorService:
    """
    Servicio para generar un gráfico de pronóstico de campo complejo usando Matplotlib.

    Combina múltiples fuentes de datos para visualizar costos (presupuesto, pronóstico, real)
    y actividades (planeadas, ejecutadas, programadas) en un solo gráfico interactivo
    con ejes dinámicos, anotaciones y cuadros de información.
    """
    def __init__(self):
        """
        Inicializa el servicio, estableciendo el estado de visibilidad inicial
        para elementos interactivos del gráfico, como la línea de costo inicial.
        """
        self.initial_cost_visible = True

    def generate_field_forecast_graph(self, title: str, **data_sources):
        """
        Genera y devuelve una figura de Matplotlib con el gráfico de pronóstico completo.

        Args:
            title (str): El título que se mostrará en el gráfico.
            **data_sources (dict): Un diccionario de DataFrames de pandas que contienen
                                   los datos a graficar. Las claves esperadas incluyen:
                                   'budget', 'forecast', 'real_cost_accumulated',
                                   'executed_activities', 'planned_activities', etc.

        Returns:
            matplotlib.figure.Figure: La figura de Matplotlib que contiene el gráfico generado,
                                      lista para ser mostrada en una interfaz de usuario.
        """
        forecast_color = '#8e44ad'
        budget_color = '#008FF6'
        real_cost_color = '#27ae60'
        text_color = '#2c3e50'
        
        # 1. Preparar meses base
        months = ['january', 'february', 'march', 'april', 'may', 'june', 
                'july', 'august', 'september', 'october', 'november', 'december']
        all_months = pd.DataFrame({'MONTH': months})
        
        # 2. Función para procesar DataFrames
        def prepare_df(df, rename_dict=None):
            if df is None or not isinstance(df, pd.DataFrame):
                return all_months.assign(VALUE=0)  # DataFrame vacío seguro
            if rename_dict:
                df = df.rename(columns=rename_dict)
            
            df.columns = df.columns.str.upper()
            return all_months.merge(df, on='MONTH', how='left').fillna(0)

        # 3. Procesar DataFrames esenciales con nombres esperados
        df_budget = prepare_df(data_sources.get("budget"))
        df_forecast = prepare_df(data_sources.get("forecast"))
        df_real_cost_accumulated = prepare_df(
            data_sources.get("real_cost_accumulated"), 
            rename_dict={"TotalAccumulatedCost": "Actual Cost"}
        )

        non_zero_indices = df_real_cost_accumulated[df_real_cost_accumulated["ACTUAL COST"] != 0].index
        df_executed_activities = prepare_df(data_sources.get("executed_activities"))
        df_planned_activities = prepare_df(data_sources.get("planned_activities"))
        
        # Crear diccionario base de series
        graph_data = {
            "BUDGET": df_budget,
            "FORECAST": df_forecast,
            "ACTUAL COST": df_real_cost_accumulated,
            "EXECUTED ACTIVITIES": df_executed_activities,
            "PLANNED ACTIVITIES": df_planned_activities,
        }
        # Procesar el valor inicial planeado si está disponible
        initial_planned_cost = data_sources.get("initial_approved_cost")
        if initial_planned_cost is not None:
            graph_data["INITIAL APPROVED COST"] = prepare_df(
                initial_planned_cost, 
                rename_dict={"VALUE": "VALUE"}
            )
        
        # Incluir cualquier otro DataFrame adicional (ej. barras extra)
        for key, df in data_sources.items():
            if key in ["budget", "forecast", "real_cost_accumulated", "executed_activities", "planned_activities"]:
                continue  # Ya están procesados
            graph_data[key.upper().replace("_", " ")] = prepare_df(df)
        
        # Obtener índices de meses
        #current_month_str = datetime.now().strftime("%B").upper()
        non_zero_indices = df_real_cost_accumulated[df_real_cost_accumulated["ACTUAL COST"] != 0].index
        last_valid_idx = non_zero_indices[-1] if len(non_zero_indices) > 0 else 0
        current_idx = last_valid_idx
        closing_idx = max(0, current_idx - 1)
        next_idx = min(11, current_idx + 1)
        
        # =========================================================================
        # 1. CALCULAR MÁXIMOS PARA ESCALA DINÁMICA
        # =========================================================================
        # Calcular valores máximos entre todas las series de costos
        max_budget = df_budget['BUDGET'].max()
        max_forecast = df_forecast['FORECAST'].max()
        max_actual = df_real_cost_accumulated['ACTUAL COST'].max()
        
        # Encontrar el máximo global (con un mínimo de 100,000 para buena visualización)
        global_max = max(max_budget, max_forecast, max_actual, 100_000)
        
        # Crear figura
        fig, ax1 = plt.subplots(figsize=(12, 7))
        
        # =========================================================================
        # 2. CONFIGURACIÓN DE EJES DINÁMICOS
        # =========================================================================
        # Eje Y de costos con escala dinámica
        ax1.set_xlabel('Month')
        ax1.set_ylabel('Cost (MUSD)', color=budget_color)
        
        # Establecer límites con margen del 20%
        ax1.set_ylim(0, global_max * 1.2)
        
        # Crear ticks dinámicos con mejor resolución para valores pequeños
        if global_max <= 100_000:  # Menor a 0.1M
            tick_step = 25_000  # Cada 0.05M para mejor visualización
        elif global_max < 500_000:  # Entre 0.1M y 0.5M
            tick_step = 100_000  # Cada 0.1M
        else:  # Mayor a 0.5M
            tick_step = 500_000  # Cada 0.5M
        y_ticks = np.arange(0, global_max * 1.2 + tick_step, tick_step)
        ax1.set_yticks(y_ticks)
        
        # Formateador para mostrar en millones
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x/1_000_000:.2f}'))
        ax1.tick_params(axis='y', labelcolor=budget_color)
        
        # Calcular el max de actividades para dinamización del grafico
        max_activities = max(
            df_planned_activities['PLANNED ACTIVITIES'].max(),
            df_executed_activities['EXECUTED ACTIVITIES'].max()
        )

        # Si hay actividades programadas, incluirlas en el cálculo
        if "scheduled_executed_activities" in data_sources:
            df_scheduled = prepare_df(data_sources.get("scheduled_executed_activities"))
            max_activities = max(max_activities, df_scheduled['SCHEDULED ACTIVITIES'].max())

        # Ajuste especial para casos con muchas actividades (175+)
        if max_activities >= 175:
            # Para casos extremos, usar escala más comprimida
            y2_max = max(50, max_activities * 5.3)  # Factor más bajo para comprimir
        else:
            y2_max = max(50, max_activities * 3)

        # Eje secundario para actividades
        ax2 = ax1.twinx()
        ax2.set_ylabel('# Activities', color=forecast_color, fontsize=12)
        ax2.set_ylim(0, y2_max)
        ax2.tick_params(axis='y', labelcolor=forecast_color)
        
        # =========================================================================
        # 3. GRAFICAR DATOS (AJUSTADO A MILLONES)
        # =========================================================================
        # Valores de X
        x_values = np.arange(1, 13)
        
        # Budget line
        ax1.plot(x_values, df_budget['BUDGET'], label='Planned Cost', color=budget_color, 
                linestyle='-', marker='x', linewidth=1)
        
        # Forecast line
        ax1.plot(x_values, df_forecast['FORECAST'], label='Forecast EOY', color=forecast_color, 
                linestyle='--', marker='.')
        
        # Encuentra índices donde ACTUAL COST no es cero
        non_zero_indices = df_real_cost_accumulated[df_real_cost_accumulated['ACTUAL COST'] != 0].index
        last_valid_idx = None
        def annotate_point(ax, x, y, text, color, offset=(20, 0)):
            ax.annotate(f"{text:.2f}M",  # Mostrar en millones
                    xy=(x, y), 
                    xytext=offset,
                    textcoords='offset points', 
                    ha='center', 
                    color=color,
                    fontsize=9,
                    fontweight='bold',
                    arrowprops=dict(arrowstyle='->', color=color))
        
        if len(non_zero_indices) > 0:
            last_valid_idx = non_zero_indices[-1]
            
            # Grafica solo hasta el último valor no nulo (inclusive)
            ax1.plot(
                x_values[:last_valid_idx + 1],
                df_real_cost_accumulated['ACTUAL COST'].iloc[:last_valid_idx + 1],
                label='Actual Cost',
                color=real_cost_color,
                marker='o',
                linestyle='-',
                linewidth=1
            )
            annotate_point(ax1, last_valid_idx + 1, 
               df_real_cost_accumulated['ACTUAL COST'].iloc[last_valid_idx], 
               df_real_cost_accumulated['ACTUAL COST'].iloc[last_valid_idx]/1_000_000, 
               real_cost_color, offset=(-12, 10))
        else:
            print("No hay valores no-cero para graficar")
        
        # Initial Planned Cost line (con interactividad)
        self.initial_line = None  # Referencia para la línea
        if "INITIAL APPROVED COST" in graph_data:
            df_initial_planned_cost = graph_data["INITIAL APPROVED COST"]
            self.initial_line = ax1.plot(
                x_values, 
                df_initial_planned_cost['VALUE'],
                label='Initial Approved Cost', 
                color='red', 
                linestyle='-', 
                linewidth=1,
                visible=self.initial_cost_visible  # Estado inicial
            )[0]  # Guardar referencia al objeto Line2D
            
            # Anotación solo si está visible
            if self.initial_cost_visible:
                last_value = df_initial_planned_cost['VALUE'].iloc[-1]
                self.initial_annotation = ax1.annotate(
                    f"{last_value/1_000_000:.2f}M", 
                    xy=(12, last_value),
                    xytext=(10, -5), 
                    textcoords='offset points',
                    ha='left',
                    color='red',
                    fontsize=9,
                    fontweight='bold'
                )
            else:
                self.initial_annotation = None
        # =========================================================================
        # 4. ANOTACIONES (AJUSTADAS A MILLONES)
        # =========================================================================
        
        if current_idx < len(df_forecast):
            forecast_val = df_forecast['FORECAST'].iloc[current_idx + 1]  
            budget_val = df_budget['BUDGET'].iloc[current_idx + 1]
            
            # Determinar offsets para evitar superposición
            if budget_val >= forecast_val:
                forecast_offset = (20, -5)
                budget_offset = (20, 5)
            else:
                forecast_offset = (20, 5)
                budget_offset = (20, -5)

            # Anotar forecast (ahora usando next_idx + 1 para la posición en X)pr
            annotate_point(ax1, current_idx + 2, 
                        forecast_val, 
                        forecast_val / 1_000_000, 
                        forecast_color, offset=forecast_offset)

            # Anotar budget
            annotate_point(ax1, current_idx + 2, 
                        budget_val, 
                        budget_val / 1_000_000, 
                        budget_color, offset=budget_offset)

        # Anotaciones finales (último punto)
        forecast_final = df_forecast['FORECAST'].iloc[-1]
        budget_final = df_budget['BUDGET'].iloc[-1]

        # Determinar offsets finales
        if budget_final >= forecast_final:
            forecast_offset = (10, -10)
            budget_offset = (10, 10)
        else:
            forecast_offset = (10, 10)
            budget_offset = (10, -10)

        # Usar índice final (por ejemplo, 12) o ajustarlo según el contexto
        final_idx = 12

        # Anotar forecast final
        annotate_point(ax1, final_idx, 
                    forecast_final, 
                    forecast_final / 1_000_000, 
                    forecast_color, offset=forecast_offset)

        # Anotar budget final
        annotate_point(ax1, final_idx, 
                    budget_final, 
                    budget_final / 1_000_000, 
                    budget_color, offset=budget_offset)

        # 5. Barras
        # --- MODIFICACIÓN: Definir tamaños de fuente para las etiquetas ---
        normal_fontsize = 8
        reduced_fontsize = 6.5 # Tamaño más pequeño para valores >= 300

        # --- Anchos y un espacio (gap) para evitar colisiones ---
        base_width = 0.25
        increased_width = 0.30
        gap = 0.03

        x = np.arange(1, 13)
        # Verificar si tenemos datos de actividades programadas
        has_scheduled = "scheduled_executed_activities" in data_sources
        if has_scheduled:
            df_scheduled = prepare_df(data_sources.get("scheduled_executed_activities"))
            df_scheduled_display = df_scheduled.copy()
            df_scheduled_display.loc[:current_idx, 'SCHEDULED ACTIVITIES'] = np.nan

        # Procesar datos mensuales (el código de preparación no cambia)
        df_scheduled_monthly = None
        if "scheduled_executed_activities_monthly" in data_sources:
            df_scheduled_monthly = prepare_df(data_sources.get("scheduled_executed_activities_monthly"))

        df_executed_monthly = None
        if "executed_activities_monthly" in data_sources:
            df_executed_monthly = prepare_df(data_sources.get("executed_activities_monthly"))
            df_executed_monthly.loc[current_idx + 1:, 'EXECUTED ACTIVITIES'] = np.nan

        df_planned_monthly = None
        if "planned_activities_monthly" in data_sources:
            df_planned_monthly = prepare_df(data_sources.get("planned_activities_monthly"))

        df_executed_activities_display = df_executed_activities.copy()
        df_executed_activities_display.loc[current_idx + 1:, 'EXECUTED ACTIVITIES'] = np.nan

        labels_added = {"planned": False, "executed": False, "scheduled": False}

        for month_idx in range(12):
            month_x = month_idx + 1
            
            # Obtener valores para este mes
            has_scheduled_this_month = False
            scheduled_value = 0
            if has_scheduled:
                scheduled_value = df_scheduled_display['SCHEDULED ACTIVITIES'].iloc[month_idx]
                has_scheduled_this_month = not np.isnan(scheduled_value) and scheduled_value > 0
            
            planned_value = df_planned_activities['PLANNED ACTIVITIES'].iloc[month_idx]
            executed_value = df_executed_activities_display['EXECUTED ACTIVITIES'].iloc[month_idx]

            # --- LÓGICA DE POSICIONAMIENTO PRECISO ---

            # 1. Determinar el ancho de cada barra ANTES de calcular su posición
            planned_bar_width = increased_width if planned_value > 100 else base_width
            
            is_executed_valid = not np.isnan(executed_value) and executed_value >= 0
            executed_bar_width = increased_width if is_executed_valid and executed_value > 100 else base_width
            
            scheduled_bar_width = increased_width if has_scheduled_this_month and scheduled_value > 100 else base_width

            # 2. Calcular la posición X de cada barra basado en los anchos finales
            x_planned, x_scheduled, x_executed = None, None, None

            if has_scheduled_this_month:
                x_scheduled = month_x
                x_planned = month_x - (scheduled_bar_width / 2) - gap - (planned_bar_width / 2)
                x_executed = month_x + (scheduled_bar_width / 2) + gap + (executed_bar_width / 2)
            else:
                x_planned = month_x - (gap / 2) - (planned_bar_width / 2)
                x_executed = month_x + (gap / 2) + (executed_bar_width / 2)

            # 3. Dibujar las barras en sus posiciones calculadas
            if planned_value > 0:
                ax2.bar(x_planned, planned_value, planned_bar_width,
                        color=budget_color, alpha=0.7,
                        label='Planned Activities' if not labels_added["planned"] else "")
                labels_added["planned"] = True

            if is_executed_valid:
                ax2.bar(x_executed, executed_value, executed_bar_width,
                        color=real_cost_color, alpha=0.7,
                        label='Executed Activities' if not labels_added["executed"] else "")
                labels_added["executed"] = True

            if has_scheduled_this_month:
                ax2.bar(x_scheduled, scheduled_value, scheduled_bar_width,
                        color=forecast_color, alpha=0.7,
                        label='Scheduled Activities' if not labels_added["scheduled"] else "")
                labels_added["scheduled"] = True

            # --- Lógica de Etiquetas (Usa las posiciones X ya calculadas) ---
            y_offset = y2_max * 0.01

            # Etiqueta para 'planned'
            if planned_value > 0 and x_planned is not None:
                # MODIFICACIÓN: Determinar tamaño de fuente dinámicamente
                font_size_planned = reduced_fontsize if planned_value >= 250 else normal_fontsize
                ax2.text(x_planned, planned_value + y_offset, f"{int(planned_value)}",
                        ha='center', fontsize=font_size_planned, color=text_color) # <-- Usar variable
                if df_planned_monthly is not None:
                    planned_monthly = df_planned_monthly['PLANNED ACTIVITIES'].iloc[month_idx]
                    if not np.isnan(planned_monthly):
                        ax2.text(x_planned, planned_value / 2, f"{int(planned_monthly)}",
                                ha='center', va='center', fontsize=8, color='white', fontweight='semibold')

            # Etiqueta para 'executed'
            if is_executed_valid and x_executed is not None:
                # MODIFICACIÓN: Determinar tamaño de fuente dinámicamente
                font_size_executed = reduced_fontsize if executed_value >= 250 else normal_fontsize
                ax2.text(x_executed, executed_value + y_offset, f"{int(executed_value)}",
                        ha='center', fontsize=font_size_executed, color=text_color) # <-- Usar variable
                if df_executed_monthly is not None:
                    monthly_activities = df_executed_monthly['EXECUTED ACTIVITIES'].iloc[month_idx]
                    if not np.isnan(monthly_activities):
                        ax2.text(x_executed, executed_value / 2, f"{int(monthly_activities)}",
                                ha='center', va='center', fontsize=8, color='white', fontweight='semibold')
            
            # Etiqueta para 'scheduled'
            if has_scheduled_this_month and x_scheduled is not None:
                # MODIFICACIÓN: Determinar tamaño de fuente dinámicamente
                font_size_scheduled = reduced_fontsize if scheduled_value >= 250 else normal_fontsize
                ax2.text(x_scheduled, scheduled_value + y_offset, f"{int(scheduled_value)}",
                        ha='center', fontsize=font_size_scheduled, color=text_color) # <-- Usar variable
                if df_scheduled_monthly is not None:
                    scheduled_monthly = df_scheduled_monthly['SCHEDULED ACTIVITIES'].iloc[month_idx]
                    if not np.isnan(scheduled_monthly):
                        ax2.text(x_scheduled, scheduled_value / 2, f"{int(scheduled_monthly)}",
                                ha='center', va='center', fontsize=8, color='white', fontweight='semibold')
        # =========================================================================
        # 6. CUADRO DE INFORMACIÓN (AJUSTADO A MILLONES)
        # =========================================================================
        closing_month_name = all_months['MONTH'].iloc[current_idx]
        current_month_name = all_months['MONTH'].iloc[current_idx + 1]
        next_month_name = all_months['MONTH'].iloc[next_idx + 1]
        
        current_real = df_real_cost_accumulated['ACTUAL COST'].iloc[current_idx] / 1_000_000
        current_fc = df_forecast['FORECAST'].iloc[current_idx + 1] / 1_000_000
        next_fc = df_forecast['FORECAST'].iloc[next_idx + 2] / 1_000_000
        eoy_fc = df_forecast['FORECAST'].iloc[-1] / 1_000_000
        eoy_budget = df_budget['BUDGET'].iloc[-1] / 1_000_000
        delta = eoy_fc - eoy_budget
        delta_sign = "+" if delta >= 0 else "-"
        delta_text = f"{delta_sign}{abs(delta):.2f} M"
        
        info_text = (
            f"{closing_month_name.capitalize()} (closing): {current_real:.2f} M\n"
            f"===== Forecast =====\n"
            f"{current_month_name.capitalize()}: {current_fc:.2f} M\n"
            f"{next_month_name.capitalize()}: {next_fc:.2f} M\n"
            f"=== Year-End Summary: ===\n"
            f"Forecast: {eoy_fc:.2f} M\n"
            f"Planned: {eoy_budget:.2f} M\n"
            f"Difference: {delta_text}"
        )
        
        fancy_box = FancyBboxPatch((0.05, 0.68), 0.32, 0.30, boxstyle="round,pad=0.02", 
                                fc=budget_color, ec="none", alpha=0.8, transform=ax1.transAxes)
        ax1.add_patch(fancy_box)
        ax1.text(0.05 + 0.32/2, 0.68 + 0.30/2, info_text, ha='center', va='center', 
                transform=ax1.transAxes, color='white', fontsize=11)#, fontweight='bold' 

        # ================= NUEVO CUADRO INFO CPI/SPI =====================
        cpi_spi_info = data_sources.get("cpi_spi_info")
        if cpi_spi_info and cpi_spi_info["current_month"] is not None:
            tomato_color = "#F7492A"
            # Cuadro más pequeño y letras más pequeñas
            info_text_2 = (
                f"CPI {cpi_spi_info['current_month']}: {cpi_spi_info['cpi_current']:.2f}\n"
                f"SPI {cpi_spi_info['current_month']}: {cpi_spi_info['spi_current']:.2f}\n"
                f"CPI {cpi_spi_info['next_month']}: {cpi_spi_info['cpi_next']:.2f}\n"
                f"SPI {cpi_spi_info['next_month']}: {cpi_spi_info['spi_next']:.2f}"
            )
            # Cambia tamaño y posición del cuadro (height reducido)
            # Mover el cuadro más arriba cambiando la coordenada Y (por ejemplo, de 0.76 a 0.82)
            fancy_box_2 = FancyBboxPatch((0.42, 0.84), 0.16, 0.13, boxstyle="round,pad=0.02",
                                         fc=tomato_color, ec="none", alpha=0.8, transform=ax1.transAxes)
            ax1.add_patch(fancy_box_2)
            ax1.text(0.42 + 0.16/2, 0.84 + 0.13/2, info_text_2, ha='center', va='center',
                     transform=ax1.transAxes, color='white', fontsize=9, fontweight='bold')
        # =========================================================================
        # 7. CONFIGURACIÓN FINAL
        # =========================================================================
        ax1.set_xticks(x)
        ax1.set_xticklabels([month[:3] for month in months], fontsize=10, ha='center')
        ax1.grid(True, linestyle='--', alpha=0.6)
        
        # Leyendas combinadas
        lines, labels = ax1.get_legend_handles_labels()
        bars, bar_labels = ax2.get_legend_handles_labels()

        # Ajustar ncol según si hay actividades programadas
        # Leyendas por separado
        lines, line_labels = ax1.get_legend_handles_labels()
        bars, bar_labels = ax2.get_legend_handles_labels()

        # Leyenda de líneas
        legend1 = ax1.legend(lines, line_labels, 
                            loc='upper center', 
                            bbox_to_anchor=(0.5, -0.12), 
                            ncol=3, 
                            fontsize=9)

        # Leyenda de barras (debajo de la de líneas)
        legend2 = ax2.legend(bars, bar_labels, 
                            loc='upper center', 
                            bbox_to_anchor=(0.5, -0.21), 
                            ncol=3, 
                            fontsize=9)

        # Añadir ambas leyendas al gráfico
        ax1.add_artist(legend1)
        
        plt.title(title, fontsize=14, fontweight='bold', pad=20)
        plt.tight_layout()
        if "INITIAL APPROVED COST" in graph_data:
           # Crear eje para el botón (posición más compacta)
            ax_button = plt.axes([0.85, 0.02, 0.12, 0.04])  # Tamaño más pequeño y posición ajustada

            # Crear el botón con un diseño compacto
            self.toggle_button = Button(
                ax_button, 
                'Hide Approved' if self.initial_cost_visible else 'Show Approved',
                color="#3d5db6",  # Fondo gris claro
                hovercolor="#082864"  # Fondo más oscuro al pasar el mouse
            )

            # Personalizar el texto del botón
            self.toggle_button.label.set_fontsize(9)  # Tamaño de fuente más pequeño
            self.toggle_button.label.set_fontweight('bold')  # Negrita
            self.toggle_button.label.set_color("#FFFFFF")  # Texto negro

            # Conectar función de callback
            self.toggle_button.on_clicked(self.toggle_initial_cost)

        return fig
        
    def toggle_initial_cost(self, event):
        """Función para alternar la visibilidad del costo inicial"""
        # Cambiar estado
        self.initial_cost_visible = not self.initial_cost_visible
        
        # Actualizar línea
        self.initial_line.set_visible(self.initial_cost_visible)
        
        # Actualizar anotación
        if self.initial_cost_visible:
            # Recuperar el último valor (necesitas acceso a los datos aquí)
            last_value = self.initial_line.get_ydata()[-1]
            self.initial_annotation = self.initial_line.axes.annotate(
                f"{last_value/1_000_000:.2f}M", 
                xy=(12, last_value),
                xytext=(10, -5), 
                textcoords='offset points',
                ha='left',
                color='red',
                fontsize=9,
                fontweight='bold'
            )
        elif hasattr(self, 'initial_annotation') and self.initial_annotation:
            self.initial_annotation.remove()
            self.initial_annotation = None
        
        # Actualizar texto del botón
        self.toggle_button.label.set_text(
            'Hide Approved' if self.initial_cost_visible else 'Show Approved'
        )
        
        # Redibujar el canvas
        plt.draw()
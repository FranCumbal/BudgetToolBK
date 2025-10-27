import pandas as pd
from datetime import datetime
from utils.dates import normalize_month_names, get_month_number, get_month_name

class PlanAnualActividades1:
    """
    Clase encargada de gestionar el plan anual de actividades. Esta clase permite:
    - Cargar los datos desde un archivo Excel predefinido usando el `DataLoader`.
    - Obtener el total anual planificado por tipo de actividad.
    - Calcular las actividades ejecutadas hasta el momento, integrando datos históricos.
    - Distribuir las actividades restantes de forma uniforme en los meses futuros.
    - Integrar datos desde CDF para meses actuales y próximos.
    - Generar un DataFrame final con la planificación mensual ajustada por tipo de actividad.

    Atributos:
        data_loader (DataLoader): Encargado de cargar los datos desde Excel o fuentes externas.
        plan_path (str): Ruta del archivo Excel que contiene el plan.
        sheet_name (str): Hoja del archivo Excel a utilizar.
        plan_df (pd.DataFrame): DataFrame con el plan cargado y estructurado.
        cdf_df (pd.DataFrame): DataFrame de actividades CDF cargado automáticamente.
    """

    def __init__(self, data_loader, plan_path: str, sheet_name="ForecastedPlan"+str(datetime.now().year)): # Esto es provisional, tratando de arreglar las cosas
        self.data_loader = data_loader
        self.plan_path = plan_path
        print("En el plan")
        print(sheet_name)
        print(plan_path, "bro2")
        self.sheet_name = sheet_name
        self.plan_df = self.data_loader.load_plan_actividades_from_excel(plan_path, sheet_name)

        # 🆕 Cargar CDF automáticamente
        try:
            self.cdf_df = self.data_loader.load_cdf_activities(self.data_loader, datetime.now().year)
            print("✅ CDF cargado correctamente en PlanAnualActividades.")
        except Exception as e:
            self.cdf_df = None
            print(f"⚠️ No se pudo cargar CDF al iniciar PlanAnualActividades: {e}")

    def get_total_por_tipo(self):
        """
        Retorna un diccionario con el total planificado por cada tipo de actividad.
        """
        return {
            row['Tipo de Actividad']: int(row['Total'])
            for _, row in self.plan_df.iterrows() if row['Tipo de Actividad'] != 'Total'
        }

    def get_done_por_tipo(self, year=2025):
        """
        Calcula la cantidad de actividades ejecutadas por tipo y mes en base al presupuesto ejecutado.

        Args:
            year (int): Año de referencia para consultar las actividades ejecutadas.

        Returns:
            dict: Diccionario con estructura {tipo: {mes: cantidad}}.
        """
        df = self.data_loader.load_budget_data_per_year(year)
        df['TYPE'] = df['TYPE'].fillna('')
        df['MONTH'] = df['MONTH'].apply(lambda m: str(m).strip())
        df['MONTH'] = normalize_month_names(df['MONTH'])

        done_dict = {}
        for _, row in df.iterrows():
            tipo = row['TYPE']
            mes = row['MONTH']
            if tipo and mes:
                if tipo not in done_dict:
                    done_dict[tipo] = {}
                if mes not in done_dict[tipo]:
                    done_dict[tipo][mes] = 0
                done_dict[tipo][mes] += 1

        print(f"📦 Actividades hechas por tipo y mes: {done_dict}")
        return done_dict

    def calcular_distribucion_por_tipo(self, year=datetime.now().year):
        """
        Calcula la distribución mensual por tipo de actividad, considerando:
        - Actividades ya ejecutadas (histórico).
        - Actividades registradas desde CDF.
        - Actividades restantes distribuidas uniformemente.

        Args:
            year (int): Año en curso.

        Returns:
            pd.DataFrame: Plan ajustado con la distribución por mes.
        """
        distribucion_df = self.plan_df.copy()
        print("AHORA?")
        print(distribucion_df)
        done_counts = self.get_done_por_tipo(year)

        columnas_meses = [c for c in distribucion_df.columns if c not in ['Tipo de Actividad', 'Total', 'No.']]
        mes_actual = datetime.now().month
        mes_siguiente = mes_actual + 1 if mes_actual < 12 else 12

        # 🆕 Usar el CDF interno
        cdf_counts_by_month = {}
        if self.cdf_df is not None:
            grouped = self.data_loader.group_cdf_by_month(self.cdf_df, col='activity_type')
            for _, row in grouped.iterrows():
                mes = row['month_num']
                lista = row['activity_type']
                for tipo in set(lista):
                    if tipo not in cdf_counts_by_month:
                        cdf_counts_by_month[tipo] = {}
                    cdf_counts_by_month[tipo][mes] = lista.count(tipo)
        for idx, row in distribucion_df.iterrows():
            if row['Tipo de Actividad'] == 'TOTAL':
                continue

            tipo_codigo = row['No.']
            tipo_nombre = row['Tipo de Actividad']
            total_planificado = int(row['Total'])

            ejecutado_por_mes = done_counts.get(tipo_codigo, done_counts.get(tipo_nombre, {}))

            for mes_nombre in columnas_meses:
                valor = ejecutado_por_mes.get(mes_nombre, 0)
                distribucion_df.at[idx, mes_nombre] = valor

            for mes_num in [mes_actual, mes_siguiente]:
                mes_nombre = get_month_name(mes_num)
                valor_cdf = cdf_counts_by_month.get(tipo_codigo, {}).get(mes_num, 0)
                celda = distribucion_df.at[idx, mes_nombre]
                if pd.isna(celda) or celda == 0:
                    distribucion_df.at[idx, mes_nombre] = valor_cdf

            definidos = sum(
                int(distribucion_df.at[idx, mes]) for mes in columnas_meses if pd.notna(distribucion_df.at[idx, mes])
            )
            faltante = max(total_planificado - definidos, 0)

            meses_disponibles = [
                mes for mes in columnas_meses
                if get_month_number(mes) > mes_siguiente and (pd.isna(distribucion_df.at[idx, mes]) or distribucion_df.at[idx, mes] == 0)
            ]

            if faltante > 0 and meses_disponibles:
                base = faltante // len(meses_disponibles)
                extra = faltante % len(meses_disponibles)
                for i, mes in enumerate(meses_disponibles):
                    distribucion_df.at[idx, mes] = base + (1 if i < extra else 0)

        totales = distribucion_df[columnas_meses].drop(index=distribucion_df.shape[0]-1).sum(numeric_only=True)
        distribucion_df.loc[distribucion_df['Tipo de Actividad'] == 'TOTAL', columnas_meses] = totales.values
        distribucion_df.loc[distribucion_df['Tipo de Actividad'] == 'TOTAL', 'Total'] = int(totales.sum())

        print("✅ Distribución final generada.")
        print(distribucion_df)
        return distribucion_df
    
    def calcular_distribucion_hibrida(self, year=datetime.now().year, saved_excel_path=None, saved_sheet_name=None):
        """
        Versión híbrida que preserva valores guardados manualmente y aplica distribución automática 
        solo en celdas vacías o cero.
        
        Args:
            year (int): Año en curso.
            saved_excel_path (str): Ruta del archivo Excel guardado.
            saved_sheet_name (str): Nombre de la hoja Excel guardada.
            
        Returns:
            pd.DataFrame: Plan ajustado con valores guardados preservados y distribución automática en celdas vacías.
        """
        # 1. Generar la distribución automática base
        distribucion_automatica = self.calcular_distribucion_por_tipo(year)
        
        # 2. Intentar cargar valores guardados
        valores_guardados = None
        if saved_excel_path and saved_sheet_name:
            try:
                valores_guardados = pd.read_excel(saved_excel_path, sheet_name=saved_sheet_name)
                print(f"✅ Valores guardados cargados desde {saved_sheet_name}")
            except Exception as e:
                print(f"⚠️ No se pudieron cargar valores guardados: {e}")
                print("📋 Usando solo distribución automática")
        
        # 3. Si no hay valores guardados, devolver distribución automática
        if valores_guardados is None or valores_guardados.empty:
            return distribucion_automatica
        
        # 4. Crear DataFrame híbrido
        distribucion_hibrida = distribucion_automatica.copy()
        columnas_meses = [c for c in distribucion_hibrida.columns if c not in ['Tipo de Actividad', 'Total', 'No.']]
        
        # 5. Preservar valores guardados manualmente (solo en columnas editables)
        mes_actual = datetime.now().month
        mes_siguiente = mes_actual + 1 if mes_actual < 12 else 12
        from utils.dates import get_month_number, get_month_name
        
        columnas_editables = [
            mes for mes in columnas_meses 
            if get_month_number(mes) > mes_siguiente
        ]
        
        # 6. Hacer merge por tipo de actividad para preservar valores
        for idx, row in distribucion_hibrida.iterrows():
            if row['Tipo de Actividad'] == 'TOTAL':
                continue
                
            tipo_codigo = row['No.']
            
            # Buscar la fila correspondiente en valores guardados
            fila_guardada = valores_guardados[
                (valores_guardados['No.'] == tipo_codigo) | 
                (valores_guardados['Tipo de Actividad'] == row['Tipo de Actividad'])
            ]
            
            if not fila_guardada.empty:
                fila_guardada = fila_guardada.iloc[0]
                
                # Solo preservar valores en columnas editables que tengan contenido
                for mes in columnas_editables:
                    if mes in fila_guardada.index:
                        valor_guardado = fila_guardada[mes]
                        if pd.notna(valor_guardado) and valor_guardado > 0:
                            distribucion_hibrida.at[idx, mes] = int(valor_guardado)
        
        # 7. Recalcular totales
        totales = distribucion_hibrida[columnas_meses].drop(index=distribucion_hibrida.shape[0]-1).sum(numeric_only=True)
        distribucion_hibrida.loc[distribucion_hibrida['Tipo de Actividad'] == 'TOTAL', columnas_meses] = totales.values
        distribucion_hibrida.loc[distribucion_hibrida['Tipo de Actividad'] == 'TOTAL', 'Total'] = int(totales.sum())
        
        return distribucion_hibrida

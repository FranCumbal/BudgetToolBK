import os
import math
import pandas as pd
from datetime import datetime
from utils.dates import get_days_in_months, get_month_number
from utils.file_manager import get_operative_capacity_avg_days_file

class OperativeCapacityManager:
    """
    Clase encargada de gestionar la tabla de capacidad operativa:
    carga, generación inicial, actualización, recalculo y guardado.
    """

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.operative_capacity_avg_days = get_operative_capacity_avg_days_file()
        self._load_days_avg_config()
        self.df = self._load_or_initialize()
        
    def _load_or_initialize(self):
        """
        Carga el archivo desde Excel o lo genera si no existe.
        """
        if os.path.exists(self.file_path):
            try:
                df = pd.read_excel(self.file_path)
                print(f"✅ Capacidad operativa cargada desde: {self.file_path}")
            except Exception as e:
                print(f"⚠️ Error leyendo {self.file_path}: {e}")
                df = self._generate_initial()
        else:
            print(f"📄 No existe {self.file_path}, se genera archivo inicial.")
            df = self._generate_initial()

        df = self._ensure_columns_exist(df)
        return self._recalculate(df)
    
    def _load_days_avg_config(self):
        self.days_avg = 13 
        if os.path.exists(self.operative_capacity_avg_days):
            try:
                df = pd.read_csv(self.operative_capacity_avg_days)
                if "days_avg" in df["key"].values:
                    self.days_avg = float(df[df["key"] == "days_avg"]["value"].values[0])
                    print(f"⚙️ days_avg cargado desde config: {self.days_avg}")
            except Exception as e:
                print(f"⚠️ Error leyendo config: {e}")
        else:
            self._save_days_avg_config()  # Crea el archivo si no existe

    def _save_days_avg_config(self):
        config_df = pd.DataFrame([{"key": "days_avg", "value": self.days_avg}])
        os.makedirs(os.path.dirname(self.operative_capacity_avg_days), exist_ok=True)
        config_df.to_csv(self.operative_capacity_avg_days, index=False)
        print(f"💾 Configuración guardada en {self.operative_capacity_avg_days}")

    def set_days_avg(self, days_avg: float):
        """
        Establece el promedio de días para cálculos futuros.
        """
        if not isinstance(days_avg, float) or days_avg <= 0:
            raise ValueError("El promedio de días debe ser un entero positivo.")
        self.days_avg = days_avg
        self._save_days_avg_config()
        self.df = self._recalculate(self.df)
        print(f"Promedio de días establecido: {self.days_avg}")

    def get_days_avg(self) -> float:
        return self.days_avg
    
    def get_total_tentative_opex_wells(self):
        """Devuelve el numero de pozos sugeridos por la estadistica de los dias promedio establecidos por Richard manualmente"""
        df_opex_wells = self.df.copy()
        df_opex_wells["Numero acumulado de pozos OPEX"] = df_opex_wells["Numero tentativo de pozos OPEX"].cumsum()
        total_tentative_opex_wells = df_opex_wells["Numero acumulado de pozos OPEX"].iloc[-1]
        return total_tentative_opex_wells
    
    def _generate_initial(self):
        """
        Genera un DataFrame inicial con datos base por mes.
        """
        current_year = datetime.now().year
        print(current_year)
        dias_por_mes = get_days_in_months(current_year)
        print(dias_por_mes)
        taladros = 3
        data = []

        for month, dias in dias_por_mes.items():
            print(month)
            print(dias)
            data.append({
                "Mes": month,
                "Taladros": 3,
                "Días CAPEX": 0,
                "Días Certificación": 0,
                "Días OPEX 4to Rig": 0,
                "Días CAPEX 4to Rig": 0,
                "Días Operativos": dias * 3,
                "Total Días OPEX": dias * 3,
                "Numero tentativo de pozos OPEX": math.ceil((dias * 3)/self.days_avg ) #11.9
            })
            print("DATA_______________________________________________________")
            print(data)
        return pd.DataFrame(data)

    def _ensure_columns_exist(self, df: pd.DataFrame):
        """
        Asegura que las columnas necesarias existan en el DataFrame.
        """
        needed_cols = [
            "Mes", "Taladros", "Días CAPEX", "Días Certificación",
            "Días Operativos", "Total Días OPEX", "Numero tentativo de pozos OPEX",
            "Días OPEX 4to Rig", "Días CAPEX 4to Rig"
        ]
        for col in needed_cols:
            if col not in df.columns:
                df[col] = 0
        return df

    def _recalculate(self, df: pd.DataFrame):
        """
        Recalcula los valores derivados por fila, incluyendo una lógica avanzada para
        el cálculo de pozos OPEX: truncamiento y redistribución del sobrante decimal.
        """
        import math

        current_year = datetime.now().year
        dias_por_mes = get_days_in_months(current_year)

        pozos_truncados = []
        decimales = []
        total_real = 0.0

        # 1. Calcular totales OPEX y número de pozos estimado (truncado + decimal)
        for idx, row in df.iterrows():
            mes = row["Mes"]
            mes_num = get_month_number(mes) if isinstance(mes, str) else mes
            if mes_num not in dias_por_mes:
                pozos_truncados.append(0)
                decimales.append(0)
                continue

            dias_mes = dias_por_mes[mes_num]
            taladros = row["Taladros"]
            dias_capex = row["Días CAPEX"]
            dias_cert = row["Días Certificación"]
            dias_4to_opex = row.get("Días OPEX 4to Rig", 0)
            dias_4to_capex = row.get("Días CAPEX 4to Rig", 0)

            # Cálculos base
            dias_operativos_base = dias_mes * taladros
            dias_operativos_total = dias_operativos_base + dias_4to_opex + dias_4to_capex
            total_opex = dias_operativos_base - dias_capex - dias_cert + dias_4to_opex

            # Actualizar valores en DataFrame
            df.at[idx, "Días Operativos"] = dias_operativos_total
            df.at[idx, "Total Días OPEX"] = total_opex

            # Cálculo de pozos con duración promedio de 13 días
            pozo_exacto = total_opex / self.days_avg if total_opex > 0 else 0 ###pozo_exacto = total_opex / 11.9 if total_opex > 0 else 0
            truncado = math.floor(pozo_exacto)
            decimal = pozo_exacto - truncado

            pozos_truncados.append(truncado)
            decimales.append(decimal)
            total_real += pozo_exacto

        # 2. Redistribuir sobrante decimal como pozos adicionales
        sobrante_pozo = round(total_real) - sum(pozos_truncados)
        indices_ordenados = sorted(range(len(decimales)), key=lambda i: decimales[i], reverse=True)

        for i in range(sobrante_pozo):
            idx = indices_ordenados[i]
            pozos_truncados[idx] += 1

        # 3. Asignar resultado final al DataFrame
        for idx, val in enumerate(pozos_truncados):
            df.at[idx, "Numero tentativo de pozos OPEX"] = val

        return df


    def update_value(self, row_index, column, value):
        """
        Actualiza un valor y recalcula todos los valores derivados.
        """
        if row_index < 0 or row_index >= len(self.df):
            raise IndexError("Índice fuera de rango.")
        if column not in self.df.columns:
            raise ValueError(f"Columna {column} no existe.")

        self.df.at[row_index, column] = value
        self.df = self._recalculate(self.df)  # << Esto recalcula todo lo demás

    def save(self, file_path=None):
        """
        Guarda el archivo al Excel original o a una ruta personalizada.
        """
        path = file_path or self.file_path
        self.df.to_excel(path, index=False)
        print(f"💾 Capacidad operativa guardada en {path}")

    def export_to(self, file_path):
        """
        Guarda una copia del archivo Excel en la ruta especificada.
        """
        self.df.to_excel(file_path, index=False)
        print(f"📤 Copia de la tabla guardada en: {file_path}")

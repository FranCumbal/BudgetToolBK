import os
import re
import pdfplumber
import pandas as pd
from datetime import datetime
from utils.file_manager import get_specific_schedule_activities_path, get_varillera_schedule_activities_path


# Constantes compartidas
DEFAULT_COLUMNS = [
    "Quote Number",
    "Quote Effective Date",
    "Year",
    "UWI/API",
    "Net Total (USD)",
    "Scheduled Execution Month",
    "Validation",
]

MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

VALIDATIONS = ["Pending", "Yes", "No"]

# Mantenemos la ruta global para compatibilidad
CSV_PATH = get_varillera_schedule_activities_path()


class QuoteExtractorService:
    """Servicio base para extracción de cotizaciones (originalmente para Varillera)"""
    
    def __init__(self):
        # Mantiene la funcionalidad original para Varillera
        self.CSV_PATH = CSV_PATH
        self.dataframe = self._load_or_create_csv()

    def _load_or_create_csv(self):
        """Carga el CSV existente o crea uno nuevo"""
        if os.path.exists(self.CSV_PATH):
            df = pd.read_csv(self.CSV_PATH)
        else:
            df = pd.DataFrame(columns=DEFAULT_COLUMNS)
        return df

    def get_extraction_patterns(self):
        """
        Define los patrones de extracción.
        Las clases hijas pueden sobrescribir este método para patrones específicos.
        """
        return {
            "Quote Number": r"Quote Number\s*:\s*(Q\.\d+)",
            "Quote Effective Date": r"Quote Effective Date\s*:\s*(\d{1,2}-[A-Za-z]{3}-\d{4})",
            "UWI/API": r"UWI/API\s*:\s*([A-Z0-9-]+)",
            "Net Total (USD)": r"Net Total \(USD\)\s*:\s*([\d.,]+)"
        }

    def extract_data_from_pdf(self, pdf_path):
        """Extrae datos del PDF usando los patrones definidos"""
        patrones = self.get_extraction_patterns()
        datos = {key: None for key in patrones}
        
        with pdfplumber.open(pdf_path) as pdf:
            texto = "\n".join([p.extract_text() or "" for p in pdf.pages])

        for campo, patron in patrones.items():
            match = re.search(patron, texto, re.IGNORECASE)
            if match:
                datos[campo] = match.group(1).strip()

        # Campos adicionales
        datos["Scheduled Execution Month"] = ""
        datos["Validation"] = ""
        datos["Year"] = self._extract_year(datos.get("Quote Effective Date", ""))

        return datos

    def _extract_year(self, date_str):
        """Extrae el año de una fecha en formato string"""
        try:
            return datetime.strptime(date_str, "%d-%b-%Y").strftime("%Y")
        except:
            return "Unknown"

    def add_or_update_entry(self, new_data):
        """Agrega o actualiza una entrada en el DataFrame"""
        if "Quote Number" not in new_data or not new_data["Quote Number"]:
            return False

        existing_index = self.dataframe[self.dataframe["Quote Number"] == new_data["Quote Number"]].index
        if not existing_index.empty:
            self.dataframe.loc[existing_index[0]] = new_data
        else:
            self.dataframe = pd.concat([self.dataframe, pd.DataFrame([new_data])], ignore_index=True)

        return True

    def delete_rows_by_indexes(self, indexes):
        """Elimina filas por índices"""
        self.dataframe.drop(indexes, inplace=True)
        self.dataframe.reset_index(drop=True, inplace=True)

    def save_to_csv(self):
        """Guarda el DataFrame al archivo CSV"""
        # Intentar convertir a fecha real
        try:
            self.dataframe["Quote Effective Date"] = pd.to_datetime(
                self.dataframe["Quote Effective Date"], errors="coerce", dayfirst=False
            )
            self.dataframe = self.dataframe.sort_values(by="Quote Effective Date")
        except Exception as e:
            print("[WARN] No se pudo ordenar por fecha:", e)

        self.dataframe.to_csv(self.CSV_PATH, index=False)

    def get_columns(self):
        """Retorna las columnas del DataFrame o las columnas por defecto"""
        return list(self.dataframe.columns) if not self.dataframe.empty else DEFAULT_COLUMNS

    def get_data_as_list(self):
        """Retorna los datos como lista de diccionarios"""
        return self.dataframe.to_dict(orient="records")


class SouthZoneQuoteExtractorService(QuoteExtractorService):
    """Servicio específico para líneas de la Zona Sur que hereda de QuoteExtractorService"""
    
    def __init__(self, line_name):
        # No llamamos super().__init__() porque necesitamos customizar la inicialización
        self.line_name = line_name
        self.CSV_PATH = get_specific_schedule_activities_path(line_name)
        self.dataframe = self._load_or_create_csv()
    
    def get_extraction_patterns(self):
        """
        Patrones específicos para la zona sur.
        Puedes personalizar estos patrones si las cotizaciones de la zona sur tienen formato diferente.
        """
        # Por ahora usa los mismos patrones que la clase padre
        # Pero puedes sobrescribirlos aquí si necesitas patrones específicos para zona sur
        base_patterns = super().get_extraction_patterns()
        
        # Ejemplo de personalización para zona sur (descomenta si necesitas):
        # base_patterns["Quote Number"] = r"South Quote\s*:\s*(SQ\.\d+)"
        # base_patterns["UWI/API"] = r"South UWI\s*:\s*([A-Z0-9-]+)"
        
        return base_patterns
    
    def _extract_year(self, date_str):
        """
        Sobrescribe la extracción de año si las fechas de zona sur tienen formato diferente.
        Por ahora usa la implementación de la clase padre.
        """
        return super()._extract_year(date_str)
    
    def save_to_csv(self):
        """
        Sobrescribe el método de guardado para usar la ruta específica de la zona sur.
        """
        # Intentar convertir a fecha real
        try:
            self.dataframe["Quote Effective Date"] = pd.to_datetime(
                self.dataframe["Quote Effective Date"], errors="coerce", dayfirst=False
            )
            self.dataframe = self.dataframe.sort_values(by="Quote Effective Date")
        except Exception as e:
            print(f"[WARN] No se pudo ordenar por fecha para {self.line_name}:", e)

        self.dataframe.to_csv(self.CSV_PATH, index=False)
import os
import glob
from datetime import datetime, timedelta

SPANISH_MONTHS = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
}

def get_user_base_dir():
    """
    Retorna la ruta base del usuario en OneDrive, validando dos rutas posibles.
    Si no se encuentra, retorna una ruta de fallback para evitar que la aplicación falle.

    Returns:
        str: Ruta encontrada o ruta de fallback.
    """
    usuario = os.getlogin()
    # Se buscan dos posibles nombres para la carpeta de OneDrive
    ruta_1 = fr"C:/Users/{usuario}/OneDrive - SLB/DIGITALIZACION ING. PROD. & EJEC_ - General"
    ruta_2 = fr"C:/Users/{usuario}/OneDrive - SLB/General - DIGITALIZACION ING. PROD. & EJEC_"
    if os.path.exists(ruta_1): return ruta_1
    if os.path.exists(ruta_2): return ruta_2
    
    print("ADVERTENCIA: No se encontró la ruta base de usuario 'General' de OneDrive. Usando ruta de prueba 'C:/TestSLB/'.")
    return get_test_path()
    

def get_user_base_dir_rig(): 
    usuario = os.getlogin()
    now = datetime.now()
    # Si es enero, el presupuesto corresponde al año anterior.
    budget_year = now.year - 1 if now.month == 1 else now.year
    
    base_1 = fr"C:/Users/{usuario}/OneDrive - SLB/SHAYA _ INGENIERÍA _ CAMPO - 00. BUDGET" #Socializar esta ruta
    # C:\Users\rgalarraga\OneDrive - Schlumberger\SHAYA _ INGENIERÍA _ CAMPO - 00. BUDGET
    base_2 = fr"C:/Users/{usuario}/OneDrive - Schlumberger/SHAYA _ INGENIERÍA _ CAMPO - 00. BUDGET" #como es de ruben

    base_to_use = base_1 if os.path.exists(base_1) else base_2 #Esta es la valida para configurar con los ingenieros
    
    folder = os.path.join(base_to_use, f"BUDGET {budget_year}")

    os.makedirs(folder, exist_ok=True)
    return folder

def get_test_path():
    ruta_3 = fr"C:/"
    os.makedirs(ruta_3, exist_ok=True)
    return ruta_3

def get_forecast_services_path_file():
    services_catalog_path = os.path.join(get_catalog_dir(), "services_forecast_path.csv")
    return services_catalog_path

def get_catalog_dir():
    return os.path.join(get_user_base_dir(), "06 Budget Tool", "00 CATALOGUE")

def get_comments_file_path():
    return os.path.join(get_catalog_dir(), "reporte_comentarios.xlsx")

def get_capex_config_path():
    """Retorna la ruta al archivo de configuración de meses CAPEX."""
    return os.path.join(get_catalog_dir(), "capex_config.csv")

def get_catalog_path(filename="catalogo_solo_valores.xlsx"):
    return os.path.join(get_catalog_dir(), filename)

def get_operative_capacity_avg_days_file():
    return os.path.join(get_catalog_dir(), "operative_capacity_avg_days.csv")

def get_tubulars_config_path(filename="tubulars_config.xlsx") -> str:
    return os.path.join(get_catalog_dir(), filename)

def get_selected_services_wells_path(filename="selected_services_wells.xlsx") -> str:
    return os.path.join(get_catalog_dir(), filename)

def get_template_path(filename="Plantilla_de_actividades.xlsx") -> str:
    return os.path.join(get_catalog_dir(), filename)

def get_operative_capacity_path():
    return os.path.join(get_catalog_dir(), "operative_capacity.xlsx")

def get_plan_path(year: int):
    return os.path.join(get_user_base_dir(), "06 Budget Tool", "PLAN", str(year), f"CDFPlan{year}.xlsx")

def get_forecasted_plan_path(year: int):
    return os.path.join(get_user_base_dir(), "06 Budget Tool", "PLAN", str(year), f"ForecastedPlan{year}.xlsx")

def get_planning_cost_path(year: int):
    path = os.path.join(get_user_base_dir(), "06 Budget Tool", "PLAN", str(year), "Planning Cost")
    os.makedirs(path, exist_ok=True)
    return path

def get_planning_cost_by_line_path(line_name: str, year: int):
    #Si no existe crear el archivo
    path = os.path.join(get_user_base_dir(), "06 Budget Tool", "PLAN", str(year), "Planning Cost", f"{line_name}_Planning_Cost.xlsx")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return path

def get_budget_opex_path(year: int):
    return os.path.join(get_user_base_dir(), "06 Budget Tool", "PLAN", str(year), f"PresupuestoOpex_{year}.xlsx")

def get_budget_als_dir():
    return os.path.join(get_user_base_dir(), "06 Budget Tool", "REPOSITORY", "ALS")

def get_field_file_cost():
    folder = os.path.join(get_user_base_dir_rig(), "3. COSTOS MENSUALES")
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, "Control de costos.xlsx")
    return path

def get_specific_schedule_activities_path(line_name: str):
    if line_name == "ITEM 104 Varillera": # Esto es para el nuevo requerimiento, no se generalizo desde el principio porque al ultimo pidieron el cambio
        return get_varillera_schedule_activities_path()
    
    filename = f"{line_name}_scheduled_path.csv"
    try:
        folder = os.path.join(get_user_base_dir_rig(), "0. Budget Tool", "0. CTU Docs")
        os.makedirs(folder, exist_ok=True)
    except Exception as e:
        #print(f"Error al crear el directorio: {e}")
        folder = get_test_path()
    return os.path.join(folder, filename)

def get_varillera_schedule_activities_path():
    filename = "varillera_scheduled_path.csv"
    try:
        folder = os.path.join(get_user_base_dir_rig(), "0. Budget Tool", "1. Varillera Docs")
        os.makedirs(folder, exist_ok=True)
    except Exception as e:
        folder = get_test_path()
    return os.path.join(folder, filename)

def get_planned_activities_catalog_path():
    filename = "Catalogo de Actividades RIG.csv"
    try:
        folder = os.path.join(get_user_base_dir_rig(), "0. Budget Tool", "1. Varillera Docs")
        os.makedirs(folder, exist_ok=True)
    except Exception as e:
        #print(f"Error al crear el directorio con la primera ruta: {e} continuando con la segunda ruta")
        folder = get_test_path()
    return os.path.join(folder, filename)

def get_field_line_comments_file_path(): # Comments
    filename = "reporte_comentarios_lineas_campo.csv"
    try:
        folder = os.path.join(get_user_base_dir_rig(), "0. Budget Tool", "2. Field Lines Comments")
        os.makedirs(folder, exist_ok=True)
    except Exception as e:
        #print(f"Error al crear el directorio con la primera ruta: {e} continuando con la segunda ruta")
        folder = get_test_path()
    return os.path.join(folder, filename)

def get_historical_initial_cost_approved_path(): #VARILLERA
    filename = "historical_initial_cost_approved.csv"
    try:
        folder = os.path.join(get_user_base_dir_rig(), "0. Budget Tool", "1. Varillera Docs")
        os.makedirs(folder, exist_ok=True)
    except Exception as e:
        #print(f"Error al crear el directorio con la primera ruta: {e} continuando con la segunda ruta")
        folder = get_test_path()
    return os.path.join(folder, filename)

def get_cpi_spi_path(line_title=None): #cpi and spi
    """
    Retorna la ruta del archivo CSV de CPI/SPI.
    Si se proporciona line_title, retorna la ruta específica para esa línea.
    Si no se proporciona, retorna el directorio base para búsqueda de archivos.
    """
    try:
        base_dir = os.path.join(get_user_base_dir_rig(), "0. Budget Tool", "4. CPI and SPI")
        os.makedirs(base_dir, exist_ok=True)
    except Exception as e:
        #print(f"Error al crear el directorio: {e}")
        base_dir = get_test_path()
    if line_title:
        # Sanitizar el título para usar como nombre de archivo
        sanitized_title = "".join(c for c in line_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        sanitized_title = sanitized_title.replace(' ', '_')
        filename = f"cpi_spi_{sanitized_title}.csv"
        return os.path.join(base_dir, filename)
    else:
        return base_dir

def get_manual_planning_path(line_title=None): #Manual planning
    try:
        base_dir = os.path.join(get_user_base_dir_rig(), "0. Budget Tool", "3. Manual Planning")
        os.makedirs(base_dir, exist_ok=True)
    except Exception as e:
        #print(f"Error al crear el directorio: {e}")
        base_dir = get_test_path()
    if line_title:
        # Sanitizar el título para usar como nombre de archivo
        safe_title = line_title.replace(" ", "_").replace("/", "_").replace("\\", "_")
        return os.path.join(base_dir, f"manual_planning_{safe_title}.csv")
    else:
        return base_dir
    

def get_categorizer_executed_catalog_path_by_line_name(line_title=None): #categorizer
    try:
        base_dir = os.path.join(get_user_base_dir_rig(), "0. Budget Tool", "5. Executed Activities Classification")
        os.makedirs(base_dir, exist_ok=True)
    except Exception as e:
        #print(f"Error al crear el directorio: {e}")
        base_dir = get_test_path()
    if line_title:
        # Sanitizar el título para usar como nombre de archivo
        safe_title = line_title.replace(" ", "_").replace("/", "_").replace("\\", "_")
        return os.path.join(base_dir, f"categorizer_executed_activities_{safe_title}.csv")
    else:
        return base_dir
    
def get_completion_status_path():
    filename = "field_lines_completion_status.csv"
    folder = os.path.join(get_user_base_dir_rig(), "0. Budget Tool", "7. Lead Configuration")
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, filename)

def get_all_manual_planning_files(): #Manual planning
    """
    Retorna una lista de todos los archivos de planificación manual encontrados.
    Retorna una lista de tuplas (line_title, file_path).
    """
    base_dir = get_manual_planning_path()
    files = []
    
    if os.path.exists(base_dir):
        for filename in os.listdir(base_dir):
            if filename.startswith("manual_planning_") and filename.endswith(".csv"):
                # Extraer el título de la línea del nombre del archivo
                line_title = filename[16:-4].replace("_", " ") 
                file_path = os.path.join(base_dir, filename)
                files.append((line_title, file_path))
    
    return files

def get_cotizacion_path(year: int) -> str:
    """
    Devuelve la ruta del archivo de cotización para el año dado, buscando en dos posibles ubicaciones.

    Args:
        year (int): Año del presupuesto
    Returns:
        str: Ruta al archivo .xlsm
    Raises:
        FileNotFoundError: Si ninguna ruta existe.
    """
    usuario = os.getlogin()
    ruta_1 = os.path.join(fr"C:/Users/{usuario}/OneDrive - SLB", "2023 Costos y Forecast", f"Seguimiento Budget {year} ALS Shaya.xlsm")
    ruta_2 = os.path.join(fr"C:/Users/{usuario}/OneDrive - SLB", "APS _ Shaya _ Production Eng. & Execution - 2023 Costos y Forecast", f"Seguimiento Budget {year} ALS Shaya.xlsm")
    if os.path.exists(ruta_1): return ruta_1
    if os.path.exists(ruta_2): return ruta_2
    raise FileNotFoundError("No se encontró ninguna de las rutas de cotización esperadas.")

def get_single_excel_file_path(directory_path: str) -> str:
    """
    Busca un único archivo Excel válido dentro de un directorio.

    Args:
        directory_path (str): Ruta al directorio
    Returns:
        str: Ruta del archivo Excel encontrado
    Raises:
        FileNotFoundError: Si no hay archivos
        ValueError: Si hay más de un archivo Excel
    """
    excel_files = [f for f in os.listdir(directory_path) if f.lower().endswith((".xlsx", ".xlsm")) and not f.startswith("~$")]
    if not excel_files:
        raise FileNotFoundError(f"No se encontró ningún archivo Excel en: {directory_path}")
    if len(excel_files) > 1:
        raise ValueError(f"Se encontró más de un archivo Excel en: {directory_path}")
    return os.path.join(directory_path, excel_files[0])

def build_base_report_path() -> str:
    """
    Construye la ruta base de reportes para 'Cierre Costos', validando dos rutas posibles.

    Returns:
        str: Ruta existente
    Raises:
        FileNotFoundError: Si ninguna ruta existe
    """
    usuario = os.getlogin()
    año_actual = datetime.now().year
    ruta_1 = os.path.join(fr"C:/Users/{usuario}/OneDrive - SLB/APS _ Shaya _ Production Eng. & Execution - 03 Budget - Documents/03 Budget", str(año_actual), "Cierre Costos")
    ruta_2 = os.path.join(fr"C:/Users/{usuario}/OneDrive - SLB/APS _ Shaya _ Production Eng. & Execution - 03 Budget - 03 Budget", str(año_actual), "Cierre Costos")
    if os.path.exists(ruta_1): return ruta_1
    if os.path.exists(ruta_2): return ruta_2
    raise FileNotFoundError("No se encontró ninguna de las rutas base de reportes esperadas.")

def buscar_archivo_excel_mas_reciente(ruta: str, mes: str) -> str | None:
    """
    Retorna la ruta al archivo Excel más reciente en una subcarpeta del mes.

    Args:
        ruta (str): Ruta base.
        mes (str): Subcarpeta del mes, ej. '04.Abril'.

    Returns:
        str | None: Ruta del archivo más reciente o None si no hay archivos.
    """
    carpeta_mes = os.path.join(ruta, mes)
    archivos_excel = glob.glob(os.path.join(carpeta_mes, '*.xlsx'))
    return max(archivos_excel, key=os.path.getctime) if archivos_excel else None

def obtener_archivo_reporte_actual() -> str | None:
    """
    Obtiene la ruta del archivo más reciente del mes anterior para 'Cierre Costos'.

    Returns:
        str | None: Ruta del archivo Excel o None si no se encuentra
    """
    hoy = datetime.today()
    primer_dia_mes = hoy.replace(day=1)
    mes_anterior_fecha = primer_dia_mes - timedelta(days=1)
    mes_anterior = f"{mes_anterior_fecha.month:02d}.{SPANISH_MONTHS[mes_anterior_fecha.month]}"
    return buscar_archivo_excel_mas_reciente(build_base_report_path(), mes_anterior)

def get_output_path_for_pptx(year=None, month=None) -> str:
    """
    Retorna la ruta de guardado del archivo PPTX generado por el sistema.

    Args:
        year (int, optional): Año. Si no se proporciona, se usa el año actual.
        month (str, optional): Mes. Si no se proporciona, se usa el mes actual.

    Returns:
        str: Ruta completa del archivo PPTX.
    """
    now = datetime.now()
    year = year or now.year
    month = month or now.strftime("%B")
    reports_dir = os.path.join(get_user_base_dir(), "06 Budget Tool", "Reports", str(year), month)
    os.makedirs(reports_dir, exist_ok=True)
    return os.path.join(reports_dir, "budget_follow.pptx")



def get_all_cpi_spi_files():
    """
    Retorna una lista de todos los archivos de CPI/SPI encontrados.
    Retorna una lista de tuplas (line_title, file_path).
    """
    base_dir = get_cpi_spi_path()
    files = []
    
    if os.path.exists(base_dir):
        for filename in os.listdir(base_dir):
            if filename.startswith("cpi_spi_") and filename.endswith(".csv"):
                # Extraer el título de la línea del nombre del archivo
                title_part = filename[8:-4]  # Remover "cpi_spi_" y ".csv"
                line_title = title_part.replace('_', ' ')
                file_path = os.path.join(base_dir, filename)
                files.append((line_title, file_path))
    
    return files

def get_field_approved_budget_activities_from_file(): #approved budget
    """
    Retorna la ruta del archivo CSV de approved_budget_activities_field_lines.csv
    """
    filename = "approved_budget_activities_field_lines.csv"
    try:
        folder = os.path.join(get_user_base_dir_rig(), "0. Budget Tool", "6. Approved Budget Activities")
        os.makedirs(folder, exist_ok=True)
    except Exception as e:
        #print(f"Error al crear el directorio con la primera ruta: {e} continuando con la segunda ruta")
        folder = get_test_path()
    return os.path.join(folder, filename)


def get_categorizer_executed_catalog_path(): #categorizer
    """
    Retorna la ruta del archivo CSV para el catálogo de actividades ejecutadas categorizadas.
    """
    filename = "categorizer_executed_activities.csv"
    try:
        folder = os.path.join(get_user_base_dir_rig(), "0. Budget Tool", "5. Executed Activities Classification")
        os.makedirs(folder, exist_ok=True)
    except Exception as e:
        #print(f"Error al crear el directorio con la primera ruta: {e} continuando con la segunda ruta")
        folder = get_test_path()
    return os.path.join(folder, filename)
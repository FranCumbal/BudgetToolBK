import pandas as pd

def group_budget(budget_data, line):
    
    """
    Agrupa los datos del presupuesto según la columna especificada y devuelve un DataFrame.

    Parámetros:
    budget_data (DataFrame): El DataFrame que contiene los datos del presupuesto.
    line (str): El nombre de la columna por la cual se agruparán los datos.

    Retorna:
    DataFrame: Un DataFrame con los datos agrupados por mes y la suma de la columna especificada.
    """
    budget_data = budget_data.groupby('MONTH')[line].sum()
    # Convertir la Serie a DataFrame
    budget_df = budget_data.reset_index()
    
    return budget_df


def group_budget_by_month(data, year=2025):
    """
    Filtra por año y agrupa los datos de presupuesto por mes, sumando los valores.

    Args:
        data (pd.DataFrame): DataFrame con columnas 'YEAR', 'MONTH' y 'Total'.
        year (int, optional): Año específico para filtrar los datos.

    Returns:
        pd.DataFrame: DataFrame con 'MONTH' y 'Total' sumado por mes.
    """
    # Validar que existan las columnas necesarias
    required_columns = {'YEAR', 'MONTH', 'Total'}
    if not required_columns.issubset(data.columns):
        raise ValueError("El DataFrame debe contener las columnas 'YEAR', 'MONTH' y 'Total'.")

    # Reemplazar abreviaciones por nombres completos
    data['MONTH'] = data['MONTH'].replace({'Jan': 'January', 'Feb': 'February'})

    # Filtrar por año si se proporciona
    if year is not None:
        data = data[data['YEAR'] == year]

    # Agrupar por mes y sumar los valores
    grouped_data = data.groupby('MONTH', as_index=False)['Total'].sum()

    # Ordenar los meses
    month_order = ["January", "February", "March", "April", "May", "June",
                   "July", "August", "September", "October", "November", "December"]
    grouped_data['MONTH'] = pd.Categorical(grouped_data['MONTH'], categories=month_order, ordered=True)
    grouped_data = grouped_data.sort_values('MONTH')

    return grouped_data

def group_by_month(data):
    """
    Groups matched data by YEAR and MONTH, summing up the actual values for each group.

    Args:
        data (pd.DataFrame): Matched data containing actual or planned values.

    Returns:
        pd.DataFrame: Data grouped by YEAR and MONTH.
    """
    return data.groupby(["YEAR", "MONTH"]).sum().reset_index()


def group_data(data, group_mapping, group_by=None):
    """
    Groups data based on the specified column mappings and optional group-by criteria.

    Args:
        data (pd.DataFrame): DataFrame containing raw data.
        group_mapping (dict): Mapping of group names to column names.
        group_by (list): Optional columns to group by (e.g., ['YEAR', 'MONTH']).

    Returns:
        pd.DataFrame: Grouped data with totals for each group and original columns for merging.
    """
    grouped_data = {}

    # Apply column mappings to calculate group totals
    for group, columns in group_mapping.items():
        grouped_data[group] = data[columns].sum(axis=1, skipna=True)

    # Convert grouped data to DataFrame
    grouped_df = pd.DataFrame(grouped_data)

    # Include original columns required for merging
    if group_by:
        grouped_df = pd.concat([data[group_by], grouped_df], axis=1)

        # Aggregate by group-by columns
        grouped_df = grouped_df.groupby(group_by).sum().reset_index()
        print('grouped_df')
        print(grouped_df)

    return grouped_df


def match_jobs_with_budget(cotizacion, budget, group_mapping_budget, group_mapping_cotizacion):
    """
    Matches jobs from cotización with budget data, using budget values when available.
    For unmatched jobs, use cotización values.

    Args:
        cotizacion (pd.DataFrame): Cotización data (baseline planned jobs).
        budget (pd.DataFrame): Budget data (actual values for matched jobs).
        group_mapping_budget (dict): Mapping for budget grouping.
        group_mapping_cotizacion (dict): Mapping for cotización grouping.

    Returns:
        pd.DataFrame: Combined data with actual or planned values.
    """
    # Mapping numeric months to three-letter abbreviations
    MONTH_MAPPING = {
        1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr",
        5: "May", 6: "Jun", 7: "Jul", 8: "Aug",
        9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"
    }
    cotizacion = cotizacion.rename(columns={"POZO": "WELL", "MES": "MONTH", "AÑO": "YEAR"})
    
    # Convertir a string, quitar espacios, poner en mayúsculas
    cotizacion["WELL"] = cotizacion["WELL"].astype(str).str.strip().str.upper()

    # Paso 2: Normalizar 'WELL' en budget (si existe)
    if "WELL" in budget.columns:
        budget["WELL"] = budget["WELL"].astype(str).str.strip().str.upper()
        
    
    # Step 1: Normalize months in cotización
    
    cotizacion["MONTH"] = cotizacion["MONTH"].map(MONTH_MAPPING)

    # Step 2: Normalize months in budget using a normalization dictionary
    MONTH_NORMALIZATION = {
        "Jan": "Jan", "January": "Jan",
        "Feb": "Feb", "February": "Feb",
        "March": "Mar",
        "April": "Apr",
        "May": "May",
        "June": "Jun",
        "July": "Jul",
        "August": "Aug",
        "September": "Sep",
        "October": "Oct",
        "November": "Nov",
        "December": "Dic"
    }
    budget["MONTH"] = budget["MONTH"].str.strip().map(MONTH_NORMALIZATION)

    # Step 3: Group both datasets for easier matching
    grouped_budget = group_data(data=budget, group_mapping=group_mapping_budget, group_by=["WELL", "YEAR", "MONTH"])

    grouped_cotizacion = group_data(data=cotizacion, group_mapping=group_mapping_cotizacion, group_by=["WELL", "YEAR", "MONTH"])
    
    grouped_cotizacion.to_excel(r"summary\als\grouped_cotizacion.xlsx")
    grouped_budget.to_excel(r"summary\als\grouped_budget.xlsx")


    # Step 4: Merge cotización with budget (on WELL, MONTH, YEAR)
    merged = grouped_cotizacion.merge(
        grouped_budget,
        on=["WELL", "MONTH", "YEAR"],
        how="left",
        suffixes=("_cotizacion", "_budget")
    )

    #exportar a un archivo excel
    merged.to_excel(r"summary\als\merged.xlsx")



    for group in group_mapping_budget.keys():
        col_budget = f"{group}_budget"
        col_cotizacion = f"{group}_cotizacion"
        col_actual = f"{group}_Actual"

        if group == "B&H":
            # Solo usar B&H del presupuesto, no de cotización
            merged[col_actual] = merged[col_budget]  # no se rellena con cotización
        else:
            merged[col_actual] = merged[col_budget].fillna(merged[col_cotizacion])


    return merged



BUDGET_GROUP_MAPPING = {
    "Servicio": ["Pull", "Run", "NPT", "Preensamble"],
    "Equipo": ["Equipo ", "Reparacion", "Misc. Fondo ", "Business Model Discount"],
    "Protectores de Cable": ["Protectores", "Low profile"],
    "Capilar": ["Capilar"],
    "Equipo Superficie": ["Misc. Superficie", "Equipo Superficie", "Transformadores", "Mantenimiento "],
    "Desarenador": ["Desarenador"],
    "Cable Nuevo": ["Cable Nuevo"],
    "B&H": ["B&H"]
}

COTIZACION_GROUP_MAPPING = {
    "Servicio": ["instalacion $"],
    "Equipo": ["Bomba als (Sarta + misceláneos", "Motor EON", "AGH Extendido o DoblE $", "Prot Advanced T1", "Tailpipe o Cabeza InY"],
    "Protectores de Cable": ["Protectore de Cable Nuev"],
    "Capilar": ["Capilar?        (Material) ALS"],
    "Equipo Superficie": ["Set de Superficie"],
    "Desarenador": ["DESARENADOR"],
    "Cable Nuevo": ["Cable Nuevo"],
    "B&H": ["$ de B&H 2020, 2021"]
}

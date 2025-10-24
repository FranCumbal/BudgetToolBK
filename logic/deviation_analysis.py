# logic/deviation_analysis.py
import pandas as pd

def calculate_deviations(data, group_mapping, threshold=20000):
    """
    Calculates deviations between actual (cotizacion) and planned (budget) values at the job level.

    Args:
        data (pd.DataFrame): Data containing actual (cotizacion) and planned (budget) values.
        group_mapping (dict): Mapping of group names to column names.
        threshold (int): Deviation threshold to flag.

    Returns:
        pd.DataFrame: Deviations exceeding the threshold at the job level.
    """
    # Calculate deviations for each group
    for group in group_mapping.keys():
        data[f"{group}_Deviation"] = data[f"{group}_cotizacion"] - data[f"{group}_budget"]
    
    # Filter rows where any deviation exceeds the threshold in absolute terms
    deviation_columns = [f"{group}_Deviation" for group in group_mapping.keys()]
    deviations = data[data[deviation_columns].max(axis=1) > threshold]

    return deviations

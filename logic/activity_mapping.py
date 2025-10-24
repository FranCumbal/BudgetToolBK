# logic/activity_mapping.py
import pandas as pd

def map_services_and_costs(jobs_data: pd.DataFrame,
                           template_df: pd.DataFrame,
                           catalog_df: pd.DataFrame) -> pd.DataFrame:
    """
    1) Une jobs_data con la plantilla (en 'activity_type') para expandir
       cada job según los servicios que requiere.
    2) Une con catalogo_df (en ['servicio','linea']) para obtener el costo unitario.
    3) Devuelve un DataFrame con una fila por (job, servicio) y la columna 'CostByService'.
    """
    # Merge con la plantilla
    merged_1 = pd.merge(
        jobs_data,
        template_df,
        on="activity_type",
        how="left"
    )

    # Merge con el catálogo
    merged_2 = pd.merge(
        merged_1,
        catalog_df,
        on=["type", "line"],
        how="left"
    )

    # Costo por servicio (si no hay coincidencia, fillna(0))
    merged_2['CostByService'] = merged_2['cost'].fillna(0)

    return merged_2

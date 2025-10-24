import os
import pandas as pd
from utils.file_manager import get_comments_file_path, get_field_line_comments_file_path


def load_comments() -> pd.DataFrame:
    """
    Carga los comentarios desde el archivo definido en la ruta estándar.

    Returns:
        pd.DataFrame: DataFrame con las columnas ['Report Title', 'Mes', 'Fecha', 'Usuario', 'Comentario'].
        Si el archivo no existe, retorna un DataFrame vacío con dichas columnas.
    """
    path = get_comments_file_path()
    if os.path.exists(path):
        return pd.read_excel(path)
    else:
        return pd.DataFrame(columns=["Report Title", "Mes", "Fecha", "Usuario", "Comentario"])

def save_comment(df: pd.DataFrame) -> None:
    """
    Guarda el DataFrame de comentarios en la ruta definida.

    Args:
        df (pd.DataFrame): DataFrame con los comentarios actualizados que se desea guardar.
    """
    path = get_comments_file_path()
    df.to_excel(path, index=False)


def load_field_line_comments() -> pd.DataFrame:
    """
    Carga los comentarios de líneas de campo desde el archivo CSV.
    """
    path = get_field_line_comments_file_path()
    if os.path.exists(path):
        return pd.read_csv(path)
    else:
        return pd.DataFrame(columns=["Report Title", "Mes", "Fecha", "Usuario", "Comentario"])

def save_field_line_comment(df: pd.DataFrame) -> None:
    """
    Guarda el DataFrame de comentarios de líneas de campo en el archivo CSV.
    """
    path = get_field_line_comments_file_path()
    df.to_csv(path, index=False)

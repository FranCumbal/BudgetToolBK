import json
import os
import sys

def resource_path(relative_path):
    """ Obtiene la ruta absoluta al recurso, funciona para desarrollo y para PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def load_months_from_file(path="utils/months.json"):
    with open(resource_path(path), "r", encoding="utf-8") as f:
        return json.load(f)
    
def load_field_reports_from_json():
    json_path = "utils/field_lines_report.json"
    with open(resource_path(json_path), "r", encoding="utf-8") as f:
        configs = json.load(f)
    return configs  # Solo retorna la lista de dicts

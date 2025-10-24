MONTH_NAME_TO_ABREV = {
            'january': 'ene', 'ene': 'ene',
            'february': 'feb', 'feb': 'feb',
            'march': 'mar', 'mar': 'mar',
            'april': 'abr', 'abr': 'abr',
            'may': 'may', 'may': 'may',
            'june': 'jun', 'jun': 'jun',
            'july': 'jul', 'jul': 'jul',
            'august': 'ago', 'ago': 'ago',
            'september': 'sept', 'september': 'sep',
            'october': 'oct', 'oct': 'oct',
            'november': 'nov', 'nov': 'nov',
            'december': 'dic', 'dic': 'dic'
        }

MONTH_ES_TO_MONTH_EN = {
            'enero': 'january', 'febrero': 'february', 'marzo': 'march',
            'abril': 'april', 'mayo': 'may', 'junio': 'june',
            'julio': 'july', 'agosto': 'august', 'septiembre': 'september',
            'octubre': 'october', 'noviembre': 'november', 'diciembre': 'december'
        }

NAME_MONTH_COMPLETE = {
            'ene': 'january', 'feb': 'february', 'mar': 'march',
            'abr': 'april', 'may': 'may', 'jun': 'june',
            'jul': 'july', 'ago': 'august', 'sept': 'september', 'sep': 'september',  # Clave actualizada
            'oct': 'october', 'nov': 'november', 'dic': 'december'
        }

SORTED_MONTHS = ['ene', 'feb', 'mar', 'abr', 'may', 'jun',
                'jul', 'ago', 'sep', 'oct', 'nov', 'dic']

MONTH_ABREV_TO_NAME = {v: k.capitalize() for k, v in MONTH_NAME_TO_ABREV.items() if len(v) <= 4}

def normalizar_mes(mes):
    mes = mes.strip().lower()
    if mes in MONTH_NAME_TO_ABREV:
        return MONTH_NAME_TO_ABREV[mes]
    if mes in MONTH_ABREV_TO_NAME:
        return MONTH_ABREV_TO_NAME[mes]
    if mes in SORTED_MONTHS:
        return SORTED_MONTHS[SORTED_MONTHS.index(mes)]
    raise ValueError(f"Mes '{mes}' no reconocido.")
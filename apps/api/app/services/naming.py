import re
from string import Formatter


def safe_filename(s: str) -> str:
    s = str(s) if s is not None else ""
    s = re.sub(r"[\\/:*?\"<>|]+", " ", s).strip()
    s = re.sub(r"\s+", " ", s)
    s = s.replace(" ", "_")
    return s[:140] if s else "documento"


def apply_pattern(pattern: str, row: dict, row_index: int) -> str:
    # pattern uses python format: Proceso_{NumeroProceso}_{NombreContribuyente}
    data = dict(row)
    data["row_index"] = row_index
    try:
        name = pattern.format(**data)
    except KeyError as e:
        missing = str(e).strip("'")
        raise KeyError(f"Falta columna requerida para el patron: {missing}")
    return safe_filename(name)


def extract_pattern_fields(pattern: str) -> set[str]:
    fields: set[str] = set()
    for _, field_name, _, _ in Formatter().parse(pattern):
        if field_name:
            fields.add(field_name)
    return fields

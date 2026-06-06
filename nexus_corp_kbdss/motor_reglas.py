"""Motor de reglas para Nexus-Corp KBDSS.

Este modulo lee la base de conocimiento XML, compara una situacion
ingresada por el usuario y devuelve las reglas aplicables.
"""

from pathlib import Path
import xml.etree.ElementTree as ET


DATA_DIR = Path(__file__).resolve().parent / "data"
REGLAS_XML = DATA_DIR / "reglas.xml"


def _normalizar(texto):
    """Convierte texto a una forma simple para comparar valores."""
    return (texto or "").strip().lower()


def _convertir_numero(valor):
    """Intenta convertir un valor a numero; si no puede, devuelve None."""
    try:
        return float(str(valor).replace(",", "."))
    except (TypeError, ValueError):
        return None


def cargar_reglas(ruta_xml=REGLAS_XML):
    """Carga las reglas desde XML y las devuelve como una lista de dicts."""
    if not Path(ruta_xml).exists():
        return []

    tree = ET.parse(ruta_xml)
    root = tree.getroot()
    reglas = []

    for nodo in root.findall("regla"):
        reglas.append(
            {
                "id": nodo.get("id", ""),
                "nombre": nodo.findtext("nombre", default=""),
                "area": nodo.findtext("area", default=""),
                "variable": nodo.findtext("variable", default=""),
                "operador": nodo.findtext("operador", default=""),
                "valor": nodo.findtext("valor", default=""),
                "recomendacion": nodo.findtext("recomendacion", default=""),
                "prioridad": nodo.findtext("prioridad", default=""),
            }
        )

    return reglas


def comparar_valores(valor_actual, operador, valor_regla):
    """Evalua una condicion simple entre el valor ingresado y el valor de regla."""
    operador = _normalizar(operador)

    if operador in {"menor que", "mayor que", "igual a"}:
        actual_num = _convertir_numero(valor_actual)
        regla_num = _convertir_numero(valor_regla)

        if actual_num is None or regla_num is None:
            actual = _normalizar(valor_actual)
            regla = _normalizar(valor_regla)
            if operador == "igual a":
                return actual == regla
            return False

        if operador == "menor que":
            return actual_num < regla_num
        if operador == "mayor que":
            return actual_num > regla_num
        return actual_num == regla_num

    if operador == "contiene":
        return _normalizar(valor_regla) in _normalizar(valor_actual)

    return False


def evaluar_decision(area, variable, valor_actual, ruta_xml=REGLAS_XML):
    """Devuelve la primera regla aplicable para una situacion empresarial."""
    area_normalizada = _normalizar(area)
    variable_normalizada = _normalizar(variable)

    for regla in cargar_reglas(ruta_xml):
        if _normalizar(regla["area"]) != area_normalizada:
            continue
        if _normalizar(regla["variable"]) != variable_normalizada:
            continue
        if comparar_valores(valor_actual, regla["operador"], regla["valor"]):
            return {
                "encontrada": True,
                "nombre": regla["nombre"],
                "area": regla["area"],
                "variable": regla["variable"],
                "recomendacion": regla["recomendacion"],
                "prioridad": regla["prioridad"],
            }

    return {
        "encontrada": False,
        "mensaje": "No se encontro una regla aplicable para esta situacion.",
    }

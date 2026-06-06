"""Aplicacion web Nexus-Corp KBDSS.

Prototipo universitario de un Sistema de Gestion de Decisiones Basado
en Conocimiento usando Flask, XML y un motor de reglas en Python.
"""

from datetime import datetime
from pathlib import Path
import xml.etree.ElementTree as ET

from flask import Flask, flash, redirect, render_template, request, url_for

from motor_reglas import cargar_reglas, evaluar_decision


app = Flask(__name__)
app.secret_key = "nexus-corp-kbdss-demo"

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
REGLAS_XML = DATA_DIR / "reglas.xml"
DECISIONES_XML = DATA_DIR / "decisiones.xml"
RETRO_XML = DATA_DIR / "retroalimentacion.xml"


AREAS = ["Ventas", "Inventario", "Logistica", "Finanzas"]
OPERADORES = ["menor que", "mayor que", "igual a", "contiene"]
PRIORIDADES = ["Baja", "Media", "Alta"]


def asegurar_archivo_xml(ruta, raiz):
    """Crea un archivo XML vacio si no existe."""
    if not ruta.exists():
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ET.ElementTree(ET.Element(raiz)).write(ruta, encoding="utf-8", xml_declaration=True)


def leer_xml(ruta, raiz):
    asegurar_archivo_xml(ruta, raiz)
    return ET.parse(ruta)


def guardar_xml(tree, ruta):
    tree.write(ruta, encoding="utf-8", xml_declaration=True)


def siguiente_id(root, etiqueta):
    ids = []
    for nodo in root.findall(etiqueta):
        try:
            ids.append(int(nodo.get("id", "0")))
        except ValueError:
            ids.append(0)
    return str(max(ids, default=0) + 1)


def obtener_decisiones():
    tree = leer_xml(DECISIONES_XML, "decisiones")
    decisiones = []
    for nodo in tree.getroot().findall("decision"):
        decisiones.append(
            {
                "id": nodo.get("id", ""),
                "fecha": nodo.findtext("fecha", default=""),
                "area": nodo.findtext("area", default=""),
                "variable": nodo.findtext("variable", default=""),
                "valor": nodo.findtext("valor", default=""),
                "observacion": nodo.findtext("observacion", default=""),
                "regla": nodo.findtext("regla", default=""),
                "recomendacion": nodo.findtext("recomendacion", default=""),
                "prioridad": nodo.findtext("prioridad", default=""),
            }
        )
    return list(reversed(decisiones))


def obtener_retroalimentaciones():
    tree = leer_xml(RETRO_XML, "retroalimentaciones")
    items = []
    for nodo in tree.getroot().findall("retroalimentacion"):
        items.append(
            {
                "fecha": nodo.findtext("fecha", default=""),
                "decision_id": nodo.findtext("decision_id", default=""),
                "calificacion": nodo.findtext("calificacion", default=""),
                "comentario": nodo.findtext("comentario", default=""),
            }
        )
    return list(reversed(items))


def guardar_decision(area, variable, valor, observacion, resultado):
    tree = leer_xml(DECISIONES_XML, "decisiones")
    root = tree.getroot()
    decision = ET.SubElement(root, "decision", id=siguiente_id(root, "decision"))

    datos = {
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "area": area,
        "variable": variable,
        "valor": valor,
        "observacion": observacion,
        "regla": resultado.get("nombre", "Sin regla aplicable"),
        "recomendacion": resultado.get("recomendacion", resultado.get("mensaje", "")),
        "prioridad": resultado.get("prioridad", "N/A"),
    }

    for clave, valor_item in datos.items():
        ET.SubElement(decision, clave).text = valor_item

    guardar_xml(tree, DECISIONES_XML)
    return decision.get("id")


def promedio_utilidad():
    retro = obtener_retroalimentaciones()
    calificaciones = []
    for item in retro:
        try:
            calificaciones.append(float(item["calificacion"]))
        except ValueError:
            pass
    if not calificaciones:
        return "0.0"
    return f"{sum(calificaciones) / len(calificaciones):.1f}"


def contar_recomendaciones():
    return sum(1 for decision in obtener_decisiones() if decision["prioridad"] != "N/A")


@app.route("/")
def dashboard():
    reglas = cargar_reglas(REGLAS_XML)
    decisiones = obtener_decisiones()
    return render_template(
        "dashboard.html",
        active="dashboard",
        total_reglas=len(reglas),
        total_decisiones=len(decisiones),
        total_recomendaciones=contar_recomendaciones(),
        promedio_utilidad=promedio_utilidad(),
        recientes=decisiones[:5],
    )


@app.route("/reglas", methods=["GET", "POST"])
def reglas():
    if request.method == "POST":
        tree = leer_xml(REGLAS_XML, "reglas")
        root = tree.getroot()
        regla = ET.SubElement(root, "regla", id=siguiente_id(root, "regla"))

        campos = {
            "nombre": request.form.get("nombre", ""),
            "area": request.form.get("area", ""),
            "variable": request.form.get("variable", ""),
            "operador": request.form.get("operador", ""),
            "valor": request.form.get("valor", ""),
            "recomendacion": request.form.get("recomendacion", ""),
            "prioridad": request.form.get("prioridad", ""),
        }

        for clave, valor in campos.items():
            ET.SubElement(regla, clave).text = valor.strip()

        guardar_xml(tree, REGLAS_XML)
        flash("Regla de conocimiento registrada correctamente.", "success")
        return redirect(url_for("reglas"))

    return render_template(
        "reglas.html",
        active="reglas",
        reglas=cargar_reglas(REGLAS_XML),
        areas=AREAS,
        operadores=OPERADORES,
        prioridades=PRIORIDADES,
    )


@app.route("/evaluar", methods=["GET", "POST"])
def evaluar():
    resultado = None
    decision_id = None
    if request.method == "POST":
        area = request.form.get("area", "")
        variable = request.form.get("variable", "")
        valor = request.form.get("valor", "")
        observacion = request.form.get("observacion", "")

        resultado = evaluar_decision(area, variable, valor, REGLAS_XML)
        decision_id = guardar_decision(area, variable, valor, observacion, resultado)
        flash("Decision evaluada y guardada en reportes.", "success")

    return render_template(
        "evaluar.html",
        active="evaluar",
        areas=AREAS,
        resultado=resultado,
        decision_id=decision_id,
    )


@app.route("/whatif", methods=["GET", "POST"])
def whatif():
    interpretacion = None
    if request.method == "POST":
        area = request.form.get("area", "")
        variable = request.form.get("variable", "")
        actual = request.form.get("valor_actual", "")
        simulado = request.form.get("valor_simulado", "")
        interpretacion = generar_interpretacion(area, variable, actual, simulado)

    return render_template(
        "whatif.html",
        active="whatif",
        areas=AREAS,
        interpretacion=interpretacion,
    )


def generar_interpretacion(area, variable, actual, simulado):
    """Genera una lectura sencilla del cambio simulado."""
    try:
        actual_num = float(actual.replace(",", "."))
        simulado_num = float(simulado.replace(",", "."))
    except ValueError:
        return (
            f"En {area}, el cambio propuesto para {variable} permite comparar "
            "dos escenarios cualitativos y preparar una decision gerencial."
        )

    diferencia = simulado_num - actual_num
    tendencia = "aumenta" if diferencia > 0 else "disminuye" if diferencia < 0 else "se mantiene"
    variable_limpia = variable.replace("_", " ")

    if variable == "stock_actual" and simulado_num < actual_num:
        efecto = "el riesgo de desabastecimiento aumenta"
    elif variable in {"gasto_mensual", "retrasos_ruta"} and simulado_num > actual_num:
        efecto = "la presion operativa aumenta y requiere seguimiento"
    elif variable == "dias_sin_compra" and simulado_num > actual_num:
        efecto = "el riesgo de perdida del cliente aumenta"
    else:
        efecto = "el escenario debe revisarse con indicadores complementarios"

    return (
        f"Si {variable_limpia} {tendencia} de {actual} a {simulado} en {area}, "
        f"{efecto}."
    )


@app.route("/retroalimentacion", methods=["GET", "POST"])
def retroalimentacion():
    if request.method == "POST":
        tree = leer_xml(RETRO_XML, "retroalimentaciones")
        root = tree.getroot()
        nodo = ET.SubElement(root, "retroalimentacion", id=siguiente_id(root, "retroalimentacion"))

        campos = {
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "decision_id": request.form.get("decision_id", ""),
            "calificacion": request.form.get("calificacion", ""),
            "comentario": request.form.get("comentario", ""),
        }
        for clave, valor in campos.items():
            ET.SubElement(nodo, clave).text = valor.strip()

        guardar_xml(tree, RETRO_XML)
        flash("Retroalimentacion registrada. Gracias por mejorar el conocimiento organizacional.", "success")
        return redirect(url_for("retroalimentacion"))

    return render_template(
        "retroalimentacion.html",
        active="retroalimentacion",
        decisiones=obtener_decisiones(),
        retroalimentaciones=obtener_retroalimentaciones(),
        promedio=promedio_utilidad(),
    )


@app.route("/reportes")
def reportes():
    return render_template(
        "reportes.html",
        active="reportes",
        decisiones=obtener_decisiones(),
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)

"""Aplicación web Nexus-Corp SDBCC.

Prototipo universitario de un Sistema de Gestión de Decisiones Basado
en Conocimiento usando Flask, XML y un motor de reglas en Python.
"""

from datetime import datetime
from functools import wraps
import hashlib
from pathlib import Path
import xml.etree.ElementTree as ET

from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.utils import secure_filename

from motor_reglas import cargar_reglas, evaluar_decision


app = Flask(__name__)
app.secret_key = "nexus-corp-kbdss-demo"

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
REGLAS_XML = DATA_DIR / "reglas.xml"
DECISIONES_XML = DATA_DIR / "decisiones.xml"
RETRO_XML = DATA_DIR / "retroalimentacion.xml"
USUARIOS_XML = DATA_DIR / "usuarios.xml"
AUDITORIA_XML = DATA_DIR / "auditoria.xml"
CONFIG_XML = DATA_DIR / "configuracion.xml"
UPLOAD_DIR = BASE_DIR / "static" / "uploads"


AREAS = ["Ventas", "Inventario", "Logística", "Finanzas", "Atención al cliente", "Gerencia"]
OPERADORES = ["menor que", "mayor que", "igual a", "contiene"]
PRIORIDADES = ["Baja", "Media", "Alta"]
ESTADOS_REGLA = ["Activa", "En revisión", "Actualizada", "Descartada", "Inactiva"]
EXTENSIONES_IMAGEN = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
ROLES = [
    "Administrador del sistema",
    "Administrador de conocimiento",
    "Experto",
    "Decisor o gerente",
    "Analista",
]

PERMISOS = {
    "Administrador del sistema": {
        "dashboard",
        "usuarios",
        "reglas",
        "evaluar",
        "whatif",
        "retroalimentacion",
        "reportes",
        "auditoria",
    },
    "Administrador de conocimiento": {"dashboard", "reglas", "retroalimentacion", "reportes"},
    "Experto": {"dashboard", "reglas", "retroalimentacion"},
    "Decisor o gerente": {"dashboard", "evaluar", "whatif", "retroalimentacion", "reportes"},
    "Analista": {"dashboard", "retroalimentacion", "reportes"},
}


def asegurar_archivo_xml(ruta, raiz):
    """Crea un archivo XML vacío si no existe."""
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


def cifrar_contrasena(contrasena):
    """Genera un resumen SHA-256 para las contraseñas del prototipo."""
    return hashlib.sha256(contrasena.encode("utf-8")).hexdigest()


def obtener_usuarios():
    tree = leer_xml(USUARIOS_XML, "usuarios")
    usuarios = []
    for nodo in tree.getroot().findall("usuario"):
        usuarios.append(
            {
                "id": nodo.get("id", ""),
                "nombre": nodo.findtext("nombre", default=""),
                "usuario": nodo.findtext("usuario", default=""),
                "rol": nodo.findtext("rol", default=""),
                "area": nodo.findtext("area", default=""),
                "estado": nodo.findtext("estado", default="Activo"),
                "contrasena": nodo.findtext("contrasena", default=""),
            }
        )
    return usuarios


def buscar_usuario(nombre_usuario):
    for usuario in obtener_usuarios():
        if usuario["usuario"].lower() == (nombre_usuario or "").strip().lower():
            return usuario
    return None


def usuario_actual():
    if "usuario" not in session:
        return None
    return session["usuario"]


def puede(permiso):
    usuario = usuario_actual()
    if not usuario:
        return False
    return permiso in PERMISOS.get(usuario["rol"], set())


def requiere_login(funcion):
    @wraps(funcion)
    def envoltura(*args, **kwargs):
        if "usuario" not in session:
            flash("Debe iniciar sesión para acceder al sistema.", "warning")
            return redirect(url_for("login"))
        return funcion(*args, **kwargs)

    return envoltura


def requiere_permiso(permiso):
    def decorador(funcion):
        @wraps(funcion)
        def envoltura(*args, **kwargs):
            if "usuario" not in session:
                flash("Debe iniciar sesión para acceder al sistema.", "warning")
                return redirect(url_for("login"))
            if not puede(permiso):
                registrar_auditoria("Acceso denegado", f"Intento de acceso a {permiso}")
                flash("Su rol no tiene permiso para acceder a este módulo.", "error")
                return redirect(url_for("dashboard"))
            return funcion(*args, **kwargs)

        return envoltura

    return decorador


def registrar_auditoria(accion, detalle):
    tree = leer_xml(AUDITORIA_XML, "auditorias")
    root = tree.getroot()
    nodo = ET.SubElement(root, "auditoria", id=siguiente_id(root, "auditoria"))
    usuario = usuario_actual() or {"nombre": "Sistema", "usuario": "sistema", "rol": "Sistema"}
    campos = {
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "usuario": usuario["usuario"],
        "nombre": usuario["nombre"],
        "rol": usuario["rol"],
        "accion": accion,
        "detalle": detalle,
    }
    for clave, valor in campos.items():
        ET.SubElement(nodo, clave).text = valor
    guardar_xml(tree, AUDITORIA_XML)


def obtener_auditorias():
    tree = leer_xml(AUDITORIA_XML, "auditorias")
    eventos = []
    for nodo in tree.getroot().findall("auditoria"):
        eventos.append(
            {
                "fecha": nodo.findtext("fecha", default=""),
                "usuario": nodo.findtext("usuario", default=""),
                "nombre": nodo.findtext("nombre", default=""),
                "rol": nodo.findtext("rol", default=""),
                "accion": nodo.findtext("accion", default=""),
                "detalle": nodo.findtext("detalle", default=""),
            }
        )
    return list(reversed(eventos))


def obtener_configuracion_empresa():
    """Lee la configuración visual de la empresa."""
    tree = leer_xml(CONFIG_XML, "configuracion")
    root = tree.getroot()
    empresa = root.find("empresa")
    if empresa is None:
        empresa = ET.SubElement(root, "empresa")
        ET.SubElement(empresa, "nombre").text = "Nexus-Corp"
        ET.SubElement(empresa, "logo").text = ""
        guardar_xml(tree, CONFIG_XML)

    return {
        "nombre": empresa.findtext("nombre", default="Nexus-Corp"),
        "logo": empresa.findtext("logo", default=""),
    }


def guardar_configuracion_empresa(nombre, logo):
    tree = leer_xml(CONFIG_XML, "configuracion")
    root = tree.getroot()
    empresa = root.find("empresa")
    if empresa is None:
        empresa = ET.SubElement(root, "empresa")

    for etiqueta, valor in {"nombre": nombre, "logo": logo}.items():
        nodo = empresa.find(etiqueta)
        if nodo is None:
            nodo = ET.SubElement(empresa, etiqueta)
        nodo.text = valor

    guardar_xml(tree, CONFIG_XML)


@app.context_processor
def contexto_usuario():
    return {
        "usuario_actual": usuario_actual(),
        "puede": puede,
        "empresa": obtener_configuracion_empresa(),
    }


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
                "usuario": nodo.findtext("usuario", default=""),
                "regla": nodo.findtext("regla", default=""),
                "recomendacion": nodo.findtext("recomendacion", default=""),
                "prioridad": nodo.findtext("prioridad", default=""),
            }
        )
    return list(reversed(decisiones))


def convertir_fecha_decision(fecha_texto):
    """Convierte la fecha guardada en XML para poder filtrarla."""
    try:
        return datetime.strptime(fecha_texto, "%Y-%m-%d %H:%M")
    except ValueError:
        return None


def filtrar_decisiones_por_fecha(decisiones, fecha_inicio="", fecha_fin=""):
    """Filtra decisiones por rango de fechas recibido desde el tablero."""
    inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d") if fecha_inicio else None
    fin = datetime.strptime(fecha_fin, "%Y-%m-%d").replace(hour=23, minute=59) if fecha_fin else None
    filtradas = []

    for decision in decisiones:
        fecha = convertir_fecha_decision(decision["fecha"])
        if fecha is None:
            continue
        if inicio and fecha < inicio:
            continue
        if fin and fecha > fin:
            continue
        filtradas.append(decision)

    return filtradas


def construir_datos_graficas(decisiones):
    """Prepara datos agregados para las gráficas del tablero."""
    areas = {area: 0 for area in AREAS}
    prioridades = {"Alta": 0, "Media": 0, "Baja": 0, "Sin prioridad": 0}
    fechas = {}

    for decision in decisiones:
        area = decision["area"]
        prioridad = decision["prioridad"]
        fecha = decision["fecha"][:10]
        areas[area] = areas.get(area, 0) + 1
        prioridades[prioridad] = prioridades.get(prioridad, 0) + 1
        fechas[fecha] = fechas.get(fecha, 0) + 1

    return {
        "areas": {"etiquetas": list(areas.keys()), "valores": list(areas.values())},
        "prioridades": {
            "etiquetas": list(prioridades.keys()),
            "valores": list(prioridades.values()),
        },
        "fechas": {
            "etiquetas": sorted(fechas.keys()),
            "valores": [fechas[fecha] for fecha in sorted(fechas.keys())],
        },
    }


def obtener_retroalimentaciones():
    tree = leer_xml(RETRO_XML, "retroalimentaciones")
    items = []
    for nodo in tree.getroot().findall("retroalimentacion"):
        items.append(
            {
                "fecha": nodo.findtext("fecha", default=""),
                "decision_id": nodo.findtext("decision_id", default=""),
                "calificacion": nodo.findtext("calificacion", default=""),
                "util": nodo.findtext("util", default=""),
                "comentario": nodo.findtext("comentario", default=""),
                "resultado": nodo.findtext("resultado", default=""),
                "sugerencia": nodo.findtext("sugerencia", default=""),
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
        "usuario": usuario_actual()["usuario"] if usuario_actual() else "sin_usuario",
        "regla": resultado.get("nombre", "Sin regla aplicable"),
        "recomendacion": resultado.get("recomendacion", resultado.get("mensaje", "")),
        "prioridad": resultado.get("prioridad", "Sin prioridad"),
    }

    for clave, valor_item in datos.items():
        ET.SubElement(decision, clave).text = valor_item

    guardar_xml(tree, DECISIONES_XML)
    registrar_auditoria("Evaluación de decisión", f"{area} / {variable} = {valor}")
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
    return sum(1 for decision in obtener_decisiones() if decision["prioridad"] != "Sin prioridad")


def contar_recomendaciones_utiles():
    utiles = 0
    for item in obtener_retroalimentaciones():
        try:
            if float(item["calificacion"]) >= 4:
                utiles += 1
        except ValueError:
            pass
    return utiles


def contar_reglas_activas(reglas):
    return sum(1 for regla in reglas if regla.get("estado", "Activa") in {"Activa", "Actualizada"})


@app.route("/")
@requiere_login
@requiere_permiso("dashboard")
def dashboard():
    reglas = cargar_reglas(REGLAS_XML)
    fecha_inicio = request.args.get("fecha_inicio", "")
    fecha_fin = request.args.get("fecha_fin", "")
    decisiones = filtrar_decisiones_por_fecha(obtener_decisiones(), fecha_inicio, fecha_fin)
    return render_template(
        "dashboard.html",
        active="dashboard",
        total_reglas=contar_reglas_activas(reglas),
        total_decisiones=len(decisiones),
        total_recomendaciones=sum(1 for decision in decisiones if decision["prioridad"] != "Sin prioridad"),
        total_utiles=contar_recomendaciones_utiles(),
        promedio_utilidad=promedio_utilidad(),
        recientes=decisiones[:5],
        datos_graficas=construir_datos_graficas(decisiones),
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
    )


@app.route("/reglas", methods=["GET", "POST"])
@requiere_login
@requiere_permiso("reglas")
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
            "experto": request.form.get("experto", usuario_actual()["nombre"]),
            "fecha_creacion": datetime.now().strftime("%Y-%m-%d"),
            "estado": request.form.get("estado", "Activa"),
        }

        for clave, valor in campos.items():
            ET.SubElement(regla, clave).text = valor.strip()

        guardar_xml(tree, REGLAS_XML)
        registrar_auditoria("Creación de regla", campos["nombre"])
        flash("Regla de conocimiento registrada correctamente.", "success")
        return redirect(url_for("reglas"))

    return render_template(
        "reglas.html",
        active="reglas",
        reglas=cargar_reglas(REGLAS_XML),
        areas=AREAS,
        operadores=OPERADORES,
        prioridades=PRIORIDADES,
        estados=ESTADOS_REGLA,
    )


@app.route("/evaluar", methods=["GET", "POST"])
@requiere_login
@requiere_permiso("evaluar")
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
        flash("Decisión evaluada y guardada en reportes.", "success")

    return render_template(
        "evaluar.html",
        active="evaluar",
        areas=AREAS,
        resultado=resultado,
        decision_id=decision_id,
    )


@app.route("/whatif", methods=["GET", "POST"])
@requiere_login
@requiere_permiso("whatif")
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
            "dos escenarios cualitativos y preparar una decisión gerencial."
        )

    diferencia = simulado_num - actual_num
    tendencia = "aumenta" if diferencia > 0 else "disminuye" if diferencia < 0 else "se mantiene"
    variable_limpia = variable.replace("_", " ")

    if variable == "stock_actual" and simulado_num < actual_num:
        efecto = "el riesgo de desabastecimiento aumenta"
    elif variable in {"gasto_mensual", "retrasos_ruta"} and simulado_num > actual_num:
        efecto = "la presión operativa aumenta y requiere seguimiento"
    elif variable == "dias_sin_compra" and simulado_num > actual_num:
        efecto = "el riesgo de pérdida del cliente aumenta"
    else:
        efecto = "el escenario debe revisarse con indicadores complementarios"

    return (
        f"Si {variable_limpia} {tendencia} de {actual} a {simulado} en {area}, "
        f"{efecto}."
    )


@app.route("/retroalimentacion", methods=["GET", "POST"])
@requiere_login
@requiere_permiso("retroalimentacion")
def retroalimentacion():
    if request.method == "POST":
        tree = leer_xml(RETRO_XML, "retroalimentaciones")
        root = tree.getroot()
        nodo = ET.SubElement(root, "retroalimentacion", id=siguiente_id(root, "retroalimentacion"))

        campos = {
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "decision_id": request.form.get("decision_id", ""),
            "util": request.form.get("util", ""),
            "calificacion": request.form.get("calificacion", ""),
            "comentario": request.form.get("comentario", ""),
            "resultado": request.form.get("resultado", ""),
            "sugerencia": request.form.get("sugerencia", ""),
        }
        for clave, valor in campos.items():
            ET.SubElement(nodo, clave).text = valor.strip()

        guardar_xml(tree, RETRO_XML)
        registrar_auditoria("Registro de retroalimentación", f"Decisión #{campos['decision_id']}")
        flash("Retroalimentación registrada. Gracias por mejorar el conocimiento organizacional.", "success")
        return redirect(url_for("retroalimentacion"))

    return render_template(
        "retroalimentacion.html",
        active="retroalimentacion",
        decisiones=obtener_decisiones(),
        retroalimentaciones=obtener_retroalimentaciones(),
        promedio=promedio_utilidad(),
    )


@app.route("/reportes")
@requiere_login
@requiere_permiso("reportes")
def reportes():
    return render_template(
        "reportes.html",
        active="reportes",
        decisiones=obtener_decisiones(),
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        nombre_usuario = request.form.get("usuario", "")
        contrasena = request.form.get("contrasena", "")
        usuario = buscar_usuario(nombre_usuario)

        if (
            usuario
            and usuario["estado"] == "Activo"
            and usuario["contrasena"] == cifrar_contrasena(contrasena)
        ):
            session["usuario"] = {
                "id": usuario["id"],
                "nombre": usuario["nombre"],
                "usuario": usuario["usuario"],
                "rol": usuario["rol"],
                "area": usuario["area"],
            }
            registrar_auditoria("Inicio de sesión", "Acceso correcto al sistema")
            return redirect(url_for("dashboard"))

        flash("Usuario o contraseña incorrectos.", "error")

    return render_template("login.html", active="login")


@app.route("/logout")
@requiere_login
def logout():
    registrar_auditoria("Cierre de sesión", "Salida del sistema")
    session.clear()
    flash("Sesión cerrada correctamente.", "success")
    return redirect(url_for("login"))


@app.route("/usuarios", methods=["GET", "POST"])
@requiere_login
@requiere_permiso("usuarios")
def usuarios():
    if request.method == "POST":
        tree = leer_xml(USUARIOS_XML, "usuarios")
        root = tree.getroot()
        nombre_usuario = request.form.get("usuario", "").strip()

        if buscar_usuario(nombre_usuario):
            flash("Ya existe un usuario con ese nombre de acceso.", "error")
            return redirect(url_for("usuarios"))

        nodo = ET.SubElement(root, "usuario", id=siguiente_id(root, "usuario"))
        campos = {
            "nombre": request.form.get("nombre", ""),
            "usuario": nombre_usuario,
            "contrasena": cifrar_contrasena(request.form.get("contrasena", "")),
            "rol": request.form.get("rol", ""),
            "area": request.form.get("area", ""),
            "estado": request.form.get("estado", "Activo"),
        }
        for clave, valor in campos.items():
            ET.SubElement(nodo, clave).text = valor.strip()

        guardar_xml(tree, USUARIOS_XML)
        registrar_auditoria("Creación de usuario", nombre_usuario)
        flash("Usuario creado correctamente.", "success")
        return redirect(url_for("usuarios"))

    return render_template(
        "usuarios.html",
        active="usuarios",
        usuarios=obtener_usuarios(),
        roles=ROLES,
        areas=AREAS,
        empresa_config=obtener_configuracion_empresa(),
    )


@app.route("/empresa-imagen", methods=["POST"])
@requiere_login
@requiere_permiso("usuarios")
def empresa_imagen():
    nombre_empresa = request.form.get("nombre_empresa", "Nexus-Corp").strip() or "Nexus-Corp"
    configuracion_actual = obtener_configuracion_empresa()
    archivo = request.files.get("logo")
    nombre_logo = configuracion_actual["logo"]

    if archivo and archivo.filename:
        extension = Path(archivo.filename).suffix.lower()
        if extension not in EXTENSIONES_IMAGEN:
            flash("Formato de imagen no permitido. Use PNG, JPG, GIF o WEBP.", "error")
            return redirect(url_for("usuarios"))

        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        nombre_seguro = secure_filename(archivo.filename)
        nombre_logo = f"empresa_{datetime.now().strftime('%Y%m%d%H%M%S')}_{nombre_seguro}"
        archivo.save(UPLOAD_DIR / nombre_logo)

    guardar_configuracion_empresa(nombre_empresa, nombre_logo)
    registrar_auditoria("Actualización de imagen corporativa", nombre_empresa)
    flash("Imagen corporativa actualizada correctamente.", "success")
    return redirect(url_for("usuarios"))


@app.route("/auditoria")
@requiere_login
@requiere_permiso("auditoria")
def auditoria():
    return render_template("auditoria.html", active="auditoria", auditorias=obtener_auditorias())


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)

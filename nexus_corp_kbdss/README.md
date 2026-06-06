# Nexus-Corp KBDSS

Prototipo funcional universitario de un Sistema de Gestion de Decisiones Basado en Conocimiento para una empresa guatemalteca ficticia.

## Instalacion y ejecucion

1. Crear un entorno virtual, opcional pero recomendado:

```bash
python -m venv .venv
```

2. Activar el entorno virtual en Windows:

```bash
.venv\Scripts\activate
```

3. Instalar Flask:

```bash
pip install -r requirements.txt
```

4. Ejecutar la aplicacion:

```bash
python app.py
```

5. Abrir el navegador en:

```text
http://127.0.0.1:5000
```

## Datos de prueba

El archivo `data/reglas.xml` incluye reglas iniciales para Inventario, Ventas, Logistica y Finanzas. Tambien existen datos base en `data/decisiones.xml` y `data/retroalimentacion.xml` para mostrar KPIs y reportes desde el primer uso.

## Cumplimiento de fases del proyecto

### 1. Diseno organizacional y conocimiento

El sistema captura conocimiento experto mediante el formulario de reglas. Ese conocimiento tacito se convierte en reglas explicitas guardadas en XML con area, variable, operador, valor, recomendacion y prioridad. El dashboard muestra un mapa de conocimiento simple: expertos, reglas XML, motor Python y decision gerencial.

### 2. Ingenieria de software

La aplicacion usa Flask como backend, plantillas HTML para la interfaz, CSS y JavaScript para la experiencia visual, archivos XML como almacenamiento y `motor_reglas.py` como modulo separado. Esta division permite explicar una arquitectura modular: interfaz, controlador Flask, motor de reglas y base de conocimiento.

### 3. Toma de decisiones

El usuario evalua datos de una situacion real, el motor compara los valores contra `reglas.xml` y devuelve recomendaciones automaticas. La pantalla What-if permite simular cambios, la seccion de retroalimentacion califica la utilidad de las recomendaciones y los reportes conservan el historial de decisiones evaluadas.

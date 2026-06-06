# Nexus-Corp SDBCC

Prototipo funcional universitario de un Sistema de Decisiones Basado en Conocimiento Corporativo para una empresa guatemalteca ficticia.

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

El archivo `data/reglas.xml` incluye reglas iniciales para Inventario, Ventas, Logística y Finanzas. También existen datos base en `data/decisiones.xml` y `data/retroalimentacion.xml` para mostrar indicadores y reportes desde el primer uso.

## Base de datos recomendada

La base de datos recomendada es SQLite. Se integraría como un archivo local en `data/nexus_corp.db`, usando un módulo nuevo llamado `repositorio_datos.py` para centralizar consultas y registros. La propuesta completa está en `PROPUESTA_BASE_DATOS.md`.

## Cumplimiento de fases del proyecto

### 1. Diseño organizacional y conocimiento

El sistema captura conocimiento experto mediante el formulario de reglas. Ese conocimiento tácito se convierte en reglas explícitas guardadas en XML con área, variable, operador, valor, recomendación y prioridad. El tablero muestra un mapa de conocimiento simple: expertos, reglas XML, motor Python y decisión gerencial.

### 2. Ingeniería de software

La aplicación usa Flask como servidor, plantillas HTML para la interfaz, CSS y JavaScript para la experiencia visual, archivos XML como almacenamiento y `motor_reglas.py` como módulo separado. Esta división permite explicar una arquitectura modular: interfaz, controlador Flask, motor de reglas y base de conocimiento.

### 3. Toma de decisiones

El usuario evalúa datos de una situación real, el motor compara los valores contra `reglas.xml` y devuelve recomendaciones automáticas. La pantalla de escenarios permite simular cambios, la sección de retroalimentación califica la utilidad de las recomendaciones y los reportes conservan el historial de decisiones evaluadas.

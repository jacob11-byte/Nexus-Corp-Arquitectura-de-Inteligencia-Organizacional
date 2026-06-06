# Propuesta de base de datos

## Recomendación principal: SQLite

Para este prototipo universitario conviene usar SQLite, porque guarda toda la información en un solo archivo y no necesita instalar un servidor de base de datos. El archivo podría ubicarse en:

```text
data/nexus_corp.db
```

## Dónde se integraría

La integración ideal sería crear un archivo nuevo:

```text
repositorio_datos.py
```

Ese archivo reemplazaría gradualmente las funciones que hoy leen y escriben XML en `app.py`. Por ejemplo:

- `obtener_decisiones()`
- `guardar_decision()`
- `obtener_retroalimentaciones()`
- `guardar retroalimentación`
- `cargar_reglas()`

## Tablas sugeridas

```sql
CREATE TABLE reglas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    area TEXT NOT NULL,
    variable TEXT NOT NULL,
    operador TEXT NOT NULL,
    valor TEXT NOT NULL,
    recomendacion TEXT NOT NULL,
    prioridad TEXT NOT NULL
);

CREATE TABLE decisiones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT NOT NULL,
    area TEXT NOT NULL,
    variable TEXT NOT NULL,
    valor TEXT NOT NULL,
    observacion TEXT,
    regla TEXT,
    recomendacion TEXT,
    prioridad TEXT
);

CREATE TABLE retroalimentaciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT NOT NULL,
    decision_id INTEGER,
    calificacion INTEGER NOT NULL,
    comentario TEXT,
    FOREIGN KEY (decision_id) REFERENCES decisiones(id)
);
```

## Alternativa para una versión más grande

Si el sistema creciera para varios usuarios, sedes o muchos registros, la opción más sólida sería PostgreSQL. Para la presentación universitaria, SQLite es suficiente, más simple de explicar y compatible con Python usando el módulo `sqlite3`.

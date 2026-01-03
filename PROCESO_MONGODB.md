# Guía Detallada del Proceso con MongoDB

Este documento explica de forma exhaustiva el ciclo de vida de los datos en MongoDB dentro del proyecto **Metro-GraphRAG Madrid Benchmark**, desde la configuración inicial hasta la ejecución de consultas complejas.

---

## 1. Configuración y Conexión

El proyecto utiliza **MongoDB** como base de datos documental para almacenar información rica en metadatos.

*   **Tecnología**: Python con el driver oficial `pymongo`.
*   **URI de Conexión**: Definida en la variable de entorno `MONGODB_URI` (por defecto `mongodb://localhost:27017/`).
*   **Base de Datos**: `metro_campus_db`.
*   **Colecciones**: `lineas`, `estaciones`, `campus`.

---

## 2. Modelado de Datos (Esquema Docuemental)

Se ha optado por un modelo híbrido que combina **referencias** (para relaciones 1:N y M:N extensas) y **embebido** (para datos que siempre se consultan juntos).

### A. Colección `lineas`
Almacena el "esqueleto" de la red de metro.
*   `numero`: Entero (ID natural, ej: 6).
*   `nombre`: Nombre descriptivo (ej: "Circular").
*   `color`: Código hexadecimal.
*   `estaciones_ids`: **Array de ObjectIds** que referencian a la colección `estaciones`, manteniendo el orden físico de las paradas.

### B. Colección `estaciones`
Contiene el detalle de cada parada.
*   `id`: Slug único (ej: `est_l6_014`).
*   `nombre`: Nombre de la estación.
*   `zona_tarifaria`: Zona (A, B1, B2, etc.).
*   `tiene_renfe`: Booleano para correspondencias.
*   `coordenadas`: Objeto con `lat` y `lng` (preparado para índices geoespaciales).
*   `lineas`: Lista de números de línea que pasan por allí.

### C. Colección `campus`
Almacena recintos universitarios y su oferta académica.
*   `nombre` y `universidad`: Metadatos principales.
*   **Embebido (`estudios`)**: Lista de documentos con Grados y Másteres. Se embeben porque un estudio no existe sin su campus en este contexto.
*   **Referencias (`estaciones_cercanas`)**: Lista de objetos que contienen un `estacion_id` (ObjectId) apuntando a la colección `estaciones`.

---

## 3. El Proceso de Carga (Core Logic)

El script `scripts/mongodb/load_data.py` realiza una "coreografía" de 4 pasos para asegurar la integridad referencial:

### Paso 1: Limpieza e Inserción de Líneas
1. Se eliminan las colecciones existentes (`drop()`).
2. Se insertan las líneas desde `lineas.json`.
3. **Punto Clave**: Se genera el `linea_id_map`, un diccionario que guarda `{numero_linea: ObjectId_generado}`.

### Paso 2: Inserción de Estaciones
1. Se cargan desde `estaciones.json`.
2. Se insertan en la colección `estaciones`.
3. **Punto Clave**: Se genera el `estacion_id_map`, un diccionario que guarda `{id_slug: ObjectId_generado}`.

### Paso 3: Vinculación Línea-Estación (`_update_lineas_with_estaciones`)
Como las líneas se insertaron antes que las estaciones, inicialmente no tenían sus IDs vinculados. El script:
1. Agrupa las estaciones por línea.
2. Las ordena según su índice.
3. Actualiza el documento de la línea en la base de datos inyectando el array de ObjectIds correcto usando el `linea_id_map` para localizar la línea.

### Paso 4: Carga de Campus y Estudios
1. Se procesa `campus.json`.
2. Para cada estación cercana, el script busca su `ObjectId` real en el `estacion_id_map` y lo guarda en el documento del campus.
3. Se inserta el documento completo (con los estudios ya embebidos).

---

## 4. Estrategia de Indexación

Para garantizar consultas instantáneas (especialmente para el agente RAG), se crean los siguientes índices:

*   **Estaciones**: Índice por `nombre` (búsquedas directas), `zona_tarifaria` (filtros), `lineas` (consultas multilínea) y `tiene_renfe`.
*   **Campus**: Índice por `universidad`, `nombre` y campos internos del array de estudios (`estudios.nombre`, `estudios.tipo`).
*   **Líneas**: Índice único por `numero`.

---

## 5. Consultas y Analítica

El archivo `scripts/mongodb/consultas_ejemplo.py` demuestra el potencial del modelo:

*   **Lecturas Simples**: Obtener estaciones de la L1 en orden (usando el array de referencias).
*   **Búsquedas por Atributos**: Estaciones con Renfe o campus de una universidad concreta.
*   **Agregaciones Complejas (Pipeline)**:
    *   `$size`: Para contar estaciones por línea.
    *   `$unwind` + `$group`: Para generar estadísticas de cuántos Grados y Másteres ofrece cada universidad en total.
    *   **Búsqueda Cross-Document**: Encontrar qué campus están cerca de una estación específica buscando dentro del array `estaciones_cercanas.nombre_estacion`.

---

## 6. Mantenimiento y Ejecución

Para resetear la base de datos y cargar los últimos cambios de los JSON:

```bash
# Ejecutar desde la raíz del proyecto
python3 scripts/mongodb/load_data.py
```

Para verificar que los datos son correctos y ver ejemplos de salida:

```bash
python3 scripts/mongodb/consultas_ejemplo.py
```

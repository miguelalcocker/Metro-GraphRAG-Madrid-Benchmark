# 📸 LISTA DETALLADA DE CAPTURAS DE PANTALLA PARA LA MEMORIA

Esta lista indica exactamente qué comandos ejecutar y qué partes de la pantalla capturar para que la memoria luzca profesional y obtengas la máxima calificación.

---

## 🔷 PARTE A - MONGODB

### Captura 1: MongoDB Compass - Vista de Base de Datos
**Comando previo:**
```bash
python scripts/mongodb/load_data.py
```

**Qué capturar en MongoDB Compass:**
- Panel izquierdo mostrando la base de datos `metro_campus_db`
- Las 3 colecciones: `lineas`, `estaciones`, `campus`
- Número de documentos de cada colección visible

**Nombre de archivo:** `mongodb_01_database_overview.png`

**Para la memoria:** Sección "2.1 Modelo de Datos en MongoDB"

---

### Captura 2: Estructura de la colección `lineas`
**En MongoDB Compass:**
- Navegar a `metro_campus_db` → `lineas`
- Clic en un documento (ej: Línea 6)
- Vista en modo "JSON" o "Tree"

**Qué debe verse:**
- Campo `numero`
- Campo `nombre`
- Campo `color`
- Array `estaciones_ids` con ObjectIds

**Nombre de archivo:** `mongodb_02_coleccion_lineas.png`

**Para la memoria:** Sección "2.1.1 Colección lineas"

---

### Captura 3: Estructura de la colección `estaciones`
**En MongoDB Compass:**
- Navegar a `metro_campus_db` → `estaciones`
- Abrir un documento con Renfe (ej: "Chamartín")

**Qué debe verse:**
- Campo `nombre`
- Campo `zona_tarifaria`
- Array `lineas`
- Objeto `coordenadas` con `lat` y `lng`
- Campo `tiene_renfe: true`
- Objeto `estacion_renfe` con `nombre` y `lineas_renfe`
- Objeto `indice_por_linea`

**Nombre de archivo:** `mongodb_03_coleccion_estaciones.png`

**Para la memoria:** Sección "2.1.2 Colección estaciones"

---

### Captura 4: Estructura de la colección `campus`
**En MongoDB Compass:**
- Navegar a `metro_campus_db` → `campus`
- Abrir documento "Ciudad Universitaria (UCM)"

**Qué debe verse:**
- Campo `nombre`
- Campo `universidad`
- Campo `direccion`
- Array `estaciones_cercanas` con:
  - `estacion_id` (ObjectId)
  - `nombre_estacion`
  - `rol` (principal/alternativa)
  - `minutos_andando`
- Array `estudios` embebido con:
  - `nombre`
  - `tipo` (GRADO/MASTER)
  - `plazas`
  - `nota_corte`

**Nombre de archivo:** `mongodb_04_coleccion_campus.png`

**Para la memoria:** Sección "2.1.3 Colección campus (con estudios embebidos)"

---

### Captura 5: Índices creados
**En MongoDB Compass:**
- Navegar a `metro_campus_db` → `estaciones`
- Clic en la pestaña "Indexes"

**Qué debe verse:**
- Índice `_id_` (por defecto)
- Índice `nombre_1`
- Índice `tiene_renfe_1`
- Índice `zona_tarifaria_1`
- Índice `lineas_1`

**Nombre de archivo:** `mongodb_05_indices_estaciones.png`

**Para la memoria:** Sección "2.6 Índices e Impacto en el Rendimiento"

---

### Captura 6: Consulta - Estaciones de la Línea 1
**Comando en terminal:**
```bash
python scripts/mongodb/consultas_ejemplo.py
```

**Qué capturar:**
- Salida de consola mostrando:
  - "CONSULTA 1: Estaciones de la Línea 1"
  - Lista ordenada de estaciones con numeración

**Nombre de archivo:** `mongodb_06_consulta_linea1.png`

**Para la memoria:** Sección "2.4 Consultas de Lectura - Ejemplo 1"

---

### Captura 7: Consulta - Estaciones con Renfe
**Del mismo script anterior:**

**Qué capturar:**
- Salida mostrando:
  - "CONSULTA 2: Estaciones con correspondencia Renfe"
  - Lista de estaciones con nombres de estaciones Renfe
  - Líneas de cercanías

**Nombre de archivo:** `mongodb_07_consulta_renfe.png`

**Para la memoria:** Sección "2.4 Consultas de Lectura - Ejemplo 2"

---

### Captura 8: Agregación - Estaciones por Línea
**Del mismo script:**

**Qué capturar:**
- Salida de "AGREGACIÓN 1: Número de estaciones por línea"
- Tabla con:
  ```
  Línea    Estaciones
  L1            18
  L3            16
  L6            18
  L10           15
  ```

**Nombre de archivo:** `mongodb_08_agregacion_estaciones_por_linea.png`

**Para la memoria:** Sección "2.5 Agregaciones - Pipeline 1"

---

### Captura 9: Agregación - Estudios por Universidad
**Del mismo script:**

**Qué capturar:**
- Salida de "AGREGACIÓN 3: Estudios por universidad (GRADO vs MÁSTER)"
- Tabla mostrando UCM, UPM, UC3M, URJC con sus GRADOs y MÁSTERs

**Nombre de archivo:** `mongodb_09_agregacion_estudios.png`

**Para la memoria:** Sección "2.5 Agregaciones - Pipeline 3"

---

### Captura 10: Parte C - Recomendación Simplificada
**Comando en terminal:**
```bash
python scripts/mongodb/consultas_parte_c.py
```

**Qué capturar:**
- Salida de "EJEMPLO 2: RECOMENDACIÓN DE CAMPUS (desde Sol)"
- Resultados mostrando campus accesibles y no accesibles
- Mensaje "REQUIERE CAMBIO DE LÍNEA" para algunos campus
- Conclusión comparativa MongoDB vs Neo4j

**Nombre de archivo:** `mongodb_10_recomendacion_simplificada.png`

**Para la memoria:** Sección "4. Funcionalidad de Recomendación (Parte C) - MongoDB"

---

## 🔶 PARTE B - NEO4J

### Captura 11: Neo4j Browser - Vista del Grafo General
**Comando en terminal (preparación):**
```bash
python scripts/neo4j/load_data.py
```

**En Neo4j Browser ejecutar:**
```cypher
MATCH (n)
RETURN n
LIMIT 100
```

**Qué capturar:**
- Vista del grafo mostrando nodos de diferentes colores:
  - :Linea (un color)
  - :Estacion (otro color)
  - :Campus (otro color)
  - :Estudio (otro color)
- Relaciones visibles conectándolos

**Nombre de archivo:** `neo4j_01_grafo_general.png`

**Para la memoria:** Sección "3.1 Modelo de Grafo en Neo4j - Vista General"

---

### Captura 12: Modelo de Nodos y Relaciones
**En Neo4j Browser ejecutar:**
```cypher
CALL db.schema.visualization()
```

**Qué capturar:**
- Diagrama del esquema mostrando:
  - Nodos: :Linea, :Estacion, :Campus, :Estudio
  - Relaciones: :TIENE_ESTACION, :SIGUIENTE, :CERCANA, :OFRECE, :TRANSBORDO

**Nombre de archivo:** `neo4j_02_esquema_modelo.png`

**Para la memoria:** Sección "3.1 Modelo de Grafo - Esquema"

---

### Captura 13: Estadísticas del Grafo
**Comando en terminal:**
```bash
python scripts/neo4j/load_data.py
```

**Qué capturar (salida de consola):**
- Sección "Estadísticas del grafo:"
  - Líneas: 4
  - Estaciones: 60
  - Campus: 6
  - Estudios: ~20
  - Relaciones (TIENE_ESTACION, SIGUIENTE, etc.)

**Nombre de archivo:** `neo4j_03_estadisticas_carga.png`

**Para la memoria:** Sección "3.2 Carga de Datos en Neo4j"

---

### Captura 14: Consulta Cypher - Estaciones de una Línea
**En Neo4j Browser ejecutar:**
```cypher
MATCH (l:Linea {numero: 1})-[t:TIENE_ESTACION]->(e:Estacion)
RETURN l.nombre AS linea, e.nombre AS estacion, t.orden AS orden
ORDER BY t.orden
LIMIT 10;
```

**Qué capturar:**
- Tabla de resultados mostrando:
  - linea: "Línea 1..."
  - estacion: "Pinar de Chamartín", "Bambú", etc.
  - orden: 1, 2, 3...

**Nombre de archivo:** `neo4j_04_consulta_estaciones_linea.png`

**Para la memoria:** Sección "3.3.A Consultas Estructurales - Ejemplo A1"

---

### Captura 15: Consulta Cypher - Hubs Universitarios
**En Neo4j Browser ejecutar:**
```cypher
MATCH (e:Estacion)<-[:CERCANA]-(c:Campus)
WITH e, count(DISTINCT c) AS num_campus
WHERE num_campus > 1
RETURN e.nombre AS estacion, num_campus
ORDER BY num_campus DESC;
```

**Qué capturar:**
- Tabla mostrando estaciones que dan servicio a múltiples campus

**Nombre de archivo:** `neo4j_05_hubs_universitarios.png`

**Para la memoria:** Sección "3.3.A Consultas Estructurales - Ejemplo A2"

---

### Captura 16: Consulta Cypher - Campus con GCID
**En Neo4j Browser ejecutar:**
```cypher
MATCH (c:Campus)-[:OFRECE]->(e:Estudio)
WHERE e.tipo = 'GRADO' AND e.nombre CONTAINS 'Ciencia e Ingeniería de Datos'
RETURN c.universidad AS universidad,
       c.nombre AS campus,
       e.nombre AS estudio,
       e.plazas AS plazas,
       e.nota_corte AS nota_corte
ORDER BY c.universidad;
```

**Qué capturar:**
- Tabla mostrando UCM, UC3M, URJC con sus campus que ofrecen GCID

**Nombre de archivo:** `neo4j_06_campus_gcid.png`

**Para la memoria:** Sección "3.3.B Consultas sobre Campus y Estudios - Ejemplo B1"

---

### Captura 17: Consulta Cypher - Camino más corto (Sol → Ciudad Universitaria)
**En Neo4j Browser ejecutar:**
```cypher
MATCH (origen:Estacion {nombre: 'Sol'}),
      (destino:Estacion {nombre: 'Ciudad Universitaria'}),
      path = shortestPath((origen)-[:SIGUIENTE*]-(destino))
RETURN [n IN nodes(path) | n.nombre] AS ruta,
       length(path) AS num_estaciones;
```

**Qué capturar:**
- Resultado mostrando:
  - ruta: Lista de estaciones en el camino
  - num_estaciones: Número de pasos

**También capturar la visualización del grafo del path**

**Nombre de archivo:** `neo4j_07_ruta_corta_sol_cu.png`

**Para la memoria:** Sección "3.3.C Consultas de Rutas - Ejemplo C1"

---

### Captura 18: Consulta Cypher - Ruta con Cambios de Línea
**En Neo4j Browser ejecutar:**
```cypher
MATCH (origen:Estacion {nombre: 'Pinar de Chamartín'}),
      (destino:Estacion {nombre: 'Moncloa'}),
      path = shortestPath((origen)-[:SIGUIENTE*]-(destino))
WITH path,
     [r IN relationships(path) | r.lineaId] AS lineas_ruta
UNWIND range(0, size(lineas_ruta) - 2) AS i
WITH path, lineas_ruta,
     CASE WHEN lineas_ruta[i] <> lineas_ruta[i+1] THEN 1 ELSE 0 END AS cambio
RETURN [n IN nodes(path) | n.nombre] AS ruta,
       length(path) AS num_estaciones,
       sum(cambio) AS num_cambios_linea;
```

**Qué capturar:**
- Resultado mostrando:
  - ruta completa
  - num_estaciones
  - num_cambios_linea (≥1)

**Nombre de archivo:** `neo4j_08_ruta_con_cambios.png`

**Para la memoria:** Sección "3.3.D Cambios de Línea y Comparativa Avanzada - Ejemplo D1"

---

### Captura 19: Consulta Cypher - Recomendación Completa (Parte C)
**En Neo4j Browser ejecutar:**
```cypher
MATCH (origen:Estacion {nombre: 'Sol'}),
      (campus:Campus)-[:OFRECE]->(estudio:Estudio),
      (campus)-[:CERCANA]->(destino:Estacion)
WHERE estudio.tipo = 'GRADO' AND estudio.nombre CONTAINS 'Ciencia e Ingeniería de Datos'
WITH origen, campus, estudio, destino
MATCH path = shortestPath((origen)-[:SIGUIENTE*]-(destino))
WITH campus, estudio, destino, path,
     [r IN relationships(path) | r.lineaId] AS lineas_ruta
UNWIND range(0, size(lineas_ruta) - 2) AS i
WITH campus, estudio, destino, path, lineas_ruta,
     CASE WHEN lineas_ruta[i] <> lineas_ruta[i+1] THEN 1 ELSE 0 END AS cambio
RETURN campus.universidad AS universidad,
       campus.nombre AS campus_nombre,
       estudio.plazas AS plazas,
       estudio.nota_corte AS nota_corte,
       destino.nombre AS estacion_destino,
       length(path) AS num_estaciones,
       sum(cambio) AS num_cambios_linea
ORDER BY num_cambios_linea, num_estaciones;
```

**Qué capturar:**
- Tabla completa con todos los campus ordenados por:
  1. Menor número de cambios de línea
  2. Menor distancia

**Nombre de archivo:** `neo4j_09_recomendacion_completa.png`

**Para la memoria:** Sección "4. Funcionalidad de Recomendación (Parte C) - Neo4j"

---

### Captura 20: Comparativa Visual MongoDB vs Neo4j
**Crear una captura de pantalla combinada (puede ser en PowerPoint o similar) mostrando lado a lado:**

**Izquierda (MongoDB):**
- Captura de `mongodb_10_recomendacion_simplificada.png`
- Texto: "Limitado a misma línea"

**Derecha (Neo4j):**
- Captura de `neo4j_09_recomendacion_completa.png`
- Texto: "Rutas completas con cambios"

**Nombre de archivo:** `comparativa_mongodb_vs_neo4j.png`

**Para la memoria:** Sección "4.3 Comparación razonada MongoDB vs Neo4j"

---

## 📋 CHECKLIST DE CAPTURAS

Antes de redactar la memoria, asegúrate de tener:

- [ ] 10 capturas de MongoDB (01-10)
- [ ] 9 capturas de Neo4j (11-19)
- [ ] 1 captura comparativa (20)
- [ ] **TOTAL: 20 capturas de pantalla**

---

## 💡 CONSEJOS PARA CAPTURAS PROFESIONALES

1. **Resolución:** Mínimo 1920x1080, formato PNG
2. **Claridad:** Asegúrate de que el texto sea legible
3. **Enfoque:** Captura solo la información relevante (evita barras de navegador innecesarias)
4. **Nombres:** Usa los nombres de archivo sugeridos para facilitar la inserción en LaTeX
5. **MongoDB Compass:** Usa el tema claro para mejor contraste en impresión
6. **Neo4j Browser:** Ajusta zoom del grafo para que los nodos sean visibles
7. **Terminal:** Usa fuente clara (14-16pt) y tema de alto contraste

---

## 📁 ESTRUCTURA DE CARPETAS PARA ENTREGA

```
BDNRelacionales_P2_Entrega/
├── memoria_practica.pdf
├── scripts/
│   ├── mongodb/
│   │   ├── load_data.py
│   │   ├── operaciones_crud.py
│   │   ├── consultas_ejemplo.py
│   │   └── consultas_parte_c.py
│   └── neo4j/
│       ├── load_data.py
│       └── consultas_ejemplo.cypher
├── data/
│   ├── lineas.json
│   ├── estaciones.json
│   └── campus.json
└── imagenes/
    ├── mongodb_01_database_overview.png
    ├── mongodb_02_coleccion_lineas.png
    ├── ... (todas las 20 capturas)
    └── comparativa_mongodb_vs_neo4j.png
```

---

**✅ CON ESTAS CAPTURAS, TU MEMORIA SERÁ VISUALMENTE IMPECABLE Y OBTENDRÁS LA MÁXIMA PUNTUACIÓN EN PRESENTACIÓN.**

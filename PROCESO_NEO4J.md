# Guía Detallada del Proceso con Neo4j

Este documento explica de forma exhaustiva el ciclo de vida de los datos en Neo4j dentro del proyecto **Metro-GraphRAG Madrid Benchmark**, centrándose en la representación topológica y el cálculo de rutas.

---

## 1. Configuración y Conexión

Neo4j se utiliza como base de datos de grafos para gestionar la red de transporte y las relaciones espaciales entre centros educativos.

*   **Tecnología**: Python con el driver oficial `neo4j` y lenguaje de consultas **Cypher**.
*   **Protocolo**: `bolt://localhost:7687`.
*   **Seguridad**: Autenticación por defecto (`neo4j/password`).

---

## 2. Modelado de Datos (Esquema de Grafo)

A diferencia de MongoDB, aquí los datos se atomizan en **Nodos** y se conectan mediante **Relaciones** con propiedades.

### Nodos (Labels)
*   **`:Linea`**: Representa una línea comercial (L1, L2, L12, etc.).
*   **`:Estacion`**: El elemento central. Almacena metadatos como `zona_tarifaria`, `tiene_renfe` y coordenadas.
*   **`:Campus`**: Recintos universitarios.
*   **`:Estudio`**: Programas académicos. A diferencia de MongoDB, aquí cada estudio es un nodo independiente (permitiendo ver qué campus comparten el mismo grado).

### Relaciones (Types)
*   **`[:TIENE_ESTACION {orden: int}]`**: Conecta una `:Linea` con sus paradas.
*   **`[:SIGUIENTE {lineaId: int, tiempo_viaje: int}]`**: Define la topología de la red. Es fundamental para algoritmos de rutas.
*   **`[:TRANSBORDO {tiempo_cambio: int}]`**: Relación reflexiva (de una estación consigo misma) o entre estaciones cercanas para modelar intercambios de línea.
*   **`[:CERCANA {minutos: int, rol: string}]`**: Conecta un `:Campus` con la red de transporte.
*   **`[:OFRECE]`**: Conecta un `:Campus` con sus `:Estudio` disponibles.

---

## 3. El Proceso de Carga (Core Logic)

El script `scripts/neo4j/load_data.py` sigue un proceso incremental para construir el grafo:

### Paso 1: Creación de Nodos Base
1. **Líneas**: Se crean los nodos maestros de cada línea.
2. **Estaciones**: Se crean los nodos de estación con sus propiedades físicas.
3. **Campus y Estudios**: Se crean los campus y se realiza un `MERGE` de los estudios para evitar duplicados (un mismo estudio puede impartirse en varios campus).

### Paso 2: Construcción de la Red de Metro
1. **Pertenencia**: Se crean relaciones `[:TIENE_ESTACION]` entre líneas y sus paradas.
2. **Conectividad**: El script agrupa estaciones por línea, las ordena y crea relaciones `[:SIGUIENTE]` consecutivas, asignando tiempos de viaje estimados.
3. **Intercambiadores**: Se identifican estaciones con múltiples líneas y se crean relaciones de `[:TRANSBORDO]`.

### Paso 3: Vinculación Educativa
1. **Oferta**: Se crean las relaciones `[:OFRECE]` entre campus y estudios.
2. **Accesibilidad**: Se crean las relaciones `[:CERCANA]` entre campus y las estaciones de metro correspondientes.

---

## 4. Índices y Constraints

Para asegurar la integridad y rapidez en grafos de gran tamaño:
*   **Constraints de Unicidad**: Se obliga a que `linea.numero`, `estacion.id` y `campus.nombre` sean únicos.
*   **Índices de Búsqueda**: Se indexan `estacion.nombre`, `estudio.nombre` y `campus.universidad` para agilizar el punto de entrada de las consultas Cypher.

---

## 5. Consultas y Potencial del Grafo

El archivo `scripts/neo4j/consultas_ejemplo.cypher` explora casos de uso que serían muy complejos en una base de datos documental:

*   **Cálculo de Rutas**: Uso de `shortestPath` para encontrar el camino entre dos estaciones (ej: Sol -> Ciudad Universitaria).
*   **Análisis Multiobjetivo**: Encontrar el mejor campus para un grado específico minimizando los transbordos de metro.
*   **Estructura de Red**: Identificar "hubs" (estaciones con más conexiones o que sirven a más campus).
*   **Tiempos de Viaje**: Sumar la propiedad `tiempo_viaje` a lo largo de un path para estimar la duración total.

---

## 6. Mantenimiento y Ejecución

Para reconstruir el grafo completo (borrado y carga):

```bash
# Ejecutar desde la raíz del proyecto
python3 scripts/neo4j/load_data.py
```

Para probar consultas directas, puedes usar la consola de Neo4j o el plugin de VS Code con los ejemplos en:
`scripts/neo4j/consultas_ejemplo.cypher`

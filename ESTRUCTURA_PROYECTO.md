# Estructura del Proyecto General y Modelado de Datos

Este documento detalla la organización del proyecto **Metro-GraphRAG Madrid Benchmark**, el modelado de los datos y cómo están almacenados en las bases de datos MongoDB y Neo4j.

## 1. Estructura General del Proyecto

El proyecto está organizado de la siguiente manera:

```text
Metro-GraphRAG-Madrid-Benchmark/
├── data/                   # Datos crudos en formato JSON
│   ├── campus.json         # Información de campus y estudios
│   ├── estaciones.json     # Información detallada de estaciones de metro
│   └── lineas.json         # Definición de las líneas de metro
├── scripts/                # Scripts de utilidad y carga de datos
│   ├── mongodb/            # Scripts específicos para MongoDB
│   │   ├── load_data.py    # Carga de datos inicial en MongoDB
│   │   └── consultas_ejemplo.py
│   ├── neo4j/              # Scripts específicos para Neo4j
│   │   ├── load_data.py    # Carga de datos inicial en Neo4j
│   │   └── consultas_ejemplo.cypher
│   └── verificar_datos.sh  # Script de verificación rápida
├── src/                    # Código fuente de la aplicación
│   └── agent/              # Lógica del agente RAG (GraphRAG)
├── README.md               # Guía principal del proyecto
├── QUICKSTART.md           # Guía rápida de inicio
├── AGENT_GUIDE.md          # Documentación detallada del agente
└── requirements.txt        # Dependencias de Python
```

---

## 2. Modelado de Datos en MongoDB

MongoDB se utiliza para almacenar los datos de forma documental, priorizando la lectura rápida y el agrupamiento de información relacionada.

### Colecciones y Documentos

1.  **`lineas`**: Almacena la información de las líneas de metro.
    *   **Campos**: `numero`, `nombre`, `color`, `estaciones_ids` (referencias a estaciones).
2.  **`estaciones`**: Almacena cada estación de forma individual.
    *   **Campos**: `id` (slug), `nombre`, `zona_tarifaria`, `tiene_renfe`, `coordenadas` (geospatial), `lineas` (lista de números).
3.  **`campus`**: Almacena los campus universitarios y sus programas.
    *   **Estrategia de Embebido**: Los estudios (Grados y Másteres) se almacenan directamente dentro del documento del campus en un array `estudios`. Esto evita joins costosos para obtener la oferta académica de un campus.
    *   **Referencias**: Contiene un array `estaciones_cercanas` con referencias a los ObjectIds de la colección `estaciones`.

---

## 3. Modelado de Datos en Neo4j

Neo4j se utiliza para representar la red de transporte y la oferta educativa como un grafo interconectado, facilitando el análisis de rutas y proximidad.

### Nodos (Labels)
*   **`:Linea`**: Representa una línea de metro (L1, L2, etc.).
*   **`:Estacion`**: Representa una parada física del metro.
*   **`:Campus`**: Representa un recinto universitario.
*   **`:Estudio`**: Representa un programa académico (Ej: "Grado en Ingeniería Informática").

### Relaciones (Types)
*   **`(:Linea)-[:TIENE_ESTACION]->(:Estacion)`**: Define qué estaciones pertenecen a qué líneas, incluyendo una propiedad `orden`.
*   **`(:Estacion)-[:SIGUIENTE]->(:Estacion)`**: Conecta estaciones consecutivas en una línea. Almacena el `tiempo_viaje` y `lineaId`.
*   **`(:Estacion)-[:TRANSBORDO]->(:Estacion)`**: Relación especial para estaciones donde coinciden varias líneas, facilitando el cálculo de cambios de línea.
*   **`(:Campus)-[:CERCANA]->(:Estacion)`**: Indica la proximidad física (propiedad `minutos_andando` y `rol`).
*   **`(:Campus)-[:OFRECE]->(:Estudio)`**: Vincula los programas académicos con el campus donde se imparten.

---

## 4. Diferencias en el Almacenamiento

| Concepto | MongoDB (Documental) | Neo4j (Grafo) |
| :--- | :--- | :--- |
| **Estudios** | Embebidos dentro de `campus`. | Nodos independientes `:Estudio` relacionados con `:Campus`. |
| **Rutas** | Difíciles de calcular (requiere lógica compleja). | Naturales mediante relaciones `:SIGUIENTE`. |
| **Búsqueda Geográfica** | Índices 2dsphere nativos. | Almacena coordenadas pero el fuerte es la topología del grafo. |
| **Flexibilidad** | Ideal para metadatos ricos y extensos. | Ideal para entender conexiones y dependencias. |

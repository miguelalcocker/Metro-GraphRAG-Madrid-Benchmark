# Metro de Madrid y Universidades - Bases de Datos NoSQL

Práctica de MongoDB y Neo4j para la asignatura de Bases de Datos No Relacionales.
**Universidad Rey Juan Carlos - Curso 2025/2026**

## Descripción del Proyecto

Sistema de información que combina datos del Metro de Madrid con campus universitarios públicos (UCM, UPM, UC3M, URJC), diseñado para ser utilizado como benchmark en investigación sobre GraphRAG para ICLR 2026.

### Características principales:

- **60 estaciones reales** del Metro de Madrid (Líneas 1, 3, 6, 10)
- **6 campus universitarios** con estudios de Grado y Máster
- **Modelo híbrido**: MongoDB para datos documentales + Neo4j para análisis de rutas
- **Preparado para experimentos**: Baseline LLM vs GraphRAG

---

## Estructura del Proyecto

```
BDNRelacionales_P2/
├── data/                          # Datos en formato JSON
│   ├── lineas.json               # 4 líneas de metro
│   ├── estaciones.json           # 60 estaciones con coordenadas reales
│   └── campus.json               # 6 campus con estudios embebidos
│
├── scripts/
│   ├── mongodb/
│   │   ├── load_data.py          # Script de carga para MongoDB
│   │   └── consultas_ejemplo.py  # Consultas CRUD y agregaciones
│   │
│   └── neo4j/
│       ├── load_data.py          # Script de carga para Neo4j
│       └── consultas_ejemplo.cypher  # Consultas Cypher de ejemplo
│
├── src/
│   └── agent/                    # (Paso 4) Clase para GraphRAG
│
├── requirements.txt              # Dependencias Python
├── .env.example                  # Plantilla de configuración
└── README.md                     # Este archivo
```

---

## Requisitos Previos

### Software necesario:

1. **Python 3.8+**
2. **MongoDB** (local o MongoDB Atlas)
3. **Neo4j Desktop** o **Neo4j Aura**

### Instalación de dependencias:

```bash
pip install -r requirements.txt
```

---

## Configuración

### 1. Configurar variables de entorno

Copia el archivo de ejemplo y configura tus credenciales:

```bash
cp .env.example .env
```

Edita `.env`:

```env
# MongoDB
MONGODB_URI=mongodb://localhost:27017/

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=tu_password
```

### 2. Verificar que MongoDB está corriendo

```bash
# Si usas MongoDB local:
sudo systemctl start mongod   # Linux
brew services start mongodb-community  # macOS

# Si usas MongoDB Atlas, asegúrate de tener el URI correcto
```

### 3. Verificar que Neo4j está corriendo

```bash
# Abre Neo4j Desktop y arranca tu base de datos
# O conecta a Neo4j Aura con el URI proporcionado
```

---

## Carga de Datos

### MongoDB

```bash
cd scripts/mongodb
python load_data.py
```

**Salida esperada:**
```
✓ Conectado a MongoDB: metro_campus_db
✓ Archivo cargado: lineas.json (4 registros)
✓ Archivo cargado: estaciones.json (60 registros)
✓ Archivo cargado: campus.json (6 registros)
...
📈 Estadísticas de la base de datos:
  • Líneas: 4
  • Estaciones: 60
  • Campus: 6
  • Estaciones con Renfe: 5
  • GRADOs: 23
  • MASTERs: 14
```

### Neo4j

```bash
cd scripts/neo4j
python load_data.py
```

**Salida esperada:**
```
✓ Conectado a Neo4j: bolt://localhost:7687
...
📈 Estadísticas del grafo:
  • Líneas: 4
  • Estaciones: 60
  • Campus: 6
  • Estudios: 20 (con MERGE)

  Relaciones:
    - :TIENE_ESTACION: 74
    - :SIGUIENTE: 56
    - :TRANSBORDO: 8
    - :CERCANA: 10
    - :OFRECE: 37
```

---

## Esquema de Datos

### MongoDB - Modelo Documental

#### Colección: `lineas`
```json
{
  "_id": ObjectId("..."),
  "numero": 1,
  "nombre": "Línea 1 - Pinar de Chamartín ↔ Valdecarros",
  "color": "#38A3DC",
  "estaciones_ids": [ObjectId("..."), ...]
}
```

#### Colección: `estaciones`
```json
{
  "_id": ObjectId("..."),
  "nombre": "Sol",
  "zona_tarifaria": "A",
  "lineas": [1, 2, 3],
  "tiene_renfe": true,
  "estacion_renfe": {
    "nombre": "Sol (Cercanías)",
    "lineas_renfe": ["C3", "C4"]
  },
  "coordenadas": {"lat": 40.4169, "lng": -3.7033},
  "indice_por_linea": {"1": 12, "2": 8, "3": 10}
}
```

#### Colección: `campus`
```json
{
  "_id": ObjectId("..."),
  "nombre": "Ciudad Universitaria (UCM)",
  "universidad": "UCM",
  "direccion": "Av. Séneca, 2, 28040 Madrid",
  "estaciones_cercanas": [
    {
      "estacion_id": ObjectId("..."),
      "nombre_estacion": "Ciudad Universitaria",
      "rol": "principal",
      "minutos_andando": 5,
      "lineas": [6]
    }
  ],
  "estudios": [
    {
      "nombre": "Máster en Inteligencia Artificial",
      "tipo": "MASTER",
      "rama": "Ingeniería y Arquitectura",
      "creditos": 60
    }
  ]
}
```

**Decisiones de diseño:**
- **Estudios embebidos**: Optimiza lecturas frecuentes de campus completos
- **Referencias a estaciones**: Evita duplicación (estaciones compartidas entre líneas)
- **Índices**: En `nombre`, `tiene_renfe`, `zona_tarifaria`, `estudios.nombre`

---

### Neo4j - Modelo de Grafo

#### Nodos:
- `:Linea` - Líneas de metro
- `:Estacion` - Estaciones con coordenadas
- `:Campus` - Campus universitarios
- `:Estudio` - Grados y Másteres

#### Relaciones:
```cypher
(:Linea)-[:TIENE_ESTACION {orden}]->(:Estacion)
(:Estacion)-[:SIGUIENTE {lineaId, tiempo_viaje}]->(:Estacion)
(:Estacion)-[:TRANSBORDO {tiempo_cambio}]->(:Estacion)
(:Campus)-[:CERCANA {minutos, rol}]->(:Estacion)
(:Campus)-[:OFRECE]->(:Estudio)
```

**Ventajas:**
- Consultas de rutas con `shortestPath()`
- Cálculo de transbordos y cambios de línea
- Análisis de grafos (centralidad, comunidades)

---

## Consultas de Ejemplo

### MongoDB

```bash
cd scripts/mongodb
python consultas_ejemplo.py
```

**Incluye:**
- Listar estaciones de una línea en orden
- Obtener estaciones con Renfe
- Campus por universidad
- Agregaciones: estudios por universidad, estaciones universitarias por zona

### Neo4j

Abre Neo4j Browser y ejecuta las consultas de `scripts/neo4j/consultas_ejemplo.cypher`:

```cypher
// Camino más corto desde Sol a Ciudad Universitaria
MATCH (origen:Estacion {nombre: 'Sol'}),
      (destino:Estacion {nombre: 'Ciudad Universitaria'}),
      path = shortestPath((origen)-[:SIGUIENTE*]-(destino))
RETURN [n IN nodes(path) | n.nombre] AS ruta,
       length(path) AS num_estaciones;
```

```cypher
// Campus que ofrecen Máster en IA, ordenados por distancia desde Sol
MATCH (origen:Estacion {nombre: 'Sol'}),
      (campus:Campus)-[:OFRECE]->(estudio:Estudio),
      (campus)-[:CERCANA]->(destino:Estacion)
WHERE estudio.nombre CONTAINS 'Inteligencia Artificial' AND estudio.tipo = 'MASTER'
WITH origen, campus, destino
MATCH path = shortestPath((origen)-[:SIGUIENTE*]-(destino))
RETURN campus.nombre, length(path) AS distancia
ORDER BY distancia;
```

---

## Casos de Uso

### 1. Recomendación Multiobjetivo

**Pregunta:** "Desde Atocha, ¿cuál es el mejor campus para estudiar el Máster en IA considerando distancia y cambios de línea?"

**MongoDB** (versión simplificada):
```python
# Buscar campus con el máster
campus_con_master = db.campus.find({
    "estudios.nombre": {"$regex": "Inteligencia Artificial"},
    "estudios.tipo": "MASTER"
})

# Calcular distancia usando indice_por_linea (solo misma línea)
```

**Neo4j** (versión completa):
```cypher
MATCH (origen:Estacion {nombre: 'Atocha'}),
      (campus:Campus)-[:OFRECE]->(estudio:Estudio),
      (campus)-[:CERCANA]->(destino:Estacion)
WHERE estudio.nombre CONTAINS 'Inteligencia Artificial' AND estudio.tipo = 'MASTER'
WITH origen, campus, destino
MATCH path = shortestPath((origen)-[:SIGUIENTE*]-(destino))
WITH campus, destino, path,
     [r IN relationships(path) | r.lineaId] AS lineas_ruta
// Calcular cambios de línea
UNWIND range(0, size(lineas_ruta) - 2) AS i
WITH campus, destino, path, lineas_ruta,
     CASE WHEN lineas_ruta[i] <> lineas_ruta[i+1] THEN 1 ELSE 0 END AS cambio
RETURN campus.nombre,
       length(path) AS distancia,
       sum(cambio) AS cambios_linea
ORDER BY cambios_linea, distancia;
```

### 2. Hubs Universitarios

**Pregunta:** "¿Qué estaciones dan servicio a más de un campus?"

**Neo4j:**
```cypher
MATCH (e:Estacion)<-[:CERCANA]-(c:Campus)
WITH e, count(DISTINCT c) AS num_campus
WHERE num_campus > 1
RETURN e.nombre, num_campus
ORDER BY num_campus DESC;
```

---

## Datos Incluidos

### Líneas de Metro:
- **Línea 1** (Azul claro): Pinar de Chamartín ↔ Valdecarros
- **Línea 3** (Amarilla): Moncloa ↔ Villaverde Alto
- **Línea 6** (Gris, Circular)
- **Línea 10** (Azul oscuro): Hospital Infanta Sofía ↔ Puerta del Sur

### Universidades y Campus:
1. **UCM** - Ciudad Universitaria
2. **UPM** - Campus de Moncloa, Campus Sur
3. **UC3M** - Campus de Leganés
4. **URJC** - Campus de Fuenlabrada, Campus de Vicálvaro

### Estudios destacados:
- Grado en Ciencia e Ingeniería de Datos (UCM, UC3M, URJC)
- Máster en Inteligencia Artificial (UCM, UC3M, UPM)
- Máster en Big Data y Data Science (UCM)
- Máster en Machine Learning (UC3M)

### Estaciones con Renfe:
- Chamartín (C1, C2, C3, C4, C7, C8, C10)
- Sol (C3, C4)
- Atocha (C1, C2, C5, C7, C10)
- Príncipe Pío (C1, C7, C10)
- Villaverde Alto (C5)

---

## Preparación para Benchmark (ICLR 2026)

El proyecto está diseñado para comparar dos enfoques:

### Baseline: LLM sin contexto
```python
prompt = "¿Cuál es la ruta más corta desde Sol hasta un campus con Máster en IA?"
respuesta = llm.generate(prompt)  # Sin acceso a BD
```

### GraphRAG: LLM con contexto estructurado
```python
# 1. Extraer subgrafo de Neo4j
subgrafo = extraer_rutas_neo4j("Sol", "Máster en IA")

# 2. Obtener detalles de MongoDB
detalles_campus = obtener_campus_mongo("Máster en IA")

# 3. Pasar contexto al LLM
contexto = f"Grafo: {subgrafo}\nCampus: {detalles_campus}"
prompt = f"Con este contexto: {contexto}\n¿Cuál es la mejor ruta?"
respuesta = llm.generate(prompt)
```

**Hipótesis:** GraphRAG mejorará precisión en recomendaciones multiobjetivo (distancia + cambios de línea + oferta académica).

---

## Paso 4: Implementación del Agente (Pendiente)

Una vez confirmada la carga de datos, se implementará la clase `MetroCampusRecommender` en `src/agent/`:

```python
class MetroCampusRecommender:
    def baseline_llm(self, estacion_origen, estudio_nombre):
        """Método sin RAG"""
        pass

    def graphrag_recommendation(self, estacion_origen, estudio_nombre):
        """Método con GraphRAG (Neo4j + MongoDB)"""
        pass
```

---

## Troubleshooting

### Error de conexión a MongoDB
```
pymongo.errors.ServerSelectionTimeoutError
```
**Solución:** Verifica que MongoDB está corriendo y el URI es correcto.

### Error de conexión a Neo4j
```
neo4j.exceptions.ServiceUnavailable
```
**Solución:** Verifica credenciales en `.env` y que Neo4j Desktop está activo.

### Módulos no encontrados
```
ModuleNotFoundError: No module named 'pymongo'
```
**Solución:**
```bash
pip install -r requirements.txt
```

---

## Autores

Proyecto desarrollado para la asignatura de **Bases de Datos No Relacionales**
Grado en Ciencia e Ingeniería de Datos - Universidad Rey Juan Carlos
Curso 2025/2026

---

## Licencia

Material docente en abierto - CC BY-SA 4.0

---

## Referencias

- [MongoDB Documentation](https://docs.mongodb.com/)
- [Neo4j Documentation](https://neo4j.com/docs/)
- [Metro de Madrid - Plano oficial](https://www.metromadrid.es/es/viaja-en-metro/plano-de-metro-de-madrid)

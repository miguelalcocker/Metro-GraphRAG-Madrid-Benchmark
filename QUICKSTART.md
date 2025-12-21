# Guía Rápida de Inicio

## 1. Instalación de Dependencias

```bash
pip install -r requirements.txt
```

## 2. Configuración

```bash
cp .env.example .env
# Edita .env con tus credenciales de MongoDB y Neo4j
```

## 3. Verificar Datos

```bash
./scripts/verificar_datos.sh
```

**Salida esperada:**
- 4 líneas de Metro
- 60 estaciones
- 6 campus universitarios
- 18 Grados + 13 Másteres

## 4. Cargar en MongoDB

```bash
cd scripts/mongodb
python load_data.py
```

**Tiempo estimado:** < 10 segundos

## 5. Cargar en Neo4j

```bash
cd scripts/neo4j
python load_data.py
```

**Tiempo estimado:** < 15 segundos

## 6. Probar Consultas

### MongoDB:
```bash
cd scripts/mongodb
python consultas_ejemplo.py
```

### Neo4j:
```bash
# Abrir Neo4j Browser: http://localhost:7474
# Ejecutar consultas de: scripts/neo4j/consultas_ejemplo.cypher
```

## 7. Consultas de Ejemplo

### MongoDB - Campus que ofrecen un Grado:
```python
db.campus.find({
    "estudios.tipo": "GRADO",
    "estudios.nombre": {"$regex": "Ingeniería de Datos"}
})
```

### Neo4j - Ruta más corta:
```cypher
MATCH (origen:Estacion {nombre: 'Sol'}),
      (destino:Estacion {nombre: 'Moncloa'}),
      path = shortestPath((origen)-[:SIGUIENTE*]-(destino))
RETURN [n IN nodes(path) | n.nombre] AS ruta;
```

## 8. Siguiente Paso

Una vez verificada la carga de datos, confirma para proceder con el **Paso 4: Implementación del Agente GraphRAG**.

---

## Troubleshooting Rápido

**Error:** `pymongo.errors.ServerSelectionTimeoutError`
- **Solución:** Verifica que MongoDB está corriendo

**Error:** `neo4j.exceptions.ServiceUnavailable`
- **Solución:** Verifica que Neo4j Desktop está activo

**Error:** `ModuleNotFoundError`
- **Solución:** `pip install -r requirements.txt`

---

## Datos Destacados

### Estaciones con Renfe (5):
- Chamartín (7 líneas Cercanías)
- Sol (C3, C4)
- Atocha (5 líneas Cercanías)
- Príncipe Pío (C1, C7, C10)
- Villaverde Alto (C5)

### Campus principales:
- **UCM** - Ciudad Universitaria (Metro L6)
- **UPM** - Moncloa (Metro L3, L6)
- **UC3M** - Leganés (Metro L12 + Legazpi L3/L6)
- **URJC** - Fuenlabrada y Vicálvaro

### Estudios más ofertados:
- Grado en Ciencia e Ingeniería de Datos (UCM, UC3M, URJC)
- Máster en Inteligencia Artificial (UCM, UC3M, UPM)

---

**¿Todo listo?** Confirma la carga de datos y procedemos con el Paso 4: Agente GraphRAG

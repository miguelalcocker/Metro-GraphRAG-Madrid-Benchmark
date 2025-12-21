# Guía del Agente Recomendador - GraphRAG

Sistema de recomendación de campus universitarios usando Metro de Madrid con comparación Baseline LLM vs GraphRAG para benchmark ICLR 2026.

---

## Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                    USUARIO                                  │
│              (Consulta en lenguaje natural)                 │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┴──────────────┐
        │                           │
        ▼                           ▼
┌───────────────┐          ┌────────────────────┐
│   BASELINE    │          │     GRAPHRAG       │
│   (Sin RAG)   │          │  (Con contexto BD) │
└───────┬───────┘          └─────────┬──────────┘
        │                            │
        │                   ┌────────┴────────┐
        │                   │                 │
        │                   ▼                 ▼
        │          ┌──────────────┐  ┌──────────────┐
        │          │   MongoDB    │  │    Neo4j     │
        │          │   (Campus)   │  │   (Rutas)    │
        │          └──────────────┘  └──────────────┘
        │                   │                 │
        │                   └────────┬────────┘
        │                            │
        │                   ┌────────▼────────┐
        │                   │    Contexto     │
        │                   │  Estructurado   │
        │                   └────────┬────────┘
        │                            │
        └────────────┬───────────────┘
                     │
                     ▼
            ┌────────────────┐
            │      LLM       │
            │ (GPT/Claude)   │
            └────────┬───────┘
                     │
                     ▼
            ┌────────────────┐
            │   RESPUESTA    │
            └────────────────┘
```

---

## Instalación y Configuración

### 1. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 2. Configurar variables de entorno

```bash
cp .env.example .env
```

Edita `.env`:

```env
# Bases de datos
MONGODB_URI=mongodb://localhost:27017/
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# LLM (opcional - sin configurar usa MockProvider)
OPENAI_API_KEY=sk-...
# O
ANTHROPIC_API_KEY=sk-ant-...
```

### 3. Cargar datos en las bases de datos

```bash
# MongoDB
cd scripts/mongodb && python load_data.py

# Neo4j
cd scripts/neo4j && python load_data.py
```

---

## Uso Básico del Agente

### Ejemplo 1: Usar MockProvider (sin API)

```python
from src.agent import MetroCampusRecommender

# Crear recomendador con proveedor simulado
recommender = MetroCampusRecommender(verbose=True)

try:
    # Consulta de ejemplo
    query = "Desde Sol, ¿cuál es el mejor campus para estudiar el Máster en Inteligencia Artificial?"

    # Comparar ambos métodos
    results = recommender.compare_methods(query)

    # Ver resultados
    print("\n=== BASELINE ===")
    print(results['baseline']['response'])

    print("\n=== GRAPHRAG ===")
    print(results['graphrag']['response'])

finally:
    recommender.close()
```

### Ejemplo 2: Usar OpenAI GPT-4

```python
from src.agent import MetroCampusRecommender, create_llm_provider

# Crear proveedor de OpenAI
llm = create_llm_provider("openai", model="gpt-4")

# Crear recomendador
recommender = MetroCampusRecommender(
    llm_provider=llm,
    verbose=True
)

try:
    query = "Desde Atocha, ¿cómo llego a la UCM?"
    result = recommender.graphrag_recommendation(query)

    print(result['response'])

finally:
    recommender.close()
```

### Ejemplo 3: Usar Claude (Anthropic)

```python
from src.agent import MetroCampusRecommender, create_llm_provider

# Crear proveedor de Claude
llm = create_llm_provider("anthropic", model="claude-3-5-sonnet-20241022")

recommender = MetroCampusRecommender(
    llm_provider=llm,
    verbose=True
)

try:
    query = "Desde Príncipe Pío, busco el Grado en Ingeniería de Datos"
    result = recommender.baseline_llm(query)

    print(result['response'])

finally:
    recommender.close()
```

### Ejemplo 4: Usar Modelo Local (Ollama)

```python
from src.agent import MetroCampusRecommender, create_llm_provider

# Crear proveedor local (requiere Ollama corriendo)
llm = create_llm_provider("local", model="llama3", base_url="http://localhost:11434")

recommender = MetroCampusRecommender(
    llm_provider=llm,
    verbose=True
)

try:
    query = "¿Qué campus de la UPM están cerca de Moncloa?"
    result = recommender.graphrag_recommendation(query)

    print(result['response'])

finally:
    recommender.close()
```

---

## Pipeline GraphRAG (4 Fases)

### Fase 1: Extracción de Entidades

El sistema extrae automáticamente:
- **Estación de origen**: "desde Sol", "estoy en Atocha"
- **Estudio buscado**: "Máster en IA", "Grado en Ingeniería"

```python
# Interno - Se ejecuta automáticamente
entities = recommender._extract_entities(query)
# {'estacion_origen': 'Sol', 'estudio': 'Inteligencia Artificial'}
```

### Fase 2: Recuperación de Contexto

Consultas simultáneas a:

**MongoDB**: Campus que ofrecen el estudio
```python
campus = recommender._search_campus_mongodb("Inteligencia Artificial")
# Retorna: [{nombre: "UCM", estudios: [...], estaciones_cercanas: [...]}]
```

**Neo4j**: Rutas óptimas con `shortestPath()`
```python
rutas = recommender._calculate_routes_neo4j("Sol", campus_list)
# Retorna: [{campus: "UCM", ruta: [...], num_cambios_linea: 1, ...}]
```

### Fase 3: Aumentación del Prompt

Construcción de prompt estructurado:

```
DATOS REALES EXTRAÍDOS DE LA BASE DE DATOS:
============================================================

CONSULTA DEL USUARIO:
Desde Sol, ¿cuál es el mejor campus para estudiar el Máster en IA?

ENTIDADES IDENTIFICADAS:
- Estación de origen: Sol
- Estudio buscado: Inteligencia Artificial

CAMPUS QUE OFRECEN ESTE ESTUDIO:
1. Ciudad Universitaria (UCM)
   - Máster en Inteligencia Artificial (MASTER)
     Créditos: 60

RUTAS CALCULADAS DESDE Sol:
1. Hacia Ciudad Universitaria (UCM)
   Estación destino: Ciudad Universitaria (principal)
   Distancia: 8 estaciones
   Transbordos: 1
   Líneas usadas: L1, L6
   Ruta: Sol → Tribunal → Alonso Martínez → ... → Ciudad Universitaria

INSTRUCCIONES:
Basándote ÚNICAMENTE en los datos anteriores...
```

### Fase 4: Generación

El LLM genera respuesta basándose **estrictamente en el contexto** proporcionado.

---

## Ejecutar el Benchmark

### Benchmark Completo (10 consultas desafío)

```bash
cd src/agent
python evaluate.py
```

**Salida esperada:**

```
================================================================================
BENCHMARK: BASELINE vs GRAPHRAG
================================================================================
Total de consultas: 10

[1/10] Procesando consulta 1...
Dificultad: medium
Query: Desde Sol, ¿cuál es el mejor campus para estudiar el Máster en IA?
  ✓ Baseline válido: True
  ✓ GraphRAG válido: True
  • Campus encontrados (GraphRAG): 3
  • Rutas calculadas (GraphRAG): 4

[2/10] Procesando consulta 2...
...

================================================================================
RESUMEN DE RESULTADOS
================================================================================

📊 TASA DE ÉXITO:
  • Baseline:  60.0%
  • GraphRAG:  90.0%

🔄 TRANSBORDOS PROMEDIO:
  • Baseline:  1.20
  • GraphRAG:  0.80

🚨 ALUCINACIONES DETECTADAS:
  • Baseline:  5
  • GraphRAG:  1

✅ GANADOR: GraphRAG

💾 Resultados guardados en: results/experiments.json
```

### Ejecutar consultas específicas

```python
from src.agent.evaluate import BenchmarkEvaluator, CHALLENGE_QUERIES
from src.agent import MetroCampusRecommender, create_llm_provider

# Crear recomendador
llm = create_llm_provider("mock")  # O "openai", "anthropic"
recommender = MetroCampusRecommender(llm_provider=llm)

# Crear evaluador
evaluator = BenchmarkEvaluator(recommender, verbose=True)

# Ejecutar solo consultas fáciles
easy_queries = [q for q in CHALLENGE_QUERIES if q['difficulty'] == 'easy']
results = evaluator.run_benchmark(queries=easy_queries)

# Ver resumen
evaluator.print_summary(results)

recommender.close()
```

---

## Métricas de Evaluación

### Success Rate (Tasa de Éxito)

**Criterios**:
- ✅ Menciona la estación de origen correcta
- ✅ Menciona al menos un campus válido
- ✅ La ruta es coherente

```python
# Automático en evaluate.py
metrics = EvaluationMetrics.validate_route(response, expected)
print(f"Válido: {metrics['is_valid']}")
```

### Número de Transbordos

**Detección automática** de patrones:
- "1 transbordo"
- "sin transbordo"
- "directo"
- "cambio de línea"

```python
num_transbordos = metrics['num_transbordos_mencionados']
```

### Alucinaciones Detectadas

**Para Baseline**:
- Menciona estaciones/campus que no existen
- Usa lenguaje incierto: "probablemente", "puede que"

**Para GraphRAG**:
- Menciona campus NO presentes en el contexto
- Inventa rutas no calculadas

```python
# GraphRAG específico
hallucinations = EvaluationMetrics.detect_hallucinations_graphrag(
    response,
    context_data
)
```

---

## Consultas Desafío Incluidas

| ID | Dificultad | Descripción                          | Requiere Transbordo |
|----|------------|--------------------------------------|---------------------|
| 1  | Medium     | Sol → Máster IA                     | Sí (L1→L6)         |
| 2  | Medium     | Atocha → Grado Ciencia de Datos     | Sí (L1→L6)         |
| 3  | Hard       | Chamartín → Máster Big Data         | Sí (L10→L6)        |
| 4  | Easy       | Príncipe Pío → UPM + IA             | No (L6 directo)    |
| 5  | Easy       | Moncloa → Ing. Informática          | No (L6 directo)    |
| 6  | Hard       | Pacífico → UC3M + Machine Learning  | Sí (L6→L3)         |
| 7  | Hard       | Sol → URJC + Cloud Computing        | Sí (L1→L10)        |
| 8  | Easy       | Ciudad Univ. → Máster Robótica      | No (L6 circular)   |
| 9  | Medium     | Plaza Castilla → Campus UCM         | Sí (L1→L6)         |
| 10 | Easy       | Cuatro Caminos → Máster Ciberseg.   | No (L6 directo)    |

---

## Resultados del Benchmark

Los resultados se guardan en `results/experiments.json`:

```json
{
  "metadata": {
    "timestamp": "2025-12-21T18:30:00",
    "total_queries": 10,
    "llm_provider": "MockProvider"
  },
  "results": [
    {
      "challenge_id": 1,
      "query": "Desde Sol, ¿cuál es el mejor campus para...",
      "baseline_response": "...",
      "graphrag_response": "...",
      "baseline_metrics": {
        "is_valid": true,
        "num_transbordos_mencionados": 1
      },
      "graphrag_metrics": {
        "is_valid": true,
        "num_transbordos_mencionados": 1
      },
      "graphrag_context": {
        "campus_found": 3,
        "routes_calculated": 4
      }
    }
  ],
  "summary": {
    "success_rates": {
      "baseline_success_rate": 0.6,
      "graphrag_success_rate": 0.9
    },
    "avg_transbordos_baseline": 1.2,
    "avg_transbordos_graphrag": 0.8,
    "total_hallucinations_baseline": 5,
    "total_hallucinations_graphrag": 1
  }
}
```

---

## Hipótesis del Benchmark (ICLR 2026)

### Hipótesis Principal

> **GraphRAG mejorará la precisión en recomendaciones multiobjetivo (distancia + cambios de línea + oferta académica) en comparación con Baseline LLM**

### Métricas Esperadas

| Métrica                    | Baseline | GraphRAG | Mejora Esperada |
|----------------------------|----------|----------|-----------------|
| Tasa de Éxito              | 50-70%   | 85-95%   | +25-35%         |
| Transbordos Correctos      | 40-60%   | 80-90%   | +40%            |
| Alucinaciones              | 20-30%   | 5-10%    | -60%            |
| Campus Correctos           | 60-75%   | 90-100%  | +30%            |

### Variables Controladas

- Mismo LLM para ambos métodos
- Mismas consultas de prueba
- Misma temperatura (0.3)
- Mismo conjunto de datos

---

## Troubleshooting

### Error: "OPENAI_API_KEY no configurada"

```bash
# Usar MockProvider en desarrollo
llm = create_llm_provider("mock")

# O configurar API key
export OPENAI_API_KEY=sk-...
```

### Error: Conexión a MongoDB/Neo4j

```bash
# Verificar que las BD están corriendo
mongosh  # MongoDB
cypher-shell  # Neo4j

# O actualizar URIs en .env
```

### MockProvider devuelve respuestas genéricas

Esto es normal. MockProvider es para testing. Para resultados reales:

```python
llm = create_llm_provider("openai", model="gpt-4")
# O
llm = create_llm_provider("anthropic", model="claude-3-5-sonnet-20241022")
```

---

## Contribuir al Benchmark

Para añadir nuevas consultas desafío:

```python
# En src/agent/evaluate.py

CHALLENGE_QUERIES.append({
    "id": 11,
    "query": "Tu consulta aquí",
    "expected": {
        "estacion_origen": "Origen",
        "estudio": "Estudio",
        "campus_validos": ["Campus 1", "Campus 2"],
        "requiere_transbordo": True/False,
        "lineas_validas": [[1, 6], [3]]
    },
    "difficulty": "easy/medium/hard"
})
```

---

## Referencias

- [Documentación MongoDB](https://docs.mongodb.com/)
- [Documentación Neo4j Cypher](https://neo4j.com/docs/cypher-manual/)
- [OpenAI API](https://platform.openai.com/docs)
- [Anthropic Claude API](https://docs.anthropic.com/)
- [Ollama (modelos locales)](https://ollama.ai/)

---

## Autores

Proyecto desarrollado para la asignatura de **Bases de Datos No Relacionales**
Grado en Ciencia e Ingeniería de Datos - Universidad Rey Juan Carlos
Curso 2025/2026

**Benchmark preparado para ICLR 2026**

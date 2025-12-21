#!/usr/bin/env python3
"""
MetroCampusRecommender - Sistema de Recomendación de Campus Universitarios
Implementa Baseline LLM vs GraphRAG para benchmark ICLR 2026
"""

import os
import re
from typing import Dict, List, Tuple, Optional, Any
from pymongo import MongoClient
from neo4j import GraphDatabase
from .llm_interface import LLMInterface, create_llm_provider


class MetroCampusRecommender:
    """
    Sistema de recomendación de campus universitarios usando Metro de Madrid

    Implementa dos enfoques:
    1. Baseline: LLM sin contexto (memoria del modelo)
    2. GraphRAG: LLM con contexto extraído de MongoDB + Neo4j
    """

    def __init__(
        self,
        mongodb_uri: Optional[str] = None,
        neo4j_uri: Optional[str] = None,
        neo4j_user: Optional[str] = None,
        neo4j_password: Optional[str] = None,
        llm_provider: Optional[LLMInterface] = None,
        verbose: bool = True
    ):
        """
        Inicializa el recomendador

        Args:
            mongodb_uri: URI de conexión a MongoDB
            neo4j_uri: URI de conexión a Neo4j
            neo4j_user: Usuario de Neo4j
            neo4j_password: Contraseña de Neo4j
            llm_provider: Proveedor de LLM (si no se provee, usa MockProvider)
            verbose: Imprimir información de debug
        """
        self.verbose = verbose

        # Configuración de conexiones
        self.mongodb_uri = mongodb_uri or os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
        self.neo4j_uri = neo4j_uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.neo4j_user = neo4j_user or os.getenv("NEO4J_USER", "neo4j")
        self.neo4j_password = neo4j_password or os.getenv("NEO4J_PASSWORD", "password")

        # Conectar a bases de datos
        self._connect_databases()

        # Configurar LLM
        self.llm = llm_provider or create_llm_provider("mock")

        if self.verbose:
            print("✓ MetroCampusRecommender inicializado")
            print(f"  • MongoDB: {self.mongodb_uri}")
            print(f"  • Neo4j: {self.neo4j_uri}")
            print(f"  • LLM: {type(self.llm).__name__}")

    def _connect_databases(self):
        """Conecta a MongoDB y Neo4j"""
        try:
            # MongoDB
            self.mongo_client = MongoClient(self.mongodb_uri)
            self.db = self.mongo_client["metro_campus_db"]

            # Verificar conexión
            self.mongo_client.server_info()

            if self.verbose:
                print("✓ Conectado a MongoDB")

        except Exception as e:
            raise ConnectionError(f"Error conectando a MongoDB: {e}")

        try:
            # Neo4j
            self.neo4j_driver = GraphDatabase.driver(
                self.neo4j_uri,
                auth=(self.neo4j_user, self.neo4j_password)
            )

            # Verificar conexión
            with self.neo4j_driver.session() as session:
                session.run("RETURN 1")

            if self.verbose:
                print("✓ Conectado a Neo4j")

        except Exception as e:
            raise ConnectionError(f"Error conectando a Neo4j: {e}")

    def close(self):
        """Cierra las conexiones a las bases de datos"""
        if hasattr(self, 'mongo_client'):
            self.mongo_client.close()
        if hasattr(self, 'neo4j_driver'):
            self.neo4j_driver.close()

        if self.verbose:
            print("✓ Conexiones cerradas")

    # ========================================================================
    # MÉTODO 1: BASELINE LLM (Sin RAG)
    # ========================================================================

    def baseline_llm(self, query: str) -> Dict[str, Any]:
        """
        Método Baseline: Consulta directa al LLM sin acceso a bases de datos

        Args:
            query: Consulta en lenguaje natural del usuario

        Returns:
            Dict con la respuesta y metadatos
        """
        if self.verbose:
            print("\n" + "=" * 70)
            print("BASELINE LLM (Sin RAG)")
            print("=" * 70)
            print(f"Consulta: {query}")

        # Prompt directo sin contexto
        prompt = f"""Eres un asistente experto en el Metro de Madrid y las universidades públicas de Madrid.

Responde a la siguiente pregunta basándote únicamente en tu conocimiento general:

{query}

Proporciona:
1. La mejor ruta en metro
2. Los campus que ofrecen el estudio mencionado
3. Estimación de tiempo de viaje
4. Número de transbordos necesarios

Respuesta:"""

        # Generar respuesta
        response = self.llm.generate(prompt, temperature=0.3)

        if self.verbose:
            print("\n📝 Respuesta del LLM (Baseline):")
            print(response)

        return {
            "method": "baseline",
            "query": query,
            "response": response,
            "context_used": None,
            "sources": []
        }

    # ========================================================================
    # MÉTODO 2: GRAPHRAG (Con contexto de BD)
    # ========================================================================

    def graphrag_recommendation(self, query: str) -> Dict[str, Any]:
        """
        Método GraphRAG: Pipeline completo con 4 fases

        Fases:
        1. Extracción: Extraer entidades (estación origen, estudio)
        2. Recuperación: Consultar MongoDB + Neo4j
        3. Aumentación: Construir prompt con contexto
        4. Generación: Generar respuesta basada en contexto

        Args:
            query: Consulta en lenguaje natural del usuario

        Returns:
            Dict con la respuesta, contexto y metadatos
        """
        if self.verbose:
            print("\n" + "=" * 70)
            print("GRAPHRAG (Con contexto de BD)")
            print("=" * 70)
            print(f"Consulta: {query}")

        # FASE 1: EXTRACCIÓN
        entities = self._extract_entities(query)

        if self.verbose:
            print(f"\n🔍 FASE 1 - Entidades extraídas:")
            print(f"  • Estación origen: {entities.get('estacion_origen', 'No detectada')}")
            print(f"  • Estudio: {entities.get('estudio', 'No detectado')}")

        # FASE 2: RECUPERACIÓN
        context_data = self._retrieve_context(entities)

        if self.verbose:
            print(f"\n📊 FASE 2 - Datos recuperados:")
            print(f"  • Campus encontrados: {len(context_data['campus'])}")
            print(f"  • Rutas calculadas: {len(context_data['rutas'])}")

        # FASE 3: AUMENTACIÓN
        augmented_prompt = self._build_augmented_prompt(query, entities, context_data)

        if self.verbose:
            print(f"\n📝 FASE 3 - Prompt aumentado construido ({len(augmented_prompt)} caracteres)")

        # FASE 4: GENERACIÓN
        response = self.llm.generate(augmented_prompt, temperature=0.3)

        if self.verbose:
            print("\n🤖 FASE 4 - Respuesta del LLM (GraphRAG):")
            print(response)

        return {
            "method": "graphrag",
            "query": query,
            "entities": entities,
            "context": context_data,
            "response": response,
            "sources": self._extract_sources(context_data)
        }

    # ========================================================================
    # FASE 1: EXTRACCIÓN DE ENTIDADES
    # ========================================================================

    def _extract_entities(self, query: str) -> Dict[str, Optional[str]]:
        """
        Extrae entidades clave de la consulta

        Args:
            query: Consulta del usuario

        Returns:
            Dict con estacion_origen y estudio
        """
        entities = {
            "estacion_origen": None,
            "estudio": None
        }

        # Extraer estación de origen (patrones comunes)
        estacion_patterns = [
            r"desde\s+([A-ZÁ-Ú][a-záéíóúñ\s]+?)(?:\s+hasta|\s+a|\s+,|\s+quiero|\s+busco|\s+para)",
            r"origen\s+([A-ZÁ-Ú][a-záéíóúñ\s]+?)(?:\s+hasta|\s+,)",
            r"estoy\s+en\s+([A-ZÁ-Ú][a-záéíóúñ\s]+?)(?:\s+y|\s+,)"
        ]

        for pattern in estacion_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                entities["estacion_origen"] = match.group(1).strip().title()
                break

        # Si no se detectó, buscar estaciones conocidas en la query
        if not entities["estacion_origen"]:
            estaciones_comunes = ["Sol", "Atocha", "Chamartín", "Moncloa", "Ciudad Universitaria",
                                   "Príncipe Pío", "Pacífico", "Plaza de Castilla"]
            for estacion in estaciones_comunes:
                if estacion.lower() in query.lower():
                    entities["estacion_origen"] = estacion
                    break

        # Extraer estudio (patrones comunes)
        estudio_patterns = [
            r"(?:Máster|Master|Grado)\s+en\s+([A-ZÁ-Úa-záéíóúñ\s]+?)(?:\s*$|\s*\?|\s+desde|\s+,)",
            r"estudiar\s+([A-ZÁ-Úa-záéíóúñ\s]+?)(?:\s+desde|\s+en|\s*\?|\s*$)",
            r"(?:programa|carrera)\s+(?:de\s+)?([A-ZÁ-Úa-záéíóúñ\s]+?)(?:\s+desde|\s*\?|\s*$)"
        ]

        for pattern in estudio_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                entities["estudio"] = match.group(1).strip()
                break

        # Si no se detectó, buscar estudios comunes
        if not entities["estudio"]:
            estudios_comunes = [
                "Inteligencia Artificial", "Ciencia e Ingeniería de Datos",
                "Machine Learning", "Big Data", "Ciberseguridad"
            ]
            for estudio in estudios_comunes:
                if estudio.lower() in query.lower():
                    entities["estudio"] = estudio
                    break

        return entities

    # ========================================================================
    # FASE 2: RECUPERACIÓN DE CONTEXTO
    # ========================================================================

    def _retrieve_context(self, entities: Dict[str, Optional[str]]) -> Dict[str, Any]:
        """
        Recupera contexto relevante de MongoDB y Neo4j

        Args:
            entities: Entidades extraídas (estación, estudio)

        Returns:
            Dict con campus, rutas y metadatos
        """
        context = {
            "campus": [],
            "rutas": [],
            "estacion_origen": entities.get("estacion_origen"),
            "estudio_buscado": entities.get("estudio")
        }

        estudio = entities.get("estudio")
        estacion_origen = entities.get("estacion_origen")

        # 1. Buscar campus en MongoDB que ofrecen el estudio
        if estudio:
            context["campus"] = self._search_campus_mongodb(estudio)

        # 2. Calcular rutas en Neo4j desde el origen a esos campus
        if estacion_origen and context["campus"]:
            context["rutas"] = self._calculate_routes_neo4j(estacion_origen, context["campus"])

        return context

    def _search_campus_mongodb(self, estudio_query: str) -> List[Dict[str, Any]]:
        """Busca campus que ofrecen un estudio en MongoDB"""
        try:
            # Buscar campus con el estudio (regex case-insensitive)
            campus_cursor = self.db.campus.find({
                "estudios.nombre": {"$regex": estudio_query, "$options": "i"}
            })

            campus_list = []
            for campus in campus_cursor:
                # Filtrar solo los estudios que coinciden
                estudios_match = [
                    e for e in campus.get("estudios", [])
                    if estudio_query.lower() in e.get("nombre", "").lower()
                ]

                if estudios_match:
                    campus_list.append({
                        "nombre": campus.get("nombre"),
                        "universidad": campus.get("universidad"),
                        "estudios": estudios_match,
                        "estaciones_cercanas": campus.get("estaciones_cercanas", [])
                    })

            return campus_list

        except Exception as e:
            if self.verbose:
                print(f"Error en MongoDB: {e}")
            return []

    def _calculate_routes_neo4j(
        self,
        estacion_origen: str,
        campus_list: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Calcula rutas óptimas en Neo4j"""
        rutas = []

        with self.neo4j_driver.session() as session:
            for campus in campus_list:
                for estacion_cercana in campus.get("estaciones_cercanas", []):
                    estacion_destino = estacion_cercana.get("nombre_estacion")

                    if not estacion_destino:
                        continue

                    # Consulta Cypher para camino más corto
                    query = """
                    MATCH (origen:Estacion {nombre: $origen}),
                          (destino:Estacion {nombre: $destino}),
                          path = shortestPath((origen)-[:SIGUIENTE*]-(destino))
                    WITH path,
                         [r IN relationships(path) | r.lineaId] AS lineas_ruta,
                         [n IN nodes(path) | n.nombre] AS nombres_ruta
                    UNWIND range(0, size(lineas_ruta) - 2) AS i
                    WITH path, lineas_ruta, nombres_ruta,
                         CASE WHEN lineas_ruta[i] <> lineas_ruta[i+1] THEN 1 ELSE 0 END AS cambio
                    RETURN nombres_ruta AS ruta,
                           length(path) AS num_estaciones,
                           sum(cambio) AS num_cambios_linea,
                           lineas_ruta
                    LIMIT 1
                    """

                    try:
                        result = session.run(
                            query,
                            origen=estacion_origen,
                            destino=estacion_destino
                        ).single()

                        if result:
                            rutas.append({
                                "campus": campus.get("nombre"),
                                "universidad": campus.get("universidad"),
                                "estacion_destino": estacion_destino,
                                "rol_estacion": estacion_cercana.get("rol"),
                                "minutos_andando": estacion_cercana.get("minutos_andando"),
                                "ruta": result["ruta"],
                                "num_estaciones": result["num_estaciones"],
                                "num_cambios_linea": result["num_cambios_linea"],
                                "lineas_usadas": list(set(result["lineas_ruta"]))
                            })

                    except Exception as e:
                        if self.verbose:
                            print(f"Error calculando ruta a {estacion_destino}: {e}")

        # Ordenar rutas por número de cambios y distancia
        rutas.sort(key=lambda x: (x["num_cambios_linea"], x["num_estaciones"]))

        return rutas

    # ========================================================================
    # FASE 3: AUMENTACIÓN DE PROMPT
    # ========================================================================

    def _build_augmented_prompt(
        self,
        original_query: str,
        entities: Dict[str, Optional[str]],
        context_data: Dict[str, Any]
    ) -> str:
        """
        Construye prompt aumentado con contexto estructurado

        Args:
            original_query: Consulta original del usuario
            entities: Entidades extraídas
            context_data: Datos recuperados de BD

        Returns:
            Prompt aumentado para el LLM
        """
        prompt = f"""Eres un asistente experto en el Metro de Madrid y las universidades públicas de Madrid.

DATOS REALES EXTRAÍDOS DE LA BASE DE DATOS:
{'=' * 60}

CONSULTA DEL USUARIO:
{original_query}

ENTIDADES IDENTIFICADAS:
- Estación de origen: {entities.get('estacion_origen', 'No especificada')}
- Estudio buscado: {entities.get('estudio', 'No especificado')}

CAMPUS QUE OFRECEN ESTE ESTUDIO:
"""

        # Añadir información de campus
        if context_data["campus"]:
            for i, campus in enumerate(context_data["campus"], 1):
                prompt += f"\n{i}. {campus['nombre']} ({campus['universidad']})\n"
                for estudio in campus["estudios"]:
                    prompt += f"   - {estudio['nombre']} ({estudio['tipo']})\n"
                    if estudio.get('creditos'):
                        prompt += f"     Créditos: {estudio['creditos']}\n"
        else:
            prompt += "\nNo se encontraron campus que ofrezcan este estudio.\n"

        # Añadir información de rutas
        prompt += f"\n\nRUTAS CALCULADAS DESDE {entities.get('estacion_origen', '[origen]')}:\n"

        if context_data["rutas"]:
            for i, ruta in enumerate(context_data["rutas"][:3], 1):  # Top 3 rutas
                prompt += f"\n{i}. Hacia {ruta['campus']} ({ruta['universidad']})\n"
                prompt += f"   Estación destino: {ruta['estacion_destino']} ({ruta['rol_estacion']})\n"
                prompt += f"   Distancia: {ruta['num_estaciones']} estaciones\n"
                prompt += f"   Transbordos: {ruta['num_cambios_linea']}\n"
                prompt += f"   Líneas usadas: {', '.join(['L' + str(l) for l in ruta['lineas_usadas']])}\n"
                prompt += f"   Ruta: {' → '.join(ruta['ruta'])}\n"
                prompt += f"   Tiempo andando desde metro: {ruta['minutos_andando']} minutos\n"
        else:
            prompt += "\nNo se pudieron calcular rutas.\n"

        # Instrucciones finales
        prompt += f"""
{'=' * 60}

INSTRUCCIONES:
1. Basándote ÚNICAMENTE en los datos anteriores (NO uses conocimiento general)
2. Recomienda la mejor opción considerando:
   - Menor número de transbordos
   - Menor distancia total
   - Tiempo de acceso andando desde la estación
3. Explica claramente la ruta paso a paso
4. Menciona el nombre exacto del estudio ofrecido
5. Si no hay datos disponibles, indícalo claramente

Responde de forma concisa y estructurada:"""

        return prompt

    # ========================================================================
    # UTILIDADES
    # ========================================================================

    def _extract_sources(self, context_data: Dict[str, Any]) -> List[str]:
        """Extrae fuentes de datos utilizadas"""
        sources = []

        if context_data.get("campus"):
            sources.append(f"MongoDB: {len(context_data['campus'])} campus")

        if context_data.get("rutas"):
            sources.append(f"Neo4j: {len(context_data['rutas'])} rutas calculadas")

        return sources

    def compare_methods(self, query: str) -> Dict[str, Any]:
        """
        Ejecuta ambos métodos y compara resultados

        Args:
            query: Consulta del usuario

        Returns:
            Dict con resultados de ambos métodos
        """
        baseline_result = self.baseline_llm(query)
        graphrag_result = self.graphrag_recommendation(query)

        return {
            "query": query,
            "baseline": baseline_result,
            "graphrag": graphrag_result,
            "comparison": {
                "baseline_used_context": False,
                "graphrag_used_context": len(graphrag_result.get("sources", [])) > 0,
                "campus_found": len(graphrag_result.get("context", {}).get("campus", [])),
                "routes_calculated": len(graphrag_result.get("context", {}).get("rutas", []))
            }
        }


# ============================================================================
# EJEMPLO DE USO
# ============================================================================

if __name__ == "__main__":
    # Crear recomendador
    recommender = MetroCampusRecommender(verbose=True)

    try:
        # Consulta de ejemplo
        query = "Desde Sol, ¿cuál es el mejor campus para estudiar el Máster en Inteligencia Artificial?"

        # Comparar métodos
        results = recommender.compare_methods(query)

        print("\n" + "=" * 70)
        print("COMPARACIÓN DE RESULTADOS")
        print("=" * 70)
        print(f"\nCampus encontrados: {results['comparison']['campus_found']}")
        print(f"Rutas calculadas: {results['comparison']['routes_calculated']}")

    finally:
        recommender.close()

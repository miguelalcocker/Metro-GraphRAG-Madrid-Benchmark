#!/usr/bin/env python3
"""
Script de Evaluación - Baseline vs GraphRAG
Sistema de métricas para benchmark ICLR 2026
"""

import json
import os
import re
from datetime import datetime
from typing import Dict, List, Any, Tuple
from recommender import MetroCampusRecommender
from llm_interface import create_llm_provider


# ============================================================================
# CONSULTAS DESAFÍO
# ============================================================================

CHALLENGE_QUERIES = [
    {
        "id": 1,
        "query": "Desde Sol, ¿cuál es el mejor campus para estudiar el Máster en Inteligencia Artificial?",
        "expected": {
            "estacion_origen": "Sol",
            "estudio": "Inteligencia Artificial",
            "campus_validos": ["Ciudad Universitaria (UCM)", "Campus de Moncloa (UPM)", "Campus de Leganés (UC3M)", "Campus Sur (UPM)"],
            "requiere_transbordo": True,
            "lineas_validas": [[1, 6], [3], [3, 6]]  # Posibles combinaciones
        },
        "difficulty": "medium"
    },
    {
        "id": 2,
        "query": "Estoy en Atocha y quiero estudiar el Grado en Ciencia e Ingeniería de Datos. ¿Qué opciones tengo?",
        "expected": {
            "estacion_origen": "Atocha",
            "estudio": "Ciencia e Ingeniería de Datos",
            "campus_validos": ["Ciudad Universitaria (UCM)", "Campus de Leganés (UC3M)", "Campus de Fuenlabrada (URJC)"],
            "requiere_transbordo": True,
            "lineas_validas": [[1, 6], [1, 3, 6]]
        },
        "difficulty": "medium"
    },
    {
        "id": 3,
        "query": "Desde Chamartín, busco el campus más cercano con Máster en Big Data",
        "expected": {
            "estacion_origen": "Chamartín",
            "estudio": "Big Data",
            "campus_validos": ["Ciudad Universitaria (UCM)", "Campus Sur (UPM)"],
            "requiere_transbordo": True,
            "lineas_validas": [[1, 6], [10, 6]]
        },
        "difficulty": "hard"
    },
    {
        "id": 4,
        "query": "¿Cómo llego desde Príncipe Pío a un campus de la UPM que ofrezca Inteligencia Artificial?",
        "expected": {
            "estacion_origen": "Príncipe Pío",
            "estudio": "Inteligencia Artificial",
            "campus_validos": ["Campus de Moncloa (UPM)", "Campus Sur (UPM)"],
            "universidad": "UPM",
            "requiere_transbordo": False,  # Príncipe Pío está en L6
            "lineas_validas": [[6], [6, 10]]
        },
        "difficulty": "easy"
    },
    {
        "id": 5,
        "query": "Desde Moncloa, ¿qué campus ofrecen el Grado en Ingeniería Informática?",
        "expected": {
            "estacion_origen": "Moncloa",
            "estudio": "Ingeniería Informática",
            "campus_validos": ["Ciudad Universitaria (UCM)", "Campus de Leganés (UC3M)"],
            "requiere_transbordo": False,  # Moncloa conecta con Ciudad Universitaria por L6
            "lineas_validas": [[6], [3, 6]]
        },
        "difficulty": "easy"
    },
    {
        "id": 6,
        "query": "Desde Pacífico, quiero llegar a la UC3M para estudiar Machine Learning",
        "expected": {
            "estacion_origen": "Pacífico",
            "estudio": "Machine Learning",
            "campus_validos": ["Campus de Leganés (UC3M)"],
            "universidad": "UC3M",
            "requiere_transbordo": True,
            "lineas_validas": [[6, 3], [1, 3]]
        },
        "difficulty": "hard"
    },
    {
        "id": 7,
        "query": "Busco un campus de la URJC desde Sol para estudiar Cloud Computing",
        "expected": {
            "estacion_origen": "Sol",
            "estudio": "Cloud Computing",
            "campus_validos": ["Campus de Fuenlabrada (URJC)", "Campus de Vicálvaro (URJC)"],
            "universidad": "URJC",
            "requiere_transbordo": True,
            "lineas_validas": [[1, 10], [2, 9]]
        },
        "difficulty": "hard"
    },
    {
        "id": 8,
        "query": "Desde Ciudad Universitaria, ¿puedo llegar a algún campus con Máster en Robótica?",
        "expected": {
            "estacion_origen": "Ciudad Universitaria",
            "estudio": "Robótica",
            "campus_validos": ["Campus de Moncloa (UPM)"],
            "requiere_transbordo": False,  # L6 conecta ambas
            "lineas_validas": [[6]]
        },
        "difficulty": "easy"
    },
    {
        "id": 9,
        "query": "Desde Plaza de Castilla, necesito llegar a un campus UCM. ¿Cuál es la mejor ruta?",
        "expected": {
            "estacion_origen": "Plaza de Castilla",
            "universidad": "UCM",
            "campus_validos": ["Ciudad Universitaria (UCM)"],
            "requiere_transbordo": True,
            "lineas_validas": [[1, 6], [10, 6]]
        },
        "difficulty": "medium"
    },
    {
        "id": 10,
        "query": "Desde Cuatro Caminos, quiero estudiar el Máster en Ciberseguridad. ¿Dónde puedo ir?",
        "expected": {
            "estacion_origen": "Cuatro Caminos",
            "estudio": "Ciberseguridad",
            "campus_validos": ["Ciudad Universitaria (UCM)"],
            "requiere_transbordo": False,  # Cuatro Caminos conecta con L6
            "lineas_validas": [[6]]
        },
        "difficulty": "easy"
    }
]


# ============================================================================
# MÉTRICAS DE EVALUACIÓN
# ============================================================================

class EvaluationMetrics:
    """Calcula métricas de evaluación para Baseline vs GraphRAG"""

    @staticmethod
    def validate_route(response: str, expected: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valida si la ruta propuesta es válida

        Returns:
            Dict con métricas de validación
        """
        metrics = {
            "is_valid": False,
            "found_correct_campus": False,
            "found_correct_origin": False,
            "num_transbordos_mencionados": 0,
            "hallucinations_detected": []
        }

        response_lower = response.lower()

        # 1. Verificar si menciona la estación de origen correcta
        if expected.get("estacion_origen"):
            if expected["estacion_origen"].lower() in response_lower:
                metrics["found_correct_origin"] = True

        # 2. Verificar si menciona algún campus válido
        for campus in expected.get("campus_validos", []):
            if campus.lower() in response_lower:
                metrics["found_correct_campus"] = True
                break

        # 3. Contar transbordos mencionados
        transbordo_patterns = [
            r"(\d+)\s*transbordo",
            r"cambio\s+de\s+l[ií]nea",
            r"sin\s+transbordo",
            r"directo"
        ]

        for pattern in transbordo_patterns:
            matches = re.findall(pattern, response_lower)
            if matches:
                if "sin transbordo" in response_lower or "directo" in response_lower:
                    metrics["num_transbordos_mencionados"] = 0
                elif matches[0].isdigit():
                    metrics["num_transbordos_mencionados"] = int(matches[0])
                else:
                    metrics["num_transbordos_mencionados"] = 1

        # 4. Detectar alucinaciones (estaciones/campus que no existen)
        hallucination_indicators = [
            "no tengo información",
            "no puedo confirmar",
            "no estoy seguro",
            "puede que",
            "probablemente"
        ]

        for indicator in hallucination_indicators:
            if indicator in response_lower:
                metrics["hallucinations_detected"].append(indicator)

        # Determinar si es válida
        metrics["is_valid"] = (
            metrics["found_correct_origin"] and
            metrics["found_correct_campus"]
        )

        return metrics

    @staticmethod
    def detect_hallucinations_graphrag(response: str, context_data: Dict[str, Any]) -> List[str]:
        """
        Detecta alucinaciones en respuesta GraphRAG comparando con el contexto

        Returns:
            Lista de alucinaciones detectadas
        """
        hallucinations = []
        response_lower = response.lower()

        # Obtener campus y estaciones del contexto
        campus_reales = set()
        estaciones_reales = set()

        for campus in context_data.get("campus", []):
            campus_reales.add(campus["nombre"].lower())

        for ruta in context_data.get("rutas", []):
            for estacion in ruta.get("ruta", []):
                estaciones_reales.add(estacion.lower())

        # Detectar mención de campus no presentes en el contexto
        campus_mencionados = re.findall(r"campus\s+(?:de\s+)?([A-ZÁ-Úa-záéíóúñ\s]+)", response, re.IGNORECASE)
        for campus_mencionado in campus_mencionados:
            campus_clean = campus_mencionado.strip().lower()
            if campus_clean and not any(campus_clean in real for real in campus_reales):
                if len(campus_clean) > 3:  # Evitar falsos positivos
                    hallucinations.append(f"Campus mencionado no en contexto: {campus_mencionado}")

        return hallucinations

    @staticmethod
    def calculate_success_rate(results: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calcula tasa de éxito para Baseline y GraphRAG"""
        baseline_success = sum(1 for r in results if r.get("baseline_metrics", {}).get("is_valid", False))
        graphrag_success = sum(1 for r in results if r.get("graphrag_metrics", {}).get("is_valid", False))

        total = len(results)

        return {
            "baseline_success_rate": baseline_success / total if total > 0 else 0,
            "graphrag_success_rate": graphrag_success / total if total > 0 else 0,
            "total_queries": total
        }


# ============================================================================
# EVALUADOR PRINCIPAL
# ============================================================================

class BenchmarkEvaluator:
    """Evaluador principal para el benchmark"""

    def __init__(self, recommender: MetroCampusRecommender, verbose: bool = True):
        """
        Inicializa el evaluador

        Args:
            recommender: Instancia de MetroCampusRecommender
            verbose: Imprimir información de progreso
        """
        self.recommender = recommender
        self.verbose = verbose
        self.metrics_calculator = EvaluationMetrics()

    def run_benchmark(self, queries: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Ejecuta el benchmark completo

        Args:
            queries: Lista de consultas desafío (usa CHALLENGE_QUERIES por defecto)

        Returns:
            Dict con resultados completos
        """
        if queries is None:
            queries = CHALLENGE_QUERIES

        results = []

        if self.verbose:
            print("\n" + "=" * 80)
            print("BENCHMARK: BASELINE vs GRAPHRAG")
            print("=" * 80)
            print(f"Total de consultas: {len(queries)}\n")

        for i, challenge in enumerate(queries, 1):
            if self.verbose:
                print(f"\n[{i}/{len(queries)}] Procesando consulta {challenge['id']}...")
                print(f"Dificultad: {challenge['difficulty']}")
                print(f"Query: {challenge['query']}")

            # Ejecutar ambos métodos
            try:
                comparison = self.recommender.compare_methods(challenge["query"])

                # Evaluar Baseline
                baseline_metrics = self.metrics_calculator.validate_route(
                    comparison["baseline"]["response"],
                    challenge["expected"]
                )

                # Evaluar GraphRAG
                graphrag_metrics = self.metrics_calculator.validate_route(
                    comparison["graphrag"]["response"],
                    challenge["expected"]
                )

                # Detectar alucinaciones específicas de GraphRAG
                graphrag_hallucinations = self.metrics_calculator.detect_hallucinations_graphrag(
                    comparison["graphrag"]["response"],
                    comparison["graphrag"].get("context", {})
                )

                result = {
                    "challenge_id": challenge["id"],
                    "query": challenge["query"],
                    "difficulty": challenge["difficulty"],
                    "expected": challenge["expected"],
                    "baseline_response": comparison["baseline"]["response"],
                    "graphrag_response": comparison["graphrag"]["response"],
                    "baseline_metrics": baseline_metrics,
                    "graphrag_metrics": graphrag_metrics,
                    "graphrag_hallucinations": graphrag_hallucinations,
                    "graphrag_context": {
                        "campus_found": len(comparison["graphrag"].get("context", {}).get("campus", [])),
                        "routes_calculated": len(comparison["graphrag"].get("context", {}).get("rutas", []))
                    }
                }

                results.append(result)

                if self.verbose:
                    print(f"  ✓ Baseline válido: {baseline_metrics['is_valid']}")
                    print(f"  ✓ GraphRAG válido: {graphrag_metrics['is_valid']}")
                    print(f"  • Campus encontrados (GraphRAG): {result['graphrag_context']['campus_found']}")
                    print(f"  • Rutas calculadas (GraphRAG): {result['graphrag_context']['routes_calculated']}")

            except Exception as e:
                if self.verbose:
                    print(f"  ✗ Error procesando consulta: {e}")

        # Calcular métricas globales
        success_rates = self.metrics_calculator.calculate_success_rate(results)

        benchmark_results = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "total_queries": len(queries),
                "llm_provider": type(self.recommender.llm).__name__
            },
            "results": results,
            "summary": {
                "success_rates": success_rates,
                "avg_transbordos_baseline": self._calculate_avg_transbordos(results, "baseline"),
                "avg_transbordos_graphrag": self._calculate_avg_transbordos(results, "graphrag"),
                "total_hallucinations_baseline": sum(
                    len(r.get("baseline_metrics", {}).get("hallucinations_detected", []))
                    for r in results
                ),
                "total_hallucinations_graphrag": sum(
                    len(r.get("graphrag_hallucinations", []))
                    for r in results
                )
            }
        }

        return benchmark_results

    def _calculate_avg_transbordos(self, results: List[Dict[str, Any]], method: str) -> float:
        """Calcula promedio de transbordos mencionados"""
        key = f"{method}_metrics"
        transbordos = [
            r.get(key, {}).get("num_transbordos_mencionados", 0)
            for r in results
            if r.get(key, {}).get("is_valid", False)
        ]

        return sum(transbordos) / len(transbordos) if transbordos else 0

    def print_summary(self, benchmark_results: Dict[str, Any]):
        """Imprime resumen de resultados"""
        summary = benchmark_results["summary"]

        print("\n" + "=" * 80)
        print("RESUMEN DE RESULTADOS")
        print("=" * 80)

        print(f"\n📊 TASA DE ÉXITO:")
        print(f"  • Baseline:  {summary['success_rates']['baseline_success_rate']:.1%}")
        print(f"  • GraphRAG:  {summary['success_rates']['graphrag_success_rate']:.1%}")

        print(f"\n🔄 TRANSBORDOS PROMEDIO:")
        print(f"  • Baseline:  {summary['avg_transbordos_baseline']:.2f}")
        print(f"  • GraphRAG:  {summary['avg_transbordos_graphrag']:.2f}")

        print(f"\n🚨 ALUCINACIONES DETECTADAS:")
        print(f"  • Baseline:  {summary['total_hallucinations_baseline']}")
        print(f"  • GraphRAG:  {summary['total_hallucinations_graphrag']}")

        print(f"\n✅ GANADOR: ", end="")
        if summary['success_rates']['graphrag_success_rate'] > summary['success_rates']['baseline_success_rate']:
            print("GraphRAG")
        elif summary['success_rates']['baseline_success_rate'] > summary['success_rates']['graphrag_success_rate']:
            print("Baseline")
        else:
            print("Empate")

        print()

    def save_results(self, benchmark_results: Dict[str, Any], output_path: str = "results/experiments.json"):
        """Guarda resultados en JSON"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(benchmark_results, f, ensure_ascii=False, indent=2)

        if self.verbose:
            print(f"\n💾 Resultados guardados en: {output_path}")


# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================

def main():
    """Función principal para ejecutar el benchmark"""
    print("=" * 80)
    print("BENCHMARK DE EVALUACIÓN - BASELINE vs GRAPHRAG")
    print("Metro de Madrid y Universidades - ICLR 2026")
    print("=" * 80)

    # Crear recomendador
    print("\n🔧 Inicializando sistema...")
    recommender = MetroCampusRecommender(
        llm_provider=create_llm_provider("mock"),  # Cambiar a "openai" o "anthropic" en producción
        verbose=False  # Desactivar verbose del recomendador para claridad
    )

    try:
        # Crear evaluador
        evaluator = BenchmarkEvaluator(recommender, verbose=True)

        # Ejecutar benchmark
        print("\n🚀 Ejecutando benchmark...")
        results = evaluator.run_benchmark()

        # Mostrar resumen
        evaluator.print_summary(results)

        # Guardar resultados
        evaluator.save_results(results)

        print("\n" + "=" * 80)
        print("✅ BENCHMARK COMPLETADO")
        print("=" * 80)

    finally:
        recommender.close()


if __name__ == "__main__":
    main()

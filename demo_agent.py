#!/usr/bin/env python3
"""
Script de Demostración del Agente Recomendador
Muestra ambos métodos: Baseline vs GraphRAG
"""

import sys
import os

# Añadir directorio src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from agent import MetroCampusRecommender, create_llm_provider


def demo_baseline_vs_graphrag():
    """Demostración de Baseline vs GraphRAG con una consulta"""

    print("=" * 80)
    print("DEMOSTRACIÓN: BASELINE vs GRAPHRAG")
    print("Metro de Madrid y Universidades - URJC 2025/2026")
    print("=" * 80)

    # Consulta de ejemplo
    query = "Desde Sol, ¿cuál es el mejor campus para estudiar el Máster en Inteligencia Artificial?"

    print(f"\n📋 CONSULTA:")
    print(f"   {query}")
    print()

    # Crear recomendador con MockProvider (para demo sin API)
    print("🔧 Inicializando sistema...")
    recommender = MetroCampusRecommender(
        llm_provider=create_llm_provider("mock"),
        verbose=False  # Desactivar logs internos para claridad
    )

    try:
        # Ejecutar ambos métodos
        print("\n" + "-" * 80)
        print("MÉTODO 1: BASELINE LLM (Sin acceso a bases de datos)")
        print("-" * 80)

        baseline_result = recommender.baseline_llm(query)
        print(f"\n{baseline_result['response']}")

        print("\n" + "-" * 80)
        print("MÉTODO 2: GRAPHRAG (Con contexto de MongoDB + Neo4j)")
        print("-" * 80)

        graphrag_result = recommender.graphrag_recommendation(query)

        # Mostrar contexto recuperado
        context = graphrag_result.get('context', {})
        print(f"\n📊 CONTEXTO RECUPERADO:")
        print(f"  • Campus encontrados: {len(context.get('campus', []))}")
        print(f"  • Rutas calculadas: {len(context.get('rutas', []))}")

        if context.get('campus'):
            print(f"\n  Campus que ofrecen el estudio:")
            for campus in context['campus']:
                print(f"    - {campus['nombre']} ({campus['universidad']})")

        if context.get('rutas'):
            print(f"\n  Mejor ruta:")
            mejor_ruta = context['rutas'][0]
            print(f"    - Destino: {mejor_ruta['campus']}")
            print(f"    - Distancia: {mejor_ruta['num_estaciones']} estaciones")
            print(f"    - Transbordos: {mejor_ruta['num_cambios_linea']}")
            print(f"    - Líneas: {', '.join(['L' + str(l) for l in mejor_ruta['lineas_usadas']])}")

        print(f"\n💬 RESPUESTA DEL LLM:")
        print(f"{graphrag_result['response']}")

        # Comparación
        print("\n" + "=" * 80)
        print("COMPARACIÓN")
        print("=" * 80)
        print(f"\n{'Característica':<30} {'Baseline':<20} {'GraphRAG':<20}")
        print("-" * 70)
        print(f"{'Usa contexto de BD':<30} {'No':<20} {'Sí':<20}")
        print(f"{'Campus encontrados':<30} {'N/A':<20} {len(context.get('campus', [])):<20}")
        print(f"{'Rutas calculadas':<30} {'N/A':<20} {len(context.get('rutas', [])):<20}")
        print(f"{'Basado en datos reales':<30} {'No':<20} {'Sí':<20}")

        print("\n" + "=" * 80)
        print("✅ DEMOSTRACIÓN COMPLETADA")
        print("=" * 80)
        print("\n💡 Para ejecutar el benchmark completo:")
        print("   cd src/agent && python evaluate.py")
        print()

    finally:
        recommender.close()


def demo_interactive():
    """Demostración interactiva con consultas del usuario"""

    print("=" * 80)
    print("MODO INTERACTIVO - AGENTE RECOMENDADOR")
    print("=" * 80)

    recommender = MetroCampusRecommender(
        llm_provider=create_llm_provider("mock"),
        verbose=False
    )

    try:
        print("\nEscribe tus consultas (o 'salir' para terminar):")
        print("Ejemplos:")
        print("  - Desde Atocha, ¿dónde puedo estudiar Ingeniería de Datos?")
        print("  - ¿Cómo llego desde Moncloa a la UPM?")
        print("  - Busco un Máster en Machine Learning desde Sol")
        print()

        while True:
            query = input("\n📋 Tu consulta: ").strip()

            if query.lower() in ['salir', 'exit', 'quit']:
                print("\n👋 ¡Hasta luego!")
                break

            if not query:
                continue

            # Elegir método
            print("\n¿Qué método quieres usar?")
            print("  1. Baseline (sin BD)")
            print("  2. GraphRAG (con BD)")
            print("  3. Comparar ambos")

            opcion = input("Opción [1/2/3]: ").strip()

            if opcion == "1":
                result = recommender.baseline_llm(query)
                print(f"\n💬 BASELINE:")
                print(result['response'])

            elif opcion == "2":
                result = recommender.graphrag_recommendation(query)
                context = result.get('context', {})
                print(f"\n📊 Campus: {len(context.get('campus', []))} | Rutas: {len(context.get('rutas', []))}")
                print(f"\n💬 GRAPHRAG:")
                print(result['response'])

            elif opcion == "3":
                comparison = recommender.compare_methods(query)
                print(f"\n💬 BASELINE:")
                print(comparison['baseline']['response'])
                print(f"\n💬 GRAPHRAG:")
                print(comparison['graphrag']['response'])

            else:
                print("❌ Opción inválida")

    finally:
        recommender.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Demo del Agente Recomendador")
    parser.add_argument(
        "--mode",
        choices=["demo", "interactive"],
        default="demo",
        help="Modo de ejecución (default: demo)"
    )

    args = parser.parse_args()

    if args.mode == "demo":
        demo_baseline_vs_graphrag()
    else:
        demo_interactive()

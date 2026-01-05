#!/usr/bin/env python3
"""
Consultas de la Parte C - Funcionalidad de Recomendación
Práctica de Bases de Datos No Relacionales - Metro de Madrid y Universidades
Universidad Rey Juan Carlos - Curso 2025/2026

Este script implementa:
- Agregación para comparar trayectos usando indice_por_linea (misma línea)
- Funcionalidad de recomendación simplificada en MongoDB
"""

import os
from pymongo import MongoClient
from typing import List, Dict, Optional
from pprint import pprint


# Configuración
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
DATABASE_NAME = "metro_campus_db"


class RecomendacionMongoDB:
    """Clase para funcionalidad de recomendación en MongoDB (Parte C)"""

    def __init__(self, uri: str, db_name: str):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        print(f"✓ Conectado a MongoDB: {db_name}\n")

    def comparar_trayectos_misma_linea(self, nombre_estacion_origen: str,
                                        nombre_estacion_destino: str,
                                        numero_linea: int):
        """
        AGREGACIÓN: Comparar trayectos en una misma línea usando indice_por_linea

        Esta función demuestra cómo MongoDB puede calcular distancias
        SOLO cuando ambas estaciones están en la MISMA línea (limitación del modelo documental)
        """
        print("=" * 80)
        print(f"📊 AGREGACIÓN: Comparación de trayecto en Línea {numero_linea}")
        print(f"   Origen: {nombre_estacion_origen}")
        print(f"   Destino: {nombre_estacion_destino}")
        print("=" * 80 + "\n")

        # Obtener índices de ambas estaciones en la línea
        estacion_origen = self.db.estaciones.find_one({"nombre": nombre_estacion_origen})
        estacion_destino = self.db.estaciones.find_one({"nombre": nombre_estacion_destino})

        if not estacion_origen or not estacion_destino:
            print("⚠️  Una o ambas estaciones no existen")
            return None

        # Verificar que ambas estén en la línea especificada
        linea_str = str(numero_linea)
        if (numero_linea not in estacion_origen.get("lineas", []) or
            numero_linea not in estacion_destino.get("lineas", [])):
            print(f"⚠️  Una o ambas estaciones no pertenecen a la Línea {numero_linea}")
            return None

        # Obtener índices
        indice_origen = estacion_origen["indice_por_linea"].get(linea_str)
        indice_destino = estacion_destino["indice_por_linea"].get(linea_str)

        # Calcular distancia (valor absoluto de la diferencia de índices)
        distancia_estaciones = abs(indice_destino - indice_origen)

        print(f"📍 Índice en L{numero_linea}:")
        print(f"   {nombre_estacion_origen}: {indice_origen}")
        print(f"   {nombre_estacion_destino}: {indice_destino}")
        print(f"\n✅ Distancia: {distancia_estaciones} estaciones")
        print(f"   Tiempo estimado: {distancia_estaciones * 2.5:.1f} minutos\n")

        return {
            "origen": nombre_estacion_origen,
            "destino": nombre_estacion_destino,
            "linea": numero_linea,
            "indice_origen": indice_origen,
            "indice_destino": indice_destino,
            "distancia_estaciones": distancia_estaciones,
            "tiempo_estimado_min": distancia_estaciones * 2.5
        }

    def recomendar_campus_simplificado(self, nombre_estacion_origen: str,
                                        nombre_estudio: str,
                                        tipo_estudio: str = "GRADO") -> List[Dict]:
        """
        PARTE C: Funcionalidad de recomendación SIMPLIFICADA en MongoDB

        Limitaciones del modelo documental:
        - Solo puede calcular distancia si origen y campus están en la MISMA línea
        - No puede calcular rutas con cambios de línea (requiere Neo4j)
        - Usa indice_por_linea para estimar distancia

        Args:
            nombre_estacion_origen: Estación desde donde el usuario parte
            nombre_estudio: Nombre del estudio a buscar (búsqueda parcial)
            tipo_estudio: GRADO o MASTER

        Returns:
            Lista de campus ordenados por accesibilidad (cuando están en misma línea)
        """
        print("=" * 80)
        print("🎓 FUNCIONALIDAD DE RECOMENDACIÓN SIMPLIFICADA - MongoDB")
        print(f"   Estación origen: {nombre_estacion_origen}")
        print(f"   Buscando: {tipo_estudio} en '{nombre_estudio}'")
        print("=" * 80 + "\n")

        # 1. Obtener la estación de origen
        estacion_origen = self.db.estaciones.find_one({"nombre": nombre_estacion_origen})
        if not estacion_origen:
            print(f"⚠️  Estación '{nombre_estacion_origen}' no encontrada")
            return []

        lineas_origen = estacion_origen.get("lineas", [])
        print(f"📍 Estación origen: {nombre_estacion_origen}")
        print(f"   Líneas disponibles: L{', L'.join(map(str, lineas_origen))}\n")

        # 2. Buscar campus que ofrecen el estudio
        campus_con_estudio = list(self.db.campus.find({
            "estudios": {
                "$elemMatch": {
                    "tipo": tipo_estudio,
                    "nombre": {"$regex": nombre_estudio, "$options": "i"}
                }
            }
        }))

        if not campus_con_estudio:
            print(f"⚠️  No se encontraron campus con {tipo_estudio} en '{nombre_estudio}'")
            return []

        print(f"✅ Encontrados {len(campus_con_estudio)} campus que ofrecen el estudio:\n")

        # 3. Para cada campus, calcular accesibilidad
        resultados = []

        for campus in campus_con_estudio:
            # Encontrar el estudio específico
            estudio_encontrado = None
            for est in campus["estudios"]:
                if est["tipo"] == tipo_estudio and nombre_estudio.lower() in est["nombre"].lower():
                    estudio_encontrado = est
                    break

            campus_info = {
                "universidad": campus["universidad"],
                "nombre_campus": campus["nombre"],
                "estudio": estudio_encontrado["nombre"],
                "plazas": estudio_encontrado.get("plazas", "N/A"),
                "nota_corte": estudio_encontrado.get("nota_corte", "N/A"),
                "estaciones_cercanas": [],
                "accesible_misma_linea": False,
                "mejor_ruta": None
            }

            # Analizar estaciones cercanas al campus
            for est_cercana in campus["estaciones_cercanas"]:
                est_id = est_cercana["estacion_id"]
                estacion_campus = self.db.estaciones.find_one({"_id": est_id})

                if not estacion_campus:
                    continue

                est_info = {
                    "nombre": estacion_campus["nombre"],
                    "rol": est_cercana["rol"],
                    "minutos_andando": est_cercana["minutos_andando"],
                    "lineas": estacion_campus.get("lineas", []),
                    "misma_linea": False,
                    "linea_comun": None,
                    "distancia_estaciones": None
                }

                # Verificar si hay línea en común
                lineas_comunes = set(lineas_origen) & set(estacion_campus.get("lineas", []))

                if lineas_comunes:
                    # Hay línea en común! Calcular distancia
                    linea_comun = list(lineas_comunes)[0]

                    indice_origen = estacion_origen["indice_por_linea"].get(str(linea_comun))
                    indice_destino = estacion_campus["indice_por_linea"].get(str(linea_comun))

                    if indice_origen is not None and indice_destino is not None:
                        distancia = abs(indice_destino - indice_origen)

                        est_info["misma_linea"] = True
                        est_info["linea_comun"] = linea_comun
                        est_info["distancia_estaciones"] = distancia
                        est_info["tiempo_total_estimado"] = (distancia * 2.5) + est_cercana["minutos_andando"]

                        campus_info["accesible_misma_linea"] = True

                        # Guardar la mejor ruta si no existe o es mejor
                        if (campus_info["mejor_ruta"] is None or
                            est_info["tiempo_total_estimado"] < campus_info["mejor_ruta"]["tiempo_total_estimado"]):
                            campus_info["mejor_ruta"] = est_info

                campus_info["estaciones_cercanas"].append(est_info)

            resultados.append(campus_info)

        # 4. Ordenar por accesibilidad
        # Primero los accesibles en misma línea, luego por tiempo total
        resultados.sort(
            key=lambda x: (
                not x["accesible_misma_linea"],  # False primero (son accesibles)
                x["mejor_ruta"]["tiempo_total_estimado"] if x["mejor_ruta"] else 9999
            )
        )

        # 5. Mostrar resultados
        print("📊 RESULTADOS DE RECOMENDACIÓN:\n")
        print("=" * 80)

        for i, campus in enumerate(resultados, 1):
            print(f"\n{i}. {campus['nombre_campus']} ({campus['universidad']})")
            print(f"   📚 Estudio: {campus['estudio']}")
            print(f"   📊 Plazas: {campus['plazas']} | Nota corte: {campus['nota_corte']}")

            if campus["accesible_misma_linea"]:
                ruta = campus["mejor_ruta"]
                print(f"\n   ✅ ACCESIBLE en MISMA LÍNEA (L{ruta['linea_comun']})")
                print(f"   🚇 Destino: {ruta['nombre']} ({ruta['rol']})")
                print(f"   📏 Distancia: {ruta['distancia_estaciones']} estaciones")
                print(f"   🚶 + {ruta['minutos_andando']} min andando")
                print(f"   ⏱️  TIEMPO TOTAL: {ruta['tiempo_total_estimado']:.1f} minutos")
            else:
                print(f"\n   ⚠️  REQUIERE CAMBIO DE LÍNEA")
                print(f"   💡 Usar Neo4j para calcular ruta completa")

                # Mostrar estaciones cercanas
                if campus["estaciones_cercanas"]:
                    est_principal = [e for e in campus["estaciones_cercanas"] if e["rol"] == "principal"]
                    if est_principal:
                        est = est_principal[0]
                        print(f"   🚇 Estación más cercana: {est['nombre']} (L{', L'.join(map(str, est['lineas']))})")

        print("\n" + "=" * 80)
        print("\n💡 LIMITACIÓN DE MONGODB:")
        print("   MongoDB solo puede calcular rutas en la MISMA línea usando indice_por_linea.")
        print("   Para rutas con cambios de línea → usar Neo4j con shortestPath()")
        print("=" * 80 + "\n")

        return resultados

    def close(self):
        """Cierra la conexión"""
        self.client.close()


def main():
    """Función principal con ejemplos de uso"""
    print("=" * 80)
    print("PARTE C - FUNCIONALIDAD DE RECOMENDACIÓN")
    print("Comparativa MongoDB (Simplificado) vs Neo4j (Completo)")
    print("=" * 80 + "\n")

    rec = RecomendacionMongoDB(MONGODB_URI, DATABASE_NAME)

    try:
        # ================================================================
        # EJEMPLO 1: Comparación de trayectos en misma línea
        # ================================================================
        print("\n" + "=" * 80)
        print("EJEMPLO 1: COMPARACIÓN DE TRAYECTOS (MISMA LÍNEA)")
        print("=" * 80 + "\n")

        # Comparar trayecto en Línea 1
        rec.comparar_trayectos_misma_linea(
            nombre_estacion_origen="Sol",
            nombre_estacion_destino="Atocha",
            numero_linea=1
        )

        # Comparar trayecto en Línea 6
        rec.comparar_trayectos_misma_linea(
            nombre_estacion_origen="Moncloa",
            nombre_estacion_destino="Ciudad Universitaria",
            numero_linea=6
        )

        # ================================================================
        # EJEMPLO 2: Recomendación simplificada desde Sol
        # ================================================================
        print("\n" + "=" * 80)
        print("EJEMPLO 2: RECOMENDACIÓN DE CAMPUS (desde Sol)")
        print("=" * 80 + "\n")

        resultados_sol = rec.recomendar_campus_simplificado(
            nombre_estacion_origen="Sol",
            nombre_estudio="Ciencia e Ingeniería de Datos",
            tipo_estudio="GRADO"
        )

        # ================================================================
        # EJEMPLO 3: Recomendación desde Ciudad Universitaria
        # ================================================================
        print("\n" + "=" * 80)
        print("EJEMPLO 3: RECOMENDACIÓN DE CAMPUS (desde Ciudad Universitaria)")
        print("=" * 80 + "\n")

        resultados_cu = rec.recomendar_campus_simplificado(
            nombre_estacion_origen="Ciudad Universitaria",
            nombre_estudio="Inteligencia Artificial",
            tipo_estudio="MASTER"
        )

        # ================================================================
        # EJEMPLO 4: Recomendación desde Atocha
        # ================================================================
        print("\n" + "=" * 80)
        print("EJEMPLO 4: RECOMENDACIÓN DE CAMPUS (desde Atocha)")
        print("=" * 80 + "\n")

        resultados_atocha = rec.recomendar_campus_simplificado(
            nombre_estacion_origen="Atocha",
            nombre_estudio="Ingeniería Informática",
            tipo_estudio="GRADO"
        )

        # ================================================================
        # RESUMEN FINAL
        # ================================================================
        print("\n" + "=" * 80)
        print("📝 CONCLUSIÓN: MongoDB vs Neo4j para RECOMENDACIÓN")
        print("=" * 80)
        print("""
🔹 MONGODB (Modelo Documental):
   ✅ Ventajas:
      - Rápido para consultas de campus y estudios
      - Buen para filtrar por características (universidad, tipo, plazas)
      - Puede calcular distancia SI origen y destino están en la MISMA línea

   ❌ Limitaciones:
      - NO puede calcular rutas con cambios de línea
      - NO puede usar algoritmos de grafos (shortestPath)
      - Lógica de trayectos limitada a comparaciones simples

🔹 NEO4J (Base de Datos de Grafos):
   ✅ Ventajas:
      - Calcula rutas óptimas con CUALQUIER número de cambios
      - Algoritmo shortestPath() nativo
      - Puede contar cambios de línea usando propiedad lineaId
      - Soporta criterios multiobjetivo (distancia + cambios + Renfe)

   ❌ Limitaciones:
      - Consultas más complejas de escribir
      - Menos eficiente para filtros por características de estudios

🎯 RECOMENDACIÓN FINAL:
   Para un sistema de recomendación REAL de campus por Metro:

   1. Usar NEO4J para calcular rutas y trayectos
   2. Usar MONGODB para obtener detalles de estudios, plazas, notas
   3. Combinar ambos: Neo4j encuentra la mejor ruta, MongoDB enriquece con datos
        """)
        print("=" * 80 + "\n")

        print("✅ PARTE C COMPLETADA")
        print("   Se ha demostrado la limitación de MongoDB y la superioridad de Neo4j")
        print("   para el problema de recomendación de campus basada en rutas de Metro.\n")

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

    finally:
        rec.close()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Script de carga de datos para Neo4j
Práctica de Bases de Datos No Relacionales - Metro de Madrid y Universidades
Universidad Rey Juan Carlos - Curso 2025/2026
"""

import json
import os
from neo4j import GraphDatabase
from typing import List, Dict

# Configuración de conexión
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

# Rutas a los archivos de datos
DATA_DIR = os.path.join(os.path.dirname(__file__), "../../data")
LINEAS_FILE = os.path.join(DATA_DIR, "lineas.json")
ESTACIONES_FILE = os.path.join(DATA_DIR, "estaciones.json")
CAMPUS_FILE = os.path.join(DATA_DIR, "campus.json")


class Neo4jLoader:
    """Clase para cargar datos en Neo4j"""

    def __init__(self, uri: str, user: str, password: str):
        """Inicializa la conexión a Neo4j"""
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        print(f"✓ Conectado a Neo4j: {uri}")

    def close(self):
        """Cierra la conexión"""
        self.driver.close()
        print("✓ Conexión cerrada")

    def load_json_file(self, file_path: str) -> List[Dict]:
        """Carga un archivo JSON"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"✓ Archivo cargado: {os.path.basename(file_path)} ({len(data)} registros)")
        return data

    def clear_database(self):
        """Elimina todos los nodos y relaciones"""
        print("\n🗑️  Limpiando base de datos Neo4j...")

        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            print("✓ Base de datos limpiada")

    def create_lineas(self, lineas_data: List[Dict]):
        """Crea nodos de líneas"""
        print("\n📊 Creando nodos :Linea...")

        with self.driver.session() as session:
            query = """
            UNWIND $lineas AS linea
            CREATE (l:Linea {
                numero: linea.numero,
                nombre: linea.nombre,
                color: linea.color
            })
            """
            session.run(query, lineas=lineas_data)
            print(f"✓ {len(lineas_data)} líneas creadas")

    def create_estaciones(self, estaciones_data: List[Dict]):
        """Crea nodos de estaciones"""
        print("\n🚇 Creando nodos :Estacion...")

        with self.driver.session() as session:
            # Preparar datos de estaciones
            estaciones_para_neo4j = []
            for est in estaciones_data:
                estacion = {
                    "id": est["id"],
                    "nombre": est["nombre"],
                    "zona_tarifaria": est["zona_tarifaria"],
                    "tiene_renfe": est["tiene_renfe"],
                    "lat": est["coordenadas"]["lat"],
                    "lng": est["coordenadas"]["lng"]
                }

                # Agregar info de Renfe si existe
                if est.get("estacion_renfe"):
                    estacion["nombre_estacion_renfe"] = est["estacion_renfe"]["nombre"]
                    estacion["lineas_renfe"] = est["estacion_renfe"]["lineas_renfe"]

                estaciones_para_neo4j.append(estacion)

            # Crear nodos
            query = """
            UNWIND $estaciones AS est
            CREATE (e:Estacion {
                id: est.id,
                nombre: est.nombre,
                zona_tarifaria: est.zona_tarifaria,
                tiene_renfe: est.tiene_renfe,
                lat: est.lat,
                lng: est.lng,
                nombre_estacion_renfe: est.nombre_estacion_renfe,
                lineas_renfe: est.lineas_renfe
            })
            """
            session.run(query, estaciones=estaciones_para_neo4j)
            print(f"✓ {len(estaciones_para_neo4j)} estaciones creadas")

    def create_relaciones_linea_estacion(self, estaciones_data: List[Dict]):
        """Crea relaciones :TIENE_ESTACION entre líneas y estaciones"""
        print("\n🔗 Creando relaciones :TIENE_ESTACION...")

        with self.driver.session() as session:
            # Preparar relaciones
            relaciones = []
            for est in estaciones_data:
                for linea_num in est["lineas"]:
                    orden = est["indice_por_linea"].get(str(linea_num), 0)
                    relaciones.append({
                        "estacion_id": est["id"],
                        "linea_numero": linea_num,
                        "orden": orden
                    })

            query = """
            UNWIND $relaciones AS rel
            MATCH (l:Linea {numero: rel.linea_numero})
            MATCH (e:Estacion {id: rel.estacion_id})
            CREATE (l)-[:TIENE_ESTACION {orden: rel.orden}]->(e)
            """
            result = session.run(query, relaciones=relaciones)
            print(f"✓ {len(relaciones)} relaciones :TIENE_ESTACION creadas")

    def create_relaciones_siguiente(self, estaciones_data: List[Dict]):
        """Crea relaciones :SIGUIENTE entre estaciones consecutivas"""
        print("\n➡️  Creando relaciones :SIGUIENTE...")

        with self.driver.session() as session:
            # Agrupar estaciones por línea
            estaciones_por_linea = {}
            for est in estaciones_data:
                for linea_num in est["lineas"]:
                    if linea_num not in estaciones_por_linea:
                        estaciones_por_linea[linea_num] = []

                    orden = est["indice_por_linea"].get(str(linea_num), 0)
                    estaciones_por_linea[linea_num].append({
                        "id": est["id"],
                        "nombre": est["nombre"],
                        "orden": orden
                    })

            # Crear relaciones :SIGUIENTE
            relaciones_siguiente = []
            for linea_num, estaciones in estaciones_por_linea.items():
                # Ordenar por índice
                estaciones_ordenadas = sorted(estaciones, key=lambda x: x["orden"])

                # Crear relaciones consecutivas
                for i in range(len(estaciones_ordenadas) - 1):
                    est_actual = estaciones_ordenadas[i]
                    est_siguiente = estaciones_ordenadas[i + 1]

                    # Tiempo de viaje estimado (2-3 minutos entre estaciones)
                    tiempo_viaje = 2 + (i % 2)  # Alterna entre 2 y 3 minutos

                    relaciones_siguiente.append({
                        "desde": est_actual["id"],
                        "hasta": est_siguiente["id"],
                        "linea_id": linea_num,
                        "tiempo_viaje": tiempo_viaje
                    })

            query = """
            UNWIND $relaciones AS rel
            MATCH (e1:Estacion {id: rel.desde})
            MATCH (e2:Estacion {id: rel.hasta})
            CREATE (e1)-[:SIGUIENTE {lineaId: rel.linea_id, tiempo_viaje: rel.tiempo_viaje}]->(e2)
            """
            result = session.run(query, relaciones=relaciones_siguiente)
            print(f"✓ {len(relaciones_siguiente)} relaciones :SIGUIENTE creadas")

    def create_relaciones_transbordo(self, estaciones_data: List[Dict]):
        """Crea relaciones :TRANSBORDO entre estaciones con múltiples líneas"""
        print("\n🔄 Creando relaciones :TRANSBORDO...")

        with self.driver.session() as session:
            # Encontrar estaciones con más de una línea
            estaciones_transbordo = [est for est in estaciones_data if len(est["lineas"]) > 1]

            count = 0
            for est in estaciones_transbordo:
                # Crear transbordo consigo misma (tiempo de cambio entre líneas)
                query = """
                MATCH (e:Estacion {id: $estacion_id})
                CREATE (e)-[:TRANSBORDO {tiempo_cambio: 3}]->(e)
                """
                session.run(query, estacion_id=est["id"])
                count += 1

            print(f"✓ {count} relaciones :TRANSBORDO creadas")

    def create_campus_y_estudios(self, campus_data: List[Dict]):
        """Crea nodos de campus y estudios con relaciones"""
        print("\n🎓 Creando nodos :Campus y :Estudio...")

        with self.driver.session() as session:
            total_campus = 0
            total_estudios = 0

            for campus in campus_data:
                # Crear nodo Campus
                query_campus = """
                CREATE (c:Campus {
                    nombre: $nombre,
                    universidad: $universidad,
                    direccion: $direccion
                })
                RETURN c
                """
                session.run(query_campus,
                            nombre=campus["nombre"],
                            universidad=campus["universidad"],
                            direccion=campus["direccion"])
                total_campus += 1

                # Crear nodos Estudio y relaciones :OFRECE
                for estudio in campus["estudios"]:
                    query_estudio = """
                    MATCH (c:Campus {nombre: $campus_nombre})
                    MERGE (e:Estudio {
                        nombre: $nombre,
                        tipo: $tipo
                    })
                    ON CREATE SET
                        e.rama = $rama,
                        e.duracion_años = $duracion_años,
                        e.creditos = $creditos,
                        e.plazas = $plazas,
                        e.nota_corte = $nota_corte,
                        e.duracion_meses = $duracion_meses
                    CREATE (c)-[:OFRECE]->(e)
                    """
                    session.run(query_estudio,
                                campus_nombre=campus["nombre"],
                                nombre=estudio["nombre"],
                                tipo=estudio["tipo"],
                                rama=estudio.get("rama"),
                                duracion_años=estudio.get("duracion_años"),
                                creditos=estudio.get("creditos"),
                                plazas=estudio.get("plazas"),
                                nota_corte=estudio.get("nota_corte"),
                                duracion_meses=estudio.get("duracion_meses"))
                    total_estudios += 1

                # Crear relaciones :CERCANA con estaciones
                for est_cercana in campus["estaciones_cercanas"]:
                    query_cercana = """
                    MATCH (c:Campus {nombre: $campus_nombre})
                    MATCH (e:Estacion {id: $estacion_id})
                    CREATE (c)-[:CERCANA {
                        minutos: $minutos,
                        rol: $rol
                    }]->(e)
                    """
                    session.run(query_cercana,
                                campus_nombre=campus["nombre"],
                                estacion_id=est_cercana["estacion_id"],
                                minutos=est_cercana["minutos_andando"],
                                rol=est_cercana["rol"])

            print(f"✓ {total_campus} campus creados")
            print(f"✓ {total_estudios} estudios creados (con MERGE para evitar duplicados)")

    def create_indexes(self):
        """Crea índices y constraints"""
        print("\n🔍 Creando índices y constraints...")

        with self.driver.session() as session:
            # Constraints
            constraints = [
                "CREATE CONSTRAINT linea_numero IF NOT EXISTS FOR (l:Linea) REQUIRE l.numero IS UNIQUE",
                "CREATE CONSTRAINT estacion_id IF NOT EXISTS FOR (e:Estacion) REQUIRE e.id IS UNIQUE",
                "CREATE CONSTRAINT campus_nombre IF NOT EXISTS FOR (c:Campus) REQUIRE c.nombre IS UNIQUE",
            ]

            for constraint in constraints:
                try:
                    session.run(constraint)
                except Exception as e:
                    # Los constraints pueden ya existir
                    pass

            # Índices
            indices = [
                "CREATE INDEX estacion_nombre IF NOT EXISTS FOR (e:Estacion) ON (e.nombre)",
                "CREATE INDEX estacion_renfe IF NOT EXISTS FOR (e:Estacion) ON (e.tiene_renfe)",
                "CREATE INDEX campus_universidad IF NOT EXISTS FOR (c:Campus) ON (c.universidad)",
                "CREATE INDEX estudio_nombre IF NOT EXISTS FOR (e:Estudio) ON (e.nombre)",
                "CREATE INDEX estudio_tipo IF NOT EXISTS FOR (e:Estudio) ON (e.tipo)",
            ]

            for index in indices:
                try:
                    session.run(index)
                except Exception as e:
                    pass

            print("✓ Índices y constraints creados")

    def show_statistics(self):
        """Muestra estadísticas del grafo"""
        print("\n📈 Estadísticas del grafo:")

        with self.driver.session() as session:
            # Contar nodos
            stats = {
                "Líneas": session.run("MATCH (l:Linea) RETURN count(l) as count").single()["count"],
                "Estaciones": session.run("MATCH (e:Estacion) RETURN count(e) as count").single()["count"],
                "Campus": session.run("MATCH (c:Campus) RETURN count(c) as count").single()["count"],
                "Estudios": session.run("MATCH (e:Estudio) RETURN count(e) as count").single()["count"],
            }

            for label, count in stats.items():
                print(f"  • {label}: {count}")

            # Contar relaciones
            print("\n  Relaciones:")
            rel_stats = {
                "TIENE_ESTACION": session.run("MATCH ()-[r:TIENE_ESTACION]->() RETURN count(r) as count").single()["count"],
                "SIGUIENTE": session.run("MATCH ()-[r:SIGUIENTE]->() RETURN count(r) as count").single()["count"],
                "TRANSBORDO": session.run("MATCH ()-[r:TRANSBORDO]->() RETURN count(r) as count").single()["count"],
                "CERCANA": session.run("MATCH ()-[r:CERCANA]->() RETURN count(r) as count").single()["count"],
                "OFRECE": session.run("MATCH ()-[r:OFRECE]->() RETURN count(r) as count").single()["count"],
            }

            for rel_type, count in rel_stats.items():
                print(f"    - :{rel_type}: {count}")


def main():
    """Función principal"""
    print("=" * 60)
    print("CARGA DE DATOS EN NEO4J")
    print("Metro de Madrid y Universidades - URJC 2025/2026")
    print("=" * 60)

    loader = Neo4jLoader(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

    try:
        # Limpiar base de datos
        loader.clear_database()

        # Cargar archivos JSON
        lineas_data = loader.load_json_file(LINEAS_FILE)
        estaciones_data = loader.load_json_file(ESTACIONES_FILE)
        campus_data = loader.load_json_file(CAMPUS_FILE)

        # Crear nodos
        loader.create_lineas(lineas_data)
        loader.create_estaciones(estaciones_data)
        loader.create_campus_y_estudios(campus_data)

        # Crear relaciones
        loader.create_relaciones_linea_estacion(estaciones_data)
        loader.create_relaciones_siguiente(estaciones_data)
        loader.create_relaciones_transbordo(estaciones_data)

        # Crear índices
        loader.create_indexes()

        # Mostrar estadísticas
        loader.show_statistics()

        print("\n" + "=" * 60)
        print("✅ CARGA COMPLETADA EXITOSAMENTE")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

    finally:
        loader.close()


if __name__ == "__main__":
    main()

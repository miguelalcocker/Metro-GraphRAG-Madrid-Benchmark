#!/usr/bin/env python3
"""
Script de carga de datos para MongoDB
Práctica de Bases de Datos No Relacionales - Metro de Madrid y Universidades
Universidad Rey Juan Carlos - Curso 2025/2026
"""

import json
import os
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import DuplicateKeyError
from bson import ObjectId
from typing import List, Dict

# Configuración de conexión
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
DATABASE_NAME = "metro_campus_db"

# Rutas a los archivos de datos
DATA_DIR = os.path.join(os.path.dirname(__file__), "../../data")
LINEAS_FILE = os.path.join(DATA_DIR, "lineas.json")
ESTACIONES_FILE = os.path.join(DATA_DIR, "estaciones.json")
CAMPUS_FILE = os.path.join(DATA_DIR, "campus.json")


class MongoDBLoader:
    """Clase para cargar datos en MongoDB"""

    def __init__(self, uri: str, db_name: str):
        """Inicializa la conexión a MongoDB"""
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        print(f"✓ Conectado a MongoDB: {db_name}")

    def load_json_file(self, file_path: str) -> List[Dict]:
        """Carga un archivo JSON y retorna su contenido"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"✓ Archivo cargado: {os.path.basename(file_path)} ({len(data)} registros)")
        return data

    def clear_collections(self):
        """Elimina todas las colecciones existentes"""
        collections = ["lineas", "estaciones", "campus"]
        for collection in collections:
            self.db[collection].drop()
            print(f"✓ Colección '{collection}' eliminada")

    def load_lineas(self, lineas_data: List[Dict]) -> Dict[int, ObjectId]:
        """Carga las líneas de metro en MongoDB"""
        print("\n📊 Cargando líneas de metro...")
        lineas_collection = self.db.lineas

        # Mapeo de número de línea a ObjectId
        linea_id_map = {}

        for linea in lineas_data:
            result = lineas_collection.insert_one(linea)
            linea_id_map[linea["numero"]] = result.inserted_id
            print(f"  • Línea {linea['numero']}: {linea['nombre']}")

        print(f"✓ {len(lineas_data)} líneas insertadas")
        return linea_id_map

    def load_estaciones(self, estaciones_data: List[Dict], linea_id_map: Dict[int, ObjectId]) -> Dict[str, ObjectId]:
        """Carga las estaciones de metro en MongoDB"""
        print("\n🚇 Cargando estaciones de metro...")
        estaciones_collection = self.db.estaciones

        # Mapeo de id de estación a ObjectId
        estacion_id_map = {}

        for estacion in estaciones_data:
            # Guardamos el id original para referencia
            original_id = estacion.pop("id")

            # Insertamos la estación
            result = estaciones_collection.insert_one(estacion)
            estacion_id_map[original_id] = result.inserted_id

            # Info de estaciones con Renfe
            renfe_info = " [RENFE]" if estacion.get("tiene_renfe") else ""
            print(f"  • {estacion['nombre']} (L{', L'.join(map(str, estacion['lineas']))}){renfe_info}")

        print(f"✓ {len(estaciones_data)} estaciones insertadas")

        # Actualizar referencias de líneas a estaciones
        print("\n🔗 Actualizando referencias línea-estación...")
        self._update_lineas_with_estaciones(linea_id_map, estacion_id_map, estaciones_data)

        return estacion_id_map

    def _update_lineas_with_estaciones(self, linea_id_map: Dict[int, ObjectId],
                                       estacion_id_map: Dict[str, ObjectId],
                                       estaciones_data: List[Dict]):
        """Actualiza las líneas con sus estaciones ordenadas"""
        lineas_collection = self.db.lineas

        # Agrupar estaciones por línea
        lineas_estaciones = {}
        for estacion_orig in estaciones_data:
            # Reconstruir el id original
            original_id = f"est_l{estacion_orig['lineas'][0]}_{str(estacion_orig['indice_por_linea'][str(estacion_orig['lineas'][0])]).zfill(3)}"

            for linea_num in estacion_orig["lineas"]:
                if linea_num not in lineas_estaciones:
                    lineas_estaciones[linea_num] = []

                orden = estacion_orig["indice_por_linea"].get(str(linea_num), 0)
                lineas_estaciones[linea_num].append({
                    "estacion_id": estacion_id_map.get(original_id),
                    "orden": orden
                })

        # Actualizar cada línea con sus estaciones ordenadas
        for linea_num, estaciones in lineas_estaciones.items():
            # Ordenar por índice
            estaciones_ordenadas = sorted(estaciones, key=lambda x: x["orden"])
            estaciones_ids = [est["estacion_id"] for est in estaciones_ordenadas]

            lineas_collection.update_one(
                {"_id": linea_id_map[linea_num]},
                {"$set": {"estaciones_ids": estaciones_ids}}
            )
            print(f"  • Línea {linea_num}: {len(estaciones_ids)} estaciones vinculadas")

    def load_campus(self, campus_data: List[Dict], estacion_id_map: Dict[str, ObjectId]):
        """Carga los campus universitarios con estudios embebidos"""
        print("\n🎓 Cargando campus universitarios...")
        campus_collection = self.db.campus

        for campus in campus_data:
            # Actualizar referencias a estaciones cercanas
            for estacion_cercana in campus["estaciones_cercanas"]:
                est_id_original = estacion_cercana["estacion_id"]
                if est_id_original in estacion_id_map:
                    estacion_cercana["estacion_id"] = estacion_id_map[est_id_original]

            # Insertar campus
            result = campus_collection.insert_one(campus)

            grados = [e for e in campus["estudios"] if e["tipo"] == "GRADO"]
            masters = [e for e in campus["estudios"] if e["tipo"] == "MASTER"]

            print(f"  • {campus['nombre']} ({campus['universidad']})")
            print(f"    - {len(grados)} Grados, {len(masters)} Másteres")
            print(f"    - Estaciones cercanas: {len(campus['estaciones_cercanas'])}")

        print(f"✓ {len(campus_data)} campus insertados")

    def create_indexes(self):
        """Crea índices para optimizar consultas"""
        print("\n🔍 Creando índices...")

        # Índices en estaciones
        self.db.estaciones.create_index([("nombre", ASCENDING)])
        self.db.estaciones.create_index([("tiene_renfe", ASCENDING)])
        self.db.estaciones.create_index([("zona_tarifaria", ASCENDING)])
        self.db.estaciones.create_index([("lineas", ASCENDING)])
        print("  ✓ Índices en 'estaciones': nombre, tiene_renfe, zona_tarifaria, lineas")

        # Índices en campus
        self.db.campus.create_index([("universidad", ASCENDING)])
        self.db.campus.create_index([("nombre", ASCENDING)])
        self.db.campus.create_index([("estudios.nombre", ASCENDING)])
        self.db.campus.create_index([("estudios.tipo", ASCENDING)])
        print("  ✓ Índices en 'campus': universidad, nombre, estudios.nombre, estudios.tipo")

        # Índices en líneas
        self.db.lineas.create_index([("numero", 1)], unique=True)
        print("  ✓ Índices en 'lineas': numero")

    def show_statistics(self):
        """Muestra estadísticas de la base de datos"""
        print("\n📈 Estadísticas de la base de datos:")
        print(f"  • Líneas: {self.db.lineas.count_documents({})}")
        print(f"  • Estaciones: {self.db.estaciones.count_documents({})}")
        print(f"  • Campus: {self.db.campus.count_documents({})}")

        # Estadísticas de estaciones con Renfe
        estaciones_renfe = self.db.estaciones.count_documents({"tiene_renfe": True})
        print(f"  • Estaciones con Renfe: {estaciones_renfe}")

        # Estadísticas de estudios
        pipeline = [
            {"$unwind": "$estudios"},
            {"$group": {
                "_id": "$estudios.tipo",
                "total": {"$sum": 1}
            }}
        ]
        estudios_stats = list(self.db.campus.aggregate(pipeline))
        for stat in estudios_stats:
            print(f"  • {stat['_id']}s: {stat['total']}")

    def close(self):
        """Cierra la conexión a MongoDB"""
        self.client.close()
        print("\n✓ Conexión cerrada")


def main():
    """Función principal"""
    print("=" * 60)
    print("CARGA DE DATOS EN MONGODB")
    print("Metro de Madrid y Universidades - URJC 2025/2026")
    print("=" * 60)

    # Crear instancia del loader
    loader = MongoDBLoader(MONGODB_URI, DATABASE_NAME)

    try:
        # Limpiar colecciones existentes
        print("\n🗑️  Limpiando base de datos...")
        loader.clear_collections()

        # Cargar archivos JSON
        lineas_data = loader.load_json_file(LINEAS_FILE)
        estaciones_data = loader.load_json_file(ESTACIONES_FILE)
        campus_data = loader.load_json_file(CAMPUS_FILE)

        # Cargar datos en MongoDB
        linea_id_map = loader.load_lineas(lineas_data)
        estacion_id_map = loader.load_estaciones(estaciones_data, linea_id_map)
        loader.load_campus(campus_data, estacion_id_map)

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

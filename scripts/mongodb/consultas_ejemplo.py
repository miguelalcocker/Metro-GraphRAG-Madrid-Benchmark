#!/usr/bin/env python3
"""
Script con consultas de ejemplo para MongoDB
Práctica de Bases de Datos No Relacionales - Metro de Madrid y Universidades
Universidad Rey Juan Carlos - Curso 2025/2026
"""

import os
from pymongo import MongoClient
from pprint import pprint

# Configuración
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
DATABASE_NAME = "metro_campus_db"


class MongoDBQueries:
    """Clase con consultas de ejemplo para MongoDB"""

    def __init__(self, uri: str, db_name: str):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        print(f"✓ Conectado a MongoDB: {db_name}\n")

    def query_1_estaciones_por_linea(self, numero_linea: int):
        """Listar estaciones de una línea en orden de paso"""
        print(f"📍 CONSULTA 1: Estaciones de la Línea {numero_linea}")
        print("-" * 60)

        # Obtener la línea
        linea = self.db.lineas.find_one({"numero": numero_linea})
        if not linea:
            print(f"Línea {numero_linea} no encontrada")
            return

        print(f"Línea: {linea['nombre']}")
        print(f"Total estaciones: {len(linea.get('estaciones_ids', []))}\n")

        # Obtener estaciones en orden
        for i, estacion_id in enumerate(linea.get('estaciones_ids', []), 1):
            estacion = self.db.estaciones.find_one({"_id": estacion_id})
            if estacion:
                print(f"{i:2d}. {estacion['nombre']} (Zona {estacion['zona_tarifaria']})")

        print()

    def query_2_estaciones_con_renfe(self):
        """Obtener estaciones con correspondencia Renfe"""
        print("🚆 CONSULTA 2: Estaciones con correspondencia Renfe")
        print("-" * 60)

        estaciones = self.db.estaciones.find({"tiene_renfe": True})
        count = 0

        for est in estaciones:
            count += 1
            renfe_info = est.get('estacion_renfe', {})
            lineas_renfe = ', '.join(renfe_info.get('lineas_renfe', []))
            lineas_metro = ', '.join([f"L{l}" for l in est.get('lineas', [])])

            print(f"{count}. {est['nombre']}")
            print(f"   Metro: {lineas_metro}")
            print(f"   Renfe: {renfe_info.get('nombre', 'N/A')} ({lineas_renfe})")
            print()

    def query_3_estaciones_por_zona(self, zona: str):
        """Obtener estaciones accesibles por zona tarifaria"""
        print(f"💰 CONSULTA 3: Estaciones en zona tarifaria {zona}")
        print("-" * 60)

        estaciones = self.db.estaciones.find({"zona_tarifaria": zona})
        estaciones_list = list(estaciones)

        print(f"Total estaciones en zona {zona}: {len(estaciones_list)}\n")

        for est in estaciones_list[:10]:  # Mostrar solo las primeras 10
            lineas = ', '.join([f"L{l}" for l in est.get('lineas', [])])
            print(f"• {est['nombre']} ({lineas})")

        if len(estaciones_list) > 10:
            print(f"... y {len(estaciones_list) - 10} estaciones más")

        print()

    def query_4_campus_por_universidad(self, universidad: str):
        """Listar campus por universidad"""
        print(f"🎓 CONSULTA 4: Campus de {universidad}")
        print("-" * 60)

        campus_list = self.db.campus.find({"universidad": universidad})

        for campus in campus_list:
            print(f"\n{campus['nombre']}")
            print(f"Dirección: {campus['direccion']}")
            print(f"Estaciones cercanas:")
            for est in campus.get('estaciones_cercanas', []):
                print(f"  • {est['nombre_estacion']} ({est['rol']}) - {est['minutos_andando']} min andando")

        print()

    def query_5_campus_por_estacion(self, nombre_estacion: str):
        """Listar campus asociados a una estación principal"""
        print(f"📍 CONSULTA 5: Campus cercanos a estación '{nombre_estacion}'")
        print("-" * 60)

        campus_list = self.db.campus.find({
            "estaciones_cercanas.nombre_estacion": nombre_estacion
        })

        count = 0
        for campus in campus_list:
            count += 1
            # Encontrar la información de la estación en este campus
            est_info = None
            for est in campus.get('estaciones_cercanas', []):
                if est['nombre_estacion'] == nombre_estacion:
                    est_info = est
                    break

            print(f"\n{count}. {campus['nombre']} ({campus['universidad']})")
            if est_info:
                print(f"   Rol: {est_info['rol']}")
                print(f"   Tiempo andando: {est_info['minutos_andando']} minutos")

        if count == 0:
            print("No se encontraron campus cercanos a esta estación")

        print()

    def query_6_estudios_grado(self, nombre_grado: str = None):
        """Listar estudios de GRADO por nombre"""
        print(f"📚 CONSULTA 6: Estudios de GRADO" + (f" - '{nombre_grado}'" if nombre_grado else ""))
        print("-" * 60)

        query = {"estudios.tipo": "GRADO"}
        if nombre_grado:
            query["estudios.nombre"] = {"$regex": nombre_grado, "$options": "i"}

        campus_list = self.db.campus.find(query)

        for campus in campus_list:
            grados = [e for e in campus.get('estudios', [])
                      if e['tipo'] == 'GRADO' and
                      (not nombre_grado or nombre_grado.lower() in e['nombre'].lower())]

            if grados:
                print(f"\n{campus['nombre']} ({campus['universidad']})")
                for grado in grados:
                    print(f"  • {grado['nombre']}")
                    print(f"    Plazas: {grado.get('plazas', 'N/A')} | Nota corte: {grado.get('nota_corte', 'N/A')}")

        print()

    def aggregation_1_estaciones_por_linea(self):
        """Calcular el número de estaciones por línea"""
        print("📊 AGREGACIÓN 1: Número de estaciones por línea")
        print("-" * 60)

        pipeline = [
            {
                "$project": {
                    "numero": 1,
                    "nombre": 1,
                    "num_estaciones": {"$size": {"$ifNull": ["$estaciones_ids", []]}}
                }
            },
            {"$sort": {"numero": 1}}
        ]

        results = self.db.lineas.aggregate(pipeline)

        print(f"{'Línea':<10} {'Estaciones':>12}")
        print("-" * 25)

        for result in results:
            print(f"L{result['numero']:<9} {result['num_estaciones']:>12}")

        print()

    def aggregation_2_estaciones_universitarias(self):
        """Calcular cuántas estaciones universitarias existen por zona tarifaria"""
        print("🎓 AGREGACIÓN 2: Estaciones universitarias por zona tarifaria")
        print("-" * 60)

        # Primero obtener todas las estaciones que son cercanas a algún campus
        estaciones_universitarias = set()
        for campus in self.db.campus.find():
            for est in campus.get('estaciones_cercanas', []):
                est_id = est.get('estacion_id')
                if est_id:
                    estaciones_universitarias.add(est_id)

        # Contar por zona tarifaria
        zona_count = {}
        for est_id in estaciones_universitarias:
            estacion = self.db.estaciones.find_one({"_id": est_id})
            if estacion:
                zona = estacion.get('zona_tarifaria', 'Desconocida')
                zona_count[zona] = zona_count.get(zona, 0) + 1

        print(f"{'Zona':>10} {'Estaciones universitarias':>25}")
        print("-" * 40)

        for zona in sorted(zona_count.keys()):
            print(f"{zona:>10} {zona_count[zona]:>25}")

        print()

    def aggregation_3_estudios_por_universidad(self):
        """Calcular cuántos estudios de GRADO y MÁSTER ofrece cada universidad"""
        print("📈 AGREGACIÓN 3: Estudios por universidad (GRADO vs MÁSTER)")
        print("-" * 60)

        pipeline = [
            {"$unwind": "$estudios"},
            {
                "$group": {
                    "_id": {
                        "universidad": "$universidad",
                        "tipo": "$estudios.tipo"
                    },
                    "total": {"$sum": 1}
                }
            },
            {"$sort": {"_id.universidad": 1, "_id.tipo": 1}}
        ]

        results = list(self.db.campus.aggregate(pipeline))

        # Agrupar por universidad
        universidades = {}
        for result in results:
            univ = result['_id']['universidad']
            tipo = result['_id']['tipo']
            total = result['total']

            if univ not in universidades:
                universidades[univ] = {"GRADO": 0, "MASTER": 0}

            universidades[univ][tipo] = total

        print(f"{'Universidad':<10} {'GRADOs':>10} {'MÁSTERs':>10} {'Total':>10}")
        print("-" * 45)

        for univ in sorted(universidades.keys()):
            grados = universidades[univ]["GRADO"]
            masters = universidades[univ]["MASTER"]
            total = grados + masters
            print(f"{univ:<10} {grados:>10} {masters:>10} {total:>10}")

        print()

    def close(self):
        """Cierra la conexión"""
        self.client.close()


def main():
    """Función principal"""
    print("=" * 60)
    print("CONSULTAS DE EJEMPLO - MONGODB")
    print("Metro de Madrid y Universidades - URJC 2025/2026")
    print("=" * 60 + "\n")

    queries = MongoDBQueries(MONGODB_URI, DATABASE_NAME)

    try:
        # CONSULTAS DE LECTURA
        queries.query_1_estaciones_por_linea(1)
        queries.query_2_estaciones_con_renfe()
        queries.query_3_estaciones_por_zona("A")
        queries.query_4_campus_por_universidad("UCM")
        queries.query_5_campus_por_estacion("Moncloa")
        queries.query_6_estudios_grado("Inteligencia Artificial")

        # AGREGACIONES
        queries.aggregation_1_estaciones_por_linea()
        queries.aggregation_2_estaciones_universitarias()
        queries.aggregation_3_estudios_por_universidad()

        print("=" * 60)
        print("✅ CONSULTAS COMPLETADAS")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

    finally:
        queries.close()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Operaciones CRUD - CREATE (Creación)
Práctica de Bases de Datos No Relacionales - Metro de Madrid y Universidades
Universidad Rey Juan Carlos - Curso 2025/2026

Este script demuestra las operaciones de creación (Create) en MongoDB:
- Insertar nuevas líneas de metro
- Registrar estaciones (con y sin correspondencia Renfe)
- Dar de alta campus universitarios con estudios embebidos
"""

import os
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from bson import ObjectId
from datetime import datetime
from typing import Dict, List, Optional


# Configuración de conexión
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
DATABASE_NAME = "metro_campus_db"


class CRUDCreateOperations:
    """Clase para operaciones de creación en MongoDB"""

    def __init__(self, uri: str, db_name: str):
        """Inicializa la conexión a MongoDB"""
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        print(f"✓ Conectado a MongoDB: {db_name}")

    def insertar_linea(self, numero: int, nombre: str, color: str, 
                       longitud_km: Optional[float] = None) -> ObjectId:
        """
        Inserta una nueva línea de metro
        
        Args:
            numero: Número de la línea (ej: 1, 2, 3...)
            nombre: Nombre descriptivo de la línea
            color: Color identificativo de la línea (hex o nombre)
            longitud_km: Longitud total de la línea en kilómetros (opcional)
        
        Returns:
            ObjectId del documento insertado
        """
        lineas_collection = self.db.lineas
        
        # Verificar si ya existe
        if lineas_collection.find_one({"numero": numero}):
            print(f"⚠️  La línea {numero} ya existe en la base de datos")
            return None
        
        # Crear documento de línea
        linea_doc = {
            "numero": numero,
            "nombre": nombre,
            "color": color,
            "estaciones_ids": [],  # Se poblará cuando se añadan estaciones
            "fecha_creacion": datetime.now()
        }
        
        if longitud_km:
            linea_doc["longitud_km"] = longitud_km
        
        # Insertar
        result = lineas_collection.insert_one(linea_doc)
        print(f"✅ Línea {numero} insertada: {nombre} (Color: {color})")
        print(f"   ID: {result.inserted_id}")
        
        return result.inserted_id

    def registrar_estacion(self, nombre: str, lineas: List[int], 
                          zona_tarifaria: str,
                          indice_por_linea: Dict[str, int],
                          tiene_renfe: bool = False,
                          estacion_renfe: Optional[Dict] = None,
                          coordenadas: Optional[Dict[str, float]] = None) -> ObjectId:
        """
        Registra una nueva estación de metro
        
        Args:
            nombre: Nombre de la estación
            lineas: Lista de números de línea que pasan por esta estación
            zona_tarifaria: Zona tarifaria (A, B1, B2, B3)
            indice_por_linea: Diccionario con el índice de la estación en cada línea
            tiene_renfe: Si tiene correspondencia con Renfe
            estacion_renfe: Información de la estación Renfe (si aplica)
            coordenadas: Coordenadas geográficas (lat, lon)
        
        Returns:
            ObjectId del documento insertado
        """
        estaciones_collection = self.db.estaciones
        
        # Verificar si ya existe
        if estaciones_collection.find_one({"nombre": nombre}):
            print(f"⚠️  La estación '{nombre}' ya existe en la base de datos")
            return None
        
        # Crear documento de estación
        estacion_doc = {
            "nombre": nombre,
            "lineas": lineas,
            "zona_tarifaria": zona_tarifaria,
            "indice_por_linea": indice_por_linea,
            "tiene_renfe": tiene_renfe,
            "fecha_registro": datetime.now()
        }
        
        # Añadir información de Renfe si aplica
        if tiene_renfe and estacion_renfe:
            estacion_doc["estacion_renfe"] = estacion_renfe
        
        # Añadir coordenadas si se proporcionan
        if coordenadas:
            estacion_doc["coordenadas"] = coordenadas
        
        # Insertar
        result = estaciones_collection.insert_one(estacion_doc)
        
        renfe_info = " [CON RENFE]" if tiene_renfe else ""
        print(f"✅ Estación registrada: {nombre}{renfe_info}")
        print(f"   Líneas: {', '.join([f'L{l}' for l in lineas])}")
        print(f"   Zona: {zona_tarifaria}")
        print(f"   ID: {result.inserted_id}")
        
        # Actualizar las líneas correspondientes
        self._actualizar_lineas_con_estacion(lineas, result.inserted_id, indice_por_linea)
        
        return result.inserted_id

    def _actualizar_lineas_con_estacion(self, lineas: List[int], 
                                        estacion_id: ObjectId,
                                        indice_por_linea: Dict[str, int]):
        """Actualiza las líneas añadiendo la nueva estación en su posición correcta"""
        lineas_collection = self.db.lineas
        
        for linea_num in lineas:
            linea = lineas_collection.find_one({"numero": linea_num})
            if linea:
                estaciones_ids = linea.get("estaciones_ids", [])
                indice = indice_por_linea.get(str(linea_num), len(estaciones_ids))
                
                # Insertar en la posición correcta
                if indice <= len(estaciones_ids):
                    estaciones_ids.insert(indice, estacion_id)
                else:
                    estaciones_ids.append(estacion_id)
                
                lineas_collection.update_one(
                    {"_id": linea["_id"]},
                    {"$set": {"estaciones_ids": estaciones_ids}}
                )
                print(f"   → Línea {linea_num} actualizada con la nueva estación")

    def dar_alta_campus(self, nombre: str, universidad: str,
                        direccion: str, ciudad: str,
                        estudios: List[Dict],
                        estaciones_cercanas: List[Dict],
                        coordenadas: Optional[Dict[str, float]] = None,
                        web: Optional[str] = None) -> ObjectId:
        """
        Da de alta un nuevo campus universitario con sus estudios embebidos
        
        Args:
            nombre: Nombre del campus
            universidad: Universidad a la que pertenece
            direccion: Dirección física
            ciudad: Ciudad donde se ubica
            estudios: Lista de estudios ofrecidos (Grados y Másteres)
                     Cada estudio debe tener: nombre, tipo (GRADO/MASTER), duracion_años, plazas
            estaciones_cercanas: Lista de estaciones cercanas con distancia
                                Cada una debe tener: estacion_id, distancia_metros, tiempo_andando_min
            coordenadas: Coordenadas geográficas (lat, lon)
            web: URL del sitio web del campus
        
        Returns:
            ObjectId del documento insertado
        """
        campus_collection = self.db.campus
        
        # Verificar si ya existe
        if campus_collection.find_one({"nombre": nombre, "universidad": universidad}):
            print(f"⚠️  El campus '{nombre}' de {universidad} ya existe")
            return None
        
        # Crear documento de campus
        campus_doc = {
            "nombre": nombre,
            "universidad": universidad,
            "direccion": direccion,
            "ciudad": ciudad,
            "estudios": estudios,
            "estaciones_cercanas": estaciones_cercanas,
            "fecha_alta": datetime.now()
        }
        
        if coordenadas:
            campus_doc["coordenadas"] = coordenadas
        
        if web:
            campus_doc["web"] = web
        
        # Insertar
        result = campus_collection.insert_one(campus_doc)
        
        # Estadísticas de estudios
        grados = [e for e in estudios if e["tipo"] == "GRADO"]
        masters = [e for e in estudios if e["tipo"] == "MASTER"]
        
        print(f"✅ Campus dado de alta: {nombre}")
        print(f"   Universidad: {universidad}")
        print(f"   Estudios: {len(grados)} Grados, {len(masters)} Másteres")
        print(f"   Estaciones cercanas: {len(estaciones_cercanas)}")
        print(f"   ID: {result.inserted_id}")
        
        return result.inserted_id

    def insertar_multiples_lineas(self, lineas: List[Dict]) -> List[ObjectId]:
        """
        Inserta múltiples líneas de metro en una sola operación
        
        Args:
            lineas: Lista de diccionarios con información de líneas
        
        Returns:
            Lista de ObjectIds insertados
        """
        lineas_collection = self.db.lineas
        
        # Añadir fecha de creación a todas
        for linea in lineas:
            linea["fecha_creacion"] = datetime.now()
            if "estaciones_ids" not in linea:
                linea["estaciones_ids"] = []
        
        try:
            result = lineas_collection.insert_many(lineas, ordered=False)
            print(f"✅ {len(result.inserted_ids)} líneas insertadas en lote")
            return result.inserted_ids
        except Exception as e:
            print(f"⚠️  Error al insertar líneas: {e}")
            return []

    def close(self):
        """Cierra la conexión a MongoDB"""
        self.client.close()
        print("\n✓ Conexión cerrada")


def ejemplos_creacion():
    """Ejemplos de operaciones de creación"""
    
    print("=" * 70)
    print("OPERACIONES CRUD - CREATE (CREACIÓN)")
    print("Metro de Madrid y Universidades - URJC 2025/2026")
    print("=" * 70)
    
    crud = CRUDCreateOperations(MONGODB_URI, DATABASE_NAME)
    
    try:
        # ================================================================
        # 1. INSERTAR NUEVAS LÍNEAS
        # ================================================================
        print("\n" + "=" * 70)
        print("1️⃣  INSERTAR NUEVAS LÍNEAS DE METRO")
        print("=" * 70)
        
        # Línea 1 - Celeste
        linea1_id = crud.insertar_linea(
            numero=1,
            nombre="Pinar de Chamartín - Valdecarros",
            color="#38A3DC",
            longitud_km=24.5
        )
        
        # Línea 2 - Roja
        linea2_id = crud.insertar_linea(
            numero=2,
            nombre="Cuatro Caminos - Las Rosas",
            color="#E8292C",
            longitud_km=14.5
        )
        
        # Línea 6 - Circular
        linea6_id = crud.insertar_linea(
            numero=6,
            nombre="Circular",
            color="#9FA4A6",
            longitud_km=23.5
        )
        
        # ================================================================
        # 2. REGISTRAR ESTACIONES
        # ================================================================
        print("\n" + "=" * 70)
        print("2️⃣  REGISTRAR ESTACIONES DE METRO")
        print("=" * 70)
        
        # Estación con Renfe: Chamartín
        chamartin_id = crud.registrar_estacion(
            nombre="Chamartín",
            lineas=[1, 10],
            zona_tarifaria="A",
            indice_por_linea={"1": 0, "10": 15},
            tiene_renfe=True,
            estacion_renfe={
                "nombre": "Madrid-Chamartín-Clara Campoamor",
                "tipo": "ESTACION_PRINCIPAL",
                "servicios": ["AVE", "Larga Distancia", "Media Distancia", "Cercanías"],
                "lineas_cercanias": ["C1", "C2", "C3", "C4", "C7", "C8", "C10"]
            },
            coordenadas={
                "latitud": 40.4729,
                "longitud": -3.6807
            }
        )
        
        # Estación con Renfe: Atocha
        atocha_id = crud.registrar_estacion(
            nombre="Atocha Renfe",
            lineas=[1],
            zona_tarifaria="A",
            indice_por_linea={"1": 18},
            tiene_renfe=True,
            estacion_renfe={
                "nombre": "Madrid-Puerta de Atocha",
                "tipo": "ESTACION_PRINCIPAL",
                "servicios": ["AVE", "Larga Distancia", "Media Distancia", "Cercanías"],
                "lineas_cercanias": ["C1", "C2", "C3", "C4", "C5", "C7", "C8", "C10"]
            },
            coordenadas={
                "latitud": 40.4067,
                "longitud": -3.6908
            }
        )
        
        # Estación sin Renfe: Plaza de Castilla
        plaza_castilla_id = crud.registrar_estacion(
            nombre="Plaza de Castilla",
            lineas=[1, 9, 10],
            zona_tarifaria="A",
            indice_por_linea={"1": 3, "9": 0, "10": 12},
            tiene_renfe=False,
            coordenadas={
                "latitud": 40.4658,
                "longitud": -3.6889
            }
        )
        
        # Estación sin Renfe: Nuevos Ministerios
        nuevos_ministerios_id = crud.registrar_estacion(
            nombre="Nuevos Ministerios",
            lineas=[6, 8, 10],
            zona_tarifaria="A",
            indice_por_linea={"6": 15, "8": 5, "10": 9},
            tiene_renfe=False,
            coordenadas={
                "latitud": 40.4463,
                "longitud": -3.6926
            }
        )
        
        # Estación sin Renfe: Ciudad Universitaria
        ciudad_universitaria_id = crud.registrar_estacion(
            nombre="Ciudad Universitaria",
            lineas=[6],
            zona_tarifaria="A",
            indice_por_linea={"6": 20},
            tiene_renfe=False,
            coordenadas={
                "latitud": 40.4496,
                "longitud": -3.7296
            }
        )
        
        # ================================================================
        # 3. DAR DE ALTA CAMPUS UNIVERSITARIOS
        # ================================================================
        print("\n" + "=" * 70)
        print("3️⃣  DAR DE ALTA CAMPUS UNIVERSITARIOS")
        print("=" * 70)
        
        # Campus Ciudad Universitaria (UCM)
        campus_ucm_id = crud.dar_alta_campus(
            nombre="Ciudad Universitaria",
            universidad="Universidad Complutense de Madrid",
            direccion="Av. Séneca, 2",
            ciudad="Madrid",
            estudios=[
                # Grados
                {
                    "nombre": "Grado en Medicina",
                    "tipo": "GRADO",
                    "duracion_años": 6,
                    "plazas": 280,
                    "nota_corte": 13.0,
                    "facultad": "Facultad de Medicina"
                },
                {
                    "nombre": "Grado en Derecho",
                    "tipo": "GRADO",
                    "duracion_años": 4,
                    "plazas": 450,
                    "nota_corte": 11.5,
                    "facultad": "Facultad de Derecho"
                },
                {
                    "nombre": "Grado en Informática",
                    "tipo": "GRADO",
                    "duracion_años": 4,
                    "plazas": 240,
                    "nota_corte": 12.0,
                    "facultad": "Facultad de Informática"
                },
                {
                    "nombre": "Grado en Física",
                    "tipo": "GRADO",
                    "duracion_años": 4,
                    "plazas": 180,
                    "nota_corte": 11.8,
                    "facultad": "Facultad de Ciencias Físicas"
                },
                # Másteres
                {
                    "nombre": "Máster en Inteligencia Artificial",
                    "tipo": "MASTER",
                    "duracion_años": 1,
                    "plazas": 60,
                    "facultad": "Facultad de Informática"
                },
                {
                    "nombre": "Máster en Abogacía",
                    "tipo": "MASTER",
                    "duracion_años": 1,
                    "plazas": 200,
                    "facultad": "Facultad de Derecho"
                },
                {
                    "nombre": "Máster en Investigación Biomédica",
                    "tipo": "MASTER",
                    "duracion_años": 1,
                    "plazas": 40,
                    "facultad": "Facultad de Medicina"
                }
            ],
            estaciones_cercanas=[
                {
                    "estacion_id": ciudad_universitaria_id,
                    "distancia_metros": 300,
                    "tiempo_andando_min": 4
                },
                {
                    "estacion_id": nuevos_ministerios_id,
                    "distancia_metros": 2500,
                    "tiempo_andando_min": 30
                }
            ],
            coordenadas={
                "latitud": 40.4496,
                "longitud": -3.7296
            },
            web="https://www.ucm.es"
        )
        
        # Campus Moncloa (UPM)
        campus_upm_id = crud.dar_alta_campus(
            nombre="Campus de Moncloa",
            universidad="Universidad Politécnica de Madrid",
            direccion="Av. Ramiro de Maeztu, 7",
            ciudad="Madrid",
            estudios=[
                # Grados
                {
                    "nombre": "Grado en Ingeniería Informática",
                    "tipo": "GRADO",
                    "duracion_años": 4,
                    "plazas": 300,
                    "nota_corte": 12.5,
                    "escuela": "ETSIINF"
                },
                {
                    "nombre": "Grado en Ingeniería Aeroespacial",
                    "tipo": "GRADO",
                    "duracion_años": 4,
                    "plazas": 180,
                    "nota_corte": 13.2,
                    "escuela": "ETSIAE"
                },
                {
                    "nombre": "Grado en Arquitectura",
                    "tipo": "GRADO",
                    "duracion_años": 6,
                    "plazas": 250,
                    "nota_corte": 12.8,
                    "escuela": "ETSAM"
                },
                # Másteres
                {
                    "nombre": "Máster en Ciberseguridad",
                    "tipo": "MASTER",
                    "duracion_años": 1,
                    "plazas": 50,
                    "escuela": "ETSIINF"
                },
                {
                    "nombre": "Máster en Ingeniería Aeronáutica",
                    "tipo": "MASTER",
                    "duracion_años": 2,
                    "plazas": 80,
                    "escuela": "ETSIAE"
                }
            ],
            estaciones_cercanas=[
                {
                    "estacion_id": ciudad_universitaria_id,
                    "distancia_metros": 800,
                    "tiempo_andando_min": 10
                }
            ],
            coordenadas={
                "latitud": 40.4530,
                "longitud": -3.7280
            },
            web="https://www.upm.es"
        )
        
        # ================================================================
        # 4. INSERCIÓN MÚLTIPLE DE LÍNEAS
        # ================================================================
        print("\n" + "=" * 70)
        print("4️⃣  INSERCIÓN MÚLTIPLE DE LÍNEAS (BATCH)")
        print("=" * 70)
        
        lineas_adicionales = [
            {
                "numero": 3,
                "nombre": "Villaverde Alto - Moncloa",
                "color": "#FFD100",
                "longitud_km": 16.4,
                "estaciones_ids": []
            },
            {
                "numero": 4,
                "nombre": "Argüelles - Pinar de Chamartín",
                "color": "#A0522D",
                "longitud_km": 16.0,
                "estaciones_ids": []
            },
            {
                "numero": 5,
                "nombre": "Alameda de Osuna - Casa de Campo",
                "color": "#92D050",
                "longitud_km": 23.2,
                "estaciones_ids": []
            }
        ]
        
        crud.insertar_multiples_lineas(lineas_adicionales)
        
        # ================================================================
        # RESUMEN FINAL
        # ================================================================
        print("\n" + "=" * 70)
        print("📊 RESUMEN DE OPERACIONES")
        print("=" * 70)
        
        total_lineas = crud.db.lineas.count_documents({})
        total_estaciones = crud.db.estaciones.count_documents({})
        total_campus = crud.db.campus.count_documents({})
        estaciones_renfe = crud.db.estaciones.count_documents({"tiene_renfe": True})
        
        print(f"✅ Total líneas en BD: {total_lineas}")
        print(f"✅ Total estaciones en BD: {total_estaciones}")
        print(f"   → Con Renfe: {estaciones_renfe}")
        print(f"   → Sin Renfe: {total_estaciones - estaciones_renfe}")
        print(f"✅ Total campus en BD: {total_campus}")
        
        print("\n" + "=" * 70)
        print("✅ OPERACIONES DE CREACIÓN COMPLETADAS")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        crud.close()


if __name__ == "__main__":
    ejemplos_creacion()
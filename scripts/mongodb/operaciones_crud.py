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

        # Creamos índices

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
        nombre_string = f"Línea {numero} - {nombre}"
        linea_doc = {
            "numero": numero,
            "nombre": nombre_string,
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
            nombre="Ciudad Universitaria Nueva",
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
            nombre="Campus de Moncloa Nueva",
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
                "nombre": "Línea 3 - Villaverde Alto - Moncloa",
                "color": "#FFD100",
                "longitud_km": 16.4,
                "estaciones_ids": []
            },
            {
                "numero": 4,
                "nombre": "Línea 4 - Argüelles - Pinar de Chamartín",
                "color": "#A0522D",
                "longitud_km": 16.0,
                "estaciones_ids": []
            },
            {
                "numero": 5,
                "nombre": "Línea 5 - Alameda de Osuna - Casa de Campo",
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


class CRUDReadOperations:
    """Clase para operaciones de lectura en MongoDB"""

    def __init__(self, uri: str, db_name: str):
        """Inicializa la conexión a MongoDB"""
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        print(f"✓ Conectado a MongoDB: {db_name}")

    def buscar_estaciones_por_zona(self, zona_tarifaria: str) -> List[Dict]:
        """
        Localiza todas las estaciones que pertenecen a una zona tarifaria específica
        
        Args:
            zona_tarifaria: Zona tarifaria a buscar (ej: "Zona A", "Zona B1", etc.)
        
        Returns:
            Lista de estaciones que pertenecen a la zona especificada
        """
        estaciones_collection = self.db.estaciones
        
        # Buscar estaciones por zona tarifaria
        estaciones = list(estaciones_collection.find(
            {"zona_tarifaria": zona_tarifaria}
        ))
        
        print(f"\n🔍 Estaciones en {zona_tarifaria}:")
        print(f"   Total encontradas: {len(estaciones)}")
        
        for estacion in estaciones:
            lineas_str = ", ".join([f"L{l}" for l in estacion.get("lineas", [])])
            renfe_mark = " 🚆" if estacion.get("tiene_renfe", False) else ""
            print(f"   • {estacion['nombre']} ({lineas_str}){renfe_mark}")
        
        return estaciones

    def consultar_correspondencias_renfe(self) -> List[Dict]:
        """
        Lista únicamente las estaciones que tienen correspondencia con Renfe
        
        Returns:
            Lista de estaciones con tiene_renfe: true
        """
        estaciones_collection = self.db.estaciones
        
        # Buscar estaciones con Renfe
        estaciones_renfe = list(estaciones_collection.find(
            {"tiene_renfe": True}
        ))
        
        print(f"\n🚆 Estaciones con correspondencia Renfe:")
        print(f"   Total encontradas: {len(estaciones_renfe)}")
        
        for estacion in estaciones_renfe:
            lineas_str = ", ".join([f"L{l}" for l in estacion.get("lineas", [])])
            estacion_renfe_info = estacion.get("estacion_renfe", {})
            nombre_renfe = estacion_renfe_info.get("nombre", "N/A")
            servicios = estacion.get("servicios", [])
            servicios_str = ", ".join(servicios) if servicios else "N/A"
            
            print(f"   • {estacion['nombre']} ({lineas_str})")
            print(f"     └─ Renfe: {nombre_renfe}")
            print(f"     └─ Servicios: {servicios_str}")
        
        return estaciones_renfe

    def buscar_campus_por_universidad(self, universidad: str) -> List[Dict]:
        """
        Busca campus que pertenecen a una universidad concreta
        
        Args:
            universidad: Nombre de la universidad (ej: "UCM", "UPM", etc.)
        
        Returns:
            Lista de campus de la universidad especificada
        """
        campus_collection = self.db.campus
        
        # Buscar campus por universidad
        campus = list(campus_collection.find(
            {"universidad": {"$regex": universidad, "$options": "i"}}
        ))
        
        print(f"\n🎓 Campus de {universidad}:")
        print(f"   Total encontrados: {len(campus)}")
        
        for c in campus:
            estudios = c.get("estudios", [])
            grados = [e for e in estudios if e["tipo"] == "GRADO"]
            masters = [e for e in estudios if e["tipo"] == "MASTER"]
            
            print(f"   • {c['nombre']}")
            print(f"     └─ Universidad: {c['universidad']}")
            print(f"     └─ Dirección: {c.get('direccion', 'N/A')}")
            print(f"     └─ Estudios: {len(grados)} Grados, {len(masters)} Másteres")
        
        return campus

    def buscar_campus_por_grado(self, nombre_grado: str) -> List[Dict]:
        """
        Busca campus que imparten un Grado específico
        
        Args:
            nombre_grado: Nombre del grado a buscar (búsqueda parcial)
        
        Returns:
            Lista de campus que ofrecen el grado especificado
        """
        campus_collection = self.db.campus
        
        # Buscar campus que tengan el grado en su array de estudios
        campus = list(campus_collection.find(
            {
                "estudios": {
                    "$elemMatch": {
                        "tipo": "GRADO",
                        "nombre": {"$regex": nombre_grado, "$options": "i"}
                    }
                }
            }
        ))
        
        print(f"\n🎓 Campus que imparten grados relacionados con '{nombre_grado}':")
        print(f"   Total encontrados: {len(campus)}")
        
        for c in campus:
            # Filtrar solo los grados que coinciden
            grados_coincidentes = [
                e for e in c.get("estudios", [])
                if e["tipo"] == "GRADO" and nombre_grado.lower() in e["nombre"].lower()
            ]
            
            print(f"   • {c['nombre']} ({c['universidad']})")
            for grado in grados_coincidentes:
                plazas = grado.get("plazas", "N/A")
                nota_corte = grado.get("nota_corte", "N/A")
                print(f"     └─ {grado['nombre']}")
                print(f"        • Plazas: {plazas}, Nota corte: {nota_corte}")
        
        return campus

    def listar_estaciones_por_linea_ordenadas(self, numero_linea: int) -> List[Dict]:
        """
        Lista las estaciones de una línea ordenadas por su indice_por_linea
        
        Args:
            numero_linea: Número de la línea (ej: 1, 2, 3, etc.)
        
        Returns:
            Lista de estaciones ordenadas por su índice en la línea
        """
        estaciones_collection = self.db.estaciones
        lineas_collection = self.db.lineas
        
        # Verificar que la línea existe
        linea = lineas_collection.find_one({"numero": numero_linea})
        if not linea:
            print(f"⚠️  La línea {numero_linea} no existe en la base de datos")
            return []
        
        # Buscar estaciones de la línea
        estaciones = list(estaciones_collection.find(
            {"lineas": numero_linea}
        ))
        
        # Ordenar por indice_por_linea
        estaciones_ordenadas = sorted(
            estaciones,
            key=lambda e: e.get("indice_por_linea", {}).get(str(numero_linea), 999)
        )
        
        print(f"\n🚇 Estaciones de la Línea {numero_linea} ({linea.get('nombre', 'N/A')}):")
        print(f"   Color: {linea.get('color', 'N/A')}")
        print(f"   Total estaciones: {len(estaciones_ordenadas)}")
        print(f"\n   Recorrido ordenado:")
        
        for i, estacion in enumerate(estaciones_ordenadas, 1):
            indice = estacion.get("indice_por_linea", {}).get(str(numero_linea), "?")
            zona = estacion.get("zona_tarifaria", "?")
            renfe_mark = " 🚆" if estacion.get("tiene_renfe", False) else ""
            
            # Mostrar otras líneas que pasan por esta estación
            otras_lineas = [l for l in estacion.get("lineas", []) if l != numero_linea]
            correspondencias = ""
            if otras_lineas:
                correspondencias = f" (↔ L{', L'.join(map(str, otras_lineas))})"
            
            print(f"   {i:2d}. [{indice:2d}] {estacion['nombre']}{renfe_mark} - Zona {zona}{correspondencias}")
        
        return estaciones_ordenadas

    def estadisticas_generales(self) -> Dict:
        """
        Genera estadísticas generales del sistema
        
        Returns:
            Diccionario con estadísticas del sistema
        """
        lineas_collection = self.db.lineas
        estaciones_collection = self.db.estaciones
        campus_collection = self.db.campus
        
        # Contar documentos
        total_lineas = lineas_collection.count_documents({})
        total_estaciones = estaciones_collection.count_documents({})
        total_campus = campus_collection.count_documents({})
        
        # Estaciones con Renfe
        estaciones_renfe = estaciones_collection.count_documents({"tiene_renfe": True})
        
        # Estaciones por zona
        zonas = estaciones_collection.distinct("zona_tarifaria")
        estaciones_por_zona = {}
        for zona in zonas:
            count = estaciones_collection.count_documents({"zona_tarifaria": zona})
            estaciones_por_zona[zona] = count
        
        # Estudios por tipo
        pipeline_estudios = [
            {"$unwind": "$estudios"},
            {"$group": {
                "_id": "$estudios.tipo",
                "total": {"$sum": 1},
                "plazas_totales": {"$sum": "$estudios.plazas"}
            }}
        ]
        estudios_stats = list(campus_collection.aggregate(pipeline_estudios))
        
        stats = {
            "total_lineas": total_lineas,
            "total_estaciones": total_estaciones,
            "total_campus": total_campus,
            "estaciones_renfe": estaciones_renfe,
            "estaciones_por_zona": estaciones_por_zona,
            "estudios_stats": estudios_stats
        }
        
        print("\n📊 ESTADÍSTICAS GENERALES DEL SISTEMA")
        print("=" * 70)
        print(f"🚇 Líneas de metro: {total_lineas}")
        print(f"🚉 Estaciones totales: {total_estaciones}")
        print(f"   └─ Con Renfe: {estaciones_renfe}")
        print(f"   └─ Sin Renfe: {total_estaciones - estaciones_renfe}")
        
        print(f"\n📍 Estaciones por zona tarifaria:")
        for zona, count in sorted(estaciones_por_zona.items()):
            print(f"   • {zona}: {count} estaciones")
        
        print(f"\n🎓 Campus universitarios: {total_campus}")
        print(f"📚 Estudios ofrecidos:")
        for stat in estudios_stats:
            tipo = stat["_id"]
            total = stat["total"]
            plazas = stat["plazas_totales"]
            print(f"   • {tipo}s: {total} programas ({plazas} plazas totales)")
        
        return stats

    def close(self):
        """Cierra la conexión a MongoDB"""
        self.client.close()
        print("\n✓ Conexión cerrada")


def ejemplos_lectura():
    """Ejemplos de operaciones de lectura"""
    
    print("=" * 70)
    print("OPERACIONES CRUD - READ (LECTURA)")
    print("Metro de Madrid y Universidades - URJC 2025/2026")
    print("=" * 70)
    
    crud = CRUDReadOperations(MONGODB_URI, DATABASE_NAME)
    
    try:
        # ================================================================
        # 1. BÚSQUEDA POR FILTROS - ZONA TARIFARIA
        # ================================================================
        print("\n" + "=" * 70)
        print("1️⃣  BÚSQUEDA POR ZONA TARIFARIA")
        print("=" * 70)
        
        # Buscar estaciones en Zona A
        estaciones_zona_a = crud.buscar_estaciones_por_zona("A")
        
        # ================================================================
        # 2. CONSULTA DE CORRESPONDENCIAS RENFE
        # ================================================================
        print("\n" + "=" * 70)
        print("2️⃣  CONSULTA DE CORRESPONDENCIAS RENFE")
        print("=" * 70)
        
        estaciones_renfe = crud.consultar_correspondencias_renfe()
        
        # ================================================================
        # 3. EXPLORACIÓN ACADÉMICA - POR UNIVERSIDAD
        # ================================================================
        print("\n" + "=" * 70)
        print("3️⃣  EXPLORACIÓN ACADÉMICA - POR UNIVERSIDAD")
        print("=" * 70)
        
        # Buscar campus de la UCM
        campus_ucm = crud.buscar_campus_por_universidad("UCM")
        
        # Buscar campus de la UPM
        campus_upm = crud.buscar_campus_por_universidad("UPM")
        
        # ================================================================
        # 4. EXPLORACIÓN ACADÉMICA - POR GRADO
        # ================================================================
        print("\n" + "=" * 70)
        print("4️⃣  EXPLORACIÓN ACADÉMICA - POR GRADO")
        print("=" * 70)
        
        # Buscar campus que imparten Informática
        campus_informatica = crud.buscar_campus_por_grado("Informática")
        
        # Buscar campus que imparten Medicina
        campus_medicina = crud.buscar_campus_por_grado("Medicina")
        
        # ================================================================
        # 5. ORDENACIÓN - ESTACIONES POR LÍNEA
        # ================================================================
        print("\n" + "=" * 70)
        print("5️⃣  ORDENACIÓN - ESTACIONES POR LÍNEA")
        print("=" * 70)
        
        # Listar estaciones de la Línea 1 ordenadas
        estaciones_l1 = crud.listar_estaciones_por_linea_ordenadas(1)
        
        # Listar estaciones de la Línea 6 ordenadas
        estaciones_l6 = crud.listar_estaciones_por_linea_ordenadas(6)
        
        # ================================================================
        # 6. ESTADÍSTICAS GENERALES
        # ================================================================
        print("\n" + "=" * 70)
        print("6️⃣  ESTADÍSTICAS GENERALES")
        print("=" * 70)
        
        stats = crud.estadisticas_generales()
        
        # ================================================================
        # RESUMEN FINAL
        # ================================================================
        print("\n" + "=" * 70)
        print("✅ OPERACIONES DE LECTURA COMPLETADAS")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        crud.close()

class CRUDUpdateOperations:
    """Clase para operaciones de actualización en MongoDB"""

    def __init__(self, uri: str, db_name: str):
        """Inicializa la conexión a MongoDB"""
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        print(f"✓ Conectado a MongoDB: {db_name}")

    def modificar_nota_corte(self, nombre_campus: str, universidad: str,
                            nombre_estudio: str, nueva_nota_corte: float) -> bool:
        """
        Actualiza la nota de corte de un estudio específico dentro de un campus
        
        Args:
            nombre_campus: Nombre del campus
            universidad: Universidad del campus
            nombre_estudio: Nombre del estudio a actualizar
            nueva_nota_corte: Nueva nota de corte
        
        Returns:
            True si se actualizó correctamente, False en caso contrario
        """
        campus_collection = self.db.campus
        
        # Buscar el campus
        campus = campus_collection.find_one({
            "nombre": nombre_campus,
            "universidad": {"$regex": universidad, "$options": "i"}
        })
        
        if not campus:
            print(f"⚠️  Campus '{nombre_campus}' de {universidad} no encontrado")
            return False
        
        # Buscar el índice del estudio en el array
        estudios = campus.get("estudios", [])
        estudio_index = None
        estudio_anterior = None
        
        for i, estudio in enumerate(estudios):
            if estudio["nombre"] == nombre_estudio:
                estudio_index = i
                estudio_anterior = estudio
                break
        
        if estudio_index is None:
            print(f"⚠️  Estudio '{nombre_estudio}' no encontrado en el campus")
            return False
        
        # Actualizar usando el operador posicional $
        result = campus_collection.update_one(
            {
                "_id": campus["_id"],
                "estudios.nombre": nombre_estudio
            },
            {
                "$set": {
                    "estudios.$.nota_corte": nueva_nota_corte,
                    "estudios.$.fecha_actualizacion": datetime.now()
                }
            }
        )
        
        if result.modified_count > 0:
            nota_anterior = estudio_anterior.get("nota_corte", "N/A")
            print(f"✅ Nota de corte actualizada:")
            print(f"   Campus: {nombre_campus} ({universidad})")
            print(f"   Estudio: {nombre_estudio}")
            print(f"   Nota anterior: {nota_anterior} → Nueva nota: {nueva_nota_corte}")
            return True
        else:
            print(f"⚠️  No se pudo actualizar la nota de corte")
            return False

    def añadir_servicio_renfe(self, nombre_estacion: str,
                             nombre_estacion_renfe: str,
                             tipo_estacion: str,
                             servicios: List[str],
                             lineas_cercanias: List[str]) -> bool:
        """
        Añade servicio Renfe a una estación que no lo tenía
        
        Args:
            nombre_estacion: Nombre de la estación de metro
            nombre_estacion_renfe: Nombre de la estación Renfe
            tipo_estacion: Tipo de estación Renfe (ej: "ESTACION_PRINCIPAL", "CERCANIAS")
            servicios: Lista de servicios (ej: ["AVE", "Cercanías"])
            lineas_cercanias: Lista de líneas de cercanías (ej: ["C1", "C2"])
        
        Returns:
            True si se actualizó correctamente, False en caso contrario
        """
        estaciones_collection = self.db.estaciones
        
        # Buscar la estación
        estacion = estaciones_collection.find_one({"nombre": nombre_estacion})
        
        if not estacion:
            print(f"⚠️  Estación '{nombre_estacion}' no encontrada")
            return False
        
        # Verificar si ya tiene Renfe
        if estacion.get("tiene_renfe", False):
            print(f"⚠️  La estación '{nombre_estacion}' ya tiene servicio Renfe")
            return False
        
        # Actualizar la estación
        result = estaciones_collection.update_one(
            {"_id": estacion["_id"]},
            {
                "$set": {
                    "tiene_renfe": True,
                    "estacion_renfe": {
                        "nombre": nombre_estacion_renfe,
                        "tipo": tipo_estacion,
                        "servicios": servicios,
                        "lineas_cercanias": lineas_cercanias,
                        "fecha_activacion": datetime.now()
                    },
                    "fecha_actualizacion": datetime.now()
                }
            }
        )
        
        if result.modified_count > 0:
            lineas_str = ", ".join([f"L{l}" for l in estacion.get("lineas", [])])
            print(f"✅ Servicio Renfe añadido:")
            print(f"   Estación Metro: {nombre_estacion} ({lineas_str})")
            print(f"   Estación Renfe: {nombre_estacion_renfe}")
            print(f"   Tipo: {tipo_estacion}")
            print(f"   Servicios: {', '.join(servicios)}")
            print(f"   Líneas Cercanías: {', '.join(lineas_cercanias)}")
            return True
        else:
            print(f"⚠️  No se pudo actualizar la estación")
            return False

    def añadir_master_a_campus(self, nombre_campus: str, universidad: str,
                               master: Dict) -> bool:
        """
        Añade un nuevo Máster al array de estudios de un campus existente
        
        Args:
            nombre_campus: Nombre del campus
            universidad: Universidad del campus
            master: Diccionario con información del máster
                   Debe contener: nombre, tipo (MASTER), duracion_años, plazas
        
        Returns:
            True si se añadió correctamente, False en caso contrario
        """
        campus_collection = self.db.campus
        
        # Verificar que el tipo sea MASTER
        if master.get("tipo") != "MASTER":
            print(f"⚠️  El tipo de estudio debe ser 'MASTER'")
            return False
        
        # Buscar el campus
        campus = campus_collection.find_one({
            "nombre": nombre_campus,
            "universidad": {"$regex": universidad, "$options": "i"}
        })
        
        if not campus:
            print(f"⚠️  Campus '{nombre_campus}' de {universidad} no encontrado")
            return False
        
        # Verificar que el máster no exista ya
        estudios = campus.get("estudios", [])
        for estudio in estudios:
            if estudio["nombre"] == master["nombre"]:
                print(f"⚠️  El máster '{master['nombre']}' ya existe en el campus")
                return False
        
        # Añadir fecha de creación al máster
        master["fecha_creacion"] = datetime.now()
        
        # Añadir el máster al array de estudios
        result = campus_collection.update_one(
            {"_id": campus["_id"]},
            {
                "$push": {"estudios": master},
                "$set": {"fecha_actualizacion": datetime.now()}
            }
        )
        
        if result.modified_count > 0:
            plazas = master.get("plazas", "N/A")
            duracion = master.get("duracion_años", "N/A")
            print(f"✅ Máster añadido al campus:")
            print(f"   Campus: {nombre_campus} ({universidad})")
            print(f"   Máster: {master['nombre']}")
            print(f"   Duración: {duracion} año(s)")
            print(f"   Plazas: {plazas}")
            
            # Mostrar estadísticas actualizadas
            campus_actualizado = campus_collection.find_one({"_id": campus["_id"]})
            estudios_actualizados = campus_actualizado.get("estudios", [])
            grados = [e for e in estudios_actualizados if e["tipo"] == "GRADO"]
            masters = [e for e in estudios_actualizados if e["tipo"] == "MASTER"]
            print(f"   Total estudios ahora: {len(grados)} Grados, {len(masters)} Másteres")
            
            return True
        else:
            print(f"⚠️  No se pudo añadir el máster")
            return False

    def actualizar_zona_tarifaria(self, nombre_estacion: str, nueva_zona: str) -> bool:
        """
        Actualiza la zona tarifaria de una estación
        
        Args:
            nombre_estacion: Nombre de la estación
            nueva_zona: Nueva zona tarifaria (ej: "A", "B1", "B2", "B3")
        
        Returns:
            True si se actualizó correctamente, False en caso contrario
        """
        estaciones_collection = self.db.estaciones
        
        # Buscar la estación
        estacion = estaciones_collection.find_one({"nombre": nombre_estacion})
        
        if not estacion:
            print(f"⚠️  Estación '{nombre_estacion}' no encontrada")
            return False
        
        zona_anterior = estacion.get("zona_tarifaria", "N/A")
        
        # Actualizar la zona
        result = estaciones_collection.update_one(
            {"_id": estacion["_id"]},
            {
                "$set": {
                    "zona_tarifaria": nueva_zona,
                    "fecha_actualizacion": datetime.now()
                }
            }
        )
        
        if result.modified_count > 0:
            lineas_str = ", ".join([f"L{l}" for l in estacion.get("lineas", [])])
            print(f"✅ Zona tarifaria actualizada:")
            print(f"   Estación: {nombre_estacion} ({lineas_str})")
            print(f"   Zona anterior: {zona_anterior} → Nueva zona: {nueva_zona}")
            return True
        else:
            print(f"⚠️  No se pudo actualizar la zona tarifaria")
            return False

    def actualizar_plazas_estudio(self, nombre_campus: str, universidad: str,
                                 nombre_estudio: str, nuevas_plazas: int) -> bool:
        """
        Actualiza el número de plazas de un estudio específico
        
        Args:
            nombre_campus: Nombre del campus
            universidad: Universidad del campus
            nombre_estudio: Nombre del estudio
            nuevas_plazas: Nuevo número de plazas
        
        Returns:
            True si se actualizó correctamente, False en caso contrario
        """
        campus_collection = self.db.campus
        
        # Actualizar usando el operador posicional
        result = campus_collection.update_one(
            {
                "nombre": nombre_campus,
                "universidad": {"$regex": universidad, "$options": "i"},
                "estudios.nombre": nombre_estudio
            },
            {
                "$set": {
                    "estudios.$.plazas": nuevas_plazas,
                    "estudios.$.fecha_actualizacion": datetime.now()
                }
            }
        )
        
        if result.modified_count > 0:
            print(f"✅ Plazas actualizadas:")
            print(f"   Campus: {nombre_campus} ({universidad})")
            print(f"   Estudio: {nombre_estudio}")
            print(f"   Nuevas plazas: {nuevas_plazas}")
            return True
        else:
            print(f"⚠️  No se pudo actualizar las plazas")
            return False

    def close(self):
        """Cierra la conexión a MongoDB"""
        self.client.close()
        print("\n✓ Conexión cerrada")


def ejemplos_actualizacion():
    """Ejemplos de operaciones de actualización"""
    
    print("=" * 70)
    print("OPERACIONES CRUD - UPDATE (ACTUALIZACIÓN)")
    print("Metro de Madrid y Universidades - URJC 2025/2026")
    print("=" * 70)
    
    crud = CRUDUpdateOperations(MONGODB_URI, DATABASE_NAME)
    
    try:
        # ================================================================
        # 1. MODIFICAR NOTAS DE CORTE
        # ================================================================
        print("\n" + "=" * 70)
        print("1️⃣  MODIFICAR NOTAS DE CORTE")
        print("=" * 70)
        
        # Actualizar nota de corte de Medicina en UCM
        crud.modificar_nota_corte(
            nombre_campus="Ciudad Universitaria (UCM)",
            universidad="UCM",
            nombre_estudio="Grado en Ciencia e Ingeniería de Datos",
            nueva_nota_corte=13.2
        )
        
        # ================================================================
        # 2. AÑADIR SERVICIOS RENFE
        # ================================================================
        print("\n" + "=" * 70)
        print("2️⃣  AÑADIR SERVICIOS RENFE A ESTACIONES")
        print("=" * 70)
        
        # Añadir Renfe a Nuevos Ministerios
        crud.añadir_servicio_renfe(
            nombre_estacion="Nuevos Ministerios",
            nombre_estacion_renfe="Madrid-Nuevos Ministerios",
            tipo_estacion="CERCANIAS",
            servicios=["Cercanías"],
            lineas_cercanias=["C1", "C2", "C3", "C4", "C7", "C8", "C10"]
        )
        
        # ================================================================
        # 3. AÑADIR NUEVO MÁSTER
        # ================================================================
        print("\n" + "=" * 70)
        print("3️⃣  AMPLIACIÓN DE OFERTA - AÑADIR MÁSTER")
        print("=" * 70)
        
        # Añadir Máster en Ciencia de Datos a UCM
        crud.añadir_master_a_campus(
            nombre_campus="Ciudad Universitaria (UCM)",
            universidad="UCM",
            master={
                "nombre": "Máster en Ciencia de Datos",
                "tipo": "MASTER",
                "duracion_años": 1,
                "plazas": 45,
                "facultad": "Facultad de Informática",
                "modalidad": "Presencial"
            }
        )
        
        # ================================================================
        # RESUMEN FINAL
        # ================================================================
        print("\n" + "=" * 70)
        print("📊 RESUMEN DE ACTUALIZACIONES")
        print("=" * 70)
        
        # Contar estaciones con Renfe después de las actualizaciones
        estaciones_renfe = crud.db.estaciones.count_documents({"tiene_renfe": True})
        print(f"✅ Estaciones con Renfe: {estaciones_renfe}")
        
        # Contar total de estudios
        pipeline = [
            {"$unwind": "$estudios"},
            {"$group": {
                "_id": "$estudios.tipo",
                "total": {"$sum": 1}
            }}
        ]
        estudios_stats = list(crud.db.campus.aggregate(pipeline))
        print(f"✅ Estudios por tipo:")
        for stat in estudios_stats:
            print(f"   • {stat['_id']}s: {stat['total']}")
        
        print("\n" + "=" * 70)
        print("✅ OPERACIONES DE ACTUALIZACIÓN COMPLETADAS")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        crud.close()

class CRUDDeleteOperations:
    """Clase para operaciones de borrado en MongoDB"""

    def __init__(self, uri: str, db_name: str):
        """Inicializa la conexión a MongoDB"""
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        print(f"✓ Conectado a MongoDB (Modo Borrado): {db_name}")

    def eliminar_estudio_de_campus(self, nombre_campus: str, universidad: str, 
                                 nombre_estudio: str) -> bool:
        """
        Elimina un estudio específico (Grado o Máster) de un campus.
        """
        campus_collection = self.db.campus
        
        # Usamos $pull para retirar el elemento del array 'estudios'
        result = campus_collection.update_one(
            {
                "nombre": nombre_campus,
                "universidad": {"$regex": universidad, "$options": "i"}
            },
            {
                "$pull": {"estudios": {"nombre": nombre_estudio}}
            }
        )

        if result.modified_count > 0:
            print(f"🗑️  Estudio eliminado correctamente:")
            print(f"   Campus: {nombre_campus}")
            print(f"   Estudio: {nombre_estudio}")
            return True
        else:
            print(f"⚠️  No se encontró el estudio '{nombre_estudio}' en ese campus o el campus no existe.")
            return False

    def eliminar_estacion(self, nombre_estacion: str) -> bool:
        """
        Elimina una estación y retira su referencia de las líneas correspondientes.
        """
        estaciones_collection = self.db.estaciones
        lineas_collection = self.db.lineas

        # 1. Buscar la estación primero para tener su ID
        estacion = estaciones_collection.find_one({"nombre": nombre_estacion})
        
        if not estacion:
            print(f"⚠️  La estación '{nombre_estacion}' no existe.")
            return False

        estacion_id = estacion["_id"]
        lineas_afectadas = estacion.get("lineas", [])

        # 2. Eliminar el documento de la estación
        estaciones_collection.delete_one({"_id": estacion_id})
        print(f"🗑️  Estación '{nombre_estacion}' eliminada de la colección 'estaciones'.")

        # 3. Limpieza: Eliminar la referencia (ObjectId) de los arrays 'estaciones_ids' en las líneas
        # Esto mantiene la integridad referencial básica sin complicar mucho el código.
        if lineas_afectadas:
            lineas_collection.update_many(
                {"numero": {"$in": lineas_afectadas}},
                {"$pull": {"estaciones_ids": estacion_id}}
            )
            print(f"   Ref. eliminada de las líneas: {lineas_afectadas}")
        
        return True

    def eliminar_campus(self, nombre_campus: str, universidad: str) -> bool:
        """
        Elimina un campus universitario completo.
        """
        campus_collection = self.db.campus

        result = campus_collection.delete_one({
            "nombre": nombre_campus,
            "universidad": {"$regex": universidad, "$options": "i"}
        })

        if result.deleted_count > 0:
            print(f"🗑️  Campus eliminado: {nombre_campus} ({universidad})")
            return True
        else:
            print(f"⚠️  No se encontró el campus '{nombre_campus}'.")
            return False

    def eliminar_linea(self, numero_linea: int) -> bool:
        """
        Elimina una línea de metro.        
        """
        lineas_collection = self.db.lineas

        result = lineas_collection.delete_one({"numero": numero_linea})

        if result.deleted_count > 0:
            print(f"🗑️  Línea {numero_linea} eliminada del sistema.")
            return True
        else:
            print(f"⚠️  La línea {numero_linea} no existe.")
            return False

    def close(self):
        """Cierra la conexión"""
        self.client.close()
        print("\n✓ Conexión cerrada (Delete)")


def ejemplos_borrado():
    """Ejemplos de operaciones de borrado"""
    
    print("=" * 70)
    print("OPERACIONES CRUD - DELETE (BORRADO)")
    print("Metro de Madrid y Universidades - URJC 2025/2026")
    print("=" * 70)
    
    crud = CRUDDeleteOperations(MONGODB_URI, DATABASE_NAME)
    
    try:
        # ================================================================
        # 1. ELIMINAR UN ESTUDIO (EMBEBIDO)
        # ================================================================
        print("\n" + "=" * 70)
        print("1️⃣  ELIMINAR ESTUDIO DE UN CAMPUS")
        print("=" * 70)
        
        # Eliminamos un Máster específico
        crud.eliminar_estudio_de_campus(
            nombre_campus="Ciudad Universitaria (UCM)", 
            universidad="UCM", 
            nombre_estudio="Grado en Ciencia e Ingeniería de Datos"
        )

        # ================================================================
        # 2. ELIMINAR UNA ESTACIÓN (Y SUS REFERENCIAS)
        # ================================================================
        print("\n" + "=" * 70)
        print("2️⃣  ELIMINAR ESTACIÓN")
        print("=" * 70)
        
        db_temp = MongoClient(MONGODB_URI)[DATABASE_NAME]
        dummy_id = db_temp.estaciones.insert_one({
            "nombre": "Estación Fantasma", 
            "lineas": [6], 
            "zona_tarifaria": "A"
        }).inserted_id
        # La añadimos a la línea 6 artificialmente
        db_temp.lineas.update_one({"numero": 6}, {"$push": {"estaciones_ids": dummy_id}})
        
        # Ahora procedemos a borrarla con nuestra clase
        crud.eliminar_estacion("Estación Fantasma")

        # ================================================================
        # 3. ELIMINAR UN CAMPUS COMPLETO
        # ================================================================
        print("\n" + "=" * 70)
        print("3️⃣  ELIMINAR CAMPUS")
        print("=" * 70)
        
        # Borramos el Campus de la UPM creado anteriormente (ejemplo)
        crud.eliminar_campus("Campus de Moncloa (UPM)", "UPM")

        # ================================================================
        # 4. ELIMINAR UNA LÍNEA
        # ================================================================
        print("\n" + "=" * 70)
        print("4️⃣  ELIMINAR LÍNEA")
        print("=" * 70)
        
        # Eliminamos la línea 4 creada en el batch anterior
        crud.eliminar_linea(4)

        # ================================================================
        # RESUMEN FINAL
        # ================================================================
        print("\n" + "=" * 70)
        print("✅ OPERACIONES DE BORRADO COMPLETADAS")
        print("=" * 70)

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
    finally:
        crud.close()


if __name__ == "__main__":
    ejemplos_creacion()
    ejemplos_lectura()
    ejemplos_actualizacion()
    ejemplos_borrado()
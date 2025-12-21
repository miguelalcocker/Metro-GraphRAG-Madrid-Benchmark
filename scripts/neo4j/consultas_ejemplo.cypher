// ============================================================================
// CONSULTAS CYPHER DE EJEMPLO
// Práctica de Bases de Datos No Relacionales - Metro de Madrid y Universidades
// Universidad Rey Juan Carlos - Curso 2025/2026
// ============================================================================

// ============================================================================
// A. CONSULTAS ESTRUCTURALES
// ============================================================================

// A1. Estaciones de una línea en orden de recorrido
MATCH (l:Linea {numero: 1})-[t:TIENE_ESTACION]->(e:Estacion)
RETURN l.nombre AS linea, e.nombre AS estacion, t.orden AS orden
ORDER BY t.orden;

// A2. Estaciones que son hubs universitarios (relacionadas con más de un campus)
MATCH (e:Estacion)<-[:CERCANA]-(c:Campus)
WITH e, count(DISTINCT c) AS num_campus
WHERE num_campus > 1
RETURN e.nombre AS estacion, num_campus
ORDER BY num_campus DESC;

// A3. Estaciones con correspondencia Renfe y cercanas a algún campus
MATCH (e:Estacion)<-[:CERCANA]-(c:Campus)
WHERE e.tiene_renfe = true
RETURN DISTINCT e.nombre AS estacion,
       e.nombre_estacion_renfe AS estacion_renfe,
       e.lineas_renfe AS lineas_renfe,
       collect(DISTINCT c.nombre) AS campus_cercanos
ORDER BY e.nombre;

// A4. Todas las estaciones con transbordo (múltiples líneas)
MATCH (e:Estacion)
WHERE e.tiene_renfe = true OR exists((e)-[:TRANSBORDO]->())
RETURN e.nombre AS estacion,
       e.tiene_renfe AS tiene_renfe,
       exists((e)-[:TRANSBORDO]->()) AS es_transbordo
ORDER BY e.nombre;


// ============================================================================
// B. CONSULTAS SOBRE CAMPUS Y ESTUDIOS
// ============================================================================

// B1. Campus que ofrecen el Grado en Ciencia e Ingeniería de Datos
MATCH (c:Campus)-[:OFRECE]->(e:Estudio)
WHERE e.tipo = 'GRADO' AND e.nombre CONTAINS 'Ciencia e Ingeniería de Datos'
RETURN c.universidad AS universidad,
       c.nombre AS campus,
       e.nombre AS estudio,
       e.plazas AS plazas,
       e.nota_corte AS nota_corte
ORDER BY c.universidad;

// B2. Número de estudios de GRADO y MÁSTER por universidad
MATCH (c:Campus)-[:OFRECE]->(e:Estudio)
WITH c.universidad AS universidad, e.tipo AS tipo, count(e) AS total
RETURN universidad,
       sum(CASE WHEN tipo = 'GRADO' THEN total ELSE 0 END) AS grados,
       sum(CASE WHEN tipo = 'MASTER' THEN total ELSE 0 END) AS masters,
       sum(total) AS total_estudios
ORDER BY universidad;

// B3. Másteres en Inteligencia Artificial y sus campus
MATCH (c:Campus)-[:OFRECE]->(e:Estudio)
WHERE e.tipo = 'MASTER' AND e.nombre CONTAINS 'Inteligencia Artificial'
RETURN e.nombre AS master,
       collect(c.universidad + ' - ' + c.nombre) AS campus
ORDER BY e.nombre;

// B4. Campus de la UCM con sus estudios
MATCH (c:Campus)-[:OFRECE]->(e:Estudio)
WHERE c.universidad = 'UCM'
RETURN c.nombre AS campus,
       collect({nombre: e.nombre, tipo: e.tipo}) AS estudios;

// B5. Estaciones más cercanas a cada campus
MATCH (c:Campus)-[r:CERCANA]->(e:Estacion)
RETURN c.nombre AS campus,
       c.universidad AS universidad,
       collect({
           estacion: e.nombre,
           minutos: r.minutos,
           rol: r.rol
       }) AS estaciones_cercanas
ORDER BY c.universidad, c.nombre;


// ============================================================================
// C. CONSULTAS DE RUTAS
// ============================================================================

// C1. Camino más corto desde Sol hasta Ciudad Universitaria
MATCH (origen:Estacion {nombre: 'Sol'}),
      (destino:Estacion {nombre: 'Ciudad Universitaria'}),
      path = shortestPath((origen)-[:SIGUIENTE*]-(destino))
RETURN [n IN nodes(path) | n.nombre] AS ruta,
       length(path) AS num_estaciones;

// C2. Camino más corto desde Atocha a cualquier estación cercana al Campus de Moncloa (UPM)
MATCH (origen:Estacion {nombre: 'Atocha'}),
      (campus:Campus {nombre: 'Campus de Moncloa (UPM)'})-[:CERCANA]->(destino:Estacion),
      path = shortestPath((origen)-[:SIGUIENTE*]-(destino))
RETURN campus.nombre AS campus,
       destino.nombre AS estacion_destino,
       [n IN nodes(path) | n.nombre] AS ruta,
       length(path) AS num_estaciones
ORDER BY num_estaciones
LIMIT 1;

// C3. Rutas desde Sol a campus que ofrecen Máster en Inteligencia Artificial
MATCH (origen:Estacion {nombre: 'Sol'}),
      (campus:Campus)-[:OFRECE]->(estudio:Estudio),
      (campus)-[:CERCANA]->(destino:Estacion)
WHERE estudio.nombre CONTAINS 'Inteligencia Artificial' AND estudio.tipo = 'MASTER'
WITH origen, campus, destino, estudio
MATCH path = shortestPath((origen)-[:SIGUIENTE*]-(destino))
RETURN campus.universidad AS universidad,
       campus.nombre AS campus,
       destino.nombre AS estacion_destino,
       length(path) AS num_estaciones,
       [n IN nodes(path) | n.nombre] AS ruta
ORDER BY num_estaciones;

// C4. Camino más corto considerando transbordos
// Desde Pacífico hasta Moncloa usando :SIGUIENTE y :TRANSBORDO
MATCH (origen:Estacion {nombre: 'Pacífico'}),
      (destino:Estacion {nombre: 'Moncloa'}),
      path = shortestPath((origen)-[:SIGUIENTE|TRANSBORDO*]-(destino))
RETURN [n IN nodes(path) | n.nombre] AS ruta,
       length(path) AS num_pasos;

// C5. Encontrar todos los campus alcanzables desde Chamartín
MATCH (origen:Estacion {nombre: 'Chamartín'}),
      (campus:Campus)-[:CERCANA]->(destino:Estacion),
      path = shortestPath((origen)-[:SIGUIENTE*..15]-(destino))
RETURN campus.nombre AS campus,
       campus.universidad AS universidad,
       destino.nombre AS estacion_destino,
       length(path) AS distancia
ORDER BY distancia;


// ============================================================================
// D. CAMBIOS DE LÍNEA Y COMPARATIVA AVANZADA
// ============================================================================

// D1. Calcular cambios de línea en una ruta (usando lineaId en :SIGUIENTE)
MATCH (origen:Estacion {nombre: 'Pinar de Chamartín'}),
      (destino:Estacion {nombre: 'Moncloa'}),
      path = shortestPath((origen)-[:SIGUIENTE*]-(destino))
WITH path,
     [r IN relationships(path) | r.lineaId] AS lineas_ruta
UNWIND range(0, size(lineas_ruta) - 2) AS i
WITH path, lineas_ruta,
     CASE WHEN lineas_ruta[i] <> lineas_ruta[i+1] THEN 1 ELSE 0 END AS cambio
RETURN [n IN nodes(path) | n.nombre] AS ruta,
       length(path) AS num_estaciones,
       sum(cambio) AS num_cambios_linea;

// D2. Comparar rutas por cambios de línea
MATCH (origen:Estacion {nombre: 'Sol'}),
      (campus:Campus {nombre: 'Ciudad Universitaria (UCM)'})-[:CERCANA]->(destino:Estacion),
      path = allShortestPaths((origen)-[:SIGUIENTE*]-(destino))
WITH path,
     [r IN relationships(path) | r.lineaId] AS lineas_ruta,
     [n IN nodes(path) | n.nombre] AS nombres_ruta
UNWIND range(0, size(lineas_ruta) - 2) AS i
WITH path, lineas_ruta, nombres_ruta,
     CASE WHEN lineas_ruta[i] <> lineas_ruta[i+1] THEN 1 ELSE 0 END AS cambio
RETURN nombres_ruta AS ruta,
       length(path) AS num_estaciones,
       sum(cambio) AS num_cambios_linea
ORDER BY num_cambios_linea, num_estaciones
LIMIT 5;

// D3. Tiempo total de viaje estimado (usando tiempo_viaje en :SIGUIENTE)
MATCH (origen:Estacion {nombre: 'Atocha'}),
      (destino:Estacion {nombre: 'Ciudad Universitaria'}),
      path = shortestPath((origen)-[:SIGUIENTE*]-(destino))
WITH path,
     [r IN relationships(path) | r.tiempo_viaje] AS tiempos
RETURN [n IN nodes(path) | n.nombre] AS ruta,
       length(path) AS num_estaciones,
       reduce(total = 0, tiempo IN tiempos | total + tiempo) AS tiempo_total_minutos;


// ============================================================================
// E. ANÁLISIS Y ESTADÍSTICAS
// ============================================================================

// E1. Top 5 estaciones con más conexiones
MATCH (e:Estacion)
WITH e, size((e)-[:SIGUIENTE]-()) + size((e)<-[:SIGUIENTE]-()) AS num_conexiones
RETURN e.nombre AS estacion, num_conexiones
ORDER BY num_conexiones DESC
LIMIT 5;

// E2. Universidades y total de estaciones cercanas (únicas)
MATCH (c:Campus)-[:CERCANA]->(e:Estacion)
WITH c.universidad AS universidad, collect(DISTINCT e) AS estaciones
RETURN universidad,
       size(estaciones) AS num_estaciones_unicas
ORDER BY num_estaciones_unicas DESC;

// E3. Estudios más ofertados (en múltiples campus)
MATCH (c:Campus)-[:OFRECE]->(e:Estudio)
WITH e.nombre AS estudio, e.tipo AS tipo, count(c) AS num_campus
WHERE num_campus > 1
RETURN estudio, tipo, num_campus
ORDER BY num_campus DESC, estudio;

// E4. Campus con mejor conectividad (más estaciones cercanas)
MATCH (c:Campus)-[:CERCANA]->(e:Estacion)
WITH c, count(e) AS num_estaciones
RETURN c.nombre AS campus,
       c.universidad AS universidad,
       num_estaciones
ORDER BY num_estaciones DESC;


// ============================================================================
// F. RECOMENDACIÓN MULTIOBJETIVO (Parte C de la práctica)
// ============================================================================

// F1. Encontrar el mejor campus para estudiar "Grado en Ciencia e Ingeniería de Datos"
//     desde la estación "Sol" (mínima distancia)
MATCH (origen:Estacion {nombre: 'Sol'}),
      (campus:Campus)-[:OFRECE]->(estudio:Estudio),
      (campus)-[:CERCANA]->(destino:Estacion)
WHERE estudio.tipo = 'GRADO' AND estudio.nombre CONTAINS 'Ciencia e Ingeniería de Datos'
WITH origen, campus, estudio, destino
MATCH path = shortestPath((origen)-[:SIGUIENTE*]-(destino))
WITH campus, estudio, destino, path,
     [r IN relationships(path) | r.lineaId] AS lineas_ruta
UNWIND range(0, size(lineas_ruta) - 2) AS i
WITH campus, estudio, destino, path, lineas_ruta,
     CASE WHEN lineas_ruta[i] <> lineas_ruta[i+1] THEN 1 ELSE 0 END AS cambio
RETURN campus.universidad AS universidad,
       campus.nombre AS campus,
       estudio.plazas AS plazas,
       estudio.nota_corte AS nota_corte,
       destino.nombre AS estacion_destino,
       length(path) AS num_estaciones,
       sum(cambio) AS num_cambios_linea,
       [n IN nodes(path) | n.nombre] AS ruta
ORDER BY num_cambios_linea, num_estaciones;


// ============================================================================
// EJEMPLOS DE USO AVANZADO
// ============================================================================

// Encontrar rutas alternativas (no solo la más corta)
MATCH (origen:Estacion {nombre: 'Sol'}),
      (destino:Estacion {nombre: 'Moncloa'}),
      path = (origen)-[:SIGUIENTE*..10]-(destino)
WHERE length(path) <= 12
RETURN DISTINCT [n IN nodes(path) | n.nombre] AS ruta,
       length(path) AS num_estaciones
ORDER BY num_estaciones
LIMIT 5;

// Grafo de subred: todas las estaciones a máximo 5 paradas de Sol
MATCH (origen:Estacion {nombre: 'Sol'})-[:SIGUIENTE*..5]-(e:Estacion)
RETURN DISTINCT e.nombre AS estacion, e.zona_tarifaria AS zona
ORDER BY e.nombre;

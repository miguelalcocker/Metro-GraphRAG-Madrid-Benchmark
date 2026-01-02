#!/bin/bash
# Script de verificación de datos
# Práctica de Bases de Datos No Relacionales - URJC 2025/2026

echo "=========================================="
echo "VERIFICACIÓN DE DATOS - METRO DE MADRID"
echo "=========================================="
echo ""

# Verificar que existen los archivos
echo "📁 Verificando archivos de datos..."
for file in data/lineas.json data/estaciones.json data/campus.json; do
    if [ -f "$file" ]; then
        echo "  ✓ $file"
    else
        echo "  ✗ $file NO ENCONTRADO"
        exit 1
    fi
done
echo ""

# Contar registros
echo "📊 Conteo de registros:"
echo "  • Líneas: $(jq 'length' data/lineas.json)"
echo "  • Estaciones: $(jq 'length' data/estaciones.json)"
echo "  • Campus: $(jq 'length' data/campus.json)"
echo ""

# Verificar líneas
echo "🚇 Líneas de Metro:"
jq -r '.[] | "  L\(.numero): \(.nombre)"' data/lineas.json
echo ""

# Estaciones con Renfe
echo "🚆 Estaciones con correspondencia Renfe:"
jq -r '.[] | select(.tiene_renfe == true) | "  • \(.nombre) - \(.estacion_renfe.nombre)"' data/estaciones.json
echo ""

# Universidades
echo "🎓 Universidades:"
jq -r '.[].universidad' data/campus.json | sort | uniq | while read univ; do
    count=$(jq -r --arg univ "$univ" '.[] | select(.universidad == $univ) | .nombre' data/campus.json | wc -l)
    echo "  • $univ: $count campus"
done
echo ""

# Estudios
echo "📚 Estudios:"
grados=$(jq -r '.[].estudios[] | select(.tipo=="GRADO")' data/campus.json | jq -s 'length')
masters=$(jq -r '.[].estudios[] | select(.tipo=="MASTER")' data/campus.json | jq -s 'length')
echo "  • Grados: $grados"
echo "  • Másteres: $masters"
echo ""

echo "=========================================="
echo "✅ VERIFICACIÓN COMPLETADA"
echo "=========================================="

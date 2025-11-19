#!/bin/bash
# Script para verificar el estado de la aplicación

echo "🔍 Verificando estado de Football Alerts API..."
echo ""

# Verificar si el proceso está corriendo
if pgrep -f "uvicorn app.main:app" > /dev/null; then
    echo "✅ Proceso uvicorn está corriendo"
    PID=$(pgrep -f "uvicorn app.main:app")
    echo "   PID: $PID"
else
    echo "❌ Proceso uvicorn NO está corriendo"
    exit 1
fi

# Verificar si responde
echo ""
echo "🌐 Verificando conectividad..."
if curl -s http://localhost:8000/api/v1/admin/stats > /dev/null; then
    echo "✅ API responde correctamente"
    echo ""
    echo "📊 Estadísticas:"
    curl -s http://localhost:8000/api/v1/admin/stats | python3 -m json.tool
else
    echo "❌ API NO está respondiendo"
    exit 1
fi

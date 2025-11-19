#!/bin/bash
# Script para mantener el Mac despierto mientras corre la app

# Obtener el directorio del script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Activar entorno virtual
source .venv/bin/activate

echo "🔥 Iniciando FastAPI y manteniendo el Mac despierto..."
echo "📍 Directorio: $SCRIPT_DIR"
echo "🌐 URL: http://localhost:8000"
echo "📊 Admin: http://localhost:8000/api/v1/admin/stats"
echo ""
echo "⚠️  Presiona CTRL+C para detener"
echo ""

# Iniciar caffeinate (evita que el Mac duerma) y uvicorn juntos
caffeinate -d -i -m -s uvicorn app.main:app --host 0.0.0.0 --port 8000

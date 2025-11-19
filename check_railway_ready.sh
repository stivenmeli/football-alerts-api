#!/bin/bash
# Script para verificar que todo está listo para Railway

echo "🔍 Verificando preparación para Railway..."
echo ""

ERROR=0

# Verificar archivos necesarios
echo "📁 Verificando archivos necesarios..."

FILES=("Procfile" "railway.toml" "requirements.txt" "runtime.txt" ".gitignore")
for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file - FALTA"
        ERROR=1
    fi
done

echo ""

# Verificar .env
echo "🔐 Verificando variables de entorno..."
if [ -f ".env" ]; then
    echo "  ✅ .env existe"
    
    # Verificar variables críticas
    REQUIRED_VARS=("API_FOOTBALL_KEY" "TELEGRAM_BOT_TOKEN" "TELEGRAM_CHAT_ID")
    for var in "${REQUIRED_VARS[@]}"; do
        if grep -q "^$var=" .env; then
            echo "  ✅ $var configurado"
        else
            echo "  ⚠️  $var - No encontrado en .env"
        fi
    done
else
    echo "  ❌ .env - No existe"
    ERROR=1
fi

echo ""

# Verificar estructura de directorios
echo "📂 Verificando estructura del proyecto..."
DIRS=("app" "app/api" "app/core" "app/models" "app/schemas" "app/services")
for dir in "${DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo "  ✅ $dir/"
    else
        echo "  ❌ $dir/ - FALTA"
        ERROR=1
    fi
done

echo ""

# Verificar Git
echo "🔄 Verificando Git..."
if [ -d ".git" ]; then
    echo "  ✅ Repositorio Git inicializado"
    
    # Ver estado
    UNTRACKED=$(git status --porcelain | grep "^??" | wc -l | xargs)
    MODIFIED=$(git status --porcelain | grep "^ M" | wc -l | xargs)
    
    if [ "$UNTRACKED" -gt 0 ] || [ "$MODIFIED" -gt 0 ]; then
        echo "  ⚠️  Hay cambios sin commit:"
        echo "      - Archivos nuevos: $UNTRACKED"
        echo "      - Archivos modificados: $MODIFIED"
        echo ""
        echo "  💡 Ejecuta:"
        echo "      git add ."
        echo "      git commit -m 'Preparado para Railway'"
    else
        echo "  ✅ Todo está en commit"
    fi
    
    # Verificar remote
    if git remote -v | grep -q "origin"; then
        echo "  ✅ Remote configurado"
        REMOTE=$(git remote get-url origin)
        echo "      URL: $REMOTE"
    else
        echo "  ⚠️  No hay remote configurado"
        echo "  💡 Para GitHub deploy, configura remote:"
        echo "      git remote add origin https://github.com/TU_USUARIO/TU_REPO.git"
    fi
else
    echo "  ⚠️  Git no inicializado"
    echo "  💡 Para usar GitHub deploy:"
    echo "      git init"
    echo "      git add ."
    echo "      git commit -m 'Initial commit'"
fi

echo ""
echo "=================================="

if [ $ERROR -eq 0 ]; then
    echo "✅ TODO LISTO PARA RAILWAY"
    echo ""
    echo "🚀 Próximos pasos:"
    echo "   1. Ve a railway.app y crea una cuenta"
    echo "   2. Si usas GitHub:"
    echo "      - git push origin main"
    echo "      - Deploy desde GitHub en Railway"
    echo "   3. Si usas Railway CLI:"
    echo "      - railway login"
    echo "      - railway init"
    echo "      - railway up"
    echo ""
    echo "📖 Guía completa: RAILWAY_DEPLOY.md"
else
    echo "❌ HAY ERRORES - Revisa los mensajes arriba"
    exit 1
fi


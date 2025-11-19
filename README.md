# ⚽ Football Alerts API

Sistema automatizado de alertas en tiempo real para partidos de fútbol. Recibe notificaciones en Telegram cuando un equipo favorito (cuota < 1.35) está perdiendo entre los minutos 55-62 del partido.

## 🚀 Características

### Core
- ⚽ **Monitoreo en tiempo real** de partidos de las principales ligas europeas
- 📊 **Análisis de cuotas** pre-partido para detectar favoritos
- 🚨 **Alertas inteligentes** vía Telegram
- 🤖 **Automatización completa** con APScheduler
- 💾 **Base de datos SQLite** para persistencia
- 🔄 **Actualizaciones cada minuto** durante partidos

### Ligas Monitoreadas
- 🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League
- 🇪🇸 La Liga
- 🇮🇹 Serie A
- 🇩🇪 Bundesliga
- 🇫🇷 Ligue 1

### Tecnologías
- ✅ FastAPI con tipado completo
- ✅ SQLAlchemy ORM
- ✅ APScheduler para tareas automáticas
- ✅ Telegram Bot API
- ✅ API-Football (RapidAPI)
- ✅ httpx para requests asíncronos
- ✅ Pydantic v2 para validación
- ✅ SQLite para base de datos

## 📋 Requisitos

- Python >= 3.11
- uv (gestor de paquetes y proyectos)
- Cuenta de Telegram
- API Key de API-Football (RapidAPI) - Plan gratuito disponible

## ⚡ Inicio Rápido

**Lee la guía completa en [SETUP.md](SETUP.md) para configuración paso a paso.**

## 🛠️ Instalación

### 1. Instalar uv (si no lo tienes)

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# O con pip
pip install uv
```

### 2. Crear entorno virtual e instalar dependencias

```bash
# Crear y activar entorno virtual con uv
uv venv

# Activar el entorno virtual
source .venv/bin/activate  # Linux/macOS
# o
.venv\Scripts\activate  # Windows

# Instalar dependencias de producción
uv pip install -e .

# Instalar dependencias de desarrollo
uv pip install -e ".[dev]"
```

### 3. Configurar variables de entorno

```bash
# Copiar el archivo de ejemplo
cp .env.example .env

# Editar .env con tus configuraciones
```

## 🏃 Ejecutar la aplicación

```bash
# Activar entorno virtual
source .venv/bin/activate

# Ejecutar en modo desarrollo
uvicorn app.main:app --reload
```

La aplicación iniciará:
- 📊 Base de datos SQLite
- 🤖 Scheduler automático
- 🔄 Jobs programados
- 🌐 API en http://localhost:8000

## 📚 Documentación y Endpoints

### Documentación Interactiva

- **Swagger UI**: http://localhost:8000/api/v1/docs
- **ReDoc**: http://localhost:8000/api/v1/redoc

### Endpoints Principales

#### Admin (Gestión Manual)

```bash
# Probar conexión Telegram
POST /api/v1/admin/test-telegram

# Obtener partidos del día
POST /api/v1/admin/fetch-fixtures

# Obtener cuotas de apuestas
POST /api/v1/admin/fetch-odds

# Ejecutar monitoreo manual
POST /api/v1/admin/monitor-matches

# Ver estadísticas
GET /api/v1/admin/stats

# Ver lista de partidos
GET /api/v1/admin/matches?monitored_only=true
```

## 🧪 Tests

```bash
# Ejecutar todos los tests
pytest

# Con cobertura
pytest --cov=app --cov-report=html

# Tests específicos
pytest tests/test_items.py -v
```

## 🔍 Linting y Type Checking

```bash
# Linting con Ruff
ruff check .

# Auto-fix
ruff check --fix .

# Formateo
ruff format .

# Type checking con mypy
mypy app/
```

## 🔄 ¿Cómo Funciona?

### Flujo Automático

1. **8:00 AM cada día** 📅
   - Obtiene fixtures del día para las 5 ligas
   - Almacena partidos en la base de datos

2. **Cada 2 horas** 📊
   - Obtiene cuotas de Bet365 para partidos sin cuotas
   - Detecta equipo favorito (menor cuota)
   - Marca para monitoreo si cuota < 1.35

3. **Cada minuto** 👁️
   - Actualiza estado de partidos en vivo
   - Verifica condiciones:
     - ✅ Minuto entre 55-62
     - ✅ Favorito está perdiendo
   - Envía alerta a Telegram si se cumplen ambas

### Ejemplo de Alerta

```
🚨 ALERTA DE VALOR 🚨

⚽ Real Madrid vs Getafe
🕐 Minuto: 58'
📊 Score: 0 - 1
😱 Real Madrid está perdiendo!
📉 Cuota pre-partido: 1.28
🏆 Liga: La Liga

#AlertaDeValor #LaLiga
```

## 📁 Estructura del Proyecto

```
fastapi-project/
├── app/
│   ├── main.py                 # Aplicación FastAPI + lifecycle
│   ├── api/
│   │   └── routes/
│   │       ├── admin.py        # Rutas administrativas
│   │       └── items.py        # Ejemplo CRUD
│   ├── core/
│   │   └── config.py           # Configuración y settings
│   ├── database/
│   │   └── __init__.py         # SQLAlchemy setup
│   ├── models/
│   │   ├── match.py            # Modelo de partido
│   │   ├── league.py           # Modelo de liga
│   │   ├── team.py             # Modelo de equipo
│   │   └── notification.py     # Modelo de notificación
│   ├── services/
│   │   ├── api_football.py     # Cliente API-Football
│   │   ├── telegram_service.py # Cliente Telegram
│   │   └── monitor_service.py  # Lógica de monitoreo
│   └── scheduler/
│       └── jobs.py             # Jobs automáticos
├── tests/
├── get_telegram_chat_id.py     # Script helper
├── SETUP.md                    # Guía de configuración
├── .env.example
└── README.md
```

## 🔧 Comandos útiles de uv

```bash
# Sincronizar dependencias con pyproject.toml
uv pip sync

# Agregar una nueva dependencia
uv pip install <paquete>

# Actualizar dependencias
uv pip install --upgrade <paquete>

# Ver dependencias instaladas
uv pip list

# Crear requirements.txt (si es necesario)
uv pip freeze > requirements.txt
```

## 💡 Consejos y Mejores Prácticas

### Optimización de Requests API

El plan gratuito de API-Football tiene **100 requests/día**. El sistema está optimizado para:
- ✅ Obtener fixtures solo 1 vez al día
- ✅ Cachear cuotas (no volver a obtener si ya existen)
- ✅ Combinar requests cuando es posible

### Mantener la Aplicación Corriendo 24/7

⚠️ **IMPORTANTE:** Cuando tu Mac entra en modo reposo, la aplicación se pausa.

**Solución rápida:**
```bash
# Mantener Mac despierto mientras corre
./keep_awake.sh
```

**Para hosting 24/7 real (sin depender de tu computadora):**
Ver guía completa → **[HOSTING.md](HOSTING.md)**

Incluye:
- ✅ Cómo evitar modo reposo en Mac
- ✅ Configurar inicio automático
- ✅ Opciones de hosting en la nube (gratis)
- ✅ Railway, Fly.io, Oracle Cloud, etc.

Para detener:
```bash
pkill -f "uvicorn app.main:app"
```

### Monitoreo de Logs

```bash
# Ver logs en tiempo real
tail -f football_alerts.log

# Ver últimas 50 líneas
tail -n 50 football_alerts.log
```

## 🐛 Troubleshooting

| Problema | Solución |
|----------|----------|
| No recibo alertas | Verifica que haya partidos monitoreados en `/api/v1/admin/matches?monitored_only=true` |
| Error de Telegram | Verifica `TELEGRAM_BOT_TOKEN` y `TELEGRAM_CHAT_ID` en `.env` |
| Error de API-Football | Verifica `API_FOOTBALL_KEY` y que no hayas excedido el límite de requests |
| Base de datos corrupta | Elimina `football_alerts.db` y reinicia la app |

## 🎯 Variables de Configuración

| Variable | Descripción | Por Defecto |
|----------|-------------|-------------|
| `FAVORITE_ODDS_THRESHOLD` | Cuota máxima para considerar favorito | 1.35 |
| `MONITOR_MINUTE_START` | Minuto inicio ventana de monitoreo | 55 |
| `MONITOR_MINUTE_END` | Minuto fin ventana de monitoreo | 62 |
| `UPDATE_INTERVAL_SECONDS` | Frecuencia de actualización | 60 |
| `LEAGUES_TO_MONITOR` | IDs de ligas a monitorear | 39,140,135,78,61 |

## 📝 Notas Importantes

- ⚠️ **Mantén tu computadora encendida** para recibir alertas
- ⚠️ **Plan gratuito**: 100 requests/día en API-Football
- ✅ **Base de datos**: SQLite local (`football_alerts.db`)
- ✅ **Sin dependencias externas**: No necesitas Redis, PostgreSQL, etc.
- ✅ **Privacidad**: Tus datos solo están en tu computadora

## 🤝 Contribuciones

¿Ideas para mejorar? ¡Las contribuciones son bienvenidas!

## 📄 Licencia

MIT


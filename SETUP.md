# 🚀 Guía de Configuración - Football Alerts API

Esta guía te llevará paso a paso para configurar y ejecutar el sistema de alertas de partidos de fútbol.

## 📋 Requisitos Previos

- ✅ Python 3.11+ instalado
- ✅ uv instalado
- ✅ Cuenta de Telegram
- ✅ Cuenta en RapidAPI (para API-Football)

---

## 🔧 Paso 1: Configurar el Entorno Virtual

```bash
# Navegar al proyecto
cd /Users/stialvarez/Documents/Proyectos/fastapi-project

# Activar el entorno virtual
source .venv/bin/activate

# Las dependencias ya están instaladas
```

---

## 🤖 Paso 2: Crear Bot de Telegram

### 2.1 Crear el Bot

1. Abre Telegram y busca: `@BotFather`
2. Envía: `/start`
3. Envía: `/newbot`
4. Escoge un nombre: `Football Alerts Bot` (o el que prefieras)
5. Escoge un username: `football_alerts_tu_nombre_bot` (debe terminar en `bot`)
6. **Guarda el TOKEN** que te da BotFather (se ve así: `6842736472:AAHfF8zX...`)

### 2.2 Obtener tu Chat ID

```bash
# Ejecutar el script helper
python get_telegram_chat_id.py

# O pasarle el token directamente
python get_telegram_chat_id.py TU_BOT_TOKEN_AQUI
```

Antes de ejecutar el script:
1. Busca tu bot en Telegram
2. Envíale un mensaje (ejemplo: "hola")
3. Ejecuta el script
4. **Guarda el CHAT_ID** que te muestra

---

## 🌐 Paso 3: Configurar API-Football

### 3.1 Crear cuenta en RapidAPI

1. Ve a: https://rapidapi.com/
2. Crea una cuenta gratuita
3. Busca: "API-Football"
4. Suscríbete al plan FREE (100 requests/día)
5. Ve a la pestaña "Endpoints"
6. Copia tu **API Key** (aparece en el código de ejemplo)

---

## ⚙️ Paso 4: Configurar Variables de Entorno

```bash
# Copiar el archivo de ejemplo
cp .env.example .env

# Editar el archivo .env
nano .env  # o vim .env, o code .env
```

Completa estos valores en `.env`:

```bash
# API-Football (obligatorio)
API_FOOTBALL_KEY=tu_api_key_de_rapidapi_aqui

# Telegram (obligatorio)
TELEGRAM_BOT_TOKEN=tu_bot_token_de_telegram_aqui
TELEGRAM_CHAT_ID=tu_chat_id_aqui

# Resto de configuración (opcional, ya tienen valores por defecto)
FAVORITE_ODDS_THRESHOLD=1.35
MONITOR_MINUTE_START=55
MONITOR_MINUTE_END=62
```

---

## 🧪 Paso 5: Probar la Configuración

### 5.1 Iniciar la aplicación

```bash
uvicorn app.main:app --reload
```

Deberías ver:
```
🚀 Starting Football Alerts API...
📊 Initializing database...
🚀 Starting scheduler...
📅 Scheduled: Fetch fixtures daily at 8:00 AM
📊 Scheduled: Fetch odds every 2 hours
👁️  Scheduled: Monitor matches every 60 seconds
✅ Application started successfully!
```

### 5.2 Probar Telegram

Abre tu navegador y ve a:

```
http://localhost:8000/api/v1/admin/test-telegram
```

Deberías recibir un mensaje de prueba en Telegram! 🎉

### 5.3 Ver estadísticas

```
http://localhost:8000/api/v1/admin/stats
```

---

## 📊 Paso 6: Cargar Datos Iniciales

### 6.1 Cargar partidos del día

```bash
curl -X POST http://localhost:8000/api/v1/admin/fetch-fixtures
```

### 6.2 Obtener cuotas

```bash
curl -X POST http://localhost:8000/api/v1/admin/fetch-odds
```

### 6.3 Ver partidos monitoreados

```
http://localhost:8000/api/v1/admin/matches?monitored_only=true
```

---

## 🔄 Paso 7: Funcionamiento Automático

Una vez configurado, el sistema funciona automáticamente:

1. **8:00 AM cada día**: Obtiene los partidos del día
2. **Cada 2 horas**: Actualiza las cuotas de apuestas
3. **Cada minuto**: Monitorea partidos en vivo

### Jobs Automáticos

- ✅ Detecta favoritos (cuota < 1.35)
- ✅ Monitorea partidos en vivo (minutos 55-62)
- ✅ Envía alerta si el favorito va perdiendo
- ✅ No repite notificaciones

---

## 📱 Endpoints Útiles

### Documentación Interactiva
```
http://localhost:8000/api/v1/docs
```

### Endpoints Admin

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/v1/admin/fetch-fixtures` | POST | Obtener partidos manualmente |
| `/api/v1/admin/fetch-odds` | POST | Obtener cuotas manualmente |
| `/api/v1/admin/monitor-matches` | POST | Ejecutar monitoreo manual |
| `/api/v1/admin/test-telegram` | POST | Probar Telegram |
| `/api/v1/admin/stats` | GET | Ver estadísticas |
| `/api/v1/admin/matches` | GET | Ver lista de partidos |

---

## 🎯 Uso Diario

### Mantener la aplicación corriendo

```bash
# Mantén esta terminal abierta
uvicorn app.main:app --reload
```

O ejecuta en segundo plano:

```bash
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > football_alerts.log 2>&1 &
```

Para detener:

```bash
pkill -f "uvicorn app.main:app"
```

---

## 🐛 Solución de Problemas

### Error: "API-Football key not configured"
- Verifica que hayas configurado `API_FOOTBALL_KEY` en `.env`

### Error: "Telegram not configured"
- Verifica `TELEGRAM_BOT_TOKEN` y `TELEGRAM_CHAT_ID` en `.env`

### No recibo notificaciones
1. Verifica que haya partidos hoy: `/api/v1/admin/stats`
2. Verifica partidos monitoreados: `/api/v1/admin/matches?monitored_only=true`
3. Ejecuta monitoreo manual: `POST /api/v1/admin/monitor-matches`

### La aplicación no inicia
```bash
# Revisar logs
tail -f football_alerts.log

# Reinstalar dependencias
uv pip install -e ".[dev]"
```

---

## 📝 Notas Importantes

- ⚠️ **Plan Gratuito de API-Football**: 100 requests/día
- ⚠️ **Mantén tu computadora encendida** para que el sistema funcione
- ✅ **Base de datos**: SQLite en `football_alerts.db`
- ✅ **Logs**: La aplicación imprime logs en la terminal

---

## 🎉 ¡Listo!

Tu sistema de alertas ya está configurado y funcionando. Recibirás notificaciones en Telegram cuando:

1. Un favorito (cuota < 1.35) esté jugando
2. El partido esté entre los minutos 55-62
3. El favorito vaya perdiendo

¡Disfruta las alertas! ⚽🚨


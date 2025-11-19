# 🚂 Guía de Deploy en Railway - Football Alerts API

Esta guía te llevará paso a paso para desplegar tu aplicación en Railway y tenerla corriendo 24/7.

---

## 📋 Requisitos Previos

✅ Ya tienes todo listo:
- ✅ Código funcionando localmente
- ✅ Variables de entorno configuradas
- ✅ Archivos de Railway creados (`Procfile`, `railway.toml`, `requirements.txt`)

---

## 🚀 Paso 1: Crear cuenta en Railway

1. Ve a [railway.app](https://railway.app)
2. Haz clic en **"Login"** o **"Start a New Project"**
3. Elige una opción para registrarte:
   - **GitHub** (Recomendado - más fácil para deploy)
   - **Google**
   - **Email**

---

## 🎯 Paso 2: Preparar Git (si usas GitHub)

### Opción A: Ya tienes Git configurado

Verifica si tu proyecto ya es un repositorio:

```bash
cd /Users/stialvarez/Documents/Proyectos/fastapi-project
git status
```

### Opción B: Inicializar Git (si no lo tienes)

```bash
cd /Users/stialvarez/Documents/Proyectos/fastapi-project

# Inicializar repositorio
git init

# Agregar archivos
git add .

# Hacer commit
git commit -m "Initial commit - Football Alerts API"

# Crear repositorio en GitHub
# Ve a github.com → New Repository → Copia la URL

# Conectar y subir
git remote add origin https://github.com/TU_USUARIO/football-alerts.git
git branch -M main
git push -u origin main
```

### Opción C: Deploy directo desde local (sin GitHub)

Railway también permite deploy desde CLI sin GitHub.

---

## 🏗️ Paso 3: Crear Proyecto en Railway

### Si usas GitHub (Más fácil):

1. En Railway, haz clic en **"New Project"**
2. Selecciona **"Deploy from GitHub repo"**
3. Autoriza a Railway para acceder a GitHub
4. Selecciona tu repositorio: `football-alerts`
5. Railway detectará automáticamente que es Python
6. Haz clic en **"Deploy Now"**

### Si NO usas GitHub (Deploy manual):

1. Instala Railway CLI:
```bash
# macOS
brew install railway

# O con npm
npm install -g @railway/cli
```

2. Login en Railway:
```bash
railway login
```

3. Inicializar proyecto:
```bash
cd /Users/stialvarez/Documents/Proyectos/fastapi-project
railway init
```

4. Deploy:
```bash
railway up
```

---

## ⚙️ Paso 4: Configurar Variables de Entorno

En Railway, ve a tu proyecto → **Variables** → Agrega estas variables:

```env
# Aplicación
PROJECT_NAME=Football Alerts API
VERSION=1.0.0
ALLOWED_ORIGINS=*

# API Football
API_FOOTBALL_KEY=455262278cbc61fe710fcd73a9e4a596
API_FOOTBALL_BASE_URL=https://v3.football.api-sports.io

# Telegram
TELEGRAM_BOT_TOKEN=tu_token_aqui
TELEGRAM_CHAT_ID=tu_chat_id_aqui

# Base de datos (Railway usa SQLite por ahora)
DATABASE_URL=sqlite:///./football_alerts.db

# Configuración de monitoreo
FAVORITE_ODDS_THRESHOLD=1.35
MONITOR_MINUTE_START=55
MONITOR_MINUTE_END=62
UPDATE_INTERVAL_SECONDS=60

# Ligas a monitorear
LEAGUES_TO_MONITOR=39,140,135,78,61,239
```

**⚠️ IMPORTANTE:** 
- Reemplaza `TELEGRAM_BOT_TOKEN` con tu token real
- Reemplaza `TELEGRAM_CHAT_ID` con tu chat ID real

### Forma rápida (copiar desde tu .env):

```bash
# En tu terminal local
cat .env
```

Copia los valores y pégalos en Railway.

---

## 🔍 Paso 5: Verificar Deploy

1. Railway mostrará los logs de despliegue
2. Espera a ver: **"Application startup complete"**
3. Railway te dará una URL como: `https://tu-app.up.railway.app`

### Probar que funciona:

```bash
# Reemplaza con tu URL de Railway
curl https://tu-app.up.railway.app/

# Ver estadísticas
curl https://tu-app.up.railway.app/api/v1/admin/stats
```

O abre en el navegador:
- `https://tu-app.up.railway.app/docs` → Ver documentación API

---

## 📊 Paso 6: Configurar Dominio (Opcional)

Railway te da una URL automática, pero si quieres una personalizada:

1. Ve a **Settings** en Railway
2. **Domains** → **Generate Domain**
3. O conecta tu propio dominio personalizado

---

## 🔧 Paso 7: Monitorear tu App

### Ver Logs en tiempo real:

En Railway:
- Ve a tu proyecto
- Haz clic en **"View Logs"**
- Verás los logs en tiempo real

O desde CLI:
```bash
railway logs
```

### Ver métricas:

Railway muestra automáticamente:
- ✅ CPU usage
- ✅ RAM usage
- ✅ Network
- ✅ Requests

---

## 🎉 Paso 8: ¡Listo! Verificar funcionamiento

### Prueba 1: API funcionando

```bash
curl https://tu-app.up.railway.app/api/v1/admin/stats
```

Deberías ver:
```json
{
  "total_matches": 134,
  "monitored_matches": 1,
  "notifications_sent": 0,
  ...
}
```

### Prueba 2: Telegram funcionando

```bash
curl -X POST https://tu-app.up.railway.app/api/v1/admin/test-telegram
```

Deberías recibir un mensaje en Telegram.

### Prueba 3: Scheduler funcionando

Espera unos minutos y revisa los logs. Deberías ver:
```
🔄 Running: Monitor matches job...
```

---

## 💰 Costos

Railway ofrece:
- **Plan Hobby (Gratis)**: 
  - $5 USD de crédito gratis/mes
  - 500 horas de ejecución (~20 días)
  - Suficiente para tu proyecto

Si excedes el plan gratis:
- **Developer Plan**: $5 USD/mes
- Ejecución ilimitada

**Para tu caso:** El plan gratis es suficiente si solo corres esta app.

---

## 🔄 Actualizaciones Futuras

### Si usas GitHub:

1. Haz cambios en tu código local
2. Commit y push:
```bash
git add .
git commit -m "Descripción de cambios"
git push
```
3. ✅ Railway detecta el cambio y hace deploy automáticamente

### Si usas Railway CLI:

```bash
railway up
```

---

## 🛠️ Comandos Útiles

```bash
# Ver información del proyecto
railway status

# Abrir en el navegador
railway open

# Ver logs
railway logs

# Conectar a la base de datos
railway connect

# Reiniciar app
railway restart

# Eliminar proyecto
railway delete
```

---

## ⚠️ Troubleshooting

### "Application failed to start"

1. Revisa los logs en Railway
2. Verifica que todas las variables de entorno están configuradas
3. Asegúrate de que `requirements.txt` tiene todas las dependencias

### "Database error"

Railway usa sistema de archivos efímero. Cada vez que se reinicia, la BD SQLite se borra.

**Solución:** Railway ofrece PostgreSQL gratis:

1. En tu proyecto → **New** → **Database** → **PostgreSQL**
2. Railway te dará una `DATABASE_URL`
3. Copia y pega en las variables de entorno
4. Actualiza `app/core/config.py` para usar PostgreSQL

### "Telegram no responde"

Verifica:
```bash
curl -X POST https://tu-app.up.railway.app/api/v1/admin/test-telegram
```

Si falla:
1. Revisa `TELEGRAM_BOT_TOKEN`
2. Revisa `TELEGRAM_CHAT_ID`
3. Asegúrate de haber enviado mensaje al bot

### "No monitorea partidos"

1. Verifica en logs que el scheduler está corriendo
2. Revisa que hay partidos marcados para monitoreo:
```bash
curl https://tu-app.up.railway.app/api/v1/admin/stats
```

---

## 📱 App móvil de Railway

Railway tiene app móvil para:
- Ver logs en tiempo real
- Ver métricas
- Reiniciar servicios
- Recibir alertas

Descarga desde:
- [iOS App Store](https://apps.apple.com/app/railway/id1643269594)
- [Google Play Store](https://play.google.com/store/apps/details?id=app.railway.android)

---

## 🎯 Checklist Final

Antes de dar por terminado el deploy, verifica:

- [ ] App desplegada y corriendo en Railway
- [ ] Todas las variables de entorno configuradas
- [ ] URL de Railway funcionando
- [ ] Endpoint `/api/v1/admin/stats` responde
- [ ] Test de Telegram exitoso
- [ ] Scheduler aparece en los logs cada minuto
- [ ] Partidos con cuotas < 1.35 marcados para monitoreo

---

## 🆘 Soporte

Si tienes problemas:

1. **Logs de Railway:** Revisa los logs para ver errores específicos
2. **Documentación Railway:** [docs.railway.app](https://docs.railway.app)
3. **Discord de Railway:** [railway.app/discord](https://railway.app/discord)
4. **Verifica archivos:**
   - `Procfile` está presente
   - `requirements.txt` tiene todas las dependencias
   - Variables de entorno correctas

---

## ✅ Siguientes Pasos

Una vez desplegado:

1. **Monitorea los logs** las primeras horas
2. **Recibe tu primera alerta** cuando haya un partido que cumpla condiciones
3. **Ajusta configuración** si es necesario (umbral de cuotas, minutos, etc.)
4. **Disfruta** de las alertas automáticas 24/7 🎉

---

## 🔗 Enlaces Útiles

- **Railway Dashboard:** [railway.app/dashboard](https://railway.app/dashboard)
- **Docs Railway:** [docs.railway.app](https://docs.railway.app)
- **API-Football:** [api-football.com](https://api-football.com)
- **Telegram Bots:** [core.telegram.org/bots](https://core.telegram.org/bots)


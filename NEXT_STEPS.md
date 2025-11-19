# 🎯 Próximos Pasos - Configuración Inicial

## ✅ Lo que ya está listo

- ✅ Estructura del proyecto completa
- ✅ Código implementado
- ✅ Dependencias instaladas
- ✅ Base de datos configurada
- ✅ Scripts helper creados

## 🚀 Lo que debes hacer AHORA

### 1️⃣ Crear tu Bot de Telegram (5 minutos)

1. **Abre Telegram** en tu celular o computadora

2. **Busca** `@BotFather` (el bot oficial con ✓ azul)

3. **Ejecuta estos comandos:**
   ```
   /start
   /newbot
   ```

4. **Elige un nombre** para tu bot
   - Ejemplo: "Football Alerts Bot"

5. **Elige un username** (debe terminar en 'bot')
   - Ejemplo: `football_alerts_2024_bot`

6. **GUARDA el TOKEN** que te da BotFather
   - Se ve así: `6842736472:AAHfF8zX5JjK9Lm2nO3pQ4rS5tU6vW7xY8z`

7. **Busca tu bot** en Telegram y **envíale un mensaje**
   - Cualquier mensaje, ejemplo: "hola"

8. **Ejecuta este script** para obtener tu Chat ID:
   ```bash
   python get_telegram_chat_id.py TU_BOT_TOKEN_AQUI
   ```
   
9. **GUARDA el CHAT_ID** que te muestra el script

---

### 2️⃣ Obtener API Key de API-Football (5 minutos)

1. **Ve a** https://rapidapi.com/

2. **Crea una cuenta** (gratis)

3. **Busca** "API-Football"

4. **Suscríbete al plan FREE**
   - 100 requests/día gratis
   - No necesitas tarjeta de crédito

5. **Copia tu API Key**
   - La encontrarás en la sección "Code Snippets"
   - Aparece en `X-RapidAPI-Key`

---

### 3️⃣ Configurar el archivo .env (2 minutos)

Edita el archivo `.env` que ya existe:

```bash
# Opción 1: Con tu editor preferido
nano .env

# Opción 2: Con VS Code
code .env

# Opción 3: Con vim
vim .env
```

**Completa estos 3 valores:**

```bash
API_FOOTBALL_KEY=TU_API_KEY_DE_RAPIDAPI_AQUI
TELEGRAM_BOT_TOKEN=TU_BOT_TOKEN_AQUI
TELEGRAM_CHAT_ID=TU_CHAT_ID_AQUI
```

El resto ya tiene valores por defecto que funcionan.

---

### 4️⃣ Probar que todo funciona (3 minutos)

```bash
# 1. Activar entorno virtual
source .venv/bin/activate

# 2. Iniciar la aplicación
uvicorn app.main:app --reload
```

**Deberías ver algo como:**
```
🚀 Starting Football Alerts API...
📊 Initializing database...
🚀 Starting scheduler...
📅 Scheduled: Fetch fixtures daily at 8:00 AM
📊 Scheduled: Fetch odds every 2 hours
👁️  Scheduled: Monitor matches every 60 seconds
✅ Application started successfully!
```

**Probar Telegram:**
1. Abre tu navegador
2. Ve a: http://localhost:8000/api/v1/admin/test-telegram
3. Deberías recibir un mensaje de prueba en Telegram! 🎉

---

## 🎊 ¡Listo!

Si llegaste hasta aquí, tu sistema está **100% configurado y funcionando**.

### ¿Qué pasa ahora?

El sistema trabajará automáticamente:

- **8:00 AM**: Obtiene partidos del día
- **Cada 2 horas**: Obtiene cuotas
- **Cada minuto**: Monitorea partidos en vivo

**Recibirás alertas en Telegram cuando:**
- Un favorito (cuota < 1.35) esté perdiendo
- En los minutos 55-62 del partido

---

## 📚 Documentación Adicional

- **Guía Completa**: Lee `SETUP.md` para más detalles
- **README**: Lee `README.md` para información técnica
- **Endpoints**: http://localhost:8000/api/v1/docs

---

## 🆘 ¿Problemas?

### No recibo el mensaje de prueba de Telegram

1. Verifica que el `TELEGRAM_BOT_TOKEN` sea correcto
2. Verifica que el `TELEGRAM_CHAT_ID` sea correcto
3. Verifica que le enviaste al menos un mensaje al bot

### Error de API-Football

1. Verifica que el `API_FOOTBALL_KEY` sea correcto
2. Verifica que estés suscrito al plan en RapidAPI
3. Verifica que no hayas excedido 100 requests/día

---

## 🎯 Comandos Útiles

```bash
# Ver documentación interactiva
http://localhost:8000/api/v1/docs

# Ver estadísticas
http://localhost:8000/api/v1/admin/stats

# Ver partidos monitoreados
http://localhost:8000/api/v1/admin/matches?monitored_only=true

# Obtener partidos manualmente (si no quieres esperar a las 8 AM)
curl -X POST http://localhost:8000/api/v1/admin/fetch-fixtures

# Obtener cuotas manualmente
curl -X POST http://localhost:8000/api/v1/admin/fetch-odds
```

---

## ✨ ¡Disfruta tu sistema de alertas!

Ahora solo mantén la aplicación corriendo y recibirás alertas automáticas. ⚽🚨


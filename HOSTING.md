# 🖥️ Guía de Hosting - Football Alerts API

Esta guía te explica cómo mantener tu aplicación corriendo 24/7.

---

## 🏠 Hosting Local (Tu Computadora)

### ⚠️ Limitaciones

Cuando usas tu computadora como servidor:
- ❌ Si entra en **modo reposo**, la app se pausa
- ❌ Si **apagas** la computadora, la app se detiene
- ❌ Si pierdes **conexión a internet**, no funcionará
- ✅ **Gratis** y sin configuraciones complejas

---

## 🔥 Opción 1: Evitar Modo Reposo (Recomendado para Mac)

### Usar el script automático:

```bash
cd /Users/stialvarez/Documents/Proyectos/fastapi-project
source .venv/bin/activate
./keep_awake.sh
```

Esto hace:
- ✅ Inicia FastAPI
- ✅ Mantiene el Mac despierto mientras corre
- ✅ Si cierras la terminal, la app se detiene (seguro)

### Alternativa manual - `caffeinate`:

```bash
# Evitar reposo mientras un comando corre
caffeinate -d -i -m -s uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Flags de caffeinate:**
- `-d` = Evita que la pantalla se apague
- `-i` = Evita reposo por inactividad
- `-m` = Evita reposo cuando cierra la tapa
- `-s` = Evita que el sistema duerma

---

## 🌐 Opción 2: Servidor en la Nube (24/7 Real)

Si quieres que funcione **siempre**, aunque tu computadora esté apagada:

### A) **Railway.app** (Recomendado - Fácil)
- 💰 **Gratis**: 500 horas/mes (~20 días)
- ⚡ Deploy en 5 minutos
- 🔧 Configuración automática

**Pasos:**
1. Crear cuenta en [railway.app](https://railway.app)
2. Conectar este repositorio Git
3. Railway detecta FastAPI automáticamente
4. Agregar variables de entorno (.env)
5. ✅ ¡Listo!

### B) **Fly.io** (Más control)
- 💰 **Gratis**: 3 VMs pequeñas
- 🐳 Requiere Docker
- 🌍 Deploy global

### C) **PythonAnywhere** (Más simple)
- 💰 **Gratis**: 1 app web
- ⚠️ Limitaciones en tareas programadas
- 📚 Muy documentado

### D) **Oracle Cloud** (Más potente)
- 💰 **Gratis**: Siempre (2 VMs)
- 🔧 Requiere más configuración
- 💪 4GB RAM, 200GB storage

---

## 🚀 Recomendación según tu caso:

### Para probar/desarrollo (1-2 semanas):
```bash
./keep_awake.sh
```
Mantén tu Mac encendido y despierto.

### Para producción (24/7):
**Railway.app** es la mejor opción:
- Fácil de configurar
- Gratis (suficiente para tu caso)
- Se mantiene corriendo siempre
- Reinicio automático si falla

---

## 📝 Configuración de macOS para máxima disponibilidad

Si decides usar tu Mac como servidor, configura:

### 1. Evitar reposo automático:

```bash
# Ver configuración actual
pmset -g

# Evitar reposo cuando está conectado a corriente
sudo pmset -c sleep 0
sudo pmset -c displaysleep 10

# Evitar reposo con batería (laptop)
sudo pmset -b sleep 0
```

### 2. Iniciar automáticamente al arrancar:

Crea un Launch Agent (servicio de macOS):

```bash
# Crear archivo de servicio
sudo tee /Library/LaunchDaemons/com.football-alerts.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.football-alerts</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>/Users/stialvarez/Documents/Proyectos/fastapi-project/keep_awake.sh</string>
    </array>
    
    <key>RunAtLoad</key>
    <true/>
    
    <key>KeepAlive</key>
    <true/>
    
    <key>WorkingDirectory</key>
    <string>/Users/stialvarez/Documents/Proyectos/fastapi-project</string>
    
    <key>StandardOutPath</key>
    <string>/Users/stialvarez/Documents/Proyectos/fastapi-project/logs/output.log</string>
    
    <key>StandardErrorPath</key>
    <string>/Users/stialvarez/Documents/Proyectos/fastapi-project/logs/error.log</string>
</dict>
</plist>
EOF

# Crear directorio de logs
mkdir -p /Users/stialvarez/Documents/Proyectos/fastapi-project/logs

# Activar servicio
sudo launchctl load /Library/LaunchDaemons/com.football-alerts.plist

# Iniciar servicio
sudo launchctl start com.football-alerts
```

**Para detener:**
```bash
sudo launchctl stop com.football-alerts
sudo launchctl unload /Library/LaunchDaemons/com.football-alerts.plist
```

---

## 🔍 Monitorear que siga corriendo

### Ver si está corriendo:

```bash
# Ver proceso
ps aux | grep uvicorn

# Ver logs (si configuraste el servicio)
tail -f /Users/stialvarez/Documents/Proyectos/fastapi-project/logs/output.log

# Probar endpoint
curl http://localhost:8000/api/v1/admin/stats
```

### Script de monitoreo:

```bash
# Crear script de verificación
cat > check_status.sh << 'EOF'
#!/bin/bash
if curl -s http://localhost:8000/api/v1/admin/stats > /dev/null; then
    echo "✅ API corriendo correctamente"
else
    echo "❌ API NO está respondiendo"
fi
EOF

chmod +x check_status.sh
```

---

## 💰 Comparación de costos:

| Opción | Costo Mensual | Disponibilidad | Configuración |
|--------|---------------|----------------|---------------|
| **Tu Mac** | $0 (electricidad) | Mientras esté encendido | Simple |
| **Railway** | $0 - $5 | 24/7 | Muy fácil |
| **Fly.io** | $0 - $3 | 24/7 | Media |
| **Oracle Cloud** | $0 | 24/7 | Compleja |
| **PythonAnywhere** | $0 - $5 | 24/7 | Fácil |

---

## ⚡ Inicio Rápido Recomendado:

### Para hoy (prueba):
```bash
./keep_awake.sh
```

### Para esta semana (si funciona bien):
Configúrate en **Railway.app** - Toma 10 minutos y es gratis.

---

## 🆘 Problemas Comunes:

### "La app se detuvo después de cerrar la terminal"
- ✅ Usa `./keep_awake.sh` o configura como servicio

### "El Mac se durmió y perdí alertas"
- ✅ Usa `caffeinate` o configura `pmset`

### "Quiero que funcione aunque apague el Mac"
- ✅ Necesitas hosting en la nube (Railway recomendado)

### "¿Cómo veo los logs?"
```bash
# Si usas el servicio:
tail -f logs/output.log

# Si usas terminal directamente:
# Los logs aparecen en la misma terminal
```

---

## 📞 Contacto / Dudas

Si tienes problemas:
1. Verifica que la app esté corriendo: `curl localhost:8000/api/v1/admin/stats`
2. Revisa los logs
3. Reinicia: `./keep_awake.sh`


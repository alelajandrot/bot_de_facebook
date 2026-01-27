# 📱 Modo Móvil (ADB) - Guía de Configuración

## Descripción
El Modo Móvil permite usar celulares Android físicos como proxies rotativos para el bot. Cada celular puede renovar su IP pública activando/desactivando el Modo Avión.

## Requisitos Previos

1. **Android Debug Bridge (ADB)**
   - Descarga desde: https://developer.android.com/studio/releases/platform-tools
   - Agrega ADB al PATH de tu sistema
   - Verifica instalación: `adb version`

2. **Celulares Android**
   - Habilitar "Opciones de Desarrollador"
   - Activar "Depuración USB"
   - Conectar por USB

3. **App de Proxy Local en cada celular**
   - Ejemplo: ProxyDroid, Drony, o similar
   - Configurar proxy local (ej: 192.168.1.10:8080)

## Configuración de Dispositivos

### Opción 1: Archivo JSON (Recomendado)

Crea un archivo `mobile_devices.json` en la carpeta `facebook_bot/`:

```json
{
    "R58M123456": "192.168.1.10:8080",
    "emulator-5554": "192.168.1.11:8080"
}
```

- **Clave**: Device ID de ADB (obtener con `adb devices`)
- **Valor**: IP:Puerto del proxy local del celular

### Opción 2: Código Python

Edita `mobile_manager.py` y modifica el diccionario `DEVICE_PROXY_MAP`:

```python
DEVICE_PROXY_MAP = {
    "R58M123456": "192.168.1.10:8080",
    "emulator-5554": "192.168.1.11:8080",
}
```

## Uso

1. **Conectar celulares por USB**
2. **Verificar conexión**: `adb devices`
3. **Activar "Modo Móvil (ADB)"** en la interfaz del bot
4. **Ejecutar tareas normalmente**

## Funcionamiento

Cuando el Modo Móvil está activo:

1. Antes de cada tarea, el bot:
   - Adquiere un celular libre (bloqueo thread-safe)
   - Activa Modo Avión → Espera → Desactiva Modo Avión
   - Espera conexión a internet
   - Asigna el proxy del celular al navegador

2. Durante la tarea:
   - El navegador usa la IP del celular

3. Después de la tarea:
   - Libera el celular para que otro hilo lo use

## Notas Importantes

- **Thread-Safe**: Los dispositivos se bloquean automáticamente para evitar conflictos
- **Rotación de IP**: Cada tarea renueva la IP del dispositivo usado
- **Fallback**: Si no hay dispositivos disponibles, usa la red de PC
- **Timeout**: Los hilos esperan hasta 60 segundos por un dispositivo libre

## Solución de Problemas

### "ADB no está disponible"
- Instala Android SDK Platform Tools
- Agrega ADB al PATH del sistema
- Reinicia la terminal/IDE

### "No hay dispositivos configurados"
- Verifica que los celulares estén conectados: `adb devices`
- Configura los dispositivos en `mobile_devices.json`
- Asegúrate de que el Device ID coincida exactamente

### "Error renovando IP"
- Verifica que el celular tenga permisos de administrador
- Algunos celulares requieren permisos root para Modo Avión
- Prueba manualmente: `adb shell settings put global airplane_mode_on 1`

### "Dispositivo no liberado"
- Los dispositivos se liberan automáticamente al finalizar la tarea
- Si hay un error, reinicia el bot

## Permisos Requeridos en Android

Para que funcione el Modo Avión vía ADB, el celular necesita:
- Opciones de Desarrollador activadas
- Depuración USB activada
- (Opcional) Permisos root para mayor compatibilidad


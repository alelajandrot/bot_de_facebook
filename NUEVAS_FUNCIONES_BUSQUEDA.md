# 🔍 Nueva Funcionalidad: Búsqueda Personalizada de Personas

## Descripción General

Se ha agregado una nueva funcionalidad al apartado de **Calentamiento de Cuentas** que permite:

1. **Buscar personas específicas por nombre o usuario**
2. **Enviar solicitudes de amistad automáticamente a esas personas**

Esto complementa la búsqueda anterior que solo enviaba solicitudes a sugerencias aleatorias del feed.

## Cambios Realizados

### 1. Interfaz de Usuario (main.py)

Se agregó una nueva sección en la pestaña **"🔥 Calentamiento"** llamada **"🔍 Búsqueda Personalizada"** con:

- **Campo de entrada**: Para escribir el nombre/usuario de la persona a buscar
- **Slider de límite**: Para establecer la cantidad máxima de solicitudes a enviar (1-30)
- **Botón de búsqueda**: "✅ Buscar y Enviar Solicitudes a Personas"

```
┌─ 🔍 Búsqueda Personalizada ────────────────────┐
│ Nombre/Usuario: [_____________________]         │
│ Solicitudes: [======●───────────────] 5         │
│ [✅ Buscar y Enviar Solicitudes a Personas]    │
└──────────────────────────────────────────────────┘
```

### 2. Nueva Función en bot_logic.py

Se agregó el método estático `search_and_add_friends()` que:

- Abre Facebook y accede a la barra de búsqueda
- Escribe el término de búsqueda (nombre/usuario)
- Localiza los botones "Agregar a amigos" en los resultados
- Hace clic automáticamente en los botones hasta alcanzar el límite especificado
- Registra cada solicitud enviada en el log
- Captura screenshots del proceso

### 3. Manejador de Eventos (main.py)

Se agregó el método `trigger_search_and_add()` que:

- Valida que se ingresó un término de búsqueda
- Obtiene la cuenta y plataforma seleccionadas
- Verifica la cuenta en la base de datos
- Ejecuta la búsqueda en modo single o batch según la configuración

## Cómo Usar

### Paso 1: Seleccionar Plataforma y Cuenta
1. Ve a la pestaña **"🔥 Calentamiento"**
2. Selecciona la plataforma (Facebook, Instagram, etc.)
3. Selecciona la cuenta con la que deseas realizar la búsqueda

### Paso 2: Configurar Búsqueda
1. En la sección **"🔍 Búsqueda Personalizada"**:
   - Escribe el nombre/usuario de la persona a buscar (ej: "Juan Pérez")
   - Ajusta el slider "Solicitudes" para indicar cuántas solicitudes enviar (máximo 30)

### Paso 3: Ejecutar
1. Haz clic en **"✅ Buscar y Enviar Solicitudes a Personas"**
2. El bot abrirá Facebook, buscará la persona y enviará solicitudes de amistad
3. Puedes ver el progreso en la consola de logs

## Ejemplo de Ejecución

```
🔍 Buscando personas: 'Juan Pérez' (santiago_lozano, máx 5)
✅ Solicitud enviada a 'Juan Pérez' (1/5)
✅ Solicitud enviada a 'Juan Pérez' (2/5)
✅ Solicitud enviada a 'Juan Pérez' (3/5)
✅ Búsqueda completada: 3/5 solicitudes enviadas para 'Juan Pérez' (santiago_lozano)
```

## Características

✅ **Búsqueda automática** en Facebook por nombre/usuario  
✅ **Envío automático de solicitudes** al hacer clic en "Agregar a amigos"  
✅ **Control de límite** de solicitudes (1-30)  
✅ **Validaciones** de cuenta y plataforma  
✅ **Comportamiento humano** simulado (delays, movimiento de mouse)  
✅ **Registro detallado** de todas las acciones  
✅ **Screenshots** del proceso  
✅ **Compatible** con modo single y batch  

## Compatibilidad

| Plataforma | Estado |
|-----------|--------|
| Facebook | ✅ Completamente soportada |
| Instagram | 🚧 Estructura básica (mejoras pendientes) |
| TikTok | ❌ No implementada |
| YouTube | ❌ No implementada |
| Twitter | ❌ No implementada |

## Notas Técnicas

- La función intenta múltiples selectores CSS para encontrar la barra de búsqueda
- Utiliza clicks forzados con fallback a movimiento manual de mouse
- Implementa esperas inteligentes entre acciones (1-3.5 segundos)
- Captura screenshots con el término de búsqueda en el nombre

## Troubleshooting

**Error: "No se pudo encontrar la barra de búsqueda"**
- Facebook puede haber cambiado la estructura de su HTML
- Intenta manualmente buscar una persona y verifica los selectores en el navegador

**No se envían solicitudes**
- Verifica que la persona existe en Facebook
- Comprueba que la cuenta de la cual buscas no es amiga aún de esa persona
- Mira los screenshots en los logs para ver qué sucedió

**Demasiados errores de clic**
- Aumenta los delays en las configuraciones si el servidor está congestionado
- Reduce el número máximo de solicitudes

## Archivos Modificados

- [facebook_bot/main.py](facebook_bot/main.py) - Interfaz y manejadores de eventos
- [facebook_bot/bot_logic.py](facebook_bot/bot_logic.py) - Función de búsqueda y envío

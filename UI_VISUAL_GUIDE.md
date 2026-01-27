# 🎯 SocialBotFarm - Guía Visual del Rediseño

## Vista General de la Interfaz

### Estructura Principal

```
┌─────────────────────────────────────────────────────────────────┐
│  SIDEBAR (Izq, 320px)          │  MAIN CONTENT (Derecha, Flex)  │
│                                │                                │
│  📊 Configuración              │  [Tabs de Plataformas]        │
│  • Modo Proxy ☑               │                                │
│  • Modo Móvil ☐               │  ┌─────────────────────────────┐│
│  • Delays (1-30s)             │  │ Facebook │ Instagram │ ...   ││
│  • Max Intentos (1-5)         │  │                             ││
│  ─────────────────────        │  │ 👤 Cuenta: [dropdown] ▼     ││
│  🔑 Login Manual               │  │                             ││
│  [Botón Azul Ciánico]         │  │ [Tarjetas de acciones]      ││
│  ─────────────────────        │  │ • URL del Post              ││
│  📸 Última Actividad          │  │ • Reacciones               ││
│  [Imagen Preview]             │  │ • Comentarios              ││
│                                │  └─────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
│ 📋 Consola de Actividad                                          │
│ [Output de logs con colores]                                    │
└─────────────────────────────────────────────────────────────────┘
```

## Esquema de Colores en Acción

### Sidebar (Zona de Configuración)

**Header:**
- Fondo: `#1e3a5f` (Blue Card)
- Texto: `#60a5fa` (Light Blue)
- Border: `#1e40af` (Dark Blue)

**Secciones:**
- Checkbox labels: `#60a5fa`
- Sliders: 
  - Track: `#1e40af`
  - Progress: `#0284c7` (Cyan)
  - Handle: `#60a5fa`

**Botón Login Manual:**
- Color: `#f97316` (Orange)
- Hover: Más oscuro
- Icon: 🔑

**Preview Box:**
- Fondo Card: `#1e3a5f`
- Fondo Imagen: `#0f172a` (Pure Black)
- Label: `#60a5fa` (Light Blue)

### Área Principal (Tabs)

**Selector de Pestaña:**
- Inactive: Gris
- Active: `#0284c7` (Cyan Bright)
- Text: `#60a5fa` (Light Blue)

**Header de Plataforma:**
- Fondo: `#1e3a5f` (Blue Card)
- Border: `#1e40af` (Dark Blue)
- Label: `#60a5fa` "👤 Cuenta:"
- ComboBox:
  - Fondo: `#0f172a`
  - Button: `#1e40af`
  - Hover Button: `#0284c7`

**Tarjetas de Acción:**

Cada tarjeta tiene:
```
┌──────────────────────────┐
│ 🔗 URL del Post          │ ← Título en #60a5fa
├──────────────────────────┤
│ [Entry field...]         │ ← Fondo #0f172a, border #1e40af
└──────────────────────────┘
```

**Botones de Acción:**
- Fondo: `#0284c7` (Cyan)
- Hover: `#1e40af` (Darker Blue)
- Text: Blanco
- Corner Radius: 8px

### Sección de Consola

**Frame:**
- Fondo: `#1e3a5f` (Blue Card)
- Border: `#1e40af` (1px)

**Header:**
- Texto: `#60a5fa` "📋 Consola de Actividad"

**Textbox:**
- Fondo: `#0f172a` (Deep Black)
- Border: `#1e40af`
- Texto: `#e5e7eb` (Gray Light)

**Logs (Coloreados):**
```
[09:45:23] [INFO] Iniciando sesión...         → #60a5fa
[09:45:24] [SUCCESS] Login completado        → #10b981
[09:45:25] [ERROR] Error en proxy            → #ef4444
[09:45:26] [WARN] Reintentando...            → #f97316
[09:45:27] [DEBUG] Datos cargados            → #8b5cf6
```

## Experiencia del Usuario

### Sensación General
- 🎯 **Profesional**: Colores corporativos azules
- 🌙 **Dark Mode**: Fácil a la vista, moderno
- ⚡ **Responsivo**: Hover states claros, feedback visual
- 🎨 **Consistente**: Mismo patrón en todas las secciones

### Interactividad

**Botones:**
- Estado normal: Cyan azul `#0284c7`
- Hover: Border oscuro `#1e40af`
- Presionado: Más oscuro aún
- Deshabilitado: Gris `#6b7280`

**Inputs:**
- Focus: Border más visible `#60a5fa`
- Placeholder: Gris tenue `#6b7280`
- Filled: Texto blanco `#e5e7eb`

**ComboBox:**
- Dropdown abierto: Button color `#0284c7`
- Opciones: Mismo esquema

## Tabs Especiales

### 🏋️ Calentamiento (Warmup)
```
┌─────────────────────────────────────┐
│ 🏋️ RUTINA DE CALENTAMIENTO          │
│ Navegación automática...            │
├─────────────────────────────────────┤
│ 📱 Plataforma: [Facebook ▼]        │
│ 👤 Cuenta: [user1 ▼]              │
│ ⏱️ Duración: [====●====] 5 min    │
│                                     │
│ [▶️ INICIAR CALENTAMIENTO]         │
│                                     │
│ ☑ Enviar solicitudes de amistad   │
│ ☑ Comentar en posts               │
└─────────────────────────────────────┘
```

### ⚙ Gestor de Cuentas
```
┌─────────────────────────────────────┐
│ ➕ Agregar Nueva Cuenta              │
├─────────────────────────────────────┤
│ Alias: [_______________]           │
│ Plataforma: [Facebook ▼]           │
│ Usuario: [_______________]         │
│ Contraseña: [•••••••]             │
│ Proxy: [_______________]           │
│                                     │
│ [💾 Guardar] [✏️ Editar] [🗑️ Eliminar] │
│                                     │
│ 📥 Importar Perfil Local           │
│ [Select Profile ▼]                 │
│ [📥 Vincular Carpeta]              │
└─────────────────────────────────────┘
```

### 📊 Estado de Cuentas
```
┌─────────────────────────────────────────────────────────┐
│ 📊 ESTADO DE CUENTAS                                    │
│ Visualiza qué cuentas tienen cookies cargadas          │
├─────────────────────────────────────────────────────────┤
│ [Filtros]                                              │
│ 🔍 Filtrar: [_______] Plataforma: [Todas ▼] [✨ Limpiar] │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ ✅ fb_user1 (facebook) - Con cookies                   │
│ ❌ ig_user2 (instagram) - Sin cookies                  │
│ ✅ tk_user3 (tiktok) - Con cookies                     │
│                                                         │
├─────────────────────────────────────────────────────────┤
│ [🔄 Refrescar Estado]  [💾 Sincronizar BD]            │
└─────────────────────────────────────────────────────────┘
```

## Tipografía en Uso

| Elemento | Font | Size | Weight | Color |
|----------|------|------|--------|-------|
| Título Principal | Segoe UI | 18 | Bold | #60a5fa |
| Subtítulo | Segoe UI | 14 | Bold | #60a5fa |
| Card Title | Segoe UI | 13 | Bold | #60a5fa |
| Label | Segoe UI | 12 | Bold | #60a5fa |
| Body Text | Segoe UI | 11 | Normal | #e5e7eb |
| Helper Text | Segoe UI | 10 | Normal | #9ca3af |
| Console | Consolas | 10 | Normal | #e5e7eb |

## Respuesta Visual

### Elementos Interactivos

**Botones:**
```
Normal:  [Blue Cyan #0284c7]
Hover:   [Dark Blue #1e40af]
Pressed: [#1e3a5f]
Focus:   [Outline en #60a5fa]
```

**Entry Fields:**
```
Normal:  [Border #1e40af, fondo #0f172a]
Hover:   [Border más visible]
Focus:   [Border #60a5fa, cursor visible]
Filled:  [Texto #e5e7eb]
```

**ComboBox:**
```
Normal:  [Button #1e40af]
Hover:   [Button #0284c7]
Abierto: [Dropdown con opciones]
```

## Consistencia Visual

✅ **Bordes**: Todos los cards tienen `border_width=1, border_color="#1e40af"`
✅ **Radio**: Cards `corner_radius=12`, Botones `corner_radius=8`
✅ **Espaciado**: Padding inner 15px, outer 20px
✅ **Tipografía**: Segoe UI en toda la app
✅ **Feedback**: Hover states en cada elemento interactivo
✅ **Accesibilidad**: Contraste suficiente entre colores

## Transiciones (Futuro)

Cuando el usuario interactúa, podría haber:
- Cambio suave de color en botones (0.2s)
- Expansión de cards al hover (animate)
- Fade in de elementos (scroll en consola)

---

**Última actualización**: 2024
**Aesthetic**: Modern Dark Mode Professional
**Framework**: CustomTkinter + Python 3.x

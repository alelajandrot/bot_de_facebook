# 🔧 Guía Técnica de Mantenimiento - Nuevo Diseño UI

## Cambios Realizados en main.py

### 1. Cambio de Tema Global

**Antes:**
```python
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")
```

**Ahora:**
```python
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")
```

### 2. Sidebar Completamente Rediseñado

**Cambios clave:**
- Width: 300 → 320
- Todos los frames usan: `corner_radius=12`, `border_width=1`, `border_color="#1e40af"`
- Headers: `fg_color="#1e3a5f"`, `text_color="#60a5fa"`
- Sliders: `fg_color="#1e40af"`, `progress_color="#0284c7"`
- Labels: `text_color="#60a5fa"`

### 3. TabView Personalizado

```python
self.tabs = ctk.CTkTabview(self, 
    command=self.on_tab_change,
    fg_color="transparent",
    border_width=0,
    segmented_button_fg_color="#1e3a5f",
    segmented_button_selected_color="#0284c7",
    segmented_button_selected_hover_color="#0284c7",
    text_color="#60a5fa"
)
```

### 4. Patrón Standard para Cards

Todas las tarjetas de contenido siguen este patrón:

```python
# Card principal
card = ctk.CTkFrame(parent, 
    corner_radius=12, 
    fg_color="#1e3a5f",
    border_width=1,
    border_color="#1e40af"
)
card.pack(fill="x", padx=15, pady=10)

# Título en la card
ctk.CTkLabel(card, 
    text="📊 Título",
    font=("Segoe UI", 13, "bold"),
    text_color="#60a5fa"  # Azul claro
).pack(anchor="w", padx=15, pady=(12, 8))

# Content (entrada, combobox, etc)
entry = ctk.CTkEntry(card,
    placeholder_text="Ej: valor",
    font=("Segoe UI", 11),
    height=35,
    fg_color="#0f172a",          # Negro puro
    border_color="#1e40af",      # Azul oscuro
    border_width=1,
    text_color="#e5e7eb",        # Gris claro
    placeholder_text_color="#6b7280"  # Gris medio
)
entry.pack(fill="x", padx=15, pady=(0, 12))

# Botón en la card
ctk.CTkButton(card,
    text="🔘 Acción",
    fg_color="#0284c7",          # Cyan
    hover_color="#1e40af",       # Azul oscuro
    text_color="#ffffff",
    font=("Segoe UI", 12, "bold"),
    corner_radius=8,
    height=40
).pack(fill="x", padx=15, pady=(10, 15))
```

## Paleta de Colores (Variables Globales)

Para mantener la consistencia, si necesitas editar la app en el futuro, usa estos valores:

```python
# Colores principales
BG_DARK = "#0f172a"        # Fondo oscuro (inputs, textbox)
BG_CARD = "#1e3a5f"        # Fondo de cards/frames
BORDER_COLOR = "#1e40af"   # Borders
ACCENT = "#60a5fa"         # Texto azul claro (títulos)
PRIMARY = "#0284c7"        # Botones primarios
HOVER = "#1e40af"          # Hover de botones
TEXT = "#e5e7eb"           # Texto normal
TEXT_SEC = "#9ca3af"       # Texto secundario
TEXT_PLACEHOLDER = "#6b7280"  # Placeholder

# Estados
SUCCESS = "#10b981"        # Verde para éxito
ERROR = "#ef4444"          # Rojo para errores
WARNING = "#f97316"        # Naranja para advertencias
```

## Tipos de Componentes

### Entry Field
```python
ctk.CTkEntry(parent,
    placeholder_text="...",
    height=35,
    fg_color=BG_DARK,
    border_color=BORDER_COLOR,
    border_width=1,
    text_color=TEXT,
    placeholder_text_color=TEXT_PLACEHOLDER
)
```

### ComboBox
```python
ctk.CTkComboBox(parent,
    values=["option1", "option2"],
    height=35,
    fg_color=BG_DARK,
    border_color=BORDER_COLOR,
    border_width=1,
    button_color=BORDER_COLOR,
    button_hover_color=PRIMARY,
    text_color=TEXT
)
```

### Button (Principal)
```python
ctk.CTkButton(parent,
    text="Acción",
    fg_color=PRIMARY,
    hover_color=HOVER,
    text_color="#ffffff",
    corner_radius=8,
    height=40,
    font=("Segoe UI", 12, "bold")
)
```

### Button (Variantes)
```python
# Success
ctk.CTkButton(parent, fg_color=SUCCESS, hover_color="#059669")

# Error
ctk.CTkButton(parent, fg_color=ERROR, hover_color="#dc2626")

# Warning
ctk.CTkButton(parent, fg_color=WARNING, hover_color="#cc7000")
```

### Label (Título)
```python
ctk.CTkLabel(parent,
    text="Titulo",
    font=("Segoe UI", 13, "bold"),
    text_color=ACCENT
)
```

### Label (Secundario)
```python
ctk.CTkLabel(parent,
    text="Descripción",
    font=("Segoe UI", 10),
    text_color=TEXT_SEC
)
```

### Textbox (Console)
```python
ctk.CTkTextbox(parent,
    height=140,
    font=("Consolas", 10),
    corner_radius=8,
    fg_color=BG_DARK,
    border_width=1,
    border_color=BORDER_COLOR,
    text_color=TEXT
)
```

### Slider
```python
ctk.CTkSlider(parent,
    from_=1, to=20,
    fg_color=BORDER_COLOR,        # Track
    progress_color=PRIMARY,        # Progress
    button_color=ACCENT,
    button_hover_color=PRIMARY
)
```

## Estructura de Frames

### Card Frame
```python
card = ctk.CTkFrame(parent, 
    corner_radius=12, 
    fg_color=BG_CARD,
    border_width=1,
    border_color=BORDER_COLOR
)
```

### Transparent Frame (para layouts)
```python
layout = ctk.CTkFrame(parent, fg_color="transparent")
```

## Espaciado Estándar

```python
# Dentro de cards
padx_inner = 15
pady_inner = 12

# Entre secciones principales
padx_outer = 20
pady_outer = 15

# Entre elementos
pad_small = 5
pad_medium = 10
```

## Reglas de Consistencia

✅ **Colores:**
- Todos los cards: `fg_color="#1e3a5f"`, `border_color="#1e40af"`
- Todos los inputs: `fg_color="#0f172a"`, `border_color="#1e40af"`
- Todos los botones primarios: `fg_color="#0284c7"`
- Todos los títulos: `text_color="#60a5fa"`

✅ **Corner Radius:**
- Cards: `corner_radius=12`
- Botones: `corner_radius=8`
- Inputs: `corner_radius=8` (default)

✅ **Heights:**
- Botones: `height=40` (normal), `height=50` (grandes)
- Inputs: `height=35`
- Sliders: automático

✅ **Fonts:**
- Títulos: `("Segoe UI", 13, "bold")` o mayor
- Normal: `("Segoe UI", 11)`
- Small: `("Segoe UI", 10)`
- Console: `("Consolas", 10)` para monospace

✅ **Borders:**
- Todos `border_width=1`
- Color: `#1e40af`

## Cómo Editar Sin Romper el Diseño

### Si necesitas agregar una nueva sección:

1. Crea un frame con:
```python
section = ctk.CTkFrame(parent,
    corner_radius=12,
    fg_color="#1e3a5f",
    border_width=1,
    border_color="#1e40af"
)
```

2. Agrega un label en azul claro:
```python
ctk.CTkLabel(section,
    text="📌 Nueva Sección",
    font=("Segoe UI", 13, "bold"),
    text_color="#60a5fa"
).pack(anchor="w", padx=15, pady=(12, 8))
```

3. Usa componentes estándar (Entry, ComboBox, Button) con colores del scheme

### Si necesitas cambiar un botón:

Usa:
- `fg_color="#0284c7"` para primarios
- `fg_color="#10b981"` para éxito
- `fg_color="#ef4444"` para errores
- Siempre: `hover_color="#1e40af"`
- Siempre: `corner_radius=8`

### Si necesitas agregar un nuevo tab:

```python
new_tab = self.tabs.add("📌 Nuevo Tab")
# Aplicar mismo pattern que otras plataformas
```

## Console (Logging)

El frame de consola está actualizado y soporta colores por tipo:

```python
self.log("Mensaje informativo", "INFO")      # #60a5fa
self.log("Operación exitosa", "SUCCESS")     # #10b981
self.log("Algo falló", "ERROR")              # #ef4444
self.log("Precaución", "WARN")               # #f97316
self.log("Detalles técnicos", "DEBUG")       # #8b5cf6
```

## Testing Visual

Para verificar que el diseño se ve consistente:

1. Abre la app
2. Revisa cada tab: Facebook, Instagram, TikTok, YouTube, Twitter
3. Verifica colores:
   - Cards: Azul medio `#1e3a5f`
   - Borders: Azul oscuro `#1e40af`
   - Títulos: Azul claro `#60a5fa`
   - Botones: Cyan `#0284c7`
   - Inputs: Negro puro `#0f172a`
4. Verifica spacing: Uniforme en todas las secciones
5. Verifica hover states: Botones cambian a azul oscuro `#1e40af`

## Archivos de Referencia

- `COLOR_PALETTE.md` - Paleta de colores detallada
- `UI_VISUAL_GUIDE.md` - Guía visual con mockups
- `UI_REDESIGN_SUMMARY.md` - Resumen de cambios

---

**Versión**: 1.0
**Fecha**: 2024
**Mantenedor**: SocialBotFarm Team

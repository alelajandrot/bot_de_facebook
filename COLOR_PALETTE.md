# 🎨 Color Palette Reference - SocialBotFarm

## Paleta Principal

```
┌─────────────────────────────────────────────────────────┐
│                  DARK MODE COLOR SYSTEM                 │
└─────────────────────────────────────────────────────────┘
```

### Colores Base

| Nombre | Hex | RGB | Uso |
|--------|-----|-----|-----|
| **Deep Black-Blue** | `#0f172a` | 15, 23, 42 | Fondo principal, textbox background |
| **Medium Blue** | `#1e3a5f` | 30, 58, 95 | Card backgrounds, section frames |
| **Dark Blue** | `#1e40af` | 30, 64, 175 | Borders, dividers, button borders |
| **Light Blue** | `#60a5fa` | 96, 165, 250 | Text headings, labels, accents |
| **Cyan/Bright Blue** | `#0284c7` | 2, 132, 199 | Buttons, hover states, progress |
| **Gray Light** | `#e5e7eb` | 229, 231, 235 | Body text, text color |
| **Gray Medium** | `#9ca3af` | 156, 163, 175 | Secondary text, helpers |
| **Gray Dark** | `#6b7280` | 107, 114, 128 | Placeholder text |

### Estados de Botones

| Estado | Color | Uso |
|--------|-------|-----|
| **Normal** | `#0284c7` | Estado por defecto |
| **Hover** | `#1e40af` | Al pasar mouse |
| **Press** | `#1e3a5f` | Al hacer clic |
| **Disabled** | `#6b7280` | Deshabilitado |

### Estados Específicos

| Tipo | Color | Hex |
|------|-------|-----|
| **Success/Save** | Verde | `#10b981` |
| **Error/Delete** | Rojo | `#ef4444` |
| **Warning** | Naranja | `#f97316` |
| **Info** | Azul | `#0284c7` |

## Aplicaciones Específicas

### Entry Fields
```python
entry = ctk.CTkEntry(
    fg_color="#0f172a",           # Fondo oscuro
    border_color="#1e40af",        # Border azul
    border_width=1,
    text_color="#e5e7eb",          # Texto claro
    placeholder_text_color="#6b7280" # Placeholder gris
)
```

### ComboBox
```python
combo = ctk.CTkComboBox(
    fg_color="#0f172a",
    border_color="#1e40af",
    button_color="#1e40af",         # Botón del combo
    button_hover_color="#0284c7",   # Hover del botón
    text_color="#e5e7eb"
)
```

### Frame/Card
```python
card = ctk.CTkFrame(
    fg_color="#1e3a5f",             # Fondo azul medio
    border_color="#1e40af",         # Border oscuro
    border_width=1,
    corner_radius=12                # Radio de esquinas
)
```

### Label
```python
label = ctk.CTkLabel(
    text="Título",
    font=("Segoe UI", 13, "bold"),
    text_color="#60a5fa"            # Texto azul claro
)
label_secondary = ctk.CTkLabel(
    text="Descripción",
    font=("Segoe UI", 10),
    text_color="#9ca3af"            # Texto gris
)
```

### Button
```python
button = ctk.CTkButton(
    text="Acción",
    fg_color="#0284c7",             # Fondo cyan
    hover_color="#1e40af",          # Hover más oscuro
    text_color="white",
    corner_radius=8,
    font=("Segoe UI", 12, "bold")
)
```

### Slider
```python
slider = ctk.CTkSlider(
    fg_color="#1e40af",             # Track
    progress_color="#0284c7",       # Progress (cyan)
    button_color="#60a5fa",         # Handle
    button_hover_color="#0284c7"
)
```

### Textbox
```python
textbox = ctk.CTkTextbox(
    fg_color="#0f172a",
    border_color="#1e40af",
    border_width=1,
    text_color="#e5e7eb"
)
```

## Gama de Colores por Tipo

### Logs/Console

```
[INFO]   → #60a5fa (Azul claro)
[SUCCESS] → #10b981 (Verde)
[ERROR]   → #ef4444 (Rojo)
[WARN]    → #f97316 (Naranja)
[DEBUG]   → #8b5cf6 (Púrpura)
```

### Plataformas (Colores Secundarios - No Usados en UI)

```
Facebook   → #1877F2 (Original, no usado en nuevo tema)
Instagram  → #C13584 (Original, no usado en nuevo tema)
TikTok     → #FE2C55 (Original, no usado en nuevo tema)
YouTube    → #FF0000 (Original, no usado en nuevo tema)
Twitter    → #1DA1F2 (Original, no usado en nuevo tema)

→ Todos reemplazados por: #0284c7 (Cyan consistente)
```

## Espaciado Estándar

```
padding_inner = 15    # Dentro de cards
padding_outer = 20    # Entre secciones
corner_radius_card = 12
corner_radius_button = 8
```

## Tipografía

```
Heading 1: ("Segoe UI", 18, "bold")        → Títulos principales
Heading 2: ("Segoe UI", 14, "bold")        → Subtítulos
Heading 3: ("Segoe UI", 13, "bold")        → Card titles
Label:     ("Segoe UI", 12, "bold")        → Labels importantes
Text:      ("Segoe UI", 11)                → Texto normal
Small:     ("Segoe UI", 10)                → Texto secundario
Helper:    ("Segoe UI", 9)                 → Descriptores
Console:   ("Consolas", 10)                → Monospace para logs
```

## Implementación Global

Para aplicar consistencia en toda la app:

```python
# Variables globales
PRIMARY_COLOR = "#0284c7"
PRIMARY_HOVER = "#1e40af"
CARD_BG = "#1e3a5f"
ACCENT_TEXT = "#60a5fa"
TEXT_COLOR = "#e5e7eb"
DARK_BG = "#0f172a"
BORDER_COLOR = "#1e40af"

# Aplicar en componentes
frame = ctk.CTkFrame(fg_color=CARD_BG, border_color=BORDER_COLOR)
button = ctk.CTkButton(fg_color=PRIMARY_COLOR, hover_color=PRIMARY_HOVER)
label = ctk.CTkLabel(text_color=ACCENT_TEXT)
```

---

**Versión**: 1.0
**Tema**: Dark Mode Professional Blue
**Actualizado**: 2024

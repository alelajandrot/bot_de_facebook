import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import sys
import os

# --- Configuración de Estilo ---
COL_BG_MAIN = "#f0f2f5"
COL_CARD = "#ffffff"
COL_ACCENT_FB = "#1877f2"   # Azul Facebook
COL_ACCENT_ALERT = "#e41e3f" # Rojo para reportar
COL_ACCENT_REACT = "#f7b928" # Amarillo "Wow"
COL_TEXT_DARK = "#050505"
COL_TEXT_LIGHT = "#65676b"

FONT_TITLE = ("Segoe UI", 24, "bold")
FONT_SUBTITLE = ("Segoe UI", 14)
FONT_BTN = ("Segoe UI", 12, "bold")

# --- Funciones para llamar a los otros scripts ---
def abrir_comentar():
    try:
        # Asegúrate de que el nombre del archivo sea correcto.
        subprocess.Popen([sys.executable, "facebook_bot_personalizado1.py"])
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo abrir el bot de comentarios:\n{e}")

def abrir_reportar():
    try:
        subprocess.Popen([sys.executable, "facebook_bot_reportar.py"])
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo abrir el bot de reportes:\n{e}")

def abrir_reaccionar():
    try:
        subprocess.Popen([sys.executable, "facebook_bot_reaccionar.py"])
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo abrir el bot de reacciones:\n{e}")


# --- Interfaz Gráfica Principal ---
root = tk.Tk()
root.title("Panel de Control - FB Tools")
# Aumentamos la altura para la nueva opción
root.geometry("800x650") 
root.configure(bg=COL_BG_MAIN)

style = ttk.Style()
style.theme_use('clam')

# Estilos personalizados
style.configure("TFrame", background=COL_BG_MAIN)
style.configure("Card.TFrame", background=COL_CARD, relief="flat")
style.configure("Title.TLabel", background=COL_BG_MAIN, foreground=COL_TEXT_DARK, font=FONT_TITLE)
style.configure("Subtitle.TLabel", background=COL_BG_MAIN, foreground=COL_TEXT_LIGHT, font=FONT_SUBTITLE)

# Estilo Botón Azul (Comentar)
style.configure("Blue.TButton", font=FONT_BTN, background=COL_ACCENT_FB, foreground="white", borderwidth=0)
style.map("Blue.TButton", background=[('active', '#166fe5')])

# Estilo Botón Rojo (Reportar)
style.configure("Red.TButton", font=FONT_BTN, background=COL_ACCENT_ALERT, foreground="white", borderwidth=0)
style.map("Red.TButton", background=[('active', '#c01b35')])

# NUEVO: Estilo Botón Amarillo (Reaccionar)
style.configure("Yellow.TButton", font=FONT_BTN, background=COL_ACCENT_REACT, foreground="white", borderwidth=0)
style.map("Yellow.TButton", background=[('active', '#e0a824')])


# --- HEADER ---
header = ttk.Frame(root)
header.pack(pady=40)

ttk.Label(header, text="🚀 FB Automation Tools", style="Title.TLabel").pack()
ttk.Label(header, text="Selecciona una herramienta para comenzar", style="Subtitle.TLabel").pack(pady=(10, 0))

# --- CONTENEDOR DE TARJETAS (MENÚ) ---
menu_frame = ttk.Frame(root)
menu_frame.pack(fill="both", expand=True, padx=50, pady=20)

# === OPCIÓN 1: COMENTAR ===
card_comentar = ttk.Frame(menu_frame, style="Card.TFrame", padding=20)
card_comentar.pack(fill="x", pady=(0, 20))

lbl_c1 = tk.Label(card_comentar, text="💬", font=("Segoe UI", 30), bg=COL_CARD)
lbl_c1.pack(side="left", padx=(0, 20))

info_c1 = ttk.Frame(card_comentar, style="Card.TFrame")
info_c1.pack(side="left", fill="both", expand=True)
tk.Label(info_c1, text="Auto-Comentar", font=("Segoe UI", 16, "bold"), bg=COL_CARD, fg=COL_TEXT_DARK).pack(anchor="w")
tk.Label(info_c1, text="Publica comentarios automáticamente en posts.", font=("Segoe UI", 10), bg=COL_CARD, fg=COL_TEXT_LIGHT).pack(anchor="w")

btn_comentar = ttk.Button(card_comentar, text="Abrir Herramienta", style="Blue.TButton", command=abrir_comentar, cursor="hand2")
btn_comentar.pack(side="right")

# === OPCIÓN 2: REPORTAR ===
card_reportar = ttk.Frame(menu_frame, style="Card.TFrame", padding=20)
card_reportar.pack(fill="x", pady=(0, 20))

lbl_c2 = tk.Label(card_reportar, text="🚨", font=("Segoe UI", 30), bg=COL_CARD)
lbl_c2.pack(side="left", padx=(0, 20))

info_c2 = ttk.Frame(card_reportar, style="Card.TFrame")
info_c2.pack(side="left", fill="both", expand=True)
tk.Label(info_c2, text="Auto-Reportar", font=("Segoe UI", 16, "bold"), bg=COL_CARD, fg=COL_TEXT_DARK).pack(anchor="w")
tk.Label(info_c2, text="Envía denuncias a publicaciones.", font=("Segoe UI", 10), bg=COL_CARD, fg=COL_TEXT_LIGHT).pack(anchor="w")

btn_reportar = ttk.Button(card_reportar, text="Abrir Herramienta", style="Red.TButton", command=abrir_reportar, cursor="hand2")
btn_reportar.pack(side="right")

# === NUEVO: OPCIÓN 3: REACCIONAR ===
card_reaccionar = ttk.Frame(menu_frame, style="Card.TFrame", padding=20)
card_reaccionar.pack(fill="x")

lbl_c3 = tk.Label(card_reaccionar, text="😮", font=("Segoe UI", 30), bg=COL_CARD) # Emoji "Wow"
lbl_c3.pack(side="left", padx=(0, 20))

info_c3 = ttk.Frame(card_reaccionar, style="Card.TFrame")
info_c3.pack(side="left", fill="both", expand=True)
tk.Label(info_c3, text="Auto-Reaccionar", font=("Segoe UI", 16, "bold"), bg=COL_CARD, fg=COL_TEXT_DARK).pack(anchor="w")
tk.Label(info_c3, text="Aplica reacciones (Me encanta, Me divierte, etc).", font=("Segoe UI", 10), bg=COL_CARD, fg=COL_TEXT_LIGHT).pack(anchor="w")

btn_reaccionar = ttk.Button(card_reaccionar, text="Abrir Herramienta", style="Yellow.TButton", command=abrir_reaccionar, cursor="hand2")
btn_reaccionar.pack(side="right")


# --- FOOTER ---
ttk.Label(root, text="v1.1 | Uso educativo solamente", background=COL_BG_MAIN, foreground="#bcc0c4", font=("Segoe UI", 8)).pack(side="bottom", pady=10)

root.mainloop()
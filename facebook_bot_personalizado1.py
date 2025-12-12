import tkinter as tk
from tkinter import messagebox, ttk, scrolledtext
from playwright.sync_api import sync_playwright, TimeoutError
import time
import random
import json
import os
# --- 1. IMPORTAMOS EL CEREBRO DE LOGIN ---
from login_manager import manejar_login

# --- Lógica del Bot ---

def random_sleep(a=2, b=5):
    time.sleep(random.uniform(a, b))

# --- INTERFAZ GRÁFICA (Va primero) ---
COL_BG_MAIN = "#f0f2f5"
COL_CARD = "#ffffff"
COL_ACCENT = "#1877f2"
COL_TEXT_DARK = "#050505"
COL_TEXT_LIGHT = "#65676b"
FONT_TITLE = ("Segoe UI", 20, "bold")
FONT_SUBTITLE = ("Segoe UI", 12, "bold")
FONT_NORMAL = ("Segoe UI", 10)

ventana = tk.Tk()
ventana.title("Facebook Auto-Comment Bot")
ventana.geometry("550x650")
ventana.configure(bg=COL_BG_MAIN)

style = ttk.Style()
style.theme_use('clam')
style.configure("TFrame", background=COL_BG_MAIN)
style.configure("Card.TFrame", background=COL_CARD, relief="flat", borderwidth=0)
style.configure("TLabel", background=COL_CARD, foreground=COL_TEXT_DARK, font=FONT_NORMAL)
style.configure("Title.TLabel", background=COL_BG_MAIN, foreground=COL_ACCENT, font=FONT_TITLE)
style.configure("Subtitle.TLabel", background=COL_CARD, foreground=COL_ACCENT, font=FONT_SUBTITLE)
style.configure("TButton", font=("Segoe UI", 11, "bold"), background=COL_BG_MAIN)
style.configure("Accent.TButton", font=("Segoe UI", 12, "bold"), background=COL_ACCENT, foreground="white")
style.map("Accent.TButton", background=[('active', '#166fe5')])


def ejecutar_bot():
    url = entry_url.get().strip()
    cantidad = entry_cantidad.get().strip()
    comentarios_texto = text_comentarios.get("1.0", tk.END).strip()
    cookies_file = combo_cookies.get().strip()

    if not cookies_file or cookies_file == "(no hay archivos .json)":
        messagebox.showerror("Error", "Por favor selecciona un archivo de cookies válido.")
        return
    if not url:
        messagebox.showerror("Error", "Por favor ingresa el link de la publicación.")
        return
    if not cantidad.isdigit() or int(cantidad) < 1:
        messagebox.showerror("Error", "Ingresa una cantidad válida de comentarios.")
        return

    comentarios = [c for c in comentarios_texto.split("\n") if c.strip()]
    if not comentarios:
         messagebox.showerror("Error", "El campo de comentarios está vacío.")
         return

    cantidad = int(cantidad)
    if len(comentarios) == 1:
        comentarios = comentarios * cantidad
    comentarios = comentarios[:cantidad]

    try:
        # 2. ACTUALIZAMOS EL TEXTO DEL BOTÓN
        btn_ejecutar.config(state="disabled", text="Iniciando Sesión...")
        ventana.update()

        with sync_playwright() as p:
            # 3. LIMPIEZA: Quitamos 'args' que daban error en Firefox
            browser = p.firefox.launch(
                headless=False,
                slow_mo=100
            )
            context = browser.new_context()

            # --- 4. CAMBIO DE LÓGICA: Usamos el Login Manager ---
            # Ya no cargamos cookies ni mostramos popups aquí.
            
            page = manejar_login(context, cookies_file)
            
            if not page:
                # Si el login falla (cookies Y credenciales), detenemos.
                messagebox.showerror("Error de Login", f"¡Falló el login para {cookies_file}!\nRevisa tu archivo 'cuentas.json' o la conexión.")
                browser.close()
                btn_ejecutar.config(state="normal", text="🚀 EJECUTAR BOT") 
                return
            
            # Si el login fue exitoso, actualizamos el botón
            btn_ejecutar.config(text="Comentando... ⏳")
            ventana.update()
            # --- FIN DEL CAMBIO ---

            try:
                # El resto del código es el mismo, ya no necesita la pausa
                
                print(f"➡️ Navegando a: {url}")
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                random_sleep(4, 6)
                
                for i, comentario in enumerate(comentarios):
                    try:
                        page.keyboard.press("PageDown")
                        random_sleep(1, 1.5)
                        campo_comentario = page.locator("div[contenteditable='true'][role='textbox']").first
                        if campo_comentario.count() == 0:
                            campo_comentario = page.locator('div[aria-label="Escribe un comentario..."]').first

                        if campo_comentario.count() > 0:
                            campo_comentario.click()
                            random_sleep(0.5, 1)
                            for letra in comentario:
                                page.keyboard.insert_text(letra)
                                time.sleep(random.uniform(0.02, 0.1))
                            
                            page.keyboard.press("Enter")
                            print(f"[{i+1}/{cantidad}] 💬 Comentado: {comentario}")
                            random_sleep(5, 8)
                        else:
                            print(f"❌ No se encontró la caja de comentarios para: {comentario}")
                    except Exception as e:
                        print(f"⚠️ Error en comentario {i+1}: {e}")

                messagebox.showinfo("¡Terminado! 🎉", f"Proceso finalizado.\nSe intentaron realizar {cantidad} comentarios.")

            except TimeoutError:
                messagebox.showerror("Timeout", "⚠️ La página tardó demasiado en responder.")
            finally:
                browser.close()

    except Exception as e:
        messagebox.showerror("Error Crítico", f"Ocurrió un error inesperado:\n{str(e)}")
    finally:
        btn_ejecutar.config(state="normal", text="🚀 EJECUTAR BOT")

# --- Construcción de la INTERFAZ GRÁFICA ---
header_frame = ttk.Frame(ventana)
header_frame.pack(pady=(20, 10), fill="x")
lbl_titulo = ttk.Label(header_frame, text="🤖 Bot de Comentarios FB", style="Title.TLabel")
lbl_titulo.pack()
ttk.Label(header_frame, text="Automatización simple de tareas", background=COL_BG_MAIN, foreground=COL_TEXT_LIGHT).pack()
main_container = ttk.Frame(ventana)
main_container.pack(fill="both", expand=True, padx=20, pady=10)
card_config = ttk.Frame(main_container, style="Card.TFrame", padding=15)
card_config.pack(fill="x", pady=(0, 15))
ttk.Label(card_config, text="⚙️ Configuración", style="Subtitle.TLabel").pack(anchor="w", pady=(0, 15))
config_grid = ttk.Frame(card_config, style="Card.TFrame")
config_grid.pack(fill="x")
config_grid.columnconfigure(1, weight=1)
ttk.Label(config_grid, text="Cuenta (Cookies):").grid(row=0, column=0, sticky="w", pady=5)

# 5. MEJORA: Ocultamos 'cuentas.json' del dropdown
archivos_json = [f for f in os.listdir('.') if f.endswith('.json') and f != "cuentas.json"]
if not archivos_json: archivos_json = ["(no hay archivos .json)"]
combo_cookies = ttk.Combobox(config_grid, values=archivos_json, state="readonly", font=FONT_NORMAL)
combo_cookies.grid(row=0, column=1, sticky="ew", padx=(10, 0), pady=5)
if archivos_json: combo_cookies.current(0)

ttk.Label(config_grid, text="Link Publicación:").grid(row=1, column=0, sticky="w", pady=5)
entry_url = ttk.Entry(config_grid, font=FONT_NORMAL)
entry_url.grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=5)
ttk.Label(config_grid, text="Cantidad total:").grid(row=2, column=0, sticky="w", pady=5)
entry_cantidad = ttk.Spinbox(config_grid, from_=1, to=100, width=10, font=FONT_NORMAL)
entry_cantidad.set(1)
entry_cantidad.grid(row=2, column=1, sticky="w", padx=(10, 0), pady=5)
card_comments = ttk.Frame(main_container, style="Card.TFrame", padding=15)
card_comments.pack(fill="both", expand=True, pady=(0, 15))
ttk.Label(card_comments, text="💬 Contenido de los Comentarios", style="Subtitle.TLabel").pack(anchor="w", pady=(0, 5))
ttk.Label(card_comments, text="Escribe cada comentario en una línea nueva.", foreground=COL_TEXT_LIGHT, font=("Segoe UI", 9)).pack(anchor="w", pady=(0, 10))
text_comentarios = scrolledtext.ScrolledText(card_comments, height=8, font=FONT_NORMAL, wrap=tk.WORD, relief="flat", bd=2, bg=COL_BG_MAIN)
text_comentarios.pack(fill="both", expand=True)
btn_ejecutar = ttk.Button(ventana, text="🚀 EJECUTAR BOT", command=ejecutar_bot, style="Accent.TButton", cursor="hand2")
btn_ejecutar.pack(fill="x", padx=20, pady=(0, 20), ipady=10)

ventana.mainloop()
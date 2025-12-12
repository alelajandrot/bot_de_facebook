import tkinter as tk
from tkinter import messagebox, ttk
from playwright.sync_api import sync_playwright, TimeoutError
import time
import random
import json
import os
import re 
# Importamos nuestro nuevo "cerebro"
from login_manager import manejar_login 

# --- Lógica del Bot de Reacciones ---

def random_sleep(a=2, b=4):
    time.sleep(random.uniform(a, b))

# --- INTERFAZ GRÁFICA (Va primero) ---
COL_BG_MAIN = "#f0f2f5"
COL_CARD = "#ffffff"
COL_ACCENT_REACT = "#f7b928" 
COL_TEXT_DARK = "#050505"

ventana = tk.Tk()
ventana.title("Bot de Reacciones FB")
ventana.geometry("500x450")
ventana.configure(bg=COL_BG_MAIN)

style = ttk.Style()
style.theme_use('clam')
style.configure("TFrame", background=COL_BG_MAIN)
style.configure("Card.TFrame", background=COL_CARD, relief="flat")
style.configure("TLabel", background=COL_CARD, foreground=COL_TEXT_DARK, font=("Segoe UI", 10))
style.configure("Title.TLabel", background=COL_BG_MAIN, foreground=COL_ACCENT_REACT, font=("Segoe UI", 20, "bold"))
style.configure("Yellow.TButton", font=("Segoe UI", 12, "bold"), background=COL_ACCENT_REACT, foreground="white", borderwidth=0)
style.map("Yellow.TButton", background=[('active', '#e0a824')])


def ejecutar_reaccion():
    url = entry_url.get().strip()
    cookies_file = combo_cookies.get().strip()
    reaccion = combo_reaccion.get().strip() 

    if not cookies_file or cookies_file == "(no hay archivos .json)":
        messagebox.showerror("Error", "Selecciona un archivo de cookies válido.")
        return
    if not url:
        messagebox.showerror("Error", "Ingresa el link de la publicación.")
        return

    try:
        btn_ejecutar.config(state="disabled", text="Iniciando Sesión...")
        ventana.update()

        with sync_playwright() as p:
            browser = p.firefox.launch(
                headless=False,
                slow_mo=100
            )
            context = browser.new_context()

            # --- CAMBIO IMPORTANTE: Usamos el Login Manager ---
            # Ya no cargamos cookies aquí, el manager lo hace
            
            page = manejar_login(context, cookies_file)
            
            if not page:
                # Si el login falla (cookies Y credenciales), detenemos.
                messagebox.showerror("Error de Login", f"¡Falló el login para {cookies_file}!\nRevisa tu archivo 'cuentas.json' o la conexión.")
                browser.close()
                btn_ejecutar.config(state="normal", text="😮 REACCIONAR")
                return
            
            # --- FIN DEL CAMBIO ---

            btn_ejecutar.config(text="Reaccionando... ⏳")
            ventana.update()

            try:
                # Ahora 'page' es la página ya logueada
                print(f"➡️ Yendo a: {url}")
                page.goto(url, wait_until="domcontentloaded")
                random_sleep(4, 6)

                # --- LÓGICA DE REACCIÓN (Sin cambios) ---
                try:
                    print("1. 🔎 Buscando la barra de acciones...")
                    comentar_regex = re.compile("Comentar", re.IGNORECASE)
                    comentar_btn = page.get_by_role("button", name=comentar_regex).first
                    comentar_btn.wait_for(state="visible", timeout=10000)
                    
                    print("2. 🔎 Buscando el botón 'Reaccionar'/'Me gusta'...")
                    like_regex = re.compile("^Reaccionar$|^Me gusta$", re.IGNORECASE)
                    
                    like_button = page.get_by_role("button", name=like_regex).first
                    like_button.wait_for(state="visible", timeout=10000)
                    print("   ✅ Botón 'Me gusta' encontrado.")
                    
                    if reaccion == "Me gusta":
                        print("👍 Aplicando 'Me gusta'...")
                        like_button.click()
                        random_sleep(1, 2)
                        messagebox.showinfo("Éxito", "Reacción 'Me gusta' aplicada.")
                    
                    else:
                        print(f"❤️ Aplicando '{reaccion}'...")
                        like_button.hover() 
                        random_sleep(1, 2)
                        
                        reaction_flyout = page.locator(f'[aria-label="{reaccion}"]').first
                        reaction_flyout.wait_for(state="visible", timeout=5000)
                        
                        reaction_flyout.click()
                        random_sleep(1, 2)
                        messagebox.showinfo("Éxito", f"Reacción '{reaccion}' aplicada.")

                except Exception as e:
                    print(f"❌ Error durante la reacción: {e}")
                    messagebox.showerror("Error de Flujo", "No se pudo encontrar el botón 'Me gusta' o la reacción específica.\n\nEl selector de Facebook pudo cambiar.")

                print("...Flujo terminado, cerrando en 3 segundos...")
                random_sleep(3, 3)

            except TimeoutError:
                messagebox.showerror("Timeout", "La página tardó demasiado en cargar.")
            finally:
                browser.close()

    except Exception as e:
        messagebox.showerror("Error general", str(e))
    finally:
         btn_ejecutar.config(state="normal", text="😮 REACCIONAR")

# --- Construcción de la INTERFAZ GRÁFICA ---
ttk.Label(ventana, text="😮 Auto-Reaccionar Post", style="Title.TLabel").pack(pady=20)
card = ttk.Frame(ventana, style="Card.TFrame", padding=20)
card.pack(fill="both", expand=True, padx=20, pady=(0, 20))
ttk.Label(card, text="Cuenta (Cookies):").pack(anchor="w", pady=5)
archivos = [f for f in os.listdir('.') if f.endswith('.json') and f != "cuentas.json"] or ["(sin cookies)"]
combo_cookies = ttk.Combobox(card, values=archivos, state="readonly", font=("Segoe UI", 10))
combo_cookies.pack(fill="x", pady=(0, 15))
if archivos: combo_cookies.current(0)
ttk.Label(card, text="Link de la Publicación:").pack(anchor="w", pady=5)
entry_url = ttk.Entry(card, font=("Segoe UI", 10))
entry_url.pack(fill="x", pady=(0, 15))
ttk.Label(card, text="Reacción a aplicar:").pack(anchor="w", pady=5)
reacciones = ["Me gusta", "Me encanta", "Me importa", "Me divierte", "Me asombra", "Me entristece", "Me enoja"]
combo_reaccion = ttk.Combobox(card, values=reacciones, state="readonly", font=("Segoe UI", 10))
combo_reaccion.set("Me gusta")
combo_reaccion.pack(fill="x", pady=(0, 20))
btn_ejecutar = ttk.Button(ventana, text="😮 REACCIONAR", style="Yellow.TButton", command=ejecutar_reaccion, cursor="hand2")
btn_ejecutar.pack(fill="x", padx=20, pady=(0, 30), ipady=5)

ventana.mainloop()
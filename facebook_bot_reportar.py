import tkinter as tk
from tkinter import messagebox, ttk
from playwright.sync_api import sync_playwright, TimeoutError
import time
import random
import json
import os
import re # Importante

# --- Lógica del Bot de Reportes ---

def random_sleep(a=2, b=4):
    time.sleep(random.uniform(a, b))

def ejecutar_reporte():
    url = entry_url.get().strip()
    cookies_file = combo_cookies.get().strip()
    motivo = combo_motivo.get().strip() 

    if not cookies_file or cookies_file == "(no hay archivos .json)":
        messagebox.showerror("Error", "Selecciona un archivo de cookies válido.")
        return

    if not url:
        messagebox.showerror("Error", "Ingresa el link de la publicación.")
        return

    try:
        btn_ejecutar.config(state="disabled", text="Procesando... ⏳")
        ventana.update()

        with sync_playwright() as p:
            browser = p.firefox.launch(
                headless=False,
                slow_mo=100
            )
            context = browser.new_context()

            if os.path.exists(cookies_file):
                with open(cookies_file, "r", encoding="utf-8") as f:
                    cookies = json.load(f)
                    context.add_cookies(cookies)
            else:
                messagebox.showerror("Error", "No se encontró el archivo de cookies.")
                btn_ejecutar.config(state="normal", text="🚨 REPORTAR AHORA")
                browser.close()
                return

            page = context.new_page()

            try:
                # 1. Login check
                page.goto("https://www.facebook.com/", wait_until="domcontentloaded")
                
                # --- PAUSA MANUAL PARA LOGIN (IGUAL QUE EL BOT DE COMENTARIOS) ---
                print("\n" + "="*60)
                print("  ⚠️ ACCIÓN REQUERIDA ⚠️")
                print("  Verifica el inicio de sesión en el navegador.")
                print("  Si las cookies fallaron, inicia sesión manualmente AHORA.")
                input("  Presiona Enter aquí para continuar...")
                print("="*60 + "\n")
                # -----------------------------------------------------------------

                # 2. Ir a la publicación
                print(f"➡️ Yendo a: {url}")
                page.goto(url, wait_until="domcontentloaded")
                random_sleep(4, 6)

                # --- INICIO DE LA LÓGICA DE REPORTE MEJORADA ---
                
                # 3. Buscar los tres puntos (...)
                try:
                    # ***** CAMBIO 1: BUSCAR LA VENTANA FLOTANTE (MODAL) PRIMERO *****
                    print("1. 🔎 Buscando el 'modal' (ventana flotante) de la publicación...")
                    # Los modales de FB suelen tener role="dialog". Esperamos que aparezca.
                    modal_publicacion = page.locator('div[role="dialog"]').first
                    modal_publicacion.wait_for(state="visible", timeout=10000)
                    print("   ✅ Modal encontrado.")

                    print("2. 🔎 Buscando menú de opciones (...) DENTRO del modal...")
                    # Ahora buscamos los 3 puntos SOLO DENTRO del modal
                    menu_locator = modal_publicacion.locator(
                        'div[aria-label="Acciones para esta publicación"],'
                        'div[aria-label="Más acciones"],'
                        'div[aria-label="Más"],'
                        # Añado un selector común en español
                        'div[aria-label="Ocultar o denunciar publicación"]'
                    ).first
                    menu_locator.wait_for(state="visible", timeout=10000)
                    menu_locator.click()
                    random_sleep(1, 2)
                
                except Exception as e:
                    print(f"❌ Error al buscar el menú (...): {e}")
                    messagebox.showerror("Error de Flujo", "No se encontró el menú de opciones (...) de la publicación.\n\nEl 'aria-label' de los 3 puntos puede ser otro. Revisa el paso de inspección.")
                    browser.close()
                    return

                # 4. Clic en "Denunciar"
                try:
                    # ***** CAMBIO 2: USAR "DENUNCIAR" EN LUGAR DE "REPORTAR" *****
                    print("🚨 Buscando botón 'Denunciar'...")
                    denunciar_regex = re.compile("denunciar", re.IGNORECASE)
                    
                    btn_denunciar = page.get_by_role("menuitem", name=denunciar_regex).first
                    
                    btn_denunciar.wait_for(state="visible", timeout=5000)
                    btn_denunciar.click()
                    random_sleep(2, 3)

                except Exception as e:
                    print(f"❌ Error al buscar el botón 'Denunciar': {e}")
                    messagebox.showerror("Error de Flujo", "Se abrió el menú, pero no se encontró la opción 'Denunciar publicación'.")
                    browser.close()
                    return

                # 5. Seleccionar motivo
                try:
                    print(f"🛑 Seleccionando motivo: {motivo}...")
                    motivo_regex = re.compile(motivo, re.IGNORECASE)
                    
                    opcion_motivo = page.locator('span, div[role="button"]').filter(has_text=motivo_regex).first
                    
                    opcion_motivo.wait_for(state="visible", timeout=10000) 
                    opcion_motivo.click()
                    random_sleep(1, 2)

                except Exception as e:
                    print(f"❌ Error al buscar el motivo '{motivo}': {e}")
                    messagebox.showerror("Error de Flujo", f"No se encontró la opción '{motivo}'. El menú de reporte pudo cambiar.")
                    browser.close()
                    return

                # 6. Enviar y Finalizar (Esto suele ser "Enviar", "Siguiente", "Listo")
                try:
                    print("✅ Buscando Enviar/Siguiente...")
                    enviar_regex = re.compile("Enviar|Siguiente", re.IGNORECASE)
                    btn_enviar = page.get_by_role("button", name=enviar_regex).first
                    
                    btn_enviar.wait_for(state="visible", timeout=5000)
                    btn_enviar.click()
                    random_sleep(2, 3)

                    try:
                        print("🧹 Buscando botón 'Listo'...")
                        listo_regex = re.compile("Listo|Cerrar", re.IGNORECASE)
                        btn_listo = page.get_by_role("button", name=listo_regex).first
                        
                        btn_listo.wait_for(state="visible", timeout=5000)
                        btn_listo.click()
                    except:
                        print("ℹ️ No se encontró botón 'Listo' (es normal si el reporte fue directo).")
                        
                    messagebox.showinfo("Éxito", "✅ El flujo de reporte se ha completado.")

                except Exception as e:
                    print(f"❌ Error al buscar 'Enviar' o 'Listo': {e}")
                    messagebox.showwarning("Atención", "Se seleccionó el motivo, pero no se pudo enviar/finalizar el reporte.")

                print("...Flujo terminado, cerrando en 5 segundos...")
                random_sleep(5, 5)

            except TimeoutError:
                messagebox.showerror("Timeout", "La página tardó demasiado en cargar.")
            finally:
                browser.close()

    except Exception as e:
        messagebox.showerror("Error general", str(e))
    finally:
         btn_ejecutar.config(state="normal", text="🚨 REPORTAR AHORA")

# --- INTERFAZ GRÁFICA (Sin cambios) ---
# ... (El resto de tu código de la GUI va aquí, déjalo tal cual) ...
COL_BG_MAIN = "#f0f2f5"
COL_CARD = "#ffffff"
COL_ACCENT_ALERT = "#e41e3f" # Rojo
COL_TEXT_DARK = "#050505"

ventana = tk.Tk()
ventana.title("Bot de Reportes FB")
ventana.geometry("500x450")
ventana.configure(bg=COL_BG_MAIN)

style = ttk.Style()
style.theme_use('clam')
style.configure("TFrame", background=COL_BG_MAIN)
style.configure("Card.TFrame", background=COL_CARD, relief="flat")
style.configure("TLabel", background=COL_CARD, foreground=COL_TEXT_DARK, font=("Segoe UI", 10))
style.configure("Title.TLabel", background=COL_BG_MAIN, foreground=COL_ACCENT_ALERT, font=("Segoe UI", 20, "bold"))
style.configure("Red.TButton", font=("Segoe UI", 12, "bold"), background=COL_ACCENT_ALERT, foreground="white", borderwidth=0)
style.map("Red.TButton", background=[('active', '#c01b35')])

# Header
ttk.Label(ventana, text="🚨 Auto-Reportar Post", style="Title.TLabel").pack(pady=20)

# Card Principal
card = ttk.Frame(ventana, style="Card.TFrame", padding=20)
card.pack(fill="both", expand=True, padx=20, pady=(0, 20))

# Inputs
ttk.Label(card, text="Cuenta (Cookies):").pack(anchor="w", pady=5)
archivos = [f for f in os.listdir('.') if f.endswith('.json')] or ["(sin cookies)"]
combo_cookies = ttk.Combobox(card, values=archivos, state="readonly", font=("Segoe UI", 10))
combo_cookies.pack(fill="x", pady=(0, 15))
if archivos: combo_cookies.current(0)

ttk.Label(card, text="Link de la Publicación a reportar:").pack(anchor="w", pady=5)
entry_url = ttk.Entry(card, font=("Segoe UI", 10))
entry_url.pack(fill="x", pady=(0, 15))

ttk.Label(card, text="Motivo del reporte (intento):").pack(anchor="w", pady=5)
motivos = ["Spam", "Desnudos", "Violencia", "Acoso", "Información falsa", "Lenguaje que incita al odio"]
combo_motivo = ttk.Combobox(card, values=motivos, state="readonly", font=("Segoe UI", 10))
combo_motivo.set("Spam") # Default
combo_motivo.pack(fill="x", pady=(0, 20))

# Botón
btn_ejecutar = ttk.Button(ventana, text="🚨 REPORTAR AHORA", style="Red.TButton", command=ejecutar_reporte, cursor="hand2")
btn_ejecutar.pack(fill="x", padx=20, pady=(0, 30), ipady=5)

ventana.mainloop()
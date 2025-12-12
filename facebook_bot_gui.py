import tkinter as tk
from tkinter import messagebox
from playwright.sync_api import sync_playwright
import time
import random
import json
import os

def random_sleep(a=2, b=5):
    time.sleep(random.uniform(a, b))

def ejecutar_bot():
    url = entry_url.get().strip()
    cantidad = entry_cantidad.get().strip()
    comentarios_texto = text_comentarios.get("1.0", tk.END).strip()
    
    if not url:
        messagebox.showerror("Error", "Por favor ingresa el link de la publicación.")
        return
    
    if not cantidad.isdigit() or int(cantidad) < 1:
        messagebox.showerror("Error", "Ingresa una cantidad válida de comentarios.")
        return
    
    comentarios = comentarios_texto.split("\n")
    cantidad = int(cantidad)

    # Si el usuario solo puso 1 comentario y pidió varios, se repite el mismo
    if len(comentarios) == 1:
        comentarios = comentarios * cantidad

    # O se toman los primeros N comentarios
    comentarios = comentarios[:cantidad]

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False, slow_mo=100)  # slow_mo hace más humano el comportamiento
            context = browser.new_context()

            # Cargar cookies si existen
            if os.path.exists("cookies.json"):
                with open("cookies.json", "r", encoding="utf-8") as f:
                    cookies = json.load(f)
                    context.add_cookies(cookies)
                    print("✅ Cookies cargadas.")
            else:
                messagebox.showinfo("Aviso", "No se encontró cookies.json. Ejecuta primero el login manual.")
                browser.close()
                return

            page = context.new_page()
            page.goto("https://www.facebook.com/")
            input("✅ Verifica que estás logueado y presiona Enter...")

            page.goto(url)
            random_sleep(5, 7)

            for comentario in comentarios:
                try:
                    # Scroll para cargar la sección de comentarios
                    for _ in range(3):
                        page.keyboard.press("PageDown")
                        random_sleep(1, 2)

                    # Intentar localizar el campo editable
                    campo_comentario = page.locator("div[contenteditable='true'][role='textbox']").first
                    
                    if campo_comentario.count() == 0:
                        raise Exception("No se encontró el campo para escribir comentarios.")

                    campo_comentario.click()
                    random_sleep()

                    for letra in comentario:
                        page.keyboard.insert_text(letra)
                        time.sleep(random.uniform(0.05, 0.2))
                    page.keyboard.press("Enter")
                    print(f"💬 Comentado: {comentario}")
                    random_sleep(4, 6)

                except Exception as e:
                    print(f"❌ Error al comentar: {e}")
            
            messagebox.showinfo("Éxito", "Comentarios publicados correctamente.")
            browser.close()

    except Exception as e:
        messagebox.showerror("Error", str(e))
        try:
            browser.close()
        except:
            pass

# --- Interfaz Tkinter ---
ventana = tk.Tk()
ventana.title("Bot Facebook")

# Link de publicación
tk.Label(ventana, text="Link de la publicación:").grid(row=0, column=0, sticky="w")
entry_url = tk.Entry(ventana, width=80)
entry_url.grid(row=0, column=1, pady=5)

# Cantidad de comentarios
tk.Label(ventana, text="Cantidad de comentarios:").grid(row=1, column=0, sticky="w")
entry_cantidad = tk.Entry(ventana, width=10)
entry_cantidad.grid(row=1, column=1, sticky="w", pady=5)

# Texto de los comentarios
tk.Label(ventana, text="Texto(s) de los comentarios (uno por línea):").grid(row=2, column=0, sticky="nw", pady=5)
text_comentarios = tk.Text(ventana, height=10, width=60)
text_comentarios.grid(row=2, column=1, pady=5)

# Botón
btn_ejecutar = tk.Button(ventana, text="Ejecutar Bot", command=ejecutar_bot)
btn_ejecutar.grid(row=3, column=1, pady=10, sticky="e")

ventana.mainloop()

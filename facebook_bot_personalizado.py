import tkinter as tk
from tkinter import messagebox, ttk
from playwright.sync_api import sync_playwright
import time
import random
import json
import os

# --- Colores y fuentes ---
COLOR_FONDO = "#f0f4f7"
COLOR_LABEL = "#333333"
COLOR_ENTRADA = "#ffffff"
COLOR_BOTON = "#007acc"
COLOR_BOTON_TEXTO = "#ffffff"
FUENTE = ("Arial", 12)
FUENTE_TITULO = ("Arial", 16, "bold")

def random_sleep(a=2, b=5):
    time.sleep(random.uniform(a, b))

def ejecutar_bot():
    url = entry_url.get().strip()
    cantidad = entry_cantidad.get().strip()
    comentarios_texto = text_comentarios.get("1.0", tk.END).strip()
    cookies_file = combo_cookies.get().strip()

    if not url:
        messagebox.showerror("Error", "Por favor ingresa el link de la publicación.")
        return
    
    if not cantidad.isdigit() or int(cantidad) < 1:
        messagebox.showerror("Error", "Ingresa una cantidad válida de comentarios.")
        return

    if not cookies_file:
        messagebox.showerror("Error", "Por favor selecciona el archivo de cookies.")
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
            browser = p.chromium.launch(headless=False, slow_mo=100)
            context = browser.new_context()

            # Cargar cookies específicas de la cuenta seleccionada
            if os.path.exists(cookies_file):
                with open(cookies_file, "r", encoding="utf-8") as f:
                    cookies = json.load(f)
                    context.add_cookies(cookies)
                    print(f"✅ Cookies cargadas desde {cookies_file}")
            else:
                messagebox.showinfo("Aviso", f"No se encontró {cookies_file}. Ejecuta primero el login manual.")
                browser.close()
                return

            page = context.new_page()
            page.goto("https://www.facebook.com/")
            input("✅ Verifica que estás logueado y presiona Enter...")

            page.goto(url)
            random_sleep(5, 7)

            for comentario in comentarios:
                try:
                    for _ in range(3):
                        page.keyboard.press("PageDown")
                        random_sleep(1, 2)

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

# --- Interfaz Tkinter personalizada ---
ventana = tk.Tk()
ventana.title("Bot Facebook")
ventana.configure(bg=COLOR_FONDO)

# Título
titulo = tk.Label(
    ventana, 
    text="Bot de Comentarios en Facebook",
    font=FUENTE_TITULO,
    bg=COLOR_FONDO,
    fg="#007acc"
)
titulo.grid(row=0, column=0, columnspan=2, pady=15)

# Link de publicación
tk.Label(ventana, text="Link de la publicación:", font=FUENTE, bg=COLOR_FONDO, fg=COLOR_LABEL).grid(row=1, column=0, sticky="w", padx=10, pady=5)
entry_url = tk.Entry(ventana, width=80, font=FUENTE, bg=COLOR_ENTRADA, fg=COLOR_LABEL)
entry_url.grid(row=1, column=1, pady=5, padx=10)

# Cantidad de comentarios
tk.Label(ventana, text="Cantidad de comentarios:", font=FUENTE, bg=COLOR_FONDO, fg=COLOR_LABEL).grid(row=2, column=0, sticky="w", padx=10, pady=5)
entry_cantidad = tk.Entry(ventana, width=10, font=FUENTE, bg=COLOR_ENTRADA, fg=COLOR_LABEL)
entry_cantidad.grid(row=2, column=1, sticky="w", pady=5, padx=10)

# Texto de los comentarios
tk.Label(ventana, text="Escribe texto(s) de los comentarios (un comentario por línea):", font=FUENTE, bg=COLOR_FONDO, fg=COLOR_LABEL).grid(row=3, column=0, sticky="nw", padx=10, pady=5)
text_comentarios = tk.Text(ventana, height=10, width=60, font=FUENTE, bg=COLOR_ENTRADA, fg=COLOR_LABEL)
text_comentarios.grid(row=3, column=1, pady=5, padx=10)

# Archivo de cookies (ComboBox)
tk.Label(ventana, text="Elije la cuenta para comentar:", font=FUENTE, bg=COLOR_FONDO, fg=COLOR_LABEL).grid(row=4, column=0, sticky="w", padx=10, pady=5)

# Buscar archivos .json en la carpeta actual
cookie_files = [f for f in os.listdir('.') if f.endswith('.json')]
if not cookie_files:
    cookie_files = ["(no hay archivos .json)"]

combo_cookies = ttk.Combobox(ventana, values=cookie_files, width=40, font=FUENTE)
combo_cookies.grid(row=4, column=1, sticky="w", pady=5, padx=10)
if cookie_files and cookie_files[0] != "(no hay archivos .json)":
    combo_cookies.current(0)

# Botón
btn_ejecutar = tk.Button(
    ventana, 
    text="Ejecutar Bot",
    command=ejecutar_bot,
    bg=COLOR_BOTON,
    fg=COLOR_BOTON_TEXTO,
    font=("Arial", 12, "bold"),
    relief="raised",
    padx=10,
    pady=5
)
btn_ejecutar.grid(row=5, column=1, pady=20, sticky="e", padx=10)

ventana.mainloop()

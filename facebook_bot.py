from playwright.sync_api import sync_playwright
import json
import time
import random

comentarios = [
    "Gracias por compartir 💬",
    "¡Muy útil!",
    "Buena info 👌"
]

def random_sleep(a=2, b=5):
    time.sleep(random.uniform(a, b))

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()

    # Cargar cookies manualmente desde tu Chrome real
    with open("cookies.json", "r", encoding="utf-8") as f:
        cookies = json.load(f)
        context.add_cookies(cookies)

    page = context.new_page()
    page.goto("https://www.facebook.com/")
    input("✅ Verifica que estás logueado y presiona Enter...")

    # Ir a la publicación
    page.goto("https://www.facebook.com/photo/?fbid=3994613324091487&set=gm.1635347961178993&idorvanity=610240220356444")  # REEMPLAZA ESTA URL
    random_sleep()

    for comentario in comentarios:
        try:
            page.click("div[aria-label='Escribe un comentario público…']", timeout=5000)
            random_sleep()
            for letra in comentario:
                page.keyboard.insert_text(letra)
                time.sleep(random.uniform(0.05, 0.2))
            page.keyboard.press("Enter")
            print(f"💬 Comentado: {comentario}")
            random_sleep(4, 6)
        except Exception as e:
            print(f"❌ Error al comentar: {e}")

    input("Presiona Enter para cerrar...")
    browser.close()

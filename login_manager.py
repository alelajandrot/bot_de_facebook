import json
import os
import time
import re
from playwright.sync_api import TimeoutError

# Carga la base de datos de cuentas al iniciar
try:
    with open("cuentas.json", "r", encoding="utf-8") as f:
        CUENTAS_BD = json.load(f)
except FileNotFoundError:
    CUENTAS_BD = {}

def manejar_login(context, cookies_file_name):
    """
    Intenta iniciar sesión con cookies. Si falla, usa usuario/contraseña.
    """
    print(f"--- Login Manager: Procesando {cookies_file_name} ---")
    
    cookies_path = cookies_file_name
    # 1. Intentar cargar cookies existentes
    if os.path.exists(cookies_path):
        try:
            with open(cookies_path, "r", encoding="utf-8") as f:
                cookies = json.load(f)
                context.add_cookies(cookies)
        except Exception as e:
            print(f"⚠️ Error leyendo cookies: {e}")

    page = context.new_page()
    try:
        page.goto("https://www.facebook.com/", wait_until="domcontentloaded", timeout=60000)
    except TimeoutError:
        print("❌ Timeout cargando Facebook.")
        return None

    # 2. Verificar si ya estamos dentro (Búsqueda bilingüe)
    try:
        search_bar = page.locator(
            'input[aria-label="Buscar en Facebook"], input[aria-label="Search Facebook"]'
        ).first
        search_bar.wait_for(state="visible", timeout=8000)
        print("✅ Login exitoso vía Cookies.")
        return page 
    except TimeoutError:
        print("⚠️ Cookies expiradas o inválidas. Intentando login manual...")

    # 3. Si las cookies fallaron, usar credenciales
    if cookies_file_name not in CUENTAS_BD:
        print(f"❌ No hay credenciales para '{cookies_file_name}' en cuentas.json")
        return None

    creds = CUENTAS_BD[cookies_file_name]
    try:
        page.goto("https://www.facebook.com/login/", wait_until="domcontentloaded")
        page.fill("#email", creds["username"])
        page.fill("#pass", creds["password"])
        page.click("#loginbutton")
        
        # Verificar login post-credenciales
        search_bar = page.locator(
            'input[aria-label="Buscar en Facebook"], input[aria-label="Search Facebook"]'
        ).first
        search_bar.wait_for(state="visible", timeout=20000)

        # Manejar popup "Guardar navegador / Ahora no"
        try:
            btn_not_now = page.locator('div[role="button"]').filter(has_text=re.compile("Ahora no|Not now", re.IGNORECASE)).first
            if btn_not_now.is_visible(timeout=5000):
                btn_not_now.click()
        except:
            pass

        # 4. Guardar las nuevas cookies para la próxima
        print("🔄 Actualizando archivo de cookies...")
        with open(cookies_path, 'w', encoding='utf-8') as f:
            json.dump(context.cookies(), f, indent=4)
            
        return page

    except Exception as e:
        print(f"❌ Error fatal en login: {e}")
        return None
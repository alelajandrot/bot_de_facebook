import sqlite3
import json
import os
import time
import shutil
import glob
from tkinter import messagebox
from playwright.sync_api import TimeoutError

# Importar Stealth
try:
    from playwright_stealth import stealth_sync
except ImportError:
    stealth_sync = None

DB_NAME = "cuentas.db"
# =========================
# Validación de cookies
# =========================
def _cookie_names(cookies_list):
    return {c.get("name") for c in (cookies_list or []) if isinstance(c, dict)}

def sesion_valida_por_cookies(platform: str, cookies_list) -> bool:
    """
    Evita guardar cookies inútiles (ej: solo 'datr').
    - Facebook: esperamos c_user y xs/sb (mínimo).
    - Instagram: esperamos sessionid (o ds_user_id + csrftoken).
    """
    platform = (platform or "").lower()
    names = _cookie_names(cookies_list)

    if platform == "facebook":
        return ("c_user" in names) and (("xs" in names) or ("sb" in names))
    if platform == "instagram":
        return ("sessionid" in names) or (("ds_user_id" in names) and ("csrftoken" in names))

    # Para otras plataformas no forzamos tanto (pero al menos algo más que 1 cookie)
    return len(names) >= 2

# ==============================================================================
#                        GESTIÓN DE BASE DE DATOS
# ==============================================================================
def init_db():
    """Inicializa la DB, migra datos y RESCATA cookies sueltas."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS cuentas (
                    alias TEXT PRIMARY KEY,
                    username TEXT,
                    password TEXT,
                    proxy TEXT,
                    platform TEXT,
                    cookies TEXT,
                    user_agent TEXT,
                    last_used TEXT
                )''')
    conn.commit()
    conn.close()
    
    migrar_credenciales_json()
    rescatar_cookies_antiguas()
    limpiar_duplicados_json()
    sincronizar_perfiles_locales()

def migrar_credenciales_json():
    if os.path.exists("cuentas.json"):
        try:
            with open("cuentas.json", "r", encoding="utf-8") as f:
                data = json.load(f)
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            for alias, info in data.items():
                clean_alias = alias.replace(".json", "")
                c.execute("SELECT alias FROM cuentas WHERE alias=?", (clean_alias,))
                if not c.fetchone():
                    c.execute("INSERT INTO cuentas (alias, username, password, proxy, platform) VALUES (?, ?, ?, ?, ?)",
                              (clean_alias, info.get("username"), info.get("password"), info.get("proxy"), info.get("platform", "facebook")))
            conn.commit()
            conn.close()
        except Exception: pass

def limpiar_duplicados_json():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute("DELETE FROM cuentas WHERE alias LIKE '%.json'")
        conn.commit()
    except: pass
    finally: conn.close()

def rescatar_cookies_antiguas():
    archivos = glob.glob("*.json")
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    for archivo in archivos:
        if archivo == "cuentas.json" or archivo == "package.json": continue
        try:
            with open(archivo, "r", encoding="utf-8") as f:
                contenido = json.load(f)
            if isinstance(contenido, list) and len(contenido) > 0 and 'name' in contenido[0]:
                alias = archivo.replace(".json", "")
                cookies_str = json.dumps(contenido)
                c.execute("UPDATE cuentas SET cookies = ? WHERE alias = ?", (cookies_str, alias))
                if c.rowcount == 0:
                    c.execute("INSERT OR REPLACE INTO cuentas (alias, cookies, platform) VALUES (?, ?, ?)", 
                              (alias, cookies_str, "facebook"))
        except: pass
    conn.commit()
    conn.close()

def obtener_datos_cuenta(alias):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM cuentas WHERE alias=?", (alias,))
    row = c.fetchone()
    conn.close()
    if row: return dict(row)
    return {}

def guardar_cookies_db(alias, cookies_list, strict=True, platform_hint=None):
    data = obtener_datos_cuenta(alias)
    platform = (platform_hint or data.get("platform", "facebook")).lower()

    if strict and not sesion_valida_por_cookies(platform, cookies_list):
        print(f"⚠️ No guardo cookies débiles para {alias} ({platform}). "
              f"Probablemente NO estás logueado (ej: solo 'datr').")
        return False

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    cookies_json = json.dumps(cookies_list)
    c.execute("UPDATE cuentas SET cookies = ?, last_used = ? WHERE alias = ?",
              (cookies_json, time.strftime("%Y-%m-%d %H:%M:%S"), alias))
    conn.commit()
    conn.close()
    return True


def guardar_nueva_cuenta(alias, user, pwd, proxy, platform):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute("INSERT OR REPLACE INTO cuentas (alias, username, password, proxy, platform) VALUES (?, ?, ?, ?, ?)",
                  (alias, user, pwd, proxy, platform))
        conn.commit()
        return True
    except: return False
    finally: conn.close()

def obtener_lista_alias():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT alias FROM cuentas ORDER BY alias ASC")
    rows = c.fetchall()
    conn.close()
    return [r[0] for r in rows]

# ==============================================================================
#                        LÓGICA DE LOGIN Y NAVEGACIÓN (CORREGIDA)
# ==============================================================================

def manejar_login(context, alias, headless_mode=False):
    """
    Versión optimizada: Prioriza archivos JSON físicos y maneja 
    tiempos de espera para evitar bloqueos en cuentas antiguas.
    """
    print(f"--- Login Manager: Procesando {alias} ---")
    
    data = obtener_datos_cuenta(alias)
    platform = data.get("platform", "facebook").lower()

    # 1. Definición de URLs por plataforma
    urls = {
        "facebook": "https://www.facebook.com/",
        "instagram": "https://www.instagram.com/",
        "twitter": "https://twitter.com/",
        "x": "https://twitter.com/",
        "youtube": "https://www.youtube.com/",
        "tiktok": "https://www.tiktok.com/"
    }
    target_url = urls.get(platform, "https://www.facebook.com/")

    # 2. CARGA DE COOKIES (Prioridad: Archivo JSON físico -> Base de Datos)
    archivo_json = f"{alias}.json"
    cookies_cargadas = False

    if os.path.exists(archivo_json):
        try:
            with open(archivo_json, "r", encoding="utf-8") as f:
                cookies = json.load(f)
                context.add_cookies(cookies)
                print(f"✅ Sesión cargada desde ARCHIVO JSON para {alias}")
                cookies_cargadas = True
        except Exception as e:
            print(f"⚠️ Error cargando archivo JSON: {e}")

    # Si no hay JSON o falló, intentamos con la DB
    if not cookies_cargadas:
        cookies_str = data.get("cookies")
        if cookies_str:
            try:
                cookies = json.loads(cookies_str)
                context.add_cookies(cookies)
                print(f"🍪 Cookies inyectadas desde DB para {platform}.")
                cookies_cargadas = True
            except Exception as e:
                print(f"⚠️ Error cookies DB: {e}")

    # 3. Lanzamiento de página con Stealth
    page = context.new_page()
    if stealth_sync: 
        stealth_sync(page)
    
    try:
        # Navegación con tiempo de espera extendido para evitar ERR_ABORTED
        print(f"🌍 Navegando a {target_url} ...")
        page.goto(target_url, wait_until="domcontentloaded", timeout=90000)
        
        # Pausa de seguridad para que Facebook procese la sesión
        page.wait_for_timeout(3000)
    except Exception as e:
        print(f"❌ Error de navegación: {e}")
        return None

    # 4. Verificación de Login
    if verificar_si_logueado(page, platform):
        print(f"✅ Login OK en {platform} ({'Archivo' if cookies_cargadas else 'Perfil'}).")
        return page 
    
    # 5. Si falló la cookie, intentar Login Automático (Solo Facebook)
    print("⚠️ Sesión no detectada. Intentando re-login o pidiendo manual...")
    
    if platform == "facebook":
        return intentar_login_facebook(page, context, alias, data, headless_mode)
    else:
        # Para otras redes, si no es headless, permitir login manual breve
        if not headless_mode:
            from tkinter import messagebox
            messagebox.showinfo("Login Requerido", f"La sesión de {platform} para {alias} expiró.\nInicia sesión manualmente en la ventana abierta.")
            try:
                # Esperar hasta 60 segundos a que el usuario se loguee
                page.wait_for_timeout(60000) 
                if verificar_si_logueado(page, platform):
                    # Guardar la nueva sesión exitosa
                    cookies = context.cookies()
                    guardar_cookies_db(alias, cookies)
                    with open(archivo_json, "w", encoding="utf-8") as f:
                        json.dump(cookies, f, indent=4)
                    return page
            except: pass
        
    return None



def intentar_login_facebook(page, context, alias, data, headless_mode):
    """Lógica específica de login para Facebook (Legacy)"""
    user = data.get("username")
    pwd = data.get("password")
    
    if not user or not pwd: return None

    try:
        campo_user = page.locator('#email, input[name="email"]').first
        if campo_user.is_visible():
            campo_user.fill(user)
            page.wait_for_timeout(1000)
            page.locator('#pass, input[name="pass"]').first.fill(pwd)
            page.wait_for_timeout(1000)
            page.locator('#loginbutton, button[name="login"], button[type="submit"]').first.click()
            page.wait_for_timeout(5000)
            
            if "checkpoint" in page.url: return None
            
            if verificar_si_logueado(page, "facebook"):
                guardar_cookies_db(alias, context.cookies())
                return page
    except: pass
    return None

def verificar_si_logueado(page, platform):
    """
    Verifica si la sesión está activa detectando elementos clave.
    Optimizado para soportar cuentas en español e inglés.
    """
    try:
        if platform == "facebook":
            # Buscamos el feed, la barra de búsqueda o el placeholder de publicación
            # Estos selectores cubren "Buscar", "Search", "¿Qué estás pensando?" y "What's on your mind?"
            return page.locator(
                'div[role="feed"], '
                'input[aria-label*="Buscar"], input[aria-label*="Search"], '
                'div[role="button"] span:has-text("¿Qué estás pensando?"), '
                'div[role="button"] span:has-text("What\'s on your mind?")'
            ).first.is_visible(timeout=7000)
        
        elif platform == "tiktok":
            # Icono de perfil o botón de carga (Upload)
            return page.locator('[data-e2e="profile-icon"], [data-e2e="upload-icon"]').first.is_visible(timeout=5000)
        
        elif platform == "youtube":
            # Avatar de usuario o botón de creación
            return page.locator('#avatar-btn, #buttons ytd-topbar-menu-button-renderer, img[alt="Avatar"]').first.is_visible(timeout=5000)
            
        elif platform in ["twitter", "x"]:
            # Botón de redactar Tweet o selector de cuenta
            return page.locator('[data-testid="SideNav_AccountSwitcher_Button"], [data-testid="SideNav_NewTweet_Button"]').first.is_visible(timeout=5000)
            
        elif platform == "instagram":
            # Iconos de Home/Inicio o el de Mensajes/Direct
            return page.locator(
                'svg[aria-label="Inicio"], svg[aria-label="Home"], '
                'svg[aria-label="Perfil"], svg[aria-label="Profile"], '
                'a[href*="/direct/inbox/"]'
            ).first.is_visible(timeout=7000)

        return False
    except Exception as e:
        print(f"⚠️ Error en verificación de login ({platform}): {e}")
        return False

def login_manual_asistido(context, alias, data):
    platform = data.get("platform", "").lower()

    PLATFORM_URLS = {
        "facebook": "https://www.facebook.com/",
        "instagram": "https://www.instagram.com/accounts/login/",
        "tiktok": "https://www.tiktok.com/login",
        "youtube": "https://accounts.google.com/",
        "twitter": "https://twitter.com/login",
        "x": "https://twitter.com/login"
    }

    if platform not in PLATFORM_URLS:
        messagebox.showerror(
            "Error",
            f"Plataforma desconocida para {alias}: {platform}"
        )
        return False

    url = PLATFORM_URLS[platform]

    page = context.new_page()
    page.goto(url, wait_until="domcontentloaded", timeout=120000)

    respuesta = messagebox.askyesno(
        "Login Manual",
        f"Cuenta: {alias}\n"
        f"Plataforma: {platform.upper()}\n\n"
        f"1️⃣ Inicia sesión COMPLETA en {platform}\n"
        f"2️⃣ Asegúrate de ver el HOME / FEED\n"
        f"3️⃣ ¿Ya terminaste?"
    )

    if not respuesta:
        return False

    # 1️⃣ Verificación visual
    if verificar_si_logueado(page, platform):
        cookies = context.cookies()
        guardar_cookies_db(
            alias,
            cookies,
            strict=True,
            platform_hint=platform
        )

        with open(f"{alias}.json", "w", encoding="utf-8") as f:
            json.dump(cookies, f, indent=4)

        return True

    # 2️⃣ Fallback por cookies (si el selector falla)
    cookies = context.cookies()
    if sesion_valida_por_cookies(platform, cookies):
        guardar_cookies_db(
            alias,
            cookies,
            strict=True,
            platform_hint=platform
        )

        with open(f"{alias}.json", "w", encoding="utf-8") as f:
            json.dump(cookies, f, indent=4)

        return True

    messagebox.showwarning(
        "Sesión inválida",
        f"No se detectó sesión válida de {platform}.\n"
        "NO se guardaron cookies."
    )
    return False



def sincronizar_perfiles_locales():
    """Busca carpetas en 'profiles' y las registra en la DB si no existen."""
    if not os.path.exists("profiles"):
        return

    carpetas = [d for d in os.listdir("profiles") if os.path.isdir(os.path.join("profiles", d))]
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    for alias in carpetas:
        # Verificar si ya existe en la DB
        c.execute("SELECT alias FROM cuentas WHERE alias=?", (alias,))
        if not c.fetchone():
            # Intentar adivinar la plataforma por el nombre (ej: fb_ o tik_)
            platform = "facebook"
            if alias.startswith("tik_"): platform = "tiktok"
            elif alias.startswith("yt_"): platform = "youtube"
            elif alias.startswith("ig_"): platform = "instagram"
            
            # Insertar cuenta básica (usuario y pass vacíos, se usarán las cookies)
            c.execute("INSERT INTO cuentas (alias, platform, username, password) VALUES (?, ?, ?, ?)",
                      (alias, platform, "Pendiente", "Pendiente"))
            print(f"✅ Perfil detectado y vinculado: {alias}")
            
    conn.commit()
    conn.close()

def importar_perfil_especifico(alias):
    """Registra una carpeta de perfil asegurando que no choque con otras."""
    import sqlite3
    conn = sqlite3.connect("cuentas.db")
    c = conn.cursor()
    
    # 1. Detección ESTRICTA de plataforma
    if alias.startswith("tik_"): 
        platform = "tiktok"
    elif alias.startswith("fb_") or "wendy" in alias or "tatiana" in alias:
        platform = "facebook"
    else:
        platform = "facebook" # Default seguro

    try:
        # 2. Usamos INSERT OR REPLACE pero manteniendo los campos de cookies limpios 
        # para que no use cookies viejas de la carpeta si es Facebook
        c.execute("""
            INSERT OR REPLACE INTO cuentas (alias, platform, username, password, cookies) 
            VALUES (?, ?, ?, ?, NULL)
        """, (alias, platform, "Importado", "Importado"))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error en Importación: {e}")
        return False
    finally:
        conn.close()
# login_manager.py (Fragmento a añadir/reemplazar)

# ==============================================================================
#           NUEVAS FUNCIONES PARA FILTRADO Y CAMUFLAJE AVANZADO
# ==============================================================================

def obtener_cuentas_por_plataforma(platform):
    """Filtra cuentas desde SQLite específicamente por plataforma"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Busca coincidencias exactas en la columna platform
    c.execute("SELECT alias FROM cuentas WHERE platform = ? ORDER BY alias ASC", (platform.lower(),))
    rows = c.fetchall()
    conn.close()
    
    # Si no encuentra por columna, intenta buscar por prefijo (fallback)
    if not rows:
        prefix_map = {"facebook": "fb_", "instagram": "ig_", "tiktok": "tik_", "youtube": "yt_", "twitter": "tw_"}
        prefix = prefix_map.get(platform.lower(), "")
        if prefix:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT alias FROM cuentas WHERE alias LIKE ? ORDER BY alias ASC", (f"{prefix}%",))
            rows = c.fetchall()
            conn.close()

    return [r[0] for r in rows] if rows else ["Sin cuentas"]

def aplicar_stealth_avanzado(page):
    """
    Inyecta JavaScript para falsificar huellas digitales de hardware (Canvas, WebGL, Audio).
    Esto hace que cada navegador parezca un dispositivo único.
    """
    stealth_script = """
    (() => {
        // 1. Ocultar WebDriver
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        
        // 2. Falsificar Hardware (RAM y Nucleos aleatorios entre valores comunes)
        const memory = [4, 8, 16, 32][Math.floor(Math.random() * 4)];
        const cores = [4, 8, 12, 16][Math.floor(Math.random() * 4)];
        Object.defineProperty(navigator, 'deviceMemory', { get: () => memory });
        Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => cores });

        // 3. Ruido en Canvas (Evita Canvas Fingerprinting exacto)
        const originalGetImageData = CanvasRenderingContext2D.prototype.getImageData;
        CanvasRenderingContext2D.prototype.getImageData = function(x, y, w, h) {
            const image = originalGetImageData.apply(this, arguments);
            // Modificamos sutilmente un píxel aleatorio para cambiar el hash
            const i = Math.floor(Math.random() * (image.data.length / 4)) * 4;
            image.data[i] = image.data[i] + (Math.random() > 0.5 ? 1 : -1);
            return image;
        };
        
        // 4. Ruido en WebGL
        const getParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {
            if (parameter === 37445) return 'Intel Open Source Technology Center'; // UNMASKED_VENDOR_WEBGL
            if (parameter === 37446) return 'Mesa DRI Intel(R) UHD Graphics 620 (Kabylake GT2)'; // UNMASKED_RENDERER_WEBGL
            return getParameter.apply(this, [parameter]);
        };
    })();
    """
    page.add_init_script(stealth_script)
    
# EJECUTAR AL INICIO
init_db()
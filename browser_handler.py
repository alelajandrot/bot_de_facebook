import os
from playwright.sync_api import sync_playwright
from login_manager import obtener_datos_cuenta, aplicar_stealth_avanzado

def get_browser_context(p, alias, headless=False, log_callback=print):
    """Configura el navegador con proxies y evasión de huella digital"""
    if not os.path.exists("profiles"): os.makedirs("profiles")
    user_data_path = os.path.join(os.getcwd(), "profiles", alias)

    # Argumentos Anti-Detección
    args = [
        '--disable-blink-features=AutomationControlled',
        '--start-maximized',
        '--no-sandbox',
        '--disable-infobars',
        '--disable-extensions',
        '--disable-popup-blocking'
    ]

    # User Agent Real Fijo (Importante para evitar bloqueos por cambio de identidad)
    ua_real = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    
    # Configuración de Proxy
    creds = obtener_datos_cuenta(alias)
    proxy_config = {"server": creds["proxy"]} if creds.get("proxy") else None

    if log_callback:
        log_callback(f"🕵️ Abriendo navegador para: {alias}", "INFO")
    
    try:
        # Intenta usar Google Chrome instalado
        context = p.chromium.launch_persistent_context(
            user_data_dir=user_data_path,
            channel="chrome",
            headless=headless,
            args=args,
            user_agent=ua_real,
            viewport=None,
            proxy=proxy_config,
            ignore_default_args=["--enable-automation"],
            locale="es-CO"
        )
    except Exception:
        # Fallback a Chromium interno
        context = p.chromium.launch_persistent_context(
            user_data_dir=user_data_path,
            headless=headless,
            args=args,
            user_agent=ua_real,
            viewport=None,
            proxy=proxy_config,
            ignore_default_args=["--enable-automation"]
        )

    # Inyección de Scripts de Camuflaje (Canvas, WebGL, etc)
    aplicar_stealth_avanzado(context)
    
    return context
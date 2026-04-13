import os
import random
import json
from playwright.sync_api import sync_playwright
from login_manager import obtener_datos_cuenta, aplicar_stealth_avanzado, guardar_huella_digital
from urllib.parse import urlparse

def get_browser_context(p, alias, headless=False, log_callback=print, mobile_proxy=None):
    if not os.path.exists("profiles"): os.makedirs("profiles")
    user_data_path = os.path.join(os.getcwd(), "profiles", alias)

    args = [
        '--disable-blink-features=AutomationControlled',
        '--start-maximized',
        '--no-sandbox',
        '--disable-infobars',
        '--disable-extensions',
        '--disable-popup-blocking',
        '--force-webrtc-ip-handling-policy=disable_non_proxied_udp',
        '--disable-features=WebRtcHideLocalIpsWithMdns'
    ]

    # 1. OBTENER DATOS DE LA CUENTA
    creds = obtener_datos_cuenta(alias)

    # 2. LÓGICA DE HUELLA DIGITAL ESTÁTICA
    ua_real = creds.get("user_agent")
    viewport_str = creds.get("viewport")
    tz = creds.get("timezone")
    
    needs_save = False
    
    # Si no tiene User-Agent guardado, generar uno
    if not ua_real:
        ua_candidates = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:116.0) Gecko/20100101 Firefox/116.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15"
        ]
        ua_real = random.choice(ua_candidates)
        needs_save = True

    # Si no tiene Viewport guardado, generar uno (guardado como texto JSON)
    if not viewport_str:
        viewports = ['null', '{"width": 1366, "height": 768}', '{"width": 1920, "height": 1080}', '{"width": 1600, "height": 900}']
        viewport_str = random.choice(viewports)
        needs_save = True

    # Si no tiene Timezone guardado, generar uno
    if not tz:
        tz = random.choice(["America/Bogota", "America/Mexico_City", "America/Los_Angeles", "Europe/Madrid"])
        needs_save = True

    # Guardar en la DB si generamos datos nuevos
    if needs_save:
        guardar_huella_digital(alias, ua_real, viewport_str, tz)
        if log_callback:
            log_callback(f"🛡️ Nueva huella digital asignada y guardada para: {alias}", "SUCCESS")

    # Convertir el string del viewport de vuelta a diccionario para Playwright
    chosen_viewport = json.loads(viewport_str) if viewport_str and viewport_str != 'null' else None

    # 3. CONFIGURACIÓN DE PROXY
    proxy_config = None
    if mobile_proxy:
        try:
            parsed = urlparse(mobile_proxy)
            proxy_config = {"server": f"{parsed.scheme}://{parsed.hostname}:{parsed.port}"}
            if parsed.username and parsed.password:
                proxy_config["username"] = parsed.username
                proxy_config["password"] = parsed.password
            if log_callback:
                log_callback(f"📱 Usando proxy móvil: {proxy_config['server']}", "INFO")
        except Exception as e:
            if log_callback:
                log_callback(f"⚠️ Error parseando proxy móvil: {e}", "WARN")
    elif creds.get("proxy"):
        proxy_config = {"server": creds["proxy"]}

    if log_callback:
        proxy_msg = proxy_config.get('server', 'N/A') if proxy_config else "Sin proxy"
        log_callback(f"🕵️ Abriendo navegador para: {alias} (Proxy: {proxy_msg})", "INFO")

    # 4. LANZAR NAVEGADOR
    try:
        context = p.chromium.launch_persistent_context(
            user_data_dir=user_data_path,
            channel="chrome",
            headless=headless,
            args=args,
            user_agent=ua_real,
            viewport=chosen_viewport,
            proxy=proxy_config,
            ignore_default_args=["--enable-automation"],
            locale="es-CO",
            timezone_id=tz,
            extra_http_headers={"Accept-Language": "es-ES,es;q=0.9,en;q=0.8"}
        )
    except Exception as e:
        if log_callback:
            log_callback(f"⚠️ Chrome nativo falló ({e}). Usando Chromium interno...", "WARN")
            
        context = p.chromium.launch_persistent_context(
            user_data_dir=user_data_path,
            headless=headless,
            args=args,
            user_agent=ua_real,
            viewport=chosen_viewport,
            proxy=proxy_config,
            ignore_default_args=["--enable-automation"],
            extra_http_headers={"Accept-Language": "es-ES,es;q=0.9,en;q=0.8"}
        )

    aplicar_stealth_avanzado(context)
    
    try:
        webrtc_blocker = r"""
        (function() {
            try {
                const NOOP = function() { throw new Error('RTCPeerConnection blocked'); };
                window.RTCPeerConnection = NOOP;
                window.webkitRTCPeerConnection = NOOP;
                if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
                    navigator.mediaDevices.getUserMedia = function() { return Promise.reject(new Error('getUserMedia blocked')); };
                }
                if (navigator.mediaDevices && navigator.mediaDevices.enumerateDevices) {
                    navigator.mediaDevices.enumerateDevices = function() { return Promise.resolve([]); };
                }
            } catch (e) {}
        })();
        """
        context.add_init_script(webrtc_blocker)
    except Exception as e:
        pass

    return context
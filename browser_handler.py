import os
import random
from playwright.sync_api import sync_playwright
from login_manager import obtener_datos_cuenta, aplicar_stealth_avanzado
from urllib.parse import urlparse

def get_browser_context(p, alias, headless=False, log_callback=print, mobile_proxy=None):
    """
    Configura el navegador con proxies y evasión de huella digital
    
    Args:
        p: Instancia de Playwright
        alias: Alias de la cuenta
        headless: Modo headless
        log_callback: Función de logging
        mobile_proxy: Proxy móvil (formato: "http://ip:puerto") - tiene prioridad sobre proxy de cuenta
    """
    if not os.path.exists("profiles"): os.makedirs("profiles")
    user_data_path = os.path.join(os.getcwd(), "profiles", alias)

    # Argumentos Anti-Detección
    args = [
        '--disable-blink-features=AutomationControlled',
        '--start-maximized',
        '--no-sandbox',
        '--disable-infobars',
        '--disable-extensions',
        '--disable-popup-blocking',
        # Mitigaciones WebRTC para evitar fugas de IP local
        # Fuerza el uso de proxy/relay y evita el uso de interfaces UDP sin proxy
        '--force-webrtc-ip-handling-policy=disable_non_proxied_udp',
        # Deshabilita características experimentales relacionadas si están presentes
        '--disable-features=WebRtcHideLocalIpsWithMdns'
    ]

    # User Agent: elegir uno aleatorio de una lista de UAs modernas
    ua_candidates = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:116.0) Gecko/20100101 Firefox/116.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15"
    ]
    ua_real = random.choice(ua_candidates)
    
    # Configuración de Proxy (Prioridad: mobile_proxy > proxy de cuenta)
    proxy_config = None
    
    if mobile_proxy:
        # Usar proxy móvil si está disponible
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
    
    if not proxy_config:
        # Fallback a proxy de cuenta (comportamiento original)
        creds = obtener_datos_cuenta(alias)
        proxy_config = {"server": creds["proxy"]} if creds.get("proxy") else None

    if log_callback:
        if proxy_config:
            log_callback(f"🕵️ Abriendo navegador para: {alias} (Proxy: {proxy_config.get('server', 'N/A')})", "INFO")
        else:
            log_callback(f"🕵️ Abriendo navegador para: {alias} (Sin proxy)", "INFO")
    
    try:
        # Intenta usar Google Chrome instalado
        # Elegir viewport aleatorio de tamaños típicos para simular distintos dispositivos/monitores
        viewports = [None, {"width":1366, "height":768}, {"width":1920, "height":1080}, {"width":1600, "height":900}]
        chosen_viewport = random.choice(viewports)

        # Timezone y headers para parecer más real
        tz = random.choice(["America/Bogota", "America/Mexico_City", "America/Los_Angeles", "Europe/Madrid"])

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
    except Exception:
        # Fallback a Chromium interno
        context = p.chromium.launch_persistent_context(
            user_data_dir=user_data_path,
            headless=headless,
            args=args,
            user_agent=ua_real,
            viewport=chosen_viewport if 'chosen_viewport' in locals() else None,
            proxy=proxy_config,
            ignore_default_args=["--enable-automation"],
            extra_http_headers={"Accept-Language": "es-ES,es;q=0.9,en;q=0.8"}
        )

    # Inyección de Scripts de Camuflaje (Canvas, WebGL, etc)
    aplicar_stealth_avanzado(context)
    # Defender contra fugas WebRTC mediante script inyectado en cada página
    try:
        webrtc_blocker = r"""
        // Bloqueo simple de WebRTC para evitar fugas de IPs locales
        (function() {
            try {
                // Sobrescribir RTCPeerConnection
                const NOOP = function() { throw new Error('RTCPeerConnection blocked by bot policy'); };
                window.RTCPeerConnection = NOOP;
                window.webkitRTCPeerConnection = NOOP;

                // Sobrescribir getUserMedia
                if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
                    navigator.mediaDevices.getUserMedia = function() { return Promise.reject(new Error('getUserMedia blocked')); };
                }

                // Evitar enumerateDevices (puede revelar dispositivos)
                if (navigator.mediaDevices && navigator.mediaDevices.enumerateDevices) {
                    navigator.mediaDevices.enumerateDevices = function() { return Promise.resolve([]); };
                }
            } catch (e) {
                // no-op
            }
        })();
        """
        context.add_init_script(webrtc_blocker)
        if log_callback:
            log_callback("🔒 WebRTC mitigations injected into context", "INFO")
    except Exception as e:
        if log_callback:
            log_callback(f"⚠️ No se pudo inyectar mitigación WebRTC: {e}", "WARN")

    return context
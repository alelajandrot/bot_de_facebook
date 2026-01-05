import time
import re
import random
from playwright.sync_api import sync_playwright
from browser_handler import get_browser_context
from login_manager import manejar_login
from utils import simulate_human_behavior, human_sleep, save_screenshot_log

class SocialActions:
    """
    Contiene la lógica de automatización para cada acción social.
    Métodos estáticos para facilitar la ejecución en hilos paralelos.
    """

    # =========================================================================
    #                               FACEBOOK (CORREGIDO)
    # =========================================================================
    @staticmethod
    def fb_reaction(alias, url, reaction, headless, logger, update_preview_cb):
        if not url: return
        with sync_playwright() as p:
            context = get_browser_context(p, alias, headless, logger)
            page = manejar_login(context, alias, headless)
            if page:
                try:
                    logger(f"Navegando al post: {url[:30]}...", "INFO")
                    page.goto(url)
                    simulate_human_behavior(page)
                    
                    # 1. Buscar el botón "Me gusta" (o el que ya esté activo) para hacer Hover
                    like_btn = page.locator('div[role="button"], span[role="button"]').filter(has_text=re.compile(r"^Me gusta$|^Like$", re.IGNORECASE)).first
                    
                    # Si no encuentra el texto, busca por aria-label (más robusto)
                    if not like_btn.is_visible(): 
                        like_btn = page.locator('[aria-label="Me gusta"], [aria-label="Like"]').first
                    
                    if like_btn.is_visible():
                        if reaction == "Me gusta":
                            # Clic directo con fuerza para evitar bloqueos de UI
                            like_btn.click(force=True)
                            logger(f"FB: Like simple enviado ({alias})", "SUCCESS")
                        else:
                            # 2. Desplegar el menú de reacciones
                            logger(f"FB: Desplegando reacciones...", "INFO")
                            like_btn.hover(force=True)
                            human_sleep(1.5, 3) # Tiempo vital para que aparezca el dock
                            
                            # Mapeo de reacciones (Español/Inglés)
                            map_react = {
                                "Me encanta": "Love", 
                                "Me divierte": "Haha", 
                                "Me asombra": "Wow", 
                                "Me entristece": "Sad", 
                                "Me enoja": "Angry"
                            }
                            eng = map_react.get(reaction, reaction)
                            
                            # 3. SELECTOR MEJORADO (SOLUCIÓN AL ERROR)
                            # Usamos coincidencia EXACTA en aria-label para evitar el error "Me encanta: 4 personas"
                            # Y buscamos dentro del dock de reacciones (role="toolbar" o similar implícito)
                            btn_react = page.locator(f'[aria-label="{reaction}"], [aria-label="{eng}"]').first
                            
                            if btn_react.is_visible():
                                # --- LA CLAVE DEL ARREGLO ---
                                # force=True atraviesa el <canvas> que interceptaba el clic
                                btn_react.click(force=True)
                                logger(f"FB: Reacción '{reaction}' enviada ({alias})", "SUCCESS")
                            else:
                                # Intento de respaldo: Clic por JS si Playwright falla visualmente
                                logger(f"Reacción visual falló, intentando inyección JS...", "WARN")
                                found = page.evaluate(f"""(reactName) => {{
                                    const labels = Array.from(document.querySelectorAll('[aria-label]'));
                                    const btn = labels.find(el => el.ariaLabel === reactName);
                                    if(btn) {{ btn.click(); return true; }}
                                    return false;
                                }}""", reaction)
                                
                                if found:
                                    logger(f"FB: Reacción '{reaction}' enviada por JS ({alias})", "SUCCESS")
                                else:
                                    logger(f"Reacción {reaction} no encontrada, dando Like normal.", "WARN")
                                    like_btn.click(force=True)
                        
                        save_screenshot_log(page, alias, "fb_react")
                        update_preview_cb()
                    else:
                        logger(f"FB: Botón base 'Me gusta' no encontrado. ¿Post privado/borrado?", "ERROR")
                        save_screenshot_log(page, alias, "error_fb_btn")
                        
                except Exception as e:
                    logger(f"Error FB React ({alias}): {e}", "ERROR")
            context.close()

    @staticmethod
    def fb_comment(alias, url, text, headless, logger, update_preview_cb):
        if not url or not text: return
        with sync_playwright() as p:
            context = get_browser_context(p, alias, headless, logger)
            page = manejar_login(context, alias, headless)
            if page:
                try:
                    page.goto(url)
                    simulate_human_behavior(page)
                    page.keyboard.press("End")
                    human_sleep(1, 2)
                    
                    # Intentar abrir caja de comentario si está colapsada
                    btn_comm = page.locator('div[role="button"]').filter(has_text=re.compile(r"Comentar|Comment", re.IGNORECASE)).first
                    if btn_comm.is_visible(): 
                        btn_comm.click(force=True)
                        human_sleep(1, 2)
                    
                    # Escribir en caja editable
                    box = page.locator('div[role="textbox"][contenteditable="true"]').first
                    if box.is_visible():
                        box.click(force=True)
                        # Escribir con retardo humano
                        page.keyboard.type(text, delay=random.randint(50, 150))
                        human_sleep(0.5, 1.5)
                        page.keyboard.press("Enter")
                        
                        logger(f"FB: Comentario publicado ({alias})", "SUCCESS")
                        save_screenshot_log(page, alias, "fb_comment")
                        update_preview_cb()
                    else:
                        logger(f"FB: Caja de comentarios no accesible ({alias})", "ERROR")
                except Exception as e:
                    logger(f"Error FB Comment ({alias}): {e}", "ERROR")
            context.close()

    # =========================================================================
    #                               INSTAGRAM
    # =========================================================================
    @staticmethod
    # =========================================================================
    # REEMPLAZA ESTA FUNCIÓN EN TU ARCHIVO bot_logic.py
    # =========================================================================

    @staticmethod
    def ig_like(alias, url, headless, logger, update_preview_cb):
        if not url: return
        with sync_playwright() as p:
            context = get_browser_context(p, alias, headless, logger)
            page = manejar_login(context, alias, headless)
            if page:
                try:
                    logger(f"Navegando al post IG...", "INFO")
                    page.goto(url)
                    # Espera inicial para que cargue la interfaz
                    page.wait_for_timeout(3000) 
                    simulate_human_behavior(page)
                    
                    # 1. VERIFICAR ESTADO INICIAL
                    # Buscamos si YA tiene like (aria-label="Ya no me gusta" o "Unlike")
                    already_liked = page.locator('svg[aria-label="Ya no me gusta"], svg[aria-label="Unlike"]').first
                    if already_liked.is_visible():
                        logger(f"IG: Este post YA tenía like ({alias})", "WARN")
                        save_screenshot_log(page, alias, "ig_already_liked")
                        context.close()
                        return

                    # 2. INTENTO PRINCIPAL: CLIC EN BOTÓN
                    logger("IG: Intentando dar Like...", "INFO")
                    like_svg = page.locator('svg[aria-label="Me gusta"], svg[aria-label="Like"]').first
                    
                    clicked = False
                    if like_svg.is_visible():
                        try:
                            # Intentamos clic en el padre (zona más grande)
                            like_svg.locator('xpath=..').click(force=True)
                            clicked = True
                        except:
                            like_svg.click(force=True)
                            clicked = True
                    
                    # Si no encontró botón, usa doble clic en imagen
                    if not clicked:
                        media = page.locator('article div[role="button"], article img').first
                        if media.is_visible():
                            media.dblclick(force=True, delay=100)
                            clicked = True
                            logger("IG: Botón no visto, usé Doble Clic.", "INFO")

                    # 3. VERIFICACIÓN INTELIGENTE (ESPERA ACTIVA)
                    # Esperamos hasta 5 segundos a que aparezca el estado "Ya no me gusta"
                    try:
                        # Buscamos el indicador de éxito
                        indicator = page.locator('svg[aria-label="Ya no me gusta"], svg[aria-label="Unlike"]')
                        indicator.wait_for(state="visible", timeout=5000)
                        logger(f"IG: ❤️ Like CONFIRMADO visualmente ({alias})", "SUCCESS")
                    except:
                        # 4. SOLO SI FALLA LA VERIFICACIÓN VISUAL, USAMOS PLAN B (TECLA L)
                        logger("IG: No se detectó cambio de color. Intentando tecla 'L'...", "WARN")
                        page.keyboard.press("l")
                        human_sleep(1, 2)
                        
                        # Verificación final post-teclazo
                        if page.locator('svg[aria-label="Ya no me gusta"], svg[aria-label="Unlike"]').is_visible():
                            logger(f"IG: Like recuperado con teclado ({alias})", "SUCCESS")
                        else:
                            logger(f"IG: Falló el Like definitivamente ({alias})", "ERROR")

                    save_screenshot_log(page, alias, "ig_like")
                    update_preview_cb()

                except Exception as e:
                    logger(f"Error IG Like ({alias}): {e}", "ERROR")
            context.close()



    @staticmethod
    def ig_comment(alias, url, text, headless, logger, update_preview_cb):
        if not url or not text: return
        with sync_playwright() as p:
            context = get_browser_context(p, alias, headless, logger)
            page = manejar_login(context, alias, headless)
            if page:
                try:
                    page.goto(url)
                    human_sleep(2, 4)
                    
                    area = page.locator('textarea[aria-label*="comentario"]').first
                    if area.is_visible():
                        area.click()
                        page.keyboard.type(text, delay=random.randint(50, 100))
                        human_sleep(0.5, 1)
                        page.keyboard.press("Enter")
                        logger(f"IG: Comentario enviado ({alias})", "SUCCESS")
                        save_screenshot_log(page, alias, "ig_comment")
                        update_preview_cb()
                    else:
                        logger(f"IG: Área de comentario no disponible ({alias})", "ERROR")
                except Exception as e:
                    logger(f"Error IG Comment ({alias}): {e}", "ERROR")
            context.close()

    # =========================================================================
    #                                TIKTOK
    # =========================================================================
    @staticmethod
    def tt_like(alias, url, headless, logger, update_preview_cb):
        if not url: return
        with sync_playwright() as p:
            context = get_browser_context(p, alias, headless, logger)
            page = manejar_login(context, alias, headless)
            if page:
                try:
                    page.goto(url)
                    simulate_human_behavior(page)
                    
                    btn = page.locator('span[data-e2e="like-icon"]').first
                    if btn.is_visible():
                        btn.click(force=True)
                        logger(f"TT: Like enviado ({alias})", "SUCCESS")
                        save_screenshot_log(page, alias, "tt_like")
                        update_preview_cb()
                    else:
                        logger(f"TT: Icono Like no encontrado ({alias})", "ERROR")
                except Exception as e:
                    logger(f"Error TT Like ({alias}): {e}", "ERROR")
            context.close()

    @staticmethod
    def tt_comment(alias, url, text, headless, logger, update_preview_cb):
        if not url or not text: return
        with sync_playwright() as p:
            context = get_browser_context(p, alias, headless, logger)
            page = manejar_login(context, alias, headless)
            if page:
                try:
                    page.goto(url)
                    human_sleep(2, 4)
                    
                    icon = page.locator('[data-e2e="comment-icon"]').first
                    if icon.is_visible(): icon.click()
                    
                    editor = page.locator('div[contenteditable="true"]').first
                    if editor.is_visible():
                        editor.click()
                        page.keyboard.type(text, delay=50)
                        human_sleep(0.5, 1)
                        page.keyboard.press("Enter")
                        logger(f"TT: Comentario enviado ({alias})", "SUCCESS")
                        save_screenshot_log(page, alias, "tt_comment")
                        update_preview_cb()
                    else:
                        logger(f"TT: Editor no accesible ({alias})", "ERROR")
                except Exception as e:
                    logger(f"Error TT Comment ({alias}): {e}", "ERROR")
            context.close()

    # =========================================================================
    #                                YOUTUBE
    # =========================================================================
    @staticmethod
    def yt_like(alias, url, headless, logger, update_preview_cb):
        if not url: return
        with sync_playwright() as p:
            context = get_browser_context(p, alias, headless, logger)
            page = manejar_login(context, alias, headless)
            if page:
                try:
                    page.goto(url)
                    simulate_human_behavior(page)
                    
                    btn = page.locator('button[aria-label^="Me gusta este video"], button[aria-label^="Like this video"]').first
                    if not btn.is_visible():
                        btn = page.locator('ytd-toggle-button-renderer#segmented-like-button button').first
                    
                    if btn.is_visible():
                        if btn.get_attribute("aria-pressed") == "true":
                            logger(f"YT: Video ya tenía Like ({alias})", "WARN")
                        else:
                            btn.click(force=True)
                            logger(f"YT: Like aplicado ({alias})", "SUCCESS")
                        save_screenshot_log(page, alias, "yt_like")
                        update_preview_cb()
                    else:
                        logger(f"YT: Botón Like no encontrado ({alias})", "ERROR")
                except Exception as e:
                    logger(f"Error YT Like ({alias}): {e}", "ERROR")
            context.close()

    @staticmethod
    def yt_comment(alias, url, text, headless, logger, update_preview_cb):
        if not url or not text: return
        with sync_playwright() as p:
            context = get_browser_context(p, alias, headless, logger)
            page = manejar_login(context, alias, headless)
            if page:
                try:
                    page.goto(url)
                    human_sleep(4, 6)
                    page.mouse.wheel(0, 600) # Scroll para cargar comentarios
                    human_sleep(2, 3)
                    
                    placeholder = page.locator('#placeholder-area').first
                    if placeholder.is_visible():
                        placeholder.click()
                        human_sleep(1, 2)
                        
                        input_box = page.locator('#contenteditable-root').first
                        if input_box.is_visible():
                            input_box.fill(text)
                            human_sleep(1, 2)
                            
                            submit_btn = page.locator('#submit-button button').first
                            submit_btn.click()
                            logger(f"YT: Comentario publicado ({alias})", "SUCCESS")
                            save_screenshot_log(page, alias, "yt_comment")
                            update_preview_cb()
                    else:
                        logger(f"YT: Sección comentarios no cargó ({alias})", "ERROR")
                except Exception as e:
                    logger(f"Error YT Comment ({alias}): {e}", "ERROR")
            context.close()

    # =========================================================================
    #                               TWITTER (X)
    # =========================================================================
    @staticmethod
    def x_like(alias, url, headless, logger, update_preview_cb):
        if not url: return
        with sync_playwright() as p:
            context = get_browser_context(p, alias, headless, logger)
            page = manejar_login(context, alias, headless)
            if page:
                try:
                    page.goto(url)
                    simulate_human_behavior(page)
                    
                    btn = page.locator('[data-testid="like"]').first
                    if btn.is_visible():
                        btn.click(force=True)
                        logger(f"X: Like enviado ({alias})", "SUCCESS")
                        save_screenshot_log(page, alias, "x_like")
                        update_preview_cb()
                    else:
                        logger(f"X: Botón Like no visible ({alias})", "ERROR")
                except Exception as e:
                    logger(f"Error X Like ({alias}): {e}", "ERROR")
            context.close()

    @staticmethod
    def x_reply(alias, url, text, headless, logger, update_preview_cb):
        if not url or not text: return
        with sync_playwright() as p:
            context = get_browser_context(p, alias, headless, logger)
            page = manejar_login(context, alias, headless)
            if page:
                try:
                    page.goto(url)
                    human_sleep(2, 4)
                    
                    page.locator('[data-testid="reply"]').first.click()
                    human_sleep(1, 2)
                    
                    page.keyboard.type(text, delay=50)
                    human_sleep(1, 2)
                    
                    page.locator('[data-testid="tweetButton"]').first.click()
                    logger(f"X: Respuesta enviada ({alias})", "SUCCESS")
                    save_screenshot_log(page, alias, "x_reply")
                    update_preview_cb()
                except Exception as e:
                    logger(f"Error X Reply ({alias}): {e}", "ERROR")
            context.close()

    # =========================================================================
    #                        CALENTAMIENTO (WARMUP)
    # =========================================================================
    @staticmethod
    def warmup(alias, minutes, headless, logger, update_preview_cb):
        """
        Rutina de navegación pasiva para generar historial y confianza (Cookies/Cache).
        """
        with sync_playwright() as p:
            context = get_browser_context(p, alias, headless, logger)
            page = manejar_login(context, alias, headless)
            
            if page:
                try:
                    logger(f"🔥 Iniciando Warmup: {alias} ({minutes} min)", "WARMUP")
                    start_time = time.time()
                    end_time = start_time + (minutes * 60)
                    
                    while time.time() < end_time:
                        remaining = int((end_time - time.time()) / 60)
                        logger(f"{alias}: Actividad en curso... (~{remaining}m restantes)", "INFO")
                        
                        # 1. Scroll natural
                        scroll_pixels = random.randint(300, 1500)
                        page.mouse.wheel(0, scroll_pixels)
                        human_sleep(3, 8)
                        
                        # 2. Movimiento de mouse
                        simulate_human_behavior(page)
                        
                        # 3. Pausa de "lectura" aleatoria
                        if random.random() > 0.8:
                            human_sleep(8, 15)
                            
                        # Actualizar UI
                        update_preview_cb()

                    logger(f"✅ Warmup completado para {alias}", "SUCCESS")
                except Exception as e:
                    logger(f"❌ Error en Warmup ({alias}): {e}", "ERROR")
            else:
                logger(f"❌ No se pudo iniciar sesión para Warmup ({alias})", "ERROR")
            
            context.close()
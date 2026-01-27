import time
import re
import random
from playwright.sync_api import sync_playwright
from browser_handler import get_browser_context
from login_manager import manejar_login
from utils import simulate_human_behavior, human_sleep, save_screenshot_log
from ai_provider import generate_comment_from_text, caption_from_image_url

class SocialActions:
    """
    Contiene la lógica de automatización para cada acción social.
    Métodos estáticos para facilitar la ejecución en hilos paralelos.
    """

    # =========================================================================
    #                               FACEBOOK (CORREGIDO)
    # =========================================================================
    @staticmethod
    def fb_reaction(alias, url, reaction, headless, logger, update_preview_cb, mobile_proxy=None, **kwargs):
        if not url: return
        with sync_playwright() as p:
            context = get_browser_context(p, alias, headless, logger, mobile_proxy=mobile_proxy)
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
    def fb_comment(alias, url, comments, headless, logger, update_preview_cb, mobile_proxy=None, **kwargs):
        if not url: return
        if isinstance(comments, str):
            comments = [comments]
        comments = [c.strip() for c in comments if c.strip()]

        # Si no hay comentarios y se solicita IA, intentamos generar uno contextual
        use_ai = kwargs.get('use_ai', False)
        ai_model = kwargs.get('ai_model', 'local_fallback')
        use_vision = kwargs.get('use_vision', False)

        count = len(comments)
        with sync_playwright() as p:
            context = get_browser_context(p, alias, headless, logger, mobile_proxy=mobile_proxy)
            page = manejar_login(context, alias, headless)
            if page:
                try:
                    page.goto(url)
                    simulate_human_behavior(page)
                    human_sleep(2, 4)
                    # Generar comentario con IA si es necesario
                    if (not comments or comments == [""]) and use_ai:
                        try:
                            post_text = page.evaluate("""() => {
                                const sel = document.querySelector('[data-testid="post_message"]') || document.querySelector('article');
                                return sel ? sel.innerText : document.body.innerText.slice(0,1000);
                            }""")
                        except Exception:
                            post_text = ""

                        generated = ""
                        if post_text and post_text.strip():
                            generated = generate_comment_from_text(post_text, model=ai_model, use_vision=use_vision)
                        elif use_vision:
                            try:
                                img = page.evaluate("""() => { const i = document.querySelector('article img'); return i ? i.src : null }""")
                            except Exception:
                                img = None
                            caption = caption_from_image_url(img)
                            generated = generate_comment_from_text(caption, model=ai_model, use_vision=use_vision)

                        if generated:
                            comments = [generated]

                    comentarios_realizados = 0
                    
                    for i, comment_text in enumerate(comments):
                        try:
                            logger(f"FB: Intentando comentario {i+1}/{count}: '{comment_text[:30]}...' ({alias})", "INFO")
                            
                            # Scroll para encontrar más posts si es necesario
                            if i > 0:
                                page.mouse.wheel(0, random.randint(300, 800))
                                human_sleep(2, 4)
                            
                            # Intentar abrir caja de comentario si está colapsada
                            btn_comm = page.locator('div[role="button"]').filter(has_text=re.compile(r"Comentar|Comment", re.IGNORECASE)).first
                            if btn_comm.is_visible(timeout=3000): 
                                btn_comm.click(force=True)
                                human_sleep(1, 2)
                            
                            # Escribir en caja editable
                            box = page.locator('div[role="textbox"][contenteditable="true"]').first
                            if box.is_visible(timeout=5000):
                                box.click(force=True)
                                human_sleep(0.5, 1)
                                
                                # Limpiar cualquier texto previo
                                page.keyboard.press("Control+A")
                                human_sleep(0.3, 0.5)
                                
                                # Escribir con retardo humano
                                page.keyboard.type(comment_text, delay=random.randint(50, 150))
                                human_sleep(0.5, 1.5)
                                page.keyboard.press("Enter")
                                human_sleep(2, 4)  # Esperar a que se publique
                                
                                comentarios_realizados += 1
                                logger(f"FB: Comentario {i+1} publicado: '{comment_text[:30]}...' ({alias})", "SUCCESS")
                            else:
                                logger(f"FB: Caja de comentarios no accesible en intento {i+1}", "WARN")
                                if i == 0:
                                    break  # Si el primero falla, salir
                        except Exception as e:
                            logger(f"FB: Error en comentario {i+1}: {e}", "WARN")
                            if i == 0:
                                break
                    
                    if comentarios_realizados > 0:
                        logger(f"FB: Total comentarios publicados: {comentarios_realizados}/{count} ({alias})", "SUCCESS")
                        save_screenshot_log(page, alias, "fb_comment")
                        update_preview_cb()
                    else:
                        logger(f"FB: No se pudo publicar ningún comentario ({alias})", "ERROR")
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
    def ig_like(alias, url, headless, logger, update_preview_cb, mobile_proxy=None, **kwargs):
        if not url: return
        with sync_playwright() as p:
            context = get_browser_context(p, alias, headless, logger, mobile_proxy=mobile_proxy)
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
    def ig_comment(alias, url, comments, headless, logger, update_preview_cb, mobile_proxy=None, **kwargs):
        if not url or not comments: return
        if isinstance(comments, str):
            comments = [comments]  # Convertir string único a lista
        comments = [c.strip() for c in comments if c.strip()]  # Filtrar vacíos
        if not comments: return
        
        count = len(comments)
        with sync_playwright() as p:
            context = get_browser_context(p, alias, headless, logger, mobile_proxy=mobile_proxy)
            page = manejar_login(context, alias, headless)
            if page:
                try:
                    page.goto(url)
                    human_sleep(3, 5)

                    # Si no hay comentarios y se solicita IA, generarlos
                    use_ai = kwargs.get('use_ai', False)
                    ai_model = kwargs.get('ai_model', 'local_fallback')
                    use_vision = kwargs.get('use_vision', False)

                    if (not comments or comments == [""]) and use_ai:
                        try:
                            post_text = page.evaluate("() => { const sel = document.querySelector('article') || document.querySelector('main'); return sel ? sel.innerText : document.body.innerText.slice(0,500); }")
                        except Exception:
                            post_text = ""

                        generated = ""
                        if post_text and post_text.strip():
                            generated = generate_comment_from_text(post_text, model=ai_model, use_vision=use_vision)
                        elif use_vision:
                            try:
                                img = page.evaluate("() => { const i = document.querySelector('article img'); return i ? i.src : null }")
                            except Exception:
                                img = None
                            caption = caption_from_image_url(img)
                            generated = generate_comment_from_text(caption, model=ai_model, use_vision=use_vision)

                        if generated:
                            comments = [generated]

                    comentarios_realizados = 0

                    for i, comment_text in enumerate(comments):
                        try:
                            logger(f"IG: Intentando comentario {i+1}/{count}: '{comment_text[:30]}...' ({alias})", "INFO")
                            
                            # Scroll para cargar más contenido si es necesario
                            if i > 0:
                                page.mouse.wheel(0, random.randint(200, 500))
                                human_sleep(2, 3)
                            
                            area = page.locator('textarea[aria-label*="comentario"], textarea[aria-label*="comment"]').first
                            if area.is_visible(timeout=5000):
                                area.click(force=True)
                                human_sleep(0.5, 1)
                                
                                # Limpiar cualquier texto previo
                                page.keyboard.press("Control+A")
                                human_sleep(0.3, 0.5)
                                
                                page.keyboard.type(comment_text, delay=random.randint(50, 100))
                                human_sleep(0.5, 1)
                                page.keyboard.press("Enter")
                                human_sleep(2, 4)  # Esperar publicación
                                
                                comentarios_realizados += 1
                                logger(f"IG: Comentario {i+1} enviado: '{comment_text[:30]}...' ({alias})", "SUCCESS")
                            else:
                                logger(f"IG: Área de comentario no disponible en intento {i+1}", "WARN")
                                if i == 0:
                                    break
                        except Exception as e:
                            logger(f"IG: Error en comentario {i+1}: {e}", "WARN")
                            if i == 0:
                                break
                    
                    if comentarios_realizados > 0:
                        logger(f"IG: Total comentarios publicados: {comentarios_realizados}/{count} ({alias})", "SUCCESS")
                        save_screenshot_log(page, alias, "ig_comment")
                        update_preview_cb()
                    else:
                        logger(f"IG: No se pudo publicar ningún comentario ({alias})", "ERROR")
                except Exception as e:
                    logger(f"Error IG Comment ({alias}): {e}", "ERROR")
            context.close()

    # =========================================================================
    #                                TIKTOK
    # =========================================================================
    @staticmethod
    def tt_like(alias, url, headless, logger, update_preview_cb, mobile_proxy=None, **kwargs):
        if not url: return
        with sync_playwright() as p:
            context = get_browser_context(p, alias, headless, logger, mobile_proxy=mobile_proxy)
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
    def tt_comment(alias, url, comments, headless, logger, update_preview_cb, mobile_proxy=None, **kwargs):
        if not url: return
        if isinstance(comments, str):
            comments = [comments]
        comments = [c.strip() for c in comments if c.strip()]

        use_ai = kwargs.get('use_ai', False)
        ai_model = kwargs.get('ai_model', 'local_fallback')
        use_vision = kwargs.get('use_vision', False)
        
        count = len(comments)
        with sync_playwright() as p:
            context = get_browser_context(p, alias, headless, logger, mobile_proxy=mobile_proxy)
            page = manejar_login(context, alias, headless)
            if page:
                try:
                    page.goto(url)
                    human_sleep(3, 5)

                    # Generar comentario con IA si está activado y no hay comentarios
                    if (not comments or comments == [""]) and use_ai:
                        try:
                            post_text = page.evaluate("() => { const sel = document.querySelector('article') || document.querySelector('main'); return sel ? sel.innerText : document.body.innerText.slice(0,500); }")
                        except Exception:
                            post_text = ""

                        generated = ""
                        if post_text and post_text.strip():
                            generated = generate_comment_from_text(post_text, model=ai_model, use_vision=use_vision)
                        elif use_vision:
                            try:
                                img = page.evaluate("() => { const i = document.querySelector('article img'); return i ? i.src : null }")
                            except Exception:
                                img = None
                            caption = caption_from_image_url(img)
                            generated = generate_comment_from_text(caption, model=ai_model, use_vision=use_vision)

                        if generated:
                            comments = [generated]
                    
                    comentarios_realizados = 0
                    
                    for i, comment_text in enumerate(comments):
                        try:
                            logger(f"TT: Intentando comentario {i+1}/{count}: '{comment_text[:30]}...' ({alias})", "INFO")
                            
                            # Abrir panel de comentarios si está cerrado
                            icon = page.locator('[data-e2e="comment-icon"]').first
                            if icon.is_visible(timeout=3000): 
                                icon.click()
                                human_sleep(1, 2)
                            
                            editor = page.locator('div[contenteditable="true"]').first
                            if editor.is_visible(timeout=5000):
                                editor.click(force=True)
                                human_sleep(0.5, 1)
                                
                                # Limpiar cualquier texto previo
                                page.keyboard.press("Control+A")
                                human_sleep(0.3, 0.5)
                                
                                page.keyboard.type(comment_text, delay=random.randint(40, 80))
                                human_sleep(0.5, 1)
                                page.keyboard.press("Enter")
                                human_sleep(2, 4)  # Esperar publicación
                                
                                comentarios_realizados += 1
                                logger(f"TT: Comentario {i+1} enviado: '{comment_text[:30]}...' ({alias})", "SUCCESS")
                            else:
                                logger(f"TT: Editor no accesible en intento {i+1}", "WARN")
                                if i == 0:
                                    break
                        except Exception as e:
                            logger(f"TT: Error en comentario {i+1}: {e}", "WARN")
                            if i == 0:
                                break
                    
                    if comentarios_realizados > 0:
                        logger(f"TT: Total comentarios publicados: {comentarios_realizados}/{count} ({alias})", "SUCCESS")
                        save_screenshot_log(page, alias, "tt_comment")
                        update_preview_cb()
                    else:
                        logger(f"TT: No se pudo publicar ningún comentario ({alias})", "ERROR")
                except Exception as e:
                    logger(f"Error TT Comment ({alias}): {e}", "ERROR")
            context.close()

    # =========================================================================
    #                                YOUTUBE
    # =========================================================================
    @staticmethod
    def yt_like(alias, url, headless, logger, update_preview_cb, mobile_proxy=None, **kwargs):
        if not url: return
        with sync_playwright() as p:
            context = get_browser_context(p, alias, headless, logger, mobile_proxy=mobile_proxy)
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
    def yt_comment(alias, url, comments, headless, logger, update_preview_cb, mobile_proxy=None, **kwargs):
        if not url or not comments: return
        if isinstance(comments, str):
            comments = [comments]  # Convertir string único a lista
        comments = [c.strip() for c in comments if c.strip()]  # Filtrar vacíos
        if not comments: return
        
        count = len(comments)
        with sync_playwright() as p:
            context = get_browser_context(p, alias, headless, logger, mobile_proxy=mobile_proxy)
            page = manejar_login(context, alias, headless)
            if page:
                try:
                    page.goto(url)
                    human_sleep(4, 6)
                    page.mouse.wheel(0, 600) # Scroll para cargar comentarios
                    human_sleep(2, 3)
                    
                    comentarios_realizados = 0
                    
                    for i, comment_text in enumerate(comments):
                        try:
                            logger(f"YT: Intentando comentario {i+1}/{count}: '{comment_text[:30]}...' ({alias})", "INFO")
                            
                            # Scroll adicional si es necesario
                            if i > 0:
                                page.mouse.wheel(0, random.randint(300, 600))
                                human_sleep(2, 3)
                            
                            placeholder = page.locator('#placeholder-area').first
                            if placeholder.is_visible(timeout=5000):
                                placeholder.click()
                                human_sleep(1, 2)
                                
                                input_box = page.locator('#contenteditable-root').first
                                if input_box.is_visible(timeout=3000):
                                    input_box.click(force=True)
                                    human_sleep(0.5, 1)
                                    
                                    # Limpiar cualquier texto previo
                                    page.keyboard.press("Control+A")
                                    human_sleep(0.3, 0.5)
                                    
                                    input_box.fill(comment_text)
                                    human_sleep(1, 2)
                                    
                                    submit_btn = page.locator('#submit-button button').first
                                    if submit_btn.is_visible():
                                        submit_btn.click()
                                        human_sleep(2, 4)  # Esperar publicación
                                        
                                        comentarios_realizados += 1
                                        logger(f"YT: Comentario {i+1} publicado: '{comment_text[:30]}...' ({alias})", "SUCCESS")
                                    else:
                                        logger(f"YT: Botón enviar no visible en intento {i+1}", "WARN")
                                else:
                                    logger(f"YT: Caja de texto no accesible en intento {i+1}", "WARN")
                                    if i == 0:
                                        break
                            else:
                                logger(f"YT: Sección comentarios no cargó en intento {i+1}", "WARN")
                                if i == 0:
                                    break
                        except Exception as e:
                            logger(f"YT: Error en comentario {i+1}: {e}", "WARN")
                            if i == 0:
                                break
                    
                    if comentarios_realizados > 0:
                        logger(f"YT: Total comentarios publicados: {comentarios_realizados}/{count} ({alias})", "SUCCESS")
                        save_screenshot_log(page, alias, "yt_comment")
                        update_preview_cb()
                    else:
                        logger(f"YT: No se pudo publicar ningún comentario ({alias})", "ERROR")
                except Exception as e:
                    logger(f"Error YT Comment ({alias}): {e}", "ERROR")
            context.close()

    # =========================================================================
    #                               TWITTER (X)
    # =========================================================================
    @staticmethod
    def x_like(alias, url, headless, logger, update_preview_cb, mobile_proxy=None, **kwargs):
        if not url: return
        with sync_playwright() as p:
            context = get_browser_context(p, alias, headless, logger, mobile_proxy=mobile_proxy)
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
    def x_reply(alias, url, comments, headless, logger, update_preview_cb, mobile_proxy=None, **kwargs):
        if not url or not comments: return
        if isinstance(comments, str):
            comments = [comments]  # Convertir string único a lista
        comments = [c.strip() for c in comments if c.strip()]  # Filtrar vacíos
        if not comments: return
        
        count = len(comments)
        with sync_playwright() as p:
            context = get_browser_context(p, alias, headless, logger, mobile_proxy=mobile_proxy)
            page = manejar_login(context, alias, headless)
            if page:
                try:
                    page.goto(url)
                    human_sleep(3, 5)
                    
                    respuestas_realizadas = 0
                    
                    for i, reply_text in enumerate(comments):
                        try:
                            logger(f"X: Intentando respuesta {i+1}/{count}: '{reply_text[:30]}...' ({alias})", "INFO")
                            
                            # Scroll si es necesario
                            if i > 0:
                                page.mouse.wheel(0, random.randint(200, 500))
                                human_sleep(2, 3)
                            
                            reply_btn = page.locator('[data-testid="reply"]').first
                            if reply_btn.is_visible(timeout=5000):
                                reply_btn.click()
                                human_sleep(1, 2)
                                
                                # Buscar el textarea de respuesta
                                textarea = page.locator('[data-testid="tweetTextarea_0"]').first
                                if textarea.is_visible(timeout=3000):
                                    textarea.click(force=True)
                                    human_sleep(0.5, 1)
                                    
                                    # Limpiar cualquier texto previo
                                    page.keyboard.press("Control+A")
                                    human_sleep(0.3, 0.5)
                                    
                                    page.keyboard.type(reply_text, delay=random.randint(40, 80))
                                    human_sleep(1, 2)
                                    
                                    tweet_btn = page.locator('[data-testid="tweetButton"]').first
                                    if tweet_btn.is_visible():
                                        tweet_btn.click()
                                        human_sleep(2, 4)  # Esperar publicación
                                        
                                        respuestas_realizadas += 1
                                        logger(f"X: Respuesta {i+1} enviada: '{reply_text[:30]}...' ({alias})", "SUCCESS")
                                        
                                        # Cerrar modal si está abierto para el siguiente intento
                                        if i < count - 1:
                                            try:
                                                page.keyboard.press("Escape")
                                                human_sleep(1, 2)
                                            except:
                                                pass
                                    else:
                                        logger(f"X: Botón enviar no visible en intento {i+1}", "WARN")
                                else:
                                    logger(f"X: Textarea no accesible en intento {i+1}", "WARN")
                                    if i == 0:
                                        break
                            else:
                                logger(f"X: Botón reply no encontrado en intento {i+1}", "WARN")
                                if i == 0:
                                    break
                        except Exception as e:
                            logger(f"X: Error en respuesta {i+1}: {e}", "WARN")
                            if i == 0:
                                break
                    
                    if respuestas_realizadas > 0:
                        logger(f"X: Total respuestas publicadas: {respuestas_realizadas}/{count} ({alias})", "SUCCESS")
                        save_screenshot_log(page, alias, "x_reply")
                        update_preview_cb()
                    else:
                        logger(f"X: No se pudo publicar ninguna respuesta ({alias})", "ERROR")
                except Exception as e:
                    logger(f"Error X Reply ({alias}): {e}", "ERROR")
            context.close()

    # =========================================================================
    #                        CALENTAMIENTO (WARMUP)
    # =========================================================================
    @staticmethod
    def warmup(alias, minutes, headless, logger, update_preview_cb, mobile_proxy=None, random_likes=False, **kwargs):
        """
        Rutina de navegación pasiva para generar historial y confianza (Cookies/Cache).
        Opcionalmente da me gustas ocasionales en publicaciones.
        """
        with sync_playwright() as p:
            context = get_browser_context(p, alias, headless, logger, mobile_proxy=mobile_proxy)
            page = manejar_login(context, alias, headless)
            
            if page:
                try:
                    logger(f"🔥 Iniciando Warmup: {alias} ({minutes} min)", "WARMUP")
                    if random_likes:
                        logger(f"👍 Me gustas ocasionales activados", "INFO")
                    
                    start_time = time.time()
                    end_time = start_time + (minutes * 60)
                    likes_count = 0
                    last_reload = time.time()
                    reload_interval = 120  # Recargar cada 2 minutos
                    
                    page.goto("https://www.facebook.com/")
                    page.wait_for_timeout(2000)
                    
                    while time.time() < end_time:
                        remaining = int((end_time - time.time()) / 60)
                        logger(f"{alias}: Actividad en curso... (~{remaining}m restantes)", "INFO")
                        
                        # Recargar página cada 2 minutos para nuevas publicaciones
                        current_time = time.time()
                        if current_time - last_reload > reload_interval:
                            logger(f"🔄 Recargando página para nuevas publicaciones...", "INFO")
                            page.reload()
                            page.wait_for_timeout(2500)
                            last_reload = current_time
                            human_sleep(1, 2)
                        
                        # 1. Dar me gusta ocasionalmente A VARIAS PUBLICACIONES
                        if random_likes and random.random() > 0.65:  # 35% de probabilidad
                            try:
                                # Buscar TODOS los botones "Me gusta" visibles en el feed
                                direct_likes = page.locator('button[aria-label="Me gusta"], button:has-text("Me gusta")')
                                likes_found = direct_likes.count()
                                
                                if likes_found > 0:
                                    # Dar me gusta a varios (no solo el primero)
                                    num_to_like = random.randint(1, min(likes_found, 3))  # Dar me gusta a 1-3
                                    liked_indices = random.sample(range(likes_found), num_to_like)
                                    
                                    for idx in liked_indices:
                                        try:
                                            like_btn = direct_likes.nth(idx)
                                            if like_btn.is_visible():
                                                like_btn.click(force=True)
                                                likes_count += 1
                                                logger(f"👍 Me gusta dado en feed ({likes_count})", "INFO")
                                                human_sleep(1, 2)
                                        except Exception:
                                            continue
                                else:
                                    # Intento 2: Buscar botón de reacciones
                                    reaction_buttons = page.locator(
                                        'button[aria-label*="Reaccion"], button[data-testid*="reaction"], '
                                        'div[role="button"][aria-label*="Reaccion"]'
                                    )
                                    
                                    if reaction_buttons.count() > 0:
                                        react_count = reaction_buttons.count()
                                        num_reactions = min(react_count, 2)
                                        react_indices = random.sample(range(react_count), num_reactions)
                                        
                                        for react_idx in react_indices:
                                            try:
                                                react_btn = reaction_buttons.nth(react_idx)
                                                if react_btn.is_visible():
                                                    react_btn.click(force=True)
                                                    page.wait_for_timeout(500)
                                                    
                                                    like_option = page.locator('button[aria-label="Me gusta"]')
                                                    if like_option.count() > 0:
                                                        like_option.first.click(force=True)
                                                        likes_count += 1
                                                        logger(f"👍 Me gusta dado en feed ({likes_count})", "INFO")
                                                        human_sleep(1, 2)
                                            except Exception:
                                                continue
                            except Exception as e:
                                logger(f"⚠️ Error dando me gustas: {str(e)[:50]}", "WARN")
                        
                        # 2. Hacer clic en videos/reels ocasionalmente
                        if random.random() > 0.75:  # 25% de probabilidad
                            try:
                                # Buscar videos/reels para hacer clic
                                video_links = page.locator('a[href*="/reel/"], a[href*="/video/"], a[href*="/watch/"]')
                                if video_links.count() > 0:
                                    video_idx = random.randint(0, min(video_links.count() - 1, 2))
                                    video_link = video_links.nth(video_idx)
                                    if video_link.is_visible():
                                        video_link.click(force=True)
                                        logger(f"🎬 Abriendo video/reel...", "INFO")
                                        page.wait_for_timeout(2000)
                                        
                                        # Dar me gusta al reel/video
                                        try:
                                            reel_likes = page.locator('button[aria-label="Me gusta"], svg[aria-label="Me gusta"]')
                                            if reel_likes.count() > 0:
                                                # Si es SVG, buscar su padre botón
                                                first_like = reel_likes.first
                                                try:
                                                    first_like.click(force=True)
                                                except:
                                                    # Si es SVG, buscar el botón padre
                                                    parent = first_like.locator('xpath=ancestor::button')
                                                    if parent.count() > 0:
                                                        parent.first.click(force=True)
                                                
                                                likes_count += 1
                                                logger(f"👍 Me gusta dado en reel/video ({likes_count})", "INFO")
                                                human_sleep(1.5, 2.5)
                                        except Exception as e:
                                            logger(f"⚠️ Error al dar me gusta al reel: {str(e)[:40]}", "WARN")
                                        
                                        # Salir del reel/video - usar go_back() en lugar de ESC
                                        try:
                                            # Intento 1: Buscar botón X o cerrar
                                            close_btns = page.locator('button[aria-label*="Cerrar"], button[aria-label*="Close"], svg[aria-label*="Cerrar"]')
                                            if close_btns.count() > 0:
                                                close_btns.first.click(force=True)
                                                logger(f"❌ Cerrando reel/video (botón cerrar)", "INFO")
                                                page.wait_for_timeout(1500)
                                            else:
                                                # Intento 2: Usar go_back() para volver a la página anterior
                                                logger(f"❌ Volviendo al feed (go_back)", "INFO")
                                                page.go_back()
                                                page.wait_for_timeout(2000)
                                        except Exception:
                                            # Intento 3: Si go_back() falla, ir directamente al home
                                            try:
                                                logger(f"❌ Volviendo al feed (home)", "INFO")
                                                page.goto("https://www.facebook.com/")
                                                page.wait_for_timeout(2000)
                                            except:
                                                pass
                                        
                                        human_sleep(1, 2)
                            except Exception as e:
                                logger(f"⚠️ Error con reel: {str(e)[:40]}", "WARN")
                        
                        # 3. Scroll natural - bajar y explorar el feed
                        scroll_pixels = random.randint(400, 1500)
                        page.mouse.wheel(0, scroll_pixels)
                        human_sleep(3, 8)
                        
                        # De vez en cuando, subir un poco para ver publicaciones anteriores (comportamiento natural)
                        if random.random() > 0.85:  # 15% de probabilidad
                            logger(f"⬆️ Subiendo en el feed (comportamiento natural)", "INFO")
                            scroll_up = random.randint(200, 600)
                            page.mouse.wheel(0, -scroll_up)
                            human_sleep(2, 4)
                        
                        # 4. Movimiento de mouse
                        simulate_human_behavior(page)
                        
                        # 4. Pausa de "lectura" aleatoria
                        if random.random() > 0.8:
                            human_sleep(8, 15)
                            
                        # Actualizar UI
                        update_preview_cb()

                    logger(f"✅ Warmup completado para {alias} ({likes_count} me gustas dados)", "SUCCESS")
                except Exception as e:
                    logger(f"❌ Error en Warmup ({alias}): {e}", "ERROR")
                finally:
                    context.close()
            else:
                logger(f"❌ No se pudo iniciar sesión para Warmup ({alias})", "ERROR")
                context.close()

    @staticmethod
    def find_and_add_friends(alias, headless, logger, update_preview_cb, mobile_proxy=None, limit=20, platform="facebook", **kwargs):
        """Busca sugerencias en el feed de la plataforma y envía solicitudes/solicita seguir hasta `limit`.
        Diseñado como proceso independiente del Warmup.
        """
        with sync_playwright() as p:
            context = get_browser_context(p, alias, headless, logger, mobile_proxy=mobile_proxy)
            page = manejar_login(context, alias, headless)
            if not page:
                context.close()
                return

            try:
                logger(f"🔎 Iniciando búsqueda de amigos: {alias} (máx {limit})", "WARMUP")

                # Para Facebook preferimos ir a la página de sugerencias de amigos
                fb_suggestions_paths = [
                    "/friends/suggestions/",
                    "/friends/suggestions",
                    "/friends/",
                    "/friends/suggested",
                    "/friends/center/suggestions/",
                ]

                navigated = False
                if platform == "facebook":
                    for pth in fb_suggestions_paths:
                        try:
                            page.goto(f"https://www.facebook.com{pth}")
                            # esperar un poco a que cargue contenido dinámico
                            page.wait_for_timeout(2000)
                            # si detectamos botones de 'Agregar a amigos' rompemos
                            if page.locator("button:has-text('Agregar a amigos'), button:has-text('Add Friend'), button:has-text('Agregar a amigo')").count() > 0:
                                navigated = True
                                break
                        except Exception:
                            continue

                    # si no encontramos la ruta específica, volvemos al feed y continuamos
                    if not navigated:
                        try:
                            page.goto("https://www.facebook.com/")
                            page.wait_for_timeout(1500)
                        except Exception:
                            pass

                elif platform == "instagram":
                    try:
                        page.goto("https://www.instagram.com/")
                        page.wait_for_timeout(1500)
                    except Exception:
                        pass

                sent = 0
                scroll_tries = 0
                # Búsqueda robusta de botones con texto localizable
                text_pattern = re.compile(r"Agregar a amigos|Agregar a amigo|Add Friend|Add friend|Agregar|Solicitar", re.IGNORECASE)

                while sent < int(limit) and scroll_tries < 60:
                    scroll_tries += 1
                    try:
                        # localizar botones que contengan el texto esperado
                        btns = page.locator('button').filter(has_text=text_pattern)
                        found = btns.count()
                    except Exception:
                        found = 0

                    if not found:
                        # scroll para cargar más sugerencias
                        page.mouse.wheel(0, random.randint(500, 1100))
                        human_sleep(1.5, 3)
                        simulate_human_behavior(page)
                        continue

                    for i in range(found):
                        if sent >= int(limit):
                            break
                        try:
                            b = btns.nth(i)
                            # verificar texto actual (por seguridad)
                            try:
                                txt = b.inner_text().strip()
                            except Exception:
                                txt = ""

                            # evitar botones no aplicables (seguir solamente) en FB si necesitamos 'agregar'
                            if platform == "facebook" and re.search(r"Seguir|Follow", txt, re.IGNORECASE):
                                continue

                            # intentar clic robusto
                            try:
                                b.click(force=True)
                            except Exception:
                                try:
                                    bbox = b.bounding_box()
                                    if bbox:
                                        cx = bbox['x'] + bbox['width']/2 + random.uniform(-4,4)
                                        cy = bbox['y'] + bbox['height']/2 + random.uniform(-4,4)
                                        page.mouse.move(int(cx), int(cy))
                                        page.mouse.click(int(cx), int(cy))
                                except Exception:
                                    continue

                            sent += 1
                            logger(f"{alias}: Solicitud enviada ({sent}/{limit})", "INFO")
                            human_sleep(1.8, 4)
                            simulate_human_behavior(page)
                            update_preview_cb()
                        except Exception:
                            continue

                    # avanzar en el feed para cargar más sugerencias
                    page.mouse.wheel(0, random.randint(600, 1300))
                    human_sleep(1, 2)
                    simulate_human_behavior(page)

                logger(f"✅ Búsqueda de amigos finalizada: {sent}/{limit} ({alias})", "SUCCESS")
                save_screenshot_log(page, alias, "friendfinder")
            except Exception as e:
                logger(f"❌ Error en FriendFinder ({alias}): {e}", "ERROR")
            finally:
                context.close()

    @staticmethod
    def search_and_add_friends(alias, search_term, headless, logger, update_preview_cb, mobile_proxy=None, limit=5, platform="facebook", **kwargs):
        """Busca personas en la sección de amigos y envía solicitudes de amistad.
        
        Args:
            alias: Alias de la cuenta
            search_term: Término de búsqueda (opcional)
            headless: Modo oculto
            logger: Función para registrar eventos
            update_preview_cb: Callback para actualizar preview
            mobile_proxy: Proxy móvil (opcional)
            limit: Máximo de solicitudes a enviar
            platform: Plataforma (facebook, instagram, etc.)
        """
        with sync_playwright() as p:
            context = get_browser_context(p, alias, headless, logger, mobile_proxy=mobile_proxy)
            page = manejar_login(context, alias, headless)
            if not page:
                context.close()
                return

            try:
                logger(f"🔍 Iniciando búsqueda de amigos ({alias})", "WARMUP")
                
                if platform == "facebook":
                    # PASO 1: Ir al HOME (una sola vez)
                    logger(f"📱 Ir al home de Facebook", "INFO")
                    page.goto("https://www.facebook.com/")
                    page.wait_for_timeout(2500)
                    
                    # PASO 2: Buscar el botón "Buscar amigos" en el sidebar
                    logger(f"🔎 Buscando botón 'Buscar amigos'...", "INFO")
                    
                    find_friends_clicked = False
                    
                    # Intentar hacer clic en el botón "Buscar amigos"
                    friend_search_selectors = [
                        'a:has-text("Buscar amigos")',
                        'a[href*="friends/suggestions"]',
                        'div:has-text("Buscar amigos")',
                        'a:has-text("Find Friends")'
                    ]
                    
                    for selector in friend_search_selectors:
                        try:
                            elements = page.locator(selector)
                            if elements.count() > 0:
                                logger(f"✓ Botón encontrado, presionando...", "INFO")
                                elements.first.click()
                                find_friends_clicked = True
                                page.wait_for_timeout(2500)
                                break
                        except Exception:
                            continue
                    
                    if not find_friends_clicked:
                        logger(f"⚠️ No se encontró el botón 'Buscar amigos'", "WARN")
                        context.close()
                        return
                    
                    # PASO 3: SOLO hacer clic en los botones "Agregar a amigos" (SIN MÁS NAVEGACIONES)
                    sent = 0
                    scroll_attempts = 0
                    max_attempts = 50
                    
                    while sent < int(limit) and scroll_attempts < max_attempts:
                        scroll_attempts += 1
                        
                        try:
                            # Buscar botones "Agregar a amigos"
                            buttons = page.locator('button:has-text("Agregar a amigos")')
                            count = buttons.count()
                            
                            if count == 0:
                                # No hay botones, hacer scroll
                                logger(f"📜 Cargando más personas...", "INFO")
                                page.mouse.wheel(0, random.randint(500, 900))
                                human_sleep(1.5, 2)
                                simulate_human_behavior(page)
                                continue
                            
                            logger(f"✓ Encontrados {count} botones 'Agregar a amigos'", "INFO")
                            
                            # Procesar cada botón
                            for i in range(count):
                                if sent >= int(limit):
                                    break
                                
                                try:
                                    btn = buttons.nth(i)
                                    
                                    # Verificar que sea visible
                                    if not btn.is_visible():
                                        continue
                                    
                                    # De vez en cuando, dar me gusta a una publicación
                                    if random.random() > 0.8:  # 20% de probabilidad
                                        try:
                                            # Intento 1: Buscar directamente el botón "Me gusta"
                                            direct_likes = page.locator('button[aria-label="Me gusta"], button:has-text("Me gusta")')
                                            if direct_likes.count() > 0:
                                                like_idx = random.randint(0, min(direct_likes.count() - 1, 2))
                                                like_btn = direct_likes.nth(like_idx)
                                                if like_btn.is_visible():
                                                    like_btn.click(force=True)
                                                    logger(f"👍 Me gusta dado", "INFO")
                                                    human_sleep(0.5, 1)
                                            else:
                                                # Intento 2: Buscar botón de reacciones y hacer clic en "Me gusta"
                                                reaction_btns = page.locator('button[aria-label*="Reaccion"]')
                                                if reaction_btns.count() > 0:
                                                    react_btn = reaction_btns.nth(0)
                                                    if react_btn.is_visible():
                                                        react_btn.click(force=True)
                                                        page.wait_for_timeout(400)
                                                        like_opt = page.locator('button[aria-label="Me gusta"]')
                                                        if like_opt.count() > 0:
                                                            like_opt.first.click(force=True)
                                                            logger(f"👍 Me gusta dado", "INFO")
                                                            human_sleep(0.5, 1)
                                        except Exception:
                                            pass
                                    
                                    # Hacer clic
                                    btn.click(force=True)
                                    sent += 1
                                    
                                    logger(f"✅ Solicitud {sent}/{limit}", "SUCCESS")
                                    human_sleep(2, 3)
                                    simulate_human_behavior(page)
                                    update_preview_cb()
                                    
                                except Exception as e:
                                    logger(f"⚠️ Error: {str(e)[:50]}", "WARN")
                                    continue
                            
                            # Si completamos, salir
                            if sent >= int(limit):
                                break
                            
                            # Scroll para más personas
                            page.mouse.wheel(0, random.randint(600, 1000))
                            human_sleep(1.5, 2.5)
                            
                        except Exception as e:
                            logger(f"⚠️ Error: {str(e)[:50]}", "WARN")
                            page.mouse.wheel(0, random.randint(400, 700))
                            human_sleep(1, 1.5)
                            continue
                    
                    logger(f"✅ Completado: {sent}/{limit} solicitudes", "SUCCESS")
                    save_screenshot_log(page, alias, "search_and_add")
                    
                elif platform == "instagram":
                    logger(f"⚠️ No soportado en Instagram", "WARN")
                else:
                    logger(f"⚠️ Plataforma no soportada", "WARN")
                    
            except Exception as e:
                logger(f"❌ Error: {str(e)[:100]}", "ERROR")
            finally:
                context.close()
            

            
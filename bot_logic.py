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
    """

    # =========================================================================
    #                               FACEBOOK
    # =========================================================================
    @staticmethod
    def fb_reaction(alias, url, reaction, headless, logger, update_preview_cb, mobile_proxy=None, **kwargs):
        if not url: 
            logger("⚠️ Error: URL vacía. No se puede iniciar.", "ERROR")
            return
            
        with sync_playwright() as p:
            try:
                context = get_browser_context(p, alias, headless, logger, mobile_proxy=mobile_proxy)
                page = manejar_login(context, alias, headless)
                if page:
                    logger(f"Navegando al post: {url[:30]}...", "INFO")
                    page.goto(url, timeout=60000)
                    simulate_human_behavior(page)
                    
                    # Buscar botón Me gusta
                    like_btn = page.locator('div[role="button"], span[role="button"]').filter(has_text=re.compile(r"^Me gusta$|^Like$", re.IGNORECASE)).first
                    if not like_btn.is_visible(): 
                        like_btn = page.locator('[aria-label="Me gusta"], [aria-label="Like"]').first
                    
                    if like_btn.is_visible():
                        if reaction == "Me gusta":
                            like_btn.click(force=True)
                            logger(f"FB: Like simple enviado ({alias})", "SUCCESS")
                        else:
                            # Reacciones complejas
                            logger(f"FB: Desplegando reacciones...", "INFO")
                            like_btn.hover(force=True)
                            human_sleep(1.5, 3)
                            
                            map_react = {"Me encanta": "Love", "Me divierte": "Haha", "Me asombra": "Wow", "Me entristece": "Sad", "Me enoja": "Angry"}
                            eng = map_react.get(reaction, reaction)
                            
                            btn_react = page.locator(f'[aria-label="{reaction}"], [aria-label="{eng}"]').first
                            if btn_react.is_visible():
                                btn_react.click(force=True)
                                logger(f"FB: Reacción '{reaction}' enviada ({alias})", "SUCCESS")
                            else:
                                logger(f"Reacción {reaction} no encontrada, dando Like normal.", "WARN")
                                like_btn.click(force=True)
                        
                        save_screenshot_log(page, alias, "fb_react")
                        update_preview_cb()
                    else:
                        logger(f"FB: Botón 'Me gusta' no encontrado. ¿Post privado?", "ERROR")
                        save_screenshot_log(page, alias, "error_fb_btn")
            except Exception as e:
                logger(f"Error FB React ({alias}): {e}", "ERROR")
            finally:
                try: context.close()
                except: pass

    @staticmethod
    def fb_comment(alias, url, comments, headless, logger, update_preview_cb, mobile_proxy=None, **kwargs):
        if not url: return
        if isinstance(comments, str): comments = [comments]
        comments = [c.strip() for c in comments if c.strip()]

        use_ai = kwargs.get('use_ai', False)
        ai_model = kwargs.get('ai_model', 'local_fallback')
        use_vision = kwargs.get('use_vision', False)

        with sync_playwright() as p:
            try:
                context = get_browser_context(p, alias, headless, logger, mobile_proxy=mobile_proxy)
                page = manejar_login(context, alias, headless)
                if page:
                    page.goto(url, timeout=60000)
                    simulate_human_behavior(page)
                    human_sleep(2, 4)

                    # Lógica IA
                    if (not comments or comments == [""]) and use_ai:
                        try:
                            post_text = page.evaluate("""() => {
                                const sel = document.querySelector('[data-testid="post_message"]') || document.querySelector('article');
                                return sel ? sel.innerText : document.body.innerText.slice(0,1000);
                            }""")
                            generated = generate_comment_from_text(post_text, model=ai_model)
                            if generated: comments = [generated]
                        except: pass

                    comentarios_realizados = 0
                    for i, comment_text in enumerate(comments):
                        try:
                            # Intentar abrir caja
                            btn_comm = page.locator('div[role="button"]').filter(has_text=re.compile(r"Comentar|Comment", re.IGNORECASE)).first
                            if btn_comm.is_visible(timeout=3000): btn_comm.click(force=True)
                            
                            box = page.locator('div[role="textbox"][contenteditable="true"]').first
                            if box.is_visible(timeout=5000):
                                box.click(force=True)
                                page.keyboard.type(comment_text, delay=random.randint(50, 150))
                                human_sleep(0.5, 1)
                                page.keyboard.press("Enter")
                                human_sleep(3, 5) # Espera importante para que se publique
                                comentarios_realizados += 1
                                logger(f"FB: Comentario enviado: '{comment_text[:20]}...'", "SUCCESS")
                        except Exception as e:
                            logger(f"Error comentando: {e}", "WARN")

                    if comentarios_realizados > 0:
                        save_screenshot_log(page, alias, "fb_comment")
                        update_preview_cb()
            except Exception as e:
                logger(f"Error FB Comment ({alias}): {e}", "ERROR")
            finally:
                try: context.close()
                except: pass

    # =========================================================================
    #                               INSTAGRAM (CORREGIDO)
    # =========================================================================
    @staticmethod
    def ig_like(alias, url, headless, logger, update_preview_cb, mobile_proxy=None, **kwargs):
        if not url: return
        with sync_playwright() as p:
            try:
                context = get_browser_context(p, alias, headless, logger, mobile_proxy=mobile_proxy)
                page = manejar_login(context, alias, headless)
                if page:
                    logger(f"Navegando al post IG...", "INFO")
                    page.goto(url, timeout=60000)
                    human_sleep(2, 4)
                    simulate_human_behavior(page)

                    # Verificar si ya tiene like
                    already_liked = page.locator('svg[aria-label="Ya no me gusta"], svg[aria-label="Unlike"]').first
                    if already_liked.is_visible():
                        logger(f"IG: Este post YA tenía like ({alias})", "WARN")
                    else:
                        # Intentar dar like
                        like_svg = page.locator('svg[aria-label="Me gusta"], svg[aria-label="Like"]').first
                        if like_svg.is_visible():
                            like_svg.click(force=True)
                        else:
                            # Fallback doble clic
                            page.locator('article img').first.dblclick(force=True)
                        
                        logger(f"IG: Like enviado ({alias})", "SUCCESS")
                        save_screenshot_log(page, alias, "ig_like")
                        update_preview_cb()
            except Exception as e:
                logger(f"Error IG Like ({alias}): {e}", "ERROR")
            finally:
                try: context.close()
                except: pass

    @staticmethod
    def ig_comment(alias, url, comments, headless, logger, update_preview_cb, mobile_proxy=None, **kwargs):
        if not url: return
        if isinstance(comments, str): comments = [comments]
        comments = [c.strip() for c in comments if c.strip()]

        with sync_playwright() as p:
            try:
                context = get_browser_context(p, alias, headless, logger, mobile_proxy=mobile_proxy)
                page = manejar_login(context, alias, headless)
                if page:
                    page.goto(url, timeout=60000)
                    human_sleep(3, 5)
                    
                    area = page.locator('textarea[aria-label*="comentario"], textarea[aria-label*="comment"]').first
                    if area.is_visible(timeout=5000):
                        for comment in comments:
                            area.click(force=True)
                            page.keyboard.type(comment, delay=random.randint(50, 100))
                            human_sleep(0.5, 1)
                            page.keyboard.press("Enter")
                            human_sleep(2, 4)
                            logger(f"IG: Comentario enviado ({alias})", "SUCCESS")
                        
                        save_screenshot_log(page, alias, "ig_comment")
                        update_preview_cb()
                    else:
                        logger("IG: Caja de comentarios no encontrada", "ERROR")
            except Exception as e:
                logger(f"Error IG Comment ({alias}): {e}", "ERROR")
            finally:
                try: context.close()
                except: pass

    # ... (MANTÉN EL RESTO DE MÉTODOS TT_LIKE, YT_LIKE, ETC. SIN CAMBIOS SI YA FUNCIONABAN) ...
    # Asegúrate de agregar el bloque finally: try: context.close() except: pass en todos.

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
                                            except Exception as e:
                                                logger(f"X: Aviso: No se pudo presionar Escape: {e}", "WARN")

                        
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
    def warmup(alias, minutes, headless, logger, update_preview_cb, mobile_proxy=None, random_likes=False, friend_requests=False, friend_request_limit=5, **kwargs):
        """
        Rutina de calentamiento COMPLETA:
        1. (Opcional) Busca amigos en sugerencias y envía solicitudes.
        2. Navega el feed, ve historias y da likes.
        """
        with sync_playwright() as p:
            context = get_browser_context(p, alias, headless, logger, mobile_proxy=mobile_proxy)
            page = manejar_login(context, alias, headless)
            
            if page:
                try:
                    logger(f"🔥 Warmup INICIADO: {alias} ({minutes} min)", "WARMUP")
                    
                    # =================================================================
                    # FASE 1: SOLICITUDES DE AMISTAD (Si está activado)
                    # =================================================================
                    if friend_requests:
                        try:
                            logger("👥 Fase 1: Buscando sugerencias de amistad...", "INFO")
                            # Navegar directamente a sugerencias (según tu imagen 2)
                            page.goto("https://www.facebook.com/friends/suggestions")
                            human_sleep(3, 5)
                            
                            enviadas = 0
                            intentos_scroll = 0
                            
                            while enviadas < friend_request_limit and intentos_scroll < 10:
                                # Buscar botones "Agregar a amigos" visibles
                                # Usamos selectores robustos para el texto en español
                                botones = page.locator('div[role="button"] span').filter(has_text="Agregar a amigos").all()
                                
                                # Si no hay botones, hacemos scroll
                                if not botones:
                                    logger("📜 Scrolleando para buscar más personas...", "INFO")
                                    page.mouse.wheel(0, random.randint(500, 800))
                                    human_sleep(2, 4)
                                    intentos_scroll += 1
                                    continue
                                
                                # Seleccionar un botón aleatorio de los visibles (comportamiento humano: no siempre es el primero)
                                btn = random.choice(botones[:4]) # Elegir entre los primeros 4 visibles
                                
                                if btn.is_visible():
                                    # Mover mouse hacia el botón suavemente
                                    btn.hover()
                                    human_sleep(0.5, 1.5) # "Pensar" si agregarlo
                                    
                                    # Clic
                                    btn.click()
                                    enviadas += 1
                                    logger(f"✅ Solicitud enviada ({enviadas}/{friend_request_limit})", "SUCCESS")
                                    
                                    # Pausa humana entre solicitudes (importante para evitar bloqueos)
                                    human_sleep(3, 7)
                                    
                                    # A veces, scrollear un poco después de agregar
                                    if random.random() > 0.5:
                                        page.mouse.wheel(0, random.randint(100, 300))
                                        human_sleep(1, 2)
                                
                                update_preview_cb()
                            
                            logger(f"👥 Fase de amigos completada. Volviendo al Feed...", "INFO")
                        except Exception as e:
                            logger(f"⚠️ Error en fase de amigos: {e}", "WARN")

                    # =================================================================
                    # FASE 2: NAVEGACIÓN EN FEED (STORIES + LIKES)
                    # =================================================================
                    start_time = time.time()
                    end_time = start_time + (minutes * 60)
                    likes_count = 0
                    stories_watched = 0
                    
                    if page.url != "https://www.facebook.com/":
                        page.goto("https://www.facebook.com/")
                    
                    human_sleep(3, 6)

                    while time.time() < end_time:
                        remaining = int((end_time - time.time()) / 60)
                        if remaining % 2 == 0: # Loguear cada tanto para no saturar
                             logger(f"{alias}: Navegando feed... (~{remaining}m restantes)", "INFO")

                        # 1. Ver Historias (Stories)
                        if random.random() > 0.85:
                            try:
                                stories = page.locator('div[aria-label^="Historia de"], div[aria-label^="Story by"]').first
                                if stories.is_visible():
                                    logger("👀 Viendo historia...", "INFO")
                                    stories.click()
                                    human_sleep(4, 10)
                                    page.keyboard.press("Escape")
                                    stories_watched += 1
                                    human_sleep(2, 3)
                            except: pass

                        # 2. Scroll y Lectura
                        scroll_amount = random.randint(300, 900)
                        page.mouse.wheel(0, scroll_amount)
                        human_sleep(2, 6) # Tiempo de lectura
                        
                        # 3. Dar Likes Ocasionales
                        if random_likes and random.random() > 0.75:
                            try:
                                # Busca botones "Me gusta" visibles usando lógica JS para asegurar visibilidad
                                like_selector = 'div[role="button"][aria-label="Me gusta"]'
                                found = page.evaluate(f"""() => {{
                                    const btns = Array.from(document.querySelectorAll('{like_selector}'));
                                    const visible = btns.find(b => {{
                                        const r = b.getBoundingClientRect();
                                        return r.top > 0 && r.bottom < window.innerHeight;
                                    }});
                                    if (visible) {{ visible.click(); return true; }}
                                    return false;
                                }}""")
                                
                                if found:
                                    likes_count += 1
                                    logger(f"👍 Like dado en feed ({likes_count})", "SUCCESS")
                                    human_sleep(1, 2)
                            except: pass

                        simulate_human_behavior(page)
                        update_preview_cb()

                    logger(f"✅ Warmup FINALIZADO: {alias} (Solicitudes: {enviadas if friend_requests else 0}, Likes: {likes_count})", "SUCCESS")
                
                except Exception as e:
                    logger(f"❌ Error Crítico en Warmup ({alias}): {e}", "ERROR")
                    save_screenshot_log(page, alias, "error_warmup")
                finally:
                    context.close()
            else:
                logger(f"❌ No se pudo iniciar sesión ({alias})", "ERROR")
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
    
    @staticmethod
    def fb_create_post(alias, text, image_path, headless, logger, update_preview_cb, mobile_proxy=None, **kwargs):
        from playwright.sync_api import sync_playwright
        from browser_handler import get_browser_context
        from login_manager import manejar_login
        from utils import human_sleep, save_screenshot_log
        import os

        if not os.path.exists(image_path):
            logger(f"❌ FB Post: La imagen no existe en la ruta {image_path}", "ERROR")
            return

        with sync_playwright() as p:
            try:
                context = get_browser_context(p, alias, headless, logger, mobile_proxy=mobile_proxy)
                page = manejar_login(context, alias, headless)
                
                if page:
                    logger(f"📝 Iniciando creación de publicación con imagen para {alias}...", "INFO")
                    page.goto("https://www.facebook.com/", timeout=60000)
                    human_sleep(3, 5)

                    # 1. Abrir la caja de "¿Qué estás pensando?"
                    crear_post_btn = page.locator('div[role="button"]:has-text("¿Qué estás pensando?"), div[role="button"]:has-text("What\'s on your mind")').first
                    crear_post_btn.click()
                    human_sleep(2, 4)

                    # 2. Escribir el texto
                    caja_texto = page.locator('div[role="textbox"][contenteditable="true"]').first
                    caja_texto.fill(text)
                    human_sleep(1, 2)

                    # 3. Interceptar la subida de archivo y hacer clic en el ícono de Foto/Video
                    with page.expect_file_chooser() as fc_info:
                        page.locator('div[aria-label="Foto/video"], div[aria-label="Photo/video"]').first.click()
                    
                    # Subir el archivo
                    file_chooser = fc_info.value
                    file_chooser.set_files(image_path)
                    logger("🖼️ Imagen cargada en el navegador...", "INFO")
                    human_sleep(4, 7) # Esperar a que la previsualización cargue

                    # 4. Publicar
                    btn_publicar = page.locator('div[aria-label="Publicar"], div[aria-label="Post"]').first
                    btn_publicar.click()
                    
                    logger("✅ Publicación enviada. Esperando confirmación...", "SUCCESS")
                    human_sleep(8, 12) # Espera crucial para que FB procese la subida

                    save_screenshot_log(page, alias, "fb_post_image")
                    update_preview_cb()

            except Exception as e:
                logger(f"Error FB Create Post ({alias}): {e}", "ERROR")
            finally:
                try: context.close()
                except: pass


    @staticmethod
    def fb_update_profile_picture(alias, image_path, headless, logger, update_preview_cb, mobile_proxy=None, **kwargs):
        from playwright.sync_api import sync_playwright
        from browser_handler import get_browser_context
        from login_manager import manejar_login
        from utils import human_sleep, save_screenshot_log
        import os

        if not os.path.exists(image_path):
            logger(f"❌ FB Perfil: La imagen no existe {image_path}", "ERROR")
            return

        with sync_playwright() as p:
            try:
                context = get_browser_context(p, alias, headless, logger, mobile_proxy=mobile_proxy)
                page = manejar_login(context, alias, headless)
                
                if page:
                    logger(f"👤 Actualizando foto de perfil para {alias}...", "INFO")
                    
                    # 1. Navegar al perfil (haciendo clic en la foto de la barra superior o yendo a /me)
                    page.goto("https://www.facebook.com/me", timeout=60000)
                    human_sleep(4, 6)

                    # 2. Hacer clic en la foto de perfil actual para cambiarla
                    btn_camara = page.locator('div[aria-label="Actualizar foto de perfil"], div[aria-label="Update profile picture"]').first
                    btn_camara.click()
                    human_sleep(2, 3)

                    # 3. Interceptar selector de archivos para "Subir foto"
                    with page.expect_file_chooser() as fc_info:
                        page.locator('div[role="button"]:has-text("Subir foto"), div[role="button"]:has-text("Upload photo")').first.click()
                    
                    file_chooser = fc_info.value
                    file_chooser.set_files(image_path)
                    logger("🖼️ Imagen subida, configurando recorte...", "INFO")
                    human_sleep(5, 8)

                    # 4. Guardar
                    btn_guardar = page.locator('div[aria-label="Guardar"], div[aria-label="Save"]').first
                    btn_guardar.click()
                    
                    logger("✅ Foto de perfil actualizada con éxito.", "SUCCESS")
                    human_sleep(5, 8) 

                    save_screenshot_log(page, alias, "fb_profile_pic")
                    update_preview_cb()

            except Exception as e:
                logger(f"Error FB Profile Pic ({alias}): {e}", "ERROR")
            finally:
                try: context.close()
                except: pass
            

            
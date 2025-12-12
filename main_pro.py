import customtkinter as ctk
import threading
import time
import random
import os
import re
from tkinter import messagebox
from playwright.sync_api import sync_playwright

# Importamos el login manager
try:
    from login_manager import manejar_login
except ImportError:
    messagebox.showerror("Error", "Falta el archivo login_manager.py")
    exit()

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class SocialBotApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.is_running = False 
        self.title("Social Bot Suite - Modular v3.0")
        self.geometry("1100x850")
        
        # Grid Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- SIDEBAR (Configuración General) ---
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        ctk.CTkLabel(self.sidebar, text="🤖 CONTROL PANEL", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, padx=20, pady=20)
        
        ctk.CTkLabel(self.sidebar, text="Cuenta (Cookies):").grid(row=1, column=0, sticky="w", padx=20)
        self.combo_cookies = ctk.CTkComboBox(self.sidebar, values=self.get_json_files())
        self.combo_cookies.grid(row=2, column=0, padx=20, pady=(0, 20))

        self.var_headless = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(self.sidebar, text="Ocultar Navegador", variable=self.var_headless).grid(row=3, column=0, padx=20, pady=10, sticky="w")

        ctk.CTkButton(self.sidebar, text="🔄 Recargar Cookies", command=self.refresh_cookies, fg_color="transparent", border_width=1).grid(row=4, column=0, padx=20, pady=20)

        # --- TABS PRINCIPALES ---
        self.tabs = ctk.CTkTabview(self)
        self.tabs.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")

        self.tab_fb = self.tabs.add("Facebook")
        self.tab_ig = self.tabs.add("Instagram")
        self.tab_x = self.tabs.add("X (Twitter)")

        self.setup_facebook_ui()
        self.setup_instagram_ui()
        self.setup_x_ui()

        # --- CONSOLA ---
        self.log_frame = ctk.CTkFrame(self, height=150)
        self.log_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        self.console = ctk.CTkTextbox(self.log_frame, height=120, font=("Consolas", 11))
        self.console.pack(fill="both", padx=10, pady=5)
        self.console.configure(state="disabled")

    # ================= UTILIDADES =================
    def log(self, msg, type="INFO"):
        ts = time.strftime("%H:%M:%S")
        icons = {"INFO": "ℹ️", "SUCCESS": "✅", "ERROR": "❌", "WARN": "⚠️"}
        text = f"[{ts}] {icons.get(type, '')} {msg}\n"
        self.console.configure(state="normal")
        self.console.insert("end", text)
        self.console.see("end")
        self.console.configure(state="disabled")
        print(text.strip())

    def get_json_files(self):
        files = [f for f in os.listdir('.') if f.endswith('.json') and f != "cuentas.json"]
        return files if files else ["Sin cookies"]

    def refresh_cookies(self):
        self.combo_cookies.configure(values=self.get_json_files())
        if self.get_json_files()[0] != "Sin cookies": self.combo_cookies.set(self.get_json_files()[0])

    def human_sleep(self, a=2, b=4):
        time.sleep(random.uniform(a, b))

    def start_thread(self, target_func):
        if self.is_running:
            self.log("Bot ocupado. Espera a que termine la acción actual.", "WARN")
            return
        self.is_running = True
        threading.Thread(target=target_func).start()

    def get_browser(self, p):
        return p.firefox.launch(headless=self.var_headless.get(), slow_mo=50)

    # =========================================================================
    #                               FACEBOOK
    # =========================================================================
    def setup_facebook_ui(self):
        f = self.tab_fb
        f.grid_columnconfigure((0, 1, 2), weight=1) # 3 Columnas

        # INPUT URL COMÚN
        ctk.CTkLabel(f, text="Link del Post de Facebook:", font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=3, pady=(10, 5))
        self.fb_url = ctk.CTkEntry(f, width=500, placeholder_text="https://www.facebook.com/...")
        self.fb_url.grid(row=1, column=0, columnspan=3, pady=(0, 20))

        # --- SECCIÓN 1: REACCIONES ---
        frame_react = ctk.CTkFrame(f)
        frame_react.grid(row=2, column=0, padx=10, sticky="nsew")
        ctk.CTkLabel(frame_react, text="😮 REACCIONES", font=("Arial", 14, "bold"), text_color="#f7b928").pack(pady=10)
        
        self.fb_react_combo = ctk.CTkComboBox(frame_react, values=["Me gusta", "Me encanta", "Me divierte", "Me importa", "Me asombra", "Me entristece", "Me enoja"])
        self.fb_react_combo.pack(pady=5)
        
        ctk.CTkButton(frame_react, text="Ejecutar Reacción", fg_color="#f7b928", text_color="black", 
                      command=lambda: self.start_thread(self.fb_logic_reaction)).pack(pady=15)

        # --- SECCIÓN 2: COMENTARIOS ---
        frame_comm = ctk.CTkFrame(f)
        frame_comm.grid(row=2, column=1, padx=10, sticky="nsew")
        ctk.CTkLabel(frame_comm, text="💬 COMENTAR", font=("Arial", 14, "bold"), text_color="#1877F2").pack(pady=10)
        
        self.fb_comment_txt = ctk.CTkTextbox(frame_comm, height=80)
        self.fb_comment_txt.pack(pady=5, padx=5)
        
        ctk.CTkButton(frame_comm, text="Enviar Comentario", fg_color="#1877F2", 
                      command=lambda: self.start_thread(self.fb_logic_comment)).pack(pady=15)

        # --- SECCIÓN 3: REPORTAR ---
        frame_rep = ctk.CTkFrame(f)
        frame_rep.grid(row=2, column=2, padx=10, sticky="nsew")
        ctk.CTkLabel(frame_rep, text="🚨 REPORTAR", font=("Arial", 14, "bold"), text_color="#e41e3f").pack(pady=10)
        
        self.fb_rep_combo = ctk.CTkComboBox(frame_rep, values=["Spam", "Violencia", "Acoso", "Información falsa", "Desnudos"])
        self.fb_rep_combo.pack(pady=5)
        
        ctk.CTkButton(frame_rep, text="Enviar Reporte", fg_color="#e41e3f", 
                      command=lambda: self.start_thread(self.fb_logic_report)).pack(pady=15)

    # --- LÓGICA FB: REACCIÓN ---
    def fb_logic_reaction(self):
        url = self.fb_url.get()
        cookie = self.combo_cookies.get()
        reaction = self.fb_react_combo.get()
        
        if not url: return self.finish_task("Falta URL", "ERROR")

        try:
            with sync_playwright() as p:
                browser = self.get_browser(p)
                context = browser.new_context()
                page = manejar_login(context, cookie)
                if page:
                    page.goto(url, wait_until="domcontentloaded")
                    self.human_sleep()
                    
                    # Lógica robusta de búsqueda por texto
                    regex_like = re.compile(r"^Me gusta$|^Like$", re.IGNORECASE)
                    like_btn = page.locator('div[role="button"], span[role="button"]').filter(has_text=regex_like).first
                    if not like_btn.is_visible():
                         like_btn = page.locator('[aria-label="Me gusta"], [aria-label="Like"]').first

                    if like_btn.is_visible():
                        if reaction == "Me gusta":
                            like_btn.click()
                            self.log(f"FB: Like aplicado", "SUCCESS")
                        else:
                            self.log(f"FB: Buscando reacción {reaction}...")
                            like_btn.hover(force=True)
                            self.human_sleep(2)
                            # Mapeo simple para buscar el icono en el menú
                            map_react = {"Me encanta": "Love", "Me divierte": "Haha", "Me importa": "Care"}
                            english_name = map_react.get(reaction, reaction) # Fallback al español
                            
                            btn_react = page.locator(f'[aria-label="{reaction}"], [aria-label="{english_name}"]').first
                            if btn_react.is_visible():
                                btn_react.click()
                                self.log(f"FB: Reacción {reaction} aplicada", "SUCCESS")
                            else:
                                self.log("FB: No encontré el icono en el menú flotante", "ERROR")
                    else:
                        self.log("FB: Botón Me Gusta no visible", "ERROR")
                    browser.close()
        except Exception as e:
            self.log(f"Error FB React: {e}", "ERROR")
        finally:
            self.is_running = False

    # --- LÓGICA FB: COMENTAR ---
    def fb_logic_comment(self):
        url = self.fb_url.get()
        cookie = self.combo_cookies.get()
        text = self.fb_comment_txt.get("1.0", "end").strip()
        
        if not url or not text: return self.finish_task("Falta URL o Comentario", "ERROR")

        try:
            with sync_playwright() as p:
                browser = self.get_browser(p)
                context = browser.new_context()
                page = manejar_login(context, cookie)
                if page:
                    page.goto(url)
                    self.human_sleep()
                    
                    # Buscar caja de comentarios
                    box = page.locator('div[role="textbox"][contenteditable="true"]').first
                    if not box.is_visible():
                        # Intentar clicar en "Escribe un comentario..." para activar la caja
                        page.get_by_text(re.compile("comentario|comment", re.IGNORECASE)).first.click()
                        self.human_sleep(1)
                    
                    if box.is_visible():
                        box.click()
                        page.keyboard.type(text, delay=50)
                        self.human_sleep(1)
                        page.keyboard.press("Enter")
                        self.log("FB: Comentario enviado", "SUCCESS")
                    else:
                        self.log("FB: No encontré caja de comentarios", "ERROR")
                    browser.close()
        except Exception as e:
            self.log(f"Error FB Comment: {e}", "ERROR")
        finally:
            self.is_running = False

    # --- LÓGICA FB: REPORTAR ---
    def fb_logic_report(self):
        url = self.fb_url.get()
        cookie = self.combo_cookies.get()
        motivo = self.fb_rep_combo.get()
        
        if not url: return self.finish_task("Falta URL", "ERROR")

        try:
            with sync_playwright() as p:
                browser = self.get_browser(p)
                context = browser.new_context()
                page = manejar_login(context, cookie)
                if page:
                    page.goto(url)
                    self.human_sleep(3)
                    
                    # 1. Menú 3 puntos
                    menu = page.locator('div[aria-haspopup="menu"]').first
                    if not menu.is_visible():
                         menu = page.locator('div[role="button"]').filter(has_text="acciones").first
                    
                    if menu.is_visible():
                        menu.click()
                        self.human_sleep(1)
                        # 2. Opción Reportar
                        page.locator('div[role="menuitem"]').filter(has_text=re.compile("Report|Denunciar", re.IGNORECASE)).first.click()
                        self.human_sleep(2)
                        
                        # 3. Motivo (Texto parcial)
                        page.get_by_text(re.compile(motivo, re.IGNORECASE)).first.click()
                        self.human_sleep(1)
                        
                        # 4. Enviar
                        btn_send = page.locator('div[role="button"]').filter(has_text=re.compile("Enviar|Submit|Done", re.IGNORECASE)).first
                        if btn_send.is_visible():
                            btn_send.click()
                            self.log("FB: Reporte enviado", "SUCCESS")
                        else:
                            self.log("FB: No pude finalizar el reporte", "WARN")
                    else:
                        self.log("FB: No encontré el menú (...)", "ERROR")
                    browser.close()
        except Exception as e:
            self.log(f"Error FB Report: {e}", "ERROR")
        finally:
            self.is_running = False

    # =========================================================================
    #                               INSTAGRAM
    # =========================================================================
    def setup_instagram_ui(self):
        f = self.tab_ig
        f.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(f, text="Link del Post de Instagram:", text_color="#C13584", font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=2, pady=(10, 5))
        self.ig_url = ctk.CTkEntry(f, width=500)
        self.ig_url.grid(row=1, column=0, columnspan=2, pady=(0, 20))

        # --- IG LIKE ---
        frame_ig_like = ctk.CTkFrame(f)
        frame_ig_like.grid(row=2, column=0, padx=10, sticky="nsew")
        ctk.CTkButton(frame_ig_like, text="❤ DAR LIKE", fg_color="#C13584", 
                      command=lambda: self.start_thread(self.ig_logic_like)).pack(pady=20, padx=20)

        # --- IG COMENTAR ---
        frame_ig_comm = ctk.CTkFrame(f)
        frame_ig_comm.grid(row=2, column=1, padx=10, sticky="nsew")
        self.ig_comment_txt = ctk.CTkEntry(frame_ig_comm, placeholder_text="Escribe comentario...", width=200)
        self.ig_comment_txt.pack(pady=10)
        ctk.CTkButton(frame_ig_comm, text="💬 COMENTAR", fg_color="#C13584", 
                      command=lambda: self.start_thread(self.ig_logic_comment)).pack(pady=10)

        ctk.CTkLabel(f, text="*Se usará la sesión de Facebook para intentar entrar a Instagram", font=("Arial", 10)).grid(row=3, column=0, columnspan=2, pady=10)

    def ig_login_helper(self, p, cookie):
        self.log("Iniciando motor híbrido (FB -> IG)...")
        browser = self.get_browser(p)
        context = browser.new_context()
        
        # 1. Cargamos cookies de FB
        page = manejar_login(context, cookie) 
        if not page: 
            browser.close()
            return None, None
        
        # 2. Vamos a Instagram
        self.log("Navegando a Instagram.com...")
        try:
            page.goto("https://www.instagram.com/", wait_until="domcontentloaded", timeout=60000)
            self.human_sleep(3, 5)
        except Exception as e:
            self.log(f"Alerta cargando IG: {e}", "WARN")

        # 3. LOGIN / VINCULACIÓN
        try:
            # Buscar botones de login: Ahora incluye "Log in with Facebook" (Tu imagen 1)
            btn_login_fb = page.locator('button, div[role="button"], span, a').filter(
                has_text=re.compile(r"Log in with Facebook|Iniciar sesión con Facebook|Continuar|Continue", re.IGNORECASE)
            ).first

            if btn_login_fb.is_visible(timeout=5000):
                self.log("Botón Login detectado. Clickeando...", "INFO")
                btn_login_fb.click()
                self.human_sleep(5)
            
            # --- CENTRO DE CUENTAS (ALLOW / PERMITIR) ---
            btn_allow = page.locator('div[role="button"], button').filter(
                has_text=re.compile(r"Allow and continue|Permitir y continuar|Sí, finalizar configuración", re.IGNORECASE)
            ).first
            
            if btn_allow.is_visible(timeout=8000):
                self.log("Aceptando vinculación (Allow)...", "INFO")
                btn_allow.click()
                self.human_sleep(5) 

            # --- CORRECCIÓN CRÍTICA: MANEJO DE "SOMETHING WENT WRONG" ---
            # Si Instagram nos manda a la url maldita /accounts/signup/ o sale el error
            error_indicator = page.locator('body').filter(has_text=re.compile(r"Something went wrong|Esta página no funciona", re.IGNORECASE))
            
            if "accounts/signup" in page.url or error_indicator.is_visible(timeout=3000):
                self.log("⚠️ Detectado error 'Something went wrong'. Saltando error forzando Home...", "WARN")
                try:
                    # Forzamos ir al feed principal. Generalmente la cookie YA está guardada.
                    page.goto("https://www.instagram.com/", wait_until="domcontentloaded")
                    self.human_sleep(5)
                except:
                    pass
            # -----------------------------------------------------------

            # 4. Manejo de Popups Post-Login ("Guardar info", "Notificaciones")
            try:
                btn_not_now = page.locator('button, div[role="button"]').filter(has_text=re.compile(r"Ahora no|Not now|Cancel", re.IGNORECASE)).first
                if btn_not_now.is_visible(timeout=5000):
                    btn_not_now.click()
            except: pass

        except Exception as e:
            self.log(f"Nota en proceso de login: {e}", "WARN")

        # Verificación final
        try:
            if page.locator('svg[aria-label="Inicio"], svg[aria-label="Home"]').first.is_visible(timeout=8000):
                self.log("Login en Instagram EXITOSO.", "SUCCESS")
            else:
                self.log("No veo el feed, pero intentaré continuar al video...", "WARN")
        except:
            pass

        return browser, page

    def ig_logic_like(self):
        url = self.ig_url.get()
        cookie = self.combo_cookies.get()
        if not url: return self.finish_task("Falta URL", "ERROR")

        try:
            with sync_playwright() as p:
                browser, page = self.ig_login_helper(p, cookie)
                if page:
                    try:
                        self.log(f"Yendo al post: {url}")
                        page.goto(url, wait_until="domcontentloaded")
                        self.human_sleep(3, 5)

                        # --- NUEVO: MANEJO DEL POPUP EN EL VIDEO (Tu captura) ---
                        # Buscamos el botón "Continue with Facebook" dentro del video
                        btn_continue_modal = page.locator('span, button').filter(
                            has_text=re.compile(r"Continue with Facebook|Continuar con Facebook", re.IGNORECASE)
                        ).first
                        
                        if btn_continue_modal.is_visible():
                            self.log("Detectado Popup 'Continue with Facebook' en el video. Clickeando...", "WARN")
                            btn_continue_modal.click()
                            self.human_sleep(5, 7) # Esperar a que recargue la página
                            
                            # A veces, después de este click, pide el "Allow/Permitir" otra vez
                            btn_allow = page.locator('div[role="button"], button').filter(
                                has_text=re.compile(r"Allow and continue|Permitir y continuar", re.IGNORECASE)
                            ).first
                            if btn_allow.is_visible():
                                btn_allow.click()
                                self.human_sleep(3)
                        # -------------------------------------------------------
                        
                        # Búsqueda del corazón (SVG)
                        heart = page.locator('svg[aria-label="Me gusta"], svg[aria-label="Like"]').first
                        unlike = page.locator('svg[aria-label="Ya no me gusta"], svg[aria-label="Unlike"]').first
                        
                        if unlike.is_visible():
                            self.log("IG: Ya tenías like en este post.", "WARN")
                        elif heart.is_visible():
                            heart.click()
                            self.log("IG: ❤ Like aplicado correctamente.", "SUCCESS")
                        else:
                            self.log("IG: No encontré el botón de corazón (¿Bloqueo o error de carga?).", "ERROR")
                            
                    except Exception as e:
                        self.log(f"Error durante la acción en IG: {e}", "ERROR")
                    
                    self.human_sleep(1)
                    browser.close()
                else:
                    self.log("No se pudo iniciar sesión en IG.", "ERROR")
        except Exception as e:
            self.log(f"Error Critico IG: {e}", "ERROR")
        finally:
            self.is_running = False

    def ig_logic_comment(self):
        url = self.ig_url.get()
        text = self.ig_comment_txt.get()
        cookie = self.combo_cookies.get()
        if not url or not text: return self.finish_task("Falta URL o Texto", "ERROR")

        try:
            with sync_playwright() as p:
                browser, page = self.ig_login_helper(p, cookie)
                if page:
                    try:
                        page.goto(url, wait_until="domcontentloaded")
                        self.human_sleep()
                        
                        # Instagram suele usar un textarea que crece
                        box = page.locator('textarea[aria-label*="comentario"], textarea[aria-label*="comment"]').first
                        
                        if not box.is_visible():
                             # A veces hay que dar clic en el botón de globo de texto para que salga la caja en móviles/algunas vistas
                             page.locator('svg[aria-label="Comentar"], svg[aria-label="Comment"]').first.click()
                             self.human_sleep(1)

                        if box.is_visible():
                            box.click()
                            self.human_sleep(0.5)
                            page.keyboard.type(text, delay=50)
                            self.human_sleep(0.5)
                            page.keyboard.press("Enter")
                            self.log("IG: Comentario enviado.", "SUCCESS")
                        else:
                            self.log("IG: No pude encontrar la caja de comentarios.", "ERROR")
                    
                    except Exception as e:
                         self.log(f"Error comentando en IG: {e}", "ERROR")
                    
                    browser.close()
                else:
                    self.log("No se pudo iniciar sesión en IG.", "ERROR")
        except Exception as e:
            self.log(f"Error Critico IG Comment: {e}", "ERROR")
        finally:
            self.is_running = False    
    # =========================================================================
    #                               X (TWITTER)
    # =========================================================================
    def setup_x_ui(self):
        f = self.tab_x
        f.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(f, text="Link del Tweet:", text_color="#1DA1F2", font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=2, pady=(10, 5))
        self.x_url = ctk.CTkEntry(f, width=500)
        self.x_url.grid(row=1, column=0, columnspan=2, pady=(0, 20))

        # --- X LIKE ---
        frame_x_like = ctk.CTkFrame(f)
        frame_x_like.grid(row=2, column=0, padx=10, sticky="nsew")
        ctk.CTkButton(frame_x_like, text="❤ LIKE", fg_color="#1DA1F2", 
                      command=lambda: self.start_thread(self.x_logic_like)).pack(pady=20, padx=20)

        # --- X REPLY ---
        frame_x_reply = ctk.CTkFrame(f)
        frame_x_reply.grid(row=2, column=1, padx=10, sticky="nsew")
        self.x_reply_txt = ctk.CTkEntry(frame_x_reply, placeholder_text="Respuesta...", width=200)
        self.x_reply_txt.pack(pady=10)
        ctk.CTkButton(frame_x_reply, text="↩ RESPONDER", fg_color="#1DA1F2", 
                      command=lambda: self.start_thread(self.x_logic_reply)).pack(pady=10)

    def x_logic_like(self):
        url = self.x_url.get()
        cookie = self.combo_cookies.get()
        if not url: return self.finish_task("Falta URL", "ERROR")

        try:
            with sync_playwright() as p:
                browser = self.get_browser(p)
                context = browser.new_context()
                manejar_login(context, cookie) # Intento de cargar cookies
                page = context.new_page()
                page.goto(url)
                self.human_sleep()

                like_btn = page.locator('[data-testid="like"]').first
                if like_btn.is_visible():
                    like_btn.click()
                    self.log("X: Like aplicado", "SUCCESS")
                elif page.locator('[data-testid="unlike"]').is_visible():
                    self.log("X: Ya tenías like", "WARN")
                else:
                    self.log("X: No encontré botón like (¿Login?)", "ERROR")
                browser.close()
        except Exception as e:
            self.log(f"Error X Like: {e}", "ERROR")
        finally:
            self.is_running = False

    def x_logic_reply(self):
        url = self.x_url.get()
        text = self.x_reply_txt.get()
        cookie = self.combo_cookies.get()
        if not url or not text: return self.finish_task("Falta URL o Texto", "ERROR")

        try:
            with sync_playwright() as p:
                browser = self.get_browser(p)
                context = browser.new_context()
                manejar_login(context, cookie)
                page = context.new_page()
                page.goto(url)
                self.human_sleep()

                # Abrir caja reply
                page.locator('[data-testid="reply"]').first.click()
                self.human_sleep(1)
                
                editor = page.locator('[data-testid="tweetTextarea_0"]').first
                if editor.is_visible():
                    editor.click()
                    page.keyboard.type(text, delay=50)
                    self.human_sleep(1)
                    page.locator('[data-testid="tweetButton"]').first.click()
                    self.log("X: Reply enviado", "SUCCESS")
                else:
                    self.log("X: No pude abrir editor respuesta", "ERROR")
                browser.close()
        except Exception as e:
            self.log(f"Error X Reply: {e}", "ERROR")
        finally:
            self.is_running = False

    def finish_task(self, msg, type):
        self.log(msg, type)
        self.is_running = False

if __name__ == "__main__":
    app = SocialBotApp()
    app.mainloop()
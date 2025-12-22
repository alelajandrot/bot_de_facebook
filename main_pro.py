import customtkinter as ctk
import threading
import time
import random
import os
import re
from tkinter import messagebox
from PIL import Image
from playwright.sync_api import sync_playwright
from concurrent.futures import ThreadPoolExecutor
from fake_useragent import UserAgent

# Importamos las funciones del login_manager
try:
    from login_manager import (
    manejar_login,
    obtener_datos_cuenta,
    login_manual_asistido,
    obtener_lista_alias,
    guardar_nueva_cuenta,
    verificar_si_logueado,
    guardar_cookies_db
)
except ImportError as e:
    messagebox.showerror("Error Crítico", f"Error importando login_manager: {e}\nAsegurate de haber actualizado ese archivo primero.")
    exit()

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# CONFIGURACIÓN
MAX_WORKERS = 3

class SocialBotApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.is_running = False 
        self.title("Social Bot Farm - PRO vFinal (FB + IG + X + YT + TikTok)")
        self.geometry("1300x900")
        
        # Grid Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # =========================================================================
        #                             SIDEBAR (PANEL DE CONTROL)
        # =========================================================================
        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        # Título
        ctk.CTkLabel(self.sidebar, text="🤖 FARM CONTROL", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, padx=20, pady=20)
        
        # --- SELECCIÓN DE CUENTA ---
        ctk.CTkLabel(self.sidebar, text="Cuenta Individual:").grid(row=1, column=0, sticky="w", padx=20)
        self.combo_cuentas = ctk.CTkComboBox(self.sidebar, values=self.get_account_list())
        self.combo_cuentas.grid(row=2, column=0, padx=20, pady=(0, 10))

        # --- OPCIONES ---
        self.var_headless = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(self.sidebar, text="Modo Oculto (Headless)", variable=self.var_headless).grid(row=3, column=0, padx=20, pady=10, sticky="w")
        
        self.var_batch = ctk.BooleanVar(value=False)
        self.chk_batch = ctk.CTkCheckBox(self.sidebar, text="🔥 MODO MASIVO", variable=self.var_batch, fg_color="#e63946")
        self.chk_batch.grid(row=4, column=0, padx=20, pady=10, sticky="w")

        # --- SLIDER DE HILOS ---
        self.lbl_workers = ctk.CTkLabel(self.sidebar, text="Navegadores Simultáneos: 1", font=("Arial", 11))
        self.lbl_workers.grid(row=5, column=0, padx=20, pady=(5, 0), sticky="w")
        
        self.slider_workers = ctk.CTkSlider(self.sidebar, from_=1, to=5, number_of_steps=4, command=self.update_worker_label)
        self.slider_workers.grid(row=6, column=0, padx=20, pady=(0, 20), sticky="ew")
        self.slider_workers.set(1)

        # --- BOTONES DE GESTIÓN ---
        ctk.CTkButton(self.sidebar, text="🔄 Recargar DB", command=self.refresh_ui_list, border_width=1, fg_color="transparent").grid(row=7, column=0, padx=20, pady=5)

        ctk.CTkButton(self.sidebar, text="🔑 Generar Cookie (Manual)", 
                      command=lambda: self.start_thread(self.run_manual_login_wizard),
                      fg_color="#D35400", hover_color="#E67E22").grid(row=8, column=0, padx=20, pady=5)

        # --- VISTA PREVIA ---
        ctk.CTkLabel(self.sidebar, text="📸 Última Actividad:").grid(row=9, column=0, padx=20, pady=(20, 5))
        self.lbl_screenshot = ctk.CTkLabel(self.sidebar, text="[Sin imagen]", width=200, height=120, fg_color="#2b2b2b")
        self.lbl_screenshot.grid(row=10, column=0, padx=20, pady=5)

        # =========================================================================
        #                        TABS PRINCIPALES (MODIFICADO)
        # =========================================================================
        self.tabs = ctk.CTkTabview(self)
        self.tabs.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")

        self.tab_fb = self.tabs.add("Facebook")
        self.tab_warmup = self.tabs.add("🔥 Calentamiento")
        self.tab_ig = self.tabs.add("Instagram")
        self.tab_x = self.tabs.add("X (Twitter)")
        
        # --- NUEVOS TABS ---
        self.tab_yt = self.tabs.add("YouTube")
        self.tab_tt = self.tabs.add("TikTok")
        # -------------------
        
        self.tab_accounts = self.tabs.add("⚙ Gestor Cuentas")

        # Inicializar interfaces
        self.setup_facebook_ui()
        self.setup_warmup_ui()
        self.setup_instagram_ui()
        self.setup_x_ui()
        
        # --- INICIALIZAR NUEVAS UI ---
        self.setup_youtube_ui()
        self.setup_tiktok_ui()
        # -----------------------------
        
        self.setup_accounts_ui()

        # --- CONSOLA ---
        self.log_frame = ctk.CTkFrame(self, height=150)
        self.log_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        self.console = ctk.CTkTextbox(self.log_frame, height=120, font=("Consolas", 11))
        self.console.pack(fill="both", padx=10, pady=5)
        self.console.configure(state="disabled")

    # =========================================================================
    #                    LÓGICA GENERAL Y UTILIDADES
    # =========================================================================

    def log(self, msg, type="INFO"):
        ts = time.strftime("%H:%M:%S")
        icons = {"INFO": "ℹ️", "SUCCESS": "✅", "ERROR": "❌", "WARN": "⚠️", "BATCH": "🔥", "WARMUP": "🏋️"}
        text = f"[{ts}] {icons.get(type, '')} {msg}\n"
        
        def _update():
            self.console.configure(state="normal")
            self.console.insert("end", text)
            self.console.see("end")
            self.console.configure(state="disabled")
        self.after(0, _update)
        print(text.strip())

    def update_screenshot_preview(self, path):
        def _update():
            try:
                if os.path.exists(path):
                    img = Image.open(path)
                    img.thumbnail((200, 150))
                    photo = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
                    self.lbl_screenshot.configure(image=photo, text="")
                else:
                    self.lbl_screenshot.configure(text="Error Img")
            except Exception as e:
                print(f"Error mostrando screenshot: {e}")
        self.after(0, _update)

    def get_account_list(self):
        cuentas = obtener_lista_alias()
        return cuentas if cuentas else ["Sin cuentas"]

    def refresh_ui_list(self):
        new_values = self.get_account_list()
        self.combo_cuentas.configure(values=new_values)
        if new_values[0] != "Sin cuentas":
            self.combo_cuentas.set(new_values[0])

    def human_sleep(self, a=2, b=4):
        time.sleep(random.uniform(a, b))

    def update_worker_label(self, value):
        self.lbl_workers.configure(text=f"Navegadores Simultáneos: {int(value)}")

    def simulate_human_behavior(self, page):
        try:
            for _ in range(random.randint(1, 3)):
                page.mouse.wheel(0, random.randint(200, 500))
                time.sleep(random.uniform(0.5, 1.0))
            w, h = page.viewport_size['width'], page.viewport_size['height']
            page.mouse.move(random.randint(10, w-10), random.randint(10, h-10), steps=10)
        except: pass

    # =========================================================================
    #              NAVEGADOR ANTI-DETECT
    # =========================================================================
    # =========================================================================
    #              NAVEGADOR ANTI-DETECT (MEJORADO - STEALTH)
    # =========================================================================
    # =========================================================================
    #         NAVEGADOR CON MEMORIA (PERFILES PERSISTENTES) - SOLUCIÓN DEFINITIVA
    # =========================================================================
    # =========================================================================
    #         NAVEGADOR "MODO FANTASMA" (SIN BANDERAS DE BOT)
    # =========================================================================
    def get_browser_context(self, p, alias):
        """
        Lanza el navegador ocultando TODAS las alertas de automatización.
        Usa un User Agent fijo para evitar bloqueos en Instagram y Facebook.
        """
        headless = self.var_headless.get()
        
        # 1. Crear carpeta de perfil persistente
        if not os.path.exists("profiles"):
            os.makedirs("profiles")
        user_data_path = os.path.join(os.getcwd(), "profiles", alias)

        # 2. Argumentos de Evasión (Stealth)
        args = [
            '--disable-blink-features=AutomationControlled', # Oculta la bandera de bot
            '--start-maximized',
            '--no-sandbox',
            '--disable-infobars',
            '--disable-dev-shm-usage',
            '--disable-extensions',
            '--disable-popup-blocking',
            '--window-position=0,0'
        ]

        # 3. User Agent Fijo (Crucial para que IG no dé Timeout)
        ua_real = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"

        creds = obtener_datos_cuenta(alias)
        proxy_config = {"server": creds["proxy"]} if creds.get("proxy") else None

        self.log(f"🕵️ Abriendo Chrome Real (Modo Fantasma) para: {alias}", "INFO")

        # 4. LANZAMIENTO AVANZADO (Sin duplicados de argumentos)
        try:
            context = p.chromium.launch_persistent_context(
                user_data_dir=user_data_path,
                headless=headless,
                args=args,
                ignore_default_args=["--enable-automation"], 
                channel="chrome", # Usa Google Chrome instalado
                user_agent=ua_real, # <--- Se define una sola vez para evitar SyntaxError
                viewport=None,
                locale="es-CO",
                geolocation={"latitude": 4.7110, "longitude": -74.0721},
                permissions=["geolocation"],
                proxy=proxy_config,
                slow_mo=30
            )
        except Exception as e:
            self.log("⚠️ No encontré Google Chrome, usando Chromium interno...", "WARN")
            context = p.chromium.launch_persistent_context(
                user_data_dir=user_data_path,
                headless=headless,
                args=args,
                ignore_default_args=["--enable-automation"], 
                user_agent=ua_real, # <--- Se define una sola vez aquí también
                viewport=None,
                proxy=proxy_config
            )

        # 5. Parche final de Javascript (Evasión extra)
        init_script = """
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        """
        context.add_init_script(init_script)

        return context, context


    # =========================================================================
    #                  THREADING & BATCHING
    # =========================================================================
    def start_thread(self, target_func):
        if self.is_running:
            self.log("Sistema ocupado. Espera...", "WARN")
            return
        
        if self.var_batch.get():
            self.log(f"🚀 INICIANDO MODO MASIVO", "BATCH")
            threading.Thread(target=lambda: self.run_batch_task(target_func)).start()
        else:
            self.is_running = True
            threading.Thread(target=lambda: self.run_single_task(target_func)).start()

    def run_single_task(self, logic_func):
        alias = self.combo_cuentas.get()
        if alias == "Sin cuentas": 
            self.is_running = False
            return
        try:
            logic_func(alias=alias)
        except Exception as e:
            self.log(f"Error tarea individual: {e}", "ERROR")
        finally:
            self.is_running = False

    def run_batch_task(self, logic_func):
        self.is_running = True
        accounts_list = self.get_account_list()
        
        if accounts_list == ["Sin cuentas"]:
            self.log("No hay cuentas para batch", "ERROR")
            self.is_running = False
            return

        current_workers = int(self.slider_workers.get())
        self.log(f"🚀 Procesando con {current_workers} hilos", "BATCH")

        with ThreadPoolExecutor(max_workers=current_workers) as executor:
            futures = []
            for alias in accounts_list:
                self.log(f"Encolando tarea: {alias}", "BATCH")
                futures.append(executor.submit(self.wrapper_batch_logic, logic_func, alias))
            
            for future in futures:
                try: future.result()
                except Exception as e: self.log(f"Error en un hilo: {e}", "ERROR")
        
        self.log("🔥 Lote Masivo Finalizado", "SUCCESS")
        self.is_running = False

    def wrapper_batch_logic(self, logic_func, alias):
        try:
            time.sleep(random.uniform(2, 10))
            logic_func(alias=alias)
        except Exception as e:
            self.log(f"Fallo en cuenta {alias}: {e}", "ERROR")

    # Busca esta función en main_pro.py y modifícala así:
    def run_manual_login_wizard(self, alias=None):
        if not alias:
            alias = self.combo_cuentas.get()

        data = obtener_datos_cuenta(alias)
        platform = data.get("platform")

        if not platform:
            messagebox.showerror(
                "Error",
                f"La cuenta {alias} no tiene plataforma definida"
            )
            return

        try:
            with sync_playwright() as p:
                browser, context = self.get_browser_context(p, alias)

                ok = login_manual_asistido(context, alias, data)

                if ok:
                    self.log(
                        f"✅ Cookies guardadas correctamente para {alias} ({platform})",
                        "SUCCESS"
                    )
                else:
                    self.log(
                        f"⚠️ No se guardaron cookies para {alias} ({platform})",
                        "WARN"
                    )

                context.close()

        except Exception as e:
            self.log(f"❌ Error en login manual: {e}", "ERROR")




    # =========================================================================
    #                       CALENTAMIENTO UI & LOGIC
    # =========================================================================
    def setup_warmup_ui(self):
        f = self.tab_warmup
        ctk.CTkLabel(f, text="🏋️ RUTINA DE CALENTAMIENTO", font=("Arial", 16, "bold")).pack(pady=10)
        self.slider_warmup = ctk.CTkSlider(f, from_=1, to=10, number_of_steps=9)
        self.slider_warmup.pack(pady=20)
        self.slider_warmup.set(3)
        ctk.CTkLabel(f, text="Duración por cuenta (minutos)").pack()
        ctk.CTkButton(f, text="▶ INICIAR", fg_color="#27ae60", height=50, 
                      command=lambda: self.start_thread(self.logic_warmup)).pack(pady=30)

    def logic_warmup(self, alias=None):
        minutes = self.slider_warmup.get()
        self.log(f"Iniciando Warmup ({minutes} min) para {alias}", "WARMUP")
        try:
            with sync_playwright() as p:
                browser, context = self.get_browser_context(p, alias)
                page = manejar_login(context, alias, self.var_headless.get())
                if page:
                    start_time = time.time()
                    end_time = start_time + (minutes * 60)
                    while time.time() < end_time:
                        page.mouse.wheel(0, random.randint(300, 1000))
                        time.sleep(random.uniform(2, 8))
                    self.log(f"Warmup finalizado: {alias}", "SUCCESS")
                    browser.close()
                else: self.log(f"Falló login Warmup: {alias}", "ERROR")
        except Exception as e: self.log(f"Error Warmup {alias}: {e}", "ERROR")

    # =========================================================================
    #                             FACEBOOK
    # =========================================================================
    def setup_facebook_ui(self):
        f = self.tab_fb
        f.grid_columnconfigure((0, 1, 2), weight=1)
        ctk.CTkLabel(f, text="Link del Post de Facebook:", font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=3, pady=(10, 5))
        self.fb_url = ctk.CTkEntry(f, width=500, placeholder_text="https://www.facebook.com/...")
        self.fb_url.grid(row=1, column=0, columnspan=3, pady=(0, 20))

        frame_react = ctk.CTkFrame(f)
        frame_react.grid(row=2, column=0, padx=10, sticky="nsew")
        self.fb_react_combo = ctk.CTkComboBox(frame_react, values=["Me gusta", "Me encanta", "Me divierte"])
        self.fb_react_combo.pack(pady=5)
        ctk.CTkButton(frame_react, text="Reaccionar", fg_color="#f7b928", text_color="black", 
                      command=lambda: self.start_thread(self.fb_logic_reaction)).pack(pady=10)

        frame_comm = ctk.CTkFrame(f)
        frame_comm.grid(row=2, column=1, padx=10, sticky="nsew")
        self.fb_comment_txt = ctk.CTkTextbox(frame_comm, height=60)
        self.fb_comment_txt.pack(pady=5, padx=5)
        ctk.CTkButton(frame_comm, text="Comentar", fg_color="#1877F2", 
                      command=lambda: self.start_thread(self.fb_logic_comment)).pack(pady=10)

        frame_rep = ctk.CTkFrame(f)
        frame_rep.grid(row=2, column=2, padx=10, sticky="nsew")
        self.fb_rep_combo = ctk.CTkComboBox(frame_rep, values=["Spam", "Violencia", "Acoso"])
        self.fb_rep_combo.pack(pady=5)
        ctk.CTkButton(frame_rep, text="Reportar", fg_color="#e41e3f", 
                      command=lambda: self.start_thread(self.fb_logic_report)).pack(pady=10)

    def fb_logic_reaction(self, alias=None):
        url = self.fb_url.get()
        reaction = self.fb_react_combo.get()
        if not url: return
        try:
            with sync_playwright() as p:
                browser, context = self.get_browser_context(p, alias)
                page = manejar_login(context, alias, self.var_headless.get())
                if page:
                    page.goto(url)
                    self.simulate_human_behavior(page)
                    
                    like_btn = page.locator('div[role="button"], span[role="button"]').filter(has_text=re.compile(r"^Me gusta$|^Like$", re.IGNORECASE)).first
                    if not like_btn.is_visible(): like_btn = page.locator('[aria-label="Me gusta"], [aria-label="Like"]').first
                    
                    if like_btn.is_visible():
                        if reaction == "Me gusta":
                            like_btn.click()
                        else:
                            like_btn.hover(force=True)
                            self.human_sleep(1, 2)
                            map_react = {"Me encanta": "Love", "Me divierte": "Haha"}
                            eng = map_react.get(reaction, reaction)
                            page.locator(f'[aria-label="{reaction}"], [aria-label="{eng}"]').first.click()
                        
                        self.log(f"FB: {reaction} aplicado ({alias})", "SUCCESS")
                        shot = f"logs/fb_{alias}_{int(time.time())}.png"
                        page.screenshot(path=shot)
                        self.update_screenshot_preview(shot)
                    else: self.log("FB: Botón no visible", "ERROR")
                    browser.close()
        except Exception as e: self.log(f"Error FB React: {e}", "ERROR")

    def fb_logic_comment(self, alias=None):
        url = self.fb_url.get()
        text = self.fb_comment_txt.get("1.0", "end").strip()
        if not url or not text: return
        try:
            with sync_playwright() as p:
                browser, context = self.get_browser_context(p, alias)
                page = manejar_login(context, alias, self.var_headless.get())
                if page:
                    page.goto(url)
                    self.simulate_human_behavior(page)
                    
                    # 1. Intentar encontrar la caja de texto directamente
                    # Usamos un selector más robusto para la caja de comentarios de FB
                    box = page.locator('div[role="textbox"][aria-label*="Escribe un comentario"], div[role="textbox"][contenteditable="true"]').first
                    
                    # 2. Si no es visible, intentar forzar la aparición de la caja
                    if not box.is_visible():
                        # Buscamos el botón "Comentar" (el que tiene el icono junto a Like)
                        btn_abrir = page.locator('div[role="button"]').filter(has_text=re.compile(r"Comentar|Comment", re.IGNORECASE)).first
                        if btn_abrir.is_visible():
                            btn_abrir.click(force=True) # force=True evita el error de "intercepts pointer events"
                            self.human_sleep(1, 2)

                    # 3. Escribir el comentario
                    if box.is_visible():
                        box.click(force=True)
                        page.keyboard.type(text, delay=random.randint(50, 100))
                        page.wait_for_timeout(500)
                        page.keyboard.press("Enter")
                        
                        self.log(f"FB: Comentario enviado ({alias})", "SUCCESS")
                        shot = f"logs/fb_comm_{alias}_{int(time.time())}.png"
                        page.screenshot(path=shot)
                    else:
                        self.log("FB: No se encontró la caja para comentar", "ERROR")
                    
                    browser.close()
        except Exception as e: 
            self.log(f"Error FB Comment: {e}", "ERROR")


    def fb_logic_report(self, alias=None):
        # Lógica simplificada
        pass

    # =========================================================================
    #                             INSTAGRAM
    # =========================================================================
    def setup_instagram_ui(self):
        f = self.tab_ig
        f.grid_columnconfigure((0, 1), weight=1)
        ctk.CTkLabel(f, text="Link Instagram:", text_color="#C13584").grid(row=0, column=0, columnspan=2)
        self.ig_url = ctk.CTkEntry(f, width=500)
        self.ig_url.grid(row=1, column=0, columnspan=2, pady=(0, 20))
        
        ctk.CTkButton(f, text="❤ DAR LIKE", fg_color="#C13584", command=lambda: self.start_thread(self.ig_logic_like)).grid(row=2, column=0, padx=10)
        
        self.ig_comment_txt = ctk.CTkEntry(f, placeholder_text="Comentario...")
        self.ig_comment_txt.grid(row=2, column=1, padx=10)
        ctk.CTkButton(f, text="💬 COMENTAR", fg_color="#C13584", command=lambda: self.start_thread(self.ig_logic_comment)).grid(row=3, column=1, pady=10)

    def ig_login_helper(self, context, alias):
            page = manejar_login(context, alias, self.var_headless.get())
            if not page:
                return None

            page.set_default_timeout(40000)
            
            try:
                self.log(f"IG: Accediendo a Instagram para {alias}...", "INFO")
                # Cambiado a domcontentloaded para mayor velocidad y evitar bloqueos
                page.goto("https://www.instagram.com/", wait_until="domcontentloaded", timeout=90000)
                page.wait_for_timeout(3000)

                if verificar_si_logueado(page, "instagram"):
                    self.log(f"IG: Sesión activa detectada para {alias}", "SUCCESS")
                    return page

                # Intento de login si la cookie falló
                page.goto("https://www.instagram.com/accounts/login/", wait_until="domcontentloaded")
                
                data = obtener_datos_cuenta(alias)
                user = data.get("username")
                pwd = data.get("password")

                if user and pwd and user != "Pendiente":
                    page.fill('input[name="username"]', user)
                    page.fill('input[name="password"]', pwd)
                    page.click('button[type="submit"]')
                    page.wait_for_timeout(7000)

                    if verificar_si_logueado(page, "instagram"):
                        guardar_cookies_db(alias, context.cookies(), strict=True, platform_hint="instagram")
                        return page

                return page
            except Exception as e:
                self.log(f"Error en acceso IG: {e}", "ERROR")
                return page



    def ig_logic_like(self, alias=None):
        url = self.ig_url.get()
        if not url: return

        try:
            with sync_playwright() as p:
                browser, context = self.get_browser_context(p, alias)
                page = self.ig_login_helper(context, alias)

                if not page:
                    context.close()
                    return

                self.log(f"IG: Abriendo post en {alias}...", "INFO")
                page.goto(url, wait_until="domcontentloaded")
                # Tiempo para que el JavaScript cargue los iconos
                page.wait_for_timeout(6000)

                # --- LÓGICA BASADA EN TU INSPECTOR DE ELEMENTOS ---
                self.log("IG: Localizando botón de Like...", "INFO")
                
                # Buscamos el SVG que tiene el título "Me gusta" o el aria-label
                # Y luego subimos al DIV que tiene role="button"
                heart_icon = page.locator('svg[aria-label="Me gusta"], svg:has(title:text("Me gusta"))').first
                
                if heart_icon.is_visible():
                    # Subimos en la jerarquía hasta encontrar el DIV clickable que viste en naranja
                    button_to_click = heart_icon.locator('xpath=./ancestor::div[@role="button"]').first
                    
                    if button_to_click.is_visible():
                        button_to_click.click(force=True)
                        self.log(f"IG: ❤️ Like aplicado en el contenedor DIV ({alias})", "SUCCESS")
                    else:
                        # Respaldo: Clic directo al corazón si el ancestro falla
                        heart_icon.click(force=True)
                        self.log(f"IG: Like aplicado directamente al SVG ({alias})", "SUCCESS")
                else:
                    # MÉTODO ALTERNATIVO: Doble clic en la imagen (comportamiento de App)
                    self.log("IG: Botón no detectado, intentando doble clic en imagen...", "WARN")
                    # El div contenedor de la imagen según tus capturas
                    page.mouse.dblclick(500, 400) 
                    page.wait_for_timeout(1000)
                    page.keyboard.press("l")

                # Verificación final de estado
                page.wait_for_timeout(2000)
                if page.locator('svg[aria-label="Ya no me gusta"]').is_visible(timeout=2000):
                    self.log(f"IG: Confirmado: Corazón ahora es rojo ({alias})", "SUCCESS")

                shot = f"logs/ig_like_{alias}_{int(time.time())}.png"
                page.screenshot(path=shot)
                self.update_screenshot_preview(shot)
                browser.close()

        except Exception as e:
            self.log(f"Error crítico en IG Like: {e}", "ERROR")



    def ig_logic_comment(self, alias=None):
        url = self.ig_url.get()
        text = self.ig_comment_txt.get()
        if not url or not text: return
        try:
            with sync_playwright() as p:
                browser, context = self.get_browser_context(p, alias)
                page = self.ig_login_helper(context, alias)
                if page:
                    page.goto(url)
                    time.sleep(3)
                    box = page.locator('textarea[aria-label*="comentario"]').first
                    if box.is_visible():
                        box.click(force=True) # <--- Agrega force=True aquí
                        page.keyboard.type(text)
                        page.keyboard.press("Enter")
                        self.log(f"IG: Comentario enviado ({alias})", "SUCCESS")
                    browser.close()
        except Exception as e: self.log(f"Error IG Comment: {e}", "ERROR")

    # =========================================================================
    #                             X (TWITTER)
    # =========================================================================
    def setup_x_ui(self):
        f = self.tab_x
        f.grid_columnconfigure((0, 1), weight=1)
        ctk.CTkLabel(f, text="Link Tweet:", text_color="#1DA1F2").grid(row=0, column=0, columnspan=2)
        self.x_url = ctk.CTkEntry(f, width=500)
        self.x_url.grid(row=1, column=0, columnspan=2, pady=(0, 20))
        
        ctk.CTkButton(f, text="❤ LIKE", fg_color="#1DA1F2", command=lambda: self.start_thread(self.x_logic_like)).grid(row=2, column=0)
        
        self.x_reply_txt = ctk.CTkEntry(f, placeholder_text="Respuesta...")
        self.x_reply_txt.grid(row=2, column=1)
        ctk.CTkButton(f, text="RESPONDER", fg_color="#1DA1F2", command=lambda: self.start_thread(self.x_logic_reply)).grid(row=3, column=1)

    def x_logic_like(self, alias=None):
        url = self.x_url.get()
        if not url: return
        try:
            with sync_playwright() as p:
                browser, context = self.get_browser_context(p, alias)
                page = manejar_login(context, alias, self.var_headless.get())
                if page:
                    page.goto(url)
                    page.locator('[data-testid="like"]').first.click()
                    self.log(f"X: Like enviado ({alias})", "SUCCESS")
                    browser.close()
        except Exception as e: self.log(f"Error X Like: {e}", "ERROR")

    def x_logic_reply(self, alias=None):
        url = self.x_url.get()
        text = self.x_reply_txt.get()
        if not url or not text: return
        try:
            with sync_playwright() as p:
                browser, context = self.get_browser_context(p, alias)
                page = manejar_login(context, alias, self.var_headless.get())
                if page:
                    page.goto(url)
                    page.locator('[data-testid="reply"]').first.click()
                    time.sleep(1)
                    page.locator('[data-testid="tweetTextarea_0"]').first.type(text)
                    page.locator('[data-testid="tweetButton"]').first.click()
                    self.log(f"X: Reply enviado ({alias})", "SUCCESS")
                    browser.close()
        except Exception as e: self.log(f"Error X Reply: {e}", "ERROR")

    # =========================================================================
    #                             YOUTUBE UI & LOGIC
    # =========================================================================
    def setup_youtube_ui(self):
        f = self.tab_yt
        f.grid_columnconfigure((0, 1), weight=1)
        ctk.CTkLabel(f, text="Link del Video de YouTube:", text_color="#FF0000", font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=2, pady=(10, 5))
        self.yt_url = ctk.CTkEntry(f, width=500, placeholder_text="https://www.youtube.com/watch?v=...")
        self.yt_url.grid(row=1, column=0, columnspan=2, pady=(0, 20))
        
        frame_yt_like = ctk.CTkFrame(f)
        frame_yt_like.grid(row=2, column=0, padx=10, sticky="nsew")
        ctk.CTkButton(frame_yt_like, text="👍 DAR LIKE", fg_color="#FF0000", command=lambda: self.start_thread(self.yt_logic_like)).pack(pady=20, padx=20)
        
        frame_yt_comm = ctk.CTkFrame(f)
        frame_yt_comm.grid(row=2, column=1, padx=10, sticky="nsew")
        self.yt_comment_txt = ctk.CTkEntry(frame_yt_comm, placeholder_text="Comentario...", width=200)
        self.yt_comment_txt.pack(pady=10)
        ctk.CTkButton(frame_yt_comm, text="💬 COMENTAR", fg_color="#FF0000", command=lambda: self.start_thread(self.yt_logic_comment)).pack(pady=10)

    def yt_logic_like(self, alias=None):
        url = self.yt_url.get()
        if not url: return
        try:
            with sync_playwright() as p:
                browser, context = self.get_browser_context(p, alias)
                page = manejar_login(context, alias, self.var_headless.get())
                if page:
                    page.goto(url)
                    self.simulate_human_behavior(page)
                    like_btn = page.locator('button[aria-label^="Me gusta este video"], button[aria-label^="Like this video"]').first
                    if not like_btn.is_visible():
                        like_btn = page.locator('ytd-toggle-button-renderer#segmented-like-button button').first

                    if like_btn.is_visible():
                        if like_btn.get_attribute("aria-pressed") == "true":
                             self.log(f"YT: Ya tenías like ({alias})", "WARN")
                        else:
                            like_btn.click()
                            self.log(f"YT: 👍 Like aplicado ({alias})", "SUCCESS")
                            shot = f"logs/yt_like_{alias}_{int(time.time())}.png"
                            page.screenshot(path=shot)
                            self.update_screenshot_preview(shot)
                    else: self.log("YT: No encontré botón Like", "ERROR")
                    browser.close()
        except Exception as e: self.log(f"Error YT Like: {e}", "ERROR")

    def yt_logic_comment(self, alias=None):
        url = self.yt_url.get()
        text = self.yt_comment_txt.get()
        if not url or not text: return
        try:
            with sync_playwright() as p:
                browser, context = self.get_browser_context(p, alias)
                page = manejar_login(context, alias, self.var_headless.get())
                if page:
                    page.goto(url)
                    page.wait_for_timeout(7000)
                    page.mouse.wheel(0, 600)
                    page.wait_for_timeout(2000)
                    placeholder = page.locator('#placeholder-area').first
                    if placeholder.is_visible():
                        placeholder.click()
                        page.wait_for_timeout(1000)
                        input_box = page.locator('#contenteditable-root').first
                        if input_box.is_visible():
                            input_box.fill(text)
                            page.wait_for_timeout(1000)
                            btn_submit = page.locator('#submit-button button[aria-label*="Comentar"], #submit-button button[aria-label*="Comment"]').first
                            if btn_submit.is_visible():
                                btn_submit.click()
                                self.log(f"YT: Comentario enviado ({alias})", "SUCCESS")
                            else: self.log("YT: Botón enviar no visible", "ERROR")
                        else: self.log("YT: Caja no activa", "ERROR")
                    else: self.log("YT: Comentarios no cargaron", "ERROR")
                    browser.close()
        except Exception as e: self.log(f"Error YT Comment: {e}", "ERROR")

    # =========================================================================
    #                             TIKTOK UI & LOGIC
    # =========================================================================
    def setup_tiktok_ui(self):
        f = self.tab_tt
        f.grid_columnconfigure((0, 1), weight=1)
        ctk.CTkLabel(f, text="Link del Video de TikTok:", text_color="#00f2ea", font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=2, pady=(10, 5))
        self.tt_url = ctk.CTkEntry(f, width=500, placeholder_text="https://www.tiktok.com/@user/video/...")
        self.tt_url.grid(row=1, column=0, columnspan=2, pady=(0, 20))
        
        frame_tt_like = ctk.CTkFrame(f)
        frame_tt_like.grid(row=2, column=0, padx=10, sticky="nsew")
        ctk.CTkButton(frame_tt_like, text="❤ DAR HEART", fg_color="#FE2C55", command=lambda: self.start_thread(self.tt_logic_like)).pack(pady=20, padx=20)
        
        frame_tt_comm = ctk.CTkFrame(f)
        frame_tt_comm.grid(row=2, column=1, padx=10, sticky="nsew")
        self.tt_comment_txt = ctk.CTkEntry(frame_tt_comm, placeholder_text="Comentario...", width=200)
        self.tt_comment_txt.pack(pady=10)
        ctk.CTkButton(frame_tt_comm, text="💬 COMENTAR", fg_color="#FE2C55", command=lambda: self.start_thread(self.tt_logic_comment)).pack(pady=10)

    def tt_logic_like(self, alias=None):
        url = self.tt_url.get()
        if not url: return
        try:
            with sync_playwright() as p:
                browser, context = self.get_browser_context(p, alias)
                page = manejar_login(context, alias, self.var_headless.get())
                if page:
                    page.goto(url, wait_until="domcontentloaded")
                    self.simulate_human_behavior(page)
                    like_icon = page.locator('span[data-e2e="like-icon"]').first
                    if like_icon.is_visible():
                        like_icon.click(force=True)
                        self.log(f"TT: ❤ Heart Clicked ({alias})", "SUCCESS")
                        shot = f"logs/tt_like_{alias}_{int(time.time())}.png"
                        page.screenshot(path=shot)
                        self.update_screenshot_preview(shot)
                    else: self.log("TT: Botón Like no encontrado", "ERROR")
                    browser.close()
        except Exception as e: self.log(f"Error TT Like: {e}", "ERROR")

    def tt_logic_comment(self, alias=None):
        url = self.tt_url.get()
        text = self.tt_comment_txt.get()
        if not url or not text: return
        try:
            with sync_playwright() as p:
                browser, context = self.get_browser_context(p, alias)
                page = manejar_login(context, alias, self.var_headless.get())
                if page:
                    page.goto(url)
                    self.human_sleep(2, 4)
                    editor = page.locator('div[contenteditable="true"]').first
                    if not editor.is_visible():
                        page.locator('[data-e2e="comment-icon"]').click()
                        self.human_sleep(1)
                    if editor.is_visible():
                        editor.click()
                        self.human_sleep(0.5)
                        page.keyboard.type(text, delay=50)
                        self.human_sleep(1)
                        btn_post = page.locator('[data-e2e="comment-post"]').first
                        if btn_post.is_visible():
                            btn_post.click()
                            self.log(f"TT: Comentario enviado ({alias})", "SUCCESS")
                        else:
                            page.keyboard.press("Enter")
                            self.log(f"TT: Comentario enviado (Enter) ({alias})", "SUCCESS")
                    else: self.log("TT: Input no accesible", "ERROR")
                    browser.close()
        except Exception as e: self.log(f"Error TT Comment: {e}", "ERROR")

    # =========================================================================
    #                             GESTOR CUENTAS
    # =========================================================================

    # Reemplaza la función anterior con esta versión completa
    def setup_accounts_ui(self):
        tab = self.tab_accounts
        ctk.CTkLabel(tab, text="Agregar Nueva Cuenta a DB", font=("Arial", 14, "bold")).pack(pady=10)
        
        self.entry_new_alias = ctk.CTkEntry(tab, placeholder_text="Alias único (ej: cuenta1)", width=300)
        self.entry_new_alias.pack(pady=5)
        
        self.combo_platform = ctk.CTkComboBox(tab, values=["facebook", "instagram", "twitter", "youtube", "tiktok"], width=300)
        self.combo_platform.pack(pady=5)
        self.combo_platform.set("facebook")

        self.entry_new_user = ctk.CTkEntry(tab, placeholder_text="Usuario / Email", width=300)
        self.entry_new_user.pack(pady=5)
        
        self.entry_new_pass = ctk.CTkEntry(tab, placeholder_text="Contraseña", show="*", width=300)
        self.entry_new_pass.pack(pady=5)
        
        self.entry_new_proxy = ctk.CTkEntry(tab, placeholder_text="Proxy (http://... o vacío)", width=300)
        self.entry_new_proxy.pack(pady=5)
        
        ctk.CTkButton(tab, text="💾 Guardar en SQLite", command=self.save_account_db, fg_color="#27ae60").pack(pady=20)

        # --- ESTA ES LA NUEVA SECCIÓN QUE AGREGAMOS ---
        ctk.CTkLabel(tab, text="📥 Importar desde Carpeta Profiles", font=("Arial", 14, "bold")).pack(pady=(30, 10))
        
        # Cargamos la lista de carpetas físicas
        self.combo_importar = ctk.CTkComboBox(tab, values=self.get_profiles_folder_list(), width=300)
        self.combo_importar.pack(pady=5)
        
        ctk.CTkButton(tab, text="🚀 Vincular Perfil Seleccionado", 
                      command=self.ejecutar_importacion, 
                      fg_color="#3498db").pack(pady=10)

    # Agrega estas dos funciones nuevas justo después de setup_accounts_ui
    def get_profiles_folder_list(self):
        """Lista las carpetas físicas que están en /profiles/"""
        import os
        if not os.path.exists("profiles"): return ["No hay perfiles"]
        carpetas = [d for d in os.listdir("profiles") if os.path.isdir(os.path.join("profiles", d))]
        return carpetas if carpetas else ["Carpeta vacía"]

    def ejecutar_importacion(self):
        alias = self.combo_importar.get()
        if alias in ["No hay perfiles", "Carpeta vacía"]: 
            self.log("Selecciona una carpeta válida de la lista", "WARN")
            return
        
        from login_manager import importar_perfil_especifico
        if importar_perfil_especifico(alias):
            self.log(f"Perfil {alias} vinculado con éxito", "SUCCESS")
            messagebox.showinfo("Éxito", f"El perfil '{alias}' ha sido agregado a la lista.")
            self.refresh_ui_list()
        else:
            self.log(f"Error vinculando {alias} (¿Ya existe?)", "ERROR")


    def save_account_db(self):
        alias = self.entry_new_alias.get()
        user = self.entry_new_user.get()
        pwd = self.entry_new_pass.get()
        proxy = self.entry_new_proxy.get()
        platform = self.combo_platform.get()
        
        if alias and user and pwd:
            ok = guardar_nueva_cuenta(alias, user, pwd, proxy, platform)
            if ok:
                messagebox.showinfo("Éxito", "Cuenta guardada en SQLite")
                self.refresh_ui_list()
                self.entry_new_alias.delete(0, "end")
                self.entry_new_user.delete(0, "end")
                self.entry_new_pass.delete(0, "end")
            else:
                messagebox.showerror("Error", "No se pudo guardar (¿Alias repetido?)")
        else:
            messagebox.showwarning("Faltan datos", "Llena alias, usuario y contraseña")
    def ig_logic_like(self, alias=None):
            url = self.ig_url.get()
            if not url: return

            try:
                with sync_playwright() as p:
                    browser, context = self.get_browser_context(p, alias)
                    page = self.ig_login_helper(context, alias)

                    if not page:
                        context.close()
                        return

                    # Ir al post directamente
                    page.goto(url, wait_until="domcontentloaded")
                    page.wait_for_timeout(5000)

                    # 1. FOCO: Clic en el centro de la pantalla para asegurar que IG escuche el teclado
                    page.mouse.click(400, 400) 
                    page.wait_for_timeout(1000)

                    # 2. ACCIÓN: Tecla 'L' (El método más seguro en IG)
                    page.keyboard.press("l")
                    page.wait_for_timeout(2000)

                    # 3. VERIFICACIÓN: Buscar si el corazón ahora es rojo ("Ya no me gusta")
                    # Se prueban selectores en varios idiomas para evitar fallos
                    check_like = page.locator('svg[aria-label*="Ya no me gusta"], svg[aria-label*="Unlike"]').first
                    
                    if check_like.is_visible(timeout=3000):
                        self.log(f"IG: ❤️ Like CONFIRMADO en {alias}", "SUCCESS")
                    else:
                        # Intento de RESPALDO: Clic directo al icono del corazón
                        btn_respaldo = page.locator('section span svg[aria-label="Me gusta"], section span svg[aria-label="Like"]').first
                        if btn_respaldo.is_visible():
                            btn_respaldo.click(force=True)
                            self.log(f"IG: Like aplicado vía clic forzado ({alias})", "SUCCESS")
                        else:
                            self.log(f"IG: No se pudo aplicar el Like en {alias}", "WARN")

                    # Screenshot de prueba
                    shot = f"logs/ig_like_{alias}_{int(time.time())}.png"
                    page.screenshot(path=shot)
                    self.update_screenshot_preview(shot)
                    
                    browser.close()
            except Exception as e:
                self.log(f"Error en IG Like: {e}", "ERROR")



if __name__ == "__main__":
    if not os.path.exists("logs"): os.makedirs("logs")
    app = SocialBotApp()
    app.mainloop()
import customtkinter as ctk
import threading
import time
import random
import os
from concurrent.futures import ThreadPoolExecutor
from tkinter import messagebox
from PIL import Image

# --- ESTA ES LA LÍNEA QUE FALTABA ---
from playwright.sync_api import sync_playwright 

# IMPORTACIONES MODULARES
# Asegúrate de que login_manager.py, browser_handler.py y bot_logic.py estén en la misma carpeta
try:
    from login_manager import (
        obtener_datos_cuenta, 
        login_manual_asistido, 
        obtener_cuentas_por_plataforma, 
        guardar_nueva_cuenta, 
        importar_perfil_especifico
    )
    from browser_handler import get_browser_context
    from bot_logic import SocialActions
except ImportError as e:
    messagebox.showerror("Error de Dependencias", f"Faltan archivos necesarios:\n{e}")
    exit()

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class SocialBotApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.is_running = False 
        self.title("Social Bot Farm - PRO v5.2 (Fixed Imports)")
        self.geometry("1400x950")
        
        # Almacenamiento de referencias a widgets dinámicos
        self.account_selectors = {} 
        
        # Configuración de Grid Principal
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Inicialización de Componentes UI
        self.setup_sidebar()
        self.setup_main_tabs()
        self.setup_console()

    # =========================================================================
    #                       PANEL LATERAL (SIDEBAR)
    # =========================================================================
    def setup_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=280, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        ctk.CTkLabel(self.sidebar, text="🤖 FARM CONTROL", font=("Segoe UI", 22, "bold")).pack(pady=30)
        
        # --- Opciones de Ejecución ---
        self.var_headless = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(self.sidebar, text="Modo Oculto (Headless)", variable=self.var_headless).pack(pady=10, padx=20, anchor="w")
        
        self.var_batch = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(self.sidebar, text="🔥 MODO MASIVO (100+)", variable=self.var_batch, fg_color="#e63946").pack(pady=10, padx=20, anchor="w")

        # --- Slider de Hilos (Concurrency) ---
        ctk.CTkLabel(self.sidebar, text="Hilos Simultáneos:").pack(padx=20, anchor="w", pady=(10,0))
        self.lbl_workers = ctk.CTkLabel(self.sidebar, text="1", font=("Arial", 12, "bold"))
        self.lbl_workers.pack(padx=20, anchor="w")
        
        self.slider_workers = ctk.CTkSlider(self.sidebar, from_=1, to=10, number_of_steps=9, command=lambda v: self.lbl_workers.configure(text=str(int(v))))
        self.slider_workers.pack(pady=10, padx=20, fill="x")
        self.slider_workers.set(1)

        # --- Botones Generales ---
        ctk.CTkButton(self.sidebar, text="🔄 Refrescar Listas", command=self.on_tab_change, border_width=1, fg_color="transparent").pack(pady=20)
        
        ctk.CTkButton(self.sidebar, text="🔑 Login Manual (Global)", 
                      command=lambda: self.run_manual_login(None),
                      fg_color="#D35400", hover_color="#E67E22").pack(pady=5, padx=20, fill="x")

        # --- Vista Previa de Pantalla ---
        ctk.CTkLabel(self.sidebar, text="📸 Última Actividad:").pack(side="bottom", pady=(0, 5))
        self.lbl_screenshot = ctk.CTkLabel(self.sidebar, text="[Sin imagen]", width=200, height=120, fg_color="#2b2b2b")
        self.lbl_screenshot.pack(side="bottom", pady=20, padx=20)

    # =========================================================================
    #                       SISTEMA DE PESTAÑAS (TABS)
    # =========================================================================
    def setup_main_tabs(self):
        self.tabs = ctk.CTkTabview(self, command=self.on_tab_change)
        self.tabs.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")

        # Definición de Plataformas soportadas
        self.plataformas = {
            "Facebook": "facebook",
            "Instagram": "instagram",
            "TikTok": "tiktok",
            "YouTube": "youtube",
            "X (Twitter)": "twitter"
        }

        # Generación dinámica de Tabs para cada red social
        for name, key in self.plataformas.items():
            tab = self.tabs.add(name)
            self.build_platform_ui(tab, key)

        # Tab Especial: Calentamiento
        self.tab_warmup = self.tabs.add("🔥 Calentamiento")
        self.setup_warmup_ui()
        
        # Tab Especial: Gestión de Cuentas
        self.tab_accounts = self.tabs.add("⚙ Gestor Cuentas")
        self.setup_accounts_ui()

    def build_platform_ui(self, tab, platform_key):
        """Construye la interfaz genérica para cada red social"""
        tab.grid_columnconfigure(0, weight=1)
        
        # 1. HEADER: Selector de Cuentas
        header_frame = ctk.CTkFrame(tab)
        header_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(header_frame, text=f"Cuentas {platform_key.upper()}:", font=("Arial", 12, "bold")).pack(side="left", padx=10)
        
        # Cargar lista inicial
        cuentas = obtener_cuentas_por_plataforma(platform_key)
        selector = ctk.CTkComboBox(header_frame, values=cuentas, width=280)
        selector.pack(side="left", padx=10)
        
        # Guardar referencia para acceder luego
        self.account_selectors[platform_key] = selector

        # 2. BODY: Controles específicos
        body_frame = ctk.CTkFrame(tab, fg_color="transparent")
        body_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Llamar a la función constructora específica
        if platform_key == "facebook": self.ui_facebook(body_frame)
        elif platform_key == "instagram": self.ui_instagram(body_frame)
        elif platform_key == "tiktok": self.ui_tiktok(body_frame)
        elif platform_key == "youtube": self.ui_youtube(body_frame)
        elif platform_key == "twitter": self.ui_twitter(body_frame)

    def on_tab_change(self):
        """Evento al cambiar de pestaña: Refresca la lista de usuarios correspondiente"""
        try:
            tab_name = self.tabs.get()
            key_map = {k: v for k, v in self.plataformas.items()}
            
            if tab_name in key_map:
                platform_key = key_map[tab_name]
                nuevas_cuentas = obtener_cuentas_por_plataforma(platform_key)
                
                if platform_key in self.account_selectors:
                    selector = self.account_selectors[platform_key]
                    selector.configure(values=nuevas_cuentas)
                    if nuevas_cuentas and nuevas_cuentas[0] != "Sin cuentas":
                        selector.set(nuevas_cuentas[0])
        except Exception: pass

    # =========================================================================
    #               INTERFACES ESPECÍFICAS (CONTROLES INTERNOS)
    # =========================================================================
    
    def ui_facebook(self, parent):
        parent.grid_columnconfigure((0, 1, 2), weight=1)
        
        # URL
        ctk.CTkLabel(parent, text="Link del Post:", font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=3)
        self.fb_url = ctk.CTkEntry(parent, width=400, placeholder_text="https://facebook.com/...")
        self.fb_url.grid(row=1, column=0, columnspan=3, pady=10)

        # Reacciones
        ctk.CTkLabel(parent, text="Tipo Reacción:").grid(row=2, column=0)
        self.fb_react_combo = ctk.CTkComboBox(parent, values=["Me gusta", "Me encanta", "Me divierte", "Me asombra"])
        self.fb_react_combo.grid(row=3, column=0, pady=5)
        
        ctk.CTkButton(parent, text="👍 Reaccionar", fg_color="#1877F2",
                      command=lambda: self.start_execution("fb_react", "facebook")).grid(row=4, column=0, padx=5, pady=10)

        # Comentarios
        ctk.CTkLabel(parent, text="Texto Comentario:").grid(row=2, column=1)
        self.fb_comment_txt = ctk.CTkEntry(parent, placeholder_text="Escribe algo...", width=200)
        self.fb_comment_txt.grid(row=3, column=1, pady=5)
        
        ctk.CTkButton(parent, text="💬 Comentar", fg_color="#1877F2",
                      command=lambda: self.start_execution("fb_comment", "facebook")).grid(row=4, column=1, padx=5, pady=10)

    def ui_instagram(self, parent):
        parent.grid_columnconfigure((0, 1), weight=1)
        
        # URL
        ctk.CTkLabel(parent, text="Link Instagram:", text_color="#C13584").grid(row=0, column=0, columnspan=2)
        self.ig_url = ctk.CTkEntry(parent, width=400, placeholder_text="https://instagram.com/p/...")
        self.ig_url.grid(row=1, column=0, columnspan=2, pady=10)
        
        # Like
        ctk.CTkButton(parent, text="❤ DAR LIKE", fg_color="#C13584", 
                      command=lambda: self.start_execution("ig_like", "instagram")).grid(row=2, column=0, padx=10, pady=10)
        
        # Comentario
        self.ig_comment_txt = ctk.CTkEntry(parent, placeholder_text="Comentario...", width=200)
        self.ig_comment_txt.grid(row=2, column=1, pady=5)
        ctk.CTkButton(parent, text="💬 COMENTAR", fg_color="#C13584", 
                      command=lambda: self.start_execution("ig_comment", "instagram")).grid(row=3, column=1, padx=10, pady=5)

    def ui_tiktok(self, parent):
        parent.grid_columnconfigure((0, 1), weight=1)
        
        # URL
        ctk.CTkLabel(parent, text="Link TikTok:", text_color="#00f2ea").grid(row=0, column=0, columnspan=2)
        self.tt_url = ctk.CTkEntry(parent, width=400)
        self.tt_url.grid(row=1, column=0, columnspan=2, pady=10)
        
        # Like
        ctk.CTkButton(parent, text="❤ DAR HEART", fg_color="#FE2C55", hover_color="#000000",
                      command=lambda: self.start_execution("tt_like", "tiktok")).grid(row=2, column=0, padx=10, pady=10)

        # Comentario
        self.tt_comment_txt = ctk.CTkEntry(parent, placeholder_text="Comentario...", width=200)
        self.tt_comment_txt.grid(row=2, column=1, pady=5)
        ctk.CTkButton(parent, text="💬 COMENTAR", fg_color="#FE2C55", hover_color="#000000",
                      command=lambda: self.start_execution("tt_comment", "tiktok")).grid(row=3, column=1, padx=10, pady=5)

    def ui_youtube(self, parent):
        parent.grid_columnconfigure((0, 1), weight=1)
        
        # URL
        ctk.CTkLabel(parent, text="Link YouTube:", text_color="#FF0000").grid(row=0, column=0, columnspan=2)
        self.yt_url = ctk.CTkEntry(parent, width=400)
        self.yt_url.grid(row=1, column=0, columnspan=2, pady=10)
        
        # Like
        ctk.CTkButton(parent, text="👍 LIKE", fg_color="#FF0000", 
                      command=lambda: self.start_execution("yt_like", "youtube")).grid(row=2, column=0, padx=10, pady=10)

        # Comentario
        self.yt_comment_txt = ctk.CTkEntry(parent, placeholder_text="Comentario...", width=200)
        self.yt_comment_txt.grid(row=2, column=1, pady=5)
        ctk.CTkButton(parent, text="💬 COMENTAR", fg_color="#FF0000", 
                      command=lambda: self.start_execution("yt_comment", "youtube")).grid(row=3, column=1, padx=10, pady=5)

    def ui_twitter(self, parent):
        parent.grid_columnconfigure((0, 1), weight=1)
        
        # URL
        ctk.CTkLabel(parent, text="Link Tweet (X):", text_color="#1DA1F2").grid(row=0, column=0, columnspan=2)
        self.x_url = ctk.CTkEntry(parent, width=400)
        self.x_url.grid(row=1, column=0, columnspan=2, pady=10)
        
        # Like
        ctk.CTkButton(parent, text="❤ LIKE", fg_color="#1DA1F2", 
                      command=lambda: self.start_execution("x_like", "twitter")).grid(row=2, column=0, padx=10, pady=10)

        # Reply
        self.x_reply_txt = ctk.CTkEntry(parent, placeholder_text="Tu respuesta...", width=200)
        self.x_reply_txt.grid(row=2, column=1, pady=5)
        ctk.CTkButton(parent, text="✍ RESPONDER", fg_color="#1DA1F2", 
                      command=lambda: self.start_execution("x_reply", "twitter")).grid(row=3, column=1, padx=10, pady=5)

    # =========================================================================
    #                       UI CALENTAMIENTO
    # =========================================================================
    def setup_warmup_ui(self):
        f = self.tab_warmup
        ctk.CTkLabel(f, text="🏋️ RUTINA DE CALENTAMIENTO AUTOMÁTICO", font=("Arial", 16, "bold")).pack(pady=20)
        
        ctk.CTkLabel(f, text="Selecciona Plataforma a Calentar:").pack(pady=5)
        self.combo_warmup_plat = ctk.CTkComboBox(f, values=list(self.plataformas.keys()))
        self.combo_warmup_plat.pack(pady=10)
        self.combo_warmup_plat.set("Facebook")

        ctk.CTkLabel(f, text="Duración por cuenta (minutos):").pack(pady=5)
        self.slider_warmup = ctk.CTkSlider(f, from_=1, to=20, number_of_steps=19)
        self.slider_warmup.pack(pady=10)
        
        self.lbl_warmup_val = ctk.CTkLabel(f, text="5 min")
        self.lbl_warmup_val.pack()
        self.slider_warmup.configure(command=lambda v: self.lbl_warmup_val.configure(text=f"{int(v)} min"))
        self.slider_warmup.set(5)

        ctk.CTkButton(f, text="▶ INICIAR CALENTAMIENTO", fg_color="#27ae60", height=50, font=("Arial", 14, "bold"),
                      command=self.trigger_warmup).pack(pady=30)

    def trigger_warmup(self):
        plat_ui = self.combo_warmup_plat.get()
        plat_key = self.plataformas.get(plat_ui, "facebook")
        self.start_execution("warmup", plat_key)

    # =========================================================================
    #                       MOTOR DE EJECUCIÓN
    # =========================================================================
    def start_execution(self, action_type, platform):
        if hasattr(self, 'is_running') and self.is_running:
            self.log("⚠️ El sistema está ocupado. Espera...", "WARN")
            return

        params = {}
        if action_type != "warmup":
            if platform == "facebook":
                params['url'] = self.fb_url.get()
                params['reaction'] = self.fb_react_combo.get()
                params['text'] = self.fb_comment_txt.get()
            elif platform == "instagram":
                params['url'] = self.ig_url.get()
                params['text'] = self.ig_comment_txt.get()
            elif platform == "tiktok":
                params['url'] = self.tt_url.get()
                params['text'] = self.tt_comment_txt.get()
            elif platform == "youtube":
                params['url'] = self.yt_url.get()
                params['text'] = self.yt_comment_txt.get()
            elif platform == "twitter":
                params['url'] = self.x_url.get()
                params['text'] = self.x_reply_txt.get()
        else:
            params['minutes'] = int(self.slider_warmup.get())

        target_func = None
        kwargs_gen = None
        
        common_args = {
            "headless": self.var_headless.get(),
            "logger": self.log,
            "update_preview_cb": self.update_preview
        }

        # Mapeo de Acciones
        if action_type == "warmup":
            target_func = SocialActions.warmup
            kwargs_gen = lambda alias: {"alias": alias, "minutes": params['minutes'], **common_args}
        elif action_type == "fb_react":
            target_func = SocialActions.fb_reaction
            kwargs_gen = lambda alias: {"alias": alias, "url": params['url'], "reaction": params['reaction'], **common_args}
        elif action_type == "fb_comment":
            target_func = SocialActions.fb_comment
            kwargs_gen = lambda alias: {"alias": alias, "url": params['url'], "text": params['text'], **common_args}
        elif action_type == "ig_like":
            target_func = SocialActions.ig_like
            kwargs_gen = lambda alias: {"alias": alias, "url": params['url'], **common_args}
        elif action_type == "ig_comment":
            target_func = SocialActions.ig_comment
            kwargs_gen = lambda alias: {"alias": alias, "url": params['url'], "text": params['text'], **common_args}
        elif action_type == "tt_like":
            target_func = SocialActions.tt_like
            kwargs_gen = lambda alias: {"alias": alias, "url": params['url'], **common_args}
        elif action_type == "tt_comment":
            target_func = SocialActions.tt_comment
            kwargs_gen = lambda alias: {"alias": alias, "url": params['url'], "text": params['text'], **common_args}
        elif action_type == "yt_like":
            target_func = SocialActions.yt_like
            kwargs_gen = lambda alias: {"alias": alias, "url": params['url'], **common_args}
        elif action_type == "yt_comment":
            target_func = SocialActions.yt_comment
            kwargs_gen = lambda alias: {"alias": alias, "url": params['url'], "text": params['text'], **common_args}
        elif action_type == "x_like":
            target_func = SocialActions.x_like
            kwargs_gen = lambda alias: {"alias": alias, "url": params['url'], **common_args}
        elif action_type == "x_reply":
            target_func = SocialActions.x_reply
            kwargs_gen = lambda alias: {"alias": alias, "url": params['url'], "text": params['text'], **common_args}

        if self.var_batch.get():
            threading.Thread(target=lambda: self.run_batch(target_func, platform, kwargs_gen)).start()
        else:
            threading.Thread(target=lambda: self.run_single(target_func, platform, kwargs_gen)).start()

    def run_single(self, func, platform, kwargs_gen):
        self.is_running = True
        alias = self.account_selectors[platform].get()
        
        if not alias or alias == "Sin cuentas":
            self.log("❌ Error: Selecciona una cuenta válida.", "ERROR")
            self.is_running = False
            return
        
        try:
            self.log(f"Iniciando tarea única: {alias}", "INFO")
            func(**kwargs_gen(alias))
        except Exception as e:
            self.log(f"Error Crítico: {e}", "ERROR")
        
        self.is_running = False

    def run_batch(self, func, platform, kwargs_gen):
        self.is_running = True
        cuentas = obtener_cuentas_por_plataforma(platform)
        
        if not cuentas or cuentas == ["Sin cuentas"]:
            self.log(f"❌ Error: No hay cuentas en {platform} para masivo.", "ERROR")
            self.is_running = False
            return

        workers = int(self.slider_workers.get())
        total = len(cuentas)
        self.log(f"🔥 INICIANDO MODO MASIVO: {total} cuentas | {workers} hilos", "BATCH")
        
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = []
            for i, alias in enumerate(cuentas):
                delay = random.uniform(5, 15) + (i * 2)
                self.log(f"⏳ {alias} en cola (Espera: {delay:.1f}s)", "INFO")
                futures.append(executor.submit(self._batch_wrapper, func, kwargs_gen, alias, delay))
            
            for f in futures:
                try: f.result()
                except Exception: pass
        
        self.log("✅ PROCESO MASIVO FINALIZADO", "SUCCESS")
        self.is_running = False

    def _batch_wrapper(self, func, kwargs_gen, alias, delay):
        time.sleep(delay)
        try:
            func(**kwargs_gen(alias))
        except Exception as e:
            self.log(f"Fallo en {alias}: {e}", "ERROR")

    # =========================================================================
    #                       UTILIDADES DE INTERFAZ
    # =========================================================================
    def setup_console(self):
        self.log_frame = ctk.CTkFrame(self, height=150)
        self.log_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        self.console = ctk.CTkTextbox(self.log_frame, height=120, font=("Consolas", 11))
        self.console.pack(fill="both", padx=10, pady=5)
        self.console.configure(state="disabled")

    def log(self, msg, type="INFO"):
        ts = time.strftime("%H:%M:%S")
        text = f"[{ts}] [{type}] {msg}\n"
        
        def _update():
            self.console.configure(state="normal")
            self.console.insert("end", text)
            self.console.see("end")
            self.console.configure(state="disabled")
            print(text.strip())
        
        self.after(0, _update)

    def update_preview(self):
        path = "logs/preview_last.png"
        def _refresh():
            if os.path.exists(path):
                try:
                    img = Image.open(path)
                    img.thumbnail((200, 150))
                    photo = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
                    self.lbl_screenshot.configure(image=photo, text="")
                except: pass
        self.after(0, _refresh)

    # --- UI GESTIÓN DE CUENTAS ---
    def setup_accounts_ui(self):
        tab = self.tab_accounts
        ctk.CTkLabel(tab, text="Agregar Nueva Cuenta a DB", font=("Arial", 14, "bold")).pack(pady=10)
        
        self.entry_new_alias = ctk.CTkEntry(tab, placeholder_text="Alias único (ej: fb_usuario1)")
        self.entry_new_alias.pack(pady=5)
        
        self.combo_platform = ctk.CTkComboBox(tab, values=["facebook", "instagram", "tiktok", "youtube", "twitter"])
        self.combo_platform.pack(pady=5)
        
        self.entry_new_user = ctk.CTkEntry(tab, placeholder_text="Usuario / Email")
        self.entry_new_user.pack(pady=5)
        
        self.entry_new_pass = ctk.CTkEntry(tab, placeholder_text="Contraseña", show="*")
        self.entry_new_pass.pack(pady=5)
        
        self.entry_new_proxy = ctk.CTkEntry(tab, placeholder_text="Proxy (http://user:pass@ip:port)")
        self.entry_new_proxy.pack(pady=5)
        
        ctk.CTkButton(tab, text="💾 Guardar Cuenta", command=self.save_account, fg_color="#27ae60").pack(pady=20)
        
        # Importación
        ctk.CTkLabel(tab, text="--- O Importar Perfil Local ---").pack(pady=10)
        self.combo_import = ctk.CTkComboBox(tab, values=self.get_profiles_list())
        self.combo_import.pack(pady=5)
        ctk.CTkButton(tab, text="📥 Vincular Carpeta Local", command=self.import_local_profile, fg_color="#3498db").pack(pady=5)

    def save_account(self):
        alias = self.entry_new_alias.get()
        if alias:
            if guardar_nueva_cuenta(alias, self.entry_new_user.get(), self.entry_new_pass.get(), 
                                    self.entry_new_proxy.get(), self.combo_platform.get()):
                messagebox.showinfo("Éxito", "Cuenta guardada correctamente")
                self.on_tab_change()
            else:
                messagebox.showerror("Error", "No se pudo guardar (Alias duplicado).")

    def get_profiles_list(self):
        if not os.path.exists("profiles"): return ["No hay carpetas"]
        dirs = [d for d in os.listdir("profiles") if os.path.isdir(os.path.join("profiles", d))]
        return dirs if dirs else ["Carpeta vacía"]

    def import_local_profile(self):
        alias = self.combo_import.get()
        if alias and alias != "No hay carpetas":
            if importar_perfil_especifico(alias):
                messagebox.showinfo("Importado", f"Perfil {alias} vinculado exitosamente.")
                self.on_tab_change()
            else:
                messagebox.showerror("Error", "Fallo al importar perfil.")

    # --- IMPLEMENTACIÓN DE LOGIN MANUAL ---
    def run_manual_login(self, alias=None):
        if not alias:
            try:
                tab = self.tabs.get()
                key_map = {k: v for k, v in self.plataformas.items()}
                if tab in key_map:
                    plat = key_map[tab]
                    alias = self.account_selectors[plat].get()
            except: pass
        
        if not alias or alias == "Sin cuentas":
            messagebox.showwarning("Aviso", "Selecciona una cuenta de la lista primero.")
            return

        def _manual_login_thread():
            self.log(f"🔵 Iniciando Login Manual para: {alias}...", "INFO")
            data = obtener_datos_cuenta(alias)
            with sync_playwright() as p:
                from browser_handler import get_browser_context
                # HEADLESS = FALSE obligatorio para ver la ventana
                context = get_browser_context(p, alias, headless=False, log_callback=self.log)
                
                # Llamar al asistente de login manager
                if login_manual_asistido(context, alias, data):
                    self.log(f"✅ Login Manual COMPLETADO: {alias}", "SUCCESS")
                else:
                    self.log(f"❌ Login Manual Cancelado: {alias}", "ERROR")
                context.close()
        
        threading.Thread(target=_manual_login_thread).start()

if __name__ == "__main__":
    if not os.path.exists("logs"): os.makedirs("logs")
    if not os.path.exists("profiles"): os.makedirs("profiles")
    app = SocialBotApp()
    app.mainloop()
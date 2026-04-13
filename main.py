import customtkinter as ctk
import threading
import time
import random
import os
from concurrent.futures import ThreadPoolExecutor
from tkinter import messagebox
from PIL import Image
import subprocess  # <--- AGREGAR ESTO AL INICIO CON LOS OTROS IMPORTS

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
    from mobile_manager import get_mobile_manager, check_adb_available
    from utils import exportar_cuenta_excel
except ImportError as e:
    messagebox.showerror("Error de Dependencias", f"Faltan archivos necesarios:\n{e}")
    exit()

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

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
        self.mobile_manager = get_mobile_manager(logger=self.log)
    # =========================================================================
    #                       PANEL LATERAL (SIDEBAR)
    # =========================================================================
    def setup_sidebar(self):
            # Sidebar con gradiente visual (fondo oscuro con toque azul)
            self.sidebar = ctk.CTkFrame(self, width=320, corner_radius=0, fg_color=("#0f172a", "#0f172a"))
            self.sidebar.grid(row=0, column=0, sticky="nsew")
            self.sidebar.grid_propagate(False)
            
            # --- HEADER ---
            header_frame = ctk.CTkFrame(self.sidebar, fg_color=("#1e3a5f", "#1e3a5f"), corner_radius=15)
            header_frame.pack(fill="x", padx=12, pady=(15, 10))
            
            ctk.CTkLabel(header_frame, text="🤖", font=("Segoe UI", 40)).pack(pady=(12, 5))
            ctk.CTkLabel(header_frame, text="FARM CONTROL", font=("Segoe UI", 20, "bold"), text_color="#60a5fa").pack()
            ctk.CTkLabel(header_frame, text="Social Bot Manager Pro", font=("Segoe UI", 10), text_color="#93c5fd").pack(pady=(3, 12))
            
            # Separador
            ctk.CTkFrame(self.sidebar, height=1, fg_color="#1e40af").pack(fill="x", padx=15, pady=8)
            
            # --- CONFIGURACIÓN ---
            config_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
            config_frame.pack(fill="x", padx=12, pady=5)
            ctk.CTkLabel(config_frame, text="⚙️ CONFIGURACIÓN", font=("Segoe UI", 11, "bold"), text_color="#60a5fa").pack(anchor="w", pady=(5, 8))
            
            self.var_headless = ctk.BooleanVar(value=False)
            ctk.CTkCheckBox(config_frame, text="👁️ Modo Oculto", variable=self.var_headless,
                        font=("Segoe UI", 10), text_color="#e0e7ff").pack(anchor="w", pady=4)
            
            self.var_batch = ctk.BooleanVar(value=False)
            ctk.CTkCheckBox(config_frame, text="🔥 Modo Masivo", variable=self.var_batch, 
                        fg_color="#ef4444", hover_color="#dc2626",
                        font=("Segoe UI", 10, "bold"), text_color="#fecaca").pack(anchor="w", pady=4)
            
            self.var_mobile_mode = ctk.BooleanVar(value=False)
            ctk.CTkCheckBox(config_frame, text="📱 Modo Móvil (ADB)", variable=self.var_mobile_mode,
                        fg_color="#0ea5e9", hover_color="#0284c7",
                        font=("Segoe UI", 10, "bold"), text_color="#bae6fd",
                        command=self.on_mobile_mode_toggle).pack(anchor="w", pady=4)

            self.var_use_ai = ctk.BooleanVar(value=False)
            ctk.CTkCheckBox(config_frame, text="🧠 Cerebro (IA)", variable=self.var_use_ai,
                    font=("Segoe UI", 10), text_color="#e0e7ff").pack(anchor="w", pady=4)

            # Separador
            ctk.CTkFrame(self.sidebar, height=1, fg_color="#1e40af").pack(fill="x", padx=15, pady=8)

            # --- HILOS (WORKERS) ---
            workers_frame = ctk.CTkFrame(self.sidebar, fg_color=("#1e3a5f", "#1e3a5f"), corner_radius=10)
            workers_frame.pack(fill="x", padx=12, pady=5)
            
            ctk.CTkLabel(workers_frame, text="🔀 Hilos Simultáneos", font=("Segoe UI", 11, "bold"), text_color="#60a5fa").pack(anchor="w", padx=12, pady=(8, 4))
            
            slider_container = ctk.CTkFrame(workers_frame, fg_color="transparent")
            slider_container.pack(fill="x", padx=12, pady=(0, 8))
            
            self.lbl_workers = ctk.CTkLabel(slider_container, text="1", font=("Segoe UI", 13, "bold"), 
                                        width=35, fg_color="#0284c7", text_color="white", corner_radius=6)
            self.lbl_workers.pack(side="right", padx=(8, 0))
            
            self.slider_workers = ctk.CTkSlider(slider_container, from_=1, to=10, number_of_steps=9, 
                                            command=lambda v: self.lbl_workers.configure(text=str(int(v))),
                                            fg_color="#1e40af", progress_color="#0284c7")
            self.slider_workers.pack(side="left", fill="x", expand=True)
            self.slider_workers.set(1)

            # Separador
            ctk.CTkFrame(self.sidebar, height=1, fg_color="#1e40af").pack(fill="x", padx=15, pady=8)

            # --- ACCIONES RÁPIDAS + RED (OPTIMIZADO) ---
            actions_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
            actions_frame.pack(fill="x", padx=12, pady=5)
            ctk.CTkLabel(actions_frame, text="⚡ ACCIONES RÁPIDAS", font=("Segoe UI", 11, "bold"), text_color="#60a5fa").pack(anchor="w", pady=(5, 5))
            
            # Botones un poco más bajos (height=32) para ahorrar espacio
            ctk.CTkButton(actions_frame, text="🔄 Refrescar Listas", command=self.on_tab_change, 
                        border_width=0, fg_color="#1e40af", hover_color="#1e3a8a", text_color="#60a5fa",
                        font=("Segoe UI", 10, "bold"), height=32, corner_radius=8).pack(fill="x", pady=4)
            
            ctk.CTkButton(actions_frame, text="🔑 Login Manual", 
                        command=lambda: self.run_manual_login(None),
                        fg_color="#f97316", hover_color="#ea580c", text_color="#ffffff",
                        font=("Segoe UI", 10, "bold"), height=32, corner_radius=8).pack(fill="x", pady=4)

            # >> AQUÍ ESTÁ EL SWITCH DE ETHERNET INTEGRADO <<
            eth_container = ctk.CTkFrame(actions_frame, fg_color="#0f172a", corner_radius=6)
            eth_container.pack(fill="x", pady=(6, 2))
            
            self.var_ethernet_status = ctk.BooleanVar(value=True) 
            
            self.switch_ethernet = ctk.CTkSwitch(eth_container, text="Ethernet ON",
                                                variable=self.var_ethernet_status,
                                                onvalue=True, offvalue=False,
                                                command=self.toggle_ethernet_adapter,
                                                font=("Segoe UI", 10, "bold"),
                                                height=20, switch_width=36, switch_height=18,
                                                progress_color="#10b981", fg_color="#ef4444")
            self.switch_ethernet.pack(padx=10, pady=8)

            # Separador final
            ctk.CTkFrame(self.sidebar, height=1, fg_color="#1e40af").pack(fill="x", padx=15, pady=8)

            # --- VISTA PREVIA (TAMAÑO REDUCIDO) ---
            preview_frame = ctk.CTkFrame(self.sidebar, fg_color="#1e3a5f", corner_radius=12)
            # expand=False es clave para que no empuje todo hacia arriba
            preview_frame.pack(side="bottom", fill="x", padx=12, pady=15, expand=False)
            
            preview_header = ctk.CTkLabel(preview_frame, text="📸 Última Actividad", 
                                        font=("Segoe UI", 11, "bold"), text_color="#60a5fa")
            preview_header.pack(anchor="w", padx=12, pady=(8, 4))
            
            # Altura reducida a 100px (antes 140) para que quepa el switch
            self.lbl_screenshot = ctk.CTkLabel(preview_frame, text="[Sin imagen]", 
                                            fg_color="#0f172a", corner_radius=10,
                                            font=("Segoe UI", 9), text_color="#9ca3af",
                                            width=280, height=100)
            self.lbl_screenshot.pack(padx=12, pady=(0, 12), fill="both")

    # =========================================================================
    #                       SISTEMA DE PESTAÑAS (TABS)
    # =========================================================================
    def setup_main_tabs(self):
        self.tabs = ctk.CTkTabview(self, command=self.on_tab_change, 
                                   fg_color="transparent", border_width=0,
                                   segmented_button_fg_color="#1e3a5f",
                                   segmented_button_selected_color="#0284c7",
                                   segmented_button_selected_hover_color="#0284c7",
                                   text_color="#60a5fa")
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
        
        # Tab Especial: Estado de Cuentas
        self.tab_status = self.tabs.add("📊 Estado Cuentas")
        self.setup_status_ui()

        self.tab_mobile_creator = self.tabs.add("📱 Creador Móvil")
        self.setup_mobile_creator_ui()
        
        # Asegurar que los selectores de cuenta para cada plataforma estén poblados
        try:
            self.refresh_all_account_selectors()
        except Exception:
            pass

    def build_platform_ui(self, tab, platform_key):
        """Construye la interfaz genérica para cada red social"""
        tab.grid_columnconfigure(0, weight=1)
        
        # 1. HEADER: Selector de Cuentas con mejor diseño
        header_frame = ctk.CTkFrame(tab, corner_radius=12, fg_color="#1e3a5f", border_width=1, border_color="#1e40af")
        header_frame.pack(fill="x", padx=15, pady=(15, 10))
        header_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(header_frame, text="👤 Cuenta:", font=("Segoe UI", 12, "bold"), 
                     text_color="#60a5fa").grid(row=0, column=0, padx=15, pady=12, sticky="w")
        
        # Cargar lista inicial
        cuentas = obtener_cuentas_por_plataforma(platform_key)
        selector = ctk.CTkComboBox(header_frame, values=cuentas, width=300, 
                                  font=("Segoe UI", 11), dropdown_font=("Segoe UI", 11),
                                  fg_color="#0f172a", border_color="#1e40af", border_width=1,
                                  button_color="#1e40af", button_hover_color="#0284c7",
                                  text_color="#e5e7eb")
        selector.grid(row=0, column=1, padx=15, pady=12, sticky="ew")
        
        # Guardar referencia para acceder luego
        self.account_selectors[platform_key] = selector

        # 2. BODY: Controles específicos
        body_frame = ctk.CTkFrame(tab, fg_color="transparent")
        body_frame.pack(fill="both", expand=True, padx=15, pady=10)

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
            
            # Si es el tab de Estado de Cuentas, recarga los datos frescos
            if tab_name == "📊 Estado Cuentas":
                self.refresh_status_ui()
                return
            
            if tab_name in key_map:
                platform_key = key_map[tab_name]
                nuevas_cuentas = obtener_cuentas_por_plataforma(platform_key)
                
                if platform_key in self.account_selectors:
                    selector = self.account_selectors[platform_key]
                    selector.configure(values=nuevas_cuentas)
                    if nuevas_cuentas and nuevas_cuentas[0] != "Sin cuentas":
                        selector.set(nuevas_cuentas[0])
        except Exception: pass
    
    def on_mobile_mode_toggle(self):
        """Callback cuando se activa/desactiva el modo móvil"""
        if self.var_mobile_mode.get():
            # Verificar ADB
            if not check_adb_available():
                self.log("⚠️ ADB no está disponible. Instala Android Debug Bridge.", "ERROR")
                self.var_mobile_mode.set(False)
                messagebox.showerror("ADB No Disponible", 
                    "ADB no está instalado o no está en el PATH.\n\n"
                    "Instala Android SDK Platform Tools y agrega ADB al PATH.")
                return
            
            # Verificar dispositivos
            devices = self.mobile_manager.get_available_devices()
            if not devices:
                self.log("⚠️ No hay dispositivos móviles configurados", "WARN")
                messagebox.showwarning("Sin Dispositivos", 
                    "No hay dispositivos móviles configurados.\n\n"
                    "Configura los dispositivos en mobile_manager.py o mobile_devices.json")
                self.var_mobile_mode.set(False)
            else:
                self.log(f"📱 Modo Móvil activado. {len(devices)} dispositivo(s) disponible(s)", "INFO")
        else:
            self.log("📱 Modo Móvil desactivado. Usando red de PC", "INFO")

    # =========================================================================
    #               INTERFACES ESPECÍFICAS (CONTROLES INTERNOS)
    # =========================================================================
    
    def ui_facebook(self, parent):
        parent.grid_columnconfigure((0, 1, 2), weight=1)
        parent.grid_rowconfigure(1, weight=1)
        
        # URL Section
        url_frame = ctk.CTkFrame(parent, corner_radius=12, fg_color="#1e3a5f", border_width=1, border_color="#1e40af")
        url_frame.grid(row=0, column=0, columnspan=3, sticky="ew", padx=10, pady=(0, 15))
        url_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(url_frame, text="🔗 URL del Post", font=("Segoe UI", 13, "bold"), 
                     text_color="#60a5fa").grid(row=0, column=0, padx=15, pady=(12, 5), sticky="w")
        self.fb_url = ctk.CTkEntry(url_frame, placeholder_text="https://facebook.com/...", 
                                   font=("Segoe UI", 11), height=35, 
                                   fg_color="#0f172a", border_color="#1e40af", border_width=1,
                                   text_color="#e5e7eb", placeholder_text_color="#6b7280")
        self.fb_url.grid(row=1, column=0, padx=15, pady=(0, 12), sticky="ew")

        # Reacciones Card
        react_frame = ctk.CTkFrame(parent, corner_radius=12, fg_color="#1e3a5f", border_width=1, border_color="#1e40af")
        react_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        react_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(react_frame, text="👍 Reacciones", font=("Segoe UI", 13, "bold"), text_color="#60a5fa").pack(pady=(15, 10))
        ctk.CTkLabel(react_frame, text="Tipo de reacción:", font=("Segoe UI", 10), text_color="#9ca3af").pack(pady=(0, 5))
        self.fb_react_combo = ctk.CTkComboBox(react_frame, values=["Me gusta", "Me encanta", "Me divierte", "Me asombra"],
                                             font=("Segoe UI", 11), width=200, height=35,
                                             fg_color="#0f172a", border_color="#1e40af", border_width=1,
                                             button_color="#1e40af", button_hover_color="#0284c7",
                                             text_color="#e5e7eb")
        self.fb_react_combo.pack(pady=5)
        self.fb_react_combo.set("Me gusta")
        
        ctk.CTkButton(react_frame, text="👍 Reaccionar", fg_color="#1877F2", hover_color="#0d47a1",
                     font=("Segoe UI", 12, "bold"), height=40, corner_radius=8,
                     command=lambda: self.start_execution("fb_react", "facebook")).pack(pady=(15, 15), padx=15, fill="x")

        # Comentarios Card
        comment_frame = ctk.CTkFrame(parent, corner_radius=12, fg_color="#1e3a5f", border_width=1, border_color="#1e40af")
        comment_frame.grid(row=1, column=1, sticky="nsew", padx=10, pady=5)
        comment_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(comment_frame, text="💬 Comentarios", font=("Segoe UI", 13, "bold"), text_color="#60a5fa").pack(pady=(15, 5))
        ctk.CTkLabel(comment_frame, text="Cada línea = 1 comentario", font=("Segoe UI", 9), text_color="#9ca3af").pack(pady=(0, 10))
        
        self.fb_comment_txt = ctk.CTkTextbox(comment_frame, width=250, height=150, 
                                            font=("Segoe UI", 11), corner_radius=8,
                                            fg_color="#0f172a", border_width=1, border_color="#1e40af",
                                            text_color="#e5e7eb")
        self.fb_comment_txt.pack(pady=5, padx=15, fill="both", expand=True)
        self.fb_comment_txt.insert("1.0", "Escribe comentarios...\nCada línea es un comentario diferente")
        
        ctk.CTkButton(comment_frame, text="💬 Comentar", fg_color="#1877F2", hover_color="#0d47a1",
                     font=("Segoe UI", 12, "bold"), height=40, corner_radius=8,
                     command=lambda: self.start_execution("fb_comment", "facebook")).pack(pady=(10, 15), padx=15, fill="x")

    def ui_instagram(self, parent):
        parent.grid_columnconfigure((0, 1), weight=1)
        parent.grid_rowconfigure(1, weight=1)
        
        # URL Section
        url_frame = ctk.CTkFrame(parent, corner_radius=12, fg_color="#1e3a5f", border_width=1, border_color="#1e40af")
        url_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 15))
        url_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(url_frame, text="🔗 URL del Post", font=("Segoe UI", 13, "bold"), text_color="#60a5fa").grid(row=0, column=0, padx=15, pady=(12, 5), sticky="w")
        self.ig_url = ctk.CTkEntry(url_frame, placeholder_text="https://instagram.com/p/...", 
                                   font=("Segoe UI", 11), height=35,
                                   fg_color="#230f2a", border_color="#1e40af", border_width=1,
                                   text_color="#e5e7eb", placeholder_text_color="#6b7280")
        self.ig_url.grid(row=1, column=0, padx=15, pady=(0, 12), sticky="ew")
        
        # Like Card
        like_frame = ctk.CTkFrame(parent, corner_radius=12, fg_color="#1e3a5f", border_width=1, border_color="#1e40af")
        like_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        
        ctk.CTkLabel(like_frame, text="❤️ Like", font=("Segoe UI", 13, "bold"), text_color="#60a5fa").pack(pady=(15, 10))
        ctk.CTkButton(like_frame, text="❤️ DAR LIKE", fg_color="#C13584", hover_color="#a02860",
                     font=("Segoe UI", 12, "bold"), height=50, corner_radius=8,
                     command=lambda: self.start_execution("ig_like", "instagram")).pack(pady=(20, 15), padx=20, fill="x")
        
        # Comentarios Card
        comment_frame = ctk.CTkFrame(parent, corner_radius=12, fg_color="#1e3a5f", border_width=1, border_color="#1e40af")
        comment_frame.grid(row=1, column=1, sticky="nsew", padx=10, pady=5)
        comment_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(comment_frame, text="💬 Comentarios", font=("Segoe UI", 13, "bold"), text_color="#60a5fa").pack(pady=(15, 5))
        ctk.CTkLabel(comment_frame, text="Cada línea = 1 comentario", font=("Segoe UI", 9), text_color="#9ca3af").pack(pady=(0, 10))
        
        self.ig_comment_txt = ctk.CTkTextbox(comment_frame, width=250, height=150, 
                                            font=("Segoe UI", 11), corner_radius=8,
                                            fg_color="#0f172a", border_width=1, border_color="#1e40af",
                                            text_color="#e5e7eb")
        self.ig_comment_txt.pack(pady=5, padx=15, fill="both", expand=True)
        self.ig_comment_txt.insert("1.0", "Escribe comentarios...\nCada línea es un comentario diferente")
        
        ctk.CTkButton(comment_frame, text="💬 COMENTAR", fg_color="#C13584", hover_color="#a02860",
                     font=("Segoe UI", 12, "bold"), height=40, corner_radius=8,
                     command=lambda: self.start_execution("ig_comment", "instagram")).pack(pady=(10, 15), padx=15, fill="x")

    def ui_tiktok(self, parent):
        parent.grid_columnconfigure((0, 1), weight=1)
        parent.grid_rowconfigure(1, weight=1)
        
        # URL Section
        url_frame = ctk.CTkFrame(parent, corner_radius=12, fg_color="#1e3a5f", border_width=1, border_color="#1e40af")
        url_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 15))
        url_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(url_frame, text="🔗 URL del Video", font=("Segoe UI", 13, "bold"), text_color="#60a5fa").grid(row=0, column=0, padx=15, pady=(12, 5), sticky="w")
        self.tt_url = ctk.CTkEntry(url_frame, placeholder_text="https://tiktok.com/@user/video/...", 
                                   font=("Segoe UI", 11), height=35,
                                   fg_color="#0f172a", border_color="#1e40af", border_width=1,
                                   text_color="#e5e7eb", placeholder_text_color="#6b7280")
        self.tt_url.grid(row=1, column=0, padx=15, pady=(0, 12), sticky="ew")
        
        # Like Card
        like_frame = ctk.CTkFrame(parent, corner_radius=12, fg_color="#1e3a5f", border_width=1, border_color="#1e40af")
        like_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        
        ctk.CTkLabel(like_frame, text="❤️ Heart", font=("Segoe UI", 13, "bold"), text_color="#60a5fa").pack(pady=(15, 10))
        ctk.CTkButton(like_frame, text="❤️ DAR HEART", fg_color="#FE2C55", hover_color="#d41f4a",
                     font=("Segoe UI", 12, "bold"), height=50, corner_radius=8,
                     command=lambda: self.start_execution("tt_like", "tiktok")).pack(pady=(20, 15), padx=20, fill="x")

        # Comentarios Card
        comment_frame = ctk.CTkFrame(parent, corner_radius=12, fg_color="#1e3a5f", border_width=1, border_color="#1e40af")
        comment_frame.grid(row=1, column=1, sticky="nsew", padx=10, pady=5)
        comment_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(comment_frame, text="💬 Comentarios", font=("Segoe UI", 13, "bold"), text_color="#60a5fa").pack(pady=(15, 5))
        ctk.CTkLabel(comment_frame, text="Cada línea = 1 comentario", font=("Segoe UI", 9), text_color="#9ca3af").pack(pady=(0, 10))
        
        self.tt_comment_txt = ctk.CTkTextbox(comment_frame, width=250, height=150, 
                                            font=("Segoe UI", 11), corner_radius=8,
                                            fg_color="#0f172a", border_width=1, border_color="#1e40af",
                                            text_color="#e5e7eb")
        self.tt_comment_txt.pack(pady=5, padx=15, fill="both", expand=True)
        self.tt_comment_txt.insert("1.0", "Escribe comentarios...\nCada línea es un comentario diferente")
        
        ctk.CTkButton(comment_frame, text="💬 COMENTAR", fg_color="#FE2C55", hover_color="#d41f4a",
                     font=("Segoe UI", 12, "bold"), height=40, corner_radius=8,
                     command=lambda: self.start_execution("tt_comment", "tiktok")).pack(pady=(10, 15), padx=15, fill="x")

    def ui_youtube(self, parent):
        parent.grid_columnconfigure((0, 1), weight=1)
        parent.grid_rowconfigure(1, weight=1)
        
        # URL Section
        url_frame = ctk.CTkFrame(parent, corner_radius=12, fg_color="#1e3a5f", border_width=1, border_color="#1e40af")
        url_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 15))
        url_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(url_frame, text="🔗 URL del Video", font=("Segoe UI", 13, "bold"), text_color="#60a5fa").grid(row=0, column=0, padx=15, pady=(12, 5), sticky="w")
        self.yt_url = ctk.CTkEntry(url_frame, placeholder_text="https://youtube.com/watch?v=...", 
                                   font=("Segoe UI", 11), height=35,
                                   fg_color="#0f172a", border_color="#1e40af", border_width=1,
                                   text_color="#e5e7eb", placeholder_text_color="#6b7280")
        self.yt_url.grid(row=1, column=0, padx=15, pady=(0, 12), sticky="ew")
        
        # Like Card
        like_frame = ctk.CTkFrame(parent, corner_radius=12, fg_color="#1e3a5f", border_width=1, border_color="#1e40af")
        like_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        
        ctk.CTkLabel(like_frame, text="👍 Like", font=("Segoe UI", 13, "bold"), text_color="#60a5fa").pack(pady=(15, 10))
        ctk.CTkButton(like_frame, text="👍 DAR LIKE", fg_color="#FF0000", hover_color="#cc0000",
                     font=("Segoe UI", 12, "bold"), height=50, corner_radius=8,
                     command=lambda: self.start_execution("yt_like", "youtube")).pack(pady=(20, 15), padx=20, fill="x")

        # Comentarios Card
        comment_frame = ctk.CTkFrame(parent, corner_radius=12, fg_color="#1e3a5f", border_width=1, border_color="#1e40af")
        comment_frame.grid(row=1, column=1, sticky="nsew", padx=10, pady=5)
        comment_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(comment_frame, text="💬 Comentarios", font=("Segoe UI", 13, "bold"), text_color="#60a5fa").pack(pady=(15, 5))
        ctk.CTkLabel(comment_frame, text="Cada línea = 1 comentario", font=("Segoe UI", 9), text_color="#9ca3af").pack(pady=(0, 10))
        
        self.yt_comment_txt = ctk.CTkTextbox(comment_frame, width=250, height=150, 
                                            font=("Segoe UI", 11), corner_radius=8,
                                            fg_color="#0f172a", border_width=1, border_color="#1e40af",
                                            text_color="#e5e7eb")
        self.yt_comment_txt.pack(pady=5, padx=15, fill="both", expand=True)
        self.yt_comment_txt.insert("1.0", "Escribe comentarios...\nCada línea es un comentario diferente")
        
        ctk.CTkButton(comment_frame, text="💬 COMENTAR", fg_color="#FF0000", hover_color="#cc0000",
                     font=("Segoe UI", 12, "bold"), height=40, corner_radius=8,
                     command=lambda: self.start_execution("yt_comment", "youtube")).pack(pady=(10, 15), padx=15, fill="x")

    def ui_twitter(self, parent):
        parent.grid_columnconfigure((0, 1), weight=1)
        parent.grid_rowconfigure(1, weight=1)
        
        # URL Section
        url_frame = ctk.CTkFrame(parent, corner_radius=12, fg_color="#1e3a5f", border_width=1, border_color="#1e40af")
        url_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 15))
        url_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(url_frame, text="🔗 URL del Tweet", font=("Segoe UI", 13, "bold"), text_color="#60a5fa").grid(row=0, column=0, padx=15, pady=(12, 5), sticky="w")
        self.x_url = ctk.CTkEntry(url_frame, placeholder_text="https://x.com/user/status/...", 
                                  font=("Segoe UI", 11), height=35,
                                  fg_color="#0f172a", border_color="#1e40af", border_width=1,
                                  text_color="#e5e7eb", placeholder_text_color="#6b7280")
        self.x_url.grid(row=1, column=0, padx=15, pady=(0, 12), sticky="ew")
        
        # Like Card
        like_frame = ctk.CTkFrame(parent, corner_radius=12, fg_color="#1e3a5f", border_width=1, border_color="#1e40af")
        like_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        
        ctk.CTkLabel(like_frame, text="❤️ Like", font=("Segoe UI", 13, "bold"), text_color="#60a5fa").pack(pady=(15, 10))
        ctk.CTkButton(like_frame, text="❤️ DAR LIKE", fg_color="#1DA1F2", hover_color="#1080c5",
                     font=("Segoe UI", 12, "bold"), height=50, corner_radius=8,
                     command=lambda: self.start_execution("x_like", "twitter")).pack(pady=(20, 15), padx=20, fill="x")

        # Respuestas Card
        reply_frame = ctk.CTkFrame(parent, corner_radius=12, fg_color="#1e3a5f", border_width=1, border_color="#1e40af")
        reply_frame.grid(row=1, column=1, sticky="nsew", padx=10, pady=5)
        reply_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(reply_frame, text="💬 Respuestas", font=("Segoe UI", 13, "bold"), text_color="#60a5fa").pack(pady=(15, 5))
        ctk.CTkLabel(reply_frame, text="Cada línea = 1 respuesta", font=("Segoe UI", 9), text_color="#9ca3af").pack(pady=(0, 10))
        
        self.x_reply_txt = ctk.CTkTextbox(reply_frame, width=250, height=150, 
                                         font=("Segoe UI", 11), corner_radius=8,
                                         fg_color="#0f172a", border_width=1, border_color="#1e40af",
                                         text_color="#e5e7eb")
        self.x_reply_txt.pack(pady=5, padx=15, fill="both", expand=True)
        self.x_reply_txt.insert("1.0", "Escribe respuestas...\nCada línea es una respuesta diferente")
        
        ctk.CTkButton(reply_frame, text="✍️ RESPONDER", fg_color="#1DA1F2", hover_color="#1080c5",
                     font=("Segoe UI", 12, "bold"), height=40, corner_radius=8,
                     command=lambda: self.start_execution("x_reply", "twitter")).pack(pady=(10, 15), padx=15, fill="x")

    # =========================================================================
    #                       UI CALENTAMIENTO
    # =========================================================================
# =========================================================================
    #                        CALENTAMIENTO (WARMUP) MEJORADO
    # =========================================================================
# =========================================================================
    #                        CALENTAMIENTO (WARMUP) MEJORADO
    # =========================================================================



    # =========================================================================
    #                       MOTOR DE EJECUCIÓN
    # =========================================================================
# =========================================================================
    #                       UI CALENTAMIENTO (FALTABA ESTA SECCIÓN)
    # =========================================================================
    def setup_warmup_ui(self):
        f = self.tab_warmup
        f.grid_columnconfigure(0, weight=1)
        
        # Header
        header_frame = ctk.CTkFrame(f, corner_radius=12, fg_color="#1e3a5f", border_width=1, border_color="#1e40af")
        header_frame.pack(fill="x", padx=20, pady=(20, 15))
        header_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(header_frame, text="🏋️ RUTINA DE CALENTAMIENTO", font=("Segoe UI", 18, "bold"), text_color="#60a5fa").pack(pady=(15, 5))
        ctk.CTkLabel(header_frame, text="Navegación automática para generar historial y confianza", 
                    font=("Segoe UI", 10), text_color="#9ca3af").pack(pady=(0, 15))
        
        # Configuración Card
        config_card = ctk.CTkFrame(f, corner_radius=12, fg_color="#1e3a5f", border_width=1, border_color="#1e40af")
        config_card.pack(fill="x", padx=20, pady=10)
        config_card.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(config_card, text="📱 Plataforma", font=("Segoe UI", 12, "bold"), text_color="#60a5fa").pack(pady=(15, 8))
        self.combo_warmup_plat = ctk.CTkComboBox(config_card, values=list(self.plataformas.keys()),
                                                 font=("Segoe UI", 11), width=300, height=35,
                                                 fg_color="#0f172a", border_color="#1e40af", border_width=1,
                                                 button_color="#1e40af", button_hover_color="#0284c7",
                                                 text_color="#e5e7eb",
                                                 command=self.on_warmup_platform_change)
        self.combo_warmup_plat.pack(pady=(0, 15))
        self.combo_warmup_plat.set("Facebook")

        # Selector de cuenta que realizará el calentamiento
        ctk.CTkLabel(config_card, text="👤 Cuenta para Calentamiento", font=("Segoe UI", 12, "bold"), text_color="#60a5fa").pack(pady=(6, 6))
        initial_accounts = obtener_cuentas_por_plataforma("facebook")
        self.combo_warmup_account = ctk.CTkComboBox(config_card, values=initial_accounts,
                                                   font=("Segoe UI", 11), width=300, height=35,
                                                   fg_color="#0f172a", border_color="#1e40af", border_width=1,
                                                   button_color="#1e40af", button_hover_color="#0284c7",
                                                   text_color="#e5e7eb")
        self.combo_warmup_account.pack(pady=(0, 10))
        if initial_accounts and initial_accounts[0] != "Sin cuentas":
            self.combo_warmup_account.set(initial_accounts[0])
        else:
            self.combo_warmup_account.set("Sin cuentas")

        ctk.CTkLabel(config_card, text="⏱️ Duración por cuenta", font=("Segoe UI", 12, "bold"), text_color="#60a5fa").pack(pady=(10, 8))
        
        slider_container = ctk.CTkFrame(config_card, fg_color="transparent")
        slider_container.pack(fill="x", padx=50, pady=5)
        slider_container.grid_columnconfigure(0, weight=1)
        
        self.slider_warmup = ctk.CTkSlider(slider_container, from_=1, to=20, number_of_steps=19,
                                          fg_color="#1e40af", progress_color="#0284c7",
                                          button_color="#60a5fa", button_hover_color="#0284c7",
                                          command=lambda v: self.lbl_warmup_val.configure(text=f"{int(v)} min"))
        self.slider_warmup.grid(row=0, column=0, sticky="ew")
        self.slider_warmup.set(5)
        
        self.lbl_warmup_val = ctk.CTkLabel(slider_container, text="5 min", font=("Segoe UI", 12, "bold"),
                                          width=60, fg_color="#1e40af", corner_radius=5, text_color="#60a5fa")
        self.lbl_warmup_val.grid(row=0, column=1, padx=(10, 0))

        ctk.CTkButton(config_card, text="▶️ INICIAR CALENTAMIENTO", fg_color="#0284c7", hover_color="#1e40af", 
                     height=50, font=("Segoe UI", 14, "bold"), corner_radius=8,
                     command=self.trigger_warmup).pack(pady=(20, 15), padx=50, fill="x")
        
        # Opciones avanzadas de Warmup
        options_frame = ctk.CTkFrame(config_card, fg_color="transparent")
        options_frame.pack(fill="x", padx=30, pady=(10, 12))

        self.var_warmup_friendreq = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(options_frame, text="➕ Enviar solicitudes de amistad (solo primeras 20 del feed)",
                   variable=self.var_warmup_friendreq, font=("Segoe UI", 10)).pack(anchor="w")

        self.var_warmup_likes = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(options_frame, text="👍 Me gustas ocasionales en publicaciones",
                   variable=self.var_warmup_likes, font=("Segoe UI", 10)).pack(anchor="w")

        # Controles separados para búsqueda y envío de solicitudes
        ctk.CTkLabel(options_frame, text="🔎 Búsqueda amigos (proceso separado)", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(8,4))
        limit_frame = ctk.CTkFrame(options_frame, fg_color="transparent")
        limit_frame.pack(fill="x", pady=(4,8))
        ctk.CTkLabel(limit_frame, text="Máx. solicitudes:", font=("Segoe UI", 10)).pack(side="left", padx=(0,8))
        self.slider_friend_limit = ctk.CTkSlider(limit_frame, from_=1, to=50, number_of_steps=49,
                            command=lambda v: self.lbl_friend_limit.configure(text=str(int(float(v)))))
        self.slider_friend_limit.set(20)
        self.slider_friend_limit.pack(side="left", fill="x", expand=True)
        self.lbl_friend_limit = ctk.CTkLabel(limit_frame, text="20", width=40)
        self.lbl_friend_limit.pack(side="left", padx=(8,0))
        ctk.CTkButton(options_frame, text="🔎 Buscar y Enviar Solicitudes (Feed)", fg_color="#FF8C00",
                 hover_color="#FF7A00", height=40, command=self.trigger_friendfinder).pack(pady=(6,8), padx=10, fill="x")
        
        # Nueva sección: Búsqueda personalizada por nombre/usuario
        ctk.CTkLabel(options_frame, text="🔍 Búsqueda Personalizada", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(12,4))
        search_frame = ctk.CTkFrame(options_frame, fg_color="transparent")
        search_frame.pack(fill="x", pady=(4,8))
        ctk.CTkLabel(search_frame, text="Nombre/Usuario:", font=("Segoe UI", 10)).pack(side="left", padx=(0,8))
        self.search_person_entry = ctk.CTkEntry(search_frame, placeholder_text="Buscar persona...", width=250, height=30)
        self.search_person_entry.pack(side="left", fill="x", expand=True, padx=(0,8))
        ctk.CTkLabel(search_frame, text="Solicitudes:", font=("Segoe UI", 10)).pack(side="left", padx=(0,8))
        self.slider_person_limit = ctk.CTkSlider(search_frame, from_=1, to=30, number_of_steps=29,
                            command=lambda v: self.lbl_person_limit.configure(text=str(int(float(v)))))
        self.slider_person_limit.set(5)
        self.slider_person_limit.pack(side="left", fill="x", expand=True, padx=(0,8))
        self.lbl_person_limit = ctk.CTkLabel(search_frame, text="5", width=30)
        self.lbl_person_limit.pack(side="left")
        
        ctk.CTkButton(options_frame, text="✅ Buscar y Enviar Solicitudes a Personas", fg_color="#e74c3c",
                 hover_color="#c0392b", height=40, command=self.trigger_search_and_add).pack(pady=(6,8), padx=10, fill="x")

    def trigger_warmup(self):
            plat_ui = self.combo_warmup_plat.get()
            plat_key = self.plataformas.get(plat_ui, "facebook")
            
            # Obtener explícitamente el alias seleccionado
            selected_alias = self.combo_warmup_account.get()

            if not selected_alias or selected_alias == "Sin cuentas":
                self.log("⚠️ Selecciona una cuenta válida en la lista de Calentamiento.", "WARN")
                return

            # Generar los argumentos, incluyendo el límite del slider
            kwargs_gen = lambda alias: {
                "alias": alias, 
                "minutes": int(self.slider_warmup.get()),
                # Aquí pasamos los valores de la UI a la lógica del bot
                "friend_requests": self.var_warmup_friendreq.get(), 
                "friend_request_limit": int(self.slider_friend_limit.get()), # <--- IMPORTANTE: El valor del slider
                "random_likes": self.var_warmup_likes.get(),
                "headless": self.var_headless.get(),
                "logger": self.log,
                "update_preview_cb": self.update_preview,
                "use_mobile": self.var_mobile_mode.get(),
                "use_ai": self.var_use_ai.get(),
                "ai_model": self.ai_model_selector.get() if hasattr(self, 'ai_model_selector') else "llama3",
                "use_vision": self.var_use_vision.get() if hasattr(self, 'var_use_vision') else False
            }

            # Ejecutar
            threading.Thread(target=lambda: self.run_single(
                SocialActions.warmup, 
                plat_key, 
                kwargs_gen, 
                target_alias=selected_alias
            )).start()




    def on_warmup_platform_change(self, value):
        """Actualiza la lista de cuentas disponibles cuando cambia la plataforma en el UI de Warmup."""
        try:
            plat_key = self.plataformas.get(value, "facebook")
            cuentas = obtener_cuentas_por_plataforma(plat_key)
            self.combo_warmup_account.configure(values=cuentas)
            if cuentas and cuentas[0] != "Sin cuentas":
                self.combo_warmup_account.set(cuentas[0])
            else:
                self.combo_warmup_account.set("Sin cuentas")
        except Exception:
            pass

    def trigger_friendfinder(self):
        plat_ui = self.combo_warmup_plat.get()
        plat_key = self.plataformas.get(plat_ui, "facebook")
        
        selected_alias = self.combo_warmup_account.get()
        if not selected_alias or selected_alias == "Sin cuentas":
            self.log("⚠️ Selecciona una cuenta válida para buscar amigos.", "WARN")
            return

        target_func = SocialActions.find_and_add_friends
        def kwargs_gen(alias):
            return {"alias": alias, "limit": int(self.slider_friend_limit.get()), **{
                "headless": self.var_headless.get(),
                "logger": self.log,
                "update_preview_cb": self.update_preview,
                "use_mobile": self.var_mobile_mode.get(),
                "use_ai": self.var_use_ai.get(),
                "control_tower": False,
            }}
        
        # Usamos run_single con target_alias forzado
        threading.Thread(target=lambda: self.run_single(target_func, plat_key, kwargs_gen, target_alias=selected_alias)).start()

    def trigger_search_and_add(self):
        search_term = self.search_person_entry.get().strip()
        if not search_term:
            self.log("⚠️ Por favor ingresa un nombre o usuario a buscar.", "WARN")
            return
        
        plat_ui = self.combo_warmup_plat.get()
        plat_key = self.plataformas.get(plat_ui, "facebook")
        selected_alias = self.combo_warmup_account.get()

        if not selected_alias or selected_alias == "Sin cuentas":
            self.log("⚠️ No se ha seleccionado una cuenta válida.", "WARN")
            return

        target_func = SocialActions.search_and_add_friends
        def kwargs_gen(alias):
            return {
                "alias": alias, 
                "search_term": search_term,
                "limit": int(self.slider_person_limit.get()), 
                "headless": self.var_headless.get(),
                "logger": self.log,
                "update_preview_cb": self.update_preview,
                "use_mobile": self.var_mobile_mode.get(),
                "use_ai": self.var_use_ai.get(),
                "control_tower": False,
                "platform": plat_key,
            }

        threading.Thread(target=lambda: self.run_single(target_func, plat_key, kwargs_gen, target_alias=selected_alias)).start()   
   

    def start_execution(self, action_type, platform):
        if hasattr(self, 'is_running') and self.is_running:
            self.log("⚠️ El sistema está ocupado. Espera...", "WARN")
            return

        params = {}
        # ... (Mantén el bloque de params igual que antes) ...
        if action_type != "warmup":
            if platform == "facebook":
                params['url'] = self.fb_url.get()
                params['reaction'] = self.fb_react_combo.get()
                comment_lines = [line.strip() for line in self.fb_comment_txt.get("1.0", "end-1c").split('\n') if line.strip()]
                params['comments'] = comment_lines if comment_lines else [""]
            elif platform == "instagram":
                params['url'] = self.ig_url.get()
                comment_lines = [line.strip() for line in self.ig_comment_txt.get("1.0", "end-1c").split('\n') if line.strip()]
                params['comments'] = comment_lines if comment_lines else [""]
            elif platform == "tiktok":
                params['url'] = self.tt_url.get()
                comment_lines = [line.strip() for line in self.tt_comment_txt.get("1.0", "end-1c").split('\n') if line.strip()]
                params['comments'] = comment_lines if comment_lines else [""]
            elif platform == "youtube":
                params['url'] = self.yt_url.get()
                comment_lines = [line.strip() for line in self.yt_comment_txt.get("1.0", "end-1c").split('\n') if line.strip()]
                params['comments'] = comment_lines if comment_lines else [""]
            elif platform == "twitter":
                params['url'] = self.x_url.get()
                comment_lines = [line.strip() for line in self.x_reply_txt.get("1.0", "end-1c").split('\n') if line.strip()]
                params['comments'] = comment_lines if comment_lines else [""]
        else:
            params['minutes'] = int(self.slider_warmup.get())

        target_func = None
        kwargs_gen = None
        
        # --- AQUÍ ESTÁ LA CORRECCIÓN ---
        common_args = {
            "headless": self.var_headless.get(),
            "logger": self.log,
            "update_preview_cb": self.update_preview,
            "use_mobile": self.var_mobile_mode.get(),
            "use_ai": self.var_use_ai.get(),
            # Usamos 'hasattr' para evitar el crash si el selector no existe en la UI
            "ai_model": self.ai_model_selector.get() if hasattr(self, 'ai_model_selector') else "llama3",
            "use_vision": self.var_use_vision.get() if hasattr(self, 'var_use_vision') else False,
            "control_tower": False
        }
        # -------------------------------

        # Mapeo de Acciones (El resto del código sigue igual)
        if action_type == "warmup":
            target_func = SocialActions.warmup
            kwargs_gen = lambda alias: {"alias": alias, "minutes": params['minutes'],
                                        "friend_requests": self.var_warmup_friendreq.get(),
                                        "friend_request_limit": 20,
                                        "random_likes": self.var_warmup_likes.get(),
                                        **common_args}
        elif action_type == "fb_react":
            target_func = SocialActions.fb_reaction
            kwargs_gen = lambda alias: {"alias": alias, "url": params['url'], "reaction": params['reaction'], **common_args}
        elif action_type == "fb_comment":
            target_func = SocialActions.fb_comment
            kwargs_gen = lambda alias: {"alias": alias, "url": params['url'], "comments": params['comments'], **common_args}
        elif action_type == "ig_like":
            target_func = SocialActions.ig_like
            kwargs_gen = lambda alias: {"alias": alias, "url": params['url'], **common_args}
        elif action_type == "ig_comment":
            target_func = SocialActions.ig_comment
            kwargs_gen = lambda alias: {"alias": alias, "url": params['url'], "comments": params['comments'], **common_args}
        elif action_type == "tt_like":
            target_func = SocialActions.tt_like
            kwargs_gen = lambda alias: {"alias": alias, "url": params['url'], **common_args}
        elif action_type == "tt_comment":
            target_func = SocialActions.tt_comment
            kwargs_gen = lambda alias: {"alias": alias, "url": params['url'], "comments": params['comments'], **common_args}
        elif action_type == "yt_like":
            target_func = SocialActions.yt_like
            kwargs_gen = lambda alias: {"alias": alias, "url": params['url'], **common_args}
        elif action_type == "yt_comment":
            target_func = SocialActions.yt_comment
            kwargs_gen = lambda alias: {"alias": alias, "url": params['url'], "comments": params['comments'], **common_args}
        elif action_type == "x_like":
            target_func = SocialActions.x_like
            kwargs_gen = lambda alias: {"alias": alias, "url": params['url'], **common_args}
        elif action_type == "x_reply":
            target_func = SocialActions.x_reply
            kwargs_gen = lambda alias: {"alias": alias, "url": params['url'], "comments": params['comments'], **common_args}

        if self.var_batch.get():
            threading.Thread(target=lambda: self.run_batch(target_func, platform, kwargs_gen)).start()
        else:
            threading.Thread(target=lambda: self.run_single(target_func, platform, kwargs_gen)).start()

    def run_single(self, func, platform, kwargs_gen, target_alias=None):
        """
        Ejecuta una tarea única.
        Args:
            target_alias: Si se provee, usa este alias ignorando los selectores de la pestaña.
        """
        self.is_running = True
        
        # 1. Determinar el alias a usar
        if target_alias:
            alias = target_alias
        else:
            # Si no hay alias forzado, buscar en el selector de la pestaña correspondiente
            if platform in self.account_selectors:
                alias = self.account_selectors[platform].get()
            else:
                alias = None
        
        if not alias or alias == "Sin cuentas":
            self.log(f"❌ Error: Selecciona una cuenta válida para {platform}.", "ERROR")
            self.is_running = False
            return

        # Asegurar que la cuenta existe en la DB
        try:
            from login_manager import obtener_datos_cuenta
            data = obtener_datos_cuenta(alias)
            if not data:
                self.log(f"❌ Error: La cuenta '{alias}' no existe en la base de datos.", "ERROR")
                self.is_running = False
                return
        except Exception:
            self.log(f"❌ Error comprobando cuenta en DB: {alias}", "ERROR")
            self.is_running = False
            return
        
        # Gestión de dispositivo móvil si está activo
        mobile_device = None
        if self.var_mobile_mode.get():
            mobile_device = self.mobile_manager.acquire_device_with_proxy(timeout=30.0)
            if mobile_device:
                proxy = self.mobile_manager.renew_ip_and_get_proxy(mobile_device["device_id"])
                if proxy:
                    
                    # 👇 --- INICIO DE CÓDIGO NUEVO PARA COMPROBAR IP --- 👇
                    import requests
                    try:
                        self.log(f"🔍 Probando conexión al proxy {proxy}...", "INFO")
                        proxies = {"http": f"http://{proxy}", "https": f"http://{proxy}"}
                        # Consultamos la IP pasando por el celular
                        ip_real = requests.get("https://api.ipify.org", proxies=proxies, timeout=10).text
                        self.log(f"🌍 ÉXITO: Navegando camuflado con IP: {ip_real}", "SUCCESS")
                    except Exception as e:
                        self.log(f"⚠️ El proxy no responde o está mal configurado. Ignorando proxy. Error: {e}", "WARN")
                    # 👆 --- FIN DE CÓDIGO NUEVO --- 👆

                    # Modificamos el kwargs_gen para inyectar el proxy móvil
                    original_kwargs_gen = kwargs_gen
                    kwargs_gen = lambda a: {**original_kwargs_gen(a), "mobile_proxy": f"http://{proxy}"}
                else:
                    self.log("⚠️ Error renovando IP, continuando sin proxy móvil", "WARN")
                    self.mobile_manager.release_device(mobile_device["device_id"])
                    mobile_device = None
            else:
                self.log("⚠️ No se pudo adquirir dispositivo móvil, usando red de PC", "WARN")
        
        try:
            self.log(f"🚀 Iniciando tarea: {alias} ({platform})", "INFO")
            func(**kwargs_gen(alias))
        except Exception as e:
            self.log(f"Error Crítico en ejecución: {e}", "ERROR")
        finally:
            if mobile_device:
                self.mobile_manager.release_device(mobile_device["device_id"])
        
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
        use_mobile = self.var_mobile_mode.get()
        
        if use_mobile:
            self.log(f"🔥 INICIANDO MODO MASIVO (MÓVIL): {total} cuentas | {workers} hilos", "BATCH")
        else:
            self.log(f"🔥 INICIANDO MODO MASIVO: {total} cuentas | {workers} hilos", "BATCH")
        
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = []
            for i, alias in enumerate(cuentas):
                delay = random.uniform(5, 15) + (i * 2)
                self.log(f"⏳ {alias} en cola (Espera: {delay:.1f}s)", "INFO")
                futures.append(executor.submit(self._batch_wrapper, func, kwargs_gen, alias, delay, use_mobile))
            
            for f in futures:
                try: f.result()
                except Exception: pass
        
        self.log("✅ PROCESO MASIVO FINALIZADO", "SUCCESS")
        self.is_running = False

    def _batch_wrapper(self, func, kwargs_gen, alias, delay, use_mobile=False):
        time.sleep(delay)
        
        # Gestión de dispositivo móvil si está activo
        mobile_device = None
        if use_mobile:
            mobile_device = self.mobile_manager.acquire_device_with_proxy(timeout=60.0)
            if mobile_device:
                # Renovar IP del dispositivo
                proxy = self.mobile_manager.renew_ip_and_get_proxy(mobile_device["device_id"])
                if proxy:
                    mobile_device["proxy"] = proxy
                    # Modificar kwargs_gen para incluir proxy móvil
                    original_kwargs = kwargs_gen(alias)
                    original_kwargs["mobile_proxy"] = f"http://{proxy}"
                    kwargs_gen = lambda a: original_kwargs
                else:
                    self.log(f"⚠️ Error renovando IP para {alias}, continuando sin proxy móvil", "WARN")
                    self.mobile_manager.release_device(mobile_device["device_id"])
                    mobile_device = None
        
        try:
            func(**kwargs_gen(alias))
        except Exception as e:
            self.log(f"Fallo en {alias}: {e}", "ERROR")
        finally:
            # Liberar dispositivo móvil si se usó
            if mobile_device:
                self.mobile_manager.release_device(mobile_device["device_id"])

    def toggle_ethernet_adapter(self):
        """
        Ejecuta comandos netsh para activar/desactivar Ethernet.
        Requiere ejecutar el script como ADMINISTRADOR.
        """
        estado_deseado = self.var_ethernet_status.get()
        interface_name = "Ethernet" # Asegúrate que este sea el nombre exacto en tu Windows
        
        # Si el switch está ON (True) -> Enable. Si está OFF (False) -> Disable (Tu .bat)
        accion = "enable" if estado_deseado else "disable"
        
        cmd = f'netsh interface set interface "{interface_name}" admin={accion}'
        
        try:
            # Ejecutamos el comando ocultando la ventana de consola negra
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            process = subprocess.run(cmd, shell=True, capture_output=True, text=True, startupinfo=startupinfo)
            
            if process.returncode == 0:
                if estado_deseado:
                    self.log("🔌 Ethernet HABILITADO. Usando red cableada.", "SUCCESS")
                    self.switch_ethernet.configure(text="Ethernet Activo")
                else:
                    self.log("🚫 Ethernet DESHABILITADO. Usando Wi-Fi.", "WARN")
                    self.switch_ethernet.configure(text="Ethernet Apagado")
            else:
                # Si falla (probablemente por permisos)
                err_msg = process.stderr.strip()
                self.log(f"❌ Error cambiando red: {err_msg}", "ERROR")
                self.log("⚠️ ¿Ejecutaste el programa como Administrador?", "WARN")
                
                # Revertir el switch visualmente porque falló
                self.var_ethernet_status.set(not estado_deseado)
                
        except Exception as e:
            self.log(f"❌ Error crítico en red: {e}", "ERROR")
            self.var_ethernet_status.set(not estado_deseado)

    # =========================================================================
    #                       UTILIDADES DE INTERFAZ
    # =========================================================================
    def setup_console(self):
        self.log_frame = ctk.CTkFrame(self, height=180, corner_radius=12, fg_color="#1e3a5f")
        self.log_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=15, pady=(0, 15))
        self.log_frame.grid_propagate(False)
        self.log_frame.grid_columnconfigure(0, weight=1)
        
        # Header de consola con acento premium
        console_header = ctk.CTkFrame(self.log_frame, fg_color="transparent")
        console_header.pack(fill="x", padx=15, pady=(12, 8))
        ctk.CTkLabel(console_header, text="📋 Consola de Actividad", 
                     font=("Segoe UI", 12, "bold"), text_color="#60a5fa").pack(side="left")
        
        # Textbox con fondo oscuro y acento azul
        self.console = ctk.CTkTextbox(self.log_frame, height=140, font=("Consolas", 10), 
                                      corner_radius=8, fg_color="#0f172a",
                                      text_color="#e5e7eb", border_width=1, border_color="#1e40af")
        self.console.pack(fill="both", expand=True, padx=15, pady=(0, 12))
        self.console.configure(state="disabled")

    def log(self, msg, type="INFO"):
        ts = time.strftime("%H:%M:%S")
        text = f"[{ts}] [{type}] {msg}\n"
        
        # Colores según tipo de mensaje
        color_map = {
            "INFO": "#60a5fa",      # Azul claro
            "SUCCESS": "#10b981",   # Verde
            "ERROR": "#ef4444",     # Rojo
            "WARN": "#f97316",      # Naranja
            "DEBUG": "#8b5cf6"      # Púrpura
        }
        
        color = color_map.get(type, "#e5e7eb")
        
        def _update():
            self.console.configure(state="normal")
            # Insertar timestamp en gris
            self.console.insert("end", f"[{ts}] ", ())
            # Insertar tipo con color
            self.console.insert("end", f"[{type}] ", ())
            # Insertar mensaje en color correspondiente
            self.console.insert("end", f"{msg}\n", ())
            
            # Aplicar tags de color (CustomTkinter textbox tiene limitaciones, por lo que usamos texto simple)
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
                except Exception as e:
                    print(f"⚠️ Error al cargar la vista previa: {e}")
        self.after(0, _refresh)

    # --- UI ESTADO DE CUENTAS ---
    def setup_status_ui(self):
        """Muestra el estado de todas las cuentas (con/sin cookies)"""
        tab = self.tab_status
        tab.grid_columnconfigure(0, weight=1)
        
        # Header
        header_frame = ctk.CTkFrame(tab, corner_radius=12, fg_color="#1e3a5f", border_width=1, border_color="#1e40af")
        header_frame.pack(fill="x", padx=20, pady=(20, 15))
        header_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(header_frame, text="📊 ESTADO DE CUENTAS", font=("Segoe UI", 18, "bold"), text_color="#050505").pack(pady=(15, 5))
        ctk.CTkLabel(header_frame, text="Visualiza qué cuentas tienen cookies cargadas", 
                    font=("Segoe UI", 10), text_color="#9ca3af").pack(pady=(0, 15))
        
        # Frame de filtros
        filter_frame = ctk.CTkFrame(tab, corner_radius=12, fg_color="#1e3a5f", border_width=1, border_color="#1e40af")
        filter_frame.pack(fill="x", padx=20, pady=(0, 15))
        filter_frame.grid_columnconfigure(1, weight=1)
        
        # Filtro por nombre
        ctk.CTkLabel(filter_frame, text="🔍 Filtrar:", font=("Segoe UI", 10, "bold"), text_color="#60a5fa").grid(row=0, column=0, padx=(15, 10), pady=12)
        self.filter_nombre = ctk.CTkEntry(filter_frame, placeholder_text="Por nombre...", height=35,
                                          fg_color="#0f172a", border_color="#1e40af", border_width=1,
                                          text_color="#e5e7eb")
        self.filter_nombre.grid(row=0, column=1, padx=(0, 10), pady=12, sticky="ew")
        self.filter_nombre.bind("<KeyRelease>", lambda e: self.refresh_status_ui())
        
        # Filtro por red social
        ctk.CTkLabel(filter_frame, text="Plataforma:", font=("Segoe UI", 10, "bold"), text_color="#60a5fa").grid(row=0, column=2, padx=(0, 10), pady=12)
        self.filter_platform = ctk.CTkComboBox(filter_frame, values=["Todas", "facebook", "instagram", "tiktok", "youtube", "twitter"], 
                                               height=35, fg_color="#0f172a", border_color="#1e40af", border_width=1,
                                               button_color="#1e40af", button_hover_color="#0284c7", text_color="#e5e7eb",
                                               command=self.refresh_status_ui)
        self.filter_platform.grid(row=0, column=3, padx=(0, 10), pady=12, sticky="ew")
        self.filter_platform.set("Todas")
        
        # Botón para limpiar filtros
        ctk.CTkButton(filter_frame, text="✨ Limpiar", fg_color="#1e40af", hover_color="#0284c7",
                     corner_radius=8, height=35, font=("Segoe UI", 10, "bold"),
                     command=self.limpiar_filtros).grid(row=0, column=4, padx=(0, 15), pady=12)
        
        # Frame para tabla de cuentas
        table_frame = ctk.CTkFrame(tab, corner_radius=12, fg_color="#1e3a5f", border_width=1, border_color="#1e40af")
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)
        table_frame.grid_columnconfigure(0, weight=1)
        
        # Frame scrollable para las cuentas
        scroll_frame = ctk.CTkScrollableFrame(table_frame, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        scroll_frame.grid_columnconfigure(0, weight=1)
        
        self.status_frame = scroll_frame
        
        # Botón para refrescar
        btn_frame = ctk.CTkFrame(tab, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(0, 20))
        btn_frame.grid_columnconfigure((0, 1), weight=1)
        
        ctk.CTkButton(btn_frame, text="🔄 Refrescar Estado", fg_color="#0284c7", 
                     hover_color="#1e40af", height=40, font=("Segoe UI", 12, "bold"), corner_radius=8,
                     command=self.refresh_status_ui).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        
        ctk.CTkButton(btn_frame, text="💾 Sincronizar BD", fg_color="#10b981", 
                     hover_color="#059669", height=40, font=("Segoe UI", 12, "bold"), corner_radius=8,
                     command=self.sincronizar_bd).grid(row=0, column=1, sticky="ew")
        
        # Cargar estado inicial
        self.refresh_status_ui()

    def limpiar_filtros(self):
        """Limpia los filtros y recarga la tabla"""
        self.filter_nombre.delete(0, "end")
        self.filter_platform.set("Todas")
        self.refresh_status_ui()

    def sincronizar_bd(self):
        """Sincroniza la BD: limpia espacios, duplicados y recarga datos frescos"""
        import subprocess
        import threading
        import os
        
        def ejecutar_limpieza():
            try:
                self.log("🔄 Sincronizando base de datos...", "INFO")
                
                # Obtener el directorio actual
                script_path = os.path.join(os.getcwd(), "limpiar_duplicados.py")
                
                # Ejecutar script de limpieza
                result = subprocess.run([
                    "python", 
                    script_path
                ], capture_output=True, text=True, timeout=10, cwd=os.getcwd())
                
                if result.returncode == 0:
                    self.log("✅ BD sincronizada y limpiada correctamente", "SUCCESS")
                    # Refrescar UI
                    self.after(500, self.refresh_status_ui)
                else:
                    stderr_msg = result.stderr[:150] if result.stderr else "Sin detalles"
                    self.log(f"⚠️ Error en sincronización: {stderr_msg}", "WARN")
                    self.after(500, self.refresh_status_ui)
            except Exception as e:
                self.log(f"❌ Error sincronizando BD: {str(e)[:100]}", "ERROR")
                self.after(500, self.refresh_status_ui)
        
        # Ejecutar en hilo para no bloquear UI
        thread = threading.Thread(target=ejecutar_limpieza, daemon=True)
        thread.start()

    def refresh_status_ui(self):
        """Recarga y muestra el estado de todas las cuentas con filtros aplicados"""
        # Limpiar frame anterior
        for widget in self.status_frame.winfo_children():
            widget.destroy()
        
        try:
            # Obtener todas las cuentas de la BD (fuerza lectura fresca)
            import sqlite3
            conn = sqlite3.connect("cuentas.db", check_same_thread=False)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT alias, platform, username, cookies FROM cuentas ORDER BY alias")
            todas_cuentas = c.fetchall()
            conn.close()
            
            # Convertir Row objects a tuples
            todas_cuentas = [(row[0], row[1], row[2], row[3]) for row in todas_cuentas]
            
            # Aplicar filtros
            filtro_nombre = self.filter_nombre.get().lower() if hasattr(self, 'filter_nombre') else ""
            filtro_platform = self.filter_platform.get() if hasattr(self, 'filter_platform') else "Todas"
            
            # Filtrar cuentas
            cuentas_filtradas = []
            for alias, platform, username, cookies in todas_cuentas:
                # Filtro por nombre (busca en alias y username)
                if filtro_nombre and not (filtro_nombre in alias.lower() or (username and filtro_nombre in username.lower())):
                    continue
                # Filtro por plataforma
                if filtro_platform != "Todas" and (platform or "").lower() != filtro_platform.lower():
                    continue
                cuentas_filtradas.append((alias, platform, username, cookies))
            
            if not cuentas_filtradas:
                if todas_cuentas:
                    ctk.CTkLabel(self.status_frame, text="❌ No hay cuentas que coincidan con los filtros", 
                                font=("Segoe UI", 12), text_color="gray").pack(pady=20)
                else:
                    ctk.CTkLabel(self.status_frame, text="❌ No hay cuentas registradas", 
                                font=("Segoe UI", 12), text_color="gray").pack(pady=20)
                return
            
            # Crear tabla header
            header_frame = ctk.CTkFrame(self.status_frame, fg_color=("#e0e0e0", "#404040"), corner_radius=5)
            header_frame.pack(fill="x", pady=(0, 5))
            header_frame.grid_columnconfigure(1, weight=1)
            
            ctk.CTkLabel(header_frame, text="Alias", font=("Segoe UI", 11, "bold"), width=150).grid(row=0, column=0, padx=10, pady=8)
            ctk.CTkLabel(header_frame, text="Plataforma", font=("Segoe UI", 11, "bold"), width=100).grid(row=0, column=1, padx=10, pady=8)
            ctk.CTkLabel(header_frame, text="Usuario", font=("Segoe UI", 11, "bold"), width=150).grid(row=0, column=2, padx=10, pady=8)
            ctk.CTkLabel(header_frame, text="Estado", font=("Segoe UI", 11, "bold"), width=100).grid(row=0, column=3, padx=10, pady=8)
            
            # Mostrar cada cuenta
            for i, (alias, platform, username, cookies) in enumerate(cuentas_filtradas):
                row_frame = ctk.CTkFrame(self.status_frame, fg_color=("#ffffff" if i % 2 == 0 else "#f9f9f9", 
                                                                       "#1f1f1f" if i % 2 == 0 else "#2a2a2a"), 
                                        corner_radius=5)
                row_frame.pack(fill="x", pady=2)
                row_frame.grid_columnconfigure(1, weight=1)
                
                # Alias
                ctk.CTkLabel(row_frame, text=alias, font=("Segoe UI", 10), width=150).grid(row=0, column=0, padx=10, pady=8)
                
                # Plataforma
                platform_display = platform.upper() if platform else "?"
                ctk.CTkLabel(row_frame, text=platform_display, font=("Segoe UI", 10), width=100).grid(row=0, column=1, padx=10, pady=8)
                
                # Usuario
                user_display = username[:20] + "..." if username and len(username) > 20 else (username or "N/A")
                ctk.CTkLabel(row_frame, text=user_display, font=("Segoe UI", 10), width=150).grid(row=0, column=2, padx=10, pady=8)
                
                # Estado (cookies) - verificar si tiene cookies válidas
                tiene_cookies = False
                if cookies:
                    try:
                        import json
                        cookies_list = json.loads(cookies)
                        # Verificar que hay al menos una cookie
                        tiene_cookies = isinstance(cookies_list, list) and len(cookies_list) > 0
                    except:
                        tiene_cookies = False
                
                if tiene_cookies:
                    status_text = "✅ Con Cookies"
                    status_color = "#27ae60"
                else:
                    status_text = "❌ Sin Cookies"
                    status_color = "#e74c3c"
                
                ctk.CTkLabel(row_frame, text=status_text, font=("Segoe UI", 10, "bold"), 
                            text_color=status_color, width=100).grid(row=0, column=3, padx=10, pady=8)
            
            # Resumen
            summary_frame = ctk.CTkFrame(self.status_frame, fg_color=("#e8f5e9", "#1b5e20"), corner_radius=5)
            summary_frame.pack(fill="x", pady=(10, 0))
            
            # Contar cuentas con cookies en las cuentas filtradas
            con_cookies = 0
            for _, _, _, cookies in cuentas_filtradas:
                if cookies:
                    try:
                        import json
                        cookies_list = json.loads(cookies)
                        if isinstance(cookies_list, list) and len(cookies_list) > 0:
                            con_cookies += 1
                    except:
                        pass
            
            sin_cookies = len(cuentas_filtradas) - con_cookies
            
            resumen_text = f"📊 Total: {len(cuentas_filtradas)} | ✅ Con Cookies: {con_cookies} | ❌ Sin Cookies: {sin_cookies}"
            if filtro_nombre or filtro_platform != "Todas":
                resumen_text += f" | 🔍 Filtros activos"
            ctk.CTkLabel(summary_frame, text=resumen_text, font=("Segoe UI", 11, "bold")).pack(pady=8)
            
        except Exception as e:
            self.log(f"Error al refrescar estado: {e}", "ERROR")
            ctk.CTkLabel(self.status_frame, text=f"Error: {str(e)[:80]}", 
                        font=("Segoe UI", 10), text_color="red").pack(pady=20)

    # --- UI GESTIÓN DE CUENTAS ---
    def setup_accounts_ui(self):
        tab = self.tab_accounts
        tab.grid_columnconfigure(0, weight=1)
        
        # Header
        header_frame = ctk.CTkFrame(tab, corner_radius=12, fg_color="#1e3a5f", border_width=1, border_color="#1e40af")
        header_frame.pack(fill="x", padx=20, pady=(20, 15))
        ctk.CTkLabel(header_frame, text="➕ Agregar Nueva Cuenta", font=("Segoe UI", 14, "bold"), text_color="#60a5fa").pack(pady=(12, 0))
        
        # Form Frame
        form_frame = ctk.CTkFrame(tab, corner_radius=12, fg_color="#1e3a5f", border_width=1, border_color="#1e40af")
        form_frame.pack(fill="x", padx=20, pady=10)
        form_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(form_frame, text="Alias (único)", font=("Segoe UI", 11, "bold"), text_color="#60a5fa").pack(anchor="w", padx=15, pady=(15, 5))
        self.entry_new_alias = ctk.CTkEntry(form_frame, placeholder_text="ej: fb_usuario1", height=35,
                                            fg_color="#0f172a", border_color="#1e40af", border_width=1,
                                            text_color="#e5e7eb")
        self.entry_new_alias.pack(fill="x", padx=15, pady=(0, 10))
        
        ctk.CTkLabel(form_frame, text="Plataforma", font=("Segoe UI", 11, "bold"), text_color="#60a5fa").pack(anchor="w", padx=15, pady=(0, 5))
        self.combo_platform = ctk.CTkComboBox(form_frame, values=["facebook", "instagram", "tiktok", "youtube", "twitter"],
                                              height=35, fg_color="#0f172a", border_color="#1e40af", border_width=1,
                                              button_color="#1e40af", button_hover_color="#0284c7", text_color="#e5e7eb")
        self.combo_platform.pack(fill="x", padx=15, pady=(0, 10))
        
        ctk.CTkLabel(form_frame, text="Usuario / Email", font=("Segoe UI", 11, "bold"), text_color="#60a5fa").pack(anchor="w", padx=15, pady=(0, 5))
        self.entry_new_user = ctk.CTkEntry(form_frame, placeholder_text="usuario@email.com", height=35,
                                           fg_color="#0f172a", border_color="#1e40af", border_width=1,
                                           text_color="#e5e7eb")
        self.entry_new_user.pack(fill="x", padx=15, pady=(0, 10))
        
        ctk.CTkLabel(form_frame, text="Contraseña", font=("Segoe UI", 11, "bold"), text_color="#60a5fa").pack(anchor="w", padx=15, pady=(0, 5))
        self.entry_new_pass = ctk.CTkEntry(form_frame, placeholder_text="••••••••", show="*", height=35,
                                           fg_color="#0f172a", border_color="#1e40af", border_width=1,
                                           text_color="#e5e7eb")
        self.entry_new_pass.pack(fill="x", padx=15, pady=(0, 10))
        
        ctk.CTkLabel(form_frame, text="Proxy (opcional)", font=("Segoe UI", 11, "bold"), text_color="#60a5fa").pack(anchor="w", padx=15, pady=(0, 5))
        self.entry_new_proxy = ctk.CTkEntry(form_frame, placeholder_text="http://user:pass@ip:port", height=35,
                                            fg_color="#0f172a", border_color="#1e40af", border_width=1,
                                            text_color="#e5e7eb")
        self.entry_new_proxy.pack(fill="x", padx=15, pady=(0, 15))
        # --- NUEVO: Selector de Método de Creación ---
        method_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        method_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        ctk.CTkLabel(method_frame, text="Método de Creación:", font=("Segoe UI", 11, "bold"), text_color="#60a5fa").pack(side="left", padx=(0, 10))
        
        self.var_creation_method = ctk.StringVar(value="pc_web")
        ctk.CTkRadioButton(method_frame, text="💻 PC (Navegador)", variable=self.var_creation_method, value="pc_web", font=("Segoe UI", 11)).pack(side="left", padx=10)
        ctk.CTkRadioButton(method_frame, text="📱 Celular Físico (Seguro)", variable=self.var_creation_method, value="mobile_app", font=("Segoe UI", 11)).pack(side="left", padx=10)
        # ---------------------------------------------

        # Buttons
        btn_row = ctk.CTkFrame(form_frame, fg_color="transparent")
        btn_row.pack(fill="x", padx=15, pady=(0, 15))
        btn_row.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkButton(btn_row, text="💾 Guardar", command=self.save_account, 
                     fg_color="#10b981", hover_color="#059669", corner_radius=8, height=40, font=("Segoe UI", 11, "bold")).grid(row=0, column=0, padx=3)
        ctk.CTkButton(btn_row, text="✏️ Editar", command=self.edit_account_dialog, 
                     fg_color="#0284c7", hover_color="#1e40af", corner_radius=8, height=40, font=("Segoe UI", 11, "bold")).grid(row=0, column=1, padx=3)
        ctk.CTkButton(btn_row, text="🗑️ Eliminar", command=self.delete_account_dialog, 
                     fg_color="#ef4444", hover_color="#dc2626", corner_radius=8, height=40, font=("Segoe UI", 11, "bold")).grid(row=0, column=2, padx=3)
        
        # Import Section
        import_frame = ctk.CTkFrame(tab, corner_radius=12, fg_color="#1e3a5f", border_width=1, border_color="#1e40af")
        import_frame.pack(fill="x", padx=20, pady=10)
        import_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(import_frame, text="📥 Importar Perfil Local", font=("Segoe UI", 12, "bold"), text_color="#60a5fa").pack(anchor="w", padx=15, pady=(15, 8))
        self.combo_import = ctk.CTkComboBox(import_frame, values=self.get_profiles_list(), height=35,
                                            fg_color="#0f172a", border_color="#1e40af", border_width=1,
                                            button_color="#1e40af", button_hover_color="#0284c7", text_color="#e5e7eb")
        self.combo_import.pack(fill="x", padx=15, pady=(0, 10))
        ctk.CTkButton(import_frame, text="📥 Vincular Carpeta", command=self.import_local_profile, 
                     fg_color="#0284c7", hover_color="#1e40af", corner_radius=8, height=40, font=("Segoe UI", 11, "bold")).pack(fill="x", padx=15, pady=(0, 15))

    # =========================================================================
    #                       UI CREADOR MÓVIL
    # =========================================================================
    # =========================================================================
    #                       UI CREADOR MÓVIL (UNA SIM A LA VEZ)
    # =========================================================================
    def setup_mobile_creator_ui(self):
        f = self.tab_mobile_creator
        f.grid_columnconfigure(0, weight=1)

        # Card Principal
        card = ctk.CTkFrame(f, corner_radius=12, fg_color="#1e3a5f", border_width=1, border_color="#1e40af")
        card.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(card, text="📱 CREADOR MÓVIL (1 SIM a la vez)", font=("Segoe UI", 20, "bold"), text_color="#60a5fa").pack(pady=(30, 10))
        ctk.CTkLabel(card, text="Instrucciones: Inserta la SIM, espera a que tenga señal, escribe el número y dale a Iniciar.", font=("Segoe UI", 12)).pack(pady=(0, 30))

        # Campo único: Teléfono
        config_frame = ctk.CTkFrame(card, fg_color="transparent")
        config_frame.pack(fill="x", padx=40)
        config_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(config_frame, text="Número de Teléfono (SIM actual):", font=("Segoe UI", 14, "bold")).grid(row=0, column=0, sticky="w", pady=10, padx=10)
        
        self.entry_mob_phone = ctk.CTkEntry(config_frame, placeholder_text="Ej: 3001234567", height=45, font=("Segoe UI", 16, "bold"), justify="center")
        self.entry_mob_phone.grid(row=0, column=1, padx=20, sticky="ew")

        # Botón de Inicio
        self.btn_start_mob = ctk.CTkButton(card, text="🔥 ROTAR IP Y CREAR CUENTA", 
                                          fg_color="#10b981", hover_color="#059669",
                                          height=60, font=("Segoe UI", 16, "bold"),
                                          command=self.trigger_single_mobile_creation)
        self.btn_start_mob.pack(pady=(40, 20), padx=80, fill="x")

        self.mob_progress_lbl = ctk.CTkLabel(card, text="Estado: Esperando número de teléfono...", font=("Segoe UI", 13), text_color="#9ca3af")
        self.mob_progress_lbl.pack(pady=10)

    def trigger_single_mobile_creation(self):
        """Dispara la creación de UNA cuenta tras presionar el botón"""
        phone = self.entry_mob_phone.get().strip()
        
        if not phone:
            from tkinter import messagebox
            messagebox.showwarning("Falta Número", "Debes ingresar el número de teléfono de la SIM actual.")
            return

        threading.Thread(target=self.run_single_mobile_logic, args=(phone,), daemon=True).start()

    def run_single_mobile_logic(self, phone):
        from smart_mobile import SmartMobileRescue
        from mobile_manager import renew_device_ip, get_connected_devices
        from login_manager import guardar_nueva_cuenta
        import random
        import string
        
        # Intentamos usar la librería Faker si la tienes
        try:
            from faker import Faker
            fake = Faker('es_MX')
        except ImportError:
            fake = None

        devices = get_connected_devices()
        if not devices:
            self.log("❌ No se detectó ningún celular conectado por USB.", "ERROR")
            self.mob_progress_lbl.configure(text="❌ Error: Celular no detectado. Revisa el cable.")
            return

        device_id = devices[0]
        self.is_running = True
        self.btn_start_mob.configure(state="disabled", text="⚡ PROCESANDO... NO TOCAR EL CELULAR")
        self.mob_progress_lbl.configure(text="Estado: 🔄 1/4 - Rotando IP (Modo Avión)...")
        
        try:
            # 1. ROTACIÓN DE IP (MODO AVIÓN ON/OFF)
            self.log("🔄 Ejecutando rotación de IP (Modo Avión)...", "INFO")
            renew_device_ip(device_id)

            # 2. GENERACIÓN DE DATOS TOTALMENTE ALEATORIOS
            if fake:
                nombre = fake.first_name()
                apellido = fake.last_name()
            else:
                nombres = ["Carlos", "Luis", "Maria", "Ana", "Jose", "Diego", "Laura"]
                apellidos = ["Gomez", "Perez", "Ruiz", "Lopez", "Diaz", "Torres"]
                nombre = random.choice(nombres)
                apellido = random.choice(apellidos)

            # Generar contraseña robusta aleatoria (ej: jKh8xLp2!A)
            caracteres = string.ascii_letters + string.digits
            pwd = ''.join(random.choice(caracteres) for _ in range(8)) + str(random.randint(10, 99)) + "!"
            
            # Generar Alias para la base de datos (ej: maria_ruiz_452)
            alias = f"{nombre.lower()}_{apellido.lower()}_{random.randint(100, 999)}"
            genero = random.choice(["Hombre", "Mujer"])

            self.log(f"📋 Identidad creada: {nombre} {apellido} | Genero: {genero}", "INFO")
            self.log(f"🔑 Credenciales -> User: {phone} | Pass: {pwd} | Alias: {alias}", "INFO")
            
            self.mob_progress_lbl.configure(text=f"Estado: 🤖 2/4 - Automatizando Facebook para {nombre}...")

            # 3. EJECUCIÓN DEL BOT EN EL CELULAR
            bot = SmartMobileRescue(device_id)
            datos = {
                "nombre": nombre,
                "apellido": apellido,
                "telefono": phone,
                "password": pwd,
                "genero": genero
            }

            exito = bot.automatizar_formulario_creacion("facebook", datos)
            
            # 4. GUARDADO EN BASE DE DATOS
            if exito:
                self.mob_progress_lbl.configure(text=f"Estado: 💾 3/4 - Guardando cuenta {alias} en Base de Datos...")
                self.log(f"✅ Facebook creado. Guardando cuenta {alias}...", "SUCCESS")
                
                # Guarda en SQLite
                guardar_nueva_cuenta(alias, phone, pwd, "Móvil (SIM)", "facebook")
                
                # Guarda en Excel (Si tienes importada la función)
                try:
                    exportar_cuenta_excel(alias, "facebook", phone, pwd, status="Creada (Móvil)")
                except Exception:
                    pass
                
                # Limpia la caja de texto y avisa que terminó
                self.entry_mob_phone.delete(0, 'end')
                self.mob_progress_lbl.configure(text=f"✅ ¡LISTO! Cuenta {alias} guardada. Puedes cambiar la SIM.")
                
                # Refresca las listas de la UI
                self.after(500, self.refresh_all_account_selectors)
                self.after(500, self.refresh_status_ui)
                
            else:
                self.log(f"⚠️ Fallo al crear la cuenta en Facebook.", "WARN")
                self.mob_progress_lbl.configure(text="❌ Falló la automatización. Revisa el celular.")

        except Exception as e:
            self.log(f"❌ Error crítico en creación móvil: {e}", "ERROR")
            self.mob_progress_lbl.configure(text="❌ Error en el proceso. Revisa la consola.")
        finally:
            self.is_running = False
            self.btn_start_mob.configure(state="normal", text="🔥 ROTAR IP Y CREAR CUENTA")

    def save_account(self):
        # 1. Capturamos todos los datos de los campos
        alias = self.entry_new_alias.get()
        network = self.combo_platform.get()
        user = self.entry_new_user.get()
        pwd = self.entry_new_pass.get()
        proxy = self.entry_new_proxy.get()
        
        # 2. Capturamos qué método eligió el usuario (con un fallback de seguridad)
        try:
            metodo = self.var_creation_method.get()
        except AttributeError:
            metodo = "pc_web" # Por si aún no has pegado el código de los RadioButtons en la UI

        if alias:
            # 3. Lógica del Celular (Se activará más tarde)
            if metodo == "mobile_app":
                print(f"🚀 [PRÓXIMAMENTE] Iniciando creación segura en celular para {alias}...")
                # Aquí conectaremos a smart_mobile.py en la tarde
            
            # 4. Guardamos la cuenta en la base de datos de SQLite
            if guardar_nueva_cuenta(alias, user, pwd, proxy, network):
                
                # ¡NUEVO! Guardamos la cuenta en el Excel
                try:
                    exportar_cuenta_excel(alias, network, user, pwd, status=f"Guardada ({metodo})")
                except NameError:
                    print("⚠️ Aviso: No se exportó a Excel porque falta importar la función arriba en main.py")

                # Refrescar listas visuales
                try:
                    self.refresh_all_account_selectors()
                except Exception:
                    pass
                self.on_tab_change()
                
                # Limpiar formulario
                self.entry_new_alias.delete(0, 'end')
                self.entry_new_user.delete(0, 'end')
                self.entry_new_pass.delete(0, 'end')
                self.entry_new_proxy.delete(0, 'end')

                # --- LÓGICA DE AVISO Y LOGIN INMEDIATO ---
                if metodo == "pc_web":
                    # Tu lógica original para cuando creas en PC
                    respuesta = messagebox.askyesno(
                        "Cuenta Guardada", 
                        f"La cuenta '{alias}' se guardó y exportó a Excel correctamente.\n\n"
                        "¿Deseas INICIAR SESIÓN MANUALMENTE ahora para guardar las cookies?"
                    )
                    
                    if respuesta:
                        # Lanzamos la ventana de asistencia de login
                        self.run_manual_login(alias)
                else:
                    # Aviso simple para cuando elegiste Celular Físico
                    messagebox.showinfo(
                        "Cuenta Guardada", 
                        f"La cuenta '{alias}' se guardó y exportó a Excel correctamente.\n\n"
                        "Método seleccionado: 📱 Celular Físico."
                    )
            else:
                messagebox.showerror("Error", "No se pudo guardar (Posible Alias duplicado).")
        else:
            messagebox.showwarning("Faltan datos", "El campo Alias es obligatorio.")


    
    def get_profiles_list(self):
        if not os.path.exists("profiles"): return ["No hay carpetas"]
        dirs = [d for d in os.listdir("profiles") if os.path.isdir(os.path.join("profiles", d))]
        return dirs if dirs else ["Carpeta vacía"]

    def import_local_profile(self):
        alias = self.combo_import.get()
        if alias and alias != "No hay carpetas":
            if importar_perfil_especifico(alias):
                messagebox.showinfo("Importado", f"Perfil {alias} vinculado exitosamente.")
                try:
                    self.refresh_all_account_selectors()
                except Exception:
                    pass
                self.on_tab_change()
            else:
                messagebox.showerror("Error", "Fallo al importar perfil.")

    def edit_account(self):
        alias = self.entry_new_alias.get() or None
        if not alias:
            messagebox.showwarning("Seleccionar", "Ingresa el alias que deseas editar en el campo 'Alias'.")
            return

        data = obtener_datos_cuenta(alias)
        if not data:
            messagebox.showerror("No encontrado", f"No se encontró la cuenta '{alias}' en la DB.")
            return

        # Crear ventana modal simple para editar campos básicos
        win = ctk.CTkToplevel(self)
        win.title(f"Editar: {alias}")
        win.geometry("420x260")

        ctk.CTkLabel(win, text=f"Editar cuenta: {alias}", font=("Segoe UI", 12, "bold")).pack(pady=8)

        ent_user = ctk.CTkEntry(win, placeholder_text="Usuario/Email")
        ent_user.pack(pady=6)
        ent_user.insert(0, data.get('username',''))

        ent_pass = ctk.CTkEntry(win, placeholder_text="Contraseña", show="*")
        ent_pass.pack(pady=6)
        ent_pass.insert(0, data.get('password',''))

        ent_proxy = ctk.CTkEntry(win, placeholder_text="Proxy (http://user:pass@ip:port)")
        ent_proxy.pack(pady=6)
        ent_proxy.insert(0, data.get('proxy','') or '')

        combo_plat = ctk.CTkComboBox(win, values=["facebook","instagram","tiktok","youtube","twitter"])
        combo_plat.pack(pady=6)
        combo_plat.set(data.get('platform','facebook'))

        def _save_and_close():
            from login_manager import actualizar_cuenta
            ok = actualizar_cuenta(alias, user=ent_user.get(), pwd=ent_pass.get(), proxy=ent_proxy.get(), platform=combo_plat.get())
            if ok:
                messagebox.showinfo("Editado", "Cuenta actualizada correctamente.")
                win.destroy()
                try:
                    self.refresh_all_account_selectors()
                except Exception:
                    pass
                self.on_tab_change()
            else:
                messagebox.showerror("Error", "No se pudo actualizar la cuenta.")

        ctk.CTkButton(win, text="Guardar Cambios", command=_save_and_close, fg_color="#27ae60").pack(pady=10)

    def edit_account_dialog(self):
        """Abre un diálogo para seleccionar la cuenta a editar por plataforma"""
        win = ctk.CTkToplevel(self)
        win.title("Seleccionar Cuenta a Editar")
        win.geometry("400x300")
        win.transient(self)
        win.attributes("-topmost", True)
        
        ctk.CTkLabel(win, text="Editar Cuenta", font=("Segoe UI", 14, "bold")).pack(pady=15)
        
        # Selector de plataforma
        ctk.CTkLabel(win, text="Selecciona la plataforma:", font=("Segoe UI", 11)).pack(pady=(10, 5))
        combo_platform = ctk.CTkComboBox(win, values=list(self.plataformas.keys()), width=300)
        combo_platform.pack(pady=5)
        combo_platform.set("Facebook")
        
        # Selector de cuenta (se actualiza al cambiar plataforma)
        ctk.CTkLabel(win, text="Selecciona la cuenta:", font=("Segoe UI", 11)).pack(pady=(15, 5))
        combo_account = ctk.CTkComboBox(win, values=["Sin cuentas"], width=300)
        combo_account.pack(pady=5)
        
        def actualizar_cuentas(*args):
            plat_ui = combo_platform.get()
            plat_key = self.plataformas.get(plat_ui, "facebook")
            cuentas = obtener_cuentas_por_plataforma(plat_key)
            combo_account.configure(values=cuentas if cuentas else ["Sin cuentas"])
            if cuentas and cuentas[0] != "Sin cuentas":
                combo_account.set(cuentas[0])
            else:
                combo_account.set("Sin cuentas")
        
        # Actualizar cuentas al cambiar plataforma
        combo_platform.configure(command=actualizar_cuentas)
        actualizar_cuentas()
        
        def editar_cuenta_seleccionada():
            alias = combo_account.get()
            if not alias or alias == "Sin cuentas":
                messagebox.showwarning("Error", "Selecciona una cuenta válida")
                return
            
            data = obtener_datos_cuenta(alias)
            if not data:
                messagebox.showerror("Error", f"No se encontró la cuenta '{alias}'")
                return
            
            # Cerrar el diálogo de selección
            win.destroy()
            
            # Abrir ventana de edición
            edit_win = ctk.CTkToplevel(self)
            edit_win.title(f"Editar: {alias}")
            edit_win.geometry("420x280")
            edit_win.transient(self)
            edit_win.attributes("-topmost", True)
            
            ctk.CTkLabel(edit_win, text=f"Editar cuenta: {alias}", font=("Segoe UI", 12, "bold")).pack(pady=10)
            
            ent_user = ctk.CTkEntry(edit_win, placeholder_text="Usuario/Email", width=300)
            ent_user.pack(pady=6)
            ent_user.insert(0, data.get('username',''))
            
            ent_pass = ctk.CTkEntry(edit_win, placeholder_text="Contraseña", show="*", width=300)
            ent_pass.pack(pady=6)
            ent_pass.insert(0, data.get('password',''))
            
            ent_proxy = ctk.CTkEntry(edit_win, placeholder_text="Proxy (http://user:pass@ip:port)", width=300)
            ent_proxy.pack(pady=6)
            ent_proxy.insert(0, data.get('proxy','') or '')
            
            combo_plat = ctk.CTkComboBox(edit_win, values=["facebook","instagram","tiktok","youtube","twitter"], width=300)
            combo_plat.pack(pady=6)
            combo_plat.set(data.get('platform','facebook'))
            
            def guardar_cambios():
                from login_manager import actualizar_cuenta
                ok = actualizar_cuenta(alias, user=ent_user.get(), pwd=ent_pass.get(), proxy=ent_proxy.get(), platform=combo_plat.get())
                if ok:
                    messagebox.showinfo("Éxito", "Cuenta actualizada correctamente")
                    edit_win.destroy()
                    try:
                        self.refresh_all_account_selectors()
                    except:
                        pass
                    self.on_tab_change()
                else:
                    messagebox.showerror("Error", "No se pudo actualizar la cuenta")
            
            ctk.CTkButton(edit_win, text="💾 Guardar Cambios", command=guardar_cambios, fg_color="#27ae60", width=300).pack(pady=15)
        
        ctk.CTkButton(win, text="✏️ Editar Cuenta Seleccionada", command=editar_cuenta_seleccionada, fg_color="#f39c12", width=300).pack(pady=20)

    def delete_account_dialog(self):
        """Abre un diálogo para seleccionar la cuenta a eliminar por plataforma"""
        win = ctk.CTkToplevel(self)
        win.title("Eliminar Cuenta")
        win.geometry("400x280")
        win.transient(self)
        win.attributes("-topmost", True)
        
        ctk.CTkLabel(win, text="Eliminar Cuenta", font=("Segoe UI", 14, "bold")).pack(pady=15)
        
        # Selector de plataforma
        ctk.CTkLabel(win, text="Selecciona la plataforma:", font=("Segoe UI", 11)).pack(pady=(10, 5))
        combo_platform = ctk.CTkComboBox(win, values=list(self.plataformas.keys()), width=300)
        combo_platform.pack(pady=5)
        combo_platform.set("Facebook")
        
        # Selector de cuenta
        ctk.CTkLabel(win, text="Selecciona la cuenta a eliminar:", font=("Segoe UI", 11)).pack(pady=(15, 5))
        combo_account = ctk.CTkComboBox(win, values=["Sin cuentas"], width=300)
        combo_account.pack(pady=5)
        
        def actualizar_cuentas(*args):
            plat_ui = combo_platform.get()
            plat_key = self.plataformas.get(plat_ui, "facebook")
            cuentas = obtener_cuentas_por_plataforma(plat_key)
            combo_account.configure(values=cuentas if cuentas else ["Sin cuentas"])
            if cuentas and cuentas[0] != "Sin cuentas":
                combo_account.set(cuentas[0])
            else:
                combo_account.set("Sin cuentas")
        
        combo_platform.configure(command=actualizar_cuentas)
        actualizar_cuentas()
        
        def eliminar_cuenta_seleccionada():
            alias = combo_account.get()
            if not alias or alias == "Sin cuentas":
                messagebox.showwarning("Error", "Selecciona una cuenta válida")
                return
            
            if messagebox.askyesno("Confirmar", f"¿Eliminar la cuenta '{alias}'? Esta acción no se puede deshacer."):
                from login_manager import eliminar_cuenta
                if eliminar_cuenta(alias):
                    messagebox.showinfo("Éxito", "Cuenta eliminada correctamente")
                    win.destroy()
                    try:
                        self.refresh_all_account_selectors()
                    except:
                        pass
                    self.on_tab_change()
                else:
                    messagebox.showerror("Error", "No se pudo eliminar la cuenta")
        
        ctk.CTkButton(win, text="🗑️ Eliminar Cuenta", command=eliminar_cuenta_seleccionada, fg_color="#e74c3c", width=300).pack(pady=20)

    def refresh_all_account_selectors(self):
        """Refresca todos los selectores individuales por plataforma desde la DB."""
        try:
            for platform_key, selector in list(self.account_selectors.items()):
                try:
                    cuentas = obtener_cuentas_por_plataforma(platform_key)
                    selector.configure(values=cuentas)
                    if cuentas and cuentas[0] != "Sin cuentas":
                        selector.set(cuentas[0])
                    else:
                        selector.set("Sin cuentas")
                except Exception:
                    # No rompemos todo si un selector falla
                    continue
        except Exception:
            pass

    # --- IMPLEMENTACIÓN DE LOGIN MANUAL ---
    def run_manual_login(self, alias=None):
            # 1. Obtener el alias si no viene por parámetro
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

            # 2. Obtener datos de la cuenta
            data = obtener_datos_cuenta(alias)
            if not data:
                messagebox.showerror("Error", "No se encontraron datos de la cuenta.")
                return

            # 3. Crear VENTANA FLOTANTE DE ASISTENCIA (Helper)
            helper = ctk.CTkToplevel(self)
            helper.title(f"Login: {alias}")
            helper.geometry("350x450")
            helper.attributes("-topmost", True) # Mantener siempre visible encima del navegador
            helper.resizable(False, False)

            # Contenedor principal
            frame = ctk.CTkFrame(helper, corner_radius=10)
            frame.pack(fill="both", expand=True, padx=10, pady=10)

            ctk.CTkLabel(frame, text=f"🔐 ASISTENTE DE LOGIN", font=("Segoe UI", 16, "bold"), text_color="#60a5fa").pack(pady=(15, 5))
            ctk.CTkLabel(frame, text=f"Cuenta: {alias}", font=("Segoe UI", 12)).pack(pady=(0, 10))
            
            # --- Función para copiar al portapapeles ---
            def copy_to_clipboard(text):
                self.clipboard_clear()
                self.clipboard_append(text)
                self.update() # Necesario para que el portapapeles se actualice
                messagebox.showinfo("Copiado", "Texto copiado al portapapeles", parent=helper)

            # Mostrar Usuario
            ctk.CTkLabel(frame, text="Usuario / Email:", font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=20)
            user_frame = ctk.CTkFrame(frame, fg_color="transparent")
            user_frame.pack(fill="x", padx=20, pady=(0, 10))
            
            ent_user = ctk.CTkEntry(user_frame, width=220)
            ent_user.pack(side="left", padx=(0, 5))
            ent_user.insert(0, data.get("username", ""))
            
            ctk.CTkButton(user_frame, text="📋", width=30, fg_color="#475569", 
                        command=lambda: copy_to_clipboard(data.get("username", ""))).pack(side="left")

            # Mostrar Contraseña
            ctk.CTkLabel(frame, text="Contraseña:", font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=20)
            pass_frame = ctk.CTkFrame(frame, fg_color="transparent")
            pass_frame.pack(fill="x", padx=20, pady=(0, 15))
            
            ent_pass = ctk.CTkEntry(pass_frame, width=220) # No ponemos show="*" para que puedas verla si quieres
            ent_pass.pack(side="left", padx=(0, 5))
            ent_pass.insert(0, data.get("password", ""))
            
            ctk.CTkButton(pass_frame, text="📋", width=30, fg_color="#475569", 
                        command=lambda: copy_to_clipboard(data.get("password", ""))).pack(side="left")

            # Instrucciones
            instrucciones = (
                "1. El navegador se abrirá automáticamente.\n"
                "2. Copia y pega los datos de arriba.\n"
                "3. Inicia sesión y asegúrate de entrar al Home.\n"
                "4. Presiona 'GUARDAR SESIÓN' abajo."
            )
            ctk.CTkLabel(frame, text=instrucciones, justify="left", font=("Segoe UI", 10), text_color="#9ca3af").pack(padx=20, pady=10)

            # Variables para controlar el hilo del navegador
            browser_state = {"context": None, "page": None, "playwright": None, "running": True}

            # --- Función para guardar y cerrar ---
            def save_and_close():
                if browser_state["context"]:
                    try:
                        # Capturar cookies
                        cookies = browser_state["context"].cookies()
                        
                        # Guardar en DB
                        from login_manager import guardar_cookies_db
                        guardar_cookies_db(alias, cookies, strict=False, platform_hint=data.get("platform"))
                        
                        # Guardar en JSON (Respaldo local)
                        import json
                        with open(f"{alias}.json", "w", encoding="utf-8") as f:
                            json.dump(cookies, f, indent=4)
                        
                        messagebox.showinfo("Éxito", "✅ Cookies guardadas y perfil actualizado.", parent=helper)
                        self.log(f"✅ Login Manual COMPLETADO para: {alias}", "SUCCESS")
                    except Exception as e:
                        self.log(f"Error guardando cookies: {e}", "ERROR")
                        messagebox.showerror("Error", f"No se pudieron guardar las cookies: {e}", parent=helper)
                    
                    # Cerrar navegador
                    try:
                        browser_state["context"].close()
                        browser_state["playwright"].stop()
                    except: pass
                    
                    browser_state["running"] = False
                    helper.destroy()
                    
                    # Actualizar estado UI
                    if hasattr(self, 'refresh_status_ui'):
                        self.refresh_status_ui()
                else:
                    messagebox.showwarning("Espera", "El navegador aún no está listo.", parent=helper)

            # Botón de Guardar
            btn_save = ctk.CTkButton(frame, text="💾 GUARDAR SESIÓN Y SALIR", command=save_and_close,
                                    fg_color="#10b981", hover_color="#059669", height=45, font=("Segoe UI", 12, "bold"))
            btn_save.pack(fill="x", padx=20, pady=(10, 20))

            # --- Hilo del Navegador ---
            def _browser_thread():
                self.log(f"🔵 Abriendo navegador para: {alias}...", "INFO")
                try:
                    from playwright.sync_api import sync_playwright
                    from browser_handler import get_browser_context
                    
                    p = sync_playwright().start()
                    browser_state["playwright"] = p
                    
                    # IMPORTANTE: headless=False para que puedas ver la ventana
                    context = get_browser_context(p, alias, headless=False, log_callback=self.log)
                    browser_state["context"] = context
                    
                    page = context.new_page()
                    
                    # Navegar a la plataforma
                    urls = {
                        "facebook": "https://www.facebook.com/",
                        "instagram": "https://www.instagram.com/",
                        "tiktok": "https://www.tiktok.com/login",
                        "youtube": "https://accounts.google.com/",
                        "twitter": "https://twitter.com/login"
                    }
                    plat = data.get("platform", "facebook").lower()
                    url = urls.get(plat, "https://www.facebook.com/")
                    
                    try:
                        page.goto(url)
                    except: pass

                    # Bucle infinito para mantener el navegador abierto hasta que el usuario guarde
                    while browser_state["running"]:
                        time.sleep(1)
                        # Verificar si el navegador se cerró manualmente
                        try:
                            if page.is_closed():
                                break
                        except:
                            break
                    
                    # Limpieza si se cierra el bucle
                    if browser_state["running"]:
                        context.close()
                        p.stop()
                        
                except Exception as e:
                    self.log(f"❌ Error en navegador manual: {e}", "ERROR")

            # Iniciar el hilo del navegador
            threading.Thread(target=_browser_thread, daemon=True).start()

            # Protocolo al cerrar la ventana flotante (helper)
            def on_helper_close():
                if messagebox.askyesno("Cerrar", "¿Seguro que quieres cerrar sin guardar las cookies?", parent=helper):
                    browser_state["running"] = False
                    helper.destroy()
            
            helper.protocol("WM_DELETE_WINDOW", on_helper_close)


    def run_mobile_creation_flow(self, alias, network, user, pwd, proxy):
        from smart_mobile import SmartMobileRescue
        from login_manager import guardar_nueva_cuenta
        
        self.log(f"📱 Iniciando creación en celular para {alias}...", "INFO")
        
        try:
            bot_movil = SmartMobileRescue() 
            
            datos = {
                "nombre": alias.split('_')[0], 
                "apellido": "Bot", 
                "telefono": user, # Tu número celular
                "password": pwd,
                "genero": "Hombre" # O aleatorio: random.choice(["Hombre", "Mujer"])
            }
            
            # Ejecuta la rutina del celular
            exito = bot_movil.automatizar_formulario_creacion(network, datos)
            
            if exito:
                self.log("✅ Flujo móvil terminado. Guardando en Base de Datos...", "SUCCESS")
                
                # ¡AQUÍ ESTÁ LA MAGIA DEL SQL! 
                # Llama a tu función de login_manager.py que hace el INSERT en SQLite
                if guardar_nueva_cuenta(alias, user, pwd, proxy, network):
                    self.log(f"💾 ¡Cuenta {alias} guardada en SQLite exitosamente!", "SUCCESS")
                    
                    # Refrescar la UI para que aparezca en el panel de inmediato
                    self.after(500, self.refresh_all_account_selectors)
                    self.after(500, self.refresh_status_ui)
                else:
                    self.log(f"⚠️ La cuenta se creó en el móvil, pero hubo un error guardándola en la DB (¿Alias duplicado?)", "WARN")
            else:
                self.log("❌ El flujo móvil falló o se interrumpió.", "ERROR")
                
        except Exception as e:
            self.log(f"❌ Error crítico en flujo móvil: {e}", "ERROR")



if __name__ == "__main__":
    if not os.path.exists("logs"): os.makedirs("logs")
    if not os.path.exists("profiles"): os.makedirs("profiles")
    app = SocialBotApp()
    app.mainloop()
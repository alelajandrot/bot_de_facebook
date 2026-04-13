import uiautomator2 as u2
import time
import re
from typing import Optional

class SmartMobileRescue:
    def __init__(self, device_id=None):
        print("🔌 Conectando al Escuadrón de Rescate Móvil...")
        self.d = u2.connect(device_id) 
        self.d.implicitly_wait(10.0) 
        self.d.set_fastinput_ime(False)
        print("✅ Conexión establecida con éxito.")

    # --- HELPERS MEJORADOS (AHORA SÍ ESPERAN A QUE CARGUE LA PANTALLA) ---
    def _wait_and_click(self, text_val: str, timeout: int = 12) -> bool:
        """Espera hasta 'timeout' segundos a que aparezca un texto y lo toca."""
        print(f"   👀 Buscando: '{text_val}'...")
        
        # 1. Intentar buscar por texto exacto primero (Más seguro para botones como DEFINIR)
        elem_exact = self.d(text=text_val)
        if elem_exact.wait(timeout=2):
            elem_exact.click()
            time.sleep(1.5)
            return True

        # 2. Intentar buscar por texto parcial en pantalla
        elem = self.d(textMatches=f"(?i).*{text_val}.*")
        if elem.wait(timeout=timeout): 
            elem.click()
            time.sleep(1.5) 
            return True
        
        # 3. Intentar buscar por descripción (A veces FB oculta el texto en la descripción)
        elem_desc = self.d(descriptionMatches=f"(?i).*{text_val}.*")
        if elem_desc.wait(timeout=2):
            elem_desc.click()
            time.sleep(1.5)
            return True
        
        print(f"   ⚠️ Falla: No apareció '{text_val}' después de {timeout} segundos.")
        return False

    def _wait_and_fill(self, text_val: str, input_text: str, timeout: int = 12) -> bool:
        """Espera a que aparezca la caja de texto y la llena."""
        print(f"   ✍️ Escribiendo en: '{text_val}'...")
        
        elem = self.d(className="android.widget.EditText", textMatches=f"(?i).*{text_val}.*")
        if not elem.wait(timeout=timeout):
            elem = self.d(className="android.widget.EditText", descriptionMatches=f"(?i).*{text_val}.*")
            
        if not elem.exists:
            # Fallback: tomar la primera caja de texto vacía que encuentre
            elem = self.d(className="android.widget.EditText")

        if elem.exists:
            elem.click() 
            time.sleep(1)
            self.d.send_keys(input_text, clear=True) 
            time.sleep(1)
            try: self.d.press("back") # Esconder teclado para ver el botón Siguiente
            except: pass
            return True
        
        print(f"   ⚠️ Falla: No encontré dónde escribir '{text_val}'")
        return False

    # --- TU FLUJO EXACTO PASO A PASO ---
    def automatizar_formulario_creacion(self, network: str, data: dict):
        if network.lower() == "facebook":
            print("🚀 1. Abriendo app de Facebook...")
            self.d.app_start("com.facebook.katana", stop=True)
            time.sleep(6) 

            print("📝 2. Iniciando flujo de registro...")
            if not self._wait_and_click("Crear cuenta nueva", timeout=15):
                print("❌ Abortando: No se pudo iniciar el flujo.")
                return False
            
            print("⚙️ 2.1 Eligiendo 'Crear cuenta manualmente'...")
            if self.d(textMatches="(?i).*manualmente.*").wait(timeout=8):
                self._wait_and_click("manualmente")
            
            print("🔄 2.2 Confirmando inicio ('Crear cuenta nueva' de nuevo)...")
            if self.d(textMatches="(?i).*Crear cuenta nueva.*").wait(timeout=6):
                self._wait_and_click("Crear cuenta nueva")
            elif self.d(textMatches="(?i).*Empezar.*").wait(timeout=3):
                self._wait_and_click("Empezar")

            print("👤 3. Ingresando nombre y apellido...")
            cajas_texto = self.d(className="android.widget.EditText")
            if len(cajas_texto) >= 2:
                # Usamos set_text directo y quitamos el press("back") problemático
                cajas_texto[0].set_text(data.get('nombre', 'Juan'))
                time.sleep(0.5)
                cajas_texto[1].set_text(data.get('apellido', 'Perez'))
                time.sleep(0.5)
            else:
                self._wait_and_fill("Nombre", data.get('nombre'))
                self._wait_and_fill("Apellido", data.get('apellido'))
            
            if not self._wait_and_click("Siguiente"): return False

            # --- BASADO EN TUS IMÁGENES DE FECHA ---
# --- BASADO EN TUS IMÁGENES DE FECHA ---
            print("🎂 4. Configurando fecha de nacimiento (<2000)...")
            
            if not self.d(text="DEFINIR").exists:
                self._wait_and_click("Fecha de nacimiento")
                time.sleep(1.5)

            print("   ⚙️ Rueda de fecha detectada. Ajustando valores físicamente...")
            
            # Método 100% físico: Deslizamientos en los selectores
            try:
                pickers = self.d(className="android.widget.NumberPicker")
                if len(pickers) >= 3:
                    # pickers[0] = Día | pickers[1] = Mes | pickers[2] = Año
                    
                    # 1. Ajustar el DÍA (Deslizamos 2 veces hacia abajo)
                    bounds_day = pickers[0].info['bounds']
                    cx_day = (bounds_day['left'] + bounds_day['right']) // 2
                    y_start = bounds_day['top'] + 20
                    y_end = bounds_day['bottom'] - 20
                    
                    print("   ⏬ Girando el día...")
                    for _ in range(2):
                        self.d.swipe(cx_day, y_start, cx_day, y_end, 0.15)
                        time.sleep(0.3)

                    # 2. Ajustar el AÑO (Deslizamos 7 veces hacia abajo para bajar de 2026 a ~1999)
                    bounds_year = pickers[2].info['bounds']
                    cx_year = (bounds_year['left'] + bounds_year['right']) // 2
                    
                    print("   ⏬ Girando el año...")
                    for _ in range(7):
                        self.d.swipe(cx_year, y_start, cx_year, y_end, 0.15)
                        time.sleep(0.3)
                        
            except Exception as e:
                print(f"   ⚠️ Fallo al deslizar la rueda: {e}")
            
            # Pausa obligatoria para que la animación de la rueda se detenga por completo
            time.sleep(2) 
            
            print("   ✅ Ruedas detenidas. Presionando DEFINIR...")
            boton_definir = self.d(text="DEFINIR")
            if boton_definir.exists:
                boton_definir.click()
            else:
                self._wait_and_click("DEFINIR")
                
            time.sleep(2)
            
            print("   👉 Confirmando pantalla de fecha...")
            if not self._wait_and_click("Siguiente"): return False

            # --- BASADO EN TU IMAGEN DE GÉNERO ---
            print(f"⚧ 5. Seleccionando género: {data.get('genero')}...")
            # Clic directo en Mujer u Hombre (Imagen 2)
            genero_str = data.get('genero', 'Hombre')
            self._wait_and_click(genero_str)
            if not self._wait_and_click("Siguiente"): return False

            # --- RESTO DEL FORMULARIO ---
            print(f"📱 6. Ingresando número de celular: {data.get('telefono')}...")
            caja_celular = self.d(className="android.widget.EditText", textMatches="(?i).*celular.*")
            if not caja_celular.exists:
                caja_celular = self.d(className="android.widget.EditText")
                
            if caja_celular.exists:
                caja_celular.click()
                time.sleep(1)
                
                # 🧹 Forzamos la limpieza del texto prellenado (el +57...)
                caja_celular.clear_text()
                time.sleep(0.5)
                # Plan B: Por si Facebook ignora el comando anterior, presionamos el botón "Borrar" 15 veces
                for _ in range(15):
                    self.d.press("delete")
                
                time.sleep(0.5)
                caja_celular.set_text(data.get('telefono'))
                time.sleep(1)
            else:
                print("   ⚠️ Falla: No encontré dónde escribir el celular")
                return False
                
            if not self._wait_and_click("Siguiente"): return False

            print("🔑 7. Creando contraseña...")    
            caja_pass = self.d(className="android.widget.EditText")
            if caja_pass.wait(timeout=10):
                # Insertamos texto DIRECTO sin tocarla para no abrir teclados
                caja_pass.set_text(data.get('password'))
                time.sleep(1)
                
                # Forzamos ocultar cualquier teclado que se haya colado
                try: self.d.press("back") 
                except: pass
            else:
                print("   ⚠️ Falla: No encontré dónde escribir la contraseña")
                return False
                
            if not self._wait_and_click("Siguiente"): return False

            print("⏳ 8. Guardando info y aceptando términos (puede tardar unos segundos)...")
            if self.d(textMatches="(?i).*Guardar.*").wait(timeout=5):
                self._wait_and_click("Guardar")
            elif self.d(textMatches="(?i).*Ahora no.*").exists:
                self._wait_and_click("Ahora no")
                
            self._wait_and_click("Acepto", timeout=15)
            time.sleep(10) # Pausa larga mientras FB procesa la creación en sus servidores

            print("📫 9. Seleccionando validación por SMS...")
            if self.d(textMatches="(?i).*SMS.*").wait(timeout=8):
                self._wait_and_click("SMS")
                self._wait_and_click("Siguiente")

# 🔥 AHORA FACEBOOK HACE EL TRABAJO POR NOSOTROS 🔥
            print("📩 10. Esperando que Facebook auto-detecte el SMS...")
            time.sleep(15) # Pausa para que llegue el SMS y FB lo lea solo
            
            # Por si Facebook lo llena pero no avanza automáticamente
            if self.d(text="Siguiente").exists:
                self._wait_and_click("Siguiente")

            # --- FINALIZAR (FOTO, AHORA NO, AMIGOS) ---
            print("🖼️ 11. Omitiendo foto de perfil...")
            self._wait_and_click("Omitir", timeout=20) 

            print("🚫 12. Seleccionando 'Ahora no'...")
            self._wait_and_click("Ahora no", timeout=10)

            print("🛑 13. Confirmando 'Omitir' en modal flotante...")
            # Usamos búsqueda exacta para el modal flotante para no fallar
            boton_omitir = self.d(text="Omitir")
            if boton_omitir.wait(timeout=5):
                boton_omitir.click()
            else:
                self._wait_and_click("Omitir")

            print("👥 14. Agregando 5 amigos...")
            # El botón suele decir "Agregar 5 amigos" o "Agregar amigos"
            boton_amigos = self.d(textMatches="(?i).*Agregar.*amigos.*")
            if boton_amigos.wait(timeout=10):
                boton_amigos.click()
                time.sleep(2)
            else:
                self._wait_and_click("Siguiente") # Fallback si dice Siguiente

            print("🎉 ¡CUENTA CREADA Y LISTA EN EL FEED!")
            return True


    def extraer_otp_semi_automatico(self) -> Optional[str]:
        print(f"   📩 Abriendo app de Mensajes para extraer SMS...")
        self.d.app_start("com.google.android.apps.messaging")
        time.sleep(5)
        
        mensajes_en_pantalla = self.d(textMatches=r".*\b[0-9]{5,6}\b.*")
        
        if mensajes_en_pantalla.exists:
            texto_crudo = mensajes_en_pantalla[-1].info['text']
            print(f"   📝 SMS Leído: '{texto_crudo}'")
            
            codigo = re.search(r'\b(\d{5,6})\b', texto_crudo)
            if codigo:
                numero = codigo.group(1)
                print(f"   🎯 ¡CÓDIGO EXTRAÍDO!: {numero}")
                return numero
        print("   ❌ No hay mensajes recientes con códigos en pantalla.")
        return None

if __name__ == "__main__":
    bot = SmartMobileRescue()
    datos_prueba = {
        "nombre": "Andres",
        "apellido": "Gomez",
        "telefono": "3246132026", # Reemplázalo con tu sim de prueba
        "password": "PasswordFuerte99!",
        "genero": "Hombre"
    }
    print("🚀 Arrancando prueba de creación...")
    bot.automatizar_formulario_creacion("Facebook", datos_prueba)
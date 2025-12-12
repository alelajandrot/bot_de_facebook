import time
import random
from playwright.sync_api import sync_playwright
from faker import Faker

# Configuración
DOMINIO_EMPRESA = "@tu-empresa.com"  # CAMBIA ESTO por tu dominio catch-all
fake = Faker('es_MX')  # Datos latinos

def generar_identidad():
    perfil = fake.profile()
    nombre = perfil['name'].split()[0]
    apellido = perfil['name'].split()[1]
    # Generamos un correo único basado en el nombre + números aleatorios
    email = f"{nombre.lower()}.{apellido.lower()}{random.randint(100,999)}{DOMINIO_EMPRESA}"
    password = fake.password(length=14) + "Mx1!" 
    
    return {
        "nombre": nombre,
        "apellido": apellido,
        "email": email,
        "password": password,
        "dia": str(random.randint(1, 28)),
        "mes": str(random.randint(1, 12)),
        "anio": str(random.randint(1995, 2002)),
        "genero": random.choice(["1", "2"]) # 1: Mujer, 2: Hombre (en FB)
    }

def crear_cuenta_facebook():
    datos = generar_identidad()
    print("="*40)
    print(f"🤖 BOT DE CREACIÓN DE CUENTAS")
    print(f"👤 Nombre: {datos['nombre']} {datos['apellido']}")
    print(f"📧 Email: {datos['email']}")
    print(f"🔑 Pass:  {datos['password']}")
    print("="*40)

    with sync_playwright() as p:
        # Lanzamos navegador visible (Headless=False) para que tú veas
        browser = p.firefox.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        print("🌐 Entrando a Facebook Registro...")
        page.goto("https://www.facebook.com/reg/", wait_until="domcontentloaded")

        try:
            # Llenado veloz del formulario
            page.fill('input[name="firstname"]', datos['nombre'])
            page.fill('input[name="lastname"]', datos['apellido'])
            page.fill('input[name="reg_email__"]', datos['email'])
            
            # Espera breve por si pide confirmación de email
            time.sleep(1)
            confirmacion = page.locator('input[name="reg_email_confirmation__"]')
            if confirmacion.is_visible():
                confirmacion.fill(datos['email'])

            page.fill('input[name="reg_passwd__"]', datos['password'])

            # Fechas
            page.select_option('#day', datos['dia'])
            page.select_option('#month', datos['mes'])
            page.select_option('#year', datos['anio'])

            # Género
            page.click(f"input[value='{datos['genero']}']")

            print("✅ Formulario listo.")
            print("⚠️ PASO MANUAL REQUERIDO:")
            print("1. Dale click a 'Registrarte'.")
            print("2. Facebook te pedirá código del correo o celular.")
            print("3. Resuélvelo manualmente.")
            print("4. Cuando entres al perfil, presiona ENTER aquí en la consola para guardar las cookies.")
            
            input("Esperando a que completes el registro... (Presiona Enter al terminar)")

            # Guardar la sesión automáticamente
            nombre_archivo = f"{datos['nombre']}_{datos['apellido']}.json"
            context.storage_state(path=nombre_archivo)
            print(f"💾 Cookies guardadas en: {nombre_archivo}")
            print("¡Listo para usar en el Bot Principal!")

        except Exception as e:
            print(f"❌ Error: {e}")
        
        browser.close()

if __name__ == "__main__":
    crear_cuenta_facebook()
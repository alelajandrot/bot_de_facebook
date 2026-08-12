import sqlite3
import json
import os
import glob
from playwright.sync_api import sync_playwright

def extraer_cookies_de_perfiles_fisicos():
    db_path = 'cuentas.db'
    if not os.path.exists(db_path):
        print(f"❌ No se encontró la base de datos '{db_path}'.")
        return

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    print("\n" + "="*65)
    print("🔄 EXTRAENDO COOKIES DESDE LOS PERFILES FÍSICOS")
    print("="*65)

    # Buscar la carpeta donde se guardan los perfiles de Playwright
    base_profiles = "profiles"
    if not os.path.exists(base_profiles):
        base_profiles = os.path.join("facebook_bot", "profiles")

    if not os.path.exists(base_profiles):
        print("⚠️ No se encontró la carpeta de perfiles.")
        conn.close()
        return

    # Listar todas las carpetas dentro de profiles
    carpetas_perfiles = [d for d in os.listdir(base_profiles) if os.path.isdir(os.path.join(base_profiles, d))]

    actualizadas = 0

    with sync_playwright() as p:
        for alias in carpetas_perfiles:
            profile_dir = os.path.abspath(os.path.join(base_profiles, alias))
            print(f"🔍 Inspeccionando perfil: {alias}...")

            try:
                # Lanzar contexto persistente de forma invisible (headless)
                context = p.chromium.launch_persistent_context(
                    user_data_dir=profile_dir,
                    headless=True
                )
                
                # Extraer cookies activas
                cookies = context.cookies()
                context.close()

                if cookies and len(cookies) > 0:
                    cookies_json_str = json.dumps(cookies)

                    # 1. Guardar/Actualizar en la Base de Datos
                    c.execute("""
                        UPDATE cuentas 
                        SET cookies = ?
                        WHERE alias = ?
                    """, (cookies_json_str, alias))

                    # 2. Guardar/Actualizar archivo .json local
                    archivo_json = f"{alias}.json"
                    with open(archivo_json, "w", encoding="utf-8") as f:
                        json.dump(cookies, f, indent=4)

                    print(f"  ✅ Cookies extraídas y guardadas para: {alias} ({len(cookies)} cookies)")
                    actualizadas += 1
                else:
                    print(f"  ⚠️ El perfil {alias} no tiene cookies guardadas.")

            except Exception as e:
                print(f"  ❌ Error al leer el perfil {alias}: {e}")

    conn.commit()
    conn.close()

    print("="*65)
    print(f"✅ Extracción completada. {actualizadas} cuentas actualizadas en la BD.")
    print("="*65 + "\n")

if __name__ == "__main__":
    extraer_cookies_de_perfiles_fisicos()
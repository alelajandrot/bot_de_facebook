import sqlite3
import json

def mostrar_cuentas_activas():
    # Conectarse a la base de datos
    conn = sqlite3.connect('cuentas.db')
    c = conn.cursor()
    
    # Traer todos los datos necesarios
    c.execute('SELECT alias, username, password, platform, cookies FROM cuentas ORDER BY platform, alias')
    cuentas = c.fetchall()
    
    print("\n" + "="*60)
    print("🚀 CUENTAS CON COOKIES ACTIVAS (LISTAS PARA USAR)")
    print("="*60)
    
    contador = 0
    for alias, username, password, platform, cookies in cuentas:
        # Verificar si realmente tiene cookies guardadas
        tiene_cookies = False
        if cookies:
            try:
                cookies_list = json.loads(cookies)
                if isinstance(cookies_list, list) and len(cookies_list) > 0:
                    tiene_cookies = True
            except:
                pass
                
        # Si tiene cookies, lo imprimimos en pantalla
        if tiene_cookies:
            contador += 1
            red_social = platform.upper() if platform else "DESCONOCIDA"
            print(f"📱 Red Social : {red_social}")
            print(f"🏷️ Alias      : {alias}")
            print(f"👤 Usuario    : {username}")
            print(f"🔑 Contraseña : {password}")
            print("-" * 60)
            
    print(f"✅ Total de cuentas listas y activas: {contador}\n")
    conn.close()

if __name__ == '__main__':
    mostrar_cuentas_activas()
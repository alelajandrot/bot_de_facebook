import time
from mobile_manager import (
    get_connected_devices, 
    get_device_public_ip, 
    toggle_mobile_data, 
    debug_tap
)

def probar_celular_e_ip():
    print("🚀 Iniciando prueba de control y rotación de IP...")
    
    # 1. Detectar el celular
    devices = get_connected_devices()
    if not devices:
        print("❌ No se detectaron celulares. Asegúrate de tener la 'Depuración USB' activada y el cable conectado al PC.")
        return
    
    device_id = devices[0]
    print(f"📱 Celular conectado con ID: {device_id}")

    # 2. Comprobar la IP pública inicial
    print("🔍 Obteniendo IP actual a través de la red móvil...")
    ip_original = get_device_public_ip(device_id)
    print(f"🌐 IP Original: {ip_original}")

    # 3. Mandar un toque de prueba (coordenadas X=500, Y=1000)
    print("👆 Enviando toque a la pantalla (Coordenadas: 500, 1000)...")
    debug_tap(device_id, 500, 1000)

    # 4. Apagar datos, esperar, y encender datos (Rotar IP)
    print("🔄 Apagando datos móviles...")
    toggle_mobile_data(device_id, enable=False)
    time.sleep(5) # Esperamos a que la antena corte la conexión
    
    print("🔄 Encendiendo datos móviles...")
    toggle_mobile_data(device_id, enable=True)
    
    # Le damos 15 segundos al 4G/5G para que vuelva a negociar una IP con la operadora
    print("⏳ Esperando 15 segundos para que la red se estabilice...")
    time.sleep(15) 

    # 5. Comprobar la IP nueva
    print("🔍 Obteniendo IP nueva...")
    ip_nueva = get_device_public_ip(device_id)
    print(f"🌐 IP Nueva: {ip_nueva}")

    # 6. Veredicto
    print("-" * 30)
    if ip_original and ip_nueva and ip_original != ip_nueva:
        print("✅ ¡ÉXITO! El PC controló el celular y la IP cambió correctamente.")
    elif ip_original == ip_nueva:
        print("⚠️ La IP es la misma. \nNota: Algunas operadoras (CGNAT) tardan más en soltar la IP. Intenta subir el tiempo de espera de 5 a 60 segundos con los datos apagados.")
    else:
        print("❌ Hubo un error al leer las IPs. Revisa que el celular tenga saldo/datos y la pantalla esté desbloqueada.")

if __name__ == "__main__":
    probar_celular_e_ip()adb version
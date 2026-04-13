import subprocess
import time

def toggle_airplane_mode(enable: bool):
    """Activa o desactiva el Modo Avión usando comandos nativos de Android (ADB)"""
    state = "1" if enable else "0"
    broadcast_state = "true" if enable else "false"
    
    # 1. Cambia la configuración interna del teléfono
    subprocess.run(["adb", "shell", "settings", "put", "global", "airplane_mode_on", state])
    # 2. Le avisa a la antena para que ejecute el cambio inmediatamente
    subprocess.run(["adb", "shell", "am", "broadcast", "-a", "android.intent.action.AIRPLANE_MODE", "--ez", "state", broadcast_state])

def forzar_datos_moviles():
    """Se asegura de que los datos móviles queden encendidos"""
    subprocess.run(["adb", "shell", "svc", "data", "enable"])

if __name__ == "__main__":
    print("✈️ Activando Modo Avión (Cortando señal)...")
    toggle_airplane_mode(True)
    
    # Pausa de 10 segundos para que la operadora libere tu IP anterior
    print("⏳ Esperando 10 segundos...")
    time.sleep(10)
    
    print("📡 Desactivando Modo Avión...")
    toggle_airplane_mode(False)
    
    print("📶 Asegurando que los datos móviles estén encendidos...")
    forzar_datos_moviles()
    
    print("✅ ¡Listo! Proceso terminado. Revisa tu celular.")
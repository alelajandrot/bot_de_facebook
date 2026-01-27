"""
Módulo para gestión de dispositivos móviles Android vía ADB
Permite usar celulares físicos como proxies rotativos
"""
import subprocess
import time
import threading
import json
import os
from typing import Optional, Dict, List

# ==============================================================================
# CONFIGURACIÓN DE DISPOSITIVOS
# ==============================================================================
# Mapeo de Device ID (ADB) a IP:Puerto del proxy local
# Formato: "device_id": "ip:puerto"
# Ejemplo: "R58M123456": "192.168.1.10:8080"
DEVICE_PROXY_MAP = {
    # Ejemplo - Reemplaza con tus dispositivos reales
    # "R58M123456": "192.168.1.10:8080",
    # "emulator-5554": "192.168.1.11:8080",
}

# Archivo JSON alternativo para configuración
DEVICE_CONFIG_FILE = "mobile_devices.json"

# ==============================================================================
# GESTIÓN DE BLOQUEOS (Thread-Safe)
# ==============================================================================
class DeviceLock:
    """Gestiona el bloqueo de dispositivos para uso concurrente"""
    def __init__(self):
        self._locks: Dict[str, threading.Lock] = {}
        self._in_use: Dict[str, bool] = {}
        self._lock_manager = threading.Lock()
    
    def _ensure_lock(self, device_id: str):
        """Asegura que existe un lock para el dispositivo"""
        with self._lock_manager:
            if device_id not in self._locks:
                self._locks[device_id] = threading.Lock()
                self._in_use[device_id] = False
    
    def acquire_device(self, device_id: str, timeout: float = 30.0) -> bool:
        """Intenta adquirir un dispositivo. Retorna True si tuvo éxito"""
        self._ensure_lock(device_id)
        lock = self._locks[device_id]
        
        acquired = lock.acquire(timeout=timeout)
        if acquired:
            with self._lock_manager:
                self._in_use[device_id] = True
        return acquired
    
    def release_device(self, device_id: str):
        """Libera un dispositivo"""
        self._ensure_lock(device_id)
        with self._lock_manager:
            self._in_use[device_id] = False
        self._locks[device_id].release()
    
    def is_device_available(self, device_id: str) -> bool:
        """Verifica si un dispositivo está disponible"""
        with self._lock_manager:
            return not self._in_use.get(device_id, False)

# Instancia global del gestor de bloqueos
_device_lock = DeviceLock()

# ==============================================================================
# FUNCIONES ADB
# ==============================================================================

def check_adb_available() -> bool:
    """Verifica si ADB está disponible en el sistema"""
    try:
        result = subprocess.run(
            ["adb", "version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        return False

def get_connected_devices() -> List[str]:
    """
    Obtiene la lista de dispositivos Android conectados vía USB
    Retorna lista de Device IDs
    """
    try:
        result = subprocess.run(
            ["adb", "devices"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            return []
        
        devices = []
        for line in result.stdout.strip().split('\n')[1:]:  # Saltar header
            if line.strip() and '\tdevice' in line:
                device_id = line.split('\t')[0].strip()
                if device_id:
                    devices.append(device_id)
        
        return devices
    except (subprocess.TimeoutExpired, Exception) as e:
        print(f"Error obteniendo dispositivos ADB: {e}")
        return []

def toggle_airplane_mode(device_id: str, enable: bool = True) -> bool:
    """
    Activa o desactiva el Modo Avión en un dispositivo Android
    enable=True: Activa Modo Avión (ON)
    enable=False: Desactiva Modo Avión (OFF)
    """
    try:
        # Comando para activar/desactivar modo avión
        # Usamos settings put global airplane_mode_on
        state = "1" if enable else "0"
        
        # Activar/Desactivar modo avión
        cmd1 = subprocess.run(
            ["adb", "-s", device_id, "shell", "settings", "put", "global", 
             "airplane_mode_on", state],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if cmd1.returncode != 0:
            return False
        
        # Enviar broadcast para aplicar cambios
        cmd2 = subprocess.run(
            ["adb", "-s", device_id, "shell", "am", "broadcast", "-a", 
             "android.intent.action.AIRPLANE_MODE", "--ez", "state", state],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        return cmd2.returncode == 0
    except (subprocess.TimeoutExpired, Exception) as e:
        print(f"Error cambiando modo avión en {device_id}: {e}")
        return False

def wait_for_internet(device_id: str, timeout: int = 30) -> bool:
    """
    Espera a que el dispositivo tenga conexión a internet
    Verifica haciendo ping a un servidor público
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            # Verificar conectividad con ping a Google DNS
            result = subprocess.run(
                ["adb", "-s", device_id, "shell", "ping", "-c", "1", "-W", "2", "8.8.8.8"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                return True
            
            time.sleep(2)
        except Exception:
            time.sleep(2)
    
    return False

def renew_device_ip(device_id: str, wait_time: int = 5) -> bool:
    """
    Renueva la IP pública del dispositivo activando y desactivando Modo Avión
    wait_time: Segundos de espera entre activar y desactivar
    """
    # Activar modo avión
    if not toggle_airplane_mode(device_id, enable=True):
        return False
    
    time.sleep(wait_time)
    
    # Desactivar modo avión
    if not toggle_airplane_mode(device_id, enable=False):
        return False
    
    # Esperar a que tenga internet
    return wait_for_internet(device_id, timeout=30)

# ==============================================================================
# GESTIÓN DE CONFIGURACIÓN
# ==============================================================================

def load_device_config() -> Dict[str, str]:
    """Carga la configuración de dispositivos desde archivo JSON"""
    global DEVICE_PROXY_MAP
    
    if os.path.exists(DEVICE_CONFIG_FILE):
        try:
            with open(DEVICE_CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                DEVICE_PROXY_MAP.update(config)
                return config
        except Exception as e:
            print(f"Error cargando configuración de dispositivos: {e}")
    
    return DEVICE_PROXY_MAP

def save_device_config(config: Dict[str, str]):
    """Guarda la configuración de dispositivos en archivo JSON"""
    try:
        with open(DEVICE_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error guardando configuración de dispositivos: {e}")
        return False

# Cargar configuración al importar
load_device_config()

# ==============================================================================
# GESTIÓN DE DISPOSITIVOS (API PRINCIPAL)
# ==============================================================================

class MobileDeviceManager:
    """Gestor principal de dispositivos móviles"""
    
    def __init__(self, logger=None):
        self.logger = logger or print
        self.device_proxy_map = DEVICE_PROXY_MAP.copy()
    
    def log(self, message: str, level: str = "INFO"):
        """Wrapper para logging"""
        if callable(self.logger):
            self.logger(message, level)
        else:
            print(f"[{level}] {message}")
    
    def get_available_devices(self) -> List[str]:
        """Obtiene dispositivos conectados que están configurados"""
        connected = get_connected_devices()
        configured = [d for d in connected if d in self.device_proxy_map]
        return configured
    
    def get_device_proxy(self, device_id: str) -> Optional[str]:
        """Obtiene la configuración de proxy para un dispositivo"""
        return self.device_proxy_map.get(device_id)
    
    def acquire_device_with_proxy(self, timeout: float = 60.0) -> Optional[Dict[str, str]]:
        """
        Adquiere un dispositivo libre y retorna su información
        Retorna: {"device_id": "...", "proxy": "ip:puerto"} o None
        """
        available = self.get_available_devices()
        
        if not available:
            self.log("No hay dispositivos móviles disponibles", "WARN")
            return None
        
        # Intentar adquirir cualquier dispositivo disponible
        for device_id in available:
            if _device_lock.acquire_device(device_id, timeout=timeout):
                proxy = self.get_device_proxy(device_id)
                if proxy:
                    self.log(f"Dispositivo adquirido: {device_id} (Proxy: {proxy})", "INFO")
                    return {
                        "device_id": device_id,
                        "proxy": proxy
                    }
                else:
                    _device_lock.release_device(device_id)
        
        self.log("No se pudo adquirir ningún dispositivo (todos en uso)", "WARN")
        return None
    
    def release_device(self, device_id: str):
        """Libera un dispositivo"""
        _device_lock.release_device(device_id)
        self.log(f"Dispositivo liberado: {device_id}", "INFO")
    
    def renew_ip_and_get_proxy(self, device_id: str, wait_time: int = 5) -> Optional[str]:
        """
        Renueva la IP del dispositivo y retorna su proxy
        Retorna la cadena de proxy o None si falla
        """
        self.log(f"Renovando IP para dispositivo: {device_id}", "INFO")
        
        if renew_device_ip(device_id, wait_time=wait_time):
            proxy = self.get_device_proxy(device_id)
            self.log(f"IP renovada exitosamente. Proxy: {proxy}", "SUCCESS")
            return proxy
        else:
            self.log(f"Error renovando IP para {device_id}", "ERROR")
            return None

# Instancia global del gestor
_mobile_manager = None

def get_mobile_manager(logger=None) -> MobileDeviceManager:
    """Obtiene la instancia global del gestor móvil"""
    global _mobile_manager
    if _mobile_manager is None:
        _mobile_manager = MobileDeviceManager(logger=logger)
    return _mobile_manager


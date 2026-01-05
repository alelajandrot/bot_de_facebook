import time
import random
import os
from PIL import Image

def human_sleep(a=2, b=5):
    """Espera un tiempo aleatorio entre a y b segundos"""
    time.sleep(random.uniform(a, b))

def simulate_human_behavior(page):
    """Movimientos aleatorios de mouse y scroll para engañar al sistema anti-bot"""
    try:
        # Scroll aleatorio
        for _ in range(random.randint(1, 3)):
            page.mouse.wheel(0, random.randint(200, 800))
            time.sleep(random.uniform(0.5, 1.5))
        
        # Movimiento de mouse no lineal
        w = page.viewport_size['width']
        h = page.viewport_size['height']
        page.mouse.move(random.randint(100, w-100), random.randint(100, h-100), steps=15)
    except: pass

def save_screenshot_log(page, alias, action_name):
    """Guarda captura y retorna la ruta para la UI"""
    if not os.path.exists("logs"): os.makedirs("logs")
    ts = int(time.time())
    path = f"logs/{action_name}_{alias}_{ts}.png"
    try:
        page.screenshot(path=path)
        # Guardamos una copia fija para la vista previa inmediata en la UI
        page.screenshot(path="logs/preview_last.png") 
        return path
    except: return None
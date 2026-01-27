import time
import random
import os
import math
from PIL import Image

def human_sleep(a=2, b=5):
    """Espera un tiempo aleatorio entre a y b segundos"""
    time.sleep(random.uniform(a, b))

def _cubic_bezier(p0, p1, p2, p3, t):
    """Evalúa punto en curva cúbica de Bézier para parámetro t en [0,1]."""
    u = 1 - t
    tt = t * t
    uu = u * u
    uuu = uu * u
    ttt = tt * t
    x = uuu * p0[0] + 3 * uu * t * p1[0] + 3 * u * tt * p2[0] + ttt * p3[0]
    y = uuu * p0[1] + 3 * uu * t * p1[1] + 3 * u * tt * p2[1] + ttt * p3[1]
    return (x, y)

def _ease_in_out_cubic(t):
    """Easing para simular aceleración/desaceleración humana."""
    if t < 0.5:
        return 4 * t * t * t
    else:
        return 1 - pow(-2 * t + 2, 3) / 2

def simulate_human_behavior(page):
    """Movimientos humanos del mouse usando curvas de Bézier + scroll aleatorio.

    Genera trayectorias suaves con control aleatorio y aplica easing para
    acelerar/desacelerar al inicio/fin. Llama a `page.mouse.move` paso a paso
    para reproducir el movimiento.
    """
    try:
        # Scroll aleatorio pequeño/mediano
        for _ in range(random.randint(1, 3)):
            page.mouse.wheel(0, random.randint(150, 700))
            time.sleep(random.uniform(0.4, 1.2))

        w = page.viewport_size.get('width', 1024)
        h = page.viewport_size.get('height', 768)

        # Punto de inicio (aleatorio en área central) y fin (zona objetivo aleatoria)
        start = (random.randint(int(w * 0.25), int(w * 0.75)), random.randint(int(h * 0.25), int(h * 0.75)))
        end = (random.randint(50, w - 50), random.randint(50, h - 50))

        # Controles aleatorios para darle curva (alejar ligeramente de la línea recta)
        def jitter_point(p):
            return (p[0] + random.uniform(-w * 0.12, w * 0.12), p[1] + random.uniform(-h * 0.12, h * 0.12))

        ctrl1 = jitter_point(((start[0] + end[0]) / 2, start[1] + random.uniform(-h * 0.15, h * 0.15)))
        ctrl2 = jitter_point(((start[0] + end[0]) / 2, end[1] + random.uniform(-h * 0.15, h * 0.15)))

        # Número de pasos basado en distancia
        dist = math.hypot(end[0] - start[0], end[1] - start[1])
        steps = int(min(max(dist / 5, 16), 120))  # entre 16 y 120 pasos

        # Velocidad base (pausa entre pasos) con variación
        base_delay = random.uniform(0.003, 0.02)

        for i in range(steps + 1):
            t = i / steps
            eased_t = _ease_in_out_cubic(t)
            x, y = _cubic_bezier(start, ctrl1, ctrl2, end, eased_t)

            # Añadir micro-jitter para evitar trayectorias demasiado perfectas
            jitter_x = x + random.uniform(-0.5, 0.5)
            jitter_y = y + random.uniform(-0.5, 0.5)
            try:
                page.mouse.move(int(jitter_x), int(jitter_y))
            except Exception:
                # Algunos contextos pueden requerir pasos; intentamos con steps=1
                try:
                    page.mouse.move(int(jitter_x), int(jitter_y), steps=1)
                except Exception:
                    pass

            # Pausa que simula velocidad variable (más lenta al inicio/fin)
            time.sleep(base_delay * (0.5 + random.random()))

        # Pequeña pausa final
        time.sleep(random.uniform(0.05, 0.25))
    except Exception:
        pass

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
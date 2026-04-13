import time
import random
import math
from PIL import Image
import pandas as pd
from datetime import datetime
import os

def human_sleep(min_time=2, max_time=5):
    """
    Espera un tiempo emulando el comportamiento humano real usando una Distribución Normal.
    La mayoría de las pausas ocurren cerca del promedio, con ocasionales 'distracciones'.
    """
    # 1. Calculamos la media (el pico de la campana)
    mu = (min_time + max_time) / 2.0
    
    # 2. Calculamos la desviación estándar
    # Dividir entre 6 asegura que el ~99.7% de los casos caigan dentro de tu rango original
    sigma = (max_time - min_time) / 6.0
    
    # 3. Generamos el tiempo usando la campana de Gauss
    sleep_time = random.gauss(mu, sigma)
    
    # 4. Control de límites (evitar tiempos negativos o matemáticamente absurdos)
    # Permitimos que sea un poco más rápido o un poco más lento que los límites originales
    sleep_time = max(min_time * 0.7, min(sleep_time, max_time * 1.3))
    
    # 5. Simulación de "Micro-distracciones" humanas
    # Hay un 5% de probabilidad de que el "usuario" se distraiga leyendo un mensaje, tomando agua, etc.
    if random.random() < 0.05:
        distraction = random.uniform(2.5, 7.5)
        # Opcional: imprimir en consola si quieres ver cuándo se distrae tu bot
        # print(f"☕ [Comportamiento Humano] Distracción simulada... añadiendo {distraction:.1f}s")
        sleep_time += distraction

    time.sleep(sleep_time)

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
                except Exception as e:
                    print(f"⚠️ Error al mover el mouse a {jitter_x},{jitter_y}: {e}")

            # Pausa que simula velocidad variable (más lenta al inicio/fin)
            time.sleep(base_delay * (0.5 + random.random()))

        # Pequeña pausa final
        time.sleep(random.uniform(0.05, 0.25))
    except Exception as e:
        # Este es el error global por si Playwright falla de forma general, no usamos jitter_x/y aquí.
        print(f"⚠️ Error general simulando comportamiento humano: {e}")

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
    except Exception as e:
        print(f"⚠️ Error al guardar captura de pantalla ({action_name}): {e}")
        return None

def exportar_cuenta_excel(alias, network, username, password, status="Creada"):
    """Guarda los datos de una cuenta nueva en un archivo Excel para llevar el control."""
    archivo = "cuentas_creadas.xlsx"
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Creamos la fila con los datos
    nueva_fila = pd.DataFrame([{
        "Alias": alias,
        "Red Social": network.capitalize(),
        "Usuario/Email": username,
        "Contraseña": password,
        "Estado": status,
        "Fecha de Creación": fecha
    }])
    
    try:
        # Si el archivo ya existe, lo abrimos y le agregamos la fila al final
        if os.path.exists(archivo):
            df = pd.read_excel(archivo)
            # Evitar usar append (está deprecado en pandas nuevos), usamos concat
            df = pd.concat([df, nueva_fila], ignore_index=True)
        else:
            # Si no existe, creamos el documento desde cero
            df = nueva_fila
        
        # Guardamos el archivo sin la columna de índices
        df.to_excel(archivo, index=False)
        print(f"📊 Cuenta '{alias}' exportada a Excel exitosamente.")
        return True
    except Exception as e:
        print(f"⚠️ Error exportando a Excel: {e}")
        return False
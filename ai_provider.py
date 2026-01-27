import json
import random
import urllib.request
import urllib.error

def _ollama_generate(prompt, model="llama3", timeout=60):
    """
    Llama al servidor local de Ollama.
    NOTA: 'stream': False es vital para recibir un JSON completo.
    """
    url = "http://127.0.0.1:11434/api/generate"
    
    # Payload corregido para desactivar streaming
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False 
    }
    
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
            obj = json.loads(body)
            # Ollama devuelve el texto en el campo 'response'
            return obj.get("response", "")
            
    except Exception as e:
        print(f"[IA Error] No se pudo conectar con Ollama: {e}")
        return None

def generate_comment_from_text(text, model="local_fallback", use_vision=False):
    """Genera un comentario basado en el texto del post."""
    
    # Prompt diseñado para redes sociales
    prompt = f"Actúa como un usuario de redes sociales relajado. Genera un comentario corto (máximo 15 palabras), positivo y natural para este post: '{text}'. Solo devuelve el comentario, sin comillas ni explicaciones."
    
    # 1. Intentar usar Ollama si se seleccionó
    if model and "ollama" in model.lower():
        # Asegúrate de que el nombre del modelo coincida con el que descargaste (llama3 o llama3.2)
        modelo_real = "llama3" 
        respuesta = _ollama_generate(prompt, model=modelo_real)
        if respuesta:
            return respuesta.strip()

    # 2. Fallback (Respaldo) si Ollama falla o no está seleccionado
    snippets = [
        "¡Qué buena publicación!",
        "Me encanta, gracias por compartir 😊",
        "¡Se ve genial!", 
        "Muy buen contenido, sigue así 💯",
        "Esto me alegró el día 😄"
    ]
    return random.choice(snippets)

def caption_from_image_url(image_url):
    """(Opcional) Si tienes el modelo llava instalado para ver imágenes"""
    if not image_url: return "¡Qué foto tan bonita!"
    # Lógica simple por nombre de archivo mientras tanto
    name = image_url.split('/')[-1].lower()
    if any(x in name for x in ["coffee","cafe"]): return "¡Qué rico café! ☕️"
    return "¡Excelente foto!"
import psycopg2
from psycopg2.extras import RealDictCursor

# CONFIGURACIÓN DE TU SERVIDOR (Si es local usa 'localhost', si es remoto usa la IP)
DB_CONFIG = {
    "dbname": "usuario_bots",
    "user": "postgres",
    "password": "Solocali",
    "host": "localhost", 
    "port": "5432"
}

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

def validar_usuario_app(user, password):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT rol, permisos FROM usuarios_app WHERE usuario=%s AND password=%s", (user, password))
    res = cur.fetchone()
    cur.close()
    conn.close()
    return res # Retorna un diccionario con rol y permisos

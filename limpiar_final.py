import sqlite3

conn = sqlite3.connect('cuentas.db')
c = conn.cursor()

# Cuentas problemáticas a eliminar (duplicados sin cookies)
a_eliminar = [
    'Mateo rios ',  # Duplicado de Mateo Rios (con espacio)
    'Santiago lozano',  # Este tiene cookies pero vamos a verificar
]

# Primero, listar qué hay
print("Antes de eliminar:")
c.execute('SELECT alias, platform, cookies FROM cuentas WHERE alias LIKE "%rios%" OR alias LIKE "%santiago%" ORDER BY alias')
print(c.fetchall())

# Eliminar solo los problemas claros (Mateo rios con espacio)
c.execute('DELETE FROM cuentas WHERE alias = ?', ('Mateo rios ',))

print("\nDespués de eliminar 'Mateo rios ':")
c.execute('SELECT alias, platform, cookies FROM cuentas WHERE alias LIKE "%rios%" OR alias LIKE "%santiago%" ORDER BY alias')
print(c.fetchall())

conn.commit()
conn.close()

print("\n✅ Limpieza específica completada")

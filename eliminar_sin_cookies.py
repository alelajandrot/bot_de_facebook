import sqlite3

conn = sqlite3.connect('cuentas.db')
c = conn.cursor()

# Eliminar cuentas sin cookies que son duplicados
c.execute('DELETE FROM cuentas WHERE alias = ? AND cookies IS NULL', ('Santiago lozano',))

print("Eliminada: 'Santiago lozano' (sin cookies)")

conn.commit()

# Verificar resultado final
c.execute('SELECT alias, platform FROM cuentas ORDER BY alias')
cuentas = c.fetchall()

print(f"\nCuentas finales: {len(cuentas)}")
for alias, platform in cuentas:
    print(f"  '{alias}' - {platform}")

conn.close()
print("\n✅ Completado")

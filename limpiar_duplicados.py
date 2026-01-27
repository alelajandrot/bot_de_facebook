import sqlite3

conn = sqlite3.connect('cuentas.db')
c = conn.cursor()

# Obtener todas las cuentas
c.execute('SELECT alias, platform FROM cuentas ORDER BY alias')
todas = c.fetchall()

print("Analizando duplicados (ignorando mayúsculas/minúsculas y mismo platform)...")

# Agrupar por (alias_lower, platform)
grupo = {}
for alias, platform in todas:
    key = (alias.lower(), platform.lower())
    if key not in grupo:
        grupo[key] = []
    grupo[key].append(alias)

a_eliminar = []
for (alias_lower, platform), variantes in grupo.items():
    if len(variantes) > 1:
        print(f"\n⚠️ Duplicado encontrado para '{alias_lower}' ({platform}):")
        for i, alias in enumerate(variantes):
            print(f"  {i+1}. '{alias}'")
        # Mantener el primero, marcar los demás para eliminar
        for alias in variantes[1:]:
            print(f"     -> Eliminando '{alias}'")
            a_eliminar.append(alias)

if a_eliminar:
    print(f"\n🗑️ Eliminando {len(a_eliminar)} duplicados...")
    for alias in a_eliminar:
        c.execute('DELETE FROM cuentas WHERE alias = ?', (alias,))
    conn.commit()
else:
    print("\n✅ No hay duplicados por diferenciar (mayúsculas/minúsculas)")

# Mostrar cuentas finales
c.execute('SELECT alias, platform FROM cuentas ORDER BY alias')
finales = c.fetchall()
print("\nCuentas finales en la BD:")
print("="*50)
for alias, platform in finales:
    print(f"  '{alias}' - {platform}")

print(f"\nTotal: {len(finales)} cuentas")
conn.close()

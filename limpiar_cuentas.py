import sqlite3

conn = sqlite3.connect('cuentas.db')
c = conn.cursor()

# Obtener todas las cuentas
c.execute('SELECT alias, platform FROM cuentas')
todas = c.fetchall()

print("Cuentas antes de limpiar:")
for alias, platform in todas:
    print(f"  '{alias}' - {platform}")

# Crear lista de alias a eliminar
a_eliminar = []

# Limpiar espacios en blanco al inicio y final del alias
alias_mapeados = {}  # Mapeo de alias sucio -> alias limpio
for alias, platform in todas:
    alias_limpio = alias.strip()
    if alias != alias_limpio:
        print(f"\n⚠️ Limpiando espacios: '{alias}' -> '{alias_limpio}'")
        a_eliminar.append(alias)
        # Guardar para después actualizar cookies del limpio si existe
        alias_mapeados[alias_limpio] = alias
    
# Eliminar cuentas con espacios
for alias_sucio in a_eliminar:
    print(f"  Eliminando '{alias_sucio}'")
    c.execute('DELETE FROM cuentas WHERE alias = ?', (alias_sucio,))

conn.commit()

# Ahora buscar duplicados (mismo alias pero casos diferentes, etc)
c.execute('SELECT alias, platform FROM cuentas ORDER BY alias')
todas_limpias = c.fetchall()

alias_dict = {}
for alias, platform in todas_limpias:
    alias_lower = alias.lower()
    if alias_lower not in alias_dict:
        alias_dict[alias_lower] = []
    alias_dict[alias_lower].append((alias, platform))

duplicados_encontrados = {k: v for k, v in alias_dict.items() if len(v) > 1}
if duplicados_encontrados:
    print("\nCuentas duplicadas encontradas:")
    for alias_lower, variantes in duplicados_encontrados.items():
        print(f"  '{alias_lower}':")
        for i, (alias, platform) in enumerate(variantes):
            print(f"    {i+1}. '{alias}' - {platform}")
        # Mantener el primero, eliminar los demás
        for alias, _ in variantes[1:]:
            print(f"       Eliminando '{alias}'")
            c.execute('DELETE FROM cuentas WHERE alias = ?', (alias,))
else:
    print("\nNo hay duplicados después de limpiar")

conn.commit()

# Mostrar cuentas finales
c.execute('SELECT alias, platform FROM cuentas ORDER BY alias')
finales = c.fetchall()
print("\nCuentas después de limpiar:")
for alias, platform in finales:
    print(f"  '{alias}' - {platform}")

conn.close()
print("\n✅ Base de datos limpiada correctamente")

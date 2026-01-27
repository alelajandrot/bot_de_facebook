import sqlite3

conn = sqlite3.connect('cuentas.db')
c = conn.cursor()

# Obtener todas las cuentas
c.execute('SELECT alias, platform FROM cuentas')
todas = c.fetchall()

print("Cuentas antes de limpiar espacios en blanco:")
for alias, platform in todas:
    print(f"  {repr(alias)} - {platform}")

# Limpiar todos los espacios en blanco problemáticos
cambios = []
for alias, platform in todas:
    # Limpiar: saltos de línea, espacios múltiples, espacios al inicio/final
    alias_limpio = alias.replace('\n', ' ').replace('\r', '').replace('\t', ' ')
    # Remover espacios múltiples
    while '  ' in alias_limpio:
        alias_limpio = alias_limpio.replace('  ', ' ')
    alias_limpio = alias_limpio.strip()
    
    if alias != alias_limpio:
        print(f"\n🧹 Limpiando: {repr(alias)} -> {repr(alias_limpio)}")
        cambios.append((alias, alias_limpio))
        
        # Verificar si el alias limpio ya existe
        c.execute('SELECT alias FROM cuentas WHERE alias = ?', (alias_limpio,))
        if c.fetchone():
            print(f"   ⚠️ '{alias_limpio}' ya existe, eliminando el duplicado")
            c.execute('DELETE FROM cuentas WHERE alias = ?', (alias,))
        else:
            # Actualizar el alias
            c.execute('UPDATE cuentas SET alias = ? WHERE alias = ?', (alias_limpio, alias))

conn.commit()

# Mostrar cuentas finales
c.execute('SELECT alias, platform FROM cuentas ORDER BY alias')
finales = c.fetchall()
print("\n\nCuentas después de limpiar:")
for alias, platform in finales:
    print(f"  {repr(alias)} - {platform}")

print(f"\n✅ Limpieza completada. {len(cambios)} cambios realizados")
conn.close()

import sqlite3
import json
import os

DB = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cuentas.db')
OUT = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs', 'cuentas_dump.json')

if not os.path.exists(DB):
    print('NO_DB')
    raise SystemExit(1)

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
c = conn.cursor()

c.execute('PRAGMA table_info(cuentas)')
cols = [r['name'] for r in c.fetchall()]

c.execute('SELECT * FROM cuentas')
rows = [dict(r) for r in c.fetchall()]
conn.close()

# Try to parse cookies field
for r in rows:
    if r.get('cookies'):
        try:
            r['cookies_parsed'] = json.loads(r['cookies'])
        except Exception:
            r['cookies_parsed'] = None
    else:
        r['cookies_parsed'] = None

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump({'columns': cols, 'rows': rows}, f, indent=2, ensure_ascii=False)

print(OUT)

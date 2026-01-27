import sqlite3
import json
import os

DB = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cuentas.db")
OUT_JSON = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs", "accounts_by_platform.json")

if not os.path.exists(DB):
    print(f"No se encontró DB: {DB}")
    exit(1)

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
c = conn.cursor()

c.execute("SELECT alias, platform, cookies, username, last_used FROM cuentas ORDER BY platform, alias")
rows = c.fetchall()
conn.close()

grouped = {}

for r in rows:
    platform = (r["platform"] or "unknown").lower()
    alias = r["alias"]
    username = r["username"]
    last_used = r["last_used"]
    cookies_raw = r["cookies"]
    cookie_names = []
    if cookies_raw:
        try:
            cookies = json.loads(cookies_raw)
            if isinstance(cookies, list):
                cookie_names = [c.get("name") for c in cookies if isinstance(c, dict) and c.get("name")]
            elif isinstance(cookies, dict):
                cookie_names = list(cookies.keys())
        except Exception:
            cookie_names = ["<parse_error>"]
    else:
        cookie_names = []

    entry = {
        "alias": alias,
        "username": username,
        "last_used": last_used,
        "cookies": cookie_names
    }

    grouped.setdefault(platform, []).append(entry)

# Print human-friendly
for plat, items in grouped.items():
    print(f"== Platform: {plat} ({len(items)} accounts) ==")
    for it in items:
        ck = ", ".join(it['cookies']) if it['cookies'] else "<no cookies>"
        print(f"- {it['alias']} | user={it['username']} | last_used={it['last_used']} | cookies={ck}")
    print()

# Save JSON for later
os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
with open(OUT_JSON, "w", encoding="utf-8") as f:
    json.dump(grouped, f, indent=2, ensure_ascii=False)

print(f"Listado guardado en: {OUT_JSON}")

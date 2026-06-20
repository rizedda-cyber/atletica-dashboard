"""
debug_foto.py — DIAGNOSTICO, sola lettura. Non modifica nulla.
Serve a capire perche' randomizza_foto.py dava 404.

Lancialo con:  python debug_foto.py
"""
import os
from pathlib import Path
from supabase import create_client

BUCKET = "foto-atleti"


def carica_credenziali():
    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_KEY", "")
    if url and key:
        return url, key, "env"
    secrets_path = Path(__file__).parent / ".streamlit" / "secrets.toml"
    if secrets_path.exists():
        try:
            import tomllib
            data = tomllib.loads(secrets_path.read_text(encoding="utf-8"))
        except Exception:
            try:
                import toml
                data = toml.loads(secrets_path.read_text(encoding="utf-8"))
            except Exception:
                data = {}
        sec = data.get("secrets", data)
        return sec.get("SUPABASE_URL", ""), sec.get("SUPABASE_KEY", ""), "secrets.toml"
    return "", "", "nessuna"


def path_da_url(url: str):
    if not url or f"/{BUCKET}/" not in url:
        return None
    return url.split(f"/{BUCKET}/", 1)[1].split("?", 1)[0]


url, key, fonte = carica_credenziali()
print(f"Credenziali da: {fonte}")
if not url or not key:
    raise SystemExit("ERRORE: credenziali non trovate.")
# mostra solo la coda della chiave per capire se e' anon o service (senza rivelarla)
print(f"URL progetto: {url}")
print(f"Chiave (ultimi 6): ...{key[-6:]}  lunghezza {len(key)}")

sb = create_client(url, key)

print("\n== 1) Cosa c'e' DAVVERO nel bucket, cartella 'atleti/' ==")
try:
    files = sb.storage.from_(BUCKET).list("atleti")
    print(f"  trovati {len(files)} file:", [f.get('name') for f in files][:20])
except Exception as e:
    print("  errore list:", e)

print("\n== 2) Per i primi 3 atleti con foto: percorso letto e test di lettura ==")
res = sb.table("atleti").select("id, nome_completo, foto_url").execute()
n = 0
for a in (res.data or []):
    p = path_da_url(a.get("foto_url") or "")
    if not p:
        continue
    n += 1
    print(f"\n  {a.get('nome_completo')} (id {a['id']})")
    print(f"    foto_url: {(a.get('foto_url') or '')[:90]}")
    print(f"    percorso calcolato: {p}")
    try:
        b = sb.storage.from_(BUCKET).download(p)
        print(f"    download: OK ({len(b)} byte) -> il percorso e' GIUSTO")
    except Exception as e:
        print(f"    download: FALLITO -> {e}")
    if n >= 3:
        break

print("\n== Fine diagnosi ==")

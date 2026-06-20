"""
randomizza_foto.py — Script UNA TANTUM.

Rinomina le foto degli atleti gia' presenti nel bucket 'foto-atleti' che hanno
un nome PREVEDIBILE (es. atleti/21.jpg = numero dell'atleta) assegnando loro un
nome CASUALE non indovinabile (es. atleti/9f3a...e7.jpg), e aggiorna il link
nel database. Le foto gia' con nome casuale vengono ignorate.

Come si lancia (dalla cartella del progetto):
    python randomizza_foto.py            # prova "a vuoto": mostra cosa farebbe, non cambia nulla
    python randomizza_foto.py --esegui   # esegue davvero

Credenziali: usa SUPABASE_URL / SUPABASE_KEY dalle variabili d'ambiente,
oppure le legge da .streamlit/secrets.toml (sezione [secrets]).
Serve una chiave con permessi di scrittura sullo Storage (la stessa usata per
la migrazione precedente va bene).
"""
import os
import re
import sys
import time
import secrets as _secrets
from pathlib import Path

from supabase import create_client

BUCKET = "foto-atleti"


def carica_credenziali():
    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_KEY", "")
    if url and key:
        return url, key
    # fallback: .streamlit/secrets.toml
    secrets_path = Path(__file__).parent / ".streamlit" / "secrets.toml"
    if secrets_path.exists():
        try:
            import tomllib  # Python 3.11+
            data = tomllib.loads(secrets_path.read_text(encoding="utf-8"))
        except Exception:
            try:
                import toml
                data = toml.loads(secrets_path.read_text(encoding="utf-8"))
            except Exception:
                data = {}
        sec = data.get("secrets", data)
        url = url or sec.get("SUPABASE_URL", "")
        key = key or sec.get("SUPABASE_KEY", "")
    return url, key


def path_da_url(url: str) -> str | None:
    if not url or f"/{BUCKET}/" not in url:
        return None
    return url.split(f"/{BUCKET}/", 1)[1].split("?", 1)[0]


def e_prevedibile(path: str) -> bool:
    # path tipo "atleti/21.jpg" -> nome senza estensione "21" tutto numerico = prevedibile
    base = path.rsplit("/", 1)[-1]
    nome = base.rsplit(".", 1)[0]
    return nome.isdigit()


def main():
    esegui = "--esegui" in sys.argv
    url, key = carica_credenziali()
    if not url or not key:
        print("ERRORE: credenziali Supabase non trovate (env o secrets.toml).")
        sys.exit(1)

    sb = create_client(url, key)
    modo = "ESECUZIONE REALE" if esegui else "PROVA A VUOTO (nessuna modifica)"
    print(f"== Randomizza nomi foto — {modo} ==")

    res = sb.table("atleti").select("id, nome_completo, foto_url").execute()
    atleti = res.data or []

    rinominate = ignorate = errori = 0
    for a in atleti:
        url_foto = a.get("foto_url") or ""
        p = path_da_url(url_foto)
        nome = a.get("nome_completo", f"id {a.get('id')}")
        if not p:
            ignorate += 1  # base64, vuoto o non del bucket
            continue
        if not e_prevedibile(p):
            ignorate += 1  # gia' casuale
            continue
        token = _secrets.token_hex(16)
        nuovo = f"atleti/{token}.jpg"
        if not esegui:
            print(f"  [prova] {nome}: {p} -> {nuovo}")
            rinominate += 1
            continue
        try:
            sb.storage.from_(BUCKET).move(p, nuovo)
            public = sb.storage.from_(BUCKET).get_public_url(nuovo).rstrip("?")
            full = f"{public}?v={int(time.time())}"
            sb.table("atleti").update({"foto_url": full}).eq("id", a["id"]).execute()
            print(f"  OK {nome}: {p} -> {nuovo}")
            rinominate += 1
        except Exception as e:
            print(f"  ERRORE {nome}: {e}")
            errori += 1

    print("\n--- Riepilogo ---")
    print(f"Da rinominare/rinominate: {rinominate}")
    print(f"Ignorate (gia' casuali / senza foto): {ignorate}")
    print(f"Errori: {errori}")
    if not esegui:
        print("\nNessuna modifica fatta. Per eseguire davvero: python randomizza_foto.py --esegui")


if __name__ == "__main__":
    main()

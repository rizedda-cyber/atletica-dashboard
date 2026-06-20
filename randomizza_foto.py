"""
randomizza_foto.py — Script UNA TANTUM (v2, metodo robusto).

Da' alle foto degli atleti un nome di file CASUALE (non indovinabile).
Metodo: scarica la foto dal suo link pubblico (HTTP), la ricarica nel bucket
con un nome casuale, aggiorna il link nel database, e prova a rimuovere il
vecchio file. Non usa 'move' (che dava 404). Le foto gia' casuali sono ignorate.

Lancio (dalla cartella del progetto):
    python randomizza_foto.py            # prova a vuoto (non cambia nulla)
    python randomizza_foto.py --esegui   # esegue davvero
"""
import os
import sys
import time
import secrets as _secrets
import urllib.request
from pathlib import Path

from supabase import create_client

BUCKET = "foto-atleti"


def carica_credenziali():
    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_KEY", "")
    if url and key:
        return url, key
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
        url = url or sec.get("SUPABASE_URL", "")
        key = key or sec.get("SUPABASE_KEY", "")
    return url, key


def path_da_url(url: str):
    if not url or f"/{BUCKET}/" not in url:
        return None
    return url.split(f"/{BUCKET}/", 1)[1].split("?", 1)[0]


def e_prevedibile(path: str) -> bool:
    base = path.rsplit("/", 1)[-1]
    nome = base.rsplit(".", 1)[0]
    return nome.isdigit()


def scarica(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "randomizza-foto"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def main():
    esegui = "--esegui" in sys.argv
    url, key = carica_credenziali()
    if not url or not key:
        print("ERRORE: credenziali Supabase non trovate.")
        sys.exit(1)

    sb = create_client(url, key)
    print(f"== Randomizza nomi foto (v2) — {'ESECUZIONE REALE' if esegui else 'PROVA A VUOTO'} ==")

    res = sb.table("atleti").select("id, nome_completo, foto_url").execute()
    rinominate = ignorate = errori = 0

    for a in (res.data or []):
        url_foto = a.get("foto_url") or ""
        p = path_da_url(url_foto)
        nome = a.get("nome_completo", f"id {a.get('id')}")
        if not p or not e_prevedibile(p):
            ignorate += 1
            continue

        token = _secrets.token_hex(16)
        nuovo = f"atleti/{token}.jpg"
        if not esegui:
            print(f"  [prova] {nome}: {p} -> {nuovo}")
            rinominate += 1
            continue

        try:
            # 1) scarica dal link pubblico (funziona: le foto si vedono nell'app)
            dati = scarica(url_foto)
            # 2) ricarica con nome casuale
            sb.storage.from_(BUCKET).upload(
                nuovo, dati,
                {"content-type": "image/jpeg", "cache-control": "3600"},
            )
            # 3) aggiorna il link nel database
            public = sb.storage.from_(BUCKET).get_public_url(nuovo).rstrip("?")
            full = f"{public}?v={int(time.time())}"
            sb.table("atleti").update({"foto_url": full}).eq("id", a["id"]).execute()
            # 4) prova a rimuovere il vecchio file (se fallisce non blocca)
            try:
                sb.storage.from_(BUCKET).remove([p])
                extra = "(vecchio file rimosso)"
            except Exception:
                extra = "(vecchio file NON rimosso: cancellalo a mano dal bucket)"
            print(f"  OK {nome}: {p} -> {nuovo} {extra}")
            rinominate += 1
        except Exception as e:
            print(f"  ERRORE {nome}: {e}")
            errori += 1

    print("\n--- Riepilogo ---")
    print(f"Rinominate: {rinominate}")
    print(f"Ignorate (gia' casuali / senza foto): {ignorate}")
    print(f"Errori: {errori}")
    if not esegui:
        print("\nProva a vuoto: nessuna modifica. Per eseguire: python randomizza_foto.py --esegui")


if __name__ == "__main__":
    main()

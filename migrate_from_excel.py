"""
migrate_from_excel.py — Script ONE-SHOT per migrare i dati storici Excel → Supabase.

Esecuzione:
    C:\\Users\\rized\\anaconda3\\python.exe migrate_from_excel.py

ATTENZIONE: Eseguire UNA sola volta. Il database Supabase deve avere le tabelle già create.
Esecuzioni successive salteranno i record già presenti (basandosi su data + atleta + distanza/esercizio).
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# ── Setup path per trovare i moduli locali ──────────────────────────────
BASE = Path(__file__).parent
sys.path.insert(0, str(BASE))

import pandas as pd
import numpy as np

from data_loader import load_running_data, load_vbt_data, normalize_names

# Credenziali dirette rimosse per sicurezza
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

def get_client():
    from supabase import create_client
    return create_client(SUPABASE_URL, SUPABASE_KEY)


# ──────────────────────────────────────────────────────────────────────
# UTILITÀ
# ──────────────────────────────────────────────────────────────────────

def log(msg: str, level: str = "INFO"):
    symbols = {"INFO": "  ", "OK": "OK", "WARN": "WW", "ERR": "!!"}
    print(f"[{symbols.get(level, '  ')}] {msg}")


def safe_float(val) -> float | None:
    """Converte in float o None (gestisce NaN)."""
    try:
        v = float(val)
        return None if np.isnan(v) else v
    except (TypeError, ValueError):
        return None


def safe_int(val) -> int | None:
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


# ──────────────────────────────────────────────────────────────────────
# FASE 1 — Inserimento Atleti
# ──────────────────────────────────────────────────────────────────────

def migrate_atleti(supabase, atleti_unici: list[str]) -> dict[str, int]:
    """
    Inserisce tutti gli atleti unici nel database.
    Restituisce un dizionario {nome_completo: id_db} per il mapping.
    """
    log("FASE 1 — Sincronizzazione atleti...")

    # Recupera atleti già esistenti
    existing = supabase.table("atleti").select("id, nome_completo").execute()
    nome_to_id = {r["nome_completo"]: r["id"] for r in (existing.data or [])}
    log(f"  Atleti già presenti nel DB: {len(nome_to_id)}")

    nuovi = 0
    for nome_completo in sorted(atleti_unici):
        if not nome_completo or nome_completo.strip() == "":
            continue
        if nome_completo in nome_to_id:
            continue  # Già presente, skip

        # Separa nome e cognome (ultima parola = cognome se >1 token)
        parts = nome_completo.strip().split()
        if len(parts) >= 2:
            nome = " ".join(parts[:-1])
            cognome = parts[-1]
        else:
            nome = nome_completo
            cognome = ""

        payload = {
            "nome": nome,
            "cognome": cognome,
            "nome_completo": nome_completo,
            "specialita": "",
            "attivo": True
        }
        resp = supabase.table("atleti").insert(payload).execute()
        if resp.data:
            new_id = resp.data[0]["id"]
            nome_to_id[nome_completo] = new_id
            log(f"  + Inserito: {nome_completo} (id={new_id})", "OK")
            nuovi += 1
        else:
            log(f"  Errore inserimento atleta: {nome_completo}", "ERR")

    log(f"  Atleti nuovi inseriti: {nuovi} | Totale disponibili: {len(nome_to_id)}")
    return nome_to_id


# ──────────────────────────────────────────────────────────────────────
# FASE 2 — Migrazione Sessioni Corsa
# ──────────────────────────────────────────────────────────────────────

def migrate_sessioni_corsa(supabase, df_running: pd.DataFrame, nome_to_id: dict) -> int:
    """
    Migra le sessioni di corsa. Inserisce in batch da 500 record.
    Salta i record dove l'atleta non è mappato.
    """
    log("FASE 2 — Migrazione sessioni corsa...")

    # Verifica se ci sono già dati in tabella
    existing_count = supabase.table("sessioni_corsa").select("id", count="exact").execute()
    if existing_count.count and existing_count.count > 0:
        log(f"  [WARN] Trovati {existing_count.count} record gia' presenti.", "WARN")
        risposta = input("  Vuoi procedere comunque aggiungendo i nuovi? (s/N): ").strip().lower()
        if risposta != "s":
            log("  Migrazione corsa saltata per scelta utente.", "WARN")
            return 0

    records = []
    skipped = 0

    for _, row in df_running.iterrows():
        atleta = str(row.get("Atleta", "")).strip()
        atleta_id = nome_to_id.get(atleta)

        if not atleta_id:
            skipped += 1
            continue

        data_val = row.get("Data")
        if pd.isna(data_val):
            skipped += 1
            continue

        distanza = safe_float(row.get("Distanza"))
        tempo = safe_float(row.get("Tempo"))
        if distanza is None or tempo is None:
            skipped += 1
            continue

        nota = str(row.get("Note", "")).strip() if row.get("Note") else ""

        records.append({
            "atleta_id": atleta_id,
            "data": data_val.strftime("%Y-%m-%d"),
            "distanza_m": distanza,
            "tempo_sec": round(tempo, 3),
            "nota": nota
        })

    log(f"  Record da inserire: {len(records)} | Saltati: {skipped}")

    # Inserimento in batch da 500
    BATCH = 500
    totale_inseriti = 0
    for i in range(0, len(records), BATCH):
        batch = records[i:i + BATCH]
        resp = supabase.table("sessioni_corsa").insert(batch).execute()
        n = len(resp.data) if resp.data else 0
        totale_inseriti += n
        log(f"  Batch {i//BATCH + 1}: inseriti {n}/{len(batch)}", "OK" if n == len(batch) else "WARN")

    log(f"  Totale sessioni corsa inserite: {totale_inseriti}", "OK")
    return totale_inseriti


# ──────────────────────────────────────────────────────────────────────
# FASE 3 — Migrazione Sessioni VBT
# ──────────────────────────────────────────────────────────────────────

def migrate_sessioni_vbt(supabase, df_vbt: pd.DataFrame, nome_to_id: dict) -> int:
    """Migra le sessioni VBT/palestra."""
    log("FASE 3 — Migrazione sessioni VBT (palestra)...")

    existing_count = supabase.table("sessioni_vbt").select("id", count="exact").execute()
    if existing_count.count and existing_count.count > 0:
        log(f"  [WARN] Trovati {existing_count.count} record gia' presenti.", "WARN")
        risposta = input("  Vuoi procedere comunque aggiungendo i nuovi? (s/N): ").strip().lower()
        if risposta != "s":
            log("  Migrazione VBT saltata per scelta utente.", "WARN")
            return 0

    records = []
    skipped = 0

    for _, row in df_vbt.iterrows():
        atleta = str(row.get("Atleta", "")).strip()
        atleta_id = nome_to_id.get(atleta)

        if not atleta_id:
            skipped += 1
            continue

        data_val = row.get("Data")
        if pd.isna(data_val) if hasattr(data_val, '__class__') and data_val.__class__.__name__ == 'NaT' else (data_val is None):
            skipped += 1
            continue
        try:
            if pd.isna(data_val):
                skipped += 1
                continue
        except (TypeError, ValueError):
            pass

        esercizio = str(row.get("Esercizio", "")).strip()
        if not esercizio:
            skipped += 1
            continue

        records.append({
            "atleta_id": atleta_id,
            "data": pd.Timestamp(data_val).strftime("%Y-%m-%d"),
            "esercizio": esercizio,
            "serie": safe_int(row.get("Serie")),
            "ripetizioni": safe_int(row.get("Ripetizioni")),
            "carico": safe_float(row.get("Carico")),
            "vel_media": safe_float(row.get("Vel_media")),
            "vel_max": safe_float(row.get("Vel_max")),
            "potenza_media": safe_float(row.get("Potenza_media")),
            "potenza_max": safe_float(row.get("Potenza_max")),
            "forza_max": safe_float(row.get("Forza_max")),
        })

    log(f"  Record da inserire: {len(records)} | Saltati: {skipped}")

    BATCH = 500
    totale_inseriti = 0
    for i in range(0, len(records), BATCH):
        batch = records[i:i + BATCH]
        resp = supabase.table("sessioni_vbt").insert(batch).execute()
        n = len(resp.data) if resp.data else 0
        totale_inseriti += n
        log(f"  Batch {i//BATCH + 1}: inseriti {n}/{len(batch)}", "OK" if n == len(batch) else "WARN")

    log(f"  Totale sessioni VBT inserite: {totale_inseriti}", "OK")
    return totale_inseriti


# ──────────────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  MIGRAZIONE EXCEL -> SUPABASE")
    print(f"  {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("=" * 60)

    supabase = get_client()
    log("Connessione a Supabase riuscita.", "OK")

    # Carica dati dagli Excel
    log("Caricamento file Excel...")
    running_path = BASE / "Lavori Corsa.xlsx"
    vbt_path = BASE / "VBT2026322.xlsx"

    if not running_path.exists():
        log(f"File non trovato: {running_path}", "ERR"); sys.exit(1)
    if not vbt_path.exists():
        log(f"File non trovato: {vbt_path}", "ERR"); sys.exit(1)

    df_running = normalize_names(load_running_data(running_path))
    df_vbt = normalize_names(load_vbt_data(vbt_path))

    log(f"  Sessioni corsa lette: {len(df_running)}")
    log(f"  Sessioni VBT lette:   {len(df_vbt)}")

    # Raccoglie atleti unici da entrambi i dataset
    atleti_corsa = set(df_running["Atleta"].dropna().unique())
    atleti_vbt = set(df_vbt["Atleta"].dropna().unique())
    tutti_atleti = sorted(atleti_corsa | atleti_vbt)
    log(f"  Atleti unici trovati: {len(tutti_atleti)}: {tutti_atleti}")

    # Esegui le tre fasi
    nome_to_id = migrate_atleti(supabase, tutti_atleti)
    n_corsa = migrate_sessioni_corsa(supabase, df_running, nome_to_id)
    n_vbt = migrate_sessioni_vbt(supabase, df_vbt, nome_to_id)

    print()
    print("=" * 60)
    print(f"  MIGRAZIONE COMPLETATA")
    print(f"  Sessioni corsa: {n_corsa}")
    print(f"  Sessioni VBT:   {n_vbt}")
    print("=" * 60)


if __name__ == "__main__":
    main()

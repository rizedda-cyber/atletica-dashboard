"""
supabase_connector.py — Interfaccia con il database Supabase.

Fornisce funzioni per:
  - Leggere dati (atleti, sessioni corsa, sessioni VBT) come DataFrame pandas
  - Inserire nuove sessioni di allenamento
  - Caricare foto profilo (Storage)

Utilizzato sia dall'app principale che dagli script di migrazione.
"""

import os
from pathlib import Path
from functools import lru_cache

import pandas as pd
import streamlit as st
from supabase import create_client, Client


# ──────────────────────────────────────────────────────────────────────
# INIZIALIZZAZIONE CLIENT
# ──────────────────────────────────────────────────────────────────────

@st.cache_resource
def get_supabase() -> Client:
    """
    Crea e restituisce il client Supabase (singleton, cached).
    Usa i secrets di Streamlit se disponibili, altrimenti cerca
    variabili d'ambiente SUPABASE_URL e SUPABASE_KEY.
    """
    try:
        url = st.secrets["secrets"]["SUPABASE_URL"]
        key = st.secrets["secrets"]["SUPABASE_KEY"]
    except Exception:
        url = os.environ.get("SUPABASE_URL", "")
        key = os.environ.get("SUPABASE_KEY", "")

    if not url or not key:
        raise ValueError("Credenziali Supabase non trovate in secrets.toml né in variabili d'ambiente.")

    return create_client(url, key)


# ──────────────────────────────────────────────────────────────────────
# ATLETI
# ──────────────────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False, ttl=175)
def get_atleti(with_foto: bool = True) -> pd.DataFrame:
    """Restituisce tutti gli atleti registrati nel database.

    Cachata (TTL ~3 min, invalidata dalle chiamate st.cache_data.clear()
    eseguite dall'app dopo inserimenti/modifiche) per non riscaricare la
    tabella a ogni rerun di Streamlit.

    with_foto=False esclude la colonna foto_url (blob base64), alleggerendo
    le query che servono solo per nomi/anagrafica e non mostrano le foto.
    """
    supabase = get_supabase()
    cols = "*" if with_foto else "id, nome, cognome, nome_completo, specialita, attivo, data_nascita, peso, bio"
    response = supabase.table("atleti").select(cols).order("cognome").execute()
    if response.data:
        return pd.DataFrame(response.data)
    return pd.DataFrame(columns=["id", "nome", "cognome", "nome_completo", "specialita", "foto_url", "attivo"])


def get_atleta_by_nome(nome_completo: str) -> dict | None:
    """Cerca un atleta per nome completo."""
    supabase = get_supabase()
    response = supabase.table("atleti") \
        .select("*") \
        .eq("nome_completo", nome_completo) \
        .limit(1) \
        .execute()
    return response.data[0] if response.data else None


def upsert_atleta(nome: str, cognome: str, specialita: str = "") -> dict:
    """
    Inserisce un atleta se non esiste, o aggiorna. Usa nome_completo come chiave.
    Restituisce il record dell'atleta (con id).
    """
    supabase = get_supabase()
    nome_completo = f"{nome} {cognome}".strip()

    # Cerca prima se esiste già
    existing = get_atleta_by_nome(nome_completo)
    if existing:
        return existing

    # Inserisci nuovo atleta
    payload = {
        "nome": nome,
        "cognome": cognome,
        "nome_completo": nome_completo,
        "specialita": specialita,
        "attivo": True
    }
    response = supabase.table("atleti").insert(payload).execute()
    return response.data[0] if response.data else {}


def update_atleta_profile(atleta_id: int, data_nascita: str = None, peso: float = None, bio: str = None) -> bool:
    """Aggiorna i dati anagrafici e la biografia di un atleta."""
    supabase = get_supabase()
    payload = {}
    if data_nascita is not None:
        payload["data_nascita"] = data_nascita
    if peso is not None:
        payload["peso"] = peso
    if bio is not None:
        payload["bio"] = bio
        
    if not payload:
        return True
        
    try:
        response = supabase.table("atleti").update(payload).eq("id", atleta_id).execute()
        return bool(response.data)
    except Exception as e:
        print(f"Errore update profilo atleta: {e}")
        return False


# ──────────────────────────────────────────────────────────────────────
# PIN PERSONALI ATLETI
# ──────────────────────────────────────────────────────────────────────

def get_atleta_by_pin(pin: str) -> dict | None:
    """
    Cerca un atleta che ha impostato questo PIN personale.
    Restituisce il record atleta (dict) o None se non trovato.
    Il PIN è salvato in chiaro per consentire il recupero da parte dell'admin.
    """
    if not pin or not pin.strip():
        return None
    supabase = get_supabase()
    try:
        response = supabase.table("atleti") \
            .select("*") \
            .eq("pin_personale", pin.strip()) \
            .limit(1) \
            .execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Errore get_atleta_by_pin: {e}")
        return None


def set_atleta_pin(atleta_id: int, pin: str) -> bool:
    """
    Imposta o aggiorna il PIN personale di un atleta.
    Passa pin=None per resettare (rimuovere) il PIN.
    """
    supabase = get_supabase()
    try:
        payload = {"pin_personale": pin.strip() if pin else None}
        response = supabase.table("atleti").update(payload).eq("id", atleta_id).execute()
        return bool(response.data)
    except Exception as e:
        print(f"Errore set_atleta_pin: {e}")
        return False


def get_all_pins() -> pd.DataFrame:
    """
    Restituisce tutti gli atleti con il loro PIN personale (solo per admin).
    """
    supabase = get_supabase()
    try:
        response = supabase.table("atleti") \
            .select("id, nome_completo, pin_personale") \
            .order("cognome") \
            .execute()
        if response.data:
            return pd.DataFrame(response.data)
    except Exception as e:
        print(f"Errore get_all_pins: {e}")
    return pd.DataFrame(columns=["id", "nome_completo", "pin_personale"])


# ──────────────────────────────────────────────────────────────────────
# SESSIONI CORSA
# ──────────────────────────────────────────────────────────────────────

def get_sessioni_corsa(atleta_id: int = None, from_date: str = None, to_date: str = None) -> pd.DataFrame:
    """
    Restituisce le sessioni di corsa, con join degli atleti per avere il nome.
    Parametri opzionali di filtro per atleta e intervallo date (formato 'YYYY-MM-DD').
    """
    supabase = get_supabase()
    query = supabase.table("sessioni_corsa") \
        .select("*, atleti(nome_completo, specialita)") \
        .is_("deleted_at", "null")

    if atleta_id:
        query = query.eq("atleta_id", atleta_id)
    if from_date:
        query = query.gte("data", from_date)
    if to_date:
        query = query.lte("data", to_date)

    query = query.order("data", desc=True)

    all_data = []
    chunk_size = 1000
    start = 0
    while True:
        res = query.range(start, start + chunk_size - 1).execute()
        if not res.data:
            break
        all_data.extend(res.data)
        if len(res.data) < chunk_size:
            break
        start += chunk_size

    if not all_data:
        return pd.DataFrame(columns=["id", "atleta_id", "data", "distanza_m", "tempo_sec", "nota", "Atleta"])

    df = pd.DataFrame(all_data)
    # Estrae il nome dall'oggetto annidato 'atleti'
    if "atleti" in df.columns:
        df["Atleta"] = df["atleti"].apply(
            lambda x: x.get("nome_completo", "") if isinstance(x, dict) else ""
        )
        df = df.drop(columns=["atleti"])

    # Rinomina per compatibilità con la dashboard
    df = df.rename(columns={
        "data": "Data",
        "distanza_m": "Distanza",
        "tempo_sec": "Tempo",
        "nota": "Note",
    })
    df["Data"] = pd.to_datetime(df["Data"])
    df["Distanza"] = pd.to_numeric(df["Distanza"], errors="coerce")
    df["Tempo"] = pd.to_numeric(df["Tempo"], errors="coerce")
    return df


def insert_sessione_corsa(atleta_nome: str, data: str, distanza_m: float,
                           tempo_sec: float, nota: str = "") -> bool:
    """
    Inserisce una singola sessione di corsa per un atleta (cercato per nome).
    Restituisce True se l'inserimento è riuscito.
    """
    supabase = get_supabase()
    atleta = get_atleta_by_nome(atleta_nome)
    if not atleta:
        return False

    payload = {
        "atleta_id": atleta["id"],
        "data": data,
        "distanza_m": distanza_m,
        "tempo_sec": tempo_sec,
        "nota": nota or ""
    }
    response = supabase.table("sessioni_corsa").insert(payload).execute()
    return bool(response.data)


def bulk_insert_sessioni_corsa(records: list[dict]) -> int:
    """
    Inserimento in blocco di sessioni di corsa.
    Ogni record deve avere: atleta_id, data, distanza_m, tempo_sec, nota.
    Restituisce il numero di record inseriti.
    """
    supabase = get_supabase()
    if not records:
        return 0
    response = supabase.table("sessioni_corsa").insert(records).execute()
    return len(response.data) if response.data else 0


def update_sessione_corsa(sessione_id: int, nuovo_tempo_sec: float = None, nuova_nota: str = None) -> bool:
    """Aggiorna il tempo e/o la nota di una sessione di corsa esistente."""
    supabase = get_supabase()
    payload = {}
    if nuovo_tempo_sec is not None:
        payload["tempo_sec"] = nuovo_tempo_sec
    if nuova_nota is not None:
        payload["nota"] = nuova_nota
    if not payload:
        return True
    try:
        response = supabase.table("sessioni_corsa").update(payload).eq("id", sessione_id).execute()
        return bool(response.data)
    except Exception as e:
        print(f"Errore update_sessione_corsa: {e}")
        return False


def delete_sessione_corsa(sessione_id: int) -> bool:
    """
    Elimina (soft-delete) una sessione di corsa: marca la riga come eliminata
    impostando deleted_at, senza rimuoverla fisicamente dal database.
    La riga resta recuperabile e non richiede permessi DELETE.
    """
    from datetime import datetime, timezone
    supabase = get_supabase()
    try:
        payload = {"deleted_at": datetime.now(timezone.utc).isoformat()}
        response = supabase.table("sessioni_corsa").update(payload).eq("id", sessione_id).execute()
        return bool(response.data)
    except Exception as e:
        print(f"Errore delete_sessione_corsa: {e}")
        return False


# ──────────────────────────────────────────────────────────────────────
# SESSIONI VBT
# ──────────────────────────────────────────────────────────────────────

def get_sessioni_vbt(atleta_id: int = None, from_date: str = None, to_date: str = None) -> pd.DataFrame:
    """Restituisce le sessioni VBT con join del nome atleta."""
    supabase = get_supabase()
    query = supabase.table("sessioni_vbt") \
        .select("*, atleti(nome_completo)")

    if atleta_id:
        query = query.eq("atleta_id", atleta_id)
    if from_date:
        query = query.gte("data", from_date)
    if to_date:
        query = query.lte("data", to_date)

    query = query.order("data", desc=True)

    all_data = []
    chunk_size = 1000
    start = 0
    while True:
        res = query.range(start, start + chunk_size - 1).execute()
        if not res.data:
            break
        all_data.extend(res.data)
        if len(res.data) < chunk_size:
            break
        start += chunk_size

    if not all_data:
        return pd.DataFrame(columns=["id", "atleta_id", "data", "esercizio", "carico",
                                      "vel_media", "vel_max", "potenza_media", "potenza_max",
                                      "forza_max", "Atleta"])

    df = pd.DataFrame(all_data)
    if "atleti" in df.columns:
        df["Atleta"] = df["atleti"].apply(
            lambda x: x.get("nome_completo", "") if isinstance(x, dict) else ""
        )
        df = df.drop(columns=["atleti"])

    # Rinomina per compatibilità con la dashboard
    df = df.rename(columns={
        "data": "Data",
        "esercizio": "Esercizio",
        "carico": "Carico",
        "vel_media": "Vel_media",
        "vel_max": "Vel_max",
        "potenza_media": "Potenza_media",
        "potenza_max": "Potenza_max",
        "forza_max": "Forza_max",
        "serie": "Serie",
        "ripetizioni": "Ripetizioni",
    })
    df["Data"] = pd.to_datetime(df["Data"])
    numeric_cols = ["Carico", "Vel_media", "Vel_max", "Potenza_media", "Potenza_max", "Forza_max"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def insert_sessione_vbt(atleta_nome: str, data: str, esercizio: str,
                         carico: float, vel_media: float, vel_max: float = None,
                         potenza_media: float = None, potenza_max: float = None,
                         forza_max: float = None, serie: int = None,
                         ripetizioni: int = None) -> bool:
    """Inserisce una singola sessione VBT."""
    supabase = get_supabase()
    atleta = get_atleta_by_nome(atleta_nome)
    if not atleta:
        return False

    payload = {
        "atleta_id": atleta["id"],
        "data": data,
        "esercizio": esercizio,
        "carico": carico,
        "vel_media": vel_media,
        "vel_max": vel_max,
        "potenza_media": potenza_media,
        "potenza_max": potenza_max,
        "forza_max": forza_max,
        "serie": serie,
        "ripetizioni": ripetizioni,
    }
    response = supabase.table("sessioni_vbt").insert(payload).execute()
    return bool(response.data)


def bulk_insert_sessioni_vbt(records: list[dict]) -> int:
    """Inserimento in blocco di sessioni VBT."""
    supabase = get_supabase()
    if not records:
        return 0
    response = supabase.table("sessioni_vbt").insert(records).execute()
    return len(response.data) if response.data else 0


# ──────────────────────────────────────────────────────────────────────
# FOTO PROFILO (Storage)
# ──────────────────────────────────────────────────────────────────────

def upload_foto_profilo(atleta_id: int, file_bytes: bytes, filename: str) -> str | None:
    """
    Comprime e salva la foto nel DB come stringa base64 (Bypassa Supabase Storage).
    Restituisce l'URL interno o None in caso di errore.
    """
    import base64
    from io import BytesIO
    from PIL import Image

    supabase = get_supabase()
    try:
        # Comprimi immagine con Pillow
        img = Image.open(BytesIO(file_bytes))
        # Selettore colore standard
        if img.mode in ("RGBA", "P"): 
            img = img.convert("RGB")
            
        # Ridimensiona il quadrato (max 250x250) per alleggerire la codifica base64 string
        img.thumbnail((250, 250))
        buffer = BytesIO()
        img.save(buffer, format="JPEG", quality=75)
        
        # Codifica in Base64
        b64_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
        full_url = "data:image/jpeg;base64," + b64_str
        
        # Salva sulla tabella 'atleti'
        supabase.table("atleti").update({"foto_url": full_url}).eq("id", atleta_id).execute()
        return full_url
    except Exception as e:
        print(f"Errore upload foto: {e}")
        return f"ERROR:{e}"


# ──────────────────────────────────────────────────────────────────────
# GARE UFFICIALI (PB)
# ──────────────────────────────────────────────────────────────────────

def get_gare_ufficiali(atleta_id: int = None) -> pd.DataFrame:
    """Restituisce lo storico delle gare e PB ufficiali."""
    supabase = get_supabase()
    query = supabase.table("gare_ufficiali").select("*, atleti(nome_completo)")
    
    if atleta_id:
        query = query.eq("atleta_id", atleta_id)
        
    query = query.order("data", desc=True)
    response = query.execute()
    
    if not response.data:
        return pd.DataFrame(columns=["id", "atleta_id", "specialita", "tempo", "vento", "luogo", "data"])
        
    df = pd.DataFrame(response.data)
    df["Data"] = pd.to_datetime(df["data"])
    # Rinomina
    df = df.rename(columns={
        "specialita": "Specialità",
        "tempo": "Prestazione",
        "vento": "Vento",
        "luogo": "Luogo",
    })
    return df

def insert_gara_ufficiale(atleta_nome: str, specialita: str, tempo: str,
                           vento: str = "", luogo: str = "", data: str = None) -> bool:
    """Inserisce un PB Ufficiale in Gara per un atleta."""
    supabase = get_supabase()
    atleta = get_atleta_by_nome(atleta_nome)
    if not atleta:
        return False

    payload = {
        "atleta_id": atleta["id"],
        "specialita": specialita,
        "tempo": tempo,
        "vento": vento or "",
        "luogo": luogo or "",
        "data": data
    }
    try:
        response = supabase.table("gare_ufficiali").insert(payload).execute()
        return bool(response.data)
    except Exception as e:
        print(f"Errore inserimento gara: {e}")
        return False


# ──────────────────────────────────────────────────────────────────────
# UTILITÀ
# ──────────────────────────────────────────────────────────────────────

def test_connection() -> bool:
    """Testa la connessione al database senza raising exception."""
    try:
        supabase = get_supabase()
        supabase.table("atleti").select("id").limit(1).execute()
        return True
    except Exception:
        return False

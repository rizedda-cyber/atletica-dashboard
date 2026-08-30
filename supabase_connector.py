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
def get_atleti(with_foto: bool = True, solo_attivi: bool = True) -> pd.DataFrame:
    """Restituisce gli atleti registrati nel database.

    Cachata (TTL ~3 min, invalidata dalle chiamate .clear() mirate
    eseguite dall'app dopo inserimenti/modifiche) per non riscaricare la
    tabella a ogni rerun di Streamlit.

    with_foto=False esclude la colonna foto_url (blob base64), alleggerendo
    le query che servono solo per nomi/anagrafica e non mostrano le foto.

    solo_attivi=True (default) esclude gli atleti congelati direttamente
    a livello di query, cosi' roster/KPI/selettori non li scaricano nè
    li ricalcolano. Passa solo_attivi=False solo dove serve vedere anche
    i congelati (es. pannello admin per riattivarli).
    """
    supabase = get_supabase()
    cols = "*" if with_foto else "id, nome, cognome, nome_completo, specialita, attivo, data_nascita, peso, bio"
    query = supabase.table("atleti").select(cols)
    if solo_attivi:
        # attivo NULL conta come attivo (atleti storici migrati prima che
        # esistesse questa colonna) - stessa semantica del fillna(True)
        # gia' usata altrove nell'app.
        query = query.or_("attivo.eq.true,attivo.is.null")
    response = query.order("cognome").execute()
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


def set_atleta_attivo(atleta_id: int, attivo: bool) -> bool:
    """Congela (attivo=False) o riattiva (attivo=True) un atleta.

    Un atleta congelato sparisce da roster/KPI/selettori (vedi get_atleti),
    ma i suoi dati storici restano intatti e riconsultabili passando
    solo_attivi=False.
    """
    supabase = get_supabase()
    try:
        response = supabase.table("atleti").update({"attivo": attivo}).eq("id", atleta_id).execute()
        return bool(response.data)
    except Exception as e:
        print(f"Errore set_atleta_attivo: {e}")
        return False


def get_specialita_disponibili() -> list[str]:
    """Valori distinti di 'specialita' tra gli atleti attivi (per il selettore tag)."""
    df = get_atleti(with_foto=False, solo_attivi=True)
    if df.empty or "specialita" not in df.columns:
        return []
    valori = sorted(v for v in df["specialita"].dropna().unique() if str(v).strip())
    return valori


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
    Restituisce tutti gli atleti (compresi i congelati) con il loro PIN
    personale e lo stato attivo/congelato (solo per admin).
    """
    supabase = get_supabase()
    try:
        response = supabase.table("atleti") \
            .select("id, nome_completo, pin_personale, attivo") \
            .order("cognome") \
            .execute()
        if response.data:
            return pd.DataFrame(response.data)
    except Exception as e:
        print(f"Errore get_all_pins: {e}")
    return pd.DataFrame(columns=["id", "nome_completo", "pin_personale", "attivo"])


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
# PROGRAMMA A TAG (ASSEGNAZIONI)
# ──────────────────────────────────────────────────────────────────────

def crea_assegnazione_tag(data: str, tipo_sessione: str, descrizione: str,
                           target: str, specialita: str, settimana_label: str = None) -> bool:
    """
    Crea un blocco assegnato a tutti gli atleti attivi con la 'specialita'
    indicata. Il gruppo viene espanso subito (una riga per atleta in
    assegnazione_atleti): se la squadra cambia dopo, il blocco gia'
    creato resta storicamente coerente.
    """
    supabase = get_supabase()
    df_atleti = get_atleti(with_foto=False, solo_attivi=True)
    if df_atleti.empty or "specialita" not in df_atleti.columns:
        return False
    atleti_ids = df_atleti[df_atleti["specialita"] == specialita]["id"].tolist()
    if not atleti_ids:
        return False
    return _crea_assegnazione(data, tipo_sessione, descrizione, target, atleti_ids,
                               target_tag=specialita, settimana_label=settimana_label)


def crea_assegnazione_atleti(data: str, tipo_sessione: str, descrizione: str,
                              target: str, atleti_ids: list[int], settimana_label: str = None) -> bool:
    """Crea un blocco assegnato a una selezione esplicita di atleti (1 o piu').

    Copre sia le eccezioni individuali sia i sottogruppi ad-hoc (es. "chi non
    ha gareggiato") che non corrispondono a un tag fisso.
    """
    if not atleti_ids:
        return False
    return _crea_assegnazione(data, tipo_sessione, descrizione, target, atleti_ids,
                               target_tag=None, settimana_label=settimana_label)


def _crea_assegnazione(data: str, tipo_sessione: str, descrizione: str, target: str,
                        atleti_ids: list[int], target_tag: str | None, settimana_label: str | None) -> bool:
    supabase = get_supabase()
    try:
        payload = {
            "data": data,
            "tipo_sessione": tipo_sessione,
            "descrizione": descrizione,
            "target": target or None,
            "target_tag": target_tag,
            "settimana_label": settimana_label or None,
        }
        response = supabase.table("assegnazioni").insert(payload).execute()
        if not response.data:
            return False
        assegnazione_id = response.data[0]["id"]

        righe_atleti = [{"assegnazione_id": assegnazione_id, "atleta_id": aid} for aid in atleti_ids]
        response_atleti = supabase.table("assegnazione_atleti").insert(righe_atleti).execute()
        return bool(response_atleti.data)
    except Exception as e:
        print(f"Errore _crea_assegnazione: {e}")
        return False


def get_assegnazioni_settimana(data_inizio: str, data_fine: str) -> pd.DataFrame:
    """Restituisce i blocchi assegnati (solo tabella 'assegnazioni', senza
    espandere gli atleti) in un intervallo date - usata per popolare la
    griglia con 'Duplica settimana precedente'."""
    supabase = get_supabase()
    try:
        response = supabase.table("assegnazioni") \
            .select("*") \
            .gte("data", data_inizio) \
            .lte("data", data_fine) \
            .order("data") \
            .execute()
        if response.data:
            return pd.DataFrame(response.data)
    except Exception as e:
        print(f"Errore get_assegnazioni_settimana: {e}")
    return pd.DataFrame(columns=["id", "settimana_label", "data", "tipo_sessione",
                                  "descrizione", "target", "target_tag", "creato_il"])


def get_assegnazioni_atleta(atleta_id: int, data_da: str, data_a: str) -> pd.DataFrame:
    """Assegnazioni di UN atleta (via assegnazione_atleti) in un intervallo di
    date, con i dati del blocco appiattiti (stesso pattern di get_sessioni_corsa
    per il join annidato). Usata dalla pagina 'Oggi' lato atleta."""
    supabase = get_supabase()
    try:
        response = supabase.table("assegnazione_atleti") \
            .select("*, assegnazioni(data, tipo_sessione, descrizione, target, settimana_label)") \
            .eq("atleta_id", atleta_id) \
            .execute()
    except Exception as e:
        print(f"Errore get_assegnazioni_atleta: {e}")
        response = None

    cols = ["id", "assegnazione_id", "atleta_id", "stato", "completato_il",
            "data", "tipo_sessione", "descrizione", "target", "settimana_label"]
    if not response or not response.data:
        return pd.DataFrame(columns=cols)

    df = pd.DataFrame(response.data)
    if "assegnazioni" in df.columns:
        for campo in ["data", "tipo_sessione", "descrizione", "target", "settimana_label"]:
            df[campo] = df["assegnazioni"].apply(
                lambda x, c=campo: x.get(c) if isinstance(x, dict) else None
            )
        df = df.drop(columns=["assegnazioni"])

    df["data"] = pd.to_datetime(df["data"])
    mask = (df["data"] >= pd.Timestamp(data_da)) & (df["data"] <= pd.Timestamp(data_a))
    return df[mask].sort_values("data").reset_index(drop=True)


def completa_assegnazione(assegnazione_atleti_id: int) -> bool:
    """Marca come completato un blocco assegnato a un singolo atleto (riga di
    assegnazione_atleti). Non collega nessuna riga specifica di sessioni_corsa/
    sessioni_vbt: lo stato dice solo 'fatto o no', i dati veri restano dove
    sono sempre stati."""
    from datetime import datetime, timezone
    supabase = get_supabase()
    try:
        payload = {"stato": "completato", "completato_il": datetime.now(timezone.utc).isoformat()}
        response = supabase.table("assegnazione_atleti").update(payload).eq("id", assegnazione_atleti_id).execute()
        return bool(response.data)
    except Exception as e:
        print(f"Errore completa_assegnazione: {e}")
        return False


# ──────────────────────────────────────────────────────────────────────
# FOTO PROFILO (Storage)
# ──────────────────────────────────────────────────────────────────────

FOTO_BUCKET = "foto-atleti"  # nome dell'archivio (bucket) su Supabase Storage


def _storage_path_from_url(url: str) -> str | None:
    """Ricava il percorso interno al bucket da un link pubblico Supabase.
    Es: '.../foto-atleti/atleti/abc.jpg?v=1' -> 'atleti/abc.jpg'. None se non è del bucket."""
    if not url or f"/{FOTO_BUCKET}/" not in url:
        return None
    return url.split(f"/{FOTO_BUCKET}/", 1)[1].split("?", 1)[0]


def upload_foto_profilo(atleta_id: int, file_bytes: bytes, filename: str) -> str | None:
    """
    Comprime la foto e la carica su Supabase Storage con un nome di file CASUALE
    (non indovinabile), salvando in 'foto_url' solo il link pubblico (leggero).

    Sicurezza: se l'archivio (bucket) non esiste ancora o l'upload fallisce,
    ricade automaticamente sul vecchio metodo base64, cosi' il caricamento foto
    continua a funzionare. Restituisce l'URL salvato, oppure "ERROR:..." in caso di errore.
    """
    import base64
    import time
    import secrets
    from io import BytesIO
    from PIL import Image

    supabase = get_supabase()

    # 1) Comprimi e ridimensiona
    try:
        img = Image.open(BytesIO(file_bytes))
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.thumbnail((250, 250))
        buffer = BytesIO()
        img.save(buffer, format="JPEG", quality=75)
        jpeg_bytes = buffer.getvalue()
    except Exception as e:
        return f"ERROR:{e}"

    # 2) Prova Supabase Storage con nome casuale (link leggero e non indovinabile)
    try:
        # recupera il link precedente per cancellare la vecchia foto dopo l'upload
        old_path = None
        try:
            prev = supabase.table("atleti").select("foto_url").eq("id", atleta_id).single().execute()
            old_path = _storage_path_from_url((prev.data or {}).get("foto_url", ""))
        except Exception:
            old_path = None

        token = secrets.token_hex(16)  # 32 caratteri casuali -> impossibile da indovinare
        new_path = f"atleti/{token}.jpg"
        supabase.storage.from_(FOTO_BUCKET).upload(
            new_path,
            jpeg_bytes,
            {"content-type": "image/jpeg", "cache-control": "3600"},
        )
        public_url = supabase.storage.from_(FOTO_BUCKET).get_public_url(new_path).rstrip("?")
        full_url = f"{public_url}?v={int(time.time())}"
        supabase.table("atleti").update({"foto_url": full_url}).eq("id", atleta_id).execute()

        # rimuovi la vecchia foto (best-effort, non blocca in caso di errore)
        if old_path and old_path != new_path:
            try:
                supabase.storage.from_(FOTO_BUCKET).remove([old_path])
            except Exception:
                pass
        return full_url
    except Exception as storage_err:
        # 3) FALLBACK: vecchio metodo base64 (l'archivio non c'e' ancora o upload fallito)
        try:
            b64_str = base64.b64encode(jpeg_bytes).decode("utf-8")
            full_url = "data:image/jpeg;base64," + b64_str
            supabase.table("atleti").update({"foto_url": full_url}).eq("id", atleta_id).execute()
            return full_url
        except Exception as e:
            return f"ERROR:{e}"


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

"""
ui_helpers.py — Funzioni di servizio della Dashboard Atletica.

Raccoglie le piccole funzioni "autosufficienti" prima sparse in app.py:
lettura logo e credenziali, export CSV, card grafiche (KPI/avvisi),
filtri dati per periodo/atleta e ordinamento atleti per attività recente.

Nessuna logica nuova: solo riordino. app.py le importa da qui.
"""

import pandas as pd
import streamlit as st


# ── Logo ──────────────────────────────────────────────────────────────

@st.cache_data
def get_logo_b64(path: str = "logo.png") -> str:
    """Legge e codifica il logo in base64 una sola volta (cache su disco→memoria).
    Il file non cambia mai, quindi evitiamo di rileggerlo a ogni rerun."""
    import base64
    try:
        with open(path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except Exception:
        return ""


# ── Foto di copertina squadra ─────────────────────────────────────────

# Nomi accettati per la copertina, in ordine di preferenza. Basta appoggiare
# il file nella cartella del progetto: l'app lo trova da sola.
NOMI_COPERTINA = ["copertina.jpg", "copertina.jpeg", "copertina.png", "copertina.webp"]


def get_cover_b64(max_width: int = 1800, quality: int = 82) -> str:
    """Foto di copertina della squadra come data URI JPEG, pronta per il CSS.

    Basta appoggiare un file chiamato "copertina" (jpg/png/webp) nella
    cartella del progetto. Restituisce "" se non c'e': la Home ha un fondo
    tipografico di riserva, non resta mai vuota.

    La ricerca del file NON e' cachata, la conversione si: cosi' sostituire
    la foto ha effetto subito (la firma sotto include data e dimensione del
    file, quindi cambia la chiave di cache) senza pero' ricodificare
    l'immagine a ogni rerun.
    """
    from pathlib import Path

    for nome in NOMI_COPERTINA:
        percorso = Path(nome)
        if percorso.exists():
            st_info = percorso.stat()
            return _cover_b64_da_file(str(percorso), st_info.st_mtime_ns, st_info.st_size,
                                       max_width, quality)
    return ""


@st.cache_data(show_spinner=False)
def _cover_b64_da_file(percorso: str, mtime_ns: int, dimensione: int,
                        max_width: int, quality: int) -> str:
    """Ridimensiona e codifica la copertina. mtime_ns e dimensione servono
    solo come firma per la cache (una foto nuova = chiave nuova).

    Il ridimensionamento non e' un vezzo: l'immagine finisce inline nell'HTML
    (come il logo), quindi un file da 6 MB appesantirebbe ogni rerun della
    Home. Cosi' l'allenatore puo' lasciar cadere nella cartella la foto che
    ha, a qualunque risoluzione, senza doverla preparare.
    """
    import base64
    import io as _io

    try:
        from PIL import Image
        with Image.open(percorso) as im:
            im = im.convert("RGB")
            if im.width > max_width:
                altezza = round(im.height * max_width / im.width)
                im = im.resize((max_width, altezza), Image.LANCZOS)
            buf = _io.BytesIO()
            im.save(buf, format="JPEG", quality=quality, optimize=True)
        return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
    except Exception:
        # Pillow assente o file illeggibile: si ripiega sul fondo grafico.
        return ""


# ── Credenziali (dai secrets di Streamlit) ────────────────────────────

# get_team_pin: rimossa insieme al login squadra. L'app ha due soli ruoli,
# allenatore e atleta; la chiave TEAM_PIN nei secrets non viene piu' letta.


def get_admin_password() -> str:
    """Password dell'allenatore. ADMIN_PASSWORD e' il nome giusto;
    TEAM_PASSWORD resta accettata perche' e' quella configurata oggi nei
    secrets (locali e in cloud) e rinominarla richiede di intervenire su
    entrambi."""
    for key in ["ADMIN_PASSWORD", "TEAM_PASSWORD"]:
        if key in st.secrets:
            return str(st.secrets[key])
        if "secrets" in st.secrets and key in st.secrets["secrets"]:
            return str(st.secrets["secrets"][key])
    return ""


# ── Export CSV ────────────────────────────────────────────────────────

@st.cache_data
def convert_df_to_csv(df):
    return df.to_csv(index=False).encode('utf-8')


# ── Ordinamento atleti per attività recente ───────────────────────────

def get_sort_key(atl, last_active_dates):
    """Chiave di ordinamento: (timestamp ultima attività, nome).
    last_active_dates: dizionario {atleta: ultima data attiva}."""
    dt = last_active_dates.get(atl)
    if pd.isnull(dt): return (0, atl)
    return (dt.timestamp(), atl)


# ── Filtri dati per periodo e atleta selezionati ──────────────────────

def filter_running(df, start_date, end_date, selected_athlete, esclusi=None):
    """esclusi: nomi da togliere dalla vista di squadra (atleti congelati).
    Si applica solo a "Tutta la squadra": chiedendo esplicitamente un atleta
    si vuole il suo storico completo, congelato o no."""
    mask = (df['Data'].dt.date >= start_date) & (df['Data'].dt.date <= end_date)
    if selected_athlete != "Tutta la squadra":
        mask &= df['Atleta'] == selected_athlete
    elif esclusi:
        mask &= ~df['Atleta'].isin(esclusi)
    return df[mask].copy()


def filter_vbt(df, start_date, end_date, selected_athlete, esclusi=None):
    mask = pd.Series(True, index=df.index)
    if 'Data' in df.columns:
        mask &= (df['Data'].dt.date >= start_date) & (df['Data'].dt.date <= end_date)
    if selected_athlete != "Tutta la squadra":
        mask &= df['Atleta'] == selected_athlete
    elif esclusi:
        mask &= ~df['Atleta'].isin(esclusi)
    return df[mask].copy()


# ── Card grafiche (HTML) ──────────────────────────────────────────────

def make_kpi_card(title, value, delta_text, trend, icon, val_class=""):
    delta_class = "delta-neu"
    if trend == "pos": delta_class = "delta-pos"
    elif trend == "neg": delta_class = "delta-neg"

    return f"""<div class="kpi-card">
<div class="kpi-icon">{icon}</div>
<div class="kpi-title">{title}</div>
<div class="kpi-value {val_class}">{value}</div>
<div class="kpi-delta {delta_class}">{delta_text}</div>
</div>"""


def make_alert_card(label, text, icon, color, bg_alpha="0.1"):
    """Card alert generica con bordo colorato a sinistra, in stile coerente con quelle esistenti in Home."""
    return f"""
    <div style="background: rgba({color[1]},{bg_alpha}); border-left: 4px solid {color[0]}; border-radius: 8px; padding: 14px; margin-bottom: 12px; height: 100%; box-sizing: border-box;">
        <div style="display: flex; gap: 10px; align-items: flex-start;">
            <span style="font-size: 24px; margin-top: 2px;">{icon}</span>
            <div style="flex: 1;">
                <div style="color: {color[0]}; font-weight: 700; font-family: 'DM Mono'; letter-spacing: 1px; font-size: 10px; margin-bottom: 4px;">{label}</div>
                <div style="color: #fff; font-size: 0.9em;">{text}</div>
            </div>
        </div>
    </div>
    """

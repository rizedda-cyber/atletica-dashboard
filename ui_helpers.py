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


# ── Credenziali (dai secrets di Streamlit) ────────────────────────────

def get_team_pin() -> str:
    if "TEAM_PIN" in st.secrets:
        return str(st.secrets["TEAM_PIN"])
    if "secrets" in st.secrets and "TEAM_PIN" in st.secrets["secrets"]:
        return str(st.secrets["secrets"]["TEAM_PIN"])
    return "1234"


def get_admin_password() -> str:
    # Prova prima ADMIN_PASSWORD, poi TEAM_PASSWORD come fallback
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

def filter_running(df, start_date, end_date, selected_athlete):
    mask = (df['Data'].dt.date >= start_date) & (df['Data'].dt.date <= end_date)
    if selected_athlete != "Tutta la squadra":
        mask &= df['Atleta'] == selected_athlete
    return df[mask].copy()


def filter_vbt(df, start_date, end_date, selected_athlete):
    mask = pd.Series(True, index=df.index)
    if 'Data' in df.columns:
        mask &= (df['Data'].dt.date >= start_date) & (df['Data'].dt.date <= end_date)
    if selected_athlete != "Tutta la squadra":
        mask &= df['Atleta'] == selected_athlete
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

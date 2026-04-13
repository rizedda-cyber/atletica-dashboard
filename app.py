"""
app.py — Dashboard Atletica Leggera (Settore Velocità) v3

Avvio:
    C:\\Users\\rized\\anaconda3\\python.exe -m streamlit run app.py

Novità v3:
    - Fonte dati: Supabase (cloud) con fallback automatico su Excel
    - Autenticazione squadra tramite PIN condiviso a 4 cifre
    - Form di inserimento allenamenti (sessioni corsa + VBT) protetto da PIN
    - Indicatore stato connessione cloud
"""

import streamlit as st

st.set_page_config(
    page_title="🏃 Atletica Sprint Dashboard",
    page_icon="🏃",
    layout="wide",
    initial_sidebar_state="expanded",
)
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression
from pathlib import Path
from data_loader import load_all_data

try:
    from streamlit_extras.metric_cards import style_metric_cards
except ImportError:
    def style_metric_cards(*args, **kwargs): pass

# ──────────────────────────────────────────────────────────────────────
# CONFIGURAZIONE PAGINA
# ──────────────────────────────────────────────────────────────────────

# Configurazione pagina spostata sotto import streamlit

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');

    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
    }
    h1, h2, h3, .st-emotion-cache-10trblm {
        font-family: 'Bebas Neue', sans-serif !important;
        letter-spacing: 1px !important;
        color: #E8EDF5 !important;
    }
    /* Mono per numerici stringenti */
    .dataframe {
        font-family: 'DM Mono', monospace !important;
        background-color: transparent !important;
    }
    
    /* Cover Amsicora Login Dark Neon */
    .cover {
        background: #080A0E; min-height: 500px; display: flex; flex-direction: column; align-items: center; justify-content: center;
        text-align: center; padding: 60px 40px; position: relative; overflow: hidden; margin: -6rem -4rem 2rem -4rem; border-radius: 0 0 20px 20px;
    }
    
    /* Cover Amsicora Login Dark Neon */
    .cover {
        background: #080A0E; display: flex; flex-direction: column; align-items: center; justify-content: center;
        text-align: center; padding: 40px; border-radius: 20px; margin: 0 auto; max-width: 600px; box-shadow: 0 10px 40px rgba(0,0,0,0.5);
    }
    html, body { overscroll-behavior: none; }
    
    .cover::before {
        content: ''; position: absolute; inset: 0;
        background: radial-gradient(ellipse at 30% 20%, rgba(232,255,58,0.06) 0%, transparent 60%),
                    radial-gradient(ellipse at 70% 80%, rgba(0,217,255,0.05) 0%, transparent 50%);
    }
    .cover-logo {
        width: 160px; height: 160px; border-radius: 50%; object-fit: cover;
        border: 2px solid rgba(232,255,58,0.3); box-shadow: 0 0 30px rgba(232,255,58,0.1);
        margin-bottom: 36px; position: relative; z-index: 1;
    }
    .cover-eyebrow {
        font-family: 'DM Mono', monospace; font-size: 11px; letter-spacing: 4px; color: rgba(255,255,255,0.4); text-transform: uppercase;
        margin-bottom: 16px; position: relative; z-index: 1;
    }
    .cover-title {
        font-family: 'Bebas Neue', sans-serif; font-size: clamp(40px, 6vw, 68px); color: #FFFFFF;
        line-height: 1.1; margin-bottom: 12px; position: relative; z-index: 1; letter-spacing: 2px;
    }
    .cover-title span { color: #E8FF3A; }
    .cover-subtitle {
        font-size: 16px; color: rgba(255,255,255,0.4); max-width: 480px; margin: 0 auto 40px;
        position: relative; z-index: 1;
    }

    .stTabs [data-baseweb="tab-list"] { gap: 16px; padding-bottom: 8px; }
    .stTabs [data-baseweb="tab"] { padding: 10px 24px; border-radius: 8px 8px 0 0; font-weight: 500; font-size: 1.1em; color: rgba(255,255,255,0.4); }
    .stTabs [data-baseweb="tab"][aria-selected="true"] { border-bottom-color: #E8FF3A !important; color: #E8FF3A !important; background: rgba(232,255,58,0.05); }
    .streamlit-expanderHeader { font-weight: 600 !important; font-size: 1.05em !important; font-family: 'DM Sans', sans-serif; color: #E8EDF5;}
    
    /* Regole separatori guide */
    hr.gold { border: none; border-top: 1px solid rgba(255,255,255,0.1); margin: 32px 0; }
    
    /* Componente Metriche Amsicora Sporty */
    div[data-testid="metric-container"] {
        color: white !important;
        background: rgba(255,255,255,0.03) !important;
        border-radius: 12px !important;
        border: 1px solid rgba(255,255,255,0.05) !important;
        min-height: 110px !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: center !important;
    }
    div[data-testid="metric-container"] label {
        color: rgba(255,255,255,0.4) !important;
        font-family: 'DM Mono', monospace !important;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        font-size: 11px !important;
    }
    div[data-testid="metric-container"] [data-testid="stMetricValue"] {
        color: #fff !important;
        font-family: 'Bebas Neue', sans-serif !important;
        letter-spacing: 1px;
    }

    /* Tabs to Pill Buttons Style */
    [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: transparent !important;
        overflow-x: auto !important;
        padding-bottom: 15px !important; /* Spazio per la scrollbar */
    }
    [data-baseweb="tab"] {
        background-color: #14171E !important;
        border-radius: 8px !important;
        padding: 12px 20px !important;
        color: #FFFFFF !important;
        border: 2px solid rgba(255,255,255,0.1) !important;
        font-family: 'DM Sans', sans-serif !important;
        font-weight: 700 !important;
        font-size: 1.1em !important;
        white-space: nowrap !important;
    }
    [data-baseweb="tab"][aria-selected="true"] {
        background-color: #E8FF3A !important;
        border: 2px solid #E8FF3A !important;
    }
    /* Forza il testo dentro la tab attiva ad essere scuro */
    [data-baseweb="tab"][aria-selected="true"] p, 
    [data-baseweb="tab"][aria-selected="true"] span, 
    [data-baseweb="tab"][aria-selected="true"] div {
        color: #0A0D14 !important;
    }
    
    [data-baseweb="tab"]:hover {
        background-color: rgba(232,255,58,0.2) !important;
    }
    [data-baseweb="tab"]:hover p,
    [data-baseweb="tab"]:hover span,
    [data-baseweb="tab"]:hover div {
        color: #E8FF3A !important;
    }
    
    [data-baseweb="tab-highlight"] { display: none !important; }
    
    /* Fix visibilità e contrasto Tasto Menu a tendina (Hamburger) per Mobile */
    [data-testid="collapsedControl"] {
        background-color: #E8FF3A !important;
        border-radius: 6px !important;
        padding: 4px !important;
        margin: 10px !important;
        opacity: 1 !important;
        box-shadow: 0 4px 10px rgba(232,255,58,0.3) !important;
        border: 1px solid rgba(10,13,20,0.5) !important;
    }
    [data-testid="collapsedControl"] svg {
        color: #0A0D14 !important;
        fill: #0A0D14 !important;
    }
    [data-testid="collapsedControl"]:hover {
        background-color: #d1e82e !important;
    }

    /* Premium Glass KPI Cards */
    .kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 15px; margin-bottom: 20px; }
    .kpi-card { 
        background: rgba(20, 23, 30, 0.6); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
        border-radius: 16px; border: 1px solid rgba(255, 255, 255, 0.05); padding: 20px; position: relative; overflow: hidden;
        display: flex; flex-direction: column; justify-content: space-between; transition: all 0.3s ease;
        height: 140px; box-sizing: border-box;
    }
    .kpi-card:hover { border-color: rgba(232,255,58,0.4); transform: translateY(-3px); box-shadow: 0 10px 20px rgba(0,0,0,0.5); }
    .kpi-icon { position: absolute; right: -5px; bottom: -15px; font-size: 70px; opacity: 0.04; transform: rotate(-15deg); user-select: none; pointer-events: none; text-shadow: none; }
    .kpi-title { font-size: 0.85em; color: rgba(255,255,255,0.5); font-weight: 700; text-transform: uppercase; letter-spacing: 1px; z-index: 1; margin-bottom: 5px; }
    .kpi-value { font-size: 2.2em; color: #fff; font-family: 'Bebas Neue', sans-serif; letter-spacing: 1px; margin: 0; z-index: 1; text-shadow: 0 0 10px rgba(255,255,255,0.1); line-height: 1.1; }
    .kpi-glow { color: #E8FF3A; text-shadow: 0 0 15px rgba(232,255,58,0.6); }
    .kpi-alert { color: #FF4B4B; text-shadow: 0 0 15px rgba(255,75,75,0.6); }
    .kpi-delta { font-size: 0.8em; font-weight: 700; z-index: 1; padding: 4px 8px; border-radius: 6px; display: inline-block; width: max-content; margin-top: auto; }
    .delta-pos { background: rgba(184,255,138,0.1); color: #B8FF8A; border: 1px solid rgba(184,255,138,0.2); }
    .delta-neg { background: rgba(255,75,75,0.1); color: #FF4B4B; border: 1px solid rgba(255,75,75,0.2); }
    .delta-neu { background: rgba(255,255,255,0.05); color: rgba(255,255,255,0.5); border: 1px solid rgba(255,255,255,0.1); }

    .cloud-badge { display: inline-block; padding: 2px 10px; border-radius: 20px; font-size: 0.78em; font-weight: 700; }
    .cloud-ok { background: rgba(184,255,138,0.1); color: #B8FF8A; border: 1px solid rgba(184,255,138,0.2); }
    /* Nascondi il menu di Streamlit Cloud in alto a destra (Deploy, GitHub, ecc) mantenendo visibile il bottone per riaprire la sidebar */
    .stAppDeployButton { display: none !important; }
    .stToolbarActions { display: none !important; }
    
    /* Fix visibilità e contrasto Bottoni (Login, Form Submit, Generale) */
    button[kind="primary"], 
    button[kind="primaryFormSubmit"],
    [data-testid="stFormSubmitButton"] button {
        background-color: #E8FF3A !important;
        border: none !important;
        color: #0A0D14 !important;
    }
    button[kind="primary"] *, 
    button[kind="primaryFormSubmit"] *,
    [data-testid="stFormSubmitButton"] button * {
        color: #0A0D14 !important;
        font-weight: 800 !important;
        font-size: 1.1em !important;
    }

    /* [data-testid="stSidebar"] rimosso per consentire l'uso della navbar laterale */
    /* Fix visibilità Input Box Login (evita sfondi chiari con testo bianco) */
    div[data-baseweb="input"] {
        background-color: #0A0D14 !important;
        border: 1px solid rgba(232,255,58,0.5) !important;
    }
    div[data-baseweb="input"] input {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }    
</style>
""", unsafe_allow_html=True)

style_metric_cards(
    background_color="#14171E",
    border_left_color="#E8FF3A",
    border_size_px=3, border_radius_px=12, box_shadow=False
)

import plotly.io as pio
import plotly.graph_objects as go
amsicora_template = go.layout.Template(pio.templates["plotly_dark"])
amsicora_template.layout.paper_bgcolor = "rgba(0,0,0,0)"
amsicora_template.layout.plot_bgcolor = "rgba(0,0,0,0)"
amsicora_template.layout.font.family = "DM Sans, sans-serif"
amsicora_template.layout.font.color = "#E8EDF5"
amsicora_template.layout.title.font.family = "Bebas Neue, sans-serif"
amsicora_template.layout.title.font.size = 24
amsicora_template.layout.title.font.color = "#FFFFFF"
amsicora_template.layout.xaxis.gridcolor = "rgba(255,255,255,0.05)"
amsicora_template.layout.yaxis.gridcolor = "rgba(255,255,255,0.05)"
pio.templates["amsicora"] = amsicora_template

THEME_TEMPLATE = "amsicora"
NEON_COLORS = ['#E8FF3A', '#00D9FF', '#FF6B35', '#B8FF8A', '#FFB347', '#E8EDF5', '#C9931A']
CHART_HEIGHT = 450

# ──────────────────────────────────────────────────────────────────────
# GESTIONE SESSIONE — PIN SQUADRA
# ──────────────────────────────────────────────────────────────────────

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False
if "current_page" not in st.session_state:
    st.session_state.current_page = "Home"


def get_team_pin() -> str:
    if "TEAM_PIN" in st.secrets:
        return str(st.secrets["TEAM_PIN"])
    if "secrets" in st.secrets and "TEAM_PIN" in st.secrets["secrets"]:
        return str(st.secrets["secrets"]["TEAM_PIN"])
    return "1234"

def get_admin_password() -> str:
    if "TEAM_PASSWORD" in st.secrets:
        return str(st.secrets["TEAM_PASSWORD"])
    if "secrets" in st.secrets and "TEAM_PASSWORD" in st.secrets["secrets"]:
        return str(st.secrets["secrets"]["TEAM_PASSWORD"])
    return ""

# ──────────────────────────────────────────────────────────────────────
# SCHERMATA DI VISIBILITA' BLOCCATA (HOME AMSICORA)
# ──────────────────────────────────────────────────────────────────────

if not st.session_state.authenticated:
    b64_string = ""
    try:
        import base64
        with open("logo.png", "rb") as img_file:
            b64_string = base64.b64encode(img_file.read()).decode()
    except Exception:
        pass
        
    st.markdown(f'''
    <div class="cover">
        <img class="cover-logo" src="data:image/png;base64,{b64_string}" alt="Logo">
        <div class="cover-eyebrow">Società Ginnastica Amsicora</div>
        <div class="cover-title">Atletica<br><span>Sprint</span><br>Dashboard</div>
        <div class="cover-subtitle">I dati e le statistiche di questa dashboard sono riservati allo staff e agli atleti. Inserisci il PIN.</div>
    </div>
    ''', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.container(border=True):
            st.markdown("<h4 style='text-align: center;'>Login Squadra</h4>", unsafe_allow_html=True)

            pin_input = st.text_input("Codice di Accesso", type="password", placeholder="PIN o Password...", label_visibility="collapsed")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🔐 Accedi", type="primary", use_container_width=True):
                if pin_input.strip() == get_team_pin().strip():
                    st.session_state.authenticated = True
                    st.rerun()
                elif get_admin_password() and pin_input.strip() == get_admin_password().strip():
                    st.session_state.authenticated = True
                    st.session_state.is_admin = True
                    st.rerun()
                else:
                    st.error("❌ Codice errato")
    st.stop() # Ferma il caricamento dell'app finché non c'è login

# ──────────────────────────────────────────────────────────────────────
# CARICAMENTO DATI (Supabase → fallback Excel)
# ──────────────────────────────────────────────────────────────────────

DATA_SOURCE = "excel"  # sarà aggiornato sotto

@st.cache_data(show_spinner="Connessione al cloud…", ttl=175)
def get_data_cloud():
    """Scarica i dati da Supabase. TTL 5 minuti."""
    from supabase_connector import get_sessioni_corsa, get_sessioni_vbt, test_connection
    if not test_connection():
        return None, None
    df_r = get_sessioni_corsa()
    df_v = get_sessioni_vbt()
    return df_r, df_v


@st.cache_data(show_spinner="Caricamento dati locali…")
def get_data_local():
    base = Path(__file__).parent
    return load_all_data(base / 'Lavori Corsa.xlsx', base / 'VBT2026322.xlsx')


# Prova cloud prima
_cloud_r, _cloud_v = get_data_cloud()
if _cloud_r is not None and len(_cloud_r) > 0:
    df_running, df_vbt = _cloud_r, _cloud_v
    DATA_SOURCE = "cloud"
else:
    df_running, df_vbt = get_data_local()
    DATA_SOURCE = "excel" if (_cloud_r is None) else "excel_nodata"

# Filtro Sanitario Globale Server-Side
# Rimuove distanze fittizie parse male come 1m, 8m derivate dalle label testuali sporche di excel storici
if not df_running.empty:
    df_running = df_running[df_running['Distanza'] >= 20].copy()


# ──────────────────────────────────────────────────────────────────────
# NAVIGAZIONE LATERALE (SIDEBAR) E FILTRI
# ──────────────────────────────────────────────────────────────────────
if "app_athlete" not in st.session_state:
    st.session_state.app_athlete = "Tutta la squadra"

all_athletes = sorted(set(df_running['Atleta'].unique()) | set(df_vbt['Atleta'].unique()))

with st.sidebar:
    st.markdown("### 🏃 Menu Navigazione")
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🏠 Home Squadra", use_container_width=True, type="primary" if st.session_state.current_page == "Home" else "secondary"):
        st.session_state.current_page = "Home"
        st.session_state.app_athlete = "Tutta la squadra"
        st.rerun()

    if st.button("👥 Tutti gli Atleti", use_container_width=True, type="primary" if st.session_state.current_page == "Atleti" else "secondary"):
        st.session_state.current_page = "Atleti"
        st.session_state.app_athlete = "Tutta la squadra"
        st.rerun()

    if st.button("➕ Inserisci Allenamento", use_container_width=True, type="primary" if st.session_state.current_page == "Inserimento" else "secondary"):
        st.session_state.current_page = "Inserimento"
        st.rerun()

    if st.session_state.current_page == "Dettaglio Atleta":
        st.button("👤 Dettaglio Atleta", use_container_width=True, type="primary")

    st.divider()

    st.markdown("### 📅 Opzioni Analisi")
    min_date = df_running['Data'].min().date() if not df_running.empty else pd.Timestamp(2023, 1, 1).date()
    max_date = df_running['Data'].max().date() if not df_running.empty else pd.Timestamp.now().date()
    
    with st.popover("📅 Intervallo Temporale Dati", use_container_width=True):
        date_range = st.date_input("Periodo Analisi", value=(min_date, max_date), min_value=min_date, max_value=max_date, label_visibility="collapsed")
        
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date, end_date = min_date, max_date
        
    st.divider()
    
    if DATA_SOURCE == "cloud":
        st.markdown('<div style="text-align:center;"><span class="cloud-badge cloud-ok">☁️ Supabase Connesso</span></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div style="text-align:center;"><span class="cloud-badge cloud-local">📂 Dati Locali (Excel)</span></div>', unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    role_label = "👑 Admin" if st.session_state.is_admin else "🟢 Esci / Log Out"
    if st.button(f"🚪 {role_label}", key="btn_logout", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.is_admin = False
        st.session_state.current_page = "Home"
        st.rerun()

selected_athlete = st.session_state.app_athlete

@st.cache_data
def convert_df_to_csv(df):
    return df.to_csv(index=False).encode('utf-8')

# ──────────────────────────────────────────────────────────────────────
# FILTRAGGIO DATI
# ──────────────────────────────────────────────────────────────────────

def filter_running(df):
    mask = (df['Data'].dt.date >= start_date) & (df['Data'].dt.date <= end_date)
    if selected_athlete != "Tutta la squadra":
        mask &= df['Atleta'] == selected_athlete
    return df[mask].copy()


def filter_vbt(df):
    mask = pd.Series(True, index=df.index)
    if 'Data' in df.columns:
        mask &= (df['Data'].dt.date >= start_date) & (df['Data'].dt.date <= end_date)
    if selected_athlete != "Tutta la squadra":
        mask &= df['Atleta'] == selected_athlete
    return df[mask].copy()


df_r = filter_running(df_running)
df_v = filter_vbt(df_vbt)

# Download CSV Sidebar
st.sidebar.divider()
st.sidebar.subheader("📥 Esporta Dati Filtrati")
col_d1, col_d2 = st.sidebar.columns(2)
with col_d1:
    st.download_button("Corsa (CSV)", data=convert_df_to_csv(df_r),
                        file_name='dati_corsa_filtrati.csv', mime='text/csv')
with col_d2:
    st.download_button("VBT (CSV)", data=convert_df_to_csv(df_v),
                        file_name='dati_vbt_filtrati.csv', mime='text/csv')


if selected_athlete != "Tutta la squadra":
    from supabase_connector import get_atleta_by_nome
    atleta_info = get_atleta_by_nome(selected_athlete)
    
    primo_nome = selected_athlete.split()[0]
    
    # Sesso da nome
    primo_nome_lower = primo_nome.lower()
    if primo_nome_lower.endswith('a') and primo_nome_lower not in ['andrea', 'luca', 'mattia', 'nicola', 'tobia', 'elia', 'giona']:
        sesso = "F"
    elif primo_nome_lower in ['alice', 'beatrice', 'carmen', 'chloe', 'clelia', 'cloe', 'noemi', 'iris', 'miriam']:
        sesso = "F"
    else:
        sesso = "M"
        
    benvenuto_text = "Benvenuta" if sesso == "F" else "Benvenuto"
    
    avatar_html = ""
    if atleta_info and atleta_info.get("foto_url"):
        foto_url = atleta_info["foto_url"]
        avatar_html = f'''<div style="width: 120px; height: 120px; border-radius: 50%; overflow: hidden; border: 4px solid #166534; box-shadow: 0 4px 6px rgba(0,0,0,0.1); flex-shrink: 0;">
            <img src="{foto_url}" style="width: 100%; height: 100%; object-fit: cover; object-position: center 15%; display: block;">
        </div>'''
    else:
        avatar_html = f'''<div style="width: 120px; height: 120px; border-radius: 50%; background: #e2e8f0; border: 4px solid #94a3b8; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
            <span style="font-size: 3em; color: #64748b;">👤</span>
        </div>'''
        
    @st.dialog("Aggiorna Foto Profilo")
    def render_photo_modal():
        st.markdown("**Carica il tuo avatar visibile in cima alla pagina.** (Verrà compresso automaticamente)")
        uploaded_file = st.file_uploader("Scegli un'immagine JPG o PNG (Max: 5MB)", type=["jpg", "jpeg", "png"])
        if uploaded_file and st.button("🖼️ Carica Foto Online", type="primary", use_container_width=True):
            with st.spinner("Caricamento ed ottimizzazione in corso..."):
                from supabase_connector import upload_foto_profilo
                # atleta_info is available in the outer scope
                if atleta_info and "id" in atleta_info:
                    url = upload_foto_profilo(atleta_info["id"], uploaded_file.getvalue(), uploaded_file.name)
                    if url and not url.startswith("ERROR:"):
                        st.success("✅ Foto profilo aggiornata con successo!")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        err_msg = url.replace("ERROR:", "") if url else "Sconosciuto"
                        st.error(f"❌ Errore nel caricamento della foto: {err_msg}")
                else:
                    st.error("❌ Impossibile identificare l'atleta nel cloud. L'utente deve essere presente nel database associato.")

    @st.dialog("Modifica Dati Profilo")
    def render_edit_profile_modal():
        st.markdown(f"**Aggiorna i dati per {primo_nome}**")
        
        # Load existing data robustly
        import datetime
        dn_value = None
        if atleta_info and atleta_info.get("data_nascita"):
            try:
                dn_value = datetime.datetime.strptime(atleta_info["data_nascita"], "%Y-%m-%d").date()
            except:
                pass
                
        n_data = st.date_input("Data di Nascita", value=dn_value, min_value=datetime.date(1950, 1, 1), max_value=datetime.date.today())
        
        peso_val = 65.0
        if atleta_info and atleta_info.get("peso"):
            try:
                peso_val = float(atleta_info["peso"])
            except:
                pass
        n_peso = st.number_input("Peso (kg)", min_value=30.0, max_value=150.0, step=0.1, value=peso_val)
        
        n_bio = st.text_area("Biografica / Note", value=atleta_info.get("bio", "") if atleta_info else "", placeholder="Inserisci una breve bio o i titoli!")
        
        if st.button("✅ Salva Dati", type="primary", use_container_width=True):
            from supabase_connector import update_atleta_profile
            n_data_str = n_data.strftime("%Y-%m-%d") if n_data else None
            update_atleta_profile(atleta_info["id"], n_data_str, n_peso, n_bio)
            st.success("✅ Profilo aggiornato!")
            st.cache_data.clear()
            st.rerun()

    # Prepara dati per HTML header
    bio_text = atleta_info.get('bio', '') if atleta_info else ''
    dn = atleta_info.get('data_nascita') if atleta_info else None
    eta_txt = ""
    if dn:
        import datetime
        try:
            dt = datetime.datetime.strptime(dn, "%Y-%m-%d").date()
            today = datetime.date.today()
            anni = today.year - dt.year - ((today.month, today.day) < (dt.month, dt.day))
            eta_txt = f" • {anni} anni"
        except:
            pass
            
    peso_str = str(atleta_info['peso']) if atleta_info and atleta_info.get('peso') else ""
    peso_txt = f" • {peso_str} kg" if peso_str else ""


    st.markdown(f'''
        <div style="display: flex; align-items: flex-start; gap: 24px; margin-bottom: 8px;">
            {avatar_html}
            <div style="padding-top: 5px;">
                <h1 style="margin: 0 0 6px 0; padding: 0; line-height: 1;">👋 {benvenuto_text}, {primo_nome}!</h1>
                <p style="margin: 0 0 10px 0; color: #E8FF3A; font-family: 'DM Mono', monospace; font-size: 0.9em; font-weight: 600; letter-spacing: 0.5px;">PROFILO ATLETA{eta_txt}{peso_txt}</p>
                <p style="margin: 0; color: rgba(255,255,255,0.7); font-size: 1.05em; line-height: 1.35; max-width: 600px;">
                    {bio_text if bio_text else "Nessuna biografia inserita."}
                </p>
            </div>
        </div>
    ''', unsafe_allow_html=True)
    
    if st.session_state.authenticated:
        btn1, btn2, empty_space = st.columns([2, 2, 6])
        if btn1.button("📸 Cambia Foto", key="cambia_foto_btn", use_container_width=True):
            render_photo_modal()
        if btn2.button("✏️ Modifica Dati", key="cambia_dati_btn", use_container_width=True):
            render_edit_profile_modal()
else:
    b64_string_logo = ""
    try:
        import base64
        with open("logo.png", "rb") as img_file:
            b64_string_logo = base64.b64encode(img_file.read()).decode()
    except Exception:
        pass
        
    logo_html = f'<div style="flex-shrink: 0; margin-top: 2px;"><img src="data:image/png;base64,{b64_string_logo}" style="width: 70px; height: 70px; border-radius: 50%; border: 3px solid #E8FF3A; box-shadow: 0 0 12px rgba(232,255,58,0.3); display: block;"></div>'
    
    st.markdown(f'''
        <div style="display: flex; align-items: flex-start; gap: 22px; margin-bottom: 24px;">
            {logo_html}
            <div>
                <h1 style="color: #E8EDF5; margin: 0; padding: 0; line-height: 1.1; letter-spacing: 1px;">S.G. Amsicora — Team <span style="color: #E8FF3A;">Velocità</span></h1>
                <p style="margin: 6px 0 0 0; color: rgba(255,255,255,0.7); font-size: 1.1em;">Panoramica generale della squadra, metriche di volume e database atleti attivi.</p>
            </div>
        </div>
    ''', unsafe_allow_html=True)

# KPI HTML Generation
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

if st.session_state.current_page == "Inserimento":
    st.markdown("## ➕ Inserisci Nuovo Allenamento")
    if DATA_SOURCE != "cloud":
        st.warning("⚠️ La dashboard sta usando i dati locali (Excel). L'inserimento richiede la connessione al cloud.")
    else:
        st.markdown("I dati vengono salvati direttamente nel cloud e saranno visibili a tutta la squadra.")
        
        tipo_form = st.radio("Seleziona attività:", ["🏃 Pista (corsa)", "🏋️ Palestra (VBT)"], horizontal=True, key="tipo_allenamento")
        st.divider()
        
        atleti_list = sorted(set(df_running['Atleta'].unique()) | set(df_vbt['Atleta'].unique()))
        default_atleta_idx = 0
        if selected_athlete != "Tutta la squadra" and selected_athlete in atleti_list:
            default_atleta_idx = atleti_list.index(selected_athlete)
            
        if tipo_form == "🏃 Pista (corsa)":
            from supabase_connector import insert_sessione_corsa
            with st.form("form_corsa", clear_on_submit=True):
                st.markdown("**Sessione in Pista**")
                col_a, col_b = st.columns(2)
                atleta_sel = col_a.selectbox("Atleta", options=atleti_list, index=default_atleta_idx, key="atleta_corsa")
                data_sel = col_b.date_input("Data", key="data_corsa")

                st.markdown("---")
                st.markdown("**Prove effettuate**")
                distanze_opts = [30, 40, 50, 60, 80, 100, 120, 150, 200, 300, 400]
                prove = []
                for i in range(1, 13):
                    c1, c2, c3 = st.columns([1, 1, 2])
                    dist_i = c1.selectbox(f"Dist. prova {i}", ["-"] + [f"{d}m" for d in distanze_opts], key=f"dist_{i}")
                    tempo_i = c2.text_input(f"Tempo {i} (es: 7.12)", key=f"tempo_{i}", placeholder="es. 7.12")
                    nota_i = c3.text_input(f"Nota {i}", key=f"nota_{i}", placeholder="es. vento, elettrico...")
                    if dist_i != "-" and tempo_i.strip():
                        prove.append((int(dist_i.replace("m", "")), tempo_i.strip(), nota_i.strip()))

                submitted = st.form_submit_button("✅ Salva Sessione in Pista", type="primary", use_container_width=True)

                if submitted:
                    if not prove:
                        st.error("Inserisci almeno una prova.")
                    else:
                        successi, errori = 0, 0
                        for dist, tempo_raw, nota in prove:
                            try:
                                from data_loader import parse_time
                                parsed = parse_time(tempo_raw)
                                if parsed is None:
                                    errori += 1; continue
                                ok = insert_sessione_corsa(atleta_sel, data_sel.strftime("%Y-%m-%d"), dist, parsed['tempo'], nota)
                                if ok: successi += 1
                                else: errori += 1
                            except:
                                errori += 1
                        if successi > 0:
                            st.success(f"✅ {successi} prove salvate per {atleta_sel}!")
                            st.cache_data.clear()
                            st.rerun()
                        if errori > 0:
                            st.warning(f"⚠️ {errori} prove non salvate (controlla il formato).")

        elif tipo_form == "🏋️ Palestra (VBT)":
            from supabase_connector import insert_sessione_vbt
            esercizi_noti = sorted(set(df_vbt['Esercizio'].dropna().unique()) - {'General'})
            with st.form("form_vbt", clear_on_submit=True):
                st.markdown("**Sessione in Palestra (VBT)**")
                col_a, col_b = st.columns(2)
                atleta_sel = col_a.selectbox("Atleta", options=atleti_list, index=default_atleta_idx, key="atleta_vbt")
                data_sel = col_b.date_input("Data", key="data_vbt")
                st.markdown("---")
                esercizio_sel = st.selectbox("Esercizio", options=esercizi_noti, key="esercizio_sel")
                c1, c2, c3 = st.columns(3)
                carico = c1.number_input("Carico (kg)", min_value=0.0, step=2.5, key="carico")
                vel_media = c2.number_input("Velocità Media (m/s)", min_value=0.0, step=0.01, format="%.3f", key="vel_media")
                vel_max = c3.number_input("Velocità Max (m/s)", min_value=0.0, step=0.01, format="%.3f", key="vel_max")
                c4, c5, c6 = st.columns(3)
                pot_media = c4.number_input("Potenza Media (W)", min_value=0.0, step=10.0, key="pot_media")
                pot_max = c5.number_input("Potenza Max (W)", min_value=0.0, step=10.0, key="pot_max")
                forza_max = c6.number_input("Forza Max (N)", min_value=0.0, step=10.0, key="forza_max")
                c7, c8 = st.columns(2)
                serie = c7.number_input("Serie", min_value=1, value=3, step=1, key="serie")
                rip = c8.number_input("Ripetizioni", min_value=1, value=5, step=1, key="ripetizioni")
                submitted_vbt = st.form_submit_button("✅ Salva Sessione Palestra", type="primary", use_container_width=True)
                if submitted_vbt:
                    if carico == 0:
                        st.error("Inserisci il carico utilizzato.")
                    else:
                        ok = insert_sessione_vbt(atleta_sel, data_sel.strftime("%Y-%m-%d"), esercizio_sel, carico, vel_media or None, vel_max or None, pot_media or None, pot_max or None, forza_max or None, int(serie), int(rip))
                        if ok:
                            st.success(f"✅ Sessione VBT salvata per {atleta_sel}!")
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error("❌ Errore nel salvataggio.")

elif st.session_state.current_page == "Dettaglio Atleta" and selected_athlete != "Tutta la squadra":
    pb_corse = df_r.groupby('Distanza')['Tempo'].min()
    
    is_400_runner = False
    if 400 in pb_corse.index:
        is_400_runner = True
        
    # Forza override per velocisti puri (che mostreranno i record 60/100/200 anche se hanno corso un 400)
    velocisti_puri = [
        "Enrico Deidda", "Manuel Corda", "Leonardo Carboni", "Riccardo Zedda",
        "Alberto Pinna", "Alessandro Demicheli", "Marco Benini", "Federica Loi",
        "Elena Moccia", "Sara Cesaraccio", "Laura Murgia", "Priscilla Casu",
        "Marianna Deidda", "Martina Italia", "Riccardo Murru"
    ]
    if selected_athlete in velocisti_puri:
        is_400_runner = False
        
    num_allenamenti = df_r['Data'].dt.date.nunique() if len(df_r) > 0 else 0
    c1 = make_kpi_card("Allenamenti Pista", num_allenamenti, "Sessioni Totali", "neu", "🏟️")
    
    if is_400_runner:
        d1 = pb_corse.get(150, "-")
        d2 = pb_corse.get(300, "-")
        d3 = pb_corse.get(400, "-")
        c2 = make_kpi_card("Record 150m", f"{d1:.2f}s" if d1 != "-" else "-", "Miglior Tempo", "neu" if d1 == "-" else "pos", "⏱️", "kpi-glow" if d1 != "-" else "")
        c3 = make_kpi_card("Record 300m", f"{d2:.2f}s" if d2 != "-" else "-", "Miglior Tempo", "neu" if d2 == "-" else "pos", "⚡", "kpi-glow" if d2 != "-" else "")
        c4 = make_kpi_card("Record 400m", f"{d3:.2f}s" if d3 != "-" else "-", "Miglior Tempo", "neu" if d3 == "-" else "pos", "🔥", "kpi-glow" if d3 != "-" else "")
    else:
        d1 = pb_corse.get(60, "-")
        d2 = pb_corse.get(100, "-")
        d3 = pb_corse.get(200, "-")
        c2 = make_kpi_card("Record 60m", f"{d1:.2f}s" if d1 != "-" else "-", "Miglior Tempo", "neu" if d1 == "-" else "pos", "⏱️", "kpi-glow" if d1 != "-" else "")
        c3 = make_kpi_card("Record 100m", f"{d2:.2f}s" if d2 != "-" else "-", "Miglior Tempo", "neu" if d2 == "-" else "pos", "⚡", "kpi-glow" if d2 != "-" else "")
        c4 = make_kpi_card("Record 200m", f"{d3:.2f}s" if d3 != "-" else "-", "Miglior Tempo", "neu" if d3 == "-" else "pos", "🔥", "kpi-glow" if d3 != "-" else "")
        
    st.markdown(f'<div class="kpi-grid">{c1}{c2}{c3}{c4}</div>', unsafe_allow_html=True)

elif st.session_state.current_page == "Home":
    # ────────────────────────────────────────────────────────────────
    # CALCOLO KPI DI SQUADRA (HOME)
    # ────────────────────────────────────────────────────────────────
    start_d = pd.to_datetime(start_date)
    end_d = pd.to_datetime(end_date)
    duration_days = max(1, (end_d - start_d).days)
    prev_start_d = start_d - pd.Timedelta(days=duration_days)
    prev_end_d = start_d - pd.Timedelta(days=1)
    
    # Maschere e subset pre-periodo
    mask_prev_r = (df_running['Data'].dt.date >= prev_start_d.date()) & (df_running['Data'].dt.date <= prev_end_d.date())
    df_r_prev = df_running[mask_prev_r]
    
    mask_prev_v = (df_vbt['Data'].dt.date >= prev_start_d.date()) & (df_vbt['Data'].dt.date <= prev_end_d.date())
    df_v_prev = df_vbt[mask_prev_v]

    # KPI 1. Sessioni (Presenze Atleti, calcolato come combinazioni Atleta-Giorno)
    sess_curr = df_r.groupby(['Atleta', df_r['Data'].dt.date]).ngroups if len(df_r) > 0 else 0
    sess_prev = df_r_prev.groupby(['Atleta', df_r_prev['Data'].dt.date]).ngroups if len(df_r_prev) > 0 else 0
    delta_sess = sess_curr - sess_prev

    # KPI 2. Prove
    prove_curr = len(df_r)
    prove_totali = len(df_running)
    
    # KPI 3. Record VBT
    storico_vbt = df_vbt[df_vbt['Data'].dt.date < start_d.date()].groupby(['Atleta', 'Esercizio'])['Potenza_max'].max().to_dict()
    nuovi_vbt = 0
    df_v_ex = df_v[df_v['Esercizio'] != 'General']
    for idx, row in df_v_ex.iterrows():
        k = (row['Atleta'], row['Esercizio'])
        if k in storico_vbt:
            if row['Potenza_max'] > storico_vbt[k]:
                nuovi_vbt += 1
                storico_vbt[k] = row['Potenza_max']
        else:
            storico_vbt[k] = row['Potenza_max']
            nuovi_vbt += 1

    # KPI Row 2 calcoli
    # 1. Atleti con PB nel periodo
    storico_pb = df_running[df_running['Data'].dt.date < start_d.date()].groupby(['Atleta', 'Distanza'])['Tempo'].min().to_dict()
    atleti_pb = set()
    for idx, row in df_r.iterrows():
        k = (row['Atleta'], row['Distanza'])
        if k in storico_pb:
            if row['Tempo'] < storico_pb[k]:
                atleti_pb.add(row['Atleta'])
                storico_pb[k] = row['Tempo']
        else:
            atleti_pb.add(row['Atleta'])
            storico_pb[k] = row['Tempo']
            
    # 2. Atleti inattivi
    ultime_date = pd.concat([df_running[['Atleta', 'Data']], df_vbt[['Atleta', 'Data']]]).groupby('Atleta')['Data'].max()
    inattivi = []
    for atl, ud in ultime_date.items():
        if pd.notnull(ud) and (pd.Timestamp.now().tz_localize(None) - ud).days > 7:
            inattivi.append(atl)
            
    # 3. Media sessioni/settimana
    settimane = max(1, duration_days / 7)
    tot_sess_atl = df_r.groupby('Atleta')['Data'].nunique()
    media_sess = tot_sess_atl.mean() / settimane if len(tot_sess_atl) > 0 else 0
    
    # 4. Km squadra
    km_curr = df_r['Distanza'].sum() / 1000
    km_prev = df_r_prev['Distanza'].sum() / 1000
    delta_km = km_curr - km_prev
    p_km = (delta_km / km_prev * 100) if km_prev > 0 else 0

    c1 = make_kpi_card("Sessioni Pista", sess_curr, f"↑ {delta_sess} vs prec." if delta_sess > 0 else (f"↓ {abs(delta_sess)}" if delta_sess < 0 else "Invariato"), "pos" if delta_sess > 0 else ("neg" if delta_sess<0 else "neu"), "🏟️", "kpi-glow")
    c2 = make_kpi_card("Prove Registrate", prove_curr, f"{prove_totali} totali tracciate", "neu", "🏃")
    c3 = make_kpi_card("Record (VBT)", len(df_v), f"↑ {nuovi_vbt} freschi" if nuovi_vbt > 0 else "Nessun nuovo PB", "pos" if nuovi_vbt > 0 else "neu", "🏋️")
    c4 = make_kpi_card("Atleti a Sistema", df_r['Atleta'].nunique() if len(df_r) > 0 else 0, "Attivi nel periodo", "neu", "👥")
    
    c5 = make_kpi_card("Atleti in PB", len(atleti_pb), f"🌟 Formidabile" if len(atleti_pb) > 0 else "Costanza", "pos" if len(atleti_pb) > 0 else "neu", "🏅", "kpi-glow" if len(atleti_pb) > 0 else "")
    c6 = make_kpi_card("Inattivi (>7 gg)", len(inattivi), "Da richiamare!" if len(inattivi) > 0 else "Ottimi, nessuno fermo", "neg" if len(inattivi) > 0 else "pos", "⚠️", "kpi-alert" if len(inattivi) > 0 else "")
    c7 = make_kpi_card("Media (Sett.)", f"{media_sess:.1f}", "Sess / Atleta", "neu", "📉")
    c8 = make_kpi_card("Volume Squadra", f"{km_curr:.1f} km", f"↑ {delta_km:+.1f}km ({p_km:+.0f}%)" if delta_km > 0 else (f"↓ {delta_km:+.1f}km ({p_km:+.0f}%)" if delta_km < 0 else "Invariato"), "pos" if delta_km > 0 else ("neg" if delta_km < 0 else "neu"), "🛣️")

    st.markdown(f'<div class="kpi-grid">{c1}{c2}{c3}{c4}{c5}{c6}{c7}{c8}</div>', unsafe_allow_html=True)
    
    # NOTIFICHE AUTOMATICHE E COMPLEANNI
    st.markdown("<hr class='gold'>", unsafe_allow_html=True)
    st.markdown("#### 🔔 Alert & Notifiche Group")
    
    # ── LOGICA COMPLEANNI ──
    from supabase_connector import get_atleti
    df_atleti_full = get_atleti()
    oggi_tz = pd.Timestamp.now().tz_localize(None)
    compleanni = []
    if not df_atleti_full.empty:
        for _, row in df_atleti_full.iterrows():
            if pd.notna(row.get('data_nascita')):
                try:
                    dn = pd.to_datetime(row['data_nascita'])
                    if dn.month == oggi_tz.month and dn.day == oggi_tz.day:
                        compleanni.append(row['nome_completo'])
                except:
                    pass
    if compleanni:
        txt_h = "è il compleanno di" if len(compleanni) == 1 else "sono i compleanni di"
        st.success(f"🎈 **Tanti auguri!** Oggi {txt_h}: **{', '.join(compleanni)}**! 🎉")
    alert_col1, alert_col2 = st.columns(2)
    with alert_col1:
        if atleti_pb:
            txt = " e altri" if len(atleti_pb) > 3 else ""
            st.success(f"🏆 **Record infranti:** {', '.join(list(atleti_pb)[:3])} {txt} hanno battuto il PB!")
        else:
            st.info("ℹ️ Nessun nuovo PB in questo periodo. Continuate a spingere!")
        if p_km > 0:
            st.info(f"📈 **Volume in crescita:** La squadra ha aumentato i km del {p_km:+.1f}% rispetto al periodo precedente.")
    with alert_col2:
        if inattivi:
            txt2 = " e altri" if len(inattivi) > 3 else ""
            st.warning(f"⚠️ **Attenzione:** {', '.join(inattivi[:3])} {txt2} non si allenano da oltre 7 giorni.")
        else:
            st.success("Tutti gli atleti sono attivi di recente! 🎉")

st.divider()

if st.session_state.current_page == "Home":
    st.markdown("<h3 style='margin-bottom:0;'>VOLUME SETTIMANALE (KM)</h3>", unsafe_allow_html=True)
    df_r_vol = df_r.copy()
    if not df_r_vol.empty:
        df_r_vol['Settimana'] = df_r_vol['Data'].dt.isocalendar().week
        vol_agg = df_r_vol.groupby('Settimana')['Distanza'].sum() / 1000
        vol_df = vol_agg.reset_index()
        vol_df['Settimana'] = "S" + vol_df['Settimana'].astype(str)
        fig_vol = px.bar(vol_df, x='Settimana', y='Distanza', template=THEME_TEMPLATE)
        fig_vol.update_traces(marker_color='#E8FF3A', marker_line_color='#E8FF3A', marker_line_width=1.5, opacity=0.8)
        fig_vol.update_layout(height=400, margin=dict(t=20, b=20, l=0, r=0), yaxis_title="Chilometri", xaxis_title="")
        st.plotly_chart(fig_vol, use_container_width=True)
    else:
        st.info("Nessun dato di corsa nel periodo selezionato.")
        
    st.divider()
    st.markdown("<h3 style='margin-bottom:0;'>🏆 CLASSIFICA PERSONAL BEST (PB) SQUADRA</h3>", unsafe_allow_html=True)
    if len(df_r) > 0:
        pb_df = df_r.loc[df_r.groupby(['Atleta', 'Distanza'])['Tempo'].idxmin()]
        pb_pivot = pb_df.pivot_table(index='Atleta', columns='Distanza', values='Tempo', aggfunc='min')
        pb_pivot.columns = [f"{int(c)}m" for c in pb_pivot.columns]
        
        def bg_min(s):
            return ['background-color: #90e0ef; color: #0A0D14; font-weight: bold;' if v else '' for v in (s == s.min())]

        def bg_max(s):
            return ['background-color: #fde2e4; color: #0A0D14; font-weight: bold;' if v else '' for v in (s == s.max())]

        styled_pb = pb_pivot.style.format(lambda x: f"{x:.2f}s" if pd.notnull(x) else " - ")\
                                  .apply(bg_min, axis=0)\
                                  .apply(bg_max, axis=0)
                                  
        st.dataframe(styled_pb, use_container_width=True, height=500)
    else:
        st.info("Nessuna prova presente.")
        
    st.divider()
    with st.expander("📅 Riepilogo Dettagliato Allenamenti (Vista Excel)", expanded=False):
        st.markdown("Spulcia le tabelle inserite giorno per giorno. Le colonne si espandono in base a quante prove sono state svolte sulla singola distanza nell'arco della seduta.")
        if not df_r.empty:
            giorni_sett = {0: 'Lunedì', 1: 'Martedì', 2: 'Mercoledì', 3: 'Giovedì', 4: 'Venerdì', 5: 'Sabato', 6: 'Domenica'}
            mesi = {1: 'Gennaio', 2: 'Febbraio', 3: 'Marzo', 4: 'Aprile', 5: 'Maggio', 6: 'Giugno', 7: 'Luglio', 8: 'Agosto', 9: 'Settembre', 10: 'Ottobre', 11: 'Novembre', 12: 'Dicembre'}
            
            df_r_opt = df_r.copy()
            df_r_opt['Data_date'] = df_r_opt['Data'].dt.date
            date_uniche = sorted(df_r_opt['Data_date'].unique(), reverse=True)
            
            date_options = {}
            for d in date_uniche:
                g_str = giorni_sett[d.weekday()]
                m_str = mesi[d.month]
                num_prove = len(df_r_opt[df_r_opt['Data_date'] == d])
                lbl = f"🗓️ {g_str} {d.day} {m_str} {d.year} — ({num_prove} prove)"
                date_options[d] = lbl
                
            sel_giorno = st.selectbox("Seleziona la data dell'allenamento:", date_uniche, format_func=lambda x: date_options[x])
            
            if sel_giorno:
                lbl_fmt = date_options[sel_giorno].replace('🗓️ ', '').split('—')[0].strip()
                st.markdown(f"#### 🏟️ Allenamento del {lbl_fmt}")
                st.markdown("<br>", unsafe_allow_html=True)
                
                df_day = df_r_opt[df_r_opt['Data_date'] == sel_giorno].copy()
                if not df_day.empty:
                    df_day = df_day.sort_values(by=['Distanza', 'Data']) # Mantieni eventuale ordine cronologico e alfabetico
                    df_day['Ripetizione'] = df_day.groupby(['Atleta', 'Distanza']).cumcount() + 1
                    pivot_day = df_day.pivot_table(index='Atleta', columns=['Distanza', 'Ripetizione'], values='Tempo', aggfunc='first')
                    # Flatten the MultiIndex of the columns
                    new_cols = []
                    for dist, rep in pivot_day.columns:
                        new_cols.append(f"{int(dist)}m - Pr. {rep}")
                    pivot_day.columns = new_cols
                    
                    st.dataframe(pivot_day.style.format(lambda x: f"{x:.2f}s" if pd.notnull(x) else " - "), use_container_width=True)
                else:
                    st.info("Nessuna prova in questa data.")
        else:
            st.info("Nessun dato registrato o presente nei filtri.")

elif st.session_state.current_page == "Atleti":
    from supabase_connector import get_atleti
    df_atleti = get_atleti()
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("<h3 style='margin-bottom:0;'>👥 ELENCO ATLETI</h3>", unsafe_allow_html=True)
    # Search bar e Arricchimento dati
    roster_data = []
    if not df_atleti.empty:
        for _, row in df_atleti.iterrows():
            atl = row['nome_completo']
            f_url = row.get('foto_url', '')
            
            mask_r = df_running['Atleta'] == atl
            mask_v = df_vbt['Atleta'] == atl
            last_r = df_running[mask_r]['Data'].max() if len(df_running[mask_r]) > 0 else pd.NaT
            last_v = df_vbt[mask_v]['Data'].max() if len(df_vbt[mask_v]) > 0 else pd.NaT
            
            last_d = max(last_r, last_v) if pd.notnull(last_r) and pd.notnull(last_v) else (last_r if pd.notnull(last_r) else last_v)
            days_ago = (pd.Timestamp.now().tz_localize(None) - last_d).days if pd.notnull(last_d) else 999
            
            if days_ago <= 3:
                stato = "🔥 Picco"
                color = "#E8FF3A"
                c_badge = "background: rgba(232,255,58,0.1); color: #E8FF3A;"
            elif days_ago <= 10:
                stato = "✓ Buona"
                color = "#16a34a"
                c_badge = "background: rgba(22,163,74,0.1); color: #16a34a;"
            elif days_ago <= 30:
                stato = "⚠ Monitor"
                color = "#FFB347"
                c_badge = "background: rgba(255,179,71,0.1); color: #FFB347;"
            else:
                stato = "🔴 Fermo"
                color = "#FF6B6B"
                c_badge = "background: rgba(255,107,107,0.1); color: #FF6B6B;"
                
            atl_run = df_running[mask_r]
            highlight_txt = "-"
            if len(atl_run) > 0:
                if 100 in atl_run['Distanza'].values:
                    pb = atl_run[atl_run['Distanza'] == 100]['Tempo'].min()
                    highlight_txt = f"{pb:.2f}s (100m)"
                elif 60 in atl_run['Distanza'].values:
                    pb = atl_run[atl_run['Distanza'] == 60]['Tempo'].min()
                    highlight_txt = f"{pb:.2f}s (60m)"
            
            if highlight_txt == "-" and len(df_vbt[mask_v]) > 0:
                 highlight_txt = f"{len(df_vbt[mask_v])} sess. VBT"

            roster_data.append({
                'nome': atl,
                'foto': f_url,
                'stato': stato,
                'color': color,
                'c_badge': c_badge,
                'highlight': highlight_txt
            })
            
        roster_df = pd.DataFrame(roster_data)

        # Barra di ricerca se > 10
        if len(roster_df) > 10:
            search_q = st.text_input("🔍 Cerca Atleta", placeholder="Cerca nome...", label_visibility="collapsed")
            if search_q:
                roster_df = roster_df[roster_df['nome'].str.contains(search_q, case=False, na=False)]
        
        # Grid System
        cols = st.columns(3)
        for i, row in roster_df.iterrows():
            col = cols[i % 3]
            with col.container(border=True):
                if pd.notna(row['foto']) and str(row['foto']).strip() != "":
                    av_html = f'''<div style="width:55px; height:55px; border-radius:50%; border:2px solid {row["color"]}; overflow:hidden; margin-bottom:10px;">
                                    <img src="{row["foto"]}" style="width:100%; height:100%; object-fit:cover; display:block;">
                                  </div>'''
                else:
                    inz = "".join([n[0] for n in row['nome'].split()[:2]]).upper()
                    av_html = f'''<div style="width:55px; height:55px; border-radius:50%; border:2px solid {row["color"]}; background:#14171E; color:#FFF; font-family:'DM Mono', monospace; font-size:20px; font-weight:bold; display:flex; align-items:center; justify-content:center; margin-bottom:10px;">
                                    {inz}
                                  </div>'''
                
                st.markdown(f'''
                <div>
                    {av_html}
                    <div style="font-weight:600; font-size:1.1em; line-height:1.2; margin-bottom:2px;">{row["nome"]}</div>
                    <div style="font-size:0.8em; color:rgba(255,255,255,0.5); margin-bottom:8px;">Velocità</div>
                    <div style="display:flex; align-items:center; gap:8px;">
                        <span style="font-size:10px; padding:2px 6px; border-radius:4px; font-family:'DM Mono'; {row["c_badge"]}">{row["stato"]}</span>
                        <span style="font-size:11px; color:#fff; font-family:'DM Mono'; font-weight:bold;">{row["highlight"]}</span>
                    </div>
                </div>
                ''', unsafe_allow_html=True)
                
                if st.button("Vai", key=f"nav_{row['nome']}", use_container_width=True):
                    st.session_state.app_athlete = row['nome']
                    st.session_state.current_page = "Dettaglio Atleta"
                    st.session_state.navigated_to_athlete = True
                    st.rerun()

        if st.session_state.authenticated:
            @st.dialog("Registra Nuovo Atleta")
            def render_new_atleta_modal():
                with st.form("new_atleta_form", clear_on_submit=True):
                    st.markdown("**Inserisci il nuovo membro della squadra**")
                    n1, n2 = st.columns(2)
                    nome = n1.text_input("Nome")
                    cognome = n2.text_input("Cognome")
                    spec = st.text_input("Specialità (es. Velocità, Salti)", value="Velocità")
                    if st.form_submit_button("✅ Registra Atleta", type="primary", use_container_width=True):
                        if nome.strip() and cognome.strip():
                            from supabase_connector import upsert_atleta
                            upsert_atleta(nome.strip(), cognome.strip(), spec.strip())
                            st.success("✅ Completato! (Ricaricamento...)")
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error("⚠️ Inserisci Nome e Cognome.")
                            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("➕ Aggiungi Nuovo Atleta", use_container_width=True):
                render_new_atleta_modal()

# ──────────────────────────────────────────────────────────────────────
# DETTAGLIO ATLETA (TABS PRINCIPALI)
# ──────────────────────────────────────────────────────────────────────

if st.session_state.current_page == "Dettaglio Atleta" and selected_athlete != "Tutta la squadra":
    if st.session_state.get('navigated_to_athlete', False):
        import streamlit.components.v1 as components
        components.html("""
            <script>
                var parent = window.parent;
                if (parent) {
                    var mainView = parent.document.querySelector('.main');
                    if (mainView) {
                        mainView.scrollTo({top: 0, behavior: 'instant'});
                    }
                }
            </script>
        """, height=0, width=0)
        st.session_state.navigated_to_athlete = False

    tab_labels = ["⚡ Analisi Velocità", "💪 Forza (VBT)",
                  "📊 Predizioni ML", "⚖️ Transfer", "🏅 PB & Gare"]
    
    tabs = st.tabs(tab_labels)
    tab1, tab2, tab3, tab4, tab5 = tabs[0], tabs[1], tabs[2], tabs[3], tabs[4]


    # ══════════════════════════════════════════════════════════════════════
    # TAB 1 — ANALISI VELOCITÀ
    # ══════════════════════════════════════════════════════════════════════

    with tab1:
        if len(df_r) == 0:
            st.warning("Nessun dato di corsa nel periodo/filtri selezionati.")
        else:
            st.subheader("📈 Trend dei Tempi per Distanza")

            if selected_athlete == "Tutta la squadra":
                trend_df = df_r.groupby(['Data', 'Distanza'])['Tempo'].mean().reset_index()
                trend_df['Tipo'] = 'Media squadra'
            else:
                trend_df = df_r.copy()
                trend_df['Tipo'] = selected_athlete

            trend_parts = []
            for dist in sorted(trend_df['Distanza'].unique()):
                sub = trend_df[trend_df['Distanza'] == dist].sort_values('Data').copy()
                sub['Media Mobile (3 ses.)'] = sub['Tempo'].rolling(window=3, min_periods=1).mean()
                trend_parts.append(sub)

            if trend_parts:
                trend_all = pd.concat(trend_parts)
                trend_all['Distanza (m)'] = trend_all['Distanza'].astype(int).astype(str) + "m"

                hover_cols = None
                if 'Note' in trend_all.columns and selected_athlete != "Tutta la squadra":
                    hover_cols = ['Note']

                fig_trend = px.line(
                    trend_all, x='Data', y='Tempo', color='Distanza (m)', markers=True,
                    hover_data=hover_cols, title="Evoluzione Cronometrica Assoluta (Distanze Chiave)",
                    labels={'Tempo': 'Tempo (sec)', 'Data': 'Data Test'},
                    template=THEME_TEMPLATE, color_discrete_sequence=NEON_COLORS
                )
                for dist in sorted(trend_all['Distanza'].unique()):
                    sub = trend_all[trend_all['Distanza'] == dist].sort_values('Data')
                    fig_trend.add_trace(go.Scatter(
                        x=sub['Data'], y=sub['Media Mobile (3 ses.)'], mode='lines',
                        line=dict(dash='dot', width=2), name=f"{int(dist)}m (Trend)", opacity=0.7
                    ))
            
                # Nascondi le distanze meno comuni dalla visualizzazione base (evita l'effetto tela di ragno)
                for trace in fig_trend.data:
                    try:
                        name_str = trace.name
                        if 'Trend' in name_str:
                            d_val = int(name_str.replace("m (Trend)", ""))
                        else:
                            d_val = int(name_str.replace("m", ""))
                        # Lasciamo visibili le core distances classiche e nascondiamo le altre nella legenda
                        if d_val not in [60, 100, 150, 200, 300, 400]:
                            trace.visible = 'legendonly'
                    except:
                        pass
                    
                fig_trend.update_layout(height=500, hovermode='x unified',
                                         legend=dict(orientation='h', y=-0.15), margin=dict(t=50))
                st.plotly_chart(fig_trend, use_container_width=True)

            col_pb, col_distr = st.columns([1.2, 1])

            with col_pb:
                with st.expander("🏆 Mostra Classifica Personal Best (PB)", expanded=False):
                    if selected_athlete == "Tutta la squadra":
                        pb_df = df_r.loc[df_r.groupby(['Atleta', 'Distanza'])['Tempo'].idxmin()]
                        pb_pivot = pb_df.pivot_table(index='Atleta', columns='Distanza', values='Tempo', aggfunc='min')
                        pb_pivot.columns = [f"{int(c)}m" for c in pb_pivot.columns]
                        st.dataframe(pb_pivot.style.highlight_min(axis=0, color='#90e0ef')
                                     .highlight_max(axis=0, color='#fde2e4').format("{:.2f}s"),
                                     use_container_width=True, height=350)
                    else:
                        pb_df = df_r.groupby('Distanza').agg(
                            Miglior_Tempo=('Tempo', 'min'),
                            Data_Primo_PB=('Tempo', lambda x: df_r.loc[x.idxmin(), 'Data']),
                            Note=('Tempo', lambda x: df_r.loc[x.idxmin(), 'Note'] if 'Note' in df_r.columns else ""),
                            Tempo_Medio=('Tempo', 'mean'),
                            Prove_Totali=('Tempo', 'count'),
                        ).reset_index()
                        if 'Note' in pb_df.columns and pb_df['Note'].astype(str).str.strip().eq("").all():
                            pb_df = pb_df.drop(columns=['Note'])
                        pb_df['Distanza'] = pb_df['Distanza'].astype(int).astype(str) + "m"
                        pb_df['Data_Primo_PB'] = pb_df['Data_Primo_PB'].dt.strftime('%d/%m/%Y')
                        st.dataframe(pb_df.style.format({'Miglior_Tempo': '{:.2f}', 'Tempo_Medio': '{:.2f}'})
                                     .highlight_min(subset=['Miglior_Tempo'], color='#90e0ef'),
                                     use_container_width=True, height=350)

            with col_distr:
                with st.expander("📊 Consistenza delle Rilevazioni (Boxplot)", expanded=False):
                    df_r_copy = df_r.copy()
                    df_r_copy['Distanza (m)'] = df_r_copy['Distanza'].astype(int).astype(str) + "m"
                    fig_box = px.box(df_r_copy, x='Distanza (m)', y='Tempo', color='Distanza (m)',
                                      hover_data=['Note'] if 'Note' in df_r_copy.columns else None,
                                      template=THEME_TEMPLATE, title="Dispersione dei Tempi",
                                      labels={'Tempo': 'Tempo (sec)'},
                                      color_discrete_sequence=NEON_COLORS)
                    fig_box.update_layout(showlegend=False, height=350, margin=dict(t=50))
                    st.plotly_chart(fig_box, use_container_width=True)

            if selected_athlete != "Tutta la squadra":
                st.divider()
                with st.expander("📖 Esplora Storico Risultati Completo", expanded=False):
                    st.markdown("Tutte le prestazioni registrate dall'atleta, raggruppate per distanza. **Ordinate dalla più vecchia alla più recente.** *(I filtri distanze e date del menù laterale non influenzano questa tabella, quindi potrai vedere sempre lo storico completo).*")
                
                    df_storico = df_running[df_running['Atleta'] == selected_athlete].copy()
                    if not df_storico.empty:
                        df_storico = df_storico.sort_values('Data', ascending=True)
                        df_storico['Data'] = df_storico['Data'].dt.strftime('%d/%m/%Y')
                    
                        distanze = sorted(df_storico['Distanza'].unique())
                        for d in distanze:
                            sub_df = df_storico[df_storico['Distanza'] == d][['Data', 'Tempo', 'Note']]
                            migliore = sub_df['Tempo'].min()
                            num_prove = len(sub_df)
                            st.markdown(f"**🏃 {int(d)}m** — {num_prove} prove | PB: {migliore:.2f}s")
                            st.dataframe(sub_df, use_container_width=True, hide_index=True)
                    else:
                        st.info("Nessuna prova presente per questo atleta.")


    # ══════════════════════════════════════════════════════════════════════
    # TAB 2 — FORZA E POTENZA (VBT)
    # ══════════════════════════════════════════════════════════════════════

    with tab2:
        if len(df_v) == 0:
            st.warning("Nessun dato VBT nel periodo/filtri selezionati.")
        else:
            df_v_ex = df_v[df_v['Esercizio'] != 'General'].copy()
            if len(df_v_ex) == 0:
                st.info("Solo record 'General' presenti. Seleziona esercizi specifici nella sidebar.")
            else:
                col_vbt1, col_vbt2 = st.columns(2)

                with col_vbt1:
                    st.subheader("🏋️ Massimali Stimati (Picco)")
                    with st.expander("Dettagli grafici a barre"):
                        st.write("Mostra i picchi massimi registrati nel periodo per ciascun esercizio.")

                    if selected_athlete == "Tutta la squadra":
                        agg_df = df_v_ex.groupby(['Atleta', 'Esercizio']).agg(
                            Potenza_max=('Potenza_max', 'max'), Forza_max=('Forza_max', 'max')
                        ).reset_index()
                        color_col = 'Atleta'
                    else:
                        agg_df = df_v_ex.groupby('Esercizio').agg(
                            Potenza_max=('Potenza_max', 'max'), Forza_max=('Forza_max', 'max')
                        ).reset_index()
                        color_col = 'Esercizio'

                    fig_bar = px.bar(agg_df, x='Esercizio', y='Potenza_max', color=color_col,
                                      barmode='group', template=THEME_TEMPLATE,
                                      title="Massima Espressione di Potenza (Watt)",
                                      color_discrete_sequence=NEON_COLORS)
                    fig_bar.update_layout(height=CHART_HEIGHT - 50)
                    st.plotly_chart(fig_bar, use_container_width=True)

                    fig_forza = px.bar(agg_df, x='Esercizio', y='Forza_max', color=color_col,
                                        barmode='group', template=THEME_TEMPLATE,
                                        title="Massima Espressione di Forza (Newton)",
                                        color_discrete_sequence=NEON_COLORS)
                    fig_forza.update_layout(height=CHART_HEIGHT - 50)
                    st.plotly_chart(fig_forza, use_container_width=True)

                with col_vbt2:
                    st.subheader("📉 Profilo Forza–Velocità")
                    sel_ex = st.selectbox("Analizza la curva di un esercizio:",
                                           options=sorted(df_v_ex['Esercizio'].unique()))
                    scatter_df = df_v_ex[df_v_ex['Esercizio'] == sel_ex].dropna(subset=['Carico', 'Vel_media'])

                    if len(scatter_df) > 0:
                        fig_scatter = px.scatter(
                            scatter_df, x='Carico', y='Vel_media',
                            color='Atleta' if selected_athlete == "Tutta la squadra" else None,
                            size='Potenza_media', template=THEME_TEMPLATE, hover_data=['Data'],
                            labels={'Carico': 'Carico (kg)', 'Vel_media': 'Velocità Media (m/s)'},
                            trendline='ols', color_discrete_sequence=NEON_COLORS
                        )
                        fig_scatter.update_layout(height=CHART_HEIGHT)
                        st.plotly_chart(fig_scatter, use_container_width=True)

                        from scipy import stats
                        slope, intercept, r_val, p_val, se = stats.linregress(scatter_df['Carico'], scatter_df['Vel_media'])
                        with st.expander("📊 Dettagli Modello (M.Q.O.)"):
                            st.code(f"Velocità = {slope:.4f} * Carico(kg) + {intercept:.2f}\nR² (Affidabilità): {r_val**2:.3f}")
                    else:
                        st.info("Dati insufficienti per tracciare la curva.")

                st.divider()
                st.subheader("📈 Progressione VBT Temporale")
                metric_choice = st.radio("Metrica:", ['Vel_media', 'Vel_max', 'Potenza_media', 'Potenza_max', 'Forza_max'],
                                          format_func=lambda x: x.replace('_', ' ').title(), horizontal=True)
                vbt_trend = df_v_ex.dropna(subset=['Data', metric_choice])
                if len(vbt_trend) > 0:
                    vbt_agg = vbt_trend.groupby(['Data', 'Esercizio'])[metric_choice].mean().reset_index()
                    fig_vbt_trend = px.line(vbt_agg, x='Data', y=metric_choice, color='Esercizio',
                                             markers=True, template=THEME_TEMPLATE,
                                             color_discrete_sequence=NEON_COLORS)
                    fig_vbt_trend.update_layout(height=400)
                    st.plotly_chart(fig_vbt_trend, use_container_width=True)


    # ══════════════════════════════════════════════════════════════════════
    # TAB 3 — CORRELAZIONI E PROIEZIONI
    # ══════════════════════════════════════════════════════════════════════

    with tab3:
        st.subheader("🔗 Correlazione: Palestra ↔ Pista")
        st.markdown("Verifica se un miglioramento di forza/potenza corrisponde a un calo cronometrico.")

        col_corr1, col_corr2 = st.columns(2)
        with col_corr1:
            corr_dist = st.selectbox("Corsa: Distanza (Asse Y)",
                                       options=[d for d in sorted(df_running['Distanza'].unique()) if d <= 200],
                                       index=min(2, len([d for d in sorted(df_running['Distanza'].unique()) if d <= 200]) - 1),
                                       format_func=lambda x: f"{int(x)}m")
        with col_corr2:
            corr_metric = st.selectbox("Palestra: Metrica VBT (Asse X)",
                                        options=['Potenza_max', 'Vel_max', 'Forza_max', 'Carico'],
                                        format_func=lambda x: x.replace('_', ' ').title())

        df_r_all = df_running[df_running['Distanza'] == corr_dist].copy()
        df_r_all['Mese'] = df_r_all['Data'].dt.to_period('M').astype(str)
        running_monthly = df_r_all.groupby(['Atleta', 'Mese'])['Tempo'].mean().reset_index()

        df_v_all = df_vbt[df_vbt['Esercizio'] != 'General'].copy()
        df_v_all['Mese'] = df_v_all['Data'].dt.to_period('M').astype(str)
        vbt_monthly = df_v_all.groupby(['Atleta', 'Mese'])[corr_metric].mean().reset_index()

        merged = running_monthly.merge(vbt_monthly, on=['Atleta', 'Mese'], how='inner')

        if len(merged) > 3:
            fig_corr = px.scatter(merged, x=corr_metric, y='Tempo', color='Atleta',
                                   hover_data=['Mese'], template=THEME_TEMPLATE,
                                   title="Analisi di Correlazione Assoluta",
                                   trendline='ols', color_discrete_sequence=NEON_COLORS)
            fig_corr.update_layout(height=450)
            st.plotly_chart(fig_corr, use_container_width=True)

            from scipy import stats as sp_stats
            slope, intercept, r_val, p_val, se = sp_stats.linregress(merged[corr_metric], merged['Tempo'])
            if slope < 0 and p_val < 0.05:
                st.success(f"✅ Relazione inversa forte (Forza↑ → Tempo↓). R²={r_val**2:.2f}, p={p_val:.3f}")
            elif slope < 0:
                st.info(f"ℹ️ Tendenza corretta, dati non statisticamente forti (p={p_val:.3f}).")
            else:
                st.warning("⚠️ Nessun transfer positivo rilevato nel periodo.")
        else:
            st.info("Punti insufficienti per la correlazione.")

        st.divider()
        st.subheader("🔮 Modello Lineare di Predizione (Gara)")
        available_dists = sorted(df_running['Distanza'].unique())
        short_dists = [d for d in available_dists if d <= 100]
        long_dists = [d for d in available_dists if d >= 60]

        if len(short_dists) >= 2 and len(long_dists) >= 1:
            col_p1, col_p2, col_p3 = st.columns(3)
            feat1 = col_p1.selectbox("Parziale 1", short_dists, index=0, format_func=lambda x: f"{int(x)}m")
            feat2 = col_p2.selectbox("Parziale 2", [d for d in short_dists if d != feat1], index=0, format_func=lambda x: f"{int(x)}m")
            target = col_p3.selectbox("Target Gara", [d for d in long_dists if d > max(feat1, feat2)], format_func=lambda x: f"{int(x)}m")

            df_f1 = df_running[df_running['Distanza'] == feat1][['Data', 'Atleta', 'Tempo']].rename(columns={'Tempo': 't1'})
            df_f2 = df_running[df_running['Distanza'] == feat2][['Data', 'Atleta', 'Tempo']].rename(columns={'Tempo': 't2'})
            df_tgt = df_running[df_running['Distanza'] == target][['Data', 'Atleta', 'Tempo']].rename(columns={'Tempo': 'target'})
            df_model = df_f1.merge(df_f2, on=['Data', 'Atleta']).merge(df_tgt, on=['Data', 'Atleta'])

            if len(df_model) >= 5:
                X, y = df_model[['t1', 't2']].values, df_model['target'].values
                model = LinearRegression().fit(X, y)
                score = model.score(X, y)
                with st.expander(f"📚 Modello di Predizione (R² = {score:.2f})"):
                    df_model['Previsto'] = model.predict(X)
                    fig_pred = px.scatter(df_model, x='target', y='Previsto', template=THEME_TEMPLATE,
                                           title="Reale vs Stimato")
                    m_min = min(df_model['target'].min(), df_model['Previsto'].min())
                    m_max = max(df_model['target'].max(), df_model['Previsto'].max())
                    fig_pred.add_trace(go.Scatter(x=[m_min, m_max], y=[m_min, m_max], mode='lines',
                                                   line=dict(dash='dash'), name='Previsione Perfetta'))
                    st.plotly_chart(fig_pred, use_container_width=True)

                st.markdown("##### Simulatore Predittivo")
                pred_col1, pred_col2 = st.columns(2)
                val_t1 = pred_col1.number_input(f"{int(feat1)}m (sec):", value=float(df_model['t1'].median()), step=0.05)
                val_t2 = pred_col2.number_input(f"{int(feat2)}m (sec):", value=float(df_model['t2'].median()), step=0.05)
                predicted = model.predict([[val_t1, val_t2]])[0]
                st.info(f"🏁 Potenziale sui **{int(target)}m** stimato: **{predicted:.2f} secondi**")
            else:
                st.warning("Almeno 5 corrispondenze necessarie (stessa data + atleta su tutte le distanze).")
        else:
            st.error("Distanze insufficienti.")

    # ══════════════════════════════════════════════════════════════════════
    # TAB 4 — TRANSFER E CORRELAZIONE (GYM ↔ CORSA)
    # ══════════════════════════════════════════════════════════════════════

    with tab4:
        st.subheader("⚖️ Analisi Transfer (Impatto Palestra sulla Velocità)")
        st.markdown("Questa sezione accoppia i carichi sollevati in palestra (es. Squat) con i tempi registrati in pista raggruppati mensilmente. Ti aiuta a comprendere matematicamente se all'aumentare dei tuoi massimali in sala pesi, diminuisce il tempo di scatto (Transfer Positivo).", help="I dati vengono raggruppati per Atleta e per Mese, questo per colmare la mancata simultaneità dei due allenamenti (spesso ci si allena in sala pesi in giornate diverse rispetto alla pista).")

        if len(df_v) == 0 or len(df_r) == 0:
            st.warning("Servono sia dati di corsa che dati di palestra per calcolare il transfer.")
        else:
            col_c1, col_c2 = st.columns(2)
            vbt_exercises = sorted(df_v['Esercizio'].dropna().unique())
            run_distances = [d for d in sorted(df_r['Distanza'].unique()) if d >= 20]
        
            default_vbt = "Squat" if "Squat" in vbt_exercises else (vbt_exercises[0] if vbt_exercises else "")
            ex_choice = col_c1.selectbox("Esercizio VBT Riferimento", vbt_exercises, index=vbt_exercises.index(default_vbt) if default_vbt in vbt_exercises else 0)
        
            default_run = 60 if 60 in run_distances else (run_distances[0] if run_distances else 20)
            dist_choice = col_c2.selectbox("Distanza di Sprint (Transfer)", run_distances, index=run_distances.index(default_run) if default_run in run_distances else 0)

            df_r_sub = df_r[df_r['Distanza'] == dist_choice].copy()
            df_v_sub = df_v[df_v['Esercizio'] == ex_choice].copy()
        
            if len(df_r_sub) > 0 and len(df_v_sub) > 0:
                df_r_sub['Mese'] = df_r_sub['Data'].dt.to_period('M')
                df_v_sub['Mese'] = df_v_sub['Data'].dt.to_period('M')

                aggr_r = df_r_sub.groupby(['Atleta', 'Mese'])['Tempo'].mean().reset_index()
                aggr_v = df_v_sub.groupby(['Atleta', 'Mese'])['Carico'].mean().reset_index()

                merged = pd.merge(aggr_r, aggr_v, on=['Atleta', 'Mese'], how='inner')
                merged['Mese_Str'] = merged['Mese'].astype(str)
            
                if len(merged) < 3:
                    st.info("Punti di congiunzione insufficienti per l'esercizio e sprint scelti nello stesso mese. Servono almeno 3 campioni medi mensili per attivare l'intelligenza analitica. Prova altre distanze/esercizi.")
                else:
                    import scipy.stats as stats
                    fig_corr = px.scatter(
                        merged, x='Carico', y='Tempo', color='Mese_Str',
                        hover_data=['Atleta'], trendline="ols",
                        title=f"Scatter Plot: {ex_choice} vs {dist_choice}m (Medie Mensili)",
                        labels={'Carico': f'Carico Medio Sollevato (kg)', 'Tempo': f'Tempo Medio {dist_choice}m (s)', 'Mese_Str': 'Periodo'},
                        template=THEME_TEMPLATE
                    )
                    fig_corr.update_layout(height=450)
                
                    r_val, p_val = stats.pearsonr(merged['Carico'], merged['Tempo'])
                
                    st.plotly_chart(fig_corr, use_container_width=True)
                
                    # AI Testo Intepretativo
                    st.markdown("### 🤖 Sintesi Intelligenza Analitica")
                    if r_val < -0.3:
                        txt = f"**Transfer Positivo (r = {r_val:.2f})**: C'è una correlazione inversa rilevante. I dati numerici indicano che all'aumentare dei carichi ({ex_choice}), i tempi sullo sprint ({dist_choice}m) tendono organicamente a **ridursi**."
                    elif r_val > 0.3:
                        txt = f"**Transfer Negativo (r = {r_val:.2f})**: Attenzione, i dati indicano che storicamente, nelle finestre mensili con carichi di {ex_choice} più alti, i tempi sui {dist_choice}m si sono **alzati**. Valuta un possibile sovraffaticamento o perdita di brillantezza reattiva."
                    else:
                        txt = f"**Risposta Neutra (r = {r_val:.2f})**: In questo storico, la forza aspecifica ({ex_choice}) è variata senza impattare linearmente o costantemente sull'espressione pura di sprint ({dist_choice}m)."
                    
                    st.info(txt)
            else:
                st.warning("Non ci sono dati a sufficienza per operare questa correlazione specifica.")

    # ══════════════════════════════════════════════════════════════════════
    # TAB 5 — PB & GARE
    # ══════════════════════════════════════════════════════════════════════

    with tab5:
        st.subheader("🏅 Storico Gare Ufficiali e Personal Best")
    
        from supabase_connector import get_gare_ufficiali
        if selected_athlete == "Tutta la squadra":
            df_gare = get_gare_ufficiali()
        else:
            # We need the athlete id. 
            # atleta_info should be available in the 'if selected_athlete != "Tutta la squadra"' scope.
            if "atleta_info" in locals() and atleta_info:
                df_gare = get_gare_ufficiali(atleta_info["id"])
            else:
                df_gare = pd.DataFrame()

        if st.session_state.authenticated and selected_athlete != "Tutta la squadra":
            @st.dialog("Inserisci Risultato di Gara")
            def render_pb_modal():
                with st.form("form_gara", clear_on_submit=True):
                    g_spec = st.text_input("Specialità (es. 100m, Lungo)")
                    g_tempo = st.text_input("Tempo/Misura (es. 10.89, 7.54)")
                    g_vento = st.text_input("Vento (es. +1.2)", placeholder="opzionale")
                    g_luogo = st.text_input("Città/Luogo", placeholder="opzionale")
                    g_data = st.date_input("Data della Gara")
                
                    if st.form_submit_button("✅ Salva Risultato", type="primary", use_container_width=True):
                        if g_spec.strip() and g_tempo.strip():
                            from supabase_connector import insert_gara_ufficiale
                            ok = insert_gara_ufficiale(selected_athlete, g_spec.strip(), g_tempo.strip(), g_vento.strip(), g_luogo.strip(), g_data.strftime("%Y-%m-%d"))
                            if ok:
                                st.success("✅ Risultato di gara registrato!")
                                st.cache_data.clear()
                                st.rerun()
                            else:
                                st.error("Errore nel salvataggio del PB.")
                        else:
                            st.error("Inserisci Specialità e Tempo.")
        
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("➕ Registra Nuovo PB/Gara", type="primary", use_container_width=True):
                render_pb_modal()
            
        st.markdown("<br>", unsafe_allow_html=True)
        if df_gare.empty:
            st.info("Nessuna gara ufficiale registrata.")
        else:
            df_gare_disp = df_gare.copy()
            if "atleta_id" in df_gare_disp.columns:
                df_gare_disp = df_gare_disp.drop(columns=["atleta_id"])
        
            # Pretty display in dataframe
            st.dataframe(df_gare_disp, use_container_width=True, hide_index=True)

    st.divider()

    # ──────────────────────────────────────────────────────────────────────
    # ESPORTAZIONE DATI (CSV)
    # ──────────────────────────────────────────────────────────────────────
    st.markdown("""
    <style>
    div[data-testid="stExpander"] {
        border-color: rgba(232,255,58,0.3) !important;
    }
    div[data-testid="stExpander"] summary {
        color: #E8FF3A !important;
    }
    </style>
    """, unsafe_allow_html=True)

    with st.expander("📥 Export Dati (CSV)"):
        st.markdown("Scarica i record filtrati (per atleta e date selezionate).")
        e_col1, e_col2, e_col3 = st.columns([1,1,2])
        with e_col1:
            st.download_button("🏃 Scarica CSV Corsa", data=convert_df_to_csv(df_r), file_name='dataset_corsa.csv', mime='text/csv')
        with e_col2:
            st.download_button("🏋️ Scarica CSV VBT", data=convert_df_to_csv(df_v), file_name='dataset_vbt.csv', mime='text/csv')


    st.caption("Dashboard Atletica · v3 Cloud · Powered by Supabase + Streamlit")

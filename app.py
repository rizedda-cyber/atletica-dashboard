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
from plotly.subplots import make_subplots
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
    
    /* ── FIX MOBILE LOGIN: tastiera non deve coprire il PIN box ──
       Su mobile quando si apre la tastiera virtuale il viewport si comprime.
       Usiamo scroll-padding e un layout che porta il form in cima. */
    @media (max-width: 768px) {
        /* Evita che la cover spinga il form troppo in basso */
        .cover {
            padding: 20px 16px !important;
            margin-bottom: 12px !important;
        }
        .cover-logo {
            width: 80px !important;
            height: 80px !important;
            margin-bottom: 12px !important;
        }
        .cover-title { font-size: 36px !important; }
        .cover-subtitle { font-size: 13px !important; margin-bottom: 20px !important; }
        /* Il form di login è posizionato più in alto */
        [data-testid="stVerticalBlock"] > [data-testid="stHorizontalBlock"] {
            align-items: flex-start !important;
        }
        /* Bottone Accedi: sticky in basso nel form così rimane visibile sopra la tastiera */
        [data-testid="stFormSubmitButton"] > button {
            position: sticky !important;
            bottom: 8px !important;
            z-index: 9999 !important;
        }
    }
    
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
    
    /* Nascondi solo i menu secondari tecnici (Deploy/Settings) in alto a destra, senza oscurare il contenitore del bottone menu sinistro */
    .stAppDeployButton,   
    .stToolbarActions {
        display: none !important;
        visibility: hidden !important;
    }

    /* Pulsante Hamburger (Ripristina funzionalità nativa touch ingrandendolo a dismisura) */
    [data-testid="collapsedControl"],
    [data-testid="stSidebarCollapsedControl"] {
        background-color: #E8FF3A !important;
        border-radius: 50% !important;
        padding: 5px !important;
        margin: 5px !important;
        opacity: 1 !important;
        box-shadow: 0 4px 15px rgba(232,255,58,0.6) !important;
        border: 2px solid #0A0D14 !important;
        transform: scale(1.6) translate(5px, 5px) !important;
        transition: all 0.2s ease;
        z-index: 999999 !important;
        display: block !important;
    }
    
    [data-testid="collapsedControl"] svg,
    [data-testid="stSidebarCollapsedControl"] svg {
        color: #0A0D14 !important;
        fill: #0A0D14 !important;
        display: block !important;
    }
    
    [data-testid="collapsedControl"]:hover,
    [data-testid="stSidebarCollapsedControl"]:hover {
        background-color: #d1e82e !important;
        transform: scale(1.8) translate(5px, 5px) !important;
    }

    /* Pulsante COMPRIMI MENU (Dentro la Sidebar) */
    section[data-testid="stSidebar"] header button {
        background-color: #FF4B4B !important;
        border-radius: 50% !important;
        padding: 5px !important;
        border: 2px solid #0A0D14 !important;
        transform: scale(1.3) !important;
        margin-left: auto;
    }
    section[data-testid="stSidebar"] header button svg {
        color: white !important;
        fill: white !important;
        display: block !important;
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
    .kpi-icon { position: absolute; right: -5px; bottom: -15px; font-size: 70px; opacity: 0.08; transform: rotate(-15deg); user-select: none; pointer-events: none; text-shadow: none; }
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

    /* ── FIX DUPLICATO NOME PROFILO: Evita duplicazione durante scroll ──
       Questo assicura che il nome dell'atleta non venga renderizzato due volte */
    main [data-testid="stMainBlockContainer"] h1:nth-of-type(2) {
        display: none !important;
    }

    @media (min-width: 768px) {
        .mobile-divider {
            display: none !important;
        }
    }
    @media (max-width: 767px) {
        .mobile-divider {
            border: none;
            border-top: 1px dashed rgba(232, 255, 58, 0.4);
            margin: 24px 0 16px 0;
            width: 100%;
        }
    }
    
    /* ── SMOOTH NAV: elimina flash-of-content durante cambio pagina ── */
    [data-testid="stMainBlockContainer"] {
        scroll-behavior: smooth;
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
if "is_athlete_session" not in st.session_state:
    st.session_state.is_athlete_session = False
if "logged_athlete_name" not in st.session_state:
    st.session_state.logged_athlete_name = None
if "current_page" not in st.session_state:
    st.session_state.current_page = "Home"
if "page_just_changed" not in st.session_state:
    st.session_state.page_just_changed = False

# ── HACK: Scroll-to-top puro HTML e Autochiusura ──
if st.session_state.page_just_changed:
    # 1. Autofocus Input (Scroll to top garantito dai browser su form elements muti)
    # 2. CSS Animation per nascondere visivamente l'overlay sidebar su terminali mobile per far vedere il contenuto aggiornato
    st.markdown("""
        <input type="text" autofocus style="position:absolute; top:0; left:0; opacity:0; width:1px; height:1px; z-index:-1; pointer-events:none;">
    """, unsafe_allow_html=True)
    
    st.session_state.page_just_changed = False



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
    
    # JS: quando il PIN input riceve il focus (tastiera si apre su mobile),
    # scrolla in modo che il bottone Accedi rimanga visibile sopra la tastiera.
    import streamlit.components.v1 as components
    components.html("""
    <script>
    (function() {
        function fixLoginScroll() {
            var parent = window.parent;
            if (!parent) return;
            // Trova tutti gli input di tipo password nella pagina padre
            var inputs = parent.document.querySelectorAll('input[type="password"]');
            inputs.forEach(function(inp) {
                inp.addEventListener('focus', function() {
                    // Scrolla la pagina principale verso il basso per portare
                    // il bottone Login in vista sopra la tastiera
                    setTimeout(function() {
                        var submitBtn = parent.document.querySelector('[data-testid="stFormSubmitButton"]');
                        if (submitBtn) {
                            submitBtn.scrollIntoView({behavior: 'smooth', block: 'center'});
                        }
                    }, 350);
                });
            });
        }
        // Ritarda l'attacco del listener per attendere il DOM di Streamlit
        setTimeout(fixLoginScroll, 800);
    })();
    </script>
    """, height=0, scrolling=False)
    
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.container(border=True):
            st.markdown("<h4 style='text-align: center;'>Login Squadra</h4>", unsafe_allow_html=True)
            st.markdown("<p style='text-align:center; color:rgba(255,255,255,0.4); font-size:0.85em;'>PIN squadra · PIN personale · Password admin</p>", unsafe_allow_html=True)
            with st.form("login_form"):
                pin_input = st.text_input("Codice di Accesso", type="password", placeholder="PIN o Password...", label_visibility="collapsed", key="pin_field")
                submitted_login = st.form_submit_button("🔐 Accedi", type="primary", use_container_width=True)
            if submitted_login:
                pin_str = pin_input.strip()
                # 1. CONTROLLO ADMIN (Precedenza massima)
                admin_pass = get_admin_password().strip()
                if admin_pass and pin_str == admin_pass:
                    st.session_state.authenticated = True
                    st.session_state.is_admin = True
                    st.session_state.is_athlete_session = False
                    st.session_state.logged_athlete_name = None
                    st.rerun()

                # 2. CONTROLLO SQUADRA
                elif pin_str == get_team_pin().strip():
                    st.session_state.authenticated = True
                    st.session_state.is_admin = False
                    st.session_state.is_athlete_session = False
                    st.session_state.logged_athlete_name = None
                    st.rerun()

                # 3. CONTROLLO PIN PERSONALE ATLETA
                else:
                    from supabase_connector import get_atleta_by_pin
                    atleta_trovato = get_atleta_by_pin(pin_str)
                    if atleta_trovato:
                        st.session_state.authenticated = True
                        st.session_state.is_admin = False
                        st.session_state.is_athlete_session = True
                        st.session_state.logged_athlete_name = atleta_trovato["nome_completo"]
                        st.session_state.app_athlete = atleta_trovato["nome_completo"]
                        st.session_state.current_page = "Dettaglio Atleta"
                        st.session_state.page_just_changed = True
                        st.rerun()
                    else:
                        st.error("❌ Codice errato")
    st.stop()  # Ferma il caricamento dell'app finché non c'è login

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

last_active_dates = {}
if not df_running.empty:
    last_r = df_running.groupby('Atleta')['Data'].max().to_dict()
    last_active_dates.update(last_r)
if not df_vbt.empty:
    last_v = df_vbt.groupby('Atleta')['Data'].max().to_dict()
    for atl, data in last_v.items():
        if atl in last_active_dates and pd.notnull(last_active_dates[atl]) and pd.notnull(data):
            last_active_dates[atl] = max(last_active_dates[atl], data)
        elif pd.notnull(data):
            last_active_dates[atl] = data

def get_sort_key(atl):
    dt = last_active_dates.get(atl)
    if pd.isnull(dt): return (0, atl)
    return (dt.timestamp(), atl)

all_athletes_set = set(df_running['Atleta'].unique()) if not df_running.empty else set()
if not df_vbt.empty: all_athletes_set |= set(df_vbt['Atleta'].unique())
all_athletes = sorted(list(all_athletes_set), key=lambda x: (-get_sort_key(x)[0], x))

with st.sidebar:
    st.markdown("### 🏃 Menu Navigazione")
    
    st.markdown("<br>", unsafe_allow_html=True)
    # Se l'atleta è in sessione personale, mostra il badge di stato
    if st.session_state.is_athlete_session:
        nome_corto = st.session_state.logged_athlete_name.split()[0] if st.session_state.logged_athlete_name else "Atleta"
        st.markdown(f"<div style='padding:10px; background:rgba(232,255,58,0.08); border:1px solid rgba(232,255,58,0.3); border-radius:8px; text-align:center; margin-bottom:8px;'>"
                    f"<div style='font-size:0.75em; color:rgba(255,255,255,0.4); font-family:DM Mono; letter-spacing:1px;'>ACCESSO PERSONALE</div>"
                    f"<div style='font-weight:700; color:#E8FF3A;'>{nome_corto}</div></div>", unsafe_allow_html=True)

    # Pulsanti di navigazione - Sempre visibili
    if st.button("🏠 Home Squadra", use_container_width=True, type="primary" if st.session_state.current_page == "Home" else "secondary"):
        st.session_state.current_page = "Home"
        st.session_state.app_athlete = "Tutta la squadra"
        st.session_state.page_just_changed = True
        st.rerun()

    if st.button("👥 Tutti gli Atleti", use_container_width=True, type="primary" if st.session_state.current_page == "Atleti" else "secondary"):
        st.session_state.current_page = "Atleti"
        st.session_state.app_athlete = "Tutta la squadra"
        st.session_state.page_just_changed = True
        st.rerun()

    if st.button("➕ Inserisci Allenamento", use_container_width=True, type="primary" if st.session_state.current_page == "Inserimento" else "secondary"):
        st.session_state.current_page = "Inserimento"
        st.session_state.page_just_changed = True
        st.rerun()

    # ── PULSANTE PROFILO ATLETA ──────────────────────────────────────
    if st.session_state.is_athlete_session:
        if st.session_state.current_page == "Dettaglio Atleta":
            # Già sulla pagina del profilo - mostra bottone statico
            st.button("👤 Dettaglio Atleta", use_container_width=True, type="primary")
        else:
            # Su altre pagine - offri bottone per tornare al profilo
            nome_atleta = st.session_state.logged_athlete_name
            if st.button(f"👤 Torna al Mio Profilo", use_container_width=True, type="primary"):
                st.session_state.current_page = "Dettaglio Atleta"
                st.session_state.app_athlete = nome_atleta
                st.session_state.page_just_changed = True
                st.rerun()

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

    # ── PANNELLO ADMIN: GESTIONE PIN ──────────────────────────────────
    if st.session_state.is_admin and DATA_SOURCE == "cloud":
        st.divider()
        with st.expander("🔑 Gestione PIN Atleti", expanded=False):
            from supabase_connector import get_all_pins, set_atleta_pin
            df_pins = get_all_pins()
            if not df_pins.empty:
                for _, pr in df_pins.iterrows():
                    pin_val = pr.get('pin_personale') or ''
                    c1, c2, c3 = st.columns([3, 2, 1])
                    c1.markdown(f"<div style='padding-top:6px; font-size:0.9em;'>{pr['nome_completo']}</div>", unsafe_allow_html=True)
                    nuovo_pin = c2.text_input("", value=pin_val, placeholder="nessun PIN",
                                              label_visibility="collapsed", key=f"pin_inp_{pr['id']}")
                    if c3.button("💾", key=f"pin_save_{pr['id']}", help="Salva PIN"):
                        set_atleta_pin(pr['id'], nuovo_pin if nuovo_pin.strip() else None)
                        st.success(f"✅ PIN di {pr['nome_completo'].split()[0]} aggiornato")
                        st.rerun()
            else:
                st.info("Nessun atleta nel DB.")

    st.markdown("<br>", unsafe_allow_html=True)
    if st.session_state.is_athlete_session:
        role_label = f"🏃 {st.session_state.logged_athlete_name.split()[0]}"
    elif st.session_state.is_admin:
        role_label = "👑 Admin"
    else:
        role_label = "🟢 Ospite"
    if st.button(f"🚪 {role_label} — Esci", key="btn_logout", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.is_admin = False
        st.session_state.is_athlete_session = False
        st.session_state.logged_athlete_name = None
        st.session_state.current_page = "Home"
        st.session_state.app_athlete = "Tutta la squadra"
        st.rerun()

selected_athlete = st.session_state.app_athlete

# can_edit: True se si è admin o in sessione personale atleta.
# False se si è entrati solo con il PIN squadra (accesso in sola lettura).
can_edit = st.session_state.is_admin or st.session_state.is_athlete_session

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


if selected_athlete != "Tutta la squadra" and st.session_state.current_page == "Dettaglio Atleta":
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
        <div style="display: flex; align-items: flex-start; gap: 24px; margin-bottom: 8px;" data-athlete-profile="{primo_nome}">
            {avatar_html}
            <div style="padding-top: 5px; flex: 1;">
                <h1 style="margin: 0 0 6px 0; padding: 0; line-height: 1; font-size: 2.5em;">👋 {benvenuto_text}, {primo_nome}!</h1>
                <p style="margin: 0 0 10px 0; color: #E8FF3A; font-family: 'DM Mono', monospace; font-size: 0.9em; font-weight: 600; letter-spacing: 0.5px;">PROFILO ATLETA{eta_txt}{peso_txt}</p>
                <p style="margin: 0; color: rgba(255,255,255,0.7); font-size: 1.05em; line-height: 1.35; max-width: 600px;">
                    {bio_text if bio_text else "Nessuna biografia inserita."}
                </p>
            </div>
        </div>
    ''', unsafe_allow_html=True)
    
    if can_edit:
        btn1, btn2, empty_space = st.columns([2, 2, 6])
        if btn1.button("📸 Cambia Foto", key="cambia_foto_btn", use_container_width=True):
            render_photo_modal()
        if btn2.button("✏️ Modifica Dati", key="cambia_dati_btn", use_container_width=True):
            render_edit_profile_modal()

    # ── BANNER IMPOSTA PIN PERSONALE (permette a chi entra col PIN squadra di "reclamare" il profilo) ──
    if not st.session_state.is_admin and atleta_info and not atleta_info.get('pin_personale'):
        st.markdown("<br>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown(f"🔐 **Sei {atleta_info['nome_completo']}?** Imposta un PIN personale per proteggere il tuo profilo e poter modificare i tuoi dati e i tuoi tempi.")
            with st.form("form_set_pin", clear_on_submit=True):
                c_p1, c_p2 = st.columns(2)
                p1 = c_p1.text_input("Scegli un PIN", type="password", placeholder="Almeno 4 caratteri", key="new_pin_1")
                p2 = c_p2.text_input("Conferma PIN", type="password", placeholder="Ripeti il PIN", key="new_pin_2")
                if st.form_submit_button("🔐 Imposta PIN Personale", type="primary", use_container_width=True):
                    if not p1.strip() or len(p1.strip()) < 4:
                        st.error("⚠️ Il PIN deve essere di almeno 4 caratteri.")
                    elif p1.strip() != p2.strip():
                        st.error("⚠️ I PIN non coincidono.")
                    else:
                        from supabase_connector import set_atleta_pin
                        ok = set_atleta_pin(atleta_info['id'], p1.strip())
                        if ok:
                            st.success("✅ PIN personale impostato! Dalla prossima sessione potrai accedere direttamente con questo PIN.")
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error("❌ Errore nel salvataggio del PIN. Riprova.")
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
    
    # Mostra messaggio di conferma se c'è (persiste attraverso il rerun)
    if st.session_state.get('upload_success_msg'):
        msg = st.session_state.pop('upload_success_msg')
        st.success(msg)
        st.balloons()
    
    if DATA_SOURCE != "cloud":
        st.warning("⚠️ La dashboard sta usando i dati locali (Excel). L'inserimento richiede la connessione al cloud.")
    else:
        st.markdown("I dati vengono salvati direttamente nel cloud e saranno visibili a tutta la squadra.")
        
        tipo_form = st.radio("Seleziona attività:", ["🏃 Pista (corsa)", "🏋️ Palestra (VBT)"], horizontal=True, key="tipo_allenamento")
        st.divider()
        
        atleti_list = all_athletes
        default_atleta_idx = 0
        if selected_athlete != "Tutta la squadra" and selected_athlete in atleti_list:
            default_atleta_idx = atleti_list.index(selected_athlete)
            
        if tipo_form == "🏃 Pista (corsa)":
            from supabase_connector import insert_sessione_corsa
            with st.form("form_corsa", clear_on_submit=True):
                st.markdown("**Sessione in Pista**")
                col_a, col_b = st.columns(2)
                if st.session_state.is_athlete_session:
                    atleta_sel = st.session_state.logged_athlete_name
                    col_a.markdown(f"**Atleta:** {atleta_sel}")
                else:
                    atleta_sel = col_a.selectbox("Atleta", options=atleti_list, index=default_atleta_idx, key="atleta_corsa")
                data_sel = col_b.date_input("Data", key="data_corsa")

                st.markdown("---")
                st.markdown("**Prove effettuate**")
                distanze_opts = [30, 40, 50, 60, 80, 100, 120, 150, 200, 250, 300, 400]
                prove = []
                for i in range(1, 13):
                    if i > 1:
                        st.markdown("<hr class='mobile-divider'>", unsafe_allow_html=True)
                    c1, c2, c3 = st.columns([1, 1, 2])
                    dist_sel = c1.selectbox(f"🎯 PROVA {i} (Distanza)", ["-"] + [f"{d}m" for d in distanze_opts] + ["Altro"], key=f"dist_{i}")

                    # Se seleziona "Altro", mostra text input per distanza custom
                    if dist_sel == "Altro":
                        dist_i = c1.text_input(f"Distanza (m):", value="180", key=f"dist_custom_{i}", placeholder="es. 180")
                    else:
                        dist_i = dist_sel

                    tempo_i = c2.text_input(f"⏱️ TEMPO {i}", key=f"tempo_{i}", placeholder="es. 7.12")
                    nota_i = c3.text_input(f"📝 NOTE {i}", key=f"nota_{i}", placeholder="es. vento, elettrico...")
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
                            data_label = data_sel.strftime('%d/%m/%Y')
                            st.session_state['upload_success_msg'] = (
                                f"✅ Allenamento caricato! **{successi} {'prove' if successi > 1 else 'prova'}** "
                                f"salvate per **{atleta_sel}** in data {data_label}. "
                                f"I dati sono visibili a tutta la squadra. 🏋️"
                            )
                            st.cache_data.clear()
                            st.rerun()
                        if errori > 0:
                            st.warning(f"⚠️ {errori} prove non salvate (controlla il formato tempo).")

        elif tipo_form == "🏋️ Palestra (VBT)":
            from supabase_connector import insert_sessione_vbt
            esercizi_noti = sorted(set(df_vbt['Esercizio'].dropna().unique()) - {'General'})
            with st.form("form_vbt", clear_on_submit=True):
                st.markdown("**Sessione in Palestra (VBT)**")
                col_a, col_b = st.columns(2)
                if st.session_state.is_athlete_session:
                    atleta_sel = st.session_state.logged_athlete_name
                    col_a.markdown(f"**Atleta:** {atleta_sel}")
                else:
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
                            data_label = data_sel.strftime('%d/%m/%Y')
                            st.session_state['upload_success_msg'] = (
                                f"✅ Sessione palestra caricata! Allenamento VBT di **{atleta_sel}** "
                                f"del {data_label} salvato con successo nel cloud. 💪"
                            )
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error("❌ Errore nel salvataggio.")

elif st.session_state.current_page == "Dettaglio Atleta" and selected_athlete != "Tutta la squadra":
    # ── BREADCRUMB E NAVIGAZIONE PROFILO ──────────────────────────────────
    nav_col1, nav_col2 = st.columns([1, 1])
    with nav_col1:
        if st.button("← Torna all'elenco atleti", use_container_width=True, type="secondary"):
            st.session_state.app_athlete = "Tutta la squadra"
            st.session_state.current_page = "Atleti"
            st.session_state.page_just_changed = True
            st.rerun()

    # Se sei in sessione personale, mostra il breadcrumb visivo
    if st.session_state.is_athlete_session and st.session_state.logged_athlete_name == selected_athlete:
        with nav_col2:
            st.markdown("📍 **Profilo Personale**", help="Stai visualizzando il tuo profilo personale")

    st.markdown("<br>", unsafe_allow_html=True)
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

    # ──────────────────────────────────────────────────────────────────
    # NUOVA SEZIONE: TONNELLAGGIO VS PERFORMANCE
    # ──────────────────────────────────────────────────────────────────
    st.markdown("<hr class='gold'>", unsafe_allow_html=True)
    
    col_t_title, col_t_sel = st.columns([3, 1])
    with col_t_title:
        st.markdown("<h3 style='margin-bottom: 0;'>🏋️ Analisi Tonnellaggio vs Performance</h3>", unsafe_allow_html=True)
        st.markdown("<p style='color:rgba(255,255,255,0.5); font-size: 0.95em; margin-top: 5px;'>Impatto del volume di pesistica (kg totali sollevati a settimana) sui miglioramenti cronometrici in pista.</p>", unsafe_allow_html=True)
    with col_t_sel:
        st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)
        dist_ref = st.selectbox("Distanza Gara (Pista)", options=[60, 80, 100, 150, 200, 250, 300, 400], index=0)
        
    if not df_v.empty:
        # Calcolo Tonnellaggio (Carico x Serie x Ripetizioni)
        df_v_tonn = df_v.copy()
        df_v_tonn['Carico'] = pd.to_numeric(df_v_tonn['Carico'], errors='coerce').fillna(0)
        df_v_tonn['Serie'] = pd.to_numeric(df_v_tonn['Serie'], errors='coerce').fillna(0)
        df_v_tonn['Ripetizioni'] = pd.to_numeric(df_v_tonn['Ripetizioni'], errors='coerce').fillna(0)
        df_v_tonn['Tonnellaggio'] = df_v_tonn['Carico'] * df_v_tonn['Serie'] * df_v_tonn['Ripetizioni']
        
        # Aggregazione per Settimana
        df_v_tonn['Week'] = df_v_tonn['Data'].dt.to_period('W-MON').dt.start_time
        tonn_weekly = df_v_tonn.groupby('Week')['Tonnellaggio'].sum().reset_index()
        
        # Leggo il valore del lag corrente per shiftare il tempo nel grafico (offsetting)
        current_lag = st.session_state.get('lag_slider_val', 0)
        
        # Tempi Corsa per Settimana
        df_r_ref = df_r[df_r['Distanza'] == dist_ref].copy()
        if not df_r_ref.empty:
            df_r_ref['Week'] = df_r_ref['Data'].dt.to_period('W-MON').dt.start_time
            time_weekly = df_r_ref.groupby('Week')['Tempo'].min().reset_index()
            # Applica lo shift temporale!
            # Se lag=5, il tempo della settimana 6 viene graficato alla settimana 1 per vedere la correlazione.
            if current_lag > 0:
                time_weekly['Week'] = time_weekly['Week'] - pd.to_timedelta(current_lag, unit='W')
        else:
            time_weekly = pd.DataFrame(columns=['Week', 'Tempo'])
            
        merged = pd.merge(tonn_weekly, time_weekly, on='Week', how='outer').sort_values('Week').reset_index(drop=True)
        
        if not merged.empty:
            merged['Week_Label'] = merged['Week'].dt.strftime('%d %b')
            
            best_time = merged['Tempo'].min()
            merged['is_PB'] = merged['Tempo'] == best_time
            
            picco_kg = merged['Tonnellaggio'].max()
            picco_kg_str = f"{picco_kg:,.0f} kg".replace(",", ".") if pd.notna(picco_kg) and picco_kg > 0 else "-"
            best_time_str = f"{best_time:.2f}s" if pd.notna(best_time) else "-"
            
            k1 = make_kpi_card("Picco Volume VBT", picco_kg_str, "Massimale Settimanale", "neu", "🏋️", "kpi-glow")
            k2 = make_kpi_card(f"Miglior {dist_ref}m Stagione", best_time_str, "Personal Best", "pos" if pd.notna(best_time) else "neu", "⚡", "kpi-glow" if pd.notna(best_time) else "")
            
            st.markdown(f'<div class="kpi-grid" style="grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px;">{k1}{k2}</div>', unsafe_allow_html=True)
            
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            
            fig.add_trace(
                go.Bar(
                    x=merged['Week_Label'], y=merged['Tonnellaggio'],
                    name="Tonnellaggio (kg)",
                    marker_color="rgba(74, 158, 255, 0.45)",
                    marker_line_color="#4A9EFF",
                    marker_line_width=2,
                    opacity=1
                ),
                secondary_y=False,
            )
            
            valid_times = merged.dropna(subset=['Tempo'])
            if not valid_times.empty:
                fig.add_trace(
                    go.Scatter(
                        x=valid_times['Week_Label'], y=valid_times['Tempo'],
                        name=f"Tempo {dist_ref}m (s)",
                        mode='lines+markers',
                        line=dict(color="#FFFFFF", width=3.5),
                        marker=dict(size=8, color="#080A0E", line=dict(width=2, color="#FFFFFF")),
                        connectgaps=True
                    ),
                    secondary_y=True,
                )
                
                pb_points = valid_times[valid_times['is_PB'] == True]
                if not pb_points.empty:
                    # Doppio Layer per ricreare l'effetto "Halo" (alone del PB)
                    fig.add_trace(
                        go.Scatter(
                            x=pb_points['Week_Label'], y=pb_points['Tempo'],
                            mode='markers',
                            name="Personal Best (Halo)",
                            marker=dict(size=24, color="rgba(184,255,138,0.15)", line=dict(width=2, color="rgba(184,255,138,0.6)")),
                            showlegend=False,
                            hoverinfo='skip'
                        ),
                        secondary_y=True,
                    )
                    fig.add_trace(
                        go.Scatter(
                            x=pb_points['Week_Label'], y=pb_points['Tempo'],
                            mode='markers',
                            name="Personal Best",
                            marker=dict(size=10, color="#B8FF8A"),
                            showlegend=True
                        ),
                        secondary_y=True,
                    )
            
            fig.update_layout(
                template=THEME_TEMPLATE,
                height=420,
                margin=dict(l=20, r=20, t=50, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1, font=dict(family="'DM Mono', monospace", size=11, color="rgba(255,255,255,0.6)")),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(255,255,255,0.02)",
                title=dict(text="<span style='letter-spacing: 2px;'>ANALISI SETTIMANALE PROGRESSIONE</span>", font=dict(family="'DM Mono', monospace", size=11, color="rgba(255,255,255,0.4)")),
            )
            
            fig.update_yaxes(title_text="Volume Palestra (kg)", secondary_y=False, showgrid=False, zeroline=False, color="#4A9EFF", tickfont=dict(color="rgba(255,255,255,0.3)"))
            if not valid_times.empty:
                # Inverti asse in modo che i tempi minori (più veloci) siano verso l'alto
                fig.update_yaxes(title_text=f"Tempo Gara (s)", secondary_y=True, autorange="reversed", showgrid=True, gridcolor="rgba(255,255,255,0.04)", zeroline=False, tickfont=dict(color="rgba(255,255,255,0.3)"))
            
            # Wrapper per stondare i bordi del grafico come nell'immagine
            st.markdown('<div style="border: 1px solid rgba(255,255,255,0.06); border-radius: 16px; overflow: hidden; margin-bottom: 20px;">', unsafe_allow_html=True)
            st.plotly_chart(fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Box Offset Lag Interattivo
            with st.container(border=True):
                sl1, sl2, sl3 = st.columns([1, 2, 2], vertical_alignment="center")
                with sl1:
                    # Inizializzo un valore di default qualora Streamlit faccia i capricci al primo load
                    if 'lag_slider_val' not in st.session_state:
                        st.session_state['lag_slider_val'] = 0
                    lag_v = sl2.slider("Offset Lag (Sett.)", min_value=0, max_value=8, value=st.session_state['lag_slider_val'], key='lag_slider_val', label_visibility="collapsed")
                    st.markdown(f"<div style=\"font-family: 'DM Mono', monospace; font-size: 11px; color: rgba(255,255,255,0.4); letter-spacing: 2px;\">OFFSET LAG</div>", unsafe_allow_html=True)
                    st.markdown(f"<div style=\"font-family: 'Bebas Neue', sans-serif; font-size: 34px; color: #E8FF3A; line-height: 1;\">{lag_v} SETT.</div>", unsafe_allow_html=True)
                with sl3:
                    st.markdown("<div style=\"font-size: 12px; color: rgba(255,255,255,0.4); letter-spacing: 0.5px;\">Letteratura: effetti VBT visibili su sprint in <strong style=\"color: rgba(255,255,255,0.8);\">3–8 settimane</strong> dal picco di carico.</div>", unsafe_allow_html=True)
            
            # Pills Legend - FASI
            st.markdown(f'''
            <div style="display: flex; gap: 12px; margin-top: 10px; flex-wrap: wrap;">
                <div style="padding: 6px 16px; border-radius: 20px; background: rgba(74, 158, 255, 0.1); border: 1px solid rgba(74, 158, 255, 0.3); display: flex; align-items: center; gap: 8px;">
                    <div style="width: 8px; height: 8px; border-radius: 50%; background: #4A9EFF;"></div>
                    <span style="font-family: 'DM Mono', monospace; font-size: 11px; color: #4A9EFF; font-weight: 700;">ACCUMULO</span>
                </div>
                <div style="padding: 6px 16px; border-radius: 20px; background: rgba(232, 255, 58, 0.05); border: 1px solid rgba(232, 255, 58, 0.3); display: flex; align-items: center; gap: 8px;">
                    <div style="width: 8px; height: 8px; border-radius: 50%; background: #E8FF3A;"></div>
                    <span style="font-family: 'DM Mono', monospace; font-size: 11px; color: #E8FF3A; font-weight: 700;">PICCO</span>
                </div>
                <div style="padding: 6px 16px; border-radius: 20px; background: rgba(255, 154, 58, 0.1); border: 1px solid rgba(255, 154, 58, 0.3); display: flex; align-items: center; gap: 8px;">
                    <div style="width: 8px; height: 8px; border-radius: 50%; background: #FF9A3A;"></div>
                    <span style="font-family: 'DM Mono', monospace; font-size: 11px; color: #FF9A3A; font-weight: 700;">SCARICO</span>
                </div>
                <div style="padding: 6px 16px; border-radius: 20px; background: rgba(184, 255, 138, 0.1); border: 1px solid rgba(184, 255, 138, 0.3); display: flex; align-items: center; gap: 8px;">
                    <div style="width: 8px; height: 8px; border-radius: 50%; background: #B8FF8A;"></div>
                    <span style="font-family: 'DM Mono', monospace; font-size: 11px; color: #B8FF8A; font-weight: 700;">GARA</span>
                </div>
            </div>
            ''', unsafe_allow_html=True)
            
        else:
            st.info("Non ci sono dati sufficienti per incrociare tonnellaggio e tempi in questo periodo.")
    else:
        st.info("Nessuna sessione di pesistica (VBT) inserita per questo atleta nel periodo.")

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
    # 1. Atleti con PB nel periodo (SOLO se attivi negli ultimi 30 giorni)
    storico_pb = df_running[df_running['Data'].dt.date < start_d.date()].groupby(['Atleta', 'Distanza'])['Tempo'].min().to_dict()

    # Calcola atleti attivi negli ultimi 30 giorni per filtrare falsi positivi
    ultimi_30gg = pd.Timestamp.now().tz_localize(None) - pd.Timedelta(days=30)
    df_r_30gg = df_r[df_r['Data'] >= ultimi_30gg].copy()
    atleti_attivi_30gg = set(df_r_30gg['Atleta'].unique()) if not df_r_30gg.empty else set()

    atleti_pb = set()
    for idx, row in df_r.iterrows():
        # Verifica che l'atleta sia attivo negli ultimi 30 giorni
        if row['Atleta'] not in atleti_attivi_30gg:
            continue

        k = (row['Atleta'], row['Distanza'])
        if k in storico_pb:
            if row['Tempo'] < storico_pb[k]:
                atleti_pb.add(row['Atleta'])
                storico_pb[k] = row['Tempo']
        else:
            # Distanza nuova: conta come PB solo se registrata negli ultimi 30 giorni
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
    
    # ══════════════════════════════════════════════════════════════════════
    # NOTIFICHE AUTOMATICHE, COMPLEANNI E ALERT STRUTTURATO
    # ══════════════════════════════════════════════════════════════════════
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
        st.markdown(f"""
        <div style="background: rgba(232,255,58,0.15); border: 2px solid #E8FF3A; border-radius: 12px; padding: 16px; margin-bottom: 16px;">
            <div style="display: flex; gap: 12px; align-items: center;">
                <span style="font-size: 28px;">🎈</span>
                <div>
                    <div style="color: #E8FF3A; font-weight: 700; font-family: 'DM Mono'; letter-spacing: 1px; font-size: 11px;">COMPLEANNO</div>
                    <div style="color: #fff; font-size: 0.95em; margin-top: 2px;">
                        Oggi {txt_h}: <strong>{', '.join(compleanni)}</strong>! 🎉
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── ALERT PERFORMANCE E MONITORAGGIO ──
    alert_col1, alert_col2 = st.columns(2)

    with alert_col1:
        # ALERT PB
        if atleti_pb:
            txt = " e altri" if len(atleti_pb) > 3 else ""
            pb_list = ', '.join(list(atleti_pb)[:3]) + txt
            st.markdown(f"""
            <div style="background: rgba(184,255,138,0.1); border-left: 4px solid #B8FF8A; border-radius: 8px; padding: 14px; margin-bottom: 12px;">
                <div style="display: flex; gap: 10px; align-items: flex-start;">
                    <span style="font-size: 24px; margin-top: 2px;">🏆</span>
                    <div style="flex: 1;">
                        <div style="color: #B8FF8A; font-weight: 700; font-family: 'DM Mono'; letter-spacing: 1px; font-size: 10px; margin-bottom: 4px;">RECORD INFRANTI</div>
                        <div style="color: #fff; font-size: 0.9em;">
                            <strong>{pb_list}</strong> hanno battuto il PB in questo periodo! 🔥
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="background: rgba(255,255,255,0.02); border-left: 4px solid rgba(255,255,255,0.1); border-radius: 8px; padding: 14px; margin-bottom: 12px;">
                <div style="display: flex; gap: 10px; align-items: flex-start;">
                    <span style="font-size: 24px;">💪</span>
                    <div style="flex: 1;">
                        <div style="color: rgba(255,255,255,0.5); font-weight: 700; font-family: 'DM Mono'; letter-spacing: 1px; font-size: 10px; margin-bottom: 4px;">NESSUN NUOVO PB</div>
                        <div style="color: rgba(255,255,255,0.7); font-size: 0.9em;">
                            Continuate a spingere! Il prossimo record è vicino.
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # ALERT VOLUME
        if p_km > 0:
            st.markdown(f"""
            <div style="background: rgba(100,200,255,0.1); border-left: 4px solid #64C8FF; border-radius: 8px; padding: 14px;">
                <div style="display: flex; gap: 10px; align-items: flex-start;">
                    <span style="font-size: 24px;">📈</span>
                    <div style="flex: 1;">
                        <div style="color: #64C8FF; font-weight: 700; font-family: 'DM Mono'; letter-spacing: 1px; font-size: 10px; margin-bottom: 4px;">VOLUME IN CRESCITA</div>
                        <div style="color: #fff; font-size: 0.9em;">
                            La squadra ha aumentato i km di <strong>{p_km:+.1f}%</strong> vs il periodo precedente.
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with alert_col2:
        # ALERT INATTIVI (più importante)
        if inattivi:
            txt2 = " e altri" if len(inattivi) > 3 else ""
            inattivi_list = ', '.join(inattivi[:3]) + txt2
            st.markdown(f"""
            <div style="background: rgba(255,75,75,0.15); border-left: 4px solid #FF6B6B; border-radius: 8px; padding: 14px; margin-bottom: 12px;">
                <div style="display: flex; gap: 10px; align-items: flex-start;">
                    <span style="font-size: 24px;">⚠️</span>
                    <div style="flex: 1;">
                        <div style="color: #FF6B6B; font-weight: 700; font-family: 'DM Mono'; letter-spacing: 1px; font-size: 10px; margin-bottom: 4px;">ATLETI INATTIVI (>7 GG)</div>
                        <div style="color: #fff; font-size: 0.9em;">
                            <strong>{inattivi_list}</strong> non si allenano da più di una settimana. Richiedere contatti! 📞
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="background: rgba(22,163,74,0.1); border-left: 4px solid #16a34a; border-radius: 8px; padding: 14px; margin-bottom: 12px;">
                <div style="display: flex; gap: 10px; align-items: flex-start;">
                    <span style="font-size: 24px;">✅</span>
                    <div style="flex: 1;">
                        <div style="color: #16a34a; font-weight: 700; font-family: 'DM Mono'; letter-spacing: 1px; font-size: 10px; margin-bottom: 4px;">SQUADRA ATTIVA</div>
                        <div style="color: #fff; font-size: 0.9em;">
                            Tutti gli atleti si allenano regolarmente. Ottimo lavoro! 🎉
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Spazio per futuri alert
        st.markdown(f"""
        <div style="background: rgba(255,255,255,0.02); border-left: 4px solid rgba(255,255,255,0.1); border-radius: 8px; padding: 14px;">
            <div style="display: flex; gap: 10px; align-items: flex-start;">
                <span style="font-size: 24px;">📊</span>
                <div style="flex: 1;">
                    <div style="color: rgba(255,255,255,0.5); font-weight: 700; font-family: 'DM Mono'; letter-spacing: 1px; font-size: 10px; margin-bottom: 4px;">PERIODO ANALIZZATO</div>
                    <div style="color: rgba(255,255,255,0.7); font-size: 0.9em;">
                        Dal {start_d.strftime('%d/%m/%Y')} al {end_date.strftime('%d/%m/%Y')} ({duration_days} giorni)
                    </div>
                </div>
            </div>
        </div>
        """  , unsafe_allow_html=True)

st.divider()

if st.session_state.current_page == "Home":
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
                    # ── ORDINE DI INSERIMENTO ───────────────────────────────────────────
                    # Usa l'id Supabase (auto-increment) per preservare l'ordine originale
                    # di inserimento da parte degli atleti (es. 20-30-40-20-30-40)
                    if 'id' in df_day.columns:
                        df_day = df_day.sort_values(by='id', ascending=True)
                    # else: mantieni l'ordine in cui arrivano dal DataFrame (già data desc, ma
                    # all'interno della stessa data l'ordine del DB sarà quello di inserimento)
                    df_day = df_day.reset_index(drop=True)
                    
                    # Numero progressivo ripetizione per ogni (Atleta, Distanza)
                    df_day['Ripetizione'] = df_day.groupby(['Atleta', 'Distanza']).cumcount() + 1
                    
                    # ── DIVISIONE IN GRUPPI PER SET DI DISTANZE ────────────────────────
                    # Raggruppa gli atleti che fanno distanze simili nella stessa tabella.
                    # Algoritmo: Jaccard similarity tra i set di distanze di ogni atleta.
                    atleti_distanze = df_day.groupby('Atleta')['Distanza'].apply(set).to_dict()
                    
                    def jaccard_sim(s1, s2):
                        if not s1 or not s2:
                            return 0.0
                        return len(s1 & s2) / len(s1 | s2)
                    
                    # Greedy grouping: ogni atleta finisce nel primo gruppo compatibile (≥40% overlap)
                    groups = []
                    assigned = set()
                    for atleta_a, dists_a in atleti_distanze.items():
                        if atleta_a in assigned:
                            continue
                        group = [atleta_a]
                        group_dists = set(dists_a)
                        assigned.add(atleta_a)
                        for atleta_b, dists_b in atleti_distanze.items():
                            if atleta_b in assigned:
                                continue
                            if jaccard_sim(group_dists, dists_b) >= 0.4:
                                group.append(atleta_b)
                                group_dists = group_dists | dists_b
                                assigned.add(atleta_b)
                        groups.append(group)
                    
                    # ── VISUALIZZAZIONE: una tabella per gruppo ─────────────────────────
                    show_group_labels = len(groups) > 1
                    for g_idx, group_atleti in enumerate(groups):
                        df_group = df_day[df_day['Atleta'].isin(group_atleti)].copy()
                        distanze_gruppo = sorted(df_group['Distanza'].unique())
                        dist_label = " · ".join(f"{int(d)}m" for d in distanze_gruppo)
                        
                        if show_group_labels:
                            st.markdown(
                                f"<div style='margin: 16px 0 6px 0; padding: 6px 14px; "
                                f"background: rgba(232,255,58,0.05); border-left: 3px solid #E8FF3A; "
                                f"border-radius: 4px; font-family: DM Mono, monospace; font-size: 11px; "
                                f"color: #E8FF3A; letter-spacing: 1px;'>"
                                f"GRUPPO {g_idx + 1} — {dist_label}</div>",
                                unsafe_allow_html=True
                            )
                        
                        # Costruisci le colonne nell'ordine in cui compaiono nel dataset
                        # (ordine di inserimento, non per distanza crescente)
                        cols_seen = []
                        for _, row_p in df_group.iterrows():
                            col_name = f"{int(row_p['Distanza'])}m - Pr. {int(row_p['Ripetizione'])}"
                            if col_name not in cols_seen:
                                cols_seen.append(col_name)
                        
                        # Costruisci manualmente il pivot rispettando l'ordine
                        pivot_rows = {}
                        for _, row_p in df_group.iterrows():
                            atl = row_p['Atleta']
                            col_name = f"{int(row_p['Distanza'])}m - Pr. {int(row_p['Ripetizione'])}"
                            if atl not in pivot_rows:
                                pivot_rows[atl] = {}
                            pivot_rows[atl][col_name] = row_p['Tempo']
                        
                        pivot_day = pd.DataFrame(pivot_rows).T
                        # Riordina le colonne nell'ordine originale di inserimento
                        pivot_day = pivot_day.reindex(columns=[c for c in cols_seen if c in pivot_day.columns])
                        pivot_day.index.name = 'Atleta'
                        
                        st.dataframe(
                            pivot_day.style.format(lambda x: f"{x:.2f}s" if pd.notnull(x) else " - "),
                            use_container_width=True
                        )
                else:
                    st.info("Nessuna prova in questa data.")
        else:
            st.info("Nessun dato registrato o presente nei filtri.")


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
                'highlight': highlight_txt,
                'days_ago': days_ago
            })
            
        roster_df = pd.DataFrame(roster_data)
        if not roster_df.empty:
            roster_df = roster_df.sort_values(by=['days_ago', 'nome']).reset_index(drop=True).drop(columns=['days_ago'])

        # Barra di ricerca se > 10
        if len(roster_df) > 10:
            search_q = st.text_input("🔍 Cerca Atleta", placeholder="Cerca nome...", label_visibility="collapsed")
            if search_q:
                roster_df = roster_df[roster_df['nome'].str.contains(search_q, case=False, na=False)]
        
        # Grid System
        for i in range(0, len(roster_df), 3):
            cols = st.columns(3)
            for j in range(3):
                if i + j < len(roster_df):
                    row = roster_df.iloc[i + j]
                    with cols[j].container(border=True):
                        # Avatar con border color-coded e senza foto con gradient
                        if pd.notna(row['foto']) and str(row['foto']).strip() != "":
                            av_html = f'''<div style="width:70px; height:70px; border-radius:50%; border:4px solid {row["color"]}; overflow:hidden; margin-bottom:12px; box-shadow: 0 0 20px {row["color"]}40;">
                                            <img src="{row["foto"]}" style="width:100%; height:100%; object-fit:cover; display:block;">
                                          </div>'''
                        else:
                            inz = "".join([n[0] for n in row['nome'].split()[:2]]).upper()
                            av_html = f'''<div style="width:70px; height:70px; border-radius:50%; border:4px solid {row["color"]}; background: radial-gradient(circle at 30% 30%, {row["color"]}30, {row["color"]}10); color:#FFF; font-family:'Bebas Neue', sans-serif; font-size:28px; font-weight:bold; display:flex; align-items:center; justify-content:center; margin-bottom:12px; box-shadow: 0 0 20px {row["color"]}40; letter-spacing:2px;">
                                            {inz}
                                          </div>'''

                        st.markdown(f'''
                        <div style="position: relative; padding: 6px;">
                            <div style="position: absolute; right: 8px; top: 8px; font-size: 80px; opacity: 0.06; color: {row["color"]}; user-select: none; pointer-events: none;">👤</div>
                            {av_html}
                            <div style="font-weight: 700; font-size: 1.1em; line-height: 1.3; margin-bottom: 6px; color: #E8EDF5;">{row["nome"]}</div>
                            <div style="font-size: 0.7em; color: rgba(255,255,255,0.4); margin-bottom: 12px; font-family: 'DM Mono', monospace; letter-spacing: 1px; text-transform: uppercase; font-weight: 600;">● VELOCITÀ</div>
                            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
                                <span style="font-size: 11px; padding: 5px 10px; border-radius: 6px; font-family: 'DM Mono', monospace; font-weight: 700; {row["c_badge"]}">{row["stato"]}</span>
                                <span style="font-size: 12px; color: {row["color"]}; font-family: 'DM Mono', monospace; font-weight: bold;">{row["highlight"]}</span>
                            </div>
                        </div>
                        ''', unsafe_allow_html=True)

                        if st.button("🔍 Vai al Profilo", key=f"nav_{row['nome']}", use_container_width=True):
                            st.session_state.app_athlete = row['nome']
                            st.session_state.current_page = "Dettaglio Atleta"
                            st.session_state.page_just_changed = True
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

    # ── MOSTRA TITOLO ATLETA SOLO se NON sei in profilo personale ──
    # (Se in profilo personale, il benvenuto è già mostrato sopra)
    if not (st.session_state.is_athlete_session and st.session_state.logged_athlete_name == selected_athlete):
        st.markdown(f"## 👤 {selected_athlete}")
        st.markdown("---")
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
                        if d_val not in [60, 100, 150, 200, 250, 300, 400]:
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

            # ── SEZIONE CORREZIONE TEMPI (solo per atleta in sessione o admin) ──
            if can_edit and selected_athlete != "Tutta la squadra":
                st.divider()
                with st.expander("✏️ Correggi o Elimina un Tempo", expanded=False):
                    st.markdown(
                        "Qui puoi correggere un tempo inserito per errore o eliminare una prova. "
                        "**Le modifiche sono permanenti nel database.** Usa con attenzione."
                    )
                    # Admin può scegliere l'atleta, atleta vede solo i propri
                    if st.session_state.is_admin:
                        all_atl_list = sorted(df_running['Atleta'].unique().tolist())
                        target_atleta = st.selectbox("Atleta", options=all_atl_list,
                                                     index=all_atl_list.index(selected_athlete) if selected_athlete in all_atl_list else 0,
                                                     key="corr_atleta_sel")
                    else:
                        target_atleta = selected_athlete

                    df_corr = df_running[df_running['Atleta'] == target_atleta].copy()
                    if not df_corr.empty and 'id' in df_corr.columns:
                        df_corr = df_corr.sort_values('Data', ascending=False).head(50)
                        df_corr['Label'] = (
                            df_corr['Data'].dt.strftime('%d/%m/%Y') + " — " +
                            df_corr['Distanza'].astype(int).astype(str) + "m — " +
                            df_corr['Tempo'].apply(lambda x: f"{x:.2f}s") +
                            df_corr['Note'].apply(lambda n: f" ({n})" if pd.notna(n) and str(n).strip() else "")
                        )
                        label_to_id = dict(zip(df_corr['Label'], df_corr['id']))
                        label_to_tempo = dict(zip(df_corr['Label'], df_corr['Tempo']))
                        label_to_nota = dict(zip(df_corr['Label'], df_corr['Note'].fillna('')))

                        sel_label = st.selectbox("Seleziona la prova da modificare", options=df_corr['Label'].tolist(), key="corr_sel_prova")

                        if sel_label:
                            sel_id = label_to_id[sel_label]
                            sel_tempo = label_to_tempo[sel_label]
                            sel_nota = label_to_nota[sel_label]

                            cc1, cc2 = st.columns(2)
                            with cc1:
                                with st.form("form_correggi_tempo", clear_on_submit=False):
                                    nuovo_tempo_str = st.text_input("Nuovo Tempo (secondi)", value=f"{sel_tempo:.2f}", key="corr_tempo_inp")
                                    nuova_nota = st.text_input("Note", value=sel_nota, key="corr_nota_inp")
                                    if st.form_submit_button("💾 Salva Correzione", type="primary", use_container_width=True):
                                        try:
                                            from data_loader import parse_time
                                            parsed = parse_time(nuovo_tempo_str)
                                            if parsed is None:
                                                nuovo_t = float(nuovo_tempo_str.replace(',', '.'))
                                            else:
                                                nuovo_t = parsed['tempo']
                                            from supabase_connector import update_sessione_corsa
                                            ok = update_sessione_corsa(sel_id, nuovo_t, nuova_nota.strip())
                                            if ok:
                                                st.success("✅ Tempo corretto con successo!")
                                                st.cache_data.clear()
                                                st.rerun()
                                            else:
                                                st.error("❌ Errore nel salvataggio.")
                                        except Exception as e:
                                            st.error(f"❌ Formato tempo non valido: {e}")
                            with cc2:
                                st.markdown("<br>", unsafe_allow_html=True)
                                if st.button("🗑️ Elimina questa prova", type="secondary", use_container_width=True, key="corr_delete_btn"):
                                    st.session_state['_confirm_delete_id'] = sel_id
                                    st.session_state['_confirm_delete_label'] = sel_label
                                if st.session_state.get('_confirm_delete_id') == sel_id:
                                    st.warning(f"⚠️ Sei sicuro di voler eliminare: **{sel_label}**?")
                                    if st.button("✅ Sì, elimina definitivamente", type="primary", key="corr_confirm_del", use_container_width=True):
                                        from supabase_connector import delete_sessione_corsa
                                        delete_sessione_corsa(sel_id)
                                        st.session_state.pop('_confirm_delete_id', None)
                                        st.session_state.pop('_confirm_delete_label', None)
                                        st.success("🗑️ Prova eliminata.")
                                        st.cache_data.clear()
                                        st.rerun()
                    elif 'id' not in df_corr.columns:
                        st.info("La correzione tempi è disponibile solo con i dati dal cloud (Supabase).")
                    else:
                        st.info("Nessuna prova trovata per questo atleta.")


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
        st.markdown("<h3 style='font-family: Bebas Neue; color: #fff; margin-bottom: 0; line-height: 1.1; font-size: 38px;'>PREDIZIONE <span style='color: #E8FF3A;'>PRESTAZIONE GARA</span></h3>", unsafe_allow_html=True)
        st.markdown("<span style='font-family: DM Mono; font-size: 11px; color: rgba(255,255,255,0.4); letter-spacing: 2px;'>MODELLO VITTORI · FIDAL</span>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        # 1. Estrazione PB (Auto-Fill)
        pb_30, pb_60, pb_80, pb_100, pb_200 = None, None, None, None, None
        if selected_athlete != "Tutta la squadra" and len(df_r) > 0:
            pb_corse = df_r.groupby('Distanza')['Tempo'].min()
            pb_30 = float(pb_corse.get(30, None)) if pd.notna(pb_corse.get(30, None)) else None
            pb_60 = float(pb_corse.get(60, None)) if pd.notna(pb_corse.get(60, None)) else None
            pb_80 = float(pb_corse.get(80, None)) if pd.notna(pb_corse.get(80, None)) else None
            pb_100 = float(pb_corse.get(100, None)) if pd.notna(pb_corse.get(100, None)) else None
            pb_200 = float(pb_corse.get(200, None)) if pd.notna(pb_corse.get(200, None)) else None

        col_sx, col_dx = st.columns([1, 4])
        gender_sel = col_sx.radio("Sesso Atleta", ["Maschile", "Femminile"], horizontal=True, label_visibility="collapsed")
        g_code = "M" if gender_sel == "Maschile" else "F"

        vt1, vt2 = st.tabs(["🚀 Predizione Gara (Forward)", "🎯 Calcolatore Obiettivo (Reverse)"])
        
        with vt1:
            st.markdown("<div style='font-family: DM Mono; font-size: 11px; color: rgba(255,255,255,0.4); letter-spacing: 1px; margin-bottom: 10px;'>MODALITÀ DI STIMA</div>", unsafe_allow_html=True)
            mod_stima = st.selectbox(
                "Scegli con quali dati pre-compilare il modello:",
                ["Usa tutti i PB disponibili", "Forza previsione partendo dai 30m", "Forza previsione partendo dai 60m", "Forza previsione partendo dagli 80m", "Inserimento manuale (campi vuoti)"],
                label_visibility="collapsed"
            )
            
            # Applica i filtri sui PB a seconda della modalità scelta
            p_val_30 = pb_30 if mod_stima in ["Usa tutti i PB disponibili", "Forza previsione partendo dai 30m"] else None
            p_val_60 = pb_60 if mod_stima in ["Usa tutti i PB disponibili", "Forza previsione partendo dai 60m"] else None
            p_val_80 = pb_80 if mod_stima in ["Usa tutti i PB disponibili", "Forza previsione partendo dagli 80m"] else None
            p_val_100 = pb_100 if mod_stima == "Usa tutti i PB disponibili" else None
            p_val_200 = pb_200 if mod_stima == "Usa tutti i PB disponibili" else None

            st.markdown("<div style='font-family: DM Mono; font-size: 11px; color: rgba(255,255,255,0.4); letter-spacing: 1px; margin-top: 5px; margin-bottom: 15px;'>INSERISCI I TUOI TEMPI</div>", unsafe_allow_html=True)
            i1, i2, i3, i4, i5 = st.columns(5)
            t30 = i1.number_input("30m (fermo) - s", value=p_val_30, step=0.05, format="%.2f")
            t60 = i2.number_input("60m (fermo) - s", value=p_val_60, step=0.05, format="%.2f")
            t80 = i3.number_input("80m - s", value=p_val_80, step=0.05, format="%.2f")
            t100 = i4.number_input("100m - s", value=p_val_100, step=0.05, format="%.2f")
            t200 = i5.number_input("200m - s", value=p_val_200, step=0.05, format="%.2f")
            
            p30 = t30 if (t30 and t30>0) else None
            p60 = t60 if (t60 and t60>0) else None
            p80 = t80 if (t80 and t80>0) else None
            p100 = t100 if (t100 and t100>0) else None
            p200 = t200 if (t200 and t200>0) else None

            est100 = p100 or (round(p80 * 1.231, 2) if p80 else (round(p60 * 1.576 + 0.18, 2) if p60 else (round(p30 * 2.85 + 0.30, 2) if p30 else None)))
            est60 = p60 or (round(p30 * 1.78 + 0.12, 2) if p30 else None)
            est80 = p80 or (round((est60 + est100)/2, 2) if (est60 and est100) else None)
            est200 = p200 or (round(est100 * 2 - 0.24, 2) if est100 else None)
            est400 = round(est200 * 2 + (4.2 if g_code == "F" else 3.8), 2) if est200 else None
            
            if not any([p30, p60, p80, p100, p200]):
                st.info("💡 Inserisci almeno un tempo (preferibilmente i 60m o 30m) per calcolare la regressione di Vittori.")
            else:
                st.markdown("<br><div style='padding:20px; border-radius:12px; border:1px solid rgba(255,255,255,0.06); background:rgba(255,255,255,0.02);'>", unsafe_allow_html=True)
                if est60 and not p60:
                    st.markdown(f"<div style='display:flex; justify-content:space-between; align-items:center; padding-bottom:10px; border-bottom:1px solid rgba(255,255,255,0.05);'><div><span style='font-family:DM Mono; font-size:11px; color:#aaa; letter-spacing:1px;'>60m STIMATO</span><br><small style='color:#555;'>da 30m</small></div><span style='font-family:Bebas Neue; font-size:26px; color:#fff;'>{est60:.2f}s</span></div>", unsafe_allow_html=True)
                if est80 and not p80:
                    st.markdown(f"<div style='display:flex; justify-content:space-between; align-items:center; padding-bottom:10px; border-bottom:1px solid rgba(255,255,255,0.05);'><div><span style='font-family:DM Mono; font-size:11px; color:#aaa; letter-spacing:1px;'>80m STIMATO</span><br><small style='color:#555;'>interpolato</small></div><span style='font-family:Bebas Neue; font-size:26px; color:#fff;'>{est80:.2f}s</span></div>", unsafe_allow_html=True)
                if est100:
                    src100 = "inserito" if p100 else ("da 80m" if p80 else ("da 60m" if p60 else "da 30m"))
                    bg_res = "rgba(232,255,58,0.06)" if not p100 else "transparent"
                    col_res = "#E8FF3A" if not p100 else "#fff"
                    bord = "border:1px solid rgba(232,255,58,0.2);" if not p100 else ""
                    st.markdown(f"<div style='display:flex; justify-content:space-between; align-items:center; padding:15px; margin-top:10px; border-radius:8px; background:{bg_res}; {bord}'><div><span style='font-family:DM Mono; font-size:11px; color:{col_res}; letter-spacing:1px;'>100m {'' if p100 else 'STIMATO'}</span><br><small style='color:rgba(255,255,255,0.3);'>Origine: {src100}</small></div><div><span style='font-family:Bebas Neue; font-size:38px; color:{col_res};'>{est100:.2f}s</span></div></div>", unsafe_allow_html=True)
                    st.markdown(f"<div style='text-align:right; font-family:Bebas Neue; font-size:24px; color:#4A9EFF; margin-top:4px;'>VEL. MEDIA: {(100/est100):.2f} m/s</div>", unsafe_allow_html=True)
                if est200:
                    src200 = "inserito" if p200 else "da 100m"
                    bg_res = "rgba(232,255,58,0.06)" if not p200 else "transparent"
                    col_res = "#E8FF3A" if not p200 else "#fff"
                    bord = "border:1px solid rgba(232,255,58,0.2);" if not p200 else ""
                    st.markdown(f"<div style='display:flex; justify-content:space-between; align-items:center; padding:15px; margin-top:10px; border-radius:8px; background:{bg_res}; {bord}'><div><span style='font-family:DM Mono; font-size:11px; color:{col_res}; letter-spacing:1px;'>200m {'' if p200 else 'STIMATO'}</span><br><small style='color:rgba(255,255,255,0.3);'>Origine: {src200}</small></div><div><span style='font-family:Bebas Neue; font-size:32px; color:{col_res};'>{est200:.2f}s</span></div></div>", unsafe_allow_html=True)
                if est400:
                    st.markdown(f"<div style='display:flex; justify-content:space-between; align-items:center; padding:15px; margin-top:10px;'><div><span style='font-family:DM Mono; font-size:11px; color:#aaa; letter-spacing:1px;'>400m STIMATO</span><br><small style='color:#555;'>costante Vittori {g_code}</small></div><span style='font-family:Bebas Neue; font-size:26px; color:#fff;'>{est400:.2f}s</span></div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

        with vt2:
            st.markdown("<div style='font-family: DM Mono; font-size: 11px; color: rgba(255,255,255,0.4); letter-spacing: 1px; margin-bottom: 15px;'>CALCOLO DEL GAP DAI TUOI PB REALI</div>", unsafe_allow_html=True)
            tr1, tr2 = st.columns([1, 2])
            tgt_dist = tr1.selectbox("Gara Obiettivo:", ["80m", "100m", "200m", "250m", "400m"])
            tgt_t = tr2.number_input("Tempo Bersaglio Sperato (s):", value=None, step=0.10, placeholder="Es. inserisci 10.85 per i 100m")
            
            p_tgt = tgt_t if (tgt_t and tgt_t > 0) else None
            
            if p_tgt:
                need100, need80, need60, need30 = None, None, None, None
                if tgt_dist == "80m":
                    need80 = p_tgt
                    need100 = round(p_tgt * 1.231, 2)
                    need60 = round((need100 - 0.18)/1.576, 2)
                    need30 = round((need100 - 0.30)/2.85, 2)
                elif tgt_dist == "100m":
                    need100 = p_tgt
                    need60 = round((p_tgt - 0.18)/1.576, 2)
                    need30 = round((p_tgt - 0.30)/2.85, 2)
                    need80 = round((need100 + need60)/2, 2)
                elif tgt_dist == "200m":
                    need100 = round((p_tgt + 0.24)/2, 2)
                    need60 = round((need100 - 0.18)/1.576, 2)
                    need30 = round((need100 - 0.30)/2.85, 2)
                    need80 = round((need100 + need60)/2, 2)
                elif tgt_dist == "400m":
                    need100 = round(((p_tgt - (4.2 if g_code == 'F' else 3.8))/2 + 0.24)/2, 2)
                    need60 = round((need100 - 0.18)/1.576, 2)
                    need30 = round((need100 - 0.30)/2.85, 2)
                    need80 = round((need100 + need60)/2, 2)
                    
                cur_100_est = pb_100 or (round(pb_80 * 1.231, 2) if pb_80 else (round(pb_60 * 1.576 + 0.18, 2) if pb_60 else (round(pb_30 * 2.85 + 0.30, 2) if pb_30 else None)))
                gap = round(cur_100_est - need100, 2) if cur_100_est else None
                
                st.markdown("<br><div style='padding:20px; border-radius:12px; border:1px solid rgba(255,255,255,0.06); background:rgba(255,255,255,0.02);'>", unsafe_allow_html=True)
                if tgt_dist != "100m" and tgt_dist != "80m":
                    st.markdown(f"<div style='display:flex; justify-content:space-between; align-items:center; padding-bottom:10px; border-bottom:1px solid rgba(255,255,255,0.05);'><div><span style='font-family:DM Mono; font-size:11px; color:#FF9A3A; letter-spacing:1px;'>100m NECESSARIO COME STEP</span></div><span style='font-family:Bebas Neue; font-size:26px; color:#FF9A3A;'>{need100:.2f}s</span></div>", unsafe_allow_html=True)
                if tgt_dist == "80m":
                    st.markdown(f"<div style='display:flex; justify-content:space-between; align-items:center; padding-bottom:10px; border-bottom:1px solid rgba(255,255,255,0.05);'><div><span style='font-family:DM Mono; font-size:11px; color:#FF9A3A; letter-spacing:1px;'>100m TEORICO ATTESO</span></div><span style='font-family:Bebas Neue; font-size:26px; color:#FF9A3A;'>{need100:.2f}s</span></div>", unsafe_allow_html=True)

                if need80:
                    st.markdown(f"<div style='display:flex; justify-content:space-between; align-items:center; padding:15px; margin-top:10px; border-radius:8px; background:rgba(232,255,58,0.06); border:1px solid rgba(232,255,58,0.2);'><div><span style='font-family:DM Mono; font-size:11px; color:#E8FF3A; letter-spacing:1px;'>🎯 TARGET ASINCRONO 80m</span><br><small style='color:rgba(255,255,255,0.3);'>allenamento</small></div><div><span style='font-family:Bebas Neue; font-size:32px; color:#E8FF3A;'>{need80:.2f}s</span></div></div>", unsafe_allow_html=True)
                
                st.markdown(f"<div style='display:flex; justify-content:space-between; align-items:center; padding:15px; margin-top:10px; border-radius:8px; background:rgba(232,255,58,0.03); border:1px solid rgba(232,255,58,0.1);'><div><span style='font-family:DM Mono; font-size:11px; color:#E8FF3A; letter-spacing:1px;'>🎯 TARGET ASINCRONO 60m</span><br><small style='color:rgba(255,255,255,0.3);'>allenamento</small></div><div><span style='font-family:Bebas Neue; font-size:28px; color:#E8FF3A;'>{need60:.2f}s</span></div></div>", unsafe_allow_html=True)
                st.markdown(f"<div style='display:flex; justify-content:space-between; align-items:center; padding:10px; margin-top:10px;'><div><span style='font-family:DM Mono; font-size:11px; color:#B8FF8A; letter-spacing:1px;'>🎯 TARGET ASINCRONO 30m</span></div><span style='font-family:Bebas Neue; font-size:22px; color:#B8FF8A;'>{need30:.2f}s</span></div>", unsafe_allow_html=True)
                
                if gap is not None:
                    g_col = "#FF4B4B" if gap > 0 else "#B8FF8A"
                    g_bg = "rgba(255,75,75,0.08)" if gap > 0 else "rgba(184,255,138,0.08)"
                    g_bord = "rgba(255,75,75,0.25)" if gap > 0 else "rgba(184,255,138,0.25)"
                    g_txt = "+"+str(gap) if gap > 0 else str(gap)
                    lbl_gap = "⚡ GAP DA COLMARE" if gap > 0 else "✅ TARGET GIÀ RAGGIUNGIBILE"
                    st.markdown(f"<div style='margin-top:15px; padding:15px; border-radius:10px; background:{g_bg}; border:1px solid {g_bord};'><div style='font-family:DM Mono; font-size:10px; color:{g_col}; letter-spacing:2px; margin-bottom:6px;'>{lbl_gap}</div><div style='display:flex; align-items:baseline; gap:10px;'><span style='font-family:Bebas Neue; font-size:36px; color:{g_col}; line-height:1;'>{g_txt}s</span><span style='font-size:12px; color:rgba(255,255,255,0.4);'>sul 100m stimato attuale ({cur_100_est:.2f}s)</span></div></div>", unsafe_allow_html=True)
                else:
                    st.info("Per calcolare il Gap, devi avere almeno una Prova ufficiale (100, 80, 60 o 30) a database.")
                st.markdown("</div>", unsafe_allow_html=True)

        st.divider()
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

    # ══════════════════════════════�
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
    /* Expander card-style (usato ancora in tab2, tab3, ecc.) */
    .streamlit-expanderHeader {
        font-weight: 700 !important;
        font-size: 1.05em !important;
        font-family: 'DM Sans', sans-serif !important;
        color: #E8EDF5 !important;
        padding: 14px 18px !important;
        background: rgba(255,255,255,0.02) !important;
        border-radius: 8px !important;
        border-left: 3px solid rgba(232,255,58,0.4) !important;
    }
    .streamlit-expanderHeader:hover {
        background: rgba(232,255,58,0.05) !important;
        border-left-color: #E8FF3A !important;
    }

    /* Section cards — griglia Tab Analisi Velocità */
    .sec-cards-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
        gap: 10px;
        margin: 20px 0 4px 0;
    }
    .sec-card-btn {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 8px;
        padding: 18px 12px 16px;
        background: rgba(255,255,255,0.03);
        border: 1.5px solid rgba(255,255,255,0.1);
        border-radius: 12px;
        cursor: pointer;
        transition: border-color 0.15s, background 0.15s;
        text-align: center;
        user-select: none;
        -webkit-tap-highlight-color: transparent;
    }
    .sec-card-btn:hover, .sec-card-btn.active {
        border-color: #E8FF3A;
        background: rgba(232,255,58,0.06);
    }
    .sec-card-btn.active .sec-card-icon,
    .sec-card-btn.active .sec-card-title {
        color: #E8FF3A !important;
    }
    .sec-card-icon {
        font-size: 26px;
        line-height: 1;
        color: rgba(255,255,255,0.7);
    }
    .sec-card-title {
        font-family: 'DM Sans', sans-serif;
        font-weight: 700;
        font-size: 13px;
        color: #E8EDF5;
        line-height: 1.25;
        margin: 0;
    }
    .sec-card-sub {
        font-family: 'DM Mono', monospace;
        font-size: 10px;
        color: rgba(255,255,255,0.35);
        line-height: 1.3;
        margin: 0;
        letter-spacing: 0.3px;
    }
    .sec-content-block {
        border-left: 2px solid rgba(232,255,58,0.2);
        padding-left: 16px;
        margin: 16px 0 24px 0;
    }
    /* Bottoni card griglia sezioni — stesso look delle KPI card (vetro + icona di sfondo) */
    #sec-cards-marker ~ div [data-testid="stHorizontalBlock"] button[kind="secondary"],
    #sec-cards-marker + div button[kind="secondary"] {
        min-height: 150px !important;
        padding: 20px !important;
        border-radius: 16px !important;
        border: 1px solid rgba(255,255,255,0.05) !important;
        background: rgba(20, 23, 30, 0.6) !important;
        backdrop-filter: blur(10px) !important;
        -webkit-backdrop-filter: blur(10px) !important;
        overflow: hidden !important;
        position: relative !important;
        font-size: 0.95em !important;
        white-space: pre-wrap !important;
        line-height: 1.4 !important;
        text-align: left !important;
        align-items: flex-start !important;
        justify-content: center !important;
        flex-direction: column !important;
        gap: 6px !important;
        box-shadow: none !important;
        transition: all 0.3s ease !important;
    }
    /* Icona grande, sfocata e ruotata nell'angolo (come .kpi-icon); il glifo è iniettato per card */
    #sec-cards-marker ~ div [data-testid="stHorizontalBlock"] button[kind="secondary"]::after,
    #sec-cards-marker + div button[kind="secondary"]::after {
        content: "";
        position: absolute; right: -5px; bottom: -15px;
        font-size: 70px; opacity: 0.08; transform: rotate(-15deg);
        pointer-events: none; line-height: 1;
    }
    /* Testo del label sopra l'icona di sfondo */
    #sec-cards-marker ~ div [data-testid="stHorizontalBlock"] button[kind="secondary"] [data-testid="stMarkdownContainer"],
    #sec-cards-marker + div button[kind="secondary"] [data-testid="stMarkdownContainer"] {
        position: relative !important; z-index: 1 !important;
    }
    #sec-cards-marker ~ div [data-testid="stHorizontalBlock"] button[kind="secondary"]:hover,
    #sec-cards-marker + div button[kind="secondary"]:hover {
        border-color: rgba(232,255,58,0.4) !important;
        color: #E8FF3A !important;
        transform: translateY(-3px) !important;
        box-shadow: 0 10px 20px rgba(0,0,0,0.5) !important;
    }
    /* Card ATTIVA (sezione aperta): bordo/sfondo giallo iniettati dinamicamente
       in app.py mirando alla classe wrapper .st-key-secbtn_<key> della card. */

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
        padding-bottom: 15px !important;
        flex-wrap: nowrap !important;
    }
    [data-baseweb="tab"] {
        background-color: #14171E !important;
        border-radius: 10px !important;
        padding: 14px 22px !important;
        color: #FFFFFF !important;
        border: 2px solid rgba(255,255,255,0.12) !important;
        font-family: 'DM Sans', sans-serif !important;
        font-weight: 700 !important;
        font-size: 1.15em !important;
        white-space: nowrap !important;
        min-width: 130px !important;
        text-align: center !important;
        transition: all 0.18s ease !important;
        letter-spacing: 0.3px !important;
    }
    [data-baseweb="tab"][aria-selected="true"] {
        background-color: #E8FF3A !important;
        border: 2px solid #E8FF3A !important;
        box-shadow: 0 4px 18px rgba(232,255,58,0.35) !important;
        transform: translateY(-2px) !important;
    }
    /* Forza il testo dentro la tab attiva ad essere scuro */
    [data-baseweb="tab"][aria-selected="true"] p,
    [data-baseweb="tab"][aria-selected="true"] span,
    [data-baseweb="tab"][aria-selected="true"] div {
        color: #0A0D14 !important;
    }
    [data-baseweb="tab"]:hover:not([aria-selected="true"]) {
        background-color: rgba(232,255,58,0.12) !important;
        border-color: rgba(232,255,58,0.35) !important;
        transform: translateY(-1px) !important;
    }
    [data-baseweb="tab"]:hover:not([aria-selected="true"]) p,
    [data-baseweb="tab"]:hover:not([aria-selected="true"]) span,
    [data-baseweb="tab"]:hover:not([aria-selected="true"]) div {
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

    /* ── DEEP DARK RADIAL BACKGROUND (Titanio Profondo) ──
           Sostituisce il flat #080A0E del tema con un gradiente radiale
           antracite/bluastro, fisso (non si muove con lo scroll) e leggero
           (nessun blur/animazione: solo background-image statico). */
    [data-testid="stAppViewContainer"] {
        background:
            radial-gradient(ellipse 90% 60% at 50% -8%, rgba(40, 50, 72, 0.5) 0%, rgba(8,10,14,0) 55%),
            radial-gradient(ellipse 70% 50% at 100% 105%, rgba(0, 60, 70, 0.18) 0%, rgba(8,10,14,0) 55%),
            radial-gradient(ellipse 60% 45% at -5% 100%, rgba(60, 50, 10, 0.10) 0%, rgba(8,10,14,0) 50%),
            #080A0E !important;
        background-attachment: fixed !important;
    }
    [data-testid="stHeader"] {
        background: transparent !important;
    }

    /* ── SIDEBAR PREMIUM GLASS & GRADIENT ── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0d1117 0%, #07090e 100%) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05) !important;
    }

    /* ── CUSTOM SLIM & NEON SCROLLBAR ── */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    ::-webkit-scrollbar-track {
        background: #07090e !important;
    }
    ::-webkit-scrollbar-thumb {
        background: rgba(232, 255, 58, 0.2) !important;
        border-radius: 10px !important;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #E8FF3A !important;
    }

    /* ── CORREZIONE HOVER GLOW SULLE KPI CARDS ── */
    .kpi-card:hover {
        border-color: #E8FF3A !important;
        transform: translateY(-4px) !important;
        box-shadow: 0 10px 30px rgba(232, 255, 58, 0.12) !important;
    }

    /* ── TIMELINE EVENTI (compleanni & ricorrenze) — scorrimento orizzontale ──
           Boxed come le altre alert card, e sempre su una riga (niente wrap
           né "buchi" sfalsati): la track è larga quanto il suo contenuto
           (width: max-content) e scrolla solo se non ci sta tutta. ── */
    .evt-timeline-wrap {
        position: relative; margin: 4px 0 22px 0; padding: 16px 14px 18px 14px;
        background: rgba(255,255,255,0.025);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 12px;
        overflow-x: auto; overflow-y: hidden; white-space: nowrap;
        scrollbar-width: thin;
    }
    .evt-timeline-track {
        position: relative; display: flex; flex-wrap: nowrap; align-items: flex-start;
        gap: 0; width: max-content; padding: 18px 4px 0 4px;
    }
    .evt-timeline-track::before {
        content: ''; position: absolute; top: 29px; left: 0; right: 0; height: 2px;
        background: linear-gradient(90deg, rgba(232,255,58,0.35), rgba(255,255,255,0.06));
    }
    .evt-node {
        position: relative; display: flex; flex: 0 0 auto; flex-direction: column; align-items: center;
        width: 116px; flex-shrink: 0; white-space: normal; text-align: center;
    }
    .evt-node-dot {
        width: 22px; height: 22px; border-radius: 50%; display: flex; align-items: center; justify-content: center;
        font-size: 12px; background: #0d1117; border: 2px solid rgba(255,255,255,0.18);
        margin-bottom: 10px; position: relative; z-index: 1; transition: transform 0.15s, box-shadow 0.15s;
    }
    .evt-node:hover .evt-node-dot { transform: scale(1.12); }
    .evt-node.evt-today .evt-node-dot {
        border-color: #E8FF3A; background: rgba(232,255,58,0.12);
        box-shadow: 0 0 14px rgba(232,255,58,0.55);
        animation: evtPulse 1.8s ease-in-out infinite;
    }
    @keyframes evtPulse {
        0%, 100% { box-shadow: 0 0 10px rgba(232,255,58,0.4); }
        50% { box-shadow: 0 0 20px rgba(232,255,58,0.8); }
    }
    .evt-node-date {
        font-family: 'DM Mono', monospace; font-size: 10px; letter-spacing: 1px;
        color: rgba(255,255,255,0.45); margin-bottom: 4px;
    }
    .evt-node.evt-today .evt-node-date { color: #E8FF3A; font-weight: 700; }
    .evt-node-name {
        font-family: 'DM Sans', sans-serif; font-size: 12.5px; font-weight: 600;
        color: #E8EDF5; line-height: 1.25; padding: 0 4px;
    }
    .evt-node-tag {
        font-family: 'DM Mono', monospace; font-size: 9px; letter-spacing: 0.5px;
        color: rgba(255,255,255,0.35); margin-top: 3px;
    }
    .evt-node.evt-today .evt-node-tag { color: rgba(232,255,58,0.8); }
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
# ── HOVER TOOLTIP NEON: box scuro, bordo giallo Amsicora, font mono ──
amsicora_template.layout.hoverlabel = dict(
    bgcolor="#0d1117",
    bordercolor="#E8FF3A",
    font=dict(family="DM Mono, monospace", color="#E8EDF5", size=12),
    align="left",
)
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
    b64_string = get_logo_b64()

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
    b64_string_logo = get_logo_b64()

    logo_html =f'<div style="flex-shrink: 0; margin-top: 2px;"><img src="data:image/png;base64,{b64_string_logo}" style="width: 70px; height: 70px; border-radius: 50%; border: 3px solid #E8FF3A; box-shadow: 0 0 12px rgba(232,255,58,0.3); display: block;"></div>'
    
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

def make_alert_card(label, text, icon, color, bg_alpha="0.1"):
    """Card alert generica con bordo colorato a sinistra, in stile coerente con quelle esistenti in Home."""
    return f"""
    <div style="background: rgba({color[1]},{bg_alpha}); border-left: 4px solid {color[0]}; border-radius: 8px; padding: 14px; margin-bottom: 12px;">
        <div style="display: flex; gap: 10px; align-items: flex-start;">
            <span style="font-size: 24px; margin-top: 2px;">{icon}</span>
            <div style="flex: 1;">
                <div style="color: {color[0]}; font-weight: 700; font-family: 'DM Mono'; letter-spacing: 1px; font-size: 10px; margin-bottom: 4px;">{label}</div>
                <div style="color: #fff; font-size: 0.9em;">{text}</div>
            </div>
        </div>
    </div>
    """

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
                distanze_opts = [30, 40, 50, 60, 80, 100, 120, 150, 180, 200, 250, 300, 400]
                prove = []
                for i in range(1, 13):
                    if i > 1:
                        st.markdown("<hr class='mobile-divider'>", unsafe_allow_html=True)
                    c1, c2, c3 = st.columns([1, 1, 2])

                    dist_i = c1.selectbox(f"🎯 PROVA {i} (Distanza)", ["-"] + [f"{d}m" for d in distanze_opts], key=f"dist_{i}")
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
            
            # ── Stacked per esercizio + rolling avg 3 sett. + annotazione picco ──
            tonn_ex_all = df_v_tonn.groupby(['Week', 'Esercizio'])['Tonnellaggio'].sum().reset_index()
            tonn_weekly_sorted = tonn_weekly.sort_values('Week').copy()
            tonn_weekly_sorted['Week_Label'] = tonn_weekly_sorted['Week'].dt.strftime('%d %b')
            tonn_weekly_sorted['Rolling3']   = tonn_weekly_sorted['Tonnellaggio'].rolling(3, min_periods=1).mean().round(0)
            all_week_labels = tonn_weekly_sorted['Week_Label'].tolist()
            all_week_dates  = tonn_weekly_sorted['Week'].tolist()  # per asse X ordinato
            # Top 6 esercizi per tonnellaggio totale nel periodo
            _top_ex = df_v_tonn.groupby('Esercizio')['Tonnellaggio'].sum().nlargest(6).index.tolist()
            tonn_ex_filtered = tonn_ex_all[tonn_ex_all['Esercizio'].isin(_top_ex)].copy()
            tonn_ex_filtered['Week_Label'] = tonn_ex_filtered['Week'].dt.strftime('%d %b')
            # Picco settimana
            _peak_idx_tonn = tonn_weekly_sorted['Tonnellaggio'].idxmax() if not tonn_weekly_sorted.empty else None
            _peak_wlabel   = tonn_weekly_sorted.loc[_peak_idx_tonn, 'Week_Label'] if _peak_idx_tonn is not None else None
            _peak_kg_val   = tonn_weekly_sorted.loc[_peak_idx_tonn, 'Tonnellaggio'] if _peak_idx_tonn is not None else 0

            fig = make_subplots(specs=[[{"secondary_y": True}]])

            # Stacked bars per esercizio
            _ex_palette = ["#4A9EFF", "#bf5fff", "#ff9800", "#ffeb3b", "#00e676", "#f44336"]
            for _ex_i, _ex_name in enumerate(_top_ex):
                _ex_sub = tonn_ex_filtered[tonn_ex_filtered['Esercizio'] == _ex_name]
                _ex_map = dict(zip(_ex_sub['Week_Label'], _ex_sub['Tonnellaggio']))
                _ex_y   = [_ex_map.get(lbl, 0) for lbl in all_week_labels]
                fig.add_trace(go.Bar(
                    x=all_week_dates, y=_ex_y,
                    name=_ex_name,
                    marker_color=_ex_palette[_ex_i % len(_ex_palette)],
                    opacity=0.82,
                ), secondary_y=False)

            # Linea rolling avg 3 settimane
            fig.add_trace(go.Scatter(
                x=all_week_dates, y=tonn_weekly_sorted['Rolling3'].tolist(),
                name="Media 3 sett.",
                mode='lines',
                line=dict(color="rgba(255,255,255,0.5)", width=2, dash='dot'),
            ), secondary_y=False)

            # Annotazione settimana picco
            if _peak_wlabel and _peak_kg_val > 0:
                fig.add_annotation(
                    x=tonn_weekly_sorted.loc[_peak_idx_tonn, 'Week'], y=_peak_kg_val, yref="y",
                    text=f"🏋️ {_peak_kg_val:,.0f}kg".replace(",", "."),
                    showarrow=True, arrowhead=2, arrowcolor="#E8FF3A",
                    font=dict(family="DM Mono", size=10, color="#E8FF3A"),
                    bgcolor="rgba(232,255,58,0.08)", bordercolor="#E8FF3A", borderwidth=1,
                    ay=-38,
                )

            # Linea tempi gara + PB markers
            valid_times = merged.dropna(subset=['Tempo'])
            if not valid_times.empty:
                fig.add_trace(go.Scatter(
                    x=valid_times['Week_Label'], y=valid_times['Tempo'],
                    name=f"Tempo {dist_ref}m (s)",
                    mode='lines+markers',
                    line=dict(color="#FFFFFF", width=3.5),
                    marker=dict(size=8, color="#080A0E", line=dict(width=2, color="#FFFFFF")),
                    connectgaps=True
                ), secondary_y=True)

                pb_points = valid_times[valid_times['is_PB'] == True]
                if not pb_points.empty:
                    fig.add_trace(go.Scatter(
                        x=pb_points['Week_Label'], y=pb_points['Tempo'],
                        mode='markers', name="Personal Best (Halo)",
                        marker=dict(size=24, color="rgba(184,255,138,0.15)", line=dict(width=2, color="rgba(184,255,138,0.6)")),
                        showlegend=False, hoverinfo='skip'
                    ), secondary_y=True)
                    fig.add_trace(go.Scatter(
                        x=pb_points['Week_Label'], y=pb_points['Tempo'],
                        mode='markers', name="Personal Best",
                        marker=dict(size=10, color="#B8FF8A"), showlegend=True
                    ), secondary_y=True)

            fig.update_layout(
                barmode='stack',
                template=THEME_TEMPLATE,
                height=440,
                margin=dict(l=20, r=20, t=50, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1,
                            font=dict(family="'DM Mono', monospace", size=10, color="rgba(255,255,255,0.55)")),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(255,255,255,0.02)",
                title=dict(text="<span style='letter-spacing: 2px;'>TONNELLAGGIO PER ESERCIZIO + PERFORMANCE</span>",
                           font=dict(family="'DM Mono', monospace", size=11, color="rgba(255,255,255,0.4)")),
            )
            fig.update_xaxes(type='date', tickformat='%d %b', tickfont=dict(color='rgba(255,255,255,0.3)'), showgrid=False)
            fig.update_yaxes(title_text="Volume Palestra (kg)", secondary_y=False, showgrid=False,
                             zeroline=False, color="#4A9EFF", tickfont=dict(color="rgba(255,255,255,0.3)"))
            if not valid_times.empty:
                fig.update_yaxes(title_text=f"Tempo Gara (s)", secondary_y=True, autorange="reversed",
                                 showgrid=True, gridcolor="rgba(255,255,255,0.04)",
                                 zeroline=False, tickfont=dict(color="rgba(255,255,255,0.3)"))

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
    df_atleti_full = get_atleti(with_foto=False)  # homepage: solo anagrafica, niente foto base64
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
    # ── COMPLEANNI IN ARRIVO (prossimi 7 giorni, escluso oggi) ──
    compleanni_arrivo = []  # (nome, giorni_rimanenti)
    if not df_atleti_full.empty:
        for _, row in df_atleti_full.iterrows():
            if pd.notna(row.get('data_nascita')):
                try:
                    dn = pd.to_datetime(row['data_nascita'])
                    prossimo = dn.replace(year=oggi_tz.year)
                    if prossimo.date() < oggi_tz.date():
                        prossimo = prossimo.replace(year=oggi_tz.year + 1)
                    giorni = (prossimo.date() - oggi_tz.date()).days
                    if 0 < giorni <= 7:
                        compleanni_arrivo.append((row['nome_completo'], giorni))
                except:
                    pass
    compleanni_arrivo.sort(key=lambda x: x[1])

    # ── TIMELINE EVENTI: unisce compleanni di oggi (giorni=0) e in arrivo (1-7gg).
    #    Se non ci sono compleanni, la timeline resta comunque visibile con il solo
    #    marcatore "OGGI" a indicare il giorno corrente. ──
    eventi_compleanno = [(nome, 0) for nome in compleanni] + list(compleanni_arrivo)
    eventi_compleanno.sort(key=lambda x: x[1])

    nodi_html = ""
    ha_oggi = any(g == 0 for _, g in eventi_compleanno)
    if not ha_oggi:
        data_oggi = oggi_tz.strftime('%d %b').upper()
        nodi_html += f"""
        <div class="evt-node evt-today">
            <div class="evt-node-date">{data_oggi}</div>
            <div class="evt-node-dot">📍</div>
            <div class="evt-node-name">Oggi</div>
            <div class="evt-node-tag">Nessun compleanno</div>
        </div>
        """
    for nome, giorni in eventi_compleanno:
        data_evt = (oggi_tz + pd.Timedelta(days=giorni)).strftime('%d %b').upper()
        is_today = giorni == 0
        nodo_cls = "evt-node evt-today" if is_today else "evt-node"
        tag = "OGGI 🎉" if is_today else f"in {giorni} gg"
        nodi_html += f"""
        <div class="{nodo_cls}">
            <div class="evt-node-date">{data_evt}</div>
            <div class="evt-node-dot">🎂</div>
            <div class="evt-node-name">{nome}</div>
            <div class="evt-node-tag">{tag}</div>
        </div>
        """
    html_timeline = f"""
    <div class="evt-timeline-wrap" style="height: 100%; margin: 0;">
        <div class="evt-timeline-track">{nodi_html}</div>
    </div>
    """

    # ── STOP VBT: atleti attivi in pista ma fermi sul monitoraggio forza (>14 gg) ──
    running_last = df_running.groupby('Atleta')['Data'].max() if not df_running.empty else pd.Series(dtype='datetime64[ns]')
    vbt_last = df_vbt.groupby('Atleta')['Data'].max() if not df_vbt.empty else pd.Series(dtype='datetime64[ns]')
    stop_vbt = []
    for atl, rdate in running_last.items():
        if pd.notnull(rdate) and (oggi_tz - rdate).days <= 14:
            vdate = vbt_last.get(atl)
            if pd.isnull(vdate) or (oggi_tz - vdate).days > 14:
                stop_vbt.append(atl)

    # ── TREND NEGATIVO: peggioramento sulle ultime sessioni di una distanza ──
    trend_negativo = []  # (atleta, distanza, var_pct)
    if not df_running.empty:
        for (atl, dist), g in df_running.groupby(['Atleta', 'Distanza']):
            g2 = g.dropna(subset=['Tempo']).sort_values('Data')
            if len(g2) >= 4:
                last4 = g2['Tempo'].tail(4).to_numpy()
                prev2_avg, last2_avg = last4[:2].mean(), last4[2:].mean()
                if prev2_avg > 0:
                    var_pct = (last2_avg - prev2_avg) / prev2_avg * 100
                    if var_pct > 2:
                        trend_negativo.append((atl, dist, var_pct))
    trend_negativo.sort(key=lambda x: -x[2])

    # ── TOP ADERENZA SETTIMANALE ──
    ultimi_7gg = oggi_tz - pd.Timedelta(days=7)
    sess_7 = pd.concat([df_running[['Atleta', 'Data']], df_vbt[['Atleta', 'Data']]]) if (not df_running.empty or not df_vbt.empty) else pd.DataFrame(columns=['Atleta', 'Data'])
    sess_7 = sess_7[sess_7['Data'] >= ultimi_7gg]
    top_aderenza, top_aderenza_count = None, 0
    if not sess_7.empty:
        giorni_count = sess_7.groupby('Atleta')['Data'].apply(lambda s: s.dt.date.nunique())
        if not giorni_count.empty and giorni_count.max() >= 3:
            top_aderenza = giorni_count.idxmax()
            top_aderenza_count = int(giorni_count.max())

    # ── ANAGRAFICA INCOMPLETA ──
    anagrafica_incompleta = []
    if not df_atleti_full.empty:
        df_atleti_attivi = df_atleti_full
        if 'attivo' in df_atleti_full.columns:
            df_atleti_attivi = df_atleti_full[df_atleti_full['attivo'].fillna(True) != False]
        for _, row in df_atleti_attivi.iterrows():
            if pd.isna(row.get('data_nascita')) or pd.isna(row.get('peso')):
                anagrafica_incompleta.append(row['nome_completo'])

    # ── ALERT PERFORMANCE E MONITORAGGIO: card pre-costruite e poi accoppiate
    #    in righe (timeline+periodo, pb+inattivi, trend+stopvbt, ...) così non
    #    si creano più "buchi" quando una colonna ha più card dell'altra. ──
    html_periodo = f"""
    <div style="background: rgba(255,255,255,0.02); border-left: 4px solid rgba(255,255,255,0.1); border-radius: 8px; padding: 14px; height: 100%;">
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
    """

    if atleti_pb:
        txt = " e altri" if len(atleti_pb) > 3 else ""
        pb_list = ', '.join(list(atleti_pb)[:3]) + txt
        html_pb = f"""
        <div style="background: rgba(184,255,138,0.1); border-left: 4px solid #B8FF8A; border-radius: 8px; padding: 14px;">
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
        """
    else:
        html_pb = f"""
        <div style="background: rgba(255,255,255,0.02); border-left: 4px solid rgba(255,255,255,0.1); border-radius: 8px; padding: 14px;">
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
        """

    if inattivi:
        txt2 = " e altri" if len(inattivi) > 3 else ""
        inattivi_list = ', '.join(inattivi[:3]) + txt2
        html_inattivi = f"""
        <div style="background: rgba(255,75,75,0.15); border-left: 4px solid #FF6B6B; border-radius: 8px; padding: 14px;">
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
        """
    else:
        html_inattivi = f"""
        <div style="background: rgba(22,163,74,0.1); border-left: 4px solid #16a34a; border-radius: 8px; padding: 14px;">
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
        """

    html_trend = None
    if trend_negativo:
        righe_t = [f"{atl} sui {int(dist)}m ({var:+.1f}%)" for atl, dist, var in trend_negativo[:3]]
        html_trend = make_alert_card(
            "TREND IN CALO",
            f"Tempi in peggioramento nelle ultime sessioni: <strong>{', '.join(righe_t)}</strong>. Da monitorare.",
            "📉", ("#FF6B6B", "255,107,107")
        )

    html_stopvbt = None
    if stop_vbt:
        txt3 = " e altri" if len(stop_vbt) > 3 else ""
        stop_vbt_list = ', '.join(stop_vbt[:3]) + txt3
        html_stopvbt = make_alert_card(
            "STOP VBT (>14 GG)",
            f"<strong>{stop_vbt_list}</strong> si allenano in pista ma non registrano sessioni VBT da oltre 14 giorni. Monitoraggio forza fermo.",
            "🏋️", ("#FF9A3A", "255,154,58")
        )

    html_volume = None
    if p_km > 0:
        html_volume = f"""
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
        """

    html_aderenza = None
    if top_aderenza:
        html_aderenza = make_alert_card(
            "TOP ADERENZA (7 GG)",
            f"<strong>{top_aderenza}</strong> è l'atleta più costante della settimana con {top_aderenza_count} giorni di allenamento. 💪",
            "🔥", ("#E8FF3A", "232,255,58")
        )

    html_anagrafica = None
    if anagrafica_incompleta:
        txt4 = " e altri" if len(anagrafica_incompleta) > 3 else ""
        anagrafica_list = ', '.join(anagrafica_incompleta[:3]) + txt4
        html_anagrafica = make_alert_card(
            "ANAGRAFICA INCOMPLETA",
            f"<strong>{anagrafica_list}</strong> non hanno data di nascita o peso salvati nel profilo.",
            "📋", ("rgba(255,255,255,0.5)", "255,255,255")
        )

    def render_row(left_html, right_html=None):
        """Riga a due colonne se entrambe le card sono presenti, altrimenti
        la singola card occupa tutta la larghezza: niente più "buchi"."""
        if left_html and right_html:
            rc1, rc2 = st.columns(2)
            with rc1:
                st.markdown(left_html, unsafe_allow_html=True)
            with rc2:
                st.markdown(right_html, unsafe_allow_html=True)
        elif left_html:
            st.markdown(left_html, unsafe_allow_html=True)
        elif right_html:
            st.markdown(right_html, unsafe_allow_html=True)
        if left_html or right_html:
            st.markdown('<div style="height: 12px;"></div>', unsafe_allow_html=True)

    render_row(html_timeline, html_periodo)
    render_row(html_pb, html_inattivi)
    render_row(html_trend, html_stopvbt)
    render_row(html_volume, html_aderenza)
    render_row(html_anagrafica, None)

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
        def _hex_to_rgb(h):
            h = h.lstrip('#')
            if len(h) != 6:
                return "255,255,255"
            return f"{int(h[0:2],16)},{int(h[2:4],16)},{int(h[4:6],16)}"

        for i in range(0, len(roster_df), 3):
            cols = st.columns(3)
            for j in range(3):
                if i + j < len(roster_df):
                    row = roster_df.iloc[i + j]
                    card_key = f"rostercard_{i + j}"
                    row_rgb = _hex_to_rgb(row["color"])
                    st.markdown(f"""
                    <style>
                    .st-key-{card_key} {{
                        background: radial-gradient(circle at 85% 0%, rgba({row_rgb},0.12) 0%, rgba({row_rgb},0.03) 45%, rgba(255,255,255,0.015) 100%);
                        border: 1px solid rgba({row_rgb},0.35) !important;
                        border-radius: 14px !important;
                        transition: border-color 0.15s, box-shadow 0.15s;
                    }}
                    .st-key-{card_key}:hover {{
                        border-color: rgba({row_rgb},0.8) !important;
                        box-shadow: 0 0 24px rgba({row_rgb},0.15);
                    }}
                    </style>
                    """, unsafe_allow_html=True)
                    with cols[j].container(border=True, key=card_key):
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
    tab_labels = ["⚡ Velocità & Trend", "💪 Forza & VBT",
                  "🔮 Previsioni Gara", "⚖️ Transfer Palestra", "🏅 PB & Gare"]
    
    tabs = st.tabs(tab_labels, key="dettaglio_tab_main", on_change="rerun")
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

            # ── GRIGLIA CARD SEZIONI (Proposta C) ──────────────────────────
            for k in ['_s1_pb', '_s1_storico', '_s1_correggi']:
                if k not in st.session_state:
                    st.session_state[k] = False

            # Costruisce dinamicamente le card disponibili
            _show_storico  = selected_athlete != "Tutta la squadra"
            _show_correggi = can_edit and selected_athlete != "Tutta la squadra"

            _pb_sub = "Migliori tempi · squadra" if selected_athlete == "Tutta la squadra" else "I migliori tempi dell'atleta"
            _cards = [("🏆", "Classifica PB", _pb_sub, "_s1_pb")]
            if _show_storico:
                _cards.append(("📖", "Storico Completo", "Tutte le prove registrate", "_s1_storico"))
            if _show_correggi:
                _cards.append(("✏️", "Correggi Tempo", "Modifica o elimina · admin", "_s1_correggi"))

            _sec_keys = [k for _, _, _, k in _cards]

            # Griglia bottoni card — Streamlit nativo con CSS marker
            st.markdown('<span id="sec-cards-marker"></span>', unsafe_allow_html=True)
            _btn_cols = st.columns(len(_cards))
            for i, (icon, title, sub, key) in enumerate(_cards):
                _is_active = st.session_state.get(key, False)
                # Icona grande di sfondo nell'angolo (come le KPI card in alto)
                st.markdown(
                    "<style>.st-key-secbtn_" + key + " button[kind=\"secondary\"]::after{"
                    "content:\"" + icon + "\";}</style>",
                    unsafe_allow_html=True,
                )
                # Evidenzia in giallo la card attiva (sezione aperta)
                if _is_active:
                    st.markdown(
                        "<style>.st-key-secbtn_" + key + " button[kind=\"secondary\"]{"
                        "border-color:#E8FF3A !important;"
                        "background:rgba(232,255,58,0.14) !important;"
                        "color:#E8FF3A !important;"
                        "box-shadow:0 0 22px rgba(232,255,58,0.18) !important;}</style>",
                        unsafe_allow_html=True,
                    )
                lbl = f"**{title}**\n{sub}"
                with _btn_cols[i]:
                    if st.button(lbl, key=f"secbtn_{key}", use_container_width=True, type="secondary"):
                        # Accordion: apri solo questa e chiudi le altre.
                        # Ri-cliccando la card già attiva, la si chiude.
                        for _k in _sec_keys:
                            st.session_state[_k] = False
                        st.session_state[key] = not _is_active
                        st.rerun()

            # ── CONTENUTO SEZIONE: CLASSIFICA PB ───────────────────────────
            if st.session_state.get('_s1_pb'):
                st.markdown('<div class="sec-content-block">', unsafe_allow_html=True)
                st.markdown("#### 🏆 Classifica Personal Best")
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
                st.markdown('</div>', unsafe_allow_html=True)

            # ── CONTENUTO SEZIONE: STORICO COMPLETO ────────────────────────
            if _show_storico and st.session_state.get('_s1_storico'):
                st.markdown('<div class="sec-content-block">', unsafe_allow_html=True)
                st.markdown("#### 📖 Storico Risultati Completo")
                st.markdown("Tutte le prestazioni registrate dall'atleta, raggruppate per distanza. **Ordinate dalla più vecchia alla più recente.** *(I filtri distanze e date del menù laterale non influenzano questa tabella.)*")
                df_storico = df_running[df_running['Atleta'] == selected_athlete].copy()
                if not df_storico.empty:
                    df_storico = df_storico.sort_values('Data', ascending=True)
                    df_storico['Data'] = df_storico['Data'].dt.strftime('%d/%m/%Y')
                    for d in sorted(df_storico['Distanza'].unique()):
                        sub_df = df_storico[df_storico['Distanza'] == d][['Data', 'Tempo', 'Note']]
                        st.markdown(f"**🏃 {int(d)}m** — {len(sub_df)} prove | PB: {sub_df['Tempo'].min():.2f}s")
                        st.dataframe(sub_df, use_container_width=True, hide_index=True)
                else:
                    st.info("Nessuna prova presente per questo atleta.")
                st.markdown('</div>', unsafe_allow_html=True)

            # ── SEZIONE CORREZIONE TEMPI (solo per atleta in sessione o admin) ──
            if _show_correggi and st.session_state.get('_s1_correggi'):
                st.markdown('<div class="sec-content-block">', unsafe_allow_html=True)
                st.markdown("#### ✏️ Correggi o Elimina un Tempo")
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
                st.markdown('</div>', unsafe_allow_html=True)


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
                    scatter_df = df_v_ex[df_v_ex['Esercizio'] == sel_ex].dropna(subset=['Carico', 'Vel_media', 'Potenza_media'])

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
        st.markdown("<h3 style='font-family: Bebas Neue; color: #fff; margin-bottom: 0; line-height: 1.1; font-size: 38px;'>MODELLI DI <span style='color: #E8FF3A;'>PREVISIONE GARA</span></h3>", unsafe_allow_html=True)
        st.markdown("<span style='font-family: DM Mono; font-size: 11px; color: rgba(255,255,255,0.4); letter-spacing: 2px;'>DUE APPROCCI DISTINTI · SCEGLI QUELLO PIÙ ADATTO ALL'ATLETA</span>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        # Estrazione PB atleta (storico allenamenti)
        pb_30, pb_60, pb_80, pb_100, pb_200 = None, None, None, None, None
        pb_200_auto, pb_300_auto, pb_400_auto = None, None, None
        if selected_athlete != "Tutta la squadra" and len(df_r) > 0:
            pb_corse = df_r.groupby('Distanza')['Tempo'].min()
            pb_30   = float(pb_corse.get(30, None))  if pd.notna(pb_corse.get(30, None))  else None
            pb_60   = float(pb_corse.get(60, None))  if pd.notna(pb_corse.get(60, None))  else None
            pb_80   = float(pb_corse.get(80, None))  if pd.notna(pb_corse.get(80, None))  else None
            pb_100  = float(pb_corse.get(100, None)) if pd.notna(pb_corse.get(100, None)) else None
            pb_200_auto = float(pb_corse.get(200, None)) if pd.notna(pb_corse.get(200, None)) else None
            pb_300_auto = float(pb_corse.get(300, None)) if pd.notna(pb_corse.get(300, None)) else None
            pb_400_auto = float(pb_corse.get(400, None)) if pd.notna(pb_corse.get(400, None)) else None
            pb_200 = pb_200_auto

        # Estrazione PB atleta (gare ufficiali)
        pb_gare = {}
        if selected_athlete != "Tutta la squadra" and "atleta_info" in locals() and atleta_info:
            from supabase_connector import get_gare_ufficiali
            df_g_pb = get_gare_ufficiali(atleta_info["id"])
            if not df_g_pb.empty:
                df_g_pb['tempo_float'] = pd.to_numeric(df_g_pb['Prestazione'].astype(str).str.replace(',', '.'), errors='coerce')
                for spec, group in df_g_pb.groupby('Specialità'):
                    spec_str = str(spec).strip().lower()
                    if spec_str.endswith('m'):
                        spec_clean = spec_str[:-1]
                    else:
                        spec_clean = spec_str
                    try:
                        dist_val = int(spec_clean)
                        min_time = group['tempo_float'].min()
                        if pd.notna(min_time):
                            pb_gare[dist_val] = min_time
                    except ValueError:
                        pass

        # ──────────────────────────────────────────────────────────────────
        # SEZIONE 1 — MODELLO VITTORI (Calcolatore Reverse)
        # ──────────────────────────────────────────────────────────────────
        st.markdown("""
        <div style='display:flex; align-items:center; gap:14px; margin-bottom:6px;'>
            <div style='width:4px; height:36px; background:#E8FF3A; border-radius:2px;'></div>
            <div>
                <div style='font-family:Bebas Neue; font-size:26px; color:#E8FF3A; letter-spacing:1px; line-height:1;'>MODELLO VITTORI</div>
                <div style='font-family:DM Mono; font-size:10px; color:rgba(255,255,255,0.4); letter-spacing:2px;'>CALCOLATORE REVERSE · OBIETTIVO → SPLIT NECESSARI</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<p style='font-size:13px; color:rgba(255,255,255,0.55); margin-bottom:16px;'>Dato un tempo obiettivo su una gara target, il modello Vittori calcola a ritroso quali split di allenamento (30m, 60m, 80m) devi raggiungere per avere il potenziale fisico di correre quel tempo.</p>", unsafe_allow_html=True)

        with st.container():
            col_sx, col_dx = st.columns([1, 4])
            gender_sel = col_sx.radio("Sesso", ["Maschile", "Femminile"], horizontal=True, label_visibility="collapsed")
            g_code = "M" if gender_sel == "Maschile" else "F"

            # Scelta sorgente PB
            pb_source = st.radio(
                "Sorgente dati per i tuoi PB di riferimento (usati per il calcolo del Gap):",
                ["📂 Storico Allenamenti (Pista)", "🏅 Gare Ufficiali (Database PB)"],
                horizontal=True
            )

            if pb_source == "📂 Storico Allenamenti (Pista)":
                pb_30_ref, pb_60_ref, pb_80_ref, pb_100_ref = pb_30, pb_60, pb_80, pb_100
            else:
                pb_30_ref = pb_gare.get(30, None)
                pb_60_ref = pb_gare.get(60, None)
                pb_80_ref = pb_gare.get(80, None)
                pb_100_ref = pb_gare.get(100, None)

            st.markdown("<small style='color:rgba(255,255,255,0.45);'>I tempi di riferimento sotto vengono estratti automaticamente. Se vuoti o se vuoi fare delle prove, puoi modificarli o inserirli a mano:</small>", unsafe_allow_html=True)
            vcol1, vcol2, vcol3, vcol4 = st.columns(4)
            val_pb30 = vcol1.number_input("Rif. 30m (s)", value=pb_30_ref, step=0.05, format="%.2f", placeholder="Vuoto")
            val_pb60 = vcol2.number_input("Rif. 60m (s)", value=pb_60_ref, step=0.05, format="%.2f", placeholder="Vuoto")
            val_pb80 = vcol3.number_input("Rif. 80m (s)", value=pb_80_ref, step=0.05, format="%.2f", placeholder="Vuoto")
            val_pb100 = vcol4.number_input("Rif. 100m (s)", value=pb_100_ref, step=0.05, format="%.2f", placeholder="Vuoto")

            st.markdown("<br>", unsafe_allow_html=True)

            tr1, tr2 = st.columns([1, 2])
            tgt_dist = tr1.selectbox("Gara Obiettivo", ["80m", "100m", "200m", "250m", "400m"])
            tgt_t = tr2.number_input("Tempo Bersaglio (s)", value=None, step=0.10, placeholder="es. 10.85 per i 100m")

            p_tgt = tgt_t if (tgt_t and tgt_t > 0) else None

            if p_tgt:
                need100, need80, need60, need30 = None, None, None, None
                if tgt_dist == "80m":
                    need80 = p_tgt
                    need100 = round(p_tgt * 1.231, 2)
                    need60 = round((need100 - 0.18) / 1.576, 2)
                    need30 = round((need100 - 0.30) / 2.85, 2)
                elif tgt_dist == "100m":
                    need100 = p_tgt
                    need60 = round((p_tgt - 0.18) / 1.576, 2)
                    need30 = round((p_tgt - 0.30) / 2.85, 2)
                    need80 = round((need100 + need60) / 2, 2)
                elif tgt_dist == "200m":
                    need100 = round((p_tgt + 0.24) / 2, 2)
                    need60 = round((need100 - 0.18) / 1.576, 2)
                    need30 = round((need100 - 0.30) / 2.85, 2)
                    need80 = round((need100 + need60) / 2, 2)
                elif tgt_dist == "400m":
                    need100 = round(((p_tgt - (4.2 if g_code == "F" else 3.8)) / 2 + 0.24) / 2, 2)
                    need60 = round((need100 - 0.18) / 1.576, 2)
                    need30 = round((need100 - 0.30) / 2.85, 2)
                    need80 = round((need100 + need60) / 2, 2)

                cur_100_est = val_pb100 or (round(val_pb80 * 1.231, 2) if val_pb80 else (round(val_pb60 * 1.576 + 0.18, 2) if val_pb60 else (round(val_pb30 * 2.85 + 0.30, 2) if val_pb30 else None)))
                gap = round(cur_100_est - need100, 2) if cur_100_est and need100 else None


                st.markdown("<br><div style='padding:20px; border-radius:12px; border:1px solid rgba(232,255,58,0.12); background:rgba(232,255,58,0.02);'>", unsafe_allow_html=True)
                if tgt_dist not in ("100m", "80m"):
                    st.markdown(f"<div style='display:flex; justify-content:space-between; align-items:center; padding-bottom:10px; border-bottom:1px solid rgba(255,255,255,0.05);'><div><span style='font-family:DM Mono; font-size:11px; color:#FF9A3A; letter-spacing:1px;'>100m NECESSARIO COME STEP</span></div><span style='font-family:Bebas Neue; font-size:26px; color:#FF9A3A;'>{need100:.2f}s</span></div>", unsafe_allow_html=True)
                if tgt_dist == "80m":
                    st.markdown(f"<div style='display:flex; justify-content:space-between; align-items:center; padding-bottom:10px; border-bottom:1px solid rgba(255,255,255,0.05);'><div><span style='font-family:DM Mono; font-size:11px; color:#FF9A3A; letter-spacing:1px;'>100m TEORICO ATTESO</span></div><span style='font-family:Bebas Neue; font-size:26px; color:#FF9A3A;'>{need100:.2f}s</span></div>", unsafe_allow_html=True)
                if need80:
                    st.markdown(f"<div style='display:flex; justify-content:space-between; align-items:center; padding:15px; margin-top:10px; border-radius:8px; background:rgba(232,255,58,0.06); border:1px solid rgba(232,255,58,0.2);'><div><span style='font-family:DM Mono; font-size:11px; color:#E8FF3A; letter-spacing:1px;'>🎯 TARGET 80m (allenamento)</span></div><span style='font-family:Bebas Neue; font-size:32px; color:#E8FF3A;'>{need80:.2f}s</span></div>", unsafe_allow_html=True)
                st.markdown(f"<div style='display:flex; justify-content:space-between; align-items:center; padding:15px; margin-top:10px; border-radius:8px; background:rgba(232,255,58,0.03); border:1px solid rgba(232,255,58,0.1);'><div><span style='font-family:DM Mono; font-size:11px; color:#E8FF3A; letter-spacing:1px;'>🎯 TARGET 60m (allenamento)</span></div><span style='font-family:Bebas Neue; font-size:28px; color:#E8FF3A;'>{need60:.2f}s</span></div>", unsafe_allow_html=True)
                st.markdown(f"<div style='display:flex; justify-content:space-between; align-items:center; padding:10px; margin-top:10px;'><div><span style='font-family:DM Mono; font-size:11px; color:#B8FF8A; letter-spacing:1px;'>🎯 TARGET 30m (allenamento)</span></div><span style='font-family:Bebas Neue; font-size:22px; color:#B8FF8A;'>{need30:.2f}s</span></div>", unsafe_allow_html=True)
                if gap is not None:
                    g_col = "#FF4B4B" if gap > 0 else "#B8FF8A"
                    g_bg = "rgba(255,75,75,0.08)" if gap > 0 else "rgba(184,255,138,0.08)"
                    g_bord = "rgba(255,75,75,0.25)" if gap > 0 else "rgba(184,255,138,0.25)"
                    g_txt = "+" + str(gap) if gap > 0 else str(gap)
                    lbl_gap = "⚡ GAP DA COLMARE sui 100m" if gap > 0 else "✅ TARGET GIÀ RAGGIUNGIBILE"
                    st.markdown(f"<div style='margin-top:15px; padding:15px; border-radius:10px; background:{g_bg}; border:1px solid {g_bord};'><div style='font-family:DM Mono; font-size:10px; color:{g_col}; letter-spacing:2px; margin-bottom:6px;'>{lbl_gap}</div><div style='display:flex; align-items:baseline; gap:10px;'><span style='font-family:Bebas Neue; font-size:36px; color:{g_col}; line-height:1;'>{g_txt}s</span><span style='font-size:12px; color:rgba(255,255,255,0.4);'>vs 100m stimato attuale ({cur_100_est:.2f}s)</span></div></div>", unsafe_allow_html=True)
                else:
                    st.info("Per calcolare il Gap inserisci almeno una prova (100m, 80m, 60m o 30m) nel database.")
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.info("💡 Inserisci il tempo obiettivo per vedere i target di allenamento Vittori.")

        st.markdown("<br>", unsafe_allow_html=True)
        st.divider()
        st.markdown("<br>", unsafe_allow_html=True)

        # ──────────────────────────────────────────────────────────────────
        # SEZIONE 2 — MODELLO FISIOLOGICO 400m
        # ──────────────────────────────────────────────────────────────────
        st.markdown("""
        <div style='display:flex; align-items:center; gap:14px; margin-bottom:6px;'>
            <div style='width:4px; height:36px; background:#4A9EFF; border-radius:2px;'></div>
            <div>
                <div style='font-family:Bebas Neue; font-size:26px; color:#4A9EFF; letter-spacing:1px; line-height:1;'>MODELLO FISIOLOGICO 400m</div>
                <div style='font-family:DM Mono; font-size:10px; color:rgba(255,255,255,0.4); letter-spacing:2px;'>200m PB + 300m → STIMA POTENZIALE 400m</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<p style='font-size:13px; color:rgba(255,255,255,0.55); margin-bottom:4px;'>Questo modello stima il potenziale teorico sui 400m incrociando il PB sui 200m (indicatore di velocità pura) con il miglior 300m (indicatore di tenuta lattacida). Non usa le regressioni di Vittori: si basa sulla fisiologia della corsa prolungata.</p>", unsafe_allow_html=True)

        # Guida all'uso
        with st.expander("📖 Come usare questo modello — leggi prima", expanded=False):
            st.markdown("""
**Cosa inserire:**
- **PB 200m**: il Personal Best dell'atleta sui 200m, idealmente in gara ufficiale. È l'indicatore della velocità massima sostenibile. Viene pre-compilato dal database se disponibile.
- **Miglior 300m**: il miglior tempo registrato sui 300m, anche in allenamento. È la distanza chiave per stimare la tenuta lattacida. Se non lo hai, un 300m cronometrato in allenamento ad intensità massima va benissimo.
- **PB 400m attuale** *(opzionale)*: se inserito, consente di calcolare il margine tra il potenziale teorico e la prestazione reale.

---

**Come scegliere il Profilo Velocità:**

Il profilo velocità esprime quanto l'atleta "sprinta" i 200m rispetto a come li corre in un 400m reale. In un 400m, il primo 200m sarà sempre più lento del PB sui 200m:
- 🟢 **Efficiente / Naturale (+1.0s)**: atleta con ottima gestione, poco differenziale tra PB 200m e passaggio al 200m nel 400m. Tipico del 400ista puro con buona economia di corsa.
- 🟡 **Intermedio (+1.4s)**: il caso più comune. Il 200m del 400m è circa 1.4s più lento del PB.
- 🔴 **Velocista Puro (+1.8s)**: atleta da 100-200m che "soffre" nel 400m. Il primo 200m è molto più lento del PB per conservare energie, ma cala comunque nel finale.

---

**Come scegliere la Resistenza Lattacida (L):**

L è il numero di secondi che l'atleta aggiunge ai suoi 300m per completare i restanti 100m in un 400m reale (stanchezza + accumulo acido lattico):
- **L = 12** — Ottimo 400ista: atleta che mantiene bene la velocità anche negli ultimi 100m, con ottima clearance del lattato.
- **L = 13** — Buono: discreta tenuta nel finale, calo presente ma contenuto.
- **L = 14** — Medio: calo significativo negli ultimi 100m, atleta che "muore" nel rettilineo finale.
- **L = 15** — Carente: caduta marcata. Tipico del velocista puro o di chi ha poca base aerobica.

*Come stimare L empiricamente: cronometra un 400m in allenamento e confrontalo con (miglior 300m + tempo degli ultimi 100m isolati). La differenza è L.*

---

**Indice di Coerenza C = T300 − 1.5 × T200:**

Misura quanto i 300m dell'atleta sono "coerenti" con la sua velocità di base sui 200m. Un C basso significa che l'atleta tiene bene la velocità anche a distanze maggiori (talento naturale per il 400m). Un C alto segnala che la velocità cala in modo accentuato.
            """)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── INPUT ──────────────────────────────────────────────────────────
        st.markdown("<div style='font-family:DM Mono; font-size:10px; color:rgba(255,255,255,0.35); letter-spacing:2px; margin-bottom:8px;'>STEP 1 · INSERISCI I TEMPI</div>", unsafe_allow_html=True)
        col_in1, col_in2, col_in3 = st.columns(3)

        t200pb = col_in1.number_input(
            "🏃 PB 200m (s)",
            value=pb_200_auto, step=0.05, format="%.2f",
            placeholder="es. 22.50",
            help="Personal Best sui 200m, preferibilmente in gara ufficiale. Pre-compilato dal database se disponibile."
        )
        t300 = col_in2.number_input(
            "⏱ Miglior 300m (s)",
            value=pb_300_auto, step=0.05, format="%.2f",
            placeholder="es. 35.20",
            help="Miglior tempo sui 300m, anche in allenamento a massima intensità. Chiave per stimare la tenuta lattacida."
        )
        t400_reale = col_in3.number_input(
            "🎯 PB 400m attuale (s) — opzionale",
            value=pb_400_auto, step=0.10, format="%.2f",
            placeholder="es. 48.50",
            help="Se inserito, calcola L dal database (L = PB400 − Miglior300) e il margine tra potenziale e prestazione reale."
        )

        # ── AUTO-CALIBRAZIONE DAL DB ────────────────────────────────────────
        # L calibrato: se 400m e 300m sono entrambi disponibili (anche appena inseriti)
        _t300_for_cal  = t300       if (t300       and t300       > 0) else pb_300_auto
        _t400_for_cal  = t400_reale if (t400_reale and t400_reale > 0) else pb_400_auto
        _t200_for_cal  = t200pb     if (t200pb     and t200pb     > 0) else pb_200_auto

        L_db       = round(_t400_for_cal - _t300_for_cal, 2) if (_t400_for_cal and _t300_for_cal) else None
        SRI_db     = round(_t400_for_cal / (2 * _t200_for_cal), 4) if (_t400_for_cal and _t200_for_cal) else None

        # Mappa L_db → indice radio resistenza lattacida
        def _l_to_idx(l):
            if l is None: return 1
            if l <= 12.5: return 0
            if l <= 13.5: return 1
            if l <= 14.5: return 2
            return 3

        # Mappa SRI_db → indice radio profilo velocità
        def _sri_to_idx(sri):
            if sri is None: return 1
            if sri < 1.065: return 0
            if sri <= 1.080: return 1
            return 2

        l_default_idx      = _l_to_idx(L_db)
        offset_default_idx = _sri_to_idx(SRI_db)

        # Badge calibrazione da mostrare prima dei radio
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<div style='font-family:DM Mono; font-size:10px; color:rgba(255,255,255,0.35); letter-spacing:2px; margin-bottom:10px;'>STEP 2 · PROFILA L'ATLETA</div>", unsafe_allow_html=True)

        # Mostra badge di calibrazione se i dati vengono dal DB o dai campi compilati
        badge_col1, badge_col2 = st.columns(2)
        if SRI_db is not None:
            sri_labels = ["Efficiente/Naturale", "Intermedio", "Velocista Puro"]
            sri_colors = ["#00e676", "#ffeb3b", "#f44336"]
            sri_idx = _sri_to_idx(SRI_db)
            badge_col1.markdown(f"""
            <div style='padding:10px 14px; border-radius:8px; background:rgba(0,230,118,0.06); border:1px solid rgba(0,230,118,0.25); margin-bottom:10px;'>
                <div style='font-family:DM Mono; font-size:9px; color:rgba(255,255,255,0.4); letter-spacing:1px; margin-bottom:4px;'>📊 SRI CALCOLATO DAL DB</div>
                <span style='font-family:Bebas Neue; font-size:22px; color:{sri_colors[sri_idx]};'>{SRI_db:.4f}</span>
                <span style='font-size:12px; color:rgba(255,255,255,0.5); margin-left:8px;'>→ {sri_labels[sri_idx]}</span>
                <div style='font-size:11px; color:rgba(255,255,255,0.3); margin-top:2px;'>T400 / (2 × T200) = {_t400_for_cal:.2f} / (2 × {_t200_for_cal:.2f})</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            badge_col1.markdown("""
            <div style='padding:10px 14px; border-radius:8px; background:rgba(255,255,255,0.03); border:1px dashed rgba(255,255,255,0.1); margin-bottom:10px;'>
                <div style='font-family:DM Mono; font-size:9px; color:rgba(255,255,255,0.3); letter-spacing:1px;'>SRI NON CALCOLABILE</div>
                <div style='font-size:11px; color:rgba(255,255,255,0.25); margin-top:4px;'>Inserisci PB 200m e PB 400m per calcolo automatico</div>
            </div>
            """, unsafe_allow_html=True)

        if L_db is not None:
            l_labels = ["Ottimo 400ista", "Buono", "Medio", "Carente"]
            l_colors = ["#00e676", "#ffeb3b", "#ff9800", "#f44336"]
            l_idx = _l_to_idx(L_db)
            badge_col2.markdown(f"""
            <div style='padding:10px 14px; border-radius:8px; background:rgba(0,230,118,0.06); border:1px solid rgba(0,230,118,0.25); margin-bottom:10px;'>
                <div style='font-family:DM Mono; font-size:9px; color:rgba(255,255,255,0.4); letter-spacing:1px; margin-bottom:4px;'>📊 L CALCOLATO DAL DB</div>
                <span style='font-family:Bebas Neue; font-size:22px; color:{l_colors[l_idx]};'>{L_db:.2f}s</span>
                <span style='font-size:12px; color:rgba(255,255,255,0.5); margin-left:8px;'>→ {l_labels[l_idx]}</span>
                <div style='font-size:11px; color:rgba(255,255,255,0.3); margin-top:2px;'>T400 − T300 = {_t400_for_cal:.2f} − {_t300_for_cal:.2f}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            badge_col2.markdown("""
            <div style='padding:10px 14px; border-radius:8px; background:rgba(255,255,255,0.03); border:1px dashed rgba(255,255,255,0.1); margin-bottom:10px;'>
                <div style='font-family:DM Mono; font-size:9px; color:rgba(255,255,255,0.3); letter-spacing:1px;'>L NON CALCOLABILE</div>
                <div style='font-size:11px; color:rgba(255,255,255,0.25); margin-top:4px;'>Inserisci Miglior 300m e PB 400m per calcolo automatico</div>
            </div>
            """, unsafe_allow_html=True)

        # Radio con default auto-calcolato (override manuale sempre possibile)
        override_note = " *(pre-selezionato dal DB — modificabile)*" if SRI_db is not None else ""
        override_note_l = " *(pre-selezionato dal DB — modificabile)*" if L_db is not None else ""

        col_pr1, col_pr2 = st.columns(2)
        profilo_vel = col_pr1.radio(
            f"Profilo Velocità (offset T200 in gara){override_note}",
            options=["🟢 Efficiente/Naturale  (+1.0s)", "🟡 Intermedio  (+1.4s)", "🔴 Velocista Puro  (+1.8s)"],
            index=offset_default_idx,
            help="SRI < 1.065 → Efficiente; 1.065–1.080 → Intermedio; > 1.080 → Velocista Puro. Pre-selezionato automaticamente se hai PB 200m e 400m nel database."
        )
        resistenza_latt = col_pr2.radio(
            f"Resistenza Lattacida (L){override_note_l}",
            options=["🟢 Ottimo 400ista  (L = 12.0s)", "🟡 Buono  (L = 13.0s)", "🟠 Medio  (L = 14.0s)", "🔴 Carente  (L = 15.0s)"],
            index=l_default_idx,
            help="L = PB 400m − Miglior 300m. Pre-selezionato automaticamente se hai entrambi i tempi. Puoi modificarlo manualmente come override."
        )

        # Mostra nota override se DB e scelta manuale divergono
        if L_db is not None:
            l_options = ["🟢 Ottimo 400ista  (L = 12.0s)", "🟡 Buono  (L = 13.0s)", "🟠 Medio  (L = 14.0s)", "🔴 Carente  (L = 15.0s)"]
            if l_options.index(resistenza_latt) != l_default_idx:
                col_pr2.caption(f"⚠️ Stai usando L manuale invece del valore DB ({L_db:.2f}s)")
        if SRI_db is not None:
            sri_options = ["🟢 Efficiente/Naturale  (+1.0s)", "🟡 Intermedio  (+1.4s)", "🔴 Velocista Puro  (+1.8s)"]
            if sri_options.index(profilo_vel) != offset_default_idx:
                col_pr1.caption(f"⚠️ Stai usando profilo manuale invece del valore DB (SRI={SRI_db:.4f})")

        offset_map = {
            "🟢 Efficiente/Naturale  (+1.0s)": 1.0,
            "🟡 Intermedio  (+1.4s)": 1.4,
            "🔴 Velocista Puro  (+1.8s)": 1.8,
        }
        L_map = {
            "🟢 Ottimo 400ista  (L = 12.0s)": 12.0,
            "🟡 Buono  (L = 13.0s)": 13.0,
            "🟠 Medio  (L = 14.0s)": 14.0,
            "🔴 Carente  (L = 15.0s)": 15.0,
        }
        offset_val = offset_map[profilo_vel]
        L_val      = L_map[resistenza_latt]

        st.markdown("<br>", unsafe_allow_html=True)

        if t200pb and t200pb > 0 and t300 and t300 > 0:
            # Calcoli
            T200_gara    = t200pb + offset_val
            T400_da_300  = t300 + L_val
            T400_stimato = round(0.6 * T400_da_300 + 0.4 * (2 * T200_gara + 5.5), 2)
            C            = round(t300 - 1.5 * t200pb, 3)

            # Classificazione indice C
            if C < 1.5:
                c_emoji, c_label = "🟢", "Talento 400m Naturale"
                c_desc  = "Speed endurance eccellente. L'atleta converte molto bene la sua velocità di base. La caduta di velocità dopo i 200m è contenuta e ben gestita. Ideale per specializzarsi nel 400m."
                c_color, c_bg, c_border = "#00e676", "rgba(0,230,118,0.08)", "rgba(0,230,118,0.3)"
                c_action = "✅ Insisti sul lavoro di potenza e velocità. La tenuta c'è già. Lavora sulla forza specifica per migliorare i 200m PB."
            elif C <= 2.5:
                c_emoji, c_label = "🟡", "Buon 400ista"
                c_desc  = "Buona conversione velocità-resistenza. L'atleta gestisce bene la distribuzione dello sforzo nel corso dei 400m, con margini di miglioramento sulla componente lattacida."
                c_color, c_bg, c_border = "#ffeb3b", "rgba(255,235,59,0.08)", "rgba(255,235,59,0.3)"
                c_action = "📈 Lavora sulla resistenza lattacida (ripetute 200-300m ad alta intensità) e sul controllo di gara per ottimizzare la distribuzione del ritmo."
            elif C <= 3.5:
                c_emoji, c_label = "🟠", "Velocista Convertibile"
                c_desc  = "Buona velocità di base ma endurance media. L'atleta cala visibilmente dopo i 200m. Il potenziale c'è, ma va sviluppata la tenuta nella seconda metà gara."
                c_color, c_bg, c_border = "#ff9800", "rgba(255,152,0,0.08)", "rgba(255,152,0,0.3)"
                c_action = "⚡ Priorità al lavoro lattacido: ripetute 300-350m, tempo run e threshold. Punta a portare L da {:.0f} a {:.0f} nel medio termine.".format(L_val, max(12.0, L_val - 1.0))
            else:
                c_emoji, c_label = "🔴", "Limite Endurance"
                c_desc  = "Velocità di base buona ma forte calo nella seconda metà. Necessita di un piano di lavoro lattacido/aerobico intensivo per migliorare la tenuta sulle distanze superiori ai 200m."
                c_color, c_bg, c_border = "#f44336", "rgba(244,67,54,0.08)", "rgba(244,67,54,0.3)"
                c_action = "🔧 Inserisci lavoro aerobico di base (3-4 settimane), poi scala gradualmente verso il lattacido. Obiettivo immediato: abbassare i 300m per ridurre C sotto 3.5."

            st.markdown("<div style='font-family:DM Mono; font-size:10px; color:rgba(255,255,255,0.35); letter-spacing:2px; margin-bottom:12px;'>STEP 3 · RISULTATI</div>", unsafe_allow_html=True)

            # Indice C in grande
            st.markdown(f"""
            <div style='padding:22px; border-radius:14px; background:{c_bg}; border:1px solid {c_border}; margin-bottom:20px;'>
                <div style='display:flex; align-items:center; gap:24px; flex-wrap:wrap;'>
                    <div style='text-align:center; min-width:100px;'>
                        <div style='font-family:DM Mono; font-size:10px; color:rgba(255,255,255,0.4); letter-spacing:2px; margin-bottom:4px;'>INDICE C</div>
                        <div style='font-family:Bebas Neue; font-size:60px; color:{c_color}; line-height:1;'>{C:.2f}</div>
                        <div style='font-family:DM Mono; font-size:9px; color:rgba(255,255,255,0.25);'>T300 − 1.5 × T200pb</div>
                    </div>
                    <div style='flex:1; min-width:220px;'>
                        <div style='margin-bottom:8px;'>{c_emoji} <span style='font-family:Bebas Neue; font-size:26px; color:{c_color};'>{c_label}</span></div>
                        <div style='font-size:13px; color:rgba(255,255,255,0.65); line-height:1.6; margin-bottom:12px;'>{c_desc}</div>
                        <div style='font-size:12px; color:{c_color}; background:rgba(0,0,0,0.25); padding:8px 12px; border-radius:6px; border-left:3px solid {c_color};'>{c_action}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Step intermedi visibili
            st.markdown("<div style='font-family:DM Mono; font-size:10px; color:rgba(255,255,255,0.3); letter-spacing:2px; margin-bottom:10px;'>CALCOLO STEP-BY-STEP</div>", unsafe_allow_html=True)
            sc1, sc2, sc3 = st.columns(3)
            sc1.markdown(f"""
            <div style='padding:14px; border-radius:10px; border:1px solid rgba(255,255,255,0.07); background:rgba(255,255,255,0.02); text-align:center;'>
                <div style='font-family:DM Mono; font-size:9px; color:rgba(255,255,255,0.35); letter-spacing:1px; margin-bottom:6px;'>STEP 1 · T200 GARA</div>
                <div style='font-family:Bebas Neue; font-size:32px; color:#fff;'>{T200_gara:.2f}s</div>
                <div style='font-size:11px; color:rgba(255,255,255,0.35); margin-top:4px;'>{t200pb:.2f} + {offset_val:.1f}s offset</div>
            </div>
            """, unsafe_allow_html=True)
            sc2.markdown(f"""
            <div style='padding:14px; border-radius:10px; border:1px solid rgba(255,255,255,0.07); background:rgba(255,255,255,0.02); text-align:center;'>
                <div style='font-family:DM Mono; font-size:9px; color:rgba(255,255,255,0.35); letter-spacing:1px; margin-bottom:6px;'>STEP 2 · STIMA DA 300m</div>
                <div style='font-family:Bebas Neue; font-size:32px; color:#fff;'>{T400_da_300:.2f}s</div>
                <div style='font-size:11px; color:rgba(255,255,255,0.35); margin-top:4px;'>{t300:.2f} + L={L_val:.0f}s</div>
            </div>
            """, unsafe_allow_html=True)
            sc3.markdown(f"""
            <div style='padding:14px; border-radius:10px; border:1px solid rgba(74,158,255,0.3); background:rgba(74,158,255,0.06); text-align:center;'>
                <div style='font-family:DM Mono; font-size:9px; color:#4A9EFF; letter-spacing:1px; margin-bottom:6px;'>STEP 3 · FUSION MODEL</div>
                <div style='font-family:Bebas Neue; font-size:38px; color:#4A9EFF;'>{T400_stimato:.2f}s</div>
                <div style='font-size:11px; color:rgba(74,158,255,0.6); margin-top:4px;'>60% × step2 + 40% × (2×step1 + 5.5)</div>
            </div>
            """, unsafe_allow_html=True)

            # ── Grafici analitici 400m ──────────────────────────────────────────
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("<div style='font-family:DM Mono; font-size:10px; color:rgba(255,255,255,0.3); letter-spacing:2px; margin-bottom:10px;'>ANALISI GRAFICA</div>", unsafe_allow_html=True)
            g400_col1, g400_col2 = st.columns(2)

            # Gauge Indice C (HTML)
            _c_clamped = min(4.99, max(0.0, C))
            _c_pct = (_c_clamped / 5.0) * 100
            g400_col1.markdown(f"""
            <div style='padding:14px 18px; border-radius:10px; background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.07);'>
                <div style='font-family:DM Mono; font-size:9px; color:rgba(255,255,255,0.35); letter-spacing:2px; margin-bottom:12px;'>INDICE C · SCALA 0–5</div>
                <div style='position:relative; height:14px; border-radius:7px; background:linear-gradient(to right, #00e676 0%, #00e676 30%, #ffeb3b 30%, #ffeb3b 50%, #ff9800 50%, #ff9800 70%, #f44336 70%, #f44336 100%); margin-bottom:8px;'>
                    <div style='position:absolute; top:50%; left:{_c_pct:.1f}%; transform:translate(-50%,-50%); width:20px; height:20px; border-radius:50%; background:#1a1c22; border:3px solid {c_color}; box-shadow:0 0 10px {c_color};'></div>
                </div>
                <div style='display:flex; justify-content:space-between; font-family:DM Mono; font-size:9px; color:rgba(255,255,255,0.25); margin-bottom:10px;'>
                    <span>0</span><span>1.5</span><span>2.5</span><span>3.5</span><span>5.0</span>
                </div>
                <div style='display:flex; gap:6px; flex-wrap:wrap; margin-bottom:10px;'>
                    <span style='font-size:10px; padding:2px 8px; border-radius:10px; background:rgba(0,230,118,0.12); color:#00e676;'>Talento</span>
                    <span style='font-size:10px; padding:2px 8px; border-radius:10px; background:rgba(255,235,59,0.12); color:#ffeb3b;'>Buono</span>
                    <span style='font-size:10px; padding:2px 8px; border-radius:10px; background:rgba(255,152,0,0.12); color:#ff9800;'>Convertibile</span>
                    <span style='font-size:10px; padding:2px 8px; border-radius:10px; background:rgba(244,67,54,0.12); color:#f44336;'>Limite</span>
                </div>
                <div style='font-family:Bebas Neue; font-size:28px; color:{c_color};'>C = {C:.2f} · {c_label}</div>
            </div>
            """, unsafe_allow_html=True)

            # Decomposizione componenti T400
            _comp_res  = round(0.6 * T400_da_300, 2)
            _comp_vel  = round(0.4 * (2 * T200_gara + 5.5), 2)
            fig_comp400 = go.Figure()
            fig_comp400.add_trace(go.Bar(
                name=f"Resistenza/300m (60%) = {_comp_res:.2f}s",
                x=[_comp_res], y=["T400"], orientation='h',
                marker_color="#4A9EFF",
                text=f"{_comp_res:.2f}s", textposition='inside', insidetextanchor='middle',
                textfont=dict(size=11, color='white'),
            ))
            fig_comp400.add_trace(go.Bar(
                name=f"Velocità/200m (40%) = {_comp_vel:.2f}s",
                x=[_comp_vel], y=["T400"], orientation='h',
                marker_color="#00e676",
                text=f"{_comp_vel:.2f}s", textposition='inside', insidetextanchor='middle',
                textfont=dict(size=11, color='rgba(0,0,0,0.75)'),
            ))
            fig_comp400.update_layout(
                barmode='stack', height=200,
                margin=dict(l=10, r=20, t=45, b=40),
                template=THEME_TEMPLATE,
                title=dict(text=f"COMPONENTI T400 = {T400_stimato:.2f}s", font=dict(family="DM Mono", size=10, color="rgba(255,255,255,0.4)")),
                legend=dict(orientation="h", y=-0.45, xanchor="center", x=0.5, font=dict(size=9, color="rgba(255,255,255,0.5)")),
                xaxis=dict(title="Secondi", tickfont=dict(size=10)),
                yaxis=dict(visible=False),
            )
            g400_col2.plotly_chart(fig_comp400, use_container_width=True)

            # What-if scenari
            _T400_wi_t200 = round(0.6 * T400_da_300 + 0.4 * (2 * (t200pb - 0.2 + offset_val) + 5.5), 2)
            _L_improved   = max(12.0, L_val - 1.0)
            _T400_wi_L    = round(0.6 * (t300 + _L_improved) + 0.4 * (2 * T200_gara + 5.5), 2)
            _T400_wi_both = round(0.6 * (t300 + _L_improved) + 0.4 * (2 * (t200pb - 0.2 + offset_val) + 5.5), 2)
            _wi_labels    = ["Attuale", "T200 -0.2s", f"L -1s ({_L_improved:.0f}s)", "Entrambi"]
            _wi_vals      = [T400_stimato, _T400_wi_t200, _T400_wi_L, _T400_wi_both]
            _wi_gains     = [0.0] + [round(T400_stimato - v, 2) for v in _wi_vals[1:]]
            _wi_colors    = ["#4A9EFF", "#ff9800", "#ffeb3b", "#00e676"]
            _wi_texts     = [
                f"{T400_stimato:.2f}s" if g == 0 else f"{v:.2f}s  (-{g:.2f}s)"
                for v, g in zip(_wi_vals, _wi_gains)
            ]
            fig_wi400 = go.Figure(go.Bar(
                x=_wi_labels, y=_wi_vals,
                marker_color=_wi_colors,
                text=_wi_texts,
                textposition='outside',
                textfont=dict(size=11, color="rgba(255,255,255,0.8)"),
                cliponaxis=False,
            ))
            fig_wi400.update_layout(
                height=260,
                template=THEME_TEMPLATE,
                title=dict(text="SCENARI WHAT-IF: IMPATTO DEI MIGLIORAMENTI", font=dict(family="DM Mono", size=10, color="rgba(255,255,255,0.4)")),
                yaxis=dict(
                    range=[min(_wi_vals) - 0.8, max(_wi_vals) + 0.6],
                    title="T400 stimato (s)", tickfont=dict(size=10), autorange=False,
                ),
                margin=dict(l=30, r=20, t=40, b=10),
                showlegend=False,
            )
            st.plotly_chart(fig_wi400, use_container_width=True)

            # Margine di miglioramento
            if t400_reale and t400_reale > 0:
                st.markdown("<br>", unsafe_allow_html=True)
                margine = round(t400_reale - T400_stimato, 2)
                if margine > 0:
                    mar_color, mar_bg, mar_bord = "#ff9800", "rgba(255,152,0,0.07)", "rgba(255,152,0,0.25)"
                    mar_icon = "📈"
                    mar_titolo = "MARGINE DI MIGLIORAMENTO"
                    mar_txt = f"L'atleta corre {margine:.2f}s più lento del potenziale teorico ({T400_stimato:.2f}s). Può ancora avvicinarsi a questo tempo ottimizzando la gestione di gara e la resistenza lattacida."
                else:
                    mar_color, mar_bg, mar_bord = "#00e676", "rgba(0,230,118,0.07)", "rgba(0,230,118,0.25)"
                    mar_icon = "✅"
                    mar_titolo = "POTENZIALE GIÀ ESPRESSO"
                    mar_txt = f"L'atleta corre {abs(margine):.2f}s sotto la stima teorica. Sta sfruttando al massimo (o oltre) il suo potenziale attuale. Per migliorare, è necessario sviluppare le qualità di base (velocità o resistenza)."
                st.markdown(f"""
                <div style='padding:16px 20px; border-radius:10px; background:{mar_bg}; border:1px solid {mar_bord};'>
                    <div style='font-family:DM Mono; font-size:10px; color:{mar_color}; letter-spacing:2px; margin-bottom:8px;'>{mar_icon} {mar_titolo}</div>
                    <div style='display:flex; align-items:baseline; gap:12px; margin-bottom:6px;'>
                        <span style='font-family:Bebas Neue; font-size:42px; color:{mar_color}; line-height:1;'>{("+" if margine > 0 else "")}{margine:.2f}s</span>
                        <span style='font-size:12px; color:rgba(255,255,255,0.4);'>PB attuale: {t400_reale:.2f}s · Potenziale stimato: {T400_stimato:.2f}s</span>
                    </div>
                    <div style='font-size:13px; color:rgba(255,255,255,0.6);'>{mar_txt}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style='padding:20px; border-radius:12px; border:1px dashed rgba(74,158,255,0.3); background:rgba(74,158,255,0.03); text-align:center;'>
                <div style='font-size:28px; margin-bottom:8px;'>⬆️</div>
                <div style='font-family:DM Mono; font-size:11px; color:rgba(74,158,255,0.7); letter-spacing:1px;'>Inserisci PB 200m e Miglior 300m per avviare la stima</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.divider()
        st.markdown("<br>", unsafe_allow_html=True)

        # ══════════════════════════════════════════════════════════════════
        # SEZIONE 3 — MODELLO FISIOLOGICO 200m
        # ══════════════════════════════════════════════════════════════════
        st.markdown("""
        <div style='display:flex; align-items:center; gap:14px; margin-bottom:6px;'>
            <div style='width:4px; height:36px; background:#bf5fff; border-radius:2px;'></div>
            <div>
                <div style='font-family:Bebas Neue; font-size:26px; color:#bf5fff; letter-spacing:1px; line-height:1;'>MODELLO FISIOLOGICO 200m</div>
                <div style='font-family:DM Mono; font-size:10px; color:rgba(255,255,255,0.4); letter-spacing:2px;'>100m PB → STIMA POTENZIALE 200m · SPEED RESERVE INDEX</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<p style='font-size:13px; color:rgba(255,255,255,0.55); margin-bottom:4px;'>Stima il potenziale sui 200m a partire dal PB sui 100m e dal profilo di velocità di riserva (SR200). SR200 misura quanto l'atleta paga rispetto a un doppio 100m ideale: distingue il velocista puro dal 200m specialist.</p>", unsafe_allow_html=True)

        with st.expander("📖 Come usare questo modello", expanded=False):
            st.markdown("""
**SR200 = T200 / (2 × T100)**

Misura la perdita di velocità accumulata nella curva e nella seconda metà gara. Valori di riferimento:

| SR200 | Profilo | Cosa significa |
|-------|---------|----------------|
| < 1.07 | Velocista Puro | 200m quasi doppio 100m. Vmax altissima, meno speed endurance |
| 1.07 – 1.10 | 200m Specialist | Equilibrio ottimale. Profilo più competitivo |
| > 1.10 | Speed Endurance | Tiene bene nel retto finale, ma meno Vmax di partenza |

**Come usare la predizione:**
- Se hai solo il PB 100m → scegli il profilo SR200 target per stimare il potenziale
- Se hai sia T100 che T200 → il modello calcola SR200 reale dal DB e pre-seleziona il profilo automaticamente
- Puoi sempre cambiare la selezione per vedere scenari "what if" (es: cosa succederebbe se migliorassi SR200 da 1.09 a 1.07?)

**Nota sul 60m come alternativo:** se non hai T100, il modello stima T100 ≈ 1.575 × T60 + 0.18 (formula Vittori). Meno preciso ma utile come approssimazione.
            """)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<div style='font-family:DM Mono; font-size:10px; color:rgba(255,255,255,0.35); letter-spacing:2px; margin-bottom:8px;'>STEP 1 · INSERISCI I TEMPI</div>", unsafe_allow_html=True)

        m200_col1, m200_col2, m200_col3 = st.columns(3)
        m200_t100 = m200_col1.number_input(
            "🏃 PB 100m (s)",
            value=pb_100, step=0.01, format="%.2f",
            placeholder="es. 10.85",
            help="Personal Best sui 100m. Pre-compilato dal database se disponibile."
        )
        m200_t200_reale = m200_col2.number_input(
            "🏁 PB 200m attuale (s) — opzionale",
            value=pb_200_auto, step=0.05, format="%.2f",
            placeholder="es. 21.80",
            help="Se inserito: calcola SR200 automaticamente e il margine di miglioramento."
        )
        m200_t60 = m200_col3.number_input(
            "⚡ PB 60m (s) — alternativo al 100m",
            value=pb_60, step=0.01, format="%.2f",
            placeholder="es. 6.85",
            help="Usato se T100 non disponibile. T100_stim ≈ 1.575 × T60 + 0.18 (Vittori)."
        )

        # ── Auto-calibrazione SR200 ─────────────────────────────────────────
        _m200_t100_eff = m200_t100 if (m200_t100 and m200_t100 > 0) else (
            round(1.575 * m200_t60 + 0.18, 2) if (m200_t60 and m200_t60 > 0) else None
        )
        _m200_t100_src = "DB" if (m200_t100 and m200_t100 > 0) else (
            f"stim. da T60={m200_t60:.2f}s" if (m200_t60 and m200_t60 > 0) else "—"
        )
        _m200_t200_cal  = m200_t200_reale if (m200_t200_reale and m200_t200_reale > 0) else None

        SR200_db_200m = round(_m200_t200_cal / (2 * _m200_t100_eff), 4) \
            if (_m200_t200_cal and _m200_t100_eff) else None

        def _sr200_to_idx(sr):
            if sr is None: return 1
            if sr < 1.07:  return 0
            if sr <= 1.10: return 1
            return 2

        sr200_default_idx = _sr200_to_idx(SR200_db_200m)

        # ── Step 2 – Profila ───────────────────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<div style='font-family:DM Mono; font-size:10px; color:rgba(255,255,255,0.35); letter-spacing:2px; margin-bottom:10px;'>STEP 2 · PROFILA L'ATLETA</div>", unsafe_allow_html=True)

        m200_badge_col, m200_radio_col = st.columns([1, 1])

        # Badge SR200 da DB
        _sr200_lbl_list   = ["Velocista Puro", "200m Specialist", "Speed Endurance"]
        _sr200_color_list = ["#ff9800", "#bf5fff", "#4A9EFF"]
        if SR200_db_200m is not None:
            _db_idx = _sr200_to_idx(SR200_db_200m)
            m200_badge_col.markdown(f"""
            <div style='padding:12px 16px; border-radius:10px; background:rgba(191,95,255,0.06); border:1px solid rgba(191,95,255,0.25); margin-bottom:10px;'>
                <div style='font-family:DM Mono; font-size:9px; color:rgba(255,255,255,0.4); letter-spacing:1px; margin-bottom:4px;'>📊 SR200 CALCOLATO DAL DB</div>
                <span style='font-family:Bebas Neue; font-size:28px; color:{_sr200_color_list[_db_idx]};'>{SR200_db_200m:.4f}</span>
                <span style='font-size:12px; color:rgba(255,255,255,0.5); margin-left:8px;'>→ {_sr200_lbl_list[_db_idx]}</span>
                <div style='font-size:11px; color:rgba(255,255,255,0.3); margin-top:3px;'>T200 / (2 × T100) = {_m200_t200_cal:.2f} / (2 × {_m200_t100_eff:.2f})</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            m200_badge_col.markdown("""
            <div style='padding:12px 16px; border-radius:10px; background:rgba(255,255,255,0.03); border:1px dashed rgba(255,255,255,0.1); margin-bottom:10px;'>
                <div style='font-family:DM Mono; font-size:9px; color:rgba(255,255,255,0.3); letter-spacing:1px;'>SR200 NON CALCOLABILE</div>
                <div style='font-size:11px; color:rgba(255,255,255,0.25); margin-top:4px;'>Inserisci PB 100m e PB 200m per il calcolo automatico</div>
            </div>
            """, unsafe_allow_html=True)

        _sr200_override_note = " *(pre-selezionato dal DB — modificabile)*" if SR200_db_200m else ""
        sr200_profilo = m200_radio_col.radio(
            f"Profilo SR200{_sr200_override_note}",
            options=["🟠 Velocista Puro  (SR200 ≈ 1.06)", "🟣 200m Specialist  (SR200 ≈ 1.08)", "🔵 Speed Endurance  (SR200 ≈ 1.10)"],
            index=sr200_default_idx,
            help="SR200 < 1.07 → Velocista Puro; 1.07-1.10 → 200m Specialist; >1.10 → Speed Endurance. "
                 "Cambia il profilo per simulare scenari 'what if'."
        )
        _sr200_opts = ["🟠 Velocista Puro  (SR200 ≈ 1.06)", "🟣 200m Specialist  (SR200 ≈ 1.08)", "🔵 Speed Endurance  (SR200 ≈ 1.10)"]
        if SR200_db_200m and _sr200_opts.index(sr200_profilo) != sr200_default_idx:
            m200_radio_col.caption(f"⚠️ Override manuale attivo — SR200 reale dal DB: {SR200_db_200m:.4f}")

        _sr200_val_map = {
            "🟠 Velocista Puro  (SR200 ≈ 1.06)": 1.06,
            "🟣 200m Specialist  (SR200 ≈ 1.08)": 1.08,
            "🔵 Speed Endurance  (SR200 ≈ 1.10)": 1.10,
        }
        sr200_chosen_val = _sr200_val_map[sr200_profilo]
        # Usa sempre il valore del profilo teorico selezionato per poter calcolare un margine reale
        sr200_for_pred = sr200_chosen_val

        st.markdown("<br>", unsafe_allow_html=True)

        if _m200_t100_eff and _m200_t100_eff > 0:
            T200_pred = round(2 * _m200_t100_eff * sr200_for_pred, 2)

            _si = _sr200_to_idx(sr200_for_pred)
            _sr200_colors  = ["#ff9800", "#bf5fff", "#4A9EFF"]
            _sr200_bgs     = ["rgba(255,152,0,0.08)", "rgba(191,95,255,0.08)", "rgba(74,158,255,0.08)"]
            _sr200_borders = ["rgba(255,152,0,0.3)", "rgba(191,95,255,0.3)", "rgba(74,158,255,0.3)"]
            _sr200_desc    = [
                "Velocità massima altissima, ma la seconda parte del 200m è esigente. L'atleta vive di Vmax e fatica nel mantenimento lungo il rettilineo finale. Il 100m è la specialità più naturale.",
                "Eccellente equilibrio tra velocità di base e resistenza sulla curva + rettilineo. È il profilo tipico del 200m specialist competitivo. Margini di miglioramento su entrambe le componenti.",
                "Tiene bene nel retto finale e gestisce bene la curva, ma la velocità di partenza è meno esplosiva. Può trarre vantaggio da gare tattiche ed è spesso più competitivo anche sui 400m.",
            ][_si]
            _sr200_action  = [
                "⚡ Lavora su accelerazione e Vmax (sprint lanciati 30–60m, lavoro neuromuscolare). La speed endurance sul 200m si sviluppa con ripetute 150m ad altissima intensità.",
                "📈 Profilo ideale. Mantieni l'equilibrio tra lavoro di velocità pura (60–80m) e ripetute di speed endurance (150–200m). Cura la tecnica di curva per guadagnare 0.05–0.10s.",
                "🔵 Punta a migliorare la velocità di base (lavoro neuromuscolare, forza esplosiva, sprint brevi). Abbassare il T100 sposta il profilo verso 200m Specialist.",
            ][_si]

            st.markdown("<div style='font-family:DM Mono; font-size:10px; color:rgba(255,255,255,0.35); letter-spacing:2px; margin-bottom:12px;'>STEP 3 · RISULTATI</div>", unsafe_allow_html=True)

            # SR200 in grande
            _sr200_disp = SR200_db_200m if SR200_db_200m else sr200_chosen_val
            st.markdown(f"""
            <div style='padding:22px; border-radius:14px; background:{_sr200_bgs[_si]}; border:1px solid {_sr200_borders[_si]}; margin-bottom:20px;'>
                <div style='display:flex; align-items:center; gap:24px; flex-wrap:wrap;'>
                    <div style='text-align:center; min-width:110px;'>
                        <div style='font-family:DM Mono; font-size:10px; color:rgba(255,255,255,0.4); letter-spacing:2px; margin-bottom:4px;'>SR200</div>
                        <div style='font-family:Bebas Neue; font-size:60px; color:{_sr200_colors[_si]}; line-height:1;'>{_sr200_disp:.4f}</div>
                        <div style='font-family:DM Mono; font-size:9px; color:rgba(255,255,255,0.25);'>T200 / (2 × T100)</div>
                    </div>
                    <div style='flex:1; min-width:220px;'>
                        <div style='margin-bottom:8px;'><span style='font-family:Bebas Neue; font-size:26px; color:{_sr200_colors[_si]};'>{_sr200_lbl_list[_si]}</span></div>
                        <div style='font-size:13px; color:rgba(255,255,255,0.65); line-height:1.6; margin-bottom:12px;'>{_sr200_desc}</div>
                        <div style='font-size:12px; color:{_sr200_colors[_si]}; background:rgba(0,0,0,0.25); padding:8px 12px; border-radius:6px; border-left:3px solid {_sr200_colors[_si]};'>{_sr200_action}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Step intermedi
            st.markdown("<div style='font-family:DM Mono; font-size:10px; color:rgba(255,255,255,0.3); letter-spacing:2px; margin-bottom:10px;'>CALCOLO STEP-BY-STEP</div>", unsafe_allow_html=True)
            s200c1, s200c2, s200c3 = st.columns(3)
            s200c1.markdown(f"""
            <div style='padding:14px; border-radius:10px; border:1px solid rgba(255,255,255,0.07); background:rgba(255,255,255,0.02); text-align:center;'>
                <div style='font-family:DM Mono; font-size:9px; color:rgba(255,255,255,0.35); letter-spacing:1px; margin-bottom:6px;'>T100 BASE</div>
                <div style='font-family:Bebas Neue; font-size:32px; color:#fff;'>{_m200_t100_eff:.2f}s</div>
                <div style='font-size:11px; color:rgba(255,255,255,0.35); margin-top:4px;'>fonte: {_m200_t100_src}</div>
            </div>
            """, unsafe_allow_html=True)
            s200c2.markdown(f"""
            <div style='padding:14px; border-radius:10px; border:1px solid rgba(255,255,255,0.07); background:rgba(255,255,255,0.02); text-align:center;'>
                <div style='font-family:DM Mono; font-size:9px; color:rgba(255,255,255,0.35); letter-spacing:1px; margin-bottom:6px;'>SR200 APPLICATO</div>
                <div style='font-family:Bebas Neue; font-size:32px; color:#fff;'>× {sr200_for_pred:.4f}</div>
                <div style='font-size:11px; color:rgba(255,255,255,0.35); margin-top:4px;'>{"consigliato dal DB" if (SR200_db_200m and _sr200_opts.index(sr200_profilo) == sr200_default_idx) else "override manuale"}</div>
            </div>
            """, unsafe_allow_html=True)
            s200c3.markdown(f"""
            <div style='padding:14px; border-radius:10px; border:1px solid {_sr200_borders[_si]}; background:{_sr200_bgs[_si]}; text-align:center;'>
                <div style='font-family:DM Mono; font-size:9px; color:{_sr200_colors[_si]}; letter-spacing:1px; margin-bottom:6px;'>200m POTENZIALE</div>
                <div style='font-family:Bebas Neue; font-size:38px; color:{_sr200_colors[_si]};'>{T200_pred:.2f}s</div>
                <div style='font-size:11px; color:rgba(255,255,255,0.35); margin-top:4px;'>2 × {_m200_t100_eff:.2f} × {sr200_for_pred:.4f}</div>
            </div>
            """, unsafe_allow_html=True)

            # What-if: simula scenario con profilo ottimizzato
            if SR200_db_200m and _sr200_to_idx(SR200_db_200m) > 0:
                better_sr = [1.06, 1.06, 1.08][_si]
                t200_whatif = round(2 * _m200_t100_eff * better_sr, 2)
                delta_whatif = round(T200_pred - t200_whatif, 2)
                st.markdown(f"""
                <div style='margin-top:12px; padding:10px 16px; border-radius:8px; background:rgba(255,255,255,0.03); border:1px dashed rgba(255,255,255,0.12);'>
                    <span style='font-family:DM Mono; font-size:9px; color:rgba(255,255,255,0.35); letter-spacing:1px;'>💡 WHAT IF — </span>
                    <span style='font-size:12px; color:rgba(255,255,255,0.5);'>Se l'atleta migliorasse il profilo a SR200={better_sr:.2f}: potrebbe correre <strong style='color:#fff;'>{t200_whatif:.2f}s</strong> (−{delta_whatif:.2f}s rispetto alla stima attuale)</span>
                </div>
                """, unsafe_allow_html=True)

            # ── Grafici analitici 200m ──────────────────────────────────────────
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("<div style='font-family:DM Mono; font-size:10px; color:rgba(255,255,255,0.3); letter-spacing:2px; margin-bottom:10px;'>ANALISI GRAFICA</div>", unsafe_allow_html=True)
            g200_col1, g200_col2 = st.columns([3, 2])

            # Curva T200 = 2 x T100 x SR200 per i tre profili
            _t100_range = [x / 100.0 for x in range(880, 1260, 5)]
            _sr200_curve_profiles = [
                ("Velocista Puro (1.06)", 1.06, "#ff9800"),
                ("200m Specialist (1.08)", 1.08, "#bf5fff"),
                ("Speed Endurance (1.10)", 1.10, "#4A9EFF"),
            ]
            fig_sr200_curve = go.Figure()
            for _c_lbl, _c_sr, _c_col in _sr200_curve_profiles:
                _c_y = [round(2 * x * _c_sr, 2) for x in _t100_range]
                fig_sr200_curve.add_trace(go.Scatter(
                    x=_t100_range, y=_c_y, mode='lines', name=_c_lbl,
                    line=dict(color=_c_col, width=2),
                ))
            fig_sr200_curve.add_trace(go.Scatter(
                x=[_m200_t100_eff], y=[T200_pred],
                mode='markers+text', name="Stima atleta",
                marker=dict(size=13, color="#bf5fff", symbol="diamond",
                            line=dict(width=2, color="#fff")),
                text=[f"  {T200_pred:.2f}s"], textposition="middle right",
                textfont=dict(size=11, color="#bf5fff"),
            ))
            if _m200_t200_cal:
                fig_sr200_curve.add_trace(go.Scatter(
                    x=[_m200_t100_eff], y=[_m200_t200_cal],
                    mode='markers+text', name="PB attuale",
                    marker=dict(size=12, color="#00e676", symbol="circle",
                                line=dict(width=2, color="#fff")),
                    text=[f"  {_m200_t200_cal:.2f}s"], textposition="middle right",
                    textfont=dict(size=11, color="#00e676"),
                ))
            fig_sr200_curve.update_layout(
                height=330,
                template=THEME_TEMPLATE,
                title=dict(text="CURVA T200 = 2 x T100 x SR200", font=dict(family="DM Mono", size=10, color="rgba(255,255,255,0.4)")),
                xaxis=dict(title="T100 (s)", tickfont=dict(size=10)),
                yaxis=dict(title="T200 (s)", tickfont=dict(size=10)),
                legend=dict(orientation="h", y=-0.25, xanchor="center", x=0.5, font=dict(size=9, color="rgba(255,255,255,0.5)")),
                margin=dict(l=30, r=20, t=45, b=45),
            )
            g200_col1.plotly_chart(fig_sr200_curve, use_container_width=True)

            # Confronto scenari SR200 (barre)
            _scen_labels = ["Velocista Puro", "200m Specialist", "Speed Endurance"]
            _scen_vals   = [round(2 * _m200_t100_eff * 1.06, 2),
                            round(2 * _m200_t100_eff * 1.08, 2),
                            round(2 * _m200_t100_eff * 1.10, 2)]
            _scen_colors = ["#ff9800", "#bf5fff", "#4A9EFF"]
            fig_scen200  = go.Figure(go.Bar(
                x=_scen_labels, y=_scen_vals,
                marker_color=_scen_colors,
                text=[f"{v:.2f}s" for v in _scen_vals],
                textposition='outside',
                textfont=dict(size=11, color="rgba(255,255,255,0.8)"),
                cliponaxis=False,
            ))
            if _m200_t200_cal:
                fig_scen200.add_hline(
                    y=_m200_t200_cal, line_dash="dash", line_color="#00e676", line_width=1.5,
                    annotation_text=f"PB {_m200_t200_cal:.2f}s",
                    annotation_position="top right",
                    annotation_font=dict(color="#00e676", size=10),
                )
            fig_scen200.update_layout(
                height=290,
                template=THEME_TEMPLATE,
                title=dict(text="SCENARI PROFILO SR200", font=dict(family="DM Mono", size=10, color="rgba(255,255,255,0.4)")),
                yaxis=dict(
                    range=[min(_scen_vals) - 0.6, max(_scen_vals) + 0.5],
                    title="T200 (s)", tickfont=dict(size=10), autorange=False,
                ),
                margin=dict(l=30, r=20, t=40, b=10),
                showlegend=False,
            )
            g200_col2.plotly_chart(fig_scen200, use_container_width=True)

            # Margine di miglioramento
            if _m200_t200_cal and _m200_t200_cal > 0:
                st.markdown("<br>", unsafe_allow_html=True)
                margine_200 = round(_m200_t200_cal - T200_pred, 2)
                if margine_200 > 0.01:
                    m2_color, m2_bg, m2_bord = "#ff9800", "rgba(255,152,0,0.07)", "rgba(255,152,0,0.25)"
                    m2_icon, m2_titolo = "📈", "MARGINE DI MIGLIORAMENTO"
                    m2_txt = (f"L'atleta corre {margine_200:.2f}s più lento della stima per il suo profilo attuale ({T200_pred:.2f}s con SR200={sr200_for_pred:.4f}). "
                              f"Lavorare su tecnica di curva, accelerazione iniziale e distribuzione del ritmo può colmare questo gap.")
                elif margine_200 < -0.01:
                    m2_color, m2_bg, m2_bord = "#00e676", "rgba(0,230,118,0.07)", "rgba(0,230,118,0.25)"
                    m2_icon, m2_titolo = "✅", "POTENZIALE SUPERATO"
                    m2_txt = (f"L'atleta corre {abs(margine_200):.2f}s sotto la stima del profilo ({T200_pred:.2f}s). "
                              f"Per continuare a migliorare occorre sviluppare le qualità di base: abbassare T100 o ottimizzare ulteriormente il SR200.")
                else:
                    m2_color, m2_bg, m2_bord = "#bf5fff", "rgba(191,95,255,0.07)", "rgba(191,95,255,0.25)"
                    m2_icon, m2_titolo = "⚖️", "ALLINEATO AL PROFILO"
                    m2_txt = "L'atleta sta correndo esattamente in linea con il profilo SR200 attuale. Ottima coerenza tra velocità di base e tenuta sulla distanza."
                st.markdown(f"""
                <div style='padding:16px 20px; border-radius:10px; background:{m2_bg}; border:1px solid {m2_bord};'>
                    <div style='font-family:DM Mono; font-size:10px; color:{m2_color}; letter-spacing:2px; margin-bottom:8px;'>{m2_icon} {m2_titolo}</div>
                    <div style='display:flex; align-items:baseline; gap:12px; margin-bottom:6px;'>
                        <span style='font-family:Bebas Neue; font-size:42px; color:{m2_color}; line-height:1;'>{("+" if margine_200 > 0 else "")}{margine_200:.2f}s</span>
                        <span style='font-size:12px; color:rgba(255,255,255,0.4);'>PB attuale: {_m200_t200_cal:.2f}s · Stima profilo: {T200_pred:.2f}s</span>
                    </div>
                    <div style='font-size:13px; color:rgba(255,255,255,0.6);'>{m2_txt}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style='padding:20px; border-radius:12px; border:1px dashed rgba(191,95,255,0.3); background:rgba(191,95,255,0.03); text-align:center;'>
                <div style='font-size:28px; margin-bottom:8px;'>⬆️</div>
                <div style='font-family:DM Mono; font-size:11px; color:rgba(191,95,255,0.7); letter-spacing:1px;'>Inserisci PB 100m (o PB 60m come alternativa) per avviare la stima</div>
            </div>
            """, unsafe_allow_html=True)

        # ── Roadmap 100m ────────────────────────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div style='padding:14px 18px; border-radius:10px; background:rgba(255,255,255,0.025); border:1px dashed rgba(255,255,255,0.1);'>
            <span style='font-family:DM Mono; font-size:10px; color:rgba(255,255,255,0.35); letter-spacing:2px;'>🔜 PROSSIMAMENTE · MODELLO 100m</span>
            <div style='font-size:12px; color:rgba(255,255,255,0.3); margin-top:6px;'>Userà i tempi gara ufficiali (da "Storico Gare") come fonte primaria + T60 dal database. Calcolerà Indice di Accelerazione, Vmax stimata dal flying 30m e profilo di fase (Acceleratore / Max Velocity / Bilanciato). Gli 80m da allenamento restano dato supplementare opzionale.</div>
        </div>
        """, unsafe_allow_html=True)

        # ──────────────────────────────────────────────────────────────────
        # SEZIONE 4 — MODELLO LINEARE ML (dati storici squadra) — in fondo
        # ──────────────────────────────────────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        st.divider()
        st.markdown("""
        <div style='display:flex; align-items:center; gap:14px; margin-bottom:6px;'>
            <div style='width:4px; height:36px; background:rgba(255,255,255,0.25); border-radius:2px;'></div>
            <div>
                <div style='font-family:Bebas Neue; font-size:26px; color:rgba(255,255,255,0.55); letter-spacing:1px; line-height:1;'>MODELLO LINEARE DI PREDIZIONE</div>
                <div style='font-family:DM Mono; font-size:10px; color:rgba(255,255,255,0.3); letter-spacing:2px;'>REGRESSIONE SUI DATI STORICI SQUADRA · SPERIMENTALE</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<p style='font-size:13px; color:rgba(255,255,255,0.4); margin-bottom:12px;'>Usa la regressione lineare sui dati storici della squadra per predire un tempo gara a partire da due distanze più corte. Modello esplorativo — i risultati dipendono fortemente dalla quantità di dati disponibili.</p>", unsafe_allow_html=True)

        with st.expander("📊 Apri Modello Lineare (dati storici squadra)", expanded=False):
            available_dists = sorted(df_running['Distanza'].unique())
            short_dists = [d for d in available_dists if d <= 100]
            long_dists  = [d for d in available_dists if d >= 60]
            if len(short_dists) >= 2 and len(long_dists) >= 1:
                col_p1, col_p2, col_p3 = st.columns(3)
                feat1  = col_p1.selectbox("Parziale 1", short_dists, index=0, format_func=lambda x: f"{int(x)}m")
                feat2  = col_p2.selectbox("Parziale 2", [d for d in short_dists if d != feat1], index=0, format_func=lambda x: f"{int(x)}m")
                target = col_p3.selectbox("Target Gara", [d for d in long_dists if d > max(feat1, feat2)], format_func=lambda x: f"{int(x)}m")
                df_f1   = df_running[df_running['Distanza'] == feat1][['Data', 'Atleta', 'Tempo']].rename(columns={'Tempo': 't1'})
                df_f2   = df_running[df_running['Distanza'] == feat2][['Data', 'Atleta', 'Tempo']].rename(columns={'Tempo': 't2'})
                df_tgt  = df_running[df_running['Distanza'] == target][['Data', 'Atleta', 'Tempo']].rename(columns={'Tempo': 'target'})
                df_model = df_f1.merge(df_f2, on=['Data', 'Atleta']).merge(df_tgt, on=['Data', 'Atleta'])
                if len(df_model) >= 5:
                    from sklearn.linear_model import LinearRegression  # lazy import: libreria pesante usata solo qui
                    X, y = df_model[['t1', 't2']].values, df_model['target'].values
                    model_lr = LinearRegression().fit(X, y)
                    score = model_lr.score(X, y)
                    df_model['Previsto'] = model_lr.predict(X)
                    fig_pred = px.scatter(df_model, x='target', y='Previsto', template=THEME_TEMPLATE, title=f"Reale vs Stimato (R²={score:.2f})")
                    m_min = min(df_model['target'].min(), df_model['Previsto'].min())
                    m_max = max(df_model['target'].max(), df_model['Previsto'].max())
                    fig_pred.add_trace(go.Scatter(x=[m_min, m_max], y=[m_min, m_max], mode='lines', line=dict(dash='dash'), name='Ideale'))
                    st.plotly_chart(fig_pred, use_container_width=True)
                    pred_col1, pred_col2 = st.columns(2)
                    val_t1 = pred_col1.number_input(f"{int(feat1)}m (s):", value=float(df_model['t1'].median()), step=0.05)
                    val_t2 = pred_col2.number_input(f"{int(feat2)}m (s):", value=float(df_model['t2'].median()), step=0.05)
                    predicted = model_lr.predict([[val_t1, val_t2]])[0]
                    st.info(f"🏁 Potenziale sui **{int(target)}m** stimato: **{predicted:.2f}s**")
                else:
                    st.warning("Servono almeno 5 corrispondenze (stessa data + atleta su tutte le distanze).")
            else:
                st.warning("Distanze insufficienti nel database per il modello lineare.")

    # ══════════════════════════════════════════════════════════════════════
    # TAB 4 — TRANSFER E CORRELAZIONE (GYM ↔ CORSA)
    # ══════════════════════════════════════════════════════════════════════

    with tab4:
        st.subheader("⚖️ Transfer Palestra → Pista")
        st.markdown(
            "Analisi ispirata alla metodologia **Forza-Velocità** di JB Morin PhD. "
            "Profilo Load-Velocity in palestra, curva di potenza, transfer temporale verso la pista, "
            "e calcolo del profilo sprint meccanico da split.",
            help="Fonte: JB Morin – jbmorin.net/downloads"
        )

        sub_t1, sub_t2, sub_t3, sub_t4 = st.tabs([
            "🔵 Profilo Load-Velocity",
            "⚡ Curva Potenza",
            "📊 Transfer Temporale",
            "🏃 Sprint F-V (calcolo)"
        ], key="transfer_subtabs", on_change="rerun")

        # ── SEZIONE A: LOAD-VELOCITY PROFILE ──────────────────────────────
        with sub_t1:
            st.markdown("### Profilo Forza-Velocità in Palestra")
            st.markdown(
                "Metodo Morin & Samozino. Dalla regressione lineare Carico↔Velocità si ricavano "
                "**V₀** (velocità teorica a carico zero), **L₀** (carico teorico massimo), "
                "**Pmax** e il **carico ottimale**. I punti sono colorati per zona (%vDec).",
                help="Morin JB, Samozino P (2016). Int J Sports Physiol Perform."
            )

            if len(df_v) == 0:
                st.warning("Nessun dato VBT disponibile.")
            else:
                lv_exercises = sorted([e for e in df_v['Esercizio'].dropna().unique() if e != 'General'])
                if not lv_exercises:
                    lv_exercises = sorted(df_v['Esercizio'].dropna().unique())

                col_lv1, col_lv2 = st.columns(2)
                default_ex_lv = "Squat" if "Squat" in lv_exercises else lv_exercises[0]
                lv_ex = col_lv1.selectbox(
                    "Esercizio", lv_exercises,
                    index=lv_exercises.index(default_ex_lv),
                    key="lv_ex"
                )

                lv_athletes_for_ex = sorted(
                    df_v[df_v['Esercizio'] == lv_ex]['Atleta'].dropna().unique()
                )
                if selected_athlete != "Tutta la squadra" and selected_athlete in lv_athletes_for_ex:
                    default_lv_atl = lv_athletes_for_ex.index(selected_athlete)
                else:
                    default_lv_atl = 0
                lv_atl = col_lv2.selectbox(
                    "Atleta", lv_athletes_for_ex,
                    index=default_lv_atl, key="lv_atl"
                )

                df_lv = df_v[
                    (df_v['Esercizio'] == lv_ex) & (df_v['Atleta'] == lv_atl)
                ].dropna(subset=['Carico', 'Vel_media'])

                if len(df_lv) < 3:
                    st.warning(
                        f"Servono almeno 3 set con carico e velocità per costruire il profilo. "
                        f"{lv_atl} ha {len(df_lv)} righe per {lv_ex}."
                    )
                else:
                    df_lv_agg = df_lv.groupby('Carico')['Vel_media'].median().reset_index()
                    df_lv_agg = df_lv_agg[df_lv_agg['Vel_media'] > 0].sort_values('Carico')

                    if len(df_lv_agg) < 2:
                        st.warning("Servono almeno 2 carichi diversi per la regressione.")
                    else:
                        coeffs_lv = np.polyfit(df_lv_agg['Carico'], df_lv_agg['Vel_media'], 1)
                        a_lv, b_lv = coeffs_lv

                        if b_lv <= 0 or a_lv >= 0:
                            st.warning(
                                "Profilo LV non valido: la velocità deve diminuire "
                                "all'aumentare del carico."
                            )
                        else:
                            V0_lv       = b_lv
                            L0_lv       = -b_lv / a_lv
                            Pmax_lv     = (V0_lv * L0_lv) / 4
                            opt_load_lv = L0_lv / 2
                            opt_vel_lv  = V0_lv / 2

                            k1, k2, k3, k4 = st.columns(4)
                            k1.metric("V₀ teorico", f"{V0_lv:.2f} m/s",
                                      help="Velocità estrapolata a carico nullo")
                            k2.metric("L₀ (1RM meccanico)", f"{L0_lv:.1f} kg",
                                      help="Carico estrapolato a velocità nulla")
                            k3.metric("Pmax teorica", f"{Pmax_lv:.0f} kg·m/s",
                                      help="(V₀ × L₀) / 4")
                            k4.metric("Carico ottimale", f"{opt_load_lv:.1f} kg",
                                      help="L₀/2 — carico che massimizza la potenza")

                            df_lv_agg['pct_vDec'] = (
                                1 - df_lv_agg['Vel_media'] / V0_lv
                            ) * 100

                            def _vdec_zone(pct):
                                if pct < 20:   return "Velocità / Tecnica"
                                elif pct < 40: return "Forza-Velocità"
                                elif pct < 60: return "Potenza (Pmax)"
                                elif pct < 80: return "Velocità-Forza"
                                else:          return "Forza Massima"

                            _ZC = {
                                "Velocità / Tecnica": "#00C8FF",
                                "Forza-Velocità":     "#00FF99",
                                "Potenza (Pmax)":     "#E8FF3A",
                                "Velocità-Forza":     "#FF9900",
                                "Forza Massima":      "#FF4444",
                            }
                            df_lv_agg['Zona'] = df_lv_agg['pct_vDec'].apply(_vdec_zone)

                            x_reg = np.linspace(
                                max(0, df_lv_agg['Carico'].min() * 0.8),
                                L0_lv * 1.05, 120
                            )
                            y_reg = np.clip(np.polyval(coeffs_lv, x_reg), 0, None)

                            fig_lv = go.Figure()

                            for flo, fhi, zn, zcol in [
                                (0.0, 0.2, "Velocità/Tecnica",   "rgba(0,200,255,0.07)"),
                                (0.2, 0.4, "Forza-Velocità",     "rgba(0,255,153,0.07)"),
                                (0.4, 0.6, "Potenza (Pmax)",     "rgba(232,255,58,0.10)"),
                                (0.6, 0.8, "Velocità-Forza",     "rgba(255,153,0,0.07)"),
                                (0.8, 1.0, "Forza Massima",      "rgba(255,68,68,0.07)"),
                            ]:
                                fig_lv.add_vrect(
                                    x0=L0_lv * flo, x1=L0_lv * fhi,
                                    fillcolor=zcol, line_width=0,
                                    annotation_text=zn,
                                    annotation_position="top left",
                                    annotation_font_size=9,
                                    annotation_font_color="rgba(255,255,255,0.4)"
                                )

                            fig_lv.add_trace(go.Scatter(
                                x=x_reg, y=y_reg, mode='lines',
                                name='Profilo L-V',
                                line=dict(color='rgba(232,255,58,0.6)', width=2, dash='dash')
                            ))

                            for zname, zdf in df_lv_agg.groupby('Zona'):
                                fig_lv.add_trace(go.Scatter(
                                    x=zdf['Carico'], y=zdf['Vel_media'],
                                    mode='markers+text', name=zname,
                                    marker=dict(
                                        color=_ZC[zname], size=11,
                                        line=dict(width=1, color='white')
                                    ),
                                    text=zdf['Carico'].apply(lambda x: f"{x:.0f}kg"),
                                    textposition='top center',
                                    textfont=dict(size=9, color='rgba(255,255,255,0.6)')
                                ))

                            fig_lv.add_trace(go.Scatter(
                                x=[opt_load_lv], y=[opt_vel_lv],
                                mode='markers', name='⭐ Carico Ottimale Pmax',
                                marker=dict(
                                    symbol='star', size=18, color='#E8FF3A',
                                    line=dict(width=1, color='white')
                                )
                            ))

                            fig_lv.update_layout(
                                title=f"Profilo Load-Velocity — {lv_atl} · {lv_ex}",
                                xaxis_title="Carico (kg)",
                                yaxis_title="Velocità Media (m/s)",
                                template=THEME_TEMPLATE,
                                height=490,
                                legend=dict(orientation='v', x=1.01, y=1)
                            )
                            fig_lv.update_xaxes(range=[0, L0_lv * 1.1])
                            fig_lv.update_yaxes(range=[0, V0_lv * 1.18])
                            st.plotly_chart(fig_lv, use_container_width=True)

                            st.markdown("#### 🧠 Interpretazione")
                            mean_vdec = df_lv_agg['pct_vDec'].mean()
                            if mean_vdec < 35:
                                _btxt = (
                                    f"**⚡ Orientamento Velocità** — {lv_atl} lavora prevalentemente "
                                    f"con carichi leggeri (%vDec medio: {mean_vdec:.0f}%). "
                                    f"Considera più lavoro nella zona Potenza e Velocità-Forza "
                                    f"(carichi vicino a {opt_load_lv:.0f}–{opt_load_lv*1.2:.0f} kg)."
                                )
                            elif mean_vdec > 65:
                                _btxt = (
                                    f"**💪 Orientamento Forza** — {lv_atl} lavora prevalentemente "
                                    f"con carichi pesanti (%vDec medio: {mean_vdec:.0f}%). "
                                    f"Per il transfer in pista aggiungi lavoro esplosivo "
                                    f"nella zona Potenza (≈ {opt_load_lv:.0f} kg)."
                                )
                            else:
                                _btxt = (
                                    f"**⚖️ Profilo Bilanciato** — {lv_atl} copre bene le zone "
                                    f"(%vDec medio: {mean_vdec:.0f}%). "
                                    f"Carico ottimale per Pmax: **{opt_load_lv:.1f} kg**."
                                )
                            st.info(_btxt)

                            with st.expander("📋 Dettaglio %vDec per carico"):
                                _dd = df_lv_agg[
                                    ['Carico', 'Vel_media', 'pct_vDec', 'Zona']
                                ].copy()
                                _dd.columns = [
                                    'Carico (kg)', 'Vel Media (m/s)', '%vDec', 'Zona'
                                ]
                                _dd['%vDec'] = _dd['%vDec'].round(1)
                                _dd['Vel Media (m/s)'] = _dd['Vel Media (m/s)'].round(3)
                                st.dataframe(_dd, use_container_width=True, hide_index=True)

        # ── SEZIONE B: POWER-VELOCITY CURVE ───────────────────────────────
        with sub_t2:
            st.markdown("### Curva Potenza-Velocità")
            st.markdown(
                "Mostra come la potenza espressa varia con la velocità di esecuzione. "
                "Il picco teorico si trova a V₀/2 (carico ottimale). "
                "Confronta i tuoi carichi con la zona di massima potenza."
            )

            if len(df_v) == 0:
                st.warning("Nessun dato VBT disponibile.")
            else:
                pv_exercises = sorted(
                    [e for e in df_v['Esercizio'].dropna().unique() if e != 'General']
                )
                if not pv_exercises:
                    pv_exercises = sorted(df_v['Esercizio'].dropna().unique())

                col_pv1, col_pv2 = st.columns(2)
                default_ex_pv = "Squat" if "Squat" in pv_exercises else pv_exercises[0]
                pv_ex = col_pv1.selectbox(
                    "Esercizio", pv_exercises,
                    index=pv_exercises.index(default_ex_pv),
                    key="pv_ex"
                )

                pv_athletes = sorted(
                    df_v[df_v['Esercizio'] == pv_ex]['Atleta'].dropna().unique()
                )
                if selected_athlete != "Tutta la squadra" and selected_athlete in pv_athletes:
                    default_pv_atl = pv_athletes.index(selected_athlete)
                else:
                    default_pv_atl = 0
                pv_atl = col_pv2.selectbox(
                    "Atleta", pv_athletes,
                    index=default_pv_atl, key="pv_atl"
                )

                df_pv_raw = df_v[
                    (df_v['Esercizio'] == pv_ex) & (df_v['Atleta'] == pv_atl)
                ].dropna(subset=['Carico', 'Vel_media'])
                df_pv_raw = df_pv_raw[
                    df_pv_raw['Potenza_max'].notna() | df_pv_raw['Potenza_media'].notna()
                ].copy()

                if len(df_pv_raw) < 3:
                    st.warning(
                        f"Servono almeno 3 record con dati di potenza "
                        f"per {pv_atl} su {pv_ex}."
                    )
                else:
                    _nmax = df_pv_raw['Potenza_max'].notna().sum()
                    _nmed = df_pv_raw['Potenza_media'].notna().sum()
                    use_pot_col = 'Potenza_max' if _nmax >= _nmed else 'Potenza_media'
                    label_pot = (
                        "Potenza Max (W)" if use_pot_col == 'Potenza_max'
                        else "Potenza Media (W)"
                    )

                    df_pv_agg = (
                        df_pv_raw.dropna(subset=['Vel_media', use_pot_col])
                        .groupby('Carico')
                        .agg(
                            Vel_media=('Vel_media', 'median'),
                            Potenza=(use_pot_col, 'max')
                        )
                        .reset_index()
                        .sort_values('Vel_media')
                    )

                    idx_max_pot = df_pv_agg['Potenza'].idxmax()
                    row_max_pot = df_pv_agg.loc[idx_max_pot]

                    has_parabola_pv = False
                    try:
                        c2 = np.polyfit(df_pv_agg['Vel_media'], df_pv_agg['Potenza'], 2)
                        vel_th = np.linspace(
                            df_pv_agg['Vel_media'].min() * 0.8,
                            df_pv_agg['Vel_media'].max() * 1.12,
                            100
                        )
                        pot_th = np.polyval(c2, vel_th)
                        vel_pk = -c2[1] / (2 * c2[0])
                        pot_pk = np.polyval(c2, vel_pk)
                        has_parabola_pv = c2[0] < 0
                    except Exception:
                        pass

                    fig_pv = go.Figure()
                    if has_parabola_pv:
                        fig_pv.add_trace(go.Scatter(
                            x=vel_th, y=pot_th, mode='lines',
                            name='Curva teorica',
                            line=dict(color='rgba(232,255,58,0.4)', width=2, dash='dot')
                        ))
                        fig_pv.add_trace(go.Scatter(
                            x=[vel_pk], y=[pot_pk], mode='markers',
                            name=f'Picco teorico ({vel_pk:.2f} m/s)',
                            marker=dict(symbol='star', size=16, color='#E8FF3A')
                        ))

                    fig_pv.add_trace(go.Bar(
                        x=df_pv_agg['Vel_media'],
                        y=df_pv_agg['Potenza'],
                        name=label_pot,
                        marker_color=[
                            '#E8FF3A' if i == idx_max_pot
                            else 'rgba(232,255,58,0.3)'
                            for i in df_pv_agg.index
                        ],
                        text=df_pv_agg['Carico'].apply(lambda x: f"{x:.0f}kg"),
                        textposition='outside'
                    ))

                    fig_pv.update_layout(
                        title=f"Curva Potenza-Velocità — {pv_atl} · {pv_ex}",
                        xaxis_title="Velocità Media (m/s)",
                        yaxis_title=label_pot,
                        template=THEME_TEMPLATE,
                        height=440,
                        bargap=0.3
                    )
                    st.plotly_chart(fig_pv, use_container_width=True)

                    kpv1, kpv2, kpv3 = st.columns(3)
                    kpv1.metric("Picco Potenza", f"{row_max_pot['Potenza']:.0f} W")
                    kpv2.metric("Velocità al picco", f"{row_max_pot['Vel_media']:.3f} m/s")
                    kpv3.metric("Carico al picco", f"{row_max_pot['Carico']:.1f} kg")

        # ── SEZIONE C: TRANSFER TEMPORALE (migliorato) ────────────────────
        with sub_t3:
            st.markdown("### Transfer Temporale Palestra → Pista")
            st.markdown(
                "Correlazione tra carichi medi mensili e tempi medi mensili di sprint. "
                "Una correlazione **negativa** (r < 0) indica transfer positivo.",
                help=(
                    "Dati aggregati per mese per compensare la non-contemporaneità "
                    "degli allenamenti."
                )
            )

            if len(df_v) == 0 or len(df_r) == 0:
                st.warning("Servono dati di corsa E di palestra per calcolare il transfer.")
            else:
                col_c1, col_c2 = st.columns(2)
                _vbt_ex = sorted(df_v['Esercizio'].dropna().unique())
                _run_dist = [d for d in sorted(df_r['Distanza'].unique()) if d >= 20]

                _def_vbt = "Squat" if "Squat" in _vbt_ex else (_vbt_ex[0] if _vbt_ex else "")
                ex_choice = col_c1.selectbox(
                    "Esercizio VBT", _vbt_ex,
                    index=_vbt_ex.index(_def_vbt) if _def_vbt in _vbt_ex else 0,
                    key="transfer_ex"
                )

                _def_run = 60 if 60 in _run_dist else (_run_dist[0] if _run_dist else 20)
                dist_choice = col_c2.selectbox(
                    "Distanza Sprint", _run_dist,
                    index=_run_dist.index(_def_run) if _def_run in _run_dist else 0,
                    key="transfer_dist"
                )

                if selected_athlete == "Tutta la squadra":
                    st.info(
                        "🔍 Seleziona un atleta dalla sidebar per l'analisi "
                        "di transfer personalizzata."
                    )
                else:
                    df_r_sub = df_r[df_r['Distanza'] == dist_choice].copy()
                    df_v_sub = df_v[df_v['Esercizio'] == ex_choice].copy()

                    if len(df_r_sub) == 0 and len(df_v_sub) == 0:
                        st.warning(
                            f"Mancano sia prove sui {int(dist_choice)}m "
                            f"che sessioni di {ex_choice}."
                        )
                    elif len(df_r_sub) == 0:
                        st.warning(
                            f"Nessuna prova sui {int(dist_choice)}m. "
                            f"Prova distanza diversa o amplia le date."
                        )
                    elif len(df_v_sub) == 0:
                        st.warning(
                            f"Nessuna sessione di {ex_choice}. "
                            f"Prova esercizio diverso o amplia le date."
                        )
                    else:
                        df_r_sub['Mese'] = df_r_sub['Data'].dt.to_period('M')
                        df_v_sub['Mese'] = df_v_sub['Data'].dt.to_period('M')
                        aggr_r = df_r_sub.groupby('Mese')['Tempo'].mean().reset_index()
                        aggr_v = df_v_sub.groupby('Mese')['Carico'].mean().reset_index()
                        merged = pd.merge(aggr_r, aggr_v, on='Mese', how='inner')
                        merged['Mese_Str'] = merged['Mese'].astype(str)

                        if len(merged) < 3:
                            _mr = set(df_r_sub['Data'].dt.to_period('M').unique())
                            _mv = set(df_v_sub['Data'].dt.to_period('M').unique())
                            st.warning(
                                f"Servono almeno **3 mesi** in comune. "
                                f"Attualmente: **{len(_mr & _mv)}** mese/i "
                                f"(sprint: {len(_mr)} mesi, palestra: {len(_mv)} mesi). "
                                f"Amplia il range date o cambia distanza/esercizio."
                            )
                        else:
                            import scipy.stats as stats
                            r_val, p_val = stats.pearsonr(merged['Carico'], merged['Tempo'])

                            fig_corr = px.scatter(
                                merged, x='Carico', y='Tempo', color='Mese_Str',
                                trendline="ols",
                                title=(
                                    f"Transfer {ex_choice} → {int(dist_choice)}m "
                                    f"· {selected_athlete}"
                                ),
                                labels={
                                    'Carico': f'Carico Medio {ex_choice} (kg)',
                                    'Tempo': f'Tempo Medio {int(dist_choice)}m (s)',
                                    'Mese_Str': 'Mese'
                                },
                                template=THEME_TEMPLATE,
                                color_discrete_sequence=NEON_COLORS
                            )
                            fig_corr.update_layout(height=430)
                            st.plotly_chart(fig_corr, use_container_width=True)

                            p_sig = p_val < 0.05
                            col_r1, col_r2 = st.columns(2)
                            col_r1.metric("Correlazione Pearson (r)", f"{r_val:.3f}")
                            col_r2.metric(
                                "Significatività",
                                f"p = {p_val:.3f} {'✅' if p_sig else '⚠️'}"
                            )

                            st.markdown("#### 🤖 Interpretazione")
                            if r_val < -0.3 and p_sig:
                                _ctxt = (
                                    f"**🟢 Transfer Positivo (r={r_val:.2f}, p={p_val:.3f})**: "
                                    f"Correlazione inversa significativa — all'aumentare del carico "
                                    f"in {ex_choice} i tempi sui {int(dist_choice)}m diminuiscono."
                                )
                            elif r_val < -0.3:
                                _ctxt = (
                                    f"**🟡 Tendenza Positiva (r={r_val:.2f})**: "
                                    f"Direzione corretta ma servono più dati "
                                    f"(p={p_val:.3f}) per confermare."
                                )
                            elif r_val > 0.3:
                                _ctxt = (
                                    f"**🔴 Attenzione (r={r_val:.2f})**: "
                                    f"Carico alto coincide con tempi alti — possibile "
                                    f"affaticamento o latenza del transfer. "
                                    f"Valuta riduzione del carico o finestra temporale più ampia."
                                )
                            else:
                                _ctxt = (
                                    f"**⚪ Transfer Non Lineare (r={r_val:.2f})**: "
                                    f"La variazione di carico non impatta linearmente i tempi. "
                                    f"Il transfer potrebbe essere mediato da tecnica o "
                                    f"freschezza neuromuscolare."
                                )
                            st.info(_ctxt)

        # ── SEZIONE D: SPRINT F-V PROFILE — modello Morin-Samozino completo
        with sub_t4:
            st.markdown("### Profilo F-V Sprint — Modello Morin-Samozino")
            st.markdown(
                "Inserisci i **tempi cumulativi** da **uno stesso sprint** "
                "(fotocellule a 10m, 20m, 30m...). "
                "Il modello adatta una curva esponenziale **v(t) = Vmax·(1−e^(−t/τ))** "
                "agli split, ricava la forza orizzontale istantanea (con correzione aerodinamica) "
                "e costruisce il profilo F-V: **F₀**, **V₀**, **Pmax**, **RF_max**, **Drf**.",
                help=(
                    "Morin JB & Samozino P (2016). Interpreting power-force-velocity profiles "
                    "for individualized and specific training. Int J Sports Physiol Perform. "
                    "Split dallo stesso sprint (es. fotocellule a 10, 20, 30, 40m). "
                    "Aerodrag: k = 0.5·ρ·Cd·Af."
                )
            )
            st.info("📌 Calcolo al momento — nessun dato viene salvato nel database.")
            st.markdown("---")

            # ── Parametri atleta ──
            st.markdown("**Parametri atleta:**")
            cpa1, cpa2, cpa3, cpa4 = st.columns(4)
            sp_mass   = cpa1.number_input("Massa (kg)", min_value=40.0, max_value=150.0,
                                           value=75.0, step=0.5, key="sp_mass")
            sp_height = cpa2.number_input("Altezza (m)", min_value=1.40, max_value=2.20,
                                           value=1.80, step=0.01, key="sp_height",
                                           format="%.2f")
            sp_temp   = cpa3.number_input("T° aria (°C)", min_value=-10.0, max_value=45.0,
                                           value=20.0, step=1.0, key="sp_temp",
                                           format="%.0f")
            sp_press  = cpa4.number_input("Pressione (hPa)", min_value=800.0, max_value=1050.0,
                                           value=1013.0, step=1.0, key="sp_press",
                                           format="%.0f")

            # ── Tempi cumulativi ──
            st.markdown("**Tempi cumulativi dalla partenza (s) — t₀ = 0:**")
            cs1, cs2, cs3, cs4, cs5, cs6 = st.columns(6)
            sp_t10  = cs1.number_input("10m",  min_value=0.0, max_value=5.0,  value=0.0, step=0.01, key="sp_t10",  format="%.2f")
            sp_t20  = cs2.number_input("20m",  min_value=0.0, max_value=5.0,  value=0.0, step=0.01, key="sp_t20",  format="%.2f")
            sp_t30  = cs3.number_input("30m",  min_value=0.0, max_value=6.0,  value=0.0, step=0.01, key="sp_t30",  format="%.2f")
            sp_t40  = cs4.number_input("40m",  min_value=0.0, max_value=7.0,  value=0.0, step=0.01, key="sp_t40",  format="%.2f")
            sp_t60  = cs5.number_input("60m",  min_value=0.0, max_value=10.0, value=0.0, step=0.01, key="sp_t60",  format="%.2f")
            sp_t100 = cs6.number_input("100m", min_value=0.0, max_value=15.0, value=0.0, step=0.01, key="sp_t100", format="%.2f")
            st.caption("💡 Inserisci 0 nei gate non disponibili. Servono almeno 3 checkpoint per un profilo affidabile.")

            if st.button("⚡ Calcola Profilo Sprint F-V", type="primary", key="btn_sprint_fv"):
                from scipy.optimize import minimize as _sp_minimize

                _gmap  = {10: sp_t10, 20: sp_t20, 30: sp_t30,
                          40: sp_t40, 60: sp_t60, 100: sp_t100}
                _gates = [(float(d), float(t)) for d, t in sorted(_gmap.items()) if t > 0]

                if len(_gates) < 2:
                    st.error("Inserisci almeno 2 checkpoint con tempo > 0.")
                else:
                    try:
                        # ── 1. Calcolo parametri aerodinamici ──────────────────
                        _g    = 9.81       # m/s²
                        _Cd   = 0.9        # drag coefficient (Morin default)
                        _rho  = 1.293 * (273.15 / (273.15 + sp_temp)) * (sp_press / 1013.25)
                        # Af formula Samozino — coerente con Excel e sprint_tools.html
                        _Af   = 0.2025 * (sp_height ** 0.725) * (sp_mass ** 0.425) * 0.266
                        _k    = 0.5 * _rho * _Cd * _Af   # kg/m

                        # ── 2. Fit modello esponenziale agli split ──────────────
                        # s(t) = Vmax * (t + tau * exp(-t/tau) - tau)
                        def _pos_model(t_val, Vmax_v, tau_v):
                            return Vmax_v * (t_val + tau_v * np.exp(-t_val / tau_v) - tau_v)

                        def _obj(params):
                            Vmax_v, tau_v = params
                            if Vmax_v <= 0 or tau_v <= 0.01:
                                return 1e9
                            return sum(
                                (_pos_model(t_val, Vmax_v, tau_v) - d_val) ** 2
                                for d_val, t_val in _gates
                            )

                        # Initial guess: Vmax from last gate, tau ~ 0.7 s
                        _d_last, _t_last = _gates[-1]
                        _Vmax0 = _d_last / _t_last * 1.6
                        _res = _sp_minimize(_obj, [_Vmax0, 0.7],
                                            method='Nelder-Mead',
                                            options={'xatol': 1e-9, 'fatol': 1e-12, 'maxiter': 20000})
                        _Vmax_fit, _tau_fit = _res.x

                        if _Vmax_fit <= 0 or _tau_fit <= 0:
                            st.error("Ottimizzazione del modello esponenziale fallita. "
                                     "Controlla i tempi inseriti.")
                        else:
                            # ── 3. Curva continua F-V ────────────────────────────
                            _dt    = 0.01
                            _t_arr = np.arange(0.001, _t_last + 2.5, _dt)
                            _v_arr = _Vmax_fit * (1 - np.exp(-_t_arr / _tau_fit))
                            _a_arr = (_Vmax_fit / _tau_fit) * np.exp(-_t_arr / _tau_fit)
                            _Fair  = _k * _v_arr ** 2
                            _Fdrive = sp_mass * _a_arr + _Fair   # forza orizzontale totale

                            # Usa solo la fase di vera accelerazione (v < 0.96 * Vmax)
                            _mask = _v_arr < _Vmax_fit * 0.96
                            _v_fv = _v_arr[_mask]
                            _F_fv = _Fdrive[_mask]

                            if len(_v_fv) < 10:
                                st.error("Dati insufficienti per la regressione F-V.")
                            else:
                                # ── 4. Regressione lineare F-V ─────────────────
                                _cfv = np.polyfit(_v_fv, _F_fv, 1)
                                _afv, _bfv = _cfv

                                if _bfv <= 0 or _afv >= 0:
                                    st.error("Regressione F-V non valida. "
                                             "Controlla tempi e parametri.")
                                else:
                                    _F0   = _bfv                  # N
                                    _V0   = -_bfv / _afv          # m/s
                                    _Sfv  = -_afv                 # N·s/m (slope magnitude)
                                    _Pmax = (_F0 * _V0) / 4       # W
                                    _Vopt = _V0 / 2               # m/s

                                    # Ratio of Force
                                    # RFmax e Drf calcolati da t≥0.51s (Excel/Samozino: colonna P parte da riga 52)
                                    _RF_arr = _F_fv / np.sqrt(_F_fv**2 + (sp_mass * _g)**2)
                                    _t_fv   = _t_arr[_mask]
                                    _rf51   = _t_fv >= 0.51
                                    if _rf51.any():
                                        _RF_max     = _RF_arr[_rf51][0]
                                        _drf_coeffs = np.polyfit(_v_fv[_rf51], _RF_arr[_rf51], 1)
                                    else:
                                        _RF_max     = _RF_arr[0]
                                        _drf_coeffs = np.polyfit(_v_fv, _RF_arr, 1)
                                    _Drf = _drf_coeffs[0] * 100   # %/(m/s)

                                    # ── 5. KPI ─────────────────────────────────
                                    fs1, fs2, fs3, fs4 = st.columns(4)
                                    fs1.metric("F₀", f"{_F0:.1f} N",
                                               f"{_F0/sp_mass:.2f} N/kg",
                                               help="Forza orizzontale teorica massima (a v=0)")
                                    fs2.metric("V₀ teorica", f"{_V0:.2f} m/s",
                                               help="Velocità teorica massima (a F=0)")
                                    fs3.metric("Pmax", f"{_Pmax:.0f} W",
                                               f"{_Pmax/sp_mass:.1f} W/kg",
                                               help="Potenza massima = F₀·V₀/4")
                                    fs4.metric("Sfv", f"{_Sfv:.1f} N·s/m",
                                               help="Pendenza profilo F-V: alta = orientato forza")

                                    fs5, fs6, fs7, fs8 = st.columns(4)
                                    fs5.metric("Vmax (fit)", f"{_Vmax_fit:.2f} m/s",
                                               help="Velocità massima dal fit esponenziale")
                                    fs6.metric("τ (costante tempo)", f"{_tau_fit:.3f} s",
                                               help="Costante di tempo dell'accelerazione")
                                    fs7.metric("RF_max", f"{_RF_max*100:.1f} %",
                                               help="Ratio of Force massimo (a v=0)")
                                    fs8.metric("Drf", f"{_Drf:.3f} %/(m/s)",
                                               help="Decremento di RF per unità di velocità (deve essere < 0)")

                                    # ── 6. Grafici ─────────────────────────────
                                    tab_fv1, tab_fv2, tab_fv3 = st.tabs([
                                        "📈 Profilo F-V", "⚡ Potenza-Velocità", "📉 Ratio of Force"
                                    ], key="forza_velocita_subtabs", on_change="rerun")

                                    with tab_fv1:
                                        _vr  = np.linspace(0, _V0 * 1.05, 200)
                                        _fr  = np.clip(np.polyval(_cfv, _vr), 0, None)
                                        fig_fv = go.Figure()
                                        fig_fv.add_trace(go.Scatter(
                                            x=_vr, y=_fr, mode='lines',
                                            name='Profilo F-V (lineare)',
                                            line=dict(color='rgba(232,255,58,0.6)', width=2, dash='dash')
                                        ))
                                        fig_fv.add_trace(go.Scatter(
                                            x=_v_fv[::10], y=_F_fv[::10],
                                            mode='markers', name='Dati modello',
                                            marker=dict(size=4, color='rgba(255,255,255,0.3)')
                                        ))
                                        fig_fv.add_trace(go.Scatter(
                                            x=[_Vopt], y=[_F0/2],
                                            mode='markers', name='⭐ Pmax',
                                            marker=dict(symbol='star', size=18, color='#FF9900')
                                        ))
                                        # Annotazioni split gate
                                        for _d_g, _t_g in _gates:
                                            _v_at_gate = _Vmax_fit * (1 - np.exp(-_t_g / _tau_fit))
                                            _a_at_gate = (_Vmax_fit / _tau_fit) * np.exp(-_t_g / _tau_fit)
                                            _F_at_gate = sp_mass * _a_at_gate + _k * _v_at_gate**2
                                            fig_fv.add_trace(go.Scatter(
                                                x=[_v_at_gate], y=[_F_at_gate],
                                                mode='markers+text',
                                                name=f'{int(_d_g)}m',
                                                marker=dict(size=10, color='#E8FF3A',
                                                            line=dict(width=1, color='black')),
                                                text=[f"{int(_d_g)}m"],
                                                textposition='top center',
                                                textfont=dict(size=9, color='rgba(255,255,255,0.7)'),
                                                showlegend=True
                                            ))
                                        fig_fv.update_layout(
                                            title="Profilo Forza-Velocità Sprint",
                                            xaxis_title="Velocità (m/s)",
                                            yaxis_title="Forza orizzontale (N)",
                                            template=THEME_TEMPLATE, height=430
                                        )
                                        fig_fv.update_xaxes(range=[0, _V0 * 1.1])
                                        fig_fv.update_yaxes(range=[0, _F0 * 1.2])
                                        st.plotly_chart(fig_fv, use_container_width=True)

                                    with tab_fv2:
                                        _vr2  = np.linspace(0, _V0, 200)
                                        _Fr2  = np.clip(np.polyval(_cfv, _vr2), 0, None)
                                        _Pr2  = _Fr2 * _vr2
                                        fig_pv2 = go.Figure()
                                        fig_pv2.add_trace(go.Scatter(
                                            x=_vr2, y=_Pr2, mode='lines',
                                            name='Curva Potenza',
                                            line=dict(color='#E8FF3A', width=2)
                                        ))
                                        fig_pv2.add_trace(go.Scatter(
                                            x=[_Vopt], y=[_Pmax],
                                            mode='markers', name=f'Pmax = {_Pmax:.0f} W',
                                            marker=dict(symbol='star', size=18, color='#FF9900')
                                        ))
                                        fig_pv2.update_layout(
                                            title="Curva Potenza-Velocità Sprint",
                                            xaxis_title="Velocità (m/s)",
                                            yaxis_title="Potenza (W)",
                                            template=THEME_TEMPLATE, height=400
                                        )
                                        st.plotly_chart(fig_pv2, use_container_width=True)

                                    with tab_fv3:
                                        _RF_line = _F_fv / np.sqrt(_F_fv**2 + (sp_mass*_g)**2) * 100
                                        fig_rf = go.Figure()
                                        fig_rf.add_trace(go.Scatter(
                                            x=_v_fv[::5], y=_RF_line[::5],
                                            mode='lines', name='RF (%)',
                                            line=dict(color='#00C8FF', width=2)
                                        ))
                                        fig_rf.add_hline(
                                            y=_RF_max*100, line_dash='dash',
                                            line_color='rgba(232,255,58,0.4)',
                                            annotation_text=f"RF_max = {_RF_max*100:.1f}%"
                                        )
                                        fig_rf.update_layout(
                                            title="Ratio of Force (efficacia meccanica)",
                                            xaxis_title="Velocità (m/s)",
                                            yaxis_title="RF (%)",
                                            template=THEME_TEMPLATE, height=380
                                        )
                                        st.plotly_chart(fig_rf, use_container_width=True)
                                        st.caption(
                                            "RF = Fh/Ftot — percentuale della forza totale diretta "
                                            "nella direzione del movimento. Deve essere alta all'inizio "
                                            "e diminuire gradualmente (Drf < 0)."
                                        )

                                    # ── 7. Verifica fit split ───────────────────
                                    with st.expander("📋 Verifica fit modello sugli split"):
                                        _fit_rows = []
                                        for _d_g, _t_g in _gates:
                                            _s_model = _pos_model(_t_g, _Vmax_fit, _tau_fit)
                                            _fit_rows.append({
                                                'Gate': f"{int(_d_g)}m",
                                                't misurato (s)': round(_t_g, 3),
                                                's modello (m)': round(_s_model, 3),
                                                'Errore (m)': round(_s_model - _d_g, 4),
                                            })
                                        st.dataframe(
                                            pd.DataFrame(_fit_rows),
                                            use_container_width=True, hide_index=True
                                        )
                                        st.caption(
                                            f"Vmax fit = {_Vmax_fit:.3f} m/s | "
                                            f"τ = {_tau_fit:.4f} s | "
                                            f"k (aerodrag) = {_k:.4f} kg/m | "
                                            f"ρ = {_rho:.4f} kg/m³ | "
                                            f"Af = {_Af:.4f} m²"
                                        )

                                    # ── 8. Interpretazione ──────────────────────
                                    st.markdown("#### 🧠 Interpretazione")
                                    if _Sfv > 35:
                                        _stxt = (
                                            f"**💪 Orientato alla Forza** (Sfv = {_Sfv:.1f} N·s/m): "
                                            f"Alta forza nelle fasi iniziali, ma decadenza marcata "
                                            f"con la velocità. "
                                            f"Considera sprint resistiti e lavoro forza-velocità."
                                        )
                                    elif _Sfv < 20:
                                        _stxt = (
                                            f"**⚡ Orientato alla Velocità** (Sfv = {_Sfv:.1f} N·s/m): "
                                            f"Buona velocità massima ({_Vmax_fit:.2f} m/s) "
                                            f"ma forza di accelerazione contenuta. "
                                            f"Considera partenze in blocco o sprint in salita breve."
                                        )
                                    else:
                                        _stxt = (
                                            f"**⚖️ Profilo Equilibrato** (Sfv = {_Sfv:.1f} N·s/m): "
                                            f"Buon bilanciamento forza/velocità. "
                                            f"Mantieni varietà tra lavoro di forza e sprint lanciati."
                                        )
                                    st.info(_stxt)

                    except Exception as _e_fv:
                        st.error(f"Errore nel calcolo F-V: {_e_fv}")
                        import traceback
                        st.code(traceback.format_exc())

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




# Stato ottimizzazioni — Atletica Dashboard

Nota di passaggio tra sessioni. Riferimento: `MIGLIORAMENTI_GENERALI.md`, sezione "Velocità e leggerezza".
Ultimo aggiornamento: 08/07/2026.

## Aggiornamenti successivi al 19/06

- **Fase A (foto su Storage): FATTA** (giu 2026). Bucket `foto-atleti`, foto esistenti migrate, upload nuovo su Storage con fallback base64.
- **Fase B (tab pigre): FATTA** per la pagina Dettaglio Atleta (guardie `_active_tab` sulle 5 tab principali).
- **statsmodels va tenuto in `requirements.txt`**: serve a Plotly per le linee di tendenza (`trendline='ols'`), anche se non è importato esplicitamente. Era stato rimosso per errore → crash sul cloud.
- **Modularizzazione fase 1: FATTA** (08/07/2026). Nuovo file `ui_helpers.py` con 9 funzioni di servizio spostate da `app.py` (logo, credenziali, CSV, card KPI/avvisi, filtri, ordinamento). `filter_running`, `filter_vbt` e `get_sort_key` ora ricevono i valori come parametri espliciti invece di leggere variabili globali. `app.py`: 4303 → 4249 righe. Prossime fasi: CSS in file separato, poi sezioni grandi (Dettaglio Atleta ecc.) in moduli propri.

## Fatto (già su disco, app avviabile)

Tutte le modifiche sono state applicate ai file reali e verificate (compilazione OK):

1. **Cache del logo** — `app.py`: nuova funzione `get_logo_b64()` con `@st.cache_data` (righe ~42-51). `logo.png` letto/codificato in base64 una sola volta invece che a ogni rerun nei due punti precedenti (cover di login ~riga 618 e header ~riga 1057).
2. **Lazy import scikit-learn** — `app.py`: rimosso `from sklearn.linear_model import LinearRegression` dalla testa del file; spostato dentro la funzione che lo usa (riga ~3359). Avvio a freddo più rapido.
3. **Pulizia `requirements.txt`** — rimossi `streamlit-calendar` e `statsmodels` (dipendenze morte). `scikit-learn` resta (usato).
4. **Cache + `with_foto` su `get_atleti`** — `supabase_connector.py`: `get_atleti(with_foto=True)` ora è `@st.cache_data(ttl=175)`. Con `with_foto=False` esclude la colonna `foto_url` (blob base64). La cache è invalidata dalle chiamate `st.cache_data.clear()` già presenti dopo inserimenti/modifiche.
5. **Homepage senza foto** — `app.py` riga ~1571: usa `get_atleti(with_foto=False)` (compleanni/anagrafica, non mostra foto). Il roster (riga ~1996) resta con foto.

Nota: durante una scrittura l'ultima riga di `app.py` si era troncata ed è stata riparata (il file termina con `st.caption("Dashboard Atletica · v3 Cloud · Powered by Supabase + Streamlit")`).

## Da fare (fasi pesanti — aprire una NUOVA sessione per ciascuna)

### A. Foto profilo su Supabase Storage
Oggi le foto sono salvate come stringa base64 in `atleti.foto_url` (vedi `upload_foto_profilo` in `supabase_connector.py`, riga ~407). Questo appesantisce anche il roster, che deve scaricare i blob.
- Creare bucket Storage, caricare lì le immagini, salvare solo l'URL in `foto_url`.
- Migrare le foto esistenti (script una tantum).
- Aggiornare `upload_foto_profilo` e i punti di rendering (`app.py` ~931, ~2096).
- Tocca DB + dati esistenti: fare backup prima.

### B. Tab/colonne non pigre
In Streamlit il codice dentro `st.tabs`/`st.columns` viene eseguito a ogni rerun anche per le sezioni non visibili: i grafici Plotly delle tab nascoste vengono comunque ricostruiti.
- Convertire le sezioni più pesanti da `st.tabs` a `st.radio`/`st.selectbox` così solo il ramo selezionato viene eseguito.
- Solo 3 `st.tabs` nel file: individuare quelle con più grafici e convertirle una alla volta, con test.

## Come riprendere
Incollare questa nota nella nuova sessione e indicare quale fase (A o B) affrontare. Far rileggere solo i file necessari a quella fase.

## Verifica rapida che l'app parta
```
streamlit run app.py
```
Dalla cartella del progetto. Se Supabase risponde, i dati arrivano dal cloud; le foto del roster funzionano come prima.

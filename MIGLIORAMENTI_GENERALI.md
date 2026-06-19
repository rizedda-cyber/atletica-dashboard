# Miglioramenti generali — Atletica Dashboard

Analisi della codebase (`app.py`, `supabase_connector.py`, `data_loader.py`) al 19/06/2026, al di là delle correzioni di sicurezza già applicate (revoca DELETE, rotazione chiave, soft-delete su `sessioni_corsa`). Le voci sono raggruppate per area, in ordine indicativo di priorità.

## Sicurezza residua

Il PIN personale degli atleti è salvato in chiaro nella colonna `pin_personale` di `atleti` (lo conferma anche il commento nel codice). Chiunque ottenga accesso al database o a un export vede tutti i PIN in chiaro. Andrebbe almeno hashato (es. bcrypt) lato applicazione prima dell'inserimento, oppure sostituito con un meccanismo di login più robusto.

La password admin (`ADMIN_PASSWORD`/`TEAM_PASSWORD`) viene confrontata con un semplice `==` sulla stringa letta dai secrets: funziona, ma non protegge da timing attack né da tentativi ripetuti (non c'è rate limiting né blocco dopo N tentativi falliti).

Il file `CREDENZIALI_DASHBOARD.txt` nella cartella del progetto contiene credenziali in chiaro su disco locale. È già escluso da Git, ma resta un punto debole se la cartella viene sincronizzata, condivisa o backuppata altrove: meglio spostare quei dati in un password manager.

La revoca dei permessi DELETE e il soft-delete sono stati applicati solo a `sessioni_corsa`. Le tabelle `sessioni_vbt` e `gare_ufficiali` hanno comunque perso i permessi DELETE lato database, ma l'app non ha (e non aveva) nessuna funzione di correzione o eliminazione per quei dati: se in futuro servirà permettere una correzione anche lì, andrà replicato lo stesso pattern soft-delete.

## Architettura e qualità del codice

`app.py` è un unico file da 4249 righe con appena 14 funzioni di primo livello: la maggior parte della logica (UI, calcoli, query) vive direttamente nel corpo dello script, non in funzioni testabili. Questo rende difficile isolare bug, scrivere test, e capire l'impatto di una modifica. Andrebbe scorporato in moduli per area (es. `pages/corsa.py`, `pages/vbt.py`, `pages/gare.py`, `auth.py`, `charts.py`), magari sfruttando il sistema multipagina nativo di Streamlit.

La gestione errori è incoerente: alcuni punti usano `except Exception as e: print(...)`, altri usano `except:` nudo che inghiotte silenziosamente qualsiasi errore (incluso `KeyboardInterrupt` o bug di programmazione). I `print()` finiscono nei log del server e non sono mai visibili all'utente né centralizzati: vale la pena introdurre il modulo `logging` standard con livelli (INFO/WARNING/ERROR) e mostrare messaggi di errore comprensibili nell'interfaccia invece di fallire silenziosamente.

## Affidabilità dei dati

`app.py` prova prima a leggere da Supabase (`get_data_cloud`) e, se non trova dati, ricade su `get_data_local()`, che legge `Lavori Corsa.xlsx` e `VBT2026322.xlsx` dalla cartella del progetto. Questi due file sono però esclusi da `.gitignore` (`*.xlsx`), quindi su un deploy pulito (es. dopo un nuovo clone su Streamlit Cloud) non esistono affatto: il fallback locale è inutilizzabile in produzione e darebbe un errore proprio nel momento critico in cui Supabase non risponde. Bisognerebbe decidere se questo fallback ha ancora senso e, se sì, garantire che i file siano disponibili anche in produzione (o eliminarlo e gestire l'assenza di dati cloud con un messaggio chiaro).

Le foto profilo vengono salvate come stringa base64 direttamente nella colonna `foto_url` della tabella `atleti`, bypassando Supabase Storage (il commento nel codice lo conferma esplicitamente). Questo gonfia ogni riga della tabella e ogni `SELECT *` su `atleti`, comprese le query che non hanno bisogno della foto. Migrare le foto su Supabase Storage e salvare solo l'URL alleggerirebbe le query e velocizzerebbe il caricamento della dashboard.

`data_loader.py` unifica i nomi degli atleti tra i due dataset Excel storici tramite un dizionario `NOME_MAPPING` scritto a mano (es. "Riki" → "Riccardo Murru"). Questa parte non va toccata: serve sia per lo storico migrato da Excel, sia perché i dati VBT continuano a essere caricati da un export di un altro software, dove basta un nome scritto in modo leggermente diverso per non far rientrare la riga nell'atleta giusto. Va mantenuta e aggiornata quando serve, non rimossa.

## Velocità e leggerezza

Il logo (`logo.png`) viene letto da disco e codificato in base64 due volte nel codice (righe 610 e 1055), senza nessuna cache. Streamlit riesegue tutto lo script a ogni interazione — un click, un cambio di tab, uno dei 21 `st.rerun()` presenti nel codice — quindi quella lettura/codifica viene rifatta a ogni singola interazione dell'utente, per un file che non cambia mai. Basta avvolgere la funzione che lo carica in `@st.cache_data` (o caricarlo una volta in una variabile globale) per eliminare questo lavoro ripetuto.

Nella cartella ci sono anche immagini mai usate nel codice: `Logo tondo.png` non viene richiamata da nessuna parte (sembra un duplicato di `logo.png`, stessa dimensione in byte), e i due file `scudetto-PhotoRoom...png` non risultano referenziati in `app.py` né in `data_loader.py`. A differenza dei file Excel/PDF, i PNG non sono esclusi da `.gitignore`: restano quindi nel repository Git e vengono scaricati a ogni clone/deploy senza essere usati. Vale la pena verificare se servono altrove (es. branding esterno) ed eventualmente rimuoverli dal repo.

`requirements.txt` include `streamlit-calendar` e `statsmodels`, ma nessuno dei due risulta importato in `app.py`, `supabase_connector.py` o `data_loader.py`: sono dipendenze morte che allungano comunque il tempo di build su Streamlit Cloud a ogni deploy. `scikit-learn` invece è importato in testa al file (`from sklearn.linear_model import LinearRegression`) ma usato in un solo punto del codice (riga 3362): spostare l'import dentro la funzione che lo usa (lazy import) toglie quel costo da ogni avvio a freddo, dato che `scikit-learn` è una libreria pesante da caricare.

Più in generale, in Streamlit il contenuto dentro `with st.tabs(...)` o `with st.columns(...)` non è "pigro": anche se l'utente sta guardando solo una tab, il codice di tutte le altre tab viene comunque eseguito a ogni rerun (vengono solo nascoste a livello visivo). Con 47 blocchi di tab/colonne e 32 costruzioni di grafici Plotly nel file, ogni interazione rischia di ricalcolare grafici che nessuno sta guardando in quel momento. Dove possibile, conviene condizionare la costruzione del grafico al fatto che la tab sia effettivamente quella attiva (es. con un radio/selectbox invece di `st.tabs`, che permette di eseguire solo il ramo selezionato), oppure spostare le sezioni più pesanti su pagine separate del sistema multipagina di Streamlit, così ognuna carica solo il proprio codice.

Infine, il fatto che le foto profilo viaggino come base64 dentro la riga `atleti` (già segnalato sopra) pesa anche sulla velocità, non solo sui dati: ogni query che legge gli atleti — anche quelle che non devono mostrare nessuna foto — scarica comunque quel blob da Supabase. Spostare le foto su Supabase Storage, oltre a essere più corretto architetturalmente, renderebbe più leggera e rapida ogni pagina che oggi fa solo `get_atleti()` per un elenco di nomi.

## Funzionalità mancanti

Solo le sessioni di corsa hanno una sezione "Correggi o Elimina un Tempo". Le sessioni VBT e le gare ufficiali (PB) si possono solo inserire, non correggere né eliminare: un atleta o un admin che sbaglia un dato VBT o un PB in gara non ha modo di rimediare dall'interfaccia, e deve chiedere un intervento manuale sul database.

Non esiste una cronologia delle modifiche (audit trail): quando un tempo viene corretto o una sessione viene soft-eliminata, non si registra chi ha fatto la modifica, quando, e qual era il valore precedente. Per un'app usata da più persone con ruoli diversi (admin, singoli atleti), anche un log minimale (tabella `audit_log` con utente, azione, timestamp, valore vecchio/nuovo) aiuterebbe a capire cosa è successo in caso di dati anomali.

## Test e processo di rilascio

Non ci sono test automatici: gli unici file di test trovati (`tmp_test_atleti.py`, `tmp_test_kpi.py`, `tmp_test_loader.py`) sono stati spostati in `.trash_tmp_files/` e non fanno parte di una suite reale. Funzioni come `parse_time`, i calcoli Forza-Velocità (Morin/Samozino) o `get_sessioni_corsa` sarebbero buoni candidati per test unitari, dato che un errore silenzioso lì produce numeri sbagliati senza che nessuno se ne accorga.

Gli script SQL di migrazione (`add_pin_column.sql`, `azzera_pin.sql`, `fix_dati_atleti.sql`, `supabase_rls_fix.sql`, `supabase_rls_tighten.sql`, `supabase_data_api_grants.sql`) vivono sparsi nella root del progetto senza un ordine o un sistema che tracci quali sono già stati eseguiti sul database di produzione. Una cartella `migrations/` con prefisso numerico o data, più un file che annota cosa è stato applicato, eviterebbe il rischio di rieseguire (o dimenticare di eseguire) uno script.

## Pulizia del repository

Nella cartella di progetto convivono file di lavoro molto pesanti (`Lavori Corsa.xlsx` 14 MB, due export VBT da 2 MB ciascuno, PDF e PPTX da centinaia di KB) insieme al codice sorgente. Sono già esclusi da Git, ma appesantiscono comunque la cartella locale e rendono meno immediato capire cosa sia codice attivo e cosa sia materiale di supporto: una sottocartella `docs/` o `dati_storici/` aiuterebbe a separarli visivamente.

`sprint_tools.html` è nato come migrazione di una parte dell'app pensata per essere usata esternamente: è corretto che resti uno strumento standalone separato, non va integrato né toccato.

import sys

with open('app.py', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Sposta JS Scroll
js_marker_start = "# ── JS globale: scroll-to-top"
js_start_idx = text.find(js_marker_start)
if js_start_idx != -1:
    # Trova la fine del blocco
    js_end_str = "st.session_state.page_just_changed = False\n"
    js_end_idx = text.find(js_end_str, js_start_idx)
    if js_end_idx != -1:
        js_end_idx += len(js_end_str)
        js_block = text[js_start_idx:js_end_idx]
        text = text[:js_start_idx] + text[js_end_idx:]
        
        # Aggiungiamo alla fine del file, senza rientri (poiché è globale)
        text += "\n" + js_block
        print("JS block spostato alla fine.")

# 2. Inverti Riepilogo Dettagliato e Classifica PB
pb_marker = "    st.markdown(\"<h3 style='margin-bottom:0;'>🏆 CLASSIFICA PERSONAL BEST"
pb_start_idx = text.find(pb_marker)

riepilogo_marker = "    with st.expander(\"📅 Riepilogo Dettagliato"
riepilogo_start_idx = text.find(riepilogo_marker)

# We must adjust pb_start to grab the preceding st.divider().
# If there's an st.divider() just before it.
pb_start_full = text.rfind("    st.divider()\n\n    st.markdown(\"<h3 style='margin-bottom:0;'>🏆 CLASSIFICA PERSONAL BEST", 0, pb_start_idx + len(pb_marker))

atleti_marker = "elif st.session_state.current_page == \"Atleti\":"
atleti_start_idx = text.find(atleti_marker)

# In the current file, pb_start comes before riepilogo_start, and riepilogo ends at atleti.
# The layout is: -> pb_block -> riepilogo_block -> atleti_block

if pb_start_full != -1 and riepilogo_start_idx != -1 and atleti_start_idx != -1:
    # Andiamo a cercare l'inizio reale di Riepilogo (il divider precedente)
    riepilogo_start_full = text.rfind("    st.divider()\n    with st.expander(\"📅 Riepilogo", 0, riepilogo_start_idx + len(riepilogo_marker))
    
    if riepilogo_start_full != -1:
        pb_block = text[pb_start_full:riepilogo_start_full]
        riepilogo_block = text[riepilogo_start_full:atleti_start_idx]
        
        new_text = text[:pb_start_full] + riepilogo_block + "\n" + pb_block + "\n" + text[atleti_start_idx:]
        print("Home sezioni riordinate.")
        text = new_text

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(text)

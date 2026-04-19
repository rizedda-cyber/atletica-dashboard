import sys

with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Trova inizio JS block
start_js = -1
end_js = -1
for i, line in enumerate(lines):
    if '# ── JS globale: scroll-to-top' in line:
        start_js = i
    if start_js != -1 and line.strip() == 'st.session_state.page_just_changed = False':
        end_js = i
        break

if start_js != -1 and end_js != -1:
    js_block = lines[start_js:end_js+1]
    lines = lines[:start_js] + lines[end_js+1:]
    lines.append('\n' + ''.join(js_block))
    print('JS block spostato alla fine.')

# Trova la Home
pb_idx = -1
for i, line in enumerate(lines):
    if 'CLASSIFICA PERSONAL BEST (PB) SQUADRA' in line:
        pb_idx = i - 1
        break

riepilogo_idx = -1
for i, line in enumerate(lines):
    if 'Riepilogo Dettagliato Allenamenti (Vista Excel)' in line:
        riepilogo_idx = i - 1
        break

end_riepilogo = -1
for i in range(riepilogo_idx + 1, len(lines)):
    if 'elif st.session_state.current_page == "Atleti":' in lines[i]:
        end_riepilogo = i - 1
        break

if pb_idx != -1 and riepilogo_idx != -1 and end_riepilogo != -1:
    pb_block = lines[pb_idx:riepilogo_idx]
    riepilogo_block = lines[riepilogo_idx:end_riepilogo]

    new_home = riepilogo_block + pb_block
    lines = lines[:pb_idx] + new_home + lines[end_riepilogo:]
    print('Home riordinata.')

with open('app.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

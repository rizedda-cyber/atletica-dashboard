with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

def get_line(substring):
    for i, line in enumerate(lines):
        if substring in line:
            return i
    return -1

pb_start = get_line('🏆 CLASSIFICA PERSONAL BEST')
riepil_start = get_line('with st.expander("📅 Riepilogo Dettagliato')
atleti_start = get_line('elif st.session_state.current_page == "Atleti":')

if pb_start != -1 and riepil_start != -1 and atleti_start != -1:
    block_pb_and_vol = lines[pb_start:riepil_start]  # Includes PB and Vol charts up to divider
    block_riepil = lines[riepil_start:atleti_start]  # Includes Riepilogo up to next elif
    
    # Put Riepilogo ABOVE PB and Vol
    # Important: Riepil_start should be preceded by an st.divider, but we can just prepend it
    new_home = block_riepil + ['\n    st.divider()\n\n'] + block_pb_and_vol
    
    # We remove the old parts and insert new
    final_lines = lines[:pb_start] + new_home + lines[atleti_start:]
    
    # Now for JS placement
    js_start = -1
    for i, line in enumerate(final_lines):
        if '# ── JS globale: scroll-to-top' in line:
            js_start = i
            break
            
    if js_start != -1:
        js_end = -1
        for i in range(js_start, len(final_lines)):
            if 'st.session_state.page_just_changed = False' in final_lines[i]:
                js_end = i
                break
        
        if js_end != -1:
            js_block = final_lines[js_start:js_end+1]
            final_lines = final_lines[:js_start] + final_lines[js_end+1:]
            final_lines.extend(['\n\n'] + js_block)
            
    with open('app.py', 'w', encoding='utf-8') as f:
        f.writelines(final_lines)
    print("Fatto")
else:
    print("Non trovato")

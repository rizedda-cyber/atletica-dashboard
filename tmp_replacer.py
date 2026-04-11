with open(r"c:\Users\rized\Desktop\Atletica\app.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

out = []
skip = False
for i, line in enumerate(lines):
    if line.startswith('if selected_athlete == "Tutta la squadra":') and "st.subheader(\"👥 Roster Atleti Attivi\")" in "".join(lines[i:i+3]):
        skip = True
        out.append('REPLACE_MARKER\n')
        continue
    
    if skip and line.startswith('    st.divider()'):
        skip = False
        continue
        
    if not skip:
        out.append(line)

new_content = """if selected_athlete == "Tutta la squadra":
    from supabase_connector import get_atleti
    df_atleti = get_atleti()
    
    st.markdown("<br>", unsafe_allow_html=True)
    col_r_left, col_r_right = st.columns([6, 4])
    
    with col_r_left:
        st.markdown("<h3 style='margin-bottom:0;'>ATLETI</h3>", unsafe_allow_html=True)
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
                        av_html = f'''<div style="width:55px; height:55px; border-radius:12px; border:2px solid {row["color"]}; overflow:hidden; margin-bottom:10px;">
                                        <img src="{row["foto"]}" style="width:100%; height:100%; object-fit:cover; display:block;">
                                      </div>'''
                    else:
                        inz = "".join([n[0] for n in row['nome'].split()[:2]]).upper()
                        av_html = f'''<div style="width:55px; height:55px; border-radius:12px; border:2px solid {row["color"]}; background:#14171E; color:#FFF; font-family:'DM Mono', monospace; font-size:20px; font-weight:bold; display:flex; align-items:center; justify-content:center; margin-bottom:10px;">
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
                        st.rerun()

    with col_r_right:
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
"""

res = "".join(out).replace("REPLACE_MARKER\n", new_content)
with open(r"c:\Users\rized\Desktop\Atletica\app.py", "w", encoding="utf-8") as f:
    f.write(res)
print("done")

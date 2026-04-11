import os
import re
import datetime
import pandas as pd
from data_loader import parse_time, NOME_MAPPING, normalize_names
from supabase_connector import get_supabase, get_atleti, upsert_atleta

def process_and_insert(file_path):
    print("Inizializzazione Supabase e Atleti...")
    supabase = get_supabase()
    df_atleti = get_atleti()
    
    # Crea mappa nome -> id
    nome_to_id = {}
    for _, row in df_atleti.iterrows():
        nome_to_id[row['nome_completo'].lower()] = row['id']
        
    def get_or_create_athlete(nome_raw):
        # normalize name
        nome_raw_title = nome_raw.strip().title()
        
        # Mappa usando NOME_MAPPING se presente
        title_mapping = {k.strip().title(): v for k, v in NOME_MAPPING.items()}
        mapped_nome = title_mapping.get(nome_raw_title, nome_raw_title)
        
        lower_mapped = mapped_nome.lower()
        if lower_mapped in nome_to_id:
            return nome_to_id[lower_mapped]
            
        print(f"  [!] Creazione nuovo atleta nel DB: {mapped_nome}")
        parts = mapped_nome.split()
        if len(parts) >= 2:
            n = " ".join(parts[:-1])
            c = parts[-1]
        else:
            n = mapped_nome
            c = ""
        new_record = upsert_atleta(n, c, "")
        new_id = new_record.get('id')
        nome_to_id[lower_mapped] = new_id
        return new_id

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    date_regex = re.compile(r'(lunedì|martedì|mercoledì|giovedì|venerdì|sabato|domenica)\s+(\d{2}-\d{2}-\d{2})', re.IGNORECASE)
    
    current_date = None
    headers = []
    
    records_to_insert = []
    
    for row_num, line in enumerate(lines, 1):
        line = line.strip('\n')
        if not line.strip():
            continue
            
        date_match = date_regex.search(line)
        if date_match:
            date_str_raw = date_match.group(2)
            try:
                dt = datetime.datetime.strptime(date_str_raw, "%d-%m-%y")
                current_date = dt.strftime("%Y-%m-%d")
            except:
                pass
            continue
            
        cols = line.split('\t')
        
        if len(cols) >= 2 and cols[0].lower() == 'nome' and cols[1].lower() == 'cognome':
            headers = [c.strip() for c in cols]
            continue
            
        if current_date and headers and len(cols) >= 2:
            nome = cols[0].strip()
            cognome = cols[1].strip()
            if not nome and not cognome:
                continue
            if nome.lower() in ['nome', 'lamentisti', 'velocisti', 'quattrocentisti']:
                continue
                
            atleta = f"{nome} {cognome}".strip()
            
            for i in range(2, len(cols)):
                if i >= len(headers):
                    break
                dist_str = headers[i]
                tempo_str = cols[i].strip()
                
                # Handling custom distances
                nota_extra = ""
                try:
                    if "libero 20" in dist_str.lower():
                        dist_num = 20.0
                        nota_extra = "Libero"
                    elif "cinesini" in dist_str.lower():
                        dist_num = 0.0 # 0 effectively means custom drill
                        nota_extra = "Cinesini"
                    elif "libero" in dist_str.lower():
                        dist_num = float(re.sub(r'[^0-9]', '', dist_str))
                        nota_extra = "Libero"
                    else:
                        dist_num = float(re.sub(r'[^0-9]', '', dist_str))
                except:
                    continue
                    
                if not tempo_str or tempo_str in ['/', 'KO']:
                    continue
                    
                parsed = parse_time(tempo_str)
                if parsed:
                    tempo_val = parsed['tempo']
                    nota_val = parsed['nota'] or ""
                    
                    if nota_extra:
                        nota_val = f"{nota_extra}. {nota_val}".strip(". ")
                        
                    atleta_id = get_or_create_athlete(atleta)
                    if not atleta_id:
                        continue
                        
                    records_to_insert.append({
                        "atleta_id": atleta_id,
                        "data": current_date,
                        "distanza_m": dist_num,
                        "tempo_sec": round(tempo_val, 3),
                        "nota": nota_val
                    })

    # Avoid inserting duplicates by fetching all first, but since dates are new, we could just rely on bulk insert 
    # to push them directly! In the migration script, we didn't check row-by-row for duplicates, we just asked to confirm. 
    # Since these are strictly new dates (March 13 to April 10, while OLD was till March 6), we are safe to insert directly.
    
    print(f"\nGenerati {len(records_to_insert)} record validi pronti al push!")
    
    BATCH = 500
    totale = 0
    for i in range(0, len(records_to_insert), BATCH):
        batch = records_to_insert[i:i + BATCH]
        resp = supabase.table("sessioni_corsa").insert(batch).execute()
        n = len(resp.data) if resp.data else 0
        totale += n
        print(f"Push Batch: inseriti {n}/{len(batch)}")
        
    print(f"\n🎉 SUCCESSO! {totale} tempi iniettati nel Supabase Cloud.")

if __name__ == '__main__':
    process_and_insert("tmp_new_data.tsv")

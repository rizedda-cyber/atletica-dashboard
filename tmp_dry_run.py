import re
import datetime
import pandas as pd
from data_loader import parse_time

def process_tsv(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    date_regex = re.compile(r'(lunedì|martedì|mercoledì|giovedì|venerdì|sabato|domenica)\s+(\d{2}-\d{2}-\d{2})', re.IGNORECASE)
    
    current_date = None
    headers = []
    
    report = {
        'success': [],
        'ignored_empty': 0,
        'failed_format': []
    }
    
    for row_num, line in enumerate(lines, 1):
        line = line.strip('\n')
        if not line.strip():
            continue
            
        # Check if Date row
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
        
        # Check Header
        if len(cols) >= 2 and cols[0].lower() == 'nome' and cols[1].lower() == 'cognome':
            headers = [c.strip() for c in cols]
            continue
            
        # Process athlete data
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
                
                # Check target distances
                try:
                    if "libero 20" in dist_str.lower():
                        dist_num = 20
                    elif "cinesini" in dist_str.lower():
                        dist_num = "cinesini"
                    else:
                        dist_num = int(re.sub(r'[^0-9]', '', dist_str))
                except:
                    continue # Not a valid distance column
                    
                if not tempo_str or tempo_str in ['/', 'KO']:
                    report['ignored_empty'] += 1
                    continue
                    
                parsed = parse_time(tempo_str)
                if parsed:
                    report['success'].append((current_date, atleta, dist_num, parsed['tempo'], tempo_str))
                else:
                    if 'velocista' not in tempo_str.lower() and 'non mi ricordo' not in tempo_str.lower():
                        report['failed_format'].append(f"Riga {row_num} [{atleta}] - Data: {current_date} - Dist: {dist_str} - VALORE NON VALIDO: '{tempo_str}'")

    print("=== REPORT DRY-RUN ===")
    print(f"✅ DATI VALIDI (pronti per inserimento/aggiornamento): {len(report['success'])}")
    print(f"ℹ️ DATI VUOTI (ignorati automaticamente): {report['ignored_empty']}")
    if report['failed_format']:
        print(f"❌ DATI NON RICONOSCIUTI ({len(report['failed_format'])}):")
        for f in report['failed_format']:
            print("   " + f)
    else:
        print("❌ DATI NON RICONOSCIUTI: 0")

if __name__ == '__main__':
    process_tsv("tmp_new_data.tsv")

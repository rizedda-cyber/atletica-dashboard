#!/usr/bin/env python3
import pandas as pd
from datetime import date, timedelta
import numpy as np

# Mock data
np.random.seed(42)
dates = pd.date_range(end=date.today(), periods=100, freq='D')
df_running = pd.DataFrame({
    'Data': dates,
    'Atleta': np.random.choice(['Marco', 'Sara', 'Luca', 'Elena'], 100),
    'Distanza': np.random.choice([60, 100, 200, 400], 100),
    'Tempo': np.random.uniform(7.0, 50.0, 100),
    'Note': [''] * 100
})
df_vbt = pd.DataFrame({
    'Data': dates[:50],
    'Atleta': np.random.choice(['Marco', 'Sara', 'Luca', 'Elena'], 50),
    'Esercizio': ['Squat'] * 50,
    'Potenza_max': np.random.uniform(500, 1500, 50),
    'Forza_max': np.random.uniform(1000, 3000, 50)
})

start_date = date.today() - timedelta(days=30)
end_date = date.today()
duration = (end_date - start_date).days
prev_start = start_date - timedelta(days=duration)
prev_end = start_date - timedelta(days=1)

mask_current = (df_running['Data'].dt.date >= start_date) & (df_running['Data'].dt.date <= end_date)
mask_prev = (df_running['Data'].dt.date >= prev_start) & (df_running['Data'].dt.date <= prev_end)
df_curr = df_running[mask_current]
df_prev = df_running[mask_prev]

sess_curr = df_curr['Data'].nunique()
sess_prev = df_prev['Data'].nunique()
delta_sess = sess_curr - sess_prev

prove_curr = len(df_curr)
prove_totali = len(df_running)

print(f"Sessioni: {sess_curr} (Δ {delta_sess:+} vs prec)")
print(f"Prove Registrate: {prove_curr} ({prove_totali} all-time)")

# Nuovi Record VBT nel periodo
# Calcoliamo i MAX storici fino a start_date
vbt_storico = df_vbt[df_vbt['Data'].dt.date < start_date].groupby(['Atleta', 'Esercizio'])['Potenza_max'].max().to_dict()
vbt_curr = df_vbt[(df_vbt['Data'].dt.date >= start_date) & (df_vbt['Data'].dt.date <= end_date)]
nuovi_record_vbt = 0
for idx, row in vbt_curr.iterrows():
    k = (row['Atleta'], row['Esercizio'])
    if k in vbt_storico:
        if row['Potenza_max'] > vbt_storico[k]:
            nuovi_record_vbt += 1
            vbt_storico[k] = row['Potenza_max']
    else:
        vbt_storico[k] = row['Potenza_max']
        nuovi_record_vbt += 1

print(f"Record VBT nel periodo: {nuovi_record_vbt}")

# Atleti in PB questo mese (usiamo i 30 giorni)
# Trova i min di delta storici fino a start_date
pb_storico = df_running[df_running['Data'].dt.date < start_date].groupby(['Atleta', 'Distanza'])['Tempo'].min().to_dict()
atleti_con_pb = set()
for idx, row in df_curr.iterrows():
    k = (row['Atleta'], row['Distanza'])
    if k in pb_storico:
        if row['Tempo'] < pb_storico[k]:
            atleti_con_pb.add(row['Atleta'])
            pb_storico[k] = row['Tempo']
    else:
        atleti_con_pb.add(row['Atleta'])
        pb_storico[k] = row['Tempo']

print(f"Atleti con PB: {len(atleti_con_pb)} - {atleti_con_pb}")

# Inattivi (ultimi 7 giorni)
max_date_per_atleta = pd.concat([df_running, df_vbt]).groupby('Atleta')['Data'].max()
inattivi = []
for atleta, ult_data in max_date_per_atleta.items():
    if (end_date - ult_data.date()).days > 7:
        inattivi.append(atleta)
print(f"Inattivi: {len(inattivi)} - {inattivi}")

# Media sessioni / sett
settimane_periodo = max(1, duration / 7)
tot_sessioni_per_atleta = df_curr.groupby('Atleta')['Data'].nunique()
media_sess_sett_atleta = tot_sessioni_per_atleta.mean() / settimane_periodo if len(tot_sessioni_per_atleta) > 0 else 0
print(f"Media sessioni/sett/atleta: {media_sess_sett_atleta:.1f}")

# Km totali
km_curr = df_curr['Distanza'].sum() / 1000
km_prev = df_prev['Distanza'].sum() / 1000
delta_km = km_curr - km_prev
print(f"Km totali: {km_curr:.1f} (Δ {delta_km:+.1f} vs prec)")

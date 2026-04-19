import os
from supabase import create_client
import pandas as pd
import streamlit as st

# Carica i segreti (mocking st.secrets for local script)
# In un ambiente reale userei st.secrets, qui uso variabili d'ambiente se presenti
# o provo a leggere secrets.toml se esiste.
import toml
try:
    secrets = toml.load(".streamlit/secrets.toml")
    url = secrets["secrets"]["SUPABASE_URL"]
    key = secrets["secrets"]["SUPABASE_KEY"]
except:
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")

supabase = create_client(url, key)

# Trova ID di Manuel Corda
res_atl = supabase.table("atleti").select("id").eq("nome_completo", "Manuel Corda").execute()
if not res_atl.data:
    print("Atleta non trovato")
    exit()

atleta_id = res_atl.data[0]["id"]
print(f"ID Atleta: {atleta_id}")

# Date richieste (senza anno per ora)
dates = ["10-31", "03-16", "03-06", "03-13"]

# Recupera sessioni
res = supabase.table("sessioni_corsa").select("*").eq("atleta_id", atleta_id).execute()
df = pd.DataFrame(res.data)
df['data'] = pd.to_datetime(df['data'])

# Filtra per le combinazioni mese-giorno richieste
def check_date(d):
    for target in dates:
        if d.strftime("%m-%d") == target:
            return True
    return False

filtered = df[df['data'].apply(check_date)].sort_values("data")
print(filtered[["id", "data", "distanza_m", "tempo_sec", "nota"]])

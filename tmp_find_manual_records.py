import requests
import json
import pandas as pd

URL = "https://gebesgvyogotajviursm.supabase.co"
KEY = "sb_publishable_mHfCbQPIcpBDxTx5yt1K7w_-azj4KHa"

headers = {
    "apikey": KEY,
    "Authorization": f"Bearer {KEY}",
    "Content-Type": "application/json"
}

# 1. Trova Atleta Manuel Corda
res = requests.get(f"{URL}/rest/v1/atleti?nome_completo=eq.Manuel Corda", headers=headers)
atleti = res.json()
if not atleti:
    print("Manuel Corda non trovato")
else:
    atl_id = atleti[0]['id']
    print(f"ID Atleta: {atl_id}")

    # 2. Recupera sessioni
    res = requests.get(f"{URL}/rest/v1/sessioni_corsa?atleta_id=eq.{atl_id}&order=data.asc", headers=headers)
    sessioni = res.json()
    
    df = pd.DataFrame(sessioni)
    if not df.empty:
        # Mostra le sessioni per le date interessate
        dates = ["-10-31", "-03-16", "-03-06", "-03-13"]
        def is_target(d):
            return any(target in str(d) for target in dates)
        
        filtered = df[df['data'].apply(is_target)]
        print(filtered[["id", "data", "distanza_m", "tempo_sec", "nota"]])
    else:
        print("Nessuna sessione trovata")

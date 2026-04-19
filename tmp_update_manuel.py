import requests
import json

URL = "https://gebesgvyogotajviursm.supabase.co"
KEY = "sb_publishable_mHfCbQPIcpBDxTx5yt1K7w_-azj4KHa"

headers = {
    "apikey": KEY,
    "Authorization": f"Bearer {KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

def update_record(record_id, payload):
    res = requests.patch(f"{URL}/rest/v1/sessioni_corsa?id=eq.{record_id}", headers=headers, json=payload)
    if res.status_code in (200, 204):
        print(f"✅ Record {record_id} aggiornato con {payload}")
    else:
        print(f"❌ Errore record {record_id}: {res.status_code} - {res.text}")

print("Iniziando aggiornamenti per Manuel Corda...")

# 31/10: 50m
update_record(3609, {"tempo_sec": 6.2})
update_record(3610, {"tempo_sec": 6.1})
update_record(3611, {"tempo_sec": 6.1})

# 16/03: 50m -> 80m
for rid in [5198, 5199, 5200, 5201, 5202, 5203]:
    update_record(rid, {"distanza_m": 80})

# 06/03
update_record(5114, {"distanza_m": 250}) # ex 120 a 34.70
update_record(5113, {"distanza_m": 300}) # ex 120 a 43.25
update_record(5115, {"distanza_m": 200}) # ex 150 a 28.80

# 13/03
for rid in [5279, 5277, 5301, 5303]: # ex 120 a ~19s
    update_record(rid, {"distanza_m": 150})

for rid in [5278, 5302]: # ex 120 a ~33s
    update_record(rid, {"distanza_m": 250})

for rid in [5304, 5280]: # ex 150 a 36.40s
    update_record(rid, {"distanza_m": 250})

print("Aggiornamenti completati!")

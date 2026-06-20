import base64
import time
from supabase_connector import get_supabase, FOTO_BUCKET

def main():
    print("Inizio migrazione foto a Supabase Storage...")
    supabase = get_supabase()
    
    try:
        response = supabase.table("atleti").select("id, nome_completo, foto_url").not_.is_("foto_url", "null").execute()
        atleti = response.data
    except Exception as e:
        print(f"Errore connessione al database: {e}")
        return
        
    migrati = 0
    ignorati = 0
    errori = 0
    
    for atleta in atleti:
        foto_str = atleta.get("foto_url", "")
        if not foto_str.startswith("data:image"):
            ignorati += 1
            continue
            
        print(f"Migrazione foto per: {atleta['nome_completo']} (ID: {atleta['id']})")
        
        try:
            # Estrai il base64 (data:image/jpeg;base64,/9j/4AAQ...)
            header, b64_data = foto_str.split(",", 1)
            file_bytes = base64.b64decode(b64_data)
            
            path = f"atleti/{atleta['id']}.jpg"
            
            # Carica su storage
            supabase.storage.from_(FOTO_BUCKET).upload(
                path,
                file_bytes,
                {"content-type": "image/jpeg", "upsert": "true", "cache-control": "3600"},
            )
            public_url = supabase.storage.from_(FOTO_BUCKET).get_public_url(path).rstrip("?")
            full_url = f"{public_url}?v={int(time.time())}"
            
            # Aggiorna il DB
            supabase.table("atleti").update({"foto_url": full_url}).eq("id", atleta['id']).execute()
            
            migrati += 1
            print("  -> OK")
            
        except Exception as e:
            errori += 1
            print(f"  -> ERRORE: {e}")
            
    print(f"\n--- Riepilogo ---")
    print(f"Foto migrate: {migrati}")
    print(f"Foto già a posto (ignorate): {ignorati}")
    print(f"Errori: {errori}")

if __name__ == "__main__":
    main()

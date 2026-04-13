import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
import os

# Simuliamo il caching di streamlit aggirandolo
from app import get_data_cloud

try:
    from supabase_connector import test_connection
    print("Test connection:", test_connection())
    
    r, v = get_data_cloud.__wrapped__() # Bypass st.cache_data
    if r is not None:
        print("Data Corsa:", len(r))
    else:
        print("Corsa is None")
        
except Exception as e:
    print("Errore:", e)

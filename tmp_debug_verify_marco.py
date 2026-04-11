from supabase_connector import get_sessioni_corsa
df = get_sessioni_corsa()
print("Marco 100:", df[df['Tempo'] == 100][['Data', 'Atleta', 'Distanza', 'Tempo']])

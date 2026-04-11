from supabase_connector import get_sessioni_corsa
df = get_sessioni_corsa()
print("Totale records fetchati:", len(df))
print("Mesi presenti:", df['Data'].dt.month.unique())
print("Data min:", df['Data'].min())
print("Data max:", df['Data'].max())
print("Esiste Marianna 438?", len(df[df['Tempo'] == 438]))
print("Esiste Marco 100?", len(df[df['Tempo'] == 100]))

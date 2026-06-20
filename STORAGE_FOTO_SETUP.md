# Foto su Supabase Storage — cosa fare

Obiettivo: salvare le foto degli atleti in un "archivio" (bucket) invece che
dentro il database. Risultato: dashboard più leggera e veloce.

Il codice è già pronto. Ha una rete di sicurezza: se l'archivio non è ancora
configurato, le foto continuano a funzionare col vecchio metodo. Quindi
**non si rompe niente** in nessun momento.

---

## Passo 1 — Creare l'archivio (lo fai tu su Supabase, 1 minuto)

1. Entra su https://supabase.com → apri il tuo progetto.
2. Menù a sinistra → **Storage**.
3. Clicca **New bucket**.
4. Nome esatto: `foto-atleti`  (tutto minuscolo, con il trattino).
5. Attiva l'interruttore **Public bucket** (le foto devono essere visibili nella dashboard).
6. Salva (**Create bucket**).

## Passo 2 — Permesso di caricamento (una volta sola)

Se la tua app usa la chiave "anon" di Supabase, serve dare il permesso di
caricare nel bucket. Modo più semplice:

- Menù a sinistra → **SQL Editor** → **New query**
- Incolla questo e premi **Run**:

```sql
-- Permette letture pubbliche e caricamenti nel bucket 'foto-atleti'
create policy "foto-atleti lettura pubblica"
  on storage.objects for select
  using ( bucket_id = 'foto-atleti' );

create policy "foto-atleti caricamento"
  on storage.objects for insert
  with check ( bucket_id = 'foto-atleti' );

create policy "foto-atleti aggiornamento"
  on storage.objects for update
  using ( bucket_id = 'foto-atleti' );
```

(Se invece l'app usa la chiave "service_role", questo passo non serve, ma
eseguirlo non fa danni.)

## Passo 3 — Pubblicare il codice

Vai su Antigravity e digli di pushare. Streamlit Cloud si riavvia.

## Passo 4 — Prova

1. Apri la dashboard → profilo di un atleta → **Cambia Foto** → carica una foto.
2. Se l'archivio è configurato bene, da ora quella foto è salvata come **link**
   (leggera). Se qualcosa non va, la foto viene salvata col vecchio metodo:
   funziona lo stesso, basta riprovare dopo aver sistemato i permessi.

---

## Passo 5 — Spostare le VECCHIE foto (DOPO, con calma)

I passi sopra fanno sì che le foto **nuove** vadano nell'archivio. Le foto
**già esistenti** restano nel vecchio formato finché non vengono ricaricate.
Per spostarle tutte in una volta c'è uno script dedicato, da lanciare **una
sola volta e dopo un backup del database**. Quando l'archivio funziona e vuoi
fare questo passo, chiedimelo e te lo preparo con le istruzioni.

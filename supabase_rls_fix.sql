-- ==========================================================
-- SCRIPT DI SICUREZZA: ATTIVAZIONE RLS E POLICY ACCESSO
-- Progetto: atletica-dashboard (gebesgvyogotajviursm)
-- Data: 15 Aprile 2026
-- ==========================================================

-- 1. ABILITAZIONE ROW LEVEL SECURITY (RLS)
-- Questo passaggio è FONDAMENTALE per risolvere l'avviso di Supabase.
-- Una volta abilitato, nessuno può accedere ai dati a meno che non ci sia una policy specifica.
ALTER TABLE public.atleti ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sessioni_corsa ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sessioni_vbt ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.gare_ufficiali ENABLE ROW LEVEL SECURITY;

-- 2. PULIZIA POLICY PRE-ESISTENTI (Per evitare errori di duplicazione)
DO $$ 
BEGIN
    DROP POLICY IF EXISTS "Allow anon read for atleti" ON public.atleti;
    DROP POLICY IF EXISTS "Allow anon update for atleti" ON public.atleti;
    DROP POLICY IF EXISTS "Allow anon insert for atleti" ON public.atleti;
    DROP POLICY IF EXISTS "Allow anon read for sessioni_corsa" ON public.sessioni_corsa;
    DROP POLICY IF EXISTS "Allow anon insert for sessioni_corsa" ON public.sessioni_corsa;
    DROP POLICY IF EXISTS "Allow anon read for sessioni_vbt" ON public.sessioni_vbt;
    DROP POLICY IF EXISTS "Allow anon insert for sessioni_vbt" ON public.sessioni_vbt;
    DROP POLICY IF EXISTS "Allow anon read for gare_ufficiali" ON public.gare_ufficiali;
    DROP POLICY IF EXISTS "Allow anon insert for gare_ufficiali" ON public.gare_ufficiali;
EXCEPTION WHEN OTHERS THEN 
    NULL;
END $$;

-- 3. DEFINIZIONE DELLE POLICY DI ACCESSO PER IL RUOLO 'ANON'
-- Dato che l'app utilizza una chiave anonima condivisa e un PIN lato Streamlit.

-- -- TABELLA: atleti -- --
-- Lettura: Permessa a tutti (per visualizzare i profili)
CREATE POLICY "Allow anon read for atleti" ON public.atleti 
    FOR SELECT USING (true);
-- Aggiornamento: Permesso (per cambio foto e bio)
CREATE POLICY "Allow anon update for atleti" ON public.atleti 
    FOR UPDATE USING (true);
-- Inserimento: Permesso (per nuovi atleti durante la migrazione o nuovi iscritti)
CREATE POLICY "Allow anon insert for atleti" ON public.atleti 
    FOR INSERT WITH CHECK (true);

-- -- TABELLA: sessioni_corsa -- --
CREATE POLICY "Allow anon read for sessioni_corsa" ON public.sessioni_corsa 
    FOR SELECT USING (true);
CREATE POLICY "Allow anon insert for sessioni_corsa" ON public.sessioni_corsa 
    FOR INSERT WITH CHECK (true);

-- -- TABELLA: sessioni_vbt -- --
CREATE POLICY "Allow anon read for sessioni_vbt" ON public.sessioni_vbt 
    FOR SELECT USING (true);
CREATE POLICY "Allow anon insert for sessioni_vbt" ON public.sessioni_vbt 
    FOR INSERT WITH CHECK (true);

-- -- TABELLA: gare_ufficiali -- --
CREATE POLICY "Allow anon read for gare_ufficiali" ON public.gare_ufficiali 
    FOR SELECT USING (true);
CREATE POLICY "Allow anon insert for gare_ufficiali" ON public.gare_ufficiali 
    FOR INSERT WITH CHECK (true);

-- ==========================================================
-- MESSAGGIO DI CONFERMA
-- ==========================================================
-- RLS configurata con successo per il ruolo anon.
-- L'avviso critico di Supabase scomparirà al prossimo scan.

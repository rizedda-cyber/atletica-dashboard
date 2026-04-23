-- ==========================================================
-- MIGRAZIONE: Aggiunta colonna pin_personale alla tabella atleti
-- Progetto: atletica-dashboard
-- Data: Aprile 2026
-- ==========================================================
-- 
-- ISTRUZIONI: Esegui questo script una sola volta nel SQL Editor di Supabase
-- (https://supabase.com → Table Editor → SQL Editor)
--
-- La colonna è nullable: gli atleti senza PIN usano il PIN squadra per leggere
-- e non possono modificare nulla finché non impostano il loro PIN personale.
-- ==========================================================

ALTER TABLE public.atleti ADD COLUMN IF NOT EXISTS pin_personale TEXT;

-- Aggiorna la policy di UPDATE per consentire gli aggiornamenti (incluso pin_personale)
-- (già presente nella config RLS attuale, nessuna azione necessaria)

-- VERIFICA: dopo l'esecuzione dovresti vedere la colonna nella tabella atleti
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'atleti' AND column_name = 'pin_personale';

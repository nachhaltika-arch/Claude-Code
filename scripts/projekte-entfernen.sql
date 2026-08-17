-- Alle Projekte aus der Produktivdatenbank entfernen
-- ===================================================
-- Angelegt 2026-08-17 auf Ansage: die Projekte werden später neu angelegt.
--
-- WICHTIG — vor dem Ausführen lesen:
--
-- An `projects` hängen fünfzehn Tabellen. Ein blankes `DELETE FROM projects`
-- scheitert an den Fremdschlüsseln und würde bei den übrigen Tabellen Zeilen
-- zurücklassen, deren `project_id` ins Leere zeigt. Dieses Skript trennt
-- deshalb zwei Fälle:
--
--   ABSCHNITT A — Zeilen, die BLEIBEN. Ihre `project_id` wird auf NULL
--     gesetzt, die Zeile selbst bleibt erhalten:
--       email_logs           Versandprotokoll. Bleibt ausdrücklich: Es ist
--                            der Nachweis, was wann an wen ging — und
--                            genau der wird gerade für die Aufarbeitung
--                            des Sequenz-Versands gebraucht
--       briefings            Kundenangaben, ohne Fremdschlüssel
--       assistant_conversations
--
--   ABSCHNITT B — Zeilen, die MIT GELÖSCHT werden, weil sie ohne ihr
--     Projekt keinen Inhalt haben:
--       project_checklists, communications, automation_logs,
--       time_tracking, project_scraped_pages, project_scrape_jobs,
--       project_credentials, geo_analyses, website_versions
--
--       invoices, retainer_contracts — auf Ansage vom 2026-08-17: Es gab
--       noch keine tatsächlichen Geschäfte, die Zeilen sind Testdaten.
--       Die Aufbewahrungspflicht aus § 147 AO / § 257 HGB gilt für
--       Rechnungen über echte Umsätze; hier greift sie nicht.
--       Schritt 1 listet sie trotzdem einzeln auf — bevor gelöscht wird,
--       einmal darübersehen, ob wirklich keine echte darunter ist.
--       Gesichert werden sie ohnehin (Abschnitt 0).
--
-- ⚠ EINE TABELLE VERDIENT EINE EIGENE ENTSCHEIDUNG: `customers`
--   `customers.project_id` ist NOT NULL mit Fremdschlüssel auf `projects`.
--   Solange Projekte gelöscht werden, KÖNNEN diese Zeilen nicht bleiben.
--   Darin stehen: `recurring_revenue`, `upsell_status`, `upsell_package`
--   und die CMS-Zugangsdaten (`cms_url`, `cms_username`,
--   `cms_password_encrypted`). Das ist der monatlich wiederkehrende Umsatz
--   und der Zugang zu Kundenseiten — beides nicht aus dem Projekt
--   wiederherstellbar.
--   Abschnitt 0 legt deshalb vorher eine Kopie an.
--
-- NICHT betroffen: `leads` (die Betriebe). Der laufende E-Mail-Versand hängt
-- an `leads.sequence_active` und wird hiervon NICHT gestoppt.
--
-- Ausführen in der Render-Postgres-Konsole. Das Skript öffnet eine
-- Transaktion und endet mit ROLLBACK. Erst die Zahlen ansehen, dann die
-- letzte Zeile auf COMMIT ändern und erneut ausführen.


-- ── Schritt 1: erst zählen (nur lesend) ─────────────────────────────────

SELECT 'projects' AS tabelle, count(*) FROM projects
UNION ALL SELECT 'customers (werden gelöscht)', count(*) FROM customers
UNION ALL SELECT 'invoices (werden gelöscht)', count(*) FROM invoices
UNION ALL SELECT 'retainer_contracts (werden gelöscht)', count(*) FROM retainer_contracts
UNION ALL SELECT 'email_logs (bleiben)', count(*) FROM email_logs WHERE project_id IS NOT NULL
ORDER BY 1;

-- Was an Umsatz an den customers-Zeilen hängt — vor dem Löschen ansehen:
SELECT count(*) AS kunden,
       sum(recurring_revenue) AS wiederkehrender_umsatz_pro_monat,
       count(*) FILTER (WHERE cms_password_encrypted IS NOT NULL) AS mit_cms_zugang
FROM customers;

-- Die Rechnungen einzeln — hier bitte einmal darübersehen. Erwartet werden
-- ausschliesslich Testdaten. Steht hier eine echte Rechnung, abbrechen.
SELECT id, project_id, created_at::date AS angelegt, *
FROM invoices
ORDER BY created_at DESC
LIMIT 100;


-- ── Schritt 2: löschen ──────────────────────────────────────────────────

BEGIN;

-- Abschnitt 0 — Sicherungskopien. Bleiben als Tabellen stehen, bis sie
-- ausdrücklich verworfen werden. Kosten nichts und sind der Unterschied
-- zwischen „rückholbar" und „weg".
CREATE TABLE IF NOT EXISTS customers_sicherung_2026_08_17 AS
  SELECT * FROM customers;
CREATE TABLE IF NOT EXISTS invoices_sicherung_2026_08_17 AS
  SELECT * FROM invoices;
CREATE TABLE IF NOT EXISTS retainer_contracts_sicherung_2026_08_17 AS
  SELECT * FROM retainer_contracts;
CREATE TABLE IF NOT EXISTS projects_sicherung_2026_08_17 AS
  SELECT * FROM projects;

DO $$
DECLARE
  -- Abschnitt A: Zeile bleibt, Verweis wird gelöst
  loesen text[] := ARRAY[
    'email_logs', 'briefings', 'assistant_conversations'
  ];
  -- Abschnitt B: Zeile geht mit
  entfernen text[] := ARRAY[
    'project_checklists', 'communications', 'automation_logs',
    'time_tracking', 'project_scraped_pages', 'project_scrape_jobs',
    'project_credentials', 'geo_analyses', 'website_versions',
    'invoices', 'retainer_contracts', 'customers'
  ];
  t text;
  n bigint;
BEGIN
  FOREACH t IN ARRAY loesen LOOP
    -- Tabellen werden teils erst zur Laufzeit angelegt; nicht vorhandene
    -- werden übersprungen statt die Transaktion abzubrechen.
    IF to_regclass(t) IS NOT NULL THEN
      EXECUTE format('UPDATE %I SET project_id = NULL WHERE project_id IS NOT NULL', t);
      GET DIAGNOSTICS n = ROW_COUNT;
      RAISE NOTICE 'Verweis gelöst: %  (% Zeilen bleiben erhalten)', t, n;
    END IF;
  END LOOP;

  FOREACH t IN ARRAY entfernen LOOP
    IF to_regclass(t) IS NOT NULL THEN
      EXECUTE format('DELETE FROM %I', t);
      GET DIAGNOSTICS n = ROW_COUNT;
      RAISE NOTICE 'Gelöscht: %  (% Zeilen)', t, n;
    END IF;
  END LOOP;
END $$;

DELETE FROM projects;

-- Gegenprobe — die ersten vier müssen 0 sein, die Sicherungen die alten Zahlen
SELECT 'projects' AS tabelle, count(*) FROM projects
UNION ALL SELECT 'customers', count(*) FROM customers
UNION ALL SELECT 'invoices', count(*) FROM invoices
UNION ALL SELECT 'retainer_contracts', count(*) FROM retainer_contracts
UNION ALL SELECT '— Sicherung projects', count(*) FROM projects_sicherung_2026_08_17
UNION ALL SELECT '— Sicherung customers', count(*) FROM customers_sicherung_2026_08_17
UNION ALL SELECT '— Sicherung invoices', count(*) FROM invoices_sicherung_2026_08_17
UNION ALL SELECT 'email_logs (bleibt vollständig)', count(*) FROM email_logs
ORDER BY 1;

-- Zahlen prüfen. Passt alles: diese Zeile auf COMMIT ändern.
ROLLBACK;

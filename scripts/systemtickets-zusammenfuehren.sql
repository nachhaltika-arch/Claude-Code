-- Systemtickets zusammenführen — den Bestand aufräumen, den der Datums-
-- Schlüssel angelegt hat (Befund vom 2026-08-23).
--
-- **Was passiert ist.** `job_check_overdue_phases` bildete seinen Schlüssel
-- als `stuck-{projekt}-{phase}-{JJJJMMTT}`. Das Datum darin machte jeden Tag
-- einen neuen Schlüssel und damit ein neues Ticket für denselben Sachverhalt.
-- Produktiv standen am 23.08.2026 **2.343** Zeilen in `support_tickets`,
-- davon **2.335** vom Typ `system`, alle `open`, entstanden seit dem
-- 10.04.2026 mit rund neunzehn pro Tag. Die **acht** Rückmeldungen von
-- Menschen waren darin nicht mehr auffindbar.
--
-- Der Code ist behoben; ab sofort entsteht ein Ticket je Projekt und Phase.
-- Dieses Skript räumt den **Altbestand** auf. Es läuft bewusst von Hand und
-- nicht in der Startphase: Ein Massenschreibvorgang auf Kundendaten gehört
-- nicht in einen Serverstart.
--
--   Aufruf:  psql "$DATABASE_URL" -f scripts/systemtickets-zusammenfuehren.sql
--
-- **Es wird nichts gelöscht.** Die Altzeilen werden auf `closed` gesetzt und
-- tragen den Grund in `admin_notes`. Löschen wäre bequemer und nähme jede
-- Möglichkeit, den Vorgang später nachzuvollziehen — und die Tabelle ist mit
-- 1,5 MB kein Platzproblem.
--
-- **Je Projekt und Phase bleibt genau eine Zeile offen: die jüngste.** Sie
-- trägt den aktuellen Stand, und der Code schreibt ab jetzt genau sie fort.
-- Ihre `ticket_number` wird auf den neuen Schlüssel ohne Datum gesetzt —
-- sonst legte der nächste Lauf trotzdem ein neues Ticket daneben.

BEGIN;

-- Vorher zählen, damit die Wirkung belegt ist und nicht geglaubt werden muss.
\echo '── vorher ──'
SELECT count(*) FILTER (WHERE type = 'system')                    AS system_gesamt,
       count(*) FILTER (WHERE type = 'system' AND status = 'open') AS system_offen,
       count(*) FILTER (WHERE type <> 'system')                    AS von_menschen
FROM support_tickets;

-- Die jüngste offene Zeile je Projekt+Phase — sie bleibt und wird umbenannt.
CREATE TEMP TABLE behalten ON COMMIT DROP AS
SELECT DISTINCT ON (schluessel) id, schluessel
FROM (
  SELECT id, created_at,
         regexp_replace(ticket_number, '-\d{8}$', '') AS schluessel
  FROM support_tickets
  WHERE type = 'system'
    AND status = 'open'
    AND ticket_number ~ '^stuck-\d+-phase_\d+-\d{8}$'
) t
ORDER BY schluessel, created_at DESC, id DESC;

-- Alles andere aus dieser Familie wird geschlossen, mit Grund.
UPDATE support_tickets s
SET status = 'closed',
    resolved_at = now(),
    updated_at = now(),
    admin_notes = coalesce(s.admin_notes || E'\n', '')
      || 'Automatisch geschlossen am 2026-08-23: Doppeleintrag aus dem '
      || 'Datums-Schluessel (ein Ticket je Tag statt je Sachverhalt). '
      || 'Der jeweils juengste Eintrag je Projekt und Phase bleibt offen.'
WHERE s.type = 'system'
  AND s.status = 'open'
  AND s.ticket_number ~ '^stuck-\d+-phase_\d+-\d{8}$'
  AND s.id NOT IN (SELECT id FROM behalten);

-- Die Überlebenden auf den neuen Schlüssel heben, damit der Job sie
-- fortschreibt statt ein weiteres Ticket danebenzulegen.
UPDATE support_tickets s
SET ticket_number = b.schluessel,
    updated_at = now()
FROM behalten b
WHERE s.id = b.id;

\echo '── nachher ──'
SELECT count(*) FILTER (WHERE type = 'system')                     AS system_gesamt,
       count(*) FILTER (WHERE type = 'system' AND status = 'open') AS system_offen,
       count(*) FILTER (WHERE type <> 'system')                    AS von_menschen
FROM support_tickets;

\echo '── was offen bleibt ──'
SELECT ticket_number, title, created_at::date AS seit
FROM support_tickets
WHERE type = 'system' AND status = 'open'
ORDER BY ticket_number;

COMMIT;

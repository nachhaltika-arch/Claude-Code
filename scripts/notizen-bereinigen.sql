-- Maschinenzeilen aus den Notizen der Betriebe entfernen
-- =======================================================
-- Angelegt 2026-08-17 zu UX-06.
--
-- WORUM ES GEHT
--
-- `services/lead_enrichment.py` schrieb nach jedem Lauf eine Zeile
--
--     [Auto-Enrichment] SSL: OK | Impressum: FEHLT | PageSpeed: 43/100 | Score: 65/100
--
-- **vor** das, was ein Mensch in `leads.notes` geschrieben hatte. Bei jedem
-- Lauf erneut. Das Feld fuer die eigenen Notizen fuellte sich mit
-- Maschinentext, und die eigene Notiz rutschte nach unten.
--
-- Ab dem 17.08.2026 schreibt die Anreicherung in eigene Spalten
-- (`has_ssl`, `has_impressum`, `pagespeed_mobile_score`, `enriched_at`).
-- Neue Zeilen entstehen also nicht mehr. Was schon drinsteht, bleibt aber
-- stehen — dafuer ist dieses Skript da.
--
-- WAS ES TUT
--
-- Es entfernt aus `leads.notes` jede Zeile, die mit `[Auto-Enrichment]`
-- beginnt. Alles andere bleibt Zeichen fuer Zeichen erhalten. Bleibt nach
-- dem Entfernen nichts uebrig, wird das Feld auf NULL gesetzt statt auf einen
-- leeren Text — sonst steht in der Oberflaeche ein leerer Notizkasten.
--
-- Die Befunde gehen dabei nicht verloren: Sie stecken in den neuen Spalten,
-- sobald der Betrieb das naechste Mal angereichert wird. Fuer den Altbestand
-- heisst die Anzeige bis dahin ehrlich „nicht geprueft" — das ist richtiger
-- als eine Zahl von unbekanntem Alter.
--
-- Ausfuehren in der Render-Postgres-Konsole. Das Skript oeffnet eine
-- Transaktion und endet mit ROLLBACK. Erst die Zahlen ansehen, dann die
-- letzte Zeile auf COMMIT aendern und erneut ausfuehren.


-- ── Schritt 1: erst zaehlen und ansehen (nur lesend) ────────────────────

SELECT count(*) FILTER (WHERE notes LIKE '%[Auto-Enrichment]%') AS betroffen,
       count(*) FILTER (WHERE notes IS NOT NULL AND notes <> '')  AS mit_notiz,
       count(*)                                                   AS betriebe_gesamt
FROM leads;

-- Wie viele Zeilen es je Betrieb sind — die Zahl zeigt, wie oft angereichert
-- wurde. Zweistellige Werte sind zu erwarten.
SELECT id,
       company_name,
       (length(notes) - length(replace(notes, '[Auto-Enrichment]', '')))
         / length('[Auto-Enrichment]') AS maschinenzeilen,
       length(notes) AS zeichen_gesamt
FROM leads
WHERE notes LIKE '%[Auto-Enrichment]%'
ORDER BY 3 DESC
LIMIT 50;

-- Und einmal hineinsehen: Was bliebe uebrig? Links das Alte, rechts das Neue.
-- Hier bitte pruefen, dass rechts nichts fehlt, was ein Mensch geschrieben hat.
SELECT id,
       company_name,
       notes AS vorher,
       nullif(
         trim(both E'\n' FROM
           regexp_replace(notes, '(?n)^\[Auto-Enrichment\].*$\n?', '', 'g')
         ), ''
       ) AS nachher
FROM leads
WHERE notes LIKE '%[Auto-Enrichment]%'
ORDER BY id
LIMIT 50;


-- ── Schritt 2: bereinigen ──────────────────────────────────────────────

BEGIN;

-- Sicherungskopie. Bleibt als Tabelle stehen, bis sie ausdruecklich verworfen
-- wird. Kostet nichts und ist der Unterschied zwischen „rueckholbar" und „weg".
CREATE TABLE IF NOT EXISTS leads_notizen_sicherung_2026_08_17 AS
  SELECT id, company_name, notes, now() AS gesichert_am
  FROM leads
  WHERE notes IS NOT NULL;

UPDATE leads
SET notes = nullif(
      trim(both E'\n' FROM
        regexp_replace(notes, '(?n)^\[Auto-Enrichment\].*$\n?', '', 'g')
      ), ''
    )
WHERE notes LIKE '%[Auto-Enrichment]%';

-- Gegenprobe: die erste Zahl muss 0 sein, die Sicherung die alte Menge halten.
SELECT count(*) FILTER (WHERE notes LIKE '%[Auto-Enrichment]%') AS noch_betroffen,
       count(*) FILTER (WHERE notes IS NOT NULL AND notes <> '') AS mit_notiz
FROM leads;

SELECT count(*) AS gesichert FROM leads_notizen_sicherung_2026_08_17;

-- Zahlen pruefen. Passt alles: diese Zeile auf COMMIT aendern.
ROLLBACK;

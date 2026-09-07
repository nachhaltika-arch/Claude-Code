-- Drei verwaiste Tabellen aus der Produktivdatenbank entfernen (L-146)
-- ====================================================================
-- Vorbereitet am 2026-09-07. NICHT ausgeführt — das Löschen produktiver
-- Tabellen ist Davids Entscheidung, nicht meine.
--
-- WICHTIG — vor dem Ausführen lesen:
--
-- Gemessen am 28.08.2026 bei der Wiederherstellungsprobe: Produktiv hat 73
-- Tabellen, ein frisch aufgebautes Staging 70. Die Differenz sind genau die
-- drei hier. Eine Suche über den gesamten Backend-Quelltext findet zu allen
-- dreien null Verweise — am 07.09.2026 nachgemessen, weiterhin null.
--
-- ABSCHNITT A ist eine ABFRAGE, kein Löschen. Erst lesen, dann entscheiden.
-- Dieselbe Auskunft gibt seit dem 07.09.2026 auch `GET /api/diagnostics/schema`
-- unter `verwaiste_tabellen` — ohne Datenbankzugang, hinter `require_admin`.
--
-- `schema_migrations` zuerst, und zwar aus einem Grund: Sie ist die
-- Buchführung eines Migrationsverfahrens, das beim Start gar nicht läuft — es
-- läuft allein `migrations_runtime.run_migrations`. Wer dort den
-- Migrationsstand abliest, liest 25 Zeilen, die seit Monaten nichts mehr
-- abbilden. Eine veraltete Auskunft ist schlechter als gar keine, weil sie
-- beantwortet aussieht. Die beiden anderen sind bloß Ballast.


-- ── ABSCHNITT A — nachsehen, bevor irgendetwas fällt ───────────────────
-- Werden die Zeilen irgendwo als Beleg gebraucht? Das ist die Vorbedingung
-- aus dem Lagebild-Eintrag und die einzige Frage, die dieses Skript nicht
-- selbst beantworten kann.

SELECT 'schema_migrations' AS tabelle, count(*) AS zeilen FROM schema_migrations
UNION ALL SELECT 'revoked_tokens', count(*) FROM revoked_tokens
UNION ALL SELECT 'seo_analyses',   count(*) FROM seo_analyses;

-- Und was genau darin steht — 25 Zeilen liest man in einer Minute:
SELECT * FROM schema_migrations ORDER BY 1;


-- ── ABSCHNITT B — fallen lassen ────────────────────────────────────────
-- Erst ausführen, wenn Abschnitt A gelesen ist.
--
-- Vorher eine Sicherung ziehen. `docs/sicherung-und-wiederherstellung.md`
-- beschreibt den Weg; genau diese Probe hat den Befund überhaupt erst
-- sichtbar gemacht.
--
-- `IF EXISTS`, damit ein zweiter Lauf nicht abbricht. Kein `CASCADE`: Hängt
-- wider Erwarten etwas an einer der Tabellen, soll die Anweisung **scheitern**
-- und es zeigen, statt still mitzureißen.

-- BEGIN;
-- DROP TABLE IF EXISTS schema_migrations;
-- DROP TABLE IF EXISTS revoked_tokens;
-- DROP TABLE IF EXISTS seo_analyses;
-- COMMIT;

-- Danach zur Gegenprobe `GET /api/diagnostics/schema` aufrufen: Unter
-- `bewertung` muss stehen „Keine der drei verwaisten Tabellen steht in dieser
-- Datenbank". Steht dort weiter eine Zeile, ist das DROP nicht durchgelaufen.

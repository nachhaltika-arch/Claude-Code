-- Wer hat die Widget-Bestätigungen ausgelöst?
-- ============================================
-- Angelegt 2026-08-17 zur offenen Frage vom 16.08.: Um 16:12:09 kam eine
-- Bestätigung per POST, im Protokoll stand keine Abweisung, und wer sie
-- ausgeloest hat, war nicht feststellbar.
--
-- Nur lesend. Nichts hier veraendert Daten.
--
-- WARUM DAS ZAEHLT
--
-- Die Bestaetigung ist das Doppel-Opt-in. Hat ein Postfach-Scanner sie
-- erteilt, ist sie keine Einwilligung — und im Streitfall als Nachweis
-- wertlos. Art. 5 Abs. 2 DSGVO verlangt, dass man belegen kann, wer
-- eingewilligt hat.
--
-- WAS DIE SPALTEN SAGEN
--
--   verify_sent_at        wann die Bestaetigungsmail rausging
--   verified_at           wann bestaetigt wurde
--   verified_user_agent   womit (Browser? Sicherheits-Gateway?)
--   verified_ip           von wo
--
-- Die **Dauer zwischen beiden** ist das schaerfste Merkmal, das ohne fremde
-- Hilfe zu haben ist: Ein Mensch braucht Sekunden bis Minuten — die Mail
-- muss ankommen, gelesen und geoeffnet werden. Ein Scanner braucht keine.
-- Am 16.08. kam die Berichts-Mail fuenfzehn Sekunden nach der ersten.
--
-- Seit dem 17.08. steht dasselbe auch im Tool unter Akquise → Widget-Anfragen.


-- ── 1. Alle Bestaetigungen, neueste zuerst ──────────────────────────────

SELECT id,
       email,
       website_url,
       verify_sent_at,
       verified_at,
       round(extract(epoch FROM (verified_at - verify_sent_at))) AS sekunden_bis_klick,
       verified_ip,
       left(coalesce(verified_user_agent, ''), 90) AS geraet
FROM widget_requests
WHERE verified_at IS NOT NULL
ORDER BY verified_at DESC
LIMIT 100;


-- ── 2. Die verdaechtigen: schneller als zwei Sekunden ───────────────────
-- Unter zwei Sekunden hat niemand gelesen, verstanden und gedrueckt.

SELECT id, email, verify_sent_at, verified_at,
       round(extract(epoch FROM (verified_at - verify_sent_at))) AS sekunden,
       verified_ip,
       left(coalesce(verified_user_agent, ''), 120) AS geraet
FROM widget_requests
WHERE verified_at IS NOT NULL
  AND verify_sent_at IS NOT NULL
  AND verified_at - verify_sent_at < interval '2 seconds'
ORDER BY verified_at DESC;


-- ── 3. Der konkrete Fall vom 16.08.2026, 16:12:09 ───────────────────────
-- Zeitzone beachten: verified_at steht in UTC, 16:12:09 war Ortszeit.
-- Deshalb ein grosszuegiges Fenster statt einer Punktabfrage.

SELECT id, email, website_url,
       verify_sent_at, verified_at,
       round(extract(epoch FROM (verified_at - verify_sent_at))) AS sekunden,
       verified_ip, verified_user_agent
FROM widget_requests
WHERE verified_at BETWEEN timestamp '2026-08-16 12:00:00'
                      AND timestamp '2026-08-16 20:00:00'
ORDER BY verified_at;


-- ── 4. Womit wird ueberhaupt bestaetigt? ────────────────────────────────
-- Wiederholt sich ein Geraet ueber verschiedene Empfaenger hinweg, ist es
-- keins der Empfaenger, sondern eine Maschine dazwischen.

SELECT left(coalesce(verified_user_agent, '(keines)'), 70) AS geraet,
       count(*)                                            AS bestaetigungen,
       count(DISTINCT email)                               AS verschiedene_adressen,
       min(verified_at)                                    AS zuerst,
       max(verified_at)                                    AS zuletzt
FROM widget_requests
WHERE verified_at IS NOT NULL
GROUP BY 1
ORDER BY 2 DESC;


-- ── 5. Und dieselbe Frage fuer den Marketing-Opt-in ─────────────────────
-- Hier wiegt es schwerer: Bestaetigt ist die Adresse, eingewilligt hat man
-- in Werbung. Eine vom Scanner erteilte Einwilligung ist keine.

SELECT id, email, consent_marketing, consent_at, confirmed_at,
       round(extract(epoch FROM (confirmed_at - verify_sent_at))) AS sekunden_nach_mail,
       verified_ip
FROM widget_requests
WHERE confirmed_at IS NOT NULL
ORDER BY confirmed_at DESC
LIMIT 50;

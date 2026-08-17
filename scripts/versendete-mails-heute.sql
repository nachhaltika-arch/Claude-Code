-- Wer hat heute eine E-Mail von uns bekommen?
-- ===========================================
-- Angelegt 2026-08-17 wegen des Versands aus `services/sequence_runner.py`.
--
-- Quelle ist die Tabelle `email_logs`. Zwei Hinweise dazu:
--
--   1. Die Empfängeradresse steht je nach Schreiber in `to_email` ODER in
--      `recipient`. Der Sequenz-Runner schreibt `to_email`, ältere Pfade
--      schreiben `recipient`. Die Abfragen fassen beides zusammen.
--   2. `status` sagt nur, ob der Versand angenommen wurde — nicht, ob die
--      Mail zugestellt wurde. Die Zustellung steht in Brevo unter
--      Transactional → Logs. Für eine Aufarbeitung zählt Brevo, hier steht,
--      was das System versucht hat.
--
-- „Heute" heißt hier ab Mitternacht deutscher Zeit.


-- ── 1. Die Liste: welcher Betrieb, welche Adresse, welche Mail ──────────

SELECT
    l.company_name                              AS betrieb,
    coalesce(e.to_email, e.recipient)           AS empfaenger,
    l.website_url                               AS website,
    l.lead_source                               AS herkunft,
    l.status                                    AS lead_status,
    e.template_key                              AS vorlage,
    e.subject                                   AS betreff,
    e.status                                    AS versand,
    e.sent_at AT TIME ZONE 'Europe/Berlin'      AS zeitpunkt
FROM email_logs e
LEFT JOIN leads l ON l.id = e.lead_id
WHERE e.sent_at >= (current_date AT TIME ZONE 'Europe/Berlin')
ORDER BY e.sent_at;


-- ── 2. Überblick: wie viele, welche Vorlage, erfolgreich oder nicht ─────

SELECT
    e.template_key                        AS vorlage,
    e.status                              AS versand,
    count(*)                              AS anzahl,
    min(e.sent_at AT TIME ZONE 'Europe/Berlin') AS erste,
    max(e.sent_at AT TIME ZONE 'Europe/Berlin') AS letzte
FROM email_logs e
WHERE e.sent_at >= (current_date AT TIME ZONE 'Europe/Berlin')
GROUP BY 1, 2
ORDER BY 3 DESC;


-- ── 3. Nur die Werbestrecke, nach Herkunft der Adresse ──────────────────
-- Entscheidend für die Bewertung: Wer über `landing_audit`, `domain_import`
-- oder `hwk` hereinkam, hat einer Werbestrecke nicht zugestimmt.

SELECT
    l.lead_source                     AS herkunft,
    count(*)                          AS mails,
    count(DISTINCT e.lead_id)         AS betriebe
FROM email_logs e
LEFT JOIN leads l ON l.id = e.lead_id
WHERE e.sent_at >= (current_date AT TIME ZONE 'Europe/Berlin')
  AND e.template_key LIKE 'sequence_step_%'
GROUP BY 1
ORDER BY 2 DESC;


-- ── 4. Der ganze Vorfall, nicht nur heute ───────────────────────────────
-- Die Strecke läuft stündlich und hat drei Stufen über zehn Tage. Für die
-- Aufarbeitung zählt der gesamte Zeitraum, nicht der heutige Tag.

SELECT
    date_trunc('day', e.sent_at AT TIME ZONE 'Europe/Berlin')::date AS tag,
    e.template_key                    AS vorlage,
    e.status                          AS versand,
    count(*)                          AS anzahl
FROM email_logs e
WHERE e.template_key LIKE 'sequence_step_%'
GROUP BY 1, 2, 3
ORDER BY 1 DESC, 2;


-- ── 5. Wer steht noch auf der Liste? (noch nicht versendet) ─────────────
-- Diese Betriebe bekommen beim nächsten stündlichen Lauf eine Mail,
-- solange `sequence_paused` nicht gesetzt ist.

SELECT
    l.id, l.company_name, l.email, l.lead_source, l.status,
    l.sequence_step                   AS bisherige_stufe,
    l.sequence_last_sent AT TIME ZONE 'Europe/Berlin' AS zuletzt
FROM leads l
WHERE l.sequence_active = true
  AND l.sequence_paused IS DISTINCT FROM true
  AND l.email IS NOT NULL AND l.email <> ''
ORDER BY l.sequence_last_sent NULLS FIRST;

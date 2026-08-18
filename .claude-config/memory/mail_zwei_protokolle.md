---
name: mail-zwei-protokolle
description: "Der Mailversand protokolliert in zwei Tabellen, die einander nicht kennen — email_logs und communications; deshalb ist 'wer hat was bekommen' keine Frage mit einer Antwort"
metadata: 
  node_type: memory
  type: project
  originSessionId: 465171c2-9876-4ba8-8832-f132c07da06a
  modified: 2026-08-17T15:22:54.296Z
---

**Es gibt zwei Versandprotokolle, und keines kennt das andere.**

| Tabelle | wer schreibt | was fehlt |
|---|---|---|
| `email_logs` | `services/sequence_runner.py` | alles aus dem Scheduler |
| `communications` | `_send_phase_email` (Scheduler) | alles aus den Sequenzen |

Der Netlify-Go-Live-Mailer schreibt in **keines** von beiden.

**Warum das teuer war:** Am 17.08.2026 meldete David, es gingen Mails an
Unternehmen ohne Vertrag. Ich prüfte `email_logs`, fand bei allen 61 Betrieben
null Zeilen und schloss daraus, es sei nichts versendet worden. Tatsächlich
bekam ein Betrieb seit 135 Tagen **täglich** eine Mail — protokolliert in
`communications`. Ich habe zweimal den falschen Sender beschuldigt, bevor ich
im richtigen Protokoll nachsah.

**Merksatz:** Bevor eine Aussage über versendete Mails getroffen wird, **beide**
Tabellen ansehen — und für die belastbare Antwort **Brevo → Transactional →
Logs**, denn nur dort steht, was tatsächlich zugestellt wurde. Die Tabellen
sagen bloß, was das System versucht hat.

Es gibt außerdem **keinen API-Endpunkt**, der `communications` ausliest.
`GET /api/leads/{id}/email-logs` liefert nur `email_logs`.

Abfragen liegen im Repo: `scripts/versendete-mails-heute.sql`.

Zusammenlegen der beiden Protokolle ist offen und steht in
[[resume-point-2026-08-17]].

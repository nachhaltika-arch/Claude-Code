# FEATURE 00: Brevo-Korrekturen (Vorarbeit)

**Warum zuerst?** Solange der falsche Absender im Code steht, gehen alle Automations-Mails
mit fremdem Namen raus. Und ohne `send_transactional_email` kann die Automation-Engine
später gar nichts verschicken. Diese Datei ist die Grundlage für alles Weitere.

**Repo:** nachhaltika-arch/Claude-Code · **Branch:** main
**Prompts:** 1 · **Deploy:** Backend (Render Manual Deploy) nach dem Prompt

---

## Vorher in Render eintragen (Environment Variables)

| Variable | Wert |
|---|---|
| `BREVO_SENDER_NAME` | KOMPAGNON Communications |
| `BREVO_SENDER_EMAIL` | (deine verifizierte Brevo-Absenderadresse) |

Ohne diese Variablen greifen die Standardwerte aus dem Code.

---

## Prompt 1 von 1 — Brevo-Service korrigieren und erweitern

```text
SICHERHEITSCHECK zuerst: git remote -v und git branch --show-current
Erwartet: nachhaltika-arch/Claude-Code und main. Sonst STOPPE und melde es.

ZIEL: Absender konfigurierbar machen, Mehrfach-Listen ermöglichen,
Transaktionsversand für die spätere Automation-Engine vorbereiten.

DATEI 1: backend/services/brevo_service.py
- In create_email_campaign den fest eingetragenen Absender
  {"name": "Silva Viridis", "email": "newsletter@silva-viridis.de"} ersetzen durch:
    sender_name  = os.environ.get("BREVO_SENDER_NAME", "KOMPAGNON Communications")
    sender_email = os.environ.get("BREVO_SENDER_EMAIL", "newsletter@kompagnon.de")
- Parameter list_id umbenennen in list_ids (erwartet eine Liste von IDs),
  recipients={"listIds": list_ids}
- Neue Methode send_transactional_email(to_email, to_name, subject, html_content,
  params=None, reply_to=None):
  nutzt sib_api_v3_sdk.TransactionalEmailsApi und SendSmtpEmail,
  Absender wie oben aus den Umgebungsvariablen,
  gibt bei Erfolg die messageId zurück, bei ApiException einen Fehlertext-String.
- Neue Methode unsubscribe_contact(email): setzt über ContactsApi den Kontakt
  auf emailBlacklisted=True, gibt True oder Fehlertext zurück.

DATEI 2: backend/routers/newsletter.py
- In send_campaign: ALLE gefundenen brevo_list_id sammeln (nicht nur brevo_list_rows[0])
  und als Liste an create_email_campaign(list_ids=...) übergeben.

Keine weiteren Dateien ändern. Keine bestehenden Endpunkte umbenennen.

Danach:
  git add -A
  git commit -m "fix: configurable Brevo sender, multi-list campaigns, transactional send"
  git push origin main

Melde: geänderte Dateien, Commit-Hash, Bestätigung Push auf main.
```

---

## Nach dem Prompt

1. Render → Backend-Service `claude-code-znq2` → **Manual Deploy**
2. Warten bis „Live"
3. Test: Im Newsletter-Bereich eine Testkampagne an dich selbst — Absender muss
   jetzt KOMPAGNON sein.

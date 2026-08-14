# FEATURE 02: Automation-Engine — Ausführungsmotor

**Was hier entsteht:** Der Teil, der tatsächlich sendet und wartet. Im Kern ist es
eine Warteschlange: Alle 5 Minuten schaut ein Hintergrundjob nach, welche Kontakte
„dran" sind, führt deren nächsten Schritt aus und trägt ein, wann es weitergeht.

**Repo:** nachhaltika-arch/Claude-Code · **Branch:** main
**Prompts:** 3 · **Voraussetzung:** Feature 00 und 01 sind deployed

---

## Prompt 1 von 3 — Schritt-Ausführung

```text
SICHERHEITSCHECK: git remote -v und git branch --show-current → Claude-Code / main, sonst STOPP.

ZIEL: Neue Datei backend/services/automation_executor.py.

Funktion execute_step(db, enrollment, step) -> dict mit
  {"next_step_id": int|None, "next_run_at": datetime|None, "result": str}

Behandelte step_type:

send_email
  config: {template_id, subject_override}
  → Kontaktdaten laden, Platzhalter ersetzen (Funktion aus Prompt 3),
    Abmeldelink anhängen, BrevoService.send_transactional_email aufrufen.
    Bei Fehler: Enrollment auf status='error', Log-Eintrag mit Fehlertext.

delay
  config: {mode: "duration"|"until_weekday", days, hours, weekday, time}
  → next_run_at berechnen, next_step_id = Folgeschritt

condition
  config: {field, operator, value}
    field: contact.<spalte> | lead.<spalte> | email.opened | email.clicked
    operator: equals, not_equals, contains, greater_than, less_than, is_empty, is_set
  → prüft die Bedingung und wählt als next_step_id den Kindschritt
    mit branch='yes' bzw. branch='no'

set_field       config: {table, field, value} → UPDATE auf newsletter_contacts oder leads
add_to_list     config: {list_id} → Eintrag in newsletter_contacts + Brevo-Liste
remove_from_list config: {list_id}
create_task     config: {title, assignee, due_in_days} → in bestehende Aufgaben-/Tasktabelle
                (prüfe zuerst per grep, wie Aufgaben im Projekt heißen; wenn keine
                 existiert, überspringen und im Log vermerken)
internal_notify config: {to_email, subject, body} → interne Mail, KEIN Abmeldelink
goal_check      → Enrollment auf status='goal_reached', Ablauf beenden

Jeder Schritt schreibt einen Eintrag in automation_logs
(enrollment_id, step_id, action=step_type, result, detail).

Ist kein Folgeschritt vorhanden: Enrollment auf status='completed', finished_at setzen.

  git add -A
  git commit -m "feat: automation step executor"
  git push origin main
```

---

## Prompt 2 von 3 — Hintergrund-Job und Ablaufsteuerung

```text
SICHERHEITSCHECK: git remote -v und git branch --show-current → Claude-Code / main, sonst STOPP.

VORAB: Sieh dir backend/automations/scheduler.py an und füge den neuen Job im
bestehenden APScheduler ein — KEINEN zweiten Scheduler starten.

ZIEL: Der Motor läuft von allein.

DATEI 1: backend/services/automation_runner.py
- Funktion run_due_enrollments():
    * SELECT aus automation_enrollments WHERE status='active'
      AND next_run_at <= now() LIMIT 200, sortiert nach next_run_at
    * je Eintrag:
      - Workflow laden; ist status != 'active' → überspringen
      - SENDEFENSTER prüfen (send_window): liegt jetzt außerhalb, next_run_at auf den
        nächsten erlaubten Zeitpunkt setzen und überspringen
      - ZIEL prüfen (goal_config): erreicht → status='goal_reached', beenden
      - UNTERDRÜCKUNG prüfen: Kontakt in suppression_list_ids oder abgemeldet
        (contact_consents.status='revoked') → status='cancelled', Log-Eintrag
      - sonst execute_step aufrufen und Ergebnis speichern
    * jeder Durchlauf in try/except, ein Fehler darf nicht alle anderen stoppen

DATEI 2: backend/automations/scheduler.py
- Neuen Job registrieren: run_due_enrollments, IntervalTrigger(minutes=5),
  id="automation_runner", max_instances=1, coalesce=True

DATEI 3: backend/routers/automation.py erweitern
  POST /run-now        nur Admin: run_due_enrollments() sofort ausführen (zum Testen)
  GET  /stats          Gesamtzahlen: aktive Workflows, laufende Enrollments,
                       heute gesendete Mails, Fehler letzte 24h

  git add -A
  git commit -m "feat: automation runner job with send window and goal handling"
  git push origin main
```

**Danach:** Backend deployen. Test über `/api/automation/run-now`, dann `/stats` prüfen.

---

## Prompt 3 von 3 — Personalisierung, Abmeldung, Double-Opt-in

```text
SICHERHEITSCHECK: git remote -v und git branch --show-current → Claude-Code / main, sonst STOPP.

ZIEL: Rechtssichere und personalisierte Mails.

DATEI 1: backend/services/email_personalization.py
- render_tokens(html, context) ersetzt Platzhalter im Format
  {{kontakt.vorname|Guten Tag}}  → Wert oder Ersatzwert nach dem senkrechten Strich
  Verfügbare Namensräume: kontakt.*, firma.*, lead.*, projekt.*, absender.*
- AVAILABLE_TOKENS: Liste für die Oberfläche (key + Beschreibung), damit man im Editor
  auswählen kann statt zu tippen.
- append_unsubscribe(html, token) hängt Abmeldelink und Impressumszeile an.
  Absenderdaten aus Umgebungsvariablen COMPANY_NAME, COMPANY_ADDRESS, COMPANY_IMPRINT_URL.

DATEI 2: backend/routers/public_consent.py, prefix "/api/public" OHNE Login
  POST /subscribe        Body: email, first_name, list_id, source, consent_text
                         → Eintrag in contact_consents (status='pending', doi_token
                           per secrets.token_urlsafe(32)), Bestätigungsmail über
                           BrevoService.send_transactional_email.
                           Antwort immer neutral ("Bitte E-Mail bestätigen"), auch wenn
                           die Adresse schon existiert (kein Adress-Ausspähen).
  GET  /confirm/{token}  → status='confirmed', confirmed_at, IP speichern,
                           Kontakt in newsletter_contacts + Brevo anlegen,
                           danach fire_trigger('newsletter_subscribed'),
                           HTML-Bestätigungsseite im KOMPAGNON-Design ausliefern
  GET  /unsubscribe/{token} → status='revoked', BrevoService.unsubscribe_contact,
                           alle aktiven Enrollments dieses Kontakts auf 'cancelled',
                           Bestätigungsseite ausliefern

Router in backend/main.py registrieren. Diese Endpunkte MÜSSEN ohne Login erreichbar sein.

  git add -A
  git commit -m "feat: personalization tokens, double opt-in and unsubscribe endpoints"
  git push origin main
```

**Danach:** Backend deployen. Neue Render-Variablen: `COMPANY_NAME`, `COMPANY_ADDRESS`,
`COMPANY_IMPRINT_URL`.

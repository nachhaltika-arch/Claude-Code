# FEATURE 01: Automation-Engine — Backend-Fundament

**Was hier entsteht:** Die Datenbank-Tabellen und die API, mit denen Workflows
angelegt, gespeichert und Kontakte aufgenommen werden. Noch läuft nichts von allein —
das kommt in Feature 02. Hier bauen wir das Regal, bevor wir es einräumen.

**Repo:** nachhaltika-arch/Claude-Code · **Branch:** main
**Prompts:** 3 (Teil 1 → 2 → 3) · **Deploy:** nach jedem Teil Backend deployen

---

## Prompt 1 von 3 — Datenbank-Tabellen

```text
SICHERHEITSCHECK: git remote -v und git branch --show-current
Erwartet: nachhaltika-arch/Claude-Code und main. Sonst STOPPE.

VORAB: Prüfe, wie Tabellen im Projekt angelegt werden (backend/database.py oder
ein migrations-Ordner) und folge exakt diesem bestehenden Muster.
Orientiere dich beim DB-Zugriffsstil an backend/routers/newsletter.py.

ZIEL: Sechs neue PostgreSQL-Tabellen für die E-Mail-Automation.

1) automation_workflows
   id, name, description, status TEXT DEFAULT 'draft' (draft|active|paused),
   trigger_type TEXT, trigger_config JSONB DEFAULT '{}',
   goal_config JSONB DEFAULT '{}', allow_reenrollment BOOLEAN DEFAULT false,
   suppression_list_ids INTEGER[] DEFAULT '{}',
   send_window JSONB DEFAULT '{}',            -- z.B. {"days":[1,2,3,4,5],"from":"09:00","to":"17:00"}
   consent_basis TEXT DEFAULT 'opt_in',       -- opt_in | bestandskunde | transaktional
   created_at, updated_at TIMESTAMPTZ DEFAULT now()

2) automation_steps
   id, workflow_id INT REFERENCES automation_workflows ON DELETE CASCADE,
   parent_step_id INT NULL, branch TEXT DEFAULT 'main' (main|yes|no),
   position INT DEFAULT 0, step_type TEXT, config JSONB DEFAULT '{}',
   canvas_x REAL DEFAULT 0, canvas_y REAL DEFAULT 0, created_at

3) automation_enrollments
   id, workflow_id INT, contact_id INT NULL, lead_id INT NULL,
   current_step_id INT NULL, status TEXT DEFAULT 'active'
   (active|completed|goal_reached|cancelled|error),
   next_run_at TIMESTAMPTZ, enrolled_at TIMESTAMPTZ DEFAULT now(), finished_at TIMESTAMPTZ
   INDEX auf (status, next_run_at) und auf workflow_id

4) automation_logs
   id, enrollment_id INT, step_id INT NULL, action TEXT, result TEXT,
   detail JSONB DEFAULT '{}', created_at TIMESTAMPTZ DEFAULT now()

5) email_templates
   id, name, subject, preheader, html_content TEXT, design_json JSONB DEFAULT '{}',
   template_type TEXT DEFAULT 'automation' (marketing|automation), created_at, updated_at

6) contact_consents
   id, contact_id INT, email TEXT, status TEXT DEFAULT 'pending'
   (pending|confirmed|revoked), source TEXT, doi_token TEXT UNIQUE,
   consent_text TEXT, consent_ip TEXT, requested_at, confirmed_at, revoked_at
   INDEX auf email

Danach:
  git add -A
  git commit -m "feat: add automation engine database tables"
  git push origin main

Melde: Dateipfad der Migration, Commit-Hash.
```

**Danach:** Render → Backend → Manual Deploy. In den Logs prüfen, dass keine SQL-Fehler stehen.

---

## Prompt 2 von 3 — CRUD-API für Workflows, Schritte und Vorlagen

```text
SICHERHEITSCHECK: git remote -v und git branch --show-current → Claude-Code / main, sonst STOPP.

ZIEL: Neue Datei backend/routers/automation.py mit prefix "/api/automation".
Authentifizierung wie in backend/routers/newsletter.py (get_current_user).
DB-Zugriff im selben Stil wie newsletter.py.

WORKFLOWS
  GET    /workflows                 Liste, je Workflow zusätzlich:
                                    steps_count, active_enrollments, completed_count
  POST   /workflows                 anlegen (name, description, trigger_type,
                                    trigger_config, consent_basis)
  GET    /workflows/{id}            Workflow inkl. aller Schritte (nach position sortiert)
  PATCH  /workflows/{id}            Felder aktualisieren
  DELETE /workflows/{id}            löschen (Schritte per CASCADE)
  POST   /workflows/{id}/activate   Status auf 'active'; vorher validieren:
                                    mind. 1 Schritt vorhanden, trigger_type gesetzt,
                                    consent_basis gesetzt. Sonst 400 mit Klartext-Grund.
  POST   /workflows/{id}/pause      Status auf 'paused'

SCHRITTE (Canvas speichert alles auf einmal)
  PUT    /workflows/{id}/steps      Body: Array von Schritten
                                    (temp_id, parent_temp_id, branch, position,
                                     step_type, config, canvas_x, canvas_y)
                                    → in einer Transaktion alte Schritte löschen,
                                      neue einfügen, temp_id auf echte IDs mappen,
                                      parent_step_id korrekt setzen.
                                    Rückgabe: gespeicherte Schritte mit echten IDs.

VORLAGEN
  GET/POST/PATCH/DELETE /templates   für email_templates

Erlaubte step_type-Werte (nur validieren, noch nicht ausführen):
  send_email, delay, condition, set_field, add_to_list, remove_from_list,
  create_task, internal_notify, goal_check

Router in backend/main.py registrieren.

  git add -A
  git commit -m "feat: automation workflow and template CRUD API"
  git push origin main
```

**Danach:** Backend deployen. Test: `/docs` im Backend öffnen, Endpunkte müssen erscheinen.

---

## Prompt 3 von 3 — Aufnahme (Enrollment) und Auslöser-Register

```text
SICHERHEITSCHECK: git remote -v und git branch --show-current → Claude-Code / main, sonst STOPP.

ZIEL: Kontakte in Workflows aufnehmen — manuell und automatisch bei Ereignissen.

DATEI 1: backend/services/automation_triggers.py
- Konstante AVAILABLE_TRIGGERS: Liste von Dicts mit key, label, description, config_schema.
  Enthält mindestens:
    form_submitted, newsletter_subscribed, audit_completed, audit_score_below,
    lead_created, lead_stage_changed, project_phase_changed, golive_completed,
    date_offset (X Tage nach einem Datumsfeld), manual
- Funktion fire_trigger(db, trigger_key, contact_id=None, lead_id=None, payload=None):
    * sucht alle automation_workflows mit status='active' und passendem trigger_type
    * prüft trigger_config gegen payload (z.B. score < Schwellwert)
    * EINWILLIGUNGSPRÜFUNG: bei consent_basis='opt_in' muss in contact_consents ein
      Eintrag mit status='confirmed' zur E-Mail existieren — sonst NICHT aufnehmen,
      stattdessen automation_logs-Eintrag mit result='skipped_no_consent'
    * prüft Unterdrückungslisten und allow_reenrollment (kein Doppel-Enrollment,
      wenn bereits ein aktives besteht)
    * legt automation_enrollments an: current_step_id = erster Schritt,
      next_run_at = jetzt
- Funktion enroll_contact(db, workflow_id, contact_id) für manuelle Aufnahme,
  mit denselben Prüfungen.

DATEI 2: backend/routers/automation.py erweitern
  GET  /triggers                                AVAILABLE_TRIGGERS zurückgeben
  GET  /workflows/{id}/enrollments              Liste mit Kontaktname, Status, Schritt
  POST /workflows/{id}/enroll                   Body: contact_ids[] → manuelle Aufnahme
  POST /enrollments/{id}/cancel                 Status auf 'cancelled'
  GET  /enrollments/{id}/logs                   Protokoll aus automation_logs

Noch KEINE Ausführung einbauen — nur Aufnahme. Ausführung kommt in Feature 02.

  git add -A
  git commit -m "feat: automation trigger registry and enrollment endpoints"
  git push origin main
```

**Danach:** Backend deployen.

# FEATURE 05: Anmelde-Snippet für Netlify-Kundenwebsites

**Warum das nötig ist:** Eure Kundenseiten sind statisches HTML auf Netlify — dort läuft
keine Datenbank. Damit Formulare und Newsletter-Anmeldungen von diesen Seiten in KAS
ankommen und Automationen auslösen, braucht jede Seite ein kleines Skript, das die
Daten an euer Backend meldet. Genau so läuft es bei euch schon mit Umami.

**Repo:** nachhaltika-arch/Claude-Code · **Branch:** main
**Prompts:** 2 · **Voraussetzung:** Feature 02 Prompt 3 ist deployed (Double-Opt-in)

---

## Prompt 1 von 2 — Website-Schlüssel und öffentlicher Empfangs-Endpunkt

```text
SICHERHEITSCHECK: git remote -v und git branch --show-current → Claude-Code / main, sonst STOPP.

ZIEL: Jede Kundenwebsite bekommt einen eigenen Schlüssel und darf damit
Formulardaten an KAS senden.

DATENBANK — neue Tabelle site_keys
  id, project_id INT, customer_name TEXT, site_key TEXT UNIQUE,
  allowed_origin TEXT,          -- z.B. https://kunde.de
  active BOOLEAN DEFAULT true, created_at
  Ein zweiter Eintrag pro Projekt ist nicht erlaubt (UNIQUE auf project_id).

DATEI 1: backend/routers/public_forms.py, prefix "/api/public", OHNE Login
  POST /form/{site_key}
    Body: form_type ("contact" | "newsletter"), fields (JSON), page_url,
          consent_checked (bool), consent_text (string)
    Ablauf:
      1. site_key prüfen, active=true, sonst 404 (keine Details verraten)
      2. Origin-Header gegen allowed_origin prüfen, sonst 403
      3. Einfache Missbrauchsbremse: max. 10 Absendungen pro IP und Stunde
      4. Honeypot-Feld "website" — ist es gefüllt, still mit 200 antworten
         und NICHTS speichern (Spam-Bot)
      5. form_type="contact": Lead bzw. Kommunikationseintrag im Projekt anlegen,
         danach fire_trigger('form_submitted', ...)
      6. form_type="newsletter": nur zulässig wenn consent_checked=true,
         sonst 400. Danach den Double-Opt-in-Ablauf aus /api/public/subscribe
         starten (Funktion wiederverwenden, nicht kopieren)
      7. consent_text, IP und Zeitpunkt in contact_consents protokollieren
  CORS: für diese Route Anfragen von beliebigen Origins zulassen, da sie
  von Kundendomains kommen. Bestehende CORS-Einstellungen für die übrigen
  Routen NICHT lockern.

DATEI 2: backend/routers/automation.py erweitern
  GET  /site-keys                 Liste aller Schlüssel mit Projektbezug
  POST /site-keys                 Body: project_id, allowed_origin
                                  → site_key per secrets.token_urlsafe(16) erzeugen
  PATCH /site-keys/{id}           allowed_origin ändern, aktivieren/deaktivieren

Router in backend/main.py registrieren.

  git add -A
  git commit -m "feat: site keys and public form endpoint for Netlify sites"
  git push origin main
```

**Danach:** Backend deployen.

---

## Prompt 2 von 2 — Snippet erzeugen und in den HTML-Export einbauen

```text
SICHERHEITSCHECK: git remote -v und git branch --show-current → Claude-Code / main, sonst STOPP.

VORAB: Suche per grep, wo der HTML-Export nach Netlify erzeugt wird
(Stichworte: netlify, deploy, export, zip). Melde den Dateipfad, bevor du änderst.

DATEI 1: backend/services/site_snippet.py
- Funktion build_snippet(site_key, backend_url) -> str
  Erzeugt ein eigenständiges <script>-Tag ohne externe Abhängigkeiten, das:
    * beim Laden alle Formulare mit dem Attribut data-kompagnon="contact"
      bzw. data-kompagnon="newsletter" sucht
    * deren Absenden abfängt und die Felder per fetch an
      {backend_url}/api/public/form/{site_key} sendet
    * ein verstecktes Honeypot-Feld namens "website" einfügt
    * bei Newsletter-Formularen prüft, ob die Einwilligungs-Checkbox gesetzt ist,
      und consent_text aus dem Label der Checkbox mitschickt
    * bei Erfolg eine Dankesmeldung im Formular anzeigt, bei Fehler eine
      Fehlermeldung — alles auf Deutsch, ohne Weiterleitung
    * KEINE Cookies setzt und KEINE Seitenaufrufe trackt (das macht Umami)
- Funktion build_form_html(form_type) -> str
  Fertiger HTML-Block zum Einfügen: Kontaktformular bzw. Newsletter-Anmeldung
  im KOMPAGNON-Design (#008EAA, #004F59, #FAE600, Noto Sans), mit
  Einwilligungs-Checkbox und Link zur Datenschutzerklärung.

DATEI 2: Export-Stelle erweitern
- Vor dem Export prüfen, ob für das Projekt ein site_key existiert; wenn nicht,
  automatisch erzeugen.
- Das Snippet direkt vor </body> jeder exportierten HTML-Datei einfügen.
- Falls das Snippet bereits vorhanden ist (Kennzeichnung per Kommentar
  <!-- kompagnon-forms -->), NICHT doppelt einfügen.

DATEI 3: backend/routers/automation.py
  GET /site-keys/{id}/snippet    → gibt Snippet-Code und Formular-Bausteine
                                   als Text zum Kopieren zurück

DATEI 4: frontend — im Projektbereich einen Abschnitt "Website-Formulare":
  zeigt den Schlüssel, das Snippet mit Kopieren-Button, die erlaubte Domain
  (änderbar) und die letzten 20 eingegangenen Absendungen.

  git add -A
  git commit -m "feat: generate and inject form snippet into Netlify HTML export"
  git push origin main
```

**Danach:** Backend und Frontend deployen.

---

## Testablauf nach Fertigstellung

1. Projekt öffnen → Abschnitt „Website-Formulare" → Schlüssel wird erzeugt
2. Erlaubte Domain eintragen (die spätere Kundendomain)
3. Website exportieren → im HTML-Code muss vor `</body>` das Snippet stehen
4. Auf Netlify hochladen, Formular absenden
5. In KAS erscheint der Eintrag; bei Newsletter kommt die Bestätigungsmail
6. Erst nach Klick auf den Bestätigungslink startet die Willkommens-Automation

# FEATURE 03: Visueller Workflow-Builder (Canvas)

**Was hier entsteht:** Der Teil, den du täglich siehst — eine Fläche, auf der du
Kästchen ziehst und verbindest, genau wie bei HubSpot. Technisch nutzen wir die
Bibliothek **React Flow**; sie liefert Ziehen, Zoomen und Verbindungslinien fertig mit.

**Repo:** nachhaltika-arch/Claude-Code · **Branch:** main
**Prompts:** 3 · **Voraussetzung:** Feature 01 und 02 sind deployed
**Deploy:** Frontend-Service auf Render nach jedem Teil

---

## Prompt 1 von 3 — Bibliothek, Workflow-Liste, Anlege-Dialog

```text
SICHERHEITSCHECK: git remote -v und git branch --show-current → Claude-Code / main, sonst STOPP.

VORAB: Sieh dir frontend/src/components/Newsletter.tsx an und übernimm exakt
Dateiendung (.tsx), Import-Stil, API-Client und Tailwind-Klassen dieses Bereichs.

SCHRITT 1: Im Ordner frontend ausführen: npm install reactflow
(Version 11, die mit dem Import "reactflow" arbeitet.)

SCHRITT 2: Neue Datei frontend/src/components/AutomationList.tsx
- Überschrift "Automationen", Button "Neue Automation"
- Kennzahlenkarten oben: Aktive Automationen, Laufende Kontakte,
  Heute gesendet, Fehler 24h (aus GET /api/automation/stats)
- Tabelle aller Workflows aus GET /api/automation/workflows mit Spalten:
  Name, Auslöser (Klartext-Label), Status-Chip
  (Entwurf grau / Aktiv grün / Pausiert gelb), Schritte, laufende Kontakte,
  abgeschlossen, Aktionen (Bearbeiten, Aktivieren/Pausieren, Löschen)
- Dialog "Neue Automation": Feld Name, Feld Beschreibung,
  Auswahl Auslöser aus GET /api/automation/triggers (Karten mit Titel + Erklärung),
  Pflichtauswahl Einwilligungsgrundlage:
    "Einwilligung liegt vor (Double-Opt-in)" | "Bestandskunde (§7 Abs.3 UWG)"
    | "Transaktional (kein Werbeinhalt)"
    mit Hinweistext: "Ohne dokumentierte Einwilligung sendet die Engine nicht."
  → POST /api/automation/workflows, danach in den Canvas springen

SCHRITT 3: Bereich in die Navigation einhängen — bevorzugt als Inhalt des bereits
vorhandenen Tabs "Automationen" in Newsletter.tsx.

Farben: #008EAA primär, #004F59 dunkel, #FAE600 Akzent, Schrift Noto Sans.

  git add -A
  git commit -m "feat: automation workflow list and creation dialog"
  git push origin main
```

**Danach:** Frontend auf Render deployen.

---

## Prompt 2 von 3 — Der Canvas selbst

```text
SICHERHEITSCHECK: git remote -v und git branch --show-current → Claude-Code / main, sonst STOPP.

ZIEL: Neue Datei frontend/src/components/AutomationCanvas.tsx mit React Flow.

AUFBAU
- Links: Werkzeugleiste mit ziehbaren Bausteinen, gruppiert:
    Senden      → E-Mail senden
    Warten      → Verzögerung
    Logik       → Wenn/Dann-Verzweigung, Ziel erreicht
    Daten       → Feld setzen, Zu Liste hinzufügen, Von Liste entfernen
    Intern      → Aufgabe erstellen, Team benachrichtigen
- Mitte: React-Flow-Fläche mit Hintergrundraster, Zoom-Steuerung und Minimap
- Oben rechts: Buttons Speichern, Aktivieren/Pausieren, Zurück zur Liste

KNOTEN
- Auslöser-Knoten ganz oben, fest, nicht löschbar, zeigt das Auslöser-Label
- Aktions-Knoten: eigenes Design mit Symbol, Titel, Kurzbeschreibung der Konfiguration
  (z.B. "Warten: 3 Tage"), Löschen-Symbol
- Wenn/Dann-Knoten: ZWEI Ausgänge, beschriftet "Ja" (grün) und "Nein" (rot)
- Klick auf einen Knoten öffnet das Konfigurationspanel (Prompt 3)

SPEICHERN
- Knoten und Kanten in das Format von PUT /api/automation/workflows/{id}/steps umrechnen:
  temp_id = Knoten-ID, parent_temp_id = Quellknoten der eingehenden Kante,
  branch = 'yes'|'no' bei Verzweigungen sonst 'main',
  position = Reihenfolge, canvas_x/canvas_y = Knotenposition
- Beim Laden aus GET /api/automation/workflows/{id} den umgekehrten Weg gehen
- Vor dem Speichern prüfen: keine losen Knoten ohne Verbindung, keine Kreise.
  Bei Problem: verständliche deutsche Fehlermeldung, nicht speichern.

KEINE localStorage- oder sessionStorage-Aufrufe verwenden.

  git add -A
  git commit -m "feat: visual automation canvas with react flow"
  git push origin main
```

**Danach:** Frontend deployen.

---

## Prompt 3 von 3 — Konfigurationspanel und Auswertung

```text
SICHERHEITSCHECK: git remote -v und git branch --show-current → Claude-Code / main, sonst STOPP.

ZIEL: Neue Datei frontend/src/components/AutomationStepPanel.tsx —
ein Panel rechts, das sich beim Klick auf einen Knoten öffnet.

FORMULARE JE SCHRITT-TYP
send_email        Vorlage wählen (GET /api/automation/templates),
                  Betreff überschreiben, Vorschau-Button,
                  Liste der Platzhalter zum Einfügen per Klick
delay             Umschalter "Dauer" (Tage/Stunden) oder
                  "Bis Wochentag + Uhrzeit"
condition         Feld-Auswahl, Operator-Auswahl, Wert;
                  Vorschautext in Klartext: "Wenn Gewerk gleich Dachdecker"
set_field         Tabelle, Feld, Wert
add_to_list /
remove_from_list  Listen-Auswahl aus GET /api/newsletter/lists
create_task       Titel, Zuständiger, Fällig in X Tagen
internal_notify   Empfängeradresse, Betreff, Text
goal_check        Hinweis: "Kontakt verlässt die Automation, wenn er hier ankommt"

WEITERE ERGÄNZUNGEN
- Einstellungs-Dialog des Workflows: Sendefenster (Wochentage + Von/Bis),
  Wiederaufnahme erlauben ja/nein, Unterdrückungslisten, Ziel
- Reiter "Kontakte" im Canvas: GET /api/automation/workflows/{id}/enrollments,
  Tabelle mit Name, aktuellem Schritt, Status, nächster Ausführung,
  Button "Abbrechen" je Zeile
- Klick auf eine Zeile: Protokoll aus GET /api/automation/enrollments/{id}/logs
  als Zeitstrahl
- Knoten im Canvas zeigen kleine Zahl: wie viele Kontakte diesen Schritt passiert haben

  git add -A
  git commit -m "feat: automation step configuration panel and enrollment view"
  git push origin main
```

**Danach:** Frontend deployen.

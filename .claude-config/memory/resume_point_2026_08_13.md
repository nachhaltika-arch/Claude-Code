---
name: resume-point-2026-08-13
description: "Stand 2026-08-13 — Stufe A, B und C-Phase-1 gebaut; offen nur die Qualitätsschleife über die Netlify-Vorschau"
metadata: 
  node_type: memory
  type: project
  originSessionId: cd0336bc-9108-4cbe-9f61-7419d1ccca53
  modified: 2026-08-13T18:40:41.581Z
---

**Stufe C, Phase 1 ist gebaut** (`b72848f`): „✨ Seite komponieren" im
Wireframe-Editor schlägt die **Abfolge** vor (welche Sections, welche
Reihenfolge, ein Satz Auftrag je Section) — `services/page_composer.py`, auf
Sonnet, weil es Auswahl und Reihenfolge ist. Das Markup je Section schreibt
danach Stufe B auf Opus. Bewusst zwei Phasen: eine ganze Seite in einem Aufruf
wären bis zu 18 Sections Markup in einer Antwort, beim kleinsten Formfehler
ganz verloren. Regeln C0 (nicht leer), C1 (nur freigegebene Blöcke), C2 (nie
zweimal derselbe Block hintereinander). Scharfer Lauf: Startseite 18 Sections
in 26 s, Leistungsseite 15 in 24 s, keine Wiederholung, Pflicht-Sections der
Conversion-Spec abgedeckt.

**Offen von Stufe C:** die Qualitätsschleife — Netlify-Vorschau deployen, dann
den eigenen 38-Kriterien-Audit gegen diese URL laufen lassen (~4 h). Alle Teile
existieren, der Weg ist seit „Auf die Seite übernehmen" durchgehend.

**Stufe B ist gebaut** (`cad9dba`): Ein Block lässt sich im Wireframe-Editor
für einen Kunden umschreiben — Detail-Panel → „Für diesen Kunden umschreiben".
Regeln: derselbe `data-block`-Slug, dieselben Slots (weglassen ja, umbenennen
nein = Regel B2), derselbe Vertrag, eine Reparaturrunde. Gespeichert wird als
`WireframeBlock.html_override`; das Tor sitzt im `POST /wireframe` (422 mit
Verstößen), nicht nur im Erzeuger — der Wireframe-Editor zeigt abgelehnte Saves
jetzt an, vorher gingen sie in die Konsole. Scharfer Lauf: drei Blöcke, alle im
ersten Wurf konform, 23–29 s, echt umgebaut statt abgeschrieben (der
Briefing-Hinweis „viele ältere Kunden — Telefonnummer sichtbar" kam in allen
drei an).

**Offen bei B:** Reicht „Vertrag bestanden" als Freigabe je Kunde, oder braucht
jede Variante einen Blick? Heute: dein Blick, das Panel zeigt die Vorschau und
ohne Übernehmen passiert nichts.

Stufe A des Claude-Design-Konzepts ist fertig und liegt auf `staging`:
Vertrag + Freigabe-Tor (`73c4822`, `4276676`, `511e22c`), Oberfläche
(`8681d44`), JSON-Absicherung (`61ceb0d`), Slot-Ergänzung (`38aafb5`),
Regel R5 (`d695795`).

**Der scharfe Lauf hat die Frage vor Stufe B beantwortet:** Zehn Blöcke gegen
die echte API, 8 von 9 angekommenen bestehen den Vertrag im ersten Wurf. Kein
einziger iframe, kein `id`, keine externe Quelle. Gescheitert ist einer am
JSON, nicht am Vertrag — sporadisch, `stop_reason=end_turn`. Der Vertrag ist
also keine Hürde für Stufe B.

**Marken-Override ist repariert** (`utils/brandOverride.js`, `5b508ff`): Er
kannte nur `gray-*`, während die Bibliothek 222× in `slate-*` malt; alle 45
Blöcke hatten mindestens eine ungedeckte Klasse. Jetzt volle Skala über alle
fünf Graustufen-Familien, Deckkraft und Verläufe; dunkler Kontext über drei
Custom Properties (naive Fassung: 449 KB CSS, diese: 114 KB). Test misst gegen
die 45 echten Blöcke.

**Der Zweig ist angeschlossen** (`8812f44`): „Auf die Seite übernehmen" in der
DesignView schreibt die Vorschau (Marken-CSS + Blöcke, gemeinsamer Baustein
`utils/pageHtml.js`) nach `sitemap_pages.mockup_html` → GrapesJS → Deploy.
Knopf statt Automatik, fragt vor dem Überschreiben. Daneben füllt weiter der
Agenten-Lauf dasselbe Feld — offen bleibt nur, ob beide Wege nebeneinander
bleiben (§ 9.5), nicht dringend.

**Zwei stille Fehler dabei gefunden:** Auf Pflichtseiten verwarf
`PUT /api/sitemap/pages/{id}` das Feld `mockup_html` und antwortete trotzdem
200. Und `steps_confirmed` fehlte im ORM-Modell (nur per rohem SQL in main.py
angelegt) — jede Schritt-Bestätigung ging verloren, `POST /confirm-step` meldete
`{"saved": true}`, und Wireframe/Style-Guide/Design blieben dauerhaft gesperrt.
Beides behoben und mit Tests abgesichert. Dieselbe Falle wie im Mai bei
`status`, siehe [[migration-trap-main-py]].

**Bekannte Schuld: leer** (`8e78631`). Die Kartenblöcke zeigen statt des
Google-Maps-iframes jetzt Ortsliste/Adresse und einen Link; `hero-centered` hat
ein neutrales Overlay; drei Blöcke malten ihre Icons in `stroke="#008EAA"` —
deshalb prüft R5 jetzt auch SVG-Attribute (`currentColor` ist die Lösung).

**Lehren, die sich zweimal bestätigt haben:**
- Regeln immer erst am Bestand messen. R5 war auf dem Papier „gegen
  style_guide-Token prüfen" — der Style-Guide führt aber Hex-Werte, keine
  Token, und die Marke wird über einen festen Satz gray-Klassen angewendet.
  Die tragfähige Regel heißt deshalb „nur neutrale Töne".
- Prompt-Konflikte kosten je eine Reparaturrunde: „Barrierefreiheit" gegen
  „kein `id`" ließ das Modell `aria-labelledby` bauen. Seit der Prompt den
  Ausweg nennt (`aria-label`), läuft derselbe Fall in einer Runde (130 s → 70 s).

**Lokale Testumgebung:** `kompagnon/.venv-local` (ignoriert). Damit laufen
Backend-Tests, jest und der volle Playwright-Lauf lokal; Anleitung steht in
`kompagnon/.gitignore`. Ersetzt CI nicht, siehe [[feedback-ci-pruefen-nach-push]].
Der scharfe Lauf braucht einen echten Schlüssel — er liegt in
`backend/.env.save`.

Konzept und Stand vollständig in `docs/claude-design-konzept-2026-08-13.md`.
Widget-Restpunkte liegen bei David, siehe [[resume-point-2026-08-12]].
Siehe auch [[migration-trap-main-py]] für Spaltenänderungen.

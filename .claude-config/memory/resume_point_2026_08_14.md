---
name: resume-point-2026-08-14
description: "Stand 2026-08-14 — scharfer Lauf gefahren, Assistent auf claude-sonnet-5 umgestellt; nächster Schritt braucht Render-Zugang, der fehlt"
metadata: 
  node_type: memory
  type: project
  modified: 2026-08-14T07:43:13.696Z
  originSessionId: 3d92565b-8fff-43d9-b150-99e01060374c
---

**Der scharfe Lauf ist gefahren, der Assistent läuft auf `claude-sonnet-5`.**
Zwei Commits auf `staging` (`5f7ee14`, `d3793b6`), CI vollständig grün. Was
gefunden und geändert wurde, steht im Repo:
`docs/projekt-assistent-anforderungen.md`, Abschnitte 9.4 (scharfer Lauf) und
9.5 (Modellvergleich) — dort steht Gemessenes, nicht Erinnertes.

**Der Blocker für den nächsten Schritt: Render-MCP antwortet `unauthorized`.**
Damit ist weder die Produktivdatenbank noch eine Umgebungsvariable erreichbar.
Der nächste offene Punkt — Ausgangswerte der Briefing-Abschlussquote für
Erfolgskriterium 4.3 — hängt genau daran. Ohne Zugang zuerst klären ist der
Punkt nicht bearbeitbar. Ein Render-API-Schlüssel löst es.

**So läuft ein scharfer Lauf** (das Skript lag im Scratchpad und ist weg):
Schlüssel aus `backend/.env.save` exportieren (die Zeile in `.env` ist leer,
das ist nicht dasselbe), Backend mit `.venv-local` auf 8000 starten — **erst
danach** seeden, siehe [[migration-trap-main-py]] —, `python -m tests.seed_e2e`,
dann über `POST /api/auth/login` ein Token holen und gegen
`POST /api/assistant/chat` fahren. Modell und Antwortdeckel kommen aus
`ASSISTENT_MODELL` / `ASSISTENT_MAX_TOKENS`, ein Modellvergleich braucht also
keinen Codeumbau mehr.

**Falle für jeden künftigen Modellwechsel:** Der Antwortdeckel begrenzt bei
denkenden Modellen Denken und Text gemeinsam. Die übrigen KI-Router (Sitemap,
Content, Branddesign, Component-Library) stehen weiter auf `claude-sonnet-4-6`,
mehrere rufen mit `max_tokens=800` auf — beim Umstellen reißt die Antwort sonst
mitten im Wort ab.

**Von David an diesem Tag aufgeworfen, nur aufgeschrieben:** Das Audit
unterstellt jeder Seite ein Handwerksgewerk und bewertete den Auftritt eines
politischen Kandidaten gegen den SHK-Maßstab. Offener Punkt 5 in
`docs/audit-anforderungen-2026-08-11.md`, § 6 — mit der Trennung von Erkennung
(Defekt) und Branchen-Ausweitung (Geschäftsentscheidung, berührt
[[niche-phase1]]). Nichts davon gebaut, keine Entscheidung gefallen.

**Ebenfalls offen, ungeklärt:** drei abweichende Mailadressen im System
(`hallo@kompagnon.eu` in `PricingSection.jsx`, `info@kompagnon.de` in
`config.py`, `noreply@kompagnon.group` als Brevo-Absender). `sales@kompagnon.eu`
kommt im Repo nirgends vor; ob sie im laufenden System steckt, war wegen des
Render-Blockers nicht prüfbar.

**Danach weiter offen:** echter Kunde durch Ausbau 1, dann Ausbau 2
(Projektbegleitung); Qualitätsschleife Stufe C, siehe
[[resume-point-2026-08-13]]; Widget-Restpunkte, siehe
[[resume-point-2026-08-12]].

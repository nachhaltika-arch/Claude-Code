---
name: resume-point-2026-08-18
description: "Stand 2026-08-18 — CI-Hänger behoben, zwölf blockierende KI-Aufrufe, UX-19 und UX-34 (Farbsystem), PR #42 produktiv gemerged, Deploy wartet jetzt auf den Dienst"
metadata: 
  node_type: memory
  type: project
  originSessionId: 37ff874d-ff57-46f1-bdf9-d4d2dab35d0d
  modified: 2026-08-18T10:00:12.280Z
---

**Ein Tag über Messen statt Schätzen.** Vier Themen, zehn Commits, PR #42 ist
produktiv.

## Der Tag der Reihe nach

**CI-Lauf #359 hing sechs Stunden.** `npx playwright install --with-deps`
antwortete nicht mehr; nichts wurde rot, und der **Deploy-Job wurde nie
erreicht**. In der ganzen `ci.yml` stand **kein einziges `timeout-minutes`**.
Jetzt drei Lagen: Zeitgrenze je Job (10–40), Zeitgrenze je Versuch in
`ci-retry.sh` (600s, wiederholt statt abzuwarten), apt ohne Rückfrage.
Nebenfund vom Test: `ZEITGRENZE=()` ist unter bash 3.2 mit `set -u` ein
Fehler — auf Davids Mac wäre das Skript sofort gestorben. Jetzt `env` als
wirkungsloser Vorspann.

**Zwölf statt neun blockierende KI-Aufrufe.** Ein AST-Durchlauf fand die zehn
direkten *und zwei über eine Zwischenebene* (`geo.analyze`,
`GeoGeneratorAgent.generate_all`, das das Modell zweimal ruft). Neu:
`services/ki_aufruf.frag_modell` als einziger Weg aus einer `async def`.
Sperre: `test_keine_ki_blockiert_die_schleife.py`, zwei Regeln, die zweite
transitiv. Siehe [[blockierte-ereignisschleife]].

**Danach der wichtigste Commit des Tages:** Nach dem Umbau standen 1191 Tests
grün — und **keiner führte eine der zwölf Funktionen aus**. Bei
`ai_evaluate_qa` wäre ein vergessenes `await` unsichtbar geblieben, weil sie
jeden Fehler abfängt. Zwei Dienstwege echt durchgespielt, Gegenprobe gemacht:
mit zurückgenommenem Umbau kommt der Zähler auf 0 von 5.

**UX-19 (Paket 7) war keine Gestaltungsfrage.** „Tool dunkel, Portal hell" war
eine Auslassung: Die Kundenseiten sind dem Farbsystem nie beigetreten.
Umgestellt; die Rechtsseiten (Impressum, Datenschutz, Barrierefreiheit) gab es,
aber **keine Adresse führte hin** — jetzt geroutet.

**UX-34: geschätzt 62, gemessen 140** Stellen weiße Schrift, die im
Dunkelmodus durchfällt, plus **46**, die in *beiden* Modi durchfallen — dort
war der Text nie lesbar. Dazu drei von vier Statustönen unter der Schwelle im
Hellmodus, und `[data-theme="light"]` führte ein viertes `--warn` (2.94).
Neue Werkzeuge: `utils/tokenwerte.js` (löst `var()`-Ketten je Modus auf),
`utils/weisseSchrift.test.js`, `styles/tokens.test.js`.

## Zwei Fehler von mir, beide lehrreich

1. **Ein Umbauskript veränderte Dateien während es sie durchsuchte** und
   schrieb an verschobenen Stellen. Zehn Dateien syntaktisch kaputt, **alle
   300 Tests grün** — sie lesen Dateien, statt sie zu übersetzen. Der Build
   fand es. Neu gemacht mit Änderungsliste von hinten nach vorn.
2. Beim Zurücksetzen habe ich vier eigene Dateien mit abgeräumt: In **zsh
   splittet `$VAR` in `for f in $VAR` nicht** — die Kopierschleife lief nie,
   `git checkout` danach schon.

Beides steht in [[feedback-am-gegenstand-pruefen]].

## PR #42 produktiv

31 Commits, 170 Dateien, von David gemerged (Dienstag, nicht Freitag — auf
seine Ansage; [[feedback-pr-only-fridays]] gilt weiter für *Vorschläge*).
Produktiv geprüft: `/health` ok, Kundenportal und Impressum im Dunkelmodus
live.

**Dabei der letzte Fund:** Render meldete `live` um 09:43:58, `/health` sagte
bis **09:48:32** noch `startup_complete: null`. Der Deploy-Job wartet jetzt
auf den Dienst selbst statt auf Renders Auskunft
(`test_ci_bereitschaft.py`). Siehe [[deploy-laeuft-ueber-ci]].

## Offen bei David

1. ~~Datenträger in Render~~ **erledigt 18.08. gegen 12:26 UTC**, gemeinsam
   im Dashboard (der Render-MCP ist in dieser Sitzung `unauthorized`).
   Datenträger 1 GB auf `/var/data`, `UPLOAD_ROOT=/var/data/uploads`.
   Am Dienst nachgewiesen: `df` zeigt `/dev/nvme17n1 … /var/data`, eigenes
   Dateisystem `True`, Schreibprobe bestanden. Vorher lagen **null Dateien**
   im flüchtigen Verzeichnis — es ging nichts verloren.
   **Preis dafür:** Ein Dienst mit Datenträger kann nicht mehr ohne
   Unterbrechung deployen; beim Anhängen war die Produktion **rund 1,5 Minuten
   nicht erreichbar**, und jeder künftige Deploy hat eine kurze Lücke.
2. Produktiv fehlen `STRIPE_SECRET_KEY`, `CMS_ENCRYPTION_KEY`
3. **Ein echter KI-Aufruf** (Briefing → Zielgruppenanalyse): Die zehn
   Router-Wege sind nur strukturell abgesichert
4. Datensätze: CDU-Ortsverband als „Dachdecker", `nachhaltika.denachhaltika.de`
5. **193 Stellen** weiße Schrift auf einer Fläche, die die Datei nicht nennt —
   gezählt, nicht geprüft

Prüfstand: **1197 Backend-, 300 Frontend-Tests**, CI grün auf `369`.
Voriger Stand [[resume-point-2026-08-17]].

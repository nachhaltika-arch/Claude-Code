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

## Nach dem Merge kam der längere Teil des Tages

**Akademie und Mobil, zum ersten Mal angesehen.** `/app/vertrieb` — die
Adresse aus der Mobilleiste — zeigte auf dem Desktop eine **leere Seite**
(`navigate()` im Render leitet nicht um). Die Mobil-Kacheln trugen **erfundene
Zahlen** („12 Leads", „Abonnement: Professional"), „Akademy" stand an neun
weiteren Stellen inklusive zweimal auf der Kundenurkunde, und auf der
Passwort-Seite prangte ein fremdes goldenes „HS". **Die Akademie hatte
überhaupt keinen Menüeintrag** — das hat David gefunden, nicht ich, nachdem
ich den Bereich zwei Stunden lang über die Adresszeile untersucht hatte.

**Beim Vergleich der zwei Kurseditoren (UX-42) fiel der schwerste Fund:** Es
liess sich **keine einzige Lektion anlegen** — 500 seit es den Endpunkt gibt,
`checklist_items_json` im Router, nicht im Modell. Der Modellabgleich fand
danach **zwölf Spalten**, die zugewiesen und still verworfen wurden
(Onboarding-Status, PageSpeed, Projektphase, Auftragsbestätigung).

**Drei Zugriffslöcher** (L-12 zog sie nach sich): Rolle `nutzer` sah den ganzen
Bestand, ein angemeldeter Kunde die ganze Kundenkartei (`usercards.py` samt
Alias-Routern war am 17.08. übersehen worden), und die Zeilenprüfung fragte
dasselbe Falsche. Alle drei nennen jetzt, **wer darf**.

**Geschlossen:** L-05 (halb — 14 von 16 Rechten sind weiter nur beschreibend,
und der Bildschirm sagt das jetzt), L-10 (eigenes Fehlerprotokoll), L-12,
L-13. Dazu UX-19, UX-34 bis UX-44.

**Die CI dreimal repariert:** Hänger (Zeitgrenzen), Abbruch durch Folge-Pushes
(`scripts/push-wenn-ruhig.sh` wartet jetzt), und der apt-Deadlock — `timeout`
tötet keine Enkelprozesse, das `apt-get` hielt die Sperre. Seitdem
`playwright install chromium` **ohne** `--with-deps`.

**Datenträger produktiv angehängt** (gemeinsam im Dashboard, Render-MCP war
`unauthorized`): 1 GB auf `/var/data`, `UPLOAD_ROOT` gesetzt, am Dienst
nachgewiesen. Preis: kein unterbrechungsfreier Deploy mehr.

## Morgen: L-34

Der Umzug nach Frankfurt, abgesprochen. `docs/umzug-backend-frankfurt.md` ist
um den Stand vom 18.08. ergänzt — vor allem: **Der Datenträger zieht nicht
mit** (heute null Dateien, morgen vorher zählen), die Service-IDs in den
Repository-Variablen ändern sich, und `/health` beweist mit
`uploads.dauerhaft`, ob der neue Datenträger wirklich hängt.

Prüfstand am Ende des Tages: **1248 Backend-, 323 Frontend-Tests**, CI grün
auf `391`, **26 Commits auf `staging`** seit PR #42.
Voriger Stand [[resume-point-2026-08-17]].

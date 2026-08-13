# Claude im Designbereich — Konzept und Stand

**Angelegt:** 2026-08-13 · **Zuletzt:** 2026-08-13 (Stufe A gebaut + Oberfläche)
**Frage:** Wie integrieren wir Claude in den Designbereich, um neue Homepages
zu entwickeln — statt GrapesJS oder zusätzlich?
**Verbunden:** `kas-pipeline-architecture.md` (04.05., Grundlage),
`conversion-spec-shk.md` (Pflichtinhalte), `niche_phase1.md` (Zielgruppe)

---

## 0. Stand in einem Absatz

Stufe A ist gebaut und liegt auf `staging` (Commits `73c4822`, `4276676`),
samt Oberfläche für Entwurf und Freigabe. Claude schreibt Bibliotheksblöcke,
ein prüfbarer Vertrag steht davor, ohne Freigabe erreicht kein erzeugter Block
eine Kundenseite — und wer einen Entwurf vor sich hat, liest jetzt auch, woran
es liegt. Der scharfe Lauf gegen die echte API ist gemacht: **8 von 9
angekommenen Blöcken bestehen den Vertrag im ersten Wurf**, gescheitert ist
einer am JSON statt am Vertrag (behoben). Auch die Marken-Regel R5 steht jetzt
im Prüfer, und der Marken-Override deckt die ganze Graustufen-Skala ab (§ 4.2).
Beim Bauen kam allerdings heraus, dass dieser Zweig gar nicht auf der
Kundenseite endet (§ 4.3) — das ist die offene Entscheidung vor Stufe B.
Stufe B und C sind entworfen, nicht gebaut.

---

## 1. Ausgangslage — was heute wirklich steht

Die Pipeline von Mai ist weiter gebaut, als das Dokument vermuten lässt:

| Stufe | Stand | Wo |
|---|---|---|
| 1 Analyse | ✅ | `routers/audit.py`, 38 Kriterien |
| 2 Sitemap | ✅ **mit KI** | `routers/sitemap.py`, 1.680 Zeilen |
| 3 Wireframe | ✅ **mit KI** | `routers/component_library.py`, Block-Auswahl → `projects.wireframe_data` |
| 4 Style-Guide | ✅ | `routers/branddesign.py` |
| 5 Inhalt | ✅ teilweise | `generate-copy` je Section, `agents/content_writer.py` |
| 6 Deploy | ✅ | `services/netlify_service.py` |
| Bearbeitung | ✅ | GrapesJS je Seite, `kas_gjs_data` |

Es fehlt also **kein Werkzeug**. Was fehlt, ist etwas anderes.

## 2. Der Befund: Die KI wählt aus, sie gestaltet nicht

Der Wireframe-Generator bekommt das Briefing, die Sitemap-Seiten und **alle
Bibliotheksblöcke mit ihren `ki_prompt_hint`** — und sucht daraus die
passenden aus. Das Ergebnis ist eine Liste von Block-Referenzen.

Daraus folgt eine harte Decke:

> **Jede Kundenseite ist eine Permutation derselben ~41 Blöcke.**
> Individuell werden nur Texte und Farben.

Für „schnell eine solide Seite" ist das genau richtig. Für den
Premium-Differentiator — technisch, SEO, SEA und Conversion perfekt, und
eben *nicht* die zwanzigste Seite mit demselben Hero — reicht es nicht. Zwei
SHK-Betriebe in Koblenz bekämen sichtbar dieselbe Seite in anderen Farben.

**Claude im Designbereich heißt deshalb: Claude schreibt Gestaltung, statt
sie auszuwählen.**

## 3. Grundentscheidung: GrapesJS bleibt

**Nicht ersetzen. Ergänzen.** Begründung:

* GrapesJS ist die **Korrekturschicht**. „Diesen Abstand 8 px kleiner",
  „Bild tauschen", „Zeile umbrechen" — das ist mit der Maus in zwei Sekunden
  erledigt und über einen Prompt eine Zumutung.
* Claude ist die **Erzeugungsschicht**. Aus Briefing, Marke und Branche etwas
  entstehen lassen, das vorher nicht da war — das kann kein Baukasten.
* Beides ersetzt einander nicht, es greift ineinander: **Claude entwirft,
  GrapesJS justiert.**

Ein Ersatz von GrapesJS würde jede Kleinigkeit in einen KI-Aufruf verwandeln:
langsamer, teurer, ungenauer — und ohne visuelles Feedback beim Ziehen.

## 4. Der Vertrag — der eigentliche Kern

Damit das zusammenpasst, darf Claude nicht „irgendein HTML" liefern. Was
Claude erzeugt, muss der Editor **als bearbeitbaren Komponentenbaum** einlesen
können, nicht als undurchdringlichen Klumpen.

### 4.1 Was der Vertrag heute prüft

`services/block_contract.py`, geprüft von `tests/test_block_contract.py`.

| Regel | Prüft | Warum |
|---|---|---|
| **R0** | Nicht leer | — |
| **R1** | Keine fremde Ressource: kein `<script>`, `<iframe>`, `<object>`, `<embed>`, `<link>`, `<base>`; kein `src="https://…"`; kein `@import`; kein `on…`-Attribut | IP-Übertragung ohne Einwilligung — derselbe K.-o.-Grund wie im Widget |
| **R2** | Genau eine Wurzel, und sie trägt `data-block="<slug>"` | Sonst findet der Editor den Block nicht wieder |
| **R3** | Slots als `{{kleinbuchstaben_mit_unterstrich}}`, und jeder Slot im Markup steht in den Slot-Angaben | Sonst füllt `generate-copy` ihn nie |
| **R4** | Höchstens 12 Ebenen tief, kein `id`, kein `position: fixed/sticky` | Bedienbarkeit im Editor; ein Block kann zweimal auf einer Seite stehen |
| **R5** | Nur neutrale Farbtöne (`gray`, `slate`, `zinc`, `neutral`, `stone`, `white`, `black`, `transparent`); kein eigener Farbwert (`bg-[#004F59]`), keine Farbe im `style`-Attribut | Die Marke kommt aus dem Style-Guide und ersetzt die Graustufen. Was bunt im Block steht, überlebt den Markenwechsel |

**Wichtig: Die Regeln sind an der bestehenden Bibliothek gemessen, nicht
erfunden.** Die erste Fassung dieses Dokuments verlangte `{{HEADLINE}}` in
Großbuchstaben, verbot jedes `style`-Attribut und wollte `data-gjs-*` sehen —
die 41 echten Blöcke nutzen `{{lower_snake}}`, ein `style` für die
Schriftfamilie und `data-block`. Nach dem alten Text wären 22 von 41 eigenen
Blöcken durchgefallen. Drei weitere Regeln kamen aus demselben Grund wieder
heraus: Navigation, Footer und Banner haben zu Recht keine Überschrift, ein
Hero *ist* die `h1` seiner Seite, und ein anklickbarer `wa.me`-Link ist keine
automatisch geladene Ressource.

**Drei eigene Blöcke bestehen den Vertrag nicht** und stehen als bekannte
Schuld im Test: `hw-karte` und `seo-lokal` binden Google Maps per `<iframe>`
ein. Das überträgt die Besucher-IP an Google, bevor jemand klickt — genau der
K.-o.-Grund, den unser eigener Kriterienkatalog `tracking_ohne_consent` nennt.
Jede Kundenseite mit einem dieser Blöcke fällt bei unserer eigenen Prüfung
durch. Auflösung: statische Kartengrafik oder Karte erst nach Einwilligung.
Der dritte kam mit R5 dazu: `hero-centered` legt ein Overlay in
`rgba(0,79,89,0.78)` über sein Hintergrundbild — KOMPAGNON-Teal, fest im
`style`-Attribut. Auf einer Kundenseite bleibt es teal, egal welche Marke der
Style-Guide vorgibt.

### 4.2 R5 — die Marken-Bindung, und was beim Messen herauskam

**Die Regel steht** (`services/block_contract.py`, Tabelle oben). Der Weg dahin
ist lehrreicher als die Regel selbst.

Der ursprüngliche Plan war, „jede Farb-, Schrift- und Abstandsklasse gegen den
Token-Satz aus `wireframe_data.style_guide`" zu prüfen. Das geht nicht, weil
der Style-Guide keine Tailwind-Token führt, sondern Hex-Werte — und weil die
Marke ganz anders angewendet wird als gedacht: `DesignView.buildOverrideCSS`
überschreibt einen **festen, kleinen Satz Tailwind-Graustufen** mit den
Marken-Werten (`bg-white`, `bg-gray-50/100/200/300`, `bg-gray-700/800/900`,
`text-gray-400…900`, `border-gray-200/300`).

Daraus folgt die Regel, die tatsächlich trägt: **ein Block darf nur neutrale
Töne benutzen.** Gemessen an den 45 Bibliotheksblöcken vor dem Scharfschalten —
298× `gray`, 222× `slate`, dazu `white`, `black`, `transparent`, **kein
einziger bunter Ton**; in der Datenbank-Bibliothek (96 Blöcke) ebenso wenig.
Die Regel beschreibt also, was die Bibliothek ohnehin tut, und weist genau das
ab, was Stufe B gefährdet.

**Der eigentliche Fund liegt daneben.** Der Marken-Override kannte nur
`gray-*` und `bg-white`. Die Bibliothek malt aber zu großen Teilen in
`slate-*` (222 Vorkommen), dazu `text-white/80`, `from-gray-900/95`,
`bg-gray-600`, `border-gray-700`, `ring-gray-700/30` — alles Klassen, die er
**nicht** angefasst hat. **Alle 45 Blöcke** enthalten mindestens eine davon.

**Behoben** (`utils/brandOverride.js` mit `brandOverride.test.js`): Der Override
deckt jetzt alle fünf Graustufen-Familien über die volle Skala ab, dazu
Deckkraft-Varianten und Verläufe. Der dunkle Kontext läuft über drei Custom
Properties, die dunkle Flächen setzen und alles darin erbt — die naive Fassung,
die jede Regel je dunkler Fläche wiederholte, ergab 449 KB CSS; so sind es 114.
Der Test liest die 45 echten Blöcke und verlangt für jede ihrer Farbklassen
einen Selektor. Kommt ein neuer Block mit einer neuen Klasse, fällt es dort auf.

### 4.3 Die Korrektur: Wohin dieses CSS **nicht** geht

Beim Bauen kam heraus, dass eine frühere Fassung dieses Dokuments (und mein
eigener Befund oben) zu weit ging: **Der Override erreicht die Kundenseite gar
nicht.** `buildOverrideCSS` wird an genau zwei Stellen benutzt — in der
Vorschau der DesignView und im Einzelseiten-Export per Knopf. Die
ausgelieferte Seite entsteht auf einem anderen Weg:
`sitemap_pages.mockup_html` (aus einem Agenten-Lauf) → GrapesJS →
`gjs_html`/`gjs_css` → Netlify. Die Bibliotheksblöcke werden im ganzen Frontend
nur an drei Stellen gerendert (Wireframe-Editor, Design-Vorschau,
Komponenten-Manager), und keine davon schreibt in `mockup_html`.

Das heißt zweierlei:

* Der reparierte Override wirkt dort, wo entschieden wird — in der Vorschau,
  auf deren Grundlage der Style-Guide freigegeben wird. Eine Vorschau, die halb
  Marke und halb Wireframe zeigt, führt genau an dieser Stelle in die Irre.
* **Die eigentliche Lücke vor Stufe B ist eine andere:** Wireframe + Style-Guide
  münden heute in keine ausgelieferte Seite. Stufe B würde in `wireframe_data`
  schreiben — also in denselben Zweig, der nicht angeschlossen ist. Das ist die
  Entscheidung, die vor B ansteht (§ 9.5).

**Kontrolllauf mit scharfem R5** (vier Blöcke gegen die echte API): R5 hat kein
einziges Mal ausgelöst — das Modell bleibt von sich aus grau. Aufgefallen ist
dabei etwas anderes: Zwei Blöcke setzten `id` am Titel, um per
`aria-labelledby` darauf zu zeigen, und rissen damit R4. Der Prompt verlangte
Barrierefreiheit und verbot `id`, ohne den Ausweg zu nennen. Jetzt nennt er ihn
(`aria-label` direkt am Bereich) — und derselbe Fall kommt seither in einer
Runde durch: `trust` von 130 s auf 70 s.

## 5. Drei Stufen, in dieser Reihenfolge

Bewusst gestaffelt: Jede Stufe ist für sich nützlich, und keine setzt voraus,
dass die nächste kommt.

### Stufe A — Claude als Blockautor · **gebaut**

Claude erzeugt **neue Bibliotheksblöcke** statt fertiger Seiten. Eingabe:
Kategorie, Layout-Preset, Branche, Pflicht-Elemente, Freitext-Wunsch. Ausgabe:
ein Block nach Vertrag, der **einmal** geprüft und dann beliebig oft verwendet
wird.

**Was steht:**

| Weg | Endpunkt | Verhalten |
|---|---|---|
| Erzeugen | `POST /api/components/generate` → `GET /api/components/generate/{job_id}` | Hintergrundauftrag; Prompt lehrt den Vertrag, das Ergebnis wird geprüft, Verstöße gehen **einmal** ans Modell zurück; die Reparatur wird nur übernommen, wenn sie die Verstöße wirklich verringert. Der Befund fährt als `contract` im Ergebnis mit. |
| Anlegen | `POST /api/components` | Unsauber ⇒ `status="draft"`, nicht verworfen |
| Custom speichern | `POST /api/components/save-custom` | Gleiche Prüfung — sonst käme unsauberes Markup durch die zweite Tür |
| Bearbeiten | `PUT /api/components/{slug}` | Prüft neu; bricht eine Änderung den Block, entzieht sie die Freigabe |
| Freigeben | `POST /api/components/{slug}/approve` | **422 mit den konkreten Verstößen**, solange etwas offen ist |
| Lesen | `GET /api/components` | Entwürfe unsichtbar; `?include_drafts=true` zeigt sie |

Ein Entwurf erreicht weder den Wireframe-Editor noch den Wireframe-Generator
(`_run_wireframe_job` lädt nur Freigegebenes). Ein unsauberer Block wird
bewusst **gespeichert statt verworfen**: sonst wäre die Arbeit weg und der
Grund unsichtbar.

**Modellwahl:** Die Block-Erzeugung läuft auf `claude-opus-5` — dieses Markup
landet auf Kundenseiten, da zählt Qualität mehr als der Token-Preis. Slot-Copy
(`generate-copy`) und Wireframe-Zuordnung bleiben auf `claude-sonnet-4-6`.

**Die Oberfläche dazu — gebaut:**

| Wo | Was man sieht |
|---|---|
| Komponenten-Manager, Liste | Filter „Alle / Freigegeben / Entwürfe" mit Zähler, Entwurfs-Kennzeichnung am Eintrag, ⚠️ an freigegebenen Blöcken, die den Vertrag trotzdem verletzen (die Altlast `hw-karte`, `seo-lokal`) |
| Komponenten-Manager, Editor | Status im Kopf, Verstöße im Klartext (Regel + Begründung), Freigabe-Knopf — gesperrt, solange etwas offen ist oder ungespeicherte Änderungen anstehen |
| Speichern / Anlegen | Fällt ein Block auf Entwurf, sagt die Meldung es und nennt die Zahl der offenen Punkte |
| KI-Generator | Der Befund steht schon am Ergebnis, nicht erst nach dem Speichern |
| Wireframe-Editor | Ein Block, der nicht mehr in der freigegebenen Bibliothek steht, sagt das jetzt — vorher blieb die Karte einfach leer |
| „Als Custom speichern" | Landet der Block als Entwurf, wird er **nicht** in die Seite getauscht; der Grund steht im Panel statt in der Konsole |

Zwei Dinge kamen beim Bauen dazu, weil sie auf demselben stillen Weg lagen:
Die Oberfläche vergab beim Übernehmen eines KI-Blocks einen eigenen Slug, ließ
`data-block` aber stehen — Regel R2 verletzt, Block als Entwurf, und im
Formular war nichts zu sehen, was das erklärt hätte. Und ein Nachladen nach dem
Speichern konnte eine Eingabe verschlucken, die währenddessen passierte.

`e2e/tests/block-freigabe.spec.js` prüft den Weg im Browser: unsauber anlegen →
Entwurf mit Grund → Freigabe gesperrt → reparieren → Freigabe klappt.

### Der scharfe Lauf — die Frage vor Stufe B ist beantwortet

Zehn Blöcke gegen die echte API, quer durch die Kategorien (HERO frei, HERO mit
Preset, HERO mit Formular, LEIST, TRUST, CTA, NAV, FOOT, SEO, HW). Gemessen
wurde der Auftrag selbst, nicht ein Nachbau.

| | |
|---|---|
| Angekommen | 9 von 10 |
| **Im ersten Wurf vertragskonform** | **8 von 9** |
| Reparaturrunde nötig | 1 (danach sauber) |
| Abbruch | 1 — und zwar **nicht** am Vertrag |
| Dauer je Block | 26–76 s, mit Reparatur 141 s |
| Kosten | ~38k ein / ~53k aus auf Opus 5 für zehn Blöcke |

**Der Vertrag ist keine Hürde.** Kein einziger Block enthielt einen `<iframe>`,
ein `<script>`, ein `id`-Attribut oder eine externe Quelle — auch nicht bei
`seo-lokal` und `hw-karte`, also genau dort, wo die beiden Altblöcke der
Bibliothek daran scheitern. Die Regeln liegen dort, wo das Modell ohnehin
schreibt.

**Der eine Verstoß war ein Buchhaltungsfehler — und ist erledigt.** Zwölfmal
dieselbe Regel R3: Slots im Markup (`product_1_spec_1` …), die in den
Slot-Angaben fehlten. Das kostete eine zweite Runde mit 11k Eingabe- und 8k
Ausgabe-Token für eine Angabe, die im Markup bereits stand. Seither liest
`services/block_slots.py` sie dort ab, statt sie zu erfragen: Der Generator
trägt fehlende Slots nach, bevor der Vertrag prüft — mit Beschriftung aus dem
Schlüssel (`product_1_spec_1` → „Product 1 Spec 1"), in der Reihenfolge des
Markups. Was das Modell selbst beschriftet hat, bleibt unangetastet; eine
abgeleitete Beschriftung ist immer schlechter als eine gemeinte.

Bewusst **nur im Generator**, nicht an den beiden Türen in die Bibliothek: Wer
von Hand einen Block schreibt, soll seine Slot-Angaben nicht stillschweigend
umgeschrieben bekommen — er sieht den Verstoß jetzt im Klartext und entscheidet
selbst.

**Gescheitert ist der Auftrag am JSON, nicht am Vertrag.** Beim FOOT-Block war
die Antwort ab Zeichen 9396 kein gültiges JSON mehr. Zwei Nachläufe desselben
Falls kamen sauber zurück, `stop_reason` jedes Mal `end_turn` — ein Ausrutscher,
kein Muster, aber bei ~11 % die häufigere Ausfallursache als der Vertrag.
Behoben: Der Parser lässt rohe Steuerzeichen in Zeichenketten jetzt durch
(`strict=False`), und bei kaputtem JSON bekommt das Modell den Parserfehler
zurück und **eine** zweite Chance. Bei `max_tokens` wird bewusst nicht
nachgefragt — die Antwort ist dann garantiert unvollständig. `generate-copy`
und der Wireframe-Job parsen ebenfalls nachsichtig; die zweite Chance haben sie
nicht, dafür fehlt der Beleg und ihr Auftrag ist teurer zu wiederholen. Derselbe
FOOT-Fall lief nach dem Umbau gegen die echte API sauber durch — erste Runde,
kein offener Punkt.

→ **Für Stufe B heißt das:** Der Vertrag trägt. Ein Aufruf je variierter
Section reicht in acht von neun Fällen, und die Reparaturrunde fängt den Rest.

**Was noch fehlt:**

1. **Envato als Inspirationsquelle** — noch nicht angebunden (§ 9.3).

### Stufe B — Claude als Sektionsgestalter *(mittel, nicht gebaut)*

Ein ausgewählter Block wird **für diesen Kunden umgeschrieben** — nicht nur
mit Text gefüllt, sondern im Aufbau variiert: andere Anordnung, andere
Betonung, passend zu Leistung und Region. Hier entsteht die Individualität,
die heute fehlt.

**Eingabe:** der gewählte Bibliotheksblock als Ausgangspunkt, das Briefing,
die Style-Guide-Token des Kunden, Leistung und Einzugsgebiet.
**Ausgabe:** kundeneigenes Markup, das denselben Vertrag besteht.

**Der konkrete Haken im Code:** `WireframeBlock` kennt heute nur
`slug`, `order`, `slots`. Eine Variante braucht eigenes Markup — also ein
zusätzliches Feld (`html_override`), und der Renderer muss es dem
Bibliotheks-Template vorziehen. Das ist der einzige Datenmodell-Eingriff, den
B braucht; ein neuer Speicherort entsteht nicht.

**Voraussetzungen, in dieser Reihenfolge:**

1. Stufe A trägt im Alltag ✅ (Oberfläche steht, scharfer Lauf gemacht).
2. **R5** ✅ im Prüfer, **Marken-Override** ✅ vollständig (§ 4.2).
3. Prüfung je Kunde statt je Block: der Vertrag läuft, aber niemand sieht
   jede Variante an. Offene Frage: Reicht „Vertrag bestanden" als Freigabe,
   oder braucht jede Variante einen Blick?

**Kosten:** ein Aufruf je variierter Section je Kunde. Anders als A
amortisiert sich das **nicht** über alle Kunden — deshalb sparsam einsetzen,
etwa nur für Hero und die tragende Leistungs-Section.

### Stufe C — Claude als Seitenkomponist *(groß, nicht gebaut)*

Claude entwirft die **ganze Seite** innerhalb des Style-Guides: Reihenfolge,
Rhythmus, Übergänge, Wiederholungsvermeidung. Blöcke werden zur Referenz,
nicht zur Grenze.

**Eingabe:** die Sitemap-Seite mit ihrer Rolle, das Briefing, die
Style-Guide-Token, die Pflicht-Sections aus `conversion-spec-shk.md`, die
Bibliothek als Referenz.
**Ausgabe:** eine Section-Folge mit eigenem Markup je Section.

**Die Qualitätsschleife ist der eleganteste Teil — und hat eine Hürde.** Der
Plan: den eigenen 38-Kriterien-Audit gegen die selbst erzeugte Seite laufen
lassen. Das schließt den Kreis, denn was wir Kunden vorwerfen, dürfen wir
selbst nicht liefern.

Die Hürde: **Der Audit ist URL-getrieben, nicht Markup-getrieben.**
`services/audit_runner.py` beginnt mit `fetch_homepage(url)` und prüft danach
Hosting, Header und Links — alles Dinge, die es ohne ausgelieferte Seite nicht
gibt. Der Prüfer lässt sich also nicht einfach auf einen HTML-String richten.

Der saubere Weg ist ohnehin der bessere: **erst auf eine Netlify-Vorschau
deployen, dann diese URL auditieren.** Der Deploy existiert
(`services/netlify_service.py`), und geprüft wird dann, was der Besucher
wirklich bekommt — inklusive Hosting und Header, die aus dem Markup allein gar
nicht hervorgehen. Kein Umbau des Prüfers nötig.

**Sinnvoll erst, wenn A und B im Alltag tragen.**

## 6. Leitplanken

| Leitplanke | Umsetzung | Stand |
|---|---|---|
| **Marke** | Block bleibt neutral, die Farbe kommt aus dem Style-Guide | ✅ Regel R5 im Prüfer — ⚠️ aber der Override deckt nur `gray-*` ab (§ 4.2) |
| **Conversion** | Pflicht-Sections aus `conversion-spec-shk.md` als Schema | offen, ab Stufe C |
| **Qualität** | Der eigene 38-Kriterien-Audit läuft gegen die erzeugte Seite | offen; Weg geklärt: über Netlify-Vorschau |
| **Datenschutz** | Keine externen Ressourcen, wie im Widget | ✅ Regel R1 |
| **Kosten** | Erzeugung ist ein Hintergrundauftrag | ✅ Muster in `component_library.py` |

## 7. Wo es andockt

```
Briefing + Analyse
      │
      ▼
  Sitemap (KI)  ──────────────► sitemap_pages
      │
      ▼
  Wireframe (KI)                        ┌─ Stufe A: Claude schreibt Blöcke ✅
      │  wählt Blöcke aus  ◄────────────┤   (nur freigegebene)
      │                                 └─ component_library.html_template
      ▼
  wireframe_data ──── Stufe B: Claude variiert je Kunde  (html_override)
      │
      ▼
  Style-Guide-Token ── R5 hält den Block neutral ✅ · Override lückenhaft ⚠️
      │
      ▼
  GrapesJS (kas_gjs_data) ◄── Mensch justiert     ◄── Stufe C: ganze Seite
      │
      ▼
  Netlify-Vorschau ──► QA: eigener 38-Kriterien-Audit
      │
      ▼
  Netlify-Deploy
```

Neu ist **kein** Speicherort. Stufe A schreibt in `component_library`,
Stufe B/C in `wireframe_data` bzw. `kas_gjs_data`.

## 8. Was schiefgehen kann

* **Generisches KI-Aussehen.** Ohne konkrete Welt (Branche, Ort, Betrieb,
  Materialien) fällt jedes Modell in denselben Durchschnitt. Der Prompt muss
  den *Betrieb* beschreiben, nicht „moderne Website".
* **Markendrift.** Ohne harte Token-Bindung wandert die Gestaltung ab —
  heute real offen, siehe § 4.2.
* **Unwartbares Markup.** Verschachtelung ohne Ende. Gegenmittel steht:
  Tiefenbegrenzung 12 Ebenen in R4.
* **Kosten je Kunde.** Stufe C ist ein langer Aufruf je Seite, B einer je
  Section. Stufe A amortisiert sich dagegen über alle Kunden.
* **Ein Vertrag, den die eigene Bibliothek verletzt.** Genau das ist beim
  Bauen passiert und wurde korrigiert, indem die Regeln an den echten Blöcken
  gemessen wurden. Bei R5 droht dasselbe: erst am Style-Guide messen, dann
  einschalten.

## 9. Offene Entscheidungen

1. **Wer gibt einen erzeugten Block frei** — du allein oder ein automatischer
   Vorfilter? Technisch verweigert die Freigabe heute nur bei Vertragsbruch;
   *gestalterisch* schaut noch niemand hin.
2. **Reicht bei Stufe B „Vertrag bestanden" als Freigabe je Kunde**, oder
   braucht jede Variante einen Blick? Entscheidet, ob B skaliert.
3. **Inspirationsquelle für Stufe A:** die 68 Envato-Vorlagen als
   Muster-Referenz (Ableitung, nicht Kopie) oder rein aus dem Briefing?
4. **Bleibt der GrapesJS-Editor beim Kunden** oder nur intern bei dir? Das
   entscheidet, wie streng die Sperren im Vertrag sein müssen.
5. **Wie kommt der Wireframe-Zweig auf die Seite?** (§ 4.3, neu und die
   wichtigste dieser Fragen.) Heute laufen zwei Wege nebeneinander: Der eine
   geht Sitemap → Wireframe → Style-Guide → Design-Vorschau und endet dort. Der
   andere geht über einen Agenten-Lauf in `mockup_html` → GrapesJS → Netlify
   und ist der, der beim Kunden ankommt. Stufe A und B bauen auf dem ersten.
   Drei Möglichkeiten:
   * **Anschließen:** Die Design-Vorschau schreibt ihr gerendertes HTML samt
     Override-CSS nach `mockup_html`. Kleinster Eingriff, macht den
     Wireframe-Zweig produktiv.
   * **Zusammenlegen:** Der Agenten-Lauf bekommt die Blöcke als Vorlage, statt
     frei zu erzeugen. Größer, dafür ein Weg statt zwei.
   * **Trennen und benennen:** Der Wireframe-Zweig bleibt Entwurfswerkzeug für
     dich, die Kundenseite entsteht weiter über den Agenten. Dann sind Stufe B
     und C für die Kundenseite ohne Wirkung — und das gehört ins Konzept.

## 10. Nächste Schritte

| # | Was | Aufwand | Warum jetzt |
|---|---|---|---|
| ~~1~~ | ~~Oberfläche für Entwurf und Freigabe~~ | — | **gebaut am 2026-08-13** (§ Stufe A) |
| ~~2~~ | ~~Scharfer Generierungslauf~~ | — | **gelaufen am 2026-08-13**: 8 von 9 im ersten Wurf konform; der JSON-Ausrutscher ist behoben |
| 3 | `hw-karte` / `seo-lokal` entschärfen | ~2 h | Eigene Blöcke fallen bei der eigenen Prüfung durch — in der Liste jetzt am ⚠️ zu sehen. Der scharfe Lauf zeigt: neu erzeugte Blöcke machen den Fehler nicht mehr |
| ~~4~~ | ~~R5 Marken-Bindung~~ | — | **gebaut am 2026-08-13**, an 45 Blöcken gemessen |
| ~~4b~~ | ~~Marken-Override vervollständigen~~ | — | **gebaut am 2026-08-13**: `utils/brandOverride.js`, gegen die 45 Blöcke geprüft |
| 4c | **Entscheiden, wie der Wireframe-Zweig auf die Seite kommt** (§ 9.5) | Entscheidung | Ohne sie bleiben Stufe B und C ohne Wirkung auf die Kundenseite |
| ~~5~~ | ~~R3 ohne zweite Runde~~ | — | **gebaut am 2026-08-13**: `services/block_slots.py` |
| 6 | Stufe B | offen | Erst wenn 3 steht und 4c entschieden ist |

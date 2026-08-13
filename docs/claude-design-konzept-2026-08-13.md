# Claude im Designbereich — Konzept und Stand

**Angelegt:** 2026-08-13 · **Zuletzt:** 2026-08-13 (Stufe A gebaut)
**Frage:** Wie integrieren wir Claude in den Designbereich, um neue Homepages
zu entwickeln — statt GrapesJS oder zusätzlich?
**Verbunden:** `kas-pipeline-architecture.md` (04.05., Grundlage),
`conversion-spec-shk.md` (Pflichtinhalte), `niche_phase1.md` (Zielgruppe)

---

## 0. Stand in einem Absatz

Stufe A ist gebaut und liegt auf `staging` (Commits `73c4822`, `4276676`).
Claude schreibt Bibliotheksblöcke, ein prüfbarer Vertrag steht davor, und ohne
Freigabe erreicht kein erzeugter Block eine Kundenseite. Was fehlt, ist die
Oberfläche dazu, ein scharfer Lauf gegen die echte API — und eine Vertragsregel,
die Stufe B sonst auf Sand baut (§ 4.2). Stufe B und C sind entworfen, nicht
gebaut.

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

**Wichtig: Die Regeln sind an der bestehenden Bibliothek gemessen, nicht
erfunden.** Die erste Fassung dieses Dokuments verlangte `{{HEADLINE}}` in
Großbuchstaben, verbot jedes `style`-Attribut und wollte `data-gjs-*` sehen —
die 41 echten Blöcke nutzen `{{lower_snake}}`, ein `style` für die
Schriftfamilie und `data-block`. Nach dem alten Text wären 22 von 41 eigenen
Blöcken durchgefallen. Drei weitere Regeln kamen aus demselben Grund wieder
heraus: Navigation, Footer und Banner haben zu Recht keine Überschrift, ein
Hero *ist* die `h1` seiner Seite, und ein anklickbarer `wa.me`-Link ist keine
automatisch geladene Ressource.

**Zwei eigene Blöcke bestehen den Vertrag nicht** und stehen als bekannte
Schuld im Test: `hw-karte` und `seo-lokal` binden Google Maps per `<iframe>`
ein. Das überträgt die Besucher-IP an Google, bevor jemand klickt — genau der
K.-o.-Grund, den unser eigener Kriterienkatalog `tracking_ohne_consent` nennt.
Jede Kundenseite mit einem dieser Blöcke fällt bei unserer eigenen Prüfung
durch. Auflösung: statische Kartengrafik oder Karte erst nach Einwilligung.

### 4.2 Was der Vertrag **nicht** prüft — die Lücke vor Stufe B

**Die Marken-Bindung fehlt im Code.** Leitplanke 1 sagt „nur Token aus dem
Style-Guide, freie Farben werden abgewiesen". Diese Regel steht heute nur als
Satz im Prompt (`_WIREFRAME_CONSTRAINTS`), nicht im Prüfer. Ein erzeugter
Block darf `bg-blue-500` schreiben und besteht den Vertrag.

Für Stufe A ist das verkraftbar: Wireframes sind grau, ein Mensch sieht den
Ausrutscher vor der Freigabe. **Für Stufe B ist es das nicht** — B ist genau
der Schritt, in dem Markenfarben pro Kunde angewendet werden. Ohne harte
Token-Bindung wandert die Gestaltung ab, und es merkt niemand, bis es beim
Kunden steht.

→ **Vor Stufe B zu bauen:** Regel R5, die jede Farb-, Schrift- und
Abstandsklasse gegen den Token-Satz aus `wireframe_data.style_guide` prüft.
Geschätzt ein halber Tag.

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

**Was noch fehlt:**

1. **Oberfläche.** Das Frontend kennt `status` und `contract` nicht. Heute
   verschwindet ein abgelehnter Block wortlos aus dem Wireframe-Editor. Nötig:
   Entwurfs-Kennzeichnung, Verstöße im Klartext am Block, Freigabe-Knopf.
2. **Scharfer Lauf.** Die Job-Logik ist mit einem Platzhalter getestet
   (`tests/test_component_library_gate.py`), der echte API-Aufruf noch nicht.
   Die offene Frage dahinter entscheidet über B: **Wie oft muss repariert
   werden?**
3. **Envato als Inspirationsquelle** — noch nicht angebunden (§ 9.3).

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

1. Stufe A trägt im Alltag (Oberfläche + scharfer Lauf).
2. **R5 Token-Bindung** (§ 4.2) — ohne sie driftet die Marke.
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
| **Marke** | Nur Token aus dem Style-Guide; freie Farben werden abgewiesen | ⚠️ nur im Prompt, nicht im Prüfer (§ 4.2) |
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
  Style-Guide-Token ── R5 bindet die Marke  ⚠️ fehlt
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

## 10. Nächste Schritte

| # | Was | Aufwand | Warum jetzt |
|---|---|---|---|
| 1 | Oberfläche für Entwurf und Freigabe | ~2 h | Ohne sie ist Stufe A unbenutzbar und der Rückfall auf Entwurf wirkt wie ein Fehler |
| 2 | Scharfer Generierungslauf | ~1 h | Beantwortet die Frage, die über B entscheidet: Wie oft muss repariert werden? |
| 3 | `hw-karte` / `seo-lokal` entschärfen | ~2 h | Eigene Blöcke fallen bei der eigenen Prüfung durch |
| 4 | R5 Token-Bindung | ~4 h | Voraussetzung für Stufe B |
| 5 | Stufe B | offen | Erst wenn 1–4 stehen |

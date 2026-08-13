# Claude im Designbereich — Konzept

**Stand:** 2026-08-13
**Frage:** Wie integrieren wir Claude in den Designbereich, um neue Homepages
zu entwickeln — statt GrapesJS oder zusätzlich?
**Verbunden:** `kas-pipeline-architecture.md` (04.05., Grundlage),
`conversion-spec-shk.md` (Pflichtinhalte), `niche_phase1.md` (Zielgruppe)

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
Claude erzeugt, muss GrapesJS **als bearbeitbaren Komponentenbaum** einlesen
können, nicht als einen undurchdringlichen Klumpen. Das ist die technische
Mitte des ganzen Konzepts.

**Regeln für erzeugtes Markup:**

1. **Nur Tailwind-Klassen aus dem Style-Guide-Token-Satz.** Keine freien
   Hex-Werte, keine `style=""`-Attribute. Die Marke ist damit erzwungen,
   nicht erbeten.
2. **`data-gjs-*` markiert die Bearbeitbarkeit.** Welche Knoten sind
   Textfelder, welche sind Bilder, welche sind gesperrt (Layoutgerüst).
   Ohne das entsteht ein Baum, in dem der Nutzer versehentlich das Raster
   zerlegt.
3. **Slots nach bestehender Konvention** (`{{HEADLINE}}`,
   `{{OFFER_STACK_ITEMS}}` …) — so bleibt `generate-copy` unverändert
   nutzbar.
4. **Keine externen Ressourcen.** Keine Google Fonts, keine CDN-Skripte —
   dieselbe Regel wie im Widget, aus demselben Grund (IP-Übertragung ohne
   Einwilligung).
5. **Semantisches HTML.** `<section>`, `<h2>`, `<button>` — weil unser
   eigener Kriterienkatalog Barrierefreiheit und Struktur bewertet.

Die Brücke existiert bereits: `utils/studioTemplateImport.js` liest HTML+CSS
in GrapesJS ein, `ComponentLibrary.html_template` speichert genau solches
Markup. Der Vertrag ist also **kein neues System, sondern eine Präzisierung
dessen, was schon fließt**.

## 5. Drei Stufen, in dieser Reihenfolge

Bewusst gestaffelt: Jede Stufe ist für sich nützlich, und keine setzt voraus,
dass die nächste kommt.

### Stufe A — Claude als Blockautor *(klein, sofort nützlich)*

Claude erzeugt **neue Bibliotheksblöcke** statt fertiger Seiten. Eingabe:
eine Beschreibung („Hero für Wärmepumpe mit Förderrechner-Teaser"),
optional eine Vorlage als Inspiration. Ausgabe: ein Block nach Vertrag, der
**einmal** geprüft und dann beliebig oft verwendet wird.

* Die bestehende Pipeline bleibt **unangetastet** — der Wireframe-Generator
  wählt weiter aus, nur aus mehr und besseren Blöcken.
* Qualitätsprüfung passiert einmal je Block, nicht bei jedem Kunden.
* Zahlt direkt auf den Envato-Wireframe-Plan ein: aus Vorlagen ableiten,
  statt sie zu kopieren.
* **Risiko: gering.** Ein schlechter Block wird nicht freigegeben, fertig.

### Stufe B — Claude als Sektionsgestalter *(mittel)*

Ein ausgewählter Block wird **für diesen Kunden umgeschrieben** — nicht nur
mit Text gefüllt, sondern im Aufbau variiert: andere Anordnung, andere
Betonung, passend zu Leistung und Region. Ergebnis bleibt vertragskonform und
landet als kundeneigene Variante in `wireframe_data`.

* Hier entsteht die Individualität, die heute fehlt.
* Prüfung je Kunde nötig — deshalb erst nach Stufe A.

### Stufe C — Claude als Seitenkomponist *(groß)*

Claude entwirft die **ganze Seite** innerhalb des Style-Guides: Reihenfolge,
Rhythmus, Übergänge, Wiederholungsvermeidung. Blöcke werden zur Referenz,
nicht zur Grenze.

* Größter Hebel für die Qualitätslatte, größter Prüfaufwand.
* Sinnvoll erst, wenn A und B im Alltag tragen.

## 6. Leitplanken

| Leitplanke | Umsetzung |
|---|---|
| **Marke** | Nur Token aus dem Style-Guide; freie Farben werden abgewiesen |
| **Conversion** | Pflicht-Sections aus `conversion-spec-shk.md` als Schema |
| **Qualität** | **Der eigene 38-Kriterien-Audit läuft gegen die erzeugte Seite**, bevor sie jemand sieht |
| **Datenschutz** | Keine externen Ressourcen, wie im Widget |
| **Kosten** | Erzeugung je Block/Seite ist ein Hintergrundauftrag — Muster existiert in `component_library.py` |

Der dritte Punkt ist der eleganteste: **Wir haben bereits einen Prüfer für
Homepage-Qualität gebaut.** Ihn auf die selbst erzeugte Seite anzuwenden,
schließt den Kreis — und was wir Kunden vorwerfen, dürfen wir selbst nicht
liefern.

## 7. Wo es andockt

```
Briefing + Analyse
      │
      ▼
  Sitemap (KI)  ──────────────► sitemap_pages
      │
      ▼
  Wireframe (KI)                        ┌─ Stufe A: Claude schreibt Blöcke
      │  wählt Blöcke aus  ◄────────────┤
      │                                 └─ component_library.html_template
      ▼
  wireframe_data ──── Stufe B: Claude variiert je Kunde
      │
      ▼
  Style-Guide-Token
      │
      ▼
  GrapesJS (kas_gjs_data) ◄── Mensch justiert     ◄── Stufe C: ganze Seite
      │
      ▼
  QA: eigener 38-Kriterien-Audit
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
* **Markendrift.** Ohne harte Token-Bindung wandert die Gestaltung ab. Deshalb
  Regel 1 des Vertrags.
* **Unwartbares Markup.** Verschachtelung ohne Ende, die in GrapesJS
  unbedienbar ist. Gegenmittel: `data-gjs-*` und eine Tiefenbegrenzung.
* **Kosten je Kunde.** Stufe C ist ein langer Aufruf je Seite. Stufe A
  amortisiert sich dagegen über alle Kunden.

## 9. Offene Entscheidungen

1. **Womit anfangen?** Empfehlung: Stufe A. Kleinster Eingriff, sofort
   sichtbarer Nutzen, kein Risiko für die laufende Pipeline.
2. **Wer gibt einen erzeugten Block frei** — du allein oder ein
   automatischer Vorfilter (Audit-Score + Sichtprüfung)?
3. **Inspirationsquelle für Stufe A:** die 68 Envato-Vorlagen als
   Muster-Referenz (Ableitung, nicht Kopie) oder rein aus dem Briefing?
4. **Bleibt der GrapesJS-Editor beim Kunden** oder nur intern bei dir? Das
   entscheidet, wie streng die Sperren im Vertrag sein müssen.

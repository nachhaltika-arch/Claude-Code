# Der Austausch — wie die drei Umgebungen zusammenarbeiten

**Das Problem, das dieser Ordner löst.** Gearbeitet wird in drei Umgebungen,
und nur eine davon kann committen. Claude Design und Claude Desktop erzeugen
Ergebnisse, die nirgendwo ankommen: Ein Entwurf bleibt im Verlauf, ein Motiv
bleibt ein Bild in einem Chat, eine Entscheidung bleibt ein Satz, an den sich
in vierzehn Tagen niemand erinnert. Beim nächsten Mal wird dieselbe Frage
noch einmal beantwortet — manchmal anders.

**Die Regel.** Eine Sache hat genau einen Ort, an dem sie gilt, und der ist
dieses Repo. Design und Desktop sind **Werkstätten**, kein Lager. Was dort
fertig wird, kommt hierher zurück.

---

## Wie etwas hereinkommt

Eine Datei in `austausch/eingang/` ablegen. Das war's — kein Format, kein
Schema, keine Namenskonvention, die man falsch machen kann. Markdown, ein
Bild, ein PDF, ein Textschnipsel aus der Zwischenablage.

Wenn möglich, die erste Zeile sagen lassen, **was es ist und wohin es soll**:

    Entscheidung: Check PLUS läuft zum Start mit. → Lagebild
    Entwurf: Mailtext Stufe 4 der Sequenz. → docs/
    Motiv A2-9, Fassung 3, 1080×1920. → Tool-CI

Fehlt die Zeile, ist es kein Fehler — dann wird beim Einarbeiten gefragt.

## Was damit passiert

Im Terminal:

    /eingang

Der Befehl geht jede Datei durch, ordnet sie ein, arbeitet sie an die
richtige Stelle im Repo ein und verschiebt sie nach `austausch/erledigt/`
mit dem Datum davor. Nichts wird gelöscht, nichts stillschweigend verworfen:
Was nicht eingeordnet werden kann, bleibt liegen und wird gemeldet.

## Der Weg zurück

Der Lageplan (Artefakt) hält den Stand der 114 Einträge. Er ist über alle
Geräte gleich und im Terminal auslesbar:

    /lageplan

Der Befehl holt den Stand aus dem Artefakt und trägt Erledigtes in Lagebild
und Vertriebsplan nach — damit die Quellen nicht hinter der Sicht zurückbleiben.

---

## Was in welche Umgebung gehört

| | Umgebung | Rückweg |
|---|---|---|
| Gestaltung, Motive, Layouts | **Design** | Datei nach `austausch/eingang/` |
| Denken, Entwürfe, Vorlagen, Pläne | **Desktop** | Datei nach `austausch/eingang/`, oder ein Artefakt mit `db`, das das Terminal ausliest |
| Code, Anweisungen, Lagebild, Doku | **Terminal** | ist schon hier |

**Die Grenze verläuft nicht nach Aufwand, sondern nach Wirkung.** Etwas, das
den Code ändert, gehört ins Terminal — auch wenn es klein ist. Etwas, das erst
noch durchdacht werden muss, gehört in den Desktop — auch wenn es am Ende nur
ein Satz wird.

## Was hier **nicht** hineingehört

* **Zugangsdaten, Schlüssel, Kontokennungen.** Das Repo ist öffentlich.
  Gitleaks prüft bei jeder PR, aber es kennt keine Kundendaten und keine
  Werbekonto-Nummern.
* **Dateien, die schon im Repo stehen.** Dann ist der Ort bekannt und der
  Umweg über den Eingang kostet nur einen Schritt.
* **Ein Ersatz für ein Gespräch.** Wenn etwas eine Entscheidung braucht,
  gehört es in den Lageplan oder in eine Ansage — nicht in den Briefkasten.

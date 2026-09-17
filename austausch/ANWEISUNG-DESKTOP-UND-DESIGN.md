# Zum Einfügen in Claude Desktop und Claude Design

Der Text unterhalb der Linie gehört als **Projektanweisung** in die beiden
Umgebungen, die nicht ins Repo schreiben können. Er sorgt dafür, dass dort
kein Ergebnis entsteht, das keinen Rückweg hat.

* **Claude Desktop:** Projekt „KOMPAGNON KAS NEU" → Anweisungen
* **Claude Design:** in die Projekt- oder Arbeitsbereichsanweisung

Er steht hier im Repo, damit es eine Fassung gibt, die gilt — sonst driften
die beiden Kopien auseinander und niemand weiß, welche die neuere ist.
Wird er geändert, wird er **hier** geändert und dann dort eingefügt.

---

## KOMPAGNON — wie diese Umgebung mit dem Repo zusammenarbeitet

Du arbeitest in einer **Werkstatt**, nicht im Lager. Das Lager ist das Repo
`nachhaltika-arch/Claude-Code`, und nur das Terminal kann hineinschreiben.
Alles, was hier fertig wird und keinen Rückweg bekommt, ist beim nächsten Mal
verloren — und dieselbe Frage wird noch einmal beantwortet, manchmal anders.

**Deshalb: Jedes Arbeitsergebnis endet mit einer Datei, die David nach
`austausch/eingang/` legen kann.** Nicht mit einer Zusammenfassung im Chat,
nicht mit einem Artefakt ohne Datei daneben.

### Die erste Zeile der Datei

Sie sagt, was es ist und wohin es gehört:

    Entscheidung: <Satz>. → Lagebild
    Entwurf: <Gegenstand>. → docs/
    Gestaltung: <Gegenstand>, <Maße/Fassung>. → Tool-CI

Vier Arten, mehr nicht: **Entscheidung**, **Entwurf**, **Gestaltung**,
**Arbeitsauftrag**. Passt etwas in keine, schreib das hin — der
Einarbeitungsbefehl fragt dann nach, statt zu raten.

### Was dabei gilt

* **Zahlen über das System sind hier Annahmen.** Du kannst nicht messen. Wenn
  eine Zahl in den Entwurf muss, schreib dazu, woher sie stammt — das Terminal
  misst sie nach, bevor sie ins Lagebild geht. Eine geschätzte Zahl, die als
  gemessen gelesen wird, ist teurer als eine fehlende.
* **Nichts Geheimes in die Datei.** Das Repo ist **öffentlich**. Keine
  Zugangsdaten, keine Schlüssel, keine Werbekonto- oder Kundennummern, keine
  Kundendaten. Im Zweifel: Platzhalter, und den echten Wert sagt David
  mündlich.
* **Die Tool-CI ist verbindlich** (KOMPAGNON UI/UX Guidelines v1.0): Dark Teal
  `#004F59` dominiert, Mid Teal `#008EAA` für Links, Gelb `#FAE600` als Akzent
  **höchstens einmal pro Ansicht**, Status immer durch Farbe **und** Text,
  8px-Raster. Noto Sans Black 900 für Überschriften, Noto Sans 300/400/700 für
  Fließtext, DM Mono für Zahlen.
* **Deutsch.** Dokumente, Beschriftungen, Commit-Botschaften — hier wird auf
  Deutsch gearbeitet und entschieden.

### Was hier **nicht** hingehört

Änderungen am Code. Auch kleine. Eine Zeile, die im Chat richtig aussieht,
wird im Terminal an der Datei geprüft, gegen die Tests gefahren und
committet — dieser Weg ist kürzer als der über eine Datei im Briefkasten und
hinterlässt einen Verlauf.

### Der Lageplan

Der gemeinsame Stand steht im Lageplan-Artefakt: 114 Einträge in drei Ebenen
(Marketing, Vertrieb, Produktion). Er ist auf allen Geräten gleich und wird
im Terminal ausgelesen. Wenn du hier etwas erarbeitest, das einen dieser
Einträge betrifft, **nenne seine Kennung** (`P0-11`, `L-195`) — dann findet
das Terminal die Stelle, statt sie zu suchen.

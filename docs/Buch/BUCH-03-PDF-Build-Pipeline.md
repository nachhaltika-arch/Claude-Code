# BUCH-03 — PDF-Build-Pipeline

## Warum dieser Schritt

Aus 15 Markdown-Dateien müssen **zwei verschiedene PDFs** entstehen:

| PDF | Zweck | Besonderheiten |
|---|---|---|
| `homepage-standard-screen.pdf` | Verkauf als Download | RGB, Links klickbar, kleine Dateigröße, Wasserzeichen-fähig |
| `homepage-standard-print.pdf` | Upload zu BoD | 170×240 mm, 3 mm Beschnitt, Schriften eingebettet, PDF/X-3 |

**Ganz wichtig — technische Entscheidung:** Das Buch-PDF wird **einmal vorab gebaut**, nicht
bei jeder Bestellung. Ein 200-Seiten-PDF serverseitig zu rendern dauert 30–90 Sekunden und
blockiert dabei einen Worker deiner Render-Instanz. Bei drei gleichzeitigen Bestellungen
steht dein gesamtes Backend. Der Audit-Report mit 8 Seiten ist unkritisch — 200 Seiten
sind es nicht.

Der Build läuft also **lokal auf deinem Rechner** oder in GitHub Actions. Das Ergebnis wird
als fertige Datei abgelegt. Zur Laufzeit wird nur noch das Wasserzeichen eingestempelt
(das dauert unter einer Sekunde, siehe `BUCH-06`).

---

## PFLICHT-CHECK

```bash
git remote -v && git branch --show-current
```

---

## PROMPT FÜR CLAUDE CODE

```
Führe zuerst aus: git remote -v && git branch --show-current
Erwartet: origin = nachhaltika-arch/Claude-Code, branch = claude/kompagnon-automation-system-FapM9
Bei Abweichung: stoppe und melde.

ZIEL
Eine Build-Pipeline, die aus buch/manuskript/*.md zwei PDFs erzeugt.
Der Build laeuft NICHT im FastAPI-Backend zur Laufzeit, sondern als eigenstaendiges
Python-Skript. Baue keinen API-Endpunkt dafuer.

SCHRITT 1 — Abhaengigkeiten
Lege buch/requirements-build.txt an:
  markdown==3.6
  weasyprint==62.3
  pypdf==4.2.0
  pyyaml==6.0.1
Ergaenze buch/README.md um die Installationsanleitung inklusive der
WeasyPrint-Systemabhaengigkeiten fuer Windows (GTK3 Runtime).

SCHRITT 2 — Layout
Lege buch/layout/print.css und buch/layout/screen.css an.

Gemeinsame Vorgaben (Corporate Design KOMPAGNON):
  --kc-dark:   #004F59
  --kc-mid:    #008EAA
  --kc-yellow: #FAE600
  Schrift: Noto Sans. Headlines Noto Sans Black, Fliesstext Noto Sans Regular.
  Die Schriftdateien werden lokal in buch/assets/fonts/ eingebunden, NICHT ueber
  eine Google-Fonts-URL. Das ist zwingend (Datenschutz + Offline-Build).

print.css:
  @page { size: 170mm 240mm; margin: 20mm 18mm 22mm 18mm; bleed: 3mm; marks: crop cross; }
  Spiegelnde Innenraender: @page :left / :right mit 22mm innen, 16mm aussen.
  Kolumnentitel: links Buchtitel, rechts Kapitelname.
  Seitenzahlen unten aussen, ab Kapitel 1 (Titelei ohne Zahl).
  Fliesstext 10,5pt / Zeilenabstand 1,45.
  Kapitelanfaenge immer auf rechter Seite (break-before: right).
  Farben: Ueberschriften in --kc-dark, Merkkaesten mit --kc-yellow Randlinie.

screen.css:
  @page { size: A4; margin: 20mm; } keine Beschnittmarken, keine gespiegelten Raender.
  Fliesstext 11pt. Links in --kc-mid und unterstrichen.

SCHRITT 3 — Build-Skript
Lege buch/build.py an. Funktionsweise:
  1. Liest buch/manuskript/*.md in alphabetischer Reihenfolge
  2. Parst den YAML-Frontmatter jeder Datei; bricht mit klarer Meldung ab,
     wenn eine Datei status: entwurf hat und --allow-draft nicht gesetzt ist
  3. Wandelt Markdown nach HTML (Extensions: tables, toc, attr_list, footnotes)
  4. Erzeugt automatisch ein Inhaltsverzeichnis mit Seitenzahlen
  5. Ersetzt Platzhalter: {{QR_AUDIT}} durch buch/assets/qr-audit.svg,
     {{VERSION}} durch version aus shared/homepage-standard.json
  6. Rendert per WeasyPrint nach buch/build/homepage-standard-screen.pdf
     und buch/build/homepage-standard-print.pdf
  7. Gibt am Ende aus: Seitenzahl je PDF, Dateigroesse, Anzahl Kapitel

Aufrufbar als:
  python buch/build.py --target screen
  python buch/build.py --target print
  python buch/build.py --target both

SCHRITT 4 — Druckvorstufen-Pruefung
Lege buch/check_print.py an. Prueft das Druck-PDF und meldet Verstoesse:
  - Seitenzahl durch 4 teilbar? (BoD-Anforderung fuer Bogenbindung)
  - Alle Schriften eingebettet? (per pypdf Font-Ressourcen auslesen)
  - Seitengroesse inkl. Beschnitt exakt 176x246 mm?
  - Mindestseitenzahl 48 erreicht?
Ausgabe als Liste OK/FEHLER, exit code 1 bei Fehlern.

SCHRITT 5 — buch/build/ in .gitignore
Fuege buch/build/*.pdf zu .gitignore hinzu. Die PDFs gehoeren nicht ins Repo
(Dateigroesse). Behalte buch/build/.gitkeep.

SCHRITT 6 — Verifikation
python buch/build.py --target both --allow-draft
python buch/check_print.py buch/build/homepage-standard-print.pdf
ls -lh buch/build/

SCHRITT 7
git add -A
git commit -m "Add book PDF build pipeline for screen and print output"
git push origin claude/kompagnon-automation-system-FapM9
```

---

## VERIFIKATION

| Prüfung | Erwartung |
|---|---|
| `ls -lh buch/build/` | zwei PDFs, Screen unter 15 MB |
| `python buch/check_print.py …` | alle Punkte OK |
| PDF öffnen, Seite 1 | Kapitelanfang auf rechter Seite |
| PDF öffnen, letzte Seite | Seitenzahl durch 4 teilbar |

**Häufigster Fehler:** WeasyPrint findet die Schriftdateien nicht und ersetzt sie
stillschweigend durch eine Systemschrift. Das PDF wird gebaut, sieht aber falsch aus und
`check_print.py` meldet nicht eingebettete Schriften. Prüfe das Ergebnis **immer optisch**.

---

## COMMIT-MESSAGE

```
Add book PDF build pipeline for screen and print output
```

---

## BoD-Spezifikationen (für den späteren Upload)

| Parameter | Wert |
|---|---|
| Format | 170 × 240 mm (Softcover, Standard-Fachbuch) |
| Beschnitt | 3 mm umlaufend → Dokument 176 × 246 mm |
| Farbraum Innenteil | Graustufen (günstiger) oder CMYK bei Farbabbildungen |
| Farbraum Cover | CMYK, Rückenbreite abhängig von Seitenzahl |
| Schriften | vollständig eingebettet, keine Subsetting-Lücken |
| Mindestumfang | 48 Seiten |
| Seitenzahl | durch 4 teilbar |

---

## ZWEI SCHRITTE VORAUS

- **Das Cover ist ein separates Dokument.** BoD verlangt Vorderseite, Rücken und Rückseite
  als ein einziges PDF, und die Rückenbreite hängt von der endgültigen Seitenzahl ab. Das
  Cover kann also erst gebaut werden, wenn der Innenteil final ist. Plane das ein — es ist
  der häufigste Grund für Verzögerungen bei Print-on-Demand.
- **Farbe im Innenteil vervierfacht die Druckkosten.** Bei 200 Seiten Farbe liegst du bei
  ~25 € Herstellungskosten, in Graustufen bei ~8 €. Bei 44 € Verkaufspreis ist das der
  Unterschied zwischen Marge und Nullsummenspiel. Empfehlung: Innenteil Graustufen,
  Diagramme so gestalten, dass sie ohne Farbe funktionieren (Muster statt Farbcodierung).
- **GitHub Actions später.** Sobald das Buch steht, lohnt ein Workflow, der bei jedem Push
  auf `buch/**` das Screen-PDF baut und als Artefakt anhängt. Dann siehst du Änderungen
  sofort im Layout, ohne lokal zu bauen.

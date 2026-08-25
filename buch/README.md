# Die Buch-Baustrecke

Setzt „Der Homepage Standard" aus dem Manuskript in zwei PDFs.

```bash
python3 -m venv buch/venv
buch/venv/bin/pip install -r buch/requirements-build.txt

buch/venv/bin/python buch/bauen.py --ziel beide --entwurf
buch/venv/bin/python buch/druckpruefung.py buch/build/homepage-standard-druck.pdf
```

| Datei | Format | Zweck |
|---|---|---|
| `build/homepage-standard-bildschirm.pdf` | A4 | Verkauf als Download |
| `build/homepage-standard-druck.pdf` | 170 × 240 mm | Vorlage für die Druckerei |

## Was Sie wissen sollten

**Gelesen wird aus dem Arbeitsordner des Manuskripts**, nicht aus einer Kopie
unter `buch/manuskript/`. `BUCH-03` sah eine Kopie vor; sie wäre die dritte
Fassung desselben Textes geworden. Die zweite ist am 25.08.2026 gelöscht
worden, nachdem sie mit der ersten auseinandergelaufen war.

**`--entwurf` ist Pflicht, solange die Kapitel `status: entwurf` tragen.** Ohne
den Schalter bricht der Bau ab — sonst entstünde unbemerkt ein Verkaufs-PDF
aus unfertigem Text. Alle 21 Kapitel tragen ihn derzeit.

**ReportLab statt WeasyPrint.** `BUCH-03` sah WeasyPrint vor; das rendert über
Pango und braucht Systembibliotheken, die weder auf diesem Rechner noch in der
CI liegen. ReportLab steht ohnehin im Backend, braucht keine, und
`satzmuster.py` setzt denselben Satzspiegel bereits damit.

**Der Bau läuft nicht im Dienst.** Zweihundert Seiten zu setzen hielte einen
Worker fest; bei drei gleichzeitigen Bestellungen stünde das Backend.
Ausgeliefert wird eine fertig gebaute Datei (`BUCH-06`).

## Was der Satz aus dem Manuskript liest

| Form im Manuskript | Im Buch |
|---|---|
| `::: MRG` … `:::` | Marginalie in der Randspalte, außen, auf Höhe der Textstelle |
| `::: ABB 3.1` … `:::` | maßhaltiger Platzhalter — damit die Seitenzahl stimmt |
| `<!-- SEITENUMBRUCH -->` | ein gesetzter Umbruch |
| `<!-- REDAKTIONELLE ANMERKUNGEN … -->` | Schnittkante: alles danach fällt weg |
| YAML-Vorspann | Kapitelnummer, Teil, Titel, `status`, `zielumfang` |

## Grenzen

* **Marginalien können sich überlagern**, wenn zwei dicht hintereinander
  stehen. Sie haben keine eigene Höhe im Textfluss — anders bekäme man sie
  nicht auf die Höhe ihrer Textstelle.
* **Die Seitenzahl ist noch nicht durch vier teilbar** (B6.5). Das ist ein
  Schritt der Produktion, kein Fehler des Satzes — deshalb füllt die
  Baustrecke nicht von selbst auf.
* **Kein PDF/X-3, keine Beschnittzugabe, keine Schnittmarken.** Für die
  Vorlage an BoD kommt beides dazu, sobald das Format entschieden ist (B6.3).

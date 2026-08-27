# Die Buch-Baustrecke

Setzt „Der Homepage Standard" aus dem Manuskript in PDFs.

```bash
python3 -m venv buch/venv
buch/venv/bin/pip install -r buch/requirements-build.txt

buch/venv/bin/python buch/bauen.py --ziel beide --entwurf
buch/venv/bin/python buch/bauen.py --ziel druck-a4 --entwurf
buch/venv/bin/python buch/druckpruefung.py buch/build/homepage-standard-druck.pdf
```

| Ziel | Datei | Format | Zweck |
|---|---|---|---|
| `bildschirm` | `build/homepage-standard-bildschirm.pdf` | A4 | Verkauf als Download |
| `druck` | `build/homepage-standard-druck.pdf` | 170 × 240 mm | Vorlage für die Druckerei |
| `druck-a4` | `build/homepage-standard-druck-a4.pdf` | A4 | dasselbe Buch als A4-Band |

`--ziel beide` baut `bildschirm` und `druck` — die beiden Fassungen, die das
Buchkonzept vorsieht. `druck-a4` ist ausdrücklich zu nennen.

**`druck-a4` ist nicht `bildschirm`.** Beide sind A4, und mehr haben sie nicht
gemeinsam. `bildschirm` ist ein Lesedokument: ein Block über die ganze Seite,
kein Bund, keine Marginalspalte, 11 pt auf 15,5 pt. `druck-a4` ist der
Buchsatzspiegel des Satzmusters, auf A4 aufgezogen — gespiegelte Ränder,
Marginalspalte, Kolumnentitel, Vakatseiten vor jedem Kapitel, 10 pt auf 13 pt
wie im Druck. Wer den A4-Band drucken lassen will, nimmt `druck-a4`; wer die
Datei zum Download verkauft, `bildschirm`.

**Der Schriftgrad wächst nicht mit.** A4 ist 23,5 % breiter als 170 × 240. Die
Schrift mitzuziehen hieße, das Schriftbild zu ändern, das abgenommen ist; also
bleiben 10 pt auf 13 pt, die Hauptspalte wächst nur von 95 auf 115 mm
(≈ 64 Zeichen), und der übrige Platz geht an Marginalspalte und Ränder. Die
Maße stehen in `buch/layout/satzspiegel.py`, kommentiert und mit Summenprobe.

> **Das Buchkonzept 1.2 nennt weiterhin 17 × 24 cm als Zielformat**, und 1.2
> begründet das auch: breit genug für die fünfspaltigen Tabellen, „schmal
> genug, um noch als Buch und nicht als Ordner zu wirken". `druck-a4` hebt
> diese Entscheidung nicht auf — es stellt eine zweite Fassung daneben. Wer A4
> zum Zielformat macht, ändert das Buchkonzept zuerst; jedes Format braucht
> zudem eine eigene ISBN (Buchkonzept 0.4).

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

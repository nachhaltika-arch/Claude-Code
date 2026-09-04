# Der Systemdurchlauf — ein Verfahren, kein Werkzeug

> **Wozu.** Bisher entstanden Lücken aus Anlässen: Etwas fiel auf, jemand
> maß nach, es wurde eine L-Nummer. Das findet, was auffällt — und lässt
> liegen, was still ist. Der Durchlauf dreht die Richtung um: Er fragt in
> fester Reihenfolge dieselben Fragen an dasselbe System und legt vor, was
> sich seit dem letzten Mal geändert hat.

## Die Regel, die alles andere trägt

**Ein Durchlauf, der jede Woche dieselbe Liste vorlegt, wird nach dem
zweiten Mal nicht mehr gelesen.** Deshalb steht zwischen Messung und Bericht
ein Filter, nicht nur ein Zähler. Drei Dinge gehen nicht in den Bericht:

1. was schon als offene L-Nummer geführt wird,
2. was einmal als „kein Befund" abgeräumt wurde (`docs/durchlauf/quittiert.json`),
3. was keinen Beleg hat — Datei und Zeile, oder eine Messung mit Zahl.

Punkt 3 ist keine Formalie. Ein Befund ohne Beleg wird verworfen, nicht
abgeschwächt: Er kostet sonst beim Nachprüfen mehr Zeit, als er beim Finden
gespart hat.

Eine vierte Klasse geht **immer** in den Bericht, ganz oben: der
**Rückfall** — ein Gegenstand, den die Lückenliste als erledigt führt und den
die Messung wiederfindet. Er ist das Gefährlichste, was ein Durchlauf finden
kann, weil die Liste in diesem Punkt lügt.

## Die sieben Schritte

    1  Erheben     jede Stufe misst ihre Fehlerklasse
    2  Belegen     ohne Datei:Zeile oder Messwert fällt der Befund raus
    3  Nachprüfen  Stichprobe am Gegenstand, bevor irgendetwas gemeldet wird
    4  Abgleichen  steht der Gegenstand schon als L-Nummer? Rückfall?
    5  Quittieren  ist er früher abgeräumt worden?
    6  Berichten   ein Dokument, nach Ebenen sortiert, mit Beleg je Zeile
    7  Übernehmen  von Hand: du entscheidest, was L-Nummer wird

**Schritt 3 ist nicht optional, und er ist derjenige, der beim Bauen dieses
Verfahrens am meisten gebracht hat.** Der erste Lauf meldete `GET /` als
doppelt registriert; nachgesehen lagen die zwei Fundstellen in verschiedenen
Routern, deren Präfix erst bei der Registrierung entsteht — die Messung hatte
einen leeren Präfix angenommen. Der zweite Lauf meldete `/app/kas-website`
als „Seite nicht gefunden"; die Route existiert, sie liegt unter
`/app/settings/`, und der Pfadaufbau hatte die Verschachtelung ignoriert.
**Beide Befunde wären als Systemfehler in der Lückenliste gelandet.** Beide
waren Fehler der Messung.

**Schritt 7 ist bewusst nicht automatisch.** Eine Liste, die sich selbst
verlängert, wächst schneller, als sie jemand abarbeitet; die echten offenen
Punkte gehen darin unter. Genau deshalb gibt es seit dem 01.09. den Zustand
*terminiert*.

## Die Stufen und was jede findet

Jede Stufe misst **eine** Fehlerklasse, und jede dieser Klassen hat hier schon
einmal Schaden angerichtet. Das ist der Maßstab für die Aufnahme einer
Prüfung: Sie kommt dazu, wenn sie einen Fehler gefunden hätte, der wirklich
passiert ist — nicht, weil sie sich gut liest.

| Stufe | Ebene | Findet | Vorbild |
|---|---|---|---|
| Doppelte Routen | Schnittstelle | zwei Verfahren auf einer Adresse; FastAPI bedient die erste und verschweigt die zweite | L-76 |
| Namensdrift Umgebung | Konsistenz | derselbe Schlüssel unter zwei Namen, einer davon nirgends gesetzt | L-43 |
| Umgebung ohne Blueprint | Konsistenz | Variable wird gelesen, steht in keinem Blueprint | L-42 |
| Felder ohne Leser | Datenbank | gespeichert, anklickbar, serialisiert — und von keinem Lesepfad abgefragt | L-05, L-55 |
| Seiten ohne Route | Frontend | Seitendatei, die `App.jsx` nicht einbindet | — |
| Farben außerhalb der Vorgabe | Optik | Markenfarben, die die Palette nicht kennt; Beinahe-Töne daneben | L-17, L-32 |
| Dateien über der Grenze | Konsistenz | Dateien über der doppelten 800-Zeilen-Grenze | L-25 |
| Laufzeit (Browser) | Browser | Antwortcode, Netzfehler, Konsolenfehler, leere Seite, Bildschirmfoto | L-41, L-53 |

## Der Verbindungs-Check, auf den Durchlauf abgebildet

    Datenbank hat den Wert        → Stufe „Felder ohne Leser"
          ↓
    Schnittstelle liefert ihn aus → Stufe „Doppelte Routen"; `unaufgerufene-routen.py`
          ↓
    Frontend hat eine Adresse     → `tests/test_frontend_adressen.py`, `tools/adressen.py`
          ↓
    Etwas ist im Browser sichtbar → Stufe „Laufzeit": sichtbarer Text je Seite

Die vierte Zeile ist die, die sonst durchrutscht. Ein Backend, das 200
liefert, und ein Frontend, das baut, ergeben zusammen eine leere Seite, ohne
dass irgendwo ein Fehler steht. Der Durchlauf zählt deshalb **sichtbare
Zeichen** je Seite und meldet alles unter der Schwelle als Befund.

## So läuft er

```bash
# 1 — die statischen Stufen (überall, ohne Netz, Sekunden)
python3 scripts/systemdurchlauf.py

# 2 — die Laufzeitstufe (braucht Netz, Browser und eine Anmeldung)
kompagnon/backend/venv/bin/python scripts/durchlauf-laufzeit.py \
    --basis https://kompagnon-frontend-staging.onrender.com \
    --konto DEIN_KONTO --wort DEIN_WORT

# 3 — beides in einen Bericht
python3 scripts/systemdurchlauf.py --laufzeit docs/durchlauf/laufzeit-<datum>.json
```

Ergebnis: `docs/durchlauf/befund-<datum>.md` — der Bericht zum Abhaken, und
`befunde-<datum>.json` daneben für den nächsten Vergleich.

**Einen Befund dauerhaft abräumen:** seine Kennung (steht unter jedem
Eintrag) mit Grund in `docs/durchlauf/quittiert.json` eintragen. Der Grund
ist Pflicht — ohne ihn ist später nicht nachlesbar, warum eine Zeile fehlt.

```json
{ "farbe-beinahe/#0891b2": { "grund": "Cyan der Diagrammlegende, bewusst gesetzt", "am": "2026-09-04" } }
```

## Was der Durchlauf **nicht** kann

* **Er sieht nicht, ob ein Wert stimmt.** Er sieht, dass ein Feld gelesen
  wird, nicht, ob der richtige Inhalt darin steht.
* **Er urteilt nicht über Gestaltung.** Er misst Farben gegen die Vorgabe;
  ob eine Oberfläche gut ist, steht in `docs/ux-soll-ist-kas.md` und kommt
  von einem Menschen.
* **Er ersetzt die genaueren Einzelmessungen nicht.**
  `kompagnon/backend/tools/unaufgerufene-routen.py` liest die *geladene*
  Anwendung und ist damit genauer als jede Textmessung; der Durchlauf sagt
  das im Bericht und verweist darauf.
* **Er misst nur, was er erreicht.** Routen mit Platzhalter (`:id`,
  `:token`) brauchen einen echten Datensatz und werden als *nicht gemessen*
  ausgewiesen — nicht als in Ordnung.

Der letzte Punkt ist der wichtigste: **Nicht gemessen ist nicht dasselbe wie
in Ordnung.** Jeder Bericht führt am Ende auf, was er nicht gesehen hat.

## Wie oft

Der Vorschlag: **wöchentlich, montags**, und zusätzlich vor jedem Merge nach
`main`. Der wöchentliche Lauf findet Drift, der Lauf vor dem Merge findet,
was der letzte Sprint eingebaut hat. Beide dauern Sekunden, solange die
Laufzeitstufe getrennt läuft.

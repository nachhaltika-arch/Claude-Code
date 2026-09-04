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

## Die acht Schritte

    0  Selbstprobe findet jede Stufe noch ihr eigenes Beispiel?
    1  Erheben     jede Stufe misst ihre Fehlerklasse
    2  Belegen     ohne Datei:Zeile oder Messwert fällt der Befund raus
    3  Nachprüfen  Stichprobe am Gegenstand, bevor irgendetwas gemeldet wird
    4  Abgleichen  steht der Gegenstand schon als L-Nummer? Rückfall?
    5  Quittieren  ist er früher abgeräumt worden?
    6  Berichten   ein Dokument, nach Ebenen sortiert, mit Beleg je Zeile
    7  Übernehmen  von Hand: du entscheidest, was L-Nummer wird

**Schritt 0 steht vor allem anderen, und zwar aus einem Grund, der erst beim
Bauen sichtbar wurde.** Elf der siebzehn Stufen melden heute null Befunde. Das
kann Ruhe heißen oder Blindheit — von außen sind beide nicht zu
unterscheiden, und die zweite ist die gefährliche: Ein Durchlauf, der nichts
mehr sieht, meldet Frieden. Die Selbstprobe legt deshalb Beispieldateien an,
die genau die gesuchten Fehler *enthalten*, und lässt jede Stufe darauf los.
Findet eine ihr eigenes Beispiel nicht, steht das ganz oben im Bericht, vor
jedem Sachbefund.

Beim ersten Lauf hat sie sofort etwas gefunden: Die Stufe „Geheimnis in der
Adresse" kannte nur englische Wortteile — `secret`, `key`, `token`. In einem
Repo, dessen Variablen `schluessel` und `geheimnis` heißen, hätte sie **nie**
etwas gefunden und trotzdem jede Woche eine beruhigende Null gemeldet.

**Schritt 3 ist nicht optional, und er ist derjenige, der beim Bauen dieses
Verfahrens am meisten gebracht hat.** Der erste Lauf meldete `GET /` als
doppelt registriert; nachgesehen lagen die zwei Fundstellen in verschiedenen
Routern, deren Präfix erst bei der Registrierung entsteht — die Messung hatte
einen leeren Präfix angenommen. Der zweite Lauf meldete `/app/kas-website`
als „Seite nicht gefunden"; die Route existiert, sie liegt unter
`/app/settings/`, und der Pfadaufbau hatte die Verschachtelung ignoriert.
Beim Ausbau kamen vier weitere dazu: 34 „stille Ausfälle", von denen die
ersten beiden bewusst still waren und unter drei Zeilen Begründung standen;
15 Modelltabellen mit angeblich fehlenden Migrationen, obwohl neue
Datenbanken über die Modelle selbst entstehen; 30 „unbekannte Tabellen", weil
die Suche bei `UPDATE x SET feld` das *Feld* für den Tabellennamen hielt; und
vier fehlende Pakete, die als `dnspython`, `psycopg2-binary` und
`python-whois` längst eingetragen waren.

**Alle acht wären als Systemfehler in der Lückenliste gelandet.** Alle acht
waren Fehler der Messung. Das ist die Ausbeute von Schritt 3 an einem
einzigen Tag — und der Grund, warum er kein Ratschlag ist.

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
| Felder ohne Leser | Datenbank | gespeichert, angezeigt, nie gelesen | L-05, L-55 |
| Modell ohne Migration | Datenbank | Commit ändert das Modell, rührt keine Migration an | L-86, L-93 |
| SQL nennt unbekannte Tabelle | Datenbank | rohes SQL auf einer Tabelle, die kein Modell führt | L-93 |
| Doppelte Routen | Schnittstelle | zwei Verfahren auf einer Adresse | L-76 |
| Wächter lässt ohne Geheimnis durch | Schnittstelle | Prüfung gibt ohne Schlüssel wahr zurück | L-47, L-136 |
| Geheimnis in der Adresse | Schnittstelle | Schlüssel im Pfad statt im Kopf | L-98, L-103 |
| Stiller Ausfall im Schreibpfad | Schnittstelle | Fehler geschluckt, Erfolg gemeldet | L-36, L-141 |
| Routen ohne Aufrufer / ohne Anmeldung | Schnittstelle | an der geladenen Anwendung gemessen | L-105, L-51, L-67 |
| Seiten ohne Weg | Frontend | weder Route noch Aufrufer | — |
| Bedienelement ohne Wirkung | Frontend | Knopf ohne Handler und ohne Formularrolle | L-79 |
| Farben außerhalb der Vorgabe | Optik | Markenfarben ohne Palette, Beinahe-Töne daneben | L-17, L-32, L-158 |
| Namensdrift Umgebung | Konsistenz | ein Schlüssel unter zwei Namen | L-43 |
| Umgebung ohne Blueprint | Konsistenz | Variable gelesen, in keinem Blueprint | L-42, L-156, L-157 |
| Import ohne Eintrag | Konsistenz | der nächste Neuaufbau scheitert | L-57 |
| Prüftor mit Lücke | Konsistenz | das Tor prüft weniger, als es verspricht | L-78 |
| Termine fremder Dienste | Konsistenz | angekündigte Abschaltung läuft ab | L-81 |
| Dateien über der Grenze | Konsistenz | über der doppelten 800-Zeilen-Grenze | L-25 |
| Laufzeit (Browser) | Browser | Antwortcode, Netzfehler, Konsolenfehler, leere Seite | L-41, L-53 |

## Drei Bedarfsklassen — und warum das im Bericht steht

Nicht jede Stufe läuft überall. Jede nennt deshalb, was sie braucht:

| Bedarf | Was nötig ist | Wie lange |
|---|---|---|
| `quelltext` | nichts außer dem Repo | Sekunden |
| `anwendung` | `kompagnon/backend/venv` mit den Abhängigkeiten | ~1 Minute |
| `dienst` | erreichbarer Dienst, Browser, Anmeldung | Minuten |

Die Stufen der Klasse `anwendung` messen an der **geladenen** Anwendung und
sehen damit, was aus dem Quelltext nicht ableitbar ist: eine Sperre, die am
Router hängt statt am Funktionskopf, und einen Präfix, der erst bei der
Registrierung entsteht. Sie sind genauer als alles, was eine Textmessung
könnte — deshalb ruft der Durchlauf die vorhandenen Werkzeuge auf, statt sie
nachzubauen.

Fehlt eine Voraussetzung, erscheint die Stufe im Bericht unter **„Nicht
gemessen — und das ist nicht dasselbe wie in Ordnung"**, mit Grund. Eine
nicht erhobene Zahl darf nie als Null im Bericht stehen.

## Was keine Maschine beantwortet

Vier der siebzehn Fehlerklassen aus der Lückenliste lassen sich nicht messen:
ob eine Messung misst, was sie verspricht (L-107, L-150 bis L-155); ob eine
Oberfläche verständlich ist; ob Lizenz und Rechtstexte tragen (L-148, L-149,
L-122); ob sich eine Sicherung wirklich zurückspielen lässt.

Sie verschwinden deshalb nicht, sondern stehen in
`docs/durchlauf/pruefliste.json` — jede mit einem Intervall und dem Datum der
letzten Beantwortung. Der Bericht führt am Ende auf, welche fällig sind. Wer
eine beantwortet, trägt das Datum ein; dann ist sie bis zum nächsten Mal weg.

Ebenso `docs/durchlauf/termine.json`: angekündigte Abschaltungen fremder
Dienste. Der Durchlauf ist der Wecker, damit ein Termin nicht als Zettel
endet, den niemand wiederfindet.

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
# 0 — misst der Durchlauf überhaupt noch? (einzeln aufrufbar)
python3 -m tools.durchlauf.selbstprobe

# 1 — die statischen Stufen (überall, ohne Netz, Sekunden)
python3 scripts/systemdurchlauf.py
python3 scripts/systemdurchlauf.py --nur quelltext   # nur, was ohne Umgebung geht

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

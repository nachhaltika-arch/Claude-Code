# -*- coding: utf-8 -*-
"""Der Durchlauf-Pruefer misst richtig — in beide Richtungen (L-17).

**Der Befund vom 07.09.2026.** Der Systemdurchlauf meldete „54 Felder ohne
Beschriftung", „1 Bild ohne Alternativtext" und frueher „15 Knoepfe ohne
Handler". Nachgesehen an den genannten Zeilen war **keiner davon echt** — und
fuer jeden gab es bereits eine dokumentierte Korrektur, die nur nie in
`tools/durchlauf/barrierefreiheit.py` gewandert ist:

1. **Das Tag wird am Pfeil zerschnitten.** `<input\\b[^>]*>` findet bei
   `onChange={() => set(x)}` das `>` des Pfeils und liest nur den Anfang des
   Tags. Alles danach — `aria-label`, `id`, `placeholder` — ist unsichtbar.
   `bauwerk._tag_ende` zaehlt seit dem 26.08. geschweifte Klammern mit und
   haelt in seinem eigenen Kommentar fest, dass genau dieser Fehler „fuenfzehn
   Knoepfe ohne Handler" meldete, „von denen der erste einen hatte".
2. **Ein umschliessendes `<label>` zaehlt nicht.** `<label><span>Name</span>
   <input …/></label>` ist implizit verknuepft und wird vorgelesen. L-17 hat
   diesen Messfehler am 21.08. schon einmal korrigiert: „23 der angeblich
   namenlosen Felder stehen innerhalb eines `<label>` — die richtige Zahl war
   358, nicht 381."
3. **`<img>` ohne `src` ist kein Bild.** In `AcademyAdminLesson.jsx` steht
   `Fuege Bilder mit <img>-Tags ein.` als **Hilfetext**. L-17: „Mit der
   Bedingung „muss ein `src` haben" sind es null echte Faelle."

**Warum das mehr ist als eine falsche Zahl.** Ein Pruefwerkzeug, dessen
Meldungen sich beim Nachsehen aufloesen, wird nach der dritten Meldung nicht
mehr gelesen. Danach ist es egal, ob es recht hat. Die Selbstprobe deckte das
nicht ab: Sie pflanzt Fehler und prueft, ob der Pruefer sie **findet** — die
Gegenrichtung, ob er Korrektes in Ruhe laesst, hat nie jemand gemessen.
"""
import importlib.util
import sys
from pathlib import Path

import pytest

WURZEL = Path(__file__).resolve().parents[3]
ORDNER = WURZEL / "tools" / "durchlauf"
#: Eigener Paketname, damit nichts kollidiert.
PAKET = "kompagnon_durchlauf"


def _durchlauf_modul(name: str):
    """Unter eigenem Namen geladen, nicht ueber den Suchpfad.

    `import tools.durchlauf` faende hier das **falsche** Paket: Im Backend
    liegt ein regulaeres `tools` mit `__init__.py`, im Wurzelverzeichnis nur
    ein Namensraum — und ein regulaeres Paket gewinnt gegen einen Namensraum
    unabhaengig von der Reihenfolge im Suchpfad. Ein Test, der still das
    falsche Modul prueft, waere schlimmer als keiner.

    Deshalb wird `tools/durchlauf` als eigenstaendiges Paket unter dem Namen
    `kompagnon_durchlauf` registriert; die relativen Importe darin (`.befund`)
    finden ihre Geschwister dann ueber diesen Namen.
    """
    if PAKET not in sys.modules:
        spec = importlib.util.spec_from_file_location(
            PAKET, ORDNER / "__init__.py",
            submodule_search_locations=[str(ORDNER)])
        paket = importlib.util.module_from_spec(spec)
        sys.modules[PAKET] = paket
        spec.loader.exec_module(paket)
    return importlib.import_module(f"{PAKET}.{name}")


bf = _durchlauf_modul("barrierefreiheit")

# --- Die positive Richtung: echte Fehler werden weiter gefunden. -----------

ECHT_OHNE_NAME = '<input value={x} onChange={y} />'
ECHT_OHNE_ALT = '<img src={bild} />'

# --- Die Gegenrichtung: korrekter Code loest keine Meldung aus. ------------

IM_LABEL = '<label><span>Firmenname</span><input value={x} onChange={y} /></label>'
PFEIL_DANACH = '<input onChange={() => set(x)} aria-label="Suche" />'
PFEIL_DAVOR = '<input onChange={(e) => set(e.target.value)} id="feld-1" />'
BILD_OHNE_SRC = 'Fuege Bilder mit <img>-Tags ein.'
DURCHGEREICHT = '<input {...props} style={s} />'
IM_KOMMENTAR = '{/* Kein <input> hier — die Bedienung liegt am role="checkbox". */}'


def _melden(inhalt: str, tmp_path, monkeypatch) -> str:
    """Den Pruefer auf genau eine Datei loslassen und die Notiz zurueckgeben."""
    datei = tmp_path / "Probe.jsx"
    datei.write_text(inhalt, encoding="utf-8")
    monkeypatch.setattr(bf, "_js_dateien", lambda: [datei])
    monkeypatch.setattr(bf, "kurz", lambda p: "Probe.jsx")
    return bf.fehlende_textalternativen()[1]


@pytest.mark.parametrize("inhalt,erwartet", [
    (ECHT_OHNE_NAME, "1 Felder"),
    (ECHT_OHNE_ALT, "1 Bilder"),
])
def test_echte_maengel_werden_gefunden(inhalt, erwartet, tmp_path, monkeypatch):
    """Ohne diese Haelfte waere die Reparatur nur ein leiser Pruefer."""
    assert erwartet in _melden(inhalt, tmp_path, monkeypatch)


@pytest.mark.parametrize("inhalt,warum", [
    (IM_LABEL, "implizit ueber das umschliessende <label> verknuepft"),
    (PFEIL_DANACH, "aria-label steht hinter einer Pfeilfunktion"),
    (PFEIL_DAVOR, "id steht hinter einer Pfeilfunktion"),
    (DURCHGEREICHT, "der Name kommt zur Laufzeit ueber {...props}"),
    (IM_KOMMENTAR, "das <input> steht in einem Kommentar, der erklaert, dass "
                   "dort keines ist"),
])
def test_korrekte_felder_loesen_keine_meldung_aus(inhalt, warum, tmp_path, monkeypatch):
    assert "0 Felder ohne Beschriftung" in _melden(inhalt, tmp_path, monkeypatch), warum


def test_ein_img_ohne_src_ist_kein_bild(tmp_path, monkeypatch):
    assert "0 Bilder ohne alt" in _melden(BILD_OHNE_SRC, tmp_path, monkeypatch)


def test_am_lebenden_bestand_bleibt_nichts_von_den_falschtreffern(tmp_path, monkeypatch):
    """Die Probe aufs Exempel — gemessen am echten Quellbaum, nicht an Mustern.

    Die drei gemeldeten Stellen aus dem Durchlauf vom 06.09. sind einzeln
    nachgesehen worden: `MitwirkungAktion.jsx` 94/105/180 und `Settings.jsx`
    176/179 stehen alle in einem `<label>`. Bleibt nach der Reparatur eine
    Zahl stehen, ist sie echt und gehoert abgearbeitet — dieser Test haelt
    fest, was heute uebrig ist, damit die naechste Aenderung sie nicht
    unbemerkt erhoeht.
    """
    _, notiz = bf.fehlende_textalternativen()
    felder = int(notiz.split(" Felder")[0].split(", ")[-1])
    assert felder <= OBERGRENZE_FELDER, (
        f"{felder} Felder ohne Beschriftung — die Ratsche stand bei "
        f"{OBERGRENZE_FELDER}. Entweder ist ein echter Mangel dazugekommen "
        f"oder die Messung meldet wieder Falschtreffer.")


#: Ratsche, nicht Ziel — sie verbietet mehr, sie verlangt nicht null. Eine
#: Schranke bei null waere am ersten Tag abgeschaltet worden.
OBERGRENZE_FELDER = 0

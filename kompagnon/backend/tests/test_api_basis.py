# -*- coding: utf-8 -*-
"""Das Frontend darf nicht auf sich selbst zeigen (L-145).

**Der Vorfall.** Am 2026-08-28 stand `REACT_APP_API_URL` am Dienst
`kompagnon-frontend` auf `https://kas.kompagnon.group` — auf das Frontend
selbst. Jede API-Anfrage bekam HTML statt JSON, die Oberflaeche meldete
„Verbindungsfehler", und produktiv war 40 Minuten niemand anmeldbar. Das
Backend war die ganze Zeit gesund; `/health` antwortete in 0,19 s.

**Was dieser Waechter kann und was nicht.** Er liest Dateien — den Rueckfall
im Quelltext und den Blueprint. Ob der **laufende Dienst** den richtigen Wert
gesetzt hat, kann er nicht sagen; genau das war am 28.08. der Fehler, und
dafuer gibt es `tools/api_basis_pruefen.py`, das die ausgelieferten Pakete
abruft. Ein Waechter, der so tut, als pruefe er die Wirklichkeit, waere
schlimmer als keiner.

**Warum trotzdem Zusicherungen ohne Netz nuetzlich sind.** Der Fehler hat drei
Vorstufen, die alle im Repo sichtbar sind: ein Rueckfall, der auf eine
Frontend-Adresse zeigt; ein Blueprint, der es falsch beschreibt; und eine
zweite, eigene Definition der API-Basis, die den Rueckfall umgeht. Die dritte
gab es wirklich — `NewProjectModal.jsx` las die Variable selbst und fiel auf
`""` zurueck, also auf die eigene Herkunft. Fuenf Aufrufe dieser Komponente
haetten den Ausfall vom 28.08. dauerhaft gehabt, sobald die Variable fehlt.

**Dazu wird die Pruefroutine selbst geprueft** — gegen ein gesundes Paket,
gegen das kaputte vom 28.08. und gegen eines, in dem sich die Basis nicht
bestimmen laesst. Der letzte Fall ist der wichtigste: Ein Waechter, der beim
Nichtmessen gruen bleibt, ist schlimmer als keiner.
"""
import re
from pathlib import Path

import pytest

WURZEL = Path(__file__).resolve().parent.parent.parent          # kompagnon/
QUELLE = WURZEL / "frontend" / "src"
CONFIG = QUELLE / "config.js"
BLUEPRINT = WURZEL / "render-produktiv.yaml"

# `tools` ist ein Paket neben diesem Verzeichnis — es wird als Paket
# importiert und **nicht** ueber `sys.path` eingehaengt. Der Versuch, den
# Ordner vorn auf den Suchpfad zu setzen, hat beim Bauen dieses Tests die
# Sammelphase der gesamten Suite zerlegt (129 Fehler): Alles unter `tools/`
# waere damit auch als oberste Ebene importierbar und verschattet, was der
# Backend-Wurzel gehoert. Einzeln lief die Datei trotzdem — der Schaden
# zeigte sich erst im Gesamtlauf.
from tools.api_basis_pruefen import (                            # noqa: E402
    UMGEBUNGEN, ZWEITNAME, basis_aus_paket, pruefe_paket,
)

#: Alle Adressen, unter denen ein Frontend ausgeliefert wird. Keine davon darf
#: je als API-Basis auftauchen.
FRONTEND_HERKUENFTE = tuple(sorted(
    {h for _, h, _ in UMGEBUNGEN} | set(ZWEITNAME)))

PRODUKTIV_BACKEND = "https://api.kompagnon.group"


def ohne_kommentare(quelltext: str) -> str:
    """Kommentare weg, bevor gezaehlt wird.

    **Warum das hier steht.** Beim Bauen dieses Waechters ist er ueber die
    eigene Reparatur gestolpert: Die Notiz in `NewProjectModal.jsx`, die
    *erklaert*, warum die Variable dort nicht mehr gelesen wird, enthaelt
    ihren Namen — und wurde mitgezaehlt. Ein Waechter, der Kommentare fuer
    Code haelt, meldet jede Erklaerung als Verstoss und wird abgeschaltet.
    """
    quelltext = re.sub(r"/\*.*?\*/", "", quelltext, flags=re.S)
    return re.sub(r"^\s*//.*$", "", quelltext, flags=re.M)


def test_rueckfall_zeigt_auf_das_backend_und_nicht_auf_ein_frontend():
    """Fehlt die Variable, muss der Quelltext das Backend nennen."""
    # Arrange
    text = CONFIG.read_text(encoding="utf-8")

    # Act
    treffer = re.search(r"REACT_APP_API_URL\s*\|\|\s*\n?\s*['\"]([^'\"]*)['\"]", text)

    # Assert
    assert treffer, "config.js nennt keinen Rueckfall fuer REACT_APP_API_URL"
    rueckfall = treffer.group(1)
    assert rueckfall == PRODUKTIV_BACKEND, (
        f"Rueckfall ist {rueckfall!r}, erwartet {PRODUKTIV_BACKEND!r}")
    assert rueckfall not in FRONTEND_HERKUENFTE, (
        "der Rueckfall zeigt auf ein Frontend — das ist der Ausfall vom 28.08.")


def test_es_gibt_genau_eine_definition_der_api_basis():
    """Eine zweite Definition umgeht den Rueckfall — und faellt auf `""`.

    `NewProjectModal.jsx` tat das bis zum 28.08.2026: `|| ""` heisst relative
    Adresse, also die eigene Herkunft. Der Rueckfall in `config.js` half dort
    nicht, weil die Datei ihn nie gelesen hat.
    """
    # Arrange
    dateien = [p for p in QUELLE.rglob("*.js*")
               if p.suffix in (".js", ".jsx") and "node_modules" not in p.parts]

    # Act
    eigenbau = [p.relative_to(QUELLE) for p in dateien
                if "process.env.REACT_APP_API_URL" in ohne_kommentare(
                    p.read_text(encoding="utf-8"))
                and p != CONFIG]

    # Assert
    assert eigenbau == [], (
        "diese Dateien lesen REACT_APP_API_URL selbst statt aus config.js zu "
        f"importieren: {[str(p) for p in eigenbau]}")


def test_blueprint_beschreibt_die_produktive_api_basis_richtig():
    """Die Datei steuert nicht, aber sie darf nicht falsch beschreiben (L-35)."""
    # Arrange
    text = BLUEPRINT.read_text(encoding="utf-8")

    # Act
    treffer = re.search(
        r"-\s*key:\s*REACT_APP_API_URL\s*\n\s*value:\s*(\S+)", text)

    # Assert
    assert treffer, "render-produktiv.yaml beschreibt REACT_APP_API_URL nicht"
    wert = treffer.group(1).strip("\"'")
    assert wert == PRODUKTIV_BACKEND, f"Blueprint sagt {wert!r}"
    assert wert not in FRONTEND_HERKUENFTE


def test_die_pruefung_erkennt_das_gesunde_paket():
    """Positive Zusicherung — sonst waere alles Folgende wertlos."""
    # Arrange — so sieht das echte Modul aus, zu dem `config.js` wird
    paket = 'e.d(t,{A:()=>r});const r="https://api.kompagnon.group";var x=1;'

    # Act
    maengel = pruefe_paket(paket, PRODUKTIV_BACKEND)

    # Assert
    assert maengel == []
    assert basis_aus_paket(paket) == PRODUKTIV_BACKEND


def test_die_pruefung_faellt_ueber_das_kaputte_paket_vom_28_august():
    """Der Waechter muss die Zustaende **unterscheiden**, nicht nur gruen sein.

    Nachgebaut nach dem echten Fund `main.e1437f0f.js`: Die eigene Herkunft
    stand als API-Basis da, und `api.kompagnon.group` kam weiterhin vor — aber
    nur **innerhalb** einer laengeren Adresse in einem Anzeigetext, nie als
    blanke Herkunft.

    **Deshalb wird die Basis ausdruecklich gelesen und nicht gesucht.** Eine
    Teilstring-Suche nach dem erwarteten Backend haette es hier gefunden und
    den Ausfall durchgewinkt — der Beleg dafuer steht als letzte Zusicherung.
    """
    # Arrange
    paket = ('e.d(t,{A:()=>r});const r="https://kas.kompagnon.group";'
             'label:"API Checkout",url:"https://api.kompagnon.group/api/pay"')

    # Act
    maengel = pruefe_paket(paket, PRODUKTIV_BACKEND)

    # Assert
    assert len(maengel) == 1
    assert "https://kas.kompagnon.group" in maengel[0]
    assert basis_aus_paket(paket) == "https://kas.kompagnon.group"
    assert PRODUKTIV_BACKEND in paket, "sonst belegt der Test seinen Punkt nicht"


def test_unbestimmbare_basis_ist_ein_befund_und_kein_gruen():
    """Aendert der Minifizierer die Form, muss das auffallen.

    Der gefaehrlichste Waechter ist der, der beim Nichtmessen gruen bleibt —
    dieselbe Familie wie die vier Bauarten in `waechter_ohne_wirkung`.
    """
    # Arrange
    paket = 'irgendwas ohne das erwartete Modulmuster'

    # Act
    maengel = pruefe_paket(paket, PRODUKTIV_BACKEND)

    # Assert
    assert basis_aus_paket(paket) is None
    assert len(maengel) == 1
    assert "nicht bestimmen" in maengel[0]


def test_mehrdeutiges_paket_gilt_als_unbestimmbar():
    """Zwei verschiedene Treffer heissen: nicht gemessen, nicht geraten."""
    # Arrange
    paket = ('e.d(t,{A:()=>r});const r="https://api.kompagnon.group";'
             'e.d(t,{B:()=>q});const q="https://beispiel.invalid";')

    # Act & Assert
    assert basis_aus_paket(paket) is None


@pytest.mark.parametrize("name,herkunft,backend", UMGEBUNGEN)
def test_keine_umgebung_zeigt_auf_sich_selbst(name, herkunft, backend):
    """Die Zuordnung selbst darf nicht verrutschen."""
    assert herkunft != backend, f"{name}: Herkunft und Backend sind gleich"
    assert backend not in FRONTEND_HERKUENFTE, (
        f"{name}: {backend} ist eine Frontend-Adresse")

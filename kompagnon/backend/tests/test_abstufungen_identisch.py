# -*- coding: utf-8 -*-
"""
Der Beweis zu BUCH-F1: Die Punktabstufungen als Daten rechnen genau wie die
Bedingungen, die vorher im Programmtext standen.

Die Umstellung sollte **nur verschieben, wo** die Zahlen stehen — nicht,
**welche**. Behaupten laesst sich das leicht; dieser Test weist es nach. Die
Referenzwerte unten sind die alten Bedingungen aus `audit_scoring.py`,
buchstabengetreu uebernommen (Stand 25.08.2026, vor dem Umbau).

Geprueft wird an jeder Grenze **exakt**: `>= 90` und `> 90` unterscheiden sich
um genau einen Fall, und dieser eine Fall entscheidet ueber eine ganze Stufe.
"""
import pytest

from services.audit_criteria import Source, all_criteria, find_criterion
from services.audit_scoring import _Sheet, _nach_abstufung


# ── Die alten Bedingungen, wortgetreu ─────────────────────────────────

def _tier(value, thresholds):
    """Die geloeschte Hilfsfunktion — erste passende Schwelle, `value < limit`."""
    if value is None:
        return None
    for limit, points in thresholds:
        if value < limit:
            return points
    return 0


REFERENZ = {
    "tp_lcp": lambda v: _tier(v, ((2.5, 4), (4.0, 2))),
    "tp_cls": lambda v: _tier(v, ((0.1, 3), (0.25, 1))),
    "tp_inp": lambda v: _tier(v, ((200, 2), (500, 1))),
    "tp_mobile": lambda v: 3 if v >= 90 else (2 if v >= 70 else (1 if v >= 50 else 0)),
    "bf_lighthouse": lambda v: 3 if v >= 90 else (2 if v >= 75 else (1 if v >= 50 else 0)),
    "bf_alt": lambda v: 2 if v >= 95 else (1 if v >= 80 else 0),
    "cv_cta": lambda v: 3 if v >= 3 else (2 if v >= 1 else 0),
    "cv_vertrauen": lambda v: 3 if v >= 4 else (2 if v >= 2 else (1 if v >= 1 else 0)),
    "ih_leistungsseiten": lambda v: 2 if v >= 3 else (1 if v >= 1 else 0),
}

#: Die Grenzen je Kriterium — und zusaetzlich Werte weit ausserhalb, damit ein
#: vertauschtes `richtung` („bis" statt „ab") nicht unbemerkt bleibt.
GRENZEN = {
    "tp_lcp": (2.5, 4.0),
    "tp_cls": (0.1, 0.25),
    "tp_inp": (200, 500),
    "tp_mobile": (50, 70, 90),
    "bf_lighthouse": (50, 75, 90),
    "bf_alt": (80, 95),
    "cv_cta": (1, 3),
    "cv_vertrauen": (1, 2, 4),
    "ih_leistungsseiten": (1, 3),
}


def _pruefwerte(grenzen):
    """Unter, genau auf und ueber jeder Grenze — plus die Raender."""
    werte = [0, 0.5]
    for grenze in grenzen:
        werte += [grenze - 1, grenze - 0.01, grenze, grenze + 0.01, grenze + 1]
    werte.append(max(grenzen) * 10 + 1)
    return [w for w in werte if w >= 0]


def _punkte(key, wert):
    """Die Punktzahl, die die Bewertung heute vergibt."""
    sheet = _Sheet()
    _nach_abstufung(sheet, key, wert)
    return sheet.items[key]


# ── Gleichwertigkeit ──────────────────────────────────────────────────

@pytest.mark.parametrize("key", sorted(REFERENZ))
def test_die_datenform_rechnet_wie_die_alte_bedingung(key):
    for wert in _pruefwerte(GRENZEN[key]):
        assert _punkte(key, wert) == REFERENZ[key](wert), (
            f"{key} bei {wert}: Datenform {_punkte(key, wert)}, "
            f"alte Bedingung {REFERENZ[key](wert)}"
        )


@pytest.mark.parametrize("key", sorted(REFERENZ))
def test_nicht_erhoben_bleibt_nicht_erhoben(key):
    """`None` heisst 'nicht gemessen' — und darf nie zu null Punkten werden.

    Das ist der teuerste denkbare Fehler dieses Umbaus: Eine fehlende Messung
    als Mangel des Betriebs zu verkaufen. Genau dagegen richtet sich S8.1.
    """
    sheet = _Sheet()
    _nach_abstufung(sheet, key, None)
    assert sheet.sources[key] == Source.NOT_COLLECTED


def test_kleiner_ist_besser_bleibt_kleiner_ist_besser():
    """Die Richtung „bis" darf sich nicht umdrehen.

    Wer sie verwechselt, macht aus der schnellsten Seite die langsamste — im
    Bericht und in der gedruckten Tabelle.
    """
    assert _punkte("tp_lcp", 1.0) == 4
    assert _punkte("tp_lcp", 9.0) == 0
    assert _punkte("tp_mobile", 100) == 3
    assert _punkte("tp_mobile", 10) == 0


# ── Der Katalog selbst ────────────────────────────────────────────────

def test_jedes_bewertete_kriterium_hat_eine_abstufung():
    """Ohne sie kann das Buch die Tabelle des Kriteriums nicht drucken."""
    for criterion in all_criteria():
        assert criterion.abstufung is not None, criterion.key


def test_die_beste_stufe_ist_die_punktzahl_des_kriteriums():
    """Sonst druckt das Buch eine Tabelle, die der Katalog nicht kennt."""
    for criterion in all_criteria():
        stufen = criterion.abstufung.stufen
        if not stufen:
            continue
        if criterion.abstufung.art == "SUMME":
            assert sum(s.punkte for s in stufen) == criterion.max_points, criterion.key
        else:
            assert max(s.punkte for s in stufen) == criterion.max_points, criterion.key


def test_nur_die_zahlenbasierten_schwellen_gelten_als_berechenbar():
    """`si_ssl` und `rc_formular_dsgvo` sind Staffeln ohne Zahl.

    Sie stehen als Daten fuer das Buch da, gerechnet werden sie weiterhin im
    Programm. Wer sie faelschlich als berechenbar markiert, laesst die
    Bewertung mit einer Grenze rechnen, die es nicht gibt.
    """
    berechenbar = {c.key for c in all_criteria() if c.abstufung.berechenbar}
    assert berechenbar == set(REFERENZ)


def test_bedingungen_sind_saetze_und_keine_programmierkuerzel():
    """Der Text wird gedruckt — er muss ohne Code-Kenntnis lesbar sein."""
    for criterion in all_criteria():
        for stufe in criterion.abstufung.stufen:
            assert stufe.bedingung, criterion.key
            assert not any(z in stufe.bedingung for z in (">=", "<=", "==", "_")), (
                f"{criterion.key}: {stufe.bedingung!r}"
            )


def test_eine_nicht_berechenbare_abstufung_rechnet_nicht_heimlich():
    """Lieber ein Fehler als eine erfundene Punktzahl."""
    with pytest.raises(ValueError):
        find_criterion("si_ssl").abstufung.punkte_fuer(3)


# ── Verschluckte Stufen bei Anteilswerten (L-114, 31.08.2026) ─────────

#: Anteils-Skalierungen mit **abzaehlbarem** Nenner — `sheet.scale(key, n/N)`.
#:
#: Nur diese Form kann eine Stufe verschlucken. Die drei uebrigen
#: `scale`-Aufrufe (`bf_kontrast`, `bf_tastatur`, `dg_typografie`) reichen
#: einen stetigen Lighthouse-Wert durch; dort gibt es keinen Schritt, der
#: ausfallen koennte.
ANTEIL_MIT_NENNER = {"si_header": 4}

#: Wo eine Stufe heute ausfaellt — je mit dem Schritt, der nichts bringt.
#:
#: **Nicht zu beheben, sondern zu terminieren.** Jede Aenderung hier
#: verschiebt die Katalogsumme und gehoert deshalb in die Fassung 2027.1
#: (L-114). Bis dahin haelt dieser Eintrag den Befund fest, damit er weder
#: still verschwindet noch sich unbemerkt vermehrt.
VERSCHLUCKT = {"si_header": [3]}


def _punkte_je_stufe(key: str, nenner: int) -> list:
    """Was das Kriterium bei 0, 1, … `nenner` erfuellten Teilpruefungen gibt.

    Gerechnet wie `_Sheet.scale` — `round(anteil * max_points)`; nachgebaut
    statt aufgerufen waere hier falsch, denn geprueft werden soll genau diese
    Rundung.
    """
    hoechstens = find_criterion(key).max_points
    blatt = _Sheet()
    punkte = []
    for erfuellt in range(nenner + 1):
        blatt.scale(key, erfuellt / nenner, Source.MEASURED)
        punkte.append(blatt.items[key])
    return punkte


@pytest.mark.parametrize("key,nenner", sorted(ANTEIL_MIT_NENNER.items()))
def test_verschluckte_stufen_sind_die_bekannten(key, nenner):
    """Ein Anteil auf weniger Punkte als Teilpruefungen laesst Schritte ausfallen.

    `si_header` skaliert **vier** Header auf **drei** Punkte. Am Gegenstand
    gerechnet: 0→0, 1→1, 2→2, 3→2, 4→3. Wer den dritten Header nachruestet,
    bekommt dafuer **nichts** — und im Bericht steht trotzdem, dass er zaehlt.

    Der Test verbietet den Zustand nicht, er **beziffert** ihn. Kommt ein
    Schritt dazu oder faellt einer weg, wird er rot und verlangt eine
    Entscheidung statt einer stillen Verschiebung.
    """
    punkte = _punkte_je_stufe(key, nenner)
    ohne_wirkung = [n for n in range(1, nenner + 1) if punkte[n] == punkte[n - 1]]

    assert ohne_wirkung == VERSCHLUCKT.get(key, []), (
        f"{key}: {punkte} — Schritte ohne Wirkung {ohne_wirkung}, "
        f"erwartet {VERSCHLUCKT.get(key, [])}"
    )


def test_die_zusicherung_greift_ueberhaupt():
    """Die positive Gegenprobe.

    Ohne sie waere der Test darueber auch dann gruen, wenn `_punkte_je_stufe`
    immer dieselbe Zahl laeferte — und dann meldete er jeden Schritt als
    verschluckt, statt keinen. Genau so war der Kontrast-Waechter am 30.08.
    gruen: Er las eine Form, die es nicht mehr gab, und uebersprang alles.
    """
    punkte = _punkte_je_stufe("si_header", 4)

    assert punkte == [0, 1, 2, 2, 3], punkte
    assert punkte[-1] == find_criterion("si_header").max_points


def _nenner_aus_dem_bewertungslauf() -> dict:
    """Die abzaehlbaren Nenner, wie sie im Quelltext stehen.

    Gelesen wird der Bewertungslauf, nicht der Katalog: Der Nenner steht
    **dort** (`present / 4`) und nicht am Kriterium. Wer ihn nur in der
    Tabelle oben pflegt, prueft seine eigene Annahme statt des Programms.
    """
    import pathlib
    import re

    quelle = pathlib.Path(__file__).resolve().parents[1] / "services" / "audit_scoring.py"
    aufrufe = re.findall(r'sheet\.scale\(\s*"(\w+)",\s*([^,]+),',
                         quelle.read_text(encoding="utf-8"))
    assert aufrufe, "keine scale-Aufrufe gefunden — der Ausdruck trifft nicht mehr"

    gefunden = {}
    for key, wert in aufrufe:
        geteilt = re.search(r"/\s*(\d+)\s*$", wert.strip())
        if geteilt:
            gefunden[key] = int(geteilt.group(1))
    return gefunden


def test_die_nenner_stehen_im_programm_und_nicht_nur_in_dieser_tabelle():
    """Sonst waechst die Klasse, ohne dass jemand hinsieht — und der Test
    oben rechnete mit einem Nenner, den das Programm gar nicht benutzt."""
    assert _nenner_aus_dem_bewertungslauf() == ANTEIL_MIT_NENNER

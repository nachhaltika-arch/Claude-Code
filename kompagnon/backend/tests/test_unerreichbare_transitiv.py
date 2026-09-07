# -*- coding: utf-8 -*-
"""Unerreichbarkeit wird durchgereicht, nicht nur einen Sprung weit (L-95).

**Der Befund vom 07.09.2026.** `tools/unerreichbare-dateien.py` meldete
`src/data/allTemplates.js` — drei Zeilen. Diese Datei importiert `templates.js`
(146 Zeilen) und `templates_zusatz.js` (**3.121** Zeilen), und **niemand sonst**
importiert die beiden. Der ganze Strang haengt also in der Luft; gemeldet
wurden drei Zeilen statt 3.270.

**Warum.** `erreicht(pfad, anwendung)` fragte, ob **irgendeine**
Anwendungsdatei diese Datei importiert — einen Sprung weit. Dass die
importierende Datei selbst niemanden hat, der sie ruft, blieb ungeprueft. Eine
Kette unerreichbarer Dateien deckt sich damit gegenseitig zu: Je laenger sie
ist, desto weniger faellt auf.

**Warum das mehr ist als eine zu kleine Zahl.** `templates_zusatz.js` ist mit
3.121 Zeilen die groesste Datei im Frontend und steht in **L-25** als eine von
zwei ueber der 800-Zeilen-Grenze. L-25 sagt selbst: „**Und nicht zuerst die,
die niemand aufruft** — siehe L-95." Ohne diese Messung waere sie
aufgeteilt worden statt entschieden.
"""
import importlib.util
import sys
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[3]


def _werkzeug():
    """Ueber den Pfad geladen — der Dateiname traegt einen Bindestrich und
    laesst sich nicht importieren."""
    pfad = WURZEL / "tools" / "unerreichbare-dateien.py"
    spec = importlib.util.spec_from_file_location("unerreichbare_dateien", pfad)
    modul = importlib.util.module_from_spec(spec)
    sys.modules["unerreichbare_dateien"] = modul
    spec.loader.exec_module(modul)
    return modul


W = _werkzeug()


def _bereich(ordner: Path) -> dict:
    return {
        "wurzel": ordner,
        "endungen": (".js", ".jsx"),
        "ist_test": W.frontend_ist_test,
        "einstiege": {"index"},
        "einstiegs_ordner": (),
        "sprache": "javascript",
    }


def test_eine_kette_unerreichbarer_dateien_wird_ganz_gemeldet(tmp_path):
    """Der Fall aus dem Bestand, nachgebaut.

    `index.js` ruft nur `Gebraucht.js`. `Kette1` importiert `Kette2`, und
    `Kette1` selbst ruft niemand — beide gehoeren gemeldet.
    """
    (tmp_path / "index.js").write_text(
        "import { a } from './Gebraucht';", encoding="utf-8")
    (tmp_path / "Gebraucht.js").write_text("export const a = 1;", encoding="utf-8")
    (tmp_path / "Kette1.js").write_text(
        "import { b } from './Kette2';\nexport const c = b;", encoding="utf-8")
    (tmp_path / "Kette2.js").write_text("export const b = 2;", encoding="utf-8")

    unerreichbar, _nur_tests, _n = W._pruefe(_bereich(tmp_path))
    gemeldet = {p.name for _zeilen, p in unerreichbar}
    assert "Kette1.js" in gemeldet, "die Wurzel der Kette fehlt"
    assert "Kette2.js" in gemeldet, (
        "Kette2.js wird nur von Kette1.js importiert, und die erreicht niemand "
        "— genau der Fall, den die Messung einen Sprung weit uebersah.")
    assert "Gebraucht.js" not in gemeldet


def test_was_der_einstieg_ueber_zwei_ecken_erreicht_bleibt_draussen(tmp_path):
    """Die Gegenrichtung — sonst meldete das Werkzeug bald alles.

    Ohne diese Haelfte waere eine Umstellung auf „nur direkte Einstiege
    zaehlen" ebenso gruen und vollkommen unbrauchbar.
    """
    (tmp_path / "index.js").write_text("import { e } from './Eins';", encoding="utf-8")
    (tmp_path / "Eins.js").write_text(
        "import { z } from './Zwei';\nexport const e = z;", encoding="utf-8")
    (tmp_path / "Zwei.js").write_text(
        "import { d } from './Drei';\nexport const z = d;", encoding="utf-8")
    (tmp_path / "Drei.js").write_text("export const d = 1;", encoding="utf-8")

    unerreichbar, nur_tests, _n = W._pruefe(_bereich(tmp_path))
    assert not unerreichbar and not nur_tests, (
        f"ueber drei Ecken erreichbar, trotzdem gemeldet: "
        f"{[p.name for _z, p in unerreichbar + nur_tests]}")


def test_der_vorlagenstrang_im_bestand_wird_gemeldet():
    """Am Gegenstand, nicht am Muster.

    Drei gruene Testbeispiele sagen noch nicht, dass der echte Fall auffaellt.
    """
    unerreichbar, _nur_tests, _n = W._pruefe(W.BEREICHE["frontend"])
    gemeldet = {p.name for _zeilen, p in unerreichbar}
    for datei in ("allTemplates.js", "templates.js", "templates_zusatz.js"):
        assert datei in gemeldet, f"{datei} fehlt in der Meldung"

"""Die Produktvorlage stand zweimal in `main.py` (L-29, 22.08.2026).

**Der Befund.** Beim Nachzaehlen der Preisstellen ueber **alle** Dateien fiel
auf, dass der Block „Produkte seeden (nur wenn Tabelle leer)" in `main.py`
**zweimal hintereinander** steht — rund 75 Zeilen, wortgleich bis auf
Zeilenumbrueche.

**Warum das keine harmlose Doppelung ist.** Der zweite Block ist wirkungslos:
Er prueft `count == 0`, und der erste hat die Tabelle da gerade gefuellt. Die
Falle liegt im Aendern: Wer einen Preis in der Vorlage anpasst, aendert ihn
womoeglich im zweiten Block — und **nichts** passiert. Kein Fehler, keine
Meldung, nur ein Preis, der auf einer frisch aufgesetzten Datenbank anders
aussieht als gedacht.

Nachgemessen waren beide zum Zeitpunkt des Fundes noch datengleich — die
Falle war gestellt, aber noch nicht zugeschnappt.
"""
import ast
import pathlib


WURZEL = pathlib.Path(__file__).resolve().parent.parent


def _seed_listen():
    # Seit dem 30.08.2026 in `startphase.py` statt in `main.py` (L-25).
    baum = ast.parse((WURZEL / "startphase.py").read_text(encoding="utf-8"))
    return [ast.literal_eval(knoten.value)
            for knoten in ast.walk(baum)
            if isinstance(knoten, ast.Assign)
            and any(getattr(ziel, "id", "") == "SEED" for ziel in knoten.targets)]


def test_die_produktvorlage_steht_genau_einmal():
    """Zwei Vorlagen heissen: Eine davon aendert man umsonst."""
    listen = _seed_listen()

    assert len(listen) == 1, (
        f"{len(listen)} Produktvorlagen in startphase.py — die zweite ist "
        f"wirkungslos, und wer sie aendert, merkt nichts davon.")


def test_die_vorlage_traegt_die_drei_pakete():
    """Sie ist die Quelle fuer `products` auf einer frischen Datenbank —
    faellt sie weg, startet das System ohne Katalog."""
    listen = _seed_listen()

    slugs = {eintrag["slug"] for eintrag in listen[0]}
    # Bis 23.08.2026 standen hier starter/kompagnon/premium. Der Katalog
    # fuehrt seither die Websprint-Produkte; die Bestandspakete bleiben in
    # bestehenden Datenbanken als `archived` erhalten, gehoeren aber nicht
    # mehr in die Vorlage einer frischen (L-97).
    assert slugs == {"websprint_relaunch", "websprint_neubau",
                     "websprint_system"}, slugs


def test_jeder_eintrag_hat_brutto_netto_und_steuersatz():
    """Der Beleg rechnet auf diesen drei Feldern (`paket_fuer_beleg`).
    Fehlt eines, rechnet er still auf dem Regelsatz zurueck."""
    for eintrag in _seed_listen()[0]:
        for feld in ("price_brutto", "price_netto", "tax_rate"):
            assert eintrag.get(feld), f"{eintrag['slug']}: {feld} fehlt"

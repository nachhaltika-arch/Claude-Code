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


#: Der Katalog, wie er heute gilt. Waechst er, waechst diese Menge **mit
#: Begruendung** — nicht der Test schrumpft.
#:
#: Bis 23.08.2026 standen hier starter/kompagnon/premium (L-97); die
#: Bestandspakete bleiben in bestehenden Datenbanken als `archived` erhalten,
#: gehoeren aber nicht mehr in die Vorlage einer frischen. Am 04.09.2026 kam
#: `websprint_start` dazu (WS-STA-01, L-164) — beschrieben und verpreist seit
#: dem 23.08., im Code bis dahin **null Mal** vorhanden.
KATALOG = {"websprint_start", "websprint_relaunch", "websprint_neubau",
           "websprint_system"}


#: **Ein Befund, kein Freibrief** — gefunden am 04.09.2026, als dieser
#: Waechter zum ersten Mal lief (L-167).
#:
#: Diese drei Digitalprodukte legt `migrations_runtime.py` an, die Vorlage in
#: `startphase.py` kennt sie nicht. Eine **frisch aufgesetzte** Datenbank
#: bekommt damit vier Pakete, eine gewachsene sieben — zwei verschiedene
#: Kataloge, je nachdem, wie die Datenbank entstanden ist.
#:
#: Warum sie hier als Ausnahme stehen und nicht sofort nachgetragen sind: Das
#: Buch leitet seinen Preis ueber eine f-Zeichenkette aus
#: `services/buch_preise.py` ab. In die Vorlage gehoert dieselbe Ableitung,
#: nicht die abgeleitete Zahl — sonst steht der Buchpreis an einer zweiten
#: Stelle, und genau das verhindert `test_buchpreis_eine_stelle.py`. Das ist
#: eigene Arbeit an einem eigenen Gegenstand.
#:
#: Die Liste ist bewusst geschlossen: Ein **neues** Produkt darf hier nicht
#: landen, ohne dass jemand diesen Kommentar liest.
NUR_IN_DER_MIGRATION = {"buch_homepage_standard", "check_plus",
                        "workbook_homepage_standard"}


def test_die_vorlage_traegt_den_ganzen_katalog():
    """Sie ist die Quelle fuer `products` auf einer frischen Datenbank —
    faellt sie weg, startet das System ohne Katalog."""
    listen = _seed_listen()

    slugs = {eintrag["slug"] for eintrag in listen[0]}
    assert slugs == KATALOG, slugs


def test_vorlage_und_migration_fuehren_dieselben_pakete():
    """**Der Waechter, der beim vierten Produkt gefehlt haette** (L-164).

    Die Vorlage in `startphase.py` laeuft nur, wenn `products` **leer** ist.
    Produktiv und Staging sind es nicht — dort erreicht ein Paket den Katalog
    ausschliesslich ueber `migrations_runtime.py`. Wer nur die Vorlage
    ergaenzt, hat ein Produkt gebaut, das auf keiner laufenden Datenbank
    ankommt: gruener Test, leerer Shop.

    Umgekehrt genauso: Steht ein Paket nur in der Migration, bekommt eine
    frisch aufgesetzte Datenbank es nicht — und genau das ist heute der Fall,
    siehe `NUR_IN_DER_MIGRATION`.
    """
    import re

    vorlage = {eintrag["slug"] for eintrag in _seed_listen()[0]}
    text = (WURZEL / "migrations_runtime.py").read_text(encoding="utf-8")
    # Die INSERTs nennen den Slug als erste Zeichenkette der VALUES-Zeile.
    migration = set(re.findall(r"VALUES\s+\('([a-z_]+)',", text))

    # Die scharfe Richtung: Ein Paket, das nur in der Vorlage steht, erreicht
    # **keine** laufende Datenbank. Hier gibt es keine Ausnahmen.
    assert not (vorlage - migration), (
        f"nur in der Vorlage, erreicht also weder Produktiv noch Staging: "
        f"{sorted(vorlage - migration)}")

    # Die andere Richtung mit benannter Ausnahme — der Rest muss stimmen.
    assert (migration - vorlage) == NUR_IN_DER_MIGRATION, (
        f"unerwartet nur in der Migration: "
        f"{sorted((migration - vorlage) - NUR_IN_DER_MIGRATION)} · "
        f"nicht mehr fehlend: {sorted(NUR_IN_DER_MIGRATION - (migration - vorlage))}")


def test_gekoppeltes_abo_traegt_keinen_eigenen_preis():
    """Der Abo-Preis hat **eine** Quelle: `services/abo_stunden.py`.

    Eine Produktzeile mit einem eigenen Betrag waere der zweite Ort, an dem
    79 EUR gepflegt werden muessten — und die Pflichtangabe nach § 4.1 des
    Datenblatts waere in dem Moment falsch, in dem die beiden auseinanderlaufen.
    """
    for eintrag in _seed_listen()[0]:
        if not eintrag.get("gekoppeltes_abo"):
            continue
        assert eintrag.get("abo_mindestlaufzeit"), (
            f"{eintrag['slug']}: Abo gekoppelt, aber ohne Mindestlaufzeit — "
            f"ohne sie ist kein Gesamtpreis bildbar")
        verboten = [f for f in eintrag if "abo" in f and "preis" in f]
        assert not verboten, f"{eintrag['slug']}: eigener Abo-Preis in {verboten}"


def test_jeder_eintrag_hat_brutto_netto_und_steuersatz():
    """Der Beleg rechnet auf diesen drei Feldern (`paket_fuer_beleg`).
    Fehlt eines, rechnet er still auf dem Regelsatz zurueck."""
    for eintrag in _seed_listen()[0]:
        for feld in ("price_brutto", "price_netto", "tax_rate"):
            assert eintrag.get(feld), f"{eintrag['slug']}: {feld} fehlt"

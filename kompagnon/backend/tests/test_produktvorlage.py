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
    """Die Produktvorlage — **aufgerufen**, nicht als Text gelesen.

    **Warum der Umbau am 07.09.2026 (L-167).** Vorher stand hier
    `ast.literal_eval` auf der `SEED`-Zuweisung. Das las den **Quelltext**, und
    ein Literal ist alles, was es lesen kann: Sobald ein Eintrag aus einer
    Ableitung entsteht — beim Buch kommt der Preis aus
    `services/buch_preise.py`, damit er nicht an zwei Stellen steht —, brach
    der Test mit „malformed node".

    Genau das war der Grund, warum die drei Digitalprodukte drei Tage lang
    **nur in der Migration** standen und einer frisch aufgesetzten Datenbank
    fehlten: Der Waechter erlaubte keine Ableitung.

    Jetzt prueft er, **was wirklich entsteht** — und das ist ohnehin die
    bessere Frage. `ast` bleibt fuer den Test darunter, der zaehlt, wie viele
    Vorlagen es gibt; dort ist der Text der Gegenstand.
    """
    from startphase import produkt_vorlage

    return [produkt_vorlage()]


def _seed_zuweisungen():
    """Wie viele Stellen eine Produktvorlage aufbauen — am Quelltext gezaehlt."""
    baum = ast.parse((WURZEL / "startphase.py").read_text(encoding="utf-8"))
    return [k for k in ast.walk(baum) if isinstance(k, ast.Assign)
            and any(getattr(ziel, "id", "") == "SEED" for ziel in k.targets)]


def test_die_produktvorlage_steht_genau_einmal():
    """Zwei Vorlagen heissen: Eine davon aendert man umsonst."""
    stellen = _seed_zuweisungen()

    assert len(stellen) <= 1, (
        f"{len(stellen)} Produktvorlagen in startphase.py — die zweite ist "
        f"wirkungslos, und wer sie aendert, merkt nichts davon.")


#: Der Katalog, wie er heute gilt. Waechst er, waechst diese Menge **mit
#: Begruendung** — nicht der Test schrumpft.
#:
#: Bis 23.08.2026 standen hier starter/kompagnon/premium (L-97); die
#: Bestandspakete bleiben in bestehenden Datenbanken als `archived` erhalten,
#: gehoeren aber nicht mehr in die Vorlage einer frischen. Am 04.09.2026 kam
#: `websprint_start` dazu (WS-STA-01, L-164) — beschrieben und verpreist seit
#: dem 23.08., im Code bis dahin **null Mal** vorhanden.
#: Am 07.09.2026 kamen die drei **Digitalprodukte** dazu (L-167): Sie standen
#: bis dahin nur in der Migration, also hatte eine gewachsene Datenbank sie und
#: eine frisch aufgesetzte nicht.
KATALOG = {"websprint_start", "websprint_relaunch", "websprint_neubau",
           "websprint_system", "buch_homepage_standard", "check_plus",
           "workbook_homepage_standard"}


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
#: **Leer seit dem 07.09.2026 (L-167).** Hier standen die drei Digitalprodukte:
#: Eine gewachsene Datenbank hatte sie, eine frisch aufgesetzte nicht — wer
#: lokal neu aufsetzte, bekam einen Katalog ohne Buch, Workbook und Check PLUS
#: und merkte es erst, wenn jemand danach suchte.
#:
#: **Warum es damals nicht im selben Zug behoben wurde:** Das Buch leitet
#: seinen Preis aus `services/buch_preise.py` ab, und in die Vorlage gehoert
#: dieselbe **Ableitung**, nicht die abgeleitete Zahl — sonst stuende der
#: Buchpreis an einer zweiten Stelle. Genau so ist es jetzt gebaut.
#:
#: Die Liste bleibt stehen: Sie ist der Ort, an dem eine solche Ausnahme
#: benannt und datiert werden muss. Leer heisst, es gibt keine.
NUR_IN_DER_MIGRATION = set()


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

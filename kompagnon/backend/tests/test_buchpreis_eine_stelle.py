# -*- coding: utf-8 -*-
"""Der Buchpreis steht an einer Stelle — auch nachdem er in den Katalog kam.

**Der Anlass (27.08.2026, Bitte David).** Das Buch sollte im Produkt-Editor
bearbeitbar sein, „für 49 EUR". Der naheliegende Weg wäre ein Katalogeintrag
mit einer festen `49.00` gewesen — und genau der war verboten:

`services/buch_preise.py` sagt in seinem Kopf wörtlich, wer einen Buchpreis
suche, finde ihn dort **und nur dort**. Der Grund steht daneben: Am 24.08.
stand ein Paketpreis an fünf Stellen im System, und beim Nachzählen waren es
vierzehn (L-29). Eine feste `49.00` im Katalog wäre die fünfzehnte gewesen.

**Deshalb leitet die Migration den Wert ab, statt ihn abzuschreiben.** Dieser
Test hält fest, dass sie das auch weiterhin tut — eine Absicht im Kommentar
ist keine Verbindung.

**Zwei Prüfungen, weil eine nicht reicht.** Der Quelltext-Test hält fest, dass
abgeleitet und nicht abgeschrieben wird; die Datenbank-Tests halten fest, dass
dabei der richtige Wert herauskommt. Der erste allein wäre grün bei falscher
Rechnung, der zweite allein ist **nicht falsifizierbar** — das hat die
Gegenprobe gezeigt, nicht das Nachdenken.

**Was diese Datei nicht zusichert.** Wer den Preis im Produkt-Editor ändert,
ändert die Katalogzeile — und die Kasse verkauft weiter zum Preis aus
`buch_preise`. Der Katalogeintrag ist eine Ansicht, kein Verkaufsweg (er steht
auf `draft`). Ein Riegel dagegen wäre ein gesperrtes Feld im Editor; das ist
eine Produktentscheidung und keine Testfrage.
"""
from decimal import Decimal


def _katalogzeile(db):
    from sqlalchemy import text

    return db.execute(text(
        "SELECT price_brutto, price_netto, tax_rate, delivery_type, status "
        "FROM products WHERE slug = 'buch_homepage_standard'"
    )).mappings().first()


def test_die_migration_leitet_ab_statt_abzuschreiben():
    """**Der eigentliche Waechter** — und der erste Anlauf war keiner.

    Zuerst stand hier nur ein Vergleich zwischen Katalogzeile und
    `buch_preise`. Die Gegenprobe (Preis in `buch_preise` aendern, Test
    laufen lassen) blieb **gruen**: Die Migration schrieb die Zeile bei jedem
    Lauf mit, beide Seiten bewegten sich gemeinsam, und der Test konnte gar
    nicht rot werden. Ein Waechter, der nicht falsifizierbar ist, prueft
    nichts.

    Geprueft wird deshalb die Eigenschaft, um die es geht: dass im
    Migrationstext die **abgeleitete Groesse** steht und keine feste Zahl.
    Wer `_buch_brutto` durch `49.00` ersetzt, wird hier rot — und genau das
    war der Fehler, der verhindert werden soll (L-29).
    """
    import inspect

    import migrations_runtime

    quelle = inspect.getsource(migrations_runtime.run_migrations)

    assert "from services.buch_preise import" in quelle, (
        "Die Migration holt den Buchpreis nicht mehr aus buch_preise")

    # **Genau die Werte-Zeile, nicht ein Fenster darum.** Der erste Anlauf
    # suchte in +/- 1200 Zeichen um den Slug — und traf `{_buch_brutto:.2f}`
    # in der **Beschreibung** mit. Mit fest eingetragenen Preisen blieb der
    # Test gruen. Zweiter wirkungsloser Waechter an derselben Stelle, und
    # wieder von der Gegenprobe gefunden, nicht vom Lesen.
    werte = [z for z in quelle.splitlines()
             if "'once', 5, 'draft'" in z]
    assert len(werte) == 1, f"{len(werte)} Werte-Zeilen fuer das Buch gefunden"
    assert "{_buch_brutto:.2f}" in werte[0], (
        f"Feste Zahl statt abgeleitetem Wert: {werte[0].strip()}")
    assert "{_buch_steuer:.0f}" in werte[0], (
        f"Fester Steuersatz statt abgeleitetem: {werte[0].strip()}")


def test_der_katalog_traegt_den_preis_aus_buch_preise(app):
    from database import SessionLocal
    from services.buch_preise import VARIANTEN

    erwartet = Decimal(VARIANTEN["print"]["brutto_cents"]) / 100

    db = SessionLocal()
    try:
        zeile = _katalogzeile(db)
    finally:
        db.close()

    assert zeile is not None, "Das Buch fehlt im Katalog"
    assert Decimal(str(zeile["price_brutto"])) == erwartet, (
        f"Katalog {zeile['price_brutto']} gegen buch_preise {erwartet} — "
        "der Preis steht wieder an zwei Stellen")


def test_auch_der_steuersatz_kommt_von_dort(app):
    """Sieben Prozent, nicht neunzehn.

    Bücher stehen in Anlage 2 UStG. Der Produkteditor stellt 19 % voreingestellt
    ein — für dieses Produkt wäre das falsch (BUCH-12), und ein Katalogeintrag
    mit der Voreinstellung hätte den Fehler still eingeführt.
    """
    from database import SessionLocal
    from services.buch_preise import STEUERSATZ

    db = SessionLocal()
    try:
        zeile = _katalogzeile(db)
    finally:
        db.close()

    assert Decimal(str(zeile["tax_rate"])) == Decimal(STEUERSATZ)


def test_netto_passt_zu_brutto_und_satz(app):
    """Zwei Zahlen, eine Rechnung — sonst driften sie."""
    from database import SessionLocal

    db = SessionLocal()
    try:
        zeile = _katalogzeile(db)
    finally:
        db.close()

    brutto = Decimal(str(zeile["price_brutto"]))
    satz = Decimal(str(zeile["tax_rate"]))
    erwartet = (brutto / (1 + satz / 100)).quantize(Decimal("0.01"))

    assert abs(Decimal(str(zeile["price_netto"])) - erwartet) <= Decimal("0.01")


def test_der_katalogeintrag_ist_kein_zweiter_verkaufsweg(app):
    """`draft`, und das ist der Punkt.

    Verkauft wird das Buch über `POST /api/book/checkout` — der kennt drei
    Varianten und eine Lieferanschrift. Stünde die Katalogzeile auf `live`,
    erschiene sie in `/api/products/public`, und `Checkout.jsx` böte einen
    **generischen** Kaufweg an: eine Variante, keine Anschrift, kein Versand.
    Der Käufer bekäme kein Buch.
    """
    from database import SessionLocal

    db = SessionLocal()
    try:
        zeile = _katalogzeile(db)
    finally:
        db.close()

    assert zeile["status"] == "draft"


def test_die_shop_seite_erkennt_es_als_gedrucktes_produkt(app):
    """`delivery_type` trägt die Unterscheidung, nicht der Name.

    Die Verkaufsseite filtert daran; `none` hiesse „ist ein Projekt".
    """
    from database import SessionLocal

    db = SessionLocal()
    try:
        zeile = _katalogzeile(db)
    finally:
        db.close()

    assert zeile["delivery_type"] == "print"

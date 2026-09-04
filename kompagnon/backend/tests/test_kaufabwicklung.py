# -*- coding: utf-8 -*-
"""Der Kauf löst aus, was am Produkt steht — nicht, was üblich ist.

**Entscheidung David, 27.08.2026:** Aus den angelegten Produkten soll eine
Verkaufsstrecke entstehen, damit ein fertiges Produkt einen fertigen Kanal
zur Kaufabwicklung bekommt.

Gemessen statt gebaut: Katalog, Stripe-Abgleich und Bezahlvorgang waren
bereits vollständig aus `products` erzeugt. **Der letzte Schritt war fest
verdrahtet** — `_handle_successful_payment` machte nach jeder Zahlung Lead,
Konto, Projekt, Willkommensmail und Scraper. Für ein PDF-Workbook heißt das:
ein Website-Projekt ohne Website.

Und `products.webhook_actions` trug diese fünf Namen längst, wurde im
Produkt-Editor angezeigt und von **keiner Zeile gelesen**.

**Die gefährlichste Zusicherung in dieser Datei ist die erste.** Sie hält
fest, dass sich an den Websprints nichts ändert. Ein Umbau am Zahlungspfad,
der die bestehende Kundenanlage bricht, kostet echte Aufträge — und merken
würde man es an einem Kunden, nicht an einem Test.
"""
import pytest

from services import kaufabwicklung as ka


# ── Die Vorgabe ist das Verhalten von heute ───────────────────────────

@pytest.mark.parametrize("leer", [None, [], "[]", "", "kein json"])
def test_ohne_eintrag_laeuft_alles_wie_bisher(leer):
    """**Die wichtigste Zeile.** Jedes Produkt, das vor heute entstand, trägt
    den Spaltenvorgabewert `'[]'` — und muss unverändert weiterlaufen."""
    schritte = ka.schritte_fuer({"webhook_actions": leer})

    assert schritte == frozenset(ka.VORGABE)
    assert ka.PROJEKT in schritte
    assert ka.KONTO in schritte


def test_auch_ohne_produktzeile_gilt_die_vorgabe():
    """Ein Kauf, zu dem keine Produktzeile gefunden wird, ist ein
    Websprint-Kauf — bis jemand das Gegenteil einträgt.

    Alles andere hieße, bei einem Datenfehler die Kundenanlage
    stillschweigend zu überspringen: Das Geld ist da, der Kunde nicht.
    """
    assert ka.schritte_fuer(None) == frozenset(ka.VORGABE)


def test_die_websprints_behalten_ihre_fuenf_schritte():
    """Gegen die **echten** Werte aus dem Katalog, nicht gegen erfundene."""
    gesetzt = ["create_lead", "create_user", "create_project",
               "send_welcome_email", "send_pdf"]

    schritte = ka.schritte_fuer({"webhook_actions": gesetzt})

    assert schritte == frozenset(gesetzt)


# ── Und was ein digitales Produkt bekommt ─────────────────────────────

def test_ein_download_produkt_bekommt_kein_projekt():
    """Der eigentliche Zweck des Umbaus."""
    schritte = ka.schritte_fuer({
        "webhook_actions": [ka.LEAD, ka.KONTO, ka.AUFTRAGSBESTAETIGUNG]})

    assert ka.PROJEKT not in schritte
    assert ka.SCRAPER not in schritte
    # Gegenprobe: Was drinsteht, ist auch drin.
    assert ka.LEAD in schritte and ka.KONTO in schritte


def test_ausdrueckliches_nichts_ist_etwas_anderes_als_nichts_eingetragen():
    """`[]` heißt „nie eingerichtet", `['none']` heißt „bewusst keine".

    Ohne diese Unterscheidung gäbe es keinen Weg, ein Produkt ohne
    Folgeschritte zu führen — die leere Liste ist ja der Spaltenvorgabewert.
    """
    assert ka.schritte_fuer({"webhook_actions": [ka.AKTION_KEINE]}) == frozenset()
    assert ka.schritte_fuer({"webhook_actions": []}) == frozenset(ka.VORGABE)


def test_ein_unbekannter_name_wird_gemeldet_und_nicht_ausgefuehrt(caplog):
    """Ein Haken ohne Wirkung ist der Fehler, den dieses Modul beendet —
    er soll wenigstens im Protokoll stehen."""
    import logging

    with caplog.at_level(logging.WARNING):
        schritte = ka.schritte_fuer({"webhook_actions": [ka.LEAD, "zauberei"]})

    assert schritte == frozenset({ka.LEAD})
    assert "zauberei" in caplog.text


def test_jeder_bekannte_name_wird_auch_ausgefuehrt():
    """**Die Verbindung, ohne die die Liste wieder Beschreibung wäre.**

    Wer einen Namen in `BEKANNT` einträgt, muss ihn im Zahlungspfad auch
    bauen. Geprüft wird am Quelltext von `_handle_successful_payment`: Jede
    Aktion außer `none` muss dort vorkommen.
    """
    import inspect

    from routers.payments import _handle_successful_payment

    quelle = inspect.getsource(_handle_successful_payment)

    # `none` ist die Abwesenheit, `create_lead` laeuft immer: Der Lead traegt
    # die Stripe-Sitzungskennung, an der der Idempotenz-Schutz eine
    # wiederholte Zustellung erkennt. Beide sind deshalb keine Bedingung im
    # Zahlungspfad — das steht in `services/kaufabwicklung.IMMER`.
    ausgenommen = {ka.AKTION_KEINE, *ka.IMMER}
    namen = {ka.KONTO: "KONTO", ka.PROJEKT: "PROJEKT",
             ka.WILLKOMMEN: "WILLKOMMEN",
             ka.AUFTRAGSBESTAETIGUNG: "AUFTRAGSBESTAETIGUNG",
             ka.SCRAPER: "SCRAPER"}
    fehlend = [a for a in sorted(ka.BEKANNT)
               if a not in ausgenommen and namen.get(a, a) not in quelle]

    assert not fehlend, (
        f"Diese Aktionen stehen im Produkt-Editor zur Wahl, werden aber im "
        f"Zahlungspfad nicht ausgeführt: {fehlend}")


# ── Am Katalog gemessen ───────────────────────────────────────────────

def test_die_digitalen_produkte_legen_kein_projekt_an(app):
    """Am **Bestand**, nicht an erfundenen Zeilen.

    Ohne diesen Test wäre alles oben grün und die drei Produkte trügen
    trotzdem die Websprint-Schritte.
    """
    from sqlalchemy import text

    from database import SessionLocal

    db = SessionLocal()
    try:
        zeilen = db.execute(text(
            "SELECT slug, webhook_actions FROM products "
            "WHERE slug IN ('workbook_homepage_standard', 'check_plus', "
            "               'buch_homepage_standard')"
        )).mappings().all()
    finally:
        db.close()

    assert len(zeilen) == 3, f"{len(zeilen)} von 3 Produkten im Katalog"

    for zeile in zeilen:
        schritte = ka.schritte_fuer(zeile)
        assert ka.PROJEKT not in schritte, (
            f"{zeile['slug']} legt ein Website-Projekt an")
        assert ka.SCRAPER not in schritte, (
            f"{zeile['slug']} startet einen Content-Scraper")


def test_die_websprints_im_katalog_sind_unberuehrt(app):
    """Die Gegenprobe am Bestand — sie sollen ihre fünf Schritte behalten."""
    from sqlalchemy import text

    from database import SessionLocal

    db = SessionLocal()
    try:
        zeilen = db.execute(text(
            "SELECT slug, webhook_actions FROM products "
            "WHERE slug LIKE 'websprint%'"
        )).mappings().all()
    finally:
        db.close()

    assert zeilen, "Keine Websprints im Katalog"
    for zeile in zeilen:
        schritte = ka.schritte_fuer(zeile)
        assert ka.PROJEKT in schritte, f"{zeile['slug']} legt kein Projekt mehr an"
        assert ka.KONTO in schritte

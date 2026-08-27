# -*- coding: utf-8 -*-
"""Jede Stripe-Adresse verarbeitet nur, was ihr gehört.

**Der Anlass (27.08.2026, vor dem Eintragen der Webhooks in Stripe).** Drei
Adressen sollten eingetragen werden. Die Annahme dahinter war falsch: Ein
Stripe-Endpunkt abonniert **Ereignisarten, keine Vorgänge**. Wer
`checkout.session.completed` abonniert, bekommt jede abgeschlossene Kasse
des Kontos.

Das ist der Grund, warum diese Datei vor dem Eintragen entstanden ist und
nicht nach dem ersten Käufer. Der Schaden wäre nicht sichtbar gewesen: Der
Buchkauf hätte funktioniert **und zusätzlich** ein Website-Projekt samt
Zugangsdaten erzeugt.

**Die Gegenprobe ist hier die halbe Datei.** Eine Weiche, die zu viel
aussperrt, ist schlimmer als keine — dann ginge kein einziger Kauf mehr
durch. Zu jeder „wird übersprungen"-Zusicherung steht deshalb eine
„wird verarbeitet"-Zusicherung daneben.
"""
import pytest

from services import zahlungsweg as zw


# ── Die Zuordnung selbst ──────────────────────────────────────────────

def test_ein_geo_abo_gehoert_zu_geo():
    assert zw.weg_der_sitzung({"addon_type": "geo"}) == zw.GEO


@pytest.mark.parametrize("nummer", ["B-2026-0001", "  B-2026-0002  "])
def test_eine_bestellnummer_gehoert_zu_buch_und_shop(nummer):
    """Buch und Shop schreiben beide in `book_orders` und teilen sich den
    Endpunkt — deshalb ist es hier ein Weg und nicht zwei."""
    assert zw.weg_der_sitzung({"order_number": nummer}) == zw.BUCH


def test_ein_paket_gehoert_zum_websprint():
    assert zw.weg_der_sitzung({"package": "starter"}) == zw.WEBSPRINT


@pytest.mark.parametrize("leer", [None, {}, {"order_number": ""},
                                  {"addon_type": ""}])
def test_ohne_marker_bleibt_es_der_websprint(leer):
    """**Der Rückfall ist Absicht.** Es kann in Stripe Sitzungen von vor
    dieser Änderung geben; sie werden weiter dort behandelt, wo sie bisher
    behandelt wurden. Alles andere hieße, Bestandsvorgänge stillzulegen."""
    assert zw.weg_der_sitzung(leer) == zw.WEBSPRINT


def test_die_wege_sind_verschieden():
    """Die Gegenprobe zur Zuordnung: Wären zwei Namen gleich, wäre jede
    Zusicherung oben gleichzeitig wahr und wertlos."""
    assert len({zw.GEO, zw.BUCH, zw.WEBSPRINT}) == 3


# ── Was der Websprint-Endpunkt tut ────────────────────────────────────

class _Sitzung(dict):
    """Eine Stripe-Sitzung, so viel wie der Pfad davon liest."""


def _sitzung(metadaten: dict) -> dict:
    return {
        "id": "cs_test_1",
        "metadata": metadaten,
        "amount_total": 4900,
        "customer_email": "kaeufer@example.org",
    }


class _Buchhalter:
    """Eine Sitzung, die jede Benutzung meldet.

    Sie wirft nicht, sie zählt — ein Fehlschlag beim ersten Zugriff sähe im
    Test genauso aus wie ein Fehlschlag beim zwanzigsten.
    """

    def __init__(self):
        self.benutzt = []

    def execute(self, *_a, **_k):
        self.benutzt.append("execute")
        raise AssertionError("Die Datenbank wurde angefasst")

    def add(self, *_a, **_k):
        self.benutzt.append("add")
        raise AssertionError("Es wurde etwas angelegt")

    def rollback(self, *_a, **_k):
        self.benutzt.append("rollback")


@pytest.mark.parametrize("fremd", [
    {"order_number": "B-2026-0001", "variant": "print"},
    {"addon_type": "geo"},
])
def test_der_websprint_pfad_fasst_fremde_kaeufe_nicht_an(fremd):
    """**Der eigentliche Befund.** Ohne diese Weiche hätte ein Buchkauf für
    49 EUR hier Lead, Konto, Projekt und Willkommensmail ausgelöst."""
    from routers.payments import _handle_successful_payment

    db = _Buchhalter()

    _handle_successful_payment(_sitzung(fremd), db)

    assert db.benutzt == [], f"angefasst: {db.benutzt}"


def test_und_ein_websprint_kauf_laeuft_weiter_durch():
    """**Die Gegenprobe — die wichtigere Zusicherung.** Eine Weiche, die
    alles aussperrt, wäre in beiden Tests oben grün und würde jeden echten
    Auftrag verschlucken.

    Gemessen wird der erste Zugriff auf die Datenbank: Er beweist, dass der
    Pfad an der Weiche vorbeigekommen ist. Was danach passiert, prüfen die
    Tests der Kundenanlage.
    """
    from routers.payments import _handle_successful_payment

    db = _Buchhalter()

    with pytest.raises(AssertionError, match="Die Datenbank wurde angefasst"):
        _handle_successful_payment(_sitzung({"package": "starter"}), db)

    assert db.benutzt == ["execute"]


# ── Und was der Buch-Endpunkt tut ─────────────────────────────────────

def test_der_buchpfad_laesst_websprint_kaeufe_liegen(monkeypatch):
    """Ohne diese Weiche meldete der Buchpfad bei **jedem** Websprint-Kauf
    „Webhook ohne Bestellung" als Fehler — ein Protokoll voller Fehlalarme
    ist eines, in dem der echte Fehler untergeht."""
    import routers.buch as buch

    def _keine_sitzung():
        raise AssertionError("Eine Datenbanksitzung wurde geoeffnet")

    monkeypatch.setattr(buch, "SessionLocal", _keine_sitzung)

    buch._zahlung_verbuchen(_sitzung({"package": "starter"}))


def test_und_ein_buchkauf_kommt_durch(monkeypatch):
    """Die Gegenprobe dazu."""
    import routers.buch as buch

    geoeffnet = []

    def _sitzung_zaehlen():
        geoeffnet.append(True)
        raise AssertionError("bis hierher und nicht weiter")

    monkeypatch.setattr(buch, "SessionLocal", _sitzung_zaehlen)

    with pytest.raises(AssertionError, match="bis hierher"):
        buch._zahlung_verbuchen(_sitzung({"order_number": "B-2026-0001"}))

    assert geoeffnet == [True]


# ── Und das Signaturgeheimnis ─────────────────────────────────────────

def test_der_buchpfad_hat_ein_eigenes_signaturgeheimnis():
    """**Jede in Stripe eingetragene Adresse hat ihr eigenes.** Läse der
    Buchpfad das der Zahlungsadresse, schlüge jede Signatur fehl und keine
    Bestellung würde je auf „bezahlt" gesetzt — sichtbar erst am Käufer.

    Geprüft wird die Quelle, nicht der geladene Wert: Der Wert entsteht beim
    Import aus der Umgebung, und die ist im Test leer.
    """
    from pathlib import Path

    quelle = (Path(__file__).resolve().parent.parent
              / "routers" / "buch.py").read_text(encoding="utf-8")

    assert "STRIPE_WEBHOOK_SECRET_BUCH" in quelle

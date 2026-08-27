# -*- coding: utf-8 -*-
"""Ein echtes Stripe-Objekt, kein selbstgeschriebenes `dict`.

**Der Befund (27.08.2026, erster echter Testkauf).** Die Kette stand —
Kasse, Schluessel, drei Adressen, Signaturpruefung. Der erste echte Kauf
antwortete mit HTTP 500:

    KeyError: 'get'  →  AttributeError: get

`stripe.Webhook.construct_event` liefert ein `StripeObject`, und das ist seit
**stripe 15 keine dict-Unterklasse mehr**. `sitzung.get("metadata", {})`
sucht dort keinen Methodennamen, sondern einen **Schluessel namens „get"**.

**Warum kein Test das gefunden hat, und das ist der eigentliche Punkt.**
Jeder Test dieses Bestands reicht ein `dict` herein — so, wie man eine
Stripe-Meldung von Hand aufschreibt. Die Tests waren gruen und haben nichts
Falsches geprueft: Die Logik stimmt. Was ihnen fehlte, war der **echte
Gegenstand**. Bis zu diesem Abend hat nie eine echte Stripe-Meldung dieses
System erreicht.

Diese Datei baut das Objekt deshalb mit der Bibliothek selbst. Steigt eine
kuenftige stripe-Fassung wieder um, wird sie rot — und zwar hier, nicht beim
Kaeufer.
"""
import pytest

from services.stripe_ereignis import als_dict, gegenstand


def _stripe_objekt(daten: dict):
    """So, wie die Bibliothek es aus einer Antwort baut."""
    from stripe import StripeObject

    return StripeObject.construct_from(daten, "kein_schluessel")


BEISPIEL = {
    "id": "cs_test_1",
    "amount_total": 416500,
    "customer_email": "kaeufer@example.org",
    "metadata": {"package": "websprint_relaunch", "company_name": "Testbetrieb"},
    "customer_details": {"phone": "+49 30 0"},
}


# ── Die Gegenprobe zuerst: der Fehler ist echt ────────────────────────

def test_ein_stripe_objekt_kann_kein_get():
    """**Ohne diese Zusicherung ist alles Weitere Behauptung.**

    Sie haelt fest, warum die Umwandlung ueberhaupt existiert. Faellt sie
    eines Tages weg, weil die Bibliothek wieder dict-artig wird, soll das
    auffallen — und nicht die Umwandlung stillschweigend nutzlos werden.
    """
    objekt = _stripe_objekt(BEISPIEL)

    with pytest.raises(AttributeError):
        objekt.get("metadata", {})


def test_der_zugriff_mit_klammern_geht_weiterhin():
    """Zur Abgrenzung: Es ist kein kaputtes Objekt, es ist ein anderes."""
    assert _stripe_objekt(BEISPIEL)["metadata"]["package"] == "websprint_relaunch"


# ── Und was die Umwandlung daraus macht ───────────────────────────────

def test_nach_der_umwandlung_ist_es_ein_gewoehnliches_dict():
    umgewandelt = als_dict(_stripe_objekt(BEISPIEL))

    assert type(umgewandelt) is dict
    assert umgewandelt.get("customer_email") == "kaeufer@example.org"


def test_auch_die_verschachtelten_teile():
    """`to_dict()` loest nur die oberste Ebene auf. Ohne Rekursion verschoebe
    sich der Fehler eine Ebene tiefer, statt zu verschwinden — und `metadata`
    ist genau die Ebene, auf der der Zahlungspfad arbeitet."""
    umgewandelt = als_dict(_stripe_objekt(BEISPIEL))

    assert type(umgewandelt["metadata"]) is dict
    assert umgewandelt["metadata"].get("package") == "websprint_relaunch"
    assert umgewandelt["customer_details"].get("phone") == "+49 30 0"


def test_listen_werden_mitgenommen():
    objekt = _stripe_objekt({"lines": [{"a": 1}, {"b": 2}]})

    umgewandelt = als_dict(objekt)

    assert [type(e) is dict for e in umgewandelt["lines"]] == [True, True]


def test_gewoehnliche_werte_bleiben_wie_sie_sind():
    """Die Gegenprobe zur Umwandlung: Sie darf nichts anfassen, was schon
    stimmt — sonst repariert sie an einer Stelle und bricht an zehn."""
    assert als_dict("text") == "text"
    assert als_dict(42) == 42
    assert als_dict(None) is None
    assert als_dict({"a": 1}) == {"a": 1}


# ── Der Weg durch den Webhook ─────────────────────────────────────────

def test_der_gegenstand_kommt_als_dict_aus_dem_ereignis():
    ereignis = _stripe_objekt({
        "type": "checkout.session.completed",
        "data": {"object": BEISPIEL},
    })

    sitzung = gegenstand(ereignis)

    assert type(sitzung) is dict
    assert sitzung.get("metadata", {}).get("package") == "websprint_relaunch"


@pytest.mark.parametrize("kaputt", [{}, {"data": {}}, {"data": {"object": None}}])
def test_ein_ereignis_ohne_gegenstand_stuerzt_nicht_ab(kaputt):
    """Ein Webhook, der beim Auspacken abstuerzt, laesst Stripe tagelang
    wiederholen — und im Protokoll steht ein Absturz statt einer Aussage."""
    assert gegenstand(_stripe_objekt(kaputt)) == {}


# ── Und die Wege erkennen es wieder ───────────────────────────────────

def test_der_zahlungsweg_erkennt_ein_echtes_objekt():
    """Der Zusammenschluss beider Reparaturen dieses Abends: Die Weiche aus
    L-138 arbeitet auf `metadata` — und bekam sie bisher als StripeObject."""
    from services.zahlungsweg import BUCH, WEBSPRINT, weg_der_sitzung

    websprint = gegenstand(_stripe_objekt({"data": {"object": BEISPIEL}}))
    buch = gegenstand(_stripe_objekt(
        {"data": {"object": {"id": "cs_2", "metadata": {"order_number": "HS-1"}}}}))

    assert weg_der_sitzung(websprint.get("metadata")) == WEBSPRINT
    assert weg_der_sitzung(buch.get("metadata")) == BUCH

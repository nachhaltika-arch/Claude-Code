"""Jeder Aufruf des Frontends muss im Backend eine Route treffen.

Gefunden am 21.08.2026 beim Fertigstellen von M4 (`docs/module-karte.md`).
Die gesamte Bestellstrecke war gegen eine **andere** Schnittstelle
geschrieben, als es sie gibt — und es fiel nie auf, weil keine der Seiten
erreichbar war (L-64):

    CheckoutSuccess.jsx   /api/stripe/session/{}          → /api/payments/session/{}
    PackageStarter.jsx    /api/stripe/create-checkout-session
    PackageKompagnon.jsx  ebenso                          → /api/payments/create-checkout
    PackagePremium.jsx    ebenso

Beim Nachzaehlen kamen weitere heraus, die **nichts** mit dem Bestellweg zu
tun haben — die Paketverwaltung ruft zwei Endpunkte auf, die es nicht gibt.

**Warum ein Test und keine Liste von Reparaturen:** Ein falscher Pfad faellt
erst auf, wenn jemand die Seite benutzt. Ist die Seite nicht erreichbar oder
selten, faellt er nie auf. Der Test fragt die geladene Anwendung nach ihren
Routen und vergleicht sie mit dem, was im Frontend steht — beides
normalisiert, damit `${lead.id}` und `{lead_id}` als dasselbe gelten.
"""
import pytest


# **Seit dem 24.08.2026 liegen die drei Helfer in `tools/adressen.py`** —
# gemeinsam mit `tools/unaufgerufene-routen.py`, das dieselbe Frage in die
# **andere** Richtung stellt: Welche Route ruft niemand auf? Zwei Leser
# derselben Daten, die auseinanderdriften, waeren zwei Wahrheiten.
from tools.adressen import (  # noqa: E402
    bekannte_adressen as _bekannte_adressen,
    gerufene_adressen as _gerufene_adressen,
    normalisieren as _normalisieren,
)


#: Aufrufe, die heute ins Leere gehen und **nicht** zu M4 gehoeren.
#: Jeder gehoert zu einem Modul und wird dort behandelt — die Liste soll
#: schrumpfen, nie wachsen. Stand 21.08.2026.
GEPRUEFTE_LUECKEN = {
    "/api/academy/courses/reorder":            "M8 — Kursreihenfolge speichern",
    "/api/academy/modules/{}/lessons/reorder":  "M8 — Lektionsreihenfolge speichern",
    "/api/crawler/{}":                          "M1 — Crawler-Abfrage",
    "/api/leads/{}/sequence/{}":                "M10 — Mailstrecke je Betrieb",
    "/api/projects/{}/page-content/{}":         "M6 — Seiteninhalt",
    "/api/projects/{}/screenshot/{}":           "M6 — Screenshot je Seite",
    "/api/webhooks/{}":                         "M1 — Webhook-Verwaltung",
}


def test_kein_frontend_aufruf_geht_ins_leere():
    bekannt = _bekannte_adressen()
    fehlend = {
        adresse: sorted(wo)
        for adresse, wo in _gerufene_adressen().items()
        if adresse not in bekannt and adresse not in GEPRUEFTE_LUECKEN
    }

    assert fehlend == {}, (
        "Diese Adressen ruft das Frontend auf, im Backend gibt es sie nicht. "
        f"Der Aufruf scheitert erst, wenn jemand die Seite benutzt: {fehlend}"
    )


@pytest.mark.parametrize("adresse", sorted(GEPRUEFTE_LUECKEN))
def test_jede_bekannte_luecke_ist_noch_eine(adresse):
    """Sonst steht hier bald eine Liste, die niemand mehr prueft."""
    assert adresse not in _bekannte_adressen(), (
        f"{adresse} gibt es inzwischen — der Eintrag gehoert entfernt "
        f"({GEPRUEFTE_LUECKEN[adresse]})."
    )

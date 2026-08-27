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
    trifft_irgendeine as _trifft_irgendeine,
)


#: Aufrufe, die heute ins Leere gehen und **nicht** zu M4 gehoeren.
#: Jeder gehoert zu einem Modul und wird dort behandelt — die Liste soll
#: schrumpfen, nie wachsen. Stand 21.08.2026.
#:
#: **Am 26.08.2026 von sieben auf drei geschrumpft — und nicht, weil etwas
#: gebaut wurde.** Vier Eintraege waren nie Luecken: `/api/crawler/{}`,
#: `/api/leads/{}/sequence/{}`, `/api/projects/{}/screenshot/{}` und
#: `/api/webhooks/{}` treffen ihre Routen sehr wohl — der Knopf baut nur den
#: letzten Abschnitt zur Laufzeit zusammen, und verglichen wurde als
#: Zeichenkette. Die Liste trug damit vier Aufgaben, die es nicht gab.
GEPRUEFTE_LUECKEN = {
    "/api/academy/courses/reorder":            "M8 — Kursreihenfolge speichern",
    "/api/academy/modules/{}/lessons/reorder":  "M8 — Lektionsreihenfolge speichern",
    "/api/projects/{}/page-content/{}":         "M6 — Seiteninhalt",
}


def test_kein_frontend_aufruf_geht_ins_leere():
    bekannt = _bekannte_adressen()
    fehlend = {
        adresse: sorted(wo)
        for adresse, wo in _gerufene_adressen().items()
        if not _trifft_irgendeine(adresse, bekannt)
        and adresse not in GEPRUEFTE_LUECKEN
    }

    assert fehlend == {}, (
        "Diese Adressen ruft das Frontend auf, im Backend gibt es sie nicht. "
        f"Der Aufruf scheitert erst, wenn jemand die Seite benutzt: {fehlend}"
    )


@pytest.mark.parametrize("adresse", sorted(GEPRUEFTE_LUECKEN))
def test_jede_bekannte_luecke_ist_noch_eine(adresse):
    """Sonst steht hier bald eine Liste, die niemand mehr prueft.

    **Und geprueft wird abschnittsweise, nicht als Zeichenkette
    (26.08.2026).** Vorher stand hier `adresse not in _bekannte_adressen()`.
    Damit blieb der Test fuer vier Eintraege gruen, die **keine** Luecken
    waren: `/api/leads/{}/sequence/{}` trifft `start`, `pause` und `stop`,
    der Knopf baut die Aktion nur zur Laufzeit zusammen. Der Waechter gegen
    eine ungeprueft wachsende Liste konnte den Fehler nicht sehen, den er
    verhindern sollte — er mass dieselbe Schreibweise, aus der die Liste
    entstanden war.
    """
    assert not _trifft_irgendeine(adresse, _bekannte_adressen()), (
        f"{adresse} gibt es inzwischen — der Eintrag gehoert entfernt "
        f"({GEPRUEFTE_LUECKEN[adresse]})."
    )

"""Der Bericht muss sagen, *warum* nichts passiert ist.

Beim Sammellauf am 17.08.2026 stand „Frowein Haustechnik" unter
`ohne_ergebnis` mit dem Grund **„kein brauchbarer Name im Impressum"** — und
trug in der Datenbank längst genau diesen richtigen Namen. Jemand hatte ihn
kurz zuvor über die Oberfläche gesetzt.

Drei verschiedene Lagen teilten sich eine Meldung:

  * der Betrieb hatte inzwischen schon einen Namen  → gar kein Fehlschlag
  * das Impressum war nicht lesbar                  → Sache der fremden Seite
  * das Impressum war da, nannte aber keinen Namen  → Sache der KI-Auswertung

Wer aus dem Bericht ableiten soll, ob er nachfassen muss, braucht diesen
Unterschied. „Kein Name gefunden" bei einem Betrieb, der einen hat, ist eine
falsche Auskunft — dieselbe Bauart wie das Widget und der Ladefehler heute.
"""
import pytest


@pytest.fixture
def betrieb(app):
    from database import SessionLocal, Lead

    db = SessionLocal()
    try:
        db.query(Lead).filter(Lead.website_url.like('%pytest-grund%')).delete(
            synchronize_session=False)
        db.commit()
        lead = Lead(company_name="pytest-grund.de", website_url="https://pytest-grund.de")
        db.add(lead)
        db.commit()
        db.refresh(lead)
        return lead.id
    finally:
        db.close()


def _grund_fuer(bericht, name):
    for eintrag in bericht.get("ohne_ergebnis", []):
        if eintrag["betrieb"] == name:
            return eintrag["grund"]
    return None


def _antwort(monkeypatch, ergebnis):
    async def leser(url, *args, **kwargs):
        if 'pytest-grund' in url:
            return ergebnis
        return {"success": False, "error": "nicht getestet"}
    monkeypatch.setattr(
        "services.impressum_scraper.extract_contact_from_impressum", leser)


def test_ein_unlesbares_impressum_wird_als_solches_gemeldet(client, auth_headers,
                                                            betrieb, monkeypatch):
    _antwort(monkeypatch, {"success": False, "error": "Zeitüberschreitung"})

    bericht = client.post("/api/leads/namen-nachtragen?anzahl=25",
                          headers=auth_headers).json()

    assert "nicht lesbar" in _grund_fuer(bericht, "pytest-grund.de")
    assert "Zeitüberschreitung" in _grund_fuer(bericht, "pytest-grund.de")


def test_ein_impressum_ohne_namen_wird_unterschieden(client, auth_headers,
                                                     betrieb, monkeypatch):
    """Gelesen, aber nichts drin — das ist Sache der Auswertung, nicht der Seite."""
    _antwort(monkeypatch, {"success": True, "data": {"company_name": ""}})

    bericht = client.post("/api/leads/namen-nachtragen?anzahl=25",
                          headers=auth_headers).json()

    grund = _grund_fuer(bericht, "pytest-grund.de")
    assert "gelesen" in grund and "kein Firmenname" in grund


def test_ein_untauglicher_name_wird_beim_namen_genannt(client, auth_headers,
                                                       betrieb, monkeypatch):
    """Liefert die KI wieder die Domain, soll das dastehen — nicht „nichts gefunden"."""
    _antwort(monkeypatch, {"success": True, "data": {"company_name": "pytest-grund.de"}})

    bericht = client.post("/api/leads/namen-nachtragen?anzahl=25",
                          headers=auth_headers).json()

    assert "taugt nicht" in _grund_fuer(bericht, "pytest-grund.de")


def test_ein_betrieb_mit_namen_gilt_nicht_als_fehlschlag(client, auth_headers,
                                                         betrieb, monkeypatch):
    """Der Fall Frowein: zwischendurch von jemand anderem gesetzt."""
    from database import SessionLocal, Lead

    async def leser(url, *args, **kwargs):
        # Genau bevor der Lauf ihn auswertet, setzt jemand anders den Namen.
        db = SessionLocal()
        try:
            zeile = db.query(Lead).filter(Lead.id == betrieb).first()
            zeile.company_name = "Grund Haustechnik"
            db.commit()
        finally:
            db.close()
        return {"success": True, "data": {"company_name": "Grund Haustechnik"}}

    monkeypatch.setattr(
        "services.impressum_scraper.extract_contact_from_impressum", leser)

    bericht = client.post("/api/leads/namen-nachtragen?anzahl=25",
                          headers=auth_headers).json()

    grund = _grund_fuer(bericht, "Grund Haustechnik")
    assert grund is not None, "Der Betrieb fehlt im Bericht"
    assert "schon einen richtigen Namen" in grund

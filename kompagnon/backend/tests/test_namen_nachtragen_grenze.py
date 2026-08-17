"""Der Sammellauf muss in Portionen gehen und darf nichts verlieren.

Beim Durchgehen mit David am 17.08.2026 aufgefallen, **bevor** er lief:

`POST /api/leads/namen-nachtragen` nahm bis zu 25 Betriebe in **einer**
Anfrage und schrieb **erst am Ende** in die Datenbank. Je Betrieb fallen ein
Startseitenabruf, bis zu zwölf Kandidaten und ein KI-Aufruf an — zusammen
zwei bis acht Sekunden. Bei 25 Betrieben sind das 50 bis 200 Sekunden.

Renders Proxy kappt lange Antworten. Dann wäre nicht der Rest verloren
gewesen, sondern **alles**: Der Commit kam ja nie.

Zwei Änderungen, beide klein:
  * `?anzahl=` begrenzt die Portion, damit man in Etappen fahren kann.
  * Nach jedem Betrieb wird geschrieben. Was gefunden wurde, bleibt gefunden,
    auch wenn die Verbindung danach abreißt.
"""
import pytest


@pytest.fixture
def platzhalter_betriebe(app):
    """Fünf Betriebe, deren Name eine Domain ist."""
    from database import SessionLocal, Lead

    db = SessionLocal()
    try:
        db.query(Lead).filter(Lead.website_url.like('%pytest-portion%')).delete(
            synchronize_session=False)
        db.commit()

        ids = []
        for i in range(5):
            lead = Lead(company_name=f"pytest-portion-{i}.de",
                        website_url=f"https://pytest-portion-{i}.de")
            db.add(lead)
            db.commit()
            db.refresh(lead)
            ids.append(lead.id)
        return ids
    finally:
        db.close()


@pytest.fixture
def impressum_antwortet(monkeypatch):
    def einrichten(namen_je_domain, fehler_bei=None):
        async def leser(url, *args, **kwargs):
            if fehler_bei and fehler_bei in url:
                raise RuntimeError("Verbindung abgerissen")
            for teil, name in namen_je_domain.items():
                if teil in url:
                    return {"success": True, "data": {"company_name": name}}
            return {"success": False, "error": "nichts gefunden"}

        monkeypatch.setattr(
            "services.impressum_scraper.extract_contact_from_impressum", leser)
    return einrichten


def _name(lead_id):
    from database import SessionLocal, Lead

    db = SessionLocal()
    try:
        return db.query(Lead).filter(Lead.id == lead_id).first().company_name
    finally:
        db.close()


def test_die_portion_laesst_sich_begrenzen(client, auth_headers,
                                           platzhalter_betriebe, impressum_antwortet):
    impressum_antwortet({f"pytest-portion-{i}": f"Betrieb {i}" for i in range(5)})

    bericht = client.post("/api/leads/namen-nachtragen?anzahl=2",
                          headers=auth_headers).json()

    assert bericht["geprueft"] == 2


def test_die_grenze_wird_gemeldet(client, auth_headers, platzhalter_betriebe,
                                  impressum_antwortet):
    """Sonst hält man den Lauf für vollständig, obwohl noch welche offen sind."""
    impressum_antwortet({f"pytest-portion-{i}": f"Betrieb {i}" for i in range(5)})

    bericht = client.post("/api/leads/namen-nachtragen?anzahl=2",
                          headers=auth_headers).json()

    assert bericht["grenze_erreicht"] is True


def test_eine_zu_grosse_anzahl_wird_abgewiesen(client, auth_headers,
                                               platzhalter_betriebe, impressum_antwortet):
    """Abweisen statt still deckeln.

    Wer `anzahl=9999` schickt, erwartet 9999. Bekäme er stillschweigend 25 und
    einen Bericht über 25 Betriebe, hielte er den Lauf für vollständig. Die
    Obergrenze gehört in die Antwort, nicht in eine unsichtbare Kürzung.
    """
    impressum_antwortet({})

    antwort = client.post("/api/leads/namen-nachtragen?anzahl=9999",
                          headers=auth_headers)

    assert antwort.status_code == 422


def test_was_gemeldet_wurde_steht_auch_in_der_datenbank(client, auth_headers,
                                                       platzhalter_betriebe,
                                                       impressum_antwortet):
    """Der eigentliche Punkt: nach jedem Betrieb wird geschrieben.

    Einer der Betriebe wirft mittendrin. Vorher stand der Commit am Ende —
    dann wäre auch das verloren gewesen, was davor schon gefunden war.

    Geprüft wird die Zusage selbst, nicht eine bestimmte Zeile: **Jeder
    gemeldete Name steht danach in der Datenbank.** Welche Betriebe der Lauf
    erwischt, hängt vom Bestand ab — auch von dem, den andere Tests anlegen.
    """
    impressum_antwortet(
        {f"pytest-portion-{i}": f"Betrieb {i}" for i in range(5)},
        fehler_bei="pytest-portion-2",
    )

    bericht = client.post("/api/leads/namen-nachtragen?anzahl=25",
                          headers=auth_headers).json()

    assert bericht["geaendert"], "Der Lauf hat gar nichts geändert — dann prüft der Test nichts"
    for eintrag in bericht["geaendert"]:
        assert _name(eintrag["id"]) == eintrag["nachher"], (
            f"Gemeldet wurde {eintrag['nachher']!r}, in der Datenbank steht "
            f"{_name(eintrag['id'])!r}"
        )

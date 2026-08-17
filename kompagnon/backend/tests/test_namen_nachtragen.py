"""Die Betriebe, die wie ihre Domain heissen, bekommen ihren Namen zurueck.

Der Fehler ist behoben — aber nur fuer kuenftige Laeufe. Die dreissig
Betriebe, die am 17.08.2026 in der Liste standen, hiessen weiter
`alkozei.de`, `andovski.de`, `example.com`. Dreissig Mal von Hand nachfassen
ist keine Loesung, und ein SQL-Skript kann es nicht: Der richtige Name steht
nicht in der Datenbank, er steht im Impressum.

Deshalb ein Endpunkt, der genau die Betriebe nimmt, deren Name ein Platzhalter
ist, und fuer sie das Impressum noch einmal liest.
"""
import pytest


@pytest.fixture
def betriebe(app):
    """Drei Betriebe: zwei mit Platzhalter, einer mit gepflegtem Namen."""
    from database import SessionLocal, Lead

    db = SessionLocal()
    try:
        db.query(Lead).filter(Lead.website_url.like('%pytest-namen%')).delete(
            synchronize_session=False)
        db.commit()

        angelegt = {}
        for name, url in [
            ("pytest-namen-eins.de", "https://pytest-namen-eins.de"),
            ("pytest-namen-zwei.de", "https://pytest-namen-zwei.de"),
            ("Krause Haustechnik GmbH", "https://pytest-namen-drei.de"),
        ]:
            lead = Lead(company_name=name, website_url=url)
            db.add(lead)
            db.commit()
            db.refresh(lead)
            angelegt[name] = lead.id
        return angelegt
    finally:
        db.close()


def _name_von(lead_id: int) -> str:
    from database import SessionLocal, Lead

    db = SessionLocal()
    try:
        return db.query(Lead).filter(Lead.id == lead_id).first().company_name
    finally:
        db.close()


@pytest.fixture
def impressum_liefert(monkeypatch):
    """Der Impressum-Leser antwortet, ohne ins Netz zu gehen."""
    def einrichten(namen_je_domain):
        async def falscher_leser(url, *args, **kwargs):
            for domain, firmenname in namen_je_domain.items():
                if domain in url:
                    return {"success": True, "data": {"company_name": firmenname}}
            return {"success": False, "error": "kein Impressum"}

        monkeypatch.setattr(
            "services.impressum_scraper.extract_contact_from_impressum",
            falscher_leser,
        )
    return einrichten


def test_nur_die_platzhalter_werden_angefasst(client, auth_headers, betriebe,
                                              impressum_liefert):
    impressum_liefert({
        "pytest-namen-eins": "Alkozei Haustechnik GmbH",
        "pytest-namen-zwei": "Andovski Sanitär",
        "pytest-namen-drei": "Etwas ganz anderes",
    })

    antwort = client.post("/api/leads/namen-nachtragen", headers=auth_headers)

    assert antwort.status_code == 200
    assert _name_von(betriebe["pytest-namen-eins.de"]) == "Alkozei Haustechnik GmbH"
    assert _name_von(betriebe["pytest-namen-zwei.de"]) == "Andovski Sanitär"
    # Der gepflegte Name bleibt, obwohl das Impressum etwas anderes sagt.
    assert _name_von(betriebe["Krause Haustechnik GmbH"]) == "Krause Haustechnik GmbH"


def test_der_bericht_nennt_jeden_einzelnen(client, auth_headers, betriebe,
                                           impressum_liefert):
    impressum_liefert({"pytest-namen-eins": "Alkozei Haustechnik GmbH"})

    bericht = client.post("/api/leads/namen-nachtragen", headers=auth_headers).json()

    geaendert = {e["vorher"]: e["nachher"] for e in bericht["geaendert"]}
    assert geaendert.get("pytest-namen-eins.de") == "Alkozei Haustechnik GmbH"
    # Wo das Impressum nichts hergab, steht das auch da — statt stiller Stille.
    assert any(e["betrieb"] == "pytest-namen-zwei.de" for e in bericht["ohne_ergebnis"])


def test_ohne_impressum_bleibt_der_platzhalter(client, auth_headers, betriebe,
                                               impressum_liefert):
    impressum_liefert({})

    antwort = client.post("/api/leads/namen-nachtragen", headers=auth_headers)

    assert antwort.status_code == 200
    assert antwort.json()["geaendert"] == []
    assert _name_von(betriebe["pytest-namen-eins.de"]) == "pytest-namen-eins.de"


def test_ein_kunde_darf_das_nicht(client, kunde_headers):
    antwort = client.post("/api/leads/namen-nachtragen", headers=kunde_headers)

    assert antwort.status_code == 403


def test_ohne_anmeldung_gar_nicht(client):
    antwort = client.post("/api/leads/namen-nachtragen")

    assert antwort.status_code in (401, 403)

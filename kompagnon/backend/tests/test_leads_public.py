"""
Der oeffentliche Lead-Endpunkt der Landingpage.

Diese Route ist unauthentifiziert erreichbar und stoesst anschliessend einen
kostenpflichtigen Audit-Lauf an — entsprechend genau sollte sie sich verhalten.
"""


def test_lead_wird_angelegt(client):
    response = client.post(
        "/api/leads/public",
        json={
            "website_url": "https://testbetrieb-heizung.de",
            "email": "kontakt@testbetrieb-heizung.de",
            "lead_source": "pytest",
        },
    )

    assert response.status_code == 200
    assert isinstance(response.json()["id"], int)


def test_url_ohne_schema_wird_ergaenzt(client):
    response = client.post(
        "/api/leads/public",
        json={"website_url": "testbetrieb-sanitaer.de", "email": "a@b.de"},
    )

    assert response.status_code == 200

    from database import Lead, SessionLocal
    db = SessionLocal()
    try:
        lead = db.query(Lead).filter(Lead.id == response.json()["id"]).first()
        assert lead.website_url.startswith("https://")
    finally:
        db.close()


def test_gleiche_domain_erzeugt_keinen_zweiten_lead(client):
    erster = client.post(
        "/api/leads/public",
        json={"website_url": "https://www.doppelt-erfasst.de", "email": ""},
    )
    zweiter = client.post(
        "/api/leads/public",
        json={"website_url": "http://doppelt-erfasst.de/kontakt", "email": ""},
    )

    assert erster.status_code == 200
    assert zweiter.status_code == 200
    assert erster.json()["id"] == zweiter.json()["id"]


def test_nachgereichte_email_wird_ergaenzt(client):
    erster = client.post(
        "/api/leads/public",
        json={"website_url": "https://spaeter-email.de", "email": ""},
    )
    client.post(
        "/api/leads/public",
        json={"website_url": "https://spaeter-email.de", "email": "chef@spaeter-email.de"},
    )

    from database import Lead, SessionLocal
    db = SessionLocal()
    try:
        lead = db.query(Lead).filter(Lead.id == erster.json()["id"]).first()
        assert lead.email == "chef@spaeter-email.de"
    finally:
        db.close()


def test_fehlende_url_wird_abgelehnt(client):
    response = client.post("/api/leads/public", json={"email": "a@b.de"})

    assert response.status_code == 400

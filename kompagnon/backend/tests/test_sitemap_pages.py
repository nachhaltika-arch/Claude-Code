"""Der Entwurf muss auch auf einer Pflichtseite ankommen.

Die Design-Vorschau schreibt ihr gerendertes HTML nach `mockup_html` — das ist
der Weg, auf dem der Wireframe-Zweig auf der ausgelieferten Seite landet.
Pflichtseiten (Impressum, Datenschutz) sind gegen Umbenennen, Verschieben und
Löschen gesperrt; ihr Entwurf war es bis dahin auch, und zwar stillschweigend:
Die API antwortete mit 200 und verwarf das Feld.
"""
import pytest


@pytest.fixture
def lead_mit_seiten(client, auth_headers):
    """Ein Lead mit zwei Seiten — eine freie, eine Pflichtseite."""
    from database import Lead, SessionLocal, engine
    from routers.sitemap import SitemapPage

    # `sitemap_pages` steht in routers/sitemap.py, nicht in database.py — beim
    # Anlegen des Testschemas ist die Klasse deshalb noch nicht importiert und
    # die Tabelle fehlt. Im Betrieb legt sie `main.py::_run_migrations` an.
    SitemapPage.__table__.create(bind=engine, checkfirst=True)

    db = SessionLocal()
    try:
        lead = Lead(company_name="Pytest Sitemap GmbH", email="sitemap@pytest.local")
        db.add(lead)
        db.commit()
        db.refresh(lead)

        frei = SitemapPage(lead_id=lead.id, page_name="Leistungen", position=1)
        pflicht = SitemapPage(lead_id=lead.id, page_name="Impressum", position=2,
                              ist_pflichtseite=True)
        db.add_all([frei, pflicht])
        db.commit()
        db.refresh(frei)
        db.refresh(pflicht)
        ids = (lead.id, frei.id, pflicht.id)
    finally:
        db.close()

    yield ids

    db = SessionLocal()
    try:
        db.query(SitemapPage).filter(SitemapPage.lead_id == ids[0]).delete()
        db.query(Lead).filter(Lead.id == ids[0]).delete()
        db.commit()
    finally:
        db.close()


ENTWURF = '<style>.bg-white{background:#fff}</style><section data-block="hero">…</section>'


def test_entwurf_landet_auf_einer_freien_seite(client, auth_headers, lead_mit_seiten):
    _, frei, _ = lead_mit_seiten

    antwort = client.put(f"/api/sitemap/pages/{frei}", headers=auth_headers,
                         json={"mockup_html": ENTWURF})

    assert antwort.status_code == 200, antwort.text
    assert antwort.json()["mockup_html"] == ENTWURF


def test_entwurf_landet_auch_auf_einer_pflichtseite(client, auth_headers, lead_mit_seiten):
    """Gesperrt ist die Struktur, nicht der Inhalt — ein Impressum braucht
    genauso ein Aussehen wie jede andere Seite."""
    _, _, pflicht = lead_mit_seiten

    antwort = client.put(f"/api/sitemap/pages/{pflicht}", headers=auth_headers,
                         json={"mockup_html": ENTWURF})

    assert antwort.status_code == 200, antwort.text
    assert antwort.json()["mockup_html"] == ENTWURF, \
        "Das Feld wurde verworfen — die Oberflaeche haette Erfolg gemeldet."


def test_die_struktur_einer_pflichtseite_bleibt_gesperrt(client, auth_headers,
                                                         lead_mit_seiten):
    """Sonst wäre mit dem Entwurf auch das Umbenennen durchgerutscht."""
    _, _, pflicht = lead_mit_seiten

    antwort = client.put(f"/api/sitemap/pages/{pflicht}", headers=auth_headers,
                         json={"page_name": "Umbenannt", "position": 99})

    assert antwort.status_code == 200, antwort.text
    assert antwort.json()["page_name"] == "Impressum"

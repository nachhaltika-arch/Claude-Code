"""Der Canvas an der Route: Ausgabe, Ruecknahme, Sperre.

Die Uebersetzung selbst prueft `test_design_canvas.py` ohne Datenbank. Hier
geht es um das, was nur am laufenden Endpunkt zu sehen ist: dass die Sperre
haelt, dass die Ruecknahme wirklich schreibt — und dass sie **vorher** eine
Version anlegt. Ohne die waere der Canvas ein Editor ohne Verlauf auf Markup,
das ausgeliefert wird.
"""
import pytest

from services.canvas_artboards import artboard


@pytest.fixture(scope="module")
def betrieb_mit_seite(app):
    """Ein Betrieb mit einer Sitemap-Seite und einem bestehenden Design."""
    from database import Lead, SessionLocal, engine
    from routers.designs import DesignVersion
    from routers.sitemap import SitemapPage

    # `sitemap_pages` und `mockup_versions` stehen in den Routern, nicht in
    # `database.py` — beim Anlegen des Testschemas sind die Klassen deshalb
    # noch nicht importiert und die Tabellen fehlen. Im Betrieb legt sie
    # `migrations_runtime.py::run_migrations` an.
    SitemapPage.__table__.create(bind=engine, checkfirst=True)
    DesignVersion.__table__.create(bind=engine, checkfirst=True)

    db = SessionLocal()
    try:
        lead = Lead(
            company_name="Canvas Testbetrieb GmbH",
            contact_name="Test",
            email="canvas@kompagnon.local",
            trade="heizung",
            brand_primary_color="#C0392B",
        )
        db.add(lead)
        db.commit()
        db.refresh(lead)

        seite = SitemapPage(
            lead_id=lead.id,
            page_name="Startseite",
            position=0,
            mockup_html="<h1>Alt</h1>",
        )
        db.add(seite)
        db.commit()
        db.refresh(seite)
        return {"lead_id": lead.id, "page_id": seite.id}
    finally:
        db.close()


def test_ohne_anmeldung_kein_canvas(client, betrieb_mit_seite):
    antwort = client.get(f"/api/design-canvas/{betrieb_mit_seite['lead_id']}")

    assert antwort.status_code in (401, 403)


def test_ausgabe_nennt_die_artboards(client, auth_headers, betrieb_mit_seite):
    # Act
    antwort = client.get(
        f"/api/design-canvas/{betrieb_mit_seite['lead_id']}", headers=auth_headers
    )

    # Assert
    assert antwort.status_code == 200
    daten = antwort.json()
    seite = betrieb_mit_seite["page_id"]
    assert f"Design{seite}.dc.html" in daten["files"]
    assert "<h1>Alt</h1>" in daten["files"][f"Design{seite}.dc.html"]
    assert "#C0392B" in daten["files"]["Styleguide.dc.html"]


def test_unbekannter_betrieb_ist_404(client, auth_headers):
    assert client.get("/api/design-canvas/999999", headers=auth_headers).status_code == 404


def test_ruecknahme_schreibt_und_versioniert(client, auth_headers, betrieb_mit_seite):
    # Arrange
    from database import SessionLocal
    from routers.designs import DesignVersion
    from routers.sitemap import SitemapPage

    lead_id, page_id = betrieb_mit_seite["lead_id"], betrieb_mit_seite["page_id"]
    dateien = {f"Design{page_id}.dc.html": artboard(stil="", inhalt="<h1>Neu aus dem Canvas</h1>")}

    # Act
    antwort = client.post(
        f"/api/design-canvas/{lead_id}/import",
        json={"files": dateien},
        headers=auth_headers,
    )

    # Assert
    assert antwort.status_code == 200
    assert [e["page_id"] for e in antwort.json()["geaendert"]] == [page_id]

    db = SessionLocal()
    try:
        seite = db.query(SitemapPage).filter(SitemapPage.id == page_id).first()
        assert seite.mockup_html == "<h1>Neu aus dem Canvas</h1>"

        versionen = (db.query(DesignVersion)
                       .filter(DesignVersion.sitemap_page_id == page_id).all())
        assert len(versionen) == 1
        assert versionen[0].html_content == "<h1>Neu aus dem Canvas</h1>"
        assert versionen[0].version_name.startswith("Aus dem Canvas")
    finally:
        db.close()


def test_unveraendertes_artboard_legt_keine_version_an(client, auth_headers,
                                                       betrieb_mit_seite):
    """Ein Speichern im Canvas schickt **alle** Artboards zurueck, nicht nur
    die geaenderten. Ohne diesen Vergleich waechst der Versionsverlauf bei
    jedem Speichern um jede Seite."""
    from database import SessionLocal
    from routers.designs import DesignVersion

    lead_id, page_id = betrieb_mit_seite["lead_id"], betrieb_mit_seite["page_id"]
    dateien = {f"Design{page_id}.dc.html": artboard(stil="", inhalt="<h1>Neu aus dem Canvas</h1>")}

    antwort = client.post(
        f"/api/design-canvas/{lead_id}/import",
        json={"files": dateien},
        headers=auth_headers,
    )

    assert antwort.status_code == 200
    assert antwort.json()["geaendert"] == []
    assert antwort.json()["gelesen"] == 1

    db = SessionLocal()
    try:
        anzahl = (db.query(DesignVersion)
                    .filter(DesignVersion.sitemap_page_id == page_id).count())
        assert anzahl == 1
    finally:
        db.close()

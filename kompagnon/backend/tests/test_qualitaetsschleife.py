"""
Die Qualitätsschleife — der eigene Audit gegen die selbst gebaute Seite.

Schritt 8 des Design-Konzepts: erst auf eine Vorschau deployen, dann den
eigenen Katalog gegen diese Adresse laufen lassen. Was wir Kunden vorwerfen,
dürfen wir selbst nicht liefern.

Der gefährliche Teil ist der Deploy. Eine Vorschau, die versehentlich auf der
Site des Kunden landet, überschreibt dessen Live-Auftritt — deshalb steht hier
zuerst, wohin *nicht* deployt werden darf.
"""
import asyncio

import pytest

from services import qualitaetsschleife as qs


class SeiteAttrappe:
    def __init__(self, gjs_html="", gjs_css="", mockup_html="",
                 page_name="Startseite", ki_meta_description=""):
        self.id = 7
        self.gjs_html = gjs_html
        self.gjs_css = gjs_css
        self.mockup_html = mockup_html
        self.page_name = page_name
        self.ki_meta_description = ki_meta_description


# ── Woher der Inhalt kommt ─────────────────────────────────────────

def test_der_editorstand_hat_vorrang():
    # Arrange — im Editor justiert, der Entwurf ist älter
    seite = SeiteAttrappe(gjs_html="<h1>Justiert</h1>", gjs_css="h1{color:red}",
                          mockup_html="<h1>Entwurf</h1>")

    # Act
    html, css = qs.seiten_inhalt(seite)

    # Assert
    assert "Justiert" in html
    assert css == "h1{color:red}"


def test_ohne_editorstand_zaehlt_der_entwurf():
    seite = SeiteAttrappe(mockup_html="<h1>Entwurf</h1>")

    html, _ = qs.seiten_inhalt(seite)

    assert "Entwurf" in html


def test_eine_leere_seite_wird_nicht_geprueft():
    seite = SeiteAttrappe()

    with pytest.raises(qs.NichtsZuPruefen):
        qs.seiten_inhalt(seite)


# ── Wohin deployt wird — und wohin nicht ───────────────────────────

def test_ohne_eigene_vorschau_site_wird_nicht_deployt(monkeypatch):
    # Arrange — die Variable fehlt
    monkeypatch.delenv(qs.VORSCHAU_SITE_ENV, raising=False)
    seite = SeiteAttrappe(mockup_html="<h1>Hallo</h1>")

    # Act & Assert — lieber gar nicht deployen als irgendwohin
    with pytest.raises(qs.KeineVorschauSite):
        asyncio.run(qs.deploye_vorschau(seite))


def test_die_vorschau_geht_auf_die_vorschau_site(monkeypatch):
    # Arrange
    monkeypatch.setenv(qs.VORSCHAU_SITE_ENV, "vorschau-site-123")
    gesehen = {}

    async def deploy_attrappe(site_id, html, css="", **kw):
        gesehen.update(site_id=site_id, html=html, css=css, **kw)
        return {"deploy_url": "https://abc--vorschau.netlify.app",
                "deploy_id": "d1", "state": "ready"}

    monkeypatch.setattr(qs, "deploy_html", deploy_attrappe)
    seite = SeiteAttrappe(mockup_html="<h1>Hallo</h1>", page_name="Leistungen")

    # Act
    url = asyncio.run(qs.deploye_vorschau(seite))

    # Assert
    assert gesehen["site_id"] == "vorschau-site-123"
    assert url == "https://abc--vorschau.netlify.app"


def test_die_kundensite_wird_niemals_zum_ziel(monkeypatch):
    # Arrange — die Site des Kunden steht in derselben Umgebung
    monkeypatch.setenv(qs.VORSCHAU_SITE_ENV, "vorschau-site-123")
    monkeypatch.setenv("NETLIFY_SITE_ID", "kunden-site-live")
    ziele = []

    async def deploy_attrappe(site_id, html, css="", **kw):
        ziele.append(site_id)
        return {"deploy_url": "https://abc--vorschau.netlify.app",
                "deploy_id": "d1", "state": "ready"}

    monkeypatch.setattr(qs, "deploy_html", deploy_attrappe)

    # Act
    asyncio.run(qs.deploye_vorschau(SeiteAttrappe(mockup_html="<h1>x</h1>")))

    # Assert
    assert ziele == ["vorschau-site-123"]
    assert "kunden-site-live" not in ziele


def test_die_vorschau_traegt_titel_und_beschreibung(monkeypatch):
    # Arrange
    monkeypatch.setenv(qs.VORSCHAU_SITE_ENV, "vorschau-site-123")
    gesehen = {}

    async def deploy_attrappe(site_id, html, css="", **kw):
        gesehen.update(kw)
        return {"deploy_url": "https://x.netlify.app", "deploy_id": "d",
                "state": "ready"}

    monkeypatch.setattr(qs, "deploy_html", deploy_attrappe)
    seite = SeiteAttrappe(mockup_html="<h1>x</h1>", page_name="Wärmepumpe",
                          ki_meta_description="Wärmepumpe in Musterstadt")

    # Act
    asyncio.run(qs.deploye_vorschau(seite, firmenname="Referenz GmbH"))

    # Assert — sonst prüft das Audit einen Titel, den die echte Seite nie hat
    assert gesehen["page_title"] == "Wärmepumpe"
    assert gesehen["meta_description"] == "Wärmepumpe in Musterstadt"
    assert gesehen["company_name"] == "Referenz GmbH"


def test_die_vorschau_wird_nicht_indexiert(monkeypatch):
    # Arrange — eine Vorschau der Kundenseite darf nicht in den Suchindex
    monkeypatch.setenv(qs.VORSCHAU_SITE_ENV, "vorschau-site-123")
    gesehen = {}

    async def deploy_attrappe(site_id, html, css="", **kw):
        gesehen.update(html=html, **kw)
        return {"deploy_url": "https://x.netlify.app", "deploy_id": "d",
                "state": "ready"}

    monkeypatch.setattr(qs, "deploy_html", deploy_attrappe)

    # Act
    asyncio.run(qs.deploye_vorschau(SeiteAttrappe(mockup_html="<h1>x</h1>")))

    # Assert
    assert "noindex" in gesehen["html"].lower()


# ── Der Endpunkt, der die Schleife anstößt ─────────────────────────

@pytest.fixture
def seite(client, auth_headers):
    """Eine echte Sitemap-Seite mit Entwurf, an einem echten Lead."""
    from database import Base, Lead, SessionLocal, engine
    from routers.sitemap import SitemapPage

    # `sitemap_pages` wird erst mit dem Router registriert, also nach dem
    # Schema-Aufbau in conftest. Hier nachziehen statt dort raten.
    Base.metadata.create_all(bind=engine, tables=[SitemapPage.__table__])

    db = SessionLocal()
    try:
        lead = Lead(company_name="Prüf GmbH", email="pruef@example.de")
        db.add(lead)
        db.commit()
        db.refresh(lead)

        mit = SitemapPage(lead_id=lead.id, page_name="Startseite",
                          mockup_html="<h1>Wärmepumpe in Musterstadt</h1>")
        ohne = SitemapPage(lead_id=lead.id, page_name="Leer")
        db.add_all([mit, ohne])
        db.commit()
        db.refresh(mit)
        db.refresh(ohne)
        return {"mit_inhalt": mit.id, "ohne_inhalt": ohne.id}
    finally:
        db.close()


def test_die_pruefung_braucht_eine_anmeldung(client):
    # Arrange & Act — ohne Anmeldung darf niemand Deploys auslösen
    antwort = client.post("/api/pages/1/qualitaetspruefung")

    # Assert
    assert antwort.status_code in (401, 403)


def test_eine_unbekannte_seite_meldet_sich_klar(client, auth_headers, seite):
    antwort = client.post("/api/pages/999999/qualitaetspruefung",
                          headers=auth_headers)

    assert antwort.status_code == 404


def test_ohne_vorschau_site_bleibt_die_pruefung_aus(
        client, auth_headers, seite, monkeypatch):
    # Arrange
    monkeypatch.delenv(qs.VORSCHAU_SITE_ENV, raising=False)

    # Act
    antwort = client.post(
        f"/api/pages/{seite['mit_inhalt']}/qualitaetspruefung",
        headers=auth_headers)

    # Assert — 503, nicht 500: fehlende Einrichtung, kein Absturz
    assert antwort.status_code == 503
    assert qs.VORSCHAU_SITE_ENV in antwort.json()["detail"]


def test_die_pruefung_legt_ein_audit_auf_die_vorschau_an(
        client, auth_headers, seite, monkeypatch):
    # Arrange
    monkeypatch.setenv(qs.VORSCHAU_SITE_ENV, "vorschau-123")

    async def deploy_attrappe(**_kw):
        return {"deploy_url": "https://pruef--vorschau.netlify.app",
                "deploy_id": "d1", "state": "ready"}

    monkeypatch.setattr(qs, "deploy_html", deploy_attrappe)

    # Act
    antwort = client.post(
        f"/api/pages/{seite['mit_inhalt']}/qualitaetspruefung",
        headers=auth_headers)

    # Assert
    assert antwort.status_code == 200, antwort.text
    inhalt = antwort.json()
    assert inhalt["vorschau_url"] == "https://pruef--vorschau.netlify.app"
    assert inhalt["audit_id"]


def test_das_audit_zeigt_auf_die_vorschau_nicht_auf_die_kundendomain(
        client, auth_headers, seite, monkeypatch):
    # Arrange
    monkeypatch.setenv(qs.VORSCHAU_SITE_ENV, "vorschau-123")

    async def deploy_attrappe(**_kw):
        return {"deploy_url": "https://pruef--vorschau.netlify.app",
                "deploy_id": "d1", "state": "ready"}

    monkeypatch.setattr(qs, "deploy_html", deploy_attrappe)

    # Act
    audit_id = client.post(
        f"/api/pages/{seite['mit_inhalt']}/qualitaetspruefung",
        headers=auth_headers).json()["audit_id"]

    # Assert — geprüft wird der Entwurf, nicht der Altauftritt des Kunden
    from database import AuditResult, SessionLocal
    db = SessionLocal()
    try:
        audit = db.query(AuditResult).filter(AuditResult.id == audit_id).first()
        assert audit.website_url == "https://pruef--vorschau.netlify.app"
        assert audit.sitemap_page_id == seite["mit_inhalt"]
    finally:
        db.close()


def test_eine_leere_seite_wird_abgelehnt(
        client, auth_headers, seite, monkeypatch):
    # Arrange
    monkeypatch.setenv(qs.VORSCHAU_SITE_ENV, "vorschau-123")

    # Act
    antwort = client.post(
        f"/api/pages/{seite['ohne_inhalt']}/qualitaetspruefung",
        headers=auth_headers)

    # Assert
    assert antwort.status_code == 400

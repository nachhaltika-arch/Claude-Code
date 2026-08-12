"""
Der öffentliche Widget-Endpunkt.

Er ist ohne Login von fremden Landingpages erreichbar, stößt einen
kostenpflichtigen Audit-Lauf an und verschickt E-Mails an eingegebene
Adressen. Diese Tests decken die Abwehr ab — nicht den Audit-Lauf selbst,
damit sie ohne Netzzugriff bleiben.
"""
from datetime import datetime, timedelta

import pytest

from database import SessionLocal, WidgetRequest
from routers import widget


@pytest.fixture
def aufraeumen():
    """Entfernt die in einem Test angelegten Anfragen wieder."""
    angelegte = []
    yield angelegte
    db = SessionLocal()
    try:
        db.query(WidgetRequest).filter(WidgetRequest.email.in_(angelegte)).delete(
            synchronize_session=False)
        db.commit()
    finally:
        db.close()


# ── Eingabeprüfung ────────────────────────────────────────────────────

@pytest.mark.parametrize("email", ["", "keine-mail", "a@b", "@firma.de", "name@firma"])
def test_ungueltige_email_wird_abgelehnt(client, email):
    r = client.post("/api/widget/audit",
                    json={"email": email, "website_url": "https://example.com"})
    assert r.status_code == 400
    assert "E-Mail" in r.json()["detail"]


@pytest.mark.parametrize("url", [
    "http://127.0.0.1/",
    "http://localhost:8000/",
    "http://169.254.169.254/latest/meta-data/",
    "http://192.168.0.1/",
    "file:///etc/passwd",
])
def test_interne_adressen_werden_abgelehnt(client, url):
    """Ohne diese Sperre wäre das Widget ein offener SSRF-Zugang."""
    r = client.post("/api/widget/audit",
                    json={"email": "test@example.com", "website_url": url})
    assert r.status_code == 400
    assert "nicht prüfen" in r.json()["detail"]


# ── Ratenbegrenzung ───────────────────────────────────────────────────

def test_zu_viele_anfragen_pro_email_werden_gebremst(client, aufraeumen):
    email = "vielfach@example-test.de"
    aufraeumen.append(email)

    db = SessionLocal()
    try:
        for _ in range(3):
            db.add(WidgetRequest(email=email, website_url="https://example.com",
                                 created_at=datetime.utcnow()))
        db.commit()
    finally:
        db.close()

    r = client.post("/api/widget/audit",
                    json={"email": email, "website_url": "https://example.com"})
    assert r.status_code == 429
    assert "Postfach" in r.json()["detail"]


def test_alte_anfragen_zaehlen_nicht_mehr_mit(client, aufraeumen):
    """Die Begrenzung gilt pro Tag — gestern darf die Nutzung nicht blockieren."""
    email = "gestern@example-test.de"
    aufraeumen.append(email)

    db = SessionLocal()
    try:
        for _ in range(3):
            db.add(WidgetRequest(email=email, website_url="https://example.com",
                                 created_at=datetime.utcnow() - timedelta(days=2)))
        db.commit()
        alt = db.query(WidgetRequest).filter(WidgetRequest.email == email).count()
    finally:
        db.close()

    assert alt == 3
    # Eine interne Adresse verhindert den echten Audit-Lauf, die Ratenprüfung
    # läuft aber davor — ein 400 statt 429 belegt, dass nicht gebremst wurde.
    r = client.post("/api/widget/audit",
                    json={"email": email, "website_url": "http://127.0.0.1/"})
    assert r.status_code == 400


def test_ein_ganzer_betrieb_wird_nicht_zugemuellt(client, aufraeumen):
    """Viele erfundene Adressen derselben Firma, jede unter ihrer Einzelgrenze."""
    # Arrange
    domain = "zielfirma-test.de"
    db = SessionLocal()
    try:
        for nummer in range(10):
            adresse = f"person{nummer}@{domain}"
            aufraeumen.append(adresse)
            db.add(WidgetRequest(email=adresse, website_url="https://example.com",
                                 created_at=datetime.utcnow()))
        db.commit()
    finally:
        db.close()

    # Act — eine weitere, bisher unbenutzte Adresse derselben Firma
    neue = f"chef@{domain}"
    aufraeumen.append(neue)
    r = client.post("/api/widget/audit",
                    json={"email": neue, "website_url": "https://example.com"})

    # Assert
    assert r.status_code == 429


def test_freemail_adressen_sperren_sich_nicht_gegenseitig(client, aufraeumen):
    """Bei gmx & Co. sagt die Domain nichts über den Empfänger aus."""
    # Arrange
    db = SessionLocal()
    try:
        for nummer in range(10):
            adresse = f"kunde{nummer}@gmx.de"
            aufraeumen.append(adresse)
            db.add(WidgetRequest(email=adresse, website_url="https://example.com",
                                 created_at=datetime.utcnow()))
        db.commit()
    finally:
        db.close()

    # Act — eine interne Adresse stoppt den echten Audit-Lauf; die Ratenprüfung
    # läuft davor, ein 400 statt 429 belegt also, dass nicht gebremst wurde.
    neue = "neuer-kunde@gmx.de"
    aufraeumen.append(neue)
    r = client.post("/api/widget/audit",
                    json={"email": neue, "website_url": "http://127.0.0.1/"})

    # Assert
    assert r.status_code == 400


# ── Herkunft des Aufrufers ────────────────────────────────────────────

class _AnfrageAttrappe:
    """Nur so viel Request, wie die Adressermittlung anfasst."""

    def __init__(self, headers, client_host="10.0.0.9"):
        self.headers = headers
        self.client = type("Client", (), {"host": client_host})()


def test_selbst_mitgeschickter_forwarded_kopf_bestimmt_die_zaehlung_nicht():
    """Sonst sucht sich ein Angreifer pro Anfrage eine neue Identität aus."""
    # Arrange — vorne die Behauptung des Aufrufers, hinten der echte Proxy-Eintrag
    anfrage = _AnfrageAttrappe({"x-forwarded-for": "1.2.3.4, 203.0.113.7"})

    # Act
    ip = widget._client_ip(anfrage)

    # Assert
    assert ip == "203.0.113.7"


def test_selbst_gesetzter_cloudflare_kopf_wird_ohne_proxy_ignoriert():
    """Der Kopf ist nur so viel wert wie der Proxy, der ihn setzt.

    Die Anwendung steht direkt auf Render, ohne Cloudflare davor. Damit ist
    ``CF-Connecting-IP`` reine Behauptung des Aufrufers: wer ihn pro Anfrage
    neu würfelt, hat jede Grenze pro IP ausgehebelt und kann allein das
    Tageskontingent an Analysen und E-Mails verbrauchen.
    """
    # Arrange — der Angreifer behauptet eine frische Adresse
    anfrage = _AnfrageAttrappe({
        "cf-connecting-ip": "198.51.100.77",
        "x-forwarded-for": "1.2.3.4, 203.0.113.7",
    })

    # Act
    ip = widget._client_ip(anfrage)

    # Assert — gezählt wird der Eintrag des echten Proxys
    assert ip == "203.0.113.7"


def test_proxy_kopf_gilt_erst_wenn_er_eingerichtet_ist(monkeypatch):
    """Steht doch ein Proxy davor, wird er benannt — dann zählt sein Kopf."""
    # Arrange
    monkeypatch.setenv("TRUSTED_PROXY_HEADER", "cf-connecting-ip")
    anfrage = _AnfrageAttrappe({
        "cf-connecting-ip": "203.0.113.9",
        "x-forwarded-for": "1.2.3.4, 5.6.7.8",
    })

    # Act / Assert
    assert widget._client_ip(anfrage) == "203.0.113.9"


def test_ohne_proxy_kopf_zaehlt_die_verbindung_selbst():
    assert widget._client_ip(_AnfrageAttrappe({})) == "10.0.0.9"


# ── Bericht und Bestätigung ───────────────────────────────────────────

def test_unbekannter_berichts_token_gibt_404(client):
    assert client.get("/api/widget/report/gibtesnicht").status_code == 404


def test_unbekannter_bestaetigungs_token_zeigt_hinweisseite(client):
    r = client.get("/api/widget/confirm/gibtesnicht")
    assert r.status_code == 404
    assert "nicht mehr gültig" in r.text


def test_teaser_fuer_unbekannten_token_gibt_404(client):
    assert client.get("/api/widget/teaser/gibtesnicht").status_code == 404


@pytest.fixture
def fremde_analyse():
    """Eine Analyse, wie sie im Tool über die Lead-Akquise entsteht.

    Sie gehört zu keiner Widget-Anfrage — niemand von außen darf sie sehen.
    """
    from database import AuditResult

    db = SessionLocal()
    try:
        audit = AuditResult(
            website_url="https://interner-interessent.example",
            company_name="Interner Interessent",
            status="completed",
            total_score=41,
            level="Homepage Standard Bronze",
        )
        db.add(audit)
        db.commit()
        db.refresh(audit)
        audit_id = audit.id
    finally:
        db.close()

    yield audit_id

    db = SessionLocal()
    try:
        db.query(AuditResult).filter(AuditResult.id == audit_id).delete()
        db.commit()
    finally:
        db.close()


def test_fremde_analyse_ist_ueber_den_teaser_nicht_abrufbar(client, fremde_analyse):
    """Der Teaser lief auf der laufenden Nummer der Analyse.

    Damit liess sich die Tabelle von 1 aufwärts durchzählen: jede im Tool
    angelegte Analyse mit Firma, Adresse, Punktzahl und Schwachstellen war
    ohne Login abrufbar — also die gesamte Interessentenliste.
    """
    # Act — genau der Aufruf, der vorher die fremde Analyse ausgab
    r = client.get(f"/api/widget/teaser/{fremde_analyse}")

    # Assert
    assert r.status_code == 404
    assert "Interner Interessent" not in r.text


def test_teaser_gibt_die_eigene_analyse_mit_gueltigem_token_aus(client, fremde_analyse,
                                                                aufraeumen):
    """Die Gegenprobe: mit dem Token der eigenen Anfrage geht es weiter."""
    # Arrange — eine Widget-Anfrage, die auf dieselbe Analyse zeigt
    aufraeumen.append("teaser-probe@firma-xy.de")
    db = SessionLocal()
    try:
        anfrage = WidgetRequest(
            email="teaser-probe@firma-xy.de",
            website_url="https://interner-interessent.example",
            poll_token="probe-token-fuer-den-test",
            report_token="probe-berichts-token",
            audit_id=fremde_analyse,
        )
        db.add(anfrage)
        db.commit()
    finally:
        db.close()

    # Act
    r = client.get("/api/widget/teaser/probe-token-fuer-den-test")

    # Assert
    assert r.status_code == 200
    assert r.json()["total_score"] == 41


def test_bestaetigungsseite_traegt_die_schutz_kopfzeilen(client):
    """Die Seite hängt an einem Token in der Adresszeile.

    Ohne ``Referrer-Policy`` reicht ein Klick auf einen Link, und das Token
    steht im Referer der fremden Seite. Ohne ``X-Frame-Options`` lässt sich
    die Seite in eine fremde einrahmen und der Bestätigungsklick erschleichen.
    """
    r = client.get("/api/widget/confirm/gibtesnicht")

    assert r.headers["x-frame-options"] == "DENY"
    assert r.headers["referrer-policy"] == "no-referrer"
    assert "no-store" in r.headers["cache-control"]


def test_berichtsseite_wird_nicht_indexiert():
    """Ein Bericht mit Kundendaten darf nicht in Suchmaschinen landen."""
    from services.widget_report import confirmation_page

    assert 'name="robots" content="noindex,nofollow"' in confirmation_page(True)

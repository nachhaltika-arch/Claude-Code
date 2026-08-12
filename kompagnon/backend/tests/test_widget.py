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


# ── Wohin der Link aus der E-Mail zeigt ───────────────────────────────

def test_berichtslink_zeigt_auf_den_eigenen_server(monkeypatch):
    """Der Link ist der einzige Weg zum Bericht — er muss hierher zeigen.

    Ohne ``API_BASE_URL`` fiel der Code auf die fest eingetragene
    Produktiv-Adresse zurück. Auf Staging hiess das: der Audit lief hier,
    das Token liegt hier, und die E-Mail schickte den Empfänger zum
    Produktiv-Server, der das Token nicht kennt — „Not Found". Render setzt
    ``RENDER_EXTERNAL_URL`` für jeden Dienst selbst; damit stimmt die
    Adresse ohne eine Variable, die jemand setzen muss.
    """
    from services import widget_report

    # Arrange — wie auf Staging: eigene Variable fehlt, Render kennt sich
    monkeypatch.delenv("API_BASE_URL", raising=False)
    monkeypatch.setenv("RENDER_EXTERNAL_URL",
                       "https://kompagnon-backend-staging.onrender.com")

    # Act / Assert
    assert widget_report.api_base_url() == \
        "https://kompagnon-backend-staging.onrender.com"
    assert widget_report.report_url("tok").startswith(
        "https://kompagnon-backend-staging.onrender.com/api/widget/report/")


def test_eigene_einstellung_schlaegt_die_von_render(monkeypatch):
    from services import widget_report

    monkeypatch.setenv("API_BASE_URL", "https://api.kompagnon.eu/")
    monkeypatch.setenv("RENDER_EXTERNAL_URL", "https://irgendwas.onrender.com")

    assert widget_report.api_base_url() == "https://api.kompagnon.eu"


# ── Marke ─────────────────────────────────────────────────────────────

# Zwei Werte, die hier jahrelang standen und in keiner CI belegt sind: ein
# Grün statt Pantone 3165 und ein Goldton statt Pantone 3945. Bericht und
# E-Mail sahen damit nach einer anderen Marke aus als das Tool.
ERFUNDENE_FARBEN = ("#0F2E2B", "#F5C518", "#04293a", "#207a92")


def _gerenderte_seiten() -> dict:
    """Alles, was das Backend als HTML ausliefert."""
    from services import widget_report

    return {
        "Berichts-Mail": widget_report.report_ready_email(
            company="Muster GmbH", token="t")[1],
        "Bestätigungsseite": widget_report.confirmation_page(True),
    }


def test_mails_und_seiten_tragen_die_echte_ci():
    from services import brand

    for name, text in _gerenderte_seiten().items():
        assert brand.DARK in text, f"{name}: Pantone 3165 fehlt"
        for erfunden in ERFUNDENE_FARBEN:
            assert erfunden.lower() not in text.lower(), \
                f"{name}: {erfunden} ist wieder da"


def test_das_widget_traegt_die_echte_ci():
    """Die Einbett-Seite liegt im Frontend und wird von keinem Test gebaut.

    Sie ist aber das erste, was ein Interessent von der Marke sieht — und
    hatte als einzige Datei eine komplett eigene Palette.
    """
    from pathlib import Path

    from services import brand

    widget = (Path(__file__).resolve().parents[2]
              / "frontend" / "public" / "embed" / "audit-widget.html")
    if not widget.exists():  # Backend wird ohne Frontend ausgeliefert
        pytest.skip("Frontend nicht vorhanden")

    text = widget.read_text(encoding="utf-8")
    for farbe in (brand.DARK, brand.MID, brand.YELLOW):
        assert farbe in text, f"{farbe} fehlt im Widget"
    for erfunden in ERFUNDENE_FARBEN:
        assert erfunden.lower() not in text.lower(), f"{erfunden} ist wieder da"


# ── Kein Werbebrief an eine unbestätigte Adresse ──────────────────────

def test_die_erste_mail_nennt_die_website_mit_keinem_wort():
    """Sie geht an eine Adresse, die noch niemand bestätigt hat.

    Wer eine fremde Adresse einträgt, löste dort früher einen Werbebrief mit
    Punktzahl, Mängelliste und Verkaufsknopf aus — unbestellte Werbung nach
    § 7 UWG, ausgelöst von einem Dritten. Diese Mail fragt nur, ob die
    Adresse stimmt. Auch der Berichtslink gehört noch nicht hinein: wer nicht
    bestätigt, bekommt nie einen.
    """
    from services import widget_report

    betreff, html = widget_report.verify_email(
        company="Muster GmbH", verify_token="v-123")

    assert widget_report.verify_url("v-123") in html
    assert "/api/widget/report/" not in html
    assert "checkout" not in html.lower()
    assert "Jetzt Webseite anfragen" not in html
    assert "bestätigen" in betreff.lower()


def test_die_zweite_mail_bringt_den_bericht_aber_keine_werbung():
    """Sie geht erst nach bestätigter Adresse raus."""
    from services import widget_report

    betreff, html = widget_report.report_ready_email(
        company="Muster GmbH", token="tok-123")

    assert widget_report.report_url("tok-123") in html
    assert "checkout" not in html.lower()
    assert "Jetzt Webseite anfragen" not in html
    assert "Muster GmbH" in betreff


def test_berichtsseite_traegt_pdf_und_angebot(client, fremde_analyse, aufraeumen):
    """Was aus der Mail verschwunden ist, muss hier ankommen.

    PDF und Angebot standen in der ersten Mail. Fielen sie ersatzlos weg,
    wäre der Umbau ein Rückschritt statt einer Verlagerung.
    """
    # Arrange
    aufraeumen.append("angebot@firma-xy.de")
    db = SessionLocal()
    try:
        db.add(WidgetRequest(
            email="angebot@firma-xy.de",
            website_url="https://interner-interessent.example",
            report_token="angebot-berichts-token",
            poll_token="angebot-poll-token",
            audit_id=fremde_analyse,
        ))
        db.commit()
    finally:
        db.close()

    # Act
    r = client.get("/api/widget/report/angebot-berichts-token")

    # Assert
    assert r.status_code == 200
    assert "/api/widget/report/angebot-berichts-token/pdf" in r.text
    assert "checkout/kompagnon" in r.text


def test_pdf_haengt_am_selben_token_wie_der_bericht(client):
    assert client.get("/api/widget/report/gibtesnicht/pdf").status_code == 404


def test_berichtsseite_haelt_den_klick_als_nachweis_fest(client, fremde_analyse,
                                                          aufraeumen):
    """Der Klick aus dem Postfach ist der Nachweis, dass die Adresse stimmt."""
    # Arrange
    aufraeumen.append("nachweis@firma-xy.de")
    db = SessionLocal()
    try:
        db.add(WidgetRequest(
            email="nachweis@firma-xy.de",
            website_url="https://interner-interessent.example",
            report_token="nachweis-berichts-token",
            poll_token="nachweis-poll-token",
            audit_id=fremde_analyse,
        ))
        db.commit()
    finally:
        db.close()

    # Act
    r = client.get("/api/widget/report/nachweis-berichts-token")

    # Assert
    assert r.status_code == 200
    db = SessionLocal()
    try:
        row = db.query(WidgetRequest).filter(
            WidgetRequest.report_token == "nachweis-berichts-token").first()
        assert row.report_confirmed_at is not None
    finally:
        db.close()


# ── Zwei Mails: erst bestätigen, dann der Bericht ─────────────────────

@pytest.fixture
def gesendete_mails(monkeypatch):
    """Fängt den Versand ab, statt echte Post zu verschicken."""
    briefe = []

    def _abfangen(to_email, subject, html_body, **kwargs):
        briefe.append({"an": to_email, "betreff": subject, "html": html_body})
        return True

    import services.email
    monkeypatch.setattr(services.email, "send_email", _abfangen)
    return briefe


def _anfrage_anlegen(email, audit_id, aufraeumen, **felder):
    aufraeumen.append(email)
    db = SessionLocal()
    try:
        row = WidgetRequest(
            email=email, website_url="https://interner-interessent.example",
            audit_id=audit_id, verify_token=felder.pop("verify_token", "v-tok"),
            report_token=felder.pop("report_token", "r-tok"),
            poll_token=felder.pop("poll_token", "p-tok"), **felder)
        db.add(row)
        db.commit()
        return row.id
    finally:
        db.close()


def test_ohne_bestaetigung_geht_kein_berichtslink_raus(client, fremde_analyse,
                                                       aufraeumen, gesendete_mails):
    """Der Kern der Umstellung.

    Vorher ging der Berichtslink sofort an jede eingetippte Adresse. Wer eine
    fremde eintrug, stellte dort die fertige Bewertung einer Website zu, die
    dem Empfänger gehört — ungefragt.
    """
    from routers.audit import send_widget_report

    anfrage_id = _anfrage_anlegen("unbestaetigt@firma-xy.de", fremde_analyse,
                                  aufraeumen, verify_token="v-unbestaetigt")

    send_widget_report(anfrage_id)

    assert gesendete_mails == []


def test_der_klick_bestaetigt_und_loest_die_zweite_mail_aus(client, fremde_analyse,
                                                            aufraeumen,
                                                            gesendete_mails):
    # Arrange
    anfrage_id = _anfrage_anlegen("bestaetigt@firma-xy.de", fremde_analyse,
                                  aufraeumen, verify_token="v-klick",
                                  report_token="r-klick", poll_token="p-klick")

    # Act
    r = client.get("/api/widget/verify/v-klick")

    # Assert
    assert r.status_code == 200
    assert "unterwegs" in r.text

    db = SessionLocal()
    try:
        row = db.query(WidgetRequest).filter(WidgetRequest.id == anfrage_id).first()
        assert row.verified_at is not None
        assert row.report_sent_at is not None
    finally:
        db.close()

    assert len(gesendete_mails) == 1
    from services import widget_report
    assert widget_report.report_url("r-klick") in gesendete_mails[0]["html"]


def test_zweiter_klick_schickt_die_mail_nicht_noch_einmal(client, fremde_analyse,
                                                          aufraeumen,
                                                          gesendete_mails):
    """Postfach-Scanner öffnen Links automatisch — das darf nichts auslösen."""
    _anfrage_anlegen("doppelklick@firma-xy.de", fremde_analyse, aufraeumen,
                     verify_token="v-doppelt", report_token="r-doppelt",
                     poll_token="p-doppelt")

    client.get("/api/widget/verify/v-doppelt")
    r = client.get("/api/widget/verify/v-doppelt")

    assert r.status_code == 200
    assert "bereits bestätigt" in r.text.lower()
    assert len(gesendete_mails) == 1


def test_unbekannter_bestaetigungslink_gibt_404(client):
    r = client.get("/api/widget/verify/gibtesnicht")
    assert r.status_code == 404
    assert "nicht mehr gültig" in r.text

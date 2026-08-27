"""
Der öffentliche Widget-Endpunkt.

Er ist ohne Login von fremden Landingpages erreichbar, stößt einen
kostenpflichtigen Audit-Lauf an und verschickt E-Mails an eingegebene
Adressen. Diese Tests decken die Abwehr ab — nicht den Audit-Lauf selbst,
damit sie ohne Netzzugriff bleiben.
"""
from datetime import datetime, timedelta

import re

import pytest

from database import SessionLocal, WidgetRequest
from tests.widget_hilfen import _anfrage_anlegen, _beleg



# ── Bericht und Bestätigung ───────────────────────────────────────────

def test_unbekannter_berichts_token_gibt_404(client):
    assert client.get("/api/widget/report/gibtesnicht").status_code == 404


def test_unbekannter_bestaetigungs_token_zeigt_hinweisseite(client):
    r = client.get("/api/widget/confirm/gibtesnicht")
    assert r.status_code == 404
    assert "nicht mehr gültig" in r.text


def test_teaser_fuer_unbekannten_token_gibt_404(client):
    assert client.get("/api/widget/teaser/gibtesnicht").status_code == 404






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

    widget_datei = (Path(__file__).resolve().parents[2]
                    / "frontend" / "public" / "embed" / "audit-widget.html")
    if not widget_datei.exists():  # Backend wird ohne Frontend ausgeliefert
        pytest.skip("Frontend nicht vorhanden")

    text = widget_datei.read_text(encoding="utf-8")
    for farbe in (brand.DARK, brand.MID, brand.YELLOW):
        assert farbe in text, f"{farbe} fehlt im Widget"
    for erfunden in ERFUNDENE_FARBEN:
        assert erfunden.lower() not in text.lower(), f"{erfunden} ist wieder da"


# ── Ziel des Angebots-Knopfes ─────────────────────────────────────────

def test_angebots_knopf_folgt_der_einstellung():
    """Berichtsseite und Widget müssen auf dasselbe Ziel zeigen.

    Die Berichtsseite hatte den Checkout fest verdrahtet und ignorierte die
    Einstellung, an der das Widget längst hing.
    """
    from services import widget_report

    assert widget_report.termin_url("https://calendar.google.com/x") == \
        "https://calendar.google.com/x"


def test_leere_oder_unsinnige_einstellung_faellt_auf_den_standard(caplog):
    """Der Wert kommt aus einer Eingabemaske und landet in einem href."""
    from services import widget_report

    for unsinn in ("", "   ", "javascript:alert(1)", "kompagnon.eu"):
        assert widget_report.termin_url(unsinn) == widget_report.STANDARD_TERMIN_URL


def test_standardziel_ist_der_terminkalender_ohne_kontoindex():
    """„/u/0/" steht für das Google-Konto des Kopierenden.

    Bei Besuchern mit mehreren Konten kann der Link damit ins Leere laufen.
    """
    from services import widget_report

    assert "calendar.google.com" in widget_report.STANDARD_TERMIN_URL
    assert "/u/0/" not in widget_report.STANDARD_TERMIN_URL


def test_die_berichts_mail_geht_im_selben_aufruf_raus(client, fremde_analyse,
                                                      aufraeumen, gesendete_mails):
    """Nicht als Hintergrundauftrag — der überlebt keinen Neustart.

    Ein Hintergrundauftrag läuft erst nach der Antwort. Startet der Container
    in dem Moment neu (auf Render bei jedem Deploy), ist er ersatzlos weg:
    Der Besucher hat bestätigt und bekommt nie einen Bericht. Genau das war
    bei einer Testanfrage zu sehen — bestätigt, aber keine zweite Mail.
    """
    _anfrage_anlegen("sofort@firma-xy.de", fremde_analyse, aufraeumen,
                     verify_token="v-sofort", report_token="r-sofort",
                     poll_token="p-sofort")

    # raise_server_exceptions=False wäre nötig, wenn der Versand im
    # Hintergrund liefe — hier zählt, dass die Mail schon vor der Antwort da ist.
    with client:
        r = client.post("/api/widget/verify/v-sofort",
                        data={"nachweis": _beleg("v-sofort")})

    assert r.status_code == 200
    assert len(gesendete_mails) == 1, "Die Mail kam nicht im selben Aufruf"


def test_der_bericht_folgt_nicht_der_widget_einstellung(monkeypatch):
    """Zwei Knöpfe, zwei Ziele.

    Als beide an `widget_checkout_url` hingen, überschrieb der dort
    eingetragene Wert — die Startseite — den Terminkalender, und der Bericht
    zeigte wieder auf ein Formular statt auf einen Termin.
    """
    from services import app_settings

    assert app_settings.ENV_FALLBACK["widget_booking_url"] == "WIDGET_BOOKING_URL"
    assert app_settings.ENV_FALLBACK["widget_checkout_url"] != \
        app_settings.ENV_FALLBACK["widget_booking_url"]


def test_abschicken_ohne_bedienung_bestaetigt_nichts(client, fremde_analyse,
                                                     aufraeumen, gesendete_mails):
    """Der Kern des Blockers.

    POST allein reichte nicht: In vier Live-Durchläufen bestätigte sich jede
    Anfrage von selbst, Minuten nach dem Versand und ohne Zutun eines
    Menschen — irgendetwas schickte das Formular tatsächlich ab. Das Feld
    ``nachweis`` ist im ausgelieferten HTML leer und wird erst bei einer
    echten Geste gefüllt. Wer blind abschickt, erreicht nichts.
    """
    anfrage_id = _anfrage_anlegen("blind@firma-xy.de", fremde_analyse, aufraeumen,
                                  verify_token="v-blind", report_token="r-blind",
                                  poll_token="p-blind")

    # Act — genau das, was der unbekannte Dienst tut: abschicken, Feld leer
    r = client.post("/api/widget/verify/v-blind", data={"nachweis": ""})

    # Assert
    assert r.status_code == 200
    assert gesendete_mails == [], "Es ging trotzdem eine Mail raus"

    db = SessionLocal()
    try:
        row = db.query(WidgetRequest).filter(WidgetRequest.id == anfrage_id).first()
        assert row.verified_at is None, "Ohne Bedienung wurde bestätigt"
    finally:
        db.close()


def test_ein_geratener_beleg_hilft_nicht(client, fremde_analyse, aufraeumen,
                                          gesendete_mails):
    _anfrage_anlegen("raten@firma-xy.de", fremde_analyse, aufraeumen,
                     verify_token="v-raten", report_token="r-raten",
                     poll_token="p-raten")

    client.post("/api/widget/verify/v-raten", data={"nachweis": "a" * 32})

    assert gesendete_mails == []


def test_wer_bestaetigt_hat_wird_festgehalten(client, fremde_analyse, aufraeumen,
                                               gesendete_mails):
    """Ohne diese Angaben liess sich nicht sagen, welcher Dienst da drückt."""
    anfrage_id = _anfrage_anlegen("nachweis-ua@firma-xy.de", fremde_analyse,
                                  aufraeumen, verify_token="v-ua",
                                  report_token="r-ua", poll_token="p-ua")

    client.post("/api/widget/verify/v-ua", data={"nachweis": _beleg("v-ua")},
                headers={"User-Agent": "Mozilla/5.0 (Testfall)"})

    db = SessionLocal()
    try:
        row = db.query(WidgetRequest).filter(WidgetRequest.id == anfrage_id).first()
        assert row.verified_at is not None
        assert "Testfall" in (row.verified_user_agent or "")
    finally:
        db.close()


def test_die_seite_liefert_den_beleg_nicht_im_feld_aus(client, fremde_analyse,
                                                        aufraeumen):
    """Stünde er im Feld, schickte ihn jeder blinde Absender gleich mit."""
    _anfrage_anlegen("feld@firma-xy.de", fremde_analyse, aufraeumen,
                     verify_token="v-feld", report_token="r-feld",
                     poll_token="p-feld")

    r = client.get("/api/widget/verify/v-feld")

    assert 'name="nachweis"' in r.text
    assert 'value=""' in r.text, "Das Feld wird vorbefüllt ausgeliefert"
    # Nicht gegen einen berechneten Wert prüfen: Der Beleg trägt seit dem
    # 17.08.2026 den Zeitpunkt seiner Ausgabe und ist damit bei jedem Abruf
    # ein anderer. Geprüft wird, was der Test meint — er steht im Attribut
    # und nicht im Feld.
    beleg = re.search(r'data-nachweis="(\d+\.[0-9a-f]+)"', r.text)
    assert beleg, "Der Beleg fehlt im data-Attribut"
    assert beleg.group(1) not in r.text.split('id="kpg-nachweis"')[1][:80], \
        "Der Beleg steht im Feld statt nur im Attribut"

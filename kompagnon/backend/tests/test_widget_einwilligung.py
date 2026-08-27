"""Kein Werbebrief ohne Einwilligung — die Mailstrecke des Widgets (L-25).

**Warum eigene Datei, 23.08.2026.** Der zweite Teil von `test_widget.py`, und
der mit dem hoechsten Einsatz: Hier haengt die DSGVO-Frage. Eine Adresse, die
ein Fremder in ein Formular auf einer fremden Seite tippt, ist **keine**
Einwilligung — der Bericht geht erst nach Bestaetigung hinaus, und zwischen
den beiden Mails darf keine Werbung liegen.

Diese Tests halten fest, was am 12.08.2026 aus dem Pentest kam und danach
gebaut wurde: Doppelte Einwilligung, zwei getrennte Mails, und die
Uebertragung nach Brevo erst danach.
"""
from datetime import datetime, timedelta

import re

import pytest

from database import SessionLocal, WidgetRequest
from routers import widget
from tests.widget_hilfen import _anfrage_anlegen, _beleg


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
    # Das Angebotsziel kommt aus der Einstellung; ohne gesetzten Wert ist es
    # der Terminkalender.
    from services import app_settings, widget_report

    db = SessionLocal()
    try:
        eingestellt = app_settings.get(db, "widget_booking_url")
    finally:
        db.close()
    assert widget_report.termin_url(eingestellt) in r.text
    assert "Jetzt Termin vereinbaren" in r.text


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
    r = client.post("/api/widget/verify/v-klick",
                    data={"nachweis": _beleg("v-klick")})

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

    beleg = {"nachweis": _beleg("v-doppelt")}
    client.post("/api/widget/verify/v-doppelt", data=beleg)
    r = client.post("/api/widget/verify/v-doppelt", data=beleg)

    assert r.status_code == 200
    assert "bereits bestätigt" in r.text.lower()
    assert len(gesendete_mails) == 1


def test_unbekannter_bestaetigungslink_gibt_404(client):
    r = client.post("/api/widget/verify/gibtesnicht",
                    data={"nachweis": _beleg("gibtesnicht")})
    assert r.status_code == 404
    assert "nicht mehr gültig" in r.text


def test_das_oeffnen_des_links_bestaetigt_noch_nichts(client, fremde_analyse,
                                                       aufraeumen, gesendete_mails):
    """Gmail ruft Links in E-Mails von sich aus ab.

    Als der Aufruf die Bestätigung noch selbst vollzog, kam die Berichts-Mail
    fünfzehn Sekunden nach der Bestätigungs-Mail — ohne dass ein Mensch
    geklickt hatte. Damit war das Double-Opt-in wirkungslos. Ein GET darf
    nichts verändern; erst der Knopf schickt ein POST.
    """
    # Arrange
    anfrage_id = _anfrage_anlegen("scanner@firma-xy.de", fremde_analyse,
                                  aufraeumen, verify_token="v-scanner",
                                  report_token="r-scanner", poll_token="p-scanner")

    # Act — genau das, was ein Postfach-Scanner tut
    r = client.get("/api/widget/verify/v-scanner")

    # Assert
    assert r.status_code == 200
    assert "<form" in r.text and 'method="post"' in r.text
    assert gesendete_mails == []

    db = SessionLocal()
    try:
        row = db.query(WidgetRequest).filter(WidgetRequest.id == anfrage_id).first()
        assert row.verified_at is None, "Der blosse Abruf hat bestätigt"
    finally:
        db.close()


def test_auch_der_marketing_opt_in_braucht_einen_knopf(client, fremde_analyse,
                                                       aufraeumen):
    """Eine vom Scanner erteilte Einwilligung wäre als Nachweis wertlos."""
    anfrage_id = _anfrage_anlegen("optin@firma-xy.de", fremde_analyse, aufraeumen,
                                  verify_token="v-optin", report_token="r-optin",
                                  poll_token="p-optin", confirm_token="c-optin",
                                  consent_marketing=True)

    r = client.get("/api/widget/confirm/c-optin")

    assert r.status_code == 200
    assert 'method="post"' in r.text

    db = SessionLocal()
    try:
        row = db.query(WidgetRequest).filter(WidgetRequest.id == anfrage_id).first()
        assert row.confirmed_at is None
    finally:
        db.close()

    # Erst der Knopf zaehlt.
    assert client.post("/api/widget/confirm/c-optin",
                       data={"nachweis": _beleg("c-optin")}).status_code == 200
    db = SessionLocal()
    try:
        row = db.query(WidgetRequest).filter(WidgetRequest.id == anfrage_id).first()
        assert row.confirmed_at is not None
    finally:
        db.close()


# ── Übertragung nach Brevo ────────────────────────────────────────────

def test_ohne_eingerichtete_liste_passiert_nichts(monkeypatch):
    """Fehlt die Konfiguration, darf der Klick trotzdem durchlaufen."""
    from services import widget_crm

    monkeypatch.delenv("BREVO_LIST_VERIFIED_ID", raising=False)
    assert widget_crm.liste_bestaetigt() is None
    assert widget_crm.uebertrage("a@b.de", None) is False


def test_brevo_ausfall_kippt_den_klick_nicht(monkeypatch):
    """Der Besucher steckt mitten in der Bestätigung — er darf nichts merken."""
    from services import widget_crm

    class _Kaputt:
        def __enter__(self): raise RuntimeError("Brevo down")
        def __exit__(self, *a): return False

    import services.brevo_service
    monkeypatch.setattr(services.brevo_service, "BrevoService", lambda *a, **k: _Kaputt())

    assert widget_crm.uebertrage("a@b.de", 42) is False


def test_die_beiden_listen_haengen_an_getrennten_variablen(monkeypatch):
    """Adresse bestätigt und Marketing-Opt-in dürfen nie dieselbe Liste sein.

    Sonst landet in der Liste, auf der die Automatisierung hängt, auch wer
    nur seine Adresse bestätigt hat — und wird angeschrieben, ohne
    eingewilligt zu haben.
    """
    from services import widget_crm

    monkeypatch.setenv("BREVO_LIST_VERIFIED_ID", "11")
    monkeypatch.setenv("BREVO_LIST_OPTIN_ID", "22")

    assert widget_crm.liste_bestaetigt() == 11
    assert widget_crm.liste_optin() == 22


def test_unsinnige_listen_id_wird_nicht_benutzt(monkeypatch):
    from services import widget_crm

    monkeypatch.setenv("BREVO_LIST_OPTIN_ID", "keine-zahl")
    assert widget_crm.liste_optin() is None

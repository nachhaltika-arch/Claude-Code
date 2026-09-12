# -*- coding: utf-8 -*-
"""Die Fehlschlagsmeldung hängt wirklich am Fehlschlag (L-184).

**Warum diese Datei neben den beiden anderen steht.** `test_analyse_fehler`
prüft den Klassierer, `test_widget_fehlschlag_mail` den Text. Beide wären
grün, wenn die Mail nie verschickt würde — genau die Sorte „gebaut, nicht
angeschlossen", die hier schon mehrfach vorkam. Hier wird deshalb der
**Übergang** geprüft: Ein Audit fällt um, und dann muss Post rausgehen.

**Zwei Wege führten dorthin, nur einer war angeschlossen.** Die Gesamtgrenze
des Audits setzte den Status von Hand statt über `_mark_failed` — wer über
die Zeitgrenze lief, bekam nie eine Mail, wer anders scheiterte schon. Und
der allgemeine Auffangzweig protokollierte bloss: Das Audit blieb für immer
auf `running` stehen, ohne Fehler, ohne Mail, ohne Spur in der Anfrageliste.
"""
import pytest

from database import SessionLocal
from modelle_audit import AuditResult
from modelle_widget import WidgetRequest


@pytest.fixture
def db(app):
    sitzung = SessionLocal()
    try:
        sitzung.query(WidgetRequest).delete()
        sitzung.commit()
        yield sitzung
    finally:
        sitzung.rollback()
        sitzung.close()


def _laufendes_audit(db, mit_anfrage=True):
    audit = AuditResult(website_url="https://beispiel.de",
                        company_name="Beispiel GmbH", status="running")
    db.add(audit)
    db.commit()
    db.refresh(audit)
    if mit_anfrage:
        db.add(WidgetRequest(email="besucher@beispiel.de",
                             website_url="https://beispiel.de",
                             audit_id=audit.id))
        db.commit()
    return audit.id


class TestAusDemFehlschlagWirdPost:
    def test_ein_gescheitertes_audit_meldet_sich_beim_besucher(self, db, gesendete_mails):
        from routers.audit import _mark_failed

        audit_id = _laufendes_audit(db)
        _mark_failed(audit_id, "ConnectTimeout: ")

        assert len(gesendete_mails) == 1
        assert gesendete_mails[0]["an"] == "besucher@beispiel.de"
        assert "nicht durchgelaufen" in gesendete_mails[0]["betreff"]

    def test_der_grund_steht_im_text(self, db, gesendete_mails):
        """`ConnectTimeout` heisst: seine Seite läuft, wir kommen nicht hin."""
        from routers.audit import _mark_failed

        _mark_failed(_laufendes_audit(db), "ConnectTimeout: ")

        html = gesendete_mails[0]["html"]
        assert "Bitte die Adresse prüfen" not in html
        assert "melden uns" in html

    def test_ein_tippfehler_bekommt_den_anderen_text(self, db, gesendete_mails):
        from routers.audit import _mark_failed

        _mark_failed(_laufendes_audit(db),
                     "ConnectError: [Errno -2] Name or service not known")

        assert "Adresse" in gesendete_mails[0]["html"]
        assert "melden uns" not in gesendete_mails[0]["html"]

    def test_der_status_steht_danach_auf_failed(self, db, gesendete_mails):
        from routers.audit import _mark_failed

        audit_id = _laufendes_audit(db)
        _mark_failed(audit_id, "ConnectTimeout: ")

        db.expire_all()
        audit = db.query(AuditResult).filter(AuditResult.id == audit_id).first()
        assert audit.status == "failed"


class TestWoKeinePostHingehoert:
    def test_ein_audit_aus_dem_werkzeug_verschickt_nichts(self, db, gesendete_mails):
        """Ohne `WidgetRequest` wartet niemand auf eine Mail."""
        from routers.audit import _mark_failed

        _mark_failed(_laufendes_audit(db, mit_anfrage=False), "ConnectTimeout: ")

        assert gesendete_mails == []

    def test_zweimal_umfallen_schickt_nicht_zweimal(self, db, gesendete_mails):
        """Der Zustandswechsel ist die Sperre — er passiert nur einmal."""
        from routers.audit import _mark_failed

        audit_id = _laufendes_audit(db)
        _mark_failed(audit_id, "ConnectTimeout: ")
        _mark_failed(audit_id, "ConnectTimeout: ")

        assert len(gesendete_mails) == 1


class TestDerTeaserGibtDenGrundHerausAberNichtDieMeldung:
    def test_ein_schluessel_statt_der_ausnahme(self, db, client):
        audit = AuditResult(website_url="https://beispiel.de",
                            company_name="Beispiel GmbH", status="failed",
                            error_message="ConnectTimeout: geheim-interner-hinweis")
        db.add(audit)
        db.commit()
        db.refresh(audit)
        db.add(WidgetRequest(email="k@beispiel.de", website_url="https://beispiel.de",
                             audit_id=audit.id, poll_token="grund-poll-token"))
        db.commit()

        antwort = client.get("/api/widget/teaser/grund-poll-token").json()

        assert antwort["grund"] == "nicht_erreichbar"
        assert "ConnectTimeout" not in str(antwort)
        assert "geheim-interner-hinweis" not in str(antwort)

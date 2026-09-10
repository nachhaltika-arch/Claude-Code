# -*- coding: utf-8 -*-
"""Die Anfrageliste sagt, ob die Analyse ueberhaupt durchlief (L-184).

**Der Befund vom 10.09.2026.** Schlaegt die Erhebung fehl, geht keine Mail
raus — `_notify_widget_requester` steigt aus, solange der Status nicht
`completed` ist. In der Anfrageliste sah der Fall danach **genauso aus wie
eine im Spam gelandete Mail**: „Bestaetigung angefragt: nein", sonst nichts.
Zwei voellig verschiedene Ursachen, ein Bild — und beide Male keine
Handlungsmoeglichkeit, weil die Ursache fehlte.

**Die Diagnose gab es die ganze Zeit.** `audit_results.error_message` traegt
sie; gemessen wurde am selben Tag `ConnectTimeout` fuer einen Host, der aus
dem Rechenzentrum nicht erreichbar ist (L-183). Das Widget bekommt sie ueber
`/api/widget/teaser` sogar zugestellt und wirft sie weg — dort mit Absicht,
denn dem Besucher hilft ein technischer Name nicht. **Im Werkzeug hilft er.**

**Was diese Datei nicht behauptet:** Der Lead ist damit nicht gerettet, nur
sichtbar. Ein automatischer zweiter Versuch ist **nicht** gebaut — er kostet
einen Browserlauf je Wiederholung und ist bei einer dauerhaften Sperre
sinnlos. Sichtbarkeit zuerst, Automatik erst, wenn die Zahlen sie tragen.
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


def _mit_analyse(db, status, fehler=None):
    audit = AuditResult(website_url="https://example.de", company_name="Beispiel GmbH",
                        status=status,
                        error_message=fehler)
    db.add(audit)
    db.commit()
    db.refresh(audit)
    zeile = WidgetRequest(email="k@example.de", website_url="https://example.de",
                          audit_id=audit.id)
    db.add(zeile)
    db.commit()
    return zeile


def _zeilen(client, auth_headers):
    r = client.get("/api/acquisition/widget/requests", headers=auth_headers)
    assert r.status_code == 200, r.text
    return r.json()["requests"]


class TestAnalysestand:
    def test_gescheiterte_analyse_ist_als_solche_erkennbar(self, db, client, auth_headers):
        _mit_analyse(db, "failed", "ConnectTimeout: ")
        zeile = _zeilen(client, auth_headers)[0]
        assert zeile["analyse_status"] == "failed"

    def test_der_grund_steht_dabei(self, db, client, auth_headers):
        """Der eigentliche Fund: ohne ihn ist die Zeile nicht handhabbar."""
        _mit_analyse(db, "failed", "ConnectTimeout: ")
        assert "ConnectTimeout" in _zeilen(client, auth_headers)[0]["analyse_fehler"]

    def test_eine_gelungene_analyse_nennt_keinen_fehler(self, db, client, auth_headers):
        # Gegenprobe: Sonst waere „steht ein Fehler da" auch dann wahr, wenn
        # das Feld immer gefuellt ist.
        _mit_analyse(db, "completed")
        zeile = _zeilen(client, auth_headers)[0]
        assert zeile["analyse_status"] == "completed"
        assert not zeile["analyse_fehler"]

    def test_laufende_analyse_ist_unterscheidbar(self, db, client, auth_headers):
        _mit_analyse(db, "running")
        assert _zeilen(client, auth_headers)[0]["analyse_status"] == "running"

    def test_ohne_analyse_bleibt_der_stand_leer(self, db, client, auth_headers):
        db.add(WidgetRequest(email="k@example.de", website_url="https://example.de"))
        db.commit()
        zeile = _zeilen(client, auth_headers)[0]
        assert zeile["analyse_status"] is None

    def test_eine_fehlende_analysezeile_kippt_die_liste_nicht(self, db, client, auth_headers):
        """`audit_id` zeigt ins Leere — die Liste muss trotzdem antworten."""
        db.add(WidgetRequest(email="k@example.de", website_url="https://example.de",
                             audit_id=999999))
        db.commit()
        zeile = _zeilen(client, auth_headers)[0]
        assert zeile["analyse_status"] is None

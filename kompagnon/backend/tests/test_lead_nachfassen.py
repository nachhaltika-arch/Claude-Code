# -*- coding: utf-8 -*-
"""Wer den Bericht nicht abholt, bekommt genau eine Erinnerung (L-185).

**Der Befund vom 10.09.2026.** Wer im Trichter steckenbleibt, hoert nie
wieder etwas: Im Scheduler gab es dafuer keinen Auftrag — die
Erinnerungsstrecken gelten alle fuer Projekte **nach dem Kauf**. Ab
Kampagnenstart ist jeder dieser Leads bezahlt und verloren.

**Gebaut wird nur die zweite Haelfte, und das ist eine Entscheidung.**
Naheliegend waere gewesen, auch an die **Bestaetigung** zu erinnern — dort
faellt der groesste Teil weg. Genau das verbietet aber die Mail, die wir
vorher geschickt haben. Ihr letzter Absatz lautet:

    Haben Sie das nicht angefordert? Dann ignorieren Sie diese E-Mail
    einfach. Ohne Ihre Bestaetigung schicken wir nichts weiter und
    **melden uns nicht von selbst**.

Eine Erinnerung an eine unbestaetigte Adresse waere genau das, was dieser
Satz ausschliesst. Ob der Satz geaendert wird, ist eine Entscheidung ueber
das eigene Wort und gehoert David — nicht diesem Code. Solange er steht,
wird er gehalten.

**Die zweite Strecke ist unproblematisch:** Der Empfaenger hat seine Adresse
bestaetigt und den Bericht angefordert. Dass er bereitliegt, ist Auskunft
ueber eine angeforderte Leistung, keine Werbung.

**Vier Regeln, und jede hat einen Grund, der weh tut, wenn sie fehlt.**

1. **Genau einmal.** Der Zeitpunkt steht an der Anfrage. Ohne ihn schickt
   jeder Scheduler-Lauf dieselbe Mail erneut.
2. **Nur frische Anfragen.** Beim ersten Lauf nach dem Deploy liegt der
   gesamte Bestand vor: Ohne Obergrenze ginge eine Erinnerung an jede alte
   Anfrage. Das ist kein Nachfassen mehr, sondern eine Aussendung — und der
   erste Lauf waere zugleich der teuerste Fehler.
3. **Die Frist zaehlt ab dem Versand, nicht ab dem Eingang.** Wer den
   Bericht spaet bekam, hatte auch spaet Gelegenheit.
4. **Wer geoeffnet hat, wird nicht erinnert.** Klingt selbstverstaendlich
   und ist genau die Zeile, die man vergisst.
"""
from datetime import datetime, timedelta

import pytest

from database import SessionLocal
from modelle_widget import WidgetRequest
from services import lead_nachfassen as nf


JETZT = datetime(2026, 9, 10, 12, 0, 0)


def _anfrage(db, **abweichung):
    werte = {
        "email": "kunde@example.de",
        "website_url": "https://example.de",
        "audit_id": 1,
        "verify_sent_at": JETZT - timedelta(hours=30),
        "verified_at": None,
        "report_sent_at": None,
        "report_confirmed_at": None,
        "created_at": JETZT - timedelta(hours=30),
    }
    werte.update(abweichung)
    zeile = WidgetRequest(**werte)
    db.add(zeile)
    db.commit()
    db.refresh(zeile)
    return zeile


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


class TestBerichtLiegtBereit:
    def test_nach_der_frist_faellig(self, db):
        zeile = _anfrage(db, verified_at=JETZT - timedelta(days=4),
                         report_sent_at=JETZT - timedelta(days=4))
        assert [z.id for z in nf.faelliger_bericht(db, JETZT)] == [zeile.id]

    def test_wer_geoeffnet_hat_wird_nicht_erinnert(self, db):
        _anfrage(db, verified_at=JETZT - timedelta(days=4),
                 report_sent_at=JETZT - timedelta(days=4),
                 report_confirmed_at=JETZT - timedelta(days=3))
        assert nf.faelliger_bericht(db, JETZT) == []

    def test_vor_der_frist_nicht(self, db):
        _anfrage(db, verified_at=JETZT - timedelta(hours=6),
                 report_sent_at=JETZT - timedelta(hours=6))
        assert nf.faelliger_bericht(db, JETZT) == []

    def test_genau_einmal(self, db):
        _anfrage(db, verified_at=JETZT - timedelta(days=4),
                 report_sent_at=JETZT - timedelta(days=4),
                 erinnerung_bericht_at=JETZT - timedelta(days=1))
        assert nf.faelliger_bericht(db, JETZT) == []

    def test_alter_bestand_bleibt_unberuehrt(self, db):
        _anfrage(db, verified_at=JETZT - timedelta(days=40),
                 report_sent_at=JETZT - timedelta(days=40),
                 created_at=JETZT - timedelta(days=40))
        assert nf.faelliger_bericht(db, JETZT) == []

    def test_ohne_bestaetigung_kein_bericht_und_keine_erinnerung(self, db):
        """Wer nie bestaetigt hat, hat auch keinen Bericht bekommen — und
        bekommt von dieser Strecke nichts. Der Fall gehoert der Entscheidung
        im Kopftext, nicht diesem Auftrag."""
        _anfrage(db)
        assert nf.faelliger_bericht(db, JETZT) == []


class TestMails:
    def test_die_zweite_mail_fuehrt_zum_bericht(self):
        betreff, rumpf = nf.erinnerung_bericht_mail("example.de", "berichtstoken")
        assert betreff
        assert "berichtstoken" in rumpf


# ═══════════════════════════════════════════════════════════════════
# Der Auftrag — und ob er ueberhaupt laeuft
# ═══════════════════════════════════════════════════════════════════
#
# **Die Klasse, die dieses Projekt fuenfmal getroffen hat:** ein Bauteil, das
# fertig ist und von niemandem aufgerufen wird. `webhook_actions` liess sich
# im Editor setzen und wurde nirgends gelesen; `RolePermission` sperrte
# nichts; `meta_conversions.verfuegbar()` gab es, aber kein Endpunkt rief es.
# Ein Nachfass-Auftrag, den der Scheduler nicht kennt, waere derselbe Fehler
# — und wuerde als „gebaut" gemeldet.


def test_der_auftrag_ist_im_scheduler_registriert():
    from automations import scheduler as sch

    quelle = __import__("inspect").getsource(sch)
    assert "job_bericht_erinnerung" in quelle, (
        "Der Auftrag ist gebaut, aber der Scheduler kennt ihn nicht")
    assert 'id="bericht_erinnerung"' in quelle


def test_der_auftrag_verschickt_und_markiert(db, monkeypatch):
    """Am Ergebnis geprueft: Mail raus **und** Sperre gesetzt."""
    from automations import scheduler_kontakt as sk

    versandt = []
    monkeypatch.setattr(sk, "_do_send_email",
                        lambda to_email, subject, html_body: versandt.append(to_email) or True)

    zeile = _anfrage(db, verified_at=JETZT - timedelta(days=4),
                     report_sent_at=datetime.utcnow() - timedelta(days=4),
                     report_token="btok")
    sk.job_bericht_erinnerung()

    db.expire_all()
    frisch = db.query(WidgetRequest).filter(WidgetRequest.id == zeile.id).first()
    assert versandt == ["kunde@example.de"]
    assert frisch.erinnerung_bericht_at is not None


def test_ohne_versand_keine_sperre(db, monkeypatch):
    """Sonst bekaeme der Empfaenger nie eine Erinnerung, weil der erste,
    gescheiterte Versuch ihn stillschweigend abgehakt haette."""
    from automations import scheduler_kontakt as sk

    monkeypatch.setattr(sk, "_do_send_email",
                        lambda to_email, subject, html_body: False)

    zeile = _anfrage(db, verified_at=JETZT - timedelta(days=4),
                     report_sent_at=datetime.utcnow() - timedelta(days=4),
                     report_token="btok")
    sk.job_bericht_erinnerung()

    db.expire_all()
    frisch = db.query(WidgetRequest).filter(WidgetRequest.id == zeile.id).first()
    assert frisch.erinnerung_bericht_at is None

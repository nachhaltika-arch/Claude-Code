# -*- coding: utf-8 -*-
"""Die Schalter wirken — sonst wären sie wieder nur Zierde.

**Warum diese Datei getrennt von `test_meldungsvorlieben.py` steht.** Dort
wird geprüft, dass sich ein Wert speichern und wieder lesen lässt. Genau so
weit war der Bestand heute Vormittag schon: sechs Ankreuzfelder, die sich
setzen ließen, ein Knopf, der Erfolg meldete — und **keine Stelle, die den
Wert je gelesen hätte**. Ein gespeicherter Schalter ist keine Wirkung.

Hier wird deshalb an jeder der drei Stellen gefragt, was tatsächlich
passiert: Geht die Mail raus, wenn der Schalter an ist, und bleibt sie aus,
wenn er aus ist? Beide Richtungen, denn ein Test, der nur „aus" prüft, wäre
auch grün, wenn nie eine Mail ginge.
"""
import pytest

pytestmark = pytest.mark.usefixtures("app")


@pytest.fixture(autouse=True)
def _leeren(app):
    from database import Meldungsvorliebe, SessionLocal

    db = SessionLocal()
    try:
        db.query(Meldungsvorliebe).delete()
        db.commit()
    finally:
        db.close()


@pytest.fixture
def versand(monkeypatch):
    """Fängt jeden Mailversand ab — mit der echten Unterschrift.

    `def merken(**k)` hätte am 26.08.2026 die verlorene Willkommensmail
    **nicht** gefunden: Ein falsches Schlüsselwort wäre stillschweigend
    angenommen worden. Deshalb genau die Parameter, die `send_email` führt.
    """
    gesendet = []

    def _merken(to_email, subject, html_body, **rest):
        gesendet.append({"to": to_email, "subject": subject})
        return True

    import services.email as mail

    monkeypatch.setattr(mail, "send_email", _merken)
    return gesendet


@pytest.fixture
def stellen(app):
    def _setzen(schluessel, aktiv):
        from database import SessionLocal
        from services import meldungsvorlieben

        db = SessionLocal()
        try:
            meldungsvorlieben.setzen(db, schluessel, aktiv)
        finally:
            db.close()
    return _setzen


class TestDieChatnachricht:
    """`routers/messages.py` → `SMTP_USER`. Existierte vorher, Vorgabe „an"."""

    def _senden(self, client, kunde_headers, kunde_user):
        return client.post(f"/api/messages/{kunde_user.lead_id}/kunde",
                           headers=kunde_headers,
                           json={"content": "Kurze Rueckfrage zur Seite"})

    def test_mit_schalter_an_geht_sie_raus(self, client, kunde_headers,
                                            kunde_user, versand, monkeypatch):
        monkeypatch.setattr("routers.messages.SMTP_USER", "chef@kompagnon.test")

        antwort = self._senden(client, kunde_headers, kunde_user)

        assert antwort.status_code == 200, antwort.text
        assert len(versand) == 1, "keine Mail trotz eingeschaltetem Schalter"

    def test_mit_schalter_aus_bleibt_sie_aus(self, client, kunde_headers,
                                              kunde_user, versand, stellen,
                                              monkeypatch):
        monkeypatch.setattr("routers.messages.SMTP_USER", "chef@kompagnon.test")
        stellen("chat_mail", False)

        antwort = self._senden(client, kunde_headers, kunde_user)

        assert antwort.status_code == 200, antwort.text
        assert versand == []

    def test_und_die_glocke_meldet_sie_trotzdem(self, client, kunde_headers,
                                                 kunde_user, versand, stellen,
                                                 monkeypatch):
        """**Der wichtigste Fall.** Der Schalter regelt den *zweiten* Weg zur
        selben Sache. Nähme er auch die Meldung im Werkzeug mit, hätte man
        eine Kundennachricht stummgeschaltet — danach hat niemand gefragt.
        """
        monkeypatch.setattr("routers.messages.SMTP_USER", "chef@kompagnon.test")
        stellen("chat_mail", False)

        self._senden(client, kunde_headers, kunde_user)

        from database import Benachrichtigung, SessionLocal
        db = SessionLocal()
        try:
            offen = db.query(Benachrichtigung).filter(
                Benachrichtigung.art == "chat").count()
        finally:
            db.close()

        assert offen >= 1, "die Glocke schweigt mit"


class TestDasTicket:
    """Neu. Vorgabe **aus** — wer nichts umstellt, merkt nichts."""

    def _anlegen(self, client):
        return client.post("/api/tickets", json={
            "user_email": "kunde@betrieb.test", "user_name": "Kundin",
            "type": "feedback", "priority": "medium",
            "title": "Knopf reagiert nicht",
            "description": "Beim Speichern passiert nichts.",
        })

    def test_ohne_umstellung_kommt_keine_mail(self, client, versand,
                                              monkeypatch):
        monkeypatch.setenv("SMTP_USER", "chef@kompagnon.test")

        antwort = self._anlegen(client)

        assert antwort.status_code in (200, 201), antwort.text
        assert versand == [], "ein neuer Schalter hat das Verhalten geaendert"

    def test_eingeschaltet_kommt_sie(self, client, versand, stellen,
                                      monkeypatch):
        """Gegenprobe: Ohne sie wäre der Test oben auch grün, wenn der
        Versand gar nicht gebaut wäre."""
        monkeypatch.setenv("SMTP_USER", "chef@kompagnon.test")
        stellen("ticket_mail", True)

        antwort = self._anlegen(client)

        assert antwort.status_code in (200, 201), antwort.text
        assert len(versand) == 1
        assert "Knopf reagiert nicht" in versand[0]["subject"]

    def test_ohne_empfaenger_passiert_nichts(self, client, versand, stellen,
                                              monkeypatch):
        monkeypatch.delenv("SMTP_USER", raising=False)
        stellen("ticket_mail", True)

        assert self._anlegen(client).status_code in (200, 201)
        assert versand == []

    def test_ein_fehler_im_versand_reisst_das_ticket_nicht_mit(
            self, client, stellen, monkeypatch):
        """Die Sache des Kunden ist die Hauptsache — dieselbe Reihenfolge wie
        bei `melden_leise`."""
        monkeypatch.setenv("SMTP_USER", "chef@kompagnon.test")
        stellen("ticket_mail", True)

        def _kracht(**k):
            raise RuntimeError("Brevo antwortet nicht")

        monkeypatch.setattr("services.email.send_email", _kracht)

        assert self._anlegen(client).status_code in (200, 201)


class TestBeiStoerungBleibtEsBeimBisherigen:
    def test_eine_kaputte_abfrage_schaltet_nichts_ab(self, monkeypatch):
        """**Die Richtung ist Absicht.** Wer diese Frage stellt, steht kurz
        vor einem Versand, der bisher stattfand. Ein Schalter, der bei
        Störung abschaltet, ist ein Ausfall mit Begründung — und der fällt
        niemandem auf.
        """
        from services import meldungsvorlieben

        def _kracht(db, schluessel):
            raise RuntimeError("Tabelle fehlt")

        monkeypatch.setattr(meldungsvorlieben, "soll_melden", _kracht)

        assert meldungsvorlieben.soll_melden_leise(None, "chat_mail") is True
        assert meldungsvorlieben.soll_melden_leise(None, "ticket_mail") is False

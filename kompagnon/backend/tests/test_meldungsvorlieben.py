# -*- coding: utf-8 -*-
"""Welche Meldung zusätzlich per Mail kommt — und welche nicht.

**Der Anlass (26.08.2026, Entscheidung David: „Ja, Vorlieben je Ereignis
bauen").** Unter Einstellungen standen sechs Ankreuzfelder mit einem
„Speichern"-Knopf, der grün meldete und nichts sendete. Nichts im Backend las
die sechs Schlüssel; es gab nicht einmal eine Stelle, an die sie hätten gehen
können. Sie sind am selben Tag entfernt worden, weil ein Feld, das nichts
schaltet, schlimmer ist als keines — es beendet die Suche.

**Und deshalb wird hier nichts erfunden.** Nachgezählt, welche Mails
überhaupt in Davids eigenes Postfach gehen, gibt es genau **zwei**:

* eine Chatnachricht vom Kunden (`routers/messages.py` → `SMTP_USER`),
* den monatlichen GEO-Bericht (`services/geo_monitor.py` → `ADMIN_EMAIL`).

Alles andere — Zustellalarme, Nennungsberichte, Audit-Fertigmeldungen,
Sequenzmails — geht an **Kunden** und wird vom Versandschalter und von
`project.email_notifications_enabled` geregelt, nicht von hier.

**Dazu kommt ein drittes Ereignis, das es noch nicht gab:** ein neues Ticket
meldet bisher nur die Glocke. Der Schalter dafür steht **aus** — die Vorgabe
jedes Schalters ist genau das Verhalten von heute. Wer nichts umstellt, merkt
von dieser Änderung nichts; das ist die Bedingung, unter der man Schalter
nachrüsten darf.
"""
import pytest

pytestmark = pytest.mark.usefixtures("app")

from services import meldungsvorlieben as mv  # noqa: E402


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
def db(app):
    from database import SessionLocal

    sitzung = SessionLocal()
    try:
        yield sitzung
    finally:
        sitzung.close()


class TestDieVorgabeIstDasVerhaltenVonHeute:
    def test_ohne_eintrag_gilt_die_vorgabe(self, db):
        """Kein Eintrag heisst nicht „aus". Ein leerer Bestand darf den
        Versand nicht heimlich abschalten — das waere dieselbe stille
        Verhaltensaenderung, vor der die Sperren dieses Bestands warnen."""
        assert mv.soll_melden(db, "chat_mail") is True
        assert mv.soll_melden(db, "geo_bericht") is True

    def test_und_was_es_noch_nicht_gab_bleibt_aus(self, db):
        """Ein Ticket meldet bisher nur die Glocke. Wer nichts umstellt, soll
        von dieser Aenderung nichts merken."""
        assert mv.soll_melden(db, "ticket_mail") is False

    def test_jedes_ereignis_hat_eine_beschriftung(self):
        """Ein Schluessel ohne Text wird in der Oberflaeche zu `chat_mail` —
        und dann rät der Leser, was er gerade abschaltet."""
        for schluessel, text, _ in mv.EREIGNISSE:
            assert schluessel and text
            assert len(text) > 10


class TestUmschalten:
    def test_ein_ereignis_laesst_sich_abschalten(self, db):
        mv.setzen(db, "chat_mail", False)

        assert mv.soll_melden(db, "chat_mail") is False

    def test_und_wieder_an(self, db):
        mv.setzen(db, "chat_mail", False)
        mv.setzen(db, "chat_mail", True)

        assert mv.soll_melden(db, "chat_mail") is True

    def test_zweimal_setzen_legt_keine_zweite_zeile_an(self, db):
        from database import Meldungsvorliebe

        mv.setzen(db, "chat_mail", False)
        mv.setzen(db, "chat_mail", True)

        assert db.query(Meldungsvorliebe).filter(
            Meldungsvorliebe.schluessel == "chat_mail").count() == 1

    def test_ein_unbekannter_schluessel_wird_abgewiesen(self, db):
        """Sonst legt ein Tippfehler in der Oberflaeche eine Zeile an, die
        niemand liest — und der Schalter, den der Nutzer meinte, bleibt, wo
        er war. Genau die Klasse Fehler, aus der dieser Eintrag entstand."""
        with pytest.raises(ValueError):
            mv.setzen(db, "gibts_nicht", False)

    def test_und_ein_unbekannter_wird_auch_nicht_gefragt(self, db):
        with pytest.raises(ValueError):
            mv.soll_melden(db, "gibts_nicht")


class TestDerAbrufFuerDieOberflaeche:
    def test_alle_ereignisse_kommen_mit_stand(self, db):
        stand = mv.alle(db)

        assert set(stand) == {s for s, _, _ in mv.EREIGNISSE}
        assert stand["chat_mail"]["aktiv"] is True
        assert stand["ticket_mail"]["aktiv"] is False

    def test_ein_umgeschaltetes_ereignis_steht_richtig_drin(self, db):
        mv.setzen(db, "geo_bericht", False)

        assert mv.alle(db)["geo_bericht"]["aktiv"] is False


class TestUeberDenEndpunkt:
    def test_der_innendienst_liest_den_stand(self, client, auth_headers):
        antwort = client.get("/api/benachrichtigungen/vorlieben",
                             headers=auth_headers)

        assert antwort.status_code == 200, antwort.text
        assert "chat_mail" in antwort.json()

    def test_und_stellt_um(self, client, auth_headers):
        client.put("/api/benachrichtigungen/vorlieben", headers=auth_headers,
                   json={"chat_mail": False})

        stand = client.get("/api/benachrichtigungen/vorlieben",
                           headers=auth_headers).json()
        assert stand["chat_mail"]["aktiv"] is False

    def test_ein_kunde_stellt_nichts_um(self, client, kunde_headers):
        """Der Router traegt `require_innendienst` — es sind unsere
        Meldungen, nicht seine."""
        assert client.get("/api/benachrichtigungen/vorlieben",
                          headers=kunde_headers).status_code == 403
        assert client.put("/api/benachrichtigungen/vorlieben",
                          headers=kunde_headers,
                          json={"chat_mail": False}).status_code == 403

    def test_ein_unbekannter_schluessel_ist_ein_fehler_kein_stilles_nichts(
            self, client, auth_headers):
        """Eine Oberflaeche, die einen falschen Namen schickt, soll es
        erfahren. Stillschweigend zu verwerfen hiesse: Der Knopf meldet
        Erfolg und nichts geschieht — genau der Zustand, den dieser Eintrag
        beseitigt hat."""
        antwort = client.put("/api/benachrichtigungen/vorlieben",
                             headers=auth_headers, json={"gibts_nicht": True})

        assert antwort.status_code == 400

# -*- coding: utf-8 -*-
"""Der Kunde pflegt seine Stammdaten selbst.

**Der Auftrag (26.08.2026, David).** Im Kundenportal sollen Stammdaten
bearbeitbar sein. Bisher konnte das nur der Innendienst
(`PATCH /api/leads/{id}` hinter `edit_leads`), und der Menüpunkt „Meine
Kartei" zeigte auf den Innendienst-Bildschirm — eine Route mit
`roles={['admin','auditor']}`, von der `PrivateRoute` den Kunden auf sein
Dashboard zurückwirft. Der Punkt führte also ins Nichts.

**Die entscheidende Frage ist nicht, was er ändern darf, sondern was nicht.**
Ein Betrieb trägt zweierlei: die Angaben **über** den Betrieb (Anschrift,
Ansprechpartner, Rechtsform, Registernummer) und die Angaben, die **wir**
über ihn führen — Status, Herkunft, interne Notizen, Punktzahl, Zugangs-
Token. Das Erste gehört ihm, das Zweite ist unsere Arbeitsspur.

Wer die Trennung nicht zieht, baut zwei Fehler auf einmal ein: Der Kunde
könnte seinen Vertriebsstatus auf „gewonnen" setzen, und er könnte lesen,
was der Innendienst über ihn notiert hat.

**Deshalb eine Erlaubnisliste, keine Verbotsliste.** Eine Verbotsliste
vergisst das Feld, das morgen dazukommt; eine Erlaubnisliste lässt es
draußen, bis jemand es ausdrücklich aufnimmt.
"""
import pytest

pytestmark = pytest.mark.usefixtures("app")


def _aendern(client, headers, lead_id, **felder):
    return client.patch(f"/api/leads/{lead_id}/stammdaten", headers=headers,
                        json=felder)


def _lesen(lead_id):
    from database import Lead, SessionLocal

    db = SessionLocal()
    try:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        return {s.name: getattr(lead, s.name) for s in Lead.__table__.columns}
    finally:
        db.close()


class TestWasErAendernDarf:
    def test_er_aendert_die_anschrift_seines_betriebs(
            self, client, kunde_headers, kunde_user):
        # Act
        antwort = _aendern(client, kunde_headers, kunde_user.lead_id,
                           street="Hauptstraße", house_number="12",
                           postal_code="56154", city="Boppard")

        # Assert
        assert antwort.status_code == 200, antwort.text
        daten = _lesen(kunde_user.lead_id)
        assert (daten["street"], daten["postal_code"]) == ("Hauptstraße", "56154")

    def test_er_aendert_ansprechpartner_und_telefon(
            self, client, kunde_headers, kunde_user):
        _aendern(client, kunde_headers, kunde_user.lead_id,
                 contact_name="Anna Beispiel", phone="+49 261 1234")

        daten = _lesen(kunde_user.lead_id)
        assert daten["contact_name"] == "Anna Beispiel"
        assert daten["phone"] == "+49 261 1234"

    def test_er_pflegt_die_pflichtangaben_fuers_impressum(
            self, client, kunde_headers, kunde_user):
        """Rechtsform, Registernummer, Registergericht, Geschäftsführer.

        Genau die Angaben, die im Impressum stehen müssen und die heute im
        Briefing per Hand abgefragt werden — der Betrieb kennt sie, wir nicht.
        """
        _aendern(client, kunde_headers, kunde_user.lead_id,
                 legal_form="GmbH", register_number="HRB 12345",
                 register_court="Amtsgericht Koblenz",
                 ceo_first_name="Anna", ceo_last_name="Beispiel",
                 vat_id="DE123456789")

        daten = _lesen(kunde_user.lead_id)
        assert daten["legal_form"] == "GmbH"
        assert daten["register_court"] == "Amtsgericht Koblenz"
        assert daten["vat_id"] == "DE123456789"

    def test_die_antwort_gibt_die_gespeicherten_werte_zurueck(
            self, client, kunde_headers, kunde_user):
        """Die Oberfläche soll anzeigen, was wirklich steht — nicht, was sie
        gesendet hat. Sonst sieht ein stillschweigend verworfenes Feld aus
        wie ein gespeichertes."""
        antwort = _aendern(client, kunde_headers, kunde_user.lead_id,
                           city="Koblenz")

        assert antwort.json()["stammdaten"]["city"] == "Koblenz"


class TestWasErNichtAendernDarf:
    def test_der_vertriebsstatus_bleibt_unberuehrt(
            self, client, kunde_headers, kunde_user):
        """Der Status ist unsere Arbeitsspur, nicht seine Angabe."""
        # Arrange
        vorher = _lesen(kunde_user.lead_id)["status"]

        # Act
        antwort = _aendern(client, kunde_headers, kunde_user.lead_id,
                           status="won", city="Mainz")

        # Assert — die erlaubte Aenderung greift, die andere nicht
        assert antwort.status_code == 200, antwort.text
        daten = _lesen(kunde_user.lead_id)
        assert daten["status"] == vorher, "der Kunde hat seinen Status gesetzt"
        assert daten["city"] == "Mainz"

    def test_die_antwort_sagt_welches_feld_liegen_blieb(
            self, client, kunde_headers, kunde_user):
        """Stilles Verwerfen ist die schlechtere Haelfte von „nicht erlaubt":
        Der Absender glaubt, es sei gespeichert."""
        antwort = _aendern(client, kunde_headers, kunde_user.lead_id,
                           status="won", notes="intern")

        assert set(antwort.json()["nicht_uebernommen"]) == {"status", "notes"}

    def test_die_internen_notizen_bleiben_unberuehrt(
            self, client, kunde_headers, kunde_user):
        vorher = _lesen(kunde_user.lead_id)["notes"]

        _aendern(client, kunde_headers, kunde_user.lead_id, notes="geändert")

        assert _lesen(kunde_user.lead_id)["notes"] == vorher

    @pytest.mark.parametrize("feld,wert", [
        ("customer_token", "geraten"),
        ("lead_source", "erfunden"),
        ("unread_messages", 0),
    ])
    def test_weder_token_noch_herkunft_noch_zaehler(
            self, client, kunde_headers, kunde_user, feld, wert):
        """Der Zugangs-Token ist der Schluessel zum Portal. Waere er
        setzbar, koennte sich ein Kunde einen eigenen aussuchen."""
        vorher = _lesen(kunde_user.lead_id)[feld]

        _aendern(client, kunde_headers, kunde_user.lead_id, **{feld: wert})

        assert _lesen(kunde_user.lead_id)[feld] == vorher


class TestDieGrenzenZwischenBetrieben:
    def test_ein_fremder_betrieb_bleibt_verschlossen(
            self, client, kunde_headers, fremder_betrieb):
        """Die eigene Nummer hochzuzaehlen ist der naheliegendste Angriff."""
        antwort = _aendern(client, kunde_headers, fremder_betrieb, city="Hack")

        assert antwort.status_code == 403

    def test_ohne_anmeldung_geht_nichts(self, client, kunde_user):
        antwort = client.patch(f"/api/leads/{kunde_user.lead_id}/stammdaten",
                               json={"city": "Ohne"})

        assert antwort.status_code in (401, 403)

    def test_der_innendienst_darf_weiterhin_alles(
            self, client, auth_headers, kunde_user):
        """Die Erlaubnisliste gilt dem Kunden, nicht dem Innendienst — sonst
        haette diese Aenderung dem Innendienst etwas weggenommen."""
        antwort = _aendern(client, auth_headers, kunde_user.lead_id,
                           status="qualified")

        assert antwort.status_code == 200, antwort.text
        assert _lesen(kunde_user.lead_id)["status"] == "qualified"

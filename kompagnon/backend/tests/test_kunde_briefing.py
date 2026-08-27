# -*- coding: utf-8 -*-
"""Der Kunde füllt sein Briefing selbst aus.

**Der Auftrag (26.08.2026, David).** Der Kunde soll das Briefing ausfüllen
können und Bilder und Dokumente hochladen.

**Was schon da war — und was nicht.** Den Assistenten gibt es
(`BriefingWizard.jsx`, sechs Schritte), und er ruft genau vier Adressen auf.
Alle liegen hinter `require_innendienst`; der einzige Kundenweg war
`PATCH /{lead_id}/freigabe`, also **zustimmen zu dem, was jemand anderes
eingetragen hat** (L-27). Ausfüllen konnte der Kunde nie.

Das ist die verkehrte Reihenfolge: Was ins Briefing gehört — Zielgruppe,
Leistungen, Alleinstellung, Referenzen — weiß der Betrieb und nicht wir.
Bisher hat der Innendienst es abgefragt und abgetippt.

**Kein zweiter Assistent.** Dieselben Adressen unter dem `kunden_router`,
mit derselben Eigentumsprüfung wie beim Lesen des Betriebs. Der Wizard im
Frontend bleibt unverändert; er merkt nicht, wer ihn bedient.

**Was der Kunde ausdrücklich nicht bekommt:**

- `POST /{lead_id}/suggest-field` — die KI-Vorschläge. Jeder Klick ist ein
  Modellaufruf und kostet; ob Kunden das dürfen, ist eine Preisfrage und
  keine, die beim Freischalten nebenbei entschieden wird.
- `PATCH /{lead_id}` — das ist der Innendienst-Weg für einzelne Felder.
- Fremde Betriebe, in jeder Richtung.
"""
import pytest

pytestmark = pytest.mark.usefixtures("app")


def _lesen(client, headers, lead_id):
    return client.get(f"/api/briefings/mein/{lead_id}", headers=headers)


def _schreiben(client, headers, lead_id, **felder):
    return client.put(f"/api/briefings/mein/{lead_id}", headers=headers,
                      json=felder)


class TestDasEigeneBriefing:
    def test_er_bekommt_eines_wenn_es_noch_keines_gibt(
            self, client, kunde_headers, kunde_user):
        """Ein leeres Briefing ist der Normalfall am Anfang — kein 404."""
        antwort = _lesen(client, kunde_headers, kunde_user.lead_id)

        assert antwort.status_code == 200, antwort.text
        assert antwort.json()["lead_id"] == kunde_user.lead_id

    def test_er_traegt_ein_was_nur_er_weiss(self, client, kunde_headers,
                                            kunde_user):
        """Zielgruppe und Alleinstellung kennt der Betrieb, nicht wir."""
        # Arrange
        _lesen(client, kunde_headers, kunde_user.lead_id)

        # Act
        antwort = _schreiben(client, kunde_headers, kunde_user.lead_id,
                             typischer_kunde="Eigenheimbesitzer im Umkreis 30 km",
                             usp="Notdienst rund um die Uhr")

        # Assert
        assert antwort.status_code == 200, antwort.text
        gespeichert = _lesen(client, kunde_headers, kunde_user.lead_id).json()
        assert gespeichert["typischer_kunde"] == "Eigenheimbesitzer im Umkreis 30 km"
        assert gespeichert["usp"] == "Notdienst rund um die Uhr"

    def test_zwischenspeichern_verliert_nichts(self, client, kunde_headers,
                                               kunde_user):
        """Der Assistent speichert Schritt fuer Schritt. Ein zweiter Aufruf
        darf nicht ueberschreiben, was der erste gesetzt hat — sonst waere
        jeder Schritt ein Datenverlust."""
        _lesen(client, kunde_headers, kunde_user.lead_id)
        _schreiben(client, kunde_headers, kunde_user.lead_id,
                   typischer_kunde="Erster Schritt")

        _schreiben(client, kunde_headers, kunde_user.lead_id,
                   usp="Zweiter Schritt")

        daten = _lesen(client, kunde_headers, kunde_user.lead_id).json()
        assert daten["typischer_kunde"] == "Erster Schritt"
        assert daten["usp"] == "Zweiter Schritt"

    def test_er_laedt_sein_briefing_als_pdf(self, client, kunde_headers,
                                            kunde_user):
        """Was er eingetragen hat, soll er auch mitnehmen koennen."""
        _lesen(client, kunde_headers, kunde_user.lead_id)

        antwort = client.get(f"/api/briefings/mein/{kunde_user.lead_id}/pdf",
                             headers=kunde_headers)

        assert antwort.status_code == 200, antwort.text[:200]
        assert antwort.content[:4] == b"%PDF"


class TestDieGrenzen:
    def test_ein_fremdes_briefing_bleibt_verschlossen(
            self, client, kunde_headers, fremder_betrieb):
        """Ein Briefing traegt Geschaeftsgeheimnisse — Preise, Zielgruppen,
        Alleinstellung. Die Kennung steht offen im Pfad."""
        assert _lesen(client, kunde_headers, fremder_betrieb).status_code == 403
        assert _schreiben(client, kunde_headers, fremder_betrieb,
                          usp="fremd").status_code == 403

    def test_auch_das_fremde_pdf_nicht(self, client, kunde_headers,
                                       fremder_betrieb):
        antwort = client.get(f"/api/briefings/mein/{fremder_betrieb}/pdf",
                             headers=kunde_headers)

        assert antwort.status_code == 403

    def test_ohne_anmeldung_gar_nichts(self, client, kunde_user):
        assert _lesen(client, {}, kunde_user.lead_id).status_code in (401, 403)

    def test_die_ki_vorschlaege_bleiben_beim_innendienst(
            self, client, kunde_headers, kunde_user):
        """Jeder Klick ist ein Modellaufruf. Ob Kunden ihn ausloesen duerfen,
        ist eine Preisfrage — und keine, die beim Freischalten des Briefings
        nebenbei entschieden wird."""
        antwort = client.post(
            f"/api/briefings/{kunde_user.lead_id}/suggest-field",
            headers=kunde_headers, json={"field": "usp"})

        assert antwort.status_code == 403

    def test_der_innendienst_arbeitet_unveraendert_weiter(
            self, client, auth_headers, kunde_user):
        """Die Freigabe fuer den Kunden darf dem Innendienst nichts nehmen."""
        antwort = _schreiben(client, auth_headers, kunde_user.lead_id,
                             usp="vom Innendienst")

        assert antwort.status_code == 200, antwort.text

    @pytest.mark.parametrize("feld,wert", [("status", "freigegeben"),
                                           ("project_id", 999)])
    def test_projektzuordnung_und_status_bleiben_unsere_sache(
            self, client, kunde_headers, kunde_user, feld, wert):
        """`status` traegt die Freigabe, `project_id` die Zuordnung zum
        Projekt. Beides ist Ablauf, nicht Inhalt — und Ablauf fuehren wir.

        Der Kunde koennte sonst sein Briefing selbst auf „freigegeben" setzen
        und damit einen Schritt ueberspringen, den es aus einem Grund gibt.
        """
        _lesen(client, kunde_headers, kunde_user.lead_id)
        vorher = _lesen(client, kunde_headers, kunde_user.lead_id).json().get(feld)

        antwort = _schreiben(client, kunde_headers, kunde_user.lead_id,
                             **{feld: wert}, usp="erlaubt")

        assert antwort.status_code == 200, antwort.text
        danach = _lesen(client, kunde_headers, kunde_user.lead_id).json()
        assert danach.get(feld) == vorher, f"der Kunde hat {feld} gesetzt"
        assert danach["usp"] == "erlaubt"


class TestDerWegDenDerAssistentGeht:
    """`BriefingWizard` speichert mit **POST**, nicht mit `PUT`.

    Beim Bauen fiel das erst auf, als die Oberflaeche dran war: Der
    Kundenrouter hatte nur `GET` und `PUT`, und der Assistent haette bei
    jedem Schritt einen 405 bekommen. Die Tests hier gingen an ihm vorbei,
    weil sie den Weg nahmen, den ich gebaut hatte — nicht den, den der
    Assistent nimmt.
    """

    def test_er_speichert_mit_post(self, client, kunde_headers, kunde_user):
        antwort = client.post(f"/api/briefings/mein/{kunde_user.lead_id}",
                              headers=kunde_headers,
                              json={"usp": "Meister seit 1998"})

        assert antwort.status_code == 200, antwort.text
        assert antwort.json()["usp"] == "Meister seit 1998"

    def test_auch_hier_bleiben_status_und_projekt_unsere_sache(
            self, client, kunde_headers, kunde_user):
        """Sonst haette die Erlaubnisliste ein Loch genau an der Stelle, die
        der Assistent benutzt."""
        vorher = client.get(f"/api/briefings/mein/{kunde_user.lead_id}",
                            headers=kunde_headers).json().get("status")

        client.post(f"/api/briefings/mein/{kunde_user.lead_id}",
                    headers=kunde_headers,
                    json={"status": "freigegeben", "usp": "erlaubt"})

        danach = client.get(f"/api/briefings/mein/{kunde_user.lead_id}",
                            headers=kunde_headers).json()
        assert danach.get("status") == vorher
        assert danach["usp"] == "erlaubt"

    def test_ein_fremder_betrieb_bleibt_auch_mit_post_zu(
            self, client, kunde_headers, fremder_betrieb):
        antwort = client.post(f"/api/briefings/mein/{fremder_betrieb}",
                              headers=kunde_headers, json={"usp": "fremd"})

        assert antwort.status_code == 403

# -*- coding: utf-8 -*-
"""Der Kunde erteilt seine Freigaben selbst (L-105, Entscheidung David).

**Der Befund (26.08.2026).** Das Briefing führt **elf Freigaben** — von
„Auftragserteilung & Anzahlung" über „Impressum & Datenschutz geprüft" bis
„Finale Abnahme & Go-Live Freigabe". Abgehakt hat sie bisher der
**Innendienst**: `BriefingTab.toggleFreigabe` schreibt über die
Innendienst-Route und trägt fest `durch: "KOMPAGNON"` ein.

Der Endpunkt, über den der **Kunde** sie erteilen würde, war genau dafür
gebaut — Rolle `kunde`, seine Adresse als Urheber, Datum und Uhrzeit,
**unwiderruflich** — und wurde von nirgendwo aufgerufen. Die Absicht war
also klar; es fehlte der Weg.

**Eine Abnahme, die der Auftragnehmer selbst abhakt, ist keine Abnahme.**
Bei „Finale Abnahme" und „Impressum & Datenschutz geprüft" ist das im
Streitfall der Unterschied zwischen einem Nachweis und einer Behauptung.

**Davids Entscheidung:** Der Kunde gibt selbst frei, der Innendienst behält
seinen Weg — für den Fall, dass es telefonisch oder per Mail passiert. Am
Eintrag steht dann sichtbar „KOMPAGNON" statt einer Kundenadresse. Der
Nachweis wird echt, ohne dass ein Ablauf blockiert.

**Nebenbei aufgeräumt: die Anmeldung.** Der Endpunkt las den JWT aus dem
**Rumpf** (`_token`) und entschlüsselte ihn von Hand — ein zweiter
Anmeldeweg neben dem Kopfzeilen-Verfahren, das der ganze Rest benutzt. Zwei
Wege zum selben Ziel sind zwei, die falsch sein können; das hat heute schon
einmal eine Willkommensmail gekostet. Jetzt `get_current_user` wie überall.
"""
import pytest

pytestmark = pytest.mark.usefixtures("app")

SCHLUESSEL = "abnahme_go_live"


@pytest.fixture
def briefing(app, kunde_user, client, kunde_headers):
    """Ein Briefing am Betrieb des Kunden, ohne Freigaben."""
    client.get(f"/api/briefings/mein/{kunde_user.lead_id}", headers=kunde_headers)

    from database import Briefing, SessionLocal

    db = SessionLocal()
    try:
        b = db.query(Briefing).filter(
            Briefing.lead_id == kunde_user.lead_id).first()
        b.freigaben = "{}"
        db.commit()
        return kunde_user.lead_id
    finally:
        db.close()


def _freigeben(client, headers, lead_id, key=SCHLUESSEL):
    return client.patch(f"/api/briefings/{lead_id}/freigabe",
                        headers=headers, json={"key": key})


def _stand(client, headers, lead_id):
    return client.get(f"/api/briefings/mein/{lead_id}",
                      headers=headers).json().get("freigaben", {})


class TestDerKundeGibtFrei:
    def test_er_erteilt_eine_freigabe(self, client, kunde_headers, briefing):
        antwort = _freigeben(client, kunde_headers, briefing)

        assert antwort.status_code == 200, antwort.text

    def test_sein_name_steht_darunter_nicht_unserer(self, client, kunde_headers,
                                                    briefing, kunde_user):
        """Der ganze Zweck. Steht dort „KOMPAGNON", ist es keine Abnahme,
        sondern eine Behauptung."""
        _freigeben(client, kunde_headers, briefing)

        eintrag = _stand(client, kunde_headers, briefing)[SCHLUESSEL]
        assert eintrag["durch"] == kunde_user.email
        assert eintrag["user_id"] == kunde_user.id

    def test_datum_und_uhrzeit_werden_festgehalten(self, client, kunde_headers,
                                                   briefing):
        """Ohne Zeitpunkt ist eine Freigabe im Streitfall wertlos."""
        _freigeben(client, kunde_headers, briefing)

        eintrag = _stand(client, kunde_headers, briefing)[SCHLUESSEL]
        assert eintrag["datum"] and eintrag["uhrzeit"]

    def test_er_sieht_seine_freigaben_wieder(self, client, kunde_headers,
                                             briefing):
        _freigeben(client, kunde_headers, briefing, "rechtliches")

        assert "rechtliches" in _stand(client, kunde_headers, briefing)


class TestUnwiderruflich:
    def test_eine_erteilte_freigabe_bleibt(self, client, kunde_headers,
                                           briefing):
        """Eine Abnahme, die man zurueckklicken kann, ist keine."""
        _freigeben(client, kunde_headers, briefing)

        zweiter = _freigeben(client, kunde_headers, briefing)

        assert zweiter.status_code == 400
        assert "widerrufen" in zweiter.text

    def test_und_der_erste_eintrag_bleibt_unveraendert(self, client,
                                                       kunde_headers, briefing):
        _freigeben(client, kunde_headers, briefing)
        vorher = _stand(client, kunde_headers, briefing)[SCHLUESSEL]

        _freigeben(client, kunde_headers, briefing)

        assert _stand(client, kunde_headers, briefing)[SCHLUESSEL] == vorher


class TestDieGrenzen:
    def test_ein_fremder_betrieb_bleibt_verschlossen(
            self, client, kunde_headers, fremder_betrieb):
        """Sonst gaebe ein Kunde die Abnahme eines anderen Betriebs."""
        assert _freigeben(client, kunde_headers,
                          fremder_betrieb).status_code == 403

    def test_der_innendienst_nutzt_diesen_weg_nicht(self, client, auth_headers,
                                                    briefing):
        """Er hat seinen eigenen (`PATCH /{id}` aus `BriefingTab`), und dort
        steht „KOMPAGNON" als Urheber. Erteilte er hier, traege der Eintrag
        seine Adresse — und waere von einer Kundenfreigabe nicht mehr zu
        unterscheiden. Genau das soll die Trennung verhindern."""
        assert _freigeben(client, auth_headers, briefing).status_code == 403

    def test_ohne_anmeldung_gar_nichts(self, client, briefing):
        assert _freigeben(client, {}, briefing).status_code in (401, 403)

    def test_ohne_schluessel_ist_es_ein_fehler(self, client, kunde_headers,
                                               briefing):
        antwort = client.patch(f"/api/briefings/{briefing}/freigabe",
                               headers=kunde_headers, json={})

        assert antwort.status_code == 400


class TestDerZweiteAnmeldewegIstWeg:
    def test_ein_token_im_rumpf_oeffnet_nichts_mehr(self, client, briefing):
        """Der Endpunkt las den JWT aus dem **Rumpf** und entschluesselte ihn
        von Hand — ein zweiter Anmeldeweg neben dem, den der ganze Rest
        benutzt. Zwei Wege zum selben Ziel sind zwei, die falsch sein
        koennen.
        """
        antwort = client.patch(f"/api/briefings/{briefing}/freigabe",
                               json={"key": SCHLUESSEL, "_token": "egal"})

        assert antwort.status_code in (401, 403)


def test_es_gibt_nur_noch_eine_abnahme(app):
    """**Entfernt am 26.08.2026 (Entscheidung David).**
    `POST /api/projects/{id}/abnahme` nahm einen frei getippten Namen und
    haette als **dritte** Stelle „abgenommen" behauptet — neben der
    Kundenfreigabe hier (Konto, Zeitstempel, unwiderruflich) und den
    Inhaltsfreigaben.

    Eine Abnahme ohne Beweis neben eine mit Beweis zu stellen ist ein
    Rueckschritt. Dieser Test verhindert, dass sie zurueckkommt, ohne dass
    jemand die Entscheidung noch einmal trifft.
    """
    from main import app as anwendung

    pfade = {getattr(r, "path", "") for r in anwendung.routes}

    assert "/api/projects/{project_id}/abnahme" not in pfade

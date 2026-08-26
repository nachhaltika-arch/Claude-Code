# -*- coding: utf-8 -*-
"""Erfasste Zeit — der Boden, auf dem die Marge steht.

**Der Anlass (26.08.2026, Entscheidung David).** `actual_hours` war an jedem
Projekt 0, `time_tracking` leer, und keine Oberfläche rief
`POST /api/projects/{id}/time`. Die Marge rechnete damit Festpreis minus
Werkzeugkosten und kam überall auf ~97,5 % — eine Zahl, die aussieht wie eine
Messung und keine ist. Seit demselben Tag sagt die Karte „keine Zeiten"
statt einer Zahl; jetzt bekommt sie etwas zu zeigen.

**Zwei Lücken im Endpunkt selbst, beide hier geschlossen:**

- Es gab **keinen Leseweg**. Man konnte Stunden eintragen und sie nie wieder
  sehen — eine Eingabe ohne Rückschau lädt zum doppelten Eintragen ein.
- `logged_by` war ein **Pflicht-Freitext**. Wer eintippt, wer gearbeitet hat,
  kann eintippen, was er will. Dieselbe Schwäche wie bei `POST /{id}/abnahme`
  — und dort war sie der Grund, den Endpunkt zu entfernen. Hier trägt der
  Server den angemeldeten Benutzer ein, wenn nichts mitkommt.
"""
import pytest

pytestmark = pytest.mark.usefixtures("app")


@pytest.fixture
def projekt(app):
    from database import Project, SessionLocal

    db = SessionLocal()
    try:
        p = Project(lead_id=None, status="phase_3", fixed_price=2000.0,
                    hourly_rate=45.0, ai_tool_costs=50.0, actual_hours=0)
        db.add(p)
        db.commit()
        db.refresh(p)
        kennung = p.id
    finally:
        db.close()

    yield kennung

    from sqlalchemy import text
    db = SessionLocal()
    try:
        db.execute(text("DELETE FROM time_tracking WHERE project_id = :p"),
                   {"p": kennung})
        db.query(Project).filter(Project.id == kennung).delete(
            synchronize_session=False)
        db.commit()
    finally:
        db.close()


def _erfassen(client, headers, projekt, stunden=2.5, **rest):
    daten = {"hours": stunden, "phase": 3,
             "activity_description": "Texte eingepflegt", **rest}
    return client.post(f"/api/projects/{projekt}/time", headers=headers,
                       json=daten)


class TestEintragen:
    def test_stunden_werden_erfasst(self, client, auth_headers, projekt):
        antwort = _erfassen(client, auth_headers, projekt)

        assert antwort.status_code == 200, antwort.text
        assert antwort.json()["hours_logged"] == 2.5

    def test_der_angemeldete_benutzer_steht_darunter(self, client, auth_headers,
                                                     projekt):
        """`logged_by` war ein Pflicht-Freitext. Wer eintippt, wer gearbeitet
        hat, kann eintippen, was er will — dieselbe Schwaeche, die bei
        `POST /{id}/abnahme` der Grund war, den Endpunkt zu entfernen."""
        antwort = _erfassen(client, auth_headers, projekt)

        assert antwort.json()["logged_by"], "niemand steht darunter"

    def test_die_marge_wird_dabei_neu_gerechnet(self, client, auth_headers,
                                                projekt):
        """Der eigentliche Zweck: Ohne erfasste Zeit bleibt sie „unbekannt"."""
        antwort = _erfassen(client, auth_headers, projekt, stunden=8.0)

        marge = antwort.json()["updated_margin"]
        assert marge["human_hours"] == 8.0
        assert marge["status"] != "unbekannt"


class TestNachsehen:
    def test_er_sieht_wieder_was_er_eingetragen_hat(self, client, auth_headers,
                                                    projekt):
        """Eine Eingabe ohne Rueckschau laedt zum doppelten Eintragen ein."""
        _erfassen(client, auth_headers, projekt, stunden=1.5)
        _erfassen(client, auth_headers, projekt, stunden=2.0)

        antwort = client.get(f"/api/projects/{projekt}/time", headers=auth_headers)

        assert antwort.status_code == 200, antwort.text
        assert [e["hours"] for e in antwort.json()["eintraege"]] == [2.0, 1.5]

    def test_die_summe_steht_daneben(self, client, auth_headers, projekt):
        """Sonst rechnet sie jeder Bildschirm selbst — und einer davon falsch."""
        _erfassen(client, auth_headers, projekt, stunden=1.5)
        _erfassen(client, auth_headers, projekt, stunden=2.0)

        assert client.get(f"/api/projects/{projekt}/time",
                          headers=auth_headers).json()["summe"] == 3.5

    def test_ohne_eintraege_ist_es_kein_fehler(self, client, auth_headers,
                                               projekt):
        antwort = client.get(f"/api/projects/{projekt}/time", headers=auth_headers)

        assert antwort.status_code == 200
        assert antwort.json() == {"eintraege": [], "summe": 0.0}

    def test_die_neuesten_zuerst(self, client, auth_headers, projekt):
        _erfassen(client, auth_headers, projekt, stunden=1.0,
                  activity_description="zuerst")
        _erfassen(client, auth_headers, projekt, stunden=2.0,
                  activity_description="danach")

        eintraege = client.get(f"/api/projects/{projekt}/time",
                               headers=auth_headers).json()["eintraege"]

        assert eintraege[0]["activity_description"] == "danach"


class TestDieGrenzen:
    def test_ein_kunde_erfasst_keine_zeit(self, client, kunde_headers, projekt):
        """Der Router traegt `require_innendienst` — die Marge ist unsere
        Rechnung, nicht die des Kunden."""
        assert _erfassen(client, kunde_headers, projekt).status_code == 403
        assert client.get(f"/api/projects/{projekt}/time",
                          headers=kunde_headers).status_code == 403

    def test_ein_unbekanntes_projekt_ist_404(self, client, auth_headers):
        assert _erfassen(client, auth_headers, 999999).status_code == 404

    @pytest.mark.parametrize("stunden", [0, -1.5])
    def test_null_oder_negative_stunden_werden_abgewiesen(
            self, client, auth_headers, projekt, stunden):
        """Eine negative Stunde waere eine Korrektur — und die gehoert
        besprochen, nicht stillschweigend verbucht."""
        assert _erfassen(client, auth_headers, projekt,
                         stunden=stunden).status_code == 400

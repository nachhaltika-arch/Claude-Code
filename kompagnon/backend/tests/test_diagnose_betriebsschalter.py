"""Die Schalter, die das Verhalten bestimmen, müssen sichtbar sein (L-104).

**Warum das nicht dieselbe Frage ist wie bei den Schlüsseln.** `/config`
meldet je Integration „gesetzt" oder „fehlt". Für einen Schalter ist das die
falsche Auskunft: ``USE_MOCK_EMAIL=false`` ist **gesetzt** und bedeutet
„versendet echt an Kunden". Gebraucht wird der **wirksame** Wert.

**Und genau darin lag L-104:** Die Umgebung sagte ``true``, der Scheduler
setzte den Schalter beim Start auf ``False`` zurück. Wer nur die
Umgebungsvariable liest, sieht den Fehler nie. Deshalb liest die Diagnose
über ``probemodus()`` und ``scheduler_ist_eingeschaltet()`` — dieselben
Funktionen, an denen das Verhalten wirklich hängt.

Der Bericht bleibt hinter `require_admin`: „Dieser Dienst versendet nicht"
ist eine Auskunft über den Betriebszustand, keine für die Öffentlichkeit.
"""
import pytest


class TestBetriebsschalterImBericht:
    def test_probemodus_wird_wirksam_gemeldet(self, client, auth_headers, monkeypatch):
        # Arrange — der wirksame Wert, nicht die Umgebungsvariable
        from automations import versandmodus
        monkeypatch.setattr(versandmodus, "_probemodus", True)

        # Act
        antwort = client.get("/api/diagnostics/config", headers=auth_headers)

        # Assert
        assert antwort.status_code == 200
        schalter = {s["name"]: s for s in antwort.json()["schalter"]}
        assert schalter["Mailversand"]["wirksam"] == "Probemodus"
        assert "nicht" in schalter["Mailversand"]["bedeutung"].lower()

    def test_echter_versand_wird_als_solcher_benannt(self, client, auth_headers,
                                                     monkeypatch):
        # Arrange
        from automations import versandmodus
        monkeypatch.setattr(versandmodus, "_probemodus", False)

        # Act
        schalter = {
            s["name"]: s for s in
            client.get("/api/diagnostics/config", headers=auth_headers).json()["schalter"]
        }

        # Assert — die gefährlichere Stellung muss die deutlichere Meldung haben
        assert schalter["Mailversand"]["wirksam"] == "versendet echt"

    def test_scheduler_steht_mit_im_bericht(self, client, auth_headers):
        # Act
        schalter = {
            s["name"]: s for s in
            client.get("/api/diagnostics/config", headers=auth_headers).json()["schalter"]
        }

        # Assert
        assert "Zeitauftraege" in schalter
        assert schalter["Zeitauftraege"]["wirksam"] in ("laeuft", "abgeschaltet")

    def test_kein_schalterwert_ohne_anmeldung(self, client):
        # Act & Assert — derselbe Schutz wie fuer den Rest des Berichts
        assert client.get("/api/diagnostics/config").status_code in (401, 403)

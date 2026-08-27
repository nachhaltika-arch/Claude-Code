"""Sind die Schlüssel da, ohne die eine Wiederherstellung wertlos wäre?

**Warum es diese Prüfung gibt (L-11, 23.08.2026).** `docs/sicherung-und-
wiederherstellung.md` hält seit dem 19.08. fest: Eine Datenbanksicherung
rettet den Betrieb **nicht**. Drei Dinge gehören dazu, und nur eines liegt in
der Datenbank — dazu der Datenträger und die Schlüssel. Ohne
`CREDENTIALS_KEY` und `CMS_ENCRYPTION_KEY` sind gespeicherte Zugangsdaten auch
nach vollständiger Wiederherstellung **unlesbar**.

**Was fehlte, war nicht die Erkenntnis, sondern die Messung.** Niemand konnte
sagen, ob die beiden Schlüssel produktiv überhaupt gesetzt sind. Geprüft
wurden sie erst beim **Zugriff**: `_get_fernet()` wirft, wenn der Schlüssel
fehlt, und der Aufrufer bekommt einen Fehler. Bis dahin sieht alles gesund
aus — auch `/health`.

**Es gab sogar eine Funktion dafür.** `_fernet_available()` stand in
`routers/projects.py` und beantwortete genau diese Frage. Sie wurde nie
aufgerufen; am 23.08. habe ich sie beim Aufräumen entfernt mit der Begründung,
der Startbericht beantworte das inzwischen. **Das war falsch** — er tut es
nicht, `startup_missing` listet ausgefallene Startphasen, keine fehlenden
Schlüssel. Die Funktion war nicht überflüssig, sie war **nicht
angeschlossen**. Dasselbe Muster wie L-55 und L-79: gebaut, nie verdrahtet.

**Warum die Auskunft nicht in `/health` gehört:** Der Endpunkt ist ohne
Anmeldung erreichbar. „CREDENTIALS_KEY fehlt" wäre dort eine Einladung — die
Auskunft, welcher Schutz gerade nicht greift. Sie steht deshalb im
Startprotokoll und hinter einer Anmeldung.
"""
import pytest

from services.wiederherstellbarkeit import (
    SCHLUESSEL,
    schluessel_bericht,
)


class TestDerBerichtNenntJedenSchluessel:
    def test_er_nennt_alle_bekannten(self, monkeypatch):
        # Arrange
        for name, _ in SCHLUESSEL:
            monkeypatch.delenv(name, raising=False)

        # Act
        bericht = schluessel_bericht()

        # Assert
        assert {e["name"] for e in bericht["schluessel"]} == {n for n, _ in SCHLUESSEL}

    def test_ein_fehlender_faellt_auf(self, monkeypatch):
        # Arrange
        monkeypatch.delenv("CREDENTIALS_KEY", raising=False)

        # Act
        bericht = schluessel_bericht()

        # Assert
        eintrag = next(e for e in bericht["schluessel"] if e["name"] == "CREDENTIALS_KEY")
        assert eintrag["gesetzt"] is False
        assert bericht["vollstaendig"] is False

    def test_ein_gesetzter_wird_erkannt(self, monkeypatch):
        # Arrange — ein gültiger Fernet-Schlüssel, 32 Byte base64
        monkeypatch.setenv("CREDENTIALS_KEY",
                           "bXVzdGVyc2NobHVlc3NlbC1mdWVyLWRlbi10ZXN0XzEyMw==")

        # Act
        bericht = schluessel_bericht()

        # Assert
        eintrag = next(e for e in bericht["schluessel"] if e["name"] == "CREDENTIALS_KEY")
        assert eintrag["gesetzt"] is True


class TestKeinSchluesselwertVerlaesstDieFunktion:
    """Der Bericht sagt **ob**, nie **was**. Sonst wäre er selbst das Leck."""

    def test_der_wert_steht_nirgends_im_bericht(self, monkeypatch):
        # Arrange
        geheim = "MEIN-GEHEIMER-WERT-DER-NICHT-AUFTAUCHEN-DARF"
        monkeypatch.setenv("CREDENTIALS_KEY", geheim)

        # Act
        bericht = schluessel_bericht()

        # Assert
        assert geheim not in repr(bericht)

    def test_auch_kein_teil_davon(self, monkeypatch):
        # Arrange
        monkeypatch.setenv("CMS_ENCRYPTION_KEY", "ABCDEFGH-anfang-und-ende-XYZ12345")

        # Act
        text = repr(schluessel_bericht())

        # Assert
        assert "ABCDEFGH" not in text and "XYZ12345" not in text


class TestJederSchluesselSagtWasOhneIhnFehlt:
    """Eine Liste von Variablennamen hilft niemandem beim Entscheiden."""

    @pytest.mark.parametrize("name,_wofuer", SCHLUESSEL)
    def test_jeder_traegt_seine_folge(self, name, _wofuer):
        # Act
        eintrag = next(e for e in schluessel_bericht()["schluessel"]
                       if e["name"] == name)

        # Assert
        assert len(eintrag["ohne_ihn"]) > 20, eintrag

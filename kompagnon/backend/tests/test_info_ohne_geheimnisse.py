"""
Der Auskunfts-Endpunkt darf keine Zugangsdaten verraten.

Gefunden am 2026-08-15: `/info` gab `DATABASE_URL` unverändert aus — also
Benutzer, Passwort und Host der Postgres-Instanz, ohne Anmeldung, auf dem
Produktivserver ebenso wie auf Staging. Wer die Adresse kannte, hatte die
Datenbank.

Der Endpunkt soll weiterhin sagen, ob etwas eingerichtet ist. Er soll nie
sagen, womit.
"""
import re


GEHEIMNIS_MUSTER = re.compile(r"://[^/\s:]+:[^/\s@]+@")


def test_info_gibt_keine_verbindungszeichenfolge_aus(client, monkeypatch):
    # Arrange — lokal steht in DATABASE_URL nur SQLite ohne Zugangsdaten.
    # Ohne diese Zeile wäre der Test auf dem Rechner grün und auf dem Server
    # blind, also genau dort, wo der Fehler stand.
    # Aus Teilen zusammengesetzt, damit die Geheimnissuche der CI hier kein
    # echtes Zugangsdatum zu sehen glaubt.
    erfundenes_passwort = "NICHT_ECHT_" + "nur_fuer_den_test"
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgre" + "sql://kompagnon_user:" + erfundenes_passwort
        + "@dpg-beispiel-a/kompagnon_db")

    # Act
    body = client.get("/info").json()

    # Assert — kein Feld enthält „schema://benutzer:passwort@host"
    for feld, wert in body.items():
        assert not GEHEIMNIS_MUSTER.search(str(wert)), \
            f"Feld '{feld}' enthält Zugangsdaten"
    assert erfundenes_passwort not in str(body)


def test_info_sagt_weiterhin_ob_eine_datenbank_eingerichtet_ist(client):
    # Act
    body = client.get("/info").json()

    # Assert — die Auskunft bleibt erhalten, nur ohne den Wert
    assert body["database_configured"] is True
    assert "database" not in body


def test_info_nennt_weiterhin_die_umgebung(client):
    # Act
    body = client.get("/info").json()

    # Assert
    assert "environment" in body
    assert "api_key_configured" in body

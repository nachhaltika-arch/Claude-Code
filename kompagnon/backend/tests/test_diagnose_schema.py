"""Drei Auskünfte über die laufende Datenbank — ohne Datenbankzugang (L-53, L-106).

**Warum es diesen Endpunkt gibt.** Zwei Lücken hingen am 24.08.2026 an je
einer Zeile aus der Produktiv-Datenbank, und beide Wege dorthin waren zu: Das
Render-Werkzeug scheitert am Verbindungsaufbau (`SSL/TLS required`), die
Staging-Abfrage an der Berechtigung.

* **L-53** (letzter offener P0): Antwortet `/api/dashboard/alerts` produktiv
  mit 500? Zwei Verdachtsstellen sind nachgestellt und beide echte Fehler —
  `datetime.utcnow() - start_date` bei einer `timestamptz`-Spalte und
  `sum(entry.hours)` bei einer `NULL`-Stunde. Unter dem Schema, das die
  Migrationen erzeugen, kann **keiner** von beiden eintreten. Offen ist nur,
  ob das Produktiv-Schema davon abweicht.
* **L-106**: Ist `usercards` produktiv ebenfalls leer? Dann bekommt jeder
  Kunde auf seiner Startseite einen 404.

**Warum ein Endpunkt und keine Ausnahme im Zugang.** Ein Lesekonto oder eine
geöffnete Inbound-Regel löst die Frage einmal und öffnet die Datenbank
dauerhaft — gegen die Richtung von L-44. Der Endpunkt beantwortet **genau
diese drei Fragen**, hinter `require_admin`, und lässt sich jederzeit
wiederholen, wenn dieselbe Frage wieder aufkommt.

**Er gibt keine Daten heraus, nur Form und Anzahl.** Datentyp, Nullbarkeit,
Zeilenzahl — nichts, was einen Betrieb oder eine Person nennt.
"""
import pytest


class TestSchemaBericht:
    def test_ohne_anmeldung_gibt_es_nichts(self, client):
        # Act & Assert — dieselbe Sperre wie der Rest der Diagnose
        assert client.get("/api/diagnostics/schema").status_code in (401, 403)

    def test_der_bericht_nennt_die_drei_fragen(self, client, auth_headers):
        # Act
        antwort = client.get("/api/diagnostics/schema", headers=auth_headers)

        # Assert
        assert antwort.status_code == 200
        daten = antwort.json()
        for schluessel in ("spalten", "zeilenzahlen", "bewertung"):
            assert schluessel in daten

    def test_die_beiden_verdachtsspalten_stehen_drin(self, client, auth_headers):
        # Act
        spalten = {
            f"{s['tabelle']}.{s['spalte']}": s
            for s in client.get("/api/diagnostics/schema",
                                headers=auth_headers).json()["spalten"]
        }

        # Assert
        assert "projects.start_date" in spalten
        assert "time_tracking.hours" in spalten

    def test_die_bewertung_sagt_was_die_zahl_bedeutet(self, client, auth_headers):
        """Eine Zahl ohne Deutung wird beim Lesen falsch gedeutet."""
        # Act
        bewertung = client.get("/api/diagnostics/schema",
                               headers=auth_headers).json()["bewertung"]

        # Assert — je Lücke ein Satz, der sagt, was der Befund heisst
        assert "L-53" in bewertung
        assert "L-106" in bewertung

    def test_kein_einziger_datenwert_verlaesst_den_endpunkt(self, client, auth_headers):
        """Form und Anzahl ja, Inhalt nein."""
        # Act
        roh = client.get("/api/diagnostics/schema", headers=auth_headers).text

        # Assert — kein Firmenname, keine Adresse aus der lokalen Datenbank
        for verboten in ("@", "GmbH", "http"):
            assert verboten not in roh, (
                f"Der Bericht enthaelt {verboten!r} — das riecht nach einem "
                "Datenwert. Er soll nur Form und Anzahl melden."
            )

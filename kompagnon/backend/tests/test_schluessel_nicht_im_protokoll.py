"""L-98 — Der Schlüssel darf nicht im Klartext im Protokoll stehen.

Zwei Riegel, weil ein einzelner nicht reicht:

1. **PageSpeed** schickt den Schlüssel als Kopfzeile ``X-Goog-Api-Key``
   statt als Abfrageparameter. Dann kann ihn gar keine Protokollstelle
   ausplaudern — auch kein Traceback und kein Proxy-Protokoll.
2. **Die alte Places-Schnittstelle nimmt die Kopfzeile nicht** (am
   24.08.2026 am echten Endpunkt geprüft: Antwort ``REQUEST_DENIED — You
   must use an API key to authenticate``). Dort muss der Schlüssel in der
   URL bleiben, also wird er im Protokoll geschwärzt.
"""
import logging

import pytest

from services.audit_pagespeed import auth_headers
from services.protokoll_schwaerzung import Schwaerzung, schwaerzen


class TestPagespeedSchluesselAlsKopfzeile:
    def test_setzt_kopfzeile_wenn_schluessel_vorhanden(self, monkeypatch):
        # Arrange
        monkeypatch.setenv("PAGESPEED_API_KEY", "AIzaSyGEHEIM123")

        # Act
        kopf = auth_headers()

        # Assert
        assert kopf == {"X-Goog-Api-Key": "AIzaSyGEHEIM123"}

    def test_laesst_kopfzeile_weg_wenn_kein_schluessel(self, monkeypatch):
        # Arrange — ein *leerer* Schlüssel ist bei Google 400, kein Schlüssel
        # läuft auf dem anonymen Kontingent. Die Kopfzeile muss also fehlen.
        monkeypatch.setenv("PAGESPEED_API_KEY", "")
        monkeypatch.setenv("GOOGLE_PAGESPEED_API_KEY", "")

        # Act
        kopf = auth_headers()

        # Assert
        assert kopf == {}


class TestSchwaerzung:
    @pytest.mark.parametrize("roh, erwartet", [
        (
            "HTTP Request: GET https://x/runPagespeed?url=a&key=AIzaSyGEHEIM123 200",
            "HTTP Request: GET https://x/runPagespeed?url=a&key=***geschwaerzt*** 200",
        ),
        (
            "GET https://maps.googleapis.com/x/json?input=a&key=AIzaSyGEHEIM123",
            "GET https://maps.googleapis.com/x/json?input=a&key=***geschwaerzt***",
        ),
        (
            "GET https://x?api_key=abc123&token=def456",
            "GET https://x?api_key=***geschwaerzt***&token=***geschwaerzt***",
        ),
    ])
    def test_schwaerzt_geheime_abfrageparameter(self, roh, erwartet):
        assert schwaerzen(roh) == erwartet

    def test_laesst_harmlose_parameter_stehen(self):
        # Arrange
        roh = "GET https://x?url=https://kunde.de&strategy=mobile&category=performance"

        # Act & Assert — eine Schwärzung, die zu viel schwärzt, macht das
        # Protokoll unlesbar und wird abgeschaltet.
        assert schwaerzen(roh) == roh

    def test_filter_schwaerzt_den_ausgegebenen_satz(self):
        # Arrange
        f = Schwaerzung()
        satz = logging.LogRecord(
            name="httpx", level=logging.INFO, pathname=__file__, lineno=1,
            msg='HTTP Request: GET https://x?key=%s "200 OK"',
            args=("AIzaSyGEHEIM123",), exc_info=None,
        )

        # Act
        behalten = f.filter(satz)

        # Assert — der Satz wird durchgelassen, nur eben ohne Schlüssel.
        assert behalten is True
        assert "AIzaSyGEHEIM123" not in satz.getMessage()
        assert "***geschwaerzt***" in satz.getMessage()

    def test_ruehrt_saetze_ohne_geheimnis_nicht_an(self):
        # Arrange — der häufige Fall; er darf nichts kosten.
        f = Schwaerzung()
        satz = logging.LogRecord(
            name="httpx", level=logging.INFO, pathname=__file__, lineno=1,
            msg="HTTP Request: GET https://x?url=%s", args=("https://kunde.de",),
            exc_info=None,
        )

        # Act
        f.filter(satz)

        # Assert — Vorlage und Argumente unverändert, nicht vorformatiert.
        assert satz.args == ("https://kunde.de",)

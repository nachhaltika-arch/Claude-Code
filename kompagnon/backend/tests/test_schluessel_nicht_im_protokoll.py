"""L-98 — Der Schlüssel darf nicht im Klartext im Protokoll stehen.

Zwei Riegel, weil ein einzelner nicht reicht:

1. **PageSpeed** schickt den Schlüssel als Kopfzeile ``X-Goog-Api-Key``
   statt als Abfrageparameter. Dann kann ihn gar keine Protokollstelle
   ausplaudern — auch kein Traceback und kein Proxy-Protokoll.
2. **Die alte Places-Schnittstelle nimmt die Kopfzeile nicht** (am
   24.08.2026 am echten Endpunkt geprüft: Antwort ``REQUEST_DENIED — You
   must use an API key to authenticate``). Dort muss der Schlüssel in der
   URL bleiben, also wird er im Protokoll geschwärzt.

**Warum der erfundene Schlüssel hier nicht wie ein echter aussehen darf.**
Der erste Anlauf nahm ``AIzaSy…`` — die Form eines echten Google-Schlüssels.
Der Gitleaks-Lauf der CI schlug an (drei Funde, Lauf 32716902764), und das
war richtig: Ein Wächter, der zwischen „sieht aus wie ein Schlüssel“ und „ist
einer“ unterscheiden könnte, würde beim nächsten Mal den echten durchlassen.
Der Testwert trägt jetzt seine Rolle im Namen.
"""
import logging

import pytest

from services.audit_pagespeed import auth_headers
from services.protokoll_schwaerzung import Schwaerzung, schwaerzen


class TestPagespeedSchluesselAlsKopfzeile:
    def test_setzt_kopfzeile_wenn_schluessel_vorhanden(self, monkeypatch):
        # Arrange
        monkeypatch.setenv("PAGESPEED_API_KEY", "geheim-nur-im-test")

        # Act
        kopf = auth_headers()

        # Assert
        assert kopf == {"X-Goog-Api-Key": "geheim-nur-im-test"}

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
            "HTTP Request: GET https://x/runPagespeed?url=a&key=geheim-nur-im-test 200",
            "HTTP Request: GET https://x/runPagespeed?url=a&key=***geschwaerzt*** 200",
        ),
        (
            "GET https://maps.googleapis.com/x/json?input=a&key=geheim-nur-im-test",
            "GET https://maps.googleapis.com/x/json?input=a&key=***geschwaerzt***",
        ),
        (
            "GET https://x?api_key=abc123&token=def456",
            "GET https://x?api_key=***geschwaerzt***&token=***geschwaerzt***",
        ),
    ])
    def test_schwaerzt_geheime_abfrageparameter(self, roh, erwartet):
        assert schwaerzen(roh) == erwartet

    @pytest.mark.parametrize("pfad", [
        "/api/posteingang/brevo/",
        "/api/mail-events/brevo/",
    ])
    def test_schwaerzt_auch_geheimnisse_im_pfad(self, pfad):
        """**Der Fund vom 31.08.2026 — eine Ebene weiter als L-98.**

        Beide Brevo-Webhooks tragen ihr Geheimnis im **Pfad**, weil Brevo
        nicht signiert und der Pfad die einzige Stelle ist, die unveraendert
        ankommt. Uvicorn schreibt jede Anfragezeile mit vollem Pfad ins
        Protokoll — damit stand
        `POST /api/posteingang/brevo/<Geheimnis> 200 OK` im Klartext im
        Produktivprotokoll.

        Gefunden nicht beim Suchen danach, sondern beim **Nachlesen des
        Protokolls** waehrend des Beweislaufs fuer L-18.
        """
        roh = f'INFO: 1.2.3.4:0 - "POST {pfad}geheim-nur-im-test HTTP/1.1" 200 OK'

        geschwaerzt = schwaerzen(roh)

        assert "geheim-nur-im-test" not in geschwaerzt
        # Der Weg bleibt lesbar — sonst laesst sich nicht mehr sehen, **dass**
        # der Webhook gerufen wurde.
        assert pfad in geschwaerzt
        assert "***geschwaerzt***" in geschwaerzt
        assert "200 OK" in geschwaerzt

    @pytest.mark.parametrize("pfad", [
        "/api/posteingang/brevo/geheim-nur-im-test",
        "/api/mail-events/brevo/geheim-nur-im-test",
    ])
    def test_filter_schwaerzt_die_satzform_von_uvicorn(self, pfad):
        """**Die Satzform, die uvicorn wirklich erzeugt** — nicht eine gebaute.

        Am 31.08.2026 zweimal danebengegriffen, und beide Male haette dieser
        Test es gefangen:

        1. Der Filter hing nur an den Handlern der Wurzel; `uvicorn.access`
           hat eigene und `propagate = False`.
        2. Danach hing er richtig — und wirkte trotzdem nicht: Die Schranke
           im Filter stieg aus, wenn kein `=` im Satz vorkam, und die
           Anfragezeile hat keins. Die Pfadschwaerzung war eingebaut und
           **nicht angeschlossen**.

        Die vorhandenen Tests pruefen `schwaerzen()` mit einem fertigen Satz.
        Uvicorn uebergibt den Pfad aber als **Argument** zu einer Vorlage; wer
        nur die Funktion prueft, sieht die Schranke davor nie.
        """
        satz = logging.LogRecord(
            name="uvicorn.access", level=logging.INFO, pathname=__file__,
            lineno=1, msg='%s - "%s %s HTTP/%s" %d %s',
            args=("1.2.3.4:0", "POST", pfad, "1.1", 403, "Forbidden"),
            exc_info=None,
        )

        Schwaerzung().filter(satz)

        ausgabe = satz.getMessage()
        assert "geheim-nur-im-test" not in ausgabe
        assert "***geschwaerzt***" in ausgabe
        # Der Rest der Zeile bleibt lesbar — sonst taugt das Protokoll nicht.
        assert "403 Forbidden" in ausgabe

    def test_filter_laesst_gewoehnliche_anfragezeilen_stehen(self):
        """Die Gegenprobe: Ohne sie waere der Test darueber auch dann gruen,
        wenn **jede** Anfragezeile geschwaerzt wuerde."""
        satz = logging.LogRecord(
            name="uvicorn.access", level=logging.INFO, pathname=__file__,
            lineno=1, msg='%s - "%s %s HTTP/%s" %d %s',
            args=("1.2.3.4:0", "GET", "/api/leads/12/audits", "1.1", 200, "OK"),
            exc_info=None,
        )

        Schwaerzung().filter(satz)

        assert satz.getMessage() == '1.2.3.4:0 - "GET /api/leads/12/audits HTTP/1.1" 200 OK'

    def test_der_filter_haengt_am_zugriffsprotokoll_von_uvicorn(self):
        """**Die Schwaerzung muss dort haengen, wo der Pfad hingeschrieben wird.**

        Am 31.08.2026 am laufenden Dienst gemessen statt im Code gelesen: Ein
        Aufruf auf `/api/posteingang/brevo/pruefwert…` stand danach
        **unveraendert** im Staging-Protokoll. Der Filter hing nur an den
        Handlern der Wurzel — und uvicorn setzt fuer `uvicorn.access` eigene
        Handler mit `propagate = False`. Ausgerechnet die Anfragezeile traegt
        aber den Pfad.

        Eine Schwaerzung, die die eine Zeile nicht sieht, in der das
        Geheimnis wirklich steht, ist keine.
        """
        import logging

        import main  # noqa: F401  — haengt die Filter beim Import ein

        for name in ("uvicorn.access", "uvicorn.error"):
            arten = [type(f).__name__ for f in logging.getLogger(name).filters]
            assert "Schwaerzung" in arten, (
                f"{name} hat keine Schwaerzung — der Pfad steht dort im Klartext")

    def test_laesst_gewoehnliche_pfade_stehen(self):
        """Die Gegenprobe zur Pfadschwaerzung.

        Ohne sie waere der Test darueber auch dann gruen, wenn **jeder** Pfad
        geschwaerzt wuerde — und dann waere das Protokoll unbrauchbar.
        """
        roh = 'INFO: 1.2.3.4:0 - "GET /api/leads/12/audits HTTP/1.1" 200 OK'

        assert schwaerzen(roh) == roh

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
            args=("geheim-nur-im-test",), exc_info=None,
        )

        # Act
        behalten = f.filter(satz)

        # Assert — der Satz wird durchgelassen, nur eben ohne Schlüssel.
        assert behalten is True
        assert "geheim-nur-im-test" not in satz.getMessage()
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

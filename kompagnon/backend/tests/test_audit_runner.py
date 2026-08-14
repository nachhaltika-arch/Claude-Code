"""
Das Laden der Startseite — der Schritt, an dem ein ganzes Audit hängt.

Schlägt er fehl, bricht das Audit ab und der Besucher des Widgets liest
„Die Seite war nicht erreichbar". Beobachtet wurde, dass dieselbe Adresse
mal einwandfrei antwortet und mal ein selbstsigniertes Zertifikat liefert.
Ein einzelner Fehlversuch darf deshalb nicht das Ergebnis bestimmen.
"""
import asyncio

import httpx
import pytest

from services import audit_runner
from services.url_guard import UnsafeUrlError


class AntwortAttrappe:
    def __init__(self, status_code=200, text="<html>hallo</html>"):
        self.status_code = status_code
        self.text = text
        self.headers = {}
        self.url = "https://firma.de"


@pytest.fixture(autouse=True)
def ohne_wartezeit(monkeypatch):
    """Die Pause zwischen den Versuchen interessiert hier nicht."""
    monkeypatch.setattr(audit_runner, "HOMEPAGE_RETRY_DELAY", 0)


def _antworten_nacheinander(monkeypatch, ergebnisse):
    """Lässt fetch_guarded der Reihe nach liefern oder werfen. Zählt Aufrufe."""
    aufrufe = {"anzahl": 0}

    async def gefaelscht(_client, _url, **_kwargs):
        ergebnis = ergebnisse[aufrufe["anzahl"]]
        aufrufe["anzahl"] += 1
        if isinstance(ergebnis, Exception):
            raise ergebnis
        return ergebnis

    monkeypatch.setattr(audit_runner, "fetch_guarded", gefaelscht)
    return aufrufe


def test_einzelner_zertifikatsfehler_beendet_das_audit_nicht(monkeypatch):
    # Arrange — erster Versuch scheitert am Zertifikat, zweiter klappt
    aufrufe = _antworten_nacheinander(monkeypatch, [
        httpx.ConnectError("[SSL: CERTIFICATE_VERIFY_FAILED] self-signed certificate"),
        AntwortAttrappe(),
    ])

    # Act
    ergebnis = asyncio.run(audit_runner.fetch_homepage("https://firma.de"))

    # Assert
    assert ergebnis["reachable"] is True
    assert ergebnis["status_code"] == 200
    assert aufrufe["anzahl"] == 2


def test_dauerhaft_nicht_erreichbar_meldet_den_letzten_fehler(monkeypatch):
    # Arrange
    fehler = httpx.ConnectError("Name oder Dienst nicht bekannt")
    aufrufe = _antworten_nacheinander(
        monkeypatch, [fehler] * audit_runner.HOMEPAGE_ATTEMPTS)

    # Act
    ergebnis = asyncio.run(audit_runner.fetch_homepage("https://gibtsnicht.example"))

    # Assert
    assert ergebnis["reachable"] is False
    assert "Verbindung fehlgeschlagen" in ergebnis["error"]
    assert aufrufe["anzahl"] == audit_runner.HOMEPAGE_ATTEMPTS


def test_abgelehnte_adresse_wird_nicht_wiederholt(monkeypatch):
    # Arrange — eine gesperrte Adresse ist kein Netzproblem
    aufrufe = _antworten_nacheinander(
        monkeypatch, [UnsafeUrlError("Ziel ist nicht öffentlich erreichbar")])

    # Act
    ergebnis = asyncio.run(audit_runner.fetch_homepage("http://127.0.0.1"))

    # Assert
    assert ergebnis["reachable"] is False
    assert "nicht erlaubt" in ergebnis["error"]
    assert aufrufe["anzahl"] == 1


def test_erreichbare_seite_wird_nur_einmal_geladen(monkeypatch):
    # Arrange
    aufrufe = _antworten_nacheinander(monkeypatch, [AntwortAttrappe()])

    # Act
    ergebnis = asyncio.run(audit_runner.fetch_homepage("https://firma.de"))

    # Assert
    assert ergebnis["reachable"] is True
    assert aufrufe["anzahl"] == 1


# ── Die Notiz zur Erkennung ───────────────────────────────────────────

def test_ohne_betriebsseite_steht_der_grund_in_den_notizen():
    """Sonst sieht der Leser nur eine niedrigere Abdeckung ohne Erklärung."""
    notizen = audit_runner.collection_notes(
        {}, {"betriebsseite": False, "branche": "politischer Kandidat"})

    assert notizen["angebotskriterien"]["reason"] == "keine_betriebsseite"
    assert notizen["angebotskriterien"]["detail"] == "politischer Kandidat"


def test_bei_einer_betriebsseite_gibt_es_keine_solche_notiz():
    notizen = audit_runner.collection_notes(
        {}, {"betriebsseite": True, "branche": "Dachdecker"})

    assert "angebotskriterien" not in notizen


def test_ohne_ki_ergebnis_bleibt_die_notiz_aus():
    """Ein fehlgeschlagener KI-Aufruf ist kein „kein Betrieb erkannt"."""
    assert "angebotskriterien" not in audit_runner.collection_notes({}, {})
    assert "angebotskriterien" not in audit_runner.collection_notes({})

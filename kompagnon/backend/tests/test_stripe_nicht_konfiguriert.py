"""Ein fehlender Schlüssel ist kein Serverfehler.

Befund vom 19.08.2026, gemessen am laufenden Produktivsystem:

    GET /api/payments/session/{id} → 500

Es war kein Absturz. Der Endpunkt wirft die 500 **absichtlich**, weil
`STRIPE_SECRET_KEY` produktiv nicht gesetzt ist. Nur ist 500 die falsche
Auskunft: Sie sagt „bei mir ist etwas kaputtgegangen", während in Wirklichkeit
gilt „ich bin für diese Aufgabe nicht eingerichtet".

Der Unterschied ist nicht kosmetisch. Eine 500 gehört in jede
Fehlerüberwachung und in jede Alarmierung; sie ist der Grund nachzusehen. Wenn
ein bekannter, gewollter Zustand sie auslöst, gewöhnt man sich an rote Zahlen —
und übersieht die eine echte.

Das Haus kennt die Regel bereits und schreibt sie in `routers/newsletter.py`
auf:

    503, wenn der Dienst gar nicht einsatzbereit ist (fehlender Schluessel) —
    502, wenn Brevo selbst ablehnt oder nicht erreichbar ist.

Befolgt wird sie an fünf Stellen, darunter zweimal im Zahlungs-Router selbst
(`payments.py:170`, `geo_payments.py:138`). Drei Stellen sagten trotzdem 500 —
und ausgerechnet die eine davon, die ohne Anmeldung erreichbar ist, hat es
produktiv gezeigt.
"""
import re
from pathlib import Path

import pytest

ROUTER = Path(__file__).resolve().parent.parent / "routers"


def test_die_offene_sitzungsabfrage_meldet_nicht_eingerichtet(client, monkeypatch):
    """Der produktiv gemessene Fall."""
    # Arrange
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)

    # Act
    antwort = client.get("/api/payments/session/cs_test_gibtesnicht")

    # Assert
    assert antwort.status_code == 503, (
        f"-> {antwort.status_code}: Ein fehlender Schlüssel meldet sich als "
        "Serverfehler und landet damit in jeder Alarmierung."
    )


# ── Die Richtung, nicht der Einzelfall ────────────────────────────────

@pytest.mark.parametrize("datei", ["payments.py", "geo_payments.py"])
def test_kein_fehlender_schluessel_meldet_sich_als_500(datei):
    """Damit die nächste Stelle nicht wieder 500 sagt.

    Geprüft wird an der Quelle: Ein Test, der jeden Endpunkt einzeln aufruft,
    kennt den morgen hinzugefügten nicht.
    """
    quelle = (ROUTER / datei).read_text(encoding="utf-8")

    treffer = [
        zeile.strip() for zeile in quelle.splitlines()
        if re.search(r"HTTPException\(\s*(status_code\s*=\s*)?500", zeile)
        and re.search(r"nicht konfiguriert|not_configured|fehlt", zeile)
    ]

    assert treffer == [], (
        f"{datei}: fehlende Einrichtung wird als Serverfehler gemeldet — "
        f"{treffer}"
    )

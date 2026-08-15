"""
Der Start der Anwendung — und warum produktiv sieben von acht Phasen ausfielen.

Am 15.08.2026 in den Produktiv-Logs gefunden: „DB init Timeout", „Default admin
Timeout", „Scheduler Timeout" — sieben Warnungen hintereinander, und danach
„Migrationen abgeschlossen — 462 von 462". Die Reihenfolge verrät den Fehler.

Die Phasen liefen in einem ``ThreadPoolExecutor(max_workers=1)``.
``asyncio.wait_for`` bricht das Warten ab, nicht den laufenden Thread: Die
Migration hielt den einzigen Worker 215 Sekunden, alle folgenden Phasen
standen in der Warteschlange und liefen der Reihe nach in ihr Timeout, **ohne
je gestartet worden zu sein**. „Übersprungen" war dabei die falsche Auskunft —
sie klingt nach einem Versuch.

Produktiv heißt das: kein Scheduler, keine Automationen, und „Demokonten
abschalten" lief nie. Auf Staging fiel es nicht auf, weil die Migration dort in
Sekunden durch ist — der Unterschied ist die Datenbank in Frankfurt bei einem
Backend in Oregon.
"""
import asyncio

from services.startphasen import Phase, fuehre_phasen_aus


def _sammle(protokoll, name):
    def fn():
        protokoll.append(name)
    return fn


# ── Der Normalfall ─────────────────────────────────────────────────

def test_alle_phasen_laufen_der_reihe_nach():
    # Arrange
    protokoll = []
    phasen = [Phase("Eins", _sammle(protokoll, "eins")),
              Phase("Zwei", _sammle(protokoll, "zwei")),
              Phase("Drei", _sammle(protokoll, "drei"))]

    # Act
    ergebnis = asyncio.run(fuehre_phasen_aus(phasen, budget=10))

    # Assert
    assert protokoll == ["eins", "zwei", "drei"]
    assert ergebnis.vollstaendig is True
    assert ergebnis.ausgefallen == []


# ── Eine langsame Phase darf die folgenden nicht verschlucken ──────

def test_eine_langsame_phase_blockiert_die_folgenden_nicht():
    # Arrange — genau der Produktivfall: die erste Phase dauert lange,
    # die folgenden sind kurz. Vorher kamen sie nie dran.
    protokoll = []

    def langsam():
        import time
        time.sleep(0.4)
        protokoll.append("langsam")

    phasen = [Phase("Langsam", langsam),
              Phase("Kurz A", _sammle(protokoll, "a")),
              Phase("Kurz B", _sammle(protokoll, "b"))]

    # Act
    ergebnis = asyncio.run(fuehre_phasen_aus(phasen, budget=10))

    # Assert
    assert protokoll == ["langsam", "a", "b"]
    assert ergebnis.vollstaendig is True


# ── Wenn das Budget nicht reicht ───────────────────────────────────

def test_ein_erschoepftes_budget_benennt_die_nicht_gelaufenen_phasen():
    # Arrange
    protokoll = []

    def zu_langsam():
        import time
        time.sleep(2.0)
        protokoll.append("nie fertig")

    phasen = [Phase("Bremse", zu_langsam),
              Phase("Danach A", _sammle(protokoll, "a")),
              Phase("Danach B", _sammle(protokoll, "b"))]

    # Act
    ergebnis = asyncio.run(fuehre_phasen_aus(phasen, budget=0.3))

    # Assert — nicht „übersprungen", sondern beim Namen genannt
    assert ergebnis.vollstaendig is False
    assert "Bremse" in ergebnis.ausgefallen
    assert "Danach A" in ergebnis.ausgefallen
    assert "Danach B" in ergebnis.ausgefallen


def test_eine_fehlerhafte_phase_stoppt_die_uebrigen_nicht():
    # Arrange — ein Seed darf den Scheduler nicht mitreißen
    protokoll = []

    def wirft():
        raise RuntimeError("Seed kaputt")

    phasen = [Phase("Kaputt", wirft),
              Phase("Danach", _sammle(protokoll, "danach"))]

    # Act
    ergebnis = asyncio.run(fuehre_phasen_aus(phasen, budget=10))

    # Assert
    assert protokoll == ["danach"]
    assert "Kaputt" in ergebnis.gescheitert
    assert ergebnis.vollstaendig is False


# ── Das Ergebnis muss von außen sichtbar sein ──────────────────────

def test_das_ergebnis_nennt_dauer_und_gelaufene_phasen():
    # Arrange
    phasen = [Phase("Eins", lambda: None), Phase("Zwei", lambda: None)]

    # Act
    ergebnis = asyncio.run(fuehre_phasen_aus(phasen, budget=10))

    # Assert
    assert ergebnis.gelaufen == ["Eins", "Zwei"]
    assert ergebnis.dauer >= 0


def test_ohne_phasen_ist_der_start_vollstaendig():
    ergebnis = asyncio.run(fuehre_phasen_aus([], budget=10))

    assert ergebnis.vollstaendig is True
    assert ergebnis.gelaufen == []

"""Der Probemodus muss den Scheduler-Start überleben (L-104).

**Der Fund vom 24.08.2026.** `automations/versandmodus.py` liest
``USE_MOCK_EMAIL`` aus der Umgebung — und ``CompagnonScheduler.__init__``
ruft ``setze_probemodus(use_mock_email)`` mit dem Vorgabewert ``False``.
``start_scheduler()`` uebergibt nichts, also gewinnt immer die Vorgabe:
Nach dem Start steht der Probemodus auf ``False``, egal was in der Umgebung
stand.

Das ist dieselbe Falle, vor der der Kopf von `versandmodus.py` warnt — ein
Schalter, der zur Laufzeit umgelegt wird —, nur eine Ebene hoeher: Nicht ein
kopierter *Name* fror den Wert ein, sondern ein **Vorgabewert** ueberschrieb
ihn.

**Warum das zaehlt:** `/health` meldet auf Staging ``scheduler_enabled:
true``, und unter den Zeitauftraegen sind versendende. Ohne wirksamen
Probemodus gibt es keinen Weg, einen laufenden Dienst still zu stellen,
ausser den Scheduler ganz abzuschalten.
"""
import importlib

import pytest


@pytest.fixture
def frisch(monkeypatch):
    """Beide Module neu laden — der Probemodus ist Modulzustand."""
    def _laden(umgebung: str):
        monkeypatch.setenv("USE_MOCK_EMAIL", umgebung)
        monkeypatch.setenv("SCHEDULER_JOBSTORE", "memory")
        versandmodus = importlib.reload(
            importlib.import_module("automations.versandmodus"))
        scheduler = importlib.import_module("automations.scheduler")
        importlib.reload(scheduler)
        scheduler._scheduler = None
        return versandmodus, scheduler
    return _laden


class TestProbemodusUeberlebtDenStart:
    def test_umgebung_true_bleibt_true(self, frisch):
        # Arrange
        versandmodus, scheduler = frisch("true")
        assert versandmodus.probemodus() is True, "Vorbedingung"

        # Act — genau das, was start_scheduler() tut
        scheduler.get_scheduler()

        # Assert
        assert versandmodus.probemodus() is True, (
            "USE_MOCK_EMAIL=true wurde beim Scheduler-Start verworfen — "
            "der Dienst versendet echt, obwohl Probemodus verlangt war."
        )

    def test_umgebung_false_bleibt_false(self, frisch):
        # Arrange
        versandmodus, scheduler = frisch("false")

        # Act
        scheduler.get_scheduler()

        # Assert
        assert versandmodus.probemodus() is False

    def test_ausdrueckliche_angabe_gewinnt_weiterhin(self, frisch):
        """Ein Aufrufer, der es ausdruecklich sagt, darf weiter bestimmen."""
        # Arrange — Umgebung sagt „echt versenden"
        versandmodus, scheduler = frisch("false")

        # Act — der Aufrufer verlangt ausdruecklich den Probemodus
        scheduler.get_scheduler(use_mock_email=True)

        # Assert
        assert versandmodus.probemodus() is True

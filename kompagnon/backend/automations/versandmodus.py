"""Ob Mails wirklich hinausgehen — ein Schalter an einer Stelle (L-25).

**Warum eigene Datei, 22.08.2026.** Beim Aufteilen von `scheduler.py` stand
`_use_mock_email` als Modulvariable dort, und `CompagnonScheduler.__init__`
legt sie per `global` um. Der Kontakt-Teil, der sie liest, waere damit auf
einen **Namensimport** angewiesen gewesen — und der kopiert den Wert beim
Import. Eine spaetere Umschaltung haette ihn nie erreicht: Der Scheduler
liefe im Probemodus, und die Mails gingen trotzdem hinaus.

Ein Schalter, der zur Laufzeit umgelegt wird, gehoert deshalb hinter
Funktionen — nicht hinter einen Namen, den andere kopieren.
"""
import os

#: Vorgabe aus der Umgebung. `CompagnonScheduler` kann sie ueberschreiben.
_probemodus = os.getenv("USE_MOCK_EMAIL", "false").lower() == "true"


def probemodus() -> bool:
    """Sollen Mails nur protokolliert statt versendet werden?"""
    return _probemodus


def setze_probemodus(an: bool) -> None:
    """Wird vom Scheduler beim Start aufgerufen."""
    global _probemodus
    _probemodus = bool(an)

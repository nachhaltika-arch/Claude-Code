"""
Die Phasen des Anwendungsstarts — nacheinander, mit einem gemeinsamen Budget.

Vorher bekam jede Phase ein eigenes Timeout und alle liefen in einem
``ThreadPoolExecutor(max_workers=1)``. ``asyncio.wait_for`` bricht aber nur das
Warten ab, nicht den laufenden Thread: Die Migration hielt den einzigen Worker
215 Sekunden, und die sieben folgenden Phasen standen so lange in der
Warteschlange, bis ihr eigenes Timeout ablief — **ohne je gestartet worden zu
sein**. Produktiv fehlten dadurch Scheduler, Demokonten-Abschaltung und vier
weitere Schritte, und im Log stand nur „übersprungen".

Deshalb hier ein Budget für den ganzen Ablauf statt acht Einzeltimeouts. Wer
zuerst kommt, läuft zu Ende; was danach keine Zeit mehr hat, wird beim Namen
genannt. Der Port ist zu diesem Zeitpunkt längst offen — der Start blockiert
nichts, er darf also ehrlich lange dauern.
"""
import asyncio
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Callable, List

logger = logging.getLogger(__name__)

# Produktiv brauchten allein die Migrationen 215 s (Datenbank in Frankfurt,
# Backend in Oregon). Das Budget muss den langsamsten realen Start überdecken,
# sonst verschiebt sich der Fehler nur.
STANDARD_BUDGET_SEK = 600.0


@dataclass
class Phase:
    name: str
    aufgabe: Callable[[], None]


@dataclass
class Startergebnis:
    gelaufen: List[str] = field(default_factory=list)
    gescheitert: List[str] = field(default_factory=list)
    ausgefallen: List[str] = field(default_factory=list)
    dauer: float = 0.0

    @property
    def vollstaendig(self) -> bool:
        return not self.gescheitert and not self.ausgefallen

    def bericht(self) -> str:
        if self.vollstaendig:
            return f"Start vollständig in {self.dauer:.1f}s ({len(self.gelaufen)} Phasen)"
        teile = [f"Start unvollständig nach {self.dauer:.1f}s"]
        if self.gescheitert:
            teile.append("mit Fehler: " + ", ".join(self.gescheitert))
        if self.ausgefallen:
            teile.append("nicht ausgeführt: " + ", ".join(self.ausgefallen))
        return " — ".join(teile)


async def fuehre_phasen_aus(phasen: List[Phase],
                            budget: float = STANDARD_BUDGET_SEK) -> Startergebnis:
    """Führt die Phasen nacheinander aus, bis das Budget aufgebraucht ist.

    Eine Phase, die wirft, stoppt die übrigen nicht — ein kaputter Seed darf
    nicht den Scheduler mitreißen. Eine Phase, für die keine Zeit mehr war,
    erscheint unter ``ausgefallen`` und nicht als „übersprungen": Sie hat es
    nicht versucht, und das ist etwas anderes als ein Fehlschlag.
    """
    ergebnis = Startergebnis()
    beginn = time.monotonic()

    with ThreadPoolExecutor(max_workers=1) as pool:
        loop = asyncio.get_event_loop()

        for index, phase in enumerate(phasen):
            verbleibend = budget - (time.monotonic() - beginn)
            if verbleibend <= 0:
                ergebnis.ausgefallen.extend(p.name for p in phasen[index:])
                break

            schritt = time.monotonic()
            try:
                fehler = await asyncio.wait_for(
                    loop.run_in_executor(pool, _gekapselt, phase.aufgabe),
                    timeout=verbleibend,
                )
            except asyncio.TimeoutError:
                # Der Thread läuft weiter und hält den Worker. Alles Weitere
                # käme ohnehin nicht mehr dran — deshalb hier abbrechen statt
                # die Folgephasen in dieselbe Falle laufen zu lassen.
                ergebnis.ausgefallen.extend(p.name for p in phasen[index:])
                logger.error(
                    f"  ⚠ {phase.name}: Zeitbudget erschöpft — diese und "
                    f"{len(phasen) - index - 1} weitere Phasen laufen nicht")
                break
            except Exception as e:  # noqa: BLE001
                ergebnis.gescheitert.append(phase.name)
                logger.warning(f"  ⚠ {phase.name} unerwartet: {type(e).__name__}: {e}")
                continue

            dauer = time.monotonic() - schritt
            if fehler is None:
                ergebnis.gelaufen.append(phase.name)
                logger.info(f"  ✓ {phase.name} ({dauer:.1f}s)")
            else:
                ergebnis.gescheitert.append(phase.name)
                logger.warning(f"  ⚠ {phase.name} Fehler: {fehler}")

    ergebnis.dauer = time.monotonic() - beginn
    return ergebnis


def _gekapselt(aufgabe: Callable[[], None]):
    """Führt eine Aufgabe aus und gibt ihre Ausnahme zurück, statt sie zu werfen."""
    try:
        aufgabe()
        return None
    except Exception as ex:  # noqa: BLE001
        return ex

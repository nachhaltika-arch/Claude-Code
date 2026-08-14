"""Zwei Grenzen für die Kosten des Projekt-Assistenten — Entscheidung 4.1.

* **Je Projekt** ein Euro-Budget, orientiert an den 50 €, die in
  `Project.ai_tool_costs` ohnehin im Margenmodell stehen. Der Assistent nimmt
  davon einen Teil in Anspruch, nicht das Ganze — es hängen noch andere
  KI-Aufrufe an einem Projekt.
* **Je Nutzer und Tag** eine Anzahl Anfragen. Schützt gegen einen einzelnen
  Nutzer, der das Projektbudget in einer Sitzung aufbraucht.

Beim Erreichen erscheint ein freundlicher Hinweis, kein Fehler: Der Nutzer hat
nichts falsch gemacht, und ein Weg nach vorn (Team fragen, morgen weiter) steht
dabei.

Die Werte stehen in der Umgebung, nicht im Code — § 4.1 verlangt das
ausdrücklich.
"""
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, Optional


def _zahl_aus_umgebung(name: str, standard: float) -> float:
    try:
        wert = float(os.getenv(name, "") or standard)
    except ValueError:
        return standard
    return wert if wert > 0 else standard


# Anteil am kalkulierten KI-Budget eines Projekts. Bewusst nicht die vollen
# 50 € — Audit, Sitemap, Wireframe und Blockerzeugung zahlen aus demselben Topf.
GRENZE_PROJEKT_EURO = _zahl_aus_umgebung("ASSISTENT_BUDGET_PROJEKT_EURO", 15.0)
GRENZE_NUTZER_PRO_TAG = int(_zahl_aus_umgebung("ASSISTENT_GRENZE_NUTZER_TAG", 60))

# Ab hier wird gewarnt, ohne zu sperren. Ein Hinweis vor der Wand ist mehr wert
# als die Wand.
WARNSCHWELLE = 0.8

# Preise je Million Token. Stand 2026-08; wenn sie sich ändern, ändert sich hier
# eine Zahl und nicht die Logik.
PREIS_EINGABE_PRO_MIO = _zahl_aus_umgebung("ASSISTENT_PREIS_EINGABE_MIO", 3.0)
PREIS_AUSGABE_PRO_MIO = _zahl_aus_umgebung("ASSISTENT_PREIS_AUSGABE_MIO", 15.0)


@dataclass(frozen=True)
class Verbrauch:
    """Was bisher verbraucht wurde."""

    projekt_euro: float = 0.0
    nutzer_anfragen_heute: int = 0


@dataclass(frozen=True)
class Entscheidung:
    """Darf gefragt werden — und was dem Nutzer dazu gesagt wird."""

    erlaubt: bool
    hinweis: str = ""


def kosten_fuer(eingabe_tokens: int, ausgabe_tokens: int) -> float:
    """Was ein Aufruf gekostet hat, in Euro."""
    return round(
        eingabe_tokens / 1_000_000 * PREIS_EINGABE_PRO_MIO
        + ausgabe_tokens / 1_000_000 * PREIS_AUSGABE_PRO_MIO,
        6,
    )


def anfragen_heute(zeitstempel: Iterable[datetime],
                   jetzt: Optional[datetime] = None) -> int:
    """Wie viele der Anfragen auf den heutigen Tag fallen."""
    jetzt = jetzt or datetime.now(timezone.utc)
    return sum(1 for z in zeitstempel if z.date() == jetzt.date())


def darf_fragen(verbrauch: Verbrauch) -> Entscheidung:
    """Die Entscheidung vor dem Aufruf — mit dem Satz, der dem Nutzer erscheint."""
    if verbrauch.projekt_euro >= GRENZE_PROJEKT_EURO:
        return Entscheidung(False, (
            "Für dieses Projekt ist der Assistent vorerst ausgeschöpft. "
            "Schreiben Sie Ihre Frage gern dem Team — wir antworten persönlich."))

    if verbrauch.nutzer_anfragen_heute >= GRENZE_NUTZER_PRO_TAG:
        return Entscheidung(False, (
            "Sie haben den Assistenten heute schon ausgiebig genutzt. "
            "Ab morgen steht er wieder bereit — dringende Fragen beantwortet "
            "das Team jederzeit."))

    if verbrauch.projekt_euro >= GRENZE_PROJEKT_EURO * WARNSCHWELLE:
        return Entscheidung(True, (
            "Hinweis: Der Assistent ist für dieses Projekt bald ausgeschöpft."))

    return Entscheidung(True)

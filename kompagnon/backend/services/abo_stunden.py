"""Die Pflegeachse der Zeiterfassung — Stunden je Monat und Betrieb (L-101).

**Der Anlass.** ABO-PRO (149 €/Mon.) sagt zwei Stunden Änderungen **je Monat
und Kunde** zu. Die vorhandene Erfassung zählt je **Projekt und Bauphase** —
das ist die Herstellung, nicht die Pflege, und ein Abo hat gar kein Projekt,
gegen das gebucht würde. Der Eintrag L-101 sagt es genau: Es fehlt nicht das
Werkzeug, es fehlt die **Achse**.

**Warum dieselbe Tabelle** (Entscheidung David, 31.08.2026): Es ist derselbe
Vorgang — jemand hat gearbeitet und trägt Stunden ein. Zwei Tabellen hätten
zwei Eingaben, zwei Auswertungen und irgendwann einen Abgleich gebraucht;
dieses Muster hat hier schon zweimal Zeit gekostet.

**Was dieses Modul ausdrücklich noch nicht kann: sagen, wie viel übrig ist.**
Dafür müsste am Betrieb stehen, **welches** Abo gilt, und ein solches
Vertragsobjekt gibt es nicht — es ist der zweite Teil von L-101 und eine
Entscheidung, keine Programmierarbeit. Bis dahin liefert dieses Modul den
**Verbrauch** und nennt ihn so. Eine Restzahl auszurechnen, indem man ein Abo
annimmt, wäre eine Zusage auf einer Vermutung.

Der Satz aus dem Eintrag bleibt gültig, ist aber jetzt eingelöst: **Kein Abo
verkaufen, bevor die Stunden zählbar sind.** Zählbar sind sie ab hier.
"""
import re
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from database import Lead, TimeTracking

#: Das Kontingent von ABO-PRO, in Stunden je Monat und Kunde.
#:
#: Steht hier als **benannter Wert** und nicht als 2.0 in einer Rechnung —
#: aber bewusst **ohne** Funktion, die ihn verrechnet: Solange nicht an einem
#: Betrieb steht, welches Abo gilt, wäre jede Restberechnung geraten. Wer das
#: Vertragsobjekt baut, findet die Zahl hier.
KONTINGENT_ABO_PRO_STUNDEN = 2.0

#: ABO-BAS sagt keine Änderungsstunden zu — Inhaltspflege, Sicherungen,
#: Quartals-Re-Audit. Ausdrücklich genannt, damit „kein Eintrag" nicht mit
#: „nicht erhoben" verwechselt wird.
KONTINGENT_ABO_BAS_STUNDEN = 0.0

_MONAT = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


class AboZeitFehler(ValueError):
    """Eine Eingabe, die so nicht verbucht werden darf."""


def monat_von(zeitpunkt: Optional[datetime] = None) -> str:
    """Der Abrechnungsmonat als `YYYY-MM` — der Vorschlag, nicht die Wahrheit.

    Wer am 2. September Stunden vom August einträgt, überschreibt ihn. Deshalb
    ist der Monat an der Zeile **gesetzt** und nicht aus `logged_at`
    abgeleitet: Abgeleitet verfiele das Kontingent des Vormonats still.
    """
    return (zeitpunkt or datetime.utcnow()).strftime("%Y-%m")


def pruefe_monat(monat: str) -> str:
    """`YYYY-MM`, sonst Fehler.

    Ein freier Text hier hiesse, dass „2026-8", „Aug 26" und „2026-08"
    nebeneinander in der Spalte stehen — und dann summiert jede Auswertung
    einen Teil des Monats.
    """
    monat = (monat or "").strip()
    if not _MONAT.match(monat):
        raise AboZeitFehler(
            f"Abrechnungsmonat muss die Form JJJJ-MM haben, nicht {monat!r}.")
    return monat


def eintragen(db: Session, *, lead_id: int, stunden: float, wer: str,
              taetigkeit: str = "", monat: Optional[str] = None) -> TimeTracking:
    """Pflegestunden für einen Betrieb verbuchen.

    Wirft `AboZeitFehler`, wenn die Zeile nicht eindeutig verbuchbar wäre —
    der Aufrufer macht daraus die Antwort für den Bildschirm.
    """
    if (stunden or 0) <= 0:
        # Dieselbe Regel wie auf der Projektachse: Null ist ein Fehlklick,
        # negativ ist eine Korrektur — und die gehört besprochen, nicht
        # stillschweigend verbucht.
        raise AboZeitFehler("Bitte eine Stundenzahl größer als 0 angeben.")

    if not db.query(Lead).filter(Lead.id == lead_id).first():
        raise AboZeitFehler("Betrieb nicht gefunden.")

    eintrag = TimeTracking(
        project_id=None,
        phase=None,
        lead_id=lead_id,
        abrechnungsmonat=pruefe_monat(monat or monat_von()),
        logged_by=wer,
        hours=float(stunden),
        activity_description=(taetigkeit or "")[:255],
    )
    db.add(eintrag)
    db.commit()
    db.refresh(eintrag)
    return eintrag


def monatsstand(db: Session, *, lead_id: int, monat: str) -> dict:
    """Was in diesem Monat für diesen Betrieb erfasst ist.

    **`verbraucht`, nicht `verbleibend`** — siehe Kopftext: Welches Abo gilt,
    steht an keinem Betrieb, und eine Restzahl auf einer Annahme wäre eine
    Zusage, die niemand gegeben hat.
    """
    monat = pruefe_monat(monat)
    zeilen = (db.query(TimeTracking)
                .filter(TimeTracking.lead_id == lead_id,
                        TimeTracking.abrechnungsmonat == monat)
                .order_by(TimeTracking.logged_at.desc(), TimeTracking.id.desc())
                .all())

    return {
        "monat": monat,
        "verbraucht": round(sum(z.hours or 0 for z in zeilen), 2),
        "eintraege": [{
            "id": z.id,
            "stunden": float(z.hours or 0),
            "wer": z.logged_by or "",
            "taetigkeit": z.activity_description or "",
            "erfasst_am": z.logged_at.isoformat() if z.logged_at else None,
        } for z in zeilen],
        # Der offene Rest von L-101, als Feld und nicht als Fussnote: Wer
        # diesen Bildschirm baut, sieht sofort, warum keine Restzahl kommt.
        "abo": None,
        "hinweis": ("Welches Abo für diesen Betrieb gilt, ist nirgends "
                    "hinterlegt — deshalb steht hier der Verbrauch und keine "
                    "Restzahl (L-101)."),
    }

"""
Wann eine automatische Erinnerung faellig ist.

**Warum es diese Datei gibt.** Am 17.08.2026 stellte sich heraus, dass
``job_check_missing_materials`` die Material-Erinnerung an jedes Projekt in
``phase_2`` schickte, dessen Start mehr als fuenf Tage her war — und zwar
**jeden Morgen erneut**:

    projects = db.query(Project).filter(Project.status == "phase_2").all()
    for project in projects:
        if days_since_start > 5:
            _send_phase_email(project.id, "material_reminder")

Keine Sperre, kein Nachschlagen, kein Ende. Ein Betrieb bekam die Mail ueber
135 Tage taeglich. Der Briefing-Job zwanzig Zeilen weiter unten hatte die
Sperre — er schlug in ``communications`` nach, ob die Vorlage schon einmal
rausging. Zwei Jobs derselben Bauart, einer richtig, einer nicht.

Deshalb steht die Entscheidung jetzt hier, an **einer** Stelle und als reine
Funktion: ohne Datenbank, ohne Uhrzeit, ohne Versand. Damit laesst sie sich
pruefen — die alte Fassung liess sich nur im Betrieb beobachten, und dort hat
sie vier Monate lang niemand bemerkt.

Die Regel dahinter: **Eine automatische Mail geht je Stufe genau einmal raus.**
Wer danach nicht reagiert, ist kein Fall fuer mehr Mails, sondern fuer einen
Menschen — dafuer legt ``job_check_overdue_phases`` ein Ticket an.
"""
from typing import Iterable, Optional, Sequence, Tuple

# Eine Stufe ist (Tage seit Projektstart, Vorlagenschluessel).
# Aufsteigend notiert, ausgewertet wird von oben nach unten.
Stufen = Sequence[Tuple[int, str]]

# Material: eine Erinnerung, dann uebernimmt der Mensch.
# Es gibt nur eine Vorlage (`automations/email_templates.py`), also auch nur
# eine Stufe. Weitere liessen sich hier eintragen — sie brauchen dann aber je
# eine eigene Vorlage, sonst versendet `get_template` seinen Rueckfalltext.
MATERIAL_STUFEN: Stufen = (
    (5, "material_reminder"),
)

# Briefing: sanft, klar, letzte Erinnerung — dann Schluss.
BRIEFING_STUFEN: Stufen = (
    (3,  "briefing_reminder_day_3"),
    (7,  "briefing_reminder_day_7"),
    (14, "briefing_reminder_day_14"),
)


def faellige_erinnerung(
    tage_seit_start: Optional[int],
    stufen: Stufen,
    bereits_gesendet: Iterable[str],
) -> Optional[str]:
    """Welche Vorlage ist jetzt faellig — oder ``None``.

    Ausgewertet wird die **hoechste erreichte** Stufe. Ist die schon
    verschickt, passiert nichts; es faellt bewusst niemand auf eine
    niedrigere Stufe zurueck, sonst begaenne die Staffel von vorn.

    :param tage_seit_start: Laufzeit in Tagen. ``None`` (kein Startdatum)
        und negative Werte (Start in der Zukunft) loesen nichts aus.
    :param stufen: aufsteigend nach Tagen, siehe ``MATERIAL_STUFEN``.
    :param bereits_gesendet: Vorlagenschluessel, die dieses Projekt schon
        bekommen hat. Liste oder Menge, wird nicht veraendert.
    """
    if tage_seit_start is None or tage_seit_start < 0:
        return None

    schon_da = set(bereits_gesendet)

    for schwelle, vorlage in sorted(stufen, reverse=True):
        if tage_seit_start >= schwelle:
            return None if vorlage in schon_da else vorlage

    return None

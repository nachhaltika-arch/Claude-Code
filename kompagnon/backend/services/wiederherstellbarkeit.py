"""Wäre eine Wiederherstellung vollständig? (L-11)

**Der Punkt, den `docs/sicherung-und-wiederherstellung.md` am 19.08.2026
gemacht hat:** Eine Datenbanksicherung rettet den Betrieb **nicht**. Drei
Dinge gehören dazu, und nur eines liegt in der Datenbank — dazu der
Datenträger und die Schlüssel. Wer die Datenbank zurückspielt und die
Schlüssel nicht hat, bekommt einen laufenden Dienst mit unlesbaren
Zugangsdaten: kein Fehler, keine Meldung, nur leere Felder, wo
Kundenzugänge stehen sollten.

**Was fehlte, war nicht die Erkenntnis, sondern die Messung.** Geprüft wurden
die Schlüssel bisher erst beim **Zugriff** — `_get_fernet()` wirft, wenn
`CREDENTIALS_KEY` fehlt, und der Aufrufer bekommt einen Fehler. Bis dahin
sieht alles gesund aus, `/health` eingeschlossen.

**Es gab sogar eine Funktion dafür.** `_fernet_available()` stand in
`routers/projects.py` und beantwortete genau das. Sie wurde nie aufgerufen und
fiel am 23.08. beim Aufräumen heraus — mit der Begründung, der Startbericht
beantworte es inzwischen. Diese Begründung war falsch: `startup_missing`
listet ausgefallene Startphasen, keine fehlenden Schlüssel. Die Funktion war
nicht überflüssig, sie war **nicht angeschlossen**.

**Warum die Auskunft nicht nach `/health` gehört:** Der Endpunkt ist ohne
Anmeldung erreichbar. „CREDENTIALS_KEY fehlt" wäre dort die Auskunft, welcher
Schutz gerade nicht greift — eine Einladung. Sie steht deshalb im
Startprotokoll und hinter einer Anmeldung.
"""
import logging
import os

logger = logging.getLogger(__name__)

# (Name, wofür er gebraucht wird — und was ohne ihn verloren ist)
SCHLUESSEL = (
    ("CREDENTIALS_KEY",
     "Die im Safe hinterlegten Kundenzugaenge (Hosting, CMS, Domainverwaltung) "
     "sind ohne ihn nach einer Wiederherstellung nicht mehr zu entschluesseln — "
     "die Zeilen stehen da, der Inhalt ist verloren."),
    ("CMS_ENCRYPTION_KEY",
     "Die gespeicherten CMS-Verbindungen der Kundenseiten sind ohne ihn "
     "unlesbar; jede Verbindung muesste neu eingerichtet werden."),
)


def schluessel_bericht() -> dict:
    """Welche Wiederherstellungs-Schlüssel sind gesetzt — und was fehlt ohne sie.

    Gibt **nie** einen Schlüsselwert zurück, auch nicht gekürzt. Ein Bericht
    über Geheimnisse, der Geheimnisse enthält, ist selbst das Leck; genau so
    lagen am 15.08.2026 die Datenbank-Zugangsdaten auf `/info`.
    """
    eintraege = []
    for name, ohne_ihn in SCHLUESSEL:
        wert = os.getenv(name, "").strip()
        eintraege.append({
            "name": name,
            "gesetzt": bool(wert),
            "ohne_ihn": ohne_ihn,
        })

    return {
        "schluessel": eintraege,
        "vollstaendig": all(e["gesetzt"] for e in eintraege),
    }


def beim_start_melden() -> None:
    """Einmal beim Hochfahren ins Protokoll — dort sieht es jemand.

    **Warum als eigene Meldung und nicht als Startphase:** Ein fehlender
    Schluessel ist kein Startfehler. Der Dienst laeuft, alles Uebrige geht;
    nur eine Wiederherstellung waere unvollstaendig. Ihn unter die
    ausgefallenen Phasen zu mischen hiesse, eine Ampel rot zu faerben, die
    fuer etwas anderes steht.
    """
    bericht = schluessel_bericht()
    if bericht["vollstaendig"]:
        logger.info("✓ Wiederherstellungs-Schluessel vollstaendig (%d von %d)",
                    len(bericht["schluessel"]), len(SCHLUESSEL))
        return

    fehlend = [e["name"] for e in bericht["schluessel"] if not e["gesetzt"]]
    logger.warning(
        "⚠ Wiederherstellung waere unvollstaendig — nicht gesetzt: %s. "
        "Der Betrieb laeuft; aber wer die Datenbank zurueckspielt, bekommt "
        "unlesbare Zugangsdaten. Siehe docs/sicherung-und-wiederherstellung.md",
        ", ".join(fehlend),
    )
    for eintrag in bericht["schluessel"]:
        if not eintrag["gesetzt"]:
            logger.warning("  · %s — %s", eintrag["name"], eintrag["ohne_ihn"])

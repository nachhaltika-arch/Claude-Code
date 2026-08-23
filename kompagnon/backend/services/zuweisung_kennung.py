"""Zieht Altzeilen der Akademie-Zuweisung auf die Benutzer-Kennung nach.

L-54. Das Kundenblatt rief `/api/academy/customer/{id}/…` mit der
**Betriebs-ID**, waehrend die Akademie alles andere ueber die **Benutzer-ID**
fuehrt (`AcademyProgress.user_id`, `AcademyCertificate.user_id`). Seit dem
19.08.2026 loest der Endpunkt beim Schreiben auf; neue Zeilen tragen die
Benutzer-ID. Die alten nicht.

Folgenlos war das nur, solange **niemand** die Zuweisung abfragte — und genau
das hat sich an demselben Tag geaendert. Eine Altzeile traegt damit eine Zahl,
unter der niemand sucht, und der zugewiesene Kurs bliebe unsichtbar.

Der Nachtrag schreibt nur um, wo er sicher ist:

- Die Zahl ist eine Betriebsnummer mit bekanntem Kunden **und** keine gueltige
  Benutzernummer → umschreiben
- Beides trifft zu → **liegen lassen** und melden. Raten waere hier schlimmer
  als nichts tun: Die zwei Zahlenraeume laufen unabhaengig, und ein falsch
  geratener Eintrag schaltet einem fremden Betrieb etwas frei
- Die Zahl ist schon eine Benutzernummer → nichts zu tun
- Die Zahl gehoert zu **niemandem** → liegen lassen und melden (`verwaist`)

**Die vierte Klasse kam am 2026-08-23 dazu, nach einer Messung am produktiven
Bestand.** Der Befund L-54 sagte, offen bleibe „genau der zweideutige Rest".
Produktiv gibt es davon **keine einzige** Zeile — dafuer tragen **beide**
vorhandenen Zuweisungen (29.04.2026) die Nummer 78: Betrieb „Textilpflege
Noll", der kein Kundenkonto hat. Sie gingen hier stumm durch, weil ein
fehlender Kunde (`ziel is None`) in demselben `continue` landete wie der
harmlose Fall „ist schon eine Benutzernummer". Zwei von zwei produktiven
Zeilen fielen damit aus jedem Bericht — das Werkzeug mass enger als der
Bestand reicht.
"""
import logging
from typing import Dict

from sqlalchemy.exc import SQLAlchemyError

from database import AcademyCustomerAccess, AcademyModuleAccess, Lead, User

logger = logging.getLogger(__name__)


def _kunden_nach_betrieb(db) -> Dict[int, int]:
    """Betriebsnummer → Benutzernummer, fuer alle Kundenkonten."""
    return {
        lead_id: user_id
        for user_id, lead_id in
        db.query(User.id, User.lead_id)
        .filter(User.role == 'kunde', User.lead_id.isnot(None)).all()
    }


def kennungen_nachziehen(db) -> Dict[str, int]:
    """Schreibt eindeutige Altzeilen um. Gibt einen Bericht zurueck."""
    bericht = {"umgeschrieben": 0, "zweideutig": 0, "verwaist": 0, "geprueft": 0}

    nach_betrieb = _kunden_nach_betrieb(db)
    benutzernummern = {uid for (uid,) in db.query(User.id).all()}
    verwaiste = []

    for modell, feld in ((AcademyCustomerAccess, "customer_id"),
                         (AcademyModuleAccess, "customer_id")):
        for zeile in db.query(modell).all():
            bericht["geprueft"] += 1
            kennung = getattr(zeile, feld)

            ziel = nach_betrieb.get(kennung)

            if ziel is None:
                if kennung in benutzernummern:
                    # Zeigt schon auf einen Benutzer — nichts zu tun.
                    continue
                # **Niemand steht hinter dieser Zahl.** Weder ein Benutzer noch
                # ein Betrieb mit Zugang. Umschreiben laesst sich nichts, und
                # gesehen wird die Zuweisung auch von niemandem — aber
                # stillschweigend uebergehen heisst, dass sie nie jemand
                # aufraeumt. Genau das war bei den zwei produktiven Zeilen der
                # Fall.
                bericht["verwaist"] += 1
                verwaiste.append((modell.__tablename__, zeile.id, kennung))
                continue

            if ziel == kennung:
                continue

            if kennung in benutzernummern:
                # Die Zahl ist zugleich eine gueltige Benutzernummer. Welche
                # Bedeutung gemeint war, steht nirgends — also nichts tun.
                bericht["zweideutig"] += 1
                logger.warning(
                    "Zuweisung %s#%s: Kennung %s ist Betriebs- **und** "
                    "Benutzernummer — nicht umgeschrieben",
                    modell.__tablename__, zeile.id, kennung,
                )
                continue

            setattr(zeile, feld, ziel)
            bericht["umgeschrieben"] += 1

    if bericht["umgeschrieben"]:
        db.commit()

    if verwaiste:
        _verwaiste_melden(db, verwaiste)

    return bericht


def _verwaiste_melden(db, verwaiste: list) -> None:
    """Jede verwaiste Zeile einzeln benennen — mit Betriebsnamen, wo es einen gibt.

    Eine Kennung allein hilft beim Aufraeumen nicht weiter. „78" sagt nichts,
    „78 = Textilpflege Noll, kein Kundenkonto" sagt, was zu entscheiden ist.
    Der Name wird in **einer** Abfrage geholt, nicht je Zeile.
    """
    kennungen = {k for _, _, k in verwaiste}
    namen = {
        lid: name for lid, name in
        db.query(Lead.id, Lead.company_name).filter(Lead.id.in_(kennungen)).all()
    }

    for tabelle, zeilen_id, kennung in verwaiste:
        herkunft = (f"Betrieb {kennung} „{namen[kennung]}\" ohne Kundenkonto"
                    if kennung in namen else
                    f"Kennung {kennung} gehoert weder zu einem Betrieb noch zu "
                    f"einem Benutzer")
        logger.warning("Zuweisung %s#%s verwaist — %s", tabelle, zeilen_id, herkunft)


def nachziehen_beim_start() -> None:
    """Startphase — eigene Sitzung, Bericht ins Protokoll."""
    from database import SessionLocal

    db = SessionLocal()
    try:
        bericht = kennungen_nachziehen(db)
    except SQLAlchemyError as e:  # noqa: BLE001
        db.rollback()
        logger.warning("Kennungs-Nachtrag uebersprungen: %s", e)
        return
    finally:
        db.close()

    if bericht["umgeschrieben"] or bericht["zweideutig"] or bericht["verwaist"]:
        logger.info(
            "✓ Akademie-Zuweisungen nachgezogen — %d umgeschrieben, "
            "%d zweideutig liegen gelassen, %d verwaist (von %d)",
            bericht["umgeschrieben"], bericht["zweideutig"],
            bericht["verwaist"], bericht["geprueft"],
        )


def zweideutige_kennungen(db) -> set:
    """Kennungen, bei denen nicht feststeht, was gemeint war.

    Eine Zahl ist zweideutig, wenn sie **zugleich** eine gueltige
    Benutzernummer ist und eine Betriebsnummer, hinter der ein **anderes**
    Konto steht. Dann laesst sich aus der Zeile nicht ablesen, wer gemeint
    war — und `kennungen_nachziehen` laesst sie deshalb bewusst liegen.

    **Wozu die Liste ausserhalb des Nachtrags gebraucht wird.** Bis zum
    22.08.2026 stand im Befund: „Heute ungefaehrlich, weil kein einziger Kurs
    gesperrt ist. Gefaehrlich wird es mit dem ersten gesperrten Kurs."
    Darauf zu warten ist die Luecke — der Lehrplan aus L-60 wird Kurse
    sperren. Seitdem uebergeht der Lesepfad der Akademie diese Kennungen:
    Eine Zuweisung, die zweideutig ist, schaltet **nichts** frei.

    Die sichere Richtung ist die: Jemandem einen Kurs vorzuenthalten, den er
    haben sollte, faellt auf und ist in einem Griff behoben. Ihn jemandem zu
    zeigen, der ihn nicht sehen darf, faellt nicht auf.
    """
    nach_betrieb = _kunden_nach_betrieb(db)
    if not nach_betrieb:
        return set()

    benutzernummern = {uid for (uid,) in db.query(User.id).all()}

    return {
        kennung for kennung, ziel in nach_betrieb.items()
        if kennung in benutzernummern and ziel != kennung
    }

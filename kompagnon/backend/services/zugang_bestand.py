# -*- coding: utf-8 -*-
"""Was ein neuer Zugang vom Betrieb erbt — und was nicht.

**Der Fall, den man vergisst (25.08.2026).** Ein Betrieb bekommt im Mai
seinen Kurs freigeschaltet. Im August kommt die Bueroleitung dazu. Ohne
diese Datei meldet sie sich an und findet eine leere Akademie: Die
Freischaltung steht am **Konto** des Inhabers, und sie war schon
geschrieben, bevor es das zweite Konto gab.

**Die Trennlinie ist Berechtigung gegen Leistung.**

- Was der Betrieb **darf**, erbt der neue Zugang: freigeschaltete Kurse und
  Module. Sie gelten dem Betrieb; dass sie an einer Benutzernummer haengen,
  ist nur die Bauart der Tabelle.
- Was ein Mensch **getan** hat, erbt er nicht: Fortschritt, bestandene
  Tests, Zertifikate. Ein geerbtes Zertifikat waere eine Urkunde ueber
  etwas, das dieser Mensch nie gemacht hat — und die Akademie fuehrt zu
  Nachweisen, die vorgezeigt werden.
"""
import logging

logger = logging.getLogger(__name__)

#: (Modell, Spalte des Gegenstands) — beide Berechtigungstabellen der
#: Akademie. Wer eine dritte dazunimmt, traegt sie hier ein; sonst erbt der
#: naechste Zugang sie nicht, und niemand merkt es.
BERECHTIGUNGEN = ("AcademyCustomerAccess", "course_id"), ("AcademyModuleAccess", "module_id")


def bestand_uebernehmen(db, lead_id: int, neuer_user_id: int) -> dict:
    """Dem neuen Zugang geben, was die uebrigen Zugaenge des Betriebs haben.

    Gibt je Tabelle die Zahl der uebernommenen Zeilen zurueck — der Aufrufer
    protokolliert sie, damit eine stille Null auffaellt.
    """
    from datetime import datetime

    from database import User
    import modelle_akademie

    geschwister = [z[0] for z in db.query(User.id).filter(
        User.lead_id == lead_id, User.id != neuer_user_id).all()]
    if not geschwister:
        return {}

    uebernommen = {}
    for name, feld in BERECHTIGUNGEN:
        modell = getattr(modelle_akademie, name, None)
        if modell is None:                       # Modell umbenannt oder weg
            logger.warning("Berechtigungstabelle %s gibt es nicht mehr", name)
            continue

        vorhanden = {z[0] for z in db.query(getattr(modell, feld)).filter(
            modell.customer_id == neuer_user_id).all()}
        gegenstaende = {z[0] for z in db.query(getattr(modell, feld)).filter(
            modell.customer_id.in_(geschwister)).all()} - vorhanden

        for gegenstand in sorted(gegenstaende):
            db.add(modell(customer_id=neuer_user_id,
                          assigned_at=datetime.utcnow(),
                          **{feld: gegenstand}))
        uebernommen[name] = len(gegenstaende)

    db.commit()
    return uebernommen

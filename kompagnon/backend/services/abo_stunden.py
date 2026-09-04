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

**Die Restzahl kam am 01.09.2026 dazu — sie steht aber weiter unter einer
Bedingung.** Bis dahin fehlte das Vertragsobjekt: Am Betrieb stand nicht,
**welches** Abo gilt, und eine Restzahl auszurechnen, indem man eines annimmt,
wäre eine Zusage auf einer Vermutung gewesen. Jetzt gibt es
`services/abo_vertrag.py`, und `monatsstand()` nennt die Restzahl — **genau
dann, wenn für diesen Monat ein Vertrag hinterlegt ist**. Ohne Vertrag bleibt
es bei Verbrauch und Hinweis; die Zurückhaltung ist nicht weggefallen, sie hat
nur einen Ausweg bekommen.

Der Satz aus dem Eintrag bleibt gültig, ist aber jetzt eingelöst: **Kein Abo
verkaufen, bevor die Stunden zählbar sind.** Zählbar sind sie ab hier.
"""
import re
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from database import Lead, TimeTracking

#: **Die Quelle ist `docs/produkte/abo-und-geo.md`, nicht das Lagebild.**
#:
#: Am 01.09.2026 korrigiert, und der Fehler war teuer in beide Richtungen: Die
#: Zahlen hier stammten aus dem Fließtext von L-101 („Pro zusätzlich zwei
#: Stunden", „BAS sagt keine Änderungsstunden zu"). Im Produktdatenblatt steht
#: etwas anderes — Position 5 und 8 des Leistungsverzeichnisses:
#:
#: * ABO-BAS: **Inhaltsänderungen bis 30 Minuten** je Monat → 0,5 h
#: * ABO-PRO: **Inhaltsänderungen bis 90 Minuten (statt 30)** → 1,5 h
#:
#: „statt 30", nicht „zusätzlich" — aus 30 + 90 wurden fälschlich zwei
#: Stunden. Mit 0,0 für BAS wäre **jede** Minute eines Basic-Kunden als
#: Überschreitung erschienen, und wir hätten Arbeit berechnet, die im Preis
#: steht; mit 2,0 für PRO hätten wir jeden Monat eine halbe Stunde
#: verschenkt.
#:
#: **Ein Summentext ist keine Produktdefinition.** Wer die Zahl braucht, liest
#: das Datenblatt.
KONTINGENT_ABO_PRO_STUNDEN = 1.5
KONTINGENT_ABO_BAS_STUNDEN = 0.5

#: Der Nettopreis je Monat, in Cent — Quelle wie oben.
#:
#: **Beide sind im Datenblatt als „⚠️ Annahme" gekennzeichnet.** Sie stehen
#: hier trotzdem, weil eine Rechnung eine Zahl braucht; wer sie ändert, ändert
#: sie an dieser einen Stelle. Solange die Kennzeichnung dort steht, ist jede
#: Abrechnung damit eine Annahme — und der Abrechnungslauf sagt das auch.
PREIS_ABO_BAS_NETTO_CENT = 7900
PREIS_ABO_PRO_NETTO_CENT = 14900

#: 19 %, nicht 7 %. Das Buch ist ermäßigt (Anlage 2 UStG), eine Dienstleistung
#: nicht — der Produkteditor stellt 19 % voreingestellt richtig ein, und für
#: das Buch war es ausdrücklich die Ausnahme (BUCH-12).
STEUERSATZ_ABO = 19.0


def preis_netto_cent(produkt: str) -> int:
    """Der Monatspreis eines Pflege-Abos, netto und in Cent.

    Unbekannte Kennungen bekommen den Basic-Preis — dieselbe Regel wie in
    `abo_abrechnung._preis_und_kontingent`, aus dem diese Funktion stammt.
    Sie ist bewusst nicht streng: Der Aufruf steht in einer Aufstellung, und
    eine Ausnahme dort brächte den ganzen Monatslauf zu Fall.
    """
    if produkt == "ABO-PRO":
        return PREIS_ABO_PRO_NETTO_CENT
    return PREIS_ABO_BAS_NETTO_CENT


def preis_brutto_cent(produkt: str) -> int:
    """Was tatsächlich abgebucht bzw. berechnet wird.

    **Warum das hier steht und nicht an zwei Stellen gerechnet wird
    (04.09.2026).** Die Umrechnung netto → brutto stand bis dahin inmitten
    von `abo_abrechnung.offene_posten`. Mit der Entscheidung, das Pflege-Abo
    über Stripe laufen zu lassen, braucht sie ein zweiter Aufrufer — und ein
    Abonnement, das einen anderen Betrag abbucht als die Aufstellung meldet,
    fällt niemandem auf, bis ein Kunde nachrechnet.

    Gerundet wird auf den Steuerbetrag, nicht auf die Summe: So steht in
    Rechnung und Abbuchung dieselbe Zerlegung.
    """
    netto = preis_netto_cent(produkt)
    return netto + int(round(netto * STEUERSATZ_ABO / 100))

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

    verbraucht = round(sum(z.hours or 0 for z in zeilen), 2)

    # **Seit dem 01.09.2026 gibt es das Vertragsobjekt** (L-101, zweite
    # Hälfte). Hier stand vorher fest `"abo": None` mit dem Hinweis, dass
    # nirgends steht, welches Abo gilt. Jetzt steht es — und wo es das
    # ausnahmsweise nicht tut, bleibt es bei genau dieser Zurückhaltung:
    # `abo_vertrag.stand()` gibt dann wieder `None` und einen Hinweis zurück.
    #
    # **Der Import steht hier unten und nicht im Kopf**, weil `abo_vertrag`
    # seinerseits die Kontingente aus diesem Modul liest — im Kopf wäre es ein
    # Ring, und der bricht beim Laden.
    from services import abo_vertrag

    return {
        "monat": monat,
        "verbraucht": verbraucht,
        "eintraege": [{
            "id": z.id,
            "stunden": float(z.hours or 0),
            "wer": z.logged_by or "",
            "taetigkeit": z.activity_description or "",
            "erfasst_am": z.logged_at.isoformat() if z.logged_at else None,
        } for z in zeilen],
        **abo_vertrag.stand(db, lead_id=lead_id, monat=monat,
                            verbraucht=verbraucht),
    }

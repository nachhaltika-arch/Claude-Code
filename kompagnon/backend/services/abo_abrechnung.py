# -*- coding: utf-8 -*-
"""Was diesen Monat zu berechnen ist — die Pflege-Abos (L-101).

**Die Entscheidung: per Rechnung, nicht per Abbuchung** (David, 01.09.2026).
Damit ist der letzte offene Teil von L-101 beantwortet. Stripe kann
Abonnements; das System nutzt sie nicht, und es muss auch keine
Einzugsermaechtigung verwalten.

**Was das Produktdatenblatt sagt und was David entschieden hat, geht
auseinander — und das gehoert benannt.** `docs/produkte/abo-und-geo.md`
fuehrt unter Zahlungsbedingung **Z4: monatlich im Voraus, SEPA**. Entschieden
ist Rechnung. Der Code folgt der Entscheidung; das Datenblatt traegt einen
Vermerk. Zwei Papiere, die verschiedene Zahlungswege behaupten, sind im
Streitfall schlimmer als eines mit einem sichtbaren Widerspruch.

**Dieser Lauf stellt keine Rechnung aus.** Er sagt, **was** zu berechnen ist —
Betrieb, Abo, Monat, Betrag — und meldet es. Eine Rechnungsnummer ist
fortlaufend und laesst sich nicht still zuruecknehmen; `services/rechnung.py`
sagt es selbst: „Eine zweite Nummer fuer denselben Vorgang reisst eine Luecke
in den Kreis." Was einmal vergeben ist, steht in der Buchfuehrung. Deshalb
vergibt sie ein Mensch.

**Und die Preise sind noch Annahmen.** Im Datenblatt stehen 79 und 149 € mit
einem ausdruecklichen „⚠️ Annahme". Solange das so ist, sagt jede Aufstellung
aus diesem Modul es dazu — ein Betrag, den man fuer bestaetigt haelt, wandert
sonst in eine Rechnung.
"""
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

#: Art der Meldung — dieselbe wie beim Quartals-Re-Audit: eine Aufgabe mit
#: Termin, kein Ereignis eines Kunden.
ART = "faellig"
ZIEL = "/app/betriebe"

#: Der Vorbehalt, solange die Preise im Datenblatt als Annahme markiert sind.
#: `tests/test_abo_datenblatt.py` wird rot, wenn die Markierung dort
#: verschwindet — dann gehoert dieser Satz weg.
VORBEHALT = ("Die Monatspreise stehen im Produktdatenblatt noch als Annahme "
             "(79 € / 149 € netto). Vor dem Rechnungsdruck bestätigen.")


def _preis_und_kontingent(produkt: str):
    from services import abo_stunden

    if produkt == "ABO-PRO":
        return (abo_stunden.PREIS_ABO_PRO_NETTO_CENT,
                abo_stunden.KONTINGENT_ABO_PRO_STUNDEN)
    return (abo_stunden.PREIS_ABO_BAS_NETTO_CENT,
            abo_stunden.KONTINGENT_ABO_BAS_STUNDEN)


def offene_posten(db, monat: Optional[str] = None) -> list:
    """Was fuer diesen Monat zu berechnen ist — je laufendem Vertrag eine Zeile.

    **Die verbrauchten Stunden stehen dabei**, obwohl sie den Preis nicht
    aendern: Ein Abo ist eine Pauschale, und Mehrarbeit wird gesondert
    beauftragt. Wer die Rechnung schreibt, sieht so aber sofort, wo ueber das
    Kontingent hinaus gearbeitet wurde — genau das ist das Gespraech, das vor
    der Rechnung zu fuehren ist und nicht danach.
    """
    from database import Lead
    from modelle_abo import AboVertrag
    from services import abo_stunden, abo_vertrag

    monat = abo_stunden.pruefe_monat(monat or abo_stunden.monat_von())

    laufende = (db.query(AboVertrag)
                  .filter(AboVertrag.start_monat <= monat)
                  .filter((AboVertrag.end_monat.is_(None))
                          | (AboVertrag.end_monat >= monat))
                  .order_by(AboVertrag.lead_id)
                  .all())

    posten = []
    for vertrag in laufende:
        gueltig = abo_vertrag.gilt_im_monat(db, lead_id=vertrag.lead_id,
                                            monat=monat)
        if gueltig is None or gueltig.id != vertrag.id:
            continue

        netto, kontingent = _preis_und_kontingent(gueltig.produkt)
        steuer = int(round(netto * abo_stunden.STEUERSATZ_ABO / 100))
        stand = abo_stunden.monatsstand(db, lead_id=vertrag.lead_id, monat=monat)
        betrieb = db.query(Lead).filter(Lead.id == vertrag.lead_id).first()

        posten.append({
            "lead_id": vertrag.lead_id,
            "betrieb": (betrieb.company_name if betrieb else "") or f"#{vertrag.lead_id}",
            "produkt": gueltig.produkt,
            "monat": monat,
            "netto_cent": netto,
            "steuer_cent": steuer,
            "brutto_cent": netto + steuer,
            "steuersatz": abo_stunden.STEUERSATZ_ABO,
            "kontingent_stunden": kontingent,
            "verbraucht_stunden": stand["verbraucht"],
            "ueberzogen": stand.get("ueberzogen", False),
        })
    return posten


def summe_brutto_cent(posten: list) -> int:
    return sum(p["brutto_cent"] for p in posten)


def bereits_gemeldet(db, monat: str) -> bool:
    from database import Benachrichtigung

    return db.query(Benachrichtigung).filter(
        Benachrichtigung.art == ART,
        Benachrichtigung.titel.like(f"Abrechnung {monat}%")).first() is not None


def lauf(db, monat: Optional[str] = None) -> dict:
    """Die offenen Posten feststellen und einmal melden. Wirft nie."""
    from services.abo_stunden import monat_von, pruefe_monat
    from services.benachrichtigungen import melden_leise

    monat = pruefe_monat(monat or monat_von())
    posten = offene_posten(db, monat)
    ergebnis = {"monat": monat, "posten": len(posten),
                "summe_brutto_cent": summe_brutto_cent(posten),
                "gemeldet": False}

    if not posten:
        logger.info("Abo-Abrechnung %s: nichts zu berechnen", monat)
        return ergebnis

    if bereits_gemeldet(db, monat):
        logger.info("Abo-Abrechnung %s: schon gemeldet", monat)
        return ergebnis

    euro = ergebnis["summe_brutto_cent"] / 100
    ueberzogen = [p["betrieb"] for p in posten if p["ueberzogen"]]
    hinweis = (f"{len(posten)} Pflege-Abos, zusammen "
               f"{euro:.2f} € brutto. Die Rechnungen werden von Hand "
               f"gestellt — eine Rechnungsnummer ist fortlaufend und lässt "
               f"sich nicht zurücknehmen. {VORBEHALT}")
    if ueberzogen:
        # **Zuerst das, was Geld kostet.** Wer ueber sein Kontingent
        # gearbeitet hat, ist das Gespraech vor der Rechnung — nicht danach.
        hinweis = (f"Über dem Kontingent: {', '.join(ueberzogen)}. " + hinweis)

    melden_leise(db, art=ART,
                 titel=f"Abrechnung {monat} — {len(posten)} Pflege-Abos",
                 hinweis=hinweis, ziel=ZIEL)
    ergebnis["gemeldet"] = True
    logger.info("Abo-Abrechnung %s: %d Posten gemeldet", monat, len(posten))
    return ergebnis


def lauf_mit_eigener_sitzung() -> dict:
    from database import SessionLocal

    db = SessionLocal()
    try:
        return lauf(db)
    except Exception:                                   # noqa: BLE001
        logger.exception("Abo-Abrechnung: Lauf fehlgeschlagen")
        return {"monat": "", "posten": 0, "summe_brutto_cent": 0,
                "gemeldet": False}
    finally:
        db.close()

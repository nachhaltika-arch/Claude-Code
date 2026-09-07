# -*- coding: utf-8 -*-
"""Leistungsverzeichnis, Dazubuchen und Abrufe.

**Am 07.09.2026 aus `routers/portal.py` herausgeloest (L-25).** Die Datei war
auf 1.630 Zeilen gewachsen — doppelt ueber der Grenze —, und der groesste Teil
dieses Wachstums stammt aus den Sitzungen vom 06. und 07.09.: Kundenkonto,
Mitwirkung, Dazubuchen, Zugaenge. Geschnitten ist nach **Zustaendigkeit**,
nicht nach Groesse; das ist dasselbe Vorgehen wie bei `academy.py` am 23.08.

Der Router traegt denselben Praefix wie das Hauptmodul. Die Routen bleiben
Pfad fuer Pfad dieselben — gegengeprueft mit einer Zaehlung vor und nach dem
Schnitt.
"""
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel

from database import get_db
from routers.auth_router import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/portal", tags=["portal"])


@router.get("/leistungen")
def get_leistungen(user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Was der Kunde fuer sein Pflege-Abo bekommt — und was nicht.

    **Ohne laufendes Abo bleibt die Liste leer.** Kein Basic-Umfang als
    Vorgabe: Wer keinen Pflegevertrag hat, saehe sonst Zusagen, die niemand
    gegeben hat.
    """
    from services import abo_vertrag
    from services import leistungsverzeichnis as lz

    vertrag = abo_vertrag.laufender(db, user.lead_id) if user.lead_id else None
    produkt = vertrag.produkt if vertrag else None
    positionen = lz.fuer_produkt(produkt or "")

    return {
        "produkt": produkt,
        "seit": vertrag.start_monat if vertrag else None,
        # **Die Zusage getrennt herausgegeben**, obwohl sie auch in der Liste
        # steht. Der Support-Bildschirm braucht genau diesen einen Satz und
        # soll die zwoelf Positionen dafuer nicht durchsuchen muessen — sonst
        # entstuende dort eine zweite Auswahllogik.
        "reaktionszeit": lz.reaktionszeit(produkt or ""),
        "nicht_enthalten": list(lz.NICHT_ENTHALTEN) if produkt else [],
        "verfall_hinweis": lz.VERFALL_HINWEIS if produkt else "",
        "positionen": [{
            "nummer": p.nummer, "titel": p.titel, "warum": p.warum,
            "vertragstext": p.vertragstext, "frequenz": p.frequenz,
            "ort": p.ort, "zusage": p.zusage,
        } for p in positionen],
    }


# ══════════════════════════════════════════════════════════════════════
# Dazubuchen (Entwurf `kundenkonto-neu`)
# ══════════════════════════════════════════════════════════════════════
#
# **Die Buchung ist eine verbindliche Erklaerung, keine Automatik.** Ein
# Wechsel auf Pflege Pro heisst Lastschrift ueber 177,31 € im Monat. Den
# Vertrag zu wechseln **und** das Stripe-Abo umzustellen, waeren zwei
# Eingriffe ins Geld auf einen Klick, ohne dass ein Mensch dazwischen sieht.
# Was hier entsteht, ist die Erklaerung mit Zeitpunkt, Preis und Wortlaut;
# umgesetzt wird sie vom Innendienst.


class BuchungsWunsch(BaseModel):
    verstanden: bool = False
    notiz: str = ""


def _folgemonat() -> str:
    """Der kommende Monatserste, als `JJJJ-MM`.

    Der Wechsel gilt nie im laufenden Monat: `abo_vertrag.wechseln` weist das
    ausdruecklich ab, weil zwei Vertraege im selben Monat nicht
    unterscheidbar waeren.
    """
    jetzt = datetime.utcnow()
    jahr, monat = (jetzt.year + 1, 1) if jetzt.month == 12 else (jetzt.year, jetzt.month + 1)
    return f"{jahr}-{monat:02d}"


def _offene_buchungen(db: Session, lead_id: int) -> dict:
    try:
        return {z[0]: z[1] for z in db.execute(text(
            "SELECT kennung, gebucht_am FROM buchungen "
            "WHERE lead_id = :l AND zustand = 'offen'"), {"l": lead_id}).fetchall()}
    except Exception:  # noqa: BLE001 — ohne Tabelle gibt es keine Buchungen
        db.rollback()
        return {}


@router.get("/dazubuchen")
def get_dazubuchen(user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Was dieser Kunde dazubuchen kann — mit Grund, wo nicht."""
    from services import abo_vertrag
    from services import dazubuchen as dz
    from services.kundenzugang import darf_handeln, stufe_von

    vertrag = abo_vertrag.laufender(db, user.lead_id) if user.lead_id else None
    offen = _offene_buchungen(db, user.lead_id) if user.lead_id else {}

    return {
        # **Wer nur ansehen darf, sieht die Angebote — und keinen Knopf.**
        # Eine Preisliste ist keine Handlung; das Buchen ist eine.
        "darf_buchen": darf_handeln(stufe_von(user)),
        "ab_monat": _folgemonat(),
        "angebote": [{
            "kennung": a.kennung, "titel": a.titel, "nummer": a.nummer,
            "netto_cent": a.netto_cent, "brutto_cent": a.brutto_cent,
            "steuersatz": dz.STEUERSATZ, "einmalig": a.einmalig,
            "dazu": a.dazu, "punkte": list(a.punkte),
            "zahlung": a.zahlung, "laufzeit": a.laufzeit,
            "rechtstext": a.rechtstext, "danach": a.danach,
            "buchbar": buchbar and a.kennung not in offen,
            "gebucht": a.kennung in offen,
            "gebucht_am": (offen[a.kennung].isoformat()
                           if a.kennung in offen and offen[a.kennung] else None),
            "grund": grund,
        } for a, buchbar, grund in dz.buchbar_fuer(
            vertrag.produkt if vertrag else "", offen)],
    }


@router.post("/dazubuchen/{kennung}")
def buche_dazu(kennung: str, body: BuchungsWunsch,
               user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Ein Angebot verbindlich buchen.

    **Zwei Hürden vor dem Geld:** die Rechtestufe und die ausdrueckliche
    Bestaetigung, den Wortlaut gelesen zu haben. Ein Klick ist zu wenig fuer
    eine Lastschrift.

    **Der Wortlaut und der Preis von heute werden mitgeschrieben.** Aendern wir
    beides spaeter, belegt die Buchung sonst nur, dass jemand irgendwann
    geklickt hat — dieselbe Ueberlegung wie bei der AGB-Fassung (ORDERS_05).
    """
    from services import abo_vertrag
    from services import dazubuchen as dz
    from services.kundenzugang import darf_handeln, stufe_von

    angebot = dz.ANGEBOTE.get(kennung.upper())
    if not angebot:
        raise HTTPException(404, f"Unbekanntes Angebot: {kennung}")
    if not darf_handeln(stufe_von(user)):
        raise HTTPException(403, "Dieser Zugang darf nichts dazubuchen")
    if not body.verstanden:
        raise HTTPException(400, "Bitte bestätigen Sie, dass Sie die Bedingungen gelesen haben")
    if not user.lead_id:
        raise HTTPException(400, "Kein Betrieb am Konto")

    vertrag = abo_vertrag.laufender(db, user.lead_id)
    passend = [a for a, buchbar, _ in dz.buchbar_fuer(
        vertrag.produkt if vertrag else "", _offene_buchungen(db, user.lead_id))
        if a.kennung == angebot.kennung and buchbar]
    if not passend:
        raise HTTPException(409, "Dieses Angebot steht Ihnen gerade nicht offen")

    ab = _folgemonat() if not angebot.einmalig else ""
    jetzt = datetime.utcnow()
    db.execute(text(
        "INSERT INTO buchungen (lead_id, kennung, gebucht_von, gebucht_am, "
        "ab_monat, preis_netto_cent, preis_brutto_cent, rechtstext, zustand, notiz) "
        "VALUES (:l, :k, :v, :g, :ab, :n, :b, :r, 'offen', :no)"),
        {"l": user.lead_id, "k": angebot.kennung, "v": user.email, "g": jetzt,
         "ab": ab, "n": angebot.netto_cent, "b": angebot.brutto_cent,
         "r": angebot.rechtstext, "no": (body.notiz or "")[:1000]})
    db.commit()
    logger.warning("Buchung: Betrieb %s bucht %s (%s Cent brutto) durch %s",
                   user.lead_id, angebot.kennung, angebot.brutto_cent, user.email)

    return {"ok": True, "kennung": angebot.kennung,
            "gebucht_am": jetzt.isoformat(), "ab_monat": ab or _folgemonat(),
            "danach": angebot.danach}


# ══════════════════════════════════════════════════════════════════════
# Bezahlte Leistungen abrufen (L-160 Rang 6)
# ══════════════════════════════════════════════════════════════════════
#
# Zwei Positionen des Leistungsverzeichnisses konnte der Kunde **nicht
# anfordern**, obwohl er sie monatlich bezahlt: die Ruecksicherung und die
# eine neue Unterseite im Jahr. „Selten gebraucht, aber im Ernstfall dringend
# — und dann sucht niemand nach der Telefonnummer."


class AbrufWunsch(BaseModel):
    notiz: str = ""


def _abrufbare(db: Session, user):
    """Die Positionen, die dieses Abo abrufen laesst — leer ohne Vertrag."""
    from services import abo_vertrag
    from services import leistungsverzeichnis as lz

    vertrag = abo_vertrag.laufender(db, user.lead_id) if user.lead_id else None
    if not vertrag:
        return []
    return [p for p in lz.fuer_produkt(vertrag.produkt) if p.abruf]


@router.get("/abrufe")
def get_abrufe(user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Was abrufbar ist und was schon angefordert wurde."""
    positionen = _abrufbare(db, user)

    offen = {}
    try:
        for zeile in db.execute(text(
                "SELECT position, angefordert_am FROM abrufe "
                "WHERE lead_id = :l AND zustand = 'offen'"),
                {"l": user.lead_id}).fetchall():
            offen[int(zeile[0])] = zeile[1]
    except Exception:  # noqa: BLE001 — ohne Tabelle gibt es keine Abrufe
        db.rollback()

    return {"abrufe": [{
        "nummer": p.nummer, "titel": p.titel, "warum": p.warum,
        "frequenz": p.frequenz, "knopf": p.abruf, "danach": p.abruf_danach,
        "offen": p.nummer in offen,
        "angefordert_am": (offen[p.nummer].isoformat()
                           if p.nummer in offen and offen[p.nummer] else None),
    } for p in positionen]}


@router.post("/abrufe/{position}")
def fordere_ab(position: int, body: AbrufWunsch,
               user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Eine bezahlte Leistung anfordern.

    **Der Abruf loest nichts aus, er meldet an.** Eine Ruecksicherung ist
    Handarbeit am Datenbestand; sie auf Knopfdruck zu starten waere die
    gefaehrlichste Automatik im Haus.
    """
    from services import leistungsverzeichnis as lz

    punkt = lz.NACH_NUMMER.get(position)
    if not punkt:
        raise HTTPException(404, f"Unbekannte Position: {position}")
    if not punkt.abruf:
        raise HTTPException(400, f"„{punkt.titel}“ wird nicht abgerufen")
    if punkt not in _abrufbare(db, user):
        # 403 und nicht 404: Die Position gibt es, sein Vertrag kennt sie
        # nicht. Der Unterschied steht in der Meldung.
        raise HTTPException(403, f"„{punkt.titel}“ gehört nicht zu Ihrem Vertrag")

    vorhanden = db.execute(text(
        "SELECT angefordert_am FROM abrufe WHERE lead_id = :l AND position = :p "
        "AND zustand = 'offen'"), {"l": user.lead_id, "p": position}).fetchone()
    if vorhanden:
        # **Der erste Klick zaehlt.** Sonst stuenden beim Innendienst zwei
        # Anforderungen fuer dieselbe Sache — mit zwei Anfangszeitpunkten fuer
        # dieselbe zugesagte Reaktionszeit.
        return {"ok": True, "angefordert_am": vorhanden[0].isoformat(),
                "danach": punkt.abruf_danach, "schon_offen": True}

    jetzt = datetime.utcnow()
    db.execute(text(
        "INSERT INTO abrufe (lead_id, position, angefordert_von, "
        "angefordert_am, notiz, zustand) VALUES (:l, :p, :v, :a, :n, 'offen')"),
        {"l": user.lead_id, "p": position, "v": user.email, "a": jetzt,
         "n": (body.notiz or "")[:2000]})
    db.commit()
    logger.info("Abruf: Betrieb %s fordert Position %s an (%s)",
                user.lead_id, position, punkt.titel)

    return {"ok": True, "angefordert_am": jetzt.isoformat(),
            "danach": punkt.abruf_danach, "schon_offen": False}

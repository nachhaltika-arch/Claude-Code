# -*- coding: utf-8 -*-
"""Die Frist eines konkreten Projekts (L-166).

`bauzeit.py` rechnet mit Daten und kennt keine Datenbank. Hier kommen die
Daten her: die Eingangszeitpunkte aus `mitwirkung_stand`, die Vorlage- und
Freigabezeitpunkte der beiden Freigaben M7 und M8, und die zugesagte Bauzeit
aus dem gekauften Paket.

**Warum die Ableitung an genau einer Stelle steht.** Sie wird im Kundenkonto
gebraucht und im Innendienst. Zwei Ableitungen desselben Datums sind zwei, die
auseinanderlaufen koennen — und bei einer zugesagten Frist ist das der
Unterschied zwischen einem Nachweis und einem Streit darueber, wer wann was
behauptet hat.

**Die Bauzeit kommt aus dem Paket, nicht aus einer Konstanten.** Websprint
Start liegt bei 14 Werktagen, der Neubau bei 28, das Systempaket bei 42. Eine
fest verdrahtete Zahl gaebe dem einen Kunden die Frist des anderen — dieselbe
Klasse Fehler, die L-164 beim Paket selbst gekostet hat.
"""
import logging
from datetime import date
from typing import Optional

from sqlalchemy import text

from services import bauzeit
from services import mitwirkung as kat

logger = logging.getLogger(__name__)


def bauzeit_werktage(db, project) -> int:
    """Wie viele Werktage Bauzeit das gekaufte Paket zusagt.

    Faellt die Abfrage aus oder fuehrt das Paket keine Bauzeit, gilt der
    Standard aus `bauzeit.BAUZEIT_STANDARD_WERKTAGE`. **Kein `None`:** Ein
    fehlender Katalogeintrag darf das Konto nicht leeren, und die Zahl steht
    sichtbar in der Antwort — wer sie prueft, sieht sofort, ob sie zum Paket
    passt.

    **Achtung, hier steht ein offener Widerspruch — er ist nicht meiner, aber
    er geht durch diese Zeile** (gefunden am 06.09.2026, L-173). Die vier
    Produktdatenblaetter sagen **Kalendertage**: Start 7, Relaunch 14, Neubau
    28, System 42. Der Code gibt dieselben Zahlen an fuenf Stellen als
    **Werktage** aus — `auftragsbestaetigung_pdf`, `angebot_pdf` (zweimal),
    `payments`, `email_templates`. 28 Kalendertage sind vier Wochen; 28
    Werktage sind knapp sechs. Wer nach dem Datenblatt bindet und nach dem
    Code plant, reisst die zugesagte Frist um elf Kalendertage — und genau
    daran haengt die Verzugspauschale.

    **Gerechnet wird hier in Werktagen**, weil das ist, was der Kunde in
    Auftragsbestaetigung und Willkommensmail gelesen hat. Das ist die
    ruhigere der beiden Lesarten und ausdruecklich **keine Entscheidung ueber
    den Vertrag**: Welche Einheit gilt, gehoert ins Datenblatt und zu David.
    """
    slug = (getattr(project, "package_type", "") or "").strip()
    if not slug:
        return bauzeit.BAUZEIT_STANDARD_WERKTAGE
    try:
        zeile = db.execute(
            text("SELECT delivery_days FROM products WHERE slug = :s"),
            {"s": slug},
        ).fetchone()
    except Exception as fehler:  # noqa: BLE001 — eine fehlende Tabelle kippt das Konto nicht
        logger.warning("Bauzeit: Produktzeile nicht lesbar (%s: %s) — Standard gilt",
                       type(fehler).__name__, fehler)
        try:
            db.rollback()
        except Exception:  # noqa: BLE001 — eine kaputte Sitzung bleibt kaputt
            pass
        return bauzeit.BAUZEIT_STANDARD_WERKTAGE
    if zeile and zeile[0]:
        return int(zeile[0])
    return bauzeit.BAUZEIT_STANDARD_WERKTAGE


def _merkmale(project) -> set:
    """Dieselbe Ableitung wie im Portal — bedingte Punkte gelten nur, wenn das
    Projekt ihr Merkmal traegt."""
    merkmale = set()
    if getattr(project, "migration_noetig", False):
        merkmale.add("migration")
    if getattr(project, "karriereseite", False):
        merkmale.add("karriereseite")
    return merkmale


def frist_stand(db, project, heute: Optional[date] = None,
                staende: Optional[dict] = None) -> dict:
    """Beginn, Ruhezeiten und das zugesagte Ende — als eine Antwort.

    `staende` kann uebergeben werden, wenn der Aufrufer die Zeilen ohnehin
    schon geladen hat; sonst werden sie hier gelesen. Der Rueckgabewert traegt
    **alle** Zwischenschritte, nicht nur das Ergebnis: Wer im Streit das Datum
    prueft, muss sehen koennen, woraus es entstanden ist.
    """
    from database import MitwirkungStand

    stichtag = heute or date.today()
    if staende is None:
        zeilen = (db.query(MitwirkungStand)
                  .filter(MitwirkungStand.project_id == project.id).all())
        staende = {z.kennung: z for z in zeilen}

    punkte = kat.gilt_fuer(_merkmale(project))
    vor_start = [p for p in punkte if p.wirkung == kat.FRISTBEGINN]
    freigaben = [p for p in punkte if p.wirkung == kat.FRISTPAUSE]

    eingaenge = [getattr(staende.get(p.kennung), "erledigt_am", None)
                 for p in vor_start]
    beginn = bauzeit.fristbeginn_aus(eingaenge)

    pausen = []
    for p in freigaben:
        stand = staende.get(p.kennung)
        pause = bauzeit.pause_je_freigabe(
            vorgelegt_am=getattr(stand, "vorgelegt_am", None),
            freigegeben_am=getattr(stand, "erledigt_am", None),
            heute=stichtag)
        pausen.append((p, pause))

    summe = bauzeit.pausen_summe(p for _, p in pausen)
    werktage = bauzeit_werktage(db, project)
    ende = bauzeit.bauzeitende(beginn, werktage, summe)

    return {
        "beginn": beginn.isoformat() if beginn else None,
        "bauzeit_werktage": werktage,
        "pause_werktage": summe,
        "ende": ende.isoformat() if ende else None,
        # **Das Ende ohne Ruhezeit steht daneben.** Nur so ist ablesbar, was
        # die Verzoegerung gekostet hat — die Zahl, um die es im Streit geht.
        "ende_ohne_pause": (bauzeit.bauzeitende(beginn, werktage, 0).isoformat()
                            if beginn else None),
        "freigabefrist_werktage": bauzeit.FREIGABEFRIST_WERKTAGE,
        "offene_punkte": [p.kennung for p in
                          kat.fristbeginn_offen(punkte, {k for k, s in staende.items()
                                                         if s.erledigt_am})],
        "freigaben": [{
            "kennung": p.kennung,
            "titel": p.titel,
            "vorgelegt_am": pause.vorgelegt_am.isoformat() if pause.vorgelegt_am else None,
            "freigegeben_am": pause.freigegeben_am.isoformat() if pause.freigegeben_am else None,
            "frist_bis": pause.frist_bis.isoformat() if pause.frist_bis else None,
            "werktage": pause.werktage,
            "laeuft_noch": pause.laeuft_noch,
        } for p, pause in pausen],
    }

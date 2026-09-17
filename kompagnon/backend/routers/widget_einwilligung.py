# -*- coding: utf-8 -*-
"""Der Nachweis der Einwilligung — annehmen und auswerten (L-195).

**Warum es diesen Weg gibt.** Bis zum 17.09.2026 lag die Entscheidung am
Einwilligungsdialog ausschliesslich im `localStorage` des Besuchers. Damit
fehlte beides: der Nachweis, den Art. 7 Abs. 1 DSGVO verlangt, und die
Antwort auf die teuerste offene Frage der Kampagne.

**Die Frage, in Zahlen.** Am 17.09. gemessen (`docs/kampagne/einwilligungsquote.md`):
Von 353 echten Besuchern der Tage 14.–16.09. kamen bei Meta **12** an und bei
GA4 **11** — rund 3 %, waehrend die Entscheidungsvorlage mit 60–75 % rechnet.
Drei Ursachen kommen dafuer in Frage, und keine war zu belegen:

1. Der Besucher lehnt ab oder entscheidet gar nicht.
2. Ein Werbeblocker haelt das fremde Skript an.
3. Der In-App-Browser von Facebook oder Instagram beschneidet es —
   431 von 435 Aufrufen am 16.09. waren mobil.

Gegen (1) hilft der Dialog, gegen (2) und (3) nur eine eigene Messung. Diese
Meldung geht an die **eigene erste Adresse** und laedt kein fremdes Skript;
was hier ankommt und bei Meta fehlt, ist der Blockier- und In-App-Anteil.

**Warum eigene Datei.** `routers/widget.py` hat 710 Zeilen. Der Nachweis
haengt am Widget, ist aber eine eigene Sache mit eigener Rechtsgrundlage —
und die Auswertung darunter gehoert hinter eine Anmeldung, der Rest des
Widget-Routers ist oeffentlich. Zwei Sperren in einer Datei sind eine Falle.
"""
import ipaddress
import logging
import re
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import Einwilligung, get_db
from routers.auth_router import require_innendienst
from routers.widget import _client_ip

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/widget", tags=["widget"])

# Wie viele Seitenaufrufe ein Netz in der Stunde melden darf. Grosszuegig
# gewaehlt: Hinter einem Firmenanschluss oder einem Mobilfunk-NAT sitzen viele
# echte Besucher, und wer hier zu eng zaehlt, verliert genau die Gruppe, die
# gemessen werden soll. Die Grenze soll das Fluten verhindern, nicht die
# Messung beschneiden.
MELDUNGEN_JE_NETZ_UND_STUNDE = 300

# Die harte Obergrenze. Sie steht fuer den Fall, dass jemand Kennungen
# wuerfelt: Jede neue Kennung ist eine neue Zeile, und eine Tabelle, die
# unbegrenzt waechst, ist ein Ausfall mit Ansage.
MELDUNGEN_JE_STUNDE = 20_000

ENTSCHEIDUNGEN = ("erteilt", "abgelehnt", "unbekannt")
QUELLEN = ("nachricht", "parameter", "keine")

_NACHWEIS = re.compile(r"^[a-f0-9]{16,64}$")
_MOBIL = re.compile(r"Mobile|Android|iPhone|iPad", re.IGNORECASE)


def netz_von(ip: str) -> str:
    """Das Netz statt der Adresse — IPv4 auf /24, IPv6 auf /48.

    **Diese Tabelle nimmt auch die auf, die abgelehnt haben.** Wer Tracking
    ablehnt und dafuer eine vollstaendig gespeicherte Adresse bekommt, ist
    schlechter dran als vorher — das waere das Gegenteil dessen, was der
    Eintrag bezweckt. Das Netz genuegt, um einen Eintrag im Streitfall
    einzuordnen, und reicht nicht, um jemanden wiederzuerkennen.

    Eine unlesbare Adresse ergibt einen leeren Wert und keinen Fehler: Der
    Nachweis darf nicht daran scheitern, dass ein Proxy etwas Unerwartetes
    in die Kopfzeile geschrieben hat.
    """
    try:
        adresse = ipaddress.ip_address(ip.strip())
    except ValueError:
        return ""
    praefix = 24 if adresse.version == 4 else 48
    return str(ipaddress.ip_network(f"{adresse}/{praefix}", strict=False))


def app_browser_von(user_agent: str) -> str:
    """Der In-App-Browser, wenn es einer ist.

    Die Reihenfolge ist nicht beliebig: Instagram-Kennungen tragen **auch**
    `FBAV`/`FB_IAB`, weil beide Apps dieselbe Grundlage benutzen. Wer zuerst
    auf Facebook prueft, zaehlt jeden Instagram-Aufruf als Facebook — und
    genau diese Aufteilung ist die Frage, die hier beantwortet werden soll.
    """
    if not user_agent:
        return ""
    if "Instagram" in user_agent:
        return "instagram"
    if "FBAN" in user_agent or "FB_IAB" in user_agent or "FBAV" in user_agent:
        return "facebook"
    if "; wv)" in user_agent or "WebView" in user_agent:
        return "sonstige"
    return ""


def host_von(seite: str) -> str:
    """Nur der Host der einbettenden Seite, nie der Pfad.

    Das Widget laeuft auf fremden Seiten; ohne diese Angabe waere nicht zu
    sagen, wessen Dialog gemeint ist. Der **Pfad** bleibt draussen — er kann
    Suchbegriffe und Kennungen tragen, und fuer die Frage „wessen Dialog"
    traegt er nichts bei.
    """
    wert = (seite or "").strip()[:300]
    if not wert:
        return ""
    wert = re.sub(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", "", wert)
    wert = wert.split("/")[0].split("?")[0].split("#")[0]
    return wert[:200] if re.fullmatch(r"[A-Za-z0-9.\-:\[\]]{1,200}", wert) else ""


class EinwilligungMeldung(BaseModel):
    nachweis: str
    entscheidung: str
    marketing: bool | None = None
    statistik: bool | None = None
    quelle: str = "keine"
    fassung: str = ""
    seite: str = ""


def _grenzen(db: Session, netz: str) -> None:
    seit = datetime.utcnow() - timedelta(hours=1)
    if netz:
        von_netz = db.query(Einwilligung).filter(
            Einwilligung.created_at >= seit,
            Einwilligung.netz == netz).count()
        if von_netz >= MELDUNGEN_JE_NETZ_UND_STUNDE:
            raise HTTPException(429, "Zu viele Meldungen.")
    if db.query(Einwilligung).filter(Einwilligung.created_at >= seit).count() \
            >= MELDUNGEN_JE_STUNDE:
        raise HTTPException(429, "Zu viele Meldungen.")


@router.post("/einwilligung", status_code=204)
def einwilligung_melden(meldung: EinwilligungMeldung, request: Request,
                        db: Session = Depends(get_db)):
    """Nimmt die Entscheidung eines Seitenaufrufs entgegen.

    **Sie kommt zweimal:** einmal kurz nach dem Laden — was stand da schon? —
    und noch einmal, wenn der Besucher den Dialog beantwortet. Die zweite
    Meldung **aktualisiert** die erste ueber dieselbe Kennung. Ohne diese
    Zusammenfuehrung zaehlte jeder Entschluss doppelt, und zwar ausgerechnet
    bei denen, die zustimmen: Wer ablehnt, meldet meist nur einmal.

    **Kein Statuscode, der etwas verraet.** Eine unsinnige Kennung wird
    stillschweigend verworfen (204), nicht mit 422 beantwortet. Der Endpunkt
    ist oeffentlich; wer ihn abklopft, soll daraus nichts lernen. Der einzige
    Fehler, der nach aussen dringt, ist 429 — den muss der Aufrufer sehen,
    damit er aufhoert.
    """
    if not _NACHWEIS.fullmatch((meldung.nachweis or "").strip().lower()):
        return
    if meldung.entscheidung not in ENTSCHEIDUNGEN:
        return

    nachweis = meldung.nachweis.strip().lower()
    netz = netz_von(_client_ip(request))
    user_agent = request.headers.get("user-agent", "")

    zeile = db.query(Einwilligung).filter(
        Einwilligung.nachweis == nachweis).first()

    if zeile is None:
        _grenzen(db, netz)
        zeile = Einwilligung(nachweis=nachweis, created_at=datetime.utcnow())
        db.add(zeile)

    zeile.entscheidung = meldung.entscheidung
    zeile.marketing = meldung.marketing
    zeile.statistik = meldung.statistik
    zeile.quelle = meldung.quelle if meldung.quelle in QUELLEN else "keine"
    zeile.fassung = (meldung.fassung or "").strip()[:40]
    zeile.seite = host_von(meldung.seite)
    zeile.netz = netz
    zeile.mobil = bool(_MOBIL.search(user_agent))
    zeile.app_browser = app_browser_von(user_agent)
    zeile.updated_at = datetime.utcnow()

    try:
        db.commit()
    except Exception as fehler:
        # **Zwei Aufrufe desselben Seitenaufrufs koennen sich ueberholen.**
        # Dann legt der eine an, waehrend der andere schon anlegt, und der
        # eindeutige Schluessel greift. Das ist kein Fehler des Besuchers und
        # nichts, was ihn erreichen darf — die erste Zeile steht ja.
        db.rollback()
        logger.info("Einwilligungsmeldung verworfen (%s): %s", nachweis, fehler)


@router.get("/einwilligung/auswertung",
            dependencies=[Depends(require_innendienst)])
def einwilligung_auswerten(von: str = "", bis: str = "",
                           db: Session = Depends(get_db)):
    """Die Quote, aufgeschluesselt — der Lesepfad zu der Tabelle.

    **Ohne diesen Endpunkt waere der Nachweis gebaut und nicht angeschlossen**
    — die haeufigste Fehlerklasse in diesem Projekt. Die produktive Datenbank
    ist von hier aus nicht abfragbar; ohne Lesepfad saehe niemand je eine
    dieser Zeilen.

    Gezaehlt wird, was fuer die Diagnose zaehlt: die drei Entscheidungen, und
    daneben die Aufteilung nach In-App-Browser. **Der Nenner steht bewusst
    nicht hier drin:** Er kommt aus `GET /api/widget/config` in den
    Render-Protokollen (siehe `docs/kampagne/pruefverfahren.md`, Stufe 3) und
    liegt damit ausserhalb dieser Tabelle. Zwei Zaehlungen derselben Groesse
    an zwei Orten laufen auseinander; welche dann gilt, weiss hinterher
    niemand.
    """
    abfrage = db.query(Einwilligung)
    zeitraum = {"von": None, "bis": None}

    for name, wert in (("von", von), ("bis", bis)):
        if not wert:
            continue
        try:
            tag = datetime.strptime(wert.strip(), "%Y-%m-%d")
        except ValueError:
            raise HTTPException(400, f"`{name}` erwartet JJJJ-MM-TT.")
        zeitraum[name] = tag.date().isoformat()
        if name == "von":
            abfrage = abfrage.filter(Einwilligung.created_at >= tag)
        else:
            abfrage = abfrage.filter(
                Einwilligung.created_at < tag + timedelta(days=1))

    gesamt = abfrage.count()

    def _gruppieren(spalte):
        return dict(abfrage.with_entities(spalte, func.count()).group_by(spalte).all())

    entscheidungen = _gruppieren(Einwilligung.entscheidung)
    # Alle drei immer nennen, auch die mit null Treffern. Ein fehlender
    # Schluessel liest sich wie „nicht erhoben"; hier ist die Null gemessen.
    entscheidungen = {wert: entscheidungen.get(wert, 0) for wert in ENTSCHEIDUNGEN}

    umfeld = _gruppieren(Einwilligung.app_browser)
    umfeld = {(name or "kein_app_browser"): zahl for name, zahl in umfeld.items()}

    erteilt = entscheidungen["erteilt"]
    return {
        "zeitraum": zeitraum,
        "meldungen": gesamt,
        "entscheidungen": entscheidungen,
        # `None`, nicht 0 — ohne Meldungen ist die Quote nicht erhoben und
        # ausdruecklich nicht null. Die Unterscheidung ist in diesem Projekt
        # schon mehrfach teuer geworden.
        "zustimmungsquote": round(erteilt / gesamt, 4) if gesamt else None,
        "app_browser": umfeld,
        "mobil": abfrage.filter(Einwilligung.mobil.is_(True)).count(),
        "nenner_kommt_aus": "GET /api/widget/config (Render-Protokolle), "
                            "siehe docs/kampagne/pruefverfahren.md",
    }

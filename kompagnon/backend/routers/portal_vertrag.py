# -*- coding: utf-8 -*-
"""Vertragsunterlagen, Auftragsbestaetigung und Zugaenge des Betriebs.

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
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel

from database import get_db, Project, User
from routers.auth_router import get_current_user
from routers.portal_basis import (
    verlangt_geldblick,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/portal", tags=["portal"])


@router.get("/vertragsunterlagen")
def get_vertragsunterlagen(user=Depends(verlangt_geldblick),
                           db: Session = Depends(get_db)):
    """Alles, was der Kunde unterschrieben hat — in der Fassung seines Auftrags."""
    import os as _os

    unterlagen = []
    projekt = None
    if user.lead_id:
        projekt = (db.query(Project).filter(Project.lead_id == user.lead_id)
                   .order_by(Project.created_at.desc()).first())

    # ── Auftragsbestaetigung ──────────────────────────────────────────
    pfad = getattr(projekt, "auftragsbestaetigung_pdf", None) if projekt else None
    hat_datei = bool(pfad and _os.path.exists(pfad))
    unterlagen.append({
        "titel": "Auftragsbestätigung",
        "stand": (projekt.created_at.date().isoformat()
                  if projekt and projekt.created_at else ""),
        "vorhanden": hat_datei,
        # **`art` statt Praefix-Raten in der Oberflaeche.** Die erste Fassung
        # liess den Bildschirm `adresse.startsWith("/api/")` pruefen — also
        # aus der Form der Adresse schliessen, wie sie abzurufen ist. Wie
        # eine Unterlage geholt wird, ist eine Eigenschaft der Unterlage.
        "art": "pdf" if hat_datei else "",
        "adresse": (f"/api/portal/vertragsunterlagen/auftragsbestaetigung/{projekt.id}"
                    if hat_datei else ""),
        "grund": "" if hat_datei else (
            "Für diesen Auftrag liegt keine Auftragsbestätigung als PDF vor. "
            "Sie entsteht beim Kauf über die Kasse; bei älteren oder von Hand "
            "angelegten Aufträgen fehlt sie. Schreiben Sie uns, dann schicken "
            "wir sie nach."),
    })

    # ── AGB-Fassung ───────────────────────────────────────────────────
    #
    # **Zwei Quellen, und nur eine trägt.** Der Shop haelt die Fassung je
    # Bestellung fest (`bestellungen.terms_version`, ORDERS_05). Der
    # **Websprint**-Kauf ueber Stripe tut das **nicht** — dort entsteht kein
    # Nachweis, welche Fassung galt. Das steht als eigener Eintrag im
    # Lagebild; hier wird es benannt statt verschwiegen.
    fassung, wann = "", ""
    try:
        zeile = db.execute(text(
            "SELECT terms_version, terms_accepted_at FROM bestellungen "
            "WHERE email = :mail AND terms_version <> '' "
            "ORDER BY created_at DESC LIMIT 1"), {"mail": user.email}).fetchone()
        if zeile:
            fassung = zeile[0] or ""
            wann = zeile[1].date().isoformat() if zeile[1] else ""
    except Exception:  # noqa: BLE001 — ohne Shop-Tabelle bleibt es leer
        db.rollback()

    unterlagen.append({
        "titel": "AGB-Fassung",
        "stand": f"{fassung}, zugestimmt am {wann}" if fassung and wann else fassung,
        "vorhanden": bool(fassung),
        "art": "seite" if fassung else "",
        "adresse": "/agb" if fassung else "",
        "grund": "" if fassung else (
            "Für Ihren Auftrag ist keine AGB-Fassung festgehalten. Bei Käufen "
            "über den Shop wird sie mit dem Datum Ihrer Zustimmung gespeichert; "
            "beim Websprint über die Kasse geschieht das bisher nicht."),
    })

    # ── Angebot ───────────────────────────────────────────────────────
    #
    # Das Angebot entsteht heute **auf Abruf** aus dem Audit
    # (`routers/audit.py::download_angebot_pdf`) und wird nicht als Dokument
    # aufbewahrt. Ein Link darauf zeigte also auf ein Erzeugnis von heute,
    # nicht auf das, was der Kunde damals gelesen hat — und genau darauf
    # kommt es bei einer Vertragsunterlage an.
    unterlagen.append({
        "titel": "Angebot",
        "stand": "", "vorhanden": False, "art": "", "adresse": "",
        "grund": ("Ihr Angebot wird bei Bedarf neu aus dem Audit erzeugt und "
                  "nicht als Dokument aufbewahrt. Ein Abruf hier zeigte ein "
                  "Angebot von heute, nicht das, dem Sie zugestimmt haben. "
                  "Fordern Sie es bei uns an — wir schicken die Fassung, die "
                  "für Ihren Auftrag gilt."),
    })

    return {"unterlagen": unterlagen, "projekt_id": projekt.id if projekt else None}


@router.get("/vertragsunterlagen/auftragsbestaetigung/{projekt_id}")
def hole_auftragsbestaetigung(projekt_id: int,
                              user=Depends(verlangt_geldblick),
                              db: Session = Depends(get_db)):
    """Die Auftragsbestaetigung des **eigenen** Betriebs.

    **Der Filter steht auf `lead_id`, nicht nur auf der Projektnummer** —
    sonst waere eine fortlaufende Zahl der Schluessel zu jeder fremden
    Bestaetigung. 404 statt 403: Ob es die Nummer anderswo gibt, geht diesen
    Betrieb nichts an.
    """
    import os as _os

    from fastapi.responses import FileResponse

    projekt = (db.query(Project).filter(Project.id == projekt_id,
                                        Project.lead_id == user.lead_id).first())
    pfad = getattr(projekt, "auftragsbestaetigung_pdf", None) if projekt else None
    if not pfad or not _os.path.exists(pfad):
        raise HTTPException(404, "Auftragsbestätigung nicht vorhanden")

    return FileResponse(pfad, media_type="application/pdf",
                        filename="KOMPAGNON-Auftragsbestaetigung.pdf")


# ══════════════════════════════════════════════════════════════════════
# Zugaenge fuer Kollegen (L-160 Rang 4, K7)
# ══════════════════════════════════════════════════════════════════════
#
# **Ein Betrieb ist keine Person.** Bis heute hatte er genau ein Konto; wer
# einem Kollegen Zugang geben wollte, gab sein Kennwort weiter — und damit den
# Blick auf Rechnungen und Zahlungsart. Die Routen zum Anlegen von Konten gibt
# es laengst (`/api/admin/users`), aber sie verlangen `manage_users`, also
# Innendienst: Jeder Zugang musste bei uns beantragt werden.
#
# **Die Stufen und ihre Wirkung stehen in `services/kundenzugang.py`**, nicht
# hier. Sie gelten an mehreren Stellen, und eine Rechteregel an drei Orten ist
# eine, die an zweien veraltet.


class ZugangEinladung(BaseModel):
    email: str
    recht: str = "ansehen"


@router.get("/zugaenge")
def get_zugaenge(user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Wer alles Zugang zu diesem Betrieb hat.

    **Lesen darf jeder Zugang des Betriebs**, auch die schwache Stufe: Wer
    hereinkommt, soll sehen, wer sonst noch hereinkommt. Verwalten darf nur
    die starke — sonst koennte ein Mitleser sich selbst hochstufen.
    """
    from services.kundenzugang import (BESCHREIBUNG, STUFEN, darf_verwalten,
                                       stufe_von)

    if not user.lead_id:
        return {"zugaenge": [], "darf_verwalten": False, "stufen": []}

    konten = (db.query(User).filter(User.lead_id == user.lead_id,
                                    User.role == "kunde")
              .order_by(User.created_at.asc()).all())

    return {
        "darf_verwalten": darf_verwalten(stufe_von(user)),
        "stufen": [{"wert": s, "text": BESCHREIBUNG[s]} for s in STUFEN],
        # **Kein Kennwort, kein Token, keine Sitzungskennung.** Diese Liste
        # steht auf einem Bildschirm, den mehrere Personen sehen.
        "zugaenge": [{
            "id": k.id,
            "email": k.email,
            "name": f"{k.first_name or ''} {k.last_name or ''}".strip(),
            "recht": stufe_von(k),
            "selbst": k.id == user.id,
            # Ein Konto ohne Kennwort hat die Einladung noch nicht angenommen.
            "eingeladen": not bool(k.password_hash),
            "zuletzt": k.last_login.isoformat() if k.last_login else None,
        } for k in konten],
    }


@router.post("/zugaenge")
def lade_zugang_ein(body: ZugangEinladung,
                    user=Depends(get_current_user),
                    db: Session = Depends(get_db)):
    """Einen Kollegen einladen — am eigenen Betrieb.

    **Der Betrieb kommt aus der Anmeldung, nicht aus dem Aufruf.** Ein
    `lead_id` im Rumpf waere die Einladung in einen fremden Betrieb.

    **Ohne Kennwort angelegt.** Es entsteht ueber den Zuruecksetzen-Weg, den
    es schon gibt — ein zweiter Weg, Kennwoerter zu vergeben, waere ein
    zweiter, der falsch sein kann.
    """
    from services.kundenzugang import darf_verwalten, pruefe_stufe, stufe_von

    if not darf_verwalten(stufe_von(user)):
        raise HTTPException(403, "Dieser Zugang darf keine weiteren einrichten")
    if not user.lead_id:
        raise HTTPException(400, "Kein Betrieb am Konto")

    try:
        recht = pruefe_stufe(body.recht)
    except ValueError as fehler:
        raise HTTPException(400, str(fehler)) from fehler

    adresse = (body.email or "").strip().lower()
    if "@" not in adresse or len(adresse) < 5:
        raise HTTPException(400, "Bitte eine gültige E-Mail-Adresse angeben")

    vorhanden = db.query(User).filter(User.email == adresse).first()
    if vorhanden:
        # **Kein stilles Umhaengen.** Ein bestehendes Konto einem anderen
        # Betrieb zuzuschlagen waere ein Zugriff auf fremde Daten per
        # Einladung.
        raise HTTPException(400, "Zu dieser Adresse gibt es bereits ein Konto")

    neu = User(email=adresse, role="kunde", lead_id=user.lead_id,
               is_active=True, kunde_recht=recht, created_by=user.id)
    db.add(neu)
    db.commit()
    db.refresh(neu)

    # **Die Einladungsmail darf den Zugang nicht kosten** — sie ist der
    # bequeme Teil, das Konto der wesentliche. Scheitert sie, sagt die
    # Antwort das, statt den ganzen Vorgang zurueckzunehmen.
    versandt = False
    try:
        from services.email import send_password_reset_email
        from services.qr_service import generate_token

        neu.password_reset_token = generate_token()
        neu.password_reset_expires = datetime.utcnow() + timedelta(days=7)
        db.commit()
        versandt = bool(send_password_reset_email(
            neu.email, neu.password_reset_token, neu.email))
    except Exception as fehler:  # noqa: BLE001 — siehe Kommentar
        logger.warning("Einladung an %s: Mail nicht versandt (%s)",
                       adresse, type(fehler).__name__)

    return {"ok": True, "id": neu.id, "email": neu.email, "recht": recht,
            "mail_versandt": versandt}


@router.delete("/zugaenge/{zugang_id}")
def entferne_zugang(zugang_id: int, user=Depends(get_current_user),
                    db: Session = Depends(get_db)):
    """Einen Zugang entfernen — nicht den eigenen.

    **Den eigenen nicht**, weil der letzte starke Zugang sonst verschwinden
    koennte und niemand mehr Zugaenge verwalten duerfte. Der Betrieb waere
    ausgesperrt und muesste beim Innendienst anrufen.
    """
    from services.kundenzugang import darf_verwalten, stufe_von

    if not darf_verwalten(stufe_von(user)):
        raise HTTPException(403, "Dieser Zugang darf keine anderen entfernen")
    if zugang_id == user.id:
        raise HTTPException(400, "Den eigenen Zugang können Sie hier nicht entfernen")

    konto = (db.query(User).filter(User.id == zugang_id,
                                   User.lead_id == user.lead_id,
                                   User.role == "kunde").first())
    if not konto:
        # 404 und nicht 403: Ob es die Kennung anderswo gibt, geht diesen
        # Betrieb nichts an.
        raise HTTPException(404, "Zugang nicht gefunden")

    db.delete(konto)
    db.commit()
    return {"ok": True}


# ══════════════════════════════════════════════════════════════════════
# Was im Pflege-Abo steckt (L-160, Rang 3)
# ══════════════════════════════════════════════════════════════════════
#
# **Der Befund vom 04.09.2026:** Zwoelf Positionen, fuer die der Betrieb
# monatlich zahlt — und **keine einzige** war im Konto abrufbar. Weder was er
# bekommt, noch wie viel er genutzt hat, noch wie er es anfordert. Ein Abo,
# dessen Leistungen man nicht sieht, wird gekuendigt, weil es sich nach nichts
# anfuehlt.
#
# **Die Liste steht im Katalog, nicht hier.** `services/leistungsverzeichnis.py`
# fuehrt den Wortlaut des Datenblatts; dieser Endpunkt beantwortet nur, welches
# Abo laeuft und was daraus folgt.

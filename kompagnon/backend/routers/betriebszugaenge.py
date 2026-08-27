# -*- coding: utf-8 -*-
"""Mehrere Menschen an einem Betrieb.

**Der Anlass (25.08.2026).** Ein Kundenzugang entstand bisher an genau einer
Stelle — beim Stripe-Kauf, ein Konto je Betrieb. In einem Handwerksbetrieb
arbeiten aber Inhaber und Bueroleitung am selben Vorgang; ohne zweiten Zugang
teilen sich zwei Menschen ein Passwort, und jede Spur im Protokoll zeigt auf
denselben Namen.

**Zwei Entscheidungen, beide von David:**

1. **Der Innendienst laedt ein** (`manage_users`). Nicht der Kunde seine
   Kollegen, nicht Selbstregistrierung mit Freigabe. Es entsteht kein Weg,
   auf dem sich jemand selbst Zugriff auf einen Betrieb verschafft.
2. **Ein Benutzer gehoert zu einem Betrieb.** `users.lead_id` traegt kein
   UNIQUE — mehrere Konten je Betrieb gehen ohne Schemaaenderung. Der
   umgekehrte Fall (ein Mensch ueber mehreren Betrieben) braeuchte eine
   Zuordnungstabelle und ist bewusst **nicht** gebaut; er kommt, wenn ihn
   jemand braucht, und dann mit echten Daten als Grundlage.

**Die Einladung erfindet kein zweites Verfahren.** Sie setzt denselben
`password_reset_token`, den „Passwort vergessen“ benutzt — nur mit einer
Frist von Tagen statt einer Stunde. Ein zweiter Weg zum Passwortsetzen
waere ein zweiter Weg, der falsch sein kann.
"""
import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from auth import generate_reset_token
from database import Lead, User, get_db
from routers.auth_router import verlangt_recht

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/leads", tags=["Betriebszugaenge"])

#: Wie lange eine Einladung gilt. Eine Stunde wie beim Zuruecksetzen waere zu
#: kurz — die Mail liegt ueber Nacht im Postfach; unbegrenzt waere ein
#: liegengebliebener Schluessel.
EINLADUNG_TAGE = 7

EMAIL_MUSTER = r"^[^@\s]+@[^@\s]+\.[a-zA-Z]{2,}$"


class ZugangAnlegen(BaseModel):
    email: str = Field(pattern=EMAIL_MUSTER, max_length=255)
    first_name: str = Field(default="", max_length=100)
    last_name: str = Field(default="", max_length=100)


def _betrieb(db: Session, lead_id: int) -> Lead:
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(404, "Betrieb nicht gefunden")
    return lead


def _auskunft(user: User) -> dict:
    """Was der Innendienst ueber einen Zugang sieht.

    **Ohne den Token.** Er ist der Schluessel zum Passwort dieses Menschen;
    wer die Liste sieht, koennte sich sonst als er anmelden.
    """
    offen = bool(user.password_reset_token) and not user.password_hash
    return {
        "id": user.id,
        "email": user.email,
        "name": f"{user.first_name or ''} {user.last_name or ''}".strip(),
        "aktiv": bool(user.is_active),
        "eingeladen": offen,
        "einladung_laeuft_ab": (user.password_reset_expires.isoformat()
                                if offen and user.password_reset_expires else None),
        "zuletzt_angemeldet": (user.last_login.isoformat()
                               if user.last_login else None),
    }


@router.get("/{lead_id}/zugaenge",
            dependencies=[Depends(verlangt_recht("manage_users"))])
def zugaenge_lesen(lead_id: int, db: Session = Depends(get_db)):
    """Wer sich an diesem Betrieb anmelden kann — offene Einladungen inbegriffen."""
    _betrieb(db, lead_id)
    konten = (db.query(User).filter(User.lead_id == lead_id)
              .order_by(User.created_at).all())
    return {"zugaenge": [_auskunft(k) for k in konten]}


@router.post("/{lead_id}/zugaenge", status_code=201,
             dependencies=[Depends(verlangt_recht("manage_users"))])
def zugang_einladen(lead_id: int, daten: ZugangAnlegen,
                    db: Session = Depends(get_db)):
    """Einen weiteren Menschen an diesen Betrieb lassen.

    Das Konto entsteht **ohne Passwort**. Anmelden kann sich damit niemand
    (`login` weist ein Konto ohne Hash ab); erst der Link aus der Mail macht
    es benutzbar. So liegt zu keinem Zeitpunkt ein vergebenes Passwort in
    einer Mail oder in einem Protokoll.
    """
    lead = _betrieb(db, lead_id)
    email = daten.email.lower().strip()

    vorhanden = db.query(User).filter(User.email == email).first()
    if vorhanden:
        # **Niemals umhaengen.** Waere das Konto still auf diesen Betrieb
        # gezeigt worden, haette der Mensch den Zugang zu seinem eigenen
        # verloren und einen fremden bekommen.
        raise HTTPException(409, f"Für {email} gibt es bereits einen Zugang. "
                                 f"Ein bestehendes Konto wird nicht auf einen "
                                 f"anderen Betrieb umgehängt.")

    konto = User(
        email=email,
        password_hash=None,
        first_name=daten.first_name.strip(),
        last_name=daten.last_name.strip(),
        role="kunde",
        lead_id=lead.id,
        is_active=True,
        is_verified=False,
        password_reset_token=generate_reset_token(),
        password_reset_expires=datetime.utcnow() + timedelta(days=EINLADUNG_TAGE),
    )
    db.add(konto)
    db.commit()
    db.refresh(konto)

    # Was der Betrieb schon freigeschaltet hat, gilt auch dem Neuen — sonst
    # findet er eine leere Akademie, weil die Zuweisung aelter ist als sein
    # Konto. Der Versand darf daran nicht haengen; ein Fehler hier waere
    # aergerlich, aber der Zugang steht.
    try:
        from services.zugang_bestand import bestand_uebernehmen
        geerbt = bestand_uebernehmen(db, lead.id, konto.id)
        if geerbt:
            logger.info("Zugang %s erbt vom Betrieb %s: %s",
                        konto.id, lead.id, geerbt)
    except Exception as fehler:      # noqa: BLE001
        db.rollback()
        logger.warning("Bestand für %s nicht übernommen: %s", konto.id, fehler)

    versandt = False
    try:
        from services.email import send_einladung_email
        versandt = send_einladung_email(
            konto.email, konto.password_reset_token,
            lead.company_name or "Ihrem Betrieb",
            f"{konto.first_name} {konto.last_name}".strip(), EINLADUNG_TAGE)
    except Exception as fehler:      # noqa: BLE001 — der Zugang steht schon
        logger.warning("Einladung an %s nicht versandt: %s", konto.email, fehler)

    # Der Versand darf den Vorgang nicht scheitern lassen — das Konto ist
    # angelegt, und ein zweiter Anlauf wuerde am eindeutigen `email` haengen.
    # Stattdessen sagt die Antwort, ob die Mail rausging.
    return {**_auskunft(konto), "mail_versandt": bool(versandt)}


class ZugangVerbinden(BaseModel):
    email: str = Field(pattern=EMAIL_MUSTER, max_length=255)
    #: Der zweite Klick. Ohne ihn wird ein Konto, das schon einem Betrieb
    #: gehoert, nicht angefasst — die Absage nennt den Betrieb beim Namen.
    umhaengen_bestaetigt: bool = False


@router.post("/{lead_id}/zugaenge/verbinden",
             dependencies=[Depends(verlangt_recht("manage_users"))])
def zugang_verbinden(lead_id: int, daten: ZugangVerbinden,
                     db: Session = Depends(get_db)):
    """Ein Konto, das es schon gibt, an diesen Betrieb haengen.

    **Warum es das gibt (25.08.2026).** Die Einladung weist eine bekannte
    Adresse mit 409 ab, damit niemand **still** den Zugang eines Menschen zu
    seinem Betrieb wegnimmt. Damit blieb aber kein Weg, es **absichtlich** zu
    tun — und den braucht es: ein Kauf lief auf eine Dublette, ein Betrieb
    wurde zusammengelegt, ein Konto entstand ohne Zuordnung.

    Die Regel hiess nie „nie umhaengen", sondern „nicht still umhaengen".
    Deshalb zwei Faelle:

    - Konto **ohne** Betrieb: verbinden, ohne Rueckfrage. Da ist nichts zu
      verlieren.
    - Konto **eines anderen** Betriebs: erst nach `umhaengen_bestaetigt`. Die
      Absage davor nennt den alten Betrieb beim Namen — ein Hinweis, der das
      Hindernis verschweigt, ist eine Sackgasse (L-56).

    **Beim Wechsel gibt das Konto die Freischaltungen ab und erbt die neuen.**
    Eine Freischaltung gehoert dem Betrieb; wer wechselt, nimmt sie nicht mit.
    Fortschritt und Zertifikate bleiben — die gehoeren dem Menschen.
    """
    lead = _betrieb(db, lead_id)
    email = daten.email.lower().strip()

    konto = db.query(User).filter(User.email == email).first()
    if not konto:
        raise HTTPException(404, f"Für {email} gibt es kein Konto. Diese "
                                 f"Adresse müssen Sie einladen — dabei "
                                 f"entsteht eines.")

    # Ein Mitarbeiterkonto gehoert keinem Betrieb. Ein `lead_id` daran waere
    # im besten Fall verwirrend und im schlechten der Anfang einer
    # Rechtevermischung: Die Kundenansichten fragen nach `lead_id`, nicht
    # nach der Rolle.
    if konto.role != "kunde":
        raise HTTPException(409, f"{email} ist ein Mitarbeiterkonto (Rolle "
                                 f"„{konto.role}“) und wird nicht an einen "
                                 f"Betrieb gehängt.")

    if konto.lead_id == lead.id:
        raise HTTPException(409, f"{email} gehört bereits zu diesem Betrieb.")

    alter_betrieb = konto.lead_id
    if alter_betrieb and not daten.umhaengen_bestaetigt:
        vorher = db.query(Lead).filter(Lead.id == alter_betrieb).first()
        name = vorher.company_name if vorher else f"Betrieb {alter_betrieb}"
        raise HTTPException(409, f"{email} gehört derzeit zu „{name}“. "
                                 f"Umhängen nimmt den Zugang dort weg — "
                                 f"bitte ausdrücklich bestätigen.")

    konto.lead_id = lead.id
    db.commit()
    db.refresh(konto)

    # Erst abgeben, dann erben — in dieser Reihenfolge, sonst loescht das
    # Abgeben gleich wieder, was gerade geerbt wurde.
    try:
        from services.zugang_bestand import bestand_abgeben, bestand_uebernehmen
        if alter_betrieb:
            abgegeben = bestand_abgeben(db, konto.id)
            logger.info("Zugang %s gibt an Betrieb %s ab: %s",
                        konto.id, alter_betrieb, abgegeben)
        geerbt = bestand_uebernehmen(db, lead.id, konto.id)
        if geerbt:
            logger.info("Zugang %s erbt vom Betrieb %s: %s",
                        konto.id, lead.id, geerbt)
    except Exception as fehler:      # noqa: BLE001 — die Zuordnung steht schon
        db.rollback()
        logger.warning("Bestand für %s nicht umgestellt: %s", konto.id, fehler)

    logger.info("Zugang %s (%s) mit Betrieb %s verbunden, vorher %s",
                konto.id, konto.email, lead.id, alter_betrieb or "ohne Betrieb")
    return {**_auskunft(konto), "umgehaengt_von": alter_betrieb}


@router.post("/{lead_id}/zugaenge/{user_id}/einladung",
             dependencies=[Depends(verlangt_recht("manage_users"))])
def einladung_erneuern(lead_id: int, user_id: int, db: Session = Depends(get_db)):
    """Eine abgelaufene oder nie angekommene Einladung noch einmal schicken."""
    lead = _betrieb(db, lead_id)
    konto = (db.query(User)
             .filter(User.id == user_id, User.lead_id == lead_id).first())
    if not konto:
        raise HTTPException(404, "Zugang gehört nicht zu diesem Betrieb")

    konto.password_reset_token = generate_reset_token()
    konto.password_reset_expires = datetime.utcnow() + timedelta(days=EINLADUNG_TAGE)
    db.commit()
    db.refresh(konto)

    versandt = False
    try:
        from services.email import send_einladung_email
        versandt = send_einladung_email(
            konto.email, konto.password_reset_token,
            lead.company_name or "Ihrem Betrieb",
            f"{konto.first_name} {konto.last_name}".strip(), EINLADUNG_TAGE)
    except Exception as fehler:      # noqa: BLE001
        logger.warning("Einladung an %s nicht versandt: %s", konto.email, fehler)

    return {**_auskunft(konto), "mail_versandt": bool(versandt)}


@router.delete("/{lead_id}/zugaenge/{user_id}",
               dependencies=[Depends(verlangt_recht("manage_users"))])
def zugang_entziehen(lead_id: int, user_id: int, db: Session = Depends(get_db)):
    """Den Zugang schliessen — ohne das Konto zu loeschen.

    **Deaktivieren statt loeschen**, aus zwei Gruenden: Was dieser Mensch
    angelegt hat (`created_by`, Nachrichten, Dateien), zeigt weiter auf einen
    Namen statt ins Leere. Und ein versehentliches Entziehen ist umkehrbar.

    Wer wirklich loeschen muss — Art. 17 DSGVO —, nimmt den Weg ueber
    `DELETE /api/leads/{id}?mit_zugang=true`; der raeumt den Betrieb samt
    allen Konten.
    """
    _betrieb(db, lead_id)
    konto = (db.query(User)
             .filter(User.id == user_id, User.lead_id == lead_id).first())
    if not konto:
        raise HTTPException(404, "Zugang gehört nicht zu diesem Betrieb")

    konto.is_active = False
    # Eine offene Einladung verfaellt mit — sonst setzte der Eingeladene
    # danach noch ein Passwort auf ein Konto, das entzogen wurde.
    konto.password_reset_token = None
    konto.password_reset_expires = None
    db.commit()

    # Sitzungen beenden: Ein gueltiges Token im Browser wuerde sonst
    # weiterlaufen, bis es von selbst ablaeuft.
    try:
        from sqlalchemy import text
        db.execute(text("DELETE FROM user_sessions WHERE user_id = :u"),
                   {"u": user_id})
        db.commit()
    except Exception as fehler:      # noqa: BLE001 — Tabelle evtl. nicht da
        db.rollback()
        logger.warning("Sitzungen von %s nicht beendet: %s", user_id, fehler)

    return {"success": True, "id": user_id, "aktiv": False}

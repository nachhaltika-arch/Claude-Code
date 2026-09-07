# -*- coding: utf-8 -*-
"""Auskunft und Loeschung — Art. 15 und 17 DSGVO.

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

from database import get_db, Lead
from routers.auth_router import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/portal", tags=["portal"])


# ══════════════════════════════════════════════════════════════════════
# Auskunft und Loeschung — Art. 15 und 17 DSGVO (L-160 Rang 5)
# ══════════════════════════════════════════════════════════════════════
#
# **Beides ist ein gesetzlicher Anspruch**, und beides ging bisher nur ueber
# eine Mail an uns. Wer sie nicht beantwortet bekommt, hat einen Verstoss in
# der Hand — und keine Spur, dass er gefragt hat.


@router.get("/datenkopie")
def get_datenkopie(user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Was ueber diesen Betrieb gespeichert ist — Art. 15 DSGVO.

    **Auch die leeren Bereiche stehen drin.** Eine Auskunft, die nur
    Gefundenes nennt, beantwortet die Frage nicht: „Was habt ihr ueber mich?"
    schliesst „in diesem Bereich nichts" ein.

    **Und kein Kennwort, kein Zweitfaktor, kein Zuruecksetzen-Token.** Die
    Kopie wird heruntergeladen, weitergeschickt und liegt danach irgendwo.
    Art. 15 verlangt Auskunft ueber die Daten, nicht die Herausgabe der
    Zugangsmittel.
    """
    lead = db.query(Lead).filter(Lead.id == user.lead_id).first() if user.lead_id else None

    def zaehle(tabelle: str, spalte: str = "lead_id") -> int:
        if not user.lead_id:
            return 0
        try:
            zeile = db.execute(text(
                f"SELECT COUNT(*) FROM {tabelle} WHERE {spalte} = :w"),
                {"w": user.lead_id}).fetchone()
            return int(zeile[0]) if zeile else 0
        except Exception:  # noqa: BLE001 — eine fehlende Tabelle ist kein Datum
            db.rollback()
            return 0

    bereiche = [
        {"titel": "Projekte", "anzahl": zaehle("projects")},
        {"titel": "Hochgeladene Dateien", "anzahl": zaehle("project_files")},
        {"titel": "Rechnungen", "anzahl": zaehle("invoices")},
        {"titel": "Nachrichten und Mails", "anzahl": zaehle("communications")},
        {"titel": "Audits Ihrer Website", "anzahl": zaehle("audit_results")},
        {"titel": "Änderungswünsche", "anzahl": zaehle("inhalts_anfragen")},
        {"titel": "Leistungsberichte", "anzahl": zaehle("leistungsberichte")},
        {"titel": "Zugänge", "anzahl": zaehle("users")},
    ]

    return {
        "erstellt_am": datetime.utcnow().isoformat(),
        # Das Konto — ausdruecklich Feld fuer Feld, nicht als Abbild des
        # Datensatzes: Ein `dict(user.__dict__)` haette den Kennworthash
        # mitgenommen, und zwar still.
        "konto": {
            "email": user.email,
            "vorname": user.first_name or "",
            "nachname": user.last_name or "",
            "telefon": user.phone or "",
            "rolle": user.role,
            "angelegt_am": user.created_at.isoformat() if user.created_at else None,
            "zuletzt_angemeldet": user.last_login.isoformat() if user.last_login else None,
        },
        "betrieb": {
            "id": lead.id if lead else None,
            "name": (lead.company_name or "") if lead else "",
            "ansprechpartner": (lead.contact_name or "") if lead else "",
            "email": (lead.email or "") if lead else "",
            "telefon": (lead.phone or "") if lead else "",
            "website": (lead.website_url or "") if lead else "",
        } if lead else {},
        "bereiche": bereiche,
        "hinweis": ("Diese Übersicht nennt, was wir zu Ihrem Betrieb führen. "
                    "Möchten Sie die Inhalte eines Bereichs vollständig "
                    "erhalten, schreiben Sie uns — wir liefern sie binnen "
                    "eines Monats (Art. 12 DSGVO)."),
    }


class LoeschAntrag(BaseModel):
    bestaetigung: str = ""
    verstanden: bool = False


def _loesch_huerden(db: Session, user) -> tuple:
    """Die drei Dinge, die einer Loeschung im Weg stehen — und sie sind ungleich.

    Rueckgabe: (Huerdenliste, moeglich, Sperrgrund).
    """
    from services import abo_vertrag

    vertrag = abo_vertrag.laufender(db, user.lead_id) if user.lead_id else None
    laeuft = vertrag is not None

    huerden = [
        {
            "titel": f"Ihr Pflege-Abo ({vertrag.produkt}) läuft" if vertrag
                     else "Kein laufendes Pflege-Abo",
            "dazu": ("Solange es läuft, können wir das Konto nicht löschen — es "
                     "ist die Grundlage der monatlichen Abbuchung. Kündigen Sie "
                     "zuerst; danach merken wir die Löschung vor."
                     if laeuft else
                     "Es steht kein laufender Vertrag entgegen."),
            "erfuellt": not laeuft,
            "ausraeumbar": True,
        },
        {
            "titel": "Ihre Website läuft auf unserem Hosting",
            "dazu": ("Mit dem Konto endet das Hosting, und Ihre Seite ist nicht "
                     "mehr erreichbar. Die Domain gehört Ihnen; wir legen sie "
                     "auf Ihren neuen Anbieter um und geben Ihnen die Inhalte "
                     "mit. Schreiben Sie uns, bevor Sie löschen."),
            # **Keine Sperre, eine Warnung.** Wer trotzdem loeschen will, darf
            # das — es sind seine Daten. Aber er soll die Folge vorher kennen.
            "erfuellt": None,
            "ausraeumbar": True,
        },
        {
            "titel": "Rechnungen bleiben zehn Jahre",
            "dazu": ("Das ist keine Wahl, sondern eine Pflicht: § 147 "
                     "Abgabenordnung verlangt es. Sie liegen danach gesperrt "
                     "in der Buchhaltung und werden für nichts anderes "
                     "verwendet."),
            # Weder erfuellt noch offen — sie **gilt**. Sie als Hindernis
            # darzustellen, das man ausraeumen kann, waere falsch.
            "erfuellt": None,
            "ausraeumbar": False,
        },
    ]
    sperrgrund = ("Erst wenn Ihr Pflege-Abo gekündigt ist. Es ist die Grundlage "
                  "der monatlichen Abbuchung.") if laeuft else ""
    return huerden, not laeuft, sperrgrund


@router.get("/loeschung")
def get_loeschung(user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Was einer Loeschung im Weg steht — und ob schon eine beantragt ist."""
    huerden, moeglich, sperrgrund = _loesch_huerden(db, user)

    antrag = None
    try:
        zeile = db.execute(text(
            "SELECT beantragt_am, frist_bis, zustand FROM loeschantraege "
            "WHERE lead_id = :l"), {"l": user.lead_id}).fetchone()
        if zeile:
            antrag = {"beantragt_am": zeile[0].isoformat() if zeile[0] else None,
                      "frist_bis": zeile[1].isoformat() if zeile[1] else None,
                      "zustand": zeile[2]}
    except Exception:  # noqa: BLE001 — ohne Tabelle gibt es keinen Antrag
        db.rollback()

    return {"huerden": huerden, "moeglich": moeglich, "sperrgrund": sperrgrund,
            "antrag": antrag,
            "folgen": [
                "Ihre Zugänge und die Ihrer Kollegen werden gelöscht. Niemand "
                "kann sich mehr anmelden.",
                "Ihre Website und das Hosting enden.",
                "Hochgeladene Dateien, Briefings und Berichte werden gelöscht.",
                "Rechnungen bleiben zehn Jahre gesperrt in der Buchhaltung "
                "(§ 147 AO).",
            ]}


@router.post("/loeschung")
def beantrage_loeschung(body: LoeschAntrag,
                        user=Depends(get_current_user),
                        db: Session = Depends(get_db)):
    """Die Loeschung **beantragen** — Art. 17 DSGVO.

    **Sie geschieht nicht hier.** Eine Loeschung, die sofort greift, ist bei
    einem Betrieb ohne zweiten Zugang ein Ausfall ohne Rueckweg. Was hier
    entsteht, ist der **Nachweis des Eingangs**; ab ihm laeuft die Monatsfrist
    aus Art. 12.

    **Zwei Huerden, weil ein Klick zu wenig ist:** das Wort und das Haeckchen.
    """
    if (body.bestaetigung or "").strip().upper() != "LÖSCHEN":
        raise HTTPException(400, "Bitte tippen Sie LÖSCHEN, um fortzufahren")
    if not body.verstanden:
        raise HTTPException(400, "Bitte bestätigen Sie, dass Sie die Folgen kennen")
    if not user.lead_id:
        raise HTTPException(400, "Kein Betrieb am Konto")

    _, moeglich, sperrgrund = _loesch_huerden(db, user)
    if not moeglich:
        # 409 und nicht 403: Es fehlt keine Berechtigung, es steht ein
        # Vertrag entgegen. Der Unterschied steht in der Meldung.
        raise HTTPException(409, sperrgrund)

    # **Der erste Antrag zaehlt.** Ein zweiter Klick darf die Monatsfrist
    # nicht neu starten — das waere zu unseren Gunsten, und niemand saehe es.
    vorhanden = db.execute(text(
        "SELECT beantragt_am, frist_bis FROM loeschantraege WHERE lead_id = :l"),
        {"l": user.lead_id}).fetchone()
    if vorhanden:
        return {"ok": True, "beantragt_am": vorhanden[0].isoformat(),
                "frist_bis": vorhanden[1].isoformat() if vorhanden[1] else None,
                "schon_beantragt": True}

    jetzt = datetime.utcnow()
    frist = jetzt + timedelta(days=30)
    db.execute(text(
        "INSERT INTO loeschantraege (lead_id, beantragt_von, beantragt_am, "
        "frist_bis, zustand) VALUES (:l, :v, :a, :f, 'offen')"),
        {"l": user.lead_id, "v": user.email, "a": jetzt, "f": frist})
    db.commit()
    logger.warning("Loeschantrag nach Art. 17 DSGVO: Betrieb %s durch %s, "
                   "Frist bis %s", user.lead_id, user.email, frist.date())

    return {"ok": True, "beantragt_am": jetzt.isoformat(),
            "frist_bis": frist.isoformat(), "schon_beantragt": False}


# ══════════════════════════════════════════════════════════════════════
# Vertragsunterlagen (L-160 Rang 7)
# ══════════════════════════════════════════════════════════════════════
#
# **Der Befund:** Angebot, AGB-Fassung und Auftragsbestaetigung liegen im
# System, und der Kunde kommt nicht heran. Die Auftragsbestaetigung gibt es
# als PDF am Projekt; ihr einziger Auslieferungsweg verlangt `require_admin`.
#
# **Was hier ausdruecklich nicht geschieht: etwas erfinden.** Wo eine
# Unterlage nicht vorliegt, sagt die Antwort das — mit Grund. Eine Liste mit
# fuenf Zeilen, von denen drei ins Leere fuehren, ist schlechter als eine mit
# zwei.

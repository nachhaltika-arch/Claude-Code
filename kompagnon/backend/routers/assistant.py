"""Der Projekt-Assistent — Chat, Feldprüfung, Übergabe ans Team.

Ausbau 1 aus `docs/projekt-assistent-anforderungen.md`: Begleitung durch das
Briefing, für Kunde und Mitarbeiter. Die Projektbegleitung (Ausbau 2) kommt
später, das Datenmodell ist schon projektbezogen.

Drei Dinge macht dieser Router, und die Reihenfolge ist Absicht:

1. **Rolle → Modus → Freigabeliste.** Der Modus kommt aus `User.role` auf dem
   Server; was der Client mitschickt, wird ignoriert. Der Kontext entsteht aus
   einer expliziten Feldliste (`services/assistant_context.py`).
2. **Budget vor dem Aufruf.** Erst wird gezählt, dann gefragt. Ist das Budget
   erschöpft, kommt eine freundliche Antwort — und kein Modellaufruf.
3. **Erst dann das Modell.** Mit Maßstab je Feld aus `assistant_rules.py`, damit
   die Antwort an etwas Prüfbarem hängt und nicht an gutem Willen.

Was hier bewusst *nicht* passiert: schreiben. Der Assistent schlägt vor, der
Mensch übernimmt (Entscheidung 1.3). Kein Schreibzugriff auf `briefings`.
"""
import logging
import os
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from routers.auth_router import require_any_auth
from database import (
    AssistantConversation,
    AssistantMessage,
    Briefing,
    Lead,
    Message,
    Project,
    get_db,
)
from services.assistant_budget import (
    GRENZE_NUTZER_PRO_TAG,
    GRENZE_PROJEKT_EURO,
    Verbrauch,
    darf_fragen,
    kosten_fuer,
)
from services.assistant_context import MODUS_TEAM, baue_kontext, modus_fuer_rolle
from services.rechte import gehoert_zum_innendienst
from services.assistant_rules import pruefe_antwort, regelwerk_fuer_prompt

try:
    from anthropic import Anthropic
except ImportError:  # pragma: no cover
    Anthropic = None

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/assistant", tags=["assistant"])

# Chat ist Dialog, nicht Markup — das Sonnet-Modell reicht und haelt die Kosten
# je Frage niedrig. Blockerzeugung laeuft weiter auf Opus.
#
# Sonnet 5 statt 4.6, gemessen am selben Fragensatz (docs, Abschnitt 9.6): es
# haelt die Faktensperre ein und schlaegt trotzdem vor, wo 4.6 nur noch
# zurueckfragt — 8 von 9 statt 5 von 9. Aus der Umgebung, damit der naechste
# Wechsel wieder messbar ist statt geraten.
ASSISTENT_MODELL = os.getenv("ASSISTENT_MODELL", "claude-sonnet-5")

# Deckel fuer eine Antwort. Er begrenzt Denken UND Text gemeinsam, und Sonnet 5
# denkt von sich aus mit — mit den 800 aus der 4.6-Zeit riss die Antwort mitten
# im Wort ab („Mehr Anrufe bei Heizungsausf") und wurde trotzdem als Vorschlag
# angeboten. Wer das Modell wechselt, muss diesen Wert mitziehen.
ASSISTENT_MAX_TOKENS = int(os.getenv("ASSISTENT_MAX_TOKENS", "2500"))

TONALITAET = (
    "Sprich den Nutzer mit Sie an. Kurze Saetze, keine Marketing- und keine "
    "Technikfloskeln. Beispiele aus Heizung, Sanitaer und Elektrik. Wenn du "
    "etwas nicht weisst, sag es und biete an, das Team zu fragen."
)


class ChatRequest(BaseModel):
    lead_id: int
    frage: str
    projekt_id: Optional[int] = None
    conversation_id: Optional[int] = None
    feld: Optional[str] = ""
    schritt: Optional[str] = ""
    # Bewusst entgegengenommen und bewusst ignoriert: Der Modus kommt aus der
    # Rolle. Das Feld steht hier, damit ein Client, der es schickt, keinen
    # 422-Fehler bekommt — und damit im Code sichtbar ist, dass es nichts tut.
    modus: Optional[str] = None


class FeldPruefung(BaseModel):
    feld: str
    wert: Optional[str] = ""


class Eskalation(BaseModel):
    anliegen: Optional[str] = ""


def _systemprompt(kontext: dict, feld: str) -> str:
    """Was das Modell zu sehen bekommt — Kontext, Maßstab, Tonalität."""
    import json

    felder = [feld] if feld else None
    maszstab = regelwerk_fuer_prompt(felder)
    offen = ", ".join(kontext.get("briefing_offen") or []) or "keine"
    # Ohne diese Zeile muss das Modell aus dem Regelwerk raten, welches Feld
    # gerade offen ist — im scharfen Lauf hat es dabei einen Vorschlag fuer das
    # Nachbarfeld formuliert. Uebernommen wird er trotzdem in `body.feld`.
    aktuell = (f"DAS AKTUELLE FELD IST: {feld}. Ein Vorschlag gilt immer genau "
               f"diesem Feld, keinem anderen.\n\n") if feld else ""

    return f"""Du bist der Projekt-Assistent von KOMPAGNON und begleitest einen
Handwerksbetrieb durch das Briefing seiner neuen Website.

{TONALITAET}

DEINE AUFGABE: Hilf beim Ausfuellen. Erklaere, warum ein Feld gebraucht wird,
und schlage konkrete Formulierungen vor. Du fuellst nichts selbst aus — der
Mensch uebernimmt deinen Vorschlag per Klick.

WAS DU UEBER DIESES PROJEKT WEISST:
{json.dumps(kontext, ensure_ascii=False, indent=2, default=str)}

NOCH OFFENE FELDER: {offen}

{aktuell}MASZSTAB FUER GUTE ANTWORTEN:
{maszstab or "(kein besonderer Maszstab fuer dieses Feld)"}

WAS DU NICHT ERFINDEN DARFST: Alles, was der Vorschlag ueber diesen Betrieb
behauptet, muss oben im Projektstand stehen oder im Gespraech gesagt worden
sein. Nie erfinden: Ortsnamen, Preise, Reaktionszeiten, Garantien, Meister-
und Zertifikatsangaben, Baujahre, Marken, Mitarbeiterzahlen, Jahreszahlen.
Fehlt dir eine Angabe, setze eine sichtbare Luecke in eckigen Klammern —
etwa [Orte bitte ergaenzen] — und frage in der Erklaerung danach. Ein
Vorschlag mit Luecke ist richtig; ein glatter Vorschlag mit erfundenen
Angaben wird zur Falschaussage auf der fertigen Website.

Das gilt fuer Tatsachen ueber den Betrieb. Wuensche und Gestaltung — Stil,
Wirkung, Ziel, gewuenschte Besucheraktion — darfst du weiterhin begruendet
vorschlagen, solange der Vorschlag nichts ueber den Betrieb behauptet, was
du nicht weisst.

Antworte in hoechstens fuenf Saetzen.

Wenn du einen konkreten Vorschlag fuer das aktuelle Feld hast, setze ihn als
LETZTE Zeile in genau diese Form:

VORSCHLAG: <der fertige Text, den der Nutzer uebernehmen kann>

Nur diese eine Zeile, ohne Anfuehrungszeichen und ohne Erklaerung dahinter. Hast
du keinen Vorschlag, lass die Zeile weg."""


VORSCHLAG_MARKE = "VORSCHLAG:"


def trenne_vorschlag(text: str) -> tuple:
    """Trennt den uebernehmbaren Vorschlag von der Erklaerung.

    Entscheidung 1.3: Der Assistent schlaegt vor, der Mensch uebernimmt per
    Klick. Damit die Oberflaeche einen Knopf anbieten kann, muss der Vorschlag
    maschinenlesbar sein — deshalb die letzte Zeile in fester Form. Steht sie
    nicht da, gibt es eben keinen Knopf; geraten wird nicht.
    """
    if not text:
        return "", ""
    zeilen = text.strip().split("\n")
    for i in range(len(zeilen) - 1, -1, -1):
        if zeilen[i].strip().startswith(VORSCHLAG_MARKE):
            vorschlag = zeilen[i].split(VORSCHLAG_MARKE, 1)[1].strip().strip('"„“')
            rest = "\n".join(zeilen[:i] + zeilen[i + 1:]).strip()
            return rest, vorschlag
    return text.strip(), ""


def _frag_das_modell(*, systemprompt: str, verlauf: list, frage: str) -> dict:
    """Ein Aufruf beim Modell. Getrennt, damit der Test ihn ersetzen kann."""
    if not Anthropic:
        raise HTTPException(500, "anthropic-Library nicht installiert")
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(500, "ANTHROPIC_API_KEY nicht konfiguriert")

    client = Anthropic(api_key=api_key)
    antwort = client.messages.create(
        model=ASSISTENT_MODELL, thinking={"type": "disabled"},
        max_tokens=ASSISTENT_MAX_TOKENS,
        system=systemprompt,
        messages=verlauf + [{"role": "user", "content": frage}],
    )
    text = "".join(b.text for b in (antwort.content or [])
                   if getattr(b, "type", None) == "text").strip()
    nutzung = getattr(antwort, "usage", None)
    return {
        "text": text,
        "eingabe_tokens": getattr(nutzung, "input_tokens", 0) or 0,
        "ausgabe_tokens": getattr(nutzung, "output_tokens", 0) or 0,
        # Am Deckel abgerissen. Der Text bleibt brauchbar, ein Vorschlag darin
        # ist ein Fragment — siehe `chat()`.
        "abgeschnitten": getattr(antwort, "stop_reason", None) == "max_tokens",
    }


def _verbrauch(db: Session, projekt_id: Optional[int], user_id: Optional[int]) -> Verbrauch:
    """Was dieses Projekt und dieser Nutzer bisher verbraucht haben."""
    projekt_euro = 0.0
    if projekt_id:
        projekt_euro = db.query(func.coalesce(func.sum(AssistantMessage.kosten_euro), 0.0)) \
            .join(AssistantConversation,
                  AssistantMessage.conversation_id == AssistantConversation.id) \
            .filter(AssistantConversation.project_id == projekt_id).scalar() or 0.0

    heute = 0
    if user_id:
        beginn = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0,
                                                    microsecond=0, tzinfo=None)
        heute = db.query(func.count(AssistantMessage.id)) \
            .join(AssistantConversation,
                  AssistantMessage.conversation_id == AssistantConversation.id) \
            .filter(AssistantConversation.user_id == user_id,
                    AssistantMessage.rolle == "nutzer",
                    AssistantMessage.created_at >= beginn).scalar() or 0

    return Verbrauch(projekt_euro=float(projekt_euro), nutzer_anfragen_heute=int(heute))


def _rolle_von(user) -> str:
    return getattr(user, "role", None) or (user or {}).get("role", "") \
        if not isinstance(user, str) else user


@router.post("/chat")
def chat(body: ChatRequest, db: Session = Depends(get_db),
         user=Depends(require_any_auth)):
    """Eine Frage an den Assistenten — mit Verlauf, Budget und Freigabeliste."""
    lead = db.query(Lead).filter(Lead.id == body.lead_id).first()
    if not lead:
        raise HTTPException(404, "Lead nicht gefunden")

    frage = (body.frage or "").strip()
    if not frage:
        raise HTTPException(400, "frage fehlt")

    modus = modus_fuer_rolle(_rolle_von(user))
    user_id = getattr(user, "id", None)

    gespraech = _gespraech(db, body, lead, modus, user_id)

    # Erst zählen, dann fragen.
    stand = _verbrauch(db, gespraech.project_id, user_id)
    entscheidung = darf_fragen(stand)
    if not entscheidung.erlaubt:
        _speichern(db, gespraech, "nutzer", frage, body)
        _speichern(db, gespraech, "assistent", entscheidung.hinweis, body)
        db.commit()
        return {
            "conversation_id": gespraech.id,
            "modus": modus,
            "antwort": entscheidung.hinweis,
            "budget_erschoepft": True,
            "hinweis": entscheidung.hinweis,
        }

    projekt = (db.query(Project).filter(Project.id == gespraech.project_id).first()
               if gespraech.project_id else None)
    briefing = db.query(Briefing).filter(Briefing.lead_id == lead.id).first()
    kontext = baue_kontext(modus, lead=lead, briefing=briefing, projekt=projekt)

    verlauf = [
        {"role": "user" if m.rolle == "nutzer" else "assistant", "content": m.inhalt}
        for m in gespraech.messages[-10:]
    ]

    _speichern(db, gespraech, "nutzer", frage, body)
    ergebnis = _frag_das_modell(
        systemprompt=_systemprompt(kontext, body.feld or ""),
        verlauf=verlauf, frage=frage)

    text, vorschlag = trenne_vorschlag(ergebnis["text"])
    if ergebnis.get("abgeschnitten"):
        # Die Marke steht da, der Satz dahinter ist halb. Uebernehmen wuerde ein
        # Fragment ins Briefing schreiben — lieber kein Knopf. Der Text selbst
        # bleibt stehen, er ist bis zum Abriss brauchbar.
        if vorschlag:
            text = f"{text}\n{vorschlag}".strip()
        vorschlag = ""
    kosten = kosten_fuer(ergebnis["eingabe_tokens"], ergebnis["ausgabe_tokens"])
    _speichern(db, gespraech, "assistent", text, body,
               eingabe=ergebnis["eingabe_tokens"], ausgabe=ergebnis["ausgabe_tokens"],
               kosten=kosten)
    db.commit()

    return {
        "conversation_id":   gespraech.id,
        "modus":             modus,
        "antwort":           text,
        # Leer, wenn das Modell nichts Konkretes vorzuschlagen hatte — die
        # Oberflaeche zeigt den Uebernehmen-Knopf dann gar nicht erst.
        "vorschlag":         vorschlag,
        "feld":              body.feld or "",
        "budget_erschoepft": False,
        "hinweis":           entscheidung.hinweis,
    }


def _gespraech(db: Session, body: ChatRequest, lead: Lead, modus: str,
               user_id: Optional[int]) -> AssistantConversation:
    if body.conversation_id:
        vorhanden = (db.query(AssistantConversation)
                       .filter(AssistantConversation.id == body.conversation_id,
                               AssistantConversation.lead_id == lead.id).first())
        if not vorhanden:
            raise HTTPException(404, "Gespräch nicht gefunden")
        return vorhanden

    neu = AssistantConversation(
        lead_id=lead.id, project_id=body.projekt_id, modus=modus, user_id=user_id,
        titel=(body.frage or "")[:120])
    db.add(neu)
    db.flush()
    return neu


def _speichern(db: Session, gespraech: AssistantConversation, rolle: str,
               inhalt: str, body: ChatRequest, eingabe: int = 0, ausgabe: int = 0,
               kosten: float = 0.0) -> AssistantMessage:
    nachricht = AssistantMessage(
        conversation_id=gespraech.id, rolle=rolle, inhalt=inhalt,
        schritt=body.schritt or "", feld=body.feld or "",
        eingabe_tokens=eingabe, ausgabe_tokens=ausgabe, kosten_euro=kosten)
    db.add(nachricht)
    db.flush()
    return nachricht


def _gespraech_oder_403(db: Session, conversation_id: int, user):
    """Das Gespräch — oder 403, wenn es einem anderen Betrieb gehört.

    **404 vor 403 waere hier falsch herum.** Ob es ein Gespraech mit dieser
    Nummer gibt, ist bereits eine Auskunft; deshalb erst suchen, dann die
    Zugehoerigkeit pruefen, und bei Fremdbesitz **403** — nicht 404, weil der
    Innendienst denselben Weg geht und ein echtes „gibt es nicht" von einem
    „gehoert dir nicht" unterscheiden koennen muss.
    """
    gespraech = (db.query(AssistantConversation)
                   .filter(AssistantConversation.id == conversation_id).first())
    if not gespraech:
        raise HTTPException(404, "Gespräch nicht gefunden")

    if (not gehoert_zum_innendienst(getattr(user, "role", ""))
            and getattr(user, "lead_id", None) != gespraech.lead_id):
        raise HTTPException(403, "Kein Zugriff auf dieses Gespräch")

    return gespraech


@router.get("/conversations/{conversation_id}")
def verlauf(conversation_id: int, db: Session = Depends(get_db),
            user=Depends(require_any_auth)):
    """Der gespeicherte Gesprächsverlauf — nur der eigene.

    **Bis zum 31.08.2026 stand hier nur `require_any_auth`**, und das heisst
    „irgendwer ist angemeldet". Wer die Nummer hochzaehlte, las fremde
    Gespraeche mit Namen des Betriebs, Inhalt und Kosten je Nachricht. Der
    Endpunkt hatte keinen Aufrufer, also fiel es niemandem auf — genau deshalb
    wurde er geprueft, **bevor** er einen bekam.

    Dieselbe Pruefung wie in `leads_portal.lead_oder_403`: Wer nicht zum
    Innendienst gehoert, sieht nur den eigenen Betrieb. Nicht „ist Kunde",
    sondern „gehoert nicht zum Innendienst" — die Umkehrung von 18.08.2026,
    die damals die Rolle `nutzer` durchgelassen hatte.
    """
    gespraech = _gespraech_oder_403(db, conversation_id, user)

    return {
        "conversation_id": gespraech.id,
        "lead_id":         gespraech.lead_id,
        "modus":           gespraech.modus,
        "eskaliert":       gespraech.escalated_at is not None,
        "messages": [{
            "rolle":          m.rolle,
            "inhalt":         m.inhalt,
            "feld":           m.feld,
            "schritt":        m.schritt,
            "eingabe_tokens": m.eingabe_tokens,
            "ausgabe_tokens": m.ausgabe_tokens,
            "kosten_euro":    m.kosten_euro,
        } for m in gespraech.messages],
    }


@router.post("/field-check")
def feld_pruefen(body: FeldPruefung, user=Depends(require_any_auth)):
    """Die Prüfung, die kein Modell braucht.

    Leer, zu knapp, Floskel, „trifft auf jeden zu" — das zählt der Code. Erst
    wenn eine Antwort hier durchkommt, lohnt sich eine inhaltliche Bewertung.
    """
    befund = pruefe_antwort(body.feld, body.wert)
    return {
        "feld":      befund.feld,
        "brauchbar": befund.brauchbar,
        "hinweise":  befund.hinweise,
    }


@router.post("/conversations/{conversation_id}/escalate")
def eskalieren(conversation_id: int, body: Eskalation,
               db: Session = Depends(get_db), user=Depends(require_any_auth)):
    """Aus dem Gespräch wird eine echte Nachricht ans Team.

    Entscheidung 3.2: Das trennt unverbindliche Hilfe von verbindlicher
    Kommunikation. Der Verlauf fährt zusammengefasst mit, damit niemand ihn
    nachlesen muss.

    **Am 31.08.2026 abgesichert wie `verlauf`.** Auch hier stand nur
    `require_any_auth`; ein Fremder konnte ein Gespraech eskalieren, das ihm
    nicht gehoert — und der Verlauf faehrt dabei im Klartext ans Team.
    """
    gespraech = _gespraech_oder_403(db, conversation_id, user)

    if gespraech.escalated_at is not None:
        return {"bereits_eskaliert": True, "conversation_id": gespraech.id}

    zeilen = [f"Anliegen: {body.anliegen.strip()}" if (body.anliegen or "").strip()
              else "Anliegen: (ohne Text)", "", "Bisheriges Gespräch:"]
    for m in gespraech.messages:
        wer = "Kunde" if m.rolle == "nutzer" else "Assistent"
        zeilen.append(f"— {wer}: {m.inhalt}")

    lead = db.query(Lead).filter(Lead.id == gespraech.lead_id).first()
    db.add(Message(
        lead_id=gespraech.lead_id,
        sender_role="kunde",
        sender_name=(getattr(lead, "company_name", "") or "Kunde"),
        channel="in_app",
        subject="Frage aus dem Projekt-Assistenten",
        content="\n".join(zeilen),
    ))
    gespraech.escalated_at = datetime.utcnow()
    db.commit()

    return {"bereits_eskaliert": False, "conversation_id": gespraech.id}


@router.get("/limits")
def grenzen(user=Depends(require_any_auth)):
    """Was gilt — damit die Oberfläche es anzeigen kann, statt zu raten."""
    return {
        "projekt_euro":   GRENZE_PROJEKT_EURO,
        "nutzer_pro_tag": GRENZE_NUTZER_PRO_TAG,
        "modus":          modus_fuer_rolle(_rolle_von(user)),
        "team_modus":     MODUS_TEAM,
    }

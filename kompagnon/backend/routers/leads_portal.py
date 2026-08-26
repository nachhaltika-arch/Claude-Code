"""Die Wege ohne Innendienst-Anmeldung (L-25).

**Warum eigene Datei, 22.08.2026.** In `routers/leads.py` lagen drei Router
nebeneinander: der des Innendienstes, einer fuer das Formular der
Landingpage und einer fuer das Kundenportal. Nur der erste verlangt eine
Rolle — die beiden anderen pruefen ihren Einmal-Token selbst
beziehungsweise gar nichts, weil das Formular ohne Anmeldung erreichbar
sein muss.

Drei Router mit drei verschiedenen Sperren in einer Datei mit 2.575 Zeilen
sind schwer auseinanderzuhalten. Wer hier eine Route ergaenzt und den
falschen Router nimmt, oeffnet sie oder sperrt einen Kunden aus, und keine
Meldung sagt es — dieselbe Bauart, die am 19.08. 55 offene Routen erzeugt
hat (L-51).

Vor dem Schnitt nachgemessen: Der Innendienst-Teil braucht von hier
**nichts**.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, BackgroundTasks
from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from database import Lead, Project, AuditResult, get_db, SessionLocal
from services.ratenbegrenzung import lead_grenzen
from routers.auth_router import require_any_auth, get_current_user, INNENDIENST
# `LeadResponse` steht in `leads.py`: Zwei Dateien brauchen es —
# hier der Kundenweg, drueben die Ausfuhr. Ein Antwortmodell, das
# zwei Seiten teilen, gehoert an eine Stelle.
from routers.leads import LeadResponse
import logging

logger = logging.getLogger(__name__)


# Ausdrücklich ohne Anmeldung — jede dieser Routen trägt ihre eigene Prüfung:
# das Anlegen aus dem Formular der Landingpage und der Kundenzugang über einen
# Einmal-Token aus der E-Mail.
public_router = APIRouter(prefix="/api/leads", tags=["leads-public"])


# Was ein Kunde braucht: den eigenen Betrieb, den das Kundenportal anzeigt
# (`KundenPortal.jsx`). Jede Route hier prüft selbst, ob die Zeile ihm gehört.
kunden_router = APIRouter(prefix="/api/leads", tags=["leads-kunde"],
                          dependencies=[Depends(require_any_auth)])


#: So lang sind `utm_source`, `utm_medium` und `utm_campaign` in der Tabelle.
UTM_MAX = 200




def _herkunft_aus_anzeige(daten: dict) -> dict:
    """Die UTM-Angaben aus dem Formular — begrenzt entgegengenommen (L-86).

    **Der Befund.** Bis zum 22.08.2026 uebernahm dieser Weg `website_url`,
    `email` und `lead_source`, und sonst nichts. Wer ueber eine Anzeige mit
    `?utm_source=google` kam und das Formular ausfuellte, verlor seine
    Herkunft im Moment des Absendens — und die Kanalauswertung (L-84) konnte
    bezahlte Kanaele darum nie ausweisen.

    Die Werte kommen **ohne Anmeldung** aus einem Widget auf fremden Seiten,
    und `data` ist ein rohes `dict`: Was keine Zeichenkette ist, wird nicht
    uebernommen, und was zu lang ist, wird gekuerzt statt die Anlage
    scheitern zu lassen. Gespeichert wird roh — ausgewertet oder in HTML
    gesetzt wird hier nichts.

    Fehlt eine Angabe, bleibt das Feld leer. Eine geratene Herkunft waere
    schlimmer als eine fehlende: Auf ihr wuerde gerechnet.
    """
    herkunft = {}
    for feld in ("utm_source", "utm_medium", "utm_campaign"):
        wert = daten.get(feld)
        if isinstance(wert, str) and wert.strip():
            herkunft[feld] = wert.strip()[:UTM_MAX]
    return herkunft


@public_router.post("/public")
async def create_public_lead(
    data: dict,
    db: Session = Depends(get_db),
    _grenzen=Depends(lead_grenzen),
):
    """Public endpoint for landing page audit — creates lead without login."""
    website_url = data.get('website_url', '').strip()
    email_addr = data.get('email', '').strip()
    if not website_url:
        raise HTTPException(400, "Website-URL fehlt")
    if not website_url.startswith('http'):
        website_url = 'https://' + website_url

    domain = website_url.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0]
    from sqlalchemy import or_
    existing = db.query(Lead).filter(or_(Lead.website_url.ilike(f'%{domain}%'))).first()
    if existing:
        if email_addr and not existing.email:
            existing.email = email_addr
            db.commit()
        return {'id': existing.id}

    lead = Lead(website_url=website_url, email=email_addr, company_name=domain,
                status='new', lead_source=data.get('lead_source', 'landing_audit'),
                **_herkunft_aus_anzeige(data))
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return {'id': lead.id}


@public_router.get("/portal/{token}")
def get_portal_data(token: str, db: Session = Depends(get_db)):
    """Public portal page — token is the access key."""
    lead = db.query(Lead).filter(Lead.customer_token == token).first()
    if not lead:
        raise HTTPException(404, "Ungültiger Zugangslink")

    email_domain = ''
    if lead.email and '@' in lead.email:
        email_domain = lead.email.split('@')[1]

    latest_audit = db.query(AuditResult).filter(
        AuditResult.lead_id == lead.id, AuditResult.status == 'completed',
    ).order_by(AuditResult.created_at.desc()).first()

    project = db.query(Project).filter(
        Project.lead_id == lead.id
    ).order_by(Project.created_at.desc()).first()

    return {
        'lead_id': lead.id,
        'company_name': lead.display_name or lead.company_name or '',
        'email_domain': email_domain,
        'website_url': lead.website_url or '',
        'city': lead.city or '',
        'trade': lead.trade or '',
        'contact_name': lead.contact_name or '',
        'current_score': latest_audit.total_score if latest_audit else None,
        'current_level': latest_audit.level if latest_audit else None,
        'last_audit_date': str(latest_audit.created_at)[:10] if latest_audit else None,
        'rc_score': latest_audit.rc_score if latest_audit else None,
        'tp_score': latest_audit.tp_score if latest_audit else None,
        'bf_score': latest_audit.bf_score if latest_audit else None,
        'si_score': latest_audit.si_score if latest_audit else None,
        'se_score': latest_audit.se_score if latest_audit else None,
        'ux_score': latest_audit.ux_score if latest_audit else None,
        'ai_summary': latest_audit.ai_summary if latest_audit else None,
        'website_screenshot': f'data:image/jpeg;base64,{lead.website_screenshot}' if lead.website_screenshot else None,
        'onboarding_completed': getattr(lead, 'onboarding_completed', False) or False,
        'project_id':     project.id if project else None,
        'current_phase':  project.current_phase if project else None,
        'project_status': project.status if project else None,
        'go_live_date':   str(project.go_live_date)[:10] if project and project.go_live_date else None,
    }


@public_router.post("/portal/{token}/verify")
def verify_portal_access(token: str, data: dict, db: Session = Depends(get_db)):
    """Verify access via email domain match."""
    lead = db.query(Lead).filter(Lead.customer_token == token).first()
    if not lead:
        raise HTTPException(404, "Ungültiger Link")

    input_email = data.get('email', '').lower().strip()
    if not input_email or '@' not in input_email:
        raise HTTPException(400, "Bitte gültige E-Mail eingeben")

    input_domain = input_email.split('@')[1]
    lead_domain = ''
    if lead.email and '@' in lead.email:
        lead_domain = lead.email.split('@')[1].lower()
    elif lead.website_url:
        lead_domain = lead.website_url.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0].lower()

    if not lead_domain:
        raise HTTPException(400, "Keine Domain hinterlegt")
    if input_domain != lead_domain:
        raise HTTPException(403, "E-Mail-Domain stimmt nicht überein")

    return {
        'verified': True,
        'contact_name': lead.contact_name or '',
        'email': lead.email or '',
        'phone': lead.phone or '',
        'street': lead.street or '',
        'house_number': lead.house_number or '',
        'postal_code': lead.postal_code or '',
        'city': lead.city or '',
        'legal_form': lead.legal_form or '',
        'vat_id': lead.vat_id or '',
        'register_number': lead.register_number or '',
        'register_court': lead.register_court or '',
        'ceo_first_name': lead.ceo_first_name or '',
        'ceo_last_name': lead.ceo_last_name or '',
        'geschaeftsfuehrer': lead.geschaeftsfuehrer or '',
    }


@public_router.post("/portal/{token}/complete-onboarding")
def complete_onboarding(token: str, data: dict, db: Session = Depends(get_db)):
    """Mark onboarding as completed and optionally save briefing fields."""
    lead = db.query(Lead).filter(Lead.customer_token == token).first()
    if not lead:
        raise HTTPException(404, "Ungültiger Zugangslink")

    if data.get('website_url'):
        lead.website_url = data['website_url']

    lead.onboarding_completed = True
    lead.onboarding_completed_at = datetime.utcnow()

    # Briefing-Felder speichern falls vorhanden
    gewerk       = data.get('gewerk')
    leistungen   = data.get('leistungen')
    einzugsgebiet = data.get('einzugsgebiet')
    has_logo     = data.get('has_logo')
    has_photos   = data.get('has_photos')
    anmerkungen  = data.get('anmerkungen')

    briefing_fields = any(v is not None for v in [
        gewerk, leistungen, einzugsgebiet, has_logo, has_photos, anmerkungen
    ])

    if briefing_fields:
        try:
            db.execute(text("""
                INSERT INTO briefings
                  (lead_id, gewerk, leistungen, einzugsgebiet,
                   logo_vorhanden, fotos_vorhanden, sonstige_hinweise, status)
                VALUES
                  (:lead_id, :gewerk, :leistungen, :einzugsgebiet,
                   :logo_vorhanden, :fotos_vorhanden, :sonstige_hinweise, 'entwurf')
                ON CONFLICT (lead_id) DO UPDATE SET
                  gewerk            = COALESCE(EXCLUDED.gewerk, briefings.gewerk),
                  leistungen        = COALESCE(EXCLUDED.leistungen, briefings.leistungen),
                  einzugsgebiet     = COALESCE(EXCLUDED.einzugsgebiet, briefings.einzugsgebiet),
                  logo_vorhanden    = COALESCE(EXCLUDED.logo_vorhanden, briefings.logo_vorhanden),
                  fotos_vorhanden   = COALESCE(EXCLUDED.fotos_vorhanden, briefings.fotos_vorhanden),
                  sonstige_hinweise = COALESCE(EXCLUDED.sonstige_hinweise, briefings.sonstige_hinweise),
                  updated_at        = NOW()
            """), {
                'lead_id':          lead.id,
                'gewerk':           gewerk,
                'leistungen':       leistungen,
                'einzugsgebiet':    einzugsgebiet,
                'logo_vorhanden':   has_logo,
                'fotos_vorhanden':  has_photos,
                'sonstige_hinweise': anmerkungen,
            })
        except Exception:
            # Briefings-Tabelle existiert nicht — Felder als Notiz sichern
            parts = []
            if gewerk:        parts.append(f"Gewerk: {gewerk}")
            if leistungen:    parts.append(f"Leistungen: {leistungen}")
            if einzugsgebiet: parts.append(f"Einzugsgebiet: {einzugsgebiet}")
            if anmerkungen:   parts.append(f"Anmerkungen: {anmerkungen}")
            if parts:
                lead.notes = ((lead.notes or '') + '\n' + '\n'.join(parts)).strip()

    db.commit()
    return {"success": True}


@public_router.post("/portal-auth/complete-onboarding")
def portal_auth_complete_onboarding(
    data: dict,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """JWT-geschützter Onboarding-Abschluss für Kunden."""
    from database import User as UserModel
    if current_user.role != 'kunde':
        raise HTTPException(403, "Nur für Kunden zugänglich")

    lead_id = data.get('lead_id') or current_user.lead_id
    if not lead_id:
        raise HTTPException(400, "lead_id fehlt")

    if current_user.lead_id and current_user.lead_id != lead_id:
        raise HTTPException(403, "Zugriff verweigert")

    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(404, "Lead nicht gefunden")

    if data.get('website_url'):
        lead.website_url = data['website_url']

    lead.onboarding_completed = True
    lead.onboarding_completed_at = datetime.utcnow()

    parts = []
    if data.get('gewerk'):        parts.append(f"Gewerk: {data['gewerk']}")
    if data.get('leistungen'):    parts.append(f"Leistungen: {data['leistungen']}")
    if data.get('einzugsgebiet'): parts.append(f"Einzugsgebiet: {data['einzugsgebiet']}")
    if data.get('anmerkungen'):   parts.append(f"Anmerkungen: {data['anmerkungen']}")
    if parts:
        lead.notes = ((lead.notes or '') + '\n---\nOnboarding:\n' + '\n'.join(parts)).strip()

    db.commit()
    return {"success": True}


@kunden_router.get("/{lead_id}", response_model=LeadResponse)
def get_lead(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get a specific lead by ID.

    Die einzige Lead-Route, die auch ein Kunde aufrufen darf — für den
    eigenen Betrieb. Die eigene Nummer hochzuzählen ist der naheliegendste
    Angriff, deshalb steht die Prüfung hier und nicht in der Oberfläche.

    **18.08.2026:** Die Prüfung fragte, ob jemand `kunde` ist — und liess
    damit die Rolle `nutzer` durch, die laut Rechtematrix kein `view_leads`
    hat. Jetzt umgekehrt: Wer nicht zum Innendienst gehört, sieht nur den
    eigenen Betrieb. Dieselbe Umkehrung wie in `require_innendienst`.
    """
    if current_user.role not in INNENDIENST and current_user.lead_id != lead_id:
        raise HTTPException(status_code=403, detail="Kein Zugriff auf diesen Betrieb")

    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead

# ── Stammdaten, vom Kunden gepflegt (26.08.2026) ─────────────────────
#
# **Erlaubnisliste, keine Verbotsliste.** Ein Betrieb traegt zweierlei: die
# Angaben **ueber** ihn — Anschrift, Ansprechpartner, Rechtsform,
# Registernummer — und die Angaben, die **wir** ueber ihn fuehren: Status,
# Herkunft, interne Notizen, Punktzahl, Zugangs-Token. Das Erste gehoert ihm,
# das Zweite ist unsere Arbeitsspur.
#
# Eine Verbotsliste vergisst das Feld, das morgen dazukommt. Diese Liste
# laesst es draussen, bis jemand es ausdruecklich aufnimmt — die teurere,
# aber die richtige Richtung.
#
# Ausdruecklich **nicht** darin: `status` (der Kunde setzte sich sonst selbst
# auf „gewonnen"), `notes` (unsere Notizen ueber ihn), `lead_source`,
# `customer_token` (der Schluessel zu seinem Portal), alle Punktzahlen und
# Zaehler. `email` steht drin, weil es die Geschaeftsadresse des Betriebs
# ist — die Anmeldeadresse liegt an `users` und ist davon unberuehrt.
STAMMDATEN_DES_KUNDEN = (
    "company_name", "contact_name", "phone", "email", "website_url",
    "street", "house_number", "postal_code", "city",
    "legal_form", "vat_id", "register_number", "register_court",
    "ceo_first_name", "ceo_last_name", "display_name",
)


class StammdatenAenderung(BaseModel):
    """Alles freiwillig — die Oberflaeche sendet nur, was sich geaendert hat."""

    model_config = {"extra": "allow"}


# **Eigener Pfad, nicht `PATCH /{lead_id}`.** Der Innendienst-Router liegt
# auf demselben Praefix und registriert dieselbe Adresse zuerst; meine
# Route wurde davon vollstaendig ueberdeckt (403 „Nur fuer den
# Innendienst"). `/stammdaten` ist ausserdem die genauere Sprache: Es
# geht um die Angaben des Betriebs, nicht um den Datensatz als Ganzes.
@kunden_router.patch("/{lead_id}/stammdaten")
def stammdaten_pflegen(
    lead_id: int,
    daten: StammdatenAenderung,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Der Kunde pflegt die Stammdaten seines Betriebs.

    **Warum es das gibt:** Rechtsform, Registernummer und Registergericht
    kennt der Betrieb, nicht wir — und sie muessen ins Impressum. Bisher
    wurden sie im Briefing per Hand abgefragt und vom Innendienst
    eingetragen.

    **Warum es hier steht und nicht im Lead-Router:** Dort haengt
    `edit_leads` davor, ein Innendienst-Recht. Diese Route ist die zweite
    des `kunden_router` neben dem Lesen — und sie prueft dieselbe Grenze:
    Wer nicht zum Innendienst gehoert, aendert nur den eigenen Betrieb.

    **Nicht erlaubte Felder werden verworfen und benannt.** Sie stillschweigend
    zu schlucken waere die schlechtere Haelfte von „nicht erlaubt": Der
    Absender glaubt dann, es sei gespeichert.
    """
    if current_user.role not in INNENDIENST and current_user.lead_id != lead_id:
        raise HTTPException(status_code=403, detail="Kein Zugriff auf diesen Betrieb")

    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Betrieb nicht gefunden")

    gesendet = daten.model_dump(exclude_none=True)
    # Der Innendienst behaelt seinen vollen Zugriff — die Liste gilt dem
    # Kunden. Sonst haette diese Aenderung dem Innendienst etwas weggenommen.
    erlaubt = (set(gesendet) if current_user.role in INNENDIENST
               else set(gesendet) & set(STAMMDATEN_DES_KUNDEN))
    verworfen = sorted(set(gesendet) - erlaubt)

    for feld in erlaubt:
        if hasattr(lead, feld):
            setattr(lead, feld, gesendet[feld])
    lead.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(lead)

    if verworfen:
        logger.info("Betrieb %s: %s nicht uebernommen (Rolle %s)",
                    lead_id, ", ".join(verworfen), current_user.role)

    return {
        "success": True,
        "id": lead.id,
        "stammdaten": {f: getattr(lead, f, None) for f in STAMMDATEN_DES_KUNDEN},
        "nicht_uebernommen": verworfen,
    }

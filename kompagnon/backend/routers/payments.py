"""
Stripe payment routes for KOMPAGNON checkout.
Creates Checkout Sessions, handles webhooks, returns session status.
"""
import os
import logging
import secrets
import threading
from datetime import datetime

import stripe
from services.base_urls import public_base_url
from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session

from database import Lead, User, Project, get_db

try:
    from seed_checklists import create_project_checklists
except ImportError:
    create_project_checklists = None

logger = logging.getLogger(__name__)

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
# Kein Modul-Konstantenwert mehr: der wird beim Import gelesen, und der
# Startvorgang setzt Variablen nach. public_base_url() liest bei jedem Aufruf.


def _check_stripe_config():
    if not stripe.api_key:
        logger.error(
            "STRIPE_SECRET_KEY nicht gesetzt — Stripe-Calls werden fehlschlagen. "
            "Bitte in Render.com Environment konfigurieren."
        )
    if not WEBHOOK_SECRET:
        logger.error(
            "STRIPE_WEBHOOK_SECRET nicht gesetzt — Webhook-Verifikation deaktiviert. "
            "Zahlungen werden NICHT verarbeitet. "
            "Bitte in Render.com Environment konfigurieren."
        )
    elif stripe.api_key and WEBHOOK_SECRET:
        logger.info("✓ Stripe-Konfiguration vollständig")

_check_stripe_config()

router = APIRouter(prefix="/api/payments", tags=["payments"])

def paketbezeichnung(db, slug: str) -> str:
    """Name und Preis eines Pakets — aus derselben Zeile, aus der auch
    abgerechnet wird.

    Hier stand bis zum 19.08.2026 eine feste Liste:

        "starter":   "Starter (5 Seiten · 1.500 EUR)"
        "kompagnon": "KOMPAGNON (8 Seiten · 2.000 EUR)"
        "premium":   "Premium (12 Seiten · 2.800 EUR)"

    Benutzt wird sie an genau einer Stelle — im **Text der Kundenmail** nach
    dem Kauf. Der Betrag daneben kommt aus `products`, das von Hand gepflegt
    wird. Zwei Quellen fuer dieselbe Zahl, und die eine steht in einer Mail,
    die der Kunde aufhebt.

    Sie waren bereits auseinandergelaufen: Premium stand im Frontend zweimal
    mit 2.500, hier mit 2.800; Landing.jsx nennt Kompagnon mit 3.500 statt
    2.000 (L-29).

    Ist das Produkt unbekannt, steht dort die Kennung — und **kein erfundener
    Preis**. Lieber nackt als falsch.
    """
    from sqlalchemy import text as _text

    try:
        zeile = db.execute(
            _text("SELECT name, price_brutto FROM products WHERE slug = :s"),
            {"s": slug},
        ).fetchone()
    except Exception:  # noqa: BLE001 — fehlende Tabelle darf die Mail nicht kippen
        db.rollback()
        return slug

    if not zeile:
        return slug

    name = zeile[0] or slug
    betrag = float(zeile[1] or 0)
    if betrag <= 0:
        return name

    # Deutsche Schreibweise: 1.500 statt 1,500
    return f"{name} ({betrag:,.0f} EUR)".replace(",", ".")

def projekt_festpreis(db, slug: str, bezahlt: float):
    """Der Festpreis eines Projekts — aus derselben Zeile, aus der auch
    abgerechnet wird.

    Hier stand bis zum 21.08.2026 eine zweite feste Liste, dieselbe Bauart
    wie `PACKAGE_NAMES` (L-29), nur folgenschwerer: Auf dieser Zahl rechnet
    `services/margin_calculator.py`. Ein Kunde, der 2.500 zahlte, bekam ein
    Projekt mit 2.800 Umsatz eingetragen — die Marge war zu hoch, und nichts
    im System haette widersprochen.

    Der Vorgabewert war der schlimmere Teil: Ein unbekanntes Paket bekam
    2.000 EUR **erfunden**, obwohl der tatsaechlich gezahlte Betrag im selben
    Aufruf danebenstand.

    Reihenfolge: die Produktzeile, sonst der gezahlte Betrag, sonst nichts.
    `None` heisst — die Spalte behaelt ihre Modellvorgabe, und niemand hat
    hier eine Zahl behauptet.
    """
    from sqlalchemy import text as _text

    try:
        zeile = db.execute(
            _text("SELECT price_brutto FROM products WHERE slug = :s"),
            {"s": slug},
        ).fetchone()
    except Exception:  # noqa: BLE001 — fehlende Tabelle darf den Kauf nicht kippen
        db.rollback()
        zeile = None

    if zeile:
        betrag = float(zeile[0] or 0)
        if betrag > 0:
            return betrag

    return float(bezahlt) if bezahlt and float(bezahlt) > 0 else None


@router.get("/packages")
def get_packages(db: Session = Depends(get_db)):
    from sqlalchemy import text
    import json as _j
    rows = db.execute(text(
        "SELECT slug, name, price_brutto, price_netto, tax_rate, "
        "short_desc, delivery_days, highlighted, highlight_label, "
        "features, payment_type, status "
        "FROM products WHERE status='live' ORDER BY sort_order ASC"
    )).mappings().all()
    result = {}
    for r in rows:
        feats = r["features"]
        if isinstance(feats, str):
            try:
                feats = _j.loads(feats)
            except Exception:
                feats = []
        result[r["slug"]] = {
            "name":            r["name"],
            "price":           int(float(r["price_brutto"]) * 100),
            "price_eur":       float(r["price_brutto"]),
            "netto":           float(r["price_netto"]),
            "tax":             float(r["tax_rate"]),
            "description":     r["short_desc"] or "",
            "features":        feats,
            "delivery_days":   r["delivery_days"],
            "highlighted":     r["highlighted"],
            "highlight_label": r["highlight_label"] or "",
        }
    return result


@router.post("/create-checkout")
async def create_checkout(request: Request, db: Session = Depends(get_db)):
    from sqlalchemy import text as _t
    import json as _j

    body = await request.json()
    # Kein Rueckfall auf einen Paketnamen (L-97, 23.08.2026). Hier stand
    # `body.get("package", "kompagnon")`. Solange KOMPAGNON verkaeuflich war,
    # hiess das: Wer die Angabe vergisst, kauft stillschweigend das mittlere
    # Paket. Seit die Bestandspakete archiviert sind, hiesse es: Die Abfrage
    # unten findet nichts und meldet „ungueltiges Paket" — richtig im
    # Ergebnis, irrefuehrend in der Begruendung. Fehlt die Angabe, ist das
    # ein Fehler des Aufrufers und wird als solcher benannt.
    package_id     = (body.get("package") or "").strip()
    if not package_id:
        raise HTTPException(400, "Kein Paket angegeben")
    customer_email = body.get("email", "")
    customer_name  = body.get("name", "")
    company_name   = body.get("company", "")
    website_url    = body.get("website_url", "")
    phone          = body.get("phone", "")

    row = db.execute(_t(
        "SELECT * FROM products WHERE slug=:s AND status='live'"
    ), {"s": package_id}).mappings().first()
    if not row:
        raise HTTPException(400, "Ungueltiges oder nicht verfügbares Paket")

    price_cents = int(float(row["price_brutto"]) * 100)
    package = {
        "name":            row["name"],
        "price":           price_cents,
        "description":     row["short_desc"] or "",
        "stripe_price_id": row["stripe_price_id"],
    }

    if not stripe.api_key:
        raise HTTPException(503, "Stripe nicht eingerichtet")

    if row["stripe_price_id"]:
        line_items_param = [{"price": row["stripe_price_id"], "quantity": 1}]
    else:
        line_items_param = [{
            "price_data": {
                "currency": "eur",
                "product_data": {
                    "name":        f"KOMPAGNON {package['name']}",
                    "description": package["description"],
                },
                "unit_amount": price_cents,
            },
            "quantity": 1,
        }]

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=line_items_param,
            mode="payment",
            customer_email=customer_email or None,
            metadata={
                "package":          package_id,
                "company_name":     company_name,
                "customer_name":    customer_name,
                "customer_email":   customer_email,
                "website_url":      website_url,
                "phone":            phone,
            },
            success_url=f"{public_base_url()}/checkout/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{public_base_url()}/checkout?cancelled=1",
            locale="de",
        )
        return {"checkout_url": session.url, "session_id": session.id}
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {e}")
        raise HTTPException(400, str(e))


@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig = request.headers.get("stripe-signature")

    if not WEBHOOK_SECRET:
        logger.error(
            "Stripe Webhook empfangen aber STRIPE_WEBHOOK_SECRET nicht gesetzt — "
            "Zahlung wird NICHT verarbeitet. Bitte Env-Var in Render setzen."
        )
        # 503 statt 200: Stripe macht Retry und der Fehler bleibt sichtbar,
        # bis die Konfiguration nachgezogen wird.
        raise HTTPException(status_code=503, detail="webhook_secret_not_configured")

    try:
        event = stripe.Webhook.construct_event(payload, sig, WEBHOOK_SECRET)
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Stripe Signatur ungültig: {e}")
        raise HTTPException(400, "Ungültige Webhook-Signatur")
    except Exception as e:
        logger.error(f"Stripe Webhook Fehler: {e}")
        raise HTTPException(400, "Webhook Fehler")

    if event["type"] == "checkout.session.completed":
        session_obj = event["data"]["object"]
        try:
            _handle_successful_payment(session_obj, db)
        except Exception as e:
            logger.error(
                f"Stripe: _handle_successful_payment Fehler für "
                f"Session {session_obj.get('id', '?')}: {e}",
                exc_info=True,
            )
            return {"status": "error_logged"}

    return {"status": "ok"}


class _UebersprungenerSchritt(Exception):
    """Ein Schritt, den dieses Produkt nicht hat.

    **Warum eine Ausnahme und kein `if` um den ganzen Block.** Die beiden
    Bloecke darunter stehen bereits in `try/except Exception`, und ihre
    Einrueckung ist tief. Ein zusaetzliches `if` haette sie um eine Ebene
    verschoben — eine Aenderung von hundert Zeilen am Zahlungspfad, in der
    ein echter Fehler leicht untergeht. So bleibt der Eingriff eine Zeile,
    und der Unterschied ist im Diff zu sehen.

    Das `except Exception` faengt sie mit; der Protokolleintrag sagt dann
    „uebersprungen", nicht „fehlgeschlagen".
    """


def _handle_successful_payment(session: dict, db: Session):
    """
    Nach erfolgreicher Stripe-Zahlung:
    1. Lead anlegen
    2. User + temporaeres Passwort anlegen
    3. Willkommens-E-Mail senden
    4. Projekt anlegen
    5. Content-Scraper im Hintergrund starten
    """
    from sqlalchemy import text as _t

    meta        = session.get("metadata", {})
    email       = meta.get("customer_email") or session.get("customer_email", "")
    company     = meta.get("company_name", "")
    name        = meta.get("customer_name", "")
    # Auch hier ohne Rueckfall (L-97). Die Metadaten stammen aus unserer
    # eigenen Stripe-Sitzung, die Angabe ist also normalerweise da. Fehlt sie,
    # ist ein leerer Wert die ehrlichere Antwort als ein erfundenes Paket:
    # `projekt_festpreis` faellt dann auf den tatsaechlich gezahlten Betrag
    # zurueck (L-29), und `paketbezeichnung` schreibt die Kennung statt eines
    # falschen Preises in die Kundenmail.
    package_id  = (meta.get("package") or "").strip()
    website_url = meta.get("website_url", "")
    phone_nr    = meta.get("phone", "") or \
                  (session.get("customer_details") or {}).get("phone", "")
    amount      = (session.get("amount_total", 0) or 0) / 100
    stripe_session_id = session.get("id", "")

    # ── IDEMPOTENZ-GUARD ─────────────────────────────────────────────────────
    # Stripe sendet Webhooks mehrfach bei Timeout. Ohne diesen Guard entstehen
    # doppelte Leads, User und Projekte. Notes-Feld enthält die Session-ID.
    if stripe_session_id:
        from sqlalchemy import text as _text
        existing_lead = db.execute(_text(
            "SELECT id FROM leads WHERE notes LIKE :session_pattern LIMIT 1"
        ), {"session_pattern": f"%{stripe_session_id}%"}).fetchone()

        if existing_lead:
            logger.info(
                f"Stripe Webhook: Session {stripe_session_id} bereits verarbeitet "
                f"(Lead {existing_lead[0]}) — übersprungen"
            )
            return

    logger.info(
        f"Stripe: Neue Zahlung wird verarbeitet — "
        f"{company} ({email}) | {amount:.2f} EUR | Session: {stripe_session_id}"
    )

    # ── WELCHE SCHRITTE DIESER KAUF AUSLOEST ─────────────────
    # **Bis zum 27.08.2026 waren es immer dieselben fuenf** — der
    # Websprint-Ablauf, auch fuer ein PDF-Workbook. `products.webhook_actions`
    # trug die Liste laengst und wurde von keiner Zeile gelesen.
    #
    # Die Vorgabe bleibt das Verhalten von heute: Ein Produkt ohne Eintrag
    # bekommt weiter alle fuenf. Siehe `services/kaufabwicklung.py`.
    from services.kaufabwicklung import (AUFTRAGSBESTAETIGUNG, KONTO, LEAD,
                                         PROJEKT, SCRAPER, WILLKOMMEN,
                                         schritte_fuer)

    # **Diese Abfrage darf den Kauf nicht kosten.** Beim ersten Anlauf stand
    # sie ohne Absicherung hier, und ein Fehlschlag vergiftete die Sitzung:
    # `current transaction is aborted, commands ignored until end of
    # transaction block` — danach scheitert **jede** weitere Anweisung, also
    # auch die Kundenanlage. Das Geld waere da, der Kunde nicht.
    #
    # Gefunden hat es der Gesamtlauf der Tests, nicht der Einzellauf: Die
    # beiden Dateien fuer sich blieben gruen.
    #
    # Bricht sie, gilt die Vorgabe — das Verhalten von vor dem 27.08.2026.
    _produktzeile = None
    if package_id:
        try:
            _produktzeile = db.execute(_t(
                "SELECT webhook_actions FROM products WHERE slug=:s"
            ), {"s": package_id}).mappings().first()
        except Exception as fehler:        # noqa: BLE001 — siehe Kommentar
            db.rollback()                  # sonst bleibt die Sitzung vergiftet
            logger.warning(
                "Stripe: Kaufaktionen fuer %s nicht lesbar (%s) — "
                "es gilt der vollstaendige Ablauf", package_id, fehler)
    schritte = schritte_fuer(_produktzeile)
    logger.info("Stripe: Kaufabwicklung fuer %s — Schritte: %s",
                package_id or "(ohne Produktangabe)",
                ", ".join(sorted(schritte)) or "keine")

    name_parts = name.split(" ", 1)
    first_name = name_parts[0] if name_parts else ""
    last_name  = name_parts[1] if len(name_parts) > 1 else ""

    # ── 1. LEAD ANLEGEN ──────────────────────────────────────
    lead = Lead(
        company_name = company or email or "Stripe-Kunde",
        contact_name = name,
        email        = email,
        phone        = phone_nr,
        website_url  = website_url,
        lead_source  = "stripe_checkout",
        status       = "won",
        notes        = (
            f"Zahlung: {amount:.2f} EUR | "
            f"Paket: {package_id} | "
            f"Stripe: {session.get('id', '')}"
        ),
    )
    db.add(lead)
    db.flush()  # lead.id jetzt verfuegbar

    # Customer-Token fuer den Token-basierten Portal-Zugang (/portal/{token}).
    # Erlaubt direkten Login ohne Passwort-Eingabe, Sicherheit via Email-Domain-Verify.
    from services.qr_service import generate_token
    lead.customer_token = generate_token()
    lead.customer_token_created_at = datetime.utcnow()

    logger.info(f"Stripe: Lead {lead.id} angelegt fuer {company}")

    # ── 2. USER ANLEGEN ──────────────────────────────────────
    temp_pw = None
    if email and KONTO in schritte:
        existing = db.query(User).filter(User.email == email).first()
        if not existing:
            from auth import hash_password
            temp_pw = secrets.token_urlsafe(12)
            user = User(
                email         = email,
                password_hash = hash_password(temp_pw),
                first_name    = first_name,
                last_name     = last_name,
                role          = "kunde",
                lead_id       = lead.id,
                is_active     = True,
                is_verified   = True,
            )
            db.add(user)
            logger.info(f"Stripe: User {email} angelegt (kunde)")
        else:
            logger.info(f"Stripe: User {email} existiert bereits")

    # ── 3. PROJEKT ANLEGEN ───────────────────────────────────
    # **Der Schritt, um den es geht.** Ein Workbook-Kaeufer bekam hier ein
    # Website-Projekt, das beim Schritt „Veroeffentlichung" haengen bleibt,
    # weil es keine Domain gibt.
    project_id = None
    try:
        if PROJEKT not in schritte:
            raise _UebersprungenerSchritt(PROJEKT)
        existing_project = db.query(Project).filter(
            Project.lead_id == lead.id
        ).first()
        if not existing_project:
            # Der Preis kommt aus der Produktzeile, sonst aus dem, was
            # Stripe tatsaechlich abgebucht hat (L-29).
            festpreis = projekt_festpreis(db, package_id, amount)
            project = Project(
                lead_id        = lead.id,
                status         = "phase_1",
                payment_status = "bezahlt",
                start_date     = datetime.utcnow(),
                fixed_price    = festpreis,
                hourly_rate    = 45.0,
                ai_tool_costs  = 50.0,
            )
            db.add(project)
            db.flush()
            project_id = project.id
            if create_project_checklists:
                create_project_checklists(db, project.id)
            logger.info(f"Stripe: Projekt {project.id} fuer Lead {lead.id} angelegt")
        else:
            project_id = existing_project.id
            logger.info(f"Stripe: Projekt bereits vorhanden ({project_id})")
    except _UebersprungenerSchritt:
        # **Kein Fehler.** Dieses Produkt hat den Schritt nicht — eine
        # Meldung „fehlgeschlagen" haette jemanden auf die Suche nach einem
        # Fehler geschickt, den es nicht gibt.
        logger.info("Stripe: Kein Projekt fuer %s — nicht vorgesehen",
                    package_id or "dieses Produkt")
    except Exception as e:
        logger.error(f"Stripe: Projekt-Anlage fehlgeschlagen: {e}")
        # Kein raise — Commit laeuft trotzdem durch

    # ── COMMIT (Lead + User + Projekt) ───────────────────────
    db.commit()

    # ── AUTO-SEQUENZ FÜR STRIPE-KÄUFER ──────────────────────
    try:
        from services.sequence_runner import start_sequence_for_lead
        import threading
        threading.Thread(
            target=start_sequence_for_lead,
            args=(lead.id,),
            daemon=True,
        ).start()
    except Exception as e:
        logger.warning(f"Stripe Auto-Sequenz Fehler: {e}")

    # ── AUFTRAGSBESTÄTIGUNG PDF ──────────────────────────────
    pdf_path = None
    try:
        if AUFTRAGSBESTAETIGUNG not in schritte:
            raise _UebersprungenerSchritt(AUFTRAGSBESTAETIGUNG)
        from services.auftragsbestaetigung_pdf import save_auftragsbestaetigung
        pdf_path = save_auftragsbestaetigung(
            session_id     = session.get("id", ""),
            customer_name  = name or company or email,
            customer_email = email,
            company_name   = company or "",
            package_id     = package_id,
            amount_eur     = amount,
            # Ohne die Sitzung kaeme der Preis aus einer festen Liste — bis
            # zum 22.08.2026 tat er das, und der gezahlte Betrag daneben
            # wurde nicht angesehen (L-29).
            db             = db,
        )
        if project_id:
            proj = db.query(Project).filter(Project.id == project_id).first()
            if proj:
                proj.auftragsbestaetigung_pdf = pdf_path
                db.commit()
        logger.info(f"Auftragsbestaetigung gespeichert: {pdf_path}")
    except _UebersprungenerSchritt:
        logger.info("Stripe: Keine Auftragsbestaetigung fuer %s — "
                    "nicht vorgesehen", package_id or "dieses Produkt")
    except Exception as e:
        logger.error(f"Auftragsbestaetigung PDF Fehler: {e}")

    # ── 4. WILLKOMMENS-E-MAIL ────────────────────────────────
    if email and WILLKOMMEN in schritte:
        try:
            from services.email import anhang_aus_datei, send_email
            from services.qr_service import get_portal_url
            # Token-Direktlink als primaerer Einstieg (passwortfrei, Domain-Verify).
            # Fallback auf /portal/login bleibt im Mail-Body als Login-Daten.
            portal_url = (
                get_portal_url(lead.customer_token)
                if lead.customer_token
                else public_base_url() + "/portal/login"
            )
            paket_name = paketbezeichnung(db, package_id)

            # Passwort-Abschnitt: nur anzeigen wenn neuer User
            if temp_pw:
                pw_section = f"""
                <h3 style="color:#1a2332;font-size:15px;margin:24px 0 10px">
                  Ihre Zugangsdaten:
                </h3>
                <table style="width:100%;border-collapse:collapse;
                              border:1px solid #e2e8f0;border-radius:8px;
                              overflow:hidden">
                  <tr style="background:#f8f9fa">
                    <td style="padding:10px 14px;font-weight:600;
                               font-size:13px;color:#64748b;
                               border-bottom:1px solid #e2e8f0;
                               width:120px">E-Mail</td>
                    <td style="padding:10px 14px;
                               border-bottom:1px solid #e2e8f0;
                               font-size:13px">{email}</td>
                  </tr>
                  <tr>
                    <td style="padding:10px 14px;font-weight:600;
                               font-size:13px;color:#64748b;
                               background:#f8f9fa">Passwort</td>
                    <td style="padding:10px 14px;font-family:monospace;
                               font-size:16px;letter-spacing:2px;
                               font-weight:600;color:#008eaa">
                      {temp_pw}
                    </td>
                  </tr>
                </table>
                <p style="font-size:12px;color:#E24B4A;margin:8px 0 0">
                  Bitte aendern Sie Ihr Passwort nach dem ersten Login.
                </p>
                """
            else:
                pw_section = """
                <p style="color:#64748b;font-size:13px">
                  Melden Sie sich mit Ihren bestehenden Zugangsdaten an.
                </p>
                """

            html_body = f"""
            <div style="font-family:Arial,sans-serif;
                        max-width:600px;margin:0 auto">
              <div style="background:#008eaa;padding:28px;
                          text-align:center;
                          border-radius:12px 12px 0 0">
                <div style="font-size:36px;margin-bottom:8px">🎉</div>
                <h1 style="color:white;margin:0;font-size:22px;
                           font-weight:700">
                  Willkommen bei KOMPAGNON!
                </h1>
              </div>
              <div style="padding:28px 32px;background:#ffffff">
                <p style="font-size:15px;color:#1a2332;margin-top:0">
                  Hallo {first_name or company or 'dort'},
                </p>
                <p style="color:#64748b;line-height:1.7;font-size:14px">
                  vielen Dank fuer Ihren Kauf! Ihre Zahlung ueber
                  <strong>{amount:.2f} EUR</strong> fuer das Paket
                  <strong>{paket_name}</strong> wurde erfolgreich
                  verarbeitet.
                </p>

                {pw_section}

                <div style="text-align:center;margin:28px 0">
                  <a href="{portal_url}"
                     style="display:inline-block;background:#008eaa;
                            color:white;padding:14px 32px;
                            border-radius:8px;text-decoration:none;
                            font-weight:700;font-size:15px">
                    Jetzt einloggen &#8594;
                  </a>
                </div>

                <h3 style="color:#1a2332;font-size:15px;
                           margin:24px 0 10px">
                  Ihre naechsten Schritte:
                </h3>
                <table style="width:100%">
                  <tr>
                    <td style="padding:6px 0;vertical-align:top;
                               width:28px;font-size:16px">1.</td>
                    <td style="padding:6px 0;font-size:13px;
                               color:#64748b;line-height:1.6">
                      Im Kundenportal einloggen und Briefing
                      ausfuellen (ca. 5 Min.)
                    </td>
                  </tr>
                  <tr>
                    <td style="padding:6px 0;vertical-align:top;
                               font-size:16px">2.</td>
                    <td style="padding:6px 0;font-size:13px;
                               color:#64748b;line-height:1.6">
                      Wir melden uns innerhalb von 24 Stunden
                      fuer den Strategy Workshop
                    </td>
                  </tr>
                  <tr>
                    <td style="padding:6px 0;vertical-align:top;
                               font-size:16px">3.</td>
                    <td style="padding:6px 0;font-size:13px;
                               color:#64748b;line-height:1.6">
                      Ihre neue Website ist in 14 Werktagen live
                    </td>
                  </tr>
                </table>

                <p style="color:#94a3b8;font-size:12px;
                          margin-top:24px;line-height:1.6">
                  Fragen? Antworten Sie einfach auf diese E-Mail
                  oder schreiben Sie uns:
                  <a href="mailto:info@kompagnon.eu"
                     style="color:#008eaa">
                    info@kompagnon.eu
                  </a>
                </p>
              </div>
              <div style="padding:16px;background:#f8f9fa;
                          text-align:center;
                          border-radius:0 0 12px 12px">
                <p style="color:#94a3b8;font-size:11px;margin:0">
                  KOMPAGNON Communications BP GmbH &bull;
                  kompagnon.eu
                </p>
              </div>
            </div>
            """

            ok = send_email(
                to_email        = email,
                subject         = "Willkommen bei KOMPAGNON — Ihre Zugangsdaten",
                html_body       = html_body,
                # `attachments`, nicht `attachment_path` — Letzteres gab es
                # nie, und der TypeError verhinderte **die ganze Mail** samt
                # Zugangsdaten (gefunden 26.08.2026, Waechter:
                # `test_mailaufrufe_passen.py`).
                attachments     = anhang_aus_datei(
                    pdf_path, "KOMPAGNON-Auftragsbestaetigung.pdf"),
            )
            if ok:
                logger.info(f"Stripe: Willkommens-E-Mail gesendet an {email}")
            else:
                logger.warning(f"Stripe: Willkommens-E-Mail an {email} fehlgeschlagen")

        except Exception as e:
            logger.error(f"Stripe: Willkommens-E-Mail Fehler: {e}")
            # E-Mail-Fehler darf Webhook NICHT zum Fehlschlagen bringen

    # ── 5. CONTENT-SCRAPER IM HINTERGRUND ───────────────────
    if website_url and lead.id and SCRAPER in schritte:
        def _scrape_in_background(lead_id: int):
            try:
                import asyncio
                from database import SessionLocal
                from services.lead_enrichment import enrich_lead
                _db = SessionLocal()
                try:
                    asyncio.run(enrich_lead(lead_id, _db))
                    logger.info(
                        f"Stripe: Content-Scraper abgeschlossen "
                        f"fuer Lead {lead_id}"
                    )
                finally:
                    _db.close()
            except Exception as e:
                logger.error(f"Stripe: Scraper Fehler fuer Lead {lead_id}: {e}")

        t = threading.Thread(
            target=_scrape_in_background,
            args=(lead.id,),
            daemon=True,
        )
        t.start()
        logger.info(
            f"Stripe: Content-Scraper gestartet fuer Lead {lead.id} "
            f"({website_url})"
        )

    logger.info(
        f"Stripe: Zahlung verarbeitet — "
        f"Lead {lead.id} | Projekt {project_id} | {company} | "
        f"{amount:.2f} EUR | {package_id}"
    )


@router.get("/session/{session_id}")
async def get_session_status(session_id: str):
    if not stripe.api_key:
        raise HTTPException(503, "Stripe nicht eingerichtet")
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        return {
            "status": session.payment_status,
            "customer_email": (session.customer_details.email if session.customer_details else ""),
            "amount": (session.amount_total or 0) / 100,
            "package": (session.metadata or {}).get("package", ""),
        }
    except Exception as e:
        raise HTTPException(400, str(e))

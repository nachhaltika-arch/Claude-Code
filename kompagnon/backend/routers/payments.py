"""
Stripe payment routes for KOMPAGNON checkout.
Creates Checkout Sessions, handles webhooks, returns session status.
"""
import os
import logging
import secrets

import stripe
from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session

from database import Lead, User, get_db

logger = logging.getLogger(__name__)

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://kompagnon-frontend.onrender.com")

router = APIRouter(prefix="/api/payments", tags=["payments"])

PACKAGE_NAMES = {
    "starter":   "Starter (5 Seiten)",
    "kompagnon": "KOMPAGNON (8 Seiten)",
    "premium":   "Premium (12 Seiten)",
}

PACKAGES = {
    "starter": {
        "name": "Starter",
        "price": 150000,
        "description": "5 Seiten, SEO Basic, Mobiloptimierung, 14 Tage",
    },
    "kompagnon": {
        "name": "Kompagnon",
        "price": 200000,
        "description": "8 Seiten, SEO + GEO, Workshop, Nachbetreuung",
    },
    "premium": {
        "name": "Premium",
        "price": 280000,
        "description": "12 Seiten, Shop-Ready, Fotoshooting, 3 Monate Betreuung",
    },
}


@router.get("/packages")
def get_packages():
    return PACKAGES


@router.post("/create-checkout")
async def create_checkout(request: Request):
    body = await request.json()
    package_id = body.get("package", "kompagnon")
    customer_email = body.get("email", "")
    customer_name = body.get("name", "")
    company_name = body.get("company", "")
    website_url = body.get("website_url", "")
    phone = body.get("phone", "")

    package = PACKAGES.get(package_id)
    if not package:
        raise HTTPException(400, "Ungueltiges Paket")

    if not stripe.api_key:
        raise HTTPException(500, "Stripe nicht konfiguriert")

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "eur",
                    "product_data": {
                        "name": f"KOMPAGNON {package['name']}",
                        "description": package["description"],
                    },
                    "unit_amount": package["price"],
                },
                "quantity": 1,
            }],
            mode="payment",
            customer_email=customer_email or None,
            metadata={
                "package": package_id,
                "company_name": company_name,
                "customer_name": customer_name,
                "customer_email": customer_email,
                "website_url": website_url,
                "phone": phone,
            },
            success_url=f"{FRONTEND_URL}/checkout/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{FRONTEND_URL}/checkout?cancelled=1",
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
        logger.warning("Stripe webhook secret not configured")
        raise HTTPException(400, "Webhook nicht konfiguriert")

    try:
        event = stripe.Webhook.construct_event(payload, sig, WEBHOOK_SECRET)
    except Exception as e:
        logger.error(f"Webhook verification failed: {e}")
        raise HTTPException(400, "Webhook Fehler")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        _handle_successful_payment(session, db)

    return {"status": "ok"}


def _handle_successful_payment(session: dict, db: Session):
    """Create Lead + User after successful Stripe payment."""
    meta = session.get("metadata", {})
    email = meta.get("customer_email") or session.get("customer_email", "")
    company = meta.get("company_name", "")
    name = meta.get("customer_name", "")
    package_id = meta.get("package", "kompagnon")
    website_url = meta.get("website_url", "")
    phone_nr = meta.get("phone", "") or (session.get("customer_details") or {}).get("phone", "")
    amount = (session.get("amount_total", 0) or 0) / 100

    name_parts = name.split(" ", 1)
    first_name = name_parts[0] if name_parts else ""
    last_name = name_parts[1] if len(name_parts) > 1 else ""

    # Create lead
    lead = Lead(
        company_name=company or email or "Stripe-Kunde",
        contact_name=name,
        email=email,
        phone=phone_nr,
        website_url=website_url,
        lead_source="stripe_checkout",
        status="won",
        notes=f"Zahlung erhalten: {amount} EUR | Paket: {package_id} | Stripe: {session.get('id', '')}",
    )
    db.add(lead)
    db.flush()

    paket_name = PACKAGE_NAMES.get(package_id, package_id)
    portal_url = os.getenv("FRONTEND_URL", "https://kompagnon-frontend.onrender.com") + "/portal/login"

    # Create user account if email provided and not existing
    if email:
        existing = db.query(User).filter(User.email == email).first()
        if not existing:
            from auth import hash_password
            temp_pw = secrets.token_urlsafe(12)
            user = User(
                email=email,
                password_hash=hash_password(temp_pw),
                first_name=first_name,
                last_name=last_name,
                role="kunde",
                lead_id=lead.id,
                is_active=True,
                is_verified=True,
            )
            db.add(user)
            logger.info(f"Stripe: User {email} created (kunde)")

            # Willkommens-E-Mail mit Zugangsdaten
            try:
                from services.email import send_email
                html_body = f"""
                <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto">
                  <div style="background:#008eaa;padding:30px;text-align:center">
                    <h1 style="color:white;margin:0;font-size:24px">Willkommen bei KOMPAGNON</h1>
                  </div>
                  <div style="padding:32px;background:#ffffff">
                    <p>Hallo {first_name or 'dort'},</p>
                    <p>vielen Dank fuer Ihren Kauf! Ihre Zahlung ueber
                       <strong>{amount:.2f} EUR</strong> fuer das Paket
                       <strong>{paket_name}</strong> wurde erfolgreich verarbeitet.</p>
                    <h3 style="color:#1a2332">Ihre Zugangsdaten:</h3>
                    <table style="border-collapse:collapse;width:100%">
                      <tr>
                        <td style="padding:8px;border:1px solid #e2e8f0;
                                   background:#f8f9fa;font-weight:bold">E-Mail</td>
                        <td style="padding:8px;border:1px solid #e2e8f0">{email}</td>
                      </tr>
                      <tr>
                        <td style="padding:8px;border:1px solid #e2e8f0;
                                   background:#f8f9fa;font-weight:bold">
                          Temporaeres Passwort</td>
                        <td style="padding:8px;border:1px solid #e2e8f0;
                                   font-family:monospace;font-size:16px;
                                   letter-spacing:2px">{temp_pw}</td>
                      </tr>
                    </table>
                    <p style="color:#E24B4A;font-size:13px">
                      Bitte aendern Sie Ihr Passwort nach dem ersten Login.
                    </p>
                    <div style="text-align:center;margin:32px 0">
                      <a href="{portal_url}"
                         style="background:#008eaa;color:white;padding:14px 32px;
                                border-radius:6px;text-decoration:none;
                                font-weight:bold;font-size:16px">
                        Jetzt einloggen
                      </a>
                    </div>
                    <h3 style="color:#1a2332">Naechste Schritte:</h3>
                    <ol style="color:#64748b;line-height:2">
                      <li>Melden Sie sich mit Ihren Zugangsdaten an</li>
                      <li>Fuellen Sie das Briefing-Formular aus</li>
                      <li>Wir melden uns innerhalb von 24 Stunden fuer
                          den Strategy Workshop</li>
                    </ol>
                    <p>Bei Fragen erreichen Sie uns jederzeit unter
                       <a href="mailto:info@kompagnon.eu">info@kompagnon.eu</a></p>
                  </div>
                  <div style="padding:20px;background:#f8f9fa;text-align:center">
                    <p style="color:#94a3b8;font-size:12px;margin:0">
                      KOMPAGNON Communications BP GmbH &bull; kompagnon.eu
                    </p>
                  </div>
                </div>
                """
                send_email(
                    to_email=email,
                    subject="Willkommen bei KOMPAGNON — Ihre Zugangsdaten",
                    html_body=html_body,
                )
                logger.info(f"Willkommens-E-Mail gesendet an {email}")
            except Exception as e:
                logger.error(f"Willkommens-E-Mail Fehler: {e}")

        else:
            # User existiert bereits — Bestaetigungs-E-Mail ohne Passwort
            try:
                from services.email import send_email
                html_body = f"""
                <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto">
                  <div style="background:#008eaa;padding:30px;text-align:center">
                    <h1 style="color:white;margin:0;font-size:24px">Bestellung bestaetigt</h1>
                  </div>
                  <div style="padding:32px;background:#ffffff">
                    <p>Hallo {first_name or 'dort'},</p>
                    <p>Ihre Zahlung ueber <strong>{amount:.2f} EUR</strong> fuer das Paket
                       <strong>{paket_name}</strong> wurde erfolgreich bestaetigt.</p>
                    <p>Bitte melden Sie sich mit Ihren bestehenden Zugangsdaten an:</p>
                    <div style="text-align:center;margin:32px 0">
                      <a href="{portal_url}"
                         style="background:#008eaa;color:white;padding:14px 32px;
                                border-radius:6px;text-decoration:none;
                                font-weight:bold;font-size:16px">
                        Zum Portal
                      </a>
                    </div>
                    <p>Bei Fragen erreichen Sie uns unter
                       <a href="mailto:info@kompagnon.eu">info@kompagnon.eu</a></p>
                  </div>
                  <div style="padding:20px;background:#f8f9fa;text-align:center">
                    <p style="color:#94a3b8;font-size:12px;margin:0">
                      KOMPAGNON Communications BP GmbH &bull; kompagnon.eu
                    </p>
                  </div>
                </div>
                """
                send_email(
                    to_email=email,
                    subject="Neue Bestellung bei KOMPAGNON bestaetigt",
                    html_body=html_body,
                )
                logger.info(f"Bestaetigungs-E-Mail gesendet an {email}")
            except Exception as e:
                logger.error(f"Bestaetigungs-E-Mail Fehler: {e}")

    db.commit()
    logger.info(f"Stripe: Lead {lead.id} created for {company} ({amount} EUR, {package_id})")


@router.get("/session/{session_id}")
async def get_session_status(session_id: str):
    if not stripe.api_key:
        raise HTTPException(500, "Stripe nicht konfiguriert")
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

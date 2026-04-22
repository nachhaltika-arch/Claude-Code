"""
Hilfsfunktionen fuer Stripe-Subscription des GEO Add-ons.

Der Preis ist NICHT hardcodiert — er kommt aus geo_analyses.upsell_price.
Der Admin setzt den Preis pro Projekt individuell im KAS.

Wichtig: Stripe braucht einen "Price" (price_xxx) fuer Subscriptions.
Wir erstellen diesen Price on-the-fly wenn er noch nicht existiert,
oder verwenden den gecachten price_id aus geo_analyses.stripe_price_id.
"""

import stripe
import os
import logging

logger = logging.getLogger(__name__)

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")

GEO_PRODUCT_NAME = "KOMPAGNON KI-Sichtbarkeit Add-on"
GEO_PRODUCT_DESCRIPTION = "Monatliches GEO/GAIO Monitoring: llms.txt, schema.org, KI-Sichtbarkeits-Report"


def get_or_create_stripe_price(monthly_price_eur: float) -> str:
    """Gibt eine Stripe Price ID zurueck. Erstellt Price/Product on-the-fly wenn noetig."""
    price_cents = int(round(monthly_price_eur * 100))

    try:
        existing = stripe.Price.list(
            active=True,
            currency="eur",
            type="recurring",
            limit=20,
        )
        for p in existing.data:
            if (
                p.unit_amount == price_cents
                and p.recurring
                and p.recurring.interval == "month"
                and p.metadata.get("kompagnon_addon") == "geo"
            ):
                logger.info("Stripe Price gefunden: %s (%d Cent)", p.id, price_cents)
                return p.id

        products = stripe.Product.list(active=True, limit=20)
        geo_product = None
        for prod in products.data:
            if prod.metadata.get("kompagnon_addon") == "geo":
                geo_product = prod
                break

        if not geo_product:
            geo_product = stripe.Product.create(
                name=GEO_PRODUCT_NAME,
                description=GEO_PRODUCT_DESCRIPTION,
                metadata={"kompagnon_addon": "geo"},
            )
            logger.info("Stripe Produkt erstellt: %s", geo_product.id)

        new_price = stripe.Price.create(
            product=geo_product.id,
            unit_amount=price_cents,
            currency="eur",
            recurring={"interval": "month"},
            metadata={"kompagnon_addon": "geo", "price_eur": str(monthly_price_eur)},
        )
        logger.info("Stripe Price erstellt: %s (%d Cent/Monat)", new_price.id, price_cents)
        return new_price.id

    except stripe.error.StripeError as e:
        logger.error("Stripe Price creation failed: %s", e)
        raise


def cancel_subscription(stripe_subscription_id: str) -> bool:
    """Kuendigt eine Stripe Subscription zum Periodenende."""
    try:
        stripe.Subscription.modify(
            stripe_subscription_id,
            cancel_at_period_end=True,
        )
        logger.info("Subscription %s zum Periodenende gekuendigt", stripe_subscription_id)
        return True
    except stripe.error.StripeError as e:
        logger.error("Kuendigung fehlgeschlagen: %s", e)
        return False

"""
Einmalig ausfuehren: python scripts/seed_impuls.py

Legt das IMPULS ISB-158 Beratungsprodukt in der products-Tabelle an.
Idempotent — ueberspringt wenn slug='impuls' bereits existiert.
"""
import os
import json
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("DATABASE_URL nicht gesetzt.")
    raise SystemExit(1)

engine = create_engine(DATABASE_URL)

impuls_product = {
    "slug": "impuls",
    "name": "IMPULS by KOMPAGNON",
    "short_desc": "Geförderte Unternehmensberatung — 50 % vom Land RLP",
    "long_desc": (
        "IMPULS ist das ISB-158-Beratungsprogramm von KOMPAGNON für KMU in Rheinland-Pfalz. "
        "Das Land Rheinland-Pfalz übernimmt 50 % der Beratungskosten (max. 500 €/Tagewerk). "
        "Beratungsschwerpunkte: Strategie, Marketing, Digitalisierung, Kommunikationsdesign. "
        "Finanzierung des Eigenanteils über MMV Leasing in 36 Monatsraten. "
        "Alle Ergebnisse werden in einem persönlichen, passwortgeschützten Online-Portal bereitgestellt."
    ),
    "price_brutto": 20000.00,
    "price_netto": 16806.72,
    "tax_rate": 19,
    "payment_type": "once",
    "delivery_days": 90,
    "highlighted": True,
    "highlight_label": "50 % Förderung",
    "features": [
        "ISB-158 Förderung: 50 % vom Land Rheinland-Pfalz",
        "Bis zu 20 Tagewerke à 8 Stunden Beratung",
        "Strategie, Marketing & Vertriebsoptimierung",
        "Digitalisierung & KI-Einsatz im Unternehmen",
        "Kommunikations- & Designberatung (max. 3 TW)",
        "Persönliches Ergebnis-Portal (passwortgeschützt)",
        "Leasingfinanzierung: ~145 €/Monat über MMV",
        "Wir übernehmen Antragstellung & Dokumentation",
    ],
    "checkout_fields": ["name", "company", "email", "phone", "message"],
    "webhook_actions": ["create_lead", "send_welcome_email"],
    "status": "draft",
    "sort_order": 10,
}

with engine.connect() as conn:
    existing = conn.execute(
        text("SELECT id FROM products WHERE slug = :slug"),
        {"slug": impuls_product["slug"]},
    ).first()

    if existing:
        print("IMPULS-Produkt existiert bereits. Kein Duplikat angelegt.")
    else:
        conn.execute(
            text("""
                INSERT INTO products (
                    slug, name, short_desc, long_desc,
                    price_brutto, price_netto, tax_rate,
                    payment_type, delivery_days, highlighted,
                    highlight_label, features, checkout_fields,
                    webhook_actions, status, sort_order
                ) VALUES (
                    :slug, :name, :sd, :ld,
                    :pb, :pn, :tr,
                    :pt, :dd, :hl,
                    :hll, CAST(:feat AS jsonb), CAST(:cf AS jsonb),
                    CAST(:wa AS jsonb), :status, :so
                )
            """),
            {
                "slug": impuls_product["slug"],
                "name": impuls_product["name"],
                "sd": impuls_product["short_desc"],
                "ld": impuls_product["long_desc"],
                "pb": impuls_product["price_brutto"],
                "pn": impuls_product["price_netto"],
                "tr": impuls_product["tax_rate"],
                "pt": impuls_product["payment_type"],
                "dd": impuls_product["delivery_days"],
                "hl": impuls_product["highlighted"],
                "hll": impuls_product["highlight_label"],
                "feat": json.dumps(impuls_product["features"]),
                "cf": json.dumps(impuls_product["checkout_fields"]),
                "wa": json.dumps(impuls_product["webhook_actions"]),
                "status": impuls_product["status"],
                "so": impuls_product["sort_order"],
            },
        )
        conn.commit()
        print("IMPULS-Produkt erfolgreich angelegt.")

# Landing-Page-Eintrag in public_pages — idempotent via ON CONFLICT.
with engine.connect() as conn:
    conn.execute(text("""
        INSERT INTO public_pages (slug, name, page_type, status, react_component)
        VALUES ('/paket/impuls', 'IMPULS: Geförderte Beratung', 'paket', 'live', 'PackageImpuls')
        ON CONFLICT (slug) DO NOTHING
    """))
    conn.commit()
    print("IMPULS Landing Page in public_pages eingetragen (oder bereits vorhanden).")

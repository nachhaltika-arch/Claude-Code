"""
Einmalig ausfuehren: python scripts/seed_products.py

Stellt sicher, dass die 4 Kernprodukte (Starter, Kompagnon, Premium, IMPULS)
in der products-Tabelle existieren. Idempotent via ON CONFLICT.
"""
import os
import json
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("DATABASE_URL nicht gesetzt.")
    raise SystemExit(1)

engine = create_engine(DATABASE_URL)

PRODUCTS = [
    {
        "slug": "starter", "name": "Starter-Paket", "sort_order": 1,
        "short_desc": "5 Seiten, SEO Basic, Mobiloptimierung", "long_desc": "",
        "price_brutto": 1500.00, "price_netto": 1260.50, "tax_rate": 19,
        "payment_type": "once", "delivery_days": 14, "status": "live",
        "category": "website",
        "highlighted": False, "highlight_label": "",
        "features": ["5-seitige WordPress-Website", "Mobile-First Design",
                     "SEO-Grundoptimierung", "SSL-Zertifikat & DSGVO-konform",
                     "Kontaktformular", "30 Tage Support"],
        "checkout_fields": ["name", "company", "email", "phone"],
        "webhook_actions": ["create_lead", "create_user", "create_project",
                            "send_welcome_email", "send_pdf"],
    },
    {
        "slug": "kompagnon", "name": "KOMPAGNON-Paket", "sort_order": 2,
        "short_desc": "8 Seiten, SEO + GEO, Workshop, Nachbetreuung", "long_desc": "",
        "price_brutto": 2000.00, "price_netto": 1680.67, "tax_rate": 19,
        "payment_type": "once", "delivery_days": 14, "status": "live",
        "category": "website",
        "highlighted": True, "highlight_label": "Empfehlung",
        "features": ["8-seitige WordPress-Website", "SEO + GEO-Optimierung",
                     "Strategy Workshop (60 Min.)", "Schema Markup & KI-Optimierung",
                     "Google Business Verknuepfung", "30 Tage Support"],
        "checkout_fields": ["name", "company", "email", "phone"],
        "webhook_actions": ["create_lead", "create_user", "create_project",
                            "send_welcome_email", "send_pdf"],
    },
    {
        "slug": "premium", "name": "Premium-Paket", "sort_order": 3,
        "short_desc": "12 Seiten, Shop-Ready, Fotoshooting", "long_desc": "",
        "price_brutto": 2800.00, "price_netto": 2352.94, "tax_rate": 19,
        "payment_type": "once", "delivery_days": 21, "status": "live",
        "category": "website",
        "highlighted": False, "highlight_label": "",
        "features": ["12-seitige WordPress-Website", "Individual-Design nach CI",
                     "SEO + GEO + KI-Volloptimierung", "Strategy Workshop (90 Min.)",
                     "Professioneller Fotoshooting-Tag", "Google Ads Einrichtung",
                     "3 Monate Support"],
        "checkout_fields": ["name", "company", "email", "phone"],
        "webhook_actions": ["create_lead", "create_user", "create_project",
                            "send_welcome_email", "send_pdf"],
    },
    {
        "slug": "impuls", "name": "IMPULS by KOMPAGNON", "sort_order": 10,
        "short_desc": "Geförderte Unternehmensberatung — 50 % vom Land RLP",
        "long_desc": (
            "IMPULS ist das ISB-158-Beratungsprogramm von KOMPAGNON für KMU in Rheinland-Pfalz. "
            "Das Land Rheinland-Pfalz übernimmt 50 % der Beratungskosten (max. 500 €/Tagewerk). "
            "Beratungsschwerpunkte: Strategie, Marketing, Digitalisierung, Kommunikationsdesign. "
            "Finanzierung des Eigenanteils über MMV Leasing in 36 Monatsraten. "
            "Alle Ergebnisse werden in einem persönlichen, passwortgeschützten Online-Portal bereitgestellt."
        ),
        "price_brutto": 20000.00, "price_netto": 16806.72, "tax_rate": 19,
        "payment_type": "once", "delivery_days": 90, "status": "draft",
        "category": "beratung",
        "highlighted": True, "highlight_label": "50 % Förderung",
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
    },
]

with engine.connect() as conn:
    inserted = 0
    skipped = 0
    for p in PRODUCTS:
        existing = conn.execute(
            text("SELECT id FROM products WHERE slug = :slug"),
            {"slug": p["slug"]},
        ).first()
        if existing:
            print(f"  {p['slug']} existiert bereits (id={existing.id}) — uebersprungen")
            skipped += 1
            continue
        conn.execute(text("""
            INSERT INTO products (
                slug, name, short_desc, long_desc,
                price_brutto, price_netto, tax_rate,
                payment_type, delivery_days,
                highlighted, highlight_label,
                features, checkout_fields, webhook_actions,
                status, sort_order, category
            ) VALUES (
                :slug, :name, :sd, :ld,
                :pb, :pn, :tr,
                :pt, :dd,
                :hl, :hll,
                CAST(:feat AS jsonb), CAST(:cf AS jsonb), CAST(:wa AS jsonb),
                :status, :so, :cat
            )
        """), {
            "slug":   p["slug"],
            "name":   p["name"],
            "sd":     p["short_desc"],
            "ld":     p.get("long_desc", ""),
            "pb":     p["price_brutto"],
            "pn":     p["price_netto"],
            "tr":     p["tax_rate"],
            "pt":     p["payment_type"],
            "dd":     p["delivery_days"],
            "hl":     p.get("highlighted", False),
            "hll":    p.get("highlight_label", ""),
            "feat":   json.dumps(p["features"]),
            "cf":     json.dumps(p["checkout_fields"]),
            "wa":     json.dumps(p["webhook_actions"]),
            "status": p["status"],
            "so":     p["sort_order"],
            "cat":    p.get("category", "sonstige"),
        })
        inserted += 1
        print(f"  {p['slug']} eingetragen")
    conn.commit()
    print(f"\nFertig: {inserted} eingetragen, {skipped} uebersprungen")

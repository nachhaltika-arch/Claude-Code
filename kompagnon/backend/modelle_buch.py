# -*- coding: utf-8 -*-
"""Bestellungen des Buchs „Der Homepage Standard" (BUCH-04).

**Warum eine eigene Tabelle und keine Erweiterung der Paketlogik.** Eine
Buchbestellung ist etwas anderes als ein Paketkauf:

* Es gibt **drei Varianten** — PDF, Druck, beides —, und der Ablauf danach
  unterscheidet sich vollständig: Die PDF-Fassung wird sofort ausgeliefert,
  die gedruckte geht von Hand an die Druckerei.
* Der Druck braucht eine **Lieferanschrift**. Der bestehende Checkout erfasst
  keine.
* Die PDF-Fassung braucht ein **Zählwerk für Abrufe** und einen befristeten
  Zugang — sonst wandert ein Link durch ein Forum.
* Beides braucht den **Verzicht auf das Widerrufsrecht** mit Zeitstempel.

**Alle Beträge in Cent.** `39.90` als Fließkommazahl ergibt beim Summieren
Beträge wie `39.900000000000006`. Stripe rechnet ohnehin in Cent, und die
Buchhaltung dankt es.

**Diese Datei wird von `database.py` am Ende importiert.** Ohne das wäre sie
nie geladen, `create_all` legte die Tabelle nie an — und der erste Kauf
scheiterte an einer Tabelle, die es nicht gibt. `tests/test_modelle_vollstaendig.py`
hält das fest.
"""
from datetime import datetime

from sqlalchemy import (Boolean, Column, Date, DateTime, ForeignKey, Integer,
                        Numeric, String)

from database import Base


class BookOrder(Base):
    """Eine Bestellung des Buchs — vom Warenkorb bis zur Auslieferung."""

    __tablename__ = "book_orders"

    id = Column(Integer, primary_key=True, index=True)
    #: Fortlaufend je Jahr, `HS-2026-0001`. Steht auf der Rechnung und in
    #: jeder Mail; deshalb sprechend und nicht die Datenbankkennung.
    order_number = Column(String(20), unique=True, nullable=False, index=True)
    variant = Column(String(10), nullable=False)          # pdf | print | bundle
    #: Die Fassung des Standards, gegen die dieses Buch geschrieben ist.
    #: Ohne sie lässt sich später nicht sagen, welchen Katalog ein Käufer hat.
    book_version = Column(String(10), nullable=False, default="")

    # ── Wer bestellt ─────────────────────────────────────────────────
    email = Column(String(255), nullable=False, index=True)
    first_name = Column(String(100), default="")
    last_name = Column(String(100), default="")
    company = Column(String(200), default="")

    # ── Lieferanschrift, nur bei Druck und Bündel ────────────────────
    ship_street = Column(String(200), default="")
    ship_zip = Column(String(20), default="")
    ship_city = Column(String(100), default="")
    ship_country = Column(String(2), default="DE")

    # ── Preise, alles in Cent ────────────────────────────────────────
    price_gross_cents = Column(Integer, nullable=False, default=0)
    #: Sieben Prozent — Bücher stehen in Anlage 2 UStG, und das E-Book ist
    #: dem gedruckten Buch seit Dezember 2019 gleichgestellt. Die 19 %, die
    #: der Produkteditor voreinstellt, wären hier falsch (BUCH-12).
    tax_rate = Column(Numeric(4, 2), nullable=False, default=7.00)
    shipping_cents = Column(Integer, nullable=False, default=0)

    # ── Stripe ───────────────────────────────────────────────────────
    stripe_session_id = Column(String(255), unique=True, index=True)
    stripe_payment_intent = Column(String(255), default="")
    payment_status = Column(String(20), nullable=False, default="pending")

    # ── Widerrufsrecht bei digitalen Inhalten (§ 356 Abs. 5 BGB) ─────
    #: Ohne dokumentierte Zustimmung hat jeder Käufer der PDF-Fassung
    #: vierzehn Tage Rückgaberecht auf eine Datei, die er längst hat. Der
    #: Zeitstempel ist der Nachweis, nicht das Häkchen allein.
    waiver_accepted = Column(Boolean, nullable=False, default=False)
    waiver_accepted_at = Column(DateTime, nullable=True)

    #: **Welche AGB-Fassung akzeptiert wurde** (L-100, ORDERS_05). Der Punkt,
    #: den ORDERS_05 „den Punkt, den fast alle vergessen" nennt: Aendern sich
    #: die AGB, ist ohne diese Angabe im Streitfall nicht mehr feststellbar,
    #: welchen Bedingungen der Kaeufer zugestimmt hat. Die Zustimmung allein
    #: belegt dann nur, dass jemand irgendwann irgendetwas angehakt hat.
    terms_version = Column(String(20), default="")
    #: Wann zugestimmt wurde. Wie beim Verzicht ist der Zeitstempel der
    #: Nachweis, nicht das Haeckchen allein.
    terms_accepted_at = Column(DateTime, nullable=True)

    # ── Auslieferung der PDF-Fassung ─────────────────────────────────
    download_token = Column(String(64), unique=True, index=True)
    download_expires_at = Column(DateTime, nullable=True)
    download_count = Column(Integer, nullable=False, default=0)
    delivered_at = Column(DateTime, nullable=True)

    # ── Abwicklung der gedruckten Fassung ────────────────────────────
    fulfillment_status = Column(String(20), default="not_applicable")
    fulfillment_exported_at = Column(DateTime, nullable=True)
    tracking_number = Column(String(100), default="")

    # ── Welches Katalogprodukt (27.08.2026) ──────────────────────────
    #: Leer bei den Buchbestellungen von vor dem 27.08. — dort sagt
    #: `variant` (pdf/print/bundle), was gekauft wurde. Fuer alles andere aus
    #: `products` steht hier der Slug.
    product_slug = Column(String(100), default="", index=True)

    #: Steuert Widerrufsrecht und Nettoausweis. Ein Geschaeftskunde hat kein
    #: Widerrufsrecht nach § 355 BGB; ein Verbraucher schon, und deshalb
    #: braucht er den Verzicht (§ 356 Abs. 5), bevor sofort ausgeliefert wird.
    is_business = Column(Boolean, nullable=False, default=False)
    buyer_vat_id = Column(String(50), default="")

    #: **Vorgemerkt** fuer ein Angebot, aber noch nicht verbraucht
    #: (L-100, ORDERS_08; Entscheidung David 29.08.2026: eingeloest wird bei
    #: **Annahme**). Zwischen Angebot und Annahme liegen Wochen — ohne diese
    #: Vormerkung liesse sich dieselbe Anrechnung einem zweiten Angebot
    #: beilegen und bei Annahme beider zweimal abziehen.
    #:
    #: Der Rueckweg gehoert dazu: Ein **verlorener** Deal gibt sie frei.
    #: Sonst haette „bei Annahme" genau die Wirkung, die sie vermeiden soll —
    #: die Anrechnung waere fuer immer blockiert statt sofort verbraucht.
    credit_reserved_deal_id = Column(Integer, nullable=True, index=True)
    credit_reserved_at = Column(DateTime, nullable=True)

    #: Auf welchen Deal der Betrag angerechnet wurde (L-100, ORDERS_08).
    #: **Die Einloesung ist endgueltig.** Eine Ruecknahme erfolgt nur von Hand
    #: mit Protokolleintrag — sonst entstuende ein Weg, denselben Betrag
    #: mehrfach anzurechnen.
    credit_redeemed_deal_id = Column(Integer, nullable=True, index=True)
    credit_redeemed_at = Column(DateTime, nullable=True)

    #: Bis wann sich der Betrag auf einen Websprint anrechnen laesst
    #: (Garantie G5). Errechnet beim Kauf aus `products.credit_months` —
    #: **nicht** spaeter aus dem heutigen Stand des Katalogs: Wer im Mai
    #: gekauft hat, behaelt die Frist, die im Mai galt.
    credit_valid_until = Column(Date, nullable=True)

    # ── Anschluss an den Vertrieb ────────────────────────────────────
    #: **Der eigentliche Geschäftszweck.** Ohne diese Verknüpfung verkauft
    #: das System Bücher und verliert die Käufer: Sie tauchen in keiner
    #: Pipeline auf und werden nie wieder angesprochen.
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=True, index=True)
    utm_source = Column(String(100), default="")
    utm_campaign = Column(String(100), default="")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def gesamt_cents(self) -> int:
        """Was der Käufer zahlt — Buch plus Versand."""
        return int(self.price_gross_cents or 0) + int(self.shipping_cents or 0)

    @property
    def braucht_anschrift(self) -> bool:
        return self.variant in ("print", "bundle")

    @property
    def ist_digital(self) -> bool:
        return self.variant in ("pdf", "bundle")

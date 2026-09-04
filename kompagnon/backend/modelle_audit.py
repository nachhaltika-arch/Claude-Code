"""Die Modelle der Analyse: Audit-Ergebnis und KI-Sichtbarkeit (L-25).

**Warum eigene Datei, 23.08.2026.** `database.py` stand bei 1.019 Zeilen mit
19 Modellen. Diese beiden sind mit zusammen 187 Zeilen die groessten nach
`Lead` und `Project`, und sie gehoeren zusammen: Das eine haelt fest, was die
Pruefung einer Website ergeben hat, das andere, ob eine KI den Betrieb nennt.

`AuditResult` traegt den Kriterienkatalog als JSON — seit dem 11.08.2026, damit
neue Kriterien keine Migration brauchen. `GeoAnalysis` traegt den Verlauf der
KI-Sichtbarkeit (L-85) und die Stripe-Angaben des GEO-Abonnements.

**Diese Datei muss geladen werden**, wie alle `modelle_*.py`: `database.py`
holt sie am Ende per Wildcard. Die `relationship()`-Aufrufe nennen ihre
Gegenseite als Zeichenkette, und SQLAlchemy loest den Namen erst beim ersten
Zugriff auf — fehlt die Datei, faellt das nicht beim Start auf, sondern bei
irgendeiner Abfrage.
"""
from datetime import datetime

from sqlalchemy import (Boolean, Column, DateTime, Float, ForeignKey, Integer,
                        JSON, Numeric, String, Text)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from database import Base


class AuditResult(Base):
    """Website audit results based on Homepage Standard framework."""
    __tablename__ = "audit_results"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=True)
    # Gesetzt, wenn dieses Audit eine Eigenprüfung ist: die Qualitätsschleife
    # deployt eine selbst gebaute Seite als Vorschau und misst sie mit
    # demselben Katalog, den wir Kunden vorhalten. `website_url` zeigt dann auf
    # die Vorschau, nicht auf den Auftritt des Kunden.
    sitemap_page_id = Column(Integer, nullable=True, index=True)
    website_url = Column(String(500), nullable=False)
    company_name = Column(String(255), nullable=False)
    contact_name = Column(String(255))
    city = Column(String(100))
    trade = Column(String(100))

    # Async status: pending -> running -> completed / failed
    status = Column(String(50), default="pending")
    error_message = Column(Text)

    # Das Geheimnis, mit dem ein Interessent ohne Konto sein eigenes Ergebnis
    # abholt. Ohne das war die Kennung eine fortlaufende Zahl, und wer sie
    # hochzaehlte, las fremde Audits (L-52, 19.08.2026). Das Widget macht es
    # unter `/api/widget/report/{token}` seit jeher so.
    # Bestandsdaten haben keins und bleiben damit nur ueber eine Anmeldung
    # erreichbar — ein Audit von gestern holt niemand mehr ueber die
    # Landingpage ab.
    public_token = Column(String(64), nullable=True, index=True)

    # Scores (6 categories)
    total_score = Column(Integer, default=0)  # 0-100
    level = Column(String(50))  # Nicht konform, Bronze, Silber, Gold, Platin
    rc_score = Column(Integer, default=0)  # Rechtliche Compliance (max 30)
    tp_score = Column(Integer, default=0)  # Technische Performance (max 20)
    bf_score = Column(Integer, default=0)  # Barrierefreiheit (max 20)
    si_score = Column(Integer, default=0)  # Sicherheit & Datenschutz (max 15)
    se_score = Column(Integer, default=0)  # SEO & Sichtbarkeit (max 10)
    ux_score = Column(Integer, default=0)  # Inhalt & Nutzererfahrung (max 5)

    # Granular item scores (per-criterion)
    rc_impressum = Column(Integer, default=0)
    rc_datenschutz = Column(Integer, default=0)
    rc_cookie = Column(Integer, default=0)
    rc_bfsg = Column(Integer, default=0)
    rc_urheberrecht = Column(Integer, default=0)
    rc_ecommerce = Column(Integer, default=0)
    tp_lcp = Column(Integer, default=0)
    tp_cls = Column(Integer, default=0)
    tp_inp = Column(Integer, default=0)
    tp_mobile = Column(Integer, default=0)
    tp_bilder = Column(Integer, default=0)
    ho_anbieter = Column(Integer, default=0)
    ho_uptime = Column(Integer, default=0)
    ho_http = Column(Integer, default=0)
    ho_backup = Column(Integer, default=0)
    ho_cdn = Column(Integer, default=0)
    bf_kontrast = Column(Integer, default=0)
    bf_tastatur = Column(Integer, default=0)
    bf_screenreader = Column(Integer, default=0)
    bf_lesbarkeit = Column(Integer, default=0)
    si_ssl = Column(Integer, default=0)
    si_header = Column(Integer, default=0)
    si_drittanbieter = Column(Integer, default=0)
    si_formulare = Column(Integer, default=0)
    se_seo = Column(Integer, default=0)
    se_schema = Column(Integer, default=0)
    se_lokal = Column(Integer, default=0)
    ux_erstindruck = Column(Integer, default=0)
    ux_cta = Column(Integer, default=0)
    ux_navigation = Column(Integer, default=0)
    ux_vertrauen = Column(Integer, default=0)
    ux_content = Column(Integer, default=0)
    ux_kontakt = Column(Integer, default=0)

    # Kriterienkatalog ab 2026-08-11 (siehe services/audit_criteria.py).
    # JSON statt Einzelspalten, damit neue Kriterien keine Migration brauchen.
    # Die Einzelspalten oberhalb sind Altbestand und werden nicht mehr gefüllt.
    item_scores = Column(Text, default="{}")      # {kriterium: punkte}
    item_sources = Column(Text, default="{}")     # {kriterium: gemessen|abgeleitet|...}
    item_belege = Column(Text, default="{}")      # {kriterium: gemessener Wert im Klartext}
    category_scores = Column(Text, default="[]")  # [{key, label, score, max, ...}]
    blockers = Column(Text, default="[]")         # K.-o.-Kriterien
    coverage = Column(Integer, default=0)         # Anteil erhobener Punkte in %
    collection_notes = Column(Text, default="{}") # warum eine Prüfung ausfiel

    # Über wie viele Seiten das Audit urteilt. Bis zum 21.08.2026 war es immer
    # genau eine — die Startseite. Ohne diese Zahl vergleicht jemand später
    # eine alte Note mit einer neuen, ohne zu merken, dass die eine über eine
    # Seite und die andere über zwanzig gefällt wurde. Die Vorgabe 1 ist für
    # Altzeilen deshalb keine Behelfszahl, sondern die Wahrheit.
    # Die Spalten legt `migrations_runtime.py::run_migrations` an, nicht `create_all`.
    seiten_geprueft = Column(Integer, default=1)
    seiten_gefunden = Column(Integer, nullable=True)

    # Wogegen bewertet wurde (Homepage Standard 2026.2, Branchenmodell). Die
    # Klasse entscheidet, welche Kriterien überhaupt gelten — ohne sie lässt
    # sich ein Bericht später weder erklären noch mit einem neueren vergleichen.
    # Die Spalten legt `migrations_runtime.py::run_migrations` an, nicht `create_all`.
    erkannte_branche = Column(String, default="")   # Freitext des Modells
    branchenklasse = Column(String, default="")     # K1…K6
    standard_version = Column(String, default="")   # Fassung des Standards

    # Raw check results
    ssl_ok = Column(Boolean, default=False)
    impressum_ok = Column(Boolean, default=False)
    datenschutz_ok = Column(Boolean, default=False)
    lcp_value = Column(Float)  # seconds
    cls_value = Column(Float)
    inp_value = Column(Float)  # ms
    mobile_score = Column(Integer)  # 0-100
    performance_score = Column(Integer)  # 0-100

    # Scraped data (auto-detected from website)
    scraped_phone = Column(String(50), default="")
    scraped_email = Column(String(255), default="")
    scraped_description = Column(Text, default="")
    screenshot_base64 = Column(Text, default="")

    # AI analysis
    ai_summary = Column(Text)  # 3-5 sentences plain language
    top_issues = Column(Text)  # JSON array of top issues
    recommendations = Column(Text)  # JSON array of recommendations

    # GEO / KI-Sichtbarkeit
    llms_txt = Column(Boolean, default=False)
    robots_ai_friendly = Column(Boolean, default=False)
    structured_data = Column(Boolean, default=False)
    ai_mentions = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    lead = relationship("Lead", backref="audits", foreign_keys=[lead_id])


class GeoAnalysis(Base):
    __tablename__ = "geo_analyses"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    geo_score_total = Column(Integer, default=0)
    llms_txt_score = Column(Integer, default=0)
    robots_ai_score = Column(Integer, default=0)
    structured_data_score = Column(Integer, default=0)
    content_depth_score = Column(Integer, default=0)
    local_signal_score = Column(Integer, default=0)

    raw_checks = Column(JSONB, default=dict)
    recommendations = Column(JSONB, default=list)
    generated_files = Column(JSONB, default=dict)

    status = Column(String(50), default="pending")
    error_message = Column(Text, nullable=True)

    upsell_active = Column(Boolean, default=False)
    upsell_price = Column(Float, nullable=True)

    # Monitoring
    last_monitored_at = Column(DateTime, nullable=True)
    monitoring_history = Column(JSONB, default=list)
    monitoring_enabled = Column(Boolean, default=True)
    last_score_change = Column(Integer, nullable=True)

    # Ob eine KI den Betrieb auf eine Kundenfrage hin wirklich nennt (L-58 b).
    # Die Spalten legt `migrations_runtime.py::run_migrations` an, nicht `create_all` —
    # siehe die Nachbarn oben. NULL heisst „nie gelaufen", nicht „nicht
    # gefunden": Der Lauf kostet Geld und laeuft nur auf Anforderung.
    ki_sichtbarkeit = Column(JSONB, nullable=True)
    ki_sichtbarkeit_am = Column(DateTime, nullable=True)
    # Je Lauf die Trefferzahl je System — ohne die Antworttexte, die
    # den Verlauf in einem Jahr unlesbar machten (L-85). Nach oben
    # begrenzt: `services/ki_sichtbarkeit.VERLAUF_MAX`.
    ki_sichtbarkeit_verlauf = Column(JSONB, nullable=True)

    # Ist die Auslieferung angekommen? (GEO-01, Position 6)
    #
    # Der Deploy meldet „erfolgreich" — ob die Datei danach unter ihrer
    # Adresse steht, hat das eine mit dem anderen nicht zu tun. Hier steht das
    # Ergebnis der Nachschau am lebenden Dienst. NULL heisst „nie geprueft",
    # nicht „nicht angekommen".
    auslieferung = Column(JSONB, nullable=True)
    auslieferung_am = Column(DateTime, nullable=True)

    # Stripe Subscription
    stripe_subscription_id = Column(String(200), nullable=True)
    stripe_customer_id = Column(String(200), nullable=True)
    stripe_price_id = Column(String(200), nullable=True)
    subscription_status = Column(String(50), nullable=True)
    subscription_started_at = Column(DateTime, nullable=True)
    subscription_canceled_at = Column(DateTime, nullable=True)
    subscription_current_period_end = Column(DateTime, nullable=True)

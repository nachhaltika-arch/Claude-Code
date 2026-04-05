"""
Seed script to populate ProjectChecklist with all 7-phase items.
Run once after database creation: python seed_checklists.py
"""
from database import SessionLocal, init_db, ProjectChecklist
from datetime import datetime

# Phase 1: Onboarding (Erstkontakt bis Vertragsabschluss)
PHASE_1 = [
    ("AKQ-01", "Erstkontakt durchgeführt", "both", True),
    ("AKQ-02", "Website analysiert", "ki", True),
    ("AKQ-03", "Geo-Check durchgeführt", "ki", False),
    ("AKQ-04", "Leistungsbeschreibung versendet", "human", True),
    ("AKQ-05", "Angebot erstellt", "human", False),
    ("AKQ-06", "Angebot präsentiert", "human", False),
    ("AKQ-07", "Vertrag unterzeichnet", "human", True),
]

# Phase 2: Briefing (Informationen sammeln, Zahlung)
PHASE_2 = [
    ("BRF-01", "Zahlung eingegangen", "human", True),
    ("BRF-02", "Kickoff-Termin durchgeführt", "human", False),
    ("BRF-03", "USP erarbeitet", "both", True),
    ("BRF-04", "Bildmaterial-Deadline definiert", "human", True),
    ("BRF-05", "Bildmaterial eingegangen", "human", True),
    ("BRF-06", "Kundenfreigabe Bildmaterial", "human", False),
    ("BRF-07", "Öffnungszeiten dokumentiert", "human", False),
    ("BRF-08", "Team/Mitarbeiter-Infos gesammelt", "human", False),
]

# Phase 3: Texte & Schema (Content-Erstellung, KI-generiert)
PHASE_3 = [
    ("TXT-01", "Hero-Headline KI-generiert", "ki", True),
    ("TXT-02", "Hero-Subline KI-generiert", "ki", False),
    ("TXT-03", "About-Text KI-generiert", "ki", True),
    ("TXT-04", "Leistungstexte KI-generiert", "ki", True),
    ("TXT-05", "FAQ (min. 5) KI-generiert", "ki", True),
    ("TXT-06", "Texte Mensch-reviewed", "human", True),
    ("TXT-07", "Texte freigegeben", "human", False),
    ("SEM-01", "Seitentitel (Meta-Tags) generiert", "ki", False),
    ("SEM-02", "Meta-Descriptions generiert", "ki", False),
    ("SEM-03", "Local Business Schema (JSON-LD)", "ki", True),
    ("SEM-04", "FAQ Schema (JSON-LD)", "ki", False),
    ("SEM-05", "Breadcrumb Schema (JSON-LD)", "ki", False),
    ("SEM-06", "Service Schema (JSON-LD)", "ki", False),
    ("SEM-07", "robots.txt generiert", "ki", False),
    ("SEM-08", "sitemap.xml Template erstellt", "ki", False),
]

# Phase 4: Technik & Sicherheit (WordPress-Setup, SSL, Performance)
PHASE_4 = [
    ("TEC-01", "WordPress installiert", "both", True),
    ("TEC-02", "Theme customized", "human", True),
    ("TEC-03", "SSL-Zertifikat aktiv", "human", True),
    ("TEC-04", "PageSpeed Score ≥ 85", "both", True),
    ("TEC-05", "Core Web Vitals geprüft", "ki", True),
    ("TEC-06", "Mobile-Test bestanden", "ki", False),
    ("TEC-07", "Bilder optimiert", "both", False),
    ("TEC-08", "Formulare getestet", "human", False),
    ("LEG-01", "Impressum rechtssicher", "human", True),
    ("LEG-02", "Datenschutzerklärung DSGVO-konform", "human", True),
    ("LEG-03", "Cookie-Banner implementiert", "human", False),
]

# Phase 5: QA & Kundenpräsentation (Qualitätschecks, Kundenfreigabe)
PHASE_5 = [
    ("QA-01", "Link-Check durchgeführt", "ki", True),
    ("QA-02", "Alle Formulare getestet", "human", True),
    ("QA-03", "Rich Results validiert", "ki", False),
    ("QA-04", "Typography/Design-Check", "human", False),
    ("QA-05", "Content-Check (Typos, Inhalt)", "human", True),
    ("QA-06", "GA4/Analytics integriert", "human", False),
    ("QA-07", "Search Console vorbereitet", "ki", False),
    ("ABO-01", "Kundenfreigabe eingeholt", "human", True),
    ("ABO-02", "Kundenänderungen umgesetzt", "human", False),
]

# Phase 6: Go-Live (Domain live, Indexierung, Übergabe)
PHASE_6 = [
    ("DLP-01", "Domain auf neue IP gewiesen", "human", True),
    ("DLP-02", "DNS propagiert (max. 24h)", "human", False),
    ("DLP-03", "Alte Website weiterleitet (301)", "human", False),
    ("DLP-04", "Search Console verifiziert", "human", False),
    ("DLP-05", "Indexierung in Google geprüft", "ki", False),
    ("HND-01", "Übergabe-Dokument erstellt", "human", True),
    ("HND-02", "Zugangsdaten übergeben", "human", True),
    ("HND-03", "Schulung durchgeführt", "human", False),
    ("HND-04", "Supportkanal etabliert", "human", False),
]

# Phase 7: Post-Launch (Follow-ups, Bewertung, Upsell)
PHASE_7 = [
    ("PLN-01", "Tag-1-Glückwunsch-Mail versendet", "ki", False),
    ("PLN-02", "Tag-5-Funktionscheck durchgeführt", "human", False),
    ("PLN-03", "Tag-14-Bericht erstellt", "both", False),
    ("REV-01", "Bewertungsanfrage versendet", "ki", False),
    ("REV-02", "Bewertung erhalten", "human", False),
    ("UP1-01", "Upsell-Paket besprochen", "human", False),
    ("UP1-02", "Upsell akzeptiert/abgelehnt", "human", False),
    ("FIN-01", "Projekt abgeschlossen", "human", False),
]

CHECKLIST_TEMPLATES = {
    1: PHASE_1,
    2: PHASE_2,
    3: PHASE_3,
    4: PHASE_4,
    5: PHASE_5,
    6: PHASE_6,
    7: PHASE_7,
}


def seed_checklists():
    """Create all checklist items for a new project."""
    db = SessionLocal()
    try:
        for phase, items in CHECKLIST_TEMPLATES.items():
            for item_key, item_label, responsible, is_critical in items:
                # Check if already exists (to prevent duplicates)
                existing = db.query(ProjectChecklist).filter_by(
                    phase=phase, item_key=item_key
                ).first()
                if not existing:
                    checklist = ProjectChecklist(
                        phase=phase,
                        item_key=item_key,
                        item_label=item_label,
                        responsible=responsible,
                        is_critical=is_critical,
                        is_completed=False,
                    )
                    db.add(checklist)
        db.commit()
        print("✓ Checklisten erfolgreich gepopuliert")
    except Exception as e:
        db.rollback()
        print(f"✗ Fehler beim Seeding: {e}")
    finally:
        db.close()


def create_project_checklists(db, project_id: int):
    """Create checklist items for a specific project (copy from templates)."""
    for phase, items in CHECKLIST_TEMPLATES.items():
        for item_key, item_label, responsible, is_critical in items:
            checklist = ProjectChecklist(
                project_id=project_id,
                phase=phase,
                item_key=item_key,
                item_label=item_label,
                responsible=responsible,
                is_critical=is_critical,
                is_completed=False,
            )
            db.add(checklist)
    db.commit()


if __name__ == "__main__":
    init_db()
    seed_checklists()
    print("\n📋 Datenbank initialisiert und Checklisten eingespeichert!")

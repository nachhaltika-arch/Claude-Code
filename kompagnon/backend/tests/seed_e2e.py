"""
Seed fuer die Browser-Tests.

Legt ein Admin-Konto und ein Projekt an, das weit genug fortgeschritten ist,
dass Sitemap, Wireframe und Style Guide im Online-Fertig-Editor nicht gesperrt
sind. Ohne das laesst sich der interessante Teil der Anwendung gar nicht
automatisiert pruefen — genau daran ist der manuelle Smoke-Test gescheitert:
alle Staging-Projekte stehen in Phase 1, die Views waren unerreichbar.

Die Freischaltung folgt computeStepStatus() in OnlineFertigEditor.jsx: Frei ist
immer nur der naechste Schritt nach der letzten LUECKENLOSEN Kette
abgeschlossener Schritte. Deshalb muss Phase 1 vollstaendig belegt sein.

Aufruf:
    python -m tests.seed_e2e
Gibt die angelegten IDs als JSON aus, damit die Tests sie lesen koennen.
"""
import json
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

E2E_EMAIL = "e2e-admin@kompagnon.local"
E2E_PASSWORD = "e2e-test-passwort"
E2E_COMPANY = "E2E Testbetrieb Heizung GmbH"


def _wireframe_data():
    """Minimale, aber vollstaendige Wireframe-Struktur mit Style Guide."""
    return {
        "pages": [
            {
                "page_id": 1,
                "blocks": [
                    {"slug": "hero-standard", "order": 0, "slots": {"headline": "Heizung vom Fachbetrieb"}},
                    {"slug": "leist-grid-3", "order": 1, "slots": {}},
                    {"slug": "cta-angebot", "order": 2, "slots": {}},
                ],
            }
        ],
        "style_guide": {
            "palette": {"primary": "#004F59", "accent": "#008EAA"},
            "typography": {"scale": "default"},
        },
        "style_guide_approved": False,
    }


def seed():
    from auth import hash_password
    from database import AuditResult, Lead, Project, SessionLocal, User, init_db

    init_db()
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == E2E_EMAIL).first()
        if not user:
            user = User(
                email=E2E_EMAIL,
                password_hash=hash_password(E2E_PASSWORD),
                first_name="E2E",
                last_name="Admin",
                role="admin",
                is_active=True,
                is_verified=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        lead = db.query(Lead).filter(Lead.company_name == E2E_COMPANY).first()
        if not lead:
            lead = Lead(
                company_name=E2E_COMPANY,
                website_url="https://e2e-testbetrieb.example",
                email="kontakt@e2e-testbetrieb.example",
                city="Koblenz",
                status="won",
                lead_source="e2e-seed",
            )
            db.add(lead)
            db.commit()
            db.refresh(lead)

        # Der Editor holt beim Oeffnen GET /api/audit/lead/{id}/latest. Ohne
        # Audit-Datensatz antwortet der Server mit 404 und die Browser-Konsole
        # zeigt einen Fehler — obwohl das Projekt laut audit_score eines hat.
        audit = db.query(AuditResult).filter(AuditResult.lead_id == lead.id).first()
        if not audit:
            audit = AuditResult(
                lead_id=lead.id,
                website_url="https://e2e-testbetrieb.example",
                company_name=E2E_COMPANY,
                city="Koblenz",
                trade="Heizung/Sanitaer",
                status="completed",
                total_score=72,
                level="Gold",
            )
            db.add(audit)
            db.commit()

        project = db.query(Project).filter(Project.lead_id == lead.id).first()
        if not project:
            project = Project(lead_id=lead.id, company_name=E2E_COMPANY)
            db.add(project)

        # Phase 1 lueckenlos abschliessen — sonst bleibt alles dahinter gesperrt.
        project.status = "phase_3"
        project.company_name = E2E_COMPANY
        project.website_url = "https://e2e-testbetrieb.example"
        project.has_briefing = True
        project.audit_score = 72
        project.scrape_full_at = datetime.utcnow() - timedelta(days=1)
        project.wireframe_data = _wireframe_data()

        # 'zugangsdaten' kennt keine Heuristik und muss bestaetigt werden,
        # sonst reisst die Kette genau dort ab.
        project.steps_confirmed = json.dumps({
            step: {"confirmed": True, "confirmed_at": datetime.utcnow().isoformat()}
            for step in ("briefing-unternehmen", "audit", "content-vollanalyse",
                         "briefing-website", "zugangsdaten")
        })

        db.commit()
        db.refresh(project)

        return {
            "email": E2E_EMAIL,
            "password": E2E_PASSWORD,
            "user_id": user.id,
            "lead_id": lead.id,
            "project_id": project.id,
        }
    finally:
        db.close()


if __name__ == "__main__":
    print(json.dumps(seed(), indent=2))

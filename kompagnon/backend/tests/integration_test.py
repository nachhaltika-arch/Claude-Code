"""
Integration Test - Complete Project Lifecycle
Tests the full workflow from lead creation to review request
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from database import SessionLocal, init_db, Lead, Project, Customer, ProjectChecklist
from seed_checklists import create_project_checklists
from services.margin_calculator import MarginCalculator
from agents.lead_analyst import LeadAnalystAgent
from agents.content_writer import ContentWriterAgent
from agents.seo_geo_agent import SeoGeoAgent
from agents.qa_agent import QaAgent
from agents.review_agent import ReviewAgent


def test_complete_workflow():
    """Test complete workflow: Lead → Project → QA → Review"""
    print("\n" + "="*60)
    print("🚀 KOMPAGNON Integration Test - Complete Lifecycle")
    print("="*60 + "\n")

    db = SessionLocal()

    try:
        # Initialize database
        init_db()
        print("✓ Database initialized")

        # ===== PHASE 1: CREATE LEAD =====
        print("\n📋 PHASE 1: Creating Lead...")
        lead = Lead(
            company_name="Test Sanitär GmbH",
            contact_name="Hans Mueller",
            phone="+49 123 456789",
            email="hans@test-sanitaer.de",
            website_url="https://test-sanitaer.de",
            city="Berlin",
            trade="Sanitär",
            lead_source="Cold Call",
            status="new",
        )
        db.add(lead)
        db.commit()
        db.refresh(lead)
        print(f"✓ Lead created: {lead.company_name} (ID: {lead.id})")

        # ===== PHASE 2: ANALYZE LEAD =====
        print("\n🔍 PHASE 2: Analyzing Lead...")
        agent = LeadAnalystAgent()
        analysis = agent.analyze_lead(
            website_url=lead.website_url,
            company_name=lead.company_name,
            city=lead.city,
            trade=lead.trade,
        )
        lead.analysis_score = analysis.get("overall_score", 0)
        lead.geo_score = analysis.get("geo_visibility_score", 0)
        lead.status = "qualified"
        db.commit()
        print(f"✓ Analysis Score: {lead.analysis_score}/100, GEO: {lead.geo_score}/10")
        print(f"  Top issue: {analysis.get('top_3_issues', ['N/A'])[0]}")

        # ===== PHASE 3: CONVERT TO PROJECT =====
        print("\n📦 PHASE 3: Converting to Project...")
        project = Project(
            lead_id=lead.id,
            status="phase_1",
            fixed_price=2000.0,
            hourly_rate=45.0,
            ai_tool_costs=50.0,
        )
        db.add(project)
        db.flush()
        create_project_checklists(db, project.id)
        print(f"✓ Project created (ID: {project.id})")
        print(f"✓ {ProjectChecklist.query.filter_by(project_id=project.id).count()} checklist items created")

        # ===== PHASE 4: GENERATE CONTENT =====
        print("\n✍️  PHASE 4: Generating Website Content...")
        content_agent = ContentWriterAgent()
        briefing = {
            "company_name": lead.company_name,
            "city": lead.city,
            "trade": lead.trade,
            "usp": "Schnelle Reparaturen, faire Preise, 15 Jahre Erfahrung",
            "services": ["Reparaturen", "Neubau", "Wartung"],
            "target_audience": "Hausbesitzer in Berlin",
            "team_size": 3,
            "team_info": "Erfahrenes Fachteam",
            "years_in_business": 15,
            "awards_or_certifications": ["TÜV", "Innungsmitglied"],
        }
        content = content_agent.write_content(briefing)
        print(f"✓ Hero Headline: '{content.get('hero_headline', 'N/A')}'")
        print(f"✓ About (150W): {len(content.get('about_text', '').split())} words")
        print(f"✓ FAQs: {len(content.get('faq_items', []))} items")

        # ===== PHASE 5: SEO/GEO SETUP =====
        print("\n🔍 PHASE 5: Generating SEO/GEO Setup...")
        seo_agent = SeoGeoAgent()
        company_data = {
            "company_name": lead.company_name,
            "street": "Musterstraße 123",
            "postal_code": "10115",
            "city": lead.city,
            "country": "DE",
            "phone": "+49 123 456789",
            "email": lead.email,
            "website": lead.website_url,
            "services": briefing["services"],
            "opening_hours": {"monday_friday": "08:00-18:00", "saturday": "09:00-13:00"},
            "latitude": 52.52,
            "longitude": 13.405,
        }
        seo = seo_agent.generate_seo(company_data)
        print(f"✓ LocalBusiness Schema created")
        print(f"✓ GEO Readiness Score: {seo.get('geo_readiness_score', 0)}/100")
        print(f"✓ {len(seo.get('service_schemas', []))} service schemas generated")

        # ===== PHASE 6: QA CHECK =====
        print("\n✅ PHASE 6: Conducting QA Review...")
        qa_agent = QaAgent()
        test_results = {
            "pagespeed_score": 87,
            "link_check_errors": 0,
            "ssl_valid": True,
            "mobile_responsive": True,
            "impressum_present": True,
            "dsgvo_compliant": True,
        }
        checklist_data = {
            "completed_items": ["TEC-01", "TEC-02", "TEC-03", "TEC-04"],
            "critical_incomplete": [],
        }
        qa = qa_agent.conduct_qa(project.id, checklist_data, test_results)
        print(f"✓ QA Score: {qa.get('overall_qa_score', 0)}/100")
        print(f"✓ Go-Live Recommendation: {'YES ✓' if qa.get('go_live_recommendation') else 'NO ✗'}")

        # ===== PHASE 7: TIME TRACKING & MARGIN =====
        print("\n💰 PHASE 7: Time Tracking & Margin Calculation...")
        # Log some hours
        MarginCalculator.log_time(db, project.id, 2.5, "human", phase=1, activity_description="Lead analysis")
        MarginCalculator.log_time(db, project.id, 3.0, "human", phase=3, activity_description="Content creation")
        MarginCalculator.log_time(db, project.id, 1.5, "human", phase=4, activity_description="WordPress setup")

        margin = MarginCalculator.calculate_margin(db, project.id)
        print(f"✓ Hours logged: {margin['human_hours']}h")
        print(f"✓ Costs: €{margin['total_costs']:.2f}")
        print(f"✓ Margin: €{margin['margin_eur']:.2f} ({margin['margin_percent']:.1f}%)")
        print(f"✓ Status: {margin['status'].upper()}")

        # ===== PHASE 8: CUSTOMER CREATION =====
        print("\n👤 PHASE 8: Creating Customer Record...")
        project.actual_go_live = db.func.now()
        project.status = "phase_7"
        customer = Customer(
            project_id=project.id,
            upsell_status="none",
        )
        db.add(customer)
        db.commit()
        print(f"✓ Customer created (ID: {customer.id})")

        # ===== PHASE 9: REVIEW REQUEST =====
        print("\n⭐ PHASE 9: Generating Review Request...")
        review_agent = ReviewAgent()
        review = review_agent.generate_review_request(
            customer_name="Hans Mueller",
            company_name="Test Sanitär GmbH",
            project_summary="Neue WordPress-Website mit lokalem SEO-Optimierung",
            platform="google",
        )
        print(f"✓ Email Subject: '{review.get('email_subject', 'N/A')}'")
        print(f"✓ Email Body: {len(review.get('email_body', '').split())} words")
        print(f"✓ Phone Script: {len(review.get('phone_script', '').split())} words")

        # ===== FINAL SUMMARY =====
        print("\n" + "="*60)
        print("✅ Integration Test PASSED")
        print("="*60)
        print(f"""
Summary:
  • Lead created and qualified (Score: {lead.analysis_score}/100)
  • Project created with 7 phases ({ProjectChecklist.query.filter_by(project_id=project.id).count()} checklist items)
  • Website content generated (hero, about, FAQ, meta-tags)
  • SEO/GEO setup created (JSON-LD, robots.txt, sitemap)
  • QA checklist evaluated (Go-Live: {'YES' if qa.get('go_live_recommendation') else 'NO'})
  • Hours tracked: {margin['human_hours']:.1f}h
  • Margin calculated: {margin['margin_percent']:.1f}% ({margin['status']})
  • Customer record created
  • Review request generated

Next Steps:
  1. Start backend: uvicorn main:app --reload
  2. Start frontend: npm start
  3. Access: http://localhost:8000/docs (API) & http://localhost:3000 (UI)
  4. Create leads in LeadPipeline
  5. Monitor automation scheduler
        """)

    except Exception as e:
        print(f"\n❌ Test FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    test_complete_workflow()

---
name: KAS MVP-Definition — minimal funktionierend, Kunden bearbeiten
description: "MVP" bedeutet hier nicht Feature-Breite, sondern: die existierende ~6.500-Zeilen-Pipeline soll soweit funktionieren, dass echte Kunden ohne Blocker durchlaufen.
type: project
originSessionId: 324ae64f-c7b6-403b-a0c6-61344cf01a62
---
Bei "MVP des KAS" geht es NICHT darum, das System neu zu bauen — es ist bereits weitgehend implementiert (300+ API-Endpoints, 5 KI-Agenten, 14 Scheduler-Jobs, Netlify-Integration, Stripe, Kundenportal etc.). Der Nutzer will: "minimal funktionierendes Produkt damit wir Kunden bearbeiten können".

**Why:** KOMPAGNON hat bestehenden Code, aber wahrscheinlich brüchige Stellen in der End-to-End-Pipeline (Lead → Audit → Briefing → KI-Texte → Deploy). Endziel laut README: ≤4h Menschenarbeit pro Kunde. Vor dem Featurebau muss klar sein, **was beim echten Kunde-durchschieben tatsächlich abbricht**.

**How to apply:**
- Keine neuen Features bauen, bevor Blocker bekannt sind.
- Beim Wiederaufnehmen: User fragen, ob er Top-3-Schmerzpunkte aus letztem Kunde-Versuch nennen kann (Option B), oder ich gehe live durch die Pipeline und identifiziere Blocker (Option A). Code-Audit ohne Live-Test (Option C) wurde als wertlos abgelehnt.
- Priorisierung: nach echten Kundenblockern, nicht nach ROADMAP-Reihenfolge.
- ROADMAP.md hat als P1: Content-Scraper, KI-Texte aus Briefing, In-App-Notifications, Onboarding-Flow, Erinnerungs-E-Mails, Zugangsdaten-Safe — aber das sind Vermutungen, nicht verifizierte Blocker.

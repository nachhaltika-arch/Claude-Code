---
name: KAS Niche-Phase 1 — Heizung/Sanitär/Elektrik (Wärmepumpe + Wallbox)
description: Strategische Niche-Entscheidung am 2026-05-03. Phase 1 fokussiert sich exklusiv auf SHK + E-Handwerk mit Schwerpunkt Wärmepumpen und Wallbox-Installation. Andere KMU-Branchen (Zahnärzte, Steuerberater, Restaurants etc.) kommen erst NACHDEM Phase 1 im Markt validiert ist.
type: project
originSessionId: cec1fdb4-823c-4cf5-8bc5-989a00e0d819
---
**Entscheidung:** KAS adressiert in Phase 1 exklusiv:
- **Heizungsbauer / Sanitär (SHK)**
- **Elektriker** (mit Schwerpunkt Wallbox-Installation, PV)
- **Sub-Fokus:** Wärmepumpen-Heizung (GEG-getrieben), Wallbox/E-Mobilität

**Why:**
- Markt-Tailwind extrem (Heizungsgesetz, E-Auto, Sanierungspflicht)
- Tickets 8-30k€ → rechtfertigen Premium-Pricing für KAS-Sites
- Site-Qualität in der Branche heute fast überall schlecht → leichter Wow-Effekt
- Kurze Feedback-Loops (Local-Conversion direkt messbar)
- Skalierungspfad klar: gleiche Spec funktioniert für andere Handwerker-Sub-Branchen (Maler, Dachdecker, Tischler) in Phase 2
- Hormozi-"Starving Market"-Kriterien alle erfüllt: Schmerz, Geld, Erreichbar, Wachsend

**Region Phase 1 (festgelegt 2026-05-03):**
- **Pilot-Region: Koblenz + Umkreis 50km** (Lahnstein, Neuwied, Boppard, Andernach, Mayen, Bad Ems)
- Local SEO + Google Business Profile sind dominanter Conversion-Hebel
- Persönliche Akquise möglich (Innungen, lokale Netzwerke, Vor-Ort-Termine)
- KEINE überregionale Akquise vor 5 Koblenz-Referenzkunden
- Kontakttelefon `+49 (0) 261` aus Backend bestätigt Region-Heimat

**Bewusst NICHT als Phase 1:**
- Zahnärzte/Ärzte → HWG-Compliance-Risiko in der ersten Iteration
- Steuerberater → Sales Cycle 3-9 Monate, zu langsam für Lern-Loops
- Restaurants/Gastro → schlechte Margen
- Generisches "alle KMU" → Hormozi: Riches in niches, generische Angebote konvertieren schwächer

**Component-Strategie (festgelegt 2026-05-04):**
- **Relume als Inspiration/Referenz, NICHT als Foundation** — wir nutzen Relume's 1000+ Components als Studienmaterial, kopieren keine Components 1:1 (Lizenz), bauen eigene KAS-Komponenten-Bibliothek
- Begründung: Lizenzkonform, volle Kontrolle, kein SaaS-Lock-in. Trade-off: langsamer als Relume-Foundation, aber strategisch sauber für SaaS-Wiederverkauf
- Workflow: Relume-Pattern studieren → mit Hormozi-Spec aus `docs/conversion-spec-shk.md` mappen → eigene SHK-spezifische Variante bauen → in KAS-Component-Library aufnehmen

**How to apply:**
- Conversion-Spec, Templates, content_writer-Prompts, Persona-Daten alle SHK/Elektrik-spezifisch designen
- Branchen-spezifische Keywords (Wärmepumpe Förderung, Heizungstausch, KfW, BAFA, Wallbox 11kW etc.) im SEO-Modul priorisieren
- Trust-Signale branchen-typisch: Innungs-Mitgliedschaft, Meisterbetrieb, Hersteller-Zertifizierungen (Viessmann, Vaillant, Bosch, etc.)
- Beispiel-Personas im Briefing: "Familie Mustermann saniert Eigenheim Bj. 1985, Heizung defekt, fragt sich was kostet Wärmepumpe + Förderung?"
- KEINE Erweiterung in andere Branchen, bevor mindestens 5 SHK-Kunden produktiv sind und Conversion-Daten existieren

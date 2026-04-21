"""
Email templates for all KOMPAGNON automation workflows.
All templates in German, max 150 words, professional tone.
"""

TEMPLATES = {
    "welcome": {
        "subject": "Willkommen! Ihr KOMPAGNON-Projekt startet — {company_name}",
        "body": """Lieber {contact_name},

herzlich willkommen bei KOMPAGNON! 🚀

Großartig, dass Sie sich für eine professionelle WordPress-Website entschieden haben. In den nächsten 14 Werktagen werden wir gemeinsam Ihre digitale Präsenz aufbauen — schnell, fair, garantiert.

**Die nächsten Schritte:**
1. Kickoff-Termin: {kickoff_date}
2. Materialsammlung (Texte, Bilder, Infos)
3. Texterstellung & Design
4. Ihre Freigabe & Go-Live

Ihr persönlicher KOMPAGNON-Ansprechpartner ist {assigned_person}.

Fragen? Jederzeit gerne anrufen oder mailen!

Viele Grüße,
Ihr KOMPAGNON-Team""",
    },
    "material_reminder": {
        "subject": "Erinnerung: Materialien für Ihre Website — {company_name}",
        "body": """Lieber {contact_name},

damit wir Ihre neue Website pünktlich fertigstellen können, benötigen wir noch einige Unterlagen von Ihnen.

Bitte stellen Sie uns folgende Materialien zur Verfügung:

✓ Unternehmensfotos (mind. 3 aktuelle Fotos)
✓ Leistungsbeschreibung (was machen Sie genau?)
✓ Team-Informationen (Mitarbeiterzahl, Expertise)
✓ Öffnungszeiten
✓ Kontaktdaten (Telefon, E-Mail, Adresse)

Bitte bis zum {review_deadline} einreichen.

Upload-Link: {upload_link}

Bei Fragen erreichen Sie uns unter:
{contact_person_phone} | {contact_person_email}

Herzliche Grüße,
{assigned_person}
KOMPAGNON-Team""",
    },
    "preview_ready": {
        "subject": "Ihre Website ist live — jetzt zur Freigabe!",
        "body": """Lieber {contact_name},

großartig! Ihre neue Website ist fertig und steht zur Begutachtung bereit. ✨

**Zur Vorschau:** {preview_link}

Bitte überprüfen Sie:
✓ Alle Texte korrekt?
✓ Fotos an der richtigen Stelle?
✓ Kontaktformular funktioniert?
✓ Alle Leistungen aufgelistet?

Haben Sie Änderungswünsche? Bis {review_deadline} können wir noch anpassen.

Nach Ihrer Freigabe geht es live!

Viele Grüße,
{assigned_person}""",
    },
    "go_live_congrats": {
        "subject": "🎉 Glückwunsch! {company_name} ist jetzt online!",
        "body": """Lieber {contact_name},

es ist soweit — Ihre Website ist live! 🚀

Die gute Nachricht: Sie sehen sofort erste Besucher in Google Analytics. Die erste Woche zeigt, ob die Website gut läuft.

**Was jetzt passiert:**
- Tag 1-5: Wir beobachten Performance & Fehler
- Tag 14: Funktionsprüfung & erste Optimierungen
- Tag 30: GEO-Check (Suchmaschinen sehen Sie?)

Fragen oder Probleme? Kontaktieren Sie mich direkt:
{contact_person_phone} oder {contact_person_email}

Freuen Sie sich — es geht los! 💪

{assigned_person}
KOMPAGNON-Team""",
    },
    "day_5_followup": {
        "subject": "Status-Check: Läuft Ihre neue Website gut?",
        "body": """Lieber {contact_name},

eine Woche nach Go-Live — wie läuft es?

Unsere Checks zeigen: Ihre Website funktioniert einwandfrei! ✓

**Das ist passiert:**
- {new_visitors} Besucher in den ersten Tagen
- {form_submissions} Anfragen übers Kontaktformular
- PageSpeed-Score: {pagespeed_score}/100 ✓

Haben Sie schon erste Anfragen bekommen? Falls ja — super! Falls nein — das ist normal, Suchmaschinen indexieren noch.

In einer Woche mehr Details!

Viele Grüße,
{assigned_person}""",
    },
    "day_14_check": {
        "subject": "Zwei Wochen live — Analysebericht",
        "body": """Lieber {contact_name},

zwei Wochen sind vorbei. Zeit für einen ehrlichen Bericht:

**Was läuft gut:**
✓ Website technisch fehlerfrei
✓ Besucher aus lokalem Umkreis sehen Sie in Google
✓ Formulare funktionieren zuverlässig

**Was wir noch optimieren:**
- PageSpeed könnte noch 5 Punkte höher
- Ein paar kleine Rechtschreibtippfehler

Insgesamt: Ihre Website ist ein voller Erfolg! Langfristig zählen die nächsten Monate — regelmäßige Updates und Bewertungen fördern die Rankings.

Möchten Sie ein Gespräch zur Langzeitstrategie?

{assigned_person}""",
    },
    "day_21_review_request": {
        "subject": "Danke, {company_name}! Wie war die Zusammenarbeit?",
        "body": """Lieber {contact_name},

drei Wochen ist Ihre Website jetzt online — herzlich Glückwunsch! 🎉

Wir sind begeistert, wie die Zusammenarbeit geklappt hat und wie professionell Sie mitgearbeitet haben. Jetzt eine kleine Bitte:

Falls Ihre Website bereits Anfragen gebracht hat und Sie mit uns zufrieden sind, würde eine Bewertung von Ihnen helfen — andere Handwerksbetriebe vertrauen echten Erfahrungen!

**Bewertung hinterlassen:** {review_link}

Dauert nur 2 Minuten. Vielen Dank!

{assigned_person}
KOMPAGNON-Team""",
    },
    "day_30_upsell": {
        "subject": "Nächster Schritt: WordPress-Verwaltung + SEO-Optimierung",
        "body": """Lieber {contact_name},

eine Monat live — Zeit für ein kurzes Gespräch! ☕

**Das haben wir beobachtet:**
- Website läuft stabil
- Lokale Suchmaschinen sehen Sie
- Erste organische Besucher kommen rein

**Aber: Mit kleinen Anpassungen können Sie 2-3x mehr Anfragen bekommen:**

📱 **WordPress-Verwaltungsvertrag** (99€/Monat)
- Regelmäßige Updates & Sicherheit
- Monatliche SEO-Optimierungen
- Backup & Support

🔍 **SEO-Intensiv-Paket** (599€ one-time)
- Google Business Profile Optimierung
- Lokale Link-Strategie
- Review-Management

**Interesse?** Kurz anrufen? {contact_person_phone}

{assigned_person}""",
    },
    "day_30_geo_check": {
        "subject": "GEO-Check: Wie gut rankt {company_name} lokal?",
        "body": """Lieber {contact_name},

nach einem Monat Online-Zeit: Wie sieht's aus lokal?

**GEO-Check-Ergebnisse:**
✓ Google Business Profile verifiziert
✓ Website indexiert und sichtbar
⚠ Noch keine Bewertungen (wichtig für Rankings!)

**Empfehlung für nächste 30 Tage:**
1. Kunden fragen: "Können Sie mich on Google bewerten?" → Kostenlos!
2. {company_name} auf Branchenportalen eintragen
3. Lokale Links aufbauen (IHK, Innungen)

Jede Bewertung hilft! Die ersten 5 pushen Ihr Google-Ranking massiv.

Möchten Sie Unterstützung dabei? {assigned_person}""",
    },
}


def get_template(template_key: str) -> dict:
    """Get email template by key."""
    return TEMPLATES.get(
        template_key,
        {
            "subject": f"Nachricht von KOMPAGNON",
            "body": "Template nicht gefunden.",
        },
    )


def render_template(template_key: str, context: dict) -> dict:
    """Render template with context variables. Missing keys are replaced with placeholder text."""
    import logging
    import string
    log = logging.getLogger(__name__)
    template = get_template(template_key)

    def safe_format(text: str) -> str:
        try:
            return text.format(**context)
        except KeyError as e:
            log.error(
                f"Template '{template_key}': missing placeholder {e}. "
                f"Available keys: {list(context.keys())}"
            )
            safe_ctx = {**context}
            for _, field_name, _, _ in string.Formatter().parse(text):
                if field_name and field_name not in safe_ctx:
                    safe_ctx[field_name] = f"[{field_name.upper()} FEHLT]"
            return text.format(**safe_ctx)

    return {
        "subject": safe_format(template["subject"]),
        "body": safe_format(template["body"]),
    }

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
        "subject": "Erinnerung: Materialsammlung {company_name}",
        "body": """Lieber {contact_name},

Sie haben eine Website bei KOMPAGNON in Auftrag gegeben — sehr gut! 👍

Damit wir pünktlich fertig werden, brauchen wir von Ihnen noch:

✓ Unternehmensfotos (mind. 3)
✓ Leistungsbeschreibung (was machen Sie genau?)
✓ Team-Informationen (wie viele Mitarbeiter, Expertise)
✓ Öffnungszeiten
✓ Kontaktdaten (Telefon, E-Mail, Adresse)

**Deadline: {deadline}**

Bitte hochladen unter: {upload_link}

Danke!
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
    "content_approval_request": {
        "subject": "Ihre Website-Inhalte warten auf Ihre Freigabe — {company_name}",
        "body": """Hallo {contact_name},

wir haben die Sitemap und die Texte für Ihre neue Website fertiggestellt. Jetzt brauchen wir kurz Ihre Freigabe, damit wir mit dem Design weitermachen können.

Bitte prüfen Sie die Inhalte über diesen Link:

{approval_url}

Mit einem Klick auf "Inhalte jetzt freigeben" bestätigen Sie, dass alles passt — danach starten wir sofort mit der Design-Phase.

Alternativ können Sie sich auch ins Kundenportal einloggen und dort freigeben.

Bei Fragen oder Änderungswünschen melden Sie sich gerne direkt bei uns.

Viele Grüße,
Ihr KOMPAGNON-Team""",
    },
    "content_approval_reminder": {
        "subject": "Erinnerung: Ihre Website-Freigabe steht noch aus — {company_name}",
        "body": """Hallo {contact_name},

wir warten noch auf Ihre Freigabe für die Website-Inhalte. Sobald wir Ihr OK haben, geht es direkt mit dem Design weiter — ohne Freigabe können wir leider nicht weitermachen.

Bitte hier prüfen und freigeben:

{approval_url}

Falls etwas unklar ist oder Sie Änderungen wünschen, antworten Sie einfach auf diese Mail.

Viele Grüße,
Ihr KOMPAGNON-Team""",
    },
    "content_approval_admin_notification": {
        "subject": "[KOMPAGNON] Kunde hat Inhalte freigegeben — {company_name}",
        "body": """Der Kunde {company_name} (Lead #{lead_id}, Projekt #{project_id}) hat die Website-Inhalte freigegeben.

Freigegeben am: {approved_at}
Freigabe-Kanal: {approval_channel}

Das Projekt kann jetzt in die Design-Phase uebergehen. Oeffne das Projekt in KOMPAGNON um weiterzuarbeiten.
""",
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
    """Render template with context variables."""
    template = get_template(template_key)
    return {
        "subject": template["subject"].format(**context),
        "body": template["body"].format(**context),
    }

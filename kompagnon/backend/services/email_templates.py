SEQUENZ_TEMPLATES = {

  "sequence_step_1": {
    "subject": "Wir haben Ihre Website analysiert, {firma}",
    "html": """
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto">
      <div style="background:#008eaa;padding:24px 28px;
                  border-radius:12px 12px 0 0">
        <div style="font-size:11px;color:rgba(255,255,255,.7);
                    text-transform:uppercase;letter-spacing:.08em;
                    margin-bottom:4px">KOMPAGNON</div>
        <h1 style="color:white;margin:0;font-size:20px">
          Ihre Website hat Potenzial, {firma}!
        </h1>
      </div>
      <div style="padding:24px 28px;background:#ffffff">
        <p style="color:#1a2332;font-size:15px">Guten Tag,</p>
        <p style="color:#64748b;line-height:1.7">
          wir haben Ihre Website <strong>{domain}</strong> analysiert
          und dabei Verbesserungspotenzial entdeckt.
        </p>
        <div style="background:#FFF7ED;border-left:4px solid #F59E0B;
                    padding:12px 16px;border-radius:0 8px 8px 0;
                    margin:16px 0">
          <div style="font-size:12px;font-weight:600;
                      color:#92400E;margin-bottom:4px">
            WICHTIGSTER VERBESSERUNGSPUNKT
          </div>
          <div style="font-size:14px;color:#1a2332">{top_problem}</div>
        </div>
        <p style="color:#64748b;line-height:1.7">
          In einem kostenlosen 15-Minuten-Gespräch zeigen wir Ihnen,
          wie Ihre neue Website mehr Anfragen generiert.
        </p>
        <div style="text-align:center;margin:24px 0">
          <a href="mailto:info@kompagnon.eu?subject=Termin%20anfragen"
             style="background:#008eaa;color:white;padding:12px 28px;
                    border-radius:8px;text-decoration:none;
                    font-weight:600;font-size:14px;
                    display:inline-block">
            Kostenloses Gespräch vereinbaren →
          </a>
        </div>
      </div>
      <div style="padding:14px 28px;background:#f8f9fa;
                  border-radius:0 0 12px 12px;text-align:center">
        <p style="font-size:11px;color:#94a3b8;margin:0">
          KOMPAGNON Communications BP GmbH · kompagnon.eu<br>
          <a href="mailto:info@kompagnon.eu"
             style="color:#94a3b8">info@kompagnon.eu</a>
        </p>
      </div>
    </div>""",
  },

  "sequence_step_2": {
    "subject": "3 schnelle Verbesserungen für {domain}",
    "html": """
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto">
      <div style="background:#1D9E75;padding:24px 28px;
                  border-radius:12px 12px 0 0">
        <h1 style="color:white;margin:0;font-size:20px">
          3 konkrete Tipps für {firma}
        </h1>
      </div>
      <div style="padding:24px 28px;background:#ffffff">
        <p style="color:#64748b;line-height:1.7">
          Guten Tag, hier sind die drei wichtigsten Verbesserungen
          für <strong>{domain}</strong>:
        </p>
        {tipps_html}
        <div style="text-align:center;margin:24px 0">
          <a href="mailto:info@kompagnon.eu?subject=Termin%20vereinbaren"
             style="background:#1D9E75;color:white;padding:12px 28px;
                    border-radius:8px;text-decoration:none;
                    font-weight:600;font-size:14px;
                    display:inline-block">
            Jetzt umsetzen lassen →
          </a>
        </div>
      </div>
      <div style="padding:14px 28px;background:#f8f9fa;
                  border-radius:0 0 12px 12px;text-align:center">
        <p style="font-size:11px;color:#94a3b8;margin:0">
          KOMPAGNON Communications BP GmbH · kompagnon.eu
        </p>
      </div>
    </div>""",
  },

  "sequence_step_3": {
    "subject": "Kurze Rückfrage zu Ihrer Website, {firma}",
    "html": """
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto">
      <div style="padding:28px">
        <p style="color:#1a2332;font-size:15px">Guten Tag,</p>
        <p style="color:#64748b;line-height:1.7">
          ich wollte kurz nachfragen — haben Sie unsere Analyse
          zu <strong>{domain}</strong> gesehen?
        </p>
        <p style="color:#64748b;line-height:1.7">
          Hätten Sie <strong>15 Minuten diese Woche</strong>
          für ein kurzes Gespräch?
        </p>
        <div style="text-align:center;margin:24px 0">
          <a href="mailto:info@kompagnon.eu?subject=Termin%2015%20Minuten"
             style="background:#008eaa;color:white;padding:12px 28px;
                    border-radius:8px;text-decoration:none;
                    font-weight:600;font-size:14px;
                    display:inline-block">
            Ja, gerne →
          </a>
        </div>
        <p style="color:#94a3b8;font-size:12px">
          Mit freundlichen Grüßen,<br>
          Ihr KOMPAGNON-Team<br>
          info@kompagnon.eu
        </p>
      </div>
    </div>""",
  },

  "phase_change": {
    "subject": "Ihr Projekt: Phase {phase_nr} — {phase_name}",
    "html": """
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto">
      <div style="background:#008eaa;padding:24px 28px;
                  border-radius:12px 12px 0 0">
        <div style="font-size:11px;color:rgba(255,255,255,.7);
                    margin-bottom:4px">PROJEKT-UPDATE</div>
        <h1 style="color:white;margin:0;font-size:20px">
          Phase {phase_nr}: {phase_name}
        </h1>
      </div>
      <div style="padding:24px 28px;background:#ffffff">
        <p style="color:#64748b;line-height:1.7">
          Guten Tag, {firma},<br><br>
          Ihr Projekt ist jetzt in
          <strong>Phase {phase_nr} von 7 — {phase_name}</strong>.
        </p>
        <p style="color:#64748b;line-height:1.7">{phase_beschreibung}</p>
        <div style="text-align:center;margin:24px 0">
          <a href="{portal_url}"
             style="background:#008eaa;color:white;padding:12px 28px;
                    border-radius:8px;text-decoration:none;
                    font-weight:600;font-size:14px;
                    display:inline-block">
            Zum Kundenportal →
          </a>
        </div>
      </div>
      <div style="padding:14px 28px;background:#f8f9fa;
                  border-radius:0 0 12px 12px;text-align:center">
        <p style="font-size:11px;color:#94a3b8;margin:0">
          KOMPAGNON Communications BP GmbH · kompagnon.eu
        </p>
      </div>
    </div>""",
  },
}

PHASE_NAMES = {
    1: ("Onboarding",   "Wir bereiten alles für den Strategy Workshop vor."),
    2: ("Briefing",     "Der Strategy Workshop findet statt. Inhalte und Ziele werden festgelegt."),
    3: ("Content",      "Texte, Bilder und Sitemap werden erstellt."),
    4: ("Technik",      "Ihre Website wird gebaut und konfiguriert."),
    5: ("QA & Abnahme", "Qualitätsprüfung und Ihre finale Freigabe."),
    6: ("Go-Live",      "Ihre Website geht jetzt live — herzlichen Glückwunsch!"),
    7: ("Post-Launch",  "Wir begleiten Sie noch 30 Tage nach dem Go-Live."),
}


def render(template_key: str, data: dict) -> dict:
    """Füllt Platzhalter in Subject und HTML."""
    tpl = SEQUENZ_TEMPLATES.get(template_key)
    if not tpl:
        return {"subject": "", "html": ""}
    subject = tpl["subject"].format_map(data)
    html    = tpl["html"].format_map(data)
    return {"subject": subject, "html": html}

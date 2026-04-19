"""
Einmalig ausfuehren: python scripts/seed_impuls_page.py
Legt die IMPULS Landing Page im Seiten-Manager an.
"""
import os
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("DATABASE_URL nicht gesetzt.")
    raise SystemExit(1)

engine = create_engine(DATABASE_URL)

IMPULS_HTML = """<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>IMPULS by KOMPAGNON — Geförderte Unternehmensberatung</title>
  <meta name="description" content="50 % Förderung vom Land Rheinland-Pfalz. Professionelle Unternehmensberatung für KMU — ISB Betriebsberatungsprogramm 158.">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans:wght@400;600;700;900&display=swap" rel="stylesheet">
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: 'Noto Sans', Arial, sans-serif; background: #F0F4F5; color: #1e293b; }
    a { color: inherit; text-decoration: none; }

    .header { background: #004F59; padding: 16px 32px; display: flex; align-items: center; justify-content: space-between; }
    .header-logo { color: #FAE600; font-weight: 900; font-size: 20px; letter-spacing: 0.05em; }
    .header-tag { color: rgba(255,255,255,0.5); font-size: 11px; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; }

    .hero { background: linear-gradient(135deg, #004F59 0%, #008EAA 100%); color: white; padding: 72px 32px 64px; text-align: center; }
    .hero-badge { display: inline-block; background: #FAE600; color: #004F59; font-size: 11px; font-weight: 900; letter-spacing: 0.12em; text-transform: uppercase; padding: 5px 16px; border-radius: 20px; margin-bottom: 24px; }
    .hero h1 { font-size: clamp(32px, 5vw, 60px); font-weight: 900; line-height: 1.1; margin-bottom: 20px; }
    .hero p { font-size: 18px; color: rgba(255,255,255,0.8); max-width: 560px; margin: 0 auto 32px; line-height: 1.6; }
    .hero-tags { display: flex; gap: 10px; justify-content: center; flex-wrap: wrap; }
    .hero-tag { background: rgba(255,255,255,0.12); color: rgba(255,255,255,0.7); padding: 4px 14px; border-radius: 20px; font-size: 12px; }

    .container { max-width: 1100px; margin: 0 auto; padding: 56px 32px; display: grid; grid-template-columns: 1fr 380px; gap: 56px; }
    @media (max-width: 800px) { .container { grid-template-columns: 1fr; } }

    .section-title { font-size: 22px; font-weight: 900; color: #004F59; margin-bottom: 28px; }
    .step { display: flex; gap: 16px; margin-bottom: 24px; }
    .step-nr { width: 40px; height: 40px; border-radius: 50%; background: #008EAA; color: white; font-weight: 900; font-size: 16px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
    .step-title { font-weight: 700; color: #004F59; margin-bottom: 4px; }
    .step-text { color: #555; font-size: 14px; line-height: 1.6; }

    .calc-box { background: white; border: 1px solid rgba(0,142,170,0.2); border-radius: 12px; padding: 24px; margin-top: 32px; }
    .calc-title { font-weight: 900; color: #004F59; margin-bottom: 16px; font-size: 15px; }
    .calc-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; }
    .calc-item { text-align: center; padding: 14px 8px; background: #F0F4F5; border-radius: 8px; }
    .calc-label { font-size: 11px; color: #888; margin-bottom: 4px; }
    .calc-value { font-size: 24px; font-weight: 900; }
    .calc-sub { font-size: 11px; color: #aaa; margin-top: 4px; }
    .calc-result { margin-top: 14px; padding: 10px 14px; background: rgba(0,142,170,0.1); border-radius: 8px; font-size: 13px; color: #004F59; font-weight: 600; }

    .feature { display: flex; gap: 10px; margin-bottom: 10px; font-size: 14px; color: #444; }
    .feature-check { color: #008EAA; font-weight: 900; flex-shrink: 0; }

    .prereq-box { background: rgba(0,79,89,0.05); border: 1px solid rgba(0,79,89,0.15); border-radius: 10px; padding: 20px; margin-top: 24px; }
    .prereq-title { font-weight: 700; color: #004F59; margin-bottom: 12px; }
    .prereq-item { display: flex; gap: 8px; margin-bottom: 6px; font-size: 13px; color: #555; }
    .prereq-check { color: #1D9E75; font-weight: 900; }

    .form-card { background: white; border-radius: 16px; border: 1px solid rgba(0,142,170,0.2); box-shadow: 0 4px 24px rgba(0,79,89,0.08); padding: 32px; position: sticky; top: 24px; }
    .form-badge { display: inline-block; background: #FAE600; color: #004F59; font-size: 11px; font-weight: 900; letter-spacing: 0.1em; text-transform: uppercase; padding: 4px 12px; border-radius: 20px; margin-bottom: 12px; }
    .form-title { font-size: 20px; font-weight: 900; color: #004F59; margin-bottom: 6px; }
    .form-sub { font-size: 13px; color: #888; margin-bottom: 24px; }
    .form-label { display: block; font-size: 11px; font-weight: 700; color: #888; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 5px; }
    .form-field { margin-bottom: 14px; }
    .form-input { width: 100%; padding: 10px 12px; border: 1.5px solid #e2e8f0; border-radius: 8px; font-size: 14px; font-family: inherit; outline: none; color: #1e293b; }
    .form-input:focus { border-color: #008EAA; }
    .form-textarea { width: 100%; padding: 10px 12px; border: 1.5px solid #e2e8f0; border-radius: 8px; font-size: 14px; font-family: inherit; resize: vertical; min-height: 80px; outline: none; color: #1e293b; }
    .form-btn { width: 100%; padding: 14px; background: #004F59; color: white; border: none; border-radius: 10px; font-size: 15px; font-weight: 900; cursor: pointer; font-family: inherit; transition: background 0.2s; }
    .form-btn:hover { background: #008EAA; }
    .form-hint { font-size: 11px; color: #aaa; text-align: center; margin-top: 10px; }
    .form-trust { border-top: 1px solid #f1f5f9; margin-top: 20px; padding-top: 16px; }
    .form-trust-item { font-size: 12px; color: #64748b; margin-bottom: 6px; }
    .form-success { text-align: center; padding: 32px 16px; }
    .form-success-icon { font-size: 48px; margin-bottom: 16px; }
    .form-success-title { font-size: 20px; font-weight: 900; color: #004F59; margin-bottom: 12px; }
    .form-success-text { color: #555; font-size: 15px; line-height: 1.6; margin-bottom: 20px; }
    .form-contact { background: #F0F4F5; border-radius: 8px; padding: 12px 16px; font-size: 13px; color: #666; line-height: 1.8; }
    .form-error { background: #fef2f2; border: 1px solid #fecaca; border-radius: 8px; padding: 10px 14px; font-size: 13px; color: #dc2626; margin-bottom: 14px; }

    .footer { background: #004F59; color: rgba(255,255,255,0.4); padding: 20px 32px; text-align: center; font-size: 12px; line-height: 2; }
    .footer a { color: rgba(255,255,255,0.3); margin: 0 8px; }
  </style>
</head>
<body>

  <header class="header">
    <div class="header-logo">KOMPAGNON</div>
    <div class="header-tag">IMPULS by KOMPAGNON</div>
  </header>

  <section class="hero">
    <div class="hero-badge">ISB Betriebsberatungsprogramm 158 · Rheinland-Pfalz</div>
    <h1>50 % vom Land.<br>Den Rest in Raten.</h1>
    <p>Professionelle Unternehmensberatung — gefördert, finanziert, sofort wirksam. Für KMU in Rheinland-Pfalz.</p>
    <div class="hero-tags">
      <span class="hero-tag">KMU-Förderung</span>
      <span class="hero-tag">De-minimis-Beihilfe</span>
      <span class="hero-tag">MMV Leasing</span>
      <span class="hero-tag">Akkreditierter ISB-Berater</span>
    </div>
  </section>

  <div class="container">
    <div>
      <h2 class="section-title">Wie funktioniert das Modell?</h2>

      <div class="step">
        <div class="step-nr">1</div>
        <div>
          <div class="step-title">Förderantrag stellen</div>
          <div class="step-text">Gemeinsam mit KOMPAGNON stellen Sie den Antrag bei der ISB — bevor die Beratung beginnt. Erst nach Bewilligung geht es los.</div>
        </div>
      </div>
      <div class="step">
        <div class="step-nr">2</div>
        <div>
          <div class="step-title">Beratung & Zahlung</div>
          <div class="step-text">KOMPAGNON erbringt die Beratungsleistung. Sie zahlen das volle Honorar und erhalten alle Ergebnisse strukturiert aufbereitet.</div>
        </div>
      </div>
      <div class="step">
        <div class="step-nr">3</div>
        <div>
          <div class="step-title">50 % zurück + Leasing</div>
          <div class="step-text">Die ISB erstattet Ihnen 50 % direkt auf Ihr Konto. Den Eigenanteil finanzieren Sie bequem in 36 Monatsraten über MMV Leasing.</div>
        </div>
      </div>

      <div class="calc-box">
        <div class="calc-title">Beispielrechnung: 10.000 € Honorar</div>
        <div class="calc-grid">
          <div class="calc-item">
            <div class="calc-label">Gesamthonorar</div>
            <div class="calc-value" style="color:#334155">10.000 €</div>
            <div class="calc-sub">Sie zahlen zunächst</div>
          </div>
          <div class="calc-item">
            <div class="calc-label">ISB erstattet</div>
            <div class="calc-value" style="color:#008EAA">5.000 €</div>
            <div class="calc-sub">Direkt auf Ihr Konto</div>
          </div>
          <div class="calc-item">
            <div class="calc-label">Ihre Rate</div>
            <div class="calc-value" style="color:#b45309">~145 €</div>
            <div class="calc-sub">Pro Monat / 36 Monate</div>
          </div>
        </div>
        <div class="calc-result">→ Effektive Belastung: nur ~145 €/Monat für vollwertige Unternehmensberatung</div>
      </div>

      <h2 class="section-title" style="margin-top:40px">Was ist enthalten?</h2>
      <div class="feature"><span class="feature-check">✓</span> ISB-158 Förderung: 50 % vom Land Rheinland-Pfalz</div>
      <div class="feature"><span class="feature-check">✓</span> Bis zu 20 Tagewerke à 8 Stunden Beratung</div>
      <div class="feature"><span class="feature-check">✓</span> Strategie, Marketing & Vertriebsoptimierung</div>
      <div class="feature"><span class="feature-check">✓</span> Digitalisierung & KI-Einsatz im Unternehmen</div>
      <div class="feature"><span class="feature-check">✓</span> Kommunikations- & Designberatung (max. 3 TW)</div>
      <div class="feature"><span class="feature-check">✓</span> Persönliches Ergebnis-Portal (passwortgeschützt)</div>
      <div class="feature"><span class="feature-check">✓</span> Leasingfinanzierung: ~145 €/Monat über MMV</div>
      <div class="feature"><span class="feature-check">✓</span> Wir übernehmen Antragstellung & Dokumentation</div>

      <div class="prereq-box">
        <div class="prereq-title">Wer ist förderfähig?</div>
        <div class="prereq-item"><span class="prereq-check">✓</span> Betriebsstätte in Rheinland-Pfalz</div>
        <div class="prereq-item"><span class="prereq-check">✓</span> Weniger als 250 Mitarbeiter & unter 50 Mio. € Umsatz</div>
        <div class="prereq-item"><span class="prereq-check">✓</span> Kein laufendes Insolvenzverfahren</div>
        <div class="prereq-item"><span class="prereq-check">✓</span> Antrag VOR Beratungsbeginn bei der ISB</div>
      </div>
    </div>

    <div>
      <div class="form-card">
        <div id="form-container">
          <div class="form-badge">15 Minuten · Kostenlos & unverbindlich</div>
          <div class="form-title">Jetzt Förderung sichern</div>
          <div class="form-sub">Wir prüfen Ihre Förderfähigkeit und berechnen Ihre individuelle Rate.</div>

          <div id="form-error" class="form-error" style="display:none"></div>

          <div class="form-field">
            <label class="form-label">Name *</label>
            <input class="form-input" type="text" id="f-name" placeholder="Max Mustermann">
          </div>
          <div class="form-field">
            <label class="form-label">Unternehmen *</label>
            <input class="form-input" type="text" id="f-company" placeholder="Mustermann GmbH">
          </div>
          <div class="form-field">
            <label class="form-label">E-Mail *</label>
            <input class="form-input" type="email" id="f-email" placeholder="max@mustermann.de">
          </div>
          <div class="form-field">
            <label class="form-label">Telefon</label>
            <input class="form-input" type="tel" id="f-phone" placeholder="+49 261 ...">
          </div>
          <div class="form-field">
            <label class="form-label">Ihre Situation (optional)</label>
            <textarea class="form-textarea" id="f-message" placeholder="Was möchten Sie erreichen? Welche Herausforderungen haben Sie?"></textarea>
          </div>

          <button class="form-btn" onclick="submitForm()">→ Kostenloses Erstgespräch anfragen</button>
          <div class="form-hint">Kein Risiko · Kein Aufwand · 100 % kostenlos</div>

          <div class="form-trust">
            <div class="form-trust-item">✅ Akkreditierter ISB-Berater</div>
            <div class="form-trust-item">✅ Komplette Förderabwicklung durch KOMPAGNON</div>
            <div class="form-trust-item">✅ B2B-Expertise seit 2005</div>
          </div>
        </div>

        <div id="form-success" class="form-success" style="display:none">
          <div class="form-success-icon">✅</div>
          <div class="form-success-title">Anfrage erhalten!</div>
          <div class="form-success-text">Vielen Dank. Wir melden uns innerhalb von <strong>24 Stunden</strong> für das kostenlose Erstgespräch.</div>
          <div class="form-contact">📞 +49 (0) 261 884470<br>✉ info@kompagnon.eu</div>
        </div>
      </div>
    </div>
  </div>

  <footer class="footer">
    KOMPAGNON communications BP GmbH · Koblenz · Akkreditierter Berater der ISB Rheinland-Pfalz<br>
    <a href="/impressum">Impressum</a>
    <a href="/datenschutz">Datenschutz</a>
  </footer>

  <script>
    const API = 'https://claude-code-znq2.onrender.com';

    async function submitForm() {
      const name    = document.getElementById('f-name').value.trim();
      const company = document.getElementById('f-company').value.trim();
      const email   = document.getElementById('f-email').value.trim();
      const phone   = document.getElementById('f-phone').value.trim();
      const message = document.getElementById('f-message').value.trim();
      const errEl   = document.getElementById('form-error');
      const btn     = document.querySelector('.form-btn');

      if (!name || !company || !email) {
        errEl.textContent = 'Bitte Name, Firma und E-Mail ausfüllen.';
        errEl.style.display = 'block';
        return;
      }
      errEl.style.display = 'none';
      btn.disabled = true;
      btn.textContent = '⏳ Wird gesendet...';

      try {
        const res = await fetch(API + '/api/impuls/anfrage', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name, company, email, phone, message }),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Fehler');
        document.getElementById('form-container').style.display = 'none';
        document.getElementById('form-success').style.display = 'block';
      } catch (err) {
        errEl.textContent = err.message || 'Verbindungsfehler. Bitte erneut versuchen.';
        errEl.style.display = 'block';
        btn.disabled = false;
        btn.textContent = '→ Kostenloses Erstgespräch anfragen';
      }
    }
  </script>
</body>
</html>"""

with engine.connect() as conn:
    existing = conn.execute(
        text("SELECT id FROM public_pages WHERE slug = '/paket/impuls'")
    ).first()

    if existing:
        conn.execute(text("""
            UPDATE public_pages
            SET html_content = :html,
                name = 'IMPULS: Geförderte Beratung',
                page_type = 'paket',
                status = 'draft',
                updated_at = NOW()
            WHERE slug = '/paket/impuls'
        """), {"html": IMPULS_HTML})
        print("IMPULS Landing Page aktualisiert.")
    else:
        conn.execute(text("""
            INSERT INTO public_pages
              (slug, name, page_type, status, html_content, react_component,
               meta_title, meta_description)
            VALUES
              ('/paket/impuls', 'IMPULS: Geförderte Beratung', 'paket', 'draft', :html, '',
               'IMPULS by KOMPAGNON — Geförderte Unternehmensberatung',
               '50 % Förderung vom Land Rheinland-Pfalz. Professionelle Unternehmensberatung für KMU — ISB Betriebsberatungsprogramm 158.')
        """), {"html": IMPULS_HTML})
        print("IMPULS Landing Page neu angelegt.")

    conn.commit()

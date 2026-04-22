/**
 * Handwerk Block-Bibliothek fuer GrapesJS
 * 12 vordefinierte Sektionen — Claude befuellt Inhalte via JSON
 */

export const BLOCK_TYPES = [
  'hero', 'leistungen-grid', 'usp-balken', 'ueber-uns',
  'referenzen', 'team', 'faq', 'kontakt-form',
  'cta-banner', 'oeffnungszeiten', 'testimonials', 'footer'
];

/**
 * Erstellt HTML fuer einen Block aus JSON-Daten
 * Claude liefert data, diese Funktion rendert HTML
 */
export function renderBlock(type, data, brand) {
  const primary   = brand?.primary_color   || '#008EAA';
  const secondary = brand?.secondary_color || '#004F59';
  const font      = brand?.font_primary    || 'Inter, system-ui, sans-serif';
  const radius    = brand?.border_radius   || '8px';

  switch (type) {

    case 'hero':
      return `
<section data-block="hero" style="position:relative;background:${primary};min-height:600px;display:flex;align-items:center;font-family:${font};overflow:hidden;">
  <div style="position:absolute;top:-100px;right:-100px;width:500px;height:500px;background:rgba(255,255,255,0.06);border-radius:50%;"></div>
  <div style="max-width:1140px;margin:0 auto;padding:80px 40px;display:grid;grid-template-columns:1fr 1fr;gap:64px;align-items:center;width:100%;position:relative;z-index:1;">
    <div>
      ${data.badge ? `<div style="display:inline-flex;align-items:center;gap:8px;background:rgba(255,255,255,0.15);border:1px solid rgba(255,255,255,0.25);color:white;padding:6px 16px;border-radius:100px;font-size:13px;font-weight:600;margin-bottom:24px;">✓ ${data.badge}</div>` : ''}
      <h1 style="font-size:clamp(32px,4.5vw,58px);font-weight:800;line-height:1.1;color:white;margin:0 0 20px;">${data.headline || 'Ihr zuverlässiger Partner vor Ort'}</h1>
      <p style="font-size:clamp(16px,2vw,20px);color:rgba(255,255,255,0.85);line-height:1.6;margin:0 0 36px;">${data.subline || 'Qualität und Erfahrung für Ihr Projekt.'}</p>
      <div style="display:flex;gap:12px;flex-wrap:wrap;">
        <a href="${data.cta_link || '/kontakt'}" style="display:inline-flex;align-items:center;gap:8px;padding:16px 32px;background:white;color:${primary};border-radius:8px;font-weight:700;font-size:16px;text-decoration:none;box-shadow:0 4px 24px rgba(0,0,0,0.2);">${data.cta_text || 'Jetzt anfragen'} →</a>
        ${data.cta2_text ? `<a href="${data.cta2_link || 'tel:+49'}" style="display:inline-flex;padding:16px 28px;background:transparent;border:2px solid rgba(255,255,255,0.5);color:white;border-radius:8px;font-weight:600;font-size:16px;text-decoration:none;">☎ ${data.cta2_text}</a>` : ''}
      </div>
    </div>
    <div style="background:rgba(255,255,255,0.1);backdrop-filter:blur(10px);border:1px solid rgba(255,255,255,0.2);border-radius:20px;padding:36px;">
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:24px;">
        ${(data.fakten || [{zahl:'500+',label:'Kunden'},{zahl:'20 J.',label:'Erfahrung'},{zahl:'4.9 ★',label:'Bewertung'},{zahl:'24h',label:'Notdienst'}]).map(f => `
        <div style="text-align:center;padding:20px 12px;">
          <div style="font-size:32px;font-weight:800;color:white;line-height:1;margin-bottom:8px;">${f.zahl}</div>
          <div style="font-size:13px;color:rgba(255,255,255,0.7);font-weight:500;">${f.label}</div>
        </div>`).join('')}
      </div>
    </div>
  </div>
</section>`;

    case 'leistungen-grid': {
      const items = data.items || [{icon:'🔧',titel:'Leistung 1',beschreibung:'Professionelle Ausführung.'},{icon:'⚡',titel:'Leistung 2',beschreibung:'Schnell und zuverlässig.'},{icon:'🏠',titel:'Leistung 3',beschreibung:'Qualität die überzeugt.'}];
      return `
<section data-block="leistungen-grid" style="padding:80px 40px;background:#F9FAFB;font-family:${font};">
  <div style="max-width:1140px;margin:0 auto;">
    <div style="text-align:center;margin-bottom:56px;">
      <span style="color:${primary};font-weight:700;font-size:13px;letter-spacing:0.1em;text-transform:uppercase;display:block;margin-bottom:12px;">Unsere Stärken</span>
      <h2 style="font-size:clamp(26px,3.5vw,40px);font-weight:700;color:#111827;margin:0;">${data.headline || 'Was wir für Sie tun'}</h2>
    </div>
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:24px;">
      ${items.map(item => `
      <div style="background:white;border:1px solid #E5E7EB;border-radius:16px;padding:32px;transition:transform 0.2s,box-shadow 0.2s;" onmouseover="this.style.transform='translateY(-4px)';this.style.boxShadow='0 12px 40px rgba(0,0,0,0.1)'" onmouseout="this.style.transform='';this.style.boxShadow=''">
        <div style="width:52px;height:52px;background:${primary}18;border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:24px;margin-bottom:20px;">${item.icon || '✓'}</div>
        <h3 style="font-size:18px;font-weight:700;color:#111827;margin:0 0 10px;">${item.titel || 'Leistung'}</h3>
        <p style="color:#6B7280;font-size:15px;line-height:1.6;margin:0;">${item.beschreibung || 'Professionelle Ausführung.'}</p>
      </div>`).join('')}
    </div>
  </div>
</section>`;
    }

    case 'usp-balken': {
      const usps = data.items || [];
      return `
<section data-block="usp-balken" style="
  padding:32px 40px; background:${primary}; font-family:${font};
">
  <div style="max-width:1100px; margin:0 auto;
    display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:24px;">
    ${usps.map(u => `
    <div style="text-align:center; color:white;">
      <div style="font-size:32px; margin-bottom:6px;">${u.icon || '\u2713'}</div>
      <div style="font-size:16px; font-weight:700;">${u.titel}</div>
      ${u.sub ? `<div style="font-size:13px; opacity:.8; margin-top:2px;">${u.sub}</div>` : ''}
    </div>`).join('')}
  </div>
</section>`;
    }

    case 'ueber-uns':
      return `
<section data-block="ueber-uns" style="
  padding:80px 40px; background:white; font-family:${font};
">
  <div style="max-width:1100px; margin:0 auto;
    display:grid; grid-template-columns:1fr 1fr; gap:64px; align-items:center;">
    <div>
      <span style="font-size:12px; font-weight:700; color:${primary};
        text-transform:uppercase; letter-spacing:.1em;">
        ${data.label || 'Ueber uns'}
      </span>
      <h2 style="font-size:clamp(24px,3vw,36px); font-weight:700; color:#0f172a;
        margin:12px 0 20px; line-height:1.3;">
        ${data.headline || 'Ihr Partner vor Ort'}
      </h2>
      <p style="color:#475569; font-size:16px; line-height:1.8; margin:0 0 24px;">
        ${data.text || ''}
      </p>
      ${data.facts ? `
      <div style="display:flex; gap:32px; flex-wrap:wrap; margin-bottom:28px;">
        ${data.facts.map(f => `
        <div>
          <div style="font-size:28px; font-weight:800; color:${primary};">${f.zahl}</div>
          <div style="font-size:13px; color:#64748b;">${f.label}</div>
        </div>`).join('')}
      </div>` : ''}
      ${data.cta_text ? `
      <a href="${data.cta_link || '/kontakt'}" style="
        display:inline-block; padding:14px 28px; background:${primary};
        color:white; border-radius:${radius}; font-weight:700; text-decoration:none;
      ">${data.cta_text}</a>` : ''}
    </div>
    <div style="border-radius:${radius}; overflow:hidden; background:#f1f5f9;
      aspect-ratio:4/3; display:flex; align-items:center; justify-content:center;">
      ${data.bild
        ? `<img src="${data.bild}" alt="${data.headline || ''}"
            style="width:100%; height:100%; object-fit:cover;">`
        : `<div style="font-size:64px; opacity:.2;">🏢</div>`}
    </div>
  </div>
</section>`;

    case 'cta-banner':
      return `
<section data-block="cta-banner" style="
  padding:64px 40px; background:${secondary}; text-align:center; font-family:${font};
">
  <h2 style="font-size:clamp(22px,3vw,36px); font-weight:700; color:white; margin:0 0 12px;">
    ${data.headline || 'Bereit loszulegen?'}
  </h2>
  <p style="color:rgba(255,255,255,.85); font-size:18px; margin:0 0 32px;">
    ${data.subline || 'Kontaktieren Sie uns noch heute'}
  </p>
  <div style="display:flex; gap:12px; justify-content:center; flex-wrap:wrap;">
    <a href="${data.cta_link || '/kontakt'}" style="
      padding:16px 36px; background:white; color:${secondary};
      border-radius:${radius}; font-weight:700; font-size:16px; text-decoration:none;
    ">${data.cta_text || 'Jetzt anfragen'}</a>
    ${data.phone ? `
    <a href="tel:${data.phone}" style="
      padding:16px 36px; border:2px solid white; color:white;
      border-radius:${radius}; font-weight:700; font-size:16px; text-decoration:none;
    ">${data.phone}</a>` : ''}
  </div>
</section>`;

    case 'kontakt-form':
      return `
<section data-block="kontakt-form" style="
  padding:80px 40px; background:#f8fafc; font-family:${font};
">
  <div style="max-width:640px; margin:0 auto;">
    <h2 style="font-size:clamp(24px,3vw,32px); font-weight:700; color:#0f172a;
      margin:0 0 8px; text-align:center;">
      ${data.headline || 'Kontakt aufnehmen'}
    </h2>
    <p style="text-align:center; color:#64748b; margin:0 0 40px;">
      ${data.subline || 'Wir antworten innerhalb von 24 Stunden'}
    </p>
    <form style="display:flex; flex-direction:column; gap:16px;">
      <div style="display:grid; grid-template-columns:1fr 1fr; gap:16px;">
        <input type="text" placeholder="Vorname" style="padding:12px 16px;
          border:1px solid #e2e8f0; border-radius:${radius}; font-size:14px;
          font-family:${font}; outline:none;">
        <input type="text" placeholder="Nachname" style="padding:12px 16px;
          border:1px solid #e2e8f0; border-radius:${radius}; font-size:14px;
          font-family:${font}; outline:none;">
      </div>
      <input type="email" placeholder="E-Mail-Adresse" style="padding:12px 16px;
        border:1px solid #e2e8f0; border-radius:${radius}; font-size:14px;
        font-family:${font}; outline:none;">
      <input type="tel" placeholder="Telefonnummer" style="padding:12px 16px;
        border:1px solid #e2e8f0; border-radius:${radius}; font-size:14px;
        font-family:${font}; outline:none;">
      <textarea placeholder="${data.nachricht_placeholder || 'Ihre Nachricht...'}"
        rows="5" style="padding:12px 16px; border:1px solid #e2e8f0;
        border-radius:${radius}; font-size:14px; font-family:${font};
        resize:vertical; outline:none;"></textarea>
      <button type="submit" style="padding:14px; background:${primary}; color:white;
        border:none; border-radius:${radius}; font-size:16px; font-weight:700;
        cursor:pointer; font-family:${font};">
        ${data.cta_text || 'Nachricht senden'}
      </button>
    </form>
  </div>
</section>`;

    case 'footer':
      return `
<footer data-block="footer" style="
  padding:48px 40px 24px; background:#0f172a; color:white; font-family:${font};
">
  <div style="max-width:1100px; margin:0 auto;">
    <div style="display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr));
      gap:40px; margin-bottom:40px;">
      <div>
        <div style="font-size:18px; font-weight:800; margin-bottom:12px;">
          ${data.firma || 'Ihr Betrieb'}
        </div>
        <div style="color:rgba(255,255,255,.6); font-size:13px; line-height:1.8;">
          ${data.adresse || ''}<br>
          ${data.telefon ? `<a href="tel:${data.telefon}" style="color:${primary};
            text-decoration:none;">${data.telefon}</a>` : ''}
        </div>
      </div>
      <div>
        <div style="font-weight:700; margin-bottom:12px;">Leistungen</div>
        <div style="display:flex; flex-direction:column; gap:6px;">
          ${(data.leistungen_links || []).map(l =>
            `<a href="${l.link}" style="color:rgba(255,255,255,.6); text-decoration:none;
              font-size:13px;">${l.label}</a>`).join('')}
        </div>
      </div>
      <div>
        <div style="font-weight:700; margin-bottom:12px;">Rechtliches</div>
        <div style="display:flex; flex-direction:column; gap:6px;">
          <a href="/impressum" style="color:rgba(255,255,255,.6); font-size:13px; text-decoration:none;">Impressum</a>
          <a href="/datenschutz" style="color:rgba(255,255,255,.6); font-size:13px; text-decoration:none;">Datenschutz</a>
          ${data.agb ? `<a href="/agb" style="color:rgba(255,255,255,.6); font-size:13px; text-decoration:none;">AGB</a>` : ''}
        </div>
      </div>
    </div>
    <div style="border-top:1px solid rgba(255,255,255,.1); padding-top:20px;
      text-align:center; font-size:12px; color:rgba(255,255,255,.4);">
      ${data.firma || 'Ihr Betrieb'} · Alle Rechte vorbehalten
    </div>
  </div>
</footer>`;

    default:
      return `<section data-block="${type}" style="padding:40px; background:#f8fafc;">
        <p style="text-align:center; color:#64748b;">Block: ${type}</p>
      </section>`;
  }
}

/**
 * Komplette Seite aus Block-Array rendern
 */
export function renderPage(blocks, brand) {
  const fontFamily = (brand?.font_primary || 'Inter').replace(/ /g, '+');
  const head = `<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@600;700;800&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: 'Inter', ${brand?.font_primary || 'system-ui'}, sans-serif; }
h1, h2, h3, h4 { font-family: 'Poppins', ${brand?.font_primary || 'system-ui'}, sans-serif; }
@media (max-width: 768px) {
  section { padding-left: 20px !important; padding-right: 20px !important; }
  [data-block="hero"] > div > div { grid-template-columns: 1fr !important; }
  [data-block="leistungen-grid"] > div > div:last-child { grid-template-columns: 1fr !important; }
  [data-block="usp-balken"] > div { grid-template-columns: 1fr 1fr !important; }
}
</style>
</head>
<body>`;

  const body = blocks
    .map(b => renderBlock(b.type, b.data || {}, brand))
    .join('\n');

  return head + body + '</body></html>';
}

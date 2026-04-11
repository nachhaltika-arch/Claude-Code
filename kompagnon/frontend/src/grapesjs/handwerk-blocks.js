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
<section data-block="hero" style="
  background: linear-gradient(135deg, ${primary} 0%, ${secondary} 100%);
  padding: 80px 40px; text-align: center; color: white;
  font-family: ${font};
">
  <h1 style="font-size: clamp(28px,5vw,52px); font-weight:800; margin:0 0 16px; line-height:1.2;">
    ${data.headline || 'Ihr zuverlaessiger Partner'}
  </h1>
  <p style="font-size:clamp(16px,2vw,22px); margin:0 0 32px; opacity:.9; max-width:600px; margin-left:auto; margin-right:auto;">
    ${data.subline || 'Qualitaet und Erfahrung seit Jahren'}
  </p>
  <div style="display:flex; gap:12px; justify-content:center; flex-wrap:wrap;">
    <a href="${data.cta_link || '/kontakt'}" style="
      display:inline-block; padding:16px 36px; background:white; color:${primary};
      border-radius:${radius}; font-weight:700; font-size:16px; text-decoration:none;
      transition:transform .15s;
    ">${data.cta_text || 'Jetzt anfragen'}</a>
    ${data.cta2_text ? `
    <a href="${data.cta2_link || 'tel:+49'}" style="
      display:inline-block; padding:16px 36px; background:transparent;
      border:2px solid white; color:white; border-radius:${radius};
      font-weight:700; font-size:16px; text-decoration:none;
    ">${data.cta2_text}</a>` : ''}
  </div>
  ${data.badge ? `
  <div style="margin-top:24px; display:inline-block; background:rgba(255,255,255,.15);
    padding:8px 20px; border-radius:99px; font-size:13px;">
    ${data.badge}
  </div>` : ''}
</section>`;

    case 'leistungen-grid': {
      const leistungen = data.items || [];
      return `
<section data-block="leistungen-grid" style="
  padding:72px 40px; background:#f8fafc; font-family:${font};
">
  <div style="max-width:1100px; margin:0 auto;">
    <h2 style="text-align:center; font-size:clamp(24px,3vw,36px); font-weight:700;
      color:#0f172a; margin:0 0 12px;">
      ${data.headline || 'Unsere Leistungen'}
    </h2>
    <p style="text-align:center; color:#64748b; margin:0 0 48px; font-size:17px;">
      ${data.subline || ''}
    </p>
    <div style="display:grid; grid-template-columns:repeat(auto-fill,minmax(280px,1fr)); gap:24px;">
      ${leistungen.map(l => `
      <div style="background:white; border-radius:${radius}; padding:28px;
        box-shadow:0 1px 4px rgba(0,0,0,.06); border-top:3px solid ${primary};">
        <div style="font-size:36px; margin-bottom:12px;">${l.icon || '🔧'}</div>
        <h3 style="font-size:18px; font-weight:700; color:#0f172a; margin:0 0 10px;">
          ${l.titel}
        </h3>
        <p style="color:#64748b; font-size:14px; line-height:1.7; margin:0;">
          ${l.beschreibung || ''}
        </p>
        ${l.link ? `<a href="${l.link}" style="display:inline-block; margin-top:16px;
          color:${primary}; font-weight:600; font-size:13px; text-decoration:none;">
          Mehr erfahren</a>` : ''}
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
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: ${brand?.font_primary || 'system-ui'}, sans-serif; }
@media (max-width: 768px) {
  section { padding-left: 20px !important; padding-right: 20px !important; }
  [style*="grid-template-columns: 1fr 1fr"] { grid-template-columns: 1fr !important; }
}
</style>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=${fontFamily}:wght@400;600;700;800&display=swap">
</head>
<body>`;

  const body = blocks
    .map(b => renderBlock(b.type, b.data || {}, brand))
    .join('\n');

  return head + body + '</body></html>';
}

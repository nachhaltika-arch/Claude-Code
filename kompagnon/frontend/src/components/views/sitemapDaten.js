/**
 * Der Wortschatz der Sitemap-Ansicht — Kataloge, Masse, reine Helfer (L-25).
 *
 * Am 2026-08-30 aus `SitemapViewV2.jsx` herausgeloest; die Datei trug 2.210
 * Zeilen und darin die Ansicht **und** ihre siebzehn Unterkomponenten.
 *
 * **Diese Datei ging zuerst**, weil alle vier anderen sie brauchen: Wer den
 * Abschnittskatalog bei einer der Komponenten liesse, zwaenge die uebrigen
 * drei, ihre Nachbarin zu importieren — und ein Ringschluss waere nur eine
 * Frage der Zeit. Dieselbe Ueberlegung wie beim Kriterienkatalog im Backend
 * am selben Tag.
 *
 * Es steht nichts darin, was einen Zustand haelt. Reine Werte, reine
 * Funktionen.
 */

export const KC_DARK = 'var(--kc-dark)';
export const KC_MID = 'var(--kc-mid)';
export const KC_YELLOW = 'var(--kc-yellow)';

// Spiegelung des Backend-SECTION_CATALOG (routers/sitemap.py).
export const SECTION_CATALOG = {
  header_nav:          'Sticky-Header: Logo + Hauptnavigation + ggf. CTA-Button',
  hero_value_equation: 'Hero mit Hormozi-Outcome+Time+Effort-Versprechen (Startseite)',
  hero_service:        'Hero für Service-Detail-Page mit klarem Outcome',
  hero_minimal:        'Kompakter Hero — für Über uns / Kontakt / Rechtliches',
  problem:             'Pain-Point-Section — typische Schmerzen der Zielgruppe',
  offer_stack:         'Hormozi-Wertbox: EUR-Positionen + Gesamtwert + Anker',
  process_steps:       '4-6 nummerierte Schritte mit Zeitangabe',
  guarantee_block:     '5 AGB-konforme Garantien (Risk Reversal)',
  urgency_block:       'Echte Stichtage (BAFA/GEG/Slot-Cap)',
  trust_strip:         'Logo-Streifen (Innung, Hersteller, Zertifikate)',
  fallstudien_3:       '3 Fallstudien-Cards mit Zahlen',
  service_grid:        'Übersicht aller Services',
  team:                'Team-/Meister-Vorstellung mit Fotos',
  faq:                 'Allgemeine FAQ — 8-12 Fragen',
  faq_service:         'Service-spezifische FAQ',
  content_richtext:    'Reiner Fließtext-Block — für Info-/Rechtsseiten',
  cta_inline:          'Inline-CTA zwischen Sections',
  cta_final:           'Finale CTA + Sticky-Mobile-Bottom-Bar',
  contact_form:        'Kontakt-Formular mit Tel/Mail/WhatsApp',
  footer_legal:        'Footer mit Pflicht-Links',
};

// Lesbare Labels fuer die Section-Keys in der Page-Card.
export const SECTION_LABEL = {
  header_nav:          'Header / Navigation',
  hero_value_equation: 'Hero (Value-Equation)',
  hero_service:        'Hero (Service)',
  hero_minimal:        'Hero (Minimal)',
  problem:             'Problem-Section',
  offer_stack:         'Offer-Stack',
  process_steps:       'Prozess-Schritte',
  guarantee_block:     'Garantien',
  urgency_block:       'Urgency / Stichtage',
  trust_strip:         'Trust-Strip',
  fallstudien_3:       'Fallstudien (3)',
  service_grid:        'Service-Grid',
  team:                'Team',
  faq:                 'FAQ',
  faq_service:         'FAQ (Service)',
  content_richtext:    'Fließtext-Block',
  cta_inline:          'CTA (inline)',
  cta_final:           'CTA (final)',
  contact_form:        'Kontakt-Formular',
  footer_legal:        'Footer',
};

export const PAGE_TYPE_OPTIONS = [
  { value: 'startseite', label: 'Startseite' },
  { value: 'leistung',   label: 'Leistungsseite' },
  { value: 'info',       label: 'Info-Seite' },
  { value: 'vertrauen',  label: 'Vertrauensseite' },
  { value: 'conversion', label: 'Kontakt' },
  { value: 'rechtlich',  label: 'Rechtlich' },
  { value: 'sonstige',   label: 'Sonstige' },
  { value: 'ground',     label: 'Übersicht' },
];

export const TYPE_META = {
  startseite: { label: 'Startseite',      icon: '🏠' },
  leistung:   { label: 'Leistungsseite',  icon: '🔧' },
  info:       { label: 'Info-Seite',      icon: 'ℹ️' },
  vertrauen:  { label: 'Vertrauensseite', icon: '⭐' },
  conversion: { label: 'Kontakt',         icon: '📞' },
  rechtlich:  { label: 'Rechtlich',       icon: '⚖️' },
  sonstige:   { label: 'Sonstige',        icon: '📄' },
  ground:     { label: 'Übersicht',       icon: '📋' },
};

export const PAGE_W = 280;       // Pixel-Breite einer Page-Karte
export const COL_GAP = 40;       // Abstand zwischen Geschwister-Spalten
export const ROW_GAP = 56;       // Abstand zwischen Eltern und Kinder-Reihe (inkl. Connector)

// Phase C: Link-Extraktion aus Block-Slots
// ─────────────────────────────────────────────────────────────────────────────
// Heuristik: ein Slot ist ein Link wenn:
//   - sein Key 'url'/'link'/'href' enthaelt, ODER
//   - sein Wert mit http(s)://, /, oder # beginnt
// Externe Links: http(s):// (nicht auf eine eigene sitemap_page deutend)
// Interne Links: relativer Pfad oder URL deren letzter Path-Teil mit einer
//                Page in dieser Sitemap matcht (slugified page_name).


export function slugify(s) {
  if (!s || typeof s !== 'string') return '';
  return s.toLowerCase()
    .replace(/ä/g, 'ae').replace(/ö/g, 'oe').replace(/ü/g, 'ue').replace(/ß/g, 'ss')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

export function isUrlSlot(key, value) {
  if (!value || typeof value !== 'string') return false;
  const k = (key || '').toLowerCase();
  if (k.includes('url') || k.includes('link') || k.includes('href')) return true;
  return /^(https?:\/\/|\/|#)/.test(value.trim());
}

export function isExternalUrl(value) {
  return /^https?:\/\//i.test(value || '');
}

// Versucht, einen Link-Wert auf eine Page in der Sitemap zu mappen.
// Strategien:
//   - relativer Pfad (/wallbox-installation) → Slug-Match
//   - http(s)://eigene-domain/path → Path-Match
//   - reines Page-Name-Fragment → Slug-Match
export function matchInternalPage(value, pageSlugMap) {
  if (!value || typeof value !== 'string') return null;
  let v = value.trim();
  // http(s):// strippen, um den Path zu bekommen
  if (/^https?:\/\//i.test(v)) {
    try {
      const url = new URL(v);
      v = url.pathname + (url.hash || '');
    } catch (_) {
      return null;
    }
  }
  // Hash-/Anker-Links '#section' sind seitenintern → nicht auf andere Page mappen
  if (v.startsWith('#')) return null;
  // Slashes + trailing entfernen
  const cleaned = v.replace(/^\/+|\/+$/g, '').toLowerCase();
  if (!cleaned) return null;
  // Direkter Slug-Match
  if (pageSlugMap.has(cleaned)) return pageSlugMap.get(cleaned);
  // Erstes Segment als Slug versuchen (z.B. /wallbox-installation/foerderung)
  const firstSegment = cleaned.split('/')[0];
  if (firstSegment && pageSlugMap.has(firstSegment)) return pageSlugMap.get(firstSegment);
  return null;
}

// ─────────────────────────────────────────────────────────────────────────────

// Phase 2: Globale Sections — werden konventionell auf jeder Seite verwendet.
// In der Add-Sidebar oben hervorgehoben mit Instance-Count.
export const GLOBAL_SECTION_KEYS = ['header_nav', 'footer_legal'];

// Kategorien fuer die Add-Sidebar — gruppiert nach semantischer Naehe.
export const SIDEBAR_CATEGORIES = [
  { label: 'Hero',                items: ['hero_value_equation', 'hero_service', 'hero_minimal'] },
  { label: 'Problem & Offer',     items: ['problem', 'offer_stack'] },
  { label: 'Trust / Social Proof', items: ['guarantee_block', 'urgency_block', 'trust_strip', 'fallstudien_3'] },
  { label: 'Process',             items: ['process_steps'] },
  { label: 'Service & Team',      items: ['service_grid', 'team'] },
  { label: 'FAQ',                 items: ['faq', 'faq_service'] },
  { label: 'Content',             items: ['content_richtext'] },
  { label: 'CTA & Contact',       items: ['cta_inline', 'cta_final', 'contact_form'] },
];

// ─────────────────────────────────────────────────────────────────────────────


// ── Die Knopfstile der Sitemap-Ansicht ───────────────────────────────
//
// **Sie standen am Dateiende und landeten beim Aufteilen (L-25, 30.08.2026)
// zunaechst bei den Dialogen** — obwohl die Ansicht selbst und die
// Werkzeugleiste sie ebenso brauchen. Der Build hat es gemeldet: sechs Mal
// „btnSecondary is not defined". Gemeinsames gehoert hierher, sonst importiert
// eine Komponente ihre Nachbarin.
// btnPrimary = der eine Gelb-CTA. btnTeal = Dark-Teal-Solid für sekundäre
// aktive Aktionen. btnSecondary = Outline für Hilfsaktionen.
export const btnPrimary = {
  background: KC_YELLOW, color: '#000',
  border: 'none', borderRadius: 8,
  padding: '8px 16px', fontSize: 12, fontWeight: 800,
  cursor: 'pointer',
  textTransform: 'uppercase', letterSpacing: '0.04em',
  fontFamily: 'inherit',
};
export const btnTeal = {
  background: KC_DARK, color: '#fff',
  border: 'none', borderRadius: 8,
  padding: '8px 16px', fontSize: 12, fontWeight: 700,
  cursor: 'pointer', fontFamily: 'inherit',
};
export const btnSecondary = {
  background: 'transparent', color: KC_DARK,
  border: `1.5px solid ${KC_DARK}`, borderRadius: 8,
  padding: '8px 14px', fontSize: 12, fontWeight: 700,
  cursor: 'pointer', fontFamily: 'inherit',
};

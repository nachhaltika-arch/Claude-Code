/**
 * Kataloge, Farben und Ableitungen des Auditberichts (L-25).
 *
 * Am 2026-08-30 aus `AuditReport.jsx` herausgeloest — 190 der damals 1.025
 * Zeilen. Hier stehen die Stufen, die Kategorien, die Hostingpunkte und die
 * drei kleinen Ableitungen (`buildViewCategories`, `scoreColor`, `scoreIcon`);
 * in `auditTeile.jsx` die Kategorieabschnitte und das Netzdiagramm.
 */


export const LEVEL_STYLES = {
  'Homepage Standard Platin': { bg: '#e8eaf6', color: '#283593', icon: '\uD83C\uDFC6' },
  'Homepage Standard Gold':   { bg: '#fff8e1', color: '#f57f17', icon: '\uD83E\uDD47' },
  'Homepage Standard Silber': { bg: '#f5f5f5', color: '#616161', icon: '\uD83E\uDD48' },
  'Homepage Standard Bronze': { bg: '#efebe9', color: '#4e342e', icon: '\uD83E\uDD49' },
  'Nicht konform':            { bg: '#fdecea', color: '#C8102E', icon: '⛔' },
};

export const CATEGORIES = [
  {
    key: 'rechtliche_compliance',
    label: 'Rechtliche Compliance',
    shortLabel: 'Rechtlich',
    max: 30,
    color: '#3f51b5',
    items: [
            // Diese Liste ist der **Rueckfall fuer Altbestaende** — Audits ohne
      // mitgelieferten Katalog. Ihre Punktzahlen sind deshalb bewusst die
      // alten (Impressum 7 statt heute 6): So wurden diese Audits damals
      // gerechnet. Neue Audits laufen ueber `audit.catalogue`.
      // Was hier nicht bleiben darf, ist die Rechtsangabe: Das TMG ist
      // seit Mai 2024 abgeloest (25.08.2026).
      { key: 'rc_impressum',    label: 'Impressum (§ 5 DDG)',              max: 7 },
      { key: 'rc_datenschutz',  label: 'Datenschutzerklärung (DSGVO)', max: 7 },
      { key: 'rc_cookie',       label: 'Cookie Consent (TDDDG)',            max: 6 },
      { key: 'rc_bfsg',         label: 'Barrierefreiheitserklärung (BFSG)', max: 4 },
      { key: 'rc_urheberrecht', label: 'Urheberrecht & Lizenzen',          max: 3 },
      { key: 'rc_ecommerce',    label: 'E-Commerce Pflichten',             max: 3 },
    ],
  },
  {
    key: 'technische_performance',
    label: 'Technische Performance',
    shortLabel: 'Performance',
    max: 20,
    color: '#2196f3',
    items: [
      { key: 'tp_lcp',    label: 'LCP (Ladezeit Hauptinhalt)',  max: 5 },
      { key: 'tp_cls',    label: 'CLS (Layout-Stabilität)', max: 4 },
      { key: 'tp_inp',    label: 'INP (Interaktionszeit)',      max: 3 },
      { key: 'tp_mobile', label: 'Mobile-First Design',         max: 4 },
      { key: 'tp_bilder', label: 'Bildoptimierung',             max: 4 },
    ],
  },
  {
    key: 'barrierefreiheit',
    label: 'Barrierefreiheit',
    shortLabel: 'Barrierefr.',
    max: 20,
    color: '#9c27b0',
    items: [
      { key: 'bf_kontrast',     label: 'Farbkontraste (WCAG AA)',           max: 5 },
      { key: 'bf_tastatur',     label: 'Tastaturzugänglichkeit',       max: 5 },
      { key: 'bf_screenreader', label: 'Screenreader-Kompatibilität', max: 5 },
      { key: 'bf_lesbarkeit',   label: 'Lesbarkeit & Textgröße', max: 5 },
    ],
  },
  {
    key: 'sicherheit_datenschutz',
    label: 'Sicherheit & Datenschutz',
    shortLabel: 'Sicherheit',
    max: 15,
    color: '#f44336',
    items: [
      { key: 'si_ssl',          label: 'HTTPS / SSL-Zertifikat',        max: 4 },
      { key: 'si_header',       label: 'Security-Header (HSTS, CSP)',   max: 4 },
      { key: 'si_drittanbieter',label: 'DSGVO Drittanbieter',           max: 4 },
      { key: 'si_formulare',    label: 'Formularsicherheit',            max: 3 },
    ],
  },
  {
    key: 'seo_sichtbarkeit',
    label: 'SEO & Sichtbarkeit',
    shortLabel: 'SEO',
    max: 10,
    color: '#ff9800',
    items: [
      { key: 'se_seo',    label: 'Technische SEO Grundlagen',      max: 4 },
      { key: 'se_schema', label: 'Strukturierte Daten (Schema.org)', max: 3 },
      { key: 'se_lokal',  label: 'Lokale Auffindbarkeit',          max: 3 },
    ],
  },
  {
    key: 'inhalt_nutzererfahrung',
    label: 'Inhalt & Nutzererfahrung',
    shortLabel: 'Inhalt/UX',
    max: 5,
    color: '#4caf50',
    items: [
      { key: 'ux_erstindruck', label: 'Erster Eindruck',           max: 1 },
      { key: 'ux_cta',         label: 'Klare Call-to-Action',      max: 1 },
      { key: 'ux_navigation',  label: 'Navigation & Struktur',     max: 1 },
      { key: 'ux_vertrauen',   label: 'Vertrauenssignale',         max: 1 },
      { key: 'ux_content',     label: 'Content-Qualität',     max: 1 },
      { key: 'ux_kontakt',     label: 'Kontaktmöglichkeiten', max: 1 },
    ],
  },
];

export const HOSTING_ITEMS = [
  { key: 'ho_anbieter', label: 'Anbieter identifizierbar' },
  { key: 'ho_uptime',   label: 'Erreichbarkeit' },
  { key: 'ho_cdn',      label: 'CDN aktiv' },
  { key: 'ho_cms',      label: 'CMS erkannt' },
];

// Farben und Kurzlabels für die Kategorien des überarbeiteten Katalogs.
// Die Kriterien selbst kommen aus der API — hier steht nur die Darstellung.
export const CATEGORY_META = {
  recht_compliance:  { color: '#B02418', shortLabel: 'Recht' },
  sicherheit:        { color: '#7C3AED', shortLabel: 'Sicherheit' },
  performance:       { color: '#2563EB', shortLabel: 'Performance' },
  barrierefreiheit:  { color: 'var(--info)', shortLabel: 'Barrierefrei' },
  seo:               { color: 'var(--success)', shortLabel: 'SEO' },
  design:            { color: '#DB2777', shortLabel: 'Design' },
  conversion:        { color: '#EA580C', shortLabel: 'Conversion' },
  inhalt:            { color: '#65A30D', shortLabel: 'Inhalt' },
};

// Klartext für ausgefallene Prüfungen — "nicht erhoben" allein sagt nicht,
// ob die Website ein Problem hat oder das Audit eines.
export const COLLECTION_REASONS = {
  kontingent_ohne_api_key: 'kein API-Key hinterlegt',
  kontingent_erschoepft:  'Tageskontingent erschöpft',
  api_fehler:             'API-Fehler',
  ausnahme:               'technischer Fehler',
  timeout:                'Zeitüberschreitung',
  handshake_fehlgeschlagen: 'Verbindung fehlgeschlagen',
  // Hinter der Seite steht kein Betrieb — die angebotsbezogenen Kriterien
  // gelten dann nicht und zählen nicht mit. Die erkannte Art der Seite steht
  // im title-Attribut.
  keine_betriebsseite:    'kein Betrieb erkannt — Maßstab nicht anwendbar',
};

// Quellen-Kennzeichnung: macht im Report sichtbar, worauf eine Bewertung fußt.
export const SOURCE_BADGES = {
  gemessen:       { icon: '●', color: 'var(--success)', title: 'Technisch gemessen' },
  abgeleitet:     { icon: '◐', color: '#2563EB', title: 'Aus Messwerten abgeleitet' },
  einschaetzung:  { icon: '◇', color: '#7C3AED', title: 'KI-Einschätzung' },
  nicht_erhoben:  { icon: '○', color: '#9CA3AF', title: 'Nicht erhoben — zählt nicht in den Score' },
};

/**
 * Baut die Kategorie-Ansicht aus der API-Antwort.
 * Nicht erhobene Kriterien fallen aus Punkten UND Maximum heraus, damit eine
 * fehlende Messung nicht als "null Punkte" erscheint.
 * @returns {Array|null} null, wenn das Audit noch nach dem alten Katalog lief
 */
export function buildViewCategories(audit) {
  const hasSources = audit.sources && Object.keys(audit.sources).length > 0;
  if (!Array.isArray(audit.catalogue) || !audit.catalogue.length || !hasSources) {
    return null;
  }

  return audit.catalogue.map((cat) => {
    const collected = cat.criteria.filter((c) => c.collected);
    const meta = CATEGORY_META[cat.key] || {};
    return {
      key: cat.key,
      label: cat.label,
      shortLabel: meta.shortLabel || cat.label,
      color: meta.color || 'var(--brand-primary)',
      score: collected.reduce((sum, c) => sum + (c.score || 0), 0),
      max: collected.reduce((sum, c) => sum + c.max, 0),
      nominalMax: cat.nominal_max,
      criteria: cat.criteria,
    };
  });
}

export function scoreColor(score, max) {
  if (max === 0) return 'var(--text-tertiary)';
  const pct = score / max;
  if (pct >= 1.0) return 'var(--status-success-text)';
  if (pct >= 0.5) return 'var(--status-warning-text)';
  return 'var(--brand-primary)';
}

export function scoreIcon(score, max) {
  if (max === 0) return '—';
  const pct = score / max;
  if (pct >= 1.0) return '✓';
  if (pct >= 0.5) return '⚠';
  return '✗';
}

// ═══════════════════════════════════════════════════════════
// Main Component
// ═══════════════════════════════════════════════════════════


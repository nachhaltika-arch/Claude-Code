/**
 * Der Wortschatz der Komponentenbibliothek — Kategorien, Branchen, Slots (L-25).
 *
 * Am 2026-08-30 aus `ComponentLibrary.jsx` herausgeloest. **Diese Datei ging
 * mit den Feldbausteinen zuerst**, weil alle drei Teile sie brauchen: Der
 * Build hat es gemeldet, sobald sie fehlten — `CATEGORY_OPTIONS is not
 * defined`, dreimal aus zwei verschiedenen Dateien.
 *
 * Es steht nichts darin, was einen Zustand haelt.
 */
export const KC_DARK = 'var(--kc-dark)';
export const KC_MID = 'var(--kc-mid)';

export const CATEGORY_OPTIONS = [
  'NAV', 'HERO', 'LEIST', 'TRUST', 'SEO', 'CTA', 'HW', 'FOOT', 'CUSTOM',
];

export const SOURCES = [
  { id: 'all',    label: 'Alle' },
  { id: 'kas',    label: 'KAS' },
  { id: 'hyperui', label: 'HyperUI' },
  { id: 'custom', label: 'Custom' },
];

// Entwuerfe sind der Normalfall bei KI-erzeugten Bloecken — sie brauchen einen
// eigenen Filter, sonst sucht man sie zwischen 41 freigegebenen.
export const STATES = [
  { id: 'all',      label: 'Alle' },
  { id: 'approved', label: 'Freigegeben' },
  { id: 'draft',    label: 'Entwuerfe' },
];

// Element-Picker im KI-Generator. Counts: User legt Anzahl fest (0 = KI entscheidet).
// Bools: User aktiviert/deaktiviert ein Element (false/leer = KI entscheidet).
export const COUNT_ELEMENTS = [
  { key: 'headline',    label: 'Headlines',    max: 4 },
  { key: 'subtext',     label: 'Subtexte',     max: 5 },
  { key: 'buttons',     label: 'Buttons / CTAs', max: 4 },
  { key: 'links',       label: 'Links',        max: 12 },
  { key: 'images',      label: 'Bilder',       max: 12 },
  { key: 'icons',       label: 'Icons',        max: 12 },
  { key: 'cards',       label: 'Karten',       max: 12 },
  { key: 'avatars',     label: 'Avatare',      max: 6 },
  { key: 'stats',       label: 'Stat-Counter', max: 6 },
  { key: 'form_fields', label: 'Formular-Felder', max: 8 },
];
export const BOOL_ELEMENTS = [
  { key: 'logo',     label: 'Logo' },
  { key: 'dropdown', label: 'Dropdown' },
  { key: 'search',   label: 'Such-Feld' },
  { key: 'rating',   label: 'Star-Rating' },
  { key: 'video',    label: 'Video / iframe' },
  { key: 'list',     label: 'Liste (bullet)' },
];

// Branchen-Dropdown im KI-Generator. Default 'shk' = aktuelle KAS-Niche.
// Backend kennt 'shk' / 'bauhandwerk' / 'gala' / 'maler' / 'kfz' /
// 'steuer-anwalt' / 'medizin' / 'gastro' / 'kosmetik' / 'fitness' /
// 'custom' / 'none'.
export const INDUSTRIES = [
  { id: 'shk',           label: 'SHK (Heizung/Sanitaer/Elektrik)' },
  { id: 'bauhandwerk',   label: 'Bauhandwerk (Maurer, Dachdecker, Trockenbau)' },
  { id: 'gala',          label: 'Garten- und Landschaftsbau' },
  { id: 'maler',         label: 'Maler & Stuckateur' },
  { id: 'kfz',           label: 'KFZ-Werkstatt / Auto-Service' },
  { id: 'steuer-anwalt', label: 'Steuerberater / Anwalt / Versicherung' },
  { id: 'medizin',       label: 'Arzt / Zahnarzt / Praxis' },
  { id: 'gastro',        label: 'Gastronomie / Hotel / Restaurant' },
  { id: 'kosmetik',      label: 'Friseur / Kosmetik / Wellness' },
  { id: 'fitness',       label: 'Fitness / Sport / Yoga' },
  { id: 'custom',        label: 'Custom (selbst beschreiben)…' },
  { id: 'none',          label: 'Keine — generisch' },
];

export function detectSource(tags) {
  const t = (tags || []).map((x) => String(x).toLowerCase());
  if (t.includes('hyperui')) return 'hyperui';
  if (t.includes('custom') || t.includes('user-saved')) return 'custom';
  return 'kas';
}

export function renderSlots(html, slotValues) {
  if (!html) return '';
  if (!slotValues || typeof slotValues !== 'object') return html;
  const escape = (s) => String(s).replace(/[<>&"']/g, (c) => (
    { '<': '&lt;', '>': '&gt;', '&': '&amp;', '"': '&quot;', "'": '&#39;' }[c]
  ));
  let result = html;
  Object.entries(slotValues).forEach(([key, value]) => {
    if (value == null) return;
    const re = new RegExp(`\\{\\{\\s*${key.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\s*\\}\\}`, 'g');
    result = result.replace(re, escape(value));
  });
  return result;
}

export const SLUG_REGEX = /^[a-z0-9][a-z0-9-]*$/;

// Slugify mit deutschen Sonderzeichen-Mapping (vor normalize damit ae/oe/ue/ss
// nicht durch NFD-Decomposition zu a/o/u/s reduziert werden).
export function slugify(text) {
  return (text || '')
    .toLowerCase()
    .replace(/ä/g, 'ae')
    .replace(/ö/g, 'oe')
    .replace(/ü/g, 'ue')
    .replace(/ß/g, 'ss')
    .normalize('NFD').replace(/[̀-ͯ]/g, '')
    .replace(/[^a-z0-9-]+/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-+|-+$/g, '');
}

// Macht slug eindeutig gegen die aktuelle Library — haengt -2/-3/... an wenn noetig.
export function generateUniqueSlug(base, existingSlugs) {
  if (!base) return '';
  const existing = new Set(existingSlugs);
  if (!existing.has(base)) return base;
  let n = 2;
  while (existing.has(`${base}-${n}`)) n++;
  return `${base}-${n}`;
}

export function emptyForm() {
  return {
    slug: '',
    name: '',
    category: 'CUSTOM',
    tags: [],
    html_template: '',
    slots: [],
    ki_prompt_hint: '',
    preview_note: '',
    status: 'approved',
    contract: null,
  };
}


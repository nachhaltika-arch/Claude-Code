/**
 * Kataloge, Masse und der Slot-Ersetzer der Wireframe-Ansicht (L-25).
 *
 * Am 2026-08-30 aus `WireframeView.jsx` herausgeloest; die Datei trug 1.719
 * Zeilen und darin die Ansicht plus vier Unterkomponenten.
 *
 * **Diese Datei ging zuerst**, weil Ansicht und Komponenten sie gleichermassen
 * brauchen. Es steht nichts darin, was einen Zustand haelt.
 */
export const KC_DARK = 'var(--kc-dark)';
export const KC_MID = 'var(--kc-mid)';

export const CATEGORIES = ['Alle', 'NAV', 'HERO', 'LEIST', 'TRUST', 'SEO', 'CTA', 'HW', 'FOOT'];

// W1 Relume-Parität: Responsive-Preview-Breiten. Werte entsprechen den
// Standard-Devices, die Relume's Wireframe-Builder anbietet.
export const PREVIEW_WIDTHS = {
  mobile:  '375px',
  tablet:  '768px',
  desktop: '100%',
};

// W3: ersetzt {{key}}-Marker im html_template durch slot-Werte (HTML-escaped).
// Wird in BlockCard's Live-Preview angewendet — User sieht seine Edits sofort.
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


/**
 * Die Marke über den grauen Wireframe legen.
 *
 * Die Bibliotheksblöcke sind bewusst neutral (Vertragsregel R5 im Backend
 * erzwingt das). Farbe bekommen sie erst hier: Dieses CSS überschreibt die
 * Graustufen-Klassen mit den Tokens aus dem Style-Guide des Kunden.
 *
 * **Gemessen, bevor es geschrieben wurde.** Die alte Fassung kannte nur
 * `gray-*` und `bg-white`. Die 45 Bibliotheksblöcke malen aber zu großen
 * Teilen in `slate-*` (222 Vorkommen), dazu `text-white/80`,
 * `from-gray-900/95`, `bg-gray-600`, `ring-gray-700/30` — **alle 45 Blöcke**
 * enthielten mindestens eine Klasse, die der Override nie angefasst hat. Die
 * Vorschau zeigte also halb Marke, halb Wireframe, und wer den Style-Guide
 * danach freigibt, gibt etwas frei, das so nie aussehen wird.
 *
 * `brandOverride.test.js` prüft gegen die echten Blöcke, dass keine ihrer
 * Farbklassen ungedeckt bleibt.
 *
 * Zwei Dinge, die eine reine Klassen-Abbildung nicht kann und die hier
 * trotzdem stimmen müssen:
 *
 * 1. **Kontext.** `text-gray-300` heißt auf hellem Grund „gedämpft", auf
 *    dunklem Grund „hell auf dunkel". Deshalb gibt es zusätzlich Regeln, die
 *    nur innerhalb einer dunklen Fläche greifen.
 * 2. **Deckkraft.** `bg-white/10` ist eine Aufhellung, kein Weiß. Solche
 *    Varianten werden über `color-mix` mit derselben Deckkraft gebildet.
 */

// Die fünf Graustufen-Familien von Tailwind. Für unseren Zweck sind sie
// gleichwertig — die Bibliothek nutzt `gray` und `slate`, erzeugte Blöcke
// dürfen laut R5 jede davon verwenden.
export const FAMILIEN = ['gray', 'slate', 'zinc', 'neutral', 'stone'];

const STUFEN = [50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 950];

// Ab dieser Stufe ist eine Fläche dunkel — darauf gilt die Umkehrung.
const DUNKEL_AB = 700;

// Deckkraft-Stufen, die Tailwind-Klassen üblicherweise nutzen.
const DECKKRAFT = [5, 10, 15, 20, 25, 30, 40, 50, 60, 70, 75, 80, 85, 90, 95];

/** Rolle einer Fläche (`bg-…`) je Stufe. */
function flaechenRolle(stufe) {
  if (stufe <= 100) return 'surf';
  if (stufe === 200) return 'border';
  // Eigenheit aus der ersten Fassung, bewusst beibehalten: Die hellste
  // Füllung dient in der Bibliothek als Akzent-Pille.
  if (stufe === 300) return 'acc2';
  if (stufe < DUNKEL_AB) return 'muted';
  return 'primary';
}

/** Rolle einer Schrift (`text-…`) je Stufe, auf hellem Grund. */
function schriftRolle(stufe) {
  return stufe >= DUNKEL_AB ? 'text' : 'muted';
}

function selektor(klasse) {
  // `text-white/80` ist als Selektor `.text-white\/80`
  return `.${klasse.replace('/', '\\/')}`;
}

// Jedes Praefix faerbt ueber eine andere CSS-Eigenschaft. `ring` und `outline`
// als `border-color` zu setzen sieht richtig aus und tut nichts.
const EIGENSCHAFT = {
  bg: 'background-color',
  text: 'color',
  border: 'border-color',
  divide: 'border-color',
  ring: '--tw-ring-color',
  outline: 'outline-color',
  from: '--tw-gradient-from',
  via: '--tw-gradient-via',
  to: '--tw-gradient-to',
  accent: 'accent-color',
};

// `divide-*` faerbt nicht das Element selbst, sondern die Trennlinien zwischen
// seinen Kindern — der Selektor muss dorthin zeigen.
function mitKind(sel, praefix) {
  return praefix === 'divide' ? `${sel} > :not(:last-child)` : sel;
}

function mitDeckkraft(farbe, prozent) {
  return `color-mix(in srgb, ${farbe} ${prozent}%, transparent)`;
}

/**
 * Eine Regel über alle fünf Familien — ein Selektor je Familie.
 * @param {string} praefix    Tailwind-Praefix (`bg`, `text`, `ring`, …)
 * @param {(familie: string) => string} bauKlasse  baut den Klassennamen
 * @param {string} farbe      der Farbwert
 * @param {string} umgebung   optionaler Vorsatz, z.B. eine dunkle Flaeche
 */
function regelFuerFamilien(praefix, bauKlasse, farbe, umgebung = '') {
  const selektoren = FAMILIEN
    .map((familie) => mitKind(`${umgebung}${selektor(bauKlasse(familie))}`, praefix))
    .join(',\n');
  return `${selektoren} { ${EIGENSCHAFT[praefix]}: ${farbe} !important; }`;
}

/**
 * Baut das Override-CSS aus dem Style-Guide.
 * @param {object} styleGuide
 * @returns {string}
 */
export function buildOverrideCSS(styleGuide) {
  if (!styleGuide) return '';
  const palette = styleGuide.palette || {};
  const colors = styleGuide.colors || {};
  const typo = styleGuide.typography || {};
  const buttons = styleGuide.buttons || {};
  const spacing = styleGuide.spacing || {};
  const card = styleGuide.card || {};
  const semantic = styleGuide.semantic || {};
  const variants = styleGuide.button_variants || {};

  const bg = palette.bg_primary || colors.background || '#fff';
  const surf = palette.bg_surface || '#f8fafc';
  const text = palette.text_primary || colors.text || '#0a0a0a';
  const muted = palette.text_muted || '#64748b';
  const border = palette.border || '#e2e8f0';
  const acc1 = palette.accent_1 || colors.primary || '#0a0a0a';
  const acc2 = palette.accent_2 || colors.accent || '#FAE600';

  const fontBody = typo.font_family || 'Noto Sans';
  const radiusBtn = buttons.radius || '8px';
  const radiusCard = card.radius || spacing.radius || '8px';

  const primaryBg = variants.primary?.bg || acc1;
  const primaryFg = variants.primary?.fg || bg;
  const primaryBorder = variants.primary?.border || acc1;

  const rolle = { surf, border, acc2, muted, text, primary: primaryBg };

  // Innerhalb einer dunklen Fläche kehrt sich die Bedeutung um: Schrift wird
  // hell, Linien werden durchscheinendes Hell. Statt jede Regel je dunkler
  // Fläche zu wiederholen — das waren 449 KB CSS — setzen die dunklen Flächen
  // drei Custom Properties. Die erben nach innen; jede Regel unten nimmt sie
  // mit `var(…, Fallback)`, und der Fallback gilt auf hellem Grund.
  const AUF_DUNKEL = '--kc-auf-dunkel';
  const GEDAEMPFT = '--kc-auf-dunkel-gedaempft';
  const LINIE = '--kc-auf-dunkel-linie';
  const dunkleFlaechen = FAMILIEN
    .flatMap((f) => STUFEN.filter((s) => s >= DUNKEL_AB).map((s) => `.bg-${f}-${s}`))
    .concat('.bg-black', ...FAMILIEN.flatMap((f) => STUFEN
      .filter((s) => s >= DUNKEL_AB)
      .flatMap((s) => DECKKRAFT.map((d) => `.bg-${f}-${s}\\/${d}`))));

  const imDunkeln = (eigen, hell) => `var(${eigen}, ${hell})`;

  const regeln = [
    `${dunkleFlaechen.join(',\n')} {`
    + `\n  ${AUF_DUNKEL}: ${primaryFg};`
    + `\n  ${GEDAEMPFT}: ${mitDeckkraft(primaryFg, 70)};`
    + `\n  ${LINIE}: ${mitDeckkraft(primaryFg, 20)};\n}`,
  ];

  // ── Flächen, Schrift, Linien ───────────────────────────────────────────
  STUFEN.forEach((stufe) => {
    regeln.push(regelFuerFamilien('bg', (f) => `bg-${f}-${stufe}`,
                                  rolle[flaechenRolle(stufe)]));
    // Helle Stufen sind auf dunklem Grund die helle Schrift, mittlere die
    // gedämpfte — auf hellem Grund bleibt es beim Fallback.
    regeln.push(regelFuerFamilien('text', (f) => `text-${f}-${stufe}`,
                                  stufe >= DUNKEL_AB
                                    ? rolle[schriftRolle(stufe)]
                                    : imDunkeln(stufe <= 300 ? AUF_DUNKEL : GEDAEMPFT,
                                                rolle[schriftRolle(stufe)])));
    ['border', 'divide', 'ring', 'outline'].forEach((praefix) => {
      regeln.push(regelFuerFamilien(praefix, (f) => `${praefix}-${f}-${stufe}`,
                                    imDunkeln(LINIE, border)));
    });
    if (stufe >= DUNKEL_AB) {
      ['from', 'via', 'to'].forEach((praefix) => {
        regeln.push(regelFuerFamilien(praefix, (f) => `${praefix}-${f}-${stufe}`,
                                      primaryBg));
      });
    }
  });

  // ── Grundwörter ────────────────────────────────────────────────────────
  regeln.push(`.bg-white { background-color: ${bg} !important; }`);
  regeln.push(`.text-black { color: ${text} !important; }`);
  regeln.push(`.text-white { color: ${imDunkeln(AUF_DUNKEL, '#fff')} !important; }`);
  regeln.push(`.border-white { border-color: ${imDunkeln(AUF_DUNKEL, '#fff')} !important; }`);
  regeln.push(`.ring-white { --tw-ring-color: ${imDunkeln(AUF_DUNKEL, '#fff')} !important; }`);
  regeln.push(FAMILIEN.map((f) => `.accent-${f}-700`).join(', ')
              + ` { accent-color: ${primaryBg} !important; }`);

  // ── Deckkraft-Varianten ────────────────────────────────────────────────
  //
  // Nur für Weiß und die dunklen Stufen: Genau dort benutzt die Bibliothek sie
  // (`text-white/80`, `bg-gray-700/5`, `from-gray-900/95`). Für jede Stufe
  // jede Deckkraft zu erzeugen würde das CSS vervierfachen, ohne je zu greifen.
  const DUNKLE_STUFEN = STUFEN.filter((s) => s >= DUNKEL_AB);
  DECKKRAFT.forEach((prozent) => {
    regeln.push(`.text-white\\/${prozent} { color: `
                + `${imDunkeln(AUF_DUNKEL, mitDeckkraft('#fff', prozent))} !important; }`);
    regeln.push(`.bg-white\\/${prozent} { background-color: `
                + `${imDunkeln(AUF_DUNKEL, mitDeckkraft('#fff', prozent))} !important; }`);
    regeln.push(`.border-white\\/${prozent} { border-color: `
                + `${imDunkeln(LINIE, mitDeckkraft('#fff', prozent))} !important; }`);
    regeln.push(`.ring-white\\/${prozent} { --tw-ring-color: `
                + `${imDunkeln(LINIE, mitDeckkraft('#fff', prozent))} !important; }`);

    DUNKLE_STUFEN.forEach((stufe) => {
      regeln.push(regelFuerFamilien('bg', (f) => `bg-${f}-${stufe}/${prozent}`,
                                    mitDeckkraft(primaryBg, prozent)));
      ['ring', 'border', 'divide'].forEach((praefix) => {
        regeln.push(regelFuerFamilien(praefix,
                                      (f) => `${praefix}-${f}-${stufe}/${prozent}`,
                                      imDunkeln(LINIE, mitDeckkraft(border, prozent))));
      });
      ['from', 'via', 'to'].forEach((praefix) => {
        regeln.push(regelFuerFamilien(praefix,
                                      (f) => `${praefix}-${f}-${stufe}/${prozent}`,
                                      mitDeckkraft(primaryBg, prozent)));
      });
    });
  });

  return `
/* ─── Marken-Override: Style-Guide über den grauen Wireframe ─── */
body { font-family: '${fontBody}', sans-serif; color: ${text}; background: ${bg}; }
h1, h2, h3, h4 { color: ${text}; }
p { color: ${text}; }

${regeln.join('\n')}

/* Primary-Buttons (dunkle Fläche + helle Schrift) */
.bg-gray-900.text-white, .bg-gray-800.text-white,
.bg-slate-900.text-white, .bg-slate-800.text-white,
button.bg-gray-900, button.bg-slate-900 {
  background-color: ${primaryBg} !important;
  color: ${primaryFg} !important;
  border-color: ${primaryBorder} !important;
}

/* Border-Radius */
.rounded, .rounded-md, .rounded-lg { border-radius: ${radiusBtn} !important; }
.rounded-xl, .rounded-2xl { border-radius: ${radiusCard} !important; }
button { border-radius: ${radiusBtn}; }

/* Status-Bedeutungen — als eigene Klassen direkt verwendbar. */
.status-success { background: ${semantic.success?.bg}; color: ${semantic.success?.fg}; border: 1px solid ${semantic.success?.border}; }
.status-warn    { background: ${semantic.warn?.bg};    color: ${semantic.warn?.fg};    border: 1px solid ${semantic.warn?.border}; }
.status-error   { background: ${semantic.error?.bg};   color: ${semantic.error?.fg};   border: 1px solid ${semantic.error?.border}; }
.status-info    { background: ${semantic.info?.bg};    color: ${semantic.info?.fg};    border: 1px solid ${semantic.info?.border}; }
`.trim();
}

export default buildOverrideCSS;

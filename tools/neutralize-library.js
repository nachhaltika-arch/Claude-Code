#!/usr/bin/env node
/**
 * neutralize-library.js — One-shot Tailwind-Color-Stripper.
 *
 * Geht alle HTML-Files in kompagnon/frontend/src/components/library/ durch
 * und ersetzt non-gray Brand-Farb-Klassen durch ihr Gray-Equivalent
 * (z.B. bg-blue-600 → bg-gray-600). Shade-Zahl bleibt erhalten, damit das
 * Layout-/Kontrast-Verhaeltnis dasselbe bleibt — nur der Farbton wird
 * neutralisiert.
 *
 * Phase B des Library-Cleanups (siehe memory/license_decision_no_relume.md):
 * Library-Komponenten sollen Wireframe-only sein. Brand-Farben kommen
 * spaeter aus dem Style-Guide pro Kunde.
 *
 * Aufruf:
 *   node tools/neutralize-library.js          # nur Diff anzeigen (dry-run)
 *   node tools/neutralize-library.js --write  # Files tatsaechlich ueberschreiben
 */
const fs = require('fs');
const path = require('path');

const LIBRARY_DIR = path.join(
  __dirname, '..', 'kompagnon', 'frontend', 'src', 'components', 'library',
);
const WRITE = process.argv.includes('--write');

const COLOR_NAMES = [
  'red', 'orange', 'amber', 'yellow', 'lime', 'green', 'emerald', 'teal',
  'cyan', 'sky', 'blue', 'indigo', 'violet', 'purple', 'fuchsia', 'pink', 'rose',
];

// Tailwind-Utilities, die mit color-name-shade enden koennen.
const COLOR_UTILITIES = [
  'bg', 'text', 'border', 'ring', 'divide', 'placeholder', 'accent',
  'from', 'to', 'via', 'fill', 'stroke', 'outline', 'caret', 'decoration',
];

const COLOR_GROUP = COLOR_NAMES.join('|');
const UTILITY_GROUP = COLOR_UTILITIES.join('|');

// Match: optional-prefix + utility + - + color + - + shade
// Prefix kann sein: hover:, focus:, dark:, md:, group-hover:, peer-checked:, etc.
// Wir matchen nicht den Prefix selbst — er bleibt unveraendert; wir matchen
// nur die utility-color-shade-Sequenz und ersetzen color → 'gray'.
const COLOR_CLASS_RE = new RegExp(
  `(\\b(?:${UTILITY_GROUP}))-(?:${COLOR_GROUP})-(\\d{2,3}\\b)`,
  'g',
);

function walkHtml(dir, files = []) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) walkHtml(full, files);
    else if (entry.isFile() && entry.name.endsWith('.html')) files.push(full);
  }
  return files;
}

// Tailwind-Arbitrary-Value-Klassen mit hardcoded Hex-Farben.
// Match: utility-[#hex] oder utility-[#hex/opacity]
// Diese muss man explizit mappen — kein Shade-Number-Mapping moeglich, weil
// die Brand-Farben nicht direkt einer gray-Shade entsprechen. Lightness-
// basiert mappen wir auf die nahesten Wireframe-Standards.
const HEX_CLASS_RE = new RegExp(
  `(\\b(?:${UTILITY_GROUP}))-\\[#([0-9a-fA-F]{3,8})(/\\d+)?\\]`,
  'g',
);

const HEX_TO_GRAY = {
  '004F59': '900', // KC_DARK (dark teal) — sehr dunkel
  '008EAA': '700', // KC_MID (teal) — mid-dark
  '0072B1': '700', // LinkedIn-Blau — mid-dark
  '25D366': '600', // WhatsApp-Gruen — mid
  'FAE600': '300', // KC_YELLOW — hell-mid Akzent
};

function neutralize(content) {
  let out = content.replace(COLOR_CLASS_RE, (m, utility, shade) => `${utility}-gray-${shade}`);
  out = out.replace(HEX_CLASS_RE, (m, utility, hex, opacity) => {
    const shade = HEX_TO_GRAY[hex.toUpperCase()];
    if (!shade) return m; // unbekannter Hex — unveraendert lassen, manuell pruefen
    return `${utility}-gray-${shade}${opacity || ''}`;
  });
  return out;
}

function diffSummary(before, after) {
  const beforeColor = before.match(COLOR_CLASS_RE) || [];
  const beforeHex   = before.match(HEX_CLASS_RE) || [];
  const afterColor  = after.match(COLOR_CLASS_RE) || [];
  const afterHex    = after.match(HEX_CLASS_RE) || [];
  return {
    replaced:
      (beforeColor.length - afterColor.length)
      + (beforeHex.length - afterHex.length),
    remaining: afterColor.length + afterHex.length,
  };
}

function relPath(p) {
  return path.relative(path.join(__dirname, '..'), p).replace(/\\/g, '/');
}

const files = walkHtml(LIBRARY_DIR);
let totalReplaced = 0;
let filesChanged = 0;
const changedList = [];

for (const file of files) {
  const before = fs.readFileSync(file, 'utf8');
  const after = neutralize(before);
  if (before === after) continue;
  const { replaced } = diffSummary(before, after);
  totalReplaced += replaced;
  filesChanged++;
  changedList.push({ file, replaced });
  if (WRITE) fs.writeFileSync(file, after, 'utf8');
}

console.log(`\nTotal HTML files scanned: ${files.length}`);
console.log(`Files with brand-color classes: ${filesChanged}`);
console.log(`Total color-class replacements: ${totalReplaced}`);
console.log(`\n${WRITE ? '✓ Files updated.' : '(dry-run — pass --write to apply)'}\n`);

console.log('--- Changes per file ---');
for (const { file, replaced } of changedList.sort((a, b) => b.replaced - a.replaced)) {
  console.log(`  ${replaced.toString().padStart(3)}× ${relPath(file)}`);
}

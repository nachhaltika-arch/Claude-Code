/**
 * Der Maßstab ist die echte Bibliothek — wie beim Block-Vertrag im Backend.
 *
 * Die alte Fassung des Overrides kannte nur `gray-*` und `bg-white`. Alle 45
 * Blöcke enthielten mindestens eine Farbklasse, die sie nie angefasst hat; die
 * Vorschau zeigte halb Marke, halb Wireframe. Dieser Test liest die Blöcke,
 * sammelt jede farbgebende Klasse und verlangt, dass für jede ein Selektor
 * existiert. Kommt ein neuer Block mit einer neuen Klasse dazu, fällt es hier
 * auf und nicht beim Kunden.
 */
const fs = require('fs');
const path = require('path');

const { buildOverrideCSS, FAMILIEN } = require('./brandOverride');

const BIBLIOTHEK = path.join(__dirname, '..', 'components', 'library');

const STYLE_GUIDE = {
  palette: {
    bg_primary: '#FFFFFF',
    bg_surface: '#F0FDFA',
    text_primary: '#042F2E',
    text_muted: '#5F8584',
    border: '#CCE3E1',
    accent_1: '#008EAA',
    accent_2: '#FAE600',
  },
  typography: { font_family: 'Noto Sans' },
  buttons: { radius: '10px' },
};

const FARB_PRAEFIXE = ['bg', 'text', 'border', 'divide', 'ring', 'from', 'via',
  'to', 'fill', 'stroke', 'placeholder', 'accent', 'outline', 'caret'];

const PALETTE = /^([a-z]+)-(\d{2,3})(?:\/(\d+))?$/;
const GRUNDWORT = /^(white|black)(?:\/(\d+))?$/;

/** Alle farbgebenden Klassen eines Markups — Größen und Breiten bleiben draußen. */
function farbklassen(html) {
  const gefunden = new Set();
  const treffer = html.matchAll(/class="([^"]*)"/g);
  for (const [, attribut] of treffer) {
    for (const roh of attribut.split(/\s+/)) {
      if (!roh) continue;
      const klasse = roh.split(':').pop().replace(/^!/, '');
      const strich = klasse.indexOf('-');
      if (strich < 0) continue;
      const praefix = klasse.slice(0, strich);
      const rest = klasse.slice(strich + 1);
      if (!FARB_PRAEFIXE.includes(praefix)) continue;
      if (PALETTE.test(rest) || GRUNDWORT.test(rest)) gefunden.add(klasse);
    }
  }
  return gefunden;
}

function bloecke() {
  if (!fs.existsSync(BIBLIOTHEK)) return [];
  return fs.readdirSync(BIBLIOTHEK)
    .filter((n) => n.endsWith('.html'))
    .map((n) => ({ name: n, html: fs.readFileSync(path.join(BIBLIOTHEK, n), 'utf8') }));
}

const SELEKTOR_ENDE = [',', ' ', '{', '\n', '.', ''];

function enthaeltSelektor(css, klasse) {
  const escaped = `.${klasse.replace('/', '\\/')}`;
  // Ein Selektor endet an Komma, Leerzeichen oder geschweifter Klammer — sonst
  // würde `.bg-gray-50` auch in `.bg-gray-500` gefunden. Geprüft werden alle
  // Fundstellen: `.ring-white` steht im CSS erst als `.ring-white\/5` und
  // später allein, und nur die zweite zählt.
  let index = css.indexOf(escaped);
  while (index >= 0) {
    const danach = css.slice(index + escaped.length, index + escaped.length + 1);
    if (SELEKTOR_ENDE.includes(danach)) return true;
    index = css.indexOf(escaped, index + 1);
  }
  return false;
}

describe('Marken-Override gegen die echte Bibliothek', () => {
  const css = buildOverrideCSS(STYLE_GUIDE);

  test('die Bibliothek ist nicht leer', () => {
    expect(bloecke().length).toBeGreaterThanOrEqual(20);
  });

  test('jede Farbklasse der Bibliothek wird abgedeckt', () => {
    const offen = new Map();
    bloecke().forEach(({ name, html }) => {
      farbklassen(html).forEach((klasse) => {
        if (!enthaeltSelektor(css, klasse)) {
          if (!offen.has(klasse)) offen.set(klasse, name);
        }
      });
    });

    expect(Array.from(offen.entries()).map(([k, b]) => `${k} (${b})`)).toEqual([]);
  });

  test('genau die Klassen, an denen die alte Fassung vorbeigelaufen ist', () => {
    // Aus der Messung vom 2026-08-13, absteigend nach Häufigkeit.
    ['text-slate-500', 'text-slate-600', 'text-slate-700', 'border-gray-700',
      'text-gray-300', 'bg-slate-50', 'border-slate-200', 'ring-gray-700/30',
      'bg-gray-600', 'from-gray-900/95', 'bg-white/10', 'text-white/80',
    ].forEach((klasse) => {
      expect(enthaeltSelektor(css, klasse)).toBe(true);
    });
  });
});

describe('Abbildung auf die Tokens', () => {
  const css = buildOverrideCSS(STYLE_GUIDE);

  test('helle Flächen werden zur Oberfläche des Style-Guides', () => {
    expect(css).toMatch(/\.bg-slate-50[^{]*\{ background-color: #F0FDFA/);
  });

  test('dunkle Flächen werden zur Primärfarbe', () => {
    expect(css).toMatch(/\.bg-slate-900[^{]*\{ background-color: #008EAA/);
  });

  test('kräftige Schrift wird zur Textfarbe', () => {
    expect(css).toMatch(/\.text-slate-900[^{]*\{ color: #042F2E/);
  });

  test('gedämpfte Schrift kennt beide Gründe', () => {
    // Auf hellem Grund die gedämpfte Textfarbe, auf dunklem die Variable —
    // ein und dieselbe Regel, entschieden über den Fallback.
    expect(css).toMatch(
      /\.text-slate-500[^{]*\{ color: var\(--kc-auf-dunkel-gedaempft, #5F8584\)/);
  });

  test('eine dunkle Fläche kehrt die Bedeutung um', () => {
    // Die dunklen Flächen setzen die Variablen, alles darin erbt sie. Der
    // Selektorblock ist lang — geprüft wird, dass die dunkle Fläche darin steht
    // und die Erklärung folgt, nicht ihr Abstand zueinander.
    const anfang = css.indexOf('.bg-gray-700');
    const block = css.slice(anfang, css.indexOf('}', anfang) + 1);
    expect(block).toContain('.bg-gray-900,');
    expect(block).toContain('.bg-black,');
    expect(block).toContain('--kc-auf-dunkel: #FFFFFF;');
    expect(css).toContain('--kc-auf-dunkel-gedaempft: color-mix(in srgb, #FFFFFF 70%, transparent)');
    expect(css).toContain('--kc-auf-dunkel-linie: color-mix(in srgb, #FFFFFF 20%, transparent)');
  });

  test('Deckkraft bleibt Deckkraft', () => {
    expect(css).toContain('color-mix(in srgb, #fff 80%, transparent)');
    expect(css).toMatch(/\.text-white\\\/80 \{ color: var\(--kc-auf-dunkel, color-mix/);
  });

  test('alle fünf Graustufen-Familien sind vertreten', () => {
    FAMILIEN.forEach((familie) => {
      expect(css).toContain(`.bg-${familie}-50`);
    });
  });

  test('ohne Style-Guide entsteht kein CSS', () => {
    expect(buildOverrideCSS(null)).toBe('');
  });

  test('bleibt klein genug fuer den Export', () => {
    expect(css.length).toBeLessThan(400_000);
  });
});

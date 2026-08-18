// Kontrastberechnung nach WCAG 2.1.
//
// Warum es das gibt: „zu kontrastarm" war bisher ein Eindruck, und Eindruecke
// widersprechen sich. Am 17.08.2026 stand auf der Arbeitsliste, die
// Abschnittsueberschriften des Dashboards seien beim Ueberfliegen unsichtbar.
// Gemessen hatten sie 8.89 — bestanden. Unsichtbar waren die
// *Beschriftungen unter den Zahlen* mit 2.26. Die Diagnose war falsch, weil
// niemand nachgerechnet hatte.
//
// Schwellen aus WCAG 2.1 AA:
//   4.5  normaler Text
//   3.0  grosse Schrift (ab 24px, oder ab 18.66px fett)

/** Normaler Text muss diesen Wert erreichen. */
export const AA_TEXT = 4.5;

/** Grosse Schrift darf hier bleiben. */
export const AA_GROSSE_SCHRIFT = 3.0;

/** '#RRGGBB', 'RRGGBB' oder die Kurzform '#RGB' → [r, g, b] */
export function alsRgb(farbe) {
  let roh = String(farbe).trim().replace('#', '');
  // Die Kurzform steht im Quelltext genauso oft wie die lange (`#ccc`), und
  // sie ist dieselbe Farbe — sie abzuweisen hiesse, sie nicht zu messen.
  if (/^[0-9a-fA-F]{3}$/.test(roh)) {
    roh = roh.split('').map(zeichen => zeichen + zeichen).join('');
  }
  if (!/^[0-9a-fA-F]{6}$/.test(roh)) {
    throw new Error(`Keine Hex-Farbe: ${farbe}`);
  }
  return [0, 2, 4].map(i => parseInt(roh.slice(i, i + 2), 16));
}

/** Relative Leuchtdichte nach WCAG. */
export function leuchtdichte(rgb) {
  const [r, g, b] = rgb.map(wert => {
    const anteil = wert / 255;
    return anteil <= 0.03928
      ? anteil / 12.92
      : Math.pow((anteil + 0.055) / 1.055, 2.4);
  });
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

/**
 * Kontrastverhaeltnis zweier Farben, 1 bis 21.
 * @param {string} vordergrund '#RRGGBB'
 * @param {string} hintergrund '#RRGGBB'
 * @returns {number} auf zwei Stellen gerundet
 */
export function kontrast(vordergrund, hintergrund) {
  const a = leuchtdichte(alsRgb(vordergrund));
  const b = leuchtdichte(alsRgb(hintergrund));
  const [hell, dunkel] = a > b ? [a, b] : [b, a];
  return Math.round(((hell + 0.05) / (dunkel + 0.05)) * 100) / 100;
}

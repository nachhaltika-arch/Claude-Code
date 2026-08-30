/**
 * Farbwerte und die Tonleiter der Style-Guide-Ansicht (L-25).
 *
 * Am 2026-08-30 aus `StyleGuideView.jsx` herausgeloest. Ansicht und Bausteine
 * brauchen beide `KC_DARK`; `colorScale` nur die Bausteine, steht aber
 * daneben, weil es dieselbe Sache beschreibt.
 */

export function colorScale(hex) {
  const { h, s, l } = hexToHsl(hex);
  return [
    hslToHex(h, s, Math.min(96, l + 32)),
    hslToHex(h, s, Math.min(85, l + 16)),
    hex,
    hslToHex(h, s, Math.max(18, l - 16)),
    hslToHex(h, s, Math.max(8, l - 32)),
  ];
}

export function hexToHsl(hex) {
  const m = hex.replace('#', '');
  if (m.length !== 6) return { h: 0, s: 0, l: 50 };
  const r = parseInt(m.slice(0, 2), 16) / 255;
  const g = parseInt(m.slice(2, 4), 16) / 255;
  const b = parseInt(m.slice(4, 6), 16) / 255;
  const max = Math.max(r, g, b);
  const min = Math.min(r, g, b);
  const l = (max + min) / 2;
  let h = 0;
  let s = 0;
  if (max !== min) {
    const d = max - min;
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
    switch (max) {
      case r: h = (g - b) / d + (g < b ? 6 : 0); break;
      case g: h = (b - r) / d + 2; break;
      default: h = (r - g) / d + 4;
    }
    h /= 6;
  }
  return { h: h * 360, s: s * 100, l: l * 100 };
}
export function hslToHex(h, s, l) {
  const a = (s * Math.min(l, 100 - l)) / 100 / 100;
  const f = (n) => {
    const k = (n + h / 30) % 12;
    const c = l / 100 - a * Math.max(Math.min(k - 3, 9 - k, 1), -1);
    return Math.round(255 * c).toString(16).padStart(2, '0');
  };
  return `#${f(0)}${f(8)}${f(4)}`;
}

export const KC_DARK = 'var(--kc-dark)';

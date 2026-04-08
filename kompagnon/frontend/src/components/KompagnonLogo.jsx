/**
 * KompagnonLogo — verwendet die offiziellen Marken-SVGs aus /public/
 *
 * variant:
 *   'color'  → logo-group.svg (Bildmarke + Wortmarke + "communications"), Farbe
 *   'white'  → gleiche Datei, CSS-Filter invertiert für dunkle Hintergründe
 *   'icon'   → nur Bildmarke (icon.png, kein SVG verfügbar)
 *   'word'   → nur Wortmarke ohne "communications" (logo.svg)
 */
export default function KompagnonLogo({ variant = 'color', height = 40 }) {
  const isWhite = variant === 'white';
  const isIcon  = variant === 'icon';
  const isWord  = variant === 'word';

  const filter = isWhite
    ? 'brightness(0) invert(1)'
    : undefined;

  if (isIcon) {
    return (
      <img
        src="/icon.png"
        alt="KOMPAGNON"
        style={{ height, width: 'auto', display: 'block', filter }}
      />
    );
  }

  if (isWord) {
    return (
      <img
        src="/logo.svg"
        alt="KOMPAGNON"
        style={{ height, width: 'auto', display: 'block', filter }}
      />
    );
  }

  // default: color or white — logo-group (Bildmarke + Wortmarke + communications)
  return (
    <img
      src="/logo-group.svg"
      alt="KOMPAGNON communications"
      style={{ height, width: 'auto', display: 'block', filter }}
    />
  );
}

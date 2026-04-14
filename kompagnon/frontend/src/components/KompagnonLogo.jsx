/**
 * KompagnonLogo — offizielle Marken-SVGs aus /public/
 *
 * variant:
 *   'color'  → logo-group.svg  (Bildmarke + Wortmarke + "communications")
 *   'white'  → logo-group.svg  CSS-invertiert fuer dunkle Hintergruende
 *   'icon'   → icon.svg        nur Bildmarke
 *   'word'   → logo.svg        nur Wortmarke ohne "communications"
 */
export default function KompagnonLogo({ variant = 'color', height = 40, style = {} }) {
  const isWhite = variant === 'white';
  const isIcon  = variant === 'icon';
  const isWord  = variant === 'word';

  const filter = isWhite ? 'brightness(0) invert(1)' : undefined;

  const src = isIcon
    ? '/icon.svg'
    : isWord
      ? '/logo.svg'
      : '/logo-group.svg';

  const alt = isIcon
    ? 'KOMPAGNON'
    : isWord
      ? 'KOMPAGNON'
      : 'KOMPAGNON communications';

  return (
    <img
      src={src}
      alt={alt}
      style={{
        height,
        width: 'auto',
        display: 'block',
        filter,
        ...style,
      }}
    />
  );
}

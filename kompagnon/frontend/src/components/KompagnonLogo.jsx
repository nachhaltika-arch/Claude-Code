export default function KompagnonLogo({ variant = 'color', height = 40, style = {} }) {
  const filter = variant === 'white' ? 'brightness(0) invert(1)' : undefined;

  const src = variant === 'icon' ? '/icon.svg'
    : variant === 'word'         ? '/logo.svg'
    : '/logo-group.svg';

  const alt = variant === 'icon' || variant === 'word'
    ? 'KOMPAGNON'
    : 'KOMPAGNON communications';

  return (
    <img
      src={src}
      alt={alt}
      style={{ height, width: 'auto', display: 'block', filter, ...style }}
    />
  );
}

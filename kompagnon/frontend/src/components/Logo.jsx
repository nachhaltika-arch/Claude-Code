/**
 * Logo — kompakter Einsatz der offiziellen Wortmarke (logo.svg)
 * Für Seiten ohne Sidebar (Login, Portal, Checkout…)
 */
export default function Logo({ size = 'default', variant = 'color' }) {
  const height = size === 'small' ? 24 : size === 'large' ? 48 : 36;
  const filter = variant === 'white' ? 'brightness(0) invert(1)' : undefined;

  return (
    <img
      src="/logo-group.svg"
      alt="KOMPAGNON"
      style={{ height, width: 'auto', display: 'block', filter }}
    />
  );
}

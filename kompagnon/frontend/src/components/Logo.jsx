/**
 * Logo — Wrapper fuer KompagnonLogo (Abwaertskompatibilitaet)
 *
 * Fuer neue Komponenten: direkt `KompagnonLogo` verwenden.
 * Dieser Wrapper bleibt bestehen, damit Seiten wie Login, CustomerPortal,
 * Checkout und die Paket-Seiten nicht einzeln migriert werden muessen.
 */
import KompagnonLogo from './KompagnonLogo';

export default function Logo({ size = 'default', variant = 'color' }) {
  const height = size === 'small' ? 24 : size === 'large' ? 48 : 36;
  return <KompagnonLogo variant={variant} height={height} />;
}

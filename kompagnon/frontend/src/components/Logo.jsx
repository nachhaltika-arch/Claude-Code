import KompagnonLogo from './KompagnonLogo';

export default function Logo({ size = 'default', variant = 'color' }) {
  const height = size === 'small' ? 24 : size === 'large' ? 48 : 36;
  return <KompagnonLogo variant={variant} height={height} />;
}

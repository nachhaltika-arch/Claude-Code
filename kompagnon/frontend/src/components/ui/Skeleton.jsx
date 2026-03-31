export default function Skeleton({ width = '100%', height = 16, radius = 6 }) {
  return (
    <div style={{
      width, height, borderRadius: radius,
      background: 'var(--border-light)',
      animation: 'pulse 1.5s ease infinite',
    }} />
  );
}

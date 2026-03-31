const PADDINGS = { sm: 12, md: 16, lg: 20 };

export default function Card({ padding = 'md', children, style }) {
  return (
    <div style={{
      background: 'var(--bg-surface)',
      border: '1px solid var(--border-light)',
      borderRadius: 'var(--radius-lg)',
      boxShadow: 'var(--shadow-card)',
      padding: PADDINGS[padding] || 16,
      ...style,
    }}>
      {children}
    </div>
  );
}

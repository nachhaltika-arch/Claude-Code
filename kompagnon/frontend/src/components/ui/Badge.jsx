const VARIANTS = {
  success: { background: 'var(--status-success-bg)', color: 'var(--status-success-text)' },
  warning: { background: 'var(--status-warning-bg)', color: 'var(--status-warning-text)' },
  danger:  { background: 'var(--status-danger-bg)',  color: 'var(--status-danger-text)' },
  info:    { background: 'var(--status-info-bg)',    color: 'var(--status-info-text)' },
  neutral: { background: 'var(--status-neutral-bg)', color: 'var(--status-neutral-text)' },
};

export default function Badge({ variant = 'neutral', children, style }) {
  const v = VARIANTS[variant] || VARIANTS.neutral;
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center',
      padding: '1px 8px', borderRadius: 10,
      fontSize: 11, fontWeight: 600, lineHeight: '18px',
      whiteSpace: 'nowrap',
      ...v, ...style,
    }}>
      {children}
    </span>
  );
}

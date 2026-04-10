export default function EmptyState({ icon, title, description, action, secondaryAction, compact }) {
  return (
    <div style={{
      display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center',
      textAlign: 'center',
      padding: compact ? '32px 20px' : '56px 24px',
      gap: compact ? 10 : 16,
    }}>
      {icon && (
        <div style={{ fontSize: compact ? 36 : 52, lineHeight: 1, opacity: 0.3, userSelect: 'none' }}>
          {icon}
        </div>
      )}
      <div style={{ fontSize: compact ? 14 : 16, fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1.3, maxWidth: 320 }}>
        {title}
      </div>
      {description && (
        <div style={{ fontSize: compact ? 12 : 13, color: 'var(--text-secondary)', lineHeight: 1.65, maxWidth: 380 }}>
          {description}
        </div>
      )}
      {action && (
        <button
          onClick={action.onClick}
          className="kc-btn-primary"
          style={{
            marginTop: compact ? 4 : 8,
            padding: compact ? '8px 18px' : '10px 24px',
            background: 'var(--brand-primary)', color: 'var(--text-inverse)',
            border: 'none', borderRadius: 'var(--radius-md)',
            fontSize: compact ? 12 : 13, fontWeight: 700,
            cursor: 'pointer', fontFamily: 'var(--font-sans)',
          }}
        >
          {action.label}
        </button>
      )}
      {secondaryAction && (
        <button
          onClick={secondaryAction.onClick}
          style={{
            background: 'none', border: 'none', padding: 0,
            fontSize: 12, color: 'var(--text-tertiary)',
            cursor: 'pointer', textDecoration: 'underline',
            fontFamily: 'var(--font-sans)',
          }}
        >
          {secondaryAction.label}
        </button>
      )}
    </div>
  );
}

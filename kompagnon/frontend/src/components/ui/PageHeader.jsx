export default function PageHeader({ title, subtitle, action }) {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      marginBottom: 20, paddingBottom: 16,
      borderBottom: '1px solid var(--border-light)',
    }}>
      <div>
        <h1 style={{
          fontSize: 18, fontWeight: 600, color: 'var(--text-primary)',
          fontFamily: 'var(--font-sans)', margin: 0,
        }}>{title}</h1>
        {subtitle && (
          <p style={{ fontSize: 12, color: 'var(--text-tertiary)', marginTop: 2 }}>{subtitle}</p>
        )}
      </div>
      {action && <div>{action}</div>}
    </div>
  );
}

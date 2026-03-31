const VARIANTS = {
  primary: {
    background: 'var(--brand-primary)',
    color: 'var(--text-inverse)',
    border: 'none',
    hoverBg: 'var(--brand-primary-dark)',
  },
  secondary: {
    background: 'var(--bg-surface)',
    color: 'var(--text-primary)',
    border: '1px solid var(--border-medium)',
    hoverBg: 'var(--bg-hover)',
  },
  ghost: {
    background: 'transparent',
    color: 'var(--text-secondary)',
    border: 'none',
    hoverBg: 'var(--bg-hover)',
  },
};

const SIZES = {
  sm: { padding: '5px 12px', fontSize: 12 },
  md: { padding: '7px 16px', fontSize: 13 },
};

export default function Button({ variant = 'primary', size = 'md', onClick, children, style, ...props }) {
  const v = VARIANTS[variant] || VARIANTS.primary;
  const s = SIZES[size] || SIZES.md;
  return (
    <button
      onClick={onClick}
      style={{
        display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: 6,
        background: v.background, color: v.color, border: v.border,
        borderRadius: 'var(--radius-md)', fontWeight: 500,
        cursor: 'pointer', fontFamily: 'var(--font-sans)',
        transition: 'background 0.15s, opacity 0.15s',
        minHeight: size === 'sm' ? 32 : 36,
        ...s, ...style,
      }}
      onMouseEnter={e => e.currentTarget.style.background = v.hoverBg}
      onMouseLeave={e => e.currentTarget.style.background = v.background}
      {...props}
    >
      {children}
    </button>
  );
}

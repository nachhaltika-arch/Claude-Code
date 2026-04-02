import React from 'react';

// ── Shimmer style ──────────────────────────────────────────────
const shimmerStyle = {
  background: 'linear-gradient(90deg, var(--bg-elevated) 25%, var(--bg-hover) 50%, var(--bg-elevated) 75%)',
  backgroundSize: '200% 100%',
  animation: 'skeleton-shimmer 1.5s infinite',
  borderRadius: 'var(--radius-md)',
};

// ── SkeletonText ───────────────────────────────────────────────
export function SkeletonText({ width = '100%', height = 14, style = {} }) {
  return (
    <div style={{ ...shimmerStyle, width, height, borderRadius: 'var(--radius-sm)', ...style }} />
  );
}

// ── SkeletonCard ───────────────────────────────────────────────
export function SkeletonCard({ style = {} }) {
  return (
    <div style={{
      background: 'var(--bg-surface)',
      borderRadius: 'var(--radius-xl)',
      border: '0.5px solid var(--border-light)',
      padding: 'var(--space-5)',
      boxShadow: 'var(--shadow-sm)',
      display: 'flex', flexDirection: 'column', gap: 12,
      ...style,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <div style={{ ...shimmerStyle, width: 40, height: 40, borderRadius: 'var(--radius-lg)', flexShrink: 0 }} />
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 6 }}>
          <SkeletonText width="60%" height={14} />
          <SkeletonText width="40%" height={11} />
        </div>
      </div>
      <SkeletonText width="100%" height={12} />
      <SkeletonText width="80%" height={12} />
      <SkeletonText width="90%" height={12} />
    </div>
  );
}

// ── SkeletonTable ──────────────────────────────────────────────
export function SkeletonTable({ rows = 5, cols = 4, style = {} }) {
  const widths = ['40%', '25%', '20%', '15%', '30%', '50%'];
  return (
    <div style={{
      background: 'var(--bg-surface)',
      borderRadius: 'var(--radius-xl)',
      border: '0.5px solid var(--border-light)',
      overflow: 'hidden',
      ...style,
    }}>
      {/* Header */}
      <div style={{
        display: 'flex', gap: 16, padding: '12px 16px',
        borderBottom: '1px solid var(--border-light)',
        background: 'var(--bg-app)',
      }}>
        {Array.from({ length: cols }).map((_, i) => (
          <div key={i} style={{ flex: i === 0 ? 2 : 1 }}>
            <SkeletonText width="60%" height={11} />
          </div>
        ))}
      </div>
      {/* Rows */}
      {Array.from({ length: rows }).map((_, rowIdx) => (
        <div key={rowIdx} style={{
          display: 'flex', gap: 16, padding: '12px 16px',
          borderBottom: rowIdx < rows - 1 ? '1px solid var(--border-light)' : 'none',
          alignItems: 'center',
        }}>
          {Array.from({ length: cols }).map((_, colIdx) => (
            <div key={colIdx} style={{ flex: colIdx === 0 ? 2 : 1 }}>
              <SkeletonText width={widths[(rowIdx + colIdx) % widths.length]} height={13} />
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}

// ── Spinner ────────────────────────────────────────────────────
export function Spinner({ size = 14, color = 'currentColor' }) {
  return (
    <svg
      width={size} height={size}
      viewBox="0 0 14 14" fill="none"
      style={{ animation: 'spin 0.7s linear infinite', flexShrink: 0 }}
      aria-hidden="true"
    >
      <circle cx="7" cy="7" r="5.5" stroke={color} strokeOpacity="0.25" strokeWidth="2" />
      <path d="M7 1.5A5.5 5.5 0 0 1 12.5 7" stroke={color} strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

// ── Default export (backward compat) ──────────────────────────
export default function Skeleton({ width = '100%', height = 16, radius, style = {} }) {
  return (
    <div style={{
      ...shimmerStyle,
      width, height,
      borderRadius: radius ?? 'var(--radius-md)',
      ...style,
    }} />
  );
}

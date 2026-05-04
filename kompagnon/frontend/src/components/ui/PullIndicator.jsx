export default function PullIndicator() {
  return (
    <div
      data-ptr-indicator
      data-refreshing="0"
      style={{
        position: 'absolute', top: -52, left: '50%',
        transform: 'translateX(-50%) translateY(0px)',
        opacity: 0, display: 'flex', alignItems: 'center', justifyContent: 'center',
        width: 40, height: 40, borderRadius: '50%',
        background: 'var(--bg-surface)', boxShadow: 'var(--shadow-md)',
        border: '1px solid var(--border-light)',
        zIndex: 10, transition: 'opacity 0.1s', pointerEvents: 'none',
      }}
    >
      <div
        data-ptr-spinner
        style={{
          width: 20, height: 20,
          border: '2.5px solid var(--border-light)',
          borderTopColor: 'var(--brand-primary)',
          borderRadius: '50%', transition: 'transform 0.05s linear',
        }}
      />
    </div>
  );
}

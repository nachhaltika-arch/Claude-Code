import { useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { useScreenSize } from '../../utils/responsive';

export default function ModalSheet({
  open, onClose, title, subtitle, children,
  maxWidth = 520, maxHeight, footer, headerColor, noPadding,
}) {
  const { isMobile } = useScreenSize();
  const startY = useRef(null);
  const [dragOffset, setDragOffset] = useState(0);
  const [closing, setClosing] = useState(false);

  useEffect(() => {
    if (!open) return;
    const handler = (e) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [open, onClose]);

  useEffect(() => {
    if (open) document.body.style.overflow = 'hidden';
    else document.body.style.overflow = '';
    return () => { document.body.style.overflow = ''; };
  }, [open]);

  const onTouchStart = (e) => { startY.current = e.touches[0].clientY; };
  const onTouchMove = (e) => {
    if (startY.current === null) return;
    const dy = e.touches[0].clientY - startY.current;
    if (dy > 0) setDragOffset(dy);
  };
  const onTouchEnd = () => {
    if (dragOffset > 80) {
      setClosing(true);
      setTimeout(() => { setClosing(false); setDragOffset(0); onClose(); }, 200);
    } else { setDragOffset(0); }
    startY.current = null;
  };

  if (!open) return null;

  const mobileStyle = {
    position: 'fixed', bottom: 0, left: 0, right: 0,
    background: headerColor ? undefined : 'var(--bg-surface)',
    borderRadius: '20px 20px 0 0',
    boxShadow: '0 -8px 40px rgba(0,0,0,0.18)',
    maxHeight: maxHeight || '92vh',
    display: 'flex', flexDirection: 'column', zIndex: 1001,
    transform: closing ? 'translateY(100%)' : `translateY(${dragOffset}px)`,
    transition: dragOffset === 0 ? 'transform 0.25s cubic-bezier(0.34,1.56,0.64,1)' : 'none',
    animation: !closing ? 'bwSlideUp 0.25s cubic-bezier(0.34,1.56,0.64,1)' : undefined,
    willChange: 'transform',
  };

  const desktopStyle = {
    position: 'fixed', top: '50%', left: '50%',
    transform: 'translate(-50%,-50%)',
    background: 'var(--bg-surface)',
    borderRadius: 'var(--radius-xl, 16px)',
    boxShadow: '0 24px 80px rgba(0,0,0,0.25)',
    width: '100%', maxWidth, maxHeight: maxHeight || '90vh',
    display: 'flex', flexDirection: 'column', zIndex: 1001,
    animation: 'bwSlideUp 0.2s cubic-bezier(0.34,1.56,0.64,1)',
  };

  return createPortal(
    <>
      <div onClick={onClose} style={{
        position: 'fixed', inset: 0, zIndex: 1000,
        background: 'rgba(15,28,32,0.55)',
        backdropFilter: 'blur(3px)', WebkitBackdropFilter: 'blur(3px)',
        animation: 'bwFadeIn 0.15s ease',
      }} />
      <div style={isMobile ? mobileStyle : desktopStyle} onClick={e => e.stopPropagation()}>
        {isMobile && (
          <div onTouchStart={onTouchStart} onTouchMove={onTouchMove} onTouchEnd={onTouchEnd}
            style={{ display: 'flex', justifyContent: 'center', padding: '12px 0 4px', cursor: 'grab', flexShrink: 0,
              background: headerColor || 'var(--bg-surface)', borderRadius: '20px 20px 0 0' }}>
            <div style={{ width: 36, height: 4, background: headerColor ? 'rgba(255,255,255,0.4)' : 'var(--border-medium)', borderRadius: 2 }} />
          </div>
        )}
        {(title || subtitle) && (
          <div style={{
            padding: isMobile ? '12px 20px 14px' : '18px 24px',
            borderBottom: '1px solid var(--border-light)',
            display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12,
            flexShrink: 0, background: headerColor,
            borderRadius: headerColor ? (isMobile ? '0' : 'var(--radius-xl, 16px) var(--radius-xl, 16px) 0 0') : undefined,
          }}>
            <div>
              {subtitle && <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: 3, color: headerColor ? 'rgba(255,255,255,0.7)' : 'var(--text-tertiary)' }}>{subtitle}</div>}
              {title && <div style={{ fontSize: isMobile ? 16 : 17, fontWeight: 700, color: headerColor ? '#fff' : 'var(--text-primary)' }}>{title}</div>}
            </div>
            <button onClick={onClose} aria-label="Schließen" style={{
              background: headerColor ? 'rgba(255,255,255,0.15)' : 'var(--bg-app)',
              border: 'none', borderRadius: 'var(--radius-sm)', width: 30, height: 30,
              cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center',
              color: headerColor ? '#fff' : 'var(--text-tertiary)', fontSize: 16, flexShrink: 0,
            }}>✕</button>
          </div>
        )}
        <div style={{ flex: 1, overflowY: 'auto', padding: noPadding ? 0 : (isMobile ? '16px 20px' : '20px 24px'), WebkitOverflowScrolling: 'touch' }}>
          {children}
        </div>
        {footer && (
          <div style={{
            padding: isMobile ? '12px 20px' : '14px 24px',
            borderTop: '1px solid var(--border-light)', flexShrink: 0,
            background: 'var(--bg-elevated)',
            paddingBottom: isMobile ? 'max(12px, env(safe-area-inset-bottom))' : '14px',
          }}>{footer}</div>
        )}
      </div>
    </>,
    document.body
  );
}

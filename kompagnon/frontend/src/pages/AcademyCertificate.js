import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import API_BASE_URL from '../config';

// ── Design tokens (CSS variables — auto-adapt to dark mode) ────
const T = {
  primary:    'var(--brand-primary)',
  primaryBg:  'var(--brand-primary-light)',
  border:     'var(--border-light)',
  borderMed:  'var(--border-medium)',
  text:       'var(--text-primary)',
  textSub:    'var(--text-secondary)',
  textMuted:  'var(--text-tertiary)',
  appBg:      'var(--bg-app)',
  font:       "'DM Sans', system-ui, sans-serif",
};

export default function AcademyCertificate() {
  const { code } = useParams();
  const [data,    setData]    = useState(null);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState(null);

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/academy/certificates/${code}/verify`)
      .then(r => {
        if (!r.ok) throw new Error('Zertifikat nicht gefunden');
        return r.json();
      })
      .then(setData)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, [code]);

  if (loading) return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh', background: T.appBg }}>
      <div style={{ width: 32, height: 32, borderRadius: '50%', border: `3px solid ${T.primaryBg}`, borderTopColor: T.primary, animation: 'spin 0.8s linear infinite' }} />
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );

  if (error) return (
    <div style={{
      display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center',
      minHeight: '100vh', background: T.appBg, gap: 12, fontFamily: T.font,
    }}>
      <div style={{ fontSize: 52, opacity: 0.4 }}>🔍</div>
      <div style={{ fontSize: 20, fontWeight: 700, color: '#b02020' }}>Zertifikat nicht gefunden</div>
      <div style={{ fontSize: 14, color: T.textSub, textAlign: 'center', maxWidth: 360 }}>
        Der Code <strong style={{ fontFamily: 'monospace', letterSpacing: '0.08em' }}>{code}</strong> ist ungültig oder wurde widerrufen.
      </div>
    </div>
  );

  const issuedFormatted = data.issued_at
    ? new Date(data.issued_at).toLocaleDateString('de-DE', { day: '2-digit', month: 'long', year: 'numeric' })
    : '—';

  return (
    <div style={{
      minHeight: '100vh',
      background: T.appBg,
      display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center',
      padding: '40px 16px',
      fontFamily: T.font,
    }}>
      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
        @media print {
          body { margin: 0; background: white !important; }
          .cert-no-print { display: none !important; }
          .cert-card { box-shadow: none !important; border: 2px solid ${T.borderMed} !important; }
        }
      `}</style>

      {/* ── Certificate card (A4-like) ── */}
      <div
        className="cert-card"
        style={{
          background: 'var(--bg-surface)',
          maxWidth: 680, width: '100%',
          border: `2px solid ${T.borderMed}`,
          borderRadius: '16px',
          boxShadow: '0 8px 40px rgba(0,142,170,0.10)',
          overflow: 'hidden',
        }}
      >
        {/* Inner content */}
        <div style={{ padding: '48px 56px 44px' }}>

          {/* ── Logo (centered) ── */}
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', marginBottom: 32 }}>
            <div style={{
              width: 52, height: 52, borderRadius: '14px',
              background: T.primary,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              marginBottom: 10,
            }}>
              <span style={{ color: '#fff', fontWeight: 900, fontSize: 22, letterSpacing: '-0.02em' }}>K</span>
            </div>
            <div style={{ fontSize: 15, fontWeight: 700, color: T.text, letterSpacing: '0.06em' }}>KOMPAGNON</div>
            <div style={{ fontSize: 11, color: T.textMuted, letterSpacing: '0.12em', textTransform: 'uppercase', marginTop: 2 }}>
              Akademy
            </div>
          </div>

          {/* ── Divider ── */}
          <div style={{ height: 1, background: T.border, marginBottom: 36 }} />

          {/* ── Certificate heading ── */}
          <div style={{ textAlign: 'center', marginBottom: 28 }}>
            <div style={{
              fontSize: 28, fontWeight: 700, color: T.primary,
              letterSpacing: '-0.01em', lineHeight: 1.2, marginBottom: 6,
            }}>
              Zertifikat der Teilnahme
            </div>
            <div style={{ fontSize: 14, color: T.textMuted }}>
              Hiermit wird bestätigt, dass
            </div>
          </div>

          {/* ── Recipient name ── */}
          <div style={{ textAlign: 'center', marginBottom: 8 }}>
            <div style={{
              fontSize: 24, fontWeight: 700, color: T.text,
              letterSpacing: '-0.01em', lineHeight: 1.2,
            }}>
              {data.user_name}
            </div>
          </div>

          {/* ── Course context ── */}
          <div style={{ textAlign: 'center', marginBottom: 32 }}>
            <div style={{ fontSize: 14, color: T.textMuted, marginBottom: 8 }}>
              den folgenden Kurs erfolgreich abgeschlossen hat:
            </div>
            <div style={{
              display: 'inline-block',
              background: T.primaryBg, color: T.primary,
              borderRadius: '9999px', padding: '8px 22px',
              fontSize: 18, fontWeight: 600,
            }}>
              {data.course_title}
            </div>
          </div>

          {/* ── Divider ── */}
          <div style={{ height: 1, background: T.border, marginBottom: 24 }} />

          {/* ── Date + code ── */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
            <div>
              <div style={{ fontSize: 10, color: T.textMuted, textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 3 }}>
                Ausstellungsdatum
              </div>
              <div style={{ fontSize: 12, color: T.textMuted, fontWeight: 500 }}>{issuedFormatted}</div>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#1a7a3a' }} />
              <span style={{ fontSize: 12, color: '#1a7a3a', fontWeight: 600 }}>Verifiziert</span>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: 10, color: T.textMuted, textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 3 }}>
                Zertifikat-Code
              </div>
              <div style={{ fontSize: 12, color: T.textMuted, fontFamily: 'monospace', letterSpacing: '0.1em' }}>
                {data.certificate_code}
              </div>
            </div>
          </div>
        </div>

        {/* ── Footer strip ── */}
        <div style={{
          background: T.appBg, borderTop: `1px solid ${T.border}`,
          padding: '12px 56px',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8,
        }}>
          <div style={{ fontSize: 11, color: T.textMuted }}>
            kompagnon.app/academy/certificate/{data.certificate_code}
          </div>
          <div style={{ fontSize: 11, color: T.textMuted }}>
            KOMPAGNON Akademy © {new Date().getFullYear()}
          </div>
        </div>
      </div>

      {/* ── Print / PDF button ── */}
      <button
        className="cert-no-print"
        onClick={() => window.print()}
        style={{
          marginTop: 28, padding: '11px 28px',
          background: T.primary, color: '#fff',
          border: 'none', borderRadius: '8px',
          fontSize: 13, fontWeight: 600,
          cursor: 'pointer', fontFamily: T.font,
          boxShadow: '0 2px 8px rgba(0,142,170,0.25)',
          transition: 'opacity 0.15s',
        }}
        onMouseEnter={e => e.currentTarget.style.opacity = '0.85'}
        onMouseLeave={e => e.currentTarget.style.opacity = '1'}
      >
        🖨️ Als PDF speichern
      </button>
    </div>
  );
}

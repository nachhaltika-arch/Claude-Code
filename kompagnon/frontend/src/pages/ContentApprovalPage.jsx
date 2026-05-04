import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import API_BASE_URL from '../config';

export default function ContentApprovalPage() {
  const { token } = useParams();
  const [info, setInfo]         = useState(null);
  const [loading, setLoading]   = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone]         = useState(false);
  const [error, setError]       = useState('');

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/projects/approve-content/${token}`)
      .then(r => r.ok ? r.json() : Promise.reject(r.status))
      .then(d => {
        setInfo(d);
        if (d.already_approved) setDone(true);
      })
      .catch(() => setError('Dieser Freigabe-Link ist ungültig oder bereits abgelaufen.'))
      .finally(() => setLoading(false));
  }, [token]);

  const handleApprove = async () => {
    setSubmitting(true);
    setError('');
    try {
      const r = await fetch(`${API_BASE_URL}/api/projects/approve-content/${token}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      if (r.ok) {
        setDone(true);
      } else {
        const d = await r.json().catch(() => ({}));
        setError(d.detail?.message || d.detail || 'Freigabe konnte nicht gespeichert werden.');
      }
    } catch {
      setError('Verbindungsfehler. Bitte erneut versuchen.');
    }
    setSubmitting(false);
  };

  const wrap = {
    minHeight: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: '#f4f6f8',
    padding: 20,
    fontFamily: "-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif",
  };
  const card = {
    background: '#fff',
    borderRadius: 12,
    border: '1px solid #e5e7eb',
    maxWidth: 520,
    width: '100%',
    overflow: 'hidden',
  };

  if (loading) {
    return (
      <div style={wrap}>
        <div style={{ color: '#94a3b8', fontSize: 14 }}>Laden…</div>
      </div>
    );
  }

  if (error && !info) {
    return (
      <div style={wrap}>
        <div style={card}>
          <div style={{ background: '#008EAA', padding: '24px 32px' }}>
            <div style={{ color: 'white', fontSize: 20, fontWeight: 700 }}>KOMPAGNON</div>
          </div>
          <div style={{ padding: 32, textAlign: 'center' }}>
            <div style={{ fontSize: 32, marginBottom: 16 }}>⚠️</div>
            <div style={{ fontSize: 16, fontWeight: 600, color: '#1a1a1a', marginBottom: 8 }}>
              Link ungültig
            </div>
            <div style={{ fontSize: 14, color: '#64748b' }}>{error}</div>
          </div>
        </div>
      </div>
    );
  }

  const company = info?.company_name || 'Ihr Projekt';

  return (
    <div style={wrap}>
      <div style={card}>
        {/* Header */}
        <div style={{ background: '#008EAA', padding: '24px 32px' }}>
          <div style={{ color: 'white', fontSize: 20, fontWeight: 700 }}>KOMPAGNON</div>
          <div style={{ color: 'rgba(255,255,255,.8)', fontSize: 14, marginTop: 4 }}>
            Briefing-Freigabe
          </div>
        </div>

        <div style={{ padding: 32 }}>
          {done ? (
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 48, marginBottom: 16 }}>✅</div>
              <div style={{ fontSize: 20, fontWeight: 700, color: '#059669', marginBottom: 8 }}>
                Freigabe erteilt!
              </div>
              <p style={{ fontSize: 14, color: '#64748b', margin: 0 }}>
                Vielen Dank. Ihr Briefing für <strong>{company}</strong> wurde erfolgreich
                freigegeben. Wir machen jetzt mit der Erstellung Ihrer Website weiter.
              </p>
            </div>
          ) : (
            <>
              <h2 style={{ fontSize: 18, fontWeight: 700, color: '#1a1a1a', marginTop: 0, marginBottom: 8 }}>
                Briefing freigeben
              </h2>
              <p style={{ fontSize: 14, color: '#64748b', marginTop: 0 }}>
                Wir haben das Briefing für Ihr Projekt <strong>{company}</strong> fertiggestellt.
                Bitte bestätigen Sie, dass Sie mit dem Inhalt einverstanden sind und
                wir mit der nächsten Phase beginnen dürfen.
              </p>

              {error && (
                <div style={{ background: '#fef2f2', border: '1px solid #fca5a5', borderRadius: 8, padding: '10px 14px', marginBottom: 16, fontSize: 13, color: '#dc2626' }}>
                  {error}
                </div>
              )}

              <button
                onClick={handleApprove}
                disabled={submitting}
                style={{
                  width: '100%',
                  padding: '14px 0',
                  background: submitting ? '#94a3b8' : '#008EAA',
                  color: 'white',
                  border: 'none',
                  borderRadius: 8,
                  fontSize: 16,
                  fontWeight: 700,
                  cursor: submitting ? 'not-allowed' : 'pointer',
                  fontFamily: 'inherit',
                  marginTop: 8,
                }}
              >
                {submitting ? 'Wird gespeichert…' : 'Briefing jetzt freigeben ✓'}
              </button>

              <p style={{ fontSize: 12, color: '#94a3b8', textAlign: 'center', marginTop: 16, marginBottom: 0 }}>
                Mit einem Klick bestätigen Sie die Freigabe verbindlich.
              </p>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

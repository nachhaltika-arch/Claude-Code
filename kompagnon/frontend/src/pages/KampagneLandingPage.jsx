import { useState } from 'react';
import { useParams } from 'react-router-dom';
import API_BASE_URL from '../config';

const PRIMARY = '#008eaa';

const FREEMAILS = [
  'gmail.com', 'googlemail.com', 'gmx.de', 'gmx.net',
  'web.de', 'yahoo.de', 'yahoo.com', 'hotmail.com', 'outlook.com',
  'icloud.com', 't-online.de', 'freenet.de', 'posteo.de', 'protonmail.com',
];

export default function KampagneLandingPage() {
  const { slug } = useParams();

  const [email, setEmail]   = useState('');
  const [domain, setDomain] = useState('');
  const [mobil, setMobil]   = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError]     = useState('');

  const handleEmailChange = (val) => {
    setEmail(val);
    const atIdx = val.indexOf('@');
    if (atIdx !== -1) {
      const host = val.slice(atIdx + 1).toLowerCase().trim();
      if (host && !FREEMAILS.includes(host)) {
        setDomain('https://' + host);
      } else {
        setDomain('');
      }
    } else {
      setDomain('');
    }
  };

  const handleSubmit = async () => {
    setError('');
    if (!email.trim() || !domain.trim() || !mobil.trim()) {
      setError('Bitte alle Felder ausfüllen.');
      return;
    }
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/kampagne/audit-anfrage`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          domain: domain.trim(),
          email: email.trim(),
          mobil: mobil.trim(),
          kampagne_quelle: slug || 'postkarte',
        }),
      });
      const data = await res.json();
      if (data.success) {
        setSuccess(true);
      } else {
        setError(data.error || 'Ein Fehler ist aufgetreten. Bitte versuchen Sie es erneut.');
      }
    } catch {
      setError('Verbindungsfehler. Bitte versuchen Sie es später erneut.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', background: '#f8fafc', display: 'flex', flexDirection: 'column' }}>

      {/* Header */}
      <div style={{ background: PRIMARY, padding: '16px 24px' }}>
        <span style={{
          color: '#fff', fontWeight: 800, fontSize: 22,
          letterSpacing: '-0.5px', fontFamily: 'system-ui, -apple-system, sans-serif',
        }}>
          KOMPAGNON
        </span>
      </div>

      {/* Main */}
      <div style={{ flex: 1, display: 'flex', alignItems: 'flex-start', justifyContent: 'center', padding: '32px 16px' }}>
        <div style={{
          width: '100%', maxWidth: 480, background: '#fff',
          borderRadius: 16, boxShadow: '0 4px 24px rgba(0,0,0,0.08)',
          padding: '36px 32px',
        }}>

          {/* Headline */}
          <h1 style={{
            margin: '0 0 8px', fontSize: 26, fontWeight: 800,
            color: '#111', lineHeight: 1.25,
            fontFamily: 'system-ui, -apple-system, sans-serif',
          }}>
            Wie gut ist Ihre Website wirklich?
          </h1>
          <p style={{ margin: '0 0 20px', fontSize: 16, color: '#555', lineHeight: 1.5 }}>
            Kostenloser Website-Check – Ergebnis in 24h.
          </p>

          {/* Bullets */}
          <ul style={{ listStyle: 'none', margin: '0 0 28px', padding: 0, display: 'flex', flexDirection: 'column', gap: 10 }}>
            {['Google-Sichtbarkeit', 'Ladegeschwindigkeit', 'Sicherheit'].map((item) => (
              <li key={item} style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: 15, color: '#333' }}>
                <span style={{
                  width: 24, height: 24, borderRadius: '50%',
                  background: '#e6f6fa', display: 'flex', alignItems: 'center',
                  justifyContent: 'center', flexShrink: 0,
                  fontSize: 14, color: PRIMARY, fontWeight: 700,
                }}>✓</span>
                {item}
              </li>
            ))}
          </ul>

          {success ? (
            <div style={{
              background: '#f0fdf4', border: '1.5px solid #bbf7d0',
              borderRadius: 12, padding: '24px 20px', textAlign: 'center',
            }}>
              <div style={{ fontSize: 40, marginBottom: 12 }}>✓</div>
              <p style={{ margin: 0, fontWeight: 700, fontSize: 17, color: '#166534' }}>
                Anfrage eingegangen!
              </p>
              <p style={{ margin: '8px 0 0', fontSize: 15, color: '#166534' }}>
                Wir melden uns innerhalb von 24h mit Ihrem Website-Check.
              </p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>

              {/* Feld 1 — E-Mail (zuerst, triggert Domain-Autofill) */}
              <div>
                <label style={labelStyle}>E-Mail-Adresse *</label>
                <input
                  type="email"
                  autoComplete="email"
                  placeholder="ihre@email.de"
                  value={email}
                  onChange={(e) => handleEmailChange(e.target.value)}
                  style={inputStyle}
                  disabled={loading}
                />
              </div>

              {/* Feld 2 — Website (auto-befüllt aus E-Mail) */}
              <div>
                <label style={labelStyle}>Website-Adresse *</label>
                <input
                  type="url"
                  autoComplete="url"
                  placeholder="https://ihr-betrieb.de"
                  value={domain}
                  onChange={(e) => setDomain(e.target.value)}
                  style={{
                    ...inputStyle,
                    background: domain ? '#f0fdf4' : '#fff',
                    borderColor: domain ? '#86efac' : '#d1d5db',
                  }}
                  disabled={loading}
                />
                {domain && (
                  <p style={{ margin: '4px 0 0', fontSize: 12, color: '#16a34a' }}>
                    ✓ Automatisch erkannt – Sie können die Adresse anpassen.
                  </p>
                )}
              </div>

              {/* Feld 3 — Mobilnummer */}
              <div>
                <label style={labelStyle}>WhatsApp / Mobilnummer *</label>
                <input
                  type="tel"
                  autoComplete="tel"
                  inputMode="numeric"
                  placeholder="+49 151 12345678"
                  value={mobil}
                  onChange={(e) => setMobil(e.target.value)}
                  style={inputStyle}
                  disabled={loading}
                />
              </div>

              {error && (
                <div style={{
                  background: '#fef2f2', border: '1.5px solid #fecaca',
                  borderRadius: 8, padding: '12px 14px',
                  fontSize: 14, color: '#dc2626',
                }}>
                  {error}
                </div>
              )}

              <button
                onClick={handleSubmit}
                disabled={loading}
                style={{
                  width: '100%', minHeight: 54, marginTop: 4,
                  background: loading ? '#6bb8c9' : PRIMARY,
                  color: '#fff', border: 'none', borderRadius: 10,
                  fontSize: 16, fontWeight: 700,
                  cursor: loading ? 'not-allowed' : 'pointer',
                  transition: 'background 0.15s',
                  fontFamily: 'system-ui, -apple-system, sans-serif',
                  letterSpacing: '-0.2px',
                }}
              >
                {loading ? 'Wird gesendet…' : 'Jetzt kostenlos prüfen lassen'}
              </button>

              <p style={{ margin: 0, fontSize: 12, color: '#9ca3af', textAlign: 'center', lineHeight: 1.5 }}>
                Ihre Daten werden vertraulich behandelt und nicht weitergegeben.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Footer */}
      <div style={{
        padding: '20px 16px', textAlign: 'center',
        fontSize: 13, color: '#9ca3af',
        borderTop: '1px solid #e5e7eb', background: '#fff',
      }}>
        KOMPAGNON Communications &nbsp;·&nbsp;
        <a href="/impressum" style={{ color: '#6b7280', textDecoration: 'none' }}>Impressum</a>
        &nbsp;·&nbsp;
        <a href="/datenschutz" style={{ color: '#6b7280', textDecoration: 'none' }}>Datenschutz</a>
      </div>
    </div>
  );
}

const labelStyle = {
  display: 'block', marginBottom: 6, fontSize: 14,
  fontWeight: 600, color: '#374151',
  fontFamily: 'system-ui, -apple-system, sans-serif',
};

const inputStyle = {
  width: '100%', boxSizing: 'border-box',
  padding: '14px 14px', fontSize: 16,
  border: '1.5px solid #d1d5db', borderRadius: 8,
  outline: 'none', color: '#111', background: '#fff',
  fontFamily: 'system-ui, -apple-system, sans-serif',
  appearance: 'none', WebkitAppearance: 'none',
  transition: 'border-color 0.15s, background 0.15s',
};

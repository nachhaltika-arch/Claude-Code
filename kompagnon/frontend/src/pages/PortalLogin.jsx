import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import API_BASE_URL from '../config';

export default function PortalLogin() {
  const [email, setEmail]             = useState('');
  const [password, setPassword]       = useState('');
  const [loading, setLoading]         = useState(false);
  const [error, setError]             = useState('');
  const [showForgot, setShowForgot]   = useState(false);
  const [forgotEmail, setForgotEmail] = useState('');
  const [forgotSent, setForgotSent]   = useState(false);

  const { login } = useAuth();
  const navigate  = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const res = await fetch(`${API_BASE_URL}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError('E-Mail oder Passwort falsch.');
        return;
      }
      login(data.access_token, data.user);

      if (data.user.role === 'kunde') {
        navigate('/app/dashboard');
      } else {
        navigate('/app/dashboard');
      }
    } catch {
      setError('Verbindungsfehler — bitte erneut versuchen.');
    } finally {
      setLoading(false);
    }
  };

  const handleForgot = async (e) => {
    e.preventDefault();
    try {
      await fetch(`${API_BASE_URL}/api/auth/forgot-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: forgotEmail }),
      });
      setForgotSent(true);
    } catch { setForgotSent(true); } // Immer Erfolg zeigen (Security)
  };

  const inputStyle = {
    width: '100%', padding: '12px 14px',
    border: '1px solid #e2e8f0', borderRadius: 8,
    fontSize: 16, boxSizing: 'border-box',
    color: '#1a2332', outline: 'none', background: 'white',
  };

  const labelStyle = {
    display: 'block', fontSize: 12, fontWeight: 500,
    color: '#64748b', textTransform: 'uppercase',
    letterSpacing: '0.06em', marginBottom: 6,
  };

  return (
    <div style={{ minHeight: '100vh', background: '#f0f4f8',
                  display: 'flex', alignItems: 'center',
                  justifyContent: 'center', padding: '20px' }}>
      <div style={{ width: '100%', maxWidth: 420 }}>

        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <div style={{ fontSize: 28, fontWeight: 800,
                        color: '#008eaa', marginBottom: 4,
                        letterSpacing: '-0.5px' }}>
            KOMPAGNON
          </div>
          <div style={{ fontSize: 14, color: '#64748b' }}>
            Ihr persönliches Kundenportal
          </div>
        </div>

        {/* Login-Karte */}
        <div style={{ background: 'white', borderRadius: 16,
                      padding: 32, boxShadow: '0 4px 24px rgba(0,0,0,0.08)' }}>

          {!showForgot ? (
            <>
              <h2 style={{ margin: '0 0 24px', fontSize: 20,
                            fontWeight: 600, color: '#1a2332' }}>
                Anmelden
              </h2>

              {error && (
                <div style={{ background: '#FEF2F2', border: '1px solid #FECACA',
                              borderRadius: 8, padding: '10px 14px',
                              color: '#DC2626', fontSize: 13,
                              marginBottom: 20 }}>
                  {error}
                </div>
              )}

              <form onSubmit={handleLogin}>
                <label style={labelStyle}>E-Mail-Adresse</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="ihre@email.de"
                  required
                  autoComplete="email"
                  style={{ ...inputStyle, marginBottom: 16 }}
                />

                <label style={labelStyle}>Passwort</label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Ihr Passwort"
                  required
                  autoComplete="current-password"
                  style={{ ...inputStyle, marginBottom: 24 }}
                />

                <button
                  type="submit"
                  disabled={loading}
                  style={{ width: '100%', padding: '14px',
                           background: loading ? '#94a3b8' : '#008eaa',
                           color: 'white', border: 'none',
                           borderRadius: 8, fontSize: 16,
                           fontWeight: 600,
                           cursor: loading ? 'not-allowed' : 'pointer',
                           transition: 'background 0.2s' }}>
                  {loading ? 'Wird angemeldet...' : 'Anmelden'}
                </button>
              </form>

              <div style={{ textAlign: 'center', marginTop: 16 }}>
                <button
                  onClick={() => setShowForgot(true)}
                  style={{ background: 'none', border: 'none',
                           color: '#008eaa', fontSize: 13,
                           cursor: 'pointer', textDecoration: 'underline' }}>
                  Passwort vergessen?
                </button>
              </div>
            </>
          ) : (
            <>
              <h2 style={{ margin: '0 0 8px', fontSize: 20,
                            fontWeight: 600, color: '#1a2332' }}>
                Passwort zurücksetzen
              </h2>
              <p style={{ color: '#64748b', fontSize: 14,
                          marginBottom: 24, marginTop: 0 }}>
                Geben Sie Ihre E-Mail-Adresse ein. Wir senden
                Ihnen einen Link zum Zurücksetzen.
              </p>

              {forgotSent ? (
                <div style={{ background: '#F0FDF4',
                              border: '1px solid #BBF7D0',
                              borderRadius: 8, padding: '14px',
                              color: '#166534', fontSize: 14,
                              textAlign: 'center' }}>
                  Falls diese E-Mail existiert, erhalten Sie
                  in Kürze eine Nachricht.
                </div>
              ) : (
                <form onSubmit={handleForgot}>
                  <input
                    type="email"
                    value={forgotEmail}
                    onChange={(e) => setForgotEmail(e.target.value)}
                    placeholder="ihre@email.de"
                    required
                    style={{ ...inputStyle, marginBottom: 16 }}
                  />
                  <button type="submit"
                    style={{ width: '100%', padding: '14px',
                             background: '#008eaa', color: 'white',
                             border: 'none', borderRadius: 8,
                             fontSize: 16, fontWeight: 600,
                             cursor: 'pointer' }}>
                    Link anfordern
                  </button>
                </form>
              )}

              <div style={{ textAlign: 'center', marginTop: 16 }}>
                <button
                  onClick={() => { setShowForgot(false); setForgotSent(false); }}
                  style={{ background: 'none', border: 'none',
                           color: '#64748b', fontSize: 13,
                           cursor: 'pointer' }}>
                  ← Zurück zum Login
                </button>
              </div>
            </>
          )}
        </div>

        {/* Footer-Hinweis */}
        <div style={{ textAlign: 'center', marginTop: 20,
                      fontSize: 12, color: '#94a3b8' }}>
          Zugangsdaten erhalten Sie per E-Mail nach Ihrem Kauf.<br />
          <span style={{ color: '#cbd5e1' }}>
            KOMPAGNON Communications BP GmbH · kompagnon.eu
          </span>
        </div>

        {/* QR-Code-Hinweis */}
        <div style={{ textAlign: 'center', marginTop: 12 }}>
          <span style={{ fontSize: 12, color: '#94a3b8' }}>
            Haben Sie einen QR-Code erhalten?{' '}
          </span>
          <span style={{ fontSize: 12, color: '#008eaa' }}>
            Bitte scannen Sie diesen direkt.
          </span>
        </div>
      </div>
    </div>
  );
}

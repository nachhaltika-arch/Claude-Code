import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import API_BASE_URL from '../config';

export default function PortalLogin() {
  const [mode, setMode]               = useState('login');
  const [email, setEmail]             = useState('');
  const [password, setPassword]       = useState('');
  const [forgotEmail, setForgotEmail] = useState('');
  const [loading, setLoading]         = useState(false);
  const [error, setError]             = useState('');
  const [forgotSent, setForgotSent]   = useState(false);
  const { login } = useAuth();
  const navigate   = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    if (!email || !password) {
      setError('Bitte E-Mail und Passwort eingeben.');
      return;
    }
    setLoading(true); setError('');
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
      // Alle Rollen landen auf /app/dashboard
      // Dashboard entscheidet dann ob Onboarding oder normale Ansicht
      navigate('/app/dashboard', { replace: true });
    } catch {
      setError('Verbindungsfehler — bitte erneut versuchen.');
    } finally { setLoading(false); }
  };

  const handleForgot = async (e) => {
    e.preventDefault();
    try {
      await fetch(`${API_BASE_URL}/api/auth/forgot-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: forgotEmail }),
      });
    } catch {}
    setForgotSent(true); // Immer Erfolg zeigen
  };

  const inp = {
    width: '100%', padding: '13px 14px',
    border: '1.5px solid #e2e8f0', borderRadius: 10,
    fontSize: 16, fontFamily: 'inherit',
    color: '#1a2332', background: 'white',
    boxSizing: 'border-box', outline: 'none',
    marginBottom: 16,
  };
  const lbl = {
    display: 'block', fontSize: 11, fontWeight: 600,
    color: '#64748b', textTransform: 'uppercase',
    letterSpacing: '0.06em', marginBottom: 6,
  };
  const btn = {
    width: '100%', padding: '14px', border: 'none',
    borderRadius: 10, background: '#008eaa',
    color: 'white', fontSize: 15, fontWeight: 700,
    cursor: 'pointer', fontFamily: 'inherit',
  };

  return (
    <div style={{
      minHeight: '100vh', background: '#f0f4f8',
      display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center',
      padding: 20,
    }}>
      {/* Karte */}
      <div style={{
        width: '100%', maxWidth: 420,
        background: 'white', borderRadius: 20,
        padding: 36, boxShadow: '0 8px 40px rgba(0,0,0,0.1)',
      }}>
        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <div style={{ fontSize: 26, fontWeight: 800, color: '#008eaa', letterSpacing: '-0.02em' }}>
            KOMPAGNON
          </div>
          <div style={{ fontSize: 13, color: '#94a3b8', marginTop: 4 }}>
            Ihr persönliches Kundenportal
          </div>
        </div>

        {/* ── Login ── */}
        {mode === 'login' && (
          <>
            <h2 style={{ fontSize: 18, fontWeight: 700, color: '#1a2332', margin: '0 0 20px' }}>
              Anmelden
            </h2>

            {error && (
              <div style={{
                background: '#fef2f2', border: '1px solid #fecaca',
                borderRadius: 8, padding: '10px 14px',
                fontSize: 13, color: '#b91c1c', marginBottom: 16,
              }}>
                {error}
              </div>
            )}

            <form onSubmit={handleLogin}>
              <label style={lbl}>E-Mail-Adresse</label>
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                autoComplete="email"
                placeholder="ihre@email.de"
                style={inp}
              />
              <label style={lbl}>Passwort</label>
              <input
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                autoComplete="current-password"
                placeholder="••••••••"
                style={inp}
              />
              <button type="submit" style={{ ...btn, opacity: loading ? 0.7 : 1 }} disabled={loading}>
                {loading ? 'Wird angemeldet...' : 'Anmelden →'}
              </button>
            </form>

            <div style={{ textAlign: 'center', marginTop: 20 }}>
              <button
                onClick={() => { setMode('forgot'); setError(''); }}
                style={{
                  background: 'none', border: 'none', color: '#008eaa',
                  fontSize: 13, cursor: 'pointer', fontFamily: 'inherit',
                  textDecoration: 'underline',
                }}
              >
                Passwort vergessen?
              </button>
            </div>
          </>
        )}

        {/* ── Passwort vergessen ── */}
        {mode === 'forgot' && !forgotSent && (
          <>
            <h2 style={{ fontSize: 18, fontWeight: 700, color: '#1a2332', margin: '0 0 12px' }}>
              Passwort zurücksetzen
            </h2>
            <p style={{ fontSize: 13, color: '#64748b', marginTop: 0, marginBottom: 20, lineHeight: 1.6 }}>
              Geben Sie Ihre E-Mail-Adresse ein. Falls ein Konto existiert,
              erhalten Sie einen Reset-Link.
            </p>
            <form onSubmit={handleForgot}>
              <label style={lbl}>E-Mail-Adresse</label>
              <input
                type="email"
                value={forgotEmail}
                onChange={e => setForgotEmail(e.target.value)}
                autoComplete="email"
                placeholder="ihre@email.de"
                style={inp}
              />
              <button type="submit" style={btn}>Link anfordern</button>
            </form>
            <div style={{ textAlign: 'center', marginTop: 20 }}>
              <button
                onClick={() => setMode('login')}
                style={{
                  background: 'none', border: 'none', color: '#64748b',
                  fontSize: 13, cursor: 'pointer', fontFamily: 'inherit',
                }}
              >
                ← Zurück zum Login
              </button>
            </div>
          </>
        )}

        {/* ── Passwort vergessen — Erfolg ── */}
        {mode === 'forgot' && forgotSent && (
          <>
            <div style={{
              background: '#f0fdf4', border: '1px solid #bbf7d0',
              borderRadius: 10, padding: '16px 18px',
              fontSize: 13, color: '#166534', lineHeight: 1.6,
            }}>
              Falls diese E-Mail-Adresse registriert ist, erhalten Sie in Kürze einen Reset-Link.
            </div>
            <div style={{ textAlign: 'center', marginTop: 20 }}>
              <button
                onClick={() => { setMode('login'); setForgotSent(false); }}
                style={{
                  background: 'none', border: 'none', color: '#64748b',
                  fontSize: 13, cursor: 'pointer', fontFamily: 'inherit',
                }}
              >
                ← Zurück zum Login
              </button>
            </div>
          </>
        )}
      </div>

      {/* Footer */}
      <div style={{ textAlign: 'center', fontSize: 12, color: '#94a3b8', marginTop: 24, lineHeight: 1.8 }}>
        <div>Zugangsdaten erhalten Sie per E-Mail nach Ihrem Kauf.</div>
        <div>KOMPAGNON Communications BP GmbH · kompagnon.eu</div>
      </div>
    </div>
  );
}

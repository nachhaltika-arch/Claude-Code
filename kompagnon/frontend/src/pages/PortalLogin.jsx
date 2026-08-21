import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import API_BASE_URL from '../config';
import { loadJson } from '../utils/apiRequest';
import SeitenTitel from '../components/ui/SeitenTitel';

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
    // Bewusst ohne Rueckmeldung: die Antwort darf nicht verraten, ob es zu
    // dieser Adresse ein Konto gibt. Deshalb wird immer Erfolg angezeigt.
    await loadJson(
      `${API_BASE_URL}/api/auth/forgot-password`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: forgotEmail }),
      },
      { quiet: true },
    );
    setForgotSent(true);
  };

  // Diese Seite ist der erste Bildschirm nach dem Kauf. Sie trug ihre Farben
  // bis zum 18.08.2026 als feste Hexwerte und blieb deshalb weiss, waehrend
  // das Werkzeug dem System des Betrachters folgt — der Bruch aus UX-19.
  // Jetzt dasselbe Farbsystem wie alles andere: `styles/tokens.css`.
  const inp = {
    width: '100%', padding: '13px 14px',
    border: '1.5px solid var(--border-medium)', borderRadius: 10,
    fontSize: 16, fontFamily: 'inherit',
    color: 'var(--text-primary)', background: 'var(--bg-app)',
    boxSizing: 'border-box', outline: 'none',
    marginBottom: 16,
  };
  const lbl = {
    display: 'block', fontSize: 11, fontWeight: 600,
    color: 'var(--text-tertiary)', textTransform: 'uppercase',
    letterSpacing: '0.06em', marginBottom: 6,
  };
  const btn = {
    width: '100%', padding: '14px', border: 'none',
    borderRadius: 10, background: 'var(--brand-primary)',
    // Nicht Weiss: im Dunkelmodus ist --brand-primary das helle Tuerkis,
    // Weiss darauf erreicht 2.06. Siehe `utils/kontrast.test.js`.
    color: 'var(--text-on-brand)', fontSize: 15, fontWeight: 700,
    cursor: 'pointer', fontFamily: 'inherit',
  };
  const leiser = { background: 'none', border: 'none', fontSize: 13,
    cursor: 'pointer', fontFamily: 'inherit', color: 'var(--text-secondary)' };

  return (
    <div style={{
      minHeight: '100vh', background: 'var(--bg-app)',
      display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center',
      padding: 20,
    }}>
      <SeitenTitel>Kundenportal — Anmelden</SeitenTitel>
      {/* Karte */}
      <div style={{
        width: '100%', maxWidth: 420,
        background: 'var(--bg-surface)', borderRadius: 20,
        border: '1px solid var(--border-light)',
        padding: 36, boxShadow: 'var(--shadow-xl)',
      }}>
        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <div style={{ fontSize: 26, fontWeight: 800, color: 'var(--brand-primary)', letterSpacing: '-0.02em' }}>
            KOMPAGNON
          </div>
          <div style={{ fontSize: 13, color: 'var(--text-tertiary)', marginTop: 4 }}>
            Ihr persönliches Kundenportal
          </div>
        </div>

        {/* ── Login ── */}
        {mode === 'login' && (
          <>
            <h2 style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-primary)', margin: '0 0 20px' }}>
              Anmelden
            </h2>

            {error && (
              <div style={{
                background: 'var(--status-danger-bg)',
                border: '1px solid var(--border-light)',
                borderRadius: 8, padding: '10px 14px',
                fontSize: 13, color: 'var(--status-danger-text)', marginBottom: 16,
              }}>
                {error}
              </div>
            )}

            <form onSubmit={handleLogin}>
              <label style={lbl}>E-Mail-Adresse</label>
              <input aria-label="E-Mail-Adresse"
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                autoComplete="email"
                placeholder="ihre@email.de"
                style={inp}
              />
              <label style={lbl}>Passwort</label>
              <input aria-label="Passwort"
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
                style={{ ...leiser, color: 'var(--text-brand)', textDecoration: 'underline' }}
              >
                Passwort vergessen?
              </button>
            </div>
          </>
        )}

        {/* ── Passwort vergessen ── */}
        {mode === 'forgot' && !forgotSent && (
          <>
            <h2 style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-primary)', margin: '0 0 12px' }}>
              Passwort zurücksetzen
            </h2>
            <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 0, marginBottom: 20, lineHeight: 1.6 }}>
              Geben Sie Ihre E-Mail-Adresse ein. Falls ein Konto existiert,
              erhalten Sie einen Reset-Link.
            </p>
            <form onSubmit={handleForgot}>
              <label style={lbl}>E-Mail-Adresse</label>
              <input aria-label="E-Mail-Adresse"
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
                style={leiser}
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
              background: 'var(--status-success-bg)',
              border: '1px solid var(--border-light)',
              borderRadius: 10, padding: '16px 18px',
              fontSize: 13, color: 'var(--status-success-text)', lineHeight: 1.6,
            }}>
              Falls diese E-Mail-Adresse registriert ist, erhalten Sie in Kürze einen Reset-Link.
            </div>
            <div style={{ textAlign: 'center', marginTop: 20 }}>
              <button
                onClick={() => { setMode('login'); setForgotSent(false); }}
                style={leiser}
              >
                ← Zurück zum Login
              </button>
            </div>
          </>
        )}
      </div>

      {/* Fuss — bis zum 18.08.2026 stand hier `kompagnon.eu`, eine dritte
        * Domain neben der, auf der der Kunde gerade steht. Wer sie anklickte,
        * verliess das Haus, in dem er sich anmelden wollte. Jetzt der
        * Firmenname und die eigenen Rechtsseiten. */}
      <div style={{ textAlign: 'center', fontSize: 12, color: 'var(--text-tertiary)', marginTop: 24, lineHeight: 1.8 }}>
        <div>Zugangsdaten erhalten Sie per E-Mail nach Ihrem Kauf.</div>
        <div>KOMPAGNON communications BP GmbH</div>
        <div style={{ display: 'flex', gap: 14, justifyContent: 'center' }}>
          <Link to="/impressum" style={{ color: 'var(--text-tertiary)' }}>Impressum</Link>
          <Link to="/datenschutz" style={{ color: 'var(--text-tertiary)' }}>Datenschutz</Link>
        </div>
      </div>
    </div>
  );
}

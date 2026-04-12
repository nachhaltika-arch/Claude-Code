import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Logo from '../components/Logo';
import KompagnonLogo from '../components/KompagnonLogo';
import Button from '../components/ui/Button';
import API_BASE_URL from '../config';

export default function Login() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [step, setStep] = useState('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPw, setShowPw] = useState(false);
  const [totp, setTotp] = useState(['','','','','','']);
  const [tempToken, setTempToken] = useState('');
  const [forgotEmail, setForgotEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const inputStyle = {
    width: '100%', padding: '10px 12px',
    border: '1px solid var(--border-medium)',
    borderRadius: 'var(--radius-md)',
    fontSize: 14, fontFamily: 'var(--font-sans)',
    color: 'var(--text-primary)', background: 'var(--bg-surface)',
    outline: 'none', boxSizing: 'border-box', transition: 'border-color 0.15s',
  };

  const labelStyle = {
    display: 'block', fontSize: 11, fontWeight: 500,
    color: 'var(--text-tertiary)', textTransform: 'uppercase',
    letterSpacing: '0.06em', marginBottom: 6,
  };

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
      if (!res.ok) { setError(data.detail || 'E-Mail oder Passwort falsch'); return; }
      if (data.require_2fa) { setTempToken(data.temp_token); setStep('2fa'); return; }
      login(data.access_token, data.user);
      navigate('/app/dashboard');
    } catch {
      setError('Verbindungsfehler');
    } finally {
      setLoading(false);
    }
  };

  const handle2FA = async () => {
    const code = totp.join('');
    if (code.length !== 6) return;
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/auth/login/2fa`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ temp_token: tempToken, totp_code: code }),
      });
      const data = await res.json();
      if (!res.ok) { setError('Code ungültig'); setTotp(['','','','','','']); return; }
      login(data.access_token, data.user);
      navigate('/app/dashboard');
    } catch {
      setError('Fehler');
    } finally {
      setLoading(false);
    }
  };

  const handleForgot = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await fetch(`${API_BASE_URL}/api/auth/forgot-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: forgotEmail }),
      });
      setSuccess('Falls diese E-Mail existiert, erhalten Sie einen Reset-Link.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh', background: 'var(--bg-app)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      padding: 20, fontFamily: 'var(--font-sans)',
    }}>
      <div style={{ width: '100%', maxWidth: 380 }}>

        {/* Logo */}
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          marginBottom: '2rem',
          gap: '0.5rem',
          cursor: 'pointer',
        }} onClick={() => navigate('/')}>
          <KompagnonLogo height={52} variant="color" showTagline={false} />
          <p style={{
            fontSize: '0.8rem',
            color: 'var(--color-text-secondary)',
            letterSpacing: '0.15em',
            textTransform: 'uppercase',
            marginTop: '0.5rem',
          }}>
            Automation System
          </p>
        </div>

        {/* Card */}
        <div style={{
          background: 'var(--bg-surface)', borderRadius: 'var(--radius-xl)',
          border: '1px solid var(--border-light)', boxShadow: 'var(--shadow-elevated)',
          padding: 28,
        }}>

          {/* LOGIN */}
          {step === 'login' && (
            <>
              <h2 style={{ fontSize: 18, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 4 }}>Anmelden</h2>
              <p style={{ fontSize: 12, color: 'var(--text-tertiary)', marginBottom: 20 }}>Willkommen zurück</p>

              {error && (
                <div style={{ background: 'var(--status-danger-bg)', color: 'var(--status-danger-text)', borderRadius: 'var(--radius-md)', padding: '10px 12px', fontSize: 12, marginBottom: 16 }}>
                  {error}
                </div>
              )}

              <form onSubmit={handleLogin}>
                <div style={{ marginBottom: 14 }}>
                  <label style={labelStyle}>E-Mail</label>
                  <input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="ihre@email.de" required style={inputStyle}
                    onFocus={e => e.target.style.borderColor = 'var(--brand-primary)'}
                    onBlur={e => e.target.style.borderColor = 'var(--border-medium)'} />
                </div>

                <div style={{ marginBottom: 8 }}>
                  <label style={labelStyle}>Passwort</label>
                  <div style={{ position: 'relative' }}>
                    <input type={showPw ? 'text' : 'password'} value={password} onChange={e => setPassword(e.target.value)}
                      placeholder="••••••••" required style={{ ...inputStyle, paddingRight: 40 }}
                      onFocus={e => e.target.style.borderColor = 'var(--brand-primary)'}
                      onBlur={e => e.target.style.borderColor = 'var(--border-medium)'} />
                    <button type="button" onClick={() => setShowPw(!showPw)} style={{
                      position: 'absolute', right: 10, top: '50%', transform: 'translateY(-50%)',
                      background: 'none', border: 'none', color: 'var(--text-tertiary)', cursor: 'pointer', fontSize: 14, padding: 0,
                    }}>
                      {showPw ? '🙈' : '👁️'}
                    </button>
                  </div>
                </div>

                <div style={{ textAlign: 'right', marginBottom: 18 }}>
                  <button type="button" onClick={() => setStep('forgot')} style={{
                    background: 'none', border: 'none', color: 'var(--brand-primary)',
                    fontSize: 11, cursor: 'pointer', fontFamily: 'var(--font-sans)',
                  }}>
                    Passwort vergessen?
                  </button>
                </div>

                <Button type="submit" fullWidth disabled={loading}>
                  {loading ? 'Anmelden...' : 'Anmelden →'}
                </Button>
              </form>

              <div style={{ textAlign: 'center', marginTop: 16, fontSize: 12, color: 'var(--text-tertiary)' }}>
                Kein Konto?{' '}
                <Link to="/register" style={{ color: 'var(--brand-primary)', fontWeight: 500 }}>Registrieren</Link>
              </div>
            </>
          )}

          {/* 2FA */}
          {step === '2fa' && (
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 36, marginBottom: 12 }}>🔐</div>
              <h2 style={{ fontSize: 16, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 6 }}>Zwei-Faktor-Code</h2>
              <p style={{ fontSize: 12, color: 'var(--text-tertiary)', marginBottom: 24 }}>
                6-stelligen Code aus Ihrer Authenticator-App eingeben
              </p>

              {error && (
                <div style={{ background: 'var(--status-danger-bg)', color: 'var(--status-danger-text)', borderRadius: 'var(--radius-md)', padding: '8px 12px', fontSize: 12, marginBottom: 16 }}>
                  {error}
                </div>
              )}

              <div style={{ display: 'flex', gap: 6, justifyContent: 'center', marginBottom: 20 }}>
                {totp.map((d, i) => (
                  <input key={i} id={`t${i}`} type="text" inputMode="numeric" maxLength={1} value={d}
                    onChange={e => {
                      if (!/^\d*$/.test(e.target.value)) return;
                      const n = [...totp];
                      n[i] = e.target.value.slice(-1);
                      setTotp(n);
                      if (e.target.value && i < 5) document.getElementById(`t${i+1}`)?.focus();
                      if (n.every(x => x) && n.join('').length === 6) setTimeout(handle2FA, 100);
                    }}
                    onKeyDown={e => { if (e.key === 'Backspace' && !d && i > 0) document.getElementById(`t${i-1}`)?.focus(); }}
                    style={{
                      width: 42, height: 48, textAlign: 'center', fontSize: 20, fontWeight: 600,
                      border: `1.5px solid ${d ? 'var(--brand-primary)' : 'var(--border-medium)'}`,
                      borderRadius: 'var(--radius-md)', outline: 'none',
                      fontFamily: 'var(--font-mono)', color: 'var(--text-primary)',
                      background: 'var(--bg-surface)', marginRight: i === 2 ? 10 : 0,
                    }}
                  />
                ))}
              </div>

              <Button fullWidth onClick={handle2FA} disabled={loading || totp.join('').length !== 6}>
                {loading ? 'Prüfen...' : 'Bestätigen'}
              </Button>

              <button onClick={() => { setStep('login'); setError(''); setTotp(['','','','','','']); }} style={{
                background: 'none', border: 'none', color: 'var(--text-tertiary)',
                fontSize: 12, cursor: 'pointer', marginTop: 12, fontFamily: 'var(--font-sans)',
              }}>
                ← Zurück
              </button>
            </div>
          )}

          {/* PASSWORT VERGESSEN */}
          {step === 'forgot' && (
            <>
              <h2 style={{ fontSize: 16, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 4 }}>Passwort zurücksetzen</h2>
              <p style={{ fontSize: 12, color: 'var(--text-tertiary)', marginBottom: 20 }}>Reset-Link per E-Mail erhalten</p>

              {success ? (
                <div style={{ background: 'var(--status-success-bg)', color: 'var(--status-success-text)', borderRadius: 'var(--radius-md)', padding: '12px', fontSize: 13, textAlign: 'center' }}>
                  ✓ {success}
                </div>
              ) : (
                <form onSubmit={handleForgot}>
                  <div style={{ marginBottom: 16 }}>
                    <label style={labelStyle}>E-Mail</label>
                    <input type="email" value={forgotEmail} onChange={e => setForgotEmail(e.target.value)}
                      placeholder="ihre@email.de" required style={inputStyle}
                      onFocus={e => e.target.style.borderColor = 'var(--brand-primary)'}
                      onBlur={e => e.target.style.borderColor = 'var(--border-medium)'} />
                  </div>
                  <Button type="submit" fullWidth disabled={loading}>
                    {loading ? 'Senden...' : 'Reset-Link senden'}
                  </Button>
                </form>
              )}

              <button onClick={() => { setStep('login'); setSuccess(''); }} style={{
                background: 'none', border: 'none', color: 'var(--text-tertiary)',
                fontSize: 12, cursor: 'pointer', marginTop: 12,
                fontFamily: 'var(--font-sans)', display: 'block', width: '100%', textAlign: 'center',
              }}>
                ← Zurück zum Login
              </button>
            </>
          )}
        </div>

        {/* Footer */}
        <div style={{ textAlign: 'center', marginTop: 16, fontSize: 11, color: 'var(--text-tertiary)' }}>
          © 2026 KOMPAGNON
        </div>
      </div>
    </div>
  );
}

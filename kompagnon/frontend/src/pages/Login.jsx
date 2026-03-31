import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import API_BASE_URL from '../config';
import Logo from '../components/Logo';

export default function Login() {
  const navigate = useNavigate();
  const { login } = useAuth();

  const [step, setStep] = useState('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [totpCode, setTotpCode] = useState(['', '', '', '', '', '']);
  const [tempToken, setTempToken] = useState('');
  const [forgotEmail, setForgotEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

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
    } catch { setError('Verbindungsfehler. Bitte erneut versuchen.'); }
    finally { setLoading(false); }
  };

  const handle2FA = async () => {
    const code = totpCode.join('');
    if (code.length !== 6) return;
    setLoading(true);
    setError('');
    try {
      const res = await fetch(`${API_BASE_URL}/api/auth/login/2fa`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ temp_token: tempToken, totp_code: code }),
      });
      const data = await res.json();
      if (!res.ok) { setError('Code falsch. Bitte erneut versuchen.'); setTotpCode(['', '', '', '', '', '']); return; }
      login(data.access_token, data.user);
      navigate('/app/dashboard');
    } catch { setError('Fehler. Bitte erneut versuchen.'); }
    finally { setLoading(false); }
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
      setSuccess('Falls die E-Mail existiert, erhalten Sie in Kürze einen Reset-Link.');
    } finally { setLoading(false); }
  };

  const handleTotpInput = (index, value) => {
    if (!/^\d*$/.test(value)) return;
    const next = [...totpCode];
    next[index] = value.slice(-1);
    setTotpCode(next);
    if (value && index < 5) document.getElementById(`totp-${index + 1}`)?.focus();
    if (next.every((d) => d) && next.join('').length === 6) setTimeout(() => handle2FA(), 100);
  };

  const handleTotpKeyDown = (index, e) => {
    if (e.key === 'Backspace' && !totpCode[index] && index > 0) document.getElementById(`totp-${index - 1}`)?.focus();
  };

  const inp = {
    width: '100%', padding: '10px 14px', border: '1px solid var(--border-light)',
    borderRadius: 'var(--radius-md)', fontSize: 14, fontFamily: 'var(--font-sans)',
    background: 'var(--bg-surface)', color: 'var(--text-primary)', outline: 'none',
    transition: 'border-color 0.15s',
  };
  const lbl = {
    display: 'block', fontSize: 12, fontWeight: 500, color: 'var(--text-secondary)',
    marginBottom: 6,
  };

  return (
    <div style={{
      minHeight: '100vh', background: 'var(--bg-app)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      padding: 20, fontFamily: 'var(--font-sans)',
    }}>
      <div style={{ width: '100%', maxWidth: 420 }}>
        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <div onClick={() => navigate('/')} style={{ display: 'inline-flex', flexDirection: 'column', alignItems: 'center', cursor: 'pointer', gap: 8 }}>
            <div style={{ color: 'var(--brand-primary)' }}>
              <Logo size="large" />
            </div>
          </div>
        </div>

        {/* Card */}
        <div style={{
          background: 'var(--bg-surface)', borderRadius: 'var(--radius-xl)',
          padding: 32, boxShadow: 'var(--shadow-elevated)',
          border: '1px solid var(--border-light)',
        }}>

          {/* ── LOGIN ── */}
          {step === 'login' && (
            <>
              <h2 style={{ margin: '0 0 6px', fontSize: 18, fontWeight: 500, color: 'var(--text-primary)' }}>Willkommen zurück</h2>
              <p style={{ margin: '0 0 24px', color: 'var(--text-secondary)', fontSize: 13 }}>Melden Sie sich in Ihrem Konto an</p>

              {error && (
                <div style={{
                  background: 'var(--status-danger-bg)', color: 'var(--status-danger-text)',
                  borderRadius: 'var(--radius-md)', padding: '10px 14px', fontSize: 13, marginBottom: 16,
                }}>
                  {error}
                </div>
              )}

              {/* Demo Accounts */}
              <div style={{ marginBottom: 20 }}>
                <div style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 8, textAlign: 'center' }}>
                  Demo-Zugänge
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 6 }}>
                  {[
                    { role: 'Admin', email: 'admin@kompagnon.de', password: 'Admin2025!', desc: 'Volle Rechte' },
                    { role: 'Auditor', email: 'auditor@kompagnon.de', password: 'Auditor2025!', desc: 'Audit-Zugang' },
                    { role: 'Nutzer', email: 'nutzer@kompagnon.de', password: 'Nutzer2025!', desc: 'Eingeschränkt' },
                    { role: 'Kunde', email: 'kunde@kompagnon.de', password: 'Kunde2025!', desc: 'Nur eigene Daten' },
                  ].map((d) => (
                    <button key={d.role} type="button" onClick={() => { setEmail(d.email); setPassword(d.password); }} style={{
                      display: 'flex', flexDirection: 'column', alignItems: 'flex-start', padding: '8px 10px',
                      background: 'var(--bg-hover)', border: '1px solid var(--border-light)',
                      borderRadius: 'var(--radius-md)', cursor: 'pointer', textAlign: 'left',
                      fontFamily: 'var(--font-sans)', transition: 'border-color 0.15s',
                    }}
                    onMouseEnter={e => e.currentTarget.style.borderColor = 'var(--brand-primary)'}
                    onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--border-light)'}
                    >
                      <span style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-primary)' }}>{d.role}</span>
                      <span style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>{d.desc}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Divider */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 12, margin: '16px 0' }}>
                <div style={{ flex: 1, height: 1, background: 'var(--border-light)' }} />
                <span style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>E-Mail Login</span>
                <div style={{ flex: 1, height: 1, background: 'var(--border-light)' }} />
              </div>

              <form onSubmit={handleLogin}>
                <div style={{ marginBottom: 14 }}>
                  <label style={lbl}>E-Mail-Adresse</label>
                  <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="ihre@email.de" required style={inp}
                    onFocus={e => e.target.style.borderColor = 'var(--brand-primary)'}
                    onBlur={e => e.target.style.borderColor = 'var(--border-light)'} />
                </div>
                <div style={{ marginBottom: 8 }}>
                  <label style={lbl}>Passwort</label>
                  <div style={{ position: 'relative' }}>
                    <input type={showPassword ? 'text' : 'password'} value={password} onChange={(e) => setPassword(e.target.value)}
                      placeholder="........" required style={{ ...inp, paddingRight: 44 }}
                      onFocus={e => e.target.style.borderColor = 'var(--brand-primary)'}
                      onBlur={e => e.target.style.borderColor = 'var(--border-light)'} />
                    <button type="button" onClick={() => setShowPassword(!showPassword)} style={{
                      position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)',
                      background: 'none', border: 'none', cursor: 'pointer', fontSize: 14, color: 'var(--text-tertiary)', padding: 0, lineHeight: 1,
                    }}>
                      {showPassword ? '🙈' : '👁️'}
                    </button>
                  </div>
                </div>
                <div style={{ textAlign: 'right', marginBottom: 20 }}>
                  <button type="button" onClick={() => setStep('forgot')} style={{
                    background: 'none', border: 'none', color: 'var(--brand-primary)', fontSize: 12,
                    cursor: 'pointer', padding: 0,
                  }}>
                    Passwort vergessen?
                  </button>
                </div>
                <button type="submit" disabled={loading} style={{
                  width: '100%', padding: '12px', background: loading ? 'var(--text-tertiary)' : 'var(--brand-primary)',
                  color: 'var(--text-inverse)', border: 'none', borderRadius: 'var(--radius-md)',
                  fontSize: 14, fontWeight: 500, cursor: loading ? 'not-allowed' : 'pointer',
                  fontFamily: 'var(--font-sans)', minHeight: 44, transition: 'background 0.15s',
                }}
                onMouseEnter={e => { if (!loading) e.currentTarget.style.background = 'var(--brand-primary-dark)'; }}
                onMouseLeave={e => { if (!loading) e.currentTarget.style.background = 'var(--brand-primary)'; }}
                >
                  {loading ? 'Anmelden...' : 'Anmelden'}
                </button>
              </form>

              <div style={{ textAlign: 'center', marginTop: 20, fontSize: 13, color: 'var(--text-secondary)' }}>
                Noch kein Konto?{' '}
                <Link to="/register" style={{ color: 'var(--brand-primary)', fontWeight: 500 }}>Jetzt registrieren</Link>
              </div>
            </>
          )}

          {/* ── 2FA ── */}
          {step === '2fa' && (
            <div style={{ textAlign: 'center' }}>
              <h2 style={{ margin: '0 0 6px', fontSize: 18, fontWeight: 500, color: 'var(--text-primary)' }}>Zwei-Faktor-Authentifizierung</h2>
              <p style={{ margin: '0 0 24px', color: 'var(--text-secondary)', fontSize: 13 }}>6-stelligen Code eingeben</p>

              {error && (
                <div style={{ background: 'var(--status-danger-bg)', color: 'var(--status-danger-text)', borderRadius: 'var(--radius-md)', padding: '10px 14px', fontSize: 13, marginBottom: 16 }}>
                  {error}
                </div>
              )}

              <div style={{ display: 'flex', gap: 8, justifyContent: 'center', marginBottom: 24 }}>
                {totpCode.map((digit, i) => (
                  <input key={i} id={`totp-${i}`} type="text" inputMode="numeric" maxLength={1} value={digit}
                    onChange={(e) => handleTotpInput(i, e.target.value)} onKeyDown={(e) => handleTotpKeyDown(i, e)}
                    autoFocus={i === 0}
                    style={{
                      width: 42, height: 48, textAlign: 'center', fontSize: 20, fontWeight: 500,
                      border: `1.5px solid ${digit ? 'var(--brand-primary)' : 'var(--border-light)'}`,
                      borderRadius: 'var(--radius-md)', outline: 'none',
                      fontFamily: 'var(--font-sans)', color: 'var(--text-primary)',
                      marginRight: i === 2 ? 12 : 0,
                    }}
                  />
                ))}
              </div>

              <button onClick={handle2FA} disabled={loading || totpCode.join('').length !== 6} style={{
                width: '100%', padding: '12px', background: 'var(--brand-primary)', color: 'var(--text-inverse)',
                border: 'none', borderRadius: 'var(--radius-md)', fontSize: 14, fontWeight: 500,
                cursor: 'pointer', fontFamily: 'var(--font-sans)', marginBottom: 12, minHeight: 44,
              }}>
                {loading ? 'Prüfen...' : 'Bestätigen'}
              </button>
              <button onClick={() => { setStep('login'); setError(''); setTotpCode(['', '', '', '', '', '']); }} style={{
                background: 'none', border: 'none', color: 'var(--text-secondary)', fontSize: 13, cursor: 'pointer',
              }}>
                Zurück zum Login
              </button>
            </div>
          )}

          {/* ── FORGOT ── */}
          {step === 'forgot' && (
            <>
              <h2 style={{ margin: '0 0 6px', fontSize: 18, fontWeight: 500, color: 'var(--text-primary)' }}>Passwort zurücksetzen</h2>
              <p style={{ margin: '0 0 20px', color: 'var(--text-secondary)', fontSize: 13 }}>Wir senden Ihnen einen Reset-Link</p>

              {success ? (
                <div style={{
                  background: 'var(--status-success-bg)', color: 'var(--status-success-text)',
                  borderRadius: 'var(--radius-md)', padding: 14, fontSize: 13, textAlign: 'center',
                }}>
                  {success}
                </div>
              ) : (
                <form onSubmit={handleForgot}>
                  <div style={{ marginBottom: 16 }}>
                    <label style={lbl}>E-Mail-Adresse</label>
                    <input type="email" value={forgotEmail} onChange={(e) => setForgotEmail(e.target.value)} placeholder="ihre@email.de" required style={inp}
                      onFocus={e => e.target.style.borderColor = 'var(--brand-primary)'}
                      onBlur={e => e.target.style.borderColor = 'var(--border-light)'} />
                  </div>
                  <button type="submit" disabled={loading} style={{
                    width: '100%', padding: '12px', background: 'var(--brand-primary)', color: 'var(--text-inverse)',
                    border: 'none', borderRadius: 'var(--radius-md)', fontSize: 14, fontWeight: 500,
                    cursor: 'pointer', fontFamily: 'var(--font-sans)', marginBottom: 12, minHeight: 44,
                  }}>
                    {loading ? 'Senden...' : 'Reset-Link senden'}
                  </button>
                </form>
              )}
              <button onClick={() => { setStep('login'); setSuccess(''); }} style={{
                background: 'none', border: 'none', color: 'var(--text-secondary)', fontSize: 13, cursor: 'pointer',
                display: 'block', margin: '12px auto 0',
              }}>
                Zurück zum Login
              </button>
            </>
          )}
        </div>

        {/* Footer */}
        <div style={{ textAlign: 'center', marginTop: 20, fontSize: 11, color: 'var(--text-tertiary)' }}>
          2025 KOMPAGNON · <Link to="/" style={{ color: 'var(--text-tertiary)' }}>Startseite</Link>
        </div>
      </div>
    </div>
  );
}

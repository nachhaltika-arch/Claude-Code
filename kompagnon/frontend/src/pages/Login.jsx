import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import API_BASE_URL from '../config';

const NAVY = '#0F1E3A';
const AMBER = '#D4A017';

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
      setSuccess('Falls die E-Mail existiert, erhalten Sie in Kuerze einen Reset-Link.');
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
    width: '100%', padding: '11px 14px', border: '1.5px solid #d4d8e8', borderRadius: 8,
    fontSize: 15, fontFamily: 'inherit', boxSizing: 'border-box', outline: 'none',
  };
  const lbl = {
    display: 'block', fontSize: 12, fontWeight: 700, color: '#4a5a7a',
    marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.07em',
  };

  return (
    <div style={{ minHeight: '100vh', background: '#f0f2f8', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20, fontFamily: 'system-ui, sans-serif' }}>
      <div style={{ width: '100%', maxWidth: 420 }}>
        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <div onClick={() => navigate('/')} style={{ display: 'inline-flex', alignItems: 'center', gap: 10, cursor: 'pointer' }}>
            <div style={{ width: 44, height: 44, borderRadius: '50%', background: NAVY, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <span style={{ color: AMBER, fontWeight: 900, fontSize: 14 }}>HS</span>
            </div>
            <span style={{ fontSize: 22, fontWeight: 800, color: NAVY }}>KOMPAGNON</span>
          </div>
        </div>

        {/* Card */}
        <div style={{ background: '#fff', borderRadius: 16, padding: 32, boxShadow: '0 4px 24px rgba(15,30,58,0.10)' }}>

          {/* ── LOGIN ── */}
          {step === 'login' && (
            <>
              <h2 style={{ margin: '0 0 8px', fontSize: 22, fontWeight: 800, color: NAVY }}>Willkommen zurueck</h2>
              <p style={{ margin: '0 0 24px', color: '#4a5a7a', fontSize: 14 }}>Melden Sie sich in Ihrem Konto an</p>

              {/* OAuth */}
              {[
                { icon: 'G', label: 'Mit Google anmelden', bg: '#fff', border: '#d0d8e8', color: NAVY },
                { icon: '\uD83C\uDF4E', label: 'Mit Apple anmelden', bg: '#000', border: '#000', color: '#fff' },
                { icon: 'f', label: 'Mit Facebook anmelden', bg: '#1877F2', border: '#1877F2', color: '#fff' },
                { icon: '\uD83C\uDFE2', label: 'Mit SSO anmelden', bg: '#f0f2f8', border: '#d0d8e8', color: NAVY },
              ].map((btn) => (
                <button key={btn.label} style={{
                  width: '100%', padding: '11px 16px', marginBottom: 10, background: btn.bg, color: btn.color,
                  border: `1.5px solid ${btn.border}`, borderRadius: 8, fontSize: 14, fontWeight: 600, cursor: 'pointer',
                  display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10, fontFamily: 'inherit',
                }}>
                  <span style={{ fontWeight: 800 }}>{btn.icon}</span> {btn.label}
                </button>
              ))}

              {/* Divider */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 12, margin: '20px 0' }}>
                <div style={{ flex: 1, height: 1, background: '#e8eaf2' }} />
                <span style={{ fontSize: 13, color: '#64748b' }}>oder mit E-Mail</span>
                <div style={{ flex: 1, height: 1, background: '#e8eaf2' }} />
              </div>

              {error && <div style={{ background: '#fee2e2', color: '#c0392b', borderRadius: 8, padding: '10px 14px', fontSize: 13, marginBottom: 16 }}>{error}</div>}

              {/* Demo Accounts */}
              <div style={{ marginBottom: 24 }}>
                <div style={{ fontSize: 11, fontWeight: 700, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 10, textAlign: 'center' }}>
                  Demo-Zugaenge
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                  {[
                    { role: 'Admin', email: 'admin@kompagnon.de', password: 'Admin2025!', icon: '👑', color: '#0F1E3A', bg: '#f0f2f8', desc: 'Volle Rechte' },
                    { role: 'Auditor', email: 'auditor@kompagnon.de', password: 'Auditor2025!', icon: '🔍', color: '#1e40af', bg: '#eff6ff', desc: 'Audit-Zugang' },
                    { role: 'Nutzer', email: 'nutzer@kompagnon.de', password: 'Nutzer2025!', icon: '👤', color: '#0f766e', bg: '#f0fdfa', desc: 'Eingeschraenkt' },
                    { role: 'Kunde', email: 'kunde@kompagnon.de', password: 'Kunde2025!', icon: '🏢', color: '#7c3aed', bg: '#faf5ff', desc: 'Nur eigene Daten' },
                  ].map((d) => (
                    <button key={d.role} type="button" onClick={() => { setEmail(d.email); setPassword(d.password); }} style={{
                      display: 'flex', flexDirection: 'column', alignItems: 'flex-start', padding: '10px 12px',
                      background: d.bg, border: `1.5px solid ${d.color}20`, borderRadius: 10, cursor: 'pointer', textAlign: 'left', minHeight: 44,
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 2 }}>
                        <span style={{ fontSize: 14 }}>{d.icon}</span>
                        <span style={{ fontSize: 13, fontWeight: 700, color: d.color }}>{d.role}</span>
                      </div>
                      <span style={{ fontSize: 11, color: '#64748b' }}>{d.desc}</span>
                    </button>
                  ))}
                </div>
                <div style={{ textAlign: 'center', marginTop: 8, fontSize: 11, color: '#64748b' }}>Klick befuellt die Felder automatisch</div>
              </div>

              <form onSubmit={handleLogin}>
                <div style={{ marginBottom: 14 }}>
                  <label style={lbl}>E-Mail-Adresse</label>
                  <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="ihre@email.de" required style={inp} />
                </div>
                <div style={{ marginBottom: 8 }}>
                  <label style={lbl}>Passwort</label>
                  <div style={{ position: 'relative' }}>
                    <input type={showPassword ? 'text' : 'password'} value={password} onChange={(e) => setPassword(e.target.value)} placeholder="........" required style={{ ...inp, paddingRight: 44 }} />
                    <button type="button" onClick={() => setShowPassword(!showPassword)} style={{
                      position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)',
                      background: 'none', border: 'none', cursor: 'pointer', fontSize: 16, color: '#64748b', padding: 0,
                    }}>
                      {showPassword ? '\uD83D\uDE48' : '\uD83D\uDC41\uFE0F'}
                    </button>
                  </div>
                </div>
                <div style={{ textAlign: 'right', marginBottom: 20 }}>
                  <button type="button" onClick={() => setStep('forgot')} style={{ background: 'none', border: 'none', color: NAVY, fontSize: 13, cursor: 'pointer', textDecoration: 'underline', padding: 0 }}>
                    Passwort vergessen?
                  </button>
                </div>
                <button type="submit" disabled={loading} style={{
                  width: '100%', padding: '13px', background: loading ? '#64748b' : NAVY, color: '#fff',
                  border: 'none', borderRadius: 8, fontSize: 15, fontWeight: 700, cursor: loading ? 'not-allowed' : 'pointer', fontFamily: 'inherit', minHeight: 48,
                }}>
                  {loading ? 'Anmelden...' : 'Anmelden'}
                </button>
              </form>

              <div style={{ textAlign: 'center', marginTop: 20, fontSize: 14, color: '#4a5a7a' }}>
                Noch kein Konto?{' '}
                <Link to="/register" style={{ color: NAVY, fontWeight: 700, textDecoration: 'none' }}>Jetzt registrieren</Link>
              </div>
            </>
          )}

          {/* ── 2FA ── */}
          {step === '2fa' && (
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 40, marginBottom: 12 }}>🔐</div>
              <h2 style={{ margin: '0 0 8px', fontSize: 20, fontWeight: 800, color: NAVY }}>Zwei-Faktor-Authentifizierung</h2>
              <p style={{ margin: '0 0 28px', color: '#4a5a7a', fontSize: 14 }}>Geben Sie den 6-stelligen Code aus Ihrer Authenticator-App ein</p>

              {error && <div style={{ background: '#fee2e2', color: '#c0392b', borderRadius: 8, padding: '10px 14px', fontSize: 13, marginBottom: 16 }}>{error}</div>}

              <div style={{ display: 'flex', gap: 8, justifyContent: 'center', marginBottom: 24 }}>
                {totpCode.map((digit, i) => (
                  <input key={i} id={`totp-${i}`} type="text" inputMode="numeric" maxLength={1} value={digit}
                    onChange={(e) => handleTotpInput(i, e.target.value)} onKeyDown={(e) => handleTotpKeyDown(i, e)}
                    autoFocus={i === 0}
                    style={{
                      width: 44, height: 52, textAlign: 'center', fontSize: 22, fontWeight: 700,
                      border: `2px solid ${digit ? NAVY : '#d4d8e8'}`, borderRadius: 8, outline: 'none',
                      fontFamily: 'inherit', color: NAVY, marginRight: i === 2 ? 16 : 0,
                    }}
                  />
                ))}
              </div>

              <button onClick={handle2FA} disabled={loading || totpCode.join('').length !== 6} style={{
                width: '100%', padding: '13px', background: NAVY, color: '#fff', border: 'none', borderRadius: 8,
                fontSize: 15, fontWeight: 700, cursor: 'pointer', fontFamily: 'inherit', marginBottom: 12, minHeight: 48,
              }}>
                {loading ? 'Pruefen...' : 'Bestaetigen'}
              </button>
              <button onClick={() => { setStep('login'); setError(''); setTotpCode(['', '', '', '', '', '']); }} style={{
                background: 'none', border: 'none', color: '#4a5a7a', fontSize: 13, cursor: 'pointer', textDecoration: 'underline',
              }}>
                Zurueck zum Login
              </button>
            </div>
          )}

          {/* ── FORGOT ── */}
          {step === 'forgot' && (
            <>
              <h2 style={{ margin: '0 0 8px', fontSize: 20, fontWeight: 800, color: NAVY }}>Passwort zuruecksetzen</h2>
              <p style={{ margin: '0 0 24px', color: '#4a5a7a', fontSize: 14 }}>Wir senden Ihnen einen Reset-Link</p>

              {success ? (
                <div style={{ background: '#f0fff4', color: '#2a7a3a', borderRadius: 8, padding: 14, fontSize: 14, textAlign: 'center' }}>
                  {success}
                </div>
              ) : (
                <form onSubmit={handleForgot}>
                  <div style={{ marginBottom: 16 }}>
                    <label style={lbl}>E-Mail-Adresse</label>
                    <input type="email" value={forgotEmail} onChange={(e) => setForgotEmail(e.target.value)} placeholder="ihre@email.de" required style={inp} />
                  </div>
                  <button type="submit" disabled={loading} style={{
                    width: '100%', padding: '13px', background: NAVY, color: '#fff', border: 'none', borderRadius: 8,
                    fontSize: 15, fontWeight: 700, cursor: 'pointer', fontFamily: 'inherit', marginBottom: 12, minHeight: 48,
                  }}>
                    {loading ? 'Senden...' : 'Reset-Link senden'}
                  </button>
                </form>
              )}
              <button onClick={() => { setStep('login'); setSuccess(''); }} style={{
                background: 'none', border: 'none', color: '#4a5a7a', fontSize: 13, cursor: 'pointer',
                textDecoration: 'underline', display: 'block', margin: '12px auto 0',
              }}>
                Zurueck zum Login
              </button>
            </>
          )}
        </div>

        {/* Footer */}
        <div style={{ textAlign: 'center', marginTop: 20, fontSize: 12, color: '#64748b' }}>
          2025 KOMPAGNON · <Link to="/" style={{ color: '#64748b' }}>Startseite</Link>
        </div>
      </div>
    </div>
  );
}

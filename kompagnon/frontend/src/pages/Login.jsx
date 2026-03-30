import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import API_BASE_URL from '../config';

const NAVY = '#0F1E3A';
const ACCENT = '#C8102E';

export default function Login() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [step, setStep] = useState('login'); // login | 2fa | forgot
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPw, setShowPw] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  // 2FA
  const [tempToken, setTempToken] = useState('');
  const [totpCode, setTotpCode] = useState(['', '', '', '', '', '']);
  const totpRefs = Array.from({ length: 6 }, () => React.createRef());

  // Forgot
  const [forgotSent, setForgotSent] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Anmeldung fehlgeschlagen');

      if (data.require_2fa) {
        setTempToken(data.temp_token);
        setStep('2fa');
      } else {
        login(data.access_token, data.user);
        navigate('/');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handle2FA = async () => {
    setError('');
    setLoading(true);
    const code = totpCode.join('');
    try {
      const res = await fetch(`${API_BASE_URL}/api/auth/login/2fa`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ temp_token: tempToken, totp_code: code }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || '2FA fehlgeschlagen');
      login(data.access_token, data.user);
      navigate('/');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleForgot = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/auth/forgot-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || 'Fehler');
      }
      setForgotSent(true);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const onTotpChange = (i, val) => {
    if (val.length > 1) val = val.slice(-1);
    if (val && !/^\d$/.test(val)) return;
    const next = [...totpCode];
    next[i] = val;
    setTotpCode(next);
    if (val && i < 5) totpRefs[i + 1].current?.focus();
    if (next.every((c) => c) && next.join('').length === 6) {
      setTimeout(() => handle2FA(), 100);
    }
  };

  const onTotpKeyDown = (i, e) => {
    if (e.key === 'Backspace' && !totpCode[i] && i > 0) {
      totpRefs[i - 1].current?.focus();
    }
  };

  const cardStyle = {
    background: '#fff', borderRadius: 16, padding: '40px 36px',
    maxWidth: 420, width: '100%', boxShadow: '0 8px 40px rgba(0,0,0,0.08)',
  };
  const inputStyle = {
    width: '100%', padding: '12px 14px', border: '1.5px solid #d4d8e8',
    borderRadius: 8, fontSize: 16, boxSizing: 'border-box', outline: 'none',
  };
  const btnStyle = {
    width: '100%', padding: '13px', background: NAVY, color: '#fff',
    border: 'none', borderRadius: 8, fontSize: 16, fontWeight: 700,
    cursor: 'pointer', opacity: loading ? 0.6 : 1, minHeight: 48,
  };

  return (
    <div style={{
      minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center',
      background: `linear-gradient(135deg, ${NAVY} 0%, #1a3050 100%)`, padding: 20,
    }}>
      <div style={cardStyle}>
        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: 28 }}>
          <div style={{ fontSize: 28, fontWeight: 900, color: NAVY, letterSpacing: '-0.5px' }}>KOMPAGNON</div>
        </div>

        {step === 'login' && (
          <>
            <h2 style={{ textAlign: 'center', fontSize: 20, color: NAVY, marginBottom: 24, fontWeight: 600 }}>
              Willkommen zurueck
            </h2>
            <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              <div>
                <label style={{ fontSize: 13, fontWeight: 600, color: '#4a5a74', display: 'block', marginBottom: 6 }}>E-Mail-Adresse</label>
                <input style={inputStyle} type="email" value={email} onChange={(e) => setEmail(e.target.value)} required placeholder="name@firma.de" />
              </div>
              <div>
                <label style={{ fontSize: 13, fontWeight: 600, color: '#4a5a74', display: 'block', marginBottom: 6 }}>Passwort</label>
                <div style={{ position: 'relative' }}>
                  <input style={inputStyle} type={showPw ? 'text' : 'password'} value={password} onChange={(e) => setPassword(e.target.value)} required placeholder="Passwort eingeben" />
                  <button type="button" onClick={() => setShowPw(!showPw)} style={{
                    position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)',
                    background: 'none', border: 'none', cursor: 'pointer', fontSize: 18, color: '#8a9ab8',
                  }}>
                    {showPw ? '🙈' : '👁'}
                  </button>
                </div>
              </div>
              {error && <div style={{ color: ACCENT, fontSize: 13, fontWeight: 600 }}>{error}</div>}
              <button type="submit" disabled={loading} style={btnStyle}>
                {loading ? 'Wird angemeldet...' : 'Anmelden'}
              </button>
            </form>
            <div style={{ textAlign: 'center', marginTop: 20, fontSize: 13, color: '#6a7a9a' }}>
              <button onClick={() => setStep('forgot')} style={{ background: 'none', border: 'none', color: '#2a5aa0', cursor: 'pointer', fontSize: 13 }}>
                Passwort vergessen?
              </button>
              <div style={{ marginTop: 12 }}>
                Noch kein Konto? <Link to="/register" style={{ color: '#2a5aa0', fontWeight: 600, textDecoration: 'none' }}>Registrieren</Link>
              </div>
            </div>
          </>
        )}

        {step === '2fa' && (
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: 36, marginBottom: 12 }}>🔐</div>
            <h2 style={{ fontSize: 18, color: NAVY, marginBottom: 8 }}>Zwei-Faktor-Authentifizierung</h2>
            <p style={{ fontSize: 13, color: '#6a7a9a', marginBottom: 24 }}>
              Geben Sie den 6-stelligen Code aus Ihrer Authenticator-App ein
            </p>
            <div style={{ display: 'flex', gap: 8, justifyContent: 'center', marginBottom: 20 }}>
              {totpCode.map((digit, i) => (
                <input
                  key={i}
                  ref={totpRefs[i]}
                  value={digit}
                  onChange={(e) => onTotpChange(i, e.target.value)}
                  onKeyDown={(e) => onTotpKeyDown(i, e)}
                  style={{
                    width: 44, height: 52, textAlign: 'center', fontSize: 22, fontWeight: 700,
                    border: '2px solid #d4d8e8', borderRadius: 10, outline: 'none',
                  }}
                  maxLength={1}
                  inputMode="numeric"
                  autoFocus={i === 0}
                />
              ))}
            </div>
            {error && <div style={{ color: ACCENT, fontSize: 13, marginBottom: 12 }}>{error}</div>}
            <button onClick={handle2FA} disabled={loading} style={btnStyle}>
              {loading ? 'Wird geprueft...' : 'Code bestaetigen'}
            </button>
            <button onClick={() => { setStep('login'); setError(''); }} style={{ background: 'none', border: 'none', color: '#6a7a9a', marginTop: 16, cursor: 'pointer', fontSize: 13 }}>
              Zurueck zum Login
            </button>
          </div>
        )}

        {step === 'forgot' && (
          <div>
            <h2 style={{ textAlign: 'center', fontSize: 18, color: NAVY, marginBottom: 16 }}>Passwort zuruecksetzen</h2>
            {forgotSent ? (
              <div style={{ textAlign: 'center', color: '#2a9a5a', fontSize: 14 }}>
                Falls die E-Mail existiert, wurde ein Reset-Link gesendet.
                <br /><br />
                <button onClick={() => { setStep('login'); setForgotSent(false); }} style={{ background: 'none', border: 'none', color: '#2a5aa0', cursor: 'pointer', fontSize: 14 }}>
                  Zurueck zum Login
                </button>
              </div>
            ) : (
              <form onSubmit={handleForgot} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                <input style={inputStyle} type="email" value={email} onChange={(e) => setEmail(e.target.value)} required placeholder="E-Mail-Adresse" />
                {error && <div style={{ color: ACCENT, fontSize: 13 }}>{error}</div>}
                <button type="submit" disabled={loading} style={btnStyle}>Link senden</button>
                <button type="button" onClick={() => setStep('login')} style={{ background: 'none', border: 'none', color: '#6a7a9a', cursor: 'pointer', fontSize: 13 }}>
                  Zurueck zum Login
                </button>
              </form>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

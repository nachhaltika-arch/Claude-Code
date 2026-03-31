import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
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

  const DEMOS = [
    { role: 'Admin', email: 'admin@kompagnon.de', password: 'Admin2025!' },
    { role: 'Auditor', email: 'auditor@kompagnon.de', password: 'Auditor2025!' },
    { role: 'Nutzer', email: 'nutzer@kompagnon.de', password: 'Nutzer2025!' },
    { role: 'Kunde', email: 'kunde@kompagnon.de', password: 'Kunde2025!' },
  ];

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const res = await fetch(`${API_BASE_URL}/api/auth/login`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      const data = await res.json();
      if (!res.ok) { setError(data.detail || 'E-Mail oder Passwort falsch'); return; }
      if (data.require_2fa) { setTempToken(data.temp_token); setStep('2fa'); return; }
      login(data.access_token, data.user);
      navigate('/app/dashboard');
    } catch { setError('Verbindungsfehler'); }
    finally { setLoading(false); }
  };

  const handle2FA = async () => {
    const code = totp.join('');
    if (code.length !== 6) return;
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/auth/login/2fa`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ temp_token: tempToken, totp_code: code }),
      });
      const data = await res.json();
      if (!res.ok) { setError('Code ungültig'); setTotp(['','','','','','']); return; }
      login(data.access_token, data.user);
      navigate('/app/dashboard');
    } catch { setError('Fehler'); }
    finally { setLoading(false); }
  };

  const handleForgot = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await fetch(`${API_BASE_URL}/api/auth/forgot-password`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: forgotEmail }),
      });
      setSuccess('Falls diese E-Mail existiert, erhalten Sie einen Reset-Link.');
    } finally { setLoading(false); }
  };

  return (
    <div className="min-vh-100 bg-light d-flex align-items-center justify-content-center p-3">
      <div style={{ width: '100%', maxWidth: 420 }}>
        <h3 className="text-center fw-bold mb-4">KOMPAGNON</h3>

        <div className="card shadow">
          {/* LOGIN */}
          {step === 'login' && (
            <>
              <div className="card-header bg-dark text-white text-center py-3">
                <h5 className="mb-0"><i className="fas fa-lock me-2"></i>Anmelden</h5>
              </div>
              <div className="card-body p-4">
                {/* Demo buttons */}
                <p className="text-muted small text-center mb-2">Demo-Zugänge</p>
                <div className="row g-2 mb-3">
                  {DEMOS.map(d => (
                    <div className="col-6" key={d.role}>
                      <button className="btn btn-outline-secondary btn-sm w-100" onClick={() => { setEmail(d.email); setPassword(d.password); }}>
                        {d.role}
                      </button>
                    </div>
                  ))}
                </div>
                <hr />

                {error && <div className="alert alert-danger py-2 small">{error}</div>}

                <form onSubmit={handleLogin}>
                  <div className="form-floating mb-3">
                    <input type="email" className="form-control" id="loginEmail" placeholder="E-Mail" value={email} onChange={e => setEmail(e.target.value)} required />
                    <label htmlFor="loginEmail">E-Mail-Adresse</label>
                  </div>
                  <div className="form-floating mb-2">
                    <input type={showPw ? 'text' : 'password'} className="form-control" id="loginPw" placeholder="Passwort" value={password} onChange={e => setPassword(e.target.value)} required />
                    <label htmlFor="loginPw">Passwort</label>
                  </div>
                  <div className="form-check mb-3">
                    <input className="form-check-input" type="checkbox" id="showPw" checked={showPw} onChange={() => setShowPw(!showPw)} />
                    <label className="form-check-label small" htmlFor="showPw">Passwort anzeigen</label>
                  </div>
                  <div className="text-end mb-3">
                    <button type="button" className="btn btn-link btn-sm p-0 text-decoration-none" onClick={() => setStep('forgot')}>
                      Passwort vergessen?
                    </button>
                  </div>
                  <button type="submit" className="btn btn-primary w-100" disabled={loading}>
                    {loading ? <><span className="spinner-border spinner-border-sm me-2"></span>Anmelden...</> : <><i className="fas fa-right-to-bracket me-2"></i>Anmelden</>}
                  </button>
                </form>

                <p className="text-center mt-3 mb-0 small text-muted">
                  Kein Konto? <Link to="/register" className="text-decoration-none">Registrieren</Link>
                </p>
              </div>
            </>
          )}

          {/* 2FA */}
          {step === '2fa' && (
            <>
              <div className="card-header bg-dark text-white text-center py-3">
                <h5 className="mb-0"><i className="fas fa-shield-halved me-2"></i>Zwei-Faktor-Code</h5>
              </div>
              <div className="card-body p-4 text-center">
                <p className="text-muted small mb-3">6-stelligen Code aus Ihrer Authenticator-App eingeben</p>
                {error && <div className="alert alert-danger py-2 small">{error}</div>}
                <div className="d-flex gap-2 justify-content-center mb-3">
                  {totp.map((d, i) => (
                    <input key={i} id={`t${i}`} type="text" inputMode="numeric" maxLength={1} value={d}
                      className="form-control text-center fw-bold" style={{ width: 44, height: 48, fontSize: 20 }}
                      onChange={e => {
                        if (!/^\d*$/.test(e.target.value)) return;
                        const n = [...totp]; n[i] = e.target.value.slice(-1); setTotp(n);
                        if (e.target.value && i < 5) document.getElementById(`t${i+1}`)?.focus();
                        if (n.every(x => x) && n.join('').length === 6) setTimeout(handle2FA, 100);
                      }}
                      onKeyDown={e => { if (e.key === 'Backspace' && !d && i > 0) document.getElementById(`t${i-1}`)?.focus(); }}
                    />
                  ))}
                </div>
                <button className="btn btn-primary w-100 mb-2" onClick={handle2FA} disabled={loading || totp.join('').length !== 6}>
                  {loading ? 'Prüfen...' : 'Bestätigen'}
                </button>
                <button className="btn btn-link btn-sm text-muted" onClick={() => { setStep('login'); setError(''); setTotp(['','','','','','']); }}>
                  ← Zurück
                </button>
              </div>
            </>
          )}

          {/* FORGOT */}
          {step === 'forgot' && (
            <>
              <div className="card-header bg-dark text-white text-center py-3">
                <h5 className="mb-0">Passwort zurücksetzen</h5>
              </div>
              <div className="card-body p-4">
                {success ? (
                  <div className="alert alert-success small">{success}</div>
                ) : (
                  <form onSubmit={handleForgot}>
                    <div className="form-floating mb-3">
                      <input type="email" className="form-control" id="forgotEmail" placeholder="E-Mail" value={forgotEmail} onChange={e => setForgotEmail(e.target.value)} required />
                      <label htmlFor="forgotEmail">E-Mail-Adresse</label>
                    </div>
                    <button type="submit" className="btn btn-primary w-100" disabled={loading}>
                      {loading ? 'Senden...' : 'Reset-Link senden'}
                    </button>
                  </form>
                )}
                <div className="text-center mt-3">
                  <button className="btn btn-link btn-sm text-muted" onClick={() => { setStep('login'); setSuccess(''); }}>
                    ← Zurück zum Login
                  </button>
                </div>
              </div>
            </>
          )}
        </div>

        <p className="text-center mt-3 text-muted small">© 2026 KOMPAGNON</p>
      </div>
    </div>
  );
}

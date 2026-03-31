import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useScreenSize } from '../utils/responsive';
import API_BASE_URL from '../config';


const AMBER = '#D4A017';

export default function Register() {
  const navigate = useNavigate();
  const { isMobile } = useScreenSize();
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [passwordConfirm, setPasswordConfirm] = useState('');
  const [agb, setAgb] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const handleRegister = async (e) => {
    e.preventDefault();
    setError('');
    if (password !== passwordConfirm) { setError('Passwoerter stimmen nicht ueberein'); return; }
    if (password.length < 8) { setError('Passwort muss mindestens 8 Zeichen haben'); return; }
    if (!agb) { setError('Bitte akzeptieren Sie die AGB'); return; }

    setLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, first_name: firstName, last_name: lastName }),
      });
      const data = await res.json();
      if (!res.ok) { setError(data.detail || 'Registrierung fehlgeschlagen'); return; }
      setSuccess(true);
    } catch { setError('Verbindungsfehler. Bitte erneut versuchen.'); }
    finally { setLoading(false); }
  };

  const inp = {
    width: '100%', padding: '11px 14px', border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)',
    fontSize: 15, fontFamily: 'var(--font-sans)', boxSizing: 'border-box', outline: 'none',
  };
  const lbl = {
    display: 'block', fontSize: 12, fontWeight: 700, color: 'var(--text-secondary)',
    marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.07em',
  };

  // Success screen
  if (success) {
    return (
      <div style={{ minHeight: '100vh', background: 'var(--bg-app)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20, fontFamily: 'var(--font-sans)' }}>
        <div style={{ width: '100%', maxWidth: 420 }}>
          <div style={{ textAlign: 'center', marginBottom: 32 }}>
            <div onClick={() => navigate('/')} style={{ display: 'inline-flex', alignItems: 'center', gap: 10, cursor: 'pointer' }}>
              <div style={{ width: 44, height: 44, borderRadius: '50%', background: 'var(--brand-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <span style={{ color: AMBER, fontWeight: 900, fontSize: 14 }}>HS</span>
              </div>
              <span style={{ fontSize: 22, fontWeight: 800, color: 'var(--text-primary)' }}>KOMPAGNON</span>
            </div>
          </div>
          <div style={{ background: 'var(--bg-surface)', borderRadius: 'var(--radius-xl)', padding: 32, boxShadow: '0 4px 24px rgba(15,30,58,0.10)', textAlign: 'center' }}>
            <div style={{ fontSize: 48, marginBottom: 16 }}>🎉</div>
            <h2 style={{ color: 'var(--text-primary)', marginBottom: 8, fontSize: 22, fontWeight: 800 }}>Konto erstellt!</h2>
            <p style={{ color: 'var(--text-secondary)', marginBottom: 24, fontSize: 14 }}>
              Ihr Konto wurde erfolgreich angelegt. Sie koennen sich jetzt anmelden.
            </p>
            <button onClick={() => navigate('/login')} style={{
              width: '100%', background: 'var(--brand-primary)', color: '#fff', border: 'none', borderRadius: 'var(--radius-md)',
              padding: '13px 28px', fontSize: 15, fontWeight: 700, cursor: 'pointer', minHeight: 48,
            }}>
              Jetzt anmelden
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg-app)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20, fontFamily: 'var(--font-sans)' }}>
      <div style={{ width: '100%', maxWidth: 420 }}>
        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <div onClick={() => navigate('/')} style={{ display: 'inline-flex', alignItems: 'center', gap: 10, cursor: 'pointer' }}>
            <div style={{ width: 44, height: 44, borderRadius: '50%', background: 'var(--brand-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <span style={{ color: AMBER, fontWeight: 900, fontSize: 14 }}>HS</span>
            </div>
            <span style={{ fontSize: 22, fontWeight: 800, color: 'var(--text-primary)' }}>KOMPAGNON</span>
          </div>
        </div>

        {/* Card */}
        <div style={{ background: 'var(--bg-surface)', borderRadius: 'var(--radius-xl)', padding: 32, boxShadow: '0 4px 24px rgba(15,30,58,0.10)' }}>
          <h2 style={{ margin: '0 0 8px', fontSize: 22, fontWeight: 800, color: 'var(--text-primary)' }}>Konto erstellen</h2>
          <p style={{ margin: '0 0 24px', color: 'var(--text-secondary)', fontSize: 14 }}>Starten Sie mit KOMPAGNON</p>

          {/* OAuth */}
          {[
            { icon: 'G', label: 'Mit Google registrieren', bg: '#fff', border: '#d0d8e8', color: 'var(--text-primary)' },
            { icon: '\uD83C\uDF4E', label: 'Mit Apple registrieren', bg: '#000', border: '#000', color: '#fff' },
            { icon: 'f', label: 'Mit Facebook registrieren', bg: '#1877F2', border: '#1877F2', color: '#fff' },
          ].map((btn) => (
            <button key={btn.label} style={{
              width: '100%', padding: '11px 16px', marginBottom: 10, background: btn.bg, color: btn.color,
              border: `1.5px solid ${btn.border}`, borderRadius: 'var(--radius-md)', fontSize: 14, fontWeight: 600, cursor: 'pointer',
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10, fontFamily: 'var(--font-sans)',
            }}>
              <span style={{ fontWeight: 800 }}>{btn.icon}</span> {btn.label}
            </button>
          ))}

          {/* Divider */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, margin: '20px 0' }}>
            <div style={{ flex: 1, height: 1, background: '#e8eaf2' }} />
            <span style={{ fontSize: 13, color: 'var(--text-tertiary)' }}>oder mit E-Mail</span>
            <div style={{ flex: 1, height: 1, background: '#e8eaf2' }} />
          </div>

          {error && <div style={{ background: 'var(--status-danger-bg)', color: 'var(--status-danger-text)', borderRadius: 'var(--radius-md)', padding: '10px 14px', fontSize: 13, marginBottom: 16 }}>{error}</div>}

          <form onSubmit={handleRegister}>
            <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr', gap: 12, marginBottom: 14 }}>
              <div>
                <label style={lbl}>Vorname</label>
                <input value={firstName} onChange={(e) => setFirstName(e.target.value)} placeholder="Max" style={inp} />
              </div>
              <div>
                <label style={lbl}>Nachname</label>
                <input value={lastName} onChange={(e) => setLastName(e.target.value)} placeholder="Mustermann" style={inp} />
              </div>
            </div>
            <div style={{ marginBottom: 14 }}>
              <label style={lbl}>E-Mail-Adresse</label>
              <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="ihre@email.de" required style={inp} />
            </div>
            <div style={{ marginBottom: 14 }}>
              <label style={lbl}>Passwort (min. 8 Zeichen)</label>
              <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Sicheres Passwort" required style={inp} />
            </div>
            <div style={{ marginBottom: 14 }}>
              <label style={lbl}>Passwort wiederholen</label>
              <input type="password" value={passwordConfirm} onChange={(e) => setPasswordConfirm(e.target.value)} placeholder="Passwort bestaetigen" required style={inp} />
            </div>

            <label style={{ display: 'flex', alignItems: 'flex-start', gap: 8, fontSize: 13, color: '#4a5a74', cursor: 'pointer', marginBottom: 20 }}>
              <input type="checkbox" checked={agb} onChange={(e) => setAgb(e.target.checked)} style={{ marginTop: 2 }} />
              <span>Ich akzeptiere die AGB und Datenschutzrichtlinie</span>
            </label>

            <button type="submit" disabled={loading} style={{
              width: '100%', padding: '13px', background: loading ? '#64748b' : 'var(--brand-primary)', color: '#fff',
              border: 'none', borderRadius: 'var(--radius-md)', fontSize: 15, fontWeight: 700, cursor: loading ? 'not-allowed' : 'pointer',
              fontFamily: 'var(--font-sans)', minHeight: 48,
            }}>
              {loading ? 'Wird erstellt...' : 'Konto erstellen'}
            </button>
          </form>

          <div style={{ textAlign: 'center', marginTop: 20, fontSize: 14, color: 'var(--text-secondary)' }}>
            Bereits ein Konto?{' '}
            <Link to="/login" style={{ color: 'var(--text-primary)', fontWeight: 700, textDecoration: 'none' }}>Anmelden</Link>
          </div>
        </div>

        {/* Footer */}
        <div style={{ textAlign: 'center', marginTop: 20, fontSize: 12, color: 'var(--text-tertiary)' }}>
          2025 KOMPAGNON · <Link to="/" style={{ color: 'var(--text-tertiary)' }}>Startseite</Link>
        </div>
      </div>
    </div>
  );
}

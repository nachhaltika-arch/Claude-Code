import React, { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import API_BASE_URL from '../config';
import PasswordStrength, { isPasswordStrong } from '../components/PasswordStrength';



export default function ResetPassword() {
  const nav = useNavigate();
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [showPw, setShowPw] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const handleReset = async (e) => {
    e.preventDefault();
    setError('');
    if (!isPasswordStrong(password)) {
      setError('Passwort zu schwach — bitte alle Anforderungen erfuellen');
      return;
    }
    if (password !== confirm) { setError('Passwoerter stimmen nicht ueberein'); return; }
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/auth/reset-password`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token, new_password: password }),
      });
      const data = await res.json();
      if (!res.ok) { setError(data.detail || 'Fehler'); return; }
      setSuccess(true);
    } catch { setError('Verbindungsfehler.'); }
    finally { setLoading(false); }
  };

  if (!token) {
    return (
      <div style={{ minHeight: '100vh', background: 'var(--bg-app)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20, fontFamily: 'var(--font-sans)' }}>
        <div style={{ background: 'var(--bg-surface)', borderRadius: 'var(--radius-xl)', padding: 40, maxWidth: 400, width: '100%', textAlign: 'center', boxShadow: '0 4px 24px rgba(15,30,58,0.10)' }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>❌</div>
          <h2 style={{ color: 'var(--text-primary)', marginBottom: 8, fontSize: 20, fontWeight: 800 }}>Ungueltiger Link</h2>
          <p style={{ color: 'var(--text-tertiary)', fontSize: 14, marginBottom: 24 }}>Bitte fordern Sie einen neuen Reset-Link an.</p>
          <button onClick={() => nav('/login')} style={{ background: 'var(--brand-primary)', color: '#fff', border: 'none', borderRadius: 'var(--radius-md)', padding: '12px 24px', fontSize: 14, fontWeight: 700, cursor: 'pointer', minHeight: 44 }}>Zum Login</button>
        </div>
      </div>
    );
  }

  const inp = { width: '100%', padding: '11px 14px', border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)', fontSize: 15, boxSizing: 'border-box', outline: 'none', fontFamily: 'var(--font-sans)' };

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg-app)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20, fontFamily: 'var(--font-sans)' }}>
      <div style={{ width: '100%', maxWidth: 420 }}>
        <div style={{ textAlign: 'center', marginBottom: 28, cursor: 'pointer' }} onClick={() => nav('/')}>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: 10 }}>
            <div style={{ width: 40, height: 40, borderRadius: '50%', background: 'var(--brand-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <span style={{ color: '#D4A017', fontWeight: 900, fontSize: 13 }}>HS</span>
            </div>
            <span style={{ fontSize: 20, fontWeight: 800, color: 'var(--text-primary)' }}>KOMPAGNON</span>
          </div>
        </div>
        <div style={{ background: 'var(--bg-surface)', borderRadius: 'var(--radius-xl)', padding: 32, boxShadow: '0 4px 24px rgba(15,30,58,0.10)' }}>
          {success ? (
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 52, marginBottom: 16 }}>✅</div>
              <h2 style={{ fontSize: 20, fontWeight: 800, color: 'var(--text-primary)', marginBottom: 8 }}>Passwort geaendert!</h2>
              <p style={{ fontSize: 14, color: 'var(--text-tertiary)', marginBottom: 24, lineHeight: 1.5 }}>Sie koennen sich jetzt einloggen.</p>
              <button onClick={() => nav('/login')} style={{ width: '100%', padding: 12, background: 'var(--brand-primary)', color: '#fff', border: 'none', borderRadius: 'var(--radius-md)', fontSize: 15, fontWeight: 700, cursor: 'pointer', minHeight: 48 }}>Zum Login</button>
            </div>
          ) : (
            <>
              <h2 style={{ fontSize: 22, fontWeight: 800, color: 'var(--text-primary)', margin: '0 0 8px' }}>Neues Passwort</h2>
              <p style={{ fontSize: 14, color: 'var(--text-tertiary)', margin: '0 0 24px' }}>Vergeben Sie ein neues sicheres Passwort.</p>
              {error && <div style={{ background: 'var(--status-danger-bg)', color: 'var(--status-danger-text)', borderRadius: 'var(--radius-md)', padding: '10px 14px', fontSize: 13, marginBottom: 16 }}>{error}</div>}
              <form onSubmit={handleReset}>
                <div style={{ marginBottom: 14 }}>
                  <label style={{ display: 'block', fontSize: 12, fontWeight: 700, color: 'var(--text-tertiary)', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.07em' }}>Neues Passwort</label>
                  <div style={{ position: 'relative' }}>
                    <input type={showPw ? 'text' : 'password'} value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Sicheres Passwort" required style={{ ...inp, paddingRight: 44 }} />
                    <button type="button" onClick={() => setShowPw(!showPw)} style={{ position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', cursor: 'pointer', fontSize: 16, color: 'var(--text-tertiary)', padding: 0 }}>
                      {showPw ? '🙈' : '👁️'}
                    </button>
                  </div>
                  <PasswordStrength password={password} />
                </div>
                <div style={{ marginBottom: 24 }}>
                  <label style={{ display: 'block', fontSize: 12, fontWeight: 700, color: 'var(--text-tertiary)', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.07em' }}>Passwort bestaetigen</label>
                  <input type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)} placeholder="Passwort wiederholen" required
                    style={{ ...inp, borderColor: confirm && confirm !== password ? '#fca5a5' : confirm && confirm === password ? '#86efac' : '#d4d8e8' }} />
                  {confirm && confirm === password && <div style={{ fontSize: 12, color: '#059669', marginTop: 4 }}>Passwoerter stimmen ueberein</div>}
                </div>
                <button type="submit" disabled={loading} style={{ width: '100%', padding: 13, background: loading ? '#64748b' : 'var(--brand-primary)', color: '#fff', border: 'none', borderRadius: 'var(--radius-md)', fontSize: 15, fontWeight: 700, cursor: loading ? 'not-allowed' : 'pointer', minHeight: 48 }}>
                  {loading ? 'Wird gespeichert...' : 'Passwort speichern'}
                </button>
              </form>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

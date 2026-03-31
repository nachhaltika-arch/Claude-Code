import React, { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import API_BASE_URL from '../config';

const N = '#0F1E3A';

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
    if (password.length < 8) { setError('Passwort muss mindestens 8 Zeichen haben'); return; }
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
      <div style={{ minHeight: '100vh', background: '#f0f2f8', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20, fontFamily: 'system-ui, sans-serif' }}>
        <div style={{ background: '#fff', borderRadius: 16, padding: 40, maxWidth: 400, width: '100%', textAlign: 'center', boxShadow: '0 4px 24px rgba(15,30,58,0.10)' }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>❌</div>
          <h2 style={{ color: N, marginBottom: 8, fontSize: 20, fontWeight: 800 }}>Ungueltiger Link</h2>
          <p style={{ color: '#64748b', fontSize: 14, marginBottom: 24 }}>Bitte fordern Sie einen neuen Reset-Link an.</p>
          <button onClick={() => nav('/login')} style={{ background: N, color: '#fff', border: 'none', borderRadius: 8, padding: '12px 24px', fontSize: 14, fontWeight: 700, cursor: 'pointer', minHeight: 44 }}>Zum Login</button>
        </div>
      </div>
    );
  }

  const inp = { width: '100%', padding: '11px 14px', border: '1.5px solid #d4d8e8', borderRadius: 8, fontSize: 15, boxSizing: 'border-box', outline: 'none', fontFamily: 'inherit' };

  return (
    <div style={{ minHeight: '100vh', background: '#f0f2f8', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20, fontFamily: 'system-ui, sans-serif' }}>
      <div style={{ width: '100%', maxWidth: 420 }}>
        <div style={{ textAlign: 'center', marginBottom: 28, cursor: 'pointer' }} onClick={() => nav('/')}>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: 10 }}>
            <div style={{ width: 40, height: 40, borderRadius: '50%', background: N, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <span style={{ color: '#D4A017', fontWeight: 900, fontSize: 13 }}>HS</span>
            </div>
            <span style={{ fontSize: 20, fontWeight: 800, color: N }}>KOMPAGNON</span>
          </div>
        </div>
        <div style={{ background: '#fff', borderRadius: 16, padding: 32, boxShadow: '0 4px 24px rgba(15,30,58,0.10)' }}>
          {success ? (
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 52, marginBottom: 16 }}>✅</div>
              <h2 style={{ fontSize: 20, fontWeight: 800, color: N, marginBottom: 8 }}>Passwort geaendert!</h2>
              <p style={{ fontSize: 14, color: '#64748b', marginBottom: 24, lineHeight: 1.5 }}>Sie koennen sich jetzt einloggen.</p>
              <button onClick={() => nav('/login')} style={{ width: '100%', padding: 12, background: N, color: '#fff', border: 'none', borderRadius: 8, fontSize: 15, fontWeight: 700, cursor: 'pointer', minHeight: 48 }}>Zum Login</button>
            </div>
          ) : (
            <>
              <h2 style={{ fontSize: 22, fontWeight: 800, color: N, margin: '0 0 8px' }}>Neues Passwort</h2>
              <p style={{ fontSize: 14, color: '#64748b', margin: '0 0 24px' }}>Vergeben Sie ein neues sicheres Passwort.</p>
              {error && <div style={{ background: '#fee2e2', color: '#c0392b', borderRadius: 8, padding: '10px 14px', fontSize: 13, marginBottom: 16 }}>{error}</div>}
              <form onSubmit={handleReset}>
                <div style={{ marginBottom: 14 }}>
                  <label style={{ display: 'block', fontSize: 12, fontWeight: 700, color: '#64748b', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.07em' }}>Neues Passwort</label>
                  <div style={{ position: 'relative' }}>
                    <input type={showPw ? 'text' : 'password'} value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Min. 8 Zeichen" required style={{ ...inp, paddingRight: 44 }} />
                    <button type="button" onClick={() => setShowPw(!showPw)} style={{ position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', cursor: 'pointer', fontSize: 16, color: '#64748b', padding: 0 }}>
                      {showPw ? '🙈' : '👁️'}
                    </button>
                  </div>
                  {password && (
                    <div style={{ marginTop: 6, display: 'flex', gap: 4 }}>
                      {[1, 2, 3, 4].map((i) => (
                        <div key={i} style={{ flex: 1, height: 3, borderRadius: 2, background: password.length >= i * 4 ? (i <= 1 ? '#dc2626' : i <= 2 ? '#d97706' : i <= 3 ? '#2563eb' : '#059669') : '#e2e8f0' }} />
                      ))}
                    </div>
                  )}
                </div>
                <div style={{ marginBottom: 24 }}>
                  <label style={{ display: 'block', fontSize: 12, fontWeight: 700, color: '#64748b', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.07em' }}>Passwort bestaetigen</label>
                  <input type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)} placeholder="Passwort wiederholen" required
                    style={{ ...inp, borderColor: confirm && confirm !== password ? '#fca5a5' : confirm && confirm === password ? '#86efac' : '#d4d8e8' }} />
                  {confirm && confirm === password && <div style={{ fontSize: 12, color: '#059669', marginTop: 4 }}>Passwoerter stimmen ueberein</div>}
                </div>
                <button type="submit" disabled={loading} style={{ width: '100%', padding: 13, background: loading ? '#64748b' : N, color: '#fff', border: 'none', borderRadius: 8, fontSize: 15, fontWeight: 700, cursor: loading ? 'not-allowed' : 'pointer', minHeight: 48 }}>
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

import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import API_BASE_URL from '../config';

const NAVY = '#0F1E3A';
const ACCENT = '#C8102E';

export default function Register() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ first_name: '', last_name: '', email: '', password: '', password2: '' });
  const [agreed, setAgreed] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    if (form.password !== form.password2) { setError('Passwoerter stimmen nicht ueberein'); return; }
    if (form.password.length < 8) { setError('Passwort muss mindestens 8 Zeichen haben'); return; }
    if (!agreed) { setError('Bitte AGB akzeptieren'); return; }

    setLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: form.email, password: form.password, first_name: form.first_name, last_name: form.last_name }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Registrierung fehlgeschlagen');
      setSuccess(true);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
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
      <div style={{ background: '#fff', borderRadius: 16, padding: '40px 36px', maxWidth: 420, width: '100%', boxShadow: '0 8px 40px rgba(0,0,0,0.08)' }}>
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          <div style={{ fontSize: 28, fontWeight: 900, color: NAVY }}>KOMPAGNON</div>
          <h2 style={{ fontSize: 20, color: NAVY, marginTop: 12, fontWeight: 600 }}>Konto erstellen</h2>
        </div>

        {success ? (
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: 48, marginBottom: 16 }}>✅</div>
            <p style={{ fontSize: 15, color: '#2a9a5a', fontWeight: 600 }}>Konto erfolgreich erstellt!</p>
            <p style={{ fontSize: 13, color: '#6a7a9a', marginTop: 8 }}>Sie koennen sich jetzt anmelden.</p>
            <button onClick={() => navigate('/login')} style={{ ...btnStyle, marginTop: 20 }}>Zum Login</button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <div>
                <label style={{ fontSize: 13, fontWeight: 600, color: '#4a5a74', display: 'block', marginBottom: 4 }}>Vorname</label>
                <input style={inputStyle} value={form.first_name} onChange={set('first_name')} placeholder="Max" />
              </div>
              <div>
                <label style={{ fontSize: 13, fontWeight: 600, color: '#4a5a74', display: 'block', marginBottom: 4 }}>Nachname</label>
                <input style={inputStyle} value={form.last_name} onChange={set('last_name')} placeholder="Mustermann" />
              </div>
            </div>
            <div>
              <label style={{ fontSize: 13, fontWeight: 600, color: '#4a5a74', display: 'block', marginBottom: 4 }}>E-Mail-Adresse</label>
              <input style={inputStyle} type="email" value={form.email} onChange={set('email')} required placeholder="name@firma.de" />
            </div>
            <div>
              <label style={{ fontSize: 13, fontWeight: 600, color: '#4a5a74', display: 'block', marginBottom: 4 }}>Passwort (min. 8 Zeichen)</label>
              <input style={inputStyle} type="password" value={form.password} onChange={set('password')} required placeholder="Sicheres Passwort" />
            </div>
            <div>
              <label style={{ fontSize: 13, fontWeight: 600, color: '#4a5a74', display: 'block', marginBottom: 4 }}>Passwort wiederholen</label>
              <input style={inputStyle} type="password" value={form.password2} onChange={set('password2')} required placeholder="Passwort bestaetigen" />
            </div>
            <label style={{ display: 'flex', alignItems: 'flex-start', gap: 8, fontSize: 13, color: '#4a5a74', cursor: 'pointer' }}>
              <input type="checkbox" checked={agreed} onChange={(e) => setAgreed(e.target.checked)} style={{ marginTop: 2 }} />
              <span>Ich akzeptiere die AGB und Datenschutzrichtlinie</span>
            </label>
            {error && <div style={{ color: ACCENT, fontSize: 13, fontWeight: 600 }}>{error}</div>}
            <button type="submit" disabled={loading} style={btnStyle}>
              {loading ? 'Wird erstellt...' : 'Konto erstellen'}
            </button>
            <div style={{ textAlign: 'center', fontSize: 13, color: '#6a7a9a' }}>
              Bereits ein Konto? <Link to="/login" style={{ color: '#2a5aa0', fontWeight: 600, textDecoration: 'none' }}>Anmelden</Link>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}

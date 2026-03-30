import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { useAuth, apiCall } from '../context/AuthContext';
import { useScreenSize } from '../utils/responsive';

const NAVY = '#0F1E3A';

export default function Profile() {
  const { user, logout } = useAuth();
  const { isMobile } = useScreenSize();
  const navigate = useNavigate();
  const [tab, setTab] = useState('profil');
  const [form, setForm] = useState({ first_name: '', last_name: '', phone: '', position: '' });
  const [pwForm, setPwForm] = useState({ current_password: '', new_password: '', new_password2: '' });
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (user) setForm({ first_name: user.first_name || '', last_name: user.last_name || '', phone: user.phone || '', position: user.position || '' });
  }, [user]);

  const saveProfile = async () => {
    setSaving(true);
    try {
      const res = await apiCall('/api/auth/me', { method: 'PATCH', body: JSON.stringify(form) });
      if (res.ok) toast.success('Profil gespeichert');
      else throw new Error((await res.json()).detail);
    } catch (e) { toast.error(e.message); }
    finally { setSaving(false); }
  };

  const changePassword = async (e) => {
    e.preventDefault();
    if (pwForm.new_password !== pwForm.new_password2) { toast.error('Passwoerter stimmen nicht ueberein'); return; }
    setSaving(true);
    try {
      const res = await apiCall('/api/auth/change-password', {
        method: 'POST',
        body: JSON.stringify({ current_password: pwForm.current_password, new_password: pwForm.new_password }),
      });
      if (res.ok) { toast.success('Passwort geaendert'); setPwForm({ current_password: '', new_password: '', new_password2: '' }); }
      else throw new Error((await res.json()).detail);
    } catch (e) { toast.error(e.message); }
    finally { setSaving(false); }
  };

  const inputStyle = { width: '100%', padding: '10px 12px', border: '1.5px solid #d4d8e8', borderRadius: 8, fontSize: 16, boxSizing: 'border-box' };
  const tabs = [{ key: 'profil', label: 'Profil' }, { key: 'sicherheit', label: 'Sicherheit' }];
  if (user?.role === 'admin' || user?.role === 'auditor') tabs.splice(1, 0, { key: 'unterschrift', label: 'Unterschrift' });

  return (
    <div style={{ maxWidth: 700, margin: '0 auto' }}>
      <h1 style={{ fontSize: 22, fontWeight: 800, color: NAVY, marginBottom: 20 }}>Mein Profil</h1>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 4, marginBottom: 24, borderBottom: '2px solid #eef0f8' }}>
        {tabs.map((t) => (
          <button key={t.key} onClick={() => setTab(t.key)} style={{
            padding: '10px 20px', background: 'none', border: 'none', borderBottom: tab === t.key ? `3px solid ${NAVY}` : '3px solid transparent',
            color: tab === t.key ? NAVY : '#5a6878', fontWeight: 700, fontSize: 14, cursor: 'pointer', marginBottom: -2,
          }}>
            {t.label}
          </button>
        ))}
      </div>

      {tab === 'profil' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr', gap: 12 }}>
            <Field label="Vorname" value={form.first_name} onChange={(v) => setForm((f) => ({ ...f, first_name: v }))} />
            <Field label="Nachname" value={form.last_name} onChange={(v) => setForm((f) => ({ ...f, last_name: v }))} />
          </div>
          <Field label="E-Mail" value={user?.email || ''} disabled />
          <Field label="Telefon" value={form.phone} onChange={(v) => setForm((f) => ({ ...f, phone: v }))} />
          {(user?.role === 'admin' || user?.role === 'auditor') && (
            <Field label="Position" value={form.position} onChange={(v) => setForm((f) => ({ ...f, position: v }))} placeholder="z.B. Senior Auditor" />
          )}
          <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
            <button onClick={saveProfile} disabled={saving} style={{ background: NAVY, color: '#fff', border: 'none', borderRadius: 8, padding: '10px 24px', fontSize: 14, fontWeight: 700, cursor: 'pointer', minHeight: 44 }}>
              {saving ? 'Speichern...' : 'Profil speichern'}
            </button>
          </div>
          <div style={{ background: '#f8f9fc', borderRadius: 8, padding: 16, marginTop: 16 }}>
            <div style={{ fontSize: 12, color: '#5a6878', marginBottom: 4 }}>Rolle</div>
            <div style={{ fontSize: 14, fontWeight: 700, color: NAVY, textTransform: 'capitalize' }}>{user?.role}</div>
          </div>
        </div>
      )}

      {tab === 'unterschrift' && <SignatureTab />}

      {tab === 'sicherheit' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
          <div>
            <h3 style={{ fontSize: 16, color: NAVY, marginBottom: 12 }}>Passwort aendern</h3>
            <form onSubmit={changePassword} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <Field label="Aktuelles Passwort" type="password" value={pwForm.current_password} onChange={(v) => setPwForm((f) => ({ ...f, current_password: v }))} />
              <Field label="Neues Passwort" type="password" value={pwForm.new_password} onChange={(v) => setPwForm((f) => ({ ...f, new_password: v }))} />
              <Field label="Neues Passwort wiederholen" type="password" value={pwForm.new_password2} onChange={(v) => setPwForm((f) => ({ ...f, new_password2: v }))} />
              <button type="submit" disabled={saving} style={{ background: NAVY, color: '#fff', border: 'none', borderRadius: 8, padding: '10px 20px', fontSize: 14, fontWeight: 700, cursor: 'pointer', alignSelf: 'flex-start', minHeight: 44 }}>
                Passwort aendern
              </button>
            </form>
          </div>
          <div>
            <h3 style={{ fontSize: 16, color: NAVY, marginBottom: 12 }}>Zwei-Faktor-Authentifizierung</h3>
            <div style={{ fontSize: 14, color: user?.totp_enabled ? '#2a9a5a' : '#c03030', fontWeight: 600, marginBottom: 12 }}>
              {user?.totp_enabled ? '2FA ist aktiviert' : '2FA ist nicht aktiviert'}
            </div>
            <button onClick={() => navigate('/app/2fa-setup')} style={{ background: '#f0f2f8', color: NAVY, border: 'none', borderRadius: 8, padding: '10px 20px', fontSize: 14, fontWeight: 700, cursor: 'pointer', minHeight: 44 }}>
              {user?.totp_enabled ? '2FA verwalten' : '2FA einrichten'}
            </button>
          </div>
          <div>
            <button onClick={() => { logout(); navigate('/'); }} style={{ background: '#fdecea', color: '#c03030', border: 'none', borderRadius: 8, padding: '10px 20px', fontSize: 14, fontWeight: 700, cursor: 'pointer', minHeight: 44 }}>
              Abmelden
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function Field({ label, value, onChange, disabled, type = 'text', placeholder = '' }) {
  return (
    <div>
      <label style={{ fontSize: 12, fontWeight: 600, color: '#5a6878', display: 'block', marginBottom: 4 }}>{label}</label>
      <input
        type={type} value={value} placeholder={placeholder}
        onChange={onChange ? (e) => onChange(e.target.value) : undefined}
        disabled={disabled}
        style={{ width: '100%', padding: '10px 12px', border: '1.5px solid #d4d8e8', borderRadius: 8, fontSize: 16, boxSizing: 'border-box', opacity: disabled ? 0.5 : 1 }}
      />
    </div>
  );
}

function SignatureTab() {
  const canvasRef = useRef(null);
  const [drawing, setDrawing] = useState(false);
  const [saved, setSaved] = useState(false);

  const getPos = (e) => {
    const rect = canvasRef.current.getBoundingClientRect();
    const touch = e.touches ? e.touches[0] : e;
    return { x: touch.clientX - rect.left, y: touch.clientY - rect.top };
  };

  const startDraw = (e) => {
    e.preventDefault();
    setDrawing(true);
    const ctx = canvasRef.current.getContext('2d');
    const { x, y } = getPos(e);
    ctx.beginPath();
    ctx.moveTo(x, y);
  };

  const draw = (e) => {
    if (!drawing) return;
    e.preventDefault();
    const ctx = canvasRef.current.getContext('2d');
    const { x, y } = getPos(e);
    ctx.lineWidth = 2;
    ctx.strokeStyle = '#000';
    ctx.lineCap = 'round';
    ctx.lineTo(x, y);
    ctx.stroke();
  };

  const stopDraw = () => setDrawing(false);

  const clear = () => {
    const ctx = canvasRef.current.getContext('2d');
    ctx.clearRect(0, 0, 400, 150);
    ctx.fillStyle = '#fff';
    ctx.fillRect(0, 0, 400, 150);
    setSaved(false);
  };

  const save = async () => {
    const dataURL = canvasRef.current.toDataURL('image/png');
    try {
      const res = await apiCall('/api/auth/me/signature', {
        method: 'POST', body: JSON.stringify({ signature_data: dataURL }),
      });
      if (res.ok) { toast.success('Unterschrift gespeichert'); setSaved(true); }
      else throw new Error((await res.json()).detail);
    } catch (e) { toast.error(e.message); }
  };

  useEffect(() => {
    if (canvasRef.current) {
      const ctx = canvasRef.current.getContext('2d');
      ctx.fillStyle = '#fff';
      ctx.fillRect(0, 0, 400, 150);
    }
  }, []);

  return (
    <div>
      <h3 style={{ fontSize: 16, color: '#0F1E3A', marginBottom: 12 }}>Digitale Unterschrift</h3>
      <p style={{ fontSize: 13, color: '#4a5a7a', marginBottom: 16 }}>
        Zeichnen Sie Ihre Unterschrift fuer Audit-Berichte:
      </p>
      <canvas
        ref={canvasRef} width={400} height={150}
        style={{ border: '1.5px solid #d4d8e8', borderRadius: 8, cursor: 'crosshair', touchAction: 'none', maxWidth: '100%' }}
        onMouseDown={startDraw} onMouseMove={draw} onMouseUp={stopDraw} onMouseLeave={stopDraw}
        onTouchStart={startDraw} onTouchMove={draw} onTouchEnd={stopDraw}
      />
      <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
        <button onClick={clear} style={{ background: '#f0f2f8', color: '#0F1E3A', border: 'none', borderRadius: 8, padding: '10px 20px', fontSize: 14, fontWeight: 700, cursor: 'pointer', minHeight: 44 }}>
          Loeschen
        </button>
        <button onClick={save} style={{ background: '#0F1E3A', color: '#fff', border: 'none', borderRadius: 8, padding: '10px 20px', fontSize: 14, fontWeight: 700, cursor: 'pointer', minHeight: 44 }}>
          Unterschrift speichern
        </button>
      </div>
      {saved && <div style={{ color: '#2a9a5a', fontSize: 13, marginTop: 8, fontWeight: 600 }}>Gespeichert!</div>}
    </div>
  );
}

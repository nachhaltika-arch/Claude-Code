import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { useAuth, apiCall } from '../context/AuthContext';
import { useScreenSize } from '../utils/responsive';



export default function Settings({ tab }) {
  if (tab === 'security') return <SecurityTab />;
  if (tab === 'system') return <SystemTab />;
  if (tab === 'notifications') return <NotificationsTab />;
  if (tab === 'subscription') return <SubscriptionTab />;
  return <ProfileTab />;
}

// ── Profile ──
function ProfileTab() {
  const { user } = useAuth();
  const { isMobile } = useScreenSize();
  const [form, setForm] = useState({ first_name: '', last_name: '', phone: '', position: '' });
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (user) setForm({ first_name: user.first_name || '', last_name: user.last_name || '', phone: user.phone || '', position: user.position || '' });
  }, [user]);

  const save = async () => {
    setSaving(true);
    try {
      const res = await apiCall('/api/auth/me', { method: 'PATCH', body: JSON.stringify(form) });
      if (res.ok) toast.success('Profil gespeichert');
      else toast.error((await res.json()).detail || 'Fehler');
    } catch (e) { toast.error(e.message); }
    finally { setSaving(false); }
  };

  return (
    <Card title="Profil-Einstellungen" icon="👤">
      <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr', gap: 14 }}>
        <Field label="Vorname" value={form.first_name} onChange={(v) => setForm((f) => ({ ...f, first_name: v }))} />
        <Field label="Nachname" value={form.last_name} onChange={(v) => setForm((f) => ({ ...f, last_name: v }))} />
      </div>
      <Field label="E-Mail" value={user?.email || ''} disabled />
      <Field label="Telefon" value={form.phone} onChange={(v) => setForm((f) => ({ ...f, phone: v }))} />
      {(user?.role === 'admin' || user?.role === 'auditor') && (
        <Field label="Position" value={form.position} onChange={(v) => setForm((f) => ({ ...f, position: v }))} placeholder="z.B. Senior Auditor" />
      )}
      <Btn onClick={save} loading={saving}>Aenderungen speichern</Btn>
      {(user?.role === 'admin' || user?.role === 'auditor') && <SignatureSection />}
    </Card>
  );
}

function SignatureSection() {
  const canvasRef = useRef(null);
  const [drawing, setDrawing] = useState(false);

  const getPos = (e) => {
    const rect = canvasRef.current.getBoundingClientRect();
    const t = e.touches ? e.touches[0] : e;
    return { x: t.clientX - rect.left, y: t.clientY - rect.top };
  };
  const start = (e) => { e.preventDefault(); setDrawing(true); const ctx = canvasRef.current.getContext('2d'); const { x, y } = getPos(e); ctx.beginPath(); ctx.moveTo(x, y); };
  const draw = (e) => { if (!drawing) return; e.preventDefault(); const ctx = canvasRef.current.getContext('2d'); const { x, y } = getPos(e); ctx.lineWidth = 2; ctx.strokeStyle = '#000'; ctx.lineCap = 'round'; ctx.lineTo(x, y); ctx.stroke(); };
  const stop = () => setDrawing(false);
  const clear = () => { const ctx = canvasRef.current.getContext('2d'); ctx.clearRect(0, 0, 400, 150); ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, 400, 150); };
  const save = async () => {
    const url = canvasRef.current.toDataURL('image/png');
    const res = await apiCall('/api/auth/me/signature', { method: 'POST', body: JSON.stringify({ signature_data: url }) });
    if (res.ok) toast.success('Unterschrift gespeichert');
    else toast.error('Fehler');
  };

  useEffect(() => { if (canvasRef.current) { const ctx = canvasRef.current.getContext('2d'); ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, 400, 150); } }, []);

  return (
    <div style={{ marginTop: 24, paddingTop: 24, borderTop: '1px solid var(--border-light)' }}>
      <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 12 }}>Digitale Unterschrift</div>
      <canvas ref={canvasRef} width={400} height={150} style={{ border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)', cursor: 'crosshair', touchAction: 'none', maxWidth: '100%' }}
        onMouseDown={start} onMouseMove={draw} onMouseUp={stop} onMouseLeave={stop}
        onTouchStart={start} onTouchMove={draw} onTouchEnd={stop} />
      <div style={{ display: 'flex', gap: 8, marginTop: 10 }}>
        <Btn onClick={clear} secondary>Loeschen</Btn>
        <Btn onClick={save}>Speichern</Btn>
      </div>
    </div>
  );
}

// ── Security ──
function SecurityTab() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [pw, setPw] = useState({ current_password: '', new_password: '', confirm: '' });
  const [saving, setSaving] = useState(false);

  const changePw = async (e) => {
    e.preventDefault();
    if (pw.new_password !== pw.confirm) { toast.error('Passwoerter stimmen nicht ueberein'); return; }
    setSaving(true);
    try {
      const res = await apiCall('/api/auth/change-password', { method: 'POST', body: JSON.stringify({ current_password: pw.current_password, new_password: pw.new_password }) });
      if (res.ok) { toast.success('Passwort geaendert'); setPw({ current_password: '', new_password: '', confirm: '' }); }
      else toast.error((await res.json()).detail || 'Fehler');
    } finally { setSaving(false); }
  };

  return (
    <>
      <Card title="Passwort aendern" icon="🔑">
        <form onSubmit={changePw} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <Field label="Aktuelles Passwort" type="password" value={pw.current_password} onChange={(v) => setPw((f) => ({ ...f, current_password: v }))} />
          <Field label="Neues Passwort" type="password" value={pw.new_password} onChange={(v) => setPw((f) => ({ ...f, new_password: v }))} />
          <Field label="Passwort bestaetigen" type="password" value={pw.confirm} onChange={(v) => setPw((f) => ({ ...f, confirm: v }))} />
          <Btn type="submit" loading={saving}>Passwort aendern</Btn>
        </form>
      </Card>
      <Card title="Zwei-Faktor-Authentifizierung" icon="🔐">
        <div style={{ fontSize: 14, color: user?.totp_enabled ? '#2a9a5a' : '#c03030', fontWeight: 600, marginBottom: 12 }}>
          Status: {user?.totp_enabled ? 'Aktiv' : 'Inaktiv'}
        </div>
        <Btn onClick={() => navigate('/app/2fa-setup')} secondary>{user?.totp_enabled ? '2FA verwalten' : '2FA einrichten'}</Btn>
      </Card>
      <Card title="Konto" icon="⚠️">
        <Btn onClick={() => { logout(); navigate('/'); }} danger>Abmelden</Btn>
      </Card>
    </>
  );
}

// ── System (admin) ──
function SystemTab() {
  const [settings, setSettings] = useState({});
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    apiCall('/api/admin/settings').then((r) => r.json()).then(setSettings).catch(() => {});
  }, []);

  const save = async () => {
    setSaving(true);
    try {
      const res = await apiCall('/api/admin/settings', { method: 'PATCH', body: JSON.stringify({ settings }) });
      if (res.ok) toast.success('Gespeichert');
      else toast.error('Fehler');
    } finally { setSaving(false); }
  };

  const set = (key) => (v) => setSettings((s) => ({ ...s, [key]: v }));

  return (
    <Card title="Systemeinstellungen" icon="🏢">
      <Field label="Firmenname" value={settings.company_name || ''} onChange={set('company_name')} placeholder="KOMPAGNON" />
      <Field label="Website" value={settings.company_website || ''} onChange={set('company_website')} placeholder="kompagnon.de" />
      <Field label="Auditor-Name im PDF" value={settings.pdf_auditor_name || ''} onChange={set('pdf_auditor_name')} placeholder="KOMPAGNON Communications" />
      <Field label="PDF-Footer-Text" value={settings.pdf_footer_text || ''} onChange={set('pdf_footer_text')} placeholder="Dieses Audit ersetzt keine Rechtsberatung." />
      <div style={{ marginTop: 8 }}>
        <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-secondary)', marginBottom: 6 }}>Freie Registrierung</div>
        <div style={{ display: 'flex', gap: 16 }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 14, cursor: 'pointer' }}>
            <input type="radio" checked={settings.registration_mode !== 'invite_only'} onChange={() => set('registration_mode')('open')} /> Erlaubt
          </label>
          <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 14, cursor: 'pointer' }}>
            <input type="radio" checked={settings.registration_mode === 'invite_only'} onChange={() => set('registration_mode')('invite_only')} /> Nur per Einladung
          </label>
        </div>
      </div>
      <Btn onClick={save} loading={saving} style={{ marginTop: 16 }}>Einstellungen speichern</Btn>
    </Card>
  );
}

// ── Notifications ──
function NotificationsTab() {
  const { user } = useAuth();
  const [prefs, setPrefs] = useState({ new_lead: true, audit_done: true, project_status: true, daily_report: false, review_reminder: true, weekly_report: false });
  const [smtp, setSmtp] = useState({ host: '', port: '', user: '', password: '', from_name: '', from_email: '' });

  const toggle = (key) => setPrefs((p) => ({ ...p, [key]: !p[key] }));

  return (
    <>
      <Card title="E-Mail Benachrichtigungen" icon="📧">
        {[
          ['new_lead', 'Neuer Lead eingegangen'],
          ['audit_done', 'Audit abgeschlossen'],
          ['project_status', 'Projekt-Status geaendert'],
          ['daily_report', 'Taeglicher Zusammenfassungsreport'],
          ['review_reminder', 'Bewertungs-Erinnerung'],
          ['weekly_report', 'Woechentlicher Report'],
        ].map(([key, label]) => (
          <label key={key} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '8px 0', cursor: 'pointer', fontSize: 14, borderBottom: '1px solid #f0f2f8' }}>
            <input type="checkbox" checked={prefs[key]} onChange={() => toggle(key)} />
            {label}
          </label>
        ))}
        <Btn onClick={() => toast.success('Gespeichert')} style={{ marginTop: 12 }}>Speichern</Btn>
      </Card>
      {user?.role === 'admin' && (
        <Card title="SMTP-Einstellungen" icon="⚙️">
          <Field label="SMTP Host" value={smtp.host} onChange={(v) => setSmtp((s) => ({ ...s, host: v }))} placeholder="smtp.example.com" />
          <Field label="SMTP Port" value={smtp.port} onChange={(v) => setSmtp((s) => ({ ...s, port: v }))} placeholder="587" />
          <Field label="Benutzername" value={smtp.user} onChange={(v) => setSmtp((s) => ({ ...s, user: v }))} />
          <Field label="Passwort" type="password" value={smtp.password} onChange={(v) => setSmtp((s) => ({ ...s, password: v }))} />
          <Field label="Absender-Name" value={smtp.from_name} onChange={(v) => setSmtp((s) => ({ ...s, from_name: v }))} placeholder="KOMPAGNON" />
          <Field label="Absender-E-Mail" value={smtp.from_email} onChange={(v) => setSmtp((s) => ({ ...s, from_email: v }))} placeholder="noreply@kompagnon.de" />
          <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
            <Btn onClick={() => apiCall('/api/admin/settings/test-email', { method: 'POST' }).then(() => toast.success('Test-Mail gesendet'))} secondary>Test-E-Mail senden</Btn>
            <Btn onClick={() => toast.success('Gespeichert')}>Speichern</Btn>
          </div>
        </Card>
      )}
    </>
  );
}

// ── Subscription ──
function SubscriptionTab() {
  return (
    <>
      <Card title="Aktueller Plan" icon="💳">
        <div style={{ background: '#f0f4ff', borderRadius: 10, padding: 20, marginBottom: 16 }}>
          <div style={{ fontSize: 11, color: 'var(--text-secondary)', textTransform: 'uppercase', marginBottom: 4 }}>Aktueller Plan</div>
          <div style={{ fontSize: 22, fontWeight: 800, color: 'var(--text-primary)' }}>Professional</div>
          <div style={{ fontSize: 14, color: 'var(--text-secondary)', marginTop: 4 }}>99 Euro / Monat</div>
        </div>
        <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 4 }}>Nutzung diesen Monat:</div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: 14 }}>
          <div>Audits: 12 / unbegrenzt</div>
          <div>Nutzer: 3 / 10</div>
          <div>Leads: 145 / unbegrenzt</div>
        </div>
      </Card>
      <Card title="Rechnungen" icon="📄">
        {['Maerz 2026 — 99 Euro', 'Februar 2026 — 99 Euro', 'Januar 2026 — 99 Euro'].map((inv, i) => (
          <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid #f0f2f8', fontSize: 14 }}>
            <span>{inv}</span>
            <button style={{ background: 'none', border: 'none', color: 'var(--text-primary)', fontWeight: 700, fontSize: 13, cursor: 'pointer' }}>PDF</button>
          </div>
        ))}
      </Card>
    </>
  );
}

// ── Shared Components ──
function Card({ title, icon, children }) {
  return (
    <div style={{ background: 'var(--bg-surface)', borderRadius: 'var(--radius-lg)', border: '1px solid var(--border-light)', padding: 24, marginBottom: 16 }}>
      {title && <h3 style={{ margin: '0 0 16px', fontSize: 16, fontWeight: 700, color: 'var(--text-primary)' }}>{icon} {title}</h3>}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>{children}</div>
    </div>
  );
}

function Field({ label, value, onChange, disabled, type = 'text', placeholder = '' }) {
  return (
    <div>
      <label style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-secondary)', display: 'block', marginBottom: 4 }}>{label}</label>
      <input type={type} value={value} placeholder={placeholder} onChange={onChange ? (e) => onChange(e.target.value) : undefined} disabled={disabled}
        style={{ width: '100%', padding: '10px 12px', border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)', fontSize: 16, boxSizing: 'border-box', opacity: disabled ? 0.5 : 1 }} />
    </div>
  );
}

function Btn({ children, onClick, type = 'button', loading, secondary, danger, style: extraStyle }) {
  const bg = danger ? '#fdecea' : secondary ? '#f0f2f8' : 'var(--brand-primary)';
  const fg = danger ? '#c03030' : secondary ? 'var(--brand-primary)' : '#fff';
  return (
    <button type={type} onClick={onClick} disabled={loading} style={{
      background: bg, color: fg, border: 'none', borderRadius: 'var(--radius-md)', padding: '10px 20px',
      fontSize: 14, fontWeight: 700, cursor: loading ? 'not-allowed' : 'pointer', minHeight: 44,
      opacity: loading ? 0.6 : 1, ...extraStyle,
    }}>
      {loading ? 'Speichern...' : children}
    </button>
  );
}

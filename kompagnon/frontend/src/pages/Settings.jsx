import React, { useState, useEffect, useRef } from 'react';
import MeldungsVorlieben from '../components/einstellungen/MeldungsVorlieben';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { useAuth, apiCall } from '../context/AuthContext';
import { useVersand } from '../context/VersandContext';
import { reportApiError } from '../utils/apiRequest';
import { useScreenSize } from '../utils/responsive';
import Feld from '../components/ui/Feld';
import SeitenTitel from '../components/ui/SeitenTitel';



export default function Settings({ tab }) {
  return (
    <div style={{ width: '100%', minWidth: 0, overflowX: 'hidden' }}>
      {tab === 'security' ? <SecurityTab /> : tab === 'system' ? <SystemTab /> : tab === 'notifications' ? <NotificationsTab /> : tab === 'subscription' ? <SubscriptionTab /> : <ProfileTab />}
    </div>
  );
}

// ── Profile ──
function ProfileTab() {
  const { user, hasRole } = useAuth();
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
      if (res.ok) toast.success('Profildaten gespeichert');
      else { const d = await res.json().catch(() => ({})); toast.error(d.detail || 'Profil konnte nicht gespeichert werden'); }
    } catch (e) { toast.error(e.message); }
    finally { setSaving(false); }
  };

  return (
    <Card title="Profil-Einstellungen" icon="👤">
      <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr', gap: 14, minWidth: 0, width: '100%' }}>
        <Field label="Vorname" value={form.first_name} onChange={(v) => setForm((f) => ({ ...f, first_name: v }))} />
        <Field label="Nachname" value={form.last_name} onChange={(v) => setForm((f) => ({ ...f, last_name: v }))} />
      </div>
      <Field label="E-Mail" value={user?.email || ''} disabled />
      <Field label="Telefon" value={form.phone} onChange={(v) => setForm((f) => ({ ...f, phone: v }))} />
      {(hasRole('admin') || hasRole('auditor')) && (
        <Field label="Position" value={form.position} onChange={(v) => setForm((f) => ({ ...f, position: v }))} placeholder="z.B. Senior Auditor" />
      )}
      <Btn onClick={save} loading={saving}>Aenderungen speichern</Btn>
      {(hasRole('admin') || hasRole('auditor')) && <SignatureSection />}
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
    else toast.error('Aktion fehlgeschlagen — bitte erneut versuchen');
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
    if (pw.new_password !== pw.confirm) { toast.error('Die beiden Passwörter stimmen nicht überein'); return; }
    setSaving(true);
    try {
      const res = await apiCall('/api/auth/change-password', { method: 'POST', body: JSON.stringify({ current_password: pw.current_password, new_password: pw.new_password }) });
      if (res.ok) { toast.success('Passwort erfolgreich geändert'); setPw({ current_password: '', new_password: '', confirm: '' }); }
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
    apiCall('/api/admin/settings')
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then(setSettings)
      .catch((error) => reportApiError(error, 'Systemeinstellungen'));
  }, []);

  const save = async () => {
    setSaving(true);
    try {
      const res = await apiCall('/api/admin/settings', { method: 'PATCH', body: JSON.stringify({ settings }) });
      if (res.ok) toast.success('Einstellungen gespeichert');
      else toast.error('Aktion fehlgeschlagen — bitte erneut versuchen');
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

// ── Not-Aus für automatischen Mailversand ──
//
// Am 17.08.2026 verschickte ein täglicher Job vier Monate lang Erinnerungen an
// Firmen, die nie Kunde waren — und es gab keinen Weg, ihn anzuhalten außer
// einem Eingriff in die Datenbank. Dieser Schalter ist das, was gefehlt hat.
function VersandSchalter() {
  const { erlaubt, laedt, umschalten } = useVersand();
  const [schaltet, setSchaltet] = useState(false);

  const klick = async () => {
    if (schaltet || laedt) return;
    const ziel = !erlaubt;
    setSchaltet(true);
    try {
      const jetzt = await umschalten(ziel);
      toast.success(jetzt
        ? 'Automatischer Versand ist eingeschaltet'
        : 'Automatischer Versand ist abgeschaltet');
    } catch (fehler) {
      toast.error(`Schalter nicht umgelegt: ${fehler.message}`);
    } finally {
      setSchaltet(false);
    }
  };

  const an = erlaubt === true;
  const unbekannt = erlaubt === null;

  return (
    <Card title="Automatischer E-Mail-Versand" icon="🛑">
      <div style={{ display: 'flex', alignItems: 'center', gap: 14, padding: '4px 0' }}>
        <button
          type="button" onClick={klick} disabled={laedt || schaltet || unbekannt}
          role="switch" aria-checked={an}
          aria-label="Automatischen E-Mail-Versand umschalten"
          style={{
            width: 52, height: 28, borderRadius: 14, flexShrink: 0,
            border: '1px solid var(--border-medium)',
            background: an ? 'var(--status-success-text)' : 'var(--bg-app)',
            cursor: (laedt || schaltet || unbekannt) ? 'not-allowed' : 'pointer',
            opacity: (laedt || schaltet) ? 0.6 : 1,
            position: 'relative', transition: 'background 0.15s', padding: 0,
          }}
        >
          <span style={{
            position: 'absolute', top: 2, left: an ? 26 : 2,
            width: 22, height: 22, borderRadius: '50%',
            background: '#fff', boxShadow: 'var(--shadow-sm)',
            transition: 'left 0.15s',
          }} />
        </button>
        <div>
          <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>
            {laedt ? 'Wird geladen…'
              : unbekannt ? 'Zustand unbekannt'
              : an ? 'Eingeschaltet' : 'Abgeschaltet'}
          </div>
          <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 2 }}>
            {an
              ? 'Erinnerungen, E-Mail-Strecken und Berichte gehen automatisch raus.'
              : 'Kein Job verschickt von sich aus E-Mails. Wirkt sofort.'}
          </div>
        </div>
      </div>

      <div style={{
        marginTop: 14, padding: '10px 12px', background: 'var(--bg-app)',
        borderRadius: 'var(--radius-md)', fontSize: 12,
        color: 'var(--text-secondary)', lineHeight: 1.6,
      }}>
        <strong style={{ color: 'var(--text-primary)' }}>Was der Schalter nicht sperrt:</strong>{' '}
        Mails, die jemand selbst ausgelöst hat — Passwort zurücksetzen, Anmeldung,
        die Bestätigung aus dem Analyse-Widget. Diese dürfen nie an einem Schalter
        hängen, den jemand vergessen hat.
      </div>
    </Card>
  );
}

// ── Notifications ──
function NotificationsTab() {
  const { hasRole, token } = useAuth();
  const [testEmail, setTestEmail] = useState('');
  const [testResult, setTestResult] = useState(null);

  const sendTest = async () => {
    setTestResult(null);
    const r = await apiCall(
      `/api/automations/test-email?recipient=${encodeURIComponent(testEmail)}`,
      { method: 'POST' }
    );
    setTestResult(r.ok ? 'success' : 'error');
  };

  return (
    <>
      {hasRole('admin') && <VersandSchalter />}
      <Card title="Benachrichtigungen" icon="🔔">
        <MeldungsVorlieben token={token} />
      </Card>
      {hasRole('admin') && (
        <Card title="E-Mail-Versand" icon="⚙️">
          <p style={{ fontSize: 14, lineHeight: 1.6, color: 'var(--text-secondary)', margin: '0 0 4px' }}>
            Der Versand läuft über <strong>Brevo</strong>; Zugang und
            Absenderadresse stehen als Umgebungsvariablen in Render und
            gehören dorthin — ein Passwortfeld im Browser wäre ein zweiter
            Ort für dasselbe Geheimnis.
          </p>
          <p style={{ fontSize: 13, lineHeight: 1.6, color: 'var(--text-tertiary)', margin: '0 0 4px' }}>
            Hier stand bis zum 26.08.2026 ein vollständiges SMTP-Formular samt
            Passwortfeld mit einem „Speichern"-Knopf, der nichts sendete und
            trotzdem Erfolg meldete. Ein getipptes Passwort war danach
            verworfen.
          </p>
          <div style={{ marginTop: 20 }}>
            <label style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-secondary)', display: 'block', marginBottom: 4 }}>SMTP Test-E-Mail</label>
            <div style={{ display: 'flex', gap: 8 }}>
              <input
                type="email"
                value={testEmail}
                onChange={e => setTestEmail(e.target.value)}
                placeholder="empfaenger@email.de"
                style={{ flex: 1, padding: '10px 12px', border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)', fontSize: 16, boxSizing: 'border-box' }}
              />
              <Btn onClick={sendTest}>Test senden</Btn>
            </div>
            {testResult === 'success' && (
              <div style={{ color: '#1D9E75', fontSize: 12, marginTop: 6 }}>
                ✓ Test-E-Mail gesendet — bitte Posteingang prüfen
              </div>
            )}
            {testResult === 'error' && (
              <div style={{ color: '#E24B4A', fontSize: 12, marginTop: 6 }}>
                ✗ Versand fehlgeschlagen — SMTP-Konfiguration prüfen
              </div>
            )}
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
      {title && <h2 style={{ margin: '0 0 16px', fontSize: 16, fontWeight: 700, color: 'var(--text-primary)' }}>{icon} {title}</h2>}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>{children}</div>
    </div>
  );
}

// Beschriftung und Feld waren Geschwister ohne `htmlFor`; der Name kam aus
// dem Platzhalter statt aus der Beschriftung, die danebenstand (L-17).
function Field({ label, value, onChange, disabled, type = 'text', placeholder = '' }) {
  return (
    <Feld label={label} labelStyle={{ fontSize: 12, fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'none', letterSpacing: 0 }}>
      <input
        type={type} value={value} placeholder={placeholder}
        onChange={onChange ? (e) => onChange(e.target.value) : undefined}
        disabled={disabled}
        style={{ width: '100%', padding: '10px 12px', border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)', fontSize: 14, background: disabled ? 'var(--bg-app)' : 'var(--bg-surface)', color: 'var(--text-primary)', boxSizing: 'border-box' }}
      />
    </Feld>
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
      <SeitenTitel>Einstellungen</SeitenTitel>
      {loading ? 'Speichern...' : children}
    </button>
  );
}

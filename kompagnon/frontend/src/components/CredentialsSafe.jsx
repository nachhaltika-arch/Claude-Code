import { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import API_BASE_URL from '../config';

export default function CredentialsSafe({ projectId, token }) {
  const [creds, setCreds] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState({ label: '', username: '', password: '', url: '', notes: '' });
  const [saving, setSaving] = useState(false);
  const [visiblePw, setVisiblePw] = useState({});

  const h = { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) };

  const load = () =>
    fetch(`${API_BASE_URL}/api/projects/${projectId}/credentials`, { headers: h })
      .then(r => r.ok ? r.json() : [])
      .then(d => setCreds(Array.isArray(d) ? d : []))
      .catch(() => {})
      .finally(() => setLoading(false));

  useEffect(() => { load(); }, [projectId]); // eslint-disable-line

  const add = async () => {
    if (!form.label.trim()) { toast.error('Bezeichnung erforderlich'); return; }
    setSaving(true);
    try {
      const r = await fetch(`${API_BASE_URL}/api/projects/${projectId}/credentials`, { method: 'POST', headers: h, body: JSON.stringify(form) });
      if (r.ok) { toast.success('Zugangsdaten gespeichert'); setShowAdd(false); setForm({ label: '', username: '', password: '', url: '', notes: '' }); load(); }
      else toast.error((await r.json()).detail || 'Fehler');
    } catch { toast.error('Speichern fehlgeschlagen'); }
    setSaving(false);
  };

  const del = async (credId) => {
    if (!window.confirm('Zugangsdaten loeschen?')) return;
    await fetch(`${API_BASE_URL}/api/projects/${projectId}/credentials/${credId}`, { method: 'DELETE', headers: h });
    setCreds(prev => prev.filter(c => c.id !== credId));
    toast.success('Geloescht');
  };

  const inputS = { width: '100%', padding: '8px 12px', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)', fontSize: 13, fontFamily: 'var(--font-sans)', background: 'var(--bg-surface)', color: 'var(--text-primary)', boxSizing: 'border-box' };
  const labelS = { fontSize: 12, fontWeight: 500, color: 'var(--text-secondary)', display: 'block', marginBottom: 4 };

  if (loading) return <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-tertiary)', fontSize: 13 }}>Laden...</div>;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>Zugangsdaten-Safe</div>
        <button onClick={() => setShowAdd(true)} style={{ padding: '6px 14px', border: 'none', borderRadius: 'var(--radius-md)', background: 'var(--brand-primary)', color: '#fff', fontSize: 12, fontWeight: 600, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>+ Zugangsdaten</button>
      </div>
      <div style={{ fontSize: 12, color: 'var(--text-tertiary)', background: 'var(--bg-app)', borderRadius: 'var(--radius-md)', padding: '8px 12px' }}>
        Alle Passwoerter werden verschluesselt gespeichert (Fernet / AES-256).
      </div>

      {creds.length === 0 ? (
        <div style={{ padding: 32, textAlign: 'center', color: 'var(--text-tertiary)', fontSize: 13, border: '2px dashed var(--border-light)', borderRadius: 8 }}>Noch keine Zugangsdaten hinterlegt.</div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {creds.map(c => (
            <div key={c.id} style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)', padding: '14px 16px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>{c.label}</span>
                <button onClick={() => del(c.id)} style={{ background: 'none', border: 'none', color: 'var(--text-tertiary)', cursor: 'pointer', fontSize: 14 }} title="Loeschen">&#128465;</button>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px 16px', fontSize: 12 }}>
                {c.username && <div><span style={{ color: 'var(--text-tertiary)' }}>Benutzer:</span> <span style={{ color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>{c.username}</span></div>}
                {c.password && <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <span style={{ color: 'var(--text-tertiary)' }}>Passwort:</span>
                  <span style={{ color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>{visiblePw[c.id] ? c.password : '\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022'}</span>
                  <button onClick={() => setVisiblePw(p => ({ ...p, [c.id]: !p[c.id] }))} style={{ background: 'none', border: 'none', color: 'var(--brand-primary)', cursor: 'pointer', fontSize: 11, padding: 0 }}>{visiblePw[c.id] ? 'Verbergen' : 'Anzeigen'}</button>
                </div>}
                {c.url && <div style={{ gridColumn: '1 / -1' }}><span style={{ color: 'var(--text-tertiary)' }}>URL:</span> <a href={c.url} target="_blank" rel="noopener noreferrer" style={{ color: 'var(--brand-primary)', fontSize: 12 }}>{c.url}</a></div>}
                {c.notes && <div style={{ gridColumn: '1 / -1', color: 'var(--text-secondary)', fontStyle: 'italic' }}>{c.notes}</div>}
              </div>
            </div>
          ))}
        </div>
      )}

      {showAdd && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', zIndex: 9999, display: 'flex', alignItems: 'center', justifyContent: 'center' }} onClick={e => e.target === e.currentTarget && setShowAdd(false)}>
          <div style={{ background: 'var(--bg-surface)', borderRadius: 12, padding: 28, width: '100%', maxWidth: 440, display: 'flex', flexDirection: 'column', gap: 12 }}>
            <h3 style={{ fontSize: 16, fontWeight: 600, color: 'var(--text-primary)', margin: 0 }}>Zugangsdaten hinzufuegen</h3>
            <div><label style={labelS}>Bezeichnung</label><input style={inputS} value={form.label} onChange={e => setForm(f => ({ ...f, label: e.target.value }))} placeholder="z.B. IONOS Hosting, WordPress Admin" /></div>
            <div><label style={labelS}>Benutzername</label><input style={inputS} value={form.username} onChange={e => setForm(f => ({ ...f, username: e.target.value }))} /></div>
            <div><label style={labelS}>Passwort</label><input style={inputS} type="password" value={form.password} onChange={e => setForm(f => ({ ...f, password: e.target.value }))} /></div>
            <div><label style={labelS}>URL</label><input style={inputS} value={form.url} onChange={e => setForm(f => ({ ...f, url: e.target.value }))} placeholder="https://..." /></div>
            <div><label style={labelS}>Notizen</label><textarea style={{ ...inputS, minHeight: 50, resize: 'vertical' }} value={form.notes} onChange={e => setForm(f => ({ ...f, notes: e.target.value }))} /></div>
            <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
              <button onClick={() => setShowAdd(false)} style={{ padding: '6px 14px', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)', background: 'var(--bg-surface)', color: 'var(--text-secondary)', fontSize: 12, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>Abbrechen</button>
              <button onClick={add} disabled={saving} style={{ padding: '6px 14px', border: 'none', borderRadius: 'var(--radius-md)', background: 'var(--brand-primary)', color: '#fff', fontSize: 12, fontWeight: 600, cursor: saving ? 'not-allowed' : 'pointer', fontFamily: 'var(--font-sans)' }}>{saving ? 'Speichern...' : 'Speichern'}</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * Die CMS-Anbindung eines Betriebs (L-25).
 *
 * Am 2026-08-30 aus `CustomerDetail.jsx` herausgeloest — 171 Zeilen.
 */
import { useState, useEffect } from 'react';
import API_BASE_URL from '../../config';

const CMS_OPTIONS = [
  { value: 'wordpress_elementor', label: 'WordPress + Elementor' },
  { value: 'webflow',             label: 'Webflow' },
  { value: 'none',                label: 'Kein CMS' },
];

export default function CmsConnectionSection({ customerId, headers }) {
  const [form, setForm]       = useState({ cms_type: '', cms_url: '', cms_username: '', cms_password: '' });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving]   = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState(null); // {ok, message}
  const [showPw, setShowPw]   = useState(false);

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/customers/${customerId}/cms-connection`, { headers })
      .then(r => r.json())
      .then(data => setForm(f => ({ ...f, cms_type: data.cms_type || '', cms_url: data.cms_url || '', cms_username: data.cms_username || '' })))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [customerId]); // eslint-disable-line

  const isWebflow = form.cms_type === 'webflow';

  const handleSave = async () => {
    setSaving(true);
    setTestResult(null);
    try {
      const res = await fetch(`${API_BASE_URL}/api/customers/${customerId}/cms-connection`, {
        method: 'PUT', headers, body: JSON.stringify(form),
      });
      if (!res.ok) throw new Error(await res.text());
    } catch (e) { console.error(e); }
    setSaving(false);
  };

  const handleTest = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      const res = await fetch(`${API_BASE_URL}/api/customers/${customerId}/cms-test`, { method: 'POST', headers });
      const data = await res.json();
      setTestResult(data);
    } catch (e) {
      setTestResult({ ok: false, message: String(e) });
    }
    setTesting(false);
  };

  const inp = {
    width: '100%', padding: '8px 10px', fontSize: 13, fontFamily: 'var(--font-sans)',
    border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)',
    background: 'var(--bg-app)', color: 'var(--text-primary)', boxSizing: 'border-box',
  };
  const lbl = { fontSize: 12, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 4, display: 'block' };

  if (loading) return (
    <div style={{ display: 'flex', justifyContent: 'center', padding: '48px 0' }}>
      <div style={{ width: 24, height: 24, borderRadius: '50%', border: '3px solid var(--border-light)', borderTopColor: 'var(--brand-primary)', animation: 'spin 0.8s linear infinite' }} />
    </div>
  );

  return (
    <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', padding: 20, display: 'flex', flexDirection: 'column', gap: 16, maxWidth: 540 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <span style={{ fontSize: 16 }}>🔌</span>
        <span style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>CMS-Verbindung</span>
      </div>

      {/* CMS type */}
      <div>
        <label style={lbl}>CMS-System</label>
        <select aria-label="CMS-System"
          value={form.cms_type}
          onChange={e => { setForm(f => ({ ...f, cms_type: e.target.value })); setTestResult(null); }}
          style={{ ...inp, cursor: 'pointer' }}
        >
          <option value="">– Auswählen –</option>
          {CMS_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
      </div>

      {form.cms_type && form.cms_type !== 'none' && (
        <>
          {/* URL (WordPress only) */}
          {!isWebflow && (
            <div>
              <label style={lbl}>Website-URL</label>
              <input aria-label="Website-URL" type="url" placeholder="https://meine-seite.de" value={form.cms_url}
                onChange={e => setForm(f => ({ ...f, cms_url: e.target.value }))} style={inp} />
            </div>
          )}

          {/* Username OR Site ID */}
          <div>
            <label style={lbl}>{isWebflow ? 'Site ID' : 'Benutzername'}</label>
            <input aria-label={isWebflow ? 'z.B. 64a1b2c3d4e5...' : 'wp-admin'} type="text"
              placeholder={isWebflow ? 'z.B. 64a1b2c3d4e5...' : 'wp-admin'}
              value={form.cms_username}
              onChange={e => setForm(f => ({ ...f, cms_username: e.target.value }))}
              style={inp}
            />
          </div>

          {/* Password OR API Token */}
          <div>
            <label style={lbl}>{isWebflow ? 'API-Token' : 'Anwendungspasswort'}</label>
            <div style={{ position: 'relative' }}>
              <input aria-label={isWebflow ? 'Bearer-Token aus Webflow-Einstellungen' : 'xxxx xxxx xxxx xxxx xxxx xxxx'}
                type={showPw ? 'text' : 'password'}
                placeholder={isWebflow ? 'Bearer-Token aus Webflow-Einstellungen' : 'xxxx xxxx xxxx xxxx xxxx xxxx'}
                value={form.cms_password}
                onChange={e => setForm(f => ({ ...f, cms_password: e.target.value }))}
                style={{ ...inp, paddingRight: 40 }}
                autoComplete="new-password"
              />
              <button onClick={() => setShowPw(v => !v)} style={{
                position: 'absolute', right: 8, top: '50%', transform: 'translateY(-50%)',
                background: 'none', border: 'none', cursor: 'pointer', fontSize: 14, color: 'var(--text-tertiary)',
              }}>{showPw ? '🙈' : '👁'}</button>
            </div>
            <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginTop: 4 }}>
              {isWebflow
                ? 'Unter Webflow → Account → Integrations → API Access'
                : 'In WordPress unter Benutzer → Profil → Anwendungspasswörter generieren'}
            </div>
          </div>
        </>
      )}

      {/* Actions */}
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        <button onClick={handleSave} disabled={saving || !form.cms_type} style={{
          padding: '8px 16px', background: 'var(--brand-primary)', color: 'var(--text-on-brand)',
          border: 'none', borderRadius: 'var(--radius-md)', fontSize: 13, fontWeight: 600,
          cursor: saving ? 'wait' : 'pointer', fontFamily: 'var(--font-sans)', opacity: saving ? 0.7 : 1,
        }}>
          {saving ? 'Speichern…' : '💾 Speichern'}
        </button>

        {form.cms_type && form.cms_type !== 'none' && (
          <button onClick={handleTest} disabled={testing} style={{
            padding: '8px 16px', background: 'var(--bg-app)', color: 'var(--text-primary)',
            border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)',
            fontSize: 13, fontWeight: 500, cursor: testing ? 'wait' : 'pointer',
            fontFamily: 'var(--font-sans)', opacity: testing ? 0.7 : 1,
          }}>
            {testing ? 'Testen…' : '🔗 Verbindung testen'}
          </button>
        )}
      </div>

      {/* Test result */}
      {testResult && (
        <div style={{
          padding: '10px 14px', borderRadius: 'var(--radius-md)', fontSize: 13,
          background: testResult.ok ? 'var(--status-success-bg)' : 'var(--status-danger-bg)',
          color:      testResult.ok ? 'var(--status-success-text)' : 'var(--status-danger-text)',
          display: 'flex', alignItems: 'center', gap: 8,
        }}>
          <span>{testResult.ok ? '✅' : '❌'}</span>
          <span>{testResult.message}</span>
        </div>
      )}
    </div>
  );
}


// ── Main component ─────────────────────────────────────────────


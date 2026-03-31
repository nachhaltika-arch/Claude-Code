import { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import API_BASE_URL from '../config';

export default function DomainImport() {
  const navigate = useNavigate();
  const { token } = useAuth();
  const fileRef = useRef();

  const [mode, setMode] = useState('csv');
  const [file, setFile] = useState(null);
  const [textInput, setTextInput] = useState('');
  const [preview, setPreview] = useState([]);
  const [jobId, setJobId] = useState(null);
  const [jobStatus, setJobStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [polling, setPolling] = useState(false);

  const h = { ...(token ? { Authorization: `Bearer ${token}` } : {}) };

  const handleFileChange = (e) => {
    const f = e.target.files[0];
    if (!f) return;
    setFile(f);
    setError('');
    const reader = new FileReader();
    reader.onload = (ev) => {
      setPreview(extractDomainsPreview(ev.target.result));
    };
    reader.readAsText(f, 'utf-8');
  };

  const handleTextChange = (val) => {
    setTextInput(val);
    setPreview(extractDomainsPreview(val));
  };

  const extractDomainsPreview = (text) => {
    const domains = [];
    const seen = new Set();
    for (const line of text.split(/[\n,;]/)) {
      const cell = line.trim().replace(/^["']|["']$/g, '');
      const clean = cell.replace(/^https?:\/\//, '').replace(/^www\./, '').split('/')[0].toLowerCase();
      if (/^[a-z0-9][a-z0-9\-\.]+\.[a-z]{2,}$/.test(clean) && !seen.has(clean)) {
        domains.push(`https://${clean}`);
        seen.add(clean);
      }
    }
    return domains.slice(0, 50);
  };

  const startImport = async () => {
    if (preview.length === 0) return;
    setLoading(true);
    setError('');
    try {
      let res;
      if (mode === 'csv' && file) {
        const form = new FormData();
        form.append('file', file);
        res = await fetch(`${API_BASE_URL}/api/leads/import/domains`, { method: 'POST', headers: h, body: form });
      } else {
        res = await fetch(`${API_BASE_URL}/api/leads/import/domains`, {
          method: 'POST', headers: { ...h, 'Content-Type': 'application/json' },
          body: JSON.stringify({ domains_text: textInput }),
        });
      }
      const data = await res.json();
      if (!res.ok) { setError(data.detail || 'Fehler'); setLoading(false); return; }
      setJobId(data.job_id);
      setJobStatus({ status: 'running', total: data.total_domains, processed: 0, results: [] });
      setLoading(false);
      pollStatus(data.job_id);
    } catch {
      setError('Verbindungsfehler');
      setLoading(false);
    }
  };

  const pollStatus = (jid) => {
    setPolling(true);
    const iv = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/api/leads/import/domains/${jid}/status`, { headers: h });
        const data = await res.json();
        setJobStatus(data);
        if (data.status === 'done' || data.status === 'error') { clearInterval(iv); setPolling(false); }
      } catch { clearInterval(iv); setPolling(false); }
    }, 3000);
    setTimeout(() => { clearInterval(iv); setPolling(false); }, 600000);
  };

  const pct = jobStatus ? Math.round(((jobStatus.processed || 0) / (jobStatus.total || 1)) * 100) : 0;

  const statusIcon = (s) => s === 'completed' ? '✅' : s === 'failed' ? '❌' : s === 'already_exists' ? '⏭️' : '⏳';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16, animation: 'fadeIn 0.3s ease', maxWidth: 900, margin: '0 auto', width: '100%' }}>

      {/* Header */}
      <div>
        <h1 style={{ fontSize: 20, fontWeight: 600, color: 'var(--text-primary)', margin: '0 0 4px' }}>Domain-Import</h1>
        <p style={{ fontSize: 12, color: 'var(--text-tertiary)', margin: 0 }}>CSV hochladen oder Domains eingeben → Audit + Impressum automatisch</p>
      </div>

      {/* Ablauf */}
      {!jobId && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 10 }}>
          {[
            { step: '1', icon: '📂', title: 'Domains laden', desc: 'CSV hochladen oder direkt eingeben', color: 'var(--brand-primary)' },
            { step: '2', icon: '🔍', title: 'Audit läuft', desc: 'Jede Domain wird automatisch geprüft', color: '#d97706' },
            { step: '3', icon: '🏢', title: 'Lead angelegt', desc: 'Automatisch in Neue Leads', color: '#059669' },
            { step: '4', icon: '📋', title: 'Impressum', desc: 'Kontaktdaten werden ausgelesen', color: '#7c3aed' },
          ].map(s => (
            <div key={s.step} style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', borderTop: `3px solid ${s.color}`, padding: '12px 14px' }}>
              <div style={{ fontSize: 20, marginBottom: 6 }}>{s.icon}</div>
              <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 3 }}>{s.title}</div>
              <div style={{ fontSize: 11, color: 'var(--text-tertiary)', lineHeight: 1.4 }}>{s.desc}</div>
            </div>
          ))}
        </div>
      )}

      {/* Import Form */}
      {!jobId && (
        <Card padding="md">
          {/* Modus Tabs */}
          <div style={{ display: 'flex', gap: 4, background: 'var(--bg-app)', borderRadius: 'var(--radius-md)', padding: 3, marginBottom: 20, width: 'fit-content' }}>
            {[
              { id: 'csv', label: '📂 CSV-Datei' },
              { id: 'text', label: '⌨️ Direkt eingeben' },
            ].map(m => (
              <button key={m.id} onClick={() => { setMode(m.id); setPreview([]); setFile(null); setTextInput(''); }} style={{
                padding: '6px 16px', borderRadius: 'var(--radius-sm)', border: 'none',
                background: mode === m.id ? 'var(--bg-surface)' : 'transparent',
                color: mode === m.id ? 'var(--brand-primary)' : 'var(--text-tertiary)',
                fontSize: 12, fontWeight: mode === m.id ? 600 : 400, cursor: 'pointer',
                fontFamily: 'var(--font-sans)', boxShadow: mode === m.id ? 'var(--shadow-card)' : 'none', transition: 'all 0.15s',
              }}>{m.label}</button>
            ))}
          </div>

          {/* CSV Upload */}
          {mode === 'csv' && (
            <div>
              <div onClick={() => fileRef.current?.click()} style={{
                border: `2px dashed ${file ? 'var(--brand-primary)' : 'var(--border-medium)'}`,
                borderRadius: 'var(--radius-lg)', padding: '32px 20px', textAlign: 'center', cursor: 'pointer',
                background: file ? 'var(--bg-active)' : 'var(--bg-app)', transition: 'all 0.15s',
              }}
              onMouseEnter={e => { e.currentTarget.style.background = 'var(--bg-hover)'; }}
              onMouseLeave={e => { e.currentTarget.style.background = file ? 'var(--bg-active)' : 'var(--bg-app)'; }}>
                <div style={{ fontSize: 32, marginBottom: 8 }}>{file ? '✅' : '📂'}</div>
                <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)', marginBottom: 4 }}>
                  {file ? file.name : 'CSV-Datei hier ablegen oder klicken'}
                </div>
                <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>
                  {file ? `${preview.length} Domains erkannt` : 'Alle Spalten werden nach Domains durchsucht'}
                </div>
              </div>
              <input ref={fileRef} type="file" accept=".csv,.txt" onChange={handleFileChange} style={{ display: 'none' }} />
            </div>
          )}

          {/* Text Eingabe */}
          {mode === 'text' && (
            <div>
              <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 6 }}>
                Domains eingeben (eine pro Zeile oder kommagetrennt)
              </div>
              <textarea value={textInput} onChange={e => handleTextChange(e.target.value)}
                placeholder={'maler-mueller.de\nsanitaer-schmidt.de\nhttps://elektro-weber.de\nwww.dachdecker-klein.de'}
                rows={8} style={{
                  width: '100%', padding: '10px 12px', border: '1px solid var(--border-medium)',
                  borderRadius: 'var(--radius-md)', fontSize: 13, fontFamily: 'var(--font-mono)',
                  color: 'var(--text-primary)', background: 'var(--bg-app)', resize: 'vertical',
                  outline: 'none', boxSizing: 'border-box', lineHeight: 1.6,
                }}
                onFocus={e => e.target.style.borderColor = 'var(--brand-primary)'}
                onBlur={e => e.target.style.borderColor = 'var(--border-medium)'} />
            </div>
          )}

          {/* Vorschau */}
          {preview.length > 0 && (
            <div style={{ marginTop: 16 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                  {preview.length} Domains erkannt
                </div>
                <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>Jede Domain → Audit + Impressum</div>
              </div>
              <div style={{ background: 'var(--bg-app)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-light)', maxHeight: 160, overflowY: 'auto', padding: '8px 10px' }}>
                {preview.map((d, i) => (
                  <div key={i} style={{ fontSize: 12, color: 'var(--brand-primary)', fontFamily: 'var(--font-mono)', padding: '2px 0', display: 'flex', alignItems: 'center', gap: 6 }}>
                    <span style={{ width: 16, fontSize: 10, color: 'var(--text-tertiary)' }}>{i + 1}</span>{d}
                  </div>
                ))}
              </div>
              <div style={{ marginTop: 10, padding: '8px 12px', background: 'var(--status-warning-bg)', borderRadius: 'var(--radius-sm)', fontSize: 11, color: 'var(--status-warning-text)', lineHeight: 1.5 }}>
                ⏱️ Verarbeitung dauert ca. <strong>{Math.ceil(preview.length * 0.5)} Minuten</strong> (Audit + Impressum pro Domain). Die Seite kann geschlossen werden — der Import läuft im Hintergrund.
              </div>
            </div>
          )}

          {error && (
            <div style={{ marginTop: 12, padding: '10px 12px', background: 'var(--status-danger-bg)', color: 'var(--status-danger-text)', borderRadius: 'var(--radius-md)', fontSize: 12 }}>{error}</div>
          )}

          <div style={{ marginTop: 16, display: 'flex', gap: 10, alignItems: 'center' }}>
            <Button variant="primary" onClick={startImport} disabled={loading || preview.length === 0}>
              {loading ? '⏳ Wird gestartet...' : `🚀 ${preview.length} Domains importieren`}
            </Button>
            {preview.length === 0 && <span style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>Zuerst Domains laden</span>}
          </div>
        </Card>
      )}

      {/* Job Status */}
      {jobId && jobStatus && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <Card padding="md">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12, flexWrap: 'wrap', gap: 8 }}>
              <div>
                <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 2 }}>
                  {jobStatus.status === 'done' ? '✅ Import abgeschlossen' : jobStatus.status === 'error' ? '❌ Import fehlgeschlagen' : '⚙️ Import läuft...'}
                </div>
                <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>
                  {jobStatus.processed || 0} von {jobStatus.total} Domains{polling && ' · wird aktualisiert...'}
                </div>
              </div>
              {jobStatus.status === 'done' && (
                <Button variant="primary" size="sm" onClick={() => navigate('/app/sales')}>→ Zur Vertriebspipeline</Button>
              )}
            </div>

            <div style={{ height: 6, background: 'var(--border-light)', borderRadius: 3, overflow: 'hidden', marginBottom: 12 }}>
              <div style={{ height: '100%', width: `${pct}%`, background: jobStatus.status === 'done' ? 'var(--status-success-text)' : 'var(--brand-primary)', borderRadius: 3, transition: 'width 0.5s ease' }} />
            </div>

            {(jobStatus.results || []).length > 0 && (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(100px, 1fr))', gap: 8, marginTop: 8 }}>
                {[
                  { label: 'Neu angelegt', count: (jobStatus.results || []).filter(r => r.status === 'created').length, color: 'var(--status-success-text)', bg: 'var(--status-success-bg)', icon: '✅' },
                  { label: 'Auditiert', count: (jobStatus.results || []).filter(r => r.audit_status === 'completed').length, color: 'var(--brand-primary)', bg: 'var(--bg-active)', icon: '🔍' },
                  { label: 'Impressum', count: (jobStatus.results || []).filter(r => r.impressum_status === 'completed').length, color: '#7c3aed', bg: '#f5f3ff', icon: '📋' },
                  { label: 'Bereits da', count: (jobStatus.results || []).filter(r => r.status === 'already_exists').length, color: 'var(--text-tertiary)', bg: 'var(--bg-app)', icon: '⏭️' },
                ].map(kpi => (
                  <div key={kpi.label} style={{ background: kpi.bg, borderRadius: 'var(--radius-md)', padding: '10px 12px', textAlign: 'center' }}>
                    <div style={{ fontSize: 18, marginBottom: 2 }}>{kpi.icon}</div>
                    <div style={{ fontSize: 18, fontWeight: 700, color: kpi.color, lineHeight: 1 }}>{kpi.count}</div>
                    <div style={{ fontSize: 10, color: 'var(--text-tertiary)', marginTop: 2 }}>{kpi.label}</div>
                  </div>
                ))}
              </div>
            )}
          </Card>

          {/* Ergebnis-Liste */}
          {(jobStatus.results || []).length > 0 && (
            <Card padding="sm">
              <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 10, padding: '0 4px' }}>
                Verarbeitete Domains
              </div>
              {jobStatus.results.map((r, i) => (
                <div key={i} onClick={() => r.lead_id && navigate(`/app/leads/${r.lead_id}`)} style={{
                  display: 'flex', alignItems: 'center', gap: 10, padding: '8px 6px',
                  borderBottom: i < jobStatus.results.length - 1 ? '1px solid var(--border-light)' : 'none',
                  cursor: r.lead_id ? 'pointer' : 'default', borderRadius: 'var(--radius-sm)', transition: 'background 0.1s',
                }}
                onMouseEnter={e => { if (r.lead_id) e.currentTarget.style.background = 'var(--bg-hover)'; }}
                onMouseLeave={e => { e.currentTarget.style.background = 'transparent'; }}>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {r.company_name || r.url.replace('https://', '')}
                    </div>
                    <div style={{ fontSize: 10, color: 'var(--brand-primary)', fontFamily: 'var(--font-mono)', marginTop: 1 }}>
                      {r.url.replace('https://', '')}
                    </div>
                  </div>
                  {r.score !== undefined && (
                    <div style={{ fontSize: 12, fontWeight: 700, color: r.score >= 70 ? 'var(--status-success-text)' : r.score >= 50 ? 'var(--status-warning-text)' : 'var(--status-danger-text)', flexShrink: 0 }}>
                      {r.score}/100
                    </div>
                  )}
                  <div style={{ display: 'flex', gap: 4, flexShrink: 0 }}>
                    <span title="Audit">{statusIcon(r.audit_status)}</span>
                    <span title="Impressum">{statusIcon(r.impressum_status)}</span>
                  </div>
                  {r.lead_id && <span style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>→</span>}
                </div>
              ))}
            </Card>
          )}

          {jobStatus.status === 'done' && (
            <div style={{ textAlign: 'center' }}>
              <button onClick={() => { setJobId(null); setJobStatus(null); setPreview([]); setFile(null); setTextInput(''); }} style={{
                background: 'none', border: 'none', color: 'var(--brand-primary)', fontSize: 13, cursor: 'pointer', fontFamily: 'var(--font-sans)', textDecoration: 'underline',
              }}>Weiteren Import starten</button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

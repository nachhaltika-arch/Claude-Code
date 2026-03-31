import { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
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
  const [checkResult, setCheckResult] = useState(null);
  const [checking, setChecking] = useState(false);
  const [importFilter, setImportFilter] = useState('new');

  const h = { ...(token ? { Authorization: `Bearer ${token}` } : {}) };

  const handleFileChange = (e) => {
    const f = e.target.files[0];
    if (!f) return;
    setFile(f); setError(''); setCheckResult(null);
    const reader = new FileReader();
    reader.onload = (ev) => setPreview(extractDomains(ev.target.result));
    reader.readAsText(f, 'utf-8');
  };

  const handleTextChange = (val) => { setTextInput(val); setCheckResult(null); setPreview(extractDomains(val)); };

  const extractDomains = (text) => {
    const domains = [], seen = new Set();
    for (const line of text.split(/[\n,;]/)) {
      const clean = line.trim().replace(/^["']|["']$/g, '').replace(/^https?:\/\//, '').replace(/^www\./, '').split('/')[0].toLowerCase();
      if (/^[a-z0-9][a-z0-9\-\.]+\.[a-z]{2,}$/.test(clean) && !seen.has(clean)) { domains.push(`https://${clean}`); seen.add(clean); }
    }
    return domains.slice(0, 50);
  };

  const checkDomains = async () => {
    if (!preview.length) return;
    setChecking(true); setCheckResult(null);
    try {
      const res = await fetch(`${API_BASE_URL}/api/leads/import/domains/check`, { method: 'POST', headers: { ...h, 'Content-Type': 'application/json' }, body: JSON.stringify({ domains: preview }) });
      setCheckResult(await res.json());
    } catch { setError('Prüfung fehlgeschlagen'); }
    finally { setChecking(false); }
  };

  const startImport = async () => {
    const toImport = checkResult ? (importFilter === 'new' ? checkResult.results.filter(r => !r.exists).map(r => r.url) : preview) : preview;
    if (!toImport.length) { setError('Keine Domains'); return; }
    setLoading(true); setError('');
    try {
      let res;
      if (mode === 'csv' && file && importFilter === 'all') {
        const form = new FormData(); form.append('file', file);
        res = await fetch(`${API_BASE_URL}/api/leads/import/domains/file`, { method: 'POST', headers: h, body: form });
      } else {
        res = await fetch(`${API_BASE_URL}/api/leads/import/domains/text`, { method: 'POST', headers: { ...h, 'Content-Type': 'application/json' }, body: JSON.stringify({ domains_text: toImport.join('\n') }) });
      }
      const data = await res.json();
      if (!res.ok) { setError(data.detail || 'Fehler'); setLoading(false); return; }
      setJobId(data.job_id); setJobStatus({ status: 'running', total: data.total_domains, processed: 0, results: [] });
      setLoading(false); pollStatus(data.job_id);
    } catch { setError('Verbindungsfehler'); setLoading(false); }
  };

  const pollStatus = (jid) => {
    setPolling(true);
    const iv = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/api/leads/import/domains/${jid}/status`, { headers: h });
        const data = await res.json(); setJobStatus(data);
        if (data.status === 'done' || data.status === 'error') { clearInterval(iv); setPolling(false); }
      } catch { clearInterval(iv); setPolling(false); }
    }, 3000);
    setTimeout(() => { clearInterval(iv); setPolling(false); }, 600000);
  };

  const pct = jobStatus ? Math.round(((jobStatus.processed || 0) / (jobStatus.total || 1)) * 100) : 0;

  return (
    <div style={{ maxWidth: 900, margin: '0 auto' }}>
      <h2 className="mb-1"><i className="fas fa-cloud-arrow-up me-2"></i>Domain-Import</h2>
      <p className="text-muted small mb-3">CSV hochladen oder Domains eingeben → Duplikat-Check → Audit + Impressum</p>

      {/* Steps */}
      {!jobId && (
        <div className="row g-2 mb-3">
          {[
            { icon: 'fa-file-csv', title: 'Domains laden', color: 'primary' },
            { icon: 'fa-magnifying-glass', title: 'Duplikat-Check', color: 'info' },
            { icon: 'fa-magnifying-glass-chart', title: 'Audit', color: 'warning' },
            { icon: 'fa-address-card', title: 'Impressum', color: 'success' },
          ].map((s, i) => (
            <div className="col-6 col-md-3" key={i}>
              <div className={`card border-${s.color} border-top-3 h-100`} style={{ borderTopWidth: 3 }}>
                <div className="card-body p-2 text-center">
                  <i className={`fas ${s.icon} fs-5 text-${s.color} mb-1`}></i>
                  <div className="small fw-semibold">{s.title}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Input Form */}
      {!jobId && (
        <div className="card shadow-sm mb-3">
          <div className="card-body">
            <ul className="nav nav-pills mb-3">
              <li className="nav-item"><button className={`nav-link ${mode === 'csv' ? 'active' : ''}`} onClick={() => { setMode('csv'); setPreview([]); setFile(null); setTextInput(''); setCheckResult(null); }}><i className="fas fa-file-csv me-1"></i> CSV-Datei</button></li>
              <li className="nav-item"><button className={`nav-link ${mode === 'text' ? 'active' : ''}`} onClick={() => { setMode('text'); setPreview([]); setFile(null); setTextInput(''); setCheckResult(null); }}><i className="fas fa-keyboard me-1"></i> Direkt eingeben</button></li>
            </ul>

            {mode === 'csv' && (
              <div className={`border border-2 border-dashed rounded-3 p-4 text-center ${file ? 'border-primary bg-light' : ''}`} style={{ cursor: 'pointer' }} onClick={() => fileRef.current?.click()}>
                <i className={`fas ${file ? 'fa-check-circle text-success' : 'fa-cloud-arrow-up text-muted'} fs-1 mb-2`}></i>
                <div className="fw-semibold">{file ? file.name : 'CSV-Datei hier ablegen oder klicken'}</div>
                <small className="text-muted">{file ? `${preview.length} Domains erkannt` : 'Alle Spalten werden nach Domains durchsucht'}</small>
                <input ref={fileRef} type="file" accept=".csv,.txt" onChange={handleFileChange} className="d-none" />
              </div>
            )}

            {mode === 'text' && (
              <textarea className="form-control font-monospace" rows={6} value={textInput} onChange={e => handleTextChange(e.target.value)} placeholder={'maler-mueller.de\nsanitaer-schmidt.de\nhttps://elektro-weber.de'} />
            )}

            {/* Preview + Check */}
            {preview.length > 0 && (
              <div className="mt-3">
                {!checkResult ? (
                  <div className="d-flex justify-content-between align-items-center mb-2">
                    <small className="text-muted fw-semibold text-uppercase">{preview.length} Domains erkannt</small>
                    <button className="btn btn-outline-primary btn-sm" onClick={checkDomains} disabled={checking}>
                      {checking ? <><span className="spinner-border spinner-border-sm me-1"></span>Prüfen...</> : <><i className="fas fa-magnifying-glass me-1"></i>Duplikate prüfen</>}
                    </button>
                  </div>
                ) : (
                  <div className="mb-3">
                    <div className="row g-2 mb-2">
                      {[
                        { label: 'Neu', val: checkResult.new_count, bg: 'success' },
                        { label: 'Vorhanden', val: checkResult.existing_count, bg: 'secondary' },
                        { label: 'Gesamt', val: checkResult.total, bg: 'primary' },
                      ].map(k => (
                        <div className="col-4" key={k.label}>
                          <div className={`card bg-${k.bg} bg-opacity-10 text-center p-2`}>
                            <div className={`fs-4 fw-bold text-${k.bg}`}>{k.val}</div>
                            <small className="text-muted">{k.label}</small>
                          </div>
                        </div>
                      ))}
                    </div>
                    {checkResult.existing_count > 0 && (
                      <div className="btn-group btn-group-sm mb-2">
                        <button className={`btn ${importFilter === 'new' ? 'btn-primary' : 'btn-outline-secondary'}`} onClick={() => setImportFilter('new')}>Nur neue ({checkResult.new_count})</button>
                        <button className={`btn ${importFilter === 'all' ? 'btn-primary' : 'btn-outline-secondary'}`} onClick={() => setImportFilter('all')}>Alle ({checkResult.total})</button>
                      </div>
                    )}
                    <div className="list-group list-group-flush border rounded" style={{ maxHeight: 180, overflowY: 'auto' }}>
                      {checkResult.results.filter(r => importFilter === 'all' || !r.exists).map((r, i) => (
                        <div key={i} className={`list-group-item d-flex align-items-center gap-2 py-1 px-2 small ${r.exists ? 'text-muted' : ''}`}>
                          <i className={`fas ${r.exists ? 'fa-forward text-secondary' : 'fa-circle-plus text-success'}`}></i>
                          <span className="font-monospace flex-grow-1 text-truncate">{r.domain}</span>
                          {r.score > 0 && <span className="badge bg-secondary">{r.score}</span>}
                          {r.exists && r.company_name && <small className="text-muted">{r.company_name}</small>}
                        </div>
                      ))}
                    </div>
                    <button className="btn btn-link btn-sm text-muted mt-1" onClick={() => { setCheckResult(null); setImportFilter('new'); }}>↺ Erneut prüfen</button>
                  </div>
                )}
              </div>
            )}

            {error && <div className="alert alert-danger py-2 small mt-2">{error}</div>}

            <div className="mt-3">
              <button className="btn btn-primary" onClick={checkResult ? startImport : checkDomains}
                disabled={loading || !preview.length || checking || (checkResult && checkResult.new_count === 0 && importFilter === 'new')}>
                {loading ? <><span className="spinner-border spinner-border-sm me-1"></span>Startet...</>
                  : checking ? <><span className="spinner-border spinner-border-sm me-1"></span>Prüft...</>
                  : checkResult ? <><i className="fas fa-rocket me-1"></i>{importFilter === 'new' ? checkResult.new_count : checkResult.total} Domains importieren</>
                  : <><i className="fas fa-magnifying-glass me-1"></i>{preview.length} Domains prüfen</>}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Job Status */}
      {jobId && jobStatus && (
        <div className="card shadow-sm">
          <div className="card-body">
            <div className="d-flex justify-content-between align-items-center mb-3">
              <div>
                <h5 className="mb-0">
                  {jobStatus.status === 'done' ? <><i className="fas fa-check-circle text-success me-2"></i>Import abgeschlossen</> : jobStatus.status === 'error' ? <><i className="fas fa-circle-xmark text-danger me-2"></i>Fehler</> : <><span className="spinner-border spinner-border-sm me-2"></span>Import läuft...</>}
                </h5>
                <small className="text-muted">{jobStatus.processed || 0} von {jobStatus.total} Domains{polling && ' · wird aktualisiert'}</small>
              </div>
              {jobStatus.status === 'done' && <button className="btn btn-primary btn-sm" onClick={() => navigate('/app/sales')}><i className="fas fa-arrow-right me-1"></i>Zur Pipeline</button>}
            </div>
            <div className="progress mb-3" style={{ height: 8 }}>
              <div className={`progress-bar ${jobStatus.status === 'done' ? 'bg-success' : ''}`} style={{ width: `${pct}%` }}></div>
            </div>
            {(jobStatus.results || []).length > 0 && (
              <div className="list-group list-group-flush border rounded" style={{ maxHeight: 300, overflowY: 'auto' }}>
                {jobStatus.results.map((r, i) => (
                  <div key={i} className="list-group-item d-flex align-items-center gap-2 py-2 px-2 small" style={{ cursor: r.lead_id ? 'pointer' : 'default' }} onClick={() => r.lead_id && navigate(`/app/leads/${r.lead_id}`)}>
                    <span className="fw-semibold flex-grow-1 text-truncate">{r.company_name || r.url.replace('https://', '')}</span>
                    {r.score !== undefined && r.score !== null && <span className="badge bg-secondary">{r.score}/100</span>}
                    {r.audit_status === 'completed' && <i className="fas fa-check text-success" title="Audit"></i>}
                    {r.impressum_status === 'completed' && <i className="fas fa-check text-info" title="Impressum"></i>}
                    {r.status === 'already_exists' && <span className="badge bg-light text-muted border">vorhanden</span>}
                  </div>
                ))}
              </div>
            )}
            {jobStatus.status === 'done' && (
              <div className="text-center mt-3">
                <button className="btn btn-link text-muted small" onClick={() => { setJobId(null); setJobStatus(null); setPreview([]); setFile(null); setTextInput(''); setCheckResult(null); }}>Weiteren Import starten</button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useScreenSize } from '../utils/responsive';
import API_BASE_URL from '../config';
import WebsiteDesigner from '../components/WebsiteDesigner';

// ── PageSpeed helpers ──────────────────────────────────────────

function scoreColor(score) {
  if (score === null || score === undefined) return { bg: 'var(--status-neutral-bg)', text: 'var(--status-neutral-text)' };
  if (score >= 90) return { bg: 'var(--status-success-bg)', text: 'var(--status-success-text)' };
  if (score >= 50) return { bg: 'var(--status-warning-bg)', text: 'var(--status-warning-text)' };
  return { bg: 'var(--status-danger-bg)', text: 'var(--status-danger-text)' };
}

function vitalColor(key, raw) {
  if (raw === null || raw === undefined) return { bg: 'var(--status-neutral-bg)', text: 'var(--status-neutral-text)' };
  const thresholds = {
    lcp: [2500, 4000],
    cls: [0.1, 0.25],
    inp: [200, 500],
    fcp: [1800, 3000],
  };
  const [good, poor] = thresholds[key];
  if (raw < good) return { bg: 'var(--status-success-bg)', text: 'var(--status-success-text)' };
  if (raw < poor) return { bg: 'var(--status-warning-bg)', text: 'var(--status-warning-text)' };
  return { bg: 'var(--status-danger-bg)', text: 'var(--status-danger-text)' };
}

function fmtVital(key, raw) {
  if (raw === null || raw === undefined) return '—';
  if (key === 'cls') return raw.toFixed(3);
  return (raw / 1000).toFixed(2) + ' s';
}

function fmtTs(iso) {
  if (!iso) return null;
  const d = new Date(iso);
  return d.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' })
    + ' ' + d.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' }) + ' Uhr';
}

// ── Audit History section component ───────────────────────────

function AuditHistorySection({ customerId, customer, headers }) {
  const { isMobile } = useScreenSize();
  const [audits, setAudits]           = useState([]);
  const [loading, setLoading]         = useState(true);
  const [error, setError]             = useState(null);
  const [starting, setStarting]       = useState(false);
  const [startError, setStartError]   = useState(null);
  const [pollingId, setPollingId]     = useState(null); // audit id being polled
  const pollRef                       = useRef(null);

  const fetchAudits = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/audit/lead/${customerId}`, { headers });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setAudits(Array.isArray(data) ? data : []);
      setError(null);
    } catch (e) {
      console.error('[AuditHistory] fetchAudits failed:', e);
      setError(`Audit-Historie konnte nicht geladen werden: ${e.message}`);
    } finally {
      setLoading(false);
    }
  }, [customerId]); // eslint-disable-line

  // SCHRITT 3 — customerId als Abhängigkeit
  useEffect(() => {
    setLoading(true);
    fetchAudits();
  }, [customerId]); // eslint-disable-line

  // Cleanup polling on unmount
  useEffect(() => () => { if (pollRef.current) clearInterval(pollRef.current); }, []);

  const stopPolling = () => {
    if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null; }
    setPollingId(null);
  };

  // SCHRITT 2 — Polling nach Audit-Start
  const startPolling = (auditId) => {
    setPollingId(auditId);
    pollRef.current = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/api/audit/status/${auditId}`, { headers });
        if (!res.ok) { stopPolling(); return; }
        const data = await res.json();
        if (data.status === 'completed' || data.status === 'failed') {
          stopPolling();
          fetchAudits();
        }
      } catch (e) {
        console.error('[AuditHistory] polling error:', e);
        stopPolling();
      }
    }, 3000);
  };

  const handleStartAudit = async () => {
    const websiteUrl = customer?.website_url || customer?.url || customer?.domain;
    if (!websiteUrl) {
      setStartError('Keine Website-URL beim Kunden hinterlegt.');
      return;
    }
    setStarting(true);
    setStartError(null);
    try {
      const res = await fetch(`${API_BASE_URL}/api/audit/start`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          website_url: websiteUrl,
          company_name: customer?.company_name || '',
          contact_name: customer?.contact_name || '',
          lead_id: Number(customerId),
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        setStartError(data?.detail || 'Audit konnte nicht gestartet werden.');
      } else {
        // Optimistically add a pending row, then poll for completion
        setAudits(prev => [{ id: data.id, status: 'pending', website_url: websiteUrl, created_at: new Date().toISOString() }, ...prev]);
        startPolling(data.id);
      }
    } catch (e) {
      console.error('[AuditHistory] startAudit failed:', e);
      setStartError(`Verbindungsfehler: ${e.message}`);
    }
    setStarting(false);
  };

  const scoreLabel = (score) => {
    if (score === null || score === undefined) return '—';
    return `${score}/100`;
  };

  const scoreColors = (score) => {
    if (score === null || score === undefined) return { bg: 'var(--status-neutral-bg)', text: 'var(--status-neutral-text)' };
    if (score >= 70) return { bg: 'var(--status-success-bg)', text: 'var(--status-success-text)' };
    if (score >= 45) return { bg: 'var(--status-warning-bg)', text: 'var(--status-warning-text)' };
    return { bg: 'var(--status-danger-bg)', text: 'var(--status-danger-text)' };
  };

  const statusBadge = (status, auditId) => {
    const isPolling = pollingId === auditId;
    const map = {
      completed: { label: 'Abgeschlossen', bg: 'var(--status-success-bg)', color: 'var(--status-success-text)' },
      failed:    { label: 'Fehlgeschlagen', bg: 'var(--status-danger-bg)',  color: 'var(--status-danger-text)' },
      pending:   { label: isPolling ? 'Läuft…' : 'Ausstehend', bg: 'var(--status-info-bg)', color: 'var(--status-info-text)' },
      running:   { label: 'Läuft…', bg: 'var(--status-info-bg)', color: 'var(--status-info-text)' },
    };
    const s = map[status] || map.pending;
    return (
      <span style={{
        display: 'inline-flex', alignItems: 'center', gap: 4,
        background: s.bg, color: s.color,
        borderRadius: 'var(--radius-full)', fontSize: 11, fontWeight: 600, padding: '2px 8px',
      }}>
        {(status === 'pending' || status === 'running') && (
          <span style={{ width: 7, height: 7, borderRadius: '50%', border: '1.5px solid currentColor', borderTopColor: 'transparent', animation: 'spin 0.8s linear infinite', display: 'inline-block', flexShrink: 0 }} />
        )}
        {s.label}
      </span>
    );
  };

  return (
    <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', overflow: 'hidden' }}>

      {/* Header */}
      <div style={{
        padding: isMobile ? '12px 16px' : '16px 20px',
        borderBottom: '1px solid var(--border-light)',
        display: 'flex',
        flexDirection: isMobile ? 'column' : 'row',
        alignItems: isMobile ? 'stretch' : 'center',
        justifyContent: 'space-between',
        gap: isMobile ? 10 : 0,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 16 }}>🔍</span>
          <span style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>Audit-Historie</span>
          {!loading && audits.length > 0 && (
            <span style={{ background: 'var(--brand-primary-light)', color: 'var(--brand-primary)', borderRadius: 'var(--radius-full)', fontSize: 11, fontWeight: 600, padding: '2px 8px' }}>
              {audits.length}
            </span>
          )}
        </div>
        <button
          onClick={handleStartAudit}
          disabled={starting || !!pollingId}
          style={{
            padding: '8px 14px',
            background: (starting || pollingId) ? 'var(--bg-elevated)' : 'var(--brand-primary)',
            color: (starting || pollingId) ? 'var(--text-tertiary)' : 'var(--text-inverse)',
            border: (starting || pollingId) ? '1px solid var(--border-medium)' : 'none',
            borderRadius: 'var(--radius-md)', fontSize: 12, fontWeight: 600,
            cursor: (starting || pollingId) ? 'not-allowed' : 'pointer',
            fontFamily: 'var(--font-sans)',
            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6,
            ...(isMobile ? { width: '100%' } : {}),
          }}
        >
          {(starting || pollingId) ? (
            <>
              <span style={{ width: 11, height: 11, borderRadius: '50%', border: '2px solid var(--border-medium)', borderTopColor: 'var(--brand-primary)', animation: 'spin 0.8s linear infinite', display: 'inline-block', flexShrink: 0 }} />
              {starting ? 'Wird gestartet…' : 'Audit läuft…'}
            </>
          ) : '+ Audit starten'}
        </button>
      </div>

      {/* Error banner */}
      {startError && (
        <div style={{ margin: '12px 20px 0', padding: '10px 14px', background: 'var(--status-danger-bg)', color: 'var(--status-danger-text)', borderRadius: 'var(--radius-md)', fontSize: 12 }}>
          {startError}
        </div>
      )}

      {/* Body */}
      <div style={{ padding: '4px 0' }}>
        {loading ? (
          <div style={{ padding: '32px 20px', display: 'flex', justifyContent: 'center' }}>
            <div style={{ width: 24, height: 24, borderRadius: '50%', border: '2px solid var(--border-light)', borderTopColor: 'var(--brand-primary)', animation: 'spin 0.8s linear infinite' }} />
          </div>
        ) : error ? (
          <div style={{ margin: '12px 20px', padding: '10px 14px', background: 'var(--status-danger-bg)', color: 'var(--status-danger-text)', borderRadius: 'var(--radius-md)', fontSize: 12 }}>
            {error}
          </div>
        ) : audits.length === 0 ? (
          <div style={{ padding: '32px 20px', textAlign: 'center', color: 'var(--text-tertiary)' }}>
            <div style={{ fontSize: 32, marginBottom: 8, opacity: 0.3 }}>🔍</div>
            <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 4 }}>Noch kein Audit durchgeführt</div>
            <div style={{ fontSize: 12 }}>Klicke auf „+ Audit starten" um eine Website-Analyse zu starten.</div>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            {/* Table header */}
            <div style={{
              display: 'grid', gridTemplateColumns: '1fr 100px 90px 120px',
              minWidth: 460, gap: 12, padding: '8px 20px',
              fontSize: 11, fontWeight: 600, color: 'var(--text-tertiary)',
              textTransform: 'uppercase', letterSpacing: '0.06em',
              borderBottom: '1px solid var(--border-light)',
            }}>
              <span>Website</span><span>Score</span><span>Status</span><span>Datum</span>
            </div>

            {audits.map(audit => {
              const c = scoreColors(audit.total_score);
              return (
                <div
                  key={audit.id}
                  style={{
                    display: 'grid', gridTemplateColumns: '1fr 100px 90px 120px',
                    minWidth: 460, gap: 12, padding: '12px 20px',
                    alignItems: 'center', borderBottom: '1px solid var(--border-light)',
                    transition: 'background var(--transition-fast)',
                  }}
                  onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-app)'}
                  onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                >
                  <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {audit.website_url}
                    {audit.company_name && (
                      <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 1 }}>{audit.company_name}</div>
                    )}
                  </div>
                  <div>
                    {audit.status === 'completed' ? (
                      <span style={{ display: 'inline-block', padding: '2px 8px', background: c.bg, color: c.text, borderRadius: 'var(--radius-full)', fontSize: 12, fontWeight: 700 }}>
                        {scoreLabel(audit.total_score)}
                      </span>
                    ) : (
                      <span style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>—</span>
                    )}
                  </div>
                  <div>{statusBadge(audit.status, audit.id)}</div>
                  <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>{fmtTs(audit.created_at)}</div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

// ── helpers ───────────────────────────────────────────────────

function fmtBytes(bytes) {
  if (!bytes) return '0 B';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

const FILE_TYPE_BADGES = {
  logo:         { label: 'Logo',         bg: 'var(--status-info-bg)',    color: 'var(--status-info-text)' },
  foto:         { label: 'Foto',         bg: 'var(--status-success-bg)', color: 'var(--status-success-text)' },
  text:         { label: 'Text',         bg: 'var(--status-neutral-bg)', color: 'var(--status-neutral-text)' },
  zugangsdaten: { label: 'Zugangsdaten', bg: 'var(--status-warning-bg)', color: 'var(--status-warning-text)' },
  sonstiges:    { label: 'Sonstiges',    bg: 'var(--status-neutral-bg)', color: 'var(--status-neutral-text)' },
};

// ── ProjectFilesSection ────────────────────────────────────────

function ProjectFilesSection({ customerId, token }) {
  const { isMobile } = useScreenSize();
  const fileInputRef = useRef(null);

  const [files, setFiles]           = useState([]);
  const [loading, setLoading]       = useState(true);
  const [error, setError]           = useState(null);

  // upload state
  const [pendingFile, setPendingFile]   = useState(null);
  const [fileType, setFileType]         = useState('sonstiges');
  const [note, setNote]                 = useState('');
  const [uploading, setUploading]       = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadError, setUploadError]   = useState(null);
  const [dragOver, setDragOver]         = useState(false);

  // per-row delete confirm
  const [confirmDelete, setConfirmDelete] = useState(null);
  const [deleting, setDeleting]           = useState(null);

  const authHeaders = token ? { Authorization: `Bearer ${token}` } : {};

  const fetchFiles = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/files/${customerId}`, { headers: authHeaders });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setFiles(Array.isArray(data) ? data : []);
      setError(null);
    } catch (e) {
      console.error('[ProjectFiles] fetch failed:', e);
      setError('Dateien konnten nicht geladen werden.');
    } finally {
      setLoading(false);
    }
  }, [customerId]); // eslint-disable-line

  useEffect(() => {
    setLoading(true);
    fetchFiles();
  }, [customerId]); // eslint-disable-line

  const pickFile = (f) => {
    if (!f) return;
    setPendingFile(f);
    setUploadError(null);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const f = e.dataTransfer.files[0];
    if (f) pickFile(f);
  };

  const handleUpload = () => {
    if (!pendingFile) return;
    setUploading(true);
    setUploadProgress(0);
    setUploadError(null);

    const form = new FormData();
    form.append('file', pendingFile);
    form.append('file_type', fileType);
    form.append('note', note);

    const xhr = new XMLHttpRequest();
    xhr.open('POST', `${API_BASE_URL}/api/files/upload/${customerId}`);
    if (token) xhr.setRequestHeader('Authorization', `Bearer ${token}`);

    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) setUploadProgress(Math.round((e.loaded / e.total) * 100));
    };
    xhr.onload = () => {
      setUploading(false);
      if (xhr.status >= 200 && xhr.status < 300) {
        setPendingFile(null);
        setNote('');
        setFileType('sonstiges');
        setUploadProgress(0);
        fetchFiles();
      } else {
        try {
          const err = JSON.parse(xhr.responseText);
          setUploadError(err.detail || 'Upload fehlgeschlagen.');
        } catch {
          setUploadError('Upload fehlgeschlagen.');
        }
      }
    };
    xhr.onerror = () => {
      setUploading(false);
      setUploadError('Verbindungsfehler beim Upload.');
    };
    xhr.send(form);
  };

  const handleDelete = async (fileId) => {
    setDeleting(fileId);
    try {
      const res = await fetch(`${API_BASE_URL}/api/files/${fileId}`, {
        method: 'DELETE',
        headers: authHeaders,
      });
      if (res.ok) {
        setFiles(prev => prev.filter(f => f.id !== fileId));
      } else {
        const err = await res.json();
        console.error('[ProjectFiles] delete failed:', err.detail);
      }
    } catch (e) {
      console.error('[ProjectFiles] delete error:', e);
    }
    setDeleting(null);
    setConfirmDelete(null);
  };

  const handleDownload = (fileId, filename) => {
    const a = document.createElement('a');
    a.href = `${API_BASE_URL}/api/files/download/${fileId}`;
    a.setAttribute('Authorization', token ? `Bearer ${token}` : '');
    // Open in new tab for inline-supported types (images/pdf)
    a.target = '_blank';
    a.rel = 'noreferrer';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  const dropZoneStyle = {
    border: `1.5px dashed ${dragOver ? 'var(--brand-primary)' : 'var(--border-medium)'}`,
    borderRadius: 'var(--radius-lg)',
    padding: isMobile ? '20px 16px' : '28px 20px',
    textAlign: 'center',
    cursor: 'pointer',
    background: dragOver ? 'var(--bg-active)' : 'var(--bg-app)',
    transition: 'border-color var(--transition-fast), background var(--transition-fast)',
  };

  return (
    <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', overflow: 'hidden' }}>

      {/* Section header */}
      <div style={{
        padding: isMobile ? '12px 16px' : '16px 20px',
        borderBottom: '1px solid var(--border-light)',
        display: 'flex',
        flexDirection: isMobile ? 'column' : 'row',
        alignItems: isMobile ? 'stretch' : 'center',
        justifyContent: 'space-between',
        gap: isMobile ? 10 : 0,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 16 }}>📁</span>
          <span style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>Projektdateien</span>
          {!loading && files.length > 0 && (
            <span style={{ background: 'var(--brand-primary-light)', color: 'var(--brand-primary)', borderRadius: 'var(--radius-full)', fontSize: 11, fontWeight: 600, padding: '2px 8px' }}>
              {files.length}
            </span>
          )}
        </div>
        <button
          onClick={() => fileInputRef.current?.click()}
          style={{
            padding: '8px 14px',
            background: 'var(--brand-primary)', color: 'var(--text-inverse)',
            border: 'none', borderRadius: 'var(--radius-md)',
            fontSize: 12, fontWeight: 600, cursor: 'pointer',
            fontFamily: 'var(--font-sans)',
            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6,
            ...(isMobile ? { width: '100%' } : {}),
          }}
        >+ Datei hochladen</button>
      </div>

      <div style={{ padding: isMobile ? 16 : 20, display: 'flex', flexDirection: 'column', gap: 12 }}>

        {/* Drag & Drop zone */}
        <div
          style={dropZoneStyle}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
        >
          <input
            ref={fileInputRef}
            type="file"
            style={{ display: 'none' }}
            accept=".jpg,.jpeg,.png,.gif,.pdf,.doc,.docx,.txt,.zip,.svg,.ai,.eps"
            onChange={(e) => pickFile(e.target.files[0])}
          />
          {pendingFile ? (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8 }}>
              <span style={{ fontSize: 20 }}>📄</span>
              <div style={{ textAlign: 'left' }}>
                <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>{pendingFile.name}</div>
                <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>{fmtBytes(pendingFile.size)}</div>
              </div>
              <button
                onClick={(e) => { e.stopPropagation(); setPendingFile(null); }}
                style={{ marginLeft: 8, background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-tertiary)', fontSize: 16 }}
              >×</button>
            </div>
          ) : (
            <>
              <div style={{ fontSize: 28, marginBottom: 8, opacity: 0.3 }}>📂</div>
              <div style={{ fontSize: 13, color: 'var(--text-secondary)', fontWeight: 500 }}>Dateien hier ablegen oder klicken</div>
              <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 4 }}>
                JPG, PNG, GIF, PDF, DOC, DOCX, TXT, ZIP, SVG, AI, EPS — max. 20 MB
              </div>
            </>
          )}
        </div>

        {/* Options row */}
        {pendingFile && (
          <div style={{ display: 'flex', flexDirection: isMobile ? 'column' : 'row', gap: 8 }}>
            <select
              value={fileType}
              onChange={(e) => setFileType(e.target.value)}
              style={{
                flex: '0 0 160px', padding: '8px 10px', fontSize: 13,
                border: '0.5px solid var(--border-light)', borderRadius: 'var(--radius-md)',
                background: 'var(--bg-elevated)', color: 'var(--text-primary)',
                fontFamily: 'var(--font-sans)', cursor: 'pointer',
              }}
            >
              <option value="logo">Logo</option>
              <option value="foto">Foto</option>
              <option value="text">Text</option>
              <option value="zugangsdaten">Zugangsdaten</option>
              <option value="sonstiges">Sonstiges</option>
            </select>
            <input
              type="text"
              placeholder="Notiz (optional)"
              value={note}
              onChange={(e) => setNote(e.target.value)}
              style={{
                flex: 1, padding: '8px 10px', fontSize: 13,
                border: '0.5px solid var(--border-light)', borderRadius: 'var(--radius-md)',
                background: 'var(--bg-elevated)', color: 'var(--text-primary)',
                fontFamily: 'var(--font-sans)',
              }}
            />
            <button
              onClick={handleUpload}
              disabled={uploading}
              style={{
                padding: '8px 18px', background: uploading ? 'var(--bg-elevated)' : 'var(--brand-primary)',
                color: uploading ? 'var(--text-tertiary)' : 'var(--text-inverse)',
                border: uploading ? '1px solid var(--border-medium)' : 'none',
                borderRadius: 'var(--radius-md)', fontSize: 13, fontWeight: 600,
                cursor: uploading ? 'not-allowed' : 'pointer', fontFamily: 'var(--font-sans)',
                display: 'flex', alignItems: 'center', gap: 6, flexShrink: 0,
                ...(isMobile ? { width: '100%', justifyContent: 'center' } : {}),
              }}
            >
              {uploading ? (
                <>
                  <span style={{ width: 11, height: 11, borderRadius: '50%', border: '2px solid var(--border-medium)', borderTopColor: 'var(--brand-primary)', animation: 'spin 0.8s linear infinite', display: 'inline-block' }} />
                  Wird hochgeladen…
                </>
              ) : 'Hochladen'}
            </button>
          </div>
        )}

        {/* Progress bar */}
        {uploading && (
          <div style={{ height: 4, background: 'var(--border-light)', borderRadius: 2, overflow: 'hidden' }}>
            <div style={{ height: '100%', width: `${uploadProgress}%`, background: 'var(--brand-primary)', borderRadius: 2, transition: 'width 0.2s' }} />
          </div>
        )}

        {/* Upload error */}
        {uploadError && (
          <div style={{ padding: '8px 12px', background: 'var(--status-danger-bg)', color: 'var(--status-danger-text)', borderRadius: 'var(--radius-md)', fontSize: 12 }}>
            {uploadError}
          </div>
        )}

        {/* Load error */}
        {error && (
          <div style={{ padding: '8px 12px', background: 'var(--status-danger-bg)', color: 'var(--status-danger-text)', borderRadius: 'var(--radius-md)', fontSize: 12 }}>
            {error}
          </div>
        )}

        {/* File list */}
        {loading ? (
          <div style={{ display: 'flex', justifyContent: 'center', padding: '24px 0' }}>
            <div style={{ width: 22, height: 22, borderRadius: '50%', border: '2px solid var(--border-light)', borderTopColor: 'var(--brand-primary)', animation: 'spin 0.8s linear infinite' }} />
          </div>
        ) : files.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '20px 0', color: 'var(--text-tertiary)', fontSize: 13 }}>
            Noch keine Dateien hochgeladen.
          </div>
        ) : (
          <div style={{ overflowX: 'auto', marginTop: 4 }}>
            {/* Table header */}
            <div style={{
              display: 'grid', gridTemplateColumns: '90px 1fr 70px 90px 130px 80px',
              minWidth: 560, gap: 10, padding: '6px 12px',
              fontSize: 10, fontWeight: 600, color: 'var(--text-tertiary)',
              textTransform: 'uppercase', letterSpacing: '0.06em',
              borderBottom: '1px solid var(--border-light)',
            }}>
              <span>Typ</span><span>Dateiname</span><span>Größe</span>
              <span>Von</span><span>Datum</span><span>Aktionen</span>
            </div>

            {files.map(f => {
              const badge = FILE_TYPE_BADGES[f.file_type] || FILE_TYPE_BADGES.sonstiges;
              const isConfirming = confirmDelete === f.id;
              return (
                <div
                  key={f.id}
                  style={{
                    display: 'grid', gridTemplateColumns: '90px 1fr 70px 90px 130px 80px',
                    minWidth: 560, gap: 10, padding: '10px 12px',
                    alignItems: 'center', borderBottom: '1px solid var(--border-light)',
                    transition: 'background var(--transition-fast)',
                  }}
                  onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-app)'}
                  onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                >
                  {/* Type badge */}
                  <span style={{ display: 'inline-block', padding: '2px 8px', borderRadius: 'var(--radius-full)', fontSize: 11, fontWeight: 600, background: badge.bg, color: badge.color }}>
                    {badge.label}
                  </span>

                  {/* Filename + note */}
                  <div style={{ minWidth: 0 }}>
                    <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {f.original_filename}
                    </div>
                    {f.note && (
                      <div style={{ fontSize: 11, color: 'var(--text-tertiary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', marginTop: 1 }}>
                        {f.note}
                      </div>
                    )}
                  </div>

                  {/* Size */}
                  <span style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>{fmtBytes(f.file_size)}</span>

                  {/* Uploader */}
                  <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                    {f.uploaded_by_role === 'admin' ? 'Mitarbeiter' : 'Kunde'}
                  </span>

                  {/* Date */}
                  <span style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>{fmtTs(f.uploaded_at)}</span>

                  {/* Actions */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                    {isConfirming ? (
                      <>
                        <button
                          onClick={() => handleDelete(f.id)}
                          disabled={deleting === f.id}
                          style={{ fontSize: 11, padding: '2px 8px', background: 'var(--status-danger-bg)', color: 'var(--status-danger-text)', border: 'none', borderRadius: 'var(--radius-sm)', cursor: 'pointer', fontWeight: 600, fontFamily: 'var(--font-sans)' }}
                        >
                          {deleting === f.id ? '…' : 'Löschen'}
                        </button>
                        <button
                          onClick={() => setConfirmDelete(null)}
                          style={{ fontSize: 11, padding: '2px 6px', background: 'transparent', border: 'none', color: 'var(--text-tertiary)', cursor: 'pointer', fontFamily: 'var(--font-sans)' }}
                        >Abbruch</button>
                      </>
                    ) : (
                      <>
                        {/* Download */}
                        <button
                          onClick={() => handleDownload(f.id, f.original_filename)}
                          title="Herunterladen"
                          style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--brand-primary)', padding: 4, borderRadius: 'var(--radius-sm)', display: 'flex', alignItems: 'center', transition: 'opacity var(--transition-fast)', opacity: 0.7 }}
                          onMouseEnter={e => e.currentTarget.style.opacity = '1'}
                          onMouseLeave={e => e.currentTarget.style.opacity = '0.7'}
                        >
                          <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M8 2v9M4.5 7.5L8 11l3.5-3.5"/><path d="M2.5 13.5h11"/>
                          </svg>
                        </button>
                        {/* Delete */}
                        <button
                          onClick={() => setConfirmDelete(f.id)}
                          title="Löschen"
                          style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--status-danger-text)', padding: 4, borderRadius: 'var(--radius-sm)', display: 'flex', alignItems: 'center', transition: 'opacity var(--transition-fast)', opacity: 0.6 }}
                          onMouseEnter={e => e.currentTarget.style.opacity = '1'}
                          onMouseLeave={e => e.currentTarget.style.opacity = '0.6'}
                        >
                          <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
                            <path d="M2.5 4h11M6 4V2.5h4V4M4 4l.8 9.5h6.4L12 4"/>
                          </svg>
                        </button>
                      </>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

// ── PageSpeed section component ────────────────────────────────

function PageSpeedSection({ leadId, headers }) {
  const { isMobile } = useScreenSize();
  const [ps, setPs]           = useState(null);
  const [loading, setLoading] = useState(true);
  const [measuring, setMeasuring] = useState(false);
  const [noUrl, setNoUrl]     = useState(false);
  const [error, setError]     = useState(null);

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/leads/${leadId}/pagespeed`, { headers })
      .then(r => r.ok ? r.json() : null)
      .then(data => { if (data && data.checked_at) setPs(data); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [leadId]); // eslint-disable-line

  const measure = async () => {
    setMeasuring(true);
    setError(null);
    setNoUrl(false);
    try {
      const res  = await fetch(`${API_BASE_URL}/api/leads/${leadId}/pagespeed`, { method: 'POST', headers });
      const data = await res.json();
      if (!res.ok) {
        if (data?.detail?.includes('Website-URL')) setNoUrl(true);
        else setError(data?.detail || 'Fehler bei der Messung');
      } else {
        setPs(data);
      }
    } catch { setError('Verbindungsfehler'); }
    setMeasuring(false);
  };

  const vitals = ps ? [
    { key: 'lcp', label: 'LCP', value: ps.lcp_mobile },
    { key: 'cls', label: 'CLS', value: ps.cls_mobile },
    { key: 'inp', label: 'INP', value: ps.inp_mobile },
    { key: 'fcp', label: 'FCP', value: ps.fcp_mobile },
  ] : [];

  return (
    <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', overflow: 'hidden' }}>

      {/* Section header */}
      <div style={{
        padding: isMobile ? '12px 16px' : '16px 20px',
        borderBottom: '1px solid var(--border-light)',
        display: 'flex', alignItems: 'center',
        justifyContent: 'space-between', gap: 10, flexWrap: 'wrap',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 16 }}>⚡</span>
          <span style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>Website-Performance</span>
        </div>
        <button
          onClick={measure}
          disabled={measuring}
          style={{
            padding: '6px 14px',
            background: measuring ? 'var(--bg-elevated)' : 'var(--brand-primary)',
            color: measuring ? 'var(--text-tertiary)' : 'var(--text-inverse)',
            border: measuring ? '1px solid var(--border-medium)' : 'none',
            borderRadius: 'var(--radius-md)', fontSize: 12, fontWeight: 600,
            cursor: measuring ? 'not-allowed' : 'pointer',
            fontFamily: 'var(--font-sans)', transition: 'opacity 0.15s',
            display: 'flex', alignItems: 'center', gap: 6,
            ...(isMobile ? { width: '100%', justifyContent: 'center' } : {}),
          }}
          onMouseEnter={e => { if (!measuring) e.currentTarget.style.opacity = '0.85'; }}
          onMouseLeave={e => { e.currentTarget.style.opacity = '1'; }}
        >
          {measuring ? (
            <>
              <span style={{ display: 'inline-block', width: 11, height: 11, borderRadius: '50%', border: '2px solid var(--border-medium)', borderTopColor: 'var(--brand-primary)', animation: 'spin 0.8s linear infinite', flexShrink: 0 }} />
              Wird gemessen…
            </>
          ) : 'PageSpeed messen'}
        </button>
      </div>

      {/* Body */}
      <div style={{ padding: isMobile ? '16px' : '20px' }}>
        {loading ? (
          <div style={{ display: 'flex', justifyContent: 'center', padding: '24px 0' }}>
            <div style={{ width: 24, height: 24, borderRadius: '50%', border: '2px solid var(--border-light)', borderTopColor: 'var(--brand-primary)', animation: 'spin 0.8s linear infinite' }} />
          </div>
        ) : noUrl ? (
          <div style={{ fontSize: 13, color: 'var(--text-tertiary)', textAlign: 'center', padding: '16px 0' }}>
            Keine Website-URL hinterlegt — PageSpeed-Messung nicht möglich.
          </div>
        ) : error ? (
          <div style={{ fontSize: 12, color: 'var(--status-danger-text)', background: 'var(--status-danger-bg)', borderRadius: 'var(--radius-md)', padding: '10px 14px' }}>
            {error}
          </div>
        ) : !ps ? (
          <div style={{ fontSize: 13, color: 'var(--text-tertiary)', textAlign: 'center', padding: '16px 0' }}>
            Noch keine Messung vorhanden. Klicke auf „PageSpeed messen".
          </div>
        ) : (
          <>
            {/* Score cards — 1 col mobile, 2 col desktop */}
            <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr', gap: 12, marginBottom: 16 }}>
              {[{ label: 'Mobil', score: ps.mobile_score }, { label: 'Desktop', score: ps.desktop_score }].map(({ label, score }) => {
                const c = scoreColor(score);
                return (
                  <div key={label} style={{ background: c.bg, borderRadius: 'var(--radius-lg)', padding: '20px 16px', textAlign: 'center' }}>
                    <div style={{ fontSize: 11, fontWeight: 600, color: c.text, textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 8 }}>{label}</div>
                    <div style={{ fontSize: 42, fontWeight: 700, color: c.text, lineHeight: 1 }}>{score ?? '—'}</div>
                    <div style={{ fontSize: 11, color: c.text, marginTop: 4, opacity: 0.7 }}>/ 100</div>
                  </div>
                );
              })}
            </div>

            {/* Core Web Vitals — 2×2 mobile, 4 desktop */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 10, marginBottom: 14 }}>
              {vitals.map(({ key, label, value }) => {
                const c = vitalColor(key, value);
                return (
                  <div key={key} style={{ background: c.bg, borderRadius: 'var(--radius-md)', padding: '12px 10px', textAlign: 'center' }}>
                    <div style={{ fontSize: 10, fontWeight: 600, color: c.text, textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 6 }}>{label}</div>
                    <div style={{ fontSize: 18, fontWeight: 700, color: c.text, lineHeight: 1.1 }}>{fmtVital(key, value)}</div>
                  </div>
                );
              })}
            </div>

            {ps.checked_at && (
              <div style={{ fontSize: 11, color: 'var(--text-tertiary)', textAlign: 'right' }}>
                Zuletzt gemessen: {fmtTs(ps.checked_at)}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

// ── Linked Project section ─────────────────────────────────────

function LinkedProjectSection({ leadId, headers, navigate }) {
  const [project, setProject]   = useState(null);
  const [loading, setLoading]   = useState(true);
  const [creating, setCreating] = useState(false);
  const [error, setError]       = useState(null);

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/projects/?limit=200`, { headers })
      .then(r => r.json())
      .then(data => {
        const list = Array.isArray(data) ? data : [];
        setProject(list.find(p => String(p.lead_id) === String(leadId)) || null);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [leadId]); // eslint-disable-line

  const createProject = async () => {
    setCreating(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE_URL}/api/projects/from-lead/${leadId}`, { method: 'POST', headers });
      const data = await res.json();
      if (res.ok) { setProject(data); }
      else { setError(data.detail || 'Fehler beim Anlegen des Projekts'); }
    } catch (e) { setError(String(e)); }
    setCreating(false);
  };

  const phaseLabel = (status) => {
    const m = String(status || '').match(/phase_(\d)/);
    return m ? `Phase ${m[1]} von 7` : (status === 'completed' ? 'Abgeschlossen' : status || '–');
  };

  const card = { background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', padding: '14px 16px' };

  if (loading) return null;

  return (
    <div style={card}>
      <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 10 }}>🗂 Verknüpftes Projekt</div>
      {project ? (
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 2 }}>
              {project.project_name || project.company_name || `Projekt #${project.id}`}
            </div>
            <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{phaseLabel(project.status)}</div>
          </div>
          <button onClick={() => navigate(`/app/projects/${project.id}`)} style={{
            padding: '7px 14px', background: 'var(--brand-primary)', color: '#fff',
            border: 'none', borderRadius: 'var(--radius-md)', fontSize: 12, fontWeight: 600,
            cursor: 'pointer', fontFamily: 'var(--font-sans)', flexShrink: 0,
          }}>
            Zum Projekt →
          </button>
        </div>
      ) : (
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
          <div style={{ flex: 1, fontSize: 12, color: 'var(--text-tertiary)' }}>Noch kein Projekt angelegt.</div>
          <button onClick={createProject} disabled={creating} style={{
            padding: '7px 14px', background: 'var(--bg-hover)', color: 'var(--text-secondary)',
            border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)',
            fontSize: 12, fontWeight: 500, cursor: creating ? 'wait' : 'pointer',
            fontFamily: 'var(--font-sans)', flexShrink: 0,
          }}>
            {creating ? 'Wird angelegt…' : '+ Projekt anlegen'}
          </button>
        </div>
      )}
      {error && <div style={{ marginTop: 8, fontSize: 12, color: 'var(--status-danger-text)' }}>❌ {error}</div>}
    </div>
  );
}


// ── CMS Connection section ─────────────────────────────────────

const CMS_OPTIONS = [
  { value: 'wordpress_elementor', label: 'WordPress + Elementor' },
  { value: 'webflow',             label: 'Webflow' },
  { value: 'none',                label: 'Kein CMS' },
];

function CmsConnectionSection({ customerId, headers }) {
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
  const lbl = { fontSize: 11, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 4, display: 'block' };

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
        <select
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
              <input type="url" placeholder="https://meine-seite.de" value={form.cms_url}
                onChange={e => setForm(f => ({ ...f, cms_url: e.target.value }))} style={inp} />
            </div>
          )}

          {/* Username OR Site ID */}
          <div>
            <label style={lbl}>{isWebflow ? 'Site ID' : 'Benutzername'}</label>
            <input type="text"
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
              <input
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
            <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 4 }}>
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
          padding: '8px 16px', background: 'var(--brand-primary)', color: 'white',
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

export default function CustomerDetail() {
  const { customerId } = useParams();
  const navigate       = useNavigate();
  const { token }      = useAuth();
  const { isMobile }   = useScreenSize();
  const h = { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) };

  const [customer, setCustomer]           = useState(null);
  const [loadingCustomer, setLoadingCustomer] = useState(true);
  const [activeTab, setActiveTab]          = useState('dateien');
  // lead_id for PageSpeed — loaded from project, falls back to customerId
  const [leadId, setLeadId] = useState(customerId);

  // Academy state
  const [assigned, setAssigned]     = useState([]);
  const [allCourses, setAllCourses] = useState([]);
  const [loadingAcademy, setLoadingAcademy] = useState(true);
  const [showModal, setShowModal]   = useState(false);
  const [assigning, setAssigning]   = useState(null);
  const [removing, setRemoving]     = useState(null);
  const [isDesignerOpen, setIsDesignerOpen] = useState(false);

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/leads/${customerId}`, { headers: h })
      .then(r => r.json()).then(setCustomer).catch(console.error)
      .finally(() => setLoadingCustomer(false));
    // Try to resolve the real lead_id via the linked project
    fetch(`${API_BASE_URL}/api/projects/?limit=200`, { headers: h })
      .then(r => r.ok ? r.json() : [])
      .then(projects => {
        const linked = Array.isArray(projects)
          ? projects.find(p => String(p.lead_id) === String(customerId))
          : null;
        if (linked?.lead_id) setLeadId(linked.lead_id);
      })
      .catch(() => {}); // fallback stays as customerId
  }, [customerId]); // eslint-disable-line

  useEffect(() => {
    Promise.all([
      fetch(`${API_BASE_URL}/api/academy/customer/${customerId}/courses`, { headers: h }).then(r => r.json()),
      fetch(`${API_BASE_URL}/api/academy/courses`, { headers: h }).then(r => r.json()),
    ])
      .then(([assignedData, coursesData]) => {
        setAssigned(Array.isArray(assignedData) ? assignedData : []);
        setAllCourses(Array.isArray(coursesData) ? coursesData : []);
      })
      .catch(console.error)
      .finally(() => setLoadingAcademy(false));
  }, [customerId]); // eslint-disable-line

  const handleAssign = async (courseId) => {
    setAssigning(courseId);
    try {
      const res = await fetch(`${API_BASE_URL}/api/academy/customer/${customerId}/courses/${courseId}/assign`, { method: 'POST', headers: h });
      if (res.ok) {
        const data = await res.json();
        setAssigned(prev => [...prev, { ...data, progress_pct: 0, total_lessons: 0, completed: 0, certificate_code: null }]);
      }
    } catch (e) { console.error(e); }
    setAssigning(null);
    setShowModal(false);
  };

  const handleRemove = async (courseId) => {
    setRemoving(courseId);
    try {
      const res = await fetch(`${API_BASE_URL}/api/academy/customer/${customerId}/courses/${courseId}`, { method: 'DELETE', headers: h });
      if (res.ok) setAssigned(prev => prev.filter(a => a.course_id !== courseId));
    } catch (e) { console.error(e); }
    setRemoving(null);
  };

  const assignedIds = new Set(assigned.map(a => a.course_id));
  const available   = allCourses.filter(c => {
    const aud = c.target_audience || c.audience;
    return !assignedIds.has(c.id) && (aud === 'customer' || aud === 'both');
  });

  if (loadingCustomer) return (
    <div style={{ display: 'flex', justifyContent: 'center', padding: '80px 0' }}>
      <div style={{ width: 28, height: 28, borderRadius: '50%', border: '3px solid var(--border-light)', borderTopColor: 'var(--brand-primary)', animation: 'spin 0.8s linear infinite' }} />
    </div>
  );

  return (
    // SCHRITT 8 — bottom nav clearance on mobile
    <div style={{ display: 'flex', flexDirection: 'column', gap: isMobile ? 16 : 24, paddingBottom: isMobile ? 80 : 0 }}>

      {/* ── SCHRITT 2 — Header ── */}
      <div style={{
        display: 'flex',
        flexDirection: isMobile ? 'column' : 'row',
        alignItems: isMobile ? 'flex-start' : 'center',
        justifyContent: 'space-between',
        gap: isMobile ? 8 : 12,
      }}>
        {/* Back + name */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, minWidth: 0, flex: 1 }}>
          <button
            onClick={() => navigate(-1)}
            style={{ background: 'none', border: 'none', color: 'var(--text-tertiary)', cursor: 'pointer', fontSize: 13, fontFamily: 'var(--font-sans)', padding: 0, display: 'flex', alignItems: 'center', gap: 4, flexShrink: 0 }}
          >← Zurück</button>
          <span style={{ color: 'var(--border-medium)' }}>·</span>
          <h1 style={{ fontSize: isMobile ? 17 : 20, fontWeight: 700, color: 'var(--text-primary)', margin: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {customer?.contact_name || customer?.company_name || `Kunde #${customerId}`}
          </h1>
        </div>

        {/* Aktionsleiste */}
        <button
          onClick={() => setIsDesignerOpen(true)}
          style={{
            padding: '8px 16px', border: 'none', borderRadius: 'var(--radius-md)',
            background: 'var(--brand-primary)', color: '#fff',
            fontSize: 13, fontWeight: 600, cursor: 'pointer',
            fontFamily: 'var(--font-sans)', whiteSpace: 'nowrap', flexShrink: 0,
          }}
        >
          🌐 Website erstellen
        </button>
      </div>

      {/* ── Verknüpftes Projekt ── */}
      <LinkedProjectSection leadId={customerId} headers={h} navigate={navigate} />

      {/* ── Tab navigation ── */}
      <div className="kc-tab-nav" style={{ display: 'flex', gap: 4, borderBottom: '1px solid var(--border-light)', paddingBottom: 0 }}>
        {[
          { id: 'dateien',   label: 'Dateien',   icon: '📎' },
          { id: 'audits',    label: 'Audits',    icon: '📋' },
          { id: 'pagespeed', label: 'PageSpeed', icon: '⚡' },
          { id: 'akademy',   label: 'Akademy',   icon: '🎓' },
          { id: 'cms',       label: 'CMS',       icon: '🔌' },
        ].map(({ id, label, icon }) => (
          <button
            key={id}
            onClick={() => setActiveTab(id)}
            style={{
              padding: '8px 14px', border: 'none', background: 'none', cursor: 'pointer',
              fontSize: 13, fontWeight: activeTab === id ? 600 : 400, fontFamily: 'var(--font-sans)',
              color: activeTab === id ? 'var(--brand-primary)' : 'var(--text-secondary)',
              borderBottom: activeTab === id ? '2px solid var(--brand-primary)' : '2px solid transparent',
              marginBottom: -1, whiteSpace: 'nowrap', transition: 'color var(--transition-fast)',
              display: 'flex', alignItems: 'center', gap: 6,
            }}
          >
            <span>{icon}</span>{label}
          </button>
        ))}
      </div>

      {/* ── Tab content ── */}
      {activeTab === 'dateien'   && <ProjectFilesSection customerId={customerId} token={token} />}
      {activeTab === 'audits'    && <AuditHistorySection customerId={customerId} customer={customer} headers={h} />}
      {activeTab === 'pagespeed' && (
        leadId
          ? <PageSpeedSection leadId={leadId} headers={h} />
          : <div style={{ padding: 32, textAlign: 'center', color: 'var(--text-tertiary)', fontSize: 13 }}>Lade Projektdaten…</div>
      )}
      {activeTab === 'cms'       && <CmsConnectionSection customerId={customerId} headers={h} />}
      {activeTab === 'akademy'   && <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', overflow: 'hidden' }}>

        {/* Section header — stacked on mobile */}
        <div style={{
          padding: isMobile ? '12px 16px' : '16px 20px',
          borderBottom: '1px solid var(--border-light)',
          display: 'flex',
          flexDirection: isMobile ? 'column' : 'row',
          alignItems: isMobile ? 'stretch' : 'center',
          justifyContent: 'space-between',
          gap: isMobile ? 10 : 0,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ fontSize: 16 }}>🎓</span>
            <span style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>Akademy</span>
            {!loadingAcademy && assigned.length > 0 && (
              <span style={{ background: 'var(--brand-primary-light)', color: 'var(--brand-primary)', borderRadius: 'var(--radius-full)', fontSize: 11, fontWeight: 600, padding: '2px 8px' }}>
                {assigned.length}
              </span>
            )}
          </div>
          {/* Full-width button on mobile */}
          <button
            onClick={() => setShowModal(true)}
            style={{
              padding: '8px 14px',
              background: 'var(--brand-primary)',
              color: 'var(--text-inverse)',
              border: 'none', borderRadius: 'var(--radius-md)',
              fontSize: 12, fontWeight: 600, cursor: 'pointer',
              fontFamily: 'var(--font-sans)',
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6,
              ...(isMobile ? { width: '100%' } : {}),
            }}
          >+ Kurs zuweisen</button>
        </div>

        {/* SCHRITT 4 — Course table with horizontal scroll */}
        <div style={{ padding: '4px 0' }}>
          {loadingAcademy ? (
            <div style={{ padding: '32px 20px', display: 'flex', justifyContent: 'center' }}>
              <div style={{ width: 24, height: 24, borderRadius: '50%', border: '2px solid var(--border-light)', borderTopColor: 'var(--brand-primary)', animation: 'spin 0.8s linear infinite' }} />
            </div>
          ) : assigned.length === 0 ? (
            <div style={{ padding: '32px 20px', textAlign: 'center', color: 'var(--text-tertiary)' }}>
              <div style={{ fontSize: 36, marginBottom: 8, opacity: 0.3 }}>📚</div>
              <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 4 }}>Noch keine Kurse zugewiesen</div>
              <div style={{ fontSize: 12 }}>Klicke auf „+ Kurs zuweisen" um diesem Kunden Zugriff zu geben.</div>
            </div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              {/* Table header */}
              <div style={{
                display: 'grid', gridTemplateColumns: '1fr 180px 120px 40px',
                minWidth: 520, gap: 12, padding: '8px 20px',
                fontSize: 11, fontWeight: 600, color: 'var(--text-tertiary)',
                textTransform: 'uppercase', letterSpacing: '0.06em',
                borderBottom: '1px solid var(--border-light)',
              }}>
                <span>Kurs</span><span>Fortschritt</span><span>Zertifikat</span><span />
              </div>

              {assigned.map(row => (
                <div
                  key={row.course_id}
                  style={{
                    display: 'grid', gridTemplateColumns: '1fr 180px 120px 40px',
                    minWidth: 520, gap: 12, padding: '12px 20px',
                    alignItems: 'center', borderBottom: '1px solid var(--border-light)',
                    transition: 'background 0.1s',
                  }}
                  onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-app)'}
                  onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                >
                  {/* Course name */}
                  <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)', lineHeight: 1.3 }}>
                    {row.course_title}
                    {row.assigned_at && (
                      <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 2 }}>Zugewiesen: {row.assigned_at}</div>
                    )}
                  </div>

                  {/* Progress bar */}
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                      <span style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>
                        {row.total_lessons > 0 ? `${row.completed}/${row.total_lessons}` : '—'}
                      </span>
                      <span style={{ fontSize: 10, fontWeight: 600, color: row.progress_pct === 100 ? 'var(--status-success-text)' : 'var(--text-tertiary)' }}>
                        {row.progress_pct}%
                      </span>
                    </div>
                    <div style={{ height: 5, background: 'var(--border-light)', borderRadius: 3, overflow: 'hidden' }}>
                      <div style={{ width: `${row.progress_pct}%`, height: '100%', background: row.progress_pct === 100 ? 'var(--status-success-text)' : 'var(--brand-primary)', borderRadius: 3, transition: 'width 0.4s' }} />
                    </div>
                  </div>

                  {/* Certificate */}
                  <div>
                    {row.certificate_code ? (
                      <a
                        href={`/academy/certificate/${row.certificate_code}`}
                        target="_blank" rel="noreferrer"
                        style={{
                          display: 'inline-flex', alignItems: 'center', gap: 4,
                          padding: '3px 10px',
                          background: 'var(--status-success-bg)',
                          color: 'var(--status-success-text)',
                          borderRadius: 'var(--radius-full)', fontSize: 11, fontWeight: 700,
                          textDecoration: 'none',
                        }}
                      >🏆 Zertifikat</a>
                    ) : (
                      <span style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>—</span>
                    )}
                  </div>

                  {/* Remove button */}
                  <button
                    onClick={() => handleRemove(row.course_id)}
                    disabled={removing === row.course_id}
                    title="Kurs entfernen"
                    style={{
                      background: 'none', border: 'none', cursor: 'pointer',
                      color: 'var(--status-danger-text)', padding: 4,
                      borderRadius: 'var(--radius-sm)',
                      opacity: removing === row.course_id ? 0.4 : 0.6,
                      display: 'flex', alignItems: 'center', transition: 'opacity 0.15s',
                    }}
                    onMouseEnter={e => e.currentTarget.style.opacity = '1'}
                    onMouseLeave={e => e.currentTarget.style.opacity = removing === row.course_id ? '0.4' : '0.6'}
                  >
                    <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
                      <path d="M2.5 4h11M6 4V2.5h4V4M4 4l.8 9.5h6.4L12 4"/>
                    </svg>
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>}

      {/* ── SCHRITT 6 — Assign Modal ── */}
      {showModal && (
        <>
          {/* Backdrop */}
          <div
            style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', zIndex: 100 }}
            onClick={() => setShowModal(false)}
          />

          {/* Modal — slides from bottom on mobile, centered on desktop */}
          <div style={isMobile ? {
            position: 'fixed', bottom: 0, left: 0, right: 0,
            background: 'var(--bg-surface)',
            borderRadius: '16px 16px 0 0',
            boxShadow: '0 -8px 32px rgba(0,0,0,0.18)',
            maxHeight: '80vh',
            display: 'flex', flexDirection: 'column', zIndex: 101,
          } : {
            position: 'fixed', top: '50%', left: '50%', transform: 'translate(-50%,-50%)',
            background: 'var(--bg-surface)',
            borderRadius: 'var(--radius-xl)',
            boxShadow: '0 20px 60px rgba(0,0,0,0.18)',
            width: 480, maxWidth: '90vw', maxHeight: '70vh',
            display: 'flex', flexDirection: 'column', zIndex: 101,
          }}>
            {/* Drag handle (mobile only) */}
            {isMobile && (
              <div style={{ display: 'flex', justifyContent: 'center', padding: '12px 0 0' }}>
                <div style={{ width: 36, height: 4, background: 'var(--border-medium)', borderRadius: 2 }} />
              </div>
            )}

            <div style={{ padding: isMobile ? '14px 16px' : '18px 20px', borderBottom: '1px solid var(--border-light)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' }}>Kurs zuweisen</span>
              <button onClick={() => setShowModal(false)} style={{ background: 'none', border: 'none', fontSize: 18, cursor: 'pointer', color: 'var(--text-tertiary)', lineHeight: 1 }}>×</button>
            </div>

            <div style={{ flex: 1, overflowY: 'auto', padding: 8 }}>
              {available.length === 0 ? (
                <div style={{ padding: '32px 20px', textAlign: 'center', color: 'var(--text-tertiary)', fontSize: 13 }}>
                  Alle verfügbaren Kurse wurden bereits zugewiesen.
                </div>
              ) : available.map(course => (
                <button
                  key={course.id}
                  onClick={() => handleAssign(course.id)}
                  disabled={assigning === course.id}
                  style={{
                    width: '100%', display: 'flex', alignItems: 'center', gap: 12,
                    padding: isMobile ? '14px 12px' : '12px 14px',
                    background: 'transparent', border: 'none',
                    borderRadius: 'var(--radius-md)', cursor: 'pointer', textAlign: 'left',
                    transition: 'background 0.1s', opacity: assigning === course.id ? 0.6 : 1,
                  }}
                  onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-app)'}
                  onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                >
                  <div style={{
                    width: 40, height: 40, borderRadius: 'var(--radius-md)', flexShrink: 0,
                    background: course.thumbnail_url ? `url(${course.thumbnail_url}) center/cover` : 'linear-gradient(135deg, var(--brand-primary), var(--brand-primary-deeper))',
                    display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 18,
                  }}>
                    {!course.thumbnail_url && '🎓'}
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 2 }}>{course.title}</div>
                    <div style={{ fontSize: 11, color: 'var(--text-tertiary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{course.description}</div>
                  </div>
                  <span style={{ fontSize: 12, color: 'var(--brand-primary)', fontWeight: 600, flexShrink: 0 }}>
                    {assigning === course.id ? '…' : '+ Zuweisen'}
                  </span>
                </button>
              ))}
            </div>
          </div>
        </>
      )}

      {isDesignerOpen && (
        <WebsiteDesigner
          customerId={customerId}
          customerName={customer?.contact_name || customer?.company_name}
          onClose={() => setIsDesignerOpen(false)}
        />
      )}
    </div>
  );
}

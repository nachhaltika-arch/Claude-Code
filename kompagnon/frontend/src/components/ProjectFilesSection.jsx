import { useState, useEffect, useRef, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { useScreenSize } from '../utils/responsive';
import API_BASE_URL from '../config';

function fmtBytes(bytes) {
  if (!bytes) return '0 B';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function fmtTs(iso) {
  if (!iso) return null;
  const d = new Date(iso);
  return d.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' })
    + ' ' + d.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' }) + ' Uhr';
}

const FILE_TYPE_BADGES = {
  logo:         { label: 'Logo',         bg: 'var(--status-info-bg)',    color: 'var(--status-info-text)' },
  foto:         { label: 'Foto',         bg: 'var(--status-success-bg)', color: 'var(--status-success-text)' },
  text:         { label: 'Text',         bg: 'var(--status-neutral-bg)', color: 'var(--status-neutral-text)' },
  zugangsdaten: { label: 'Zugangsdaten', bg: 'var(--status-warning-bg)', color: 'var(--status-warning-text)' },
  sonstiges:    { label: 'Sonstiges',    bg: 'var(--status-neutral-bg)', color: 'var(--status-neutral-text)' },
};

export default function ProjectFilesSection({ leadId }) {
  const { token } = useAuth();
  const { isMobile } = useScreenSize();
  const fileInputRef = useRef(null);

  const [files, setFiles]         = useState([]);
  const [loading, setLoading]     = useState(true);
  const [error, setError]         = useState(null);
  const [pendingFile, setPendingFile]   = useState(null);
  const [fileType, setFileType]         = useState('sonstiges');
  const [note, setNote]                 = useState('');
  const [uploading, setUploading]       = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadError, setUploadError]   = useState(null);
  const [dragOver, setDragOver]         = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(null);
  const [deleting, setDeleting]           = useState(null);

  const authHeaders = token ? { Authorization: `Bearer ${token}` } : {};

  const fetchFiles = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/files/${leadId}`, { headers: authHeaders });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setFiles(Array.isArray(data) ? data : []);
      setError(null);
    } catch {
      setError('Dateien konnten nicht geladen werden.');
    } finally {
      setLoading(false);
    }
  }, [leadId]); // eslint-disable-line

  useEffect(() => { setLoading(true); fetchFiles(); }, [leadId]); // eslint-disable-line

  const pickFile = (f) => { if (f) { setPendingFile(f); setUploadError(null); } };

  const handleDrop = (e) => {
    e.preventDefault(); setDragOver(false);
    const f = e.dataTransfer.files[0]; if (f) pickFile(f);
  };

  const handleUpload = () => {
    if (!pendingFile) return;
    setUploading(true); setUploadProgress(0); setUploadError(null);
    const form = new FormData();
    form.append('file', pendingFile);
    form.append('file_type', fileType);
    form.append('note', note);
    const xhr = new XMLHttpRequest();
    xhr.open('POST', `${API_BASE_URL}/api/files/upload/${leadId}`);
    if (token) xhr.setRequestHeader('Authorization', `Bearer ${token}`);
    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) setUploadProgress(Math.round((e.loaded / e.total) * 100));
    };
    xhr.onload = () => {
      setUploading(false);
      if (xhr.status >= 200 && xhr.status < 300) {
        setPendingFile(null); setNote(''); setFileType('sonstiges'); setUploadProgress(0);
        fetchFiles();
      } else {
        try { setUploadError(JSON.parse(xhr.responseText).detail || 'Upload fehlgeschlagen.'); }
        catch { setUploadError('Upload fehlgeschlagen.'); }
      }
    };
    xhr.onerror = () => { setUploading(false); setUploadError('Verbindungsfehler beim Upload.'); };
    xhr.send(form);
  };

  const handleDelete = async (fileId) => {
    setDeleting(fileId);
    try {
      const res = await fetch(`${API_BASE_URL}/api/files/${fileId}`, { method: 'DELETE', headers: authHeaders });
      if (res.ok) setFiles(prev => prev.filter(f => f.id !== fileId));
    } catch { /* ignore */ }
    setDeleting(null); setConfirmDelete(null);
  };

  const handleDownload = (fileId) => {
    const a = document.createElement('a');
    a.href = `${API_BASE_URL}/api/files/download/${fileId}`;
    a.target = '_blank'; a.rel = 'noreferrer';
    document.body.appendChild(a); a.click(); document.body.removeChild(a);
  };

  const dropZoneStyle = {
    border: `1.5px dashed ${dragOver ? 'var(--brand-primary)' : 'var(--border-medium)'}`,
    borderRadius: 'var(--radius-lg)',
    padding: isMobile ? '20px 16px' : '28px 20px',
    textAlign: 'center', cursor: 'pointer',
    background: dragOver ? 'var(--bg-active)' : 'var(--bg-app)',
    transition: 'border-color var(--transition-fast), background var(--transition-fast)',
  };

  return (
    <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', overflow: 'hidden' }}>
      {/* Header */}
      <div style={{ padding: isMobile ? '12px 16px' : '16px 20px', borderBottom: '1px solid var(--border-light)', display: 'flex', flexDirection: isMobile ? 'column' : 'row', alignItems: isMobile ? 'stretch' : 'center', justifyContent: 'space-between', gap: isMobile ? 10 : 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 16 }}>📁</span>
          <span style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>Projektdateien</span>
          {!loading && files.length > 0 && (
            <span style={{ background: 'var(--brand-primary-light)', color: 'var(--brand-primary)', borderRadius: 'var(--radius-full)', fontSize: 11, fontWeight: 600, padding: '2px 8px' }}>{files.length}</span>
          )}
        </div>
        <button
          onClick={() => fileInputRef.current?.click()}
          style={{ padding: '8px 14px', background: 'var(--brand-primary)', color: 'var(--text-inverse)', border: 'none', borderRadius: 'var(--radius-md)', fontSize: 12, fontWeight: 600, cursor: 'pointer', fontFamily: 'var(--font-sans)', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6, ...(isMobile ? { width: '100%' } : {}) }}
        >+ Datei hochladen</button>
      </div>

      <div style={{ padding: isMobile ? 16 : 20, display: 'flex', flexDirection: 'column', gap: 12 }}>
        {/* Drop zone */}
        <div style={dropZoneStyle} onDragOver={(e) => { e.preventDefault(); setDragOver(true); }} onDragLeave={() => setDragOver(false)} onDrop={handleDrop} onClick={() => fileInputRef.current?.click()}>
          <input ref={fileInputRef} type="file" style={{ display: 'none' }} accept=".jpg,.jpeg,.png,.gif,.pdf,.doc,.docx,.txt,.zip,.svg,.ai,.eps" onChange={(e) => pickFile(e.target.files[0])} />
          {pendingFile ? (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8 }}>
              <span style={{ fontSize: 20 }}>📄</span>
              <div style={{ textAlign: 'left' }}>
                <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>{pendingFile.name}</div>
                <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>{fmtBytes(pendingFile.size)}</div>
              </div>
              <button onClick={(e) => { e.stopPropagation(); setPendingFile(null); }} style={{ marginLeft: 8, background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-tertiary)', fontSize: 16 }}>×</button>
            </div>
          ) : (
            <>
              <div style={{ fontSize: 28, marginBottom: 8, opacity: 0.3 }}>📂</div>
              <div style={{ fontSize: 13, color: 'var(--text-secondary)', fontWeight: 500 }}>Dateien hier ablegen oder klicken</div>
              <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 4 }}>JPG, PNG, PDF, DOC, ZIP, SVG, AI, EPS — max. 20 MB</div>
            </>
          )}
        </div>

        {/* Options row */}
        {pendingFile && (
          <div style={{ display: 'flex', flexDirection: isMobile ? 'column' : 'row', gap: 8 }}>
            <select value={fileType} onChange={(e) => setFileType(e.target.value)} style={{ flex: '0 0 160px', padding: '8px 10px', fontSize: 13, border: '0.5px solid var(--border-light)', borderRadius: 'var(--radius-md)', background: 'var(--bg-elevated)', color: 'var(--text-primary)', fontFamily: 'var(--font-sans)', cursor: 'pointer' }}>
              <option value="logo">Logo</option>
              <option value="foto">Foto</option>
              <option value="text">Text</option>
              <option value="zugangsdaten">Zugangsdaten</option>
              <option value="sonstiges">Sonstiges</option>
            </select>
            <input type="text" placeholder="Notiz (optional)" value={note} onChange={(e) => setNote(e.target.value)} style={{ flex: 1, padding: '8px 10px', fontSize: 13, border: '0.5px solid var(--border-light)', borderRadius: 'var(--radius-md)', background: 'var(--bg-elevated)', color: 'var(--text-primary)', fontFamily: 'var(--font-sans)' }} />
            <button onClick={handleUpload} disabled={uploading} style={{ padding: '8px 18px', background: uploading ? 'var(--bg-elevated)' : 'var(--brand-primary)', color: uploading ? 'var(--text-tertiary)' : 'var(--text-inverse)', border: uploading ? '1px solid var(--border-medium)' : 'none', borderRadius: 'var(--radius-md)', fontSize: 13, fontWeight: 600, cursor: uploading ? 'not-allowed' : 'pointer', fontFamily: 'var(--font-sans)', display: 'flex', alignItems: 'center', gap: 6, flexShrink: 0, ...(isMobile ? { width: '100%', justifyContent: 'center' } : {}) }}>
              {uploading ? (<><span style={{ width: 11, height: 11, borderRadius: '50%', border: '2px solid var(--border-medium)', borderTopColor: 'var(--brand-primary)', animation: 'spin 0.8s linear infinite', display: 'inline-block' }} />Wird hochgeladen…</>) : 'Hochladen'}
            </button>
          </div>
        )}

        {uploading && (
          <div style={{ height: 4, background: 'var(--border-light)', borderRadius: 2, overflow: 'hidden' }}>
            <div style={{ height: '100%', width: `${uploadProgress}%`, background: 'var(--brand-primary)', borderRadius: 2, transition: 'width 0.2s' }} />
          </div>
        )}
        {uploadError && <div style={{ padding: '8px 12px', background: 'var(--status-danger-bg)', color: 'var(--status-danger-text)', borderRadius: 'var(--radius-md)', fontSize: 12 }}>{uploadError}</div>}
        {error && <div style={{ padding: '8px 12px', background: 'var(--status-danger-bg)', color: 'var(--status-danger-text)', borderRadius: 'var(--radius-md)', fontSize: 12 }}>{error}</div>}

        {/* File list */}
        {loading ? (
          <div style={{ display: 'flex', justifyContent: 'center', padding: '24px 0' }}>
            <div style={{ width: 22, height: 22, borderRadius: '50%', border: '2px solid var(--border-light)', borderTopColor: 'var(--brand-primary)', animation: 'spin 0.8s linear infinite' }} />
          </div>
        ) : files.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '20px 0', color: 'var(--text-tertiary)', fontSize: 13 }}>Noch keine Dateien hochgeladen.</div>
        ) : (
          <div style={{ overflowX: 'auto', marginTop: 4 }}>
            <div style={{ display: 'grid', gridTemplateColumns: '90px 1fr 70px 90px 130px 80px', minWidth: 560, gap: 10, padding: '6px 12px', fontSize: 10, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', borderBottom: '1px solid var(--border-light)' }}>
              <span>Typ</span><span>Dateiname</span><span>Größe</span><span>Von</span><span>Datum</span><span>Aktionen</span>
            </div>
            {files.map(f => {
              const badge = FILE_TYPE_BADGES[f.file_type] || FILE_TYPE_BADGES.sonstiges;
              const isConfirming = confirmDelete === f.id;
              return (
                <div key={f.id} style={{ display: 'grid', gridTemplateColumns: '90px 1fr 70px 90px 130px 80px', minWidth: 560, gap: 10, padding: '10px 12px', alignItems: 'center', borderBottom: '1px solid var(--border-light)', transition: 'background var(--transition-fast)' }} onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-app)'} onMouseLeave={e => e.currentTarget.style.background = 'transparent'}>
                  <span style={{ display: 'inline-block', padding: '2px 8px', borderRadius: 'var(--radius-full)', fontSize: 11, fontWeight: 600, background: badge.bg, color: badge.color }}>{badge.label}</span>
                  <div style={{ minWidth: 0 }}>
                    <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{f.original_filename}</div>
                    {f.note && <div style={{ fontSize: 11, color: 'var(--text-tertiary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', marginTop: 1 }}>{f.note}</div>}
                  </div>
                  <span style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>{fmtBytes(f.file_size)}</span>
                  <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{f.uploaded_by_role === 'admin' ? 'Mitarbeiter' : 'Kunde'}</span>
                  <span style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>{fmtTs(f.uploaded_at)}</span>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                    {isConfirming ? (
                      <>
                        <button onClick={() => handleDelete(f.id)} disabled={deleting === f.id} style={{ fontSize: 11, padding: '2px 8px', background: 'var(--status-danger-bg)', color: 'var(--status-danger-text)', border: 'none', borderRadius: 'var(--radius-sm)', cursor: 'pointer', fontWeight: 600, fontFamily: 'var(--font-sans)' }}>{deleting === f.id ? '…' : 'Löschen'}</button>
                        <button onClick={() => setConfirmDelete(null)} style={{ fontSize: 11, padding: '2px 6px', background: 'transparent', border: 'none', color: 'var(--text-tertiary)', cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>Abbruch</button>
                      </>
                    ) : (
                      <>
                        <button onClick={() => handleDownload(f.id)} title="Herunterladen" style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--brand-primary)', padding: 4, borderRadius: 'var(--radius-sm)', display: 'flex', alignItems: 'center', opacity: 0.7 }} onMouseEnter={e => e.currentTarget.style.opacity = '1'} onMouseLeave={e => e.currentTarget.style.opacity = '0.7'}>
                          <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M8 2v9M4.5 7.5L8 11l3.5-3.5"/><path d="M2.5 13.5h11"/></svg>
                        </button>
                        <button onClick={() => setConfirmDelete(f.id)} title="Löschen" style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--status-danger-text)', padding: 4, borderRadius: 'var(--radius-sm)', display: 'flex', alignItems: 'center', opacity: 0.6 }} onMouseEnter={e => e.currentTarget.style.opacity = '1'} onMouseLeave={e => e.currentTarget.style.opacity = '0.6'}>
                          <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"><path d="M2.5 4h11M6 4V2.5h4V4M4 4l.8 9.5h6.4L12 4"/></svg>
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

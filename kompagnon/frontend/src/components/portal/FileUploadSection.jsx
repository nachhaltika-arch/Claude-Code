/**
 * Der Dateibereich des Kundenportals (L-25).
 *
 * Am 2026-08-30 aus `CustomerPortal.jsx` herausgeloest — 300 der damals 986
 * Zeilen. Sie war dort schon eine eigene Funktion.
 */
import { useEffect, useRef, useState } from 'react';
import API_BASE_URL from '../../config';
import { datumKurz } from '../../utils/datum';

const FILE_TYPE_COLORS = {
  logo: { bg: 'var(--status-info-bg)', color: 'var(--status-info-text)' },
  foto: { bg: 'var(--status-success-bg)', color: 'var(--status-success-text)' },
  text: { bg: 'var(--status-neutral-bg)', color: 'var(--status-neutral-text)' },
  zugangsdaten: { bg: 'var(--status-warning-bg)', color: 'var(--status-warning-text)' },
  sonstiges: { bg: 'var(--status-neutral-bg)', color: 'var(--status-neutral-text)' },
};
const FILE_TYPE_LABELS = {
  logo: 'Logo',
  foto: 'Foto',
  text: 'Text',
  zugangsdaten: 'Zugangsdaten',
  sonstiges: 'Sonstiges',
};


export function FileUploadSection({ token }) {
  const fileInputRef = useRef(null);
  const [files, setFiles] = useState([]);
  const [loadingFiles, setLoadingFiles] = useState(true);
  const [dragOver, setDragOver] = useState(false);
  const [pendingFile, setPendingFile] = useState(null);
  const [fileType, setFileType] = useState('sonstiges');
  const [note, setNote] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [successMsg, setSuccessMsg] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  const loadFiles = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/files/portal/${token}`);
      if (res.ok) setFiles(await res.json());
    } catch { /* ignore */ }
    finally { setLoadingFiles(false); }
  };

  useEffect(() => { loadFiles(); }, [token]); // eslint-disable-line

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const f = e.dataTransfer.files[0];
    if (f) setPendingFile(f);
  };

  const handleFileInput = (e) => {
    const f = e.target.files[0];
    if (f) setPendingFile(f);
  };

  const handleUpload = () => {
    if (!pendingFile) return;
    setUploading(true);
    setUploadProgress(0);
    setErrorMsg('');
    setSuccessMsg('');

    const form = new FormData();
    form.append('file', pendingFile);
    form.append('file_type', fileType);
    form.append('note', note);

    const xhr = new XMLHttpRequest();
    xhr.open('POST', `${API_BASE_URL}/api/files/portal/${token}/upload`);
    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) setUploadProgress(Math.round((e.loaded / e.total) * 100));
    };
    xhr.onload = () => {
      setUploading(false);
      if (xhr.status >= 200 && xhr.status < 300) {
        setPendingFile(null);
        setFileType('sonstiges');
        setNote('');
        setUploadProgress(0);
        setSuccessMsg(`"${pendingFile.name}" wurde erfolgreich eingereicht.`);
        loadFiles();
        setTimeout(() => setSuccessMsg(''), 4000);
      } else {
        try {
          const err = JSON.parse(xhr.responseText);
          setErrorMsg(err.detail || 'Upload fehlgeschlagen');
        } catch { setErrorMsg('Upload fehlgeschlagen'); }
      }
    };
    xhr.onerror = () => { setUploading(false); setErrorMsg('Verbindungsfehler'); };
    xhr.send(form);
  };

  const formatSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const checklist = [
    { key: 'logo', label: 'Logo (SVG, AI, EPS, PNG)', icon: '🎨' },
    { key: 'foto', label: 'Fotos (JPG, PNG)', icon: '📷' },
    { key: 'text', label: 'Texte & Inhalte (DOCX, TXT)', icon: '📝' },
    { key: 'zugangsdaten', label: 'Zugangsdaten (ZIP, TXT)', icon: '🔑' },
  ];

  const uploadedTypes = new Set(files.map(f => f.file_type));

  return (
    <div style={{ marginBottom: 16 }}>
      {/* Header */}
      <div style={{ background: 'var(--bg-surface)', borderRadius: 12, padding: 20, marginBottom: 12, boxShadow: '0 1px 4px rgba(0,0,0,0.06)' }}>
        <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 10 }}>
          Unterlagen einreichen
        </div>
        <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6, margin: '0 0 14px' }}>
          Laden Sie hier die benötigten Unterlagen hoch, damit wir Ihre Website optimieren können.
        </p>
        {/* Checklist */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          {checklist.map(({ key, label, icon }) => {
            const done = uploadedTypes.has(key);
            return (
              <div key={key} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12 }}>
                <span style={{
                  width: 18, height: 18, borderRadius: '50%', flexShrink: 0,
                  background: done ? 'var(--status-success-bg)' : 'var(--bg-app)',
                  color: done ? 'var(--status-success-text)' : 'var(--text-tertiary)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 11, fontWeight: 700,
                }}>
                  {done ? '✓' : '○'}
                </span>
                <span style={{ color: done ? 'var(--status-success-text)' : 'var(--text-secondary)' }}>{icon} {label}</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Upload zone */}
      <div style={{ background: 'var(--bg-surface)', borderRadius: 12, padding: 20, marginBottom: 12, boxShadow: '0 1px 4px rgba(0,0,0,0.06)' }}>
        {successMsg && (
          <div style={{ background: 'var(--status-success-bg)', color: 'var(--status-success-text)', borderRadius: 8, padding: '10px 14px', fontSize: 12, marginBottom: 14 }}>
            ✓ {successMsg}
          </div>
        )}
        {errorMsg && (
          <div style={{ background: 'var(--status-danger-bg)', color: 'var(--status-danger-text)', borderRadius: 8, padding: '10px 14px', fontSize: 12, marginBottom: 14 }}>
            {errorMsg}
          </div>
        )}

        {/* Drop zone */}
        <div
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          onClick={() => !pendingFile && fileInputRef.current?.click()}
          style={{
            border: `2px dashed ${dragOver ? 'var(--brand-primary)' : pendingFile ? 'var(--success)' : 'var(--border-medium)'}`,
            borderRadius: 10,
            padding: '20px 16px',
            textAlign: 'center',
            cursor: pendingFile ? 'default' : 'pointer',
            background: dragOver ? 'var(--status-info-bg)' : pendingFile ? 'var(--status-success-bg)' : 'var(--bg-app)',
            transition: 'all 150ms ease',
            marginBottom: 14,
          }}
        >
          <input aria-label="Datei auswaehlen" ref={fileInputRef} id="portal-file-input" name="portal-file-input" type="file" style={{ display: 'none' }} onChange={handleFileInput} />
          {pendingFile ? (
            <div>
              <div style={{ fontSize: 22, marginBottom: 4 }}>📎</div>
              <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 2 }}>{pendingFile.name}</div>
              <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>{formatSize(pendingFile.size)}</div>
              <button
                onClick={(e) => { e.stopPropagation(); setPendingFile(null); fileInputRef.current.value = ''; }}
                style={{ marginTop: 8, background: 'none', border: 'none', fontSize: 11, color: 'var(--text-tertiary)', cursor: 'pointer', textDecoration: 'underline' }}
              >
                Andere Datei wählen
              </button>
            </div>
          ) : (
            <div>
              <div style={{ fontSize: 28, marginBottom: 6 }}>📤</div>
              <div style={{ fontSize: 13, color: 'var(--text-secondary)', fontWeight: 500 }}>Datei hierher ziehen oder tippen zum Auswählen</div>
              <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 4 }}>PDF, DOCX, JPG, PNG, SVG, AI, EPS, ZIP — max. 20 MB</div>
            </div>
          )}
        </div>

        {/* File type + note */}
        {pendingFile && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginBottom: 14 }}>
            <div>
              <label style={{ display: 'block', fontSize: 10, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 4 }}>
                Dateityp
              </label>
              <select aria-label="Dateityp"
                id="portal-file-type"
                name="portal-file-type"
                value={fileType}
                onChange={e => setFileType(e.target.value)}
                style={{ width: '100%', padding: '10px 12px', border: '1px solid var(--border-medium)', borderRadius: 8, fontSize: 14, fontFamily: 'inherit', background: 'var(--bg-surface)', color: 'var(--text-primary)', outline: 'none' }}
              >
                {Object.entries(FILE_TYPE_LABELS).map(([k, v]) => (
                  <option key={k} value={k}>{v}</option>
                ))}
              </select>
            </div>
            <div>
              <label style={{ display: 'block', fontSize: 10, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 4 }}>
                Anmerkung (optional)
              </label>
              <input aria-label="Anmerkung (optional)"
                id="portal-file-note"
                name="portal-file-note"
                type="text"
                value={note}
                onChange={e => setNote(e.target.value)}
                placeholder="z.B. Hauptlogo in Farbe"
                style={{ width: '100%', padding: '10px 12px', border: '1px solid var(--border-medium)', borderRadius: 8, fontSize: 14, fontFamily: 'inherit', boxSizing: 'border-box', outline: 'none', color: 'var(--text-primary)' }}
                onFocus={e => e.target.style.borderColor = 'var(--brand-primary-mid)'}
                onBlur={e => e.target.style.borderColor = 'var(--border-medium)'}
              />
            </div>
          </div>
        )}

        {/* Progress bar */}
        {uploading && (
          <div style={{ marginBottom: 14 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: 'var(--text-tertiary)', marginBottom: 4 }}>
              <span>Wird hochgeladen…</span>
              <span>{uploadProgress}%</span>
            </div>
            <div style={{ height: 4, background: 'var(--brand-primary-light)', borderRadius: 2, overflow: 'hidden' }}>
              <div style={{ width: `${uploadProgress}%`, height: '100%', background: 'var(--brand-primary)', borderRadius: 2, transition: 'width 0.2s ease' }} />
            </div>
          </div>
        )}

        <button
          onClick={handleUpload}
          disabled={!pendingFile || uploading}
          style={{
            width: '100%', padding: 12,
            background: 'var(--brand-primary)', opacity: !pendingFile || uploading ? 0.5 : 1,
            color: 'var(--text-on-brand)', border: 'none', borderRadius: 8,
            fontSize: 14, fontWeight: 600,
            cursor: !pendingFile || uploading ? 'not-allowed' : 'pointer',
            fontFamily: 'inherit',
          }}
        >
          {uploading ? 'Wird eingereicht…' : 'Datei einreichen →'}
        </button>
      </div>

      {/* Existing files */}
      <div style={{ background: 'var(--bg-surface)', borderRadius: 12, padding: 20, boxShadow: '0 1px 4px rgba(0,0,0,0.06)' }}>
        <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 12 }}>
          Eingereichte Dateien
        </div>
        {loadingFiles ? (
          <div style={{ color: 'var(--text-tertiary)', fontSize: 13 }}>Wird geladen…</div>
        ) : files.length === 0 ? (
          <div style={{ color: 'var(--text-tertiary)', fontSize: 13 }}>Noch keine Dateien eingereicht.</div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {files.map(f => {
              const tc = FILE_TYPE_COLORS[f.file_type] || FILE_TYPE_COLORS.sonstiges;
              return (
                <div key={f.id} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '8px 0', borderBottom: '1px solid var(--border-light)' }}>
                  <span style={{ fontSize: 16, flexShrink: 0 }}>
                    {f.file_type === 'logo' ? '🎨' : f.file_type === 'foto' ? '📷' : f.file_type === 'text' ? '📝' : f.file_type === 'zugangsdaten' ? '🔑' : '📎'}
                  </span>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 13, color: 'var(--text-secondary)', fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {f.original_filename}
                    </div>
                    <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 2 }}>
                      {datumKurz(f.uploaded_at)} · {formatSize(f.file_size)}
                      {f.note && ` · ${f.note}`}
                    </div>
                  </div>
                  <span style={{
                    flexShrink: 0, background: tc.bg, color: tc.color,
                    borderRadius: 6, fontSize: 10, fontWeight: 600,
                    padding: '2px 7px',
                  }}>
                    {FILE_TYPE_LABELS[f.file_type] || f.file_type}
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

export const PHASEN = [
  { nr: 1, label: 'Onboarding',  icon: '👋', beschreibung: 'Strategie-Workshop & Briefing' },
  { nr: 2, label: 'Briefing',    icon: '📋', beschreibung: 'Inhalte & Ziele festlegen' },
  { nr: 3, label: 'Content',     icon: '✏️', beschreibung: 'Texte, Bilder & Sitemap' },
  { nr: 4, label: 'Technik',     icon: '⚙️', beschreibung: 'Entwicklung & Umsetzung' },
  { nr: 5, label: 'Q&A',         icon: '🔍', beschreibung: 'Qualitätsprüfung & Abnahme' },
  { nr: 6, label: 'Go-Live',     icon: '🚀', beschreibung: 'Website geht online' },
  { nr: 7, label: 'Post-Launch', icon: '⭐', beschreibung: 'Nachbetreuung & Optimierung' },
];

export const getPhaseStatus = (phaseNr, currentPhase) => {
  if (!currentPhase) return 'ausstehend';
  if (phaseNr < currentPhase)  return 'abgeschlossen';
  if (phaseNr === currentPhase) return 'aktiv';
  return 'ausstehend';
};


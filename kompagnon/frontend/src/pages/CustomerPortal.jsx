import { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import API_BASE_URL from '../config';
import Logo from '../components/Logo';

const LEVEL_COLORS = {
  'Homepage Standard Platin': '#4a90d9',
  'Homepage Standard Gold': '#b8860b',
  'Homepage Standard Silber': '#708090',
  'Homepage Standard Bronze': '#cd7f32',
  'Nicht konform': '#b02020',
};

const FILE_TYPE_LABELS = {
  logo: 'Logo',
  foto: 'Foto',
  text: 'Text',
  zugangsdaten: 'Zugangsdaten',
  sonstiges: 'Sonstiges',
};

const FILE_TYPE_COLORS = {
  logo: { bg: '#e3f0fb', color: '#1565c0' },
  foto: { bg: '#e8f5e9', color: '#2e7d32' },
  text: { bg: '#f5f5f5', color: '#424242' },
  zugangsdaten: { bg: '#fff8e1', color: '#e65100' },
  sonstiges: { bg: '#f5f5f5', color: '#616161' },
};

function FileUploadSection({ token }) {
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
        <div style={{ fontSize: 12, fontWeight: 600, color: '#8fa8b0', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 10 }}>
          Unterlagen einreichen
        </div>
        <p style={{ fontSize: 13, color: '#4a6470', lineHeight: 1.6, margin: '0 0 14px' }}>
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
                  background: done ? '#e8f5e9' : '#f0f0f0',
                  color: done ? '#2e7d32' : '#bdbdbd',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 11, fontWeight: 700,
                }}>
                  {done ? '✓' : '○'}
                </span>
                <span style={{ color: done ? '#2e7d32' : '#4a6470' }}>{icon} {label}</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Upload zone */}
      <div style={{ background: 'var(--bg-surface)', borderRadius: 12, padding: 20, marginBottom: 12, boxShadow: '0 1px 4px rgba(0,0,0,0.06)' }}>
        {successMsg && (
          <div style={{ background: '#e8f5e9', color: '#2e7d32', borderRadius: 8, padding: '10px 14px', fontSize: 12, marginBottom: 14 }}>
            ✓ {successMsg}
          </div>
        )}
        {errorMsg && (
          <div style={{ background: '#ffebee', color: '#b02020', borderRadius: 8, padding: '10px 14px', fontSize: 12, marginBottom: 14 }}>
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
            border: `2px dashed ${dragOver ? '#008eaa' : pendingFile ? '#22c55e' : '#d4d8e8'}`,
            borderRadius: 10,
            padding: '20px 16px',
            textAlign: 'center',
            cursor: pendingFile ? 'default' : 'pointer',
            background: dragOver ? '#e0f4f8' : pendingFile ? '#f0fdf4' : 'var(--bg-app)',
            transition: 'all 150ms ease',
            marginBottom: 14,
          }}
        >
          <input ref={fileInputRef} type="file" style={{ display: 'none' }} onChange={handleFileInput} />
          {pendingFile ? (
            <div>
              <div style={{ fontSize: 22, marginBottom: 4 }}>📎</div>
              <div style={{ fontSize: 13, fontWeight: 600, color: '#4a6470', marginBottom: 2 }}>{pendingFile.name}</div>
              <div style={{ fontSize: 11, color: '#8fa8b0' }}>{formatSize(pendingFile.size)}</div>
              <button
                onClick={(e) => { e.stopPropagation(); setPendingFile(null); fileInputRef.current.value = ''; }}
                style={{ marginTop: 8, background: 'none', border: 'none', fontSize: 11, color: '#8fa8b0', cursor: 'pointer', textDecoration: 'underline' }}
              >
                Andere Datei wählen
              </button>
            </div>
          ) : (
            <div>
              <div style={{ fontSize: 28, marginBottom: 6 }}>📤</div>
              <div style={{ fontSize: 13, color: '#4a6470', fontWeight: 500 }}>Datei hierher ziehen oder tippen zum Auswählen</div>
              <div style={{ fontSize: 11, color: '#8fa8b0', marginTop: 4 }}>PDF, DOCX, JPG, PNG, SVG, AI, EPS, ZIP — max. 20 MB</div>
            </div>
          )}
        </div>

        {/* File type + note */}
        {pendingFile && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginBottom: 14 }}>
            <div>
              <label style={{ display: 'block', fontSize: 10, fontWeight: 600, color: '#8fa8b0', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 4 }}>
                Dateityp
              </label>
              <select
                value={fileType}
                onChange={e => setFileType(e.target.value)}
                style={{ width: '100%', padding: '10px 12px', border: '1px solid #d4d8e8', borderRadius: 8, fontSize: 14, fontFamily: 'inherit', background: 'var(--bg-surface)', color: 'var(--text-primary)', outline: 'none' }}
              >
                {Object.entries(FILE_TYPE_LABELS).map(([k, v]) => (
                  <option key={k} value={k}>{v}</option>
                ))}
              </select>
            </div>
            <div>
              <label style={{ display: 'block', fontSize: 10, fontWeight: 600, color: '#8fa8b0', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 4 }}>
                Anmerkung (optional)
              </label>
              <input
                type="text"
                value={note}
                onChange={e => setNote(e.target.value)}
                placeholder="z.B. Hauptlogo in Farbe"
                style={{ width: '100%', padding: '10px 12px', border: '1px solid #d4d8e8', borderRadius: 8, fontSize: 14, fontFamily: 'inherit', boxSizing: 'border-box', outline: 'none', color: 'var(--text-primary)' }}
                onFocus={e => e.target.style.borderColor = '#008eaa'}
                onBlur={e => e.target.style.borderColor = '#d4d8e8'}
              />
            </div>
          </div>
        )}

        {/* Progress bar */}
        {uploading && (
          <div style={{ marginBottom: 14 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: '#8fa8b0', marginBottom: 4 }}>
              <span>Wird hochgeladen…</span>
              <span>{uploadProgress}%</span>
            </div>
            <div style={{ height: 4, background: '#e0f4f8', borderRadius: 2, overflow: 'hidden' }}>
              <div style={{ width: `${uploadProgress}%`, height: '100%', background: '#008eaa', borderRadius: 2, transition: 'width 0.2s ease' }} />
            </div>
          </div>
        )}

        <button
          onClick={handleUpload}
          disabled={!pendingFile || uploading}
          style={{
            width: '100%', padding: 12,
            background: !pendingFile || uploading ? '#8fa8b0' : '#008eaa',
            color: 'white', border: 'none', borderRadius: 8,
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
        <div style={{ fontSize: 12, fontWeight: 600, color: '#8fa8b0', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 12 }}>
          Eingereichte Dateien
        </div>
        {loadingFiles ? (
          <div style={{ color: '#8fa8b0', fontSize: 13 }}>Wird geladen…</div>
        ) : files.length === 0 ? (
          <div style={{ color: '#8fa8b0', fontSize: 13 }}>Noch keine Dateien eingereicht.</div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {files.map(f => {
              const tc = FILE_TYPE_COLORS[f.file_type] || FILE_TYPE_COLORS.sonstiges;
              return (
                <div key={f.id} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '8px 0', borderBottom: '1px solid #f0f0f0' }}>
                  <span style={{ fontSize: 16, flexShrink: 0 }}>
                    {f.file_type === 'logo' ? '🎨' : f.file_type === 'foto' ? '📷' : f.file_type === 'text' ? '📝' : f.file_type === 'zugangsdaten' ? '🔑' : '📎'}
                  </span>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 13, color: '#4a6470', fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {f.original_filename}
                    </div>
                    <div style={{ fontSize: 11, color: '#8fa8b0', marginTop: 2 }}>
                      {f.uploaded_at ? new Date(f.uploaded_at).toLocaleDateString('de-DE') : '—'} · {formatSize(f.file_size)}
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

export default function CustomerPortal() {
  const { token } = useParams();
  const [step, setStep] = useState('loading');
  const [data, setData] = useState(null);
  const [email, setEmail] = useState('');
  const [verifying, setVerifying] = useState(false);
  const [verifyError, setVerifyError] = useState('');
  const [verifiedData, setVerifiedData] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => { loadPortal(); }, [token]); // eslint-disable-line

  const loadPortal = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/leads/portal/${token}`);
      if (!res.ok) { setError('Dieser Link ist ungültig oder abgelaufen.'); setStep('error'); return; }
      const d = await res.json();
      setData(d);
      setStep('verify');
    } catch { setError('Verbindungsfehler.'); setStep('error'); }
  };

  const handleVerify = async (e) => {
    e.preventDefault();
    setVerifying(true);
    setVerifyError('');
    try {
      const res = await fetch(`${API_BASE_URL}/api/leads/portal/${token}/verify`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      });
      const d = await res.json();
      if (!res.ok) { setVerifyError(d.detail || 'Verifikation fehlgeschlagen'); return; }
      setVerifiedData(d);
      setStep('dashboard');
    } catch { setVerifyError('Verbindungsfehler'); }
    finally { setVerifying(false); }
  };

  const levelColor = data?.current_level ? LEVEL_COLORS[data.current_level] : '#8fa8b0';

  // LOADING
  if (step === 'loading') return (
    <div style={{ minHeight: '100vh', background: 'var(--bg-app)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: 'var(--font-sans, system-ui)' }}>
      <div style={{ textAlign: 'center' }}>
        <div style={{ width: 40, height: 40, borderRadius: '50%', border: '3px solid #e0f4f8', borderTopColor: '#008eaa', animation: 'spin 0.8s linear infinite', margin: '0 auto 12px' }} />
        <div style={{ color: '#8fa8b0', fontSize: 13 }}>Wird geladen...</div>
      </div>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );

  // ERROR
  if (step === 'error') return (
    <div style={{ minHeight: '100vh', background: 'var(--bg-app)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20, fontFamily: 'var(--font-sans, system-ui)' }}>
      <div style={{ background: 'var(--bg-surface)', borderRadius: 16, padding: 40, maxWidth: 400, width: '100%', textAlign: 'center', boxShadow: '0 4px 24px rgba(0,0,0,0.08)' }}>
        <div style={{ fontSize: 48, marginBottom: 16 }}>🔗</div>
        <h2 style={{ fontSize: 18, color: 'var(--text-primary)', marginBottom: 8 }}>Ungültiger Link</h2>
        <p style={{ fontSize: 13, color: '#8fa8b0' }}>{error}</p>
      </div>
    </div>
  );

  // VERIFY
  if (step === 'verify') return (
    <div style={{ minHeight: '100vh', background: 'var(--bg-app)', fontFamily: 'var(--font-sans, system-ui)' }}>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      <div style={{ background: '#0f1e3a', padding: '16px 20px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Logo size="small" />
      </div>
      <div style={{ maxWidth: 420, margin: '40px auto', padding: '0 20px' }}>
        <div style={{ background: '#008eaa', borderRadius: 16, padding: 24, color: 'white', marginBottom: 20, textAlign: 'center' }}>
          <div style={{ fontSize: 36, marginBottom: 8 }}>👋</div>
          <h1 style={{ fontSize: 20, fontWeight: 600, margin: '0 0 6px' }}>Willkommen, {data?.company_name}!</h1>
          <p style={{ fontSize: 13, color: 'rgba(255,255,255,0.8)', margin: 0 }}>Ihr persönlicher Homepage-Audit Zugang</p>
        </div>
        <div style={{ background: 'var(--bg-surface)', borderRadius: 16, padding: 28, boxShadow: '0 4px 24px rgba(0,0,0,0.06)' }}>
          <h2 style={{ fontSize: 16, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 6, marginTop: 0 }}>Identität bestätigen</h2>
          <p style={{ fontSize: 12, color: '#8fa8b0', marginBottom: 20, lineHeight: 1.6 }}>
            Bitte geben Sie eine E-Mail-Adresse mit der Domain <strong style={{ color: '#008eaa' }}>@{data?.email_domain}</strong> ein.
          </p>
          {verifyError && (
            <div style={{ background: 'var(--status-danger-bg)', color: '#b02020', borderRadius: 8, padding: '10px 12px', fontSize: 12, marginBottom: 16 }}>{verifyError}</div>
          )}
          <form onSubmit={handleVerify}>
            <div style={{ marginBottom: 16 }}>
              <label style={{ display: 'block', fontSize: 10, fontWeight: 600, color: '#8fa8b0', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 6 }}>Ihre geschäftliche E-Mail</label>
              <input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder={`name@${data?.email_domain}`} required
                style={{ width: '100%', padding: '14px 16px', border: '1px solid #d4d8e8', borderRadius: 8, fontSize: 16, fontFamily: 'inherit', outline: 'none', boxSizing: 'border-box', color: 'var(--text-primary)' }}
                onFocus={e => e.target.style.borderColor = '#008eaa'} onBlur={e => e.target.style.borderColor = '#d4d8e8'} />
            </div>
            <button type="submit" disabled={verifying} style={{
              width: '100%', padding: 12, background: verifying ? '#8fa8b0' : '#008eaa', color: 'white',
              border: 'none', borderRadius: 8, fontSize: 14, fontWeight: 600, cursor: verifying ? 'not-allowed' : 'pointer',
              fontFamily: 'inherit', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
            }}>
              {verifying ? (
                <><span style={{ width: 14, height: 14, borderRadius: '50%', border: '2px solid rgba(255,255,255,0.3)', borderTopColor: 'white', animation: 'spin 0.8s linear infinite', display: 'inline-block' }} />Wird geprüft...</>
              ) : 'Zugang bestätigen →'}
            </button>
          </form>
        </div>
        <div style={{ textAlign: 'center', marginTop: 16, fontSize: 11, color: '#8fa8b0' }}>🔒 Ihre Daten sind sicher — nur Sie haben Zugriff.</div>
      </div>
    </div>
  );

  // DASHBOARD
  if (step === 'dashboard') return (
    <div style={{ minHeight: '100vh', background: 'var(--bg-app)', fontFamily: 'var(--font-sans, system-ui)' }}>
      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
      `}</style>
      <div style={{ background: '#008eaa', padding: '16px 20px 20px' }}>
        <div style={{ maxWidth: 700, margin: '0 auto', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
          <Logo size="small" />
          <div style={{ color: 'rgba(255,255,255,0.8)', fontSize: 12 }}>{data?.company_name}</div>
        </div>
        {data?.current_score !== null && (
          <div style={{ maxWidth: 700, margin: '16px auto 0', display: 'flex', alignItems: 'center', gap: 16, flexWrap: 'wrap' }}>
            <div style={{ background: 'rgba(255,255,255,0.15)', borderRadius: 12, padding: '12px 20px', textAlign: 'center', backdropFilter: 'blur(8px)', border: '1px solid rgba(255,255,255,0.2)' }}>
              <div style={{ fontSize: 'clamp(28px, 8vw, 36px)', fontWeight: 700, color: 'white', lineHeight: 1 }}>{data.current_score}</div>
              <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.6)', marginTop: 2 }}>von 100</div>
            </div>
            <div>
              <div style={{ fontSize: 18, fontWeight: 600, color: 'white' }}>{data.current_level}</div>
              <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.7)', marginTop: 3 }}>Letzte Prüfung: {data.last_audit_date}</div>
            </div>
          </div>
        )}
      </div>
      <div style={{ maxWidth: 700, margin: '0 auto', padding: '20px 16px', animation: 'fadeIn 0.4s ease' }}>
        {data?.ai_summary && (
          <div style={{ background: 'var(--bg-surface)', borderRadius: 12, padding: 20, marginBottom: 16, boxShadow: '0 1px 4px rgba(0,0,0,0.06)', border: '1px solid #e0f4f8' }}>
            <div style={{ fontSize: 12, fontWeight: 600, color: '#8fa8b0', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 8 }}>Zusammenfassung</div>
            <p style={{ fontSize: 13, color: '#4a6470', lineHeight: 1.6, margin: 0 }}>{data.ai_summary}</p>
          </div>
        )}
        {data?.rc_score !== null && (
          <div style={{ background: 'var(--bg-surface)', borderRadius: 12, padding: 20, marginBottom: 16, boxShadow: '0 1px 4px rgba(0,0,0,0.06)' }}>
            <div style={{ fontSize: 12, fontWeight: 600, color: '#8fa8b0', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 14 }}>Ihre Ergebnisse im Detail</div>
            {[
              ['Rechtliche Compliance', data.rc_score, 30],
              ['Technische Performance', data.tp_score, 20],
              ['Barrierefreiheit', data.bf_score, 20],
              ['Sicherheit & Datenschutz', data.si_score, 15],
              ['SEO & Sichtbarkeit', data.se_score, 10],
              ['Inhalt & Nutzererfahrung', data.ux_score, 5],
            ].map(([label, score, max]) => {
              const pct = Math.min(100, ((score || 0) / max) * 100);
              const col = pct >= 75 ? '#1a7a3a' : pct >= 50 ? '#a06800' : '#b02020';
              return (
                <div key={label} style={{ marginBottom: 12 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 4, color: '#4a6470' }}>
                    <span>{label}</span>
                    <span style={{ fontWeight: 600, color: col }}>{score || 0}/{max}</span>
                  </div>
                  <div style={{ height: 6, background: 'var(--bg-app)', borderRadius: 3, overflow: 'hidden' }}>
                    <div style={{ width: `${pct}%`, height: '100%', background: col, borderRadius: 3, transition: 'width 0.8s ease' }} />
                  </div>
                </div>
              );
            })}
          </div>
        )}
        {data?.website_screenshot && (
          <div style={{ background: 'var(--bg-surface)', borderRadius: 12, padding: 20, marginBottom: 16, boxShadow: '0 1px 4px rgba(0,0,0,0.06)' }}>
            <div style={{ fontSize: 12, fontWeight: 600, color: '#8fa8b0', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 10 }}>Ihre Website</div>
            <div style={{ background: 'var(--bg-app)', borderRadius: 8, overflow: 'hidden', border: '1px solid #e0f4f8' }}>
              <div style={{ background: 'var(--brand-primary-light)', padding: '6px 10px', display: 'flex', alignItems: 'center', gap: 5 }}>
                {['#ef4444','#f59e0b','#22c55e'].map(c => <div key={c} style={{ width: 8, height: 8, borderRadius: '50%', background: c }} />)}
                <div style={{ flex: 1, background: 'var(--bg-surface)', borderRadius: 4, padding: '2px 8px', fontSize: 10, color: '#8fa8b0', marginLeft: 6 }}>{data.website_url}</div>
              </div>
              <img src={data.website_screenshot} alt="Website" style={{ width: '100%', display: 'block', maxHeight: 240, objectFit: 'cover', objectPosition: 'top' }} />
            </div>
          </div>
        )}

        {/* File upload section */}
        <FileUploadSection token={token} />

        <div style={{ background: '#0f1e3a', borderRadius: 12, padding: 20, textAlign: 'center', color: 'white' }}>
          <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 6 }}>Jetzt Ihre Website optimieren</div>
          <p style={{ fontSize: 12, color: 'rgba(255,255,255,0.7)', marginBottom: 14, lineHeight: 1.5 }}>
            KOMPAGNON bringt Ihre Homepage auf Homepage Standard Gold oder Platin — in 14 Werktagen, zum Festpreis.
          </p>
          <a href="https://www.kompagnon.eu" target="_blank" rel="noopener noreferrer" style={{
            display: 'block', width: '100%', maxWidth: 320, margin: '0 auto', padding: '14px 24px', background: '#008eaa', color: 'white', textAlign: 'center',
            borderRadius: 8, fontSize: 13, fontWeight: 600, textDecoration: 'none',
          }}>Jetzt anfragen →</a>
        </div>
      </div>
    </div>
  );

  return null;
}

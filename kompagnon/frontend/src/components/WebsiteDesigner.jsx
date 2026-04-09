import { StudioEditor } from '@grapesjs/studio-sdk/react';
import '@grapesjs/studio-sdk/style';
import { useRef, useState, useCallback } from 'react';
import JSZip from 'jszip';
import toast from 'react-hot-toast';
import API_BASE_URL from '../config';

const LICENSE_KEY = process.env.REACT_APP_GJS_LICENSE_KEY || 'DEV_LICENSE_KEY';

// loadProjectFromZip: identisch zur alten Implementierung, gibt Projekt-/CSS-
// Daten zurück statt den Editor direkt zu manipulieren.
const loadProjectFromZip = async (file) => {
  const ext = file.name.split('.').pop().toLowerCase();

  if (ext === 'grapesjs') {
    const text = await file.text();
    try { return { success: true, project: JSON.parse(text), source: 'grapesjs' }; }
    catch { return { success: false, error: 'Ungültige .grapesjs-Datei' }; }
  }

  if (ext === 'zip') {
    try {
      const zip   = await JSZip.loadAsync(file);
      const files = Object.keys(zip.files);
      const gjsFile = files.find(f => f.endsWith('.grapesjs') || f.endsWith('grapesjs.json'));
      if (gjsFile) {
        const text    = await zip.files[gjsFile].async('string');
        return { success: true, project: JSON.parse(text), source: 'zip-grapesjs' };
      }
      const htmlFile = files.find(f => f.endsWith('index.html'));
      const cssFile  = files.find(f => f.endsWith('style.css'));
      if (htmlFile) {
        const html = await zip.files[htmlFile].async('string');
        const css  = cssFile ? await zip.files[cssFile].async('string') : '';
        const bodyMatch = html.match(/<body[^>]*>([\s\S]*?)<\/body>/i);
        const bodyHtml  = bodyMatch ? bodyMatch[1].trim() : html;
        return {
          success: true,
          source:  'zip-html',
          project: { pages: [{ name: 'index', component: bodyHtml }] },
          css,
        };
      }
      return { success: false, error: 'Keine erkennbare Datei im ZIP' };
    } catch (e) { return { success: false, error: `ZIP-Fehler: ${e.message}` }; }
  }
  return { success: false, error: `Format .${ext} nicht unterstützt.` };
};

export default function WebsiteDesigner({
  projectId, leadId, initialHtml, initialCss, onSave,
}) {
  const editorRef = useRef(null);
  const [showImportModal, setShowImportModal] = useState(false);
  const [importing, setImporting]   = useState(false);
  const [importMsg, setImportMsg]   = useState('');
  const [importError, setImportError] = useState('');
  const fileInputRef = useRef(null);

  // Token aus localStorage (AuthContext-kompatibel)
  const token = localStorage.getItem('token') || '';
  const authHeaders = { Authorization: `Bearer ${token}` };

  // ── Asset Manager: Bilder aus Backend laden ───────────────
  const onAssetsLoad = useCallback(async () => {
    if (!projectId) return { assets: [] };
    try {
      const res = await fetch(
        `${API_BASE_URL}/api/assets/project/${projectId}`,
        { headers: authHeaders },
      );
      const data = await res.json();
      const assets = (data.assets || []).map(a => ({
        type: 'image',
        src:  a.src.startsWith('http') ? a.src : `${API_BASE_URL}${a.src}`,
        name: a.name,
      }));
      return { assets };
    } catch {
      return { assets: [] };
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId]);

  // ── Asset Manager: Bild hochladen ─────────────────────────
  const onAssetsUpload = useCallback(async ({ files }) => {
    if (!projectId || !files?.length) return { data: [] };
    const fd = new FormData();
    fd.append('file', files[0]);
    try {
      const res = await fetch(
        `${API_BASE_URL}/api/assets/project/${projectId}/upload`,
        { method: 'POST', headers: authHeaders, body: fd },
      );
      const data = await res.json();
      const normalized = (data.data || []).map(d => ({
        ...d,
        src: d.src.startsWith('http') ? d.src : `${API_BASE_URL}${d.src}`,
      }));
      return { data: normalized };
    } catch {
      return { data: [] };
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId]);

  // ── Save-Handler (Studio SDK ruft das on demand auf) ──────
  const handleSave = useCallback(async ({ project, editor }) => {
    try {
      const html = editor?.getHtml?.() || '';
      const css  = editor?.getCss?.()  || '';
      if (onSave) onSave(html, css, project);
      toast.success('Gespeichert!');
    } catch {
      toast.error('Speichern fehlgeschlagen');
    }
  }, [onSave]);

  // ── ZIP Import Modal-Handler ──────────────────────────────
  const handleImportFile = async (e) => {
    const file = e?.target?.files?.[0];
    if (!file || !editorRef.current) return;
    setImporting(true); setImportMsg(''); setImportError('');
    const result = await loadProjectFromZip(file);
    setImporting(false);
    if (result.success) {
      try {
        editorRef.current.loadProjectData(result.project);
        if (result.css && editorRef.current.setStyle) {
          editorRef.current.setStyle(result.css);
        }
      } catch (err) {
        setImportError('Editor konnte Projekt nicht laden: ' + err.message);
        return;
      }
      setImportMsg(`✓ Template geladen (${result.source})`);
      setShowImportModal(false);
    } else {
      setImportError(result.error || 'Import fehlgeschlagen');
    }
    if (e?.target) e.target.value = '';
  };

  return (
    <div style={{ position: 'relative', display: 'flex',
                  flexDirection: 'column', height: '100vh' }}>
      {/* Toolbar */}
      <div style={{ padding: '8px 16px', background: '#1a2332',
                    display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
        <span style={{ color: '#fff', fontWeight: 600 }}>Website Designer</span>
        <span style={{ color: '#64748b', fontSize: 12 }}>
          {projectId ? `Projekt #${projectId}` : 'Neues Design'}
        </span>

        <input
          ref={fileInputRef}
          type="file"
          accept=".zip,.grapesjs"
          style={{ display: 'none' }}
          onChange={handleImportFile}
        />

        <button
          onClick={() => setShowImportModal(true)}
          disabled={importing}
          style={{
            padding: '7px 14px',
            background: importing ? '#94a3b8' : '#7c3aed',
            color: '#fff', border: 'none', borderRadius: 7,
            fontSize: 12, fontWeight: 600,
            cursor: importing ? 'not-allowed' : 'pointer',
            display: 'flex', alignItems: 'center', gap: 6,
          }}
        >
          {importing ? '⏳ Lädt...' : '📂 Template laden'}
        </button>

        {importMsg && (
          <span style={{ fontSize: 11, color: '#1D9E75', fontWeight: 500 }}>
            {importMsg}
          </span>
        )}
        {importError && !showImportModal && (
          <span style={{ fontSize: 11, color: '#E24B4A', fontWeight: 500 }}>
            ✗ {importError}
          </span>
        )}
      </div>

      {/* Studio SDK Editor */}
      <div style={{ flex: 1, minHeight: 0 }}>
        <StudioEditor
          options={{
            licenseKey: LICENSE_KEY,
            project: {
              type: 'web',
              default: {
                pages: [{ name: 'index', component: initialHtml || '' }],
              },
            },
            storage: {
              type: 'self',
              autosaveChanges: 10,
              onSave: handleSave,
            },
            assets: {
              storageType: 'self',
              onLoad:   onAssetsLoad,
              onUpload: onAssetsUpload,
            },
            canvas: {
              styles: [
                'https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.2.3/css/bootstrap.min.css',
                'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css',
              ],
            },
          }}
          onReady={(editor) => { editorRef.current = editor; }}
        />
      </div>

      {/* Import Modal */}
      {showImportModal && (
        <div style={{
          position: 'fixed', inset: 0, background: 'rgba(0,0,0,.5)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          zIndex: 9999,
        }}>
          <div style={{
            background: 'var(--bg-surface, #fff)', borderRadius: 12,
            padding: 32, width: 480, maxWidth: '90vw',
          }}>
            <h3 style={{ margin: '0 0 16px' }}>
              ZIP-Template importieren
            </h3>
            <p style={{ fontSize: 13, color: 'var(--text-secondary, #64748b)',
                        marginBottom: 20 }}>
              ZIP mit <code>index.html</code> hochladen. Optional: <code>style.css</code>.
              Oder eine <code>.grapesjs</code>-Datei.
            </p>

            <div
              onClick={() => fileInputRef.current?.click()}
              onDragOver={(e) => e.preventDefault()}
              onDrop={(e) => {
                e.preventDefault();
                const f = e.dataTransfer.files[0];
                if (f) {
                  const synth = { target: { files: [f], value: '' } };
                  handleImportFile(synth);
                }
              }}
              style={{
                border: '2px dashed #cbd5e1', borderRadius: 8,
                padding: '32px 20px', textAlign: 'center',
                cursor: 'pointer', background: '#f8fafc', marginBottom: 16,
              }}
            >
              {importing ? (
                <p style={{ margin: 0 }}>Verarbeitung...</p>
              ) : (
                <>
                  <div style={{ fontSize: 32, marginBottom: 8 }}>📦</div>
                  <p style={{ margin: 0, fontSize: 14, color: '#64748b' }}>
                    ZIP oder .grapesjs hier ablegen oder klicken
                  </p>
                </>
              )}
            </div>

            {importError && (
              <p style={{
                color: '#b91c1c', background: '#fee2e2',
                padding: '8px 12px', borderRadius: 6,
                fontSize: 13, marginBottom: 12,
              }}>
                {importError}
              </p>
            )}

            <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
              <button
                onClick={() => { setShowImportModal(false); setImportError(''); }}
                style={{
                  padding: '8px 20px', border: '1px solid #cbd5e1',
                  borderRadius: 6, background: 'transparent',
                  color: '#64748b', cursor: 'pointer',
                }}
              >
                Abbrechen
              </button>
              <button
                onClick={() => fileInputRef.current?.click()}
                disabled={importing}
                style={{
                  padding: '8px 20px', border: 'none', borderRadius: 6,
                  background: '#0d6efd', color: '#fff',
                  cursor: 'pointer', fontWeight: 600,
                }}
              >
                Datei auswählen
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

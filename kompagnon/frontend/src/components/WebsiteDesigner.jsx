import { StudioEditor } from '@grapesjs/studio-sdk/react';
import '@grapesjs/studio-sdk/style';
import { useRef, useState, useCallback, useMemo, useEffect } from 'react';
import { createPortal } from 'react-dom';
import toast from 'react-hot-toast';
// processClipboardImage now handled by useGrapesAssetManager hook
import { useGrapesAssetManager } from '../hooks/useGrapesAssetManager';
// API_BASE_URL now handled by useGrapesAssetManager hook
import { useScreenSize } from '../utils/responsive';
import { STUDIO_LICENSE_KEY, buildStudioPlugins } from '../utils/studioEditorConfig';
import { parseTemplateFile, applyTemplateToEditor } from '../utils/studioTemplateImport';
import handwerkPlugin from '../grapesjs/handwerk-plugin';
import { renderBlock } from '../grapesjs/handwerk-blocks';

export default function WebsiteDesigner({
  projectId, leadId, initialHtml, initialCss, onSave, onClose, brandData,
}) {
  const { isMobile } = useScreenSize();
  const editorRef = useRef(null);
  const plugins = useMemo(() => buildStudioPlugins(), []);

  // Listen for assets from ProjectFilesSection "→ Editor" button
  useEffect(() => {
    const onAssetAdd = (e) => {
      const editor = editorRef.current;
      if (!editor) return;
      const { src, name, category } = e.detail || {};
      if (!src) return;
      try { editor.AssetManager?.add({ type: 'image', src, name: name || src, category }); } catch { /* silent */ }
    };
    window.addEventListener('kompagnon:asset-add', onAssetAdd);

    // Listen for open-editor from DesignStudio
    const onOpenEditor = (e) => {
      const editor = editorRef.current;
      if (!editor) return;
      const { html, blocks, brand } = e.detail || {};
      if (blocks && blocks.length > 0 && brand) {
        editor.setComponents('');
        blocks.forEach(block => {
          const blockHtml = renderBlock(block.type, block.data || {}, brand);
          editor.addComponents(blockHtml);
        });
      } else if (html) {
        editor.setComponents(html);
      }
    };
    window.addEventListener('kompagnon:open-editor', onOpenEditor);

    return () => {
      window.removeEventListener('kompagnon:asset-add', onAssetAdd);
      window.removeEventListener('kompagnon:open-editor', onOpenEditor);
    };
  }, []);

  // Clipboard paste is now handled by useGrapesAssetManager hook

  const [showImportModal, setShowImportModal] = useState(false);
  const [importing, setImporting]   = useState(false);
  const [importMsg, setImportMsg]   = useState('');
  const [importError, setImportError] = useState('');
  const [saving, setSaving]         = useState(false);
  const fileInputRef = useRef(null);

  // Token aus localStorage (AuthContext-kompatibel)
  const token = localStorage.getItem('token') || '';

  // ── Asset Manager — zentraler Hook ──
  const { onAssetsLoad, onAssetsUpload, editorRef: assetEditorRef, refreshAssets, assetCount } = useGrapesAssetManager({ leadId, projectId, token });
  const [assetsRefreshing, setAssetsRefreshing] = useState(false);

  // ── Save-Handler (Studio SDK ruft das on demand auf) ──────
  const handleSave = useCallback(async ({ project, editor }) => {
    setSaving(true);
    try {
      const html = editor?.getHtml?.() || '';
      const css  = editor?.getCss?.()  || '';
      if (onSave) await onSave(html, css, project);
      toast.success('Gespeichert!');
    } catch {
      toast.error('Speichern fehlgeschlagen');
    }
    setSaving(false);
  }, [onSave]);

  // ── Manuelles Speichern (Toolbar-Button) ──────────────────
  const handleManualSave = async () => {
    const editor = editorRef.current;
    if (!editor) return toast.error('Editor noch nicht bereit');
    const project = editor.getProjectData?.() || {};
    await handleSave({ project, editor });
  };

  // ── ZIP/.grapesjs Import-Handler (shared parser) ──────────
  const handleImportFile = async (e) => {
    const file = e?.target?.files?.[0];
    if (!file || !editorRef.current) return;
    setImporting(true); setImportMsg(''); setImportError('');
    const result = await parseTemplateFile(file);
    setImporting(false);
    if (result.success) {
      try {
        applyTemplateToEditor(editorRef.current, result);
      } catch (err) {
        setImportError('Editor konnte Projekt nicht laden: ' + err.message);
        return;
      }
      setImportMsg({
        'zip-grapesjs': '✓ GrapesJS-Projekt + CSS geladen',
        'zip-html':     '✓ HTML + CSS geladen',
        'grapesjs':     '✓ GrapesJS-Projekt geladen',
      }[result.source] || '✓ Template geladen');
      setShowImportModal(false);
    } else {
      setImportError(result.error || 'Import fehlgeschlagen');
    }
    if (e?.target) e.target.value = '';
  };

  return createPortal(
    <div style={{
      position: 'fixed',
      top: 0,
      left: isMobile ? 0 : 'var(--sidebar-width)',
      right: 0,
      bottom: 0,
      zIndex: 500,
      display: 'flex', flexDirection: 'column',
      background: '#fff',
    }}>
      {/* Toolbar */}
      <div style={{ padding: '8px 16px', background: 'var(--bg-sidebar)',
                    display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
        <span style={{ color: 'var(--text-inverse)', fontWeight: 600 }}>Website Designer</span>
        <span style={{ color: 'var(--text-tertiary)', fontSize: 12 }}>
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
          {importing ? '⏳ Lädt...' : '📂 Template importieren'}
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

        <div style={{ flex: 1 }} />

        {/* Asset refresh + count */}
        <button
          onClick={async () => { setAssetsRefreshing(true); await refreshAssets(); setAssetsRefreshing(false); }}
          disabled={assetsRefreshing}
          title="Neue Kunden-Uploads laden"
          style={{
            background: 'none', border: '1px solid rgba(255,255,255,0.2)',
            color: assetsRefreshing ? 'rgba(255,255,255,0.3)' : 'rgba(255,255,255,0.6)',
            borderRadius: 4, padding: '4px 8px', cursor: assetsRefreshing ? 'not-allowed' : 'pointer',
            fontSize: 11, display: 'flex', alignItems: 'center', gap: 4, fontFamily: 'var(--font-sans)',
          }}
        >
          <span style={{ display: 'inline-block', animation: assetsRefreshing ? 'spin 0.8s linear infinite' : 'none' }}>↻</span>
          {assetCount > 0 ? `${assetCount} Bilder` : 'Assets'}
        </button>

        {/* Paste hint */}
        <span style={{ fontSize: 10, color: 'rgba(255,255,255,0.3)', display: 'flex', alignItems: 'center', gap: 4 }}>
          <kbd style={{ background: 'rgba(255,255,255,0.1)', border: '1px solid rgba(255,255,255,0.15)', borderRadius: 3, padding: '1px 4px', fontFamily: 'monospace', fontSize: 9 }}>⌘V</kbd>
          Bild
        </span>

        {saving && (
          <span style={{ color: '#94a3b8', fontSize: 12 }}>Wird gespeichert…</span>
        )}

        <button
          onClick={handleManualSave}
          disabled={saving}
          style={{
            padding: '7px 14px',
            background: saving ? '#475569' : '#16a34a',
            color: '#fff', border: 'none', borderRadius: 7,
            fontSize: 12, fontWeight: 600,
            cursor: saving ? 'not-allowed' : 'pointer',
          }}>
          💾 Speichern
        </button>

        {onClose && (
          <button
            onClick={onClose}
            title="Editor schließen"
            style={{
              padding: '7px 12px',
              background: 'rgba(255,255,255,0.15)',
              color: '#fff', border: 'none', borderRadius: 7,
              fontSize: 14, fontWeight: 600, cursor: 'pointer',
            }}>
            ✕
          </button>
        )}
      </div>

      {/* Studio SDK Editor */}
      <div style={{ flex: 1, minHeight: 0 }}>
        <StudioEditor
          options={{
            licenseKey: STUDIO_LICENSE_KEY,
            project: {
              type: 'web',
              default: {
                pages: [{ name: 'index', component: initialHtml || '' }],
              },
            },
            storage: {
              type: 'self',
              autosaveChanges: 100,
              autosaveIntervalMs: 10000,
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
            plugins,
          }}
          onReady={(editor) => {
            editorRef.current = editor;
            assetEditorRef.current = editor;
            // Register Handwerk blocks plugin
            try { handwerkPlugin(editor, { brand: brandData || {} }); } catch (e) { console.warn('Handwerk plugin:', e); }
            // Ctrl+S save
            editor.on('kompagnon:save', () => handleManualSave());
          }}
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
                  <p style={{ margin: 0, fontSize: 14, color: 'var(--text-tertiary)' }}>
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
                  color: 'var(--text-tertiary)', cursor: 'pointer',
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
    </div>,
    document.body
  );
}

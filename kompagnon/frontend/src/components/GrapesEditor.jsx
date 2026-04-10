import { useEffect, useRef, useState, useCallback, useMemo } from 'react';
import { createPortal } from 'react-dom';
import { StudioEditor } from '@grapesjs/studio-sdk/react';
import '@grapesjs/studio-sdk/style';
import { useAuth } from '../context/AuthContext';
import { useScreenSize } from '../utils/responsive';
import { STUDIO_LICENSE_KEY, buildStudioPlugins } from '../utils/studioEditorConfig';
import { parseTemplateFile, applyTemplateToEditor } from '../utils/studioTemplateImport';
import API_BASE_URL from '../config';
import toast from 'react-hot-toast';

export default function GrapesEditor({
  pageId, pageName, initialHtml, onClose, onSave, projectId, netlitySiteId, leadId,
}) {
  const { token } = useAuth();
  const { isMobile } = useScreenSize();
  const headers = { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` };
  const authHeaders = { Authorization: `Bearer ${token}` };
  const editorRef = useRef(null);
  const fileInputRef = useRef(null);
  const plugins = useMemo(() => buildStudioPlugins(), []);
  const [netlifyDeploying, setNetlifyDeploying] = useState(false);
  const [importing, setImporting] = useState(false);

  // Scroll sperren solange Editor offen ist
  useEffect(() => {
    document.body.style.overflow = 'hidden';
    return () => { document.body.style.overflow = ''; };
  }, []);

  // ── Save: HTML+CSS+gjsData an /api/pages/{id}/editor ──────
  const handleSave = useCallback(async ({ project, editor }) => {
    try {
      const html = editor?.getHtml?.() || '';
      const css  = editor?.getCss?.()  || '';
      await fetch(`${API_BASE_URL}/api/pages/${pageId}/editor`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ html, css, gjsData: project }),
      });
      toast.success('Gespeichert!');
      if (onSave) onSave({ html, css });
    } catch {
      toast.error('Seite konnte nicht gespeichert werden — bitte erneut versuchen');
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pageId, token, onSave]);

  // ── Load: bestehende Editor-Daten vom Backend ──────────────
  const handleLoad = useCallback(async () => {
    try {
      const res = await fetch(
        `${API_BASE_URL}/api/pages/${pageId}/editor`,
        { headers: authHeaders },
      );
      if (res.ok) {
        const data = await res.json();
        if (data?.gjsData && Object.keys(data.gjsData).length > 0) {
          return { project: data.gjsData };
        }
        if (data?.html) {
          return {
            project: {
              pages: [{ name: pageName || 'Seite', component: data.html }],
            },
          };
        }
      }
    } catch { /* fall through */ }
    return {
      project: {
        pages: [{ name: pageName || 'Seite', component: initialHtml || '' }],
      },
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pageId, pageName, initialHtml, token]);

  // ── Asset Manager (optional, nur wenn projectId gesetzt) ──
  // Studio SDK erwartet ein Array zurück: [{ src, type?, name? }]
  const onAssetsLoad = useCallback(async () => {
    const allAssets = [];
    // 1. Project assets
    if (projectId) {
      try {
        const res = await fetch(`${API_BASE_URL}/api/assets/project/${projectId}`, { headers: authHeaders });
        if (res.ok) {
          const data = await res.json();
          (data.assets || []).forEach(a => allAssets.push({
            type: 'image',
            src: a.src.startsWith('http') ? a.src : `${API_BASE_URL}${a.src}`,
            name: a.name,
          }));
        }
      } catch { /* silent */ }
    }
    // 2. Customer portal uploads (logos, photos)
    if (leadId) {
      try {
        const res = await fetch(`${API_BASE_URL}/api/files/${leadId}/grapesjs-assets`, { headers: authHeaders });
        if (res.ok) {
          const portalAssets = await res.json();
          if (Array.isArray(portalAssets)) allAssets.push(...portalAssets);
        }
      } catch { /* silent */ }
    }
    return allAssets;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId, leadId, token]);

  const onAssetsUpload = useCallback(async ({ files }) => {
    if (!projectId || !files?.length) return [];
    const fd = new FormData();
    for (const f of files) fd.append('file', f);
    try {
      const res = await fetch(
        `${API_BASE_URL}/api/assets/project/${projectId}/upload`,
        { method: 'POST', headers: authHeaders, body: fd },
      );
      if (!res.ok) return [];
      const data = await res.json();
      return (data.data || data.assets || []).map(d => ({
        ...d,
        src: d.src.startsWith('http') ? d.src : `${API_BASE_URL}${d.src}`,
      }));
    } catch { return []; }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId, token]);

  // ── Netlify Deploy ────────────────────────────────────────
  const handleNetlifyDeploy = async () => {
    if (!editorRef.current || !projectId) return;
    const html = editorRef.current.getHtml() || '';
    const css  = editorRef.current.getCss()  || '';
    setNetlifyDeploying(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/projects/${projectId}/netlify/deploy`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ html, css, redirects: '' }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      toast.success(
        <span>
          Live auf Netlify ✓{' '}
          {data.deploy_url && (
            <a href={data.deploy_url} target="_blank" rel="noopener noreferrer"
               style={{ color: '#16a34a', fontWeight: 700 }}>
              Link →
            </a>
          )}
        </span>
      );
    } catch {
      toast.error('Netlify-Deploy fehlgeschlagen — HTML auf Vollständigkeit prüfen');
    } finally {
      setNetlifyDeploying(false);
    }
  };

  const handlePreview = () => {
    if (!editorRef.current) return;
    const html = editorRef.current.getHtml() || '';
    const css  = editorRef.current.getCss()  || '';
    const w = window.open('', '_blank');
    w.document.write(`<!DOCTYPE html><html><head><style>${css}</style></head><body>${html}</body></html>`);
    w.document.close();
  };

  const handleManualSave = async () => {
    const editor = editorRef.current;
    if (!editor) return toast.error('Editor noch nicht bereit');
    const project = editor.getProjectData?.() || {};
    await handleSave({ project, editor });
  };

  const handleImportFile = async (e) => {
    const file = e.target.files?.[0];
    if (e.target) e.target.value = '';
    if (!file) return;
    setImporting(true);
    try {
      const parsed = await parseTemplateFile(file);
      if (!parsed.success) throw new Error(parsed.error);
      applyTemplateToEditor(editorRef.current, parsed);
      toast.success('Template importiert');
    } catch (err) { toast.error(err.message || 'Import fehlgeschlagen'); }
    setImporting(false);
  };

  return createPortal(
    <div style={{
      position: 'fixed',
      top: 0,
      left: isMobile ? 0 : 'var(--sidebar-width)',
      right: 0,
      bottom: 0,
      zIndex: 99999, display: 'flex', flexDirection: 'column',
      background: '#1a1a1a', overflow: 'hidden',
    }}>
      {/* Toolbar */}
      <div style={{
        height: 52, flexShrink: 0,
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '0 16px', background: '#1a2332', color: '#fff', zIndex: 1, gap: 10,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <button onClick={onClose} style={{
            background: 'none', border: '1px solid rgba(255,255,255,0.3)',
            color: '#fff', padding: '5px 12px', borderRadius: 6,
            cursor: 'pointer', fontSize: 13,
          }}>← Zurück</button>
          <span style={{ fontSize: 14, fontWeight: 600 }}>{pageName}</span>

          <input
            ref={fileInputRef}
            type="file"
            accept=".zip,.grapesjs"
            style={{ display: 'none' }}
            onChange={handleImportFile}
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={importing}
            style={{
              background: importing ? '#5b21b6' : '#7c3aed',
              border: 'none', color: '#fff', padding: '6px 12px',
              borderRadius: 6, cursor: importing ? 'not-allowed' : 'pointer',
              fontSize: 12, fontWeight: 600,
            }}>
            {importing ? '⏳ Lädt…' : '📂 Template importieren'}
          </button>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button onClick={handlePreview} style={{
            background: 'none', border: '1px solid rgba(255,255,255,0.3)',
            color: '#fff', padding: '6px 14px', borderRadius: 6,
            cursor: 'pointer', fontSize: 13,
          }}>👁 Vorschau</button>
          <button onClick={handleManualSave} style={{
            background: '#16a34a', border: 'none',
            color: '#fff', padding: '6px 14px', borderRadius: 6,
            cursor: 'pointer', fontSize: 13, fontWeight: 600,
          }}>💾 Speichern</button>
          {projectId && netlitySiteId && (
            <button
              onClick={handleNetlifyDeploy}
              disabled={netlifyDeploying}
              style={{
                background: netlifyDeploying ? '#166534' : '#16a34a',
                border: 'none', color: '#fff', padding: '6px 16px',
                borderRadius: 6,
                cursor: netlifyDeploying ? 'not-allowed' : 'pointer',
                fontSize: 13, fontWeight: 600,
                opacity: netlifyDeploying ? 0.8 : 1,
              }}
            >
              {netlifyDeploying ? '⏳ Wird deployed…' : '🚀 Direkt zu Netlify deployen'}
            </button>
          )}
          <button
            onClick={onClose}
            title="Editor schließen"
            style={{
              background: 'rgba(255,255,255,0.15)', border: 'none', color: '#fff',
              padding: '6px 12px', borderRadius: 6, cursor: 'pointer',
              fontSize: 14, fontWeight: 600,
            }}>
            ✕
          </button>
        </div>
      </div>

      {/* Studio SDK Canvas */}
      <div style={{ flex: 1, width: '100%', minHeight: 0 }}>
        <StudioEditor
          options={{
            licenseKey: STUDIO_LICENSE_KEY,
            project: {
              type: 'web',
              default: {
                pages: [{ name: pageName || 'Seite', component: '' }],
              },
            },
            storage: {
              type: 'self',
              autosaveChanges: 100,
              autosaveIntervalMs: 10000,
              onSave: handleSave,
              onLoad: handleLoad,
            },
            assets: projectId ? {
              storageType: 'self',
              onLoad:   onAssetsLoad,
              onUpload: onAssetsUpload,
            } : undefined,
            plugins,
          }}
          onReady={(editor) => { editorRef.current = editor; }}
        />
      </div>
    </div>,
    document.body
  );
}

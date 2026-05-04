import { useState, useCallback, useRef, useMemo } from 'react';
import { createPortal } from 'react-dom';
import { useParams, useNavigate } from 'react-router-dom';
import { StudioEditor } from '@grapesjs/studio-sdk/react';
import '@grapesjs/studio-sdk/style';
import { useAuth } from '../context/AuthContext';
import { useScreenSize } from '../utils/responsive';
import { STUDIO_LICENSE_KEY, buildStudioPlugins } from '../utils/studioEditorConfig';
import { parseTemplateFile, applyTemplateToEditor } from '../utils/studioTemplateImport';
import toast from 'react-hot-toast';
import API_BASE_URL from '../config';

export default function PublicPageEditor() {
  const { pageId } = useParams();
  const navigate   = useNavigate();
  const { token }  = useAuth();
  const { isMobile } = useScreenSize();
  const h = { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` };
  const authHeaders = { Authorization: `Bearer ${token}` };

  const editorRef   = useRef(null);
  const fileInputRef = useRef(null);
  const plugins = useMemo(() => buildStudioPlugins(), []);

  const [pageInfo, setPageInfo] = useState(null);
  const [saving, setSaving]     = useState(false);
  const [importing, setImporting] = useState(false);

  // ── Laden ────────────────────────────────────────────────
  const handleLoad = useCallback(async () => {
    try {
      const res = await fetch(
        `${API_BASE_URL}/api/pages/${pageId}`,
        { headers: authHeaders },
      );
      if (!res.ok) throw new Error('Seite nicht gefunden');
      const data = await res.json();
      setPageInfo(data);

      // GrapesJS-Daten vorhanden?
      if (data.grapesjs_data && typeof data.grapesjs_data === 'object'
          && Object.keys(data.grapesjs_data).length > 0) {
        return { project: data.grapesjs_data };
      }
      // Nur HTML vorhanden?
      if (data.html_content) {
        return {
          project: {
            pages: [{
              name: data.name || 'Seite',
              component: data.html_content,
              styles: data.css_content || '',
            }],
          },
        };
      }
      return {
        project: {
          pages: [{ name: data.name || 'Neue Seite', component: '' }],
        },
      };
    } catch (e) {
      toast.error(e.message);
      return { project: { pages: [{ name: 'Seite', component: '' }] } };
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pageId, token]);

  // ── Speichern ─────────────────────────────────────────────
  const handleSave = useCallback(async ({ project, editor }) => {
    setSaving(true);
    try {
      const html = editor?.getHtml?.() || '';
      const css  = editor?.getCss?.()  || '';
      const res = await fetch(`${API_BASE_URL}/api/pages/${pageId}`, {
        method: 'PUT', headers: h,
        body: JSON.stringify({
          grapesjs_data: project,
          html_content:  html,
          css_content:   css,
        }),
      });
      if (!res.ok) throw new Error('HTTP ' + res.status);
      toast.success('Gespeichert!');
    } catch { toast.error('Speichern fehlgeschlagen'); }
    setSaving(false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pageId, token]);

  // ── Manuelles Speichern ───────────────────────────────────
  const handleManualSave = async () => {
    const editor = editorRef.current;
    if (!editor) return toast.error('Editor noch nicht bereit');
    const project = editor.getProjectData?.() || {};
    await handleSave({ project, editor });
  };

  // ── Template importieren ─────────────────────────────────
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

  // ── Status togglen (Live ↔ Entwurf) ───────────────────────
  const togglePublish = async () => {
    const isLive = pageInfo?.status === 'live';
    const newStatus = isLive ? 'draft' : 'live';
    try {
      const res = await fetch(`${API_BASE_URL}/api/pages/${pageId}`, {
        method: 'PUT', headers: h,
        body: JSON.stringify({ status: newStatus }),
      });
      if (!res.ok) throw new Error('HTTP ' + res.status);
      setPageInfo(p => p ? { ...p, status: newStatus } : p);
      toast.success(isLive ? 'Auf Entwurf gesetzt' : 'Seite veröffentlicht ✓');
    } catch { toast.error('Fehler beim Statuswechsel'); }
  };

  const tbBtn = {
    padding: '6px 12px', background: 'rgba(255,255,255,.15)', color: '#fff',
    border: 'none', borderRadius: 6, fontSize: 12, fontWeight: 600,
    cursor: 'pointer', fontFamily: 'inherit',
  };

  return createPortal(
    <div style={{
      position: 'fixed',
      top: 0,
      left: isMobile ? 0 : 'var(--sidebar-width)',
      right: 0,
      bottom: 0,
      zIndex: 500,
      display: 'flex', flexDirection: 'column', background: '#fff',
    }}>
      {/* Toolbar */}
      <div style={{
        height: 48, background: '#1a2c32', flexShrink: 0,
        display: 'flex', alignItems: 'center', gap: 10, padding: '0 16px',
        boxShadow: '0 2px 8px rgba(0,0,0,.25)',
      }}>
        <button onClick={() => navigate('/app/pages')} style={tbBtn}>
          ← Zurück
        </button>

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
          style={{ ...tbBtn, background: '#7c3aed' }}>
          {importing ? '⏳ Lädt…' : '📂 Template importieren'}
        </button>

        {pageInfo && (
          <div style={{ color: 'rgba(255,255,255,.7)', fontSize: 13, display: 'flex',
                        alignItems: 'center', gap: 10, overflow: 'hidden' }}>
            <span style={{ fontWeight: 600, color: '#fff' }}>{pageInfo.name}</span>
            <span style={{ fontFamily: 'monospace', fontSize: 11 }}>{pageInfo.slug}</span>
            <span style={{
              padding: '2px 7px', borderRadius: 3, fontSize: 10, fontWeight: 700,
              background: pageInfo.status === 'live' ? '#d1fae5' : '#fef3c7',
              color:      pageInfo.status === 'live' ? '#065f46' : '#92400e',
            }}>
              {pageInfo.status === 'live' ? 'Live' : 'Entwurf'}
            </span>
          </div>
        )}

        <div style={{ flex: 1 }}/>

        {saving && (
          <span style={{ color: 'rgba(255,255,255,.5)', fontSize: 12 }}>Wird gespeichert…</span>
        )}

        <button onClick={handleManualSave} disabled={saving} style={{
          ...tbBtn, background: saving ? '#475569' : '#16a34a',
        }}>
          💾 Speichern
        </button>

        {pageInfo?.slug && (
          <a href={pageInfo.slug} target="_blank" rel="noreferrer" style={{
            ...tbBtn, textDecoration: 'none', display: 'inline-flex', alignItems: 'center',
          }}>
            👁 Vorschau
          </a>
        )}

        <button
          onClick={togglePublish}
          disabled={!pageInfo}
          title={pageInfo?.status === 'live' ? 'Seite auf Entwurf zurücksetzen' : 'Seite veröffentlichen'}
          style={{
            ...tbBtn,
            background: pageInfo?.status === 'live' ? '#94a3b8' : '#1d9e75',
            fontWeight: 700,
            opacity: pageInfo ? 1 : 0.5,
          }}>
          {pageInfo?.status === 'live' ? '📥 Auf Entwurf' : '🚀 Veröffentlichen'}
        </button>

        <button
          onClick={() => navigate('/app/pages')}
          title="Editor schließen"
          style={{ ...tbBtn, background: 'rgba(255,255,255,.15)', padding: '6px 10px', fontSize: 14 }}>
          ✕
        </button>
      </div>

      {/* Studio SDK */}
      <div style={{ flex: 1, overflow: 'hidden' }}>
        <StudioEditor
          options={{
            licenseKey: STUDIO_LICENSE_KEY,
            project: {
              type: 'web',
              default: { pages: [{ name: 'Seite', component: '' }] },
            },
            storage: {
              type: 'self',
              autosaveChanges: 100,
              autosaveIntervalMs: 10000,
              onSave: handleSave,
              onLoad: handleLoad,
            },
            plugins,
          }}
          onReady={(editor) => { editorRef.current = editor; }}
        />
      </div>
    </div>,
    document.body
  );
}

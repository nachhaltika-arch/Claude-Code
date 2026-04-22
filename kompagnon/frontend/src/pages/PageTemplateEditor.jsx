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

export default function PageTemplateEditor() {
  const { id }     = useParams();
  const navigate   = useNavigate();
  const { token }  = useAuth();
  const { isMobile } = useScreenSize();
  const h = { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` };
  const authHeaders = { Authorization: `Bearer ${token}` };

  const editorRef    = useRef(null);
  const fileInputRef = useRef(null);
  const plugins = useMemo(() => buildStudioPlugins(), []);

  const [tplInfo, setTplInfo] = useState(null);
  const [saving, setSaving]   = useState(false);
  const [importing, setImporting] = useState(false);

  // ── Laden ────────────────────────────────────────────────
  const handleLoad = useCallback(async () => {
    try {
      const res = await fetch(
        `${API_BASE_URL}/api/pages/templates/${id}`,
        { headers: authHeaders },
      );
      if (!res.ok) throw new Error('Template nicht gefunden');
      const data = await res.json();
      setTplInfo(data);

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
              name: data.name || 'Template',
              component: data.html_content,
              styles: data.css_content || '',
            }],
          },
        };
      }
      return {
        project: {
          pages: [{ name: data.name || 'Neues Template', component: '' }],
        },
      };
    } catch (e) {
      toast.error(e.message);
      return { project: { pages: [{ name: 'Template', component: '' }] } };
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id, token]);

  // ── Speichern ─────────────────────────────────────────────
  const handleSave = useCallback(async ({ project, editor }) => {
    if (tplInfo?.is_builtin) {
      toast.error('Eingebaute Templates können nicht geändert werden');
      return;
    }
    setSaving(true);
    try {
      const html = editor?.getHtml?.() || '';
      const css  = editor?.getCss?.()  || '';
      const res = await fetch(`${API_BASE_URL}/api/pages/templates/${id}`, {
        method: 'PUT', headers: h,
        body: JSON.stringify({
          grapesjs_data: project,
          html_content:  html,
          css_content:   css,
        }),
      });
      if (!res.ok) throw new Error('Speichern fehlgeschlagen');
      toast.success('Gespeichert!');
    } catch (e) { toast.error(e.message || 'Speichern fehlgeschlagen'); }
    setSaving(false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id, token, tplInfo]);

  // ── Manuelles Speichern ───────────────────────────────────
  const handleManualSave = async () => {
    const editor = editorRef.current;
    if (!editor) return toast.error('Editor noch nicht bereit');
    const project = editor.getProjectData?.() || {};
    await handleSave({ project, editor });
  };

  // ── Template importieren ─────────────────────────────────
  const handleImportFile = async (file) => {
    if (!file) return;
    if (tplInfo?.is_builtin) return toast.error('Eingebaute Templates sind schreibgeschützt');
    setImporting(true);
    try {
      const parsed = await parseTemplateFile(file);
      if (!parsed.success) throw new Error(parsed.error);
      const editor = editorRef.current;
      if (!editor) throw new Error('Editor noch nicht bereit');
      applyTemplateToEditor(editor, parsed);
      toast.success({
        'zip-grapesjs': '✓ GrapesJS-Projekt + CSS geladen',
        'zip-html':     '✓ HTML + CSS geladen',
        'grapesjs':     '✓ GrapesJS-Projekt geladen',
      }[parsed.source] || '✓ Template geladen');
    } catch (err) { toast.error(err.message || 'Import fehlgeschlagen'); }
    finally {
      setImporting(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const tbBtn = {
    padding: '6px 12px', background: 'rgba(255,255,255,.15)', color: '#fff',
    border: 'none', borderRadius: 6, fontSize: 12, fontWeight: 600,
    cursor: 'pointer', fontFamily: 'inherit',
  };
  const disabled = tplInfo?.is_builtin;

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
          onChange={e => { const f = e.target.files?.[0]; if (f) handleImportFile(f); }}
        />
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={importing || disabled}
          title={disabled ? 'Eingebaute Templates sind schreibgeschützt' : 'Template aus ZIP/.grapesjs importieren'}
          style={{
            ...tbBtn,
            background: '#7c3aed',
            opacity: (importing || disabled) ? 0.5 : 1,
            cursor:  (importing || disabled) ? 'not-allowed' : 'pointer',
          }}>
          {importing ? '⏳ Lädt…' : '📂 Template importieren'}
        </button>

        {tplInfo && (
          <div style={{ color: 'rgba(255,255,255,.7)', fontSize: 13, display: 'flex',
                        alignItems: 'center', gap: 10, overflow: 'hidden' }}>
            <span style={{ fontSize: 14 }}>🖼</span>
            <span style={{ fontWeight: 600, color: '#fff' }}>{tplInfo.name}</span>
            <span style={{
              padding: '2px 7px', borderRadius: 3, fontSize: 10, fontWeight: 700,
              background: '#e0f4f8', color: '#008eaa',
            }}>
              {tplInfo.category || 'allgemein'}
            </span>
            {tplInfo.is_builtin && (
              <span style={{
                padding: '2px 7px', borderRadius: 3, fontSize: 10, fontWeight: 700,
                background: '#fef3c7', color: '#92400e',
              }}>
                Built-in (read-only)
              </span>
            )}
          </div>
        )}

        <div style={{ flex: 1 }}/>

        {saving && (
          <span style={{ color: 'rgba(255,255,255,.5)', fontSize: 12 }}>Wird gespeichert…</span>
        )}

        <button
          onClick={handleManualSave}
          disabled={saving || disabled}
          style={{
            ...tbBtn,
            background: (saving || disabled) ? '#475569' : '#16a34a',
            cursor: (saving || disabled) ? 'not-allowed' : 'pointer',
          }}>
          💾 Speichern
        </button>

        <button
          onClick={() => navigate('/app/pages')}
          title="Editor schließen"
          style={{ ...tbBtn, padding: '6px 10px', fontSize: 14 }}>
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
              default: { pages: [{ name: 'Template', component: '' }] },
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

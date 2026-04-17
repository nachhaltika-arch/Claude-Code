import React, { useEffect, useRef, useState, useMemo } from 'react';
import { createPortal } from 'react-dom';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { StudioEditor } from '@grapesjs/studio-sdk/react';
import '@grapesjs/studio-sdk/style';
import toast from 'react-hot-toast';
import API_BASE_URL from '../config';
import { useAuth } from '../context/AuthContext';
import { useScreenSize } from '../utils/responsive';
import { STUDIO_LICENSE_KEY, buildStudioPlugins } from '../utils/studioEditorConfig';
import { parseTemplateFile, applyTemplateToEditor } from '../utils/studioTemplateImport';

const TOOLBAR_H = 56;

export default function TemplateEditor() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { token } = useAuth();
  const { isMobile } = useScreenSize();
  const headers = token ? { Authorization: `Bearer ${token}` } : {};
  const editorRef = useRef(null);
  const fileInputRef = useRef(null);
  const plugins = useMemo(() => buildStudioPlugins(), []);
  const [name, setName] = useState('');
  const [saving, setSaving] = useState(false);
  const [importing, setImporting] = useState(false);
  const [projectData, setProjectData] = useState(null);
  const [loaded, setLoaded] = useState(false);

  // Template laden — beim id-Wechsel Editor-State zurücksetzen,
  // damit <StudioEditor> aus dem Tree fliegt und mit den neuen
  // Daten frisch gemountet wird (sonst zeigt jedes Template denselben
  // Inhalt, weil das Studio SDK `default` nur einmal beim Init liest).
  useEffect(() => {
    setLoaded(false);
    setProjectData(null);
    setName('');
    fetch(`${API_BASE_URL}/api/templates/${id}`, { headers })
      .then(r => r.ok ? r.json() : null)
      .then(tpl => {
        if (!tpl) { setLoaded(true); return; }
        setName(tpl.name || '');
        if (tpl.grapes_data) {
          try {
            const data = typeof tpl.grapes_data === 'string'
              ? JSON.parse(tpl.grapes_data) : tpl.grapes_data;
            setProjectData(data);
          } catch {
            setProjectData({ pages: [{ name: 'index', component: tpl.html_content || '' }] });
          }
        } else if (tpl.html_content) {
          setProjectData({
            pages: [{
              name: 'index',
              component: tpl.html_content,
              styles: tpl.css_content || '',
            }],
          });
        }
        setLoaded(true);
      })
      .catch(() => setLoaded(true));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const handleSave = async () => {
    const editor = editorRef.current;
    if (!editor) return;
    setSaving(true);
    try {
      const project = editor.getProjectData?.() || null;
      const html    = editor.getHtml?.() || '';
      const css     = editor.getCss?.()  || '';
      const r = await fetch(`${API_BASE_URL}/api/templates/${id}`, {
        method: 'PUT',
        headers: { ...headers, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name,
          grapes_data:  project,
          html_content: html,
          css_content:  css,
        }),
      });
      if (!r.ok) throw new Error('Speichern fehlgeschlagen');
      toast.success('Template gespeichert');
    } catch (e) { toast.error(e.message); }
    setSaving(false);
  };

  const handlePreview = () => {
    const editor = editorRef.current;
    if (!editor) return;
    const html = `<!DOCTYPE html><html><head><style>${editor.getCss() || ''}</style></head><body>${editor.getHtml() || ''}</body></html>`;
    const blob = new Blob([html], { type: 'text/html' });
    window.open(URL.createObjectURL(blob), '_blank');
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

  const btnStyle = {
    padding: '8px 16px', border: 'none', borderRadius: 6,
    fontSize: 13, fontWeight: 600, cursor: 'pointer',
    fontFamily: 'var(--font-sans, system-ui)',
  };

  return createPortal(
    <div style={{
      position: 'fixed',
      top: 0,
      left: isMobile ? 0 : 'var(--sidebar-width)',
      right: 0,
      bottom: 0,
      zIndex: 9999, background: '#fff',
      display: 'flex', flexDirection: 'column',
    }}>
      <div style={{
        height: TOOLBAR_H, flexShrink: 0, background: '#1A2C32',
        display: 'flex', alignItems: 'center', gap: 10,
        padding: '0 16px', boxShadow: '0 2px 8px rgba(0,0,0,0.25)',
      }}>
        <Link to="/app/settings/templates" style={{
          ...btnStyle, background: 'rgba(255,255,255,0.15)',
          color: '#fff', textDecoration: 'none',
        }}>
          ← Zurück
        </Link>

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
            ...btnStyle, background: '#7c3aed', color: '#fff',
            opacity: importing ? 0.5 : 1,
          }}>
          {importing ? '⏳ Lädt…' : '📂 Template importieren'}
        </button>

        <input
          value={name}
          onChange={e => setName(e.target.value)}
          style={{
            flex: 1, maxWidth: 320, padding: '7px 12px', borderRadius: 6,
            border: 'none', fontSize: 14, fontWeight: 600,
            background: 'rgba(255,255,255,0.12)', color: '#fff',
          }}
          placeholder="Template-Name"
        />
        <div style={{ flex: 1 }} />
        <button onClick={handlePreview} style={{
          ...btnStyle, background: 'rgba(255,255,255,0.15)', color: '#fff',
        }}>👁 Vorschau</button>
        <button onClick={handleSave} disabled={saving} style={{
          ...btnStyle, background: saving ? '#ccc' : '#16a34a', color: '#fff',
        }}>
          {saving ? 'Speichert...' : '💾 Speichern'}
        </button>
        <button
          onClick={() => navigate('/app/settings/templates')}
          title="Editor schließen"
          style={{
            ...btnStyle, background: 'rgba(255,255,255,0.15)', color: '#fff',
            padding: '8px 12px',
          }}>
          ✕
        </button>
      </div>

      <div style={{ flex: 1, overflow: 'hidden' }}>
        {loaded && (
          <StudioEditor
            key={id}
            options={{
              licenseKey: STUDIO_LICENSE_KEY,
              project: {
                type: 'web',
                default: projectData || { pages: [{ name: 'index', component: '' }] },
              },
              storage: {
                type: 'self',
                autosaveChanges: 100,
                autosaveIntervalMs: 10000,
                onSave: async ({ project }) => {
                  const editor = editorRef.current;
                  if (!editor || !name) return;
                  try {
                    const html = editor.getHtml?.() ?? '';
                    const css  = editor.getCss?.()  ?? '';
                    const pd   = editor.getProjectData?.() ?? project ?? null;
                    await fetch(`${API_BASE_URL}/api/templates/${id}`, {
                      method: 'PUT',
                      headers: { ...headers, 'Content-Type': 'application/json' },
                      body: JSON.stringify({ name, html_content: html, css_content: css, grapes_data: pd }),
                    });
                  } catch (e) { console.warn('Template Autosave fehlgeschlagen:', e); }
                },
                onLoad: async () => {
                  try {
                    const res = await fetch(`${API_BASE_URL}/api/templates/${id}`, { headers });
                    if (!res.ok) return { project: { pages: [{ name: 'index', component: '' }] } };
                    const tpl = await res.json();
                    if (tpl?.grapes_data) {
                      try {
                        const data = typeof tpl.grapes_data === 'string' ? JSON.parse(tpl.grapes_data) : tpl.grapes_data;
                        if (data && typeof data === 'object' && Object.keys(data).length > 0) return { project: data };
                      } catch { /* fallthrough */ }
                    }
                    if (tpl?.html_content) {
                      return { project: { pages: [{ name: tpl.name || 'index', component: tpl.html_content, styles: tpl.css_content || '' }] } };
                    }
                    return { project: { pages: [{ name: 'index', component: '' }] } };
                  } catch { return { project: { pages: [{ name: 'index', component: '' }] } }; }
                },
              },
              plugins,
            }}
            onReady={(editor) => { editorRef.current = editor; }}
          />
        )}
      </div>
    </div>,
    document.body
  );
}

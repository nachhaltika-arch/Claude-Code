import React, { useEffect, useRef, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import grapesjs from 'grapesjs';
import grapesjsPresetWebpage from 'grapesjs-preset-webpage';
import grapesjsBlocksBasic from 'grapesjs-blocks-basic';
import 'grapesjs/dist/css/grapes.min.css';
import toast from 'react-hot-toast';
import API_BASE_URL from '../config';
import { useAuth } from '../context/AuthContext';

const TOOLBAR_H = 56;

export default function TemplateEditor() {
  const { id } = useParams();
  const { token } = useAuth();
  const headers = token ? { Authorization: `Bearer ${token}` } : {};
  const containerRef = useRef(null);
  const editorRef = useRef(null);
  const [name, setName] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!containerRef.current) return;

    const editor = grapesjs.init({
      container: containerRef.current,
      height: `calc(100vh - ${TOOLBAR_H}px)`,
      width: '100%',
      plugins: [grapesjsPresetWebpage, grapesjsBlocksBasic],
      pluginsOpts: { [grapesjsPresetWebpage]: {}, [grapesjsBlocksBasic]: {} },
      storageManager: false,
      components: '',
      style: '',
    });
    editorRef.current = editor;

    // Load template data
    fetch(`${API_BASE_URL}/api/templates/${id}`, { headers })
      .then(r => r.ok ? r.json() : null)
      .then(tpl => {
        if (!tpl) return;
        setName(tpl.name || '');
        if (tpl.grapes_data) {
          try { editor.loadProjectData(typeof tpl.grapes_data === 'string' ? JSON.parse(tpl.grapes_data) : tpl.grapes_data); return; }
          catch { /* fall through */ }
        }
        if (tpl.html_content) editor.setComponents(tpl.html_content);
        if (tpl.css_content) editor.setStyle(tpl.css_content);
      })
      .catch(() => {});

    return () => { editor.destroy(); editorRef.current = null; };
  }, [id]); // eslint-disable-line

  const handleSave = async () => {
    const editor = editorRef.current;
    if (!editor) return;
    setSaving(true);
    try {
      const r = await fetch(`${API_BASE_URL}/api/templates/${id}`, {
        method: 'PUT',
        headers: { ...headers, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name,
          grapes_data: editor.getProjectData(),
          html_content: editor.getHtml(),
          css_content: editor.getCss(),
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
    const html = `<!DOCTYPE html><html><head><style>${editor.getCss()}</style></head><body>${editor.getHtml()}</body></html>`;
    const blob = new Blob([html], { type: 'text/html' });
    window.open(URL.createObjectURL(blob), '_blank');
  };

  const btnStyle = { padding: '8px 16px', border: 'none', borderRadius: 6, fontSize: 13, fontWeight: 600, cursor: 'pointer', fontFamily: 'var(--font-sans, system-ui)' };

  return (
    <div style={{ position: 'fixed', inset: 0, zIndex: 9999, background: '#fff', display: 'flex', flexDirection: 'column' }}>
      <div style={{ height: TOOLBAR_H, flexShrink: 0, background: '#1A2C32', display: 'flex', alignItems: 'center', gap: 12, padding: '0 16px', boxShadow: '0 2px 8px rgba(0,0,0,0.25)' }}>
        <Link to="/app/settings/templates" style={{ ...btnStyle, background: 'rgba(255,255,255,0.15)', color: '#fff', textDecoration: 'none' }}>
          ← Zurück
        </Link>
        <input
          value={name}
          onChange={e => setName(e.target.value)}
          style={{ flex: 1, maxWidth: 320, padding: '7px 12px', borderRadius: 6, border: 'none', fontSize: 14, fontWeight: 600, background: 'rgba(255,255,255,0.12)', color: '#fff' }}
          placeholder="Template-Name"
        />
        <div style={{ flex: 1 }} />
        <button onClick={handlePreview} style={{ ...btnStyle, background: 'rgba(255,255,255,0.15)', color: '#fff' }}>👁 Vorschau</button>
        <button onClick={handleSave} disabled={saving} style={{ ...btnStyle, background: saving ? '#ccc' : '#16a34a', color: '#fff' }}>
          {saving ? 'Speichert...' : '💾 Speichern'}
        </button>
      </div>
      <div ref={containerRef} style={{ flex: 1, overflow: 'hidden' }} />
    </div>
  );
}

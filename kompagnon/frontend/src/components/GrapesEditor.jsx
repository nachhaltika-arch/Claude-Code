import { useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import grapesjs from 'grapesjs';
import 'grapesjs/dist/css/grapes.min.css';
import gjsPresetWebpage from 'grapesjs-preset-webpage';
import gjsBlocksBasic from 'grapesjs-blocks-basic';
import { useAuth } from '../context/AuthContext';
import API_BASE_URL from '../config';
import toast from 'react-hot-toast';

export default function GrapesEditor({ pageId, pageName, initialHtml, onClose, onSave, projectId, netlitySiteId }) {
  const editorRef = useRef(null);
  const containerRef = useRef(null);
  const { token } = useAuth();
  const headers = { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` };
  const [netlifyDeploying, setNetlifyDeploying] = useState(false);

  // Lock body scroll while editor is open
  useEffect(() => {
    document.body.style.overflow = 'hidden';
    return () => { document.body.style.overflow = ''; };
  }, []);

  useEffect(() => {
    if (editorRef.current || !containerRef.current) return;
    const editor = grapesjs.init({
      container: containerRef.current,
      height: '100%',
      width: '100%',
      storageManager: false,
      plugins: [gjsPresetWebpage, gjsBlocksBasic],
      pluginsOpts: {
        [gjsPresetWebpage]: { blocks: ['link-block', 'quote', 'text-basic'] },
        [gjsBlocksBasic]: { blocks: ['column1','column2','column3','text','link','image','video'], flexGrid: true },
      },
      deviceManager: { devices: [
        { id: 'desktop', name: 'Desktop', width: '' },
        { id: 'tablet', name: 'Tablet', width: '768px', widthMedia: '992px' },
        { id: 'mobile', name: 'Mobil', width: '375px', widthMedia: '575px' },
      ]},
    });
    if (initialHtml && typeof initialHtml === 'string' && initialHtml.trim().startsWith('<')) {
      editor.setComponents(initialHtml);
    }
    fetch(`${API_BASE_URL}/api/pages/${pageId}/editor`, { headers })
      .then(r => r.ok ? r.json() : null)
      .then(data => { if (data?.html) editor.setComponents(data.html); if (data?.css) editor.setStyle(data.css); })
      .catch(() => {});
    editorRef.current = editor;
    return () => { if (editorRef.current) { editorRef.current.destroy(); editorRef.current = null; } };
  }, [pageId]); // eslint-disable-line

  const save = async () => {
    if (!editorRef.current) return;
    const html = editorRef.current.getHtml();
    const css = editorRef.current.getCss();
    try {
      await fetch(`${API_BASE_URL}/api/pages/${pageId}/editor`, {
        method: 'POST', headers,
        body: JSON.stringify({ html, css, gjsData: editorRef.current.getProjectData() }),
      });
      toast.success('Gespeichert!');
      if (onSave) onSave({ html, css });
    } catch { toast.error('Fehler beim Speichern'); }
  };

  const preview = () => {
    if (!editorRef.current) return;
    const w = window.open('', '_blank');
    w.document.write(`<!DOCTYPE html><html><head><style>${editorRef.current.getCss()}</style></head><body>${editorRef.current.getHtml()}</body></html>`);
    w.document.close();
  };

  const netlifyDeploy = async () => {
    if (!editorRef.current || !projectId) return;
    const html = editorRef.current.getHtml();
    const css  = editorRef.current.getCss();
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
      toast.error('Deploy fehlgeschlagen — bitte HTML prüfen');
    } finally {
      setNetlifyDeploying(false);
    }
  };

  return createPortal(
    <div style={{
      position: 'fixed',
      top: 0, left: 0,
      width: '100vw',
      height: '100vh',
      zIndex: 99999,
      display: 'flex',
      flexDirection: 'column',
      background: '#1a1a1a',
      overflow: 'hidden',
    }}>
      {/* Toolbar */}
      <div style={{
        height: 52,
        flexShrink: 0,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 16px',
        background: '#1a2332',
        color: '#fff',
        zIndex: 1,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <button onClick={onClose} style={{ background: 'none', border: '1px solid rgba(255,255,255,0.3)', color: '#fff', padding: '5px 12px', borderRadius: 6, cursor: 'pointer', fontSize: 13 }}>← Zurück</button>
          <span style={{ fontSize: 14, fontWeight: 600 }}>{pageName}</span>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button onClick={preview} style={{ background: 'none', border: '1px solid rgba(255,255,255,0.3)', color: '#fff', padding: '6px 14px', borderRadius: 6, cursor: 'pointer', fontSize: 13 }}>👁 Vorschau</button>
          {projectId && netlitySiteId && (
            <button
              onClick={netlifyDeploy}
              disabled={netlifyDeploying}
              style={{ background: netlifyDeploying ? '#166534' : '#16a34a', border: 'none', color: '#fff', padding: '6px 16px', borderRadius: 6, cursor: netlifyDeploying ? 'not-allowed' : 'pointer', fontSize: 13, fontWeight: 600, opacity: netlifyDeploying ? 0.8 : 1 }}
            >
              {netlifyDeploying ? '⏳ Wird deployed…' : '🚀 Direkt zu Netlify deployen'}
            </button>
          )}
          <button onClick={save} style={{ background: '#0d6efd', border: 'none', color: '#fff', padding: '6px 16px', borderRadius: 6, cursor: 'pointer', fontSize: 13, fontWeight: 600 }}>💾 Speichern</button>
        </div>
      </div>
      {/* Canvas */}
      <div ref={containerRef} style={{
        flex: 1,
        width: '100%',
        minHeight: 0,
      }} />
    </div>,
    document.body
  );
}

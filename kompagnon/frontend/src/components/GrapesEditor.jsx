import { useEffect, useRef, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import API_BASE_URL from '../config';

const GJS_CSS = 'https://unpkg.com/grapesjs/dist/css/grapes.min.css';
const GJS_JS  = 'https://unpkg.com/grapesjs';

function loadScript(src) {
  return new Promise((resolve, reject) => {
    if (document.querySelector(`script[src="${src}"]`)) { resolve(); return; }
    const s = document.createElement('script');
    s.src = src; s.async = true;
    s.onload = resolve; s.onerror = reject;
    document.head.appendChild(s);
  });
}

function loadStyle(href) {
  if (document.querySelector(`link[href="${href}"]`)) return;
  const l = document.createElement('link');
  l.rel = 'stylesheet'; l.href = href;
  document.head.appendChild(l);
}

const BLOCKS = [
  { id: 'text',    label: '📝 Text',     content: '<p style="padding:8px">Text hier eingeben</p>' },
  { id: 'heading', label: '🔤 Überschrift', content: '<h2 style="padding:8px">Überschrift</h2>' },
  { id: 'image',   label: '🖼️ Bild',     content: '<img src="https://placehold.co/800x400" style="max-width:100%;display:block"/>' },
  { id: 'button',  label: '🔘 Button',   content: '<a href="#" style="display:inline-block;padding:12px 28px;background:#008EAA;color:#fff;border-radius:6px;text-decoration:none;font-weight:600">Jetzt anfragen</a>' },
  { id: 'hero',    label: '🦸 Hero',     content: '<div style="background:#008EAA;color:#fff;padding:80px 40px;text-align:center"><h1 style="margin:0 0 16px">Ihre Überschrift</h1><p style="margin:0 0 28px;font-size:18px">Unterzeile mit Ihrer Botschaft</p><a href="#" style="background:#fff;color:#008EAA;padding:12px 28px;border-radius:6px;text-decoration:none;font-weight:700">Jetzt anfragen</a></div>' },
  { id: 'section', label: '📦 Abschnitt', content: '<section style="padding:60px 40px;max-width:900px;margin:0 auto"><h2>Titel</h2><p>Ihr Inhalt hier…</p></section>' },
  { id: 'cols2',   label: '⬜⬜ 2 Spalten', content: '<div style="display:grid;grid-template-columns:1fr 1fr;gap:24px;padding:40px"><div style="background:#f5f5f5;padding:24px;border-radius:8px"><h3>Spalte 1</h3><p>Inhalt</p></div><div style="background:#f5f5f5;padding:24px;border-radius:8px"><h3>Spalte 2</h3><p>Inhalt</p></div></div>' },
  { id: 'card',    label: '🃏 Karte',    content: '<div style="background:#fff;border:1px solid #ddd;border-radius:12px;padding:28px;box-shadow:0 2px 8px rgba(0,0,0,0.08);max-width:360px"><h3 style="margin:0 0 8px">Kartentitel</h3><p style="margin:0;color:#555">Karteninhalt</p></div>' },
];

export default function GrapesEditor({ pageId, pageName, initialHtml, onClose, onSave }) {
  const { token } = useAuth();
  const containerRef = useRef(null);
  const editorRef    = useRef(null);
  const [ready,   setReady]   = useState(false);
  const [saving,  setSaving]  = useState(false);
  const [device,  setDevice]  = useState('desktop');
  const [saveOk,  setSaveOk]  = useState(false);

  const h = { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) };

  useEffect(() => {
    loadStyle(GJS_CSS);
    loadScript(GJS_JS).then(() => setReady(true));
  }, []);

  useEffect(() => {
    if (!ready || !containerRef.current) return;
    const grapesjs = window.grapesjs;
    if (!grapesjs) return;

    const editor = grapesjs.init({
      container: containerRef.current,
      height: '100%',
      width: '100%',
      storageManager: false,
      panels: { defaults: [] },
      canvas: {
        styles: ['https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&display=swap'],
      },
      blockManager: {
        appendTo: '#gjs-blocks-panel',
        blocks: BLOCKS,
      },
      deviceManager: {
        devices: [
          { name: 'Desktop',  width: '' },
          { name: 'Tablet',   width: '768px' },
          { name: 'Mobile',   width: '390px' },
        ],
      },
    });

    editorRef.current = editor;

    // Load saved data first, fall back to initialHtml
    fetch(`${API_BASE_URL}/api/pages/${pageId}/editor`, { headers: h })
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        if (data?.html && data.html.trim()) {
          editor.setComponents(data.html);
          if (data.css) editor.setStyle(data.css);
        } else if (initialHtml && initialHtml.trim().startsWith('<')) {
          editor.setComponents(initialHtml);
        }
      })
      .catch(() => {
        if (initialHtml && initialHtml.trim().startsWith('<')) {
          editor.setComponents(initialHtml);
        }
      });

    return () => { editor.destroy(); editorRef.current = null; };
  }, [ready]); // eslint-disable-line react-hooks/exhaustive-deps

  const switchDevice = (name) => {
    editorRef.current?.setDevice(name);
    setDevice(name.toLowerCase());
  };

  const handleSave = async () => {
    if (!editorRef.current) return;
    setSaving(true);
    try {
      const html = editorRef.current.getHtml();
      const css  = editorRef.current.getCss();
      const gjsData = editorRef.current.getProjectData?.() || {};
      await fetch(`${API_BASE_URL}/api/pages/${pageId}/editor`, {
        method: 'POST', headers: h,
        body: JSON.stringify({ html, css, gjsData }),
      });
      setSaveOk(true);
      setTimeout(() => setSaveOk(false), 2000);
      onSave?.({ html, css });
    } catch (e) {
      console.error('GrapesJS save error', e);
    } finally {
      setSaving(false);
    }
  };

  const openPreview = () => {
    if (!editorRef.current) return;
    const html = editorRef.current.getHtml();
    const css  = editorRef.current.getCss();
    const doc  = `<!DOCTYPE html><html><head><meta charset="utf-8"><style>${css}</style></head><body>${html}</body></html>`;
    const url  = 'data:text/html;charset=utf-8,' + encodeURIComponent(doc);
    window.open(url, '_blank');
  };

  const btnBase = {
    padding: '6px 14px', borderRadius: 6, fontSize: 13, fontWeight: 600,
    cursor: 'pointer', border: 'none', fontFamily: 'var(--font-sans)',
    display: 'inline-flex', alignItems: 'center', gap: 5,
  };
  const devBtn = (name) => ({
    ...btnBase,
    background: device === name ? 'rgba(255,255,255,0.2)' : 'transparent',
    color: '#fff',
    border: device === name ? '1px solid rgba(255,255,255,0.4)' : '1px solid transparent',
  });

  return (
    <div style={{ position: 'fixed', inset: 0, zIndex: 9000, display: 'flex', flexDirection: 'column', background: '#1a1a1a' }}>
      {/* Toolbar */}
      <div style={{ height: 48, background: '#0f2024', display: 'flex', alignItems: 'center', gap: 10, padding: '0 14px', flexShrink: 0 }}>
        {/* Left: back + page name */}
        <button onClick={onClose} style={{ ...btnBase, background: 'transparent', color: 'rgba(255,255,255,0.7)', border: '1px solid rgba(255,255,255,0.2)' }}>
          ← Zurück
        </button>
        <span style={{ fontSize: 13, fontWeight: 700, color: '#fff', marginLeft: 4 }}>
          {pageName}
        </span>

        {/* Center: device switcher */}
        <div style={{ flex: 1, display: 'flex', justifyContent: 'center', gap: 4 }}>
          <button onClick={() => switchDevice('Desktop')} style={devBtn('desktop')}>🖥 Desktop</button>
          <button onClick={() => switchDevice('Tablet')}  style={devBtn('tablet')}>📱 Tablet</button>
          <button onClick={() => switchDevice('Mobile')}  style={devBtn('mobile')}>📲 Mobil</button>
        </div>

        {/* Right: preview + save */}
        <button onClick={openPreview} style={{ ...btnBase, background: 'transparent', color: 'rgba(255,255,255,0.7)', border: '1px solid rgba(255,255,255,0.2)' }}>
          👁 Vorschau
        </button>
        <button onClick={handleSave} disabled={saving} style={{ ...btnBase, background: saveOk ? '#16a34a' : '#008EAA', color: '#fff', opacity: saving ? 0.7 : 1 }}>
          {saving ? '⏳ Speichert…' : saveOk ? '✓ Gespeichert' : '💾 Speichern'}
        </button>
      </div>

      {/* Editor area */}
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        {/* Blocks panel */}
        <div id="gjs-blocks-panel" style={{ width: 160, background: '#18292e', overflowY: 'auto', flexShrink: 0 }} />

        {/* Canvas */}
        <div style={{ flex: 1, overflow: 'hidden' }}>
          {!ready && (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#aaa', fontSize: 14 }}>
              Editor wird geladen…
            </div>
          )}
          <div ref={containerRef} style={{ width: '100%', height: '100%', display: ready ? 'block' : 'none' }} />
        </div>
      </div>
    </div>
  );
}

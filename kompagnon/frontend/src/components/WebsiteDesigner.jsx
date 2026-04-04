import { useEffect, useRef } from 'react';
import grapesjs from 'grapesjs';
import grapesjsPresetWebpage from 'grapesjs-preset-webpage';
import grapesjsBlocksBasic from 'grapesjs-blocks-basic';
import 'grapesjs/dist/css/grapes.min.css';

const TOOLBAR_H = 52;

export default function WebsiteDesigner({ customerId, customerName, onClose }) {
  const containerRef = useRef(null);
  const editorRef    = useRef(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const editor = grapesjs.init({
      container: containerRef.current,
      height: `calc(100vh - ${TOOLBAR_H}px)`,
      width: '100%',
      plugins: [grapesjsPresetWebpage, grapesjsBlocksBasic],
      pluginsOpts: {
        [grapesjsPresetWebpage]: {},
        [grapesjsBlocksBasic]: {},
      },
      storageManager: false,
      components: '',
      style: '',
    });

    editorRef.current = editor;

    return () => {
      editor.destroy();
      editorRef.current = null;
    };
  }, []); // eslint-disable-line

  const handleLoadKiEntwurf = async () => {
    const editor = editorRef.current;
    if (!editor) return;
    try {
      const token = localStorage.getItem('kompagnon_token');
      const API_BASE_URL = process.env.REACT_APP_API_URL || '';
      const res = await fetch(`${API_BASE_URL}/api/briefings/${customerId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) return;
      const briefing = await res.json();

      const name = customerName || `Kunde #${customerId}`;
      const gewerk = briefing.gewerk || '';
      const usp    = briefing.usp    || '';
      const leistungen = briefing.leistungen || '';

      const html = `
        <section style="font-family:sans-serif;max-width:900px;margin:0 auto;padding:40px 24px">
          <h1 style="font-size:2.2rem;font-weight:800;color:#1A2C32;margin-bottom:12px">${name}</h1>
          ${gewerk ? `<p style="font-size:1.1rem;color:#008EAA;font-weight:600;margin-bottom:24px">${gewerk}</p>` : ''}
          ${usp ? `<blockquote style="border-left:4px solid #008EAA;padding:12px 20px;background:#f0fafd;margin:0 0 24px;font-size:1rem;color:#1A2C32">${usp}</blockquote>` : ''}
          ${leistungen ? `<h2 style="font-size:1.3rem;font-weight:700;color:#1A2C32;margin-bottom:12px">Unsere Leistungen</h2><p style="color:#444;line-height:1.7">${leistungen.replace(/\n/g, '<br/>')}</p>` : ''}
        </section>
      `;
      editor.setComponents(html);
    } catch (e) {
      console.error('KI-Entwurf laden fehlgeschlagen:', e);
    }
  };

  const handlePushToCms = async () => {
    const editor = editorRef.current;
    if (!editor) return;
    const html = editor.getHtml();
    const css  = editor.getCss();
    try {
      const token = localStorage.getItem('kompagnon_token');
      const API_BASE_URL = process.env.REACT_APP_API_URL || '';
      const res = await fetch(`${API_BASE_URL}/api/customers/${customerId}/cms-push`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ html, css }),
      });
      if (res.ok) {
        alert('Erfolgreich zum CMS gepusht.');
      } else {
        const err = await res.json().catch(() => ({}));
        alert(`Fehler: ${err.detail || res.status}`);
      }
    } catch (e) {
      alert(`Verbindungsfehler: ${e.message}`);
    }
  };

  const handleDownloadHtml = () => {
    const editor = editorRef.current;
    if (!editor) return;
    const html = `<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>${customerName || 'Website'}</title>
  <style>${editor.getCss()}</style>
</head>
<body>${editor.getHtml()}</body>
</html>`;
    const blob = new Blob([html], { type: 'text/html' });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href     = url;
    a.download = `website-${customerId}.html`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const btnStyle = {
    padding: '8px 16px',
    border: 'none',
    borderRadius: 6,
    fontSize: 13,
    fontWeight: 600,
    cursor: 'pointer',
    fontFamily: 'var(--font-sans, system-ui)',
    background: 'rgba(255,255,255,0.15)',
    color: '#fff',
    transition: 'background 0.15s',
  };

  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 9999,
      background: '#fff', display: 'flex', flexDirection: 'column',
    }}>
      {/* Toolbar */}
      <div style={{
        height: TOOLBAR_H, flexShrink: 0,
        background: '#1A2C32',
        display: 'flex', alignItems: 'center',
        gap: 8, padding: '0 16px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.25)',
      }}>
        <span style={{ fontSize: 14, fontWeight: 700, color: '#fff', marginRight: 8, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: 200 }}>
          {customerName || `Kunde #${customerId}`}
        </span>

        <div style={{ flex: 1 }} />

        <button style={btnStyle} onClick={handleLoadKiEntwurf}>
          🤖 KI-Entwurf laden
        </button>
        <button style={btnStyle} onClick={handlePushToCms}>
          🚀 Zum CMS pushen
        </button>
        <button style={btnStyle} onClick={handleDownloadHtml}>
          📥 Als HTML herunterladen
        </button>

        <button
          onClick={onClose}
          style={{ ...btnStyle, background: 'rgba(255,255,255,0.08)', marginLeft: 8, fontSize: 18, lineHeight: 1, padding: '6px 12px' }}
        >
          ✕
        </button>
      </div>

      {/* GrapesJS canvas */}
      <div ref={containerRef} style={{ flex: 1, overflow: 'hidden' }} />
    </div>
  );
}

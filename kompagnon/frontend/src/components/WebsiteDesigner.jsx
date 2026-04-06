import { useEffect, useRef, useState } from 'react';
import grapesjs from 'grapesjs';
import grapesjsPresetWebpage from 'grapesjs-preset-webpage';
import grapesjsBlocksBasic from 'grapesjs-blocks-basic';
import 'grapesjs/dist/css/grapes.min.css';
import toast from 'react-hot-toast';
import API_BASE_URL from '../config';
import TemplateGallery from './TemplateGallery';

const TOOLBAR_H = 52;

export default function WebsiteDesigner({ customerId, customerName, onClose }) {
  const containerRef = useRef(null);
  const editorRef    = useRef(null);
  const [kiLoading, setKiLoading]   = useState(false);
  const [cmsLoading, setCmsLoading] = useState(false);
  const [cmsConn, setCmsConn]       = useState(null); // {cms_type, has_cms_connection}
  const [showGallery, setShowGallery] = useState(false);

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

  // Load CMS connection info for dynamic button label
  useEffect(() => {
    const token = localStorage.getItem('kompagnon_token');
    fetch(`${API_BASE_URL}/api/customers/${customerId}/cms-connection`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(r => r.ok ? r.json() : null)
      .then(d => { if (d) setCmsConn(d); })
      .catch(() => {});
  }, [customerId]); // eslint-disable-line

  const handleLoadKiEntwurf = async () => {
    const editor = editorRef.current;
    if (!editor || kiLoading) return;
    setKiLoading(true);
    try {
      const token = localStorage.getItem('kompagnon_token');
      const res = await fetch(
        `${API_BASE_URL}/api/customers/${customerId}/generate-mockup`,
        {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Fehler ${res.status}`);
      }
      const data = await res.json();
      editor.setComponents(data.html);
    } catch (e) {
      console.error('KI-Entwurf laden fehlgeschlagen:', e);
      alert(`KI-Entwurf fehlgeschlagen: ${e.message}`);
    } finally {
      setKiLoading(false);
    }
  };

  const handlePushToCms = async () => {
    const editor = editorRef.current;
    if (!editor || cmsLoading) return;
    setCmsLoading(true);
    try {
      const token = localStorage.getItem('kompagnon_token');
      const authHeader = { Authorization: `Bearer ${token}` };

      // 1. Check which CMS is configured
      const connRes = await fetch(
        `${API_BASE_URL}/api/customers/${customerId}/cms-connection`,
        { headers: authHeader }
      );
      if (!connRes.ok) throw new Error('CMS-Verbindung konnte nicht geladen werden');
      const conn = await connRes.json();

      if (!conn.has_cms_connection || conn.cms_type === 'none' || !conn.cms_type) {
        toast.error('Keine CMS-Verbindung konfiguriert. Bitte zuerst CMS-Zugangsdaten hinterlegen.');
        return;
      }

      // 2. Update local conn state for label refresh
      setCmsConn(conn);

      // 3. Combine HTML + CSS and push
      const html = editor.getHtml() + `<style>${editor.getCss()}</style>`;
      const pubRes = await fetch(
        `${API_BASE_URL}/api/customers/${customerId}/publish`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', ...authHeader },
          body: JSON.stringify({ html, page_title: customerName || `Kunde #${customerId}` }),
        }
      );
      const result = await pubRes.json().catch(() => ({}));

      if (pubRes.ok && result.success) {
        const cmsName = conn.cms_type === 'webflow' ? 'Webflow' : 'WordPress';
        toast.success(
          result.page_url
            ? <span>✅ Seite als Entwurf in {cmsName} erstellt – <a href={result.page_url} target="_blank" rel="noopener noreferrer" style={{ color: 'inherit', textDecoration: 'underline' }}>Seite öffnen ↗</a></span>
            : `✅ Seite als Entwurf in ${cmsName} erstellt`,
          { duration: 6000 }
        );
      } else {
        throw new Error(result.detail || result.message || `HTTP ${pubRes.status}`);
      }
    } catch (e) {
      toast.error(`CMS Push fehlgeschlagen: ${e.message}`, { duration: 5000 });
    } finally {
      setCmsLoading(false);
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

        <button
          style={{ ...btnStyle, opacity: kiLoading ? 0.7 : 1, cursor: kiLoading ? 'not-allowed' : 'pointer', display: 'inline-flex', alignItems: 'center', gap: 7 }}
          onClick={handleLoadKiEntwurf}
          disabled={kiLoading}
        >
          {kiLoading
            ? <><span style={{ width: 12, height: 12, borderRadius: '50%', border: '2px solid rgba(255,255,255,0.3)', borderTopColor: 'white', animation: 'spin 0.8s linear infinite', display: 'inline-block', flexShrink: 0 }} /> KI erstellt deinen Entwurf...</>
            : '🤖 KI-Entwurf laden'
          }
        </button>
        {(() => {
          const hasCms = cmsConn?.has_cms_connection;
          const cmsType = cmsConn?.cms_type;
          const label = cmsType === 'wordpress_elementor' ? '🚀 Zu WordPress pushen'
            : cmsType === 'webflow' ? '🚀 Zu Webflow pushen'
            : '🚀 Zum CMS pushen';
          const pushingLabel = cmsType === 'webflow' ? 'Pushe zu Webflow...' : 'Pushe zu WordPress...';
          const disabled = cmsLoading || !hasCms;
          return (
            <button
              style={{ ...btnStyle, opacity: disabled ? 0.45 : 1, cursor: disabled ? 'not-allowed' : 'pointer', display: 'inline-flex', alignItems: 'center', gap: 7 }}
              onClick={handlePushToCms}
              disabled={disabled}
              title={!hasCms ? 'CMS-Verbindung im Kundenprofil einrichten' : undefined}
            >
              {cmsLoading
                ? <><span style={{ width: 12, height: 12, borderRadius: '50%', border: '2px solid rgba(255,255,255,0.3)', borderTopColor: 'white', animation: 'spin 0.8s linear infinite', display: 'inline-block', flexShrink: 0 }} />{pushingLabel}</>
                : label
              }
            </button>
          );
        })()}
        <button onClick={() => setShowGallery(true)}
          style={{ padding:'8px 16px', background:'#6f42c1', color:'#fff', border:'none', borderRadius:6, cursor:'pointer', fontWeight:600 }}>
          🗂️ Template laden
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

      {showGallery && (
        <TemplateGallery
          onSelect={(tpl) => {
            if (editorRef.current) {
              editorRef.current.setComponents(tpl.html);
              editorRef.current.setStyle('');
            }
            setShowGallery(false);
          }}
          onClose={() => setShowGallery(false)}
        />
      )}
    </div>
  );
}

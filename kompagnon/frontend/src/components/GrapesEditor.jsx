import { useEffect, useRef, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import API_BASE_URL from '../config';

// ── CDN resources ──────────────────────────────────────────────────────────────
const GJS_CSS      = 'https://unpkg.com/grapesjs/dist/css/grapes.min.css';
const GJS_JS       = 'https://unpkg.com/grapesjs';
const GJS_BLOCKS   = 'https://unpkg.com/grapesjs-blocks-basic';
const GJS_WEBPAGE  = 'https://unpkg.com/grapesjs-preset-webpage';
const GJS_FORMS    = 'https://unpkg.com/grapesjs-plugin-forms';

function loadScript(src) {
  return new Promise((resolve, reject) => {
    if (document.querySelector(`script[src="${src}"]`)) { resolve(); return; }
    const s = document.createElement('script');
    s.src = src; s.async = false;
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

// ── Style overrides injected once ──────────────────────────────────────────────
const EDITOR_STYLES = `
  .gjs-editor { font-family: var(--font-sans, system-ui, sans-serif); }
  .gjs-pn-panels { display: none; }
  .gjs-cv-canvas { top: 0; }
  .gjs-block-category .gjs-title { background: #1e2d31; color: #ccc; font-size: 11px; letter-spacing: 0.06em; text-transform: uppercase; }
  .gjs-block { border-color: #2e3f44; color: #ddd; background: #1a2e33; }
  .gjs-block:hover { border-color: #008EAA; background: #1e3840; }
  .gjs-block__media { color: #008EAA; }
  .gjs-sm-sector-title { background: #1e2d31; color: #aaa; font-size: 11px; letter-spacing: 0.06em; text-transform: uppercase; }
  .gjs-sm-property { padding: 6px 10px; }
  .gjs-sm-label { color: #aaa; font-size: 11px; }
  .gjs-sm-input-holder input, .gjs-sm-input-holder select { background: #1a2e33; color: #ddd; border-color: #2e3f44; border-radius: 4px; }
  .gjs-sm-composite { border-color: #2e3f44; }
  .gjs-layer { border-color: #2e3f44; color: #ccc; }
  .gjs-layer-name { color: #ccc; }
  .gjs-layer:hover { background: #1e3840; }
  .gjs-layer.gjs-hovered { background: #1e3840; }
  .gjs-layer.gjs-selected { background: #1e3840; border-left: 3px solid #008EAA; }
  .gjs-trt-trait { padding: 6px 10px; }
  .gjs-trt-trait__wrp-label { color: #aaa; font-size: 11px; }
  .gjs-trt-trait input, .gjs-trt-trait select { background: #1a2e33; color: #ddd; border: 1px solid #2e3f44; border-radius: 4px; padding: 4px 8px; width: 100%; box-sizing: border-box; }
  .gjs-editor-cont { background: #111; }
  .gjs-toolbar { background: #008EAA; }
  .gjs-toolbar-item { color: #fff; }
  .gjs-rte-toolbar { background: #1a2e33; border-color: #2e3f44; }
  .gjs-rte-actionbar button { color: #ddd; }
  .gjs-rte-actionbar button:hover { color: #fff; background: rgba(255,255,255,0.1); }
  .gjs-mdl-dialog { background: #1a2e33; border-color: #2e3f44; color: #ddd; }
  .gjs-mdl-title { color: #fff; }
  .gjs-btn-prim { background: #008EAA; color: #fff; border: none; border-radius: 6px; padding: 8px 16px; cursor: pointer; }
  .gjs-btn-prim:hover { background: #007a94; }
  .gjs-field { background: #1a2e33; border-color: #2e3f44; color: #ddd; }
  .gjs-field input, .gjs-field textarea, .gjs-field select { color: #ddd; background: transparent; }
  .gjs-clm-tag { background: #1e3840; color: #ddd; border-color: #2e3f44; }
  .gjs-clm-tag-status { background: #008EAA; }
  .gjs-sm-color-picker { z-index: 99999; }
  #gjs-left-panel::-webkit-scrollbar, #gjs-right-panel::-webkit-scrollbar { width: 4px; }
  #gjs-left-panel::-webkit-scrollbar-track, #gjs-right-panel::-webkit-scrollbar-track { background: #111; }
  #gjs-left-panel::-webkit-scrollbar-thumb, #gjs-right-panel::-webkit-scrollbar-thumb { background: #2e3f44; border-radius: 2px; }
`;

export default function GrapesEditor({ pageId, pageName, initialHtml, onClose, onSave }) {
  const { token } = useAuth();
  const containerRef  = useRef(null);
  const editorRef     = useRef(null);
  const [ready,   setReady]   = useState(false);
  const [saving,  setSaving]  = useState(false);
  const [saveOk,  setSaveOk]  = useState(false);
  const [device,  setDevice]  = useState('desktop');
  const [leftTab, setLeftTab] = useState('blocks');   // 'blocks' | 'layers'
  const [rightTab, setRightTab] = useState('styles'); // 'styles' | 'traits'

  const h = { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) };

  // Inject editor styles once
  useEffect(() => {
    if (!document.getElementById('gjs-custom-styles')) {
      const style = document.createElement('style');
      style.id = 'gjs-custom-styles';
      style.textContent = EDITOR_STYLES;
      document.head.appendChild(style);
    }
    loadStyle(GJS_CSS);
    loadScript(GJS_JS)
      .then(() => loadScript(GJS_BLOCKS))
      .then(() => loadScript(GJS_WEBPAGE))
      .then(() => loadScript(GJS_FORMS))
      .then(() => setReady(true));
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
        styles: [
          'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap',
        ],
      },
      // Block manager renders into our custom left panel
      blockManager: {
        appendTo: '#gjs-blocks-panel',
      },
      // Style manager renders into our custom right panel
      styleManager: {
        appendTo: '#gjs-styles-panel',
        sectors: [
          {
            name: 'Abmessungen',
            open: false,
            properties: [
              'width', 'min-width', 'max-width',
              'height', 'min-height', 'max-height',
              { property: 'margin', type: 'composite' },
              { property: 'padding', type: 'composite' },
            ],
          },
          {
            name: 'Typografie',
            open: false,
            properties: [
              'font-family', 'font-size', 'font-weight', 'line-height',
              'letter-spacing', 'color', 'text-align', 'text-decoration',
            ],
          },
          {
            name: 'Hintergrund',
            open: false,
            properties: [
              'background-color',
              { property: 'background-image', type: 'file' },
              'background-size', 'background-position', 'background-repeat',
            ],
          },
          {
            name: 'Rahmen',
            open: false,
            properties: [
              'border-radius',
              { property: 'border', type: 'composite' },
              'box-shadow',
            ],
          },
          {
            name: 'Layout',
            open: false,
            properties: [
              'display', 'flex-direction', 'flex-wrap',
              'align-items', 'justify-content', 'gap',
              'position', 'top', 'right', 'bottom', 'left',
              'overflow', 'opacity',
            ],
          },
        ],
      },
      // Layer manager renders into our custom left panel (layers tab)
      layerManager: {
        appendTo: '#gjs-layers-panel',
      },
      // Trait manager (component properties) renders into right panel
      traitManager: {
        appendTo: '#gjs-traits-panel',
      },
      // Asset manager
      assetManager: {
        upload: false,
        assets: [],
      },
      // Device manager
      deviceManager: {
        devices: [
          { name: 'Desktop', width: '' },
          { name: 'Tablet',  width: '768px',  widthMedia: '992px' },
          { name: 'Mobile',  width: '390px',  widthMedia: '480px' },
        ],
      },
      // Plugins
      plugins: [
        'grapesjs-blocks-basic',
        'grapesjs-preset-webpage',
        'grapesjs-plugin-forms',
      ],
      pluginsOpts: {
        'grapesjs-blocks-basic': {
          flexGrid: true,
          addBasicStyle: true,
          category: 'Grundelemente',
          blocks: ['column1', 'column2', 'column3', 'column3-7', 'text', 'link', 'image', 'video', 'map'],
        },
        'grapesjs-preset-webpage': {
          blocksBasicOpts: { flexGrid: true },
          modalImportTitle: 'HTML importieren',
          modalImportLabel: '<div style="margin-bottom:10px;font-size:13px;color:#aaa">Fügen Sie Ihren HTML-Code ein</div>',
          modalImportContent: '',
        },
        'grapesjs-plugin-forms': {
          category: 'Formular',
        },
      },
      // Rich text editor settings
      richTextEditor: {
        actions: ['bold', 'italic', 'underline', 'strikethrough', 'link', 'wrap'],
      },
    });

    editorRef.current = editor;

    // Load saved data first, fall back to initialHtml
    fetch(`${API_BASE_URL}/api/pages/${pageId}/editor`, { headers: h })
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        if (data?.gjsData && Object.keys(data.gjsData).length > 0) {
          editor.loadProjectData(data.gjsData);
        } else if (data?.html && data.html.trim()) {
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

    // Sync device state
    editor.on('device:select', () => {
      const dev = editor.getDevice();
      setDevice(dev?.toLowerCase() || 'desktop');
    });

    return () => { editor.destroy(); editorRef.current = null; };
  }, [ready]); // eslint-disable-line react-hooks/exhaustive-deps

  const switchDevice = (name) => {
    editorRef.current?.setDevice(name);
    setDevice(name.toLowerCase());
  };

  const handleUndo = () => editorRef.current?.UndoManager.undo();
  const handleRedo = () => editorRef.current?.UndoManager.redo();

  const handleSave = async () => {
    if (!editorRef.current) return;
    setSaving(true);
    try {
      const html    = editorRef.current.getHtml();
      const css     = editorRef.current.getCss();
      const gjsData = editorRef.current.getProjectData?.() || {};
      await fetch(`${API_BASE_URL}/api/pages/${pageId}/editor`, {
        method: 'POST', headers: h,
        body: JSON.stringify({ html, css, gjsData }),
      });
      setSaveOk(true);
      setTimeout(() => setSaveOk(false), 2500);
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
    const doc  = `<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>${css}</style></head><body>${html}</body></html>`;
    window.open('data:text/html;charset=utf-8,' + encodeURIComponent(doc), '_blank');
  };

  const openCodeView = () => {
    if (!editorRef.current) return;
    editorRef.current.Commands.run('core:open-code');
  };

  // ── Style helpers ──────────────────────────────────────────────────────────
  const btn = (extra = {}) => ({
    padding: '5px 12px', borderRadius: 5, fontSize: 12, fontWeight: 600,
    cursor: 'pointer', border: 'none', fontFamily: 'inherit',
    display: 'inline-flex', alignItems: 'center', gap: 5,
    ...extra,
  });

  const devBtn = (name) => ({
    ...btn(),
    background: device === name ? 'rgba(255,255,255,0.15)' : 'transparent',
    color: device === name ? '#fff' : 'rgba(255,255,255,0.55)',
    border: `1px solid ${device === name ? 'rgba(255,255,255,0.3)' : 'transparent'}`,
  });

  const tabBtn = (active) => ({
    flex: 1, padding: '7px 0', fontSize: 11, fontWeight: 700,
    textTransform: 'uppercase', letterSpacing: '0.06em', cursor: 'pointer',
    border: 'none', borderRadius: 0,
    background: active ? '#1e3840' : 'transparent',
    color: active ? '#008EAA' : '#666',
    borderBottom: active ? '2px solid #008EAA' : '2px solid transparent',
  });

  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 9000,
      display: 'flex', flexDirection: 'column',
      background: '#111', fontFamily: 'system-ui, sans-serif',
    }}>
      {/* ── Toolbar ───────────────────────────────────────────────────────────── */}
      <div style={{
        height: 48, background: '#0d1e22', borderBottom: '1px solid #1e3840',
        display: 'flex', alignItems: 'center', gap: 6, padding: '0 12px', flexShrink: 0,
      }}>
        {/* Back + name */}
        <button onClick={onClose} style={btn({ background: 'transparent', color: 'rgba(255,255,255,0.65)', border: '1px solid rgba(255,255,255,0.15)' })}>
          ← Zurück
        </button>
        <span style={{ fontSize: 13, fontWeight: 700, color: '#fff', marginLeft: 2, marginRight: 6, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: 200 }}>
          {pageName}
        </span>

        {/* Undo / Redo */}
        <button onClick={handleUndo} title="Rückgängig (Ctrl+Z)" style={btn({ background: 'transparent', color: 'rgba(255,255,255,0.55)', border: '1px solid rgba(255,255,255,0.1)', fontSize: 15 })}>↩</button>
        <button onClick={handleRedo} title="Wiederholen (Ctrl+Y)" style={btn({ background: 'transparent', color: 'rgba(255,255,255,0.55)', border: '1px solid rgba(255,255,255,0.1)', fontSize: 15 })}>↪</button>

        {/* Device switcher (center) */}
        <div style={{ flex: 1, display: 'flex', justifyContent: 'center', gap: 2 }}>
          <button onClick={() => switchDevice('Desktop')} style={devBtn('desktop')}>🖥 Desktop</button>
          <button onClick={() => switchDevice('Tablet')}  style={devBtn('tablet')}>📱 Tablet</button>
          <button onClick={() => switchDevice('Mobile')}  style={devBtn('mobile')}>📲 Mobil</button>
        </div>

        {/* Code / Preview / Save */}
        <button onClick={openCodeView} title="HTML-Code anzeigen" style={btn({ background: 'transparent', color: 'rgba(255,255,255,0.55)', border: '1px solid rgba(255,255,255,0.1)' })}>{'</>'}</button>
        <button onClick={openPreview} style={btn({ background: 'transparent', color: 'rgba(255,255,255,0.65)', border: '1px solid rgba(255,255,255,0.15)' })}>
          👁 Vorschau
        </button>
        <button
          onClick={handleSave}
          disabled={saving}
          style={btn({ background: saveOk ? '#16a34a' : '#008EAA', color: '#fff', opacity: saving ? 0.7 : 1, minWidth: 110 })}
        >
          {saving ? '⏳ Speichert…' : saveOk ? '✓ Gespeichert' : '💾 Speichern'}
        </button>
      </div>

      {/* ── Main editor area ─────────────────────────────────────────────────── */}
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>

        {/* ── Left panel ───────────────────────────────────────────────────── */}
        <div style={{
          width: 220, background: '#131e21', borderRight: '1px solid #1e3840',
          display: 'flex', flexDirection: 'column', flexShrink: 0,
        }}>
          {/* Tab strip */}
          <div style={{ display: 'flex', borderBottom: '1px solid #1e3840', flexShrink: 0 }}>
            <button onClick={() => setLeftTab('blocks')} style={tabBtn(leftTab === 'blocks')}>🧩 Blöcke</button>
            <button onClick={() => setLeftTab('layers')} style={tabBtn(leftTab === 'layers')}>🗂 Ebenen</button>
          </div>
          {/* Blocks panel */}
          <div
            id="gjs-blocks-panel"
            style={{
              flex: 1, overflowY: 'auto',
              display: leftTab === 'blocks' ? 'block' : 'none',
            }}
          />
          {/* Layers panel */}
          <div
            id="gjs-layers-panel"
            style={{
              flex: 1, overflowY: 'auto',
              display: leftTab === 'layers' ? 'block' : 'none',
            }}
          />
        </div>

        {/* ── Canvas ───────────────────────────────────────────────────────── */}
        <div style={{ flex: 1, overflow: 'hidden', position: 'relative' }}>
          {!ready && (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#555', fontSize: 14 }}>
              Editor wird geladen…
            </div>
          )}
          <div
            ref={containerRef}
            style={{ width: '100%', height: '100%', display: ready ? 'block' : 'none' }}
          />
        </div>

        {/* ── Right panel ──────────────────────────────────────────────────── */}
        <div style={{
          width: 260, background: '#131e21', borderLeft: '1px solid #1e3840',
          display: 'flex', flexDirection: 'column', flexShrink: 0,
        }}>
          {/* Tab strip */}
          <div style={{ display: 'flex', borderBottom: '1px solid #1e3840', flexShrink: 0 }}>
            <button onClick={() => setRightTab('styles')} style={tabBtn(rightTab === 'styles')}>🎨 Stil</button>
            <button onClick={() => setRightTab('traits')} style={tabBtn(rightTab === 'traits')}>⚙️ Props</button>
          </div>
          {/* Style manager */}
          <div
            id="gjs-styles-panel"
            style={{
              flex: 1, overflowY: 'auto',
              display: rightTab === 'styles' ? 'block' : 'none',
            }}
          />
          {/* Trait manager */}
          <div
            id="gjs-traits-panel"
            style={{
              flex: 1, overflowY: 'auto', padding: '8px 0',
              display: rightTab === 'traits' ? 'block' : 'none',
            }}
          />
        </div>
      </div>
    </div>
  );
}

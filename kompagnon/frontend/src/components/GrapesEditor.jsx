import { useEffect, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import API_BASE_URL from '../config';
import toast from 'react-hot-toast';

export default function GrapesEditor({ pageId, pageName, initialHtml, onClose, onSave }) {
  const editorRef = useRef(null);
  const containerRef = useRef(null);
  const { token } = useAuth();
  const headers = { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` };

  useEffect(() => {
    if (editorRef.current || !containerRef.current) return;

    const loadEditor = async () => {
      const [
        { default: grapesjs },
        { default: gjsPresetWebpage },
        { default: gjsBlocksBasic },
      ] = await Promise.all([
        import('grapesjs'),
        import('grapesjs-preset-webpage'),
        import('grapesjs-blocks-basic'),
      ]);

      await import('grapesjs/dist/css/grapes.min.css');
      await import('grapesjs-preset-webpage/dist/grapesjs-preset-webpage.min.css');

      const editor = grapesjs.init({
        container: containerRef.current,
        height: '100%',
        width: '100%',
        storageManager: false,
        plugins: [gjsPresetWebpage, gjsBlocksBasic],
        pluginsOpts: {
          [gjsPresetWebpage]: {
            blocks: ['link-block', 'quote', 'text-basic'],
          },
          [gjsBlocksBasic]: {
            blocks: ['column1', 'column2', 'column3', 'column3-7',
                     'text', 'link', 'image', 'video', 'map'],
            flexGrid: true,
          },
        },
        deviceManager: {
          devices: [
            { id: 'desktop', name: 'Desktop', width: '' },
            { id: 'tablet',  name: 'Tablet',  width: '768px', widthMedia: '992px' },
            { id: 'mobile',  name: 'Mobil',   width: '375px', widthMedia: '575px' },
          ],
        },
        styleManager: {
          sectors: [
            {
              name: 'Dimension', open: false,
              properties: ['width', 'height', 'max-width', 'min-height', 'margin', 'padding'],
            },
            {
              name: 'Typography', open: false,
              properties: ['font-family', 'font-size', 'font-weight', 'line-height',
                           'color', 'text-align', 'text-decoration'],
            },
            {
              name: 'Decorations', open: false,
              properties: ['background-color', 'border-radius', 'border',
                           'box-shadow', 'opacity'],
            },
            {
              name: 'Flexbox', open: false,
              properties: ['display', 'flex-direction', 'justify-content',
                           'align-items', 'flex-wrap', 'gap'],
            },
          ],
        },
        canvas: {
          styles: [
            'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap',
          ],
        },
      });

      // Gespeicherte Daten laden
      try {
        const res = await fetch(`${API_BASE_URL}/api/pages/${pageId}/editor`, { headers });
        if (res.ok) {
          const data = await res.json();
          if (data.html) {
            editor.setComponents(data.html);
            if (data.css) editor.setStyle(data.css);
          } else if (initialHtml) {
            editor.setComponents(initialHtml);
          }
        } else if (initialHtml) {
          editor.setComponents(initialHtml);
        }
      } catch {
        if (initialHtml) editor.setComponents(initialHtml);
      }

      editorRef.current = editor;
    };

    loadEditor();

    return () => {
      if (editorRef.current) {
        editorRef.current.destroy();
        editorRef.current = null;
      }
    };
  }, [pageId]); // eslint-disable-line

  const save = async () => {
    if (!editorRef.current) return;
    const html = editorRef.current.getHtml();
    const css  = editorRef.current.getCss();
    try {
      await fetch(`${API_BASE_URL}/api/pages/${pageId}/editor`, {
        method: 'POST', headers,
        body: JSON.stringify({ html, css, gjsData: editorRef.current.getProjectData() }),
      });
      toast.success('Gespeichert!');
      if (onSave) onSave({ html, css });
    } catch {
      toast.error('Fehler beim Speichern');
    }
  };

  const preview = () => {
    if (!editorRef.current) return;
    const html = editorRef.current.getHtml();
    const css  = editorRef.current.getCss();
    const w = window.open('', '_blank');
    w.document.write(`<!DOCTYPE html><html><head><style>${css}</style></head><body>${html}</body></html>`);
    w.document.close();
  };

  return (
    <div style={{ position: 'fixed', inset: 0, zIndex: 9000, display: 'flex', flexDirection: 'column', background: '#f0f0f0' }}>
      {/* Toolbar */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 16px', background: '#1a2332', color: '#fff', flexShrink: 0, gap: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <button onClick={onClose} style={{ background: 'none', border: '1px solid rgba(255,255,255,0.3)', color: '#fff', padding: '5px 12px', borderRadius: 6, cursor: 'pointer', fontSize: 13 }}>
            ← Zurück
          </button>
          <span style={{ fontSize: 14, fontWeight: 600 }}>{pageName}</span>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button onClick={preview} style={{ background: 'none', border: '1px solid rgba(255,255,255,0.3)', color: '#fff', padding: '6px 14px', borderRadius: 6, cursor: 'pointer', fontSize: 13 }}>
            👁 Vorschau
          </button>
          <button onClick={save} style={{ background: '#0d6efd', border: 'none', color: '#fff', padding: '6px 16px', borderRadius: 6, cursor: 'pointer', fontSize: 13, fontWeight: 600 }}>
            💾 Speichern
          </button>
        </div>
      </div>
      {/* Editor Canvas */}
      <div ref={containerRef} style={{ flex: 1, overflow: 'hidden' }} />
    </div>
  );
}

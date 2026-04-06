import React, { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import grapesjs from 'grapesjs';
import grapesjsPresetWebpage from 'grapesjs-preset-webpage';
import grapesjsBlocksBasic from 'grapesjs-blocks-basic';
import 'grapesjs/dist/css/grapes.min.css';
import toast from 'react-hot-toast';
import API_BASE_URL from '../config';
import { useAuth } from '../context/AuthContext';
import { allTemplates } from '../data/allTemplates';

/* ─── Inline GrapesJS editor for local templates ─── */
function LocalTemplateEditor({ template, onClose }) {
  const containerRef = useRef(null);
  const editorRef = useRef(null);
  const TOOLBAR_H = 56;

  useEffect(() => {
    if (!containerRef.current) return;
    const editor = grapesjs.init({
      container: containerRef.current,
      height: `calc(100vh - ${TOOLBAR_H}px)`,
      width: '100%',
      plugins: [grapesjsPresetWebpage, grapesjsBlocksBasic],
      pluginsOpts: { [grapesjsPresetWebpage]: {}, [grapesjsBlocksBasic]: {} },
      storageManager: false,
      components: template.html || '',
      style: '',
    });
    editorRef.current = editor;
    return () => { editor.destroy(); editorRef.current = null; };
  }, [template.id]); // eslint-disable-line

  const handlePreview = () => {
    const editor = editorRef.current;
    if (!editor) return;
    const html = `<!DOCTYPE html><html lang="de"><head><meta charset="UTF-8"><style>${editor.getCss()}</style></head><body>${editor.getHtml()}</body></html>`;
    const blob = new Blob([html], { type: 'text/html' });
    window.open(URL.createObjectURL(blob), '_blank');
  };

  const handleDownload = () => {
    const editor = editorRef.current;
    if (!editor) return;
    const html = `<!DOCTYPE html><html lang="de"><head><meta charset="UTF-8"><style>${editor.getCss()}</style></head><body>${editor.getHtml()}</body></html>`;
    const blob = new Blob([html], { type: 'text/html' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `${template.id || 'template'}.html`;
    a.click();
  };

  const btnStyle = {
    padding: '8px 16px', border: 'none', borderRadius: 6,
    fontSize: 13, fontWeight: 600, cursor: 'pointer',
  };

  return (
    <div style={{ position: 'fixed', inset: 0, zIndex: 9999, background: '#fff', display: 'flex', flexDirection: 'column' }}>
      <div style={{ height: TOOLBAR_H, flexShrink: 0, background: '#1A2C32', display: 'flex', alignItems: 'center', gap: 10, padding: '0 16px', boxShadow: '0 2px 8px rgba(0,0,0,0.25)' }}>
        <button onClick={onClose} style={{ ...btnStyle, background: 'rgba(255,255,255,0.15)', color: '#fff' }}>
          ← Zurück
        </button>
        <span style={{ fontSize: 14, fontWeight: 700, color: '#fff', maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {template.thumbnail} {template.name}
        </span>
        <span style={{ fontSize: 11, background: 'rgba(255,255,255,0.12)', color: '#ccc', padding: '3px 10px', borderRadius: 12 }}>
          {template.category}
        </span>
        <div style={{ flex: 1 }} />
        <button onClick={handlePreview} style={{ ...btnStyle, background: 'rgba(255,255,255,0.15)', color: '#fff' }}>
          👁 Vorschau
        </button>
        <button onClick={handleDownload} style={{ ...btnStyle, background: '#16a34a', color: '#fff' }}>
          📥 HTML herunterladen
        </button>
      </div>
      <div ref={containerRef} style={{ flex: 1, overflow: 'hidden' }} />
    </div>
  );
}

/* ─── Main TemplateLibrary page ─── */
export default function TemplateLibrary() {
  const { token } = useAuth();
  const headers = token ? { Authorization: `Bearer ${token}` } : {};
  const [apiTemplates, setApiTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showZipModal, setShowZipModal] = useState(false);
  const [showUrlModal, setShowUrlModal] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [zipForm, setZipForm] = useState({ name: '', description: '' });
  const [urlForm, setUrlForm] = useState({ name: '', url: '', description: '' });
  const [activeTab, setActiveTab] = useState('local'); // 'local' | 'api'
  const [activeCategory, setActiveCategory] = useState('Alle');
  const [editingTemplate, setEditingTemplate] = useState(null);
  const fileRef = useRef(null);

  const load = async () => {
    setLoading(true);
    try {
      const r = await fetch(`${API_BASE_URL}/api/templates/`, { headers });
      setApiTemplates(r.ok ? await r.json() : []);
    } catch { setApiTemplates([]); }
    setLoading(false);
  };

  useEffect(() => { load(); }, []); // eslint-disable-line

  const handleZipUpload = async () => {
    const file = fileRef.current?.files?.[0];
    if (!zipForm.name || !file) return toast.error('Name und ZIP-Datei sind Pflicht');
    setUploading(true);
    try {
      const fd = new FormData();
      fd.append('file', file);
      fd.append('name', zipForm.name);
      fd.append('description', zipForm.description);
      const r = await fetch(`${API_BASE_URL}/api/templates/upload`, { method: 'POST', headers, body: fd });
      if (!r.ok) throw new Error((await r.json()).detail || 'Fehler');
      toast.success('Template hochgeladen');
      setShowZipModal(false);
      setZipForm({ name: '', description: '' });
      load();
    } catch (e) { toast.error(e.message); }
    setUploading(false);
  };

  const handleUrlImport = async () => {
    if (!urlForm.name || !urlForm.url) return toast.error('Name und URL sind Pflicht');
    setUploading(true);
    try {
      const r = await fetch(`${API_BASE_URL}/api/templates/import-url`, {
        method: 'POST',
        headers: { ...headers, 'Content-Type': 'application/json' },
        body: JSON.stringify(urlForm),
      });
      if (!r.ok) throw new Error((await r.json()).detail || 'Fehler');
      toast.success('Template importiert');
      setShowUrlModal(false);
      setUrlForm({ name: '', url: '', description: '' });
      load();
    } catch (e) { toast.error(e.message); }
    setUploading(false);
  };

  const handleDelete = async (id, name) => {
    if (!window.confirm(`Template "${name}" wirklich löschen?`)) return;
    try {
      await fetch(`${API_BASE_URL}/api/templates/${id}`, { method: 'DELETE', headers });
      toast.success('Gelöscht');
      load();
    } catch { toast.error('Fehler beim Löschen'); }
  };

  // Local templates filtered by category
  const localCategories = ['Alle', ...Array.from(new Set(allTemplates.map(t => t.category).filter(Boolean)))];
  const visibleLocal = activeCategory === 'Alle'
    ? allTemplates
    : allTemplates.filter(t => t.category === activeCategory);

  const thumbColors = ['#cfe2ff','#d1e7dd','#fff3cd','#f8d7da','#e2d9f3','#d3e9f7','#fde8d0','#d5f5e3'];

  const inp = { padding: '10px 14px', border: '1px solid #ddd', borderRadius: 6, fontSize: 14, width: '100%', boxSizing: 'border-box' };
  const overlay = { position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', zIndex: 9999, display: 'flex', alignItems: 'center', justifyContent: 'center' };
  const modal = { background: '#fff', borderRadius: 12, padding: 28, width: '100%', maxWidth: 480, display: 'flex', flexDirection: 'column', gap: 16 };

  if (editingTemplate) {
    return <LocalTemplateEditor template={editingTemplate} onClose={() => setEditingTemplate(null)} />;
  }

  return (
    <div style={{ padding: 24, maxWidth: 1200, margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h1 style={{ fontSize: 24, fontWeight: 700 }}>🗂️ Template-Bibliothek</h1>
        <div style={{ display: 'flex', gap: 10 }}>
          <button onClick={() => setShowZipModal(true)} style={{ padding: '9px 18px', background: '#0d6efd', color: '#fff', border: 'none', borderRadius: 8, fontWeight: 600, cursor: 'pointer' }}>
            📁 ZIP hochladen
          </button>
          <button onClick={() => setShowUrlModal(true)} style={{ padding: '9px 18px', background: '#6c757d', color: '#fff', border: 'none', borderRadius: 8, fontWeight: 600, cursor: 'pointer' }}>
            🌐 URL importieren
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 0, borderBottom: '2px solid #e0e0e0', marginBottom: 24 }}>
        {[
          { key: 'local', label: `Vorlagen (${allTemplates.length})` },
          { key: 'api', label: `Eigene Templates (${apiTemplates.length})` },
        ].map(tab => (
          <button key={tab.key} onClick={() => setActiveTab(tab.key)} style={{
            padding: '10px 22px', border: 'none', background: 'transparent', cursor: 'pointer',
            fontWeight: 600, fontSize: 14,
            color: activeTab === tab.key ? '#0d6efd' : '#666',
            borderBottom: activeTab === tab.key ? '2px solid #0d6efd' : '2px solid transparent',
            marginBottom: -2,
          }}>
            {tab.label}
          </button>
        ))}
      </div>

      {/* LOCAL TEMPLATES TAB */}
      {activeTab === 'local' && (
        <>
          {/* Category filter */}
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 20 }}>
            {localCategories.map(cat => (
              <button key={cat} onClick={() => setActiveCategory(cat)} style={{
                padding: '6px 16px', borderRadius: 20, border: '1px solid #dee2e6', cursor: 'pointer',
                fontSize: 13, fontWeight: 500,
                background: activeCategory === cat ? '#0d6efd' : '#fff',
                color: activeCategory === cat ? '#fff' : '#495057',
                borderColor: activeCategory === cat ? '#0d6efd' : '#dee2e6',
              }}>
                {cat}
              </button>
            ))}
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: 18 }}>
            {visibleLocal.map((tpl, idx) => (
              <div key={tpl.id} style={{ border: '1px solid #e0e0e0', borderRadius: 12, overflow: 'hidden', background: '#fff', boxShadow: '0 1px 4px rgba(0,0,0,0.07)', display: 'flex', flexDirection: 'column' }}>
                {/* Thumbnail */}
                <div style={{
                  height: 130, display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 52,
                  background: `linear-gradient(135deg, ${thumbColors[idx % thumbColors.length]}, #fff)`,
                }}>
                  {tpl.thumbnail || tpl.emoji || '📄'}
                </div>
                <div style={{ padding: '14px 16px', flex: 1, display: 'flex', flexDirection: 'column', gap: 8 }}>
                  <div style={{ fontWeight: 700, fontSize: 15, color: '#1a2332' }}>{tpl.name}</div>
                  <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                    {tpl.category && (
                      <span style={{ display: 'inline-block', background: '#e7f1ff', color: '#0d6efd', borderRadius: 12, padding: '2px 10px', fontSize: 11, fontWeight: 600 }}>
                        {tpl.category}
                      </span>
                    )}
                    {tpl.style && (
                      <span style={{ display: 'inline-block', background: '#f0fdf4', color: '#16a34a', borderRadius: 12, padding: '2px 10px', fontSize: 11, fontWeight: 600 }}>
                        {tpl.style}
                      </span>
                    )}
                  </div>
                  <button
                    onClick={() => setEditingTemplate(tpl)}
                    style={{ marginTop: 'auto', padding: '9px 14px', background: '#1A2C32', color: '#fff', border: 'none', borderRadius: 8, cursor: 'pointer', fontWeight: 700, fontSize: 13 }}
                  >
                    ✏️ Im Editor bearbeiten
                  </button>
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      {/* API TEMPLATES TAB */}
      {activeTab === 'api' && (
        loading ? (
          <div style={{ textAlign: 'center', padding: 60, color: '#888' }}>Lade Templates...</div>
        ) : apiTemplates.length === 0 ? (
          <div style={{ textAlign: 'center', padding: 60, color: '#888' }}>
            <div style={{ fontSize: 48, marginBottom: 12 }}>🗂️</div>
            <div>Noch keine eigenen Templates. Lade ein ZIP hoch oder importiere eine URL.</div>
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 20 }}>
            {apiTemplates.map(tpl => (
              <div key={tpl.id} style={{ border: '1px solid #e0e0e0', borderRadius: 10, padding: 20, background: '#fff' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 10 }}>
                  <div style={{ fontWeight: 700, fontSize: 15 }}>{tpl.name}</div>
                  <span style={{ fontSize: 11, padding: '2px 8px', borderRadius: 10, background: tpl.source === 'url' ? '#e3f2fd' : '#e8f5e9', color: tpl.source === 'url' ? '#1565c0' : '#2e7d32', fontWeight: 600 }}>
                    {tpl.source === 'url' ? '🌐 URL' : '📁 ZIP'}
                  </span>
                </div>
                {tpl.category && <div style={{ fontSize: 12, color: '#888', marginBottom: 6 }}>{tpl.category}</div>}
                {tpl.created_at && <div style={{ fontSize: 11, color: '#aaa', marginBottom: 14 }}>{new Date(tpl.created_at).toLocaleDateString('de-DE')}</div>}
                <div style={{ display: 'flex', gap: 8 }}>
                  <Link to={`/app/settings/templates/${tpl.id}`} style={{ flex: 1, padding: '7px 12px', background: '#f0f0f0', color: '#333', border: 'none', borderRadius: 6, fontWeight: 600, fontSize: 13, textAlign: 'center', textDecoration: 'none', display: 'block' }}>
                    ✏️ Bearbeiten
                  </Link>
                  <button onClick={() => handleDelete(tpl.id, tpl.name)} style={{ padding: '7px 12px', background: '#fee2e2', color: '#b91c1c', border: 'none', borderRadius: 6, fontWeight: 600, fontSize: 13, cursor: 'pointer' }}>
                    🗑️
                  </button>
                </div>
              </div>
            ))}
          </div>
        )
      )}

      {/* ZIP Modal */}
      {showZipModal && (
        <div style={overlay} onClick={e => e.target === e.currentTarget && setShowZipModal(false)}>
          <div style={modal}>
            <div style={{ fontWeight: 700, fontSize: 17 }}>📁 ZIP-Template hochladen</div>
            <input style={inp} placeholder="Template-Name *" value={zipForm.name} onChange={e => setZipForm(f => ({ ...f, name: e.target.value }))} />
            <input style={inp} placeholder="Beschreibung (optional)" value={zipForm.description} onChange={e => setZipForm(f => ({ ...f, description: e.target.value }))} />
            <input ref={fileRef} type="file" accept=".zip" style={inp} />
            <button onClick={handleZipUpload} disabled={uploading} style={{ padding: '11px', background: uploading ? '#ccc' : '#0d6efd', color: '#fff', border: 'none', borderRadius: 8, fontWeight: 700, fontSize: 15, cursor: uploading ? 'not-allowed' : 'pointer' }}>
              {uploading ? 'Wird hochgeladen...' : 'Hochladen'}
            </button>
            <button onClick={() => setShowZipModal(false)} style={{ padding: '9px', background: '#f5f5f5', color: '#555', border: 'none', borderRadius: 8, cursor: 'pointer' }}>Abbrechen</button>
          </div>
        </div>
      )}

      {/* URL Modal */}
      {showUrlModal && (
        <div style={overlay} onClick={e => e.target === e.currentTarget && setShowUrlModal(false)}>
          <div style={modal}>
            <div style={{ fontWeight: 700, fontSize: 17 }}>🌐 Template per URL importieren</div>
            <input style={inp} placeholder="Template-Name *" value={urlForm.name} onChange={e => setUrlForm(f => ({ ...f, name: e.target.value }))} />
            <input style={inp} placeholder="URL (z.B. https://...) *" value={urlForm.url} onChange={e => setUrlForm(f => ({ ...f, url: e.target.value }))} />
            <input style={inp} placeholder="Beschreibung (optional)" value={urlForm.description} onChange={e => setUrlForm(f => ({ ...f, description: e.target.value }))} />
            <div style={{ background: '#fef3c7', border: '1px solid #fbbf24', borderRadius: 8, padding: '10px 14px', fontSize: 13, color: '#92400e' }}>
              ⚠️ Gib die öffentliche Demo-URL des Templates ein. Die KI rekonstruiert das Layout. Stelle sicher dass du eine Lizenz besitzt.
            </div>
            <button onClick={handleUrlImport} disabled={uploading} style={{ padding: '11px', background: uploading ? '#ccc' : '#6f42c1', color: '#fff', border: 'none', borderRadius: 8, fontWeight: 700, fontSize: 15, cursor: uploading ? 'not-allowed' : 'pointer' }}>
              {uploading ? 'KI rekonstruiert (~10 Sek)...' : 'Importieren'}
            </button>
            <button onClick={() => setShowUrlModal(false)} style={{ padding: '9px', background: '#f5f5f5', color: '#555', border: 'none', borderRadius: 8, cursor: 'pointer' }}>Abbrechen</button>
          </div>
        </div>
      )}
    </div>
  );
}

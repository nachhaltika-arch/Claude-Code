import React, { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import toast from 'react-hot-toast';
import API_BASE_URL from '../config';
import { useAuth } from '../context/AuthContext';

export default function TemplateLibrary() {
  const { token } = useAuth();
  const headers = token ? { Authorization: `Bearer ${token}` } : {};
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showZipModal, setShowZipModal] = useState(false);
  const [showUrlModal, setShowUrlModal] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [zipForm, setZipForm] = useState({ name: '', description: '' });
  const [urlForm, setUrlForm] = useState({ name: '', url: '', description: '' });
  const fileRef = useRef(null);

  const load = async () => {
    setLoading(true);
    try {
      const r = await fetch(`${API_BASE_URL}/api/templates/`, { headers });
      setTemplates(r.ok ? await r.json() : []);
    } catch { setTemplates([]); }
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

  const inp = { padding: '10px 14px', border: '1px solid #ddd', borderRadius: 6, fontSize: 14, width: '100%', boxSizing: 'border-box' };
  const overlay = { position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', zIndex: 9999, display: 'flex', alignItems: 'center', justifyContent: 'center' };
  const modal = { background: '#fff', borderRadius: 12, padding: 28, width: '100%', maxWidth: 480, display: 'flex', flexDirection: 'column', gap: 16 };

  return (
    <div style={{ padding: 24, maxWidth: 1100, margin: '0 auto' }}>
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

      {loading ? (
        <div style={{ textAlign: 'center', padding: 60, color: '#888' }}>Lade Templates...</div>
      ) : templates.length === 0 ? (
        <div style={{ textAlign: 'center', padding: 60, color: '#888' }}>
          <div style={{ fontSize: 48, marginBottom: 12 }}>🗂️</div>
          <div>Noch keine Templates. Lade ein ZIP hoch oder importiere eine URL.</div>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 20 }}>
          {templates.map(tpl => (
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
      )}

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

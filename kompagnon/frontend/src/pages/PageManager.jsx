import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useScreenSize } from '../utils/responsive';
import toast from 'react-hot-toast';
import API_BASE_URL from '../config';

const TYPE_LABELS = {
  landing:       { label: 'Landing',     color: '#008eaa', bg: '#e0f4f8' },
  paket:         { label: 'Paket',       color: '#7c3aed', bg: '#ede9fe' },
  auth:          { label: 'Auth',        color: '#1d9e75', bg: '#d1fae5' },
  transaktional: { label: 'Transaktion', color: '#d97706', bg: '#fef3c7' },
  legal:         { label: 'Legal',       color: '#6b7280', bg: '#f3f4f6' },
  portal:        { label: 'Portal',      color: '#b9227d', bg: '#fce7f3' },
  custom:        { label: 'Custom',      color: '#374151', bg: '#e5e7eb' },
};

const STATUS_LABELS = {
  live:  { label: 'Live',    color: '#065f46', bg: '#d1fae5' },
  draft: { label: 'Entwurf', color: '#92400e', bg: '#fef3c7' },
};

const TABS = ['Alle Seiten', 'Templates', 'Produkt-Seiten'];

export default function PageManager() {
  const { token } = useAuth();
  const { isMobile } = useScreenSize();
  const navigate = useNavigate();
  const h = { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` };

  const [activeTab, setActiveTab] = useState(0);
  const [pages, setPages] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showNewPage, setShowNewPage] = useState(false);
  const [showUpload, setShowUpload] = useState(false);
  const [newPage, setNewPage] = useState({ slug: '', name: '', page_type: 'custom', description: '' });
  const [uploadForm, setUploadForm] = useState({ name: '', category: 'allgemein', file: null });
  const [uploading, setUploading] = useState(false);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [pRes, tRes] = await Promise.all([
        fetch(`${API_BASE_URL}/api/pages/`, { headers: h }),
        fetch(`${API_BASE_URL}/api/pages/templates/list`, { headers: h }),
      ]);
      if (pRes.ok) { const d = await pRes.json(); setPages(d.items ?? d); }
      if (tRes.ok) setTemplates(await tRes.json());
    } catch { toast.error('Laden fehlgeschlagen'); }
    setLoading(false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  useEffect(() => { loadData(); }, [loadData]);

  const openEditor = (page) => {
    navigate(`/app/pages/${page.id}/editor`);
  };

  const openTemplateEditor = (tpl) => {
    navigate(`/app/pages/templates/${tpl.id}/editor`);
  };

  const handleCreatePage = async () => {
    if (!newPage.slug || !newPage.name) {
      toast.error('Slug und Name sind Pflichtfelder');
      return;
    }
    try {
      const res = await fetch(`${API_BASE_URL}/api/pages/`, {
        method: 'POST', headers: h, body: JSON.stringify(newPage),
      });
      if (!res.ok) {
        const d = await res.json();
        throw new Error(d.detail || 'Fehler');
      }
      toast.success('Seite angelegt');
      setShowNewPage(false);
      setNewPage({ slug: '', name: '', page_type: 'custom', description: '' });
      loadData();
    } catch (e) { toast.error(e.message); }
  };

  const handleUploadTemplate = async () => {
    if (!uploadForm.name || !uploadForm.file) {
      toast.error('Name und Datei sind Pflichtfelder');
      return;
    }
    setUploading(true);
    try {
      const fd = new FormData();
      fd.append('name', uploadForm.name);
      fd.append('category', uploadForm.category);
      fd.append('file', uploadForm.file);
      const res = await fetch(`${API_BASE_URL}/api/pages/templates/upload`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: fd,
      });
      if (!res.ok) throw new Error('Upload fehlgeschlagen');
      toast.success('Template hochgeladen');
      setShowUpload(false);
      setUploadForm({ name: '', category: 'allgemein', file: null });
      loadData();
    } catch (e) { toast.error(e.message); }
    setUploading(false);
  };

  const handleDeleteTemplate = async (id) => {
    if (!window.confirm('Template löschen?')) return;
    try {
      await fetch(`${API_BASE_URL}/api/pages/templates/${id}`, {
        method: 'DELETE', headers: h,
      });
      toast.success('Template gelöscht');
      loadData();
    } catch { toast.error('Fehler'); }
  };

  const filteredPages = activeTab === 2
    ? pages.filter(p => p.page_type === 'paket' || p.product_id)
    : pages;

  const S = {
    badge: (config) => ({
      display: 'inline-flex', alignItems: 'center',
      padding: '2px 8px', borderRadius: 4,
      fontSize: 11, fontWeight: 700,
      color: config.color, background: config.bg,
    }),
    btn: (primary) => ({
      padding: '8px 16px', borderRadius: 6,
      fontSize: 13, fontWeight: 600,
      border: primary ? 'none' : '1px solid var(--border-light)',
      background: primary ? 'var(--brand-primary)' : 'var(--bg-surface)',
      color: primary ? '#fff' : 'var(--text-primary)',
      cursor: 'pointer', fontFamily: 'inherit',
    }),
    input: {
      width: '100%', padding: '9px 12px',
      border: '1px solid var(--border-light)', borderRadius: 6,
      fontSize: 13, fontFamily: 'inherit',
      background: 'var(--bg-app)', color: 'var(--text-primary)', outline: 'none',
    },
  };

  return (
    <div style={{ padding: isMobile ? '16px' : '24px', maxWidth: 1100, margin: '0 auto' }}>

      {/* Header */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        marginBottom: 20, flexWrap: 'wrap', gap: 10,
      }}>
        <div>
          <h1 style={{ fontSize: 20, fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
            🌐 Seiten-Manager
          </h1>
          <p style={{ fontSize: 13, color: 'var(--text-secondary)', margin: '4px 0 0' }}>
            Öffentliche Seiten verwalten, bearbeiten und veröffentlichen
          </p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button style={S.btn(false)} onClick={() => setShowUpload(true)}>
            ⬆ Template hochladen
          </button>
          <button style={S.btn(true)} onClick={() => setShowNewPage(true)}>
            + Neue Seite
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div style={{
        display: 'flex', borderBottom: '1px solid var(--border-light)',
        marginBottom: 20, gap: 0, overflowX: 'auto',
      }}>
        {TABS.map((tab, i) => (
          <button key={i} onClick={() => setActiveTab(i)} style={{
            padding: '10px 20px', fontSize: 13,
            fontWeight: activeTab === i ? 700 : 500,
            color: activeTab === i ? 'var(--brand-primary)' : 'var(--text-secondary)',
            border: 'none',
            borderBottom: activeTab === i ? '2px solid var(--brand-primary)' : '2px solid transparent',
            background: 'transparent', cursor: 'pointer',
            fontFamily: 'inherit', whiteSpace: 'nowrap',
          }}>
            {tab}
            {i === 0 && ` (${pages.length})`}
            {i === 1 && ` (${templates.length})`}
            {i === 2 && ` (${pages.filter(p => p.page_type === 'paket' || p.product_id).length})`}
          </button>
        ))}
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: 40, color: 'var(--text-tertiary)' }}>Laden…</div>
      ) : (activeTab === 0 || activeTab === 2) ? (
        <div style={{
          background: 'var(--bg-surface)', border: '1px solid var(--border-light)',
          borderRadius: 10, overflow: 'hidden',
        }}>
          {!isMobile && (
            <div style={{
              display: 'grid',
              gridTemplateColumns: '32px 2fr 1fr 100px 100px 140px',
              gap: 12, padding: '10px 16px',
              background: 'var(--bg-app)',
              borderBottom: '1px solid var(--border-light)',
              fontSize: 11, fontWeight: 700,
              color: 'var(--text-tertiary)',
              textTransform: 'uppercase', letterSpacing: '.06em',
            }}>
              <div></div>
              <div>Seite</div>
              <div>Pfad</div>
              <div>Typ</div>
              <div>Status</div>
              <div>Aktionen</div>
            </div>
          )}

          {filteredPages.map(page => {
            const typeConf   = TYPE_LABELS[page.page_type] || TYPE_LABELS.custom;
            const statusConf = STATUS_LABELS[page.status]  || STATUS_LABELS.draft;
            return (
              <div key={page.id} style={{
                display: 'grid',
                gridTemplateColumns: isMobile ? '1fr' : '32px 2fr 1fr 100px 100px 140px',
                gap: isMobile ? 6 : 12,
                padding: '12px 16px',
                borderBottom: '1px solid var(--border-light)',
                alignItems: 'center',
              }}>
                <div style={{ fontSize: 16, textAlign: isMobile ? 'left' : 'center' }}>
                  {page.page_type === 'landing' ? '🏠'
                   : page.page_type === 'paket'  ? '📦'
                   : page.page_type === 'auth'   ? '🔐'
                   : page.page_type === 'legal'  ? '🧾'
                   : page.page_type === 'portal' ? '👤'
                   : '📄'}
                </div>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>
                    {page.name}
                  </div>
                  {page.updated_at && (
                    <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>
                      {new Date(page.updated_at).toLocaleDateString('de-DE')}
                    </div>
                  )}
                </div>
                <div style={{
                  fontSize: 12, fontFamily: 'monospace',
                  color: 'var(--text-secondary)', wordBreak: 'break-all',
                }}>{page.slug}</div>
                <div><span style={S.badge(typeConf)}>{typeConf.label}</span></div>
                <div><span style={S.badge(statusConf)}>{statusConf.label}</span></div>
                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                  <button onClick={() => openEditor(page)} style={{
                    ...S.btn(true), padding: '5px 10px', fontSize: 12,
                  }}>
                    ✏️ Bearbeiten
                  </button>
                  <a href={page.slug} target="_blank" rel="noreferrer" style={{
                    ...S.btn(false), padding: '5px 10px', fontSize: 12,
                    textDecoration: 'none', display: 'inline-flex', alignItems: 'center',
                  }}>
                    👁
                  </a>
                </div>
              </div>
            );
          })}

          {filteredPages.length === 0 && (
            <div style={{ padding: 30, textAlign: 'center', color: 'var(--text-tertiary)', fontSize: 13 }}>
              Keine Seiten gefunden.
            </div>
          )}
        </div>
      ) : (
        /* Tab 1: Templates */
        <div>
          {templates.length === 0 ? (
            <div style={{
              textAlign: 'center', padding: 48,
              background: 'var(--bg-surface)', borderRadius: 10,
              border: '1px dashed var(--border-light)',
            }}>
              <div style={{ fontSize: 32, marginBottom: 12 }}>🖼</div>
              <div style={{ fontSize: 15, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 6 }}>
                Noch keine Templates
              </div>
              <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 16 }}>
                Lade ein ZIP- oder .grapesjs-File hoch um zu starten.
              </p>
              <button style={S.btn(true)} onClick={() => setShowUpload(true)}>
                ⬆ Erstes Template hochladen
              </button>
            </div>
          ) : (
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))',
              gap: 16,
            }}>
              {templates.map(tpl => (
                <div key={tpl.id} style={{
                  background: 'var(--bg-surface)',
                  border: '1px solid var(--border-light)',
                  borderRadius: 10, overflow: 'hidden',
                }}>
                  <div style={{
                    height: 120, background: 'var(--bg-app)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: 32,
                  }}>
                    {tpl.thumbnail_url
                      ? <img src={tpl.thumbnail_url} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover' }}/>
                      : '🖼'}
                  </div>
                  <div style={{ padding: '12px 14px' }}>
                    <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 4 }}>
                      {tpl.name}
                    </div>
                    <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginBottom: 10 }}>
                      {tpl.category}
                      {tpl.is_builtin && (
                        <span style={{ marginLeft: 6, ...S.badge({ color: '#374151', bg: '#e5e7eb' }) }}>
                          Built-in
                        </span>
                      )}
                    </div>
                    <div style={{ display: 'flex', gap: 6 }}>
                      <button
                        onClick={() => openTemplateEditor(tpl)}
                        disabled={tpl.is_builtin}
                        title={tpl.is_builtin ? 'Eingebaute Templates sind schreibgeschützt' : 'Template im GrapesJS-Editor bearbeiten'}
                        style={{
                          ...S.btn(true),
                          padding: '5px 10px', fontSize: 11, flex: 1,
                          opacity: tpl.is_builtin ? 0.5 : 1,
                          cursor: tpl.is_builtin ? 'not-allowed' : 'pointer',
                        }}>
                        ✏️ Bearbeiten
                      </button>
                      {!tpl.is_builtin && (
                        <button
                          onClick={() => handleDeleteTemplate(tpl.id)}
                          style={{ ...S.btn(false), padding: '5px 10px', fontSize: 11 }}>
                          🗑
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Modal: Neue Seite */}
      {showNewPage && (
        <div onClick={() => setShowNewPage(false)} style={{
          position: 'fixed', inset: 0, background: 'rgba(0,0,0,.5)',
          zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 16,
        }}>
          <div onClick={e => e.stopPropagation()} style={{
            background: 'var(--bg-surface)', borderRadius: 12, padding: 24,
            width: '100%', maxWidth: 480,
          }}>
            <h3 style={{ fontSize: 16, fontWeight: 700, marginBottom: 16, color: 'var(--text-primary)' }}>
              Neue Seite anlegen
            </h3>
            {[
              ['name', 'Name (intern)', 'Paket: Mein Produkt'],
              ['slug', 'URL-Pfad (slug)', '/paket/mein-produkt'],
              ['description', 'Beschreibung (optional)', ''],
            ].map(([key, label, ph]) => (
              <div key={key} style={{ marginBottom: 12 }}>
                <label style={{
                  display: 'block', fontSize: 11, fontWeight: 600,
                  textTransform: 'uppercase', letterSpacing: '.06em',
                  color: 'var(--text-secondary)', marginBottom: 4,
                }}>
                  {label}
                </label>
                <input
                  type="text" placeholder={ph}
                  value={newPage[key]}
                  onChange={e => setNewPage(p => ({ ...p, [key]: e.target.value }))}
                  style={S.input}
                />
              </div>
            ))}
            <div style={{ marginBottom: 20 }}>
              <label style={{
                display: 'block', fontSize: 11, fontWeight: 600,
                textTransform: 'uppercase', letterSpacing: '.06em',
                color: 'var(--text-secondary)', marginBottom: 4,
              }}>
                Typ
              </label>
              <select
                value={newPage.page_type}
                onChange={e => setNewPage(p => ({ ...p, page_type: e.target.value }))}
                style={{ ...S.input, cursor: 'pointer' }}>
                {Object.entries(TYPE_LABELS).map(([v, c]) => (
                  <option key={v} value={v}>{c.label}</option>
                ))}
              </select>
            </div>
            <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
              <button style={S.btn(false)} onClick={() => setShowNewPage(false)}>Abbrechen</button>
              <button style={S.btn(true)} onClick={handleCreatePage}>Anlegen →</button>
            </div>
          </div>
        </div>
      )}

      {/* Modal: Template Upload */}
      {showUpload && (
        <div onClick={() => setShowUpload(false)} style={{
          position: 'fixed', inset: 0, background: 'rgba(0,0,0,.5)',
          zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 16,
        }}>
          <div onClick={e => e.stopPropagation()} style={{
            background: 'var(--bg-surface)', borderRadius: 12, padding: 24,
            width: '100%', maxWidth: 440,
          }}>
            <h3 style={{ fontSize: 16, fontWeight: 700, marginBottom: 16, color: 'var(--text-primary)' }}>
              Template hochladen
            </h3>
            <div style={{ marginBottom: 12 }}>
              <label style={{
                display: 'block', fontSize: 11, fontWeight: 600,
                textTransform: 'uppercase', letterSpacing: '.06em',
                color: 'var(--text-secondary)', marginBottom: 4,
              }}>Name</label>
              <input placeholder="Mein Template" value={uploadForm.name}
                onChange={e => setUploadForm(f => ({ ...f, name: e.target.value }))}
                style={S.input}/>
            </div>
            <div style={{ marginBottom: 12 }}>
              <label style={{
                display: 'block', fontSize: 11, fontWeight: 600,
                textTransform: 'uppercase', letterSpacing: '.06em',
                color: 'var(--text-secondary)', marginBottom: 4,
              }}>Kategorie</label>
              <select value={uploadForm.category}
                onChange={e => setUploadForm(f => ({ ...f, category: e.target.value }))}
                style={{ ...S.input, cursor: 'pointer' }}>
                {['allgemein', 'landing', 'paket', 'auth', 'kampagne'].map(c => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>
            <div style={{ marginBottom: 20 }}>
              <label style={{
                display: 'block', fontSize: 11, fontWeight: 600,
                textTransform: 'uppercase', letterSpacing: '.06em',
                color: 'var(--text-secondary)', marginBottom: 4,
              }}>
                Datei (.zip oder .grapesjs)
              </label>
              <input type="file" accept=".zip,.grapesjs"
                onChange={e => setUploadForm(f => ({ ...f, file: e.target.files?.[0] || null }))}
                style={{ ...S.input, padding: '6px 12px', cursor: 'pointer' }}/>
            </div>
            <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
              <button style={S.btn(false)} onClick={() => setShowUpload(false)}>Abbrechen</button>
              <button style={S.btn(true)} onClick={handleUploadTemplate} disabled={uploading}>
                {uploading ? 'Wird hochgeladen…' : '⬆ Hochladen'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

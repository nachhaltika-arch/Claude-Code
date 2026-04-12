import React, { useState, useEffect, useCallback } from 'react';
import toast from 'react-hot-toast';
import { useAuth } from '../context/AuthContext';
import API_BASE_URL from '../config';
import GrapesEditor from '../components/GrapesEditor';

export default function KasWebsite() {
  const { token, user, isSuperadmin } = useAuth();
  const superadmin = typeof isSuperadmin === 'function' ? isSuperadmin() : user?.role === 'superadmin';
  const headers = {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${token}`,
  };

  const [pages, setPages]             = useState([]);
  const [site, setSite]               = useState(null);
  const [loading, setLoading]         = useState(true);
  const [deploying, setDeploying]     = useState(false);
  const [deployResult, setDeployResult] = useState(null);
  const [editingPage, setEditingPage] = useState(null);
  const [showNewForm, setShowNewForm] = useState(false);
  const [newPage, setNewPage]         = useState({ titel: '', pfad: '/', meta_description: '' });
  const [creatingSite, setCreatingSite] = useState(false);

  // ── Load data ────────────────────────────────────────────────────────────
  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [pagesRes, siteRes] = await Promise.all([
        fetch(`${API_BASE_URL}/api/kas/pages`, { headers }),
        fetch(`${API_BASE_URL}/api/kas/site`, { headers }),
      ]);
      if (pagesRes.ok) setPages(await pagesRes.json());
      if (siteRes.ok)  setSite(await siteRes.json());
    } catch {
      toast.error('Fehler beim Laden der KAS-Seiten');
    } finally {
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => { load(); }, []); // eslint-disable-line

  // ── Actions ──────────────────────────────────────────────────────────────
  const createSite = async () => {
    if (!superadmin) return;
    setCreatingSite(true);
    try {
      const r = await fetch(`${API_BASE_URL}/api/kas/site`, { method: 'POST', headers });
      if (!r.ok) {
        const err = await r.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${r.status}`);
      }
      const d = await r.json();
      toast.success('Netlify-Site angelegt');
      await load();
    } catch (e) {
      toast.error('Fehler: ' + e.message);
    } finally {
      setCreatingSite(false);
    }
  };

  const addPage = async () => {
    if (!newPage.titel.trim() || !newPage.pfad.trim()) {
      toast.error('Titel und Pfad sind Pflichtfelder');
      return;
    }
    try {
      const r = await fetch(`${API_BASE_URL}/api/kas/pages`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          titel: newPage.titel.trim(),
          pfad: newPage.pfad.trim(),
          meta_description: newPage.meta_description.trim(),
        }),
      });
      if (!r.ok) {
        const err = await r.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${r.status}`);
      }
      toast.success('Seite angelegt');
      setShowNewForm(false);
      setNewPage({ titel: '', pfad: '/', meta_description: '' });
      load();
    } catch (e) {
      toast.error('Fehler: ' + e.message);
    }
  };

  const deletePage = async (page) => {
    if (page.ist_startseite) {
      toast.error('Startseite kann nicht gelöscht werden');
      return;
    }
    if (!window.confirm(`"${page.titel}" wirklich löschen?`)) return;
    try {
      const r = await fetch(`${API_BASE_URL}/api/kas/pages/${page.id}`, {
        method: 'DELETE', headers,
      });
      if (!r.ok) {
        const err = await r.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${r.status}`);
      }
      toast.success('Seite gelöscht');
      load();
    } catch (e) {
      toast.error('Fehler: ' + e.message);
    }
  };

  const deploy = async () => {
    if (!superadmin) return;
    setDeploying(true);
    setDeployResult(null);
    try {
      const r = await fetch(`${API_BASE_URL}/api/kas/deploy`, { method: 'POST', headers });
      if (!r.ok) {
        const err = await r.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${r.status}`);
      }
      const d = await r.json();
      setDeployResult(d);
      toast.success(`${d.pages_deployed.length} Seiten deployed`);
      await load();
    } catch (e) {
      toast.error('Deploy fehlgeschlagen: ' + e.message);
    } finally {
      setDeploying(false);
    }
  };

  // ── GrapesEditor offen — Vollbild ────────────────────────────────────────
  if (editingPage) {
    return (
      <GrapesEditor
        pageId={editingPage.id}
        pageName={editingPage.titel}
        initialHtml=""
        endpointBase="/api/kas/pages"
        onClose={() => { setEditingPage(null); load(); }}
        onSave={() => {}}
      />
    );
  }

  // ── Styles ───────────────────────────────────────────────────────────────
  const card = {
    background: 'var(--bg-surface)',
    border: '1px solid var(--border-light)',
    borderRadius: 'var(--radius-lg)',
    padding: 20,
    marginBottom: 20,
  };
  const inp = {
    width: '100%', boxSizing: 'border-box',
    padding: '9px 12px',
    border: '1px solid var(--border-light)',
    borderRadius: 'var(--radius-md)',
    background: 'var(--bg-app)',
    color: 'var(--text-primary)',
    fontSize: 13,
    fontFamily: 'var(--font-sans)',
    outline: 'none',
  };
  const btn = (color = 'var(--brand-primary)') => ({
    padding: '8px 16px', borderRadius: 'var(--radius-md)', border: 'none',
    background: color, color: '#fff', fontSize: 13, fontWeight: 600,
    cursor: 'pointer', fontFamily: 'var(--font-sans)',
  });

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: 24 }}>
        <div style={{ fontSize: 20, fontWeight: 800, color: 'var(--text-primary)' }}>
          KAS Website
        </div>
        <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 4 }}>
          KOMPAGNON-eigene Seiten — getrennt von Kundenprojekten
        </div>
      </div>

      {/* ── Bereich 1: Netlify-Site ─────────────────────────────────────── */}
      <div style={card}>
        <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 12 }}>
          🌐 Netlify-Site
        </div>
        {site?.configured ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            <span style={{
              background: '#dcfce7', color: '#16a34a',
              padding: '3px 12px', borderRadius: 20,
              fontSize: 12, fontWeight: 700, width: 'fit-content',
            }}>
              ✓ Site aktiv
            </span>
            {site.site_url && (
              <a href={site.site_url} target="_blank" rel="noopener noreferrer"
                 style={{ fontSize: 13, color: 'var(--brand-primary)', textDecoration: 'none' }}>
                {site.site_url} →
              </a>
            )}
            {site.last_deploy && (
              <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>
                Letzter Deploy: {String(site.last_deploy).slice(0, 16).replace('T', ' ')}
              </div>
            )}
          </div>
        ) : (
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
            <span style={{ fontSize: 13, color: 'var(--text-tertiary)' }}>
              Noch keine KAS-Netlify-Site angelegt
            </span>
            <button
              onClick={createSite}
              disabled={!superadmin || creatingSite}
              title={!superadmin ? 'Nur Superadmin kann die Site anlegen' : ''}
              style={{
                ...btn(),
                opacity: superadmin && !creatingSite ? 1 : 0.4,
                cursor: superadmin && !creatingSite ? 'pointer' : 'not-allowed',
              }}
            >
              {creatingSite ? 'Lädt…' : '+ Site anlegen'}
            </button>
          </div>
        )}
      </div>

      {/* ── Bereich 2: Seiten-Tabelle ───────────────────────────────────── */}
      <div style={card}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' }}>
            📄 Seiten
          </div>
          <button onClick={() => setShowNewForm(v => !v)} style={btn('#475569')}>
            {showNewForm ? '✕ Abbrechen' : '+ Seite hinzufügen'}
          </button>
        </div>

        {showNewForm && (
          <div style={{
            background: 'var(--bg-app)', borderRadius: 'var(--radius-md)',
            padding: 16, marginBottom: 16, display: 'flex', flexDirection: 'column', gap: 10,
            border: '1px solid var(--border-light)',
          }}>
            <input style={inp} placeholder="Titel *" value={newPage.titel}
              onChange={e => setNewPage(p => ({ ...p, titel: e.target.value }))} autoFocus />
            <input style={inp} placeholder="Pfad (z.B. /leistungen) *" value={newPage.pfad}
              onChange={e => setNewPage(p => ({ ...p, pfad: e.target.value }))} />
            <input style={inp} placeholder="Meta-Description" value={newPage.meta_description}
              onChange={e => setNewPage(p => ({ ...p, meta_description: e.target.value }))} />
            <button onClick={addPage} style={btn()}>Seite anlegen</button>
          </div>
        )}

        {loading ? (
          <div style={{ color: 'var(--text-tertiary)', fontSize: 13, textAlign: 'center', padding: 20 }}>
            Lädt…
          </div>
        ) : pages.length === 0 ? (
          <div style={{ color: 'var(--text-tertiary)', fontSize: 13, textAlign: 'center', padding: 24 }}>
            Noch keine Seiten angelegt
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-light)' }}>
                  {['Titel', 'Pfad', 'Status', 'Inhalt', 'Aktionen'].map(h => (
                    <th key={h} style={{
                      textAlign: 'left', padding: '8px 12px',
                      fontSize: 10, fontWeight: 700, color: 'var(--text-tertiary)',
                      textTransform: 'uppercase', letterSpacing: '.06em',
                    }}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {pages.map(page => (
                  <tr key={page.id} style={{ borderBottom: '1px solid var(--border-light)' }}>
                    <td style={{ padding: '10px 12px', fontWeight: 600, color: 'var(--text-primary)' }}>
                      {page.ist_startseite && <span style={{ marginRight: 6 }}>🏠</span>}
                      {page.titel}
                    </td>
                    <td style={{ padding: '10px 12px', color: 'var(--text-secondary)', fontFamily: 'monospace', fontSize: 12 }}>
                      {page.pfad}
                    </td>
                    <td style={{ padding: '10px 12px' }}>
                      <span style={{
                        padding: '2px 8px', borderRadius: 4, fontSize: 11, fontWeight: 600,
                        background: page.status === 'live' ? '#dcfce7' : 'var(--bg-elevated)',
                        color:      page.status === 'live' ? '#16a34a' : 'var(--text-tertiary)',
                      }}>
                        {page.status === 'live' ? 'Live' : 'Entwurf'}
                      </span>
                    </td>
                    <td style={{ padding: '10px 12px' }}>
                      <span style={{
                        padding: '2px 8px', borderRadius: 4, fontSize: 11, fontWeight: 600,
                        background: page.has_content ? '#E6F1FB' : '#FEF9C3',
                        color:      page.has_content ? '#185FA5' : '#854D0E',
                      }}>
                        {page.has_content ? '✓ Gespeichert' : '! Leer'}
                      </span>
                    </td>
                    <td style={{ padding: '10px 12px' }}>
                      <div style={{ display: 'flex', gap: 6 }}>
                        <button onClick={() => setEditingPage(page)}
                          style={{ ...btn('var(--brand-primary)'), padding: '5px 12px', fontSize: 11 }}>
                          ✏️ Bearbeiten
                        </button>
                        {!page.ist_startseite && (
                          <button onClick={() => deletePage(page)}
                            style={{ ...btn('#dc2626'), padding: '5px 10px', fontSize: 11 }}>
                            🗑
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* ── Bereich 3: Deploy ─────────────────────────────────────────────── */}
      <div style={card}>
        <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 12 }}>
          🚀 Live deployen
        </div>
        <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 16, lineHeight: 1.6 }}>
          Deployt alle gespeicherten KAS-Seiten auf die Netlify-Site.
          {!superadmin && (
            <span style={{ color: '#dc2626', marginLeft: 6, fontWeight: 600 }}>
              Nur Superadmin kann live deployen.
            </span>
          )}
          {!site?.configured && (
            <span style={{ color: '#854D0E', marginLeft: 6, fontWeight: 600 }}>
              Zuerst Netlify-Site anlegen.
            </span>
          )}
        </div>
        <button
          onClick={deploy}
          disabled={!superadmin || deploying || !site?.configured}
          title={
            !superadmin ? 'Nur Superadmin darf deployen'
            : !site?.configured ? 'Zuerst Netlify-Site anlegen'
            : ''
          }
          style={{
            ...btn(deploying ? '#94a3b8' : '#16a34a'),
            opacity: (!superadmin || !site?.configured) ? 0.4 : 1,
            cursor: (!superadmin || !site?.configured || deploying) ? 'not-allowed' : 'pointer',
            padding: '10px 24px',
            fontSize: 14,
          }}
        >
          {deploying ? '⏳ Deploy läuft…' : '🚀 Alle Seiten deployen'}
        </button>

        {deployResult && (
          <div style={{
            marginTop: 16, padding: 14,
            background: '#dcfce7', borderRadius: 'var(--radius-md)',
            border: '1px solid #bbf7d0',
          }}>
            <div style={{ fontWeight: 700, color: '#16a34a', marginBottom: 8, fontSize: 13 }}>
              ✓ {deployResult.pages_deployed.length} Seiten deployed
            </div>
            {deployResult.deploy_url && (
              <a href={deployResult.deploy_url} target="_blank" rel="noopener noreferrer"
                 style={{ fontSize: 13, color: '#16a34a', fontWeight: 600, textDecoration: 'none' }}>
                {deployResult.deploy_url} →
              </a>
            )}
            <div style={{ marginTop: 10, fontSize: 11, color: '#166534', fontFamily: 'monospace' }}>
              {deployResult.pages_deployed.map(f => <div key={f}>• {f}</div>)}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

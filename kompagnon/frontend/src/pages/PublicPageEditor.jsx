import { useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { StudioEditor } from '@grapesjs/studio-sdk/react';
import '@grapesjs/studio-sdk/style';
import { useAuth } from '../context/AuthContext';
import { useScreenSize } from '../utils/responsive';
import toast from 'react-hot-toast';
import API_BASE_URL from '../config';

const LICENSE_KEY = process.env.REACT_APP_GJS_LICENSE_KEY || 'DEV_LICENSE_KEY';

export default function PublicPageEditor() {
  const { pageId } = useParams();
  const navigate   = useNavigate();
  const { token }  = useAuth();
  const { isMobile } = useScreenSize();
  const h = { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` };
  const authHeaders = { Authorization: `Bearer ${token}` };

  const [pageInfo, setPageInfo] = useState(null);
  const [saving, setSaving]     = useState(false);

  // ── Laden ────────────────────────────────────────────────
  const handleLoad = useCallback(async () => {
    try {
      const res = await fetch(
        `${API_BASE_URL}/api/pages/${pageId}`,
        { headers: authHeaders },
      );
      if (!res.ok) throw new Error('Seite nicht gefunden');
      const data = await res.json();
      setPageInfo(data);

      // GrapesJS-Daten vorhanden?
      if (data.grapesjs_data && typeof data.grapesjs_data === 'object'
          && Object.keys(data.grapesjs_data).length > 0) {
        return { project: data.grapesjs_data };
      }
      // Nur HTML vorhanden?
      if (data.html_content) {
        return {
          project: {
            pages: [{
              name: data.name || 'Seite',
              component: data.html_content,
              styles: data.css_content || '',
            }],
          },
        };
      }
      return {
        project: {
          pages: [{ name: data.name || 'Neue Seite', component: '' }],
        },
      };
    } catch (e) {
      toast.error(e.message);
      return { project: { pages: [{ name: 'Seite', component: '' }] } };
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pageId, token]);

  // ── Speichern ─────────────────────────────────────────────
  const handleSave = useCallback(async ({ project, editor }) => {
    setSaving(true);
    try {
      const html = editor?.getHtml?.() || '';
      const css  = editor?.getCss?.()  || '';
      await fetch(`${API_BASE_URL}/api/pages/${pageId}`, {
        method: 'PUT', headers: h,
        body: JSON.stringify({
          grapesjs_data: project,
          html_content:  html,
          css_content:   css,
        }),
      });
      toast.success('Gespeichert!');
    } catch { toast.error('Speichern fehlgeschlagen'); }
    setSaving(false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pageId, token]);

  // ── Als Live schalten ─────────────────────────────────────
  const publishPage = async () => {
    try {
      await fetch(`${API_BASE_URL}/api/pages/${pageId}`, {
        method: 'PUT', headers: h,
        body: JSON.stringify({ status: 'live' }),
      });
      setPageInfo(p => p ? { ...p, status: 'live' } : p);
      toast.success('Seite veröffentlicht ✓');
    } catch { toast.error('Fehler beim Veröffentlichen'); }
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: isMobile ? 0 : 'var(--sidebar-width)',
      right: 0,
      bottom: 0,
      zIndex: 500,
      display: 'flex', flexDirection: 'column', background: '#fff',
    }}>
      {/* Toolbar */}
      <div style={{
        height: 48, background: '#1a2c32', flexShrink: 0,
        display: 'flex', alignItems: 'center', gap: 12, padding: '0 16px',
        boxShadow: '0 2px 8px rgba(0,0,0,.25)',
      }}>
        <button onClick={() => navigate('/app/pages')} style={{
          padding: '6px 12px', background: 'rgba(255,255,255,.15)', color: '#fff',
          border: 'none', borderRadius: 6, fontSize: 12, fontWeight: 600,
          cursor: 'pointer', fontFamily: 'inherit',
        }}>
          ← Zurück
        </button>

        {pageInfo && (
          <div style={{ color: 'rgba(255,255,255,.7)', fontSize: 13, display: 'flex',
                        alignItems: 'center', gap: 10, overflow: 'hidden' }}>
            <span style={{ fontWeight: 600, color: '#fff' }}>{pageInfo.name}</span>
            <span style={{ fontFamily: 'monospace', fontSize: 11 }}>{pageInfo.slug}</span>
            <span style={{
              padding: '2px 7px', borderRadius: 3, fontSize: 10, fontWeight: 700,
              background: pageInfo.status === 'live' ? '#d1fae5' : '#fef3c7',
              color:      pageInfo.status === 'live' ? '#065f46' : '#92400e',
            }}>
              {pageInfo.status === 'live' ? 'Live' : 'Entwurf'}
            </span>
          </div>
        )}

        <div style={{ flex: 1 }}/>

        {saving && (
          <span style={{ color: 'rgba(255,255,255,.5)', fontSize: 12 }}>Wird gespeichert…</span>
        )}

        {pageInfo?.slug && (
          <a href={pageInfo.slug} target="_blank" rel="noreferrer" style={{
            padding: '6px 12px', background: 'rgba(255,255,255,.15)', color: '#fff',
            border: 'none', borderRadius: 6, fontSize: 12, fontWeight: 600,
            cursor: 'pointer', textDecoration: 'none',
          }}>
            👁 Vorschau
          </a>
        )}

        {pageInfo?.status !== 'live' && (
          <button onClick={publishPage} style={{
            padding: '6px 14px', background: '#1d9e75', color: '#fff',
            border: 'none', borderRadius: 6, fontSize: 12, fontWeight: 700,
            cursor: 'pointer', fontFamily: 'inherit',
          }}>
            🚀 Veröffentlichen
          </button>
        )}
      </div>

      {/* Studio SDK */}
      <div style={{ flex: 1, overflow: 'hidden' }}>
        <StudioEditor
          options={{
            licenseKey: LICENSE_KEY,
            project: {
              type: 'web',
              default: { pages: [{ name: 'Seite', component: '' }] },
            },
            storage: {
              type: 'self',
              autosaveChanges: 10,
              onSave: handleSave,
              onLoad: handleLoad,
            },
          }}
        />
      </div>
    </div>
  );
}

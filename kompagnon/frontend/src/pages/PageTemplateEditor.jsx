import { useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { StudioEditor } from '@grapesjs/studio-sdk/react';
import '@grapesjs/studio-sdk/style';
import { useAuth } from '../context/AuthContext';
import { useScreenSize } from '../utils/responsive';
import toast from 'react-hot-toast';
import API_BASE_URL from '../config';

const LICENSE_KEY = process.env.REACT_APP_GJS_LICENSE_KEY || 'DEV_LICENSE_KEY';

export default function PageTemplateEditor() {
  const { id }     = useParams();
  const navigate   = useNavigate();
  const { token }  = useAuth();
  const { isMobile } = useScreenSize();
  const h = { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` };
  const authHeaders = { Authorization: `Bearer ${token}` };

  const [tplInfo, setTplInfo] = useState(null);
  const [saving, setSaving]   = useState(false);

  // ── Laden ────────────────────────────────────────────────
  const handleLoad = useCallback(async () => {
    try {
      const res = await fetch(
        `${API_BASE_URL}/api/pages/templates/${id}`,
        { headers: authHeaders },
      );
      if (!res.ok) throw new Error('Template nicht gefunden');
      const data = await res.json();
      setTplInfo(data);

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
              name: data.name || 'Template',
              component: data.html_content,
              styles: data.css_content || '',
            }],
          },
        };
      }
      return {
        project: {
          pages: [{ name: data.name || 'Neues Template', component: '' }],
        },
      };
    } catch (e) {
      toast.error(e.message);
      return { project: { pages: [{ name: 'Template', component: '' }] } };
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id, token]);

  // ── Speichern ─────────────────────────────────────────────
  const handleSave = useCallback(async ({ project, editor }) => {
    if (tplInfo?.is_builtin) {
      toast.error('Eingebaute Templates können nicht geändert werden');
      return;
    }
    setSaving(true);
    try {
      const html = editor?.getHtml?.() || '';
      const css  = editor?.getCss?.()  || '';
      const res = await fetch(`${API_BASE_URL}/api/pages/templates/${id}`, {
        method: 'PUT', headers: h,
        body: JSON.stringify({
          grapesjs_data: project,
          html_content:  html,
          css_content:   css,
        }),
      });
      if (!res.ok) throw new Error('Speichern fehlgeschlagen');
      toast.success('Gespeichert!');
    } catch (e) { toast.error(e.message || 'Speichern fehlgeschlagen'); }
    setSaving(false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id, token, tplInfo]);

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

        {tplInfo && (
          <div style={{ color: 'rgba(255,255,255,.7)', fontSize: 13, display: 'flex',
                        alignItems: 'center', gap: 10, overflow: 'hidden' }}>
            <span style={{ fontSize: 14 }}>🖼</span>
            <span style={{ fontWeight: 600, color: '#fff' }}>{tplInfo.name}</span>
            <span style={{
              padding: '2px 7px', borderRadius: 3, fontSize: 10, fontWeight: 700,
              background: '#e0f4f8', color: '#008eaa',
            }}>
              {tplInfo.category || 'allgemein'}
            </span>
            {tplInfo.is_builtin && (
              <span style={{
                padding: '2px 7px', borderRadius: 3, fontSize: 10, fontWeight: 700,
                background: '#fef3c7', color: '#92400e',
              }}>
                Built-in (read-only)
              </span>
            )}
          </div>
        )}

        <div style={{ flex: 1 }}/>

        {saving && (
          <span style={{ color: 'rgba(255,255,255,.5)', fontSize: 12 }}>Wird gespeichert…</span>
        )}
      </div>

      {/* Studio SDK */}
      <div style={{ flex: 1, overflow: 'hidden' }}>
        <StudioEditor
          options={{
            licenseKey: LICENSE_KEY,
            project: {
              type: 'web',
              default: { pages: [{ name: 'Template', component: '' }] },
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

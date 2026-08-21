import { useEffect, useRef, useState, useCallback, useMemo } from 'react';
import { createPortal } from 'react-dom';
import { StudioEditor } from '@grapesjs/studio-sdk/react';
import '@grapesjs/studio-sdk/style';
import { useAuth } from '../context/AuthContext';
import { useScreenSize } from '../utils/responsive';
import { STUDIO_LICENSE_KEY, buildStudioPlugins } from '../utils/studioEditorConfig';
import { parseTemplateFile, applyTemplateToEditor } from '../utils/studioTemplateImport';
// processClipboardImage now handled by useGrapesAssetManager hook
import { useGrapesAssetManager } from '../hooks/useGrapesAssetManager';
import API_BASE_URL from '../config';
import {
  fehlermeldung, istEndzustand, pruefungAbgeschlossen, zusammenfassung,
} from '../utils/qualitaetspruefung';
import toast from 'react-hot-toast';

// Ein voller Audit braucht bis zu vier Minuten (Mehrseiten-Crawl, PageSpeed,
// KI). Alle fuenf Sekunden nachfragen reicht und haelt den Server in Ruhe.
const PRUEFUNG_ABSTAND_MS = 5000;
const PRUEFUNG_MAX_ABFRAGEN = 60;

export default function GrapesEditor({
  pageId, pageName, initialHtml, onClose, onSave, projectId, netlitySiteId, leadId,
  endpointBase = '/api/pages',
}) {
  const { token } = useAuth();
  const { isMobile } = useScreenSize();
  const headers = { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` };
  const authHeaders = { Authorization: `Bearer ${token}` };
  const editorRef = useRef(null);
  const fileInputRef = useRef(null);
  const plugins = useMemo(() => buildStudioPlugins(), []);
  const [netlifyDeploying, setNetlifyDeploying] = useState(false);
  const [pruefung, setPruefung] = useState({ laeuft: false, ergebnis: null });
  const [importing, setImporting] = useState(false);

  // Scroll sperren solange Editor offen ist
  useEffect(() => {
    document.body.style.overflow = 'hidden';
    return () => { document.body.style.overflow = ''; };
  }, []);

  // Listen for assets from ProjectFilesSection "→ Editor" button
  useEffect(() => {
    const onAssetAdd = (e) => {
      const editor = editorRef.current;
      if (!editor) return;
      const { src, name, category } = e.detail || {};
      if (!src) return;
      // Der AssetManager existiert erst nach dem Editor-Start; ein Bild, das
      // vorher eintrifft, wird beim naechsten Oeffnen ohnehin mitgeladen.
      try { editor.AssetManager?.add({ type: 'image', src, name: name || src, category }); } catch { /* Editor noch nicht bereit */ }
    };
    window.addEventListener('kompagnon:asset-add', onAssetAdd);
    return () => window.removeEventListener('kompagnon:asset-add', onAssetAdd);
  }, []);

  // Clipboard paste is now handled by useGrapesAssetManager hook

  // ── Save: HTML+CSS+gjsData an /api/pages/{id}/editor ──────
  const handleSave = useCallback(async ({ project, editor }) => {
    try {
      const html = editor?.getHtml?.() || '';
      const css  = editor?.getCss?.()  || '';
      await fetch(`${API_BASE_URL}${endpointBase}/${pageId}/editor`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ html, css, gjsData: project }),
      });
      toast.success('Gespeichert!');
      if (onSave) onSave({ html, css });
    } catch {
      toast.error('Seite konnte nicht gespeichert werden — bitte erneut versuchen');
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pageId, token, onSave, endpointBase]);

  // ── Load: bestehende Editor-Daten vom Backend ──────────────
  const handleLoad = useCallback(async () => {
    try {
      const res = await fetch(
        `${API_BASE_URL}${endpointBase}/${pageId}/editor`,
        { headers: authHeaders },
      );
      if (res.ok) {
        const data = await res.json();
        if (data?.gjsData && Object.keys(data.gjsData).length > 0) {
          return { project: data.gjsData };
        }
        if (data?.html) {
          return {
            project: {
              pages: [{ name: pageName || 'Seite', component: data.html }],
            },
          };
        }
      }
    } catch { /* fall through */ }
    return {
      project: {
        pages: [{ name: pageName || 'Seite', component: initialHtml || '' }],
      },
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pageId, pageName, initialHtml, token, endpointBase]);

  // ── Asset Manager — zentraler Hook ──
  const { onAssetsLoad, onAssetsUpload, editorRef: assetEditorRef } = useGrapesAssetManager({ leadId, projectId, token });

  // ── Netlify Deploy ────────────────────────────────────────
  const handleNetlifyDeploy = async () => {
    if (!editorRef.current || !projectId) return;
    const html = editorRef.current.getHtml() || '';
    const css  = editorRef.current.getCss()  || '';
    setNetlifyDeploying(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/projects/${projectId}/netlify/deploy`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          html,
          css,
          redirects: '',
          page_title: pageName || 'Website',
        }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      toast.success(
        <span>
          Live auf Netlify ✓{' '}
          {data.deploy_url && (
            <a href={data.deploy_url} target="_blank" rel="noopener noreferrer"
               style={{ color: '#16a34a', fontWeight: 700 }}>
              Link →
            </a>
          )}
        </span>
      );
    } catch {
      toast.error('Netlify-Deploy fehlgeschlagen — HTML auf Vollständigkeit prüfen');
    } finally {
      setNetlifyDeploying(false);
    }
  };

  const handlePreview = () => {
    if (!editorRef.current) return;
    const html = editorRef.current.getHtml() || '';
    const css  = editorRef.current.getCss()  || '';
    const w = window.open('', '_blank');
    w.document.write(`<!DOCTYPE html><html><head><style>${css}</style></head><body>${html}</body></html>`);
    w.document.close();
  };

  const handleManualSave = async () => {
    const editor = editorRef.current;
    if (!editor) return toast.error('Editor noch nicht bereit');
    const project = editor.getProjectData?.() || {};
    await handleSave({ project, editor });
  };

  // ── Eigenprüfung: unser Katalog gegen unsere eigene Seite ──
  //
  // Geprüft wird der Stand in der Datenbank, nicht der im Browser. Deshalb
  // wird erst gespeichert — sonst bezöge der Nutzer die Bewertung auf
  // Änderungen, die den Server nie erreicht haben.
  const handleQualitaetspruefung = async () => {
    const editor = editorRef.current;
    if (!editor) return toast.error('Editor noch nicht bereit');

    setPruefung({ laeuft: true, ergebnis: null });
    try {
      await handleSave({ project: editor.getProjectData?.() || {}, editor });

      const res = await fetch(
        `${API_BASE_URL}${endpointBase}/${pageId}/qualitaetspruefung`,
        { method: 'POST', headers },
      );
      if (!res.ok) {
        let detail = '';
        try { detail = (await res.json()).detail || ''; } catch { /* ohne Text */ }
        toast.error(fehlermeldung(res.status, detail));
        setPruefung({ laeuft: false, ergebnis: null });
        return;
      }

      const { audit_id: auditId } = await res.json();
      const ergebnis = await warteAufErgebnis(auditId);
      setPruefung({ laeuft: false, ergebnis });

      if (pruefungAbgeschlossen(ergebnis)) {
        const s = zusammenfassung(ergebnis);
        toast.success(`Eigenprüfung: ${s.punkte}/100 — ${s.stufe}`);
      } else {
        toast.error('Die Prüfung ist nicht durchgelaufen.');
      }
    } catch {
      toast.error(fehlermeldung(0, ''));
      setPruefung({ laeuft: false, ergebnis: null });
    }
  };

  // Der Audit läuft im Hintergrund; hier wird gewartet, bis er ein Ende hat.
  const warteAufErgebnis = async (auditId) => {
    for (let versuch = 0; versuch < PRUEFUNG_MAX_ABFRAGEN; versuch += 1) {
      await new Promise(r => setTimeout(r, PRUEFUNG_ABSTAND_MS));
      const res = await fetch(`${API_BASE_URL}/api/audit/${auditId}`,
                              { headers: authHeaders });
      if (!res.ok) continue;
      const daten = (await res.json()).data || {};
      if (istEndzustand(daten.status)) return daten;
    }
    return { status: 'failed' };
  };

  const handleImportFile = async (file) => {
    if (!file) return;
    setImporting(true);
    try {
      const parsed = await parseTemplateFile(file);
      if (!parsed.success) throw new Error(parsed.error);
      const editor = editorRef.current;
      if (!editor) throw new Error('Editor noch nicht bereit');
      applyTemplateToEditor(editor, parsed);
      toast.success({
        'zip-grapesjs': '✓ GrapesJS-Projekt + CSS geladen',
        'zip-html':     '✓ HTML + CSS geladen',
        'grapesjs':     '✓ GrapesJS-Projekt geladen',
      }[parsed.source] || '✓ Template geladen');
    } catch (err) { toast.error(err.message || 'Import fehlgeschlagen'); }
    finally {
      setImporting(false);
    }
  };

  return createPortal(
    <div style={{
      position: 'fixed',
      top: 0,
      left: isMobile ? 0 : 'var(--sidebar-width)',
      right: 0,
      bottom: 0,
      zIndex: 99999, display: 'flex', flexDirection: 'column',
      background: '#1a1a1a', overflow: 'hidden',
    }}>
      {/* Toolbar */}
      <div style={{
        height: 52, flexShrink: 0,
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '0 16px', background: '#1a2332', color: '#fff', zIndex: 1, gap: 10,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <button onClick={onClose} style={{
            background: 'none', border: '1px solid rgba(255,255,255,0.3)',
            color: '#fff', padding: '5px 12px', borderRadius: 6,
            cursor: 'pointer', fontSize: 13,
          }}>← Zurück</button>
          <span style={{ fontSize: 14, fontWeight: 600 }}>{pageName}</span>

          <input aria-label="Datei auswaehlen"
            ref={fileInputRef}
            type="file"
            accept=".zip,.grapesjs"
            style={{ display: 'none' }}
            onChange={e => { const f = e.target.files?.[0]; if (f) handleImportFile(f); e.target.value = ''; }}
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={importing}
            style={{
              background: importing ? '#5b21b6' : '#7c3aed',
              border: 'none', color: '#fff', padding: '6px 12px',
              borderRadius: 6, cursor: importing ? 'not-allowed' : 'pointer',
              fontSize: 12, fontWeight: 600,
            }}>
            {importing ? '⏳ Lädt…' : '📂 Template importieren'}
          </button>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button onClick={handlePreview} style={{
            background: 'none', border: '1px solid rgba(255,255,255,0.3)',
            color: '#fff', padding: '6px 14px', borderRadius: 6,
            cursor: 'pointer', fontSize: 13,
          }}>👁 Vorschau</button>
          <button onClick={handleManualSave} style={{
            background: 'var(--success)', border: 'none',
            color: 'var(--text-on-brand)', padding: '6px 14px', borderRadius: 6,
            cursor: 'pointer', fontSize: 13, fontWeight: 600,
          }}>💾 Speichern</button>
          <button
            onClick={handleQualitaetspruefung}
            disabled={pruefung.laeuft}
            title="Speichert und misst diese Seite mit dem Katalog, den auch Kunden bekommen"
            style={{
              background: 'none', border: '1px solid rgba(255,255,255,0.3)',
              color: '#fff', padding: '6px 14px', borderRadius: 6,
              cursor: pruefung.laeuft ? 'not-allowed' : 'pointer',
              fontSize: 13, opacity: pruefung.laeuft ? 0.6 : 1,
            }}
          >
            {pruefung.laeuft ? '⏳ Wird geprüft…' : '🔍 Qualität prüfen'}
          </button>
          {pruefungAbgeschlossen(pruefung.ergebnis) && (() => {
            const s = zusammenfassung(pruefung.ergebnis);
            const farbe = { gut: '#16a34a', mittel: '#ca8a04', schwach: '#dc2626' }[s.ampel];
            return (
              <a
                href={`${API_BASE_URL}/api/audit/${s.auditId}/pdf`}
                target="_blank" rel="noopener noreferrer"
                title={`${s.stufe} · ${s.abdeckung}% der Kriterien prüfbar — Bericht öffnen`}
                style={{
                  display: 'flex', alignItems: 'center', gap: 6,
                  background: farbe, color: '#fff', padding: '6px 12px',
                  borderRadius: 6, fontSize: 13, fontWeight: 700,
                  textDecoration: 'none',
                }}
              >
                {s.punkte}/100 <span style={{ fontWeight: 400, opacity: 0.9 }}>Bericht →</span>
              </a>
            );
          })()}
          {projectId && netlitySiteId && (
            <button
              onClick={handleNetlifyDeploy}
              disabled={netlifyDeploying}
              style={{
                background: netlifyDeploying ? '#166534' : '#16a34a',
                border: 'none', color: '#fff', padding: '6px 16px',
                borderRadius: 6,
                cursor: netlifyDeploying ? 'not-allowed' : 'pointer',
                fontSize: 13, fontWeight: 600,
                opacity: netlifyDeploying ? 0.8 : 1,
              }}
            >
              {netlifyDeploying ? '⏳ Wird deployed…' : '🚀 Direkt zu Netlify deployen'}
            </button>
          )}
          <button
            onClick={onClose}
            title="Editor schließen"
            style={{
              background: 'rgba(255,255,255,0.15)', border: 'none', color: '#fff',
              padding: '6px 12px', borderRadius: 6, cursor: 'pointer',
              fontSize: 14, fontWeight: 600,
            }}>
            ✕
          </button>
        </div>
      </div>

      {/* Studio SDK Canvas */}
      <div style={{ flex: 1, width: '100%', minHeight: 0 }}>
        <StudioEditor
          options={{
            licenseKey: STUDIO_LICENSE_KEY,
            project: {
              type: 'web',
              default: {
                pages: [{ name: pageName || 'Seite', component: '' }],
              },
            },
            storage: {
              type: 'self',
              autosaveChanges: 100,
              autosaveIntervalMs: 10000,
              onSave: handleSave,
              onLoad: handleLoad,
            },
            assets: projectId ? {
              storageType: 'self',
              onLoad:   onAssetsLoad,
              onUpload: onAssetsUpload,
            } : undefined,
            plugins,
          }}
          onReady={(editor) => { editorRef.current = editor; assetEditorRef.current = editor; }}
        />
      </div>
    </div>,
    document.body
  );
}

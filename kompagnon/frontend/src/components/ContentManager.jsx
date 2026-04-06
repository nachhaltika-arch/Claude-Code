/**
 * ContentManager — Text-Slots + Medien-Upload pro Sitemap-Seite
 * Props: { leadId, leadName, token, onClose }
 */
import { useState, useEffect, useRef, useCallback } from 'react';
import { createPortal } from 'react-dom';
import API_BASE_URL from '../config';
import { useScreenSize } from '../utils/responsive';

// ── Status-Farben ─────────────────────────────────────────────────────────────
const STATUS_COLOR = {
  ausstehend: { bg: '#F3F4F6', text: '#6B7280', label: 'Ausstehend' },
  ki_entwurf: { bg: '#DBEAFE', text: '#1D4ED8', label: 'KI-Entwurf' },
  vom_kunden: { bg: '#FEF3C7', text: '#D97706', label: 'Vom Kunden' },
  freigegeben: { bg: '#D1FAE5', text: '#065F46', label: '✅ Freigegeben' },
};

function StatusBadge({ status }) {
  const s = STATUS_COLOR[status] || STATUS_COLOR.ausstehend;
  return (
    <span style={{ background: s.bg, color: s.text, fontSize: 10, fontWeight: 600, padding: '2px 7px', borderRadius: 10, whiteSpace: 'nowrap' }}>
      {s.label}
    </span>
  );
}

// ── Debounce helper ───────────────────────────────────────────────────────────
function useDebounce(fn, delay) {
  const timer = useRef(null);
  return useCallback((...args) => {
    clearTimeout(timer.current);
    timer.current = setTimeout(() => fn(...args), delay);
  }, [fn, delay]);
}

// ── Section-Karte ─────────────────────────────────────────────────────────────
function SectionCard({ section, token, onUpdated }) {
  const [kiLoading, setKiLoading] = useState(false);
  const [kunde, setKunde] = useState(section.inhalt_kunde || '');
  const [final, setFinal] = useState(section.inhalt_final || '');
  const { isMobile } = useScreenSize();

  const h = { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' };

  async function generateKI() {
    setKiLoading(true);
    try {
      const r = await fetch(`${API_BASE_URL}/api/content/section/${section.id}/generate`, { method: 'POST', headers: h });
      const data = await r.json();
      onUpdated({ ...section, inhalt_ki: data.inhalt_ki, status: data.status });
    } finally {
      setKiLoading(false);
    }
  }

  const saveKunde = useDebounce(async (val) => {
    await fetch(`${API_BASE_URL}/api/content/section/${section.id}`, {
      method: 'PUT', headers: h,
      body: JSON.stringify({ inhalt_kunde: val, status: 'vom_kunden' }),
    });
    onUpdated({ ...section, inhalt_kunde: val, status: 'vom_kunden' });
  }, 1500);

  const saveFinal = useDebounce(async (val) => {
    await fetch(`${API_BASE_URL}/api/content/section/${section.id}`, {
      method: 'PUT', headers: h,
      body: JSON.stringify({ inhalt_final: val }),
    });
    onUpdated({ ...section, inhalt_final: val });
  }, 1500);

  async function approve() {
    await fetch(`${API_BASE_URL}/api/content/section/${section.id}`, {
      method: 'PUT', headers: h,
      body: JSON.stringify({ status: 'freigegeben' }),
    });
    onUpdated({ ...section, status: 'freigegeben' });
  }

  function adoptKI() {
    const text = section.inhalt_ki || '';
    setFinal(text);
    saveFinal(text);
  }

  const approved = section.status === 'freigegeben';

  return (
    <div style={{ border: '1px solid var(--border-light)', borderRadius: 8, overflow: 'hidden', marginBottom: 12 }}>
      {/* Header */}
      <div style={{ background: 'var(--bg-app)', padding: '10px 14px', display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
        <span style={{ fontWeight: 600, fontSize: 13, color: 'var(--text-primary)', flex: 1 }}>
          {section.slot_label}
        </span>
        {section.zeichenlimit && (
          <span style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>max. {section.zeichenlimit} Z.</span>
        )}
        <StatusBadge status={section.status} />
        <button
          onClick={generateKI}
          disabled={kiLoading}
          style={{ fontSize: 11, padding: '4px 10px', borderRadius: 6, border: '1px solid var(--brand-primary)', background: 'var(--brand-primary-light)', color: 'var(--brand-primary)', cursor: kiLoading ? 'not-allowed' : 'pointer', fontFamily: 'var(--font-sans)', display: 'flex', alignItems: 'center', gap: 4 }}
        >
          {kiLoading ? <><span style={{ width: 10, height: 10, borderRadius: '50%', border: '2px solid var(--brand-primary)', borderTopColor: 'transparent', animation: 'spin 0.8s linear infinite', display: 'inline-block' }} />Generiere...</> : '🤖 KI-Entwurf'}
        </button>
      </div>

      {/* Hinweis */}
      {section.hinweis && (
        <div style={{ padding: '6px 14px', fontSize: 11, color: 'var(--text-tertiary)', fontStyle: 'italic', borderBottom: '1px solid var(--border-light)' }}>
          {section.hinweis}
        </div>
      )}

      {/* 3-Spalten */}
      <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : 'repeat(3, 1fr)', gap: 0 }}>
        {/* KI-Entwurf */}
        <div style={{ background: '#EFF6FF', padding: 12, borderRight: '1px solid var(--border-light)' }}>
          <div style={{ fontSize: 11, fontWeight: 600, color: '#1D4ED8', marginBottom: 6 }}>KI-Entwurf</div>
          {section.inhalt_ki ? (
            <>
              <div style={{ fontSize: 12, color: '#1e3a5f', whiteSpace: 'pre-wrap', lineHeight: 1.5, minHeight: 60 }}>{section.inhalt_ki}</div>
              <button
                onClick={adoptKI}
                style={{ marginTop: 8, fontSize: 11, padding: '4px 10px', borderRadius: 6, border: '1px solid #1D4ED8', background: '#DBEAFE', color: '#1D4ED8', cursor: 'pointer', fontFamily: 'var(--font-sans)' }}
              >
                Übernehmen →
              </button>
            </>
          ) : (
            <div style={{ fontSize: 12, color: '#93C5FD', fontStyle: 'italic', minHeight: 60 }}>
              Noch kein KI-Entwurf — Klick auf 🤖
            </div>
          )}
        </div>

        {/* Vom Kunden */}
        <div style={{ background: '#FFFBEB', padding: 12, borderRight: '1px solid var(--border-light)' }}>
          <div style={{ fontSize: 11, fontWeight: 600, color: '#D97706', marginBottom: 6 }}>Vom Kunden</div>
          <textarea
            value={kunde}
            onChange={e => { setKunde(e.target.value); saveKunde(e.target.value); }}
            placeholder="Hier den Text des Kunden eintragen..."
            rows={4}
            style={{ width: '100%', fontSize: 12, border: '1px solid #FDE68A', borderRadius: 6, padding: '6px 8px', resize: 'vertical', fontFamily: 'var(--font-sans)', background: '#FFFEF5', color: 'var(--text-primary)', boxSizing: 'border-box' }}
          />
        </div>

        {/* Finaler Text */}
        <div style={{ background: '#F0FDF4', padding: 12 }}>
          <div style={{ fontSize: 11, fontWeight: 600, color: '#065F46', marginBottom: 6 }}>Finaler Text</div>
          <textarea
            value={final}
            onChange={e => { setFinal(e.target.value); saveFinal(e.target.value); }}
            placeholder="Finaler Text für den Mockup..."
            rows={4}
            style={{ width: '100%', fontSize: 12, border: '1px solid #A7F3D0', borderRadius: 6, padding: '6px 8px', resize: 'vertical', fontFamily: 'var(--font-sans)', background: '#F7FEF9', color: 'var(--text-primary)', boxSizing: 'border-box' }}
          />
          <button
            onClick={approve}
            disabled={approved}
            style={{ marginTop: 8, fontSize: 11, padding: '4px 10px', borderRadius: 6, border: `1px solid ${approved ? '#A7F3D0' : '#065F46'}`, background: approved ? '#D1FAE5' : '#065F46', color: approved ? '#065F46' : 'white', cursor: approved ? 'default' : 'pointer', fontFamily: 'var(--font-sans)' }}
          >
            {approved ? '✅ Freigegeben' : '✅ Freigeben'}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Medien-Karte ──────────────────────────────────────────────────────────────
function MediaCard({ media, token, onUpdated, onDeleted }) {
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [uploadError, setUploadError] = useState('');
  const [deleteConfirm, setDeleteConfirm] = useState(false);
  const fileRef = useRef(null);
  const h = { Authorization: `Bearer ${token}` };

  async function handleFile(file) {
    if (!file) return;
    if (file.size > 10 * 1024 * 1024) { setUploadError('Datei zu groß (max. 10 MB)'); return; }
    setUploadError('');
    setUploading(true); setProgress(10);
    try {
      const fd = new FormData();
      fd.append('file', file);
      const xhr = new XMLHttpRequest();
      xhr.upload.onprogress = e => e.lengthComputable && setProgress(Math.round(e.loaded / e.total * 90));
      xhr.open('POST', `${API_BASE_URL}/api/content/media/${media.id}/upload`);
      xhr.setRequestHeader('Authorization', `Bearer ${token}`);
      await new Promise((res, rej) => {
        xhr.onload = () => { setProgress(100); res(); };
        xhr.onerror = rej;
        xhr.send(fd);
      });
      const updated = JSON.parse(xhr.responseText);
      onUpdated({ ...media, ...updated });
    } finally {
      setUploading(false); setProgress(0);
    }
  }

  async function handleApprove() {
    await fetch(`${API_BASE_URL}/api/content/media/${media.id}`, {
      method: 'PUT', headers: { ...h, 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: 'freigegeben' }),
    });
    onUpdated({ ...media, status: 'freigegeben' });
  }

  async function handleDelete() {
    if (!deleteConfirm) { setDeleteConfirm(true); return; }
    setDeleteConfirm(false);
    await fetch(`${API_BASE_URL}/api/content/media/${media.id}`, { method: 'DELETE', headers: h });
    onDeleted(media.id);
  }

  const hasFile = media.status !== 'ausstehend' && media.dateiname;

  return (
    <div style={{ border: hasFile ? '1px solid var(--border-light)' : '2px dashed #CBD5E1', borderRadius: 10, padding: 14, background: 'var(--bg-surface)', display: 'flex', flexDirection: 'column', gap: 8 }}>
      <div style={{ fontWeight: 600, fontSize: 13, color: 'var(--text-primary)', textAlign: hasFile ? 'left' : 'center' }}>{media.slot_label}</div>
      {media.hinweis && (
        <div style={{ fontSize: 11, color: 'var(--text-tertiary)', fontStyle: 'italic', textAlign: hasFile ? 'left' : 'center' }}>{media.hinweis}</div>
      )}

      {hasFile ? (
        <>
          <img
            src={`${API_BASE_URL}/api/content/media/${media.id}/file`}
            alt={media.dateiname}
            style={{ width: '100%', maxHeight: 150, objectFit: 'cover', borderRadius: 8, display: 'block' }}
          />
          <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>
            {media.dateiname} · {media.dateigroesse_kb} KB
          </div>
          <StatusBadge status={media.status} />
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', alignItems: 'center' }}>
            {media.status !== 'freigegeben' && (
              <button onClick={handleApprove} style={{ fontSize: 11, padding: '4px 8px', borderRadius: 6, border: '1px solid #065F46', background: '#065F46', color: 'white', cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>✅ Freigeben</button>
            )}
            <button onClick={() => fileRef.current?.click()} style={{ fontSize: 11, padding: '4px 8px', borderRadius: 6, border: '1px solid var(--border-medium)', background: 'var(--bg-elevated)', color: 'var(--text-secondary)', cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>🔄 Ersetzen</button>
            {deleteConfirm ? (
              <>
                <span style={{ fontSize: 11, color: '#DC2626' }}>Sicher?</span>
                <button onClick={handleDelete} style={{ fontSize: 11, padding: '4px 8px', borderRadius: 6, border: '1px solid #DC2626', background: '#DC2626', color: 'white', cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>Ja, löschen</button>
                <button onClick={() => setDeleteConfirm(false)} style={{ fontSize: 11, padding: '4px 8px', borderRadius: 6, border: '1px solid var(--border-medium)', background: 'var(--bg-elevated)', color: 'var(--text-secondary)', cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>Abbrechen</button>
              </>
            ) : (
              <button onClick={handleDelete} style={{ fontSize: 11, padding: '4px 8px', borderRadius: 6, border: '1px solid #FCA5A5', background: '#FEF2F2', color: '#DC2626', cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>🗑️ Löschen</button>
            )}
          </div>
        </>
      ) : (
        <>
          <div
            onClick={() => fileRef.current?.click()}
            onDragOver={e => e.preventDefault()}
            onDrop={e => { e.preventDefault(); handleFile(e.dataTransfer.files[0]); }}
            style={{ padding: '20px 12px', textAlign: 'center', cursor: 'pointer', borderRadius: 8, background: '#F8FAFC' }}
          >
            <div style={{ fontSize: 28 }}>📤</div>
            <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 4 }}>Datei hier ablegen oder klicken</div>
            <div style={{ fontSize: 10, color: 'var(--text-tertiary)', marginTop: 4 }}>max. 10 MB · JPG, PNG, WebP, SVG</div>
          </div>
          {uploading && (
            <div style={{ height: 4, background: '#E2E8F0', borderRadius: 2, overflow: 'hidden' }}>
              <div style={{ width: `${progress}%`, height: '100%', background: 'var(--brand-primary)', transition: 'width 0.3s ease' }} />
            </div>
          )}
          {uploadError && (
            <div style={{ fontSize: 11, color: '#DC2626', background: '#FEF2F2', border: '1px solid #FCA5A5', borderRadius: 6, padding: '5px 10px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span>⚠️ {uploadError}</span>
              <button onClick={() => setUploadError('')} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#DC2626', fontSize: 14, lineHeight: 1, padding: 0, marginLeft: 8 }}>×</button>
            </div>
          )}
        </>
      )}
      <input ref={fileRef} type="file" accept="image/*" style={{ display: 'none' }} onChange={e => handleFile(e.target.files[0])} />
    </div>
  );
}

// ── Rechte Spalte — Seiten-Inhalt ─────────────────────────────────────────────
function PageContent({ page, token, onPageUpdated }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loadError, setLoadError] = useState('');
  const [genAllLoading, setGenAllLoading] = useState(false);
  const h = { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' };

  useEffect(() => {
    if (!page) return;
    setLoading(true); setLoadError('');
    fetch(`${API_BASE_URL}/api/content/page/${page.sitemap_page_id}`, { headers: h })
      .then(r => { if (!r.ok) throw new Error(`Fehler ${r.status}`); return r.json(); })
      .then(d => { setData(d); setLoading(false); })
      .catch(e => { setLoadError(e.message || 'Slots konnten nicht geladen werden'); setLoading(false); });
  }, [page?.sitemap_page_id]);

  function updateSection(updated) {
    setData(d => d ? { ...d, sections: d.sections.map(s => s.id === updated.id ? updated : s) } : d);
    onPageUpdated?.();
  }

  function updateMedia(updated) {
    setData(d => d ? { ...d, media: d.media.map(m => m.id === updated.id ? updated : m) } : d);
    onPageUpdated?.();
  }

  function deleteMedia(id) {
    setData(d => d ? { ...d, media: d.media.map(m => m.id === id ? { ...m, status: 'ausstehend', dateiname: null, datei_base64: null } : m) } : d);
    onPageUpdated?.();
  }

  async function generateAll() {
    setGenAllLoading(true);
    try {
      await fetch(`${API_BASE_URL}/api/content/page/${page.sitemap_page_id}/generate-all`, { method: 'POST', headers: h });
      const r = await fetch(`${API_BASE_URL}/api/content/page/${page.sitemap_page_id}`, { headers: h });
      setData(await r.json());
      onPageUpdated?.();
    } finally {
      setGenAllLoading(false);
    }
  }

  if (!page) return <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-tertiary)' }}>← Seite auswählen</div>;
  if (loading) return <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-tertiary)' }}>Lade Slots…</div>;
  if (loadError) return (
    <div style={{ padding: 40, textAlign: 'center' }}>
      <div style={{ fontSize: 28, marginBottom: 10 }}>⚠️</div>
      <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 6 }}>Slots konnten nicht geladen werden</div>
      <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginBottom: 16 }}>{loadError}</div>
      <button onClick={() => { setLoadError(''); setLoading(true); fetch(`${API_BASE_URL}/api/content/page/${page.sitemap_page_id}`, { headers: h }).then(r => r.json()).then(d => { setData(d); setLoading(false); }).catch(e => { setLoadError(e.message); setLoading(false); }); }} style={{ padding: '8px 16px', borderRadius: 8, border: '1px solid var(--border-medium)', background: 'var(--bg-elevated)', color: 'var(--text-primary)', cursor: 'pointer', fontFamily: 'var(--font-sans)', fontSize: 13 }}>Erneut versuchen</button>
    </div>
  );
  if (!data) return null;

  const mediaEingegangen = data.media.filter(m => m.status !== 'ausstehend').length;

  return (
    <div style={{ padding: '20px 24px', overflowY: 'auto', height: '100%' }}>
      {/* Seiten-Header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 16, gap: 12, flexWrap: 'wrap' }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 18, fontWeight: 600, color: 'var(--text-primary)' }}>{data.page_name}</h2>
          {page.ziel_keyword && (
            <span style={{ display: 'inline-block', marginTop: 4, fontSize: 11, background: 'var(--brand-primary-light)', color: 'var(--brand-primary)', borderRadius: 10, padding: '2px 8px', fontWeight: 600 }}>{page.ziel_keyword}</span>
          )}
          {page.zweck && <div style={{ fontSize: 12, color: 'var(--text-tertiary)', fontStyle: 'italic', marginTop: 4 }}>{page.zweck}</div>}
        </div>
        <button
          onClick={generateAll}
          disabled={genAllLoading}
          style={{ padding: '8px 16px', borderRadius: 8, border: 'none', background: genAllLoading ? 'var(--bg-elevated)' : 'var(--brand-primary)', color: genAllLoading ? 'var(--text-tertiary)' : 'white', fontSize: 13, fontWeight: 500, cursor: genAllLoading ? 'not-allowed' : 'pointer', fontFamily: 'var(--font-sans)', display: 'flex', alignItems: 'center', gap: 6, flexShrink: 0 }}
        >
          {genAllLoading
            ? <><span style={{ width: 12, height: 12, borderRadius: '50%', border: '2px solid var(--text-tertiary)', borderTopColor: 'var(--brand-primary)', animation: 'spin 0.8s linear infinite', display: 'inline-block' }} />Generiere…</>
            : '🤖 Alle Texte generieren'}
        </button>
      </div>

      {/* Text-Blöcke */}
      {data.sections.length > 0 && (
        <div style={{ marginBottom: 24 }}>
          {data.sections.map(s => (
            <SectionCard key={s.id} section={s} token={token} onUpdated={updateSection} />
          ))}
        </div>
      )}

      {/* Medien */}
      {data.media.length > 0 && (
        <>
          <div style={{ borderTop: '1px solid var(--border-light)', paddingTop: 20, marginBottom: 12 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
              <span style={{ fontSize: 15, fontWeight: 600, color: 'var(--text-primary)' }}>📁 Benötigte Medien</span>
              <span style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>{mediaEingegangen}/{data.media.length} Medien eingegangen</span>
            </div>
            {/* Hinweis-Box */}
            <div style={{ background: '#FFFBEB', border: '1px solid #FDE68A', borderRadius: 8, padding: '10px 14px', fontSize: 12, color: '#92400E', marginBottom: 14 }}>
              Bilder sollten mind. 1200px breit sein und als JPG oder PNG geliefert werden. Wir optimieren alle Bilder automatisch für die Website.
            </div>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: 14 }}>
            {data.media.map(m => (
              <MediaCard key={m.id} media={m} token={token} onUpdated={updateMedia} onDeleted={deleteMedia} />
            ))}
          </div>
        </>
      )}
    </div>
  );
}

// ── Haupt-Komponente ──────────────────────────────────────────────────────────
export default function ContentManager({ leadId, leadName, token, onClose }) {
  const [pages, setPages] = useState([]);
  const [activePage, setActivePage] = useState(null);
  const [loading, setLoading] = useState(true);
  const h = { Authorization: `Bearer ${token}` };

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/content/${leadId}`, { headers: h })
      .then(r => r.json())
      .then(data => {
        const content = Array.isArray(data) ? data.filter(p => !p.ist_pflichtseite) : [];
        setPages(content);
        if (content.length > 0) setActivePage(content[0]);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [leadId]);

  function refreshPages() {
    fetch(`${API_BASE_URL}/api/content/${leadId}`, { headers: h })
      .then(r => r.json())
      .then(data => {
        const content = Array.isArray(data) ? data.filter(p => !p.ist_pflichtseite) : [];
        setPages(content);
        if (activePage) {
          const updated = content.find(p => p.sitemap_page_id === activePage.sitemap_page_id);
          if (updated) setActivePage(updated);
        }
      });
  }

  function pageProgress(page) {
    const total = (page.sections?.length || 0) + (page.media?.length || 0);
    const done  = (page.sections?.filter(s => s.status === 'freigegeben').length || 0)
                + (page.media?.filter(m => m.status === 'freigegeben').length || 0);
    return { total, done };
  }

  const { isMobile } = useScreenSize();

  function pageIcon(type) {
    return type === 'startseite' ? '🏠' : type === 'leistung' ? '🔧' : type === 'info' ? 'ℹ️' : type === 'vertrauen' ? '⭐' : type === 'conversion' ? '📞' : '📄';
  }

  return createPortal(
    <div style={{ position: 'fixed', inset: 0, zIndex: 200, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: isMobile ? 'flex-end' : 'center', justifyContent: 'center', padding: isMobile ? 0 : 16 }}>
      <div style={{ background: 'var(--bg-surface)', borderRadius: isMobile ? '16px 16px 0 0' : 12, width: '100%', maxWidth: 1100, height: isMobile ? '94vh' : '90vh', display: 'flex', flexDirection: 'column', overflow: 'hidden', boxShadow: '0 24px 80px rgba(0,0,0,0.25)' }}>

        {/* Header */}
        <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border-light)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexShrink: 0 }}>
          <div style={{ minWidth: 0, overflow: 'hidden' }}>
            <span style={{ fontSize: 15, fontWeight: 600, color: 'var(--text-primary)' }}>Content-Management</span>
            {leadName && !isMobile && <span style={{ fontSize: 13, color: 'var(--text-tertiary)', marginLeft: 8 }}>— {leadName}</span>}
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', fontSize: 20, cursor: 'pointer', color: 'var(--text-tertiary)', lineHeight: 1, flexShrink: 0 }}>✕</button>
        </div>

        {/* Mobile: horizontale Tab-Bar */}
        {isMobile && (
          <div style={{ borderBottom: '1px solid var(--border-light)', overflowX: 'auto', display: 'flex', flexShrink: 0, scrollbarWidth: 'none', WebkitOverflowScrolling: 'touch' }}>
            {loading && <div style={{ padding: '10px 16px', color: 'var(--text-tertiary)', fontSize: 12 }}>Lade Seiten…</div>}
            {pages.map(page => {
              const { total, done } = pageProgress(page);
              const isActive = activePage?.sitemap_page_id === page.sitemap_page_id;
              return (
                <button
                  key={page.sitemap_page_id}
                  onClick={() => setActivePage(page)}
                  style={{ flexShrink: 0, padding: '10px 14px', background: 'none', border: 'none', borderBottom: isActive ? '2px solid var(--brand-primary)' : '2px solid transparent', cursor: 'pointer', fontFamily: 'var(--font-sans)', display: 'flex', alignItems: 'center', gap: 6, whiteSpace: 'nowrap' }}
                >
                  <span>{pageIcon(page.page_type)}</span>
                  <span style={{ fontSize: 13, fontWeight: isActive ? 600 : 400, color: isActive ? 'var(--brand-primary)' : 'var(--text-secondary)' }}>{page.page_name}</span>
                  {total > 0 && <span style={{ fontSize: 10, color: done === total ? '#065F46' : 'var(--text-tertiary)', fontWeight: 600 }}>{done}/{total}</span>}
                </button>
              );
            })}
          </div>
        )}

        {/* Body */}
        <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>

          {/* Desktop: Linke Spalte — Seitennavigation */}
          {!isMobile && (
            <div style={{ width: 250, flexShrink: 0, borderRight: '1px solid var(--border-light)', overflowY: 'auto', padding: '12px 0' }}>
              <div style={{ fontSize: 10, color: 'var(--text-tertiary)', padding: '0 14px 8px', fontStyle: 'italic' }}>
                Pflichtseiten werden von KOMPAGNON befüllt.
              </div>
              {loading && <div style={{ padding: '20px 14px', color: 'var(--text-tertiary)', fontSize: 12 }}>Lade Seiten…</div>}
              {pages.map(page => {
                const { total, done } = pageProgress(page);
                const isActive = activePage?.sitemap_page_id === page.sitemap_page_id;
                return (
                  <div
                    key={page.sitemap_page_id}
                    onClick={() => setActivePage(page)}
                    style={{ padding: '10px 14px', cursor: 'pointer', background: isActive ? '#E6F1FB' : 'transparent', borderLeft: isActive ? '3px solid var(--brand-primary)' : '3px solid transparent', display: 'flex', alignItems: 'center', gap: 8 }}
                  >
                    <span style={{ fontSize: 14 }}>{pageIcon(page.page_type)}</span>
                    <span style={{ flex: 1, fontSize: 13, fontWeight: isActive ? 500 : 400, color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{page.page_name}</span>
                    {total > 0 && (
                      <span style={{ fontSize: 10, color: done === total ? '#065F46' : 'var(--text-tertiary)', fontWeight: 600, flexShrink: 0 }}>
                        {done}/{total} {done === total ? '✅' : ''}
                      </span>
                    )}
                  </div>
                );
              })}
            </div>
          )}

          {/* Rechte Spalte */}
          <div style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
            <PageContent page={activePage} token={token} onPageUpdated={refreshPages} />
          </div>
        </div>
      </div>
    </div>,
    document.body
  );
}

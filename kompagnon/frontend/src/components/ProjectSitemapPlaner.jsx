import { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import toast from 'react-hot-toast';
import { DndContext, closestCenter, PointerSensor, useSensor, useSensors } from '@dnd-kit/core';
import { SortableContext, verticalListSortingStrategy, useSortable, arrayMove } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { useAuth } from '../context/AuthContext';
import API_BASE_URL from '../config';

const PAGE_TYPES = ['Landing', 'Info', 'Leistung', 'Kontakt', 'Blog'];

const DEFAULT_PAGES = [
  { id: '1', name: 'Startseite', type: 'Landing', keyword: '' },
  { id: '2', name: 'Leistungen', type: 'Info', keyword: '' },
  { id: '3', name: 'Ueber uns', type: 'Info', keyword: '' },
  { id: '4', name: 'Kontakt', type: 'Kontakt', keyword: '' },
];

let _idCounter = 100;
const nextId = () => String(++_idCounter);

// ── Sortable page card ───────────────────────────────────────────────────────

function SortablePage({ page, onChange, onDelete }) {
  const { attributes, listeners, setNodeRef, transform, transition } = useSortable({ id: page.id });
  const style = { transform: CSS.Transform.toString(transform), transition };

  return (
    <div ref={setNodeRef} style={{ ...style, display: 'flex', alignItems: 'center', gap: 8, background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)', padding: '10px 12px', marginBottom: 6 }}>
      <span {...attributes} {...listeners} style={{ cursor: 'grab', fontSize: 16, color: 'var(--text-tertiary)', flexShrink: 0, userSelect: 'none' }}>&#x2807;</span>
      <input
        value={page.name}
        onChange={e => onChange({ ...page, name: e.target.value })}
        placeholder="Seitenname"
        style={{ flex: 2, padding: '6px 10px', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)', fontSize: 13, fontFamily: 'var(--font-sans)', background: 'var(--bg-surface)', color: 'var(--text-primary)', boxSizing: 'border-box', minWidth: 0 }}
      />
      <select
        value={page.type}
        onChange={e => onChange({ ...page, type: e.target.value })}
        style={{ flex: 1, padding: '6px 8px', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)', fontSize: 12, fontFamily: 'var(--font-sans)', background: 'var(--bg-surface)', color: 'var(--text-primary)', minWidth: 90 }}
      >
        {PAGE_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
      </select>
      <input
        value={page.keyword}
        onChange={e => onChange({ ...page, keyword: e.target.value })}
        placeholder="Ziel-Keyword"
        style={{ flex: 1.5, padding: '6px 10px', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)', fontSize: 12, fontFamily: 'var(--font-sans)', background: 'var(--bg-surface)', color: 'var(--text-secondary)', boxSizing: 'border-box', minWidth: 0 }}
      />
      <button onClick={() => onDelete(page.id)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-tertiary)', fontSize: 16, padding: 4, flexShrink: 0 }} title="Seite loeschen">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M3 4h10M6 4V3a1 1 0 011-1h2a1 1 0 011 1v1M5 4v8.5a1 1 0 001 1h4a1 1 0 001-1V4"/></svg>
      </button>
    </div>
  );
}

// ── Main component ───────────────────────────────────────────────────────────

export default function ProjectSitemapPlaner({ projectId, briefingData, onClose }) {
  const { token } = useAuth();
  const [pages, setPages] = useState([]);
  const [freigabe, setFreigabe] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  const h = { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) };

  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 5 } }));

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/projects/${projectId}/sitemap`, { headers: h })
      .then(r => r.json())
      .then(data => {
        if (data.seiten && data.seiten.length > 0) {
          setPages(data.seiten.map((s, i) => ({ id: String(i + 1), name: s.name || '', type: s.type || 'Info', keyword: s.keyword || '' })));
        } else if (briefingData?.wunschseiten?.length > 0) {
          const ws = Array.isArray(briefingData.wunschseiten) ? briefingData.wunschseiten : [];
          setPages(ws.map((s, i) => ({ id: String(i + 1), name: s, type: 'Info', keyword: '' })));
        } else {
          setPages(DEFAULT_PAGES.map(p => ({ ...p })));
        }
        setFreigabe(data.freigabe || null);
      })
      .catch(() => setPages(DEFAULT_PAGES.map(p => ({ ...p }))))
      .finally(() => setLoading(false));
  }, [projectId]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleDragEnd = (event) => {
    const { active, over } = event;
    if (active.id !== over?.id) {
      setPages(prev => {
        const oldIdx = prev.findIndex(p => p.id === active.id);
        const newIdx = prev.findIndex(p => p.id === over.id);
        return arrayMove(prev, oldIdx, newIdx);
      });
    }
  };

  const updatePage = (updated) => setPages(prev => prev.map(p => p.id === updated.id ? updated : p));
  const deletePage = (id) => setPages(prev => prev.filter(p => p.id !== id));
  const addPage = () => setPages(prev => [...prev, { id: nextId(), name: '', type: 'Info', keyword: '' }]);

  const save = async () => {
    setSaving(true);
    try {
      const seiten = pages.map(p => ({ name: p.name, type: p.type, keyword: p.keyword }));
      const r = await fetch(`${API_BASE_URL}/api/projects/${projectId}/sitemap`, { method: 'PUT', headers: h, body: JSON.stringify({ seiten }) });
      if (r.ok) toast.success('Sitemap gespeichert');
      else toast.error('Speichern fehlgeschlagen');
    } catch { toast.error('Speichern fehlgeschlagen'); }
    setSaving(false);
  };

  const requestFreigabe = async () => {
    setShowConfirm(false);
    setSaving(true);
    try {
      const seiten = pages.map(p => ({ name: p.name, type: p.type, keyword: p.keyword }));
      const r = await fetch(`${API_BASE_URL}/api/projects/${projectId}/freigabe`, {
        method: 'POST', headers: h,
        body: JSON.stringify({ typ: 'sitemap', seiten, zeitstempel: new Date().toISOString() }),
      });
      if (r.ok) {
        const data = await r.json();
        setFreigabe(data.freigabe);
        toast.success('Sitemap wurde freigegeben!');
      } else toast.error('Freigabe fehlgeschlagen');
    } catch { toast.error('Freigabe fehlgeschlagen'); }
    setSaving(false);
  };

  const fmtDate = (d) => {
    const dt = new Date(d);
    return dt.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' })
      + ' um ' + dt.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' }) + ' Uhr';
  };

  const overlay = { position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', zIndex: 9999, display: 'flex', alignItems: 'center', justifyContent: 'center' };
  const modal = { background: 'var(--bg-surface)', borderRadius: 12, padding: 28, width: '100%', maxWidth: 700, maxHeight: '90vh', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 16 };

  return createPortal(
    <div style={overlay} onClick={e => e.target === e.currentTarget && onClose?.()}>
      <div style={modal} onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <h2 style={{ fontSize: 17, fontWeight: 600, color: 'var(--text-primary)', margin: 0 }}>Sitemap-Planer</h2>
            {freigabe ? (
              <span style={{ display: 'inline-block', marginTop: 6, fontSize: 11, fontWeight: 500, padding: '3px 10px', borderRadius: 999, background: 'var(--status-success-bg)', color: 'var(--status-success-text)' }}>
                Freigegeben am {fmtDate(freigabe)}
              </span>
            ) : (
              <span style={{ fontSize: 12, color: 'var(--text-tertiary)', marginTop: 4, display: 'block' }}>Freigabe ausstehend</span>
            )}
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', fontSize: 20, cursor: 'pointer', color: 'var(--text-tertiary)' }}>&#10005;</button>
        </div>

        {/* Pages list */}
        {loading ? (
          <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-tertiary)', fontSize: 13 }}>Laden...</div>
        ) : (
          <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
            <SortableContext items={pages.map(p => p.id)} strategy={verticalListSortingStrategy}>
              {pages.map(p => (
                <SortablePage key={p.id} page={p} onChange={updatePage} onDelete={deletePage} />
              ))}
            </SortableContext>
          </DndContext>
        )}

        {/* Add page */}
        <button onClick={addPage} style={{ width: '100%', padding: '10px', border: '2px dashed var(--border-light)', borderRadius: 'var(--radius-md)', background: 'none', color: 'var(--brand-primary)', fontSize: 13, fontWeight: 500, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
          + Seite hinzufuegen
        </button>

        {/* Actions */}
        <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end', flexWrap: 'wrap' }}>
          <button onClick={onClose} style={{ padding: '8px 18px', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)', background: 'var(--bg-surface)', color: 'var(--text-secondary)', fontSize: 13, fontWeight: 500, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>Schliessen</button>
          <button onClick={save} disabled={saving} style={{ padding: '8px 18px', border: 'none', borderRadius: 'var(--radius-md)', background: 'var(--brand-primary)', color: '#fff', fontSize: 13, fontWeight: 600, cursor: saving ? 'not-allowed' : 'pointer', fontFamily: 'var(--font-sans)' }}>
            {saving ? 'Speichern...' : 'Speichern'}
          </button>
          <button onClick={() => setShowConfirm(true)} disabled={saving} style={{ padding: '8px 18px', border: 'none', borderRadius: 'var(--radius-md)', background: '#008eaa', color: '#fff', fontSize: 13, fontWeight: 600, cursor: saving ? 'not-allowed' : 'pointer', fontFamily: 'var(--font-sans)' }}>
            Freigabe anfordern
          </button>
        </div>

        {/* Confirm dialog */}
        {showConfirm && (
          <div style={{ background: 'var(--status-warning-bg)', border: '1px solid #fde68a', borderRadius: 'var(--radius-md)', padding: '14px 18px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
            <span style={{ fontSize: 13, color: '#92400e' }}>Sitemap jetzt freigeben? Dies kann nicht rueckgaengig gemacht werden.</span>
            <div style={{ display: 'flex', gap: 8 }}>
              <button onClick={() => setShowConfirm(false)} style={{ padding: '6px 14px', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)', background: 'var(--bg-surface)', color: 'var(--text-secondary)', fontSize: 12, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>Abbrechen</button>
              <button onClick={requestFreigabe} style={{ padding: '6px 14px', border: 'none', borderRadius: 'var(--radius-md)', background: '#008eaa', color: '#fff', fontSize: 12, fontWeight: 600, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>Ja, freigeben</button>
            </div>
          </div>
        )}
      </div>
    </div>,
    document.body
  );
}

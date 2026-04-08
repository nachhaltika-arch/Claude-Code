import { useState, useEffect, useRef } from 'react';
import API_BASE_URL from '../config';

const SEITENTYPEN = ['Landing', 'Info', 'Leistung', 'Kontakt', 'Blog', 'Sonstiges'];

const DEFAULT_SEITEN = [
  { id: 1, name: 'Startseite',  typ: 'Landing',  keyword: 'Sanitär Koblenz', order: 1 },
  { id: 2, name: 'Leistungen',  typ: 'Leistung', keyword: '',                order: 2 },
  { id: 3, name: 'Über uns',    typ: 'Info',     keyword: '',                order: 3 },
  { id: 4, name: 'Kontakt',     typ: 'Kontakt',  keyword: '',                order: 4 },
];

export default function SitemapPlaner({ projectId, leadId, token }) {
  const h = {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${token}`,
  };

  const [seiten, setSeiten]         = useState([]);
  const [loading, setLoading]       = useState(true);
  const [saving, setSaving]         = useState(false); // eslint-disable-line
  const [freigabe, setFreigabe]     = useState(null);
  const [requesting, setRequesting] = useState(false);
  const [msg, setMsg]               = useState('');
  const [dragIdx, setDragIdx]       = useState(null);
  const [dragOver, setDragOver]     = useState(null);
  const nextId = useRef(100);

  // ── Daten laden ──────────────────────────────────────────
  useEffect(() => {
    if (!projectId) return;
    setLoading(true);

    const loadBriefingSeiten = async () => {
      if (!leadId) return [];
      try {
        const r = await fetch(
          `${API_BASE_URL}/api/briefings/${leadId}`,
          { headers: h }
        );
        if (!r.ok) return [];
        const data = await r.json();
        const wunsch = data?.inhalte?.wunschseiten || '';
        if (!wunsch) return [];
        const zeilen = wunsch
          .split(/[\n,;]+/)
          .map(s => s.trim())
          .filter(Boolean);
        return zeilen.map((name, i) => ({
          id: nextId.current++,
          name,
          typ: 'Info',
          keyword: '',
          order: i + 1,
        }));
      } catch { return []; }
    };

    const loadSitemap = async () => {
      try {
        const r = await fetch(
          `${API_BASE_URL}/api/projects/${projectId}/sitemap`,
          { headers: h }
        );
        if (!r.ok) return null;
        return await r.json();
      } catch { return null; }
    };

    Promise.all([loadSitemap(), loadBriefingSeiten()])
      .then(([sm, briefingSeiten]) => {
        if (sm && sm.seiten && sm.seiten.length > 0) {
          setSeiten(sm.seiten);
          setFreigabe(sm.sitemap_freigabe || null);
        } else if (briefingSeiten.length > 0) {
          setSeiten(briefingSeiten);
        } else {
          setSeiten(DEFAULT_SEITEN);
        }
      })
      .finally(() => setLoading(false));
  }, [projectId]); // eslint-disable-line

  // ── Auto-Save debounced ──────────────────────────────────
  useEffect(() => {
    if (loading) return;
    const t = setTimeout(() => autoSave(), 1200);
    return () => clearTimeout(t);
  }, [seiten]); // eslint-disable-line

  const autoSave = async () => {
    if (!projectId || saving) return;
    try {
      await fetch(`${API_BASE_URL}/api/projects/${projectId}/sitemap`, {
        method: 'PATCH',
        headers: h,
        body: JSON.stringify({ seiten }),
      });
    } catch {}
  };

  // ── CRUD ─────────────────────────────────────────────────
  const addSeite = () => {
    const id = nextId.current++;
    setSeiten(s => [
      ...s,
      { id, name: 'Neue Seite', typ: 'Info', keyword: '', order: s.length + 1 },
    ]);
  };

  const updateSeite = (id, field, val) =>
    setSeiten(s => s.map(p => p.id === id ? { ...p, [field]: val } : p));

  const deleteSeite = (id) =>
    setSeiten(s => s.filter(p => p.id !== id).map((p, i) => ({ ...p, order: i + 1 })));

  // ── Drag & Drop ──────────────────────────────────────────
  const onDragStart = (idx) => setDragIdx(idx);
  const onDragOver  = (e, idx) => { e.preventDefault(); setDragOver(idx); };
  const onDrop      = (e, idx) => {
    e.preventDefault();
    if (dragIdx === null || dragIdx === idx) return;
    const arr = [...seiten];
    const [moved] = arr.splice(dragIdx, 1);
    arr.splice(idx, 0, moved);
    setSeiten(arr.map((p, i) => ({ ...p, order: i + 1 })));
    setDragIdx(null);
    setDragOver(null);
  };
  const onDragEnd = () => { setDragIdx(null); setDragOver(null); };

  // ── Freigabe anfordern ───────────────────────────────────
  const requestFreigabe = async () => {
    setRequesting(true);
    setMsg('');
    try {
      const r = await fetch(
        `${API_BASE_URL}/api/projects/${projectId}/freigabe`,
        {
          method: 'POST',
          headers: h,
          body: JSON.stringify({
            typ:         'sitemap',
            seiten,
            zeitstempel: new Date().toISOString(),
          }),
        }
      );
      const d = await r.json();
      if (r.ok) {
        setFreigabe(d.sitemap_freigabe);
        setMsg('✓ Freigabe erteilt');
      } else {
        setMsg(d.detail || 'Fehler');
      }
    } catch { setMsg('Verbindungsfehler'); }
    finally { setRequesting(false); }
  };

  // ── Render ───────────────────────────────────────────────
  if (loading) {
    return (
      <div style={{ padding: 20, textAlign: 'center',
                    color: 'var(--text-secondary)', fontSize: 13 }}>
        Sitemap wird geladen…
      </div>
    );
  }

  const TYP_COLORS = {
    Landing:   { bg: '#E6F1FB', color: '#0C447C' },
    Leistung:  { bg: '#EAF3DE', color: '#27500A' },
    Info:      { bg: '#FAEEDA', color: '#633806' },
    Kontakt:   { bg: '#EEEDFE', color: '#3C3489' },
    Blog:      { bg: '#E1F5EE', color: '#085041' },
    Sonstiges: { bg: '#F1EFE8', color: '#444441' },
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

      {/* ── HEADER ── */}
      <div style={{
        display: 'flex', alignItems: 'center',
        justifyContent: 'space-between', flexWrap: 'wrap', gap: 10,
      }}>
        <div>
          <div style={{
            fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)',
            textTransform: 'uppercase', letterSpacing: '.06em', marginBottom: 2,
          }}>
            Sitemap-Planer
          </div>
          <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>
            {seiten.length} Seiten · Änderungen werden automatisch gespeichert
          </div>
        </div>
        <button
          onClick={addSeite}
          style={{
            padding: '7px 14px', borderRadius: 8, border: 'none',
            background: '#008eaa', color: 'white',
            fontSize: 12, fontWeight: 600, cursor: 'pointer',
          }}
        >
          + Seite hinzufügen
        </button>
      </div>

      {/* ── SEITEN-LISTE ── */}
      <div style={{
        background: 'var(--bg-surface)',
        border: '0.5px solid var(--border-light)',
        borderRadius: 12, overflow: 'hidden',
      }}>

        {/* Tabellen-Header */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: '28px 40px 1fr 110px 1fr 32px',
          gap: 8, padding: '8px 14px',
          background: 'var(--bg-app)',
          borderBottom: '0.5px solid var(--border-light)',
          fontSize: 10, fontWeight: 600, color: 'var(--text-tertiary)',
          textTransform: 'uppercase', letterSpacing: '.06em',
        }}>
          <div></div>
          <div>#</div>
          <div>Seitenname</div>
          <div>Typ</div>
          <div>Ziel-Keyword (SEO)</div>
          <div></div>
        </div>

        {seiten.map((seite, idx) => {
          const tc = TYP_COLORS[seite.typ] || TYP_COLORS['Sonstiges'];
          const isDragging = dragIdx === idx;
          const isOver     = dragOver === idx;
          return (
            <div
              key={seite.id}
              draggable
              onDragStart={() => onDragStart(idx)}
              onDragOver={e => onDragOver(e, idx)}
              onDrop={e => onDrop(e, idx)}
              onDragEnd={onDragEnd}
              style={{
                display: 'grid',
                gridTemplateColumns: '28px 40px 1fr 110px 1fr 32px',
                gap: 8, padding: '9px 14px', alignItems: 'center',
                borderBottom: idx < seiten.length - 1
                  ? '0.5px solid var(--border-light)' : 'none',
                background: isOver    ? 'var(--bg-active)'
                           : isDragging ? 'var(--bg-app)'
                           : 'transparent',
                transition: 'background .1s',
                opacity: isDragging ? 0.5 : 1,
                cursor: 'grab',
              }}
            >
              {/* Drag-Handle */}
              <div style={{
                color: 'var(--text-tertiary)', fontSize: 14,
                textAlign: 'center', userSelect: 'none',
              }}>
                ⠿
              </div>

              {/* Reihenfolge */}
              <div style={{
                fontSize: 11, color: 'var(--text-tertiary)',
                textAlign: 'center', fontWeight: 600,
              }}>
                {seite.order}
              </div>

              {/* Name */}
              <input
                value={seite.name}
                onChange={e => updateSeite(seite.id, 'name', e.target.value)}
                onClick={e => e.stopPropagation()}
                onMouseDown={e => e.stopPropagation()}
                draggable={false}
                style={{
                  border: '0.5px solid var(--border-light)',
                  borderRadius: 6, padding: '5px 8px',
                  fontSize: 13, fontFamily: 'inherit',
                  background: 'var(--bg-app)',
                  color: 'var(--text-primary)', outline: 'none',
                  cursor: 'text',
                }}
              />

              {/* Typ */}
              <select
                value={seite.typ}
                onChange={e => updateSeite(seite.id, 'typ', e.target.value)}
                onClick={e => e.stopPropagation()}
                draggable={false}
                style={{
                  border: 'none', borderRadius: 8, padding: '4px 8px',
                  fontSize: 11, fontWeight: 600,
                  background: tc.bg, color: tc.color,
                  cursor: 'pointer', outline: 'none',
                }}
              >
                {SEITENTYPEN.map(t => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>

              {/* Keyword */}
              <input
                value={seite.keyword}
                onChange={e => updateSeite(seite.id, 'keyword', e.target.value)}
                onClick={e => e.stopPropagation()}
                onMouseDown={e => e.stopPropagation()}
                placeholder="z.B. Sanitär Koblenz"
                draggable={false}
                style={{
                  border: '0.5px solid var(--border-light)',
                  borderRadius: 6, padding: '5px 8px',
                  fontSize: 12, fontFamily: 'inherit',
                  background: 'var(--bg-app)',
                  color: 'var(--text-primary)', outline: 'none',
                  cursor: 'text',
                }}
              />

              {/* Löschen */}
              <button
                onClick={() => deleteSeite(seite.id)}
                title="Seite löschen"
                style={{
                  background: 'none', border: 'none',
                  color: 'var(--text-tertiary)', cursor: 'pointer',
                  fontSize: 16, display: 'flex',
                  alignItems: 'center', justifyContent: 'center',
                  borderRadius: 4, padding: 2,
                }}
              >
                ×
              </button>
            </div>
          );
        })}

        {seiten.length === 0 && (
          <div style={{
            padding: 24, textAlign: 'center',
            color: 'var(--text-tertiary)', fontSize: 13,
          }}>
            Noch keine Seiten. Klicke "Seite hinzufügen".
          </div>
        )}
      </div>

      {/* ── FREIGABE-BEREICH ── */}
      <div style={{
        background: 'var(--bg-surface)',
        border: '0.5px solid var(--border-light)',
        borderRadius: 12, padding: '14px 18px',
        display: 'flex', alignItems: 'center',
        justifyContent: 'space-between', flexWrap: 'wrap', gap: 12,
      }}>
        <div>
          <div style={{
            fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)',
            textTransform: 'uppercase', letterSpacing: '.06em', marginBottom: 4,
          }}>
            Digitale Freigabe
          </div>
          {freigabe ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <span style={{
                background: '#EAF3DE', color: '#27500A',
                padding: '2px 10px', borderRadius: 10,
                fontSize: 11, fontWeight: 600,
              }}>
                ✓ Freigegeben
              </span>
              <span style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>
                am {freigabe.replace('T', ' ').slice(0, 16)} Uhr
              </span>
            </div>
          ) : (
            <div style={{
              background: '#FAEEDA', color: '#633806',
              padding: '2px 10px', borderRadius: 10,
              fontSize: 11, fontWeight: 600, display: 'inline-block',
            }}>
              ⏳ Ausstehend
            </div>
          )}
          {msg && (
            <div style={{
              fontSize: 11, marginTop: 6,
              color: msg.startsWith('✓')
                ? 'var(--status-success-text)'
                : 'var(--status-danger-text)',
            }}>
              {msg}
            </div>
          )}
        </div>

        <button
          onClick={requestFreigabe}
          disabled={requesting || seiten.length === 0}
          style={{
            padding: '9px 20px', borderRadius: 8, border: 'none',
            background: requesting ? '#94a3b8'
              : freigabe ? '#1D9E75' : '#008eaa',
            color: 'white', fontSize: 13, fontWeight: 600,
            cursor: requesting ? 'not-allowed' : 'pointer',
          }}
        >
          {requesting
            ? 'Wird übermittelt…'
            : freigabe
            ? '✓ Erneut freigeben'
            : 'Freigabe erteilen'}
        </button>
      </div>

      {/* Hinweis */}
      <div style={{ fontSize: 11, color: 'var(--text-tertiary)', padding: '6px 0' }}>
        Tipp: Zeilen per Drag & Drop neu anordnen. Änderungen werden automatisch gespeichert.
      </div>
    </div>
  );
}

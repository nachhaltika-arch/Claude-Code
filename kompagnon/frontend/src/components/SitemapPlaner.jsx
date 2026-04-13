import { useState, useEffect, useRef } from 'react';
import API_BASE_URL from '../config';

const SEITENTYPEN = ['Landing', 'Info', 'Leistung', 'Kontakt', 'Blog', 'Sonstiges'];

// ── Mapping zwischen Frontend-State und sitemap.py (System A) ───────────────
// Frontend hält intern { id, name, typ, keyword, order }.
// Backend erwartet      { page_name, page_type, ziel_keyword, position }.
const TYP_TO_BACKEND = {
  Landing:   'startseite',
  Info:      'info',
  Leistung:  'leistung',
  Kontakt:   'kontakt',
  Blog:      'blog',
  Sonstiges: 'sonstiges',
};
const BACKEND_TO_TYP = {
  startseite: 'Landing',
  landing:    'Landing',
  info:       'Info',
  leistung:   'Leistung',
  kontakt:    'Kontakt',
  blog:       'Blog',
};
const mapTypToBackend = (typ) => TYP_TO_BACKEND[typ] || 'sonstiges';
const mapTypFromBackend = (pt) => BACKEND_TO_TYP[(pt || '').toLowerCase()] || 'Sonstiges';

const seiteToBackend = (p) => ({
  page_name:    p.name,
  page_type:    mapTypToBackend(p.typ),
  ziel_keyword: p.keyword || '',
  position:     p.order,
});
const seiteFromBackend = (p) => ({
  id:      p.id,
  name:    p.page_name || '',
  typ:     mapTypFromBackend(p.page_type),
  keyword: p.ziel_keyword || '',
  order:   p.position ?? 0,
  ist_pflichtseite: !!p.ist_pflichtseite,
});

// Lokale (noch nicht persistierte) Seiten tragen negative IDs, damit sie
// nicht mit echten sitemap_pages-IDs kollidieren.
const DEFAULT_SEITEN = [
  { id: -1, name: 'Startseite',  typ: 'Landing',  keyword: 'Sanitär Koblenz', order: 1 },
  { id: -2, name: 'Leistungen',  typ: 'Leistung', keyword: '',                order: 2 },
  { id: -3, name: 'Über uns',    typ: 'Info',     keyword: '',                order: 3 },
  { id: -4, name: 'Kontakt',     typ: 'Kontakt',  keyword: '',                order: 4 },
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
  const nextId = useRef(-100);
  const savingRef = useRef(false);

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
        // Bug 3 fix: Briefing speichert wunschseiten flach unter data.wunschseiten;
        // ältere Strukturen hatten data.inhalte.wunschseiten. Beide unterstützen.
        const wunsch = data?.wunschseiten || data?.inhalte?.wunschseiten || '';
        if (!wunsch) return [];
        const zeilen = wunsch
          .split(/[\n,;]+/)
          .map(s => s.trim())
          .filter(Boolean);
        return zeilen.map((name, i) => ({
          id: nextId.current--,
          name,
          typ: 'Info',
          keyword: '',
          order: i + 1,
        }));
      } catch { return []; }
    };

    // Bug 1 fix: Laden kommt jetzt aus sitemap_pages (System A).
    // Das Projekt-Endpoint wird nur noch für den Freigabe-Zeitstempel gebraucht.
    const loadSitemap = async () => {
      try {
        if (!leadId) return { pages: [], freigabe: null };
        const [pagesRes, projectRes] = await Promise.all([
          fetch(`${API_BASE_URL}/api/sitemap/${leadId}`, { headers: h }),
          fetch(`${API_BASE_URL}/api/projects/${projectId}/sitemap`, { headers: h }),
        ]);
        const pages = pagesRes.ok ? await pagesRes.json() : [];
        const proj  = projectRes.ok ? await projectRes.json() : {};
        return {
          pages: Array.isArray(pages) ? pages : [],
          freigabe: proj?.sitemap_freigabe || null,
        };
      } catch { return { pages: [], freigabe: null }; }
    };

    Promise.all([loadSitemap(), loadBriefingSeiten()])
      .then(([sm, briefingSeiten]) => {
        if (sm.pages && sm.pages.length > 0) {
          // Backend → Frontend Feldnamen mappen
          setSeiten(sm.pages.map(seiteFromBackend));
          setFreigabe(sm.freigabe);
        } else if (briefingSeiten.length > 0) {
          setSeiten(briefingSeiten);
        } else {
          setSeiten(DEFAULT_SEITEN);
        }
      })
      .finally(() => setLoading(false));
  }, [projectId, leadId]); // eslint-disable-line

  // ── Auto-Save debounced ──────────────────────────────────
  // `saving` ist in den deps, damit nach Abschluss eines laufenden Saves
  // ein noch ausstehender Edit garantiert einen weiteren Save triggert.
  useEffect(() => {
    if (loading) return;
    if (savingRef.current) return;
    const t = setTimeout(() => autoSave(), 1200);
    return () => clearTimeout(t);
  }, [seiten, saving]); // eslint-disable-line

  // Bug 1 fix: Speichern geht jetzt nach sitemap_pages (System A).
  // sitemap.py hat keinen Bulk-Endpoint, daher diffen wir gegen den
  // aktuellen Server-Stand und feuern POST/PUT/DELETE einzeln.
  const syncToBackend = async () => {
    if (!leadId || savingRef.current) return;
    savingRef.current = true;
    setSaving(true);
    try {
      const r = await fetch(`${API_BASE_URL}/api/sitemap/${leadId}`, { headers: h });
      if (!r.ok) return;
      const serverPages = await r.json();
      const serverById  = new Map(serverPages.map(p => [p.id, p]));
      const localIds    = new Set(seiten.map(p => p.id));

      // 1. DELETE: auf dem Server, aber nicht mehr lokal. Pflichtseiten
      //    (ist_pflichtseite = true) ueberspringen — das Backend blockt sie
      //    ohnehin mit 403.
      for (const sp of serverPages) {
        if (sp.ist_pflichtseite) continue;
        if (!localIds.has(sp.id)) {
          await fetch(`${API_BASE_URL}/api/sitemap/pages/${sp.id}`, {
            method: 'DELETE',
            headers: h,
          });
        }
      }

      // 2. PUT: bekannte Seiten aktualisieren. Pflichtseiten ueberspringen,
      //    da das Backend alle strukturellen Felder (page_name, page_type,
      //    ziel_keyword, position) fuer Pflichtseiten ohnehin filtert.
      for (const p of seiten) {
        if (p.ist_pflichtseite) continue;
        if (serverById.has(p.id)) {
          await fetch(`${API_BASE_URL}/api/sitemap/pages/${p.id}`, {
            method: 'PUT',
            headers: h,
            body: JSON.stringify(seiteToBackend(p)),
          });
        }
      }

      // 3. POST: neue Seiten (negative Temp-IDs). Server gibt echte ID
      //    zurueck; wir mappen sie lokal.
      const idMap = {};
      for (const p of seiten) {
        if (!serverById.has(p.id)) {
          const cr = await fetch(`${API_BASE_URL}/api/sitemap/${leadId}/pages`, {
            method: 'POST',
            headers: h,
            body: JSON.stringify(seiteToBackend(p)),
          });
          if (cr.ok) {
            const created = await cr.json();
            idMap[p.id] = created.id;
          }
        }
      }

      if (Object.keys(idMap).length > 0) {
        setSeiten(s => s.map(p => (idMap[p.id] ? { ...p, id: idMap[p.id] } : p)));
      }
    } catch {}
    finally {
      savingRef.current = false;
      setSaving(false);
    }
  };

  const autoSave = syncToBackend;

  // ── CRUD ─────────────────────────────────────────────────
  const addSeite = () => {
    const id = nextId.current--;
    setSeiten(s => [
      ...s,
      { id, name: 'Neue Seite', typ: 'Info', keyword: '', order: s.length + 1 },
    ]);
  };

  const updateSeite = (id, field, val) =>
    setSeiten(s => s.map(p => {
      if (p.id !== id) return p;
      if (p.ist_pflichtseite) return p; // Pflichtseiten sind read-only
      return { ...p, [field]: val };
    }));

  const deleteSeite = (id) =>
    setSeiten(s => {
      const target = s.find(p => p.id === id);
      if (target?.ist_pflichtseite) return s; // Pflichtseiten nicht loeschbar
      return s.filter(p => p.id !== id).map((p, i) => ({ ...p, order: i + 1 }));
    });

  // ── Drag & Drop ──────────────────────────────────────────
  // Pflichtseiten sind per Drag weder Quelle noch Ziel — ihre Position ist
  // im Backend festgelegt (90-93) und wuerde ohnehin ignoriert.
  const onDragStart = (idx) => {
    if (seiten[idx]?.ist_pflichtseite) return;
    setDragIdx(idx);
  };
  const onDragOver  = (e, idx) => {
    if (seiten[idx]?.ist_pflichtseite) return;
    e.preventDefault();
    setDragOver(idx);
  };
  const onDrop      = (e, idx) => {
    e.preventDefault();
    if (dragIdx === null || dragIdx === idx) return;
    if (seiten[idx]?.ist_pflichtseite || seiten[dragIdx]?.ist_pflichtseite) {
      setDragIdx(null); setDragOver(null); return;
    }
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
      // Bug 1 fix: Zuerst nach sitemap_pages synchronisieren,
      // damit der Freigabestand mit dem tatsaechlich persistierten
      // Inhalt uebereinstimmt. Das Projekt-Endpoint liefert danach
      // nur noch den Freigabe-Zeitstempel.
      await syncToBackend();

      const r = await fetch(
        `${API_BASE_URL}/api/projects/${projectId}/freigabe`,
        {
          method: 'POST',
          headers: h,
          body: JSON.stringify({
            typ:         'sitemap',
            seiten:      [],
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
          const isPflicht  = !!seite.ist_pflichtseite;
          const lockedInput = {
            border: '0.5px solid var(--border-light)',
            borderRadius: 6, padding: '5px 8px',
            fontSize: 13, fontFamily: 'inherit',
            background: 'var(--bg-app)',
            color: isPflicht ? 'var(--text-tertiary)' : 'var(--text-primary)',
            outline: 'none',
            cursor: isPflicht ? 'not-allowed' : 'text',
          };
          return (
            <div
              key={seite.id}
              draggable={!isPflicht}
              onDragStart={() => onDragStart(idx)}
              onDragOver={e => onDragOver(e, idx)}
              onDrop={e => onDrop(e, idx)}
              onDragEnd={onDragEnd}
              title={isPflicht ? 'Pflichtseite — gesetzlich vorgeschrieben, nicht editierbar' : undefined}
              style={{
                display: 'grid',
                gridTemplateColumns: '28px 40px 1fr 110px 1fr 32px',
                gap: 8, padding: '9px 14px', alignItems: 'center',
                borderBottom: idx < seiten.length - 1
                  ? '0.5px solid var(--border-light)' : 'none',
                background: isOver    ? 'var(--bg-active)'
                           : isDragging ? 'var(--bg-app)'
                           : isPflicht  ? 'var(--bg-app)'
                           : 'transparent',
                transition: 'background .1s',
                opacity: isDragging ? 0.5 : isPflicht ? 0.75 : 1,
                cursor: isPflicht ? 'default' : 'grab',
              }}
            >
              {/* Drag-Handle bzw. Lock-Icon */}
              <div style={{
                color: 'var(--text-tertiary)', fontSize: 14,
                textAlign: 'center', userSelect: 'none',
              }}>
                {isPflicht ? '🔒' : '⠿'}
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
                readOnly={isPflicht}
                style={lockedInput}
              />

              {/* Typ */}
              <select
                value={seite.typ}
                onChange={e => updateSeite(seite.id, 'typ', e.target.value)}
                onClick={e => e.stopPropagation()}
                draggable={false}
                disabled={isPflicht}
                style={{
                  border: 'none', borderRadius: 8, padding: '4px 8px',
                  fontSize: 11, fontWeight: 600,
                  background: tc.bg, color: tc.color,
                  cursor: isPflicht ? 'not-allowed' : 'pointer',
                  outline: 'none',
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
                placeholder={isPflicht ? '' : 'z.B. Sanitär Koblenz'}
                draggable={false}
                readOnly={isPflicht}
                style={{ ...lockedInput, fontSize: 12 }}
              />

              {/* Löschen — fuer Pflichtseiten ausgeblendet */}
              {isPflicht ? (
                <div />
              ) : (
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
              )}
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

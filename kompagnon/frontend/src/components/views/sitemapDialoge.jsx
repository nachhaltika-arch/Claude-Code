/**
 * Detailfeld und die zwei Dialoge der Sitemap-Ansicht (L-25).
 *
 * Am 2026-08-30 aus `SitemapViewV2.jsx` herausgeloest — 316 Zeilen. Die
 * beiden Dialoge haben am selben Tag ihren Escape-Weg bekommen (L-17).
 */
import { useEffect, useState } from 'react';
import { useEscapeKey } from '../../hooks/useKeyboardShortcuts';
import {
  KC_DARK, KC_MID, PAGE_TYPE_OPTIONS, SECTION_CATALOG,
} from './sitemapDaten';

export function PageDetailPanel({ page, onClose, onSave, onDelete }) {
  const [form, setForm] = useState(() => ({
    page_name: page?.page_name || '',
    page_type: page?.page_type || 'info',
    status:    page?.status    || 'geplant',
    ai_prompt: page?.ai_prompt || '',
  }));
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setForm({
      page_name: page?.page_name || '',
      page_type: page?.page_type || 'info',
      status:    page?.status    || 'geplant',
      ai_prompt: page?.ai_prompt || '',
    });
  }, [page?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  if (!page) return null;
  const isPflicht = !!page.ist_pflichtseite;

  const handleSave = async () => {
    setSaving(true);
    await onSave(form);
    setSaving(false);
  };

  return (
    <aside style={{
      width: 340, flexShrink: 0,
      background: '#fff',
      borderLeft: '1px solid var(--border-light)',
      display: 'flex', flexDirection: 'column',
      overflow: 'hidden',
    }}>
      <div style={{
        padding: '10px 14px', borderBottom: '1px solid var(--border-light)',
        background: 'var(--bg-app)',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      }}>
        <div style={{ fontSize: 13, fontWeight: 800, color: KC_DARK }}>
          Seiten-Details
        </div>
        <button aria-label="Schließen" type="button" onClick={onClose}
          style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: 16, color: 'var(--text-secondary)', padding: 0 }}>×</button>
      </div>
      <div style={{ flex: 1, overflowY: 'auto', padding: 14, display: 'flex', flexDirection: 'column', gap: 12 }}>
        {isPflicht && (
          <div style={{ fontSize: 12, color: '#92400E', background: '#FEF3C7', padding: '6px 8px', borderRadius: 6 }}>
            🔒 Pflichtseite — Name / Type sind gesperrt.
          </div>
        )}
        <div>
          <label style={lblStyle}>Page-Name</label>
          <input aria-label="Page-Name" type="text" value={form.page_name} disabled={isPflicht}
            onChange={(e) => setForm((f) => ({ ...f, page_name: e.target.value }))}
            style={inpStyle(isPflicht)} />
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
          <div>
            <label style={lblStyle}>Type</label>
            <select aria-label="Type" value={form.page_type} disabled={isPflicht}
              onChange={(e) => setForm((f) => ({ ...f, page_type: e.target.value }))}
              style={{ ...inpStyle(isPflicht), cursor: isPflicht ? 'not-allowed' : 'pointer' }}>
              {PAGE_TYPE_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
            </select>
          </div>
          <div>
            <label style={lblStyle}>Status</label>
            <select aria-label="Status" value={form.status}
              onChange={(e) => setForm((f) => ({ ...f, status: e.target.value }))}
              style={{ ...inpStyle(false), cursor: 'pointer' }}>
              <option value="geplant">Geplant</option>
              <option value="in_bearbeitung">In Bearbeitung</option>
              <option value="freigegeben">Freigegeben</option>
              <option value="live">Live</option>
            </select>
          </div>
        </div>
        <div>
          <label style={lblStyle}>KI-Anweisung (optional)</label>
          <textarea aria-label="KI-Anweisung (optional)" value={form.ai_prompt}
            onChange={(e) => setForm((f) => ({ ...f, ai_prompt: e.target.value }))}
            placeholder="Goal / Per-Page-Kontext für KI-Generator"
            rows={4}
            style={{ ...inpStyle(false), resize: 'vertical', fontFamily: 'inherit', minHeight: 70 }} />
        </div>
      </div>
      <div style={{
        padding: '10px 14px', borderTop: '1px solid var(--border-light)',
        background: 'var(--bg-app)',
        display: 'flex', justifyContent: 'space-between', gap: 8,
      }}>
        <button type="button" onClick={onDelete}
          disabled={isPflicht}
          style={{
            padding: '8px 12px',
            background: '#fff', border: `1px solid ${isPflicht ? 'var(--border-medium)' : '#fca5a5'}`,
            color: isPflicht ? 'var(--border-medium)' : '#dc2626',
            borderRadius: 6, fontSize: 12,
            cursor: isPflicht ? 'not-allowed' : 'pointer',
          }}>
          🗑 Löschen
        </button>
        <div style={{ display: 'flex', gap: 6 }}>
          <button type="button" onClick={onClose}
            style={{ padding: '8px 12px', background: '#fff', border: '1px solid var(--border-light)', borderRadius: 6, fontSize: 12, color: 'var(--text-secondary)', cursor: 'pointer' }}>
            Abbrechen
          </button>
          <button type="button" onClick={handleSave} disabled={saving}
            style={{ padding: '8px 14px', background: KC_DARK, opacity: saving ? 0.5 : 1, color: '#fff', border: 'none', borderRadius: 6, fontSize: 12, fontWeight: 700, cursor: saving ? 'wait' : 'pointer' }}>
            {saving ? 'Speichert…' : '✓ Speichern'}
          </button>
        </div>
      </div>
    </aside>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Add-Page-Dialog (Modal)
// ─────────────────────────────────────────────────────────────────────────────

export function AddPageDialog({ parentId, parentName, onClose, onSubmit }) {
  // **Escape schliesst — WCAG 2.1.1 (30.08.2026, L-17).** Der Hintergrund
  // reagiert auf einen Klick; mit der Tastatur gab es keinen Weg heraus.
  // `role="button"` waere hier falsch: Eine Ueberlagerung ist keine
  // Schaltflaeche, sie ist der Weg zurueck.
  useEscapeKey(onClose);

  const [name, setName] = useState('');
  const [pageType, setPageType] = useState('info');
  const [busy, setBusy] = useState(false);

  const handleSubmit = async (e) => {
    if (e?.preventDefault) e.preventDefault();
    if (!name.trim() || busy) return;
    setBusy(true);
    await onSubmit(name, pageType);
    setBusy(false);
  };

  return (
    <div onClick={(e) => e.target === e.currentTarget && onClose()} style={{
      position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)',
      zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 16,
    }}>
      <form onSubmit={handleSubmit} style={{
        background: '#fff', borderRadius: 12, padding: 20,
        width: '100%', maxWidth: 420, boxShadow: '0 8px 40px rgba(0,0,0,0.18)',
      }}>
        <h3 style={{ margin: '0 0 4px', fontSize: 15, fontWeight: 700, color: KC_DARK }}>
          Neue Seite anlegen
        </h3>
        <p style={{ margin: '0 0 14px', fontSize: 12, color: 'var(--text-secondary)' }}>
          {parentId
            ? `Wird als Sub-Seite von „${parentName}" angelegt.`
            : 'Wird als Top-Level-Seite angelegt.'}
        </p>
        <div style={{ marginBottom: 10 }}>
          <label style={lblStyle}>Seitenname *</label>
          <input aria-label="Seitenname" type="text" value={name} onChange={(e) => setName(e.target.value)}
            placeholder="z.B. Wallbox-Installation"
            style={inpStyle(false)} autoFocus />
        </div>
        <div style={{ marginBottom: 16 }}>
          <label style={lblStyle}>Page-Type</label>
          <select aria-label="Page-Type" value={pageType} onChange={(e) => setPageType(e.target.value)}
            style={{ ...inpStyle(false), cursor: 'pointer' }}>
            {PAGE_TYPE_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
        </div>
        <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
          <button type="button" onClick={onClose}
            style={{ padding: '8px 14px', background: '#fff', border: '1px solid var(--border-light)', borderRadius: 8, fontSize: 12, cursor: 'pointer', color: 'var(--text-secondary)' }}>
            Abbrechen
          </button>
          <button type="submit" disabled={!name.trim() || busy}
            style={{ padding: '8px 18px', background: KC_MID, opacity: !name.trim() || busy ? 0.5 : 1, color: '#fff', border: 'none', borderRadius: 8, fontSize: 12, fontWeight: 700, cursor: !name.trim() || busy ? 'not-allowed' : 'pointer' }}>
            {busy ? 'Anlegen…' : '+ Anlegen'}
          </button>
        </div>
      </form>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Add-Section-Dialog (Modal mit Section-Catalog)
// ─────────────────────────────────────────────────────────────────────────────

export function AddSectionDialog({ existingSections, onClose, onPick }) {
  // **Escape schliesst — WCAG 2.1.1 (30.08.2026, L-17).** Der Hintergrund
  // reagiert auf einen Klick; mit der Tastatur gab es keinen Weg heraus.
  // `role="button"` waere hier falsch: Eine Ueberlagerung ist keine
  // Schaltflaeche, sie ist der Weg zurueck.
  useEscapeKey(onClose);

  const [search, setSearch] = useState('');
  const all = Object.keys(SECTION_CATALOG);
  const used = new Set(existingSections);
  const filtered = all.filter((key) => {
    const q = search.trim().toLowerCase();
    if (!q) return true;
    return key.toLowerCase().includes(q) || SECTION_CATALOG[key].toLowerCase().includes(q);
  });

  return (
    <div onClick={(e) => e.target === e.currentTarget && onClose()} style={{
      position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)',
      zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 16,
    }}>
      <div style={{
        background: '#fff', borderRadius: 12,
        width: '100%', maxWidth: 520, maxHeight: 'calc(100vh - 32px)',
        display: 'flex', flexDirection: 'column', overflow: 'hidden',
        boxShadow: '0 8px 40px rgba(0,0,0,0.18)',
      }}>
        <div style={{
          padding: '14px 18px', borderBottom: '1px solid var(--border-light)',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        }}>
          <h3 style={{ margin: 0, fontSize: 15, fontWeight: 700, color: KC_DARK }}>
            Section auswählen
          </h3>
          <button aria-label="Schließen" type="button" onClick={onClose}
            style={{ background: 'none', border: 'none', fontSize: 18, cursor: 'pointer', color: 'var(--text-secondary)' }}>×</button>
        </div>
        <div style={{ padding: '12px 18px', borderBottom: '1px solid var(--border-light)' }}>
          <input aria-label="Suchen…" type="search" placeholder="Suchen…"
            value={search} onChange={(e) => setSearch(e.target.value)}
            style={inpStyle(false)} autoFocus />
        </div>
        <div style={{ flex: 1, overflowY: 'auto', padding: 8 }}>
          {filtered.length === 0 ? (
            <div style={{ padding: 20, textAlign: 'center', color: 'var(--text-tertiary)', fontSize: 12, fontStyle: 'italic' }}>
              Kein Treffer für „{search}".
            </div>
          ) : (
            filtered.map((key) => {
              const isUsed = used.has(key);
              return (
                <button
                  key={key} type="button"
                  onClick={() => onPick(key)}
                  style={{
                    display: 'flex', flexDirection: 'column', alignItems: 'flex-start', gap: 2,
                    width: '100%', padding: '8px 10px', marginBottom: 4,
                    background: '#fff', border: '1px solid var(--border-light)', borderRadius: 6,
                    cursor: 'pointer', textAlign: 'left', fontFamily: 'inherit',
                  }}
                  onMouseEnter={(e) => { e.currentTarget.style.background = '#eff6ff'; e.currentTarget.style.borderColor = KC_MID; }}
                  onMouseLeave={(e) => { e.currentTarget.style.background = '#fff'; e.currentTarget.style.borderColor = 'var(--border-light)'; }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, width: '100%' }}>
                    <code style={{ color: KC_MID, fontWeight: 700, fontSize: 12 }}>{key}</code>
                    <span style={{ flex: 1 }} />
                    {isUsed && (
                      <span style={{ fontSize: 9, color: 'var(--text-secondary)', background: 'var(--surface)', padding: '1px 6px', borderRadius: 4 }}>
                        bereits verwendet
                      </span>
                    )}
                  </div>
                  <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.4 }}>
                    {SECTION_CATALOG[key]}
                  </div>
                </button>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Shared styles
// ─────────────────────────────────────────────────────────────────────────────

const lblStyle = {
  display: 'block', fontSize: 12, fontWeight: 700,
  color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.06em',
  marginBottom: 4,
};
const inpStyle = (disabled) => ({
  width: '100%', boxSizing: 'border-box', padding: '7px 10px',
  border: '1px solid var(--border-light)', borderRadius: 6,
  background: disabled ? 'var(--bg-app)' : '#fff',
  color: disabled ? 'var(--text-tertiary)' : '#1A2C32',
  fontSize: 12, fontFamily: 'inherit', outline: 'none',
});

// Doc: max 1 Primary (Gelb) pro Screen für die wichtigste Aktion.

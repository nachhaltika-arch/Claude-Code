/**
 * Stile, Abzeichen und der Sortierhaken der Kursverwaltung (L-25).
 *
 * Am 2026-08-30 aus `AcademyAdminCourse.jsx` herausgeloest. **Diese Datei ging
 * mit den Bausteinen**, weil beide Seiten sie brauchen — die Seite nennt `S`
 * dreizehn Mal, die Bausteine ebenso.
 */
import { useRef, useState } from 'react';

export const S = {
  input: {
    width: '100%', padding: '9px 12px',
    border: '1px solid var(--border-medium)',
    borderRadius: 'var(--radius-md)', fontSize: 13,
    fontFamily: 'var(--font-sans)', color: 'var(--text-primary)',
    background: 'var(--bg-surface)', outline: 'none', boxSizing: 'border-box',
    transition: 'border-color 0.15s',
  },
  label: {
    display: 'block', fontSize: 12, fontWeight: 600,
    color: 'var(--text-tertiary)', textTransform: 'uppercase',
    letterSpacing: '0.06em', marginBottom: 5,
  },
  card: {
    background: 'var(--bg-surface)', border: '1px solid var(--border-light)',
    borderRadius: 'var(--radius-lg)', overflow: 'hidden',
  },
  cardHeader: {
    padding: '14px 20px', borderBottom: '1px solid var(--border-light)',
    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
  },
  cardBody: { padding: '20px', display: 'flex', flexDirection: 'column', gap: 16 },
};

export const TYPE_BADGE = {
  video:     { bg: 'var(--status-info-bg)',    color: 'var(--status-info-text)',    label: 'VIDEO' },
  text:      { bg: 'var(--status-neutral-bg)', color: 'var(--status-neutral-text)', label: 'TEXT' },
  quiz:      { bg: 'var(--status-warning-bg)', color: 'var(--status-warning-text)', label: 'QUIZ' },
  checklist: { bg: 'var(--status-success-bg)', color: 'var(--status-success-text)', label: 'LISTE' },
};

export function useDragSort(items, setItems, onReorder) {
  const from = useRef(null);
  const over = useRef(null);
  const [active, setActive] = useState(false);

  const handlers = (idx) => ({
    draggable: true,
    onDragStart: () => { from.current = idx; setActive(true); },
    onDragEnter: () => { over.current = idx; },
    onDragOver:  (e) => e.preventDefault(),
    onDragEnd:   async () => {
      setActive(false);
      const f = from.current; const t = over.current;
      from.current = null; over.current = null;
      if (f === null || t === null || f === t) return;
      const next = [...items];
      const [moved] = next.splice(f, 1);
      next.splice(t, 0, moved);
      setItems(next);
      if (onReorder) await onReorder(next);
    },
  });

  return { handlers, active, overIdx: over };
}

export const AUDIENCE_LABEL = {
  employee: 'Für Mitarbeiter',
  customer: 'Für Kunden',
  both:     'Für alle',
};

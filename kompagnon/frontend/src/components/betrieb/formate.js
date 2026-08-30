/**
 * Farben und Formate der Betriebsansicht (L-25).
 *
 * Am 2026-08-30 aus `CustomerDetail.jsx` herausgeloest — die Datei trug 2.512
 * Zeilen und darin fuenf eigenstaendige Abschnitte plus ihre Helfer.
 *
 * **Warum die Helfer zuerst gingen:** Drei der fuenf Abschnitte brauchen sie.
 * Blieben sie bei einem, muessten die anderen ihren Nachbarn importieren.
 */
export function scoreColor(score) {
  if (score === null || score === undefined) return { bg: 'var(--status-neutral-bg)', text: 'var(--status-neutral-text)' };
  if (score >= 90) return { bg: 'var(--status-success-bg)', text: 'var(--status-success-text)' };
  if (score >= 50) return { bg: 'var(--status-warning-bg)', text: 'var(--status-warning-text)' };
  return { bg: 'var(--status-danger-bg)', text: 'var(--status-danger-text)' };
}

export function vitalColor(key, raw) {
  if (raw === null || raw === undefined) return { bg: 'var(--status-neutral-bg)', text: 'var(--status-neutral-text)' };
  const thresholds = {
    lcp: [2500, 4000],
    cls: [0.1, 0.25],
    inp: [200, 500],
    fcp: [1800, 3000],
  };
  const [good, poor] = thresholds[key];
  if (raw < good) return { bg: 'var(--status-success-bg)', text: 'var(--status-success-text)' };
  if (raw < poor) return { bg: 'var(--status-warning-bg)', text: 'var(--status-warning-text)' };
  return { bg: 'var(--status-danger-bg)', text: 'var(--status-danger-text)' };
}

export function fmtVital(key, raw) {
  if (raw === null || raw === undefined) return '—';
  if (key === 'cls') return raw.toFixed(3);
  return (raw / 1000).toFixed(2) + ' s';
}

export function fmtTs(iso) {
  if (!iso) return null;
  const d = new Date(iso);
  return d.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' })
    + ' ' + d.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' }) + ' Uhr';
}

// ── Audit History section component ───────────────────────────


/**
 * Gemeinsame Bausteine des Betriebsblatts (L-25).
 *
 * Farbtabellen, die Punktfarbe und die zwei Abzeichen. Am 2026-08-30 aus
 * `LeadProfile.jsx` herausgeloest — **zuerst**, weil Seite und Reiter sie
 * gleichermassen brauchen. Blieben sie bei der Seite, muesste jeder Reiter
 * seine Seite importieren, und ein Ringschluss waere nur eine Frage der Zeit.
 */
import { datumKurz } from '../../utils/datum';

export const scoreColor = (s) =>
  s >= 70 ? 'var(--status-success-text)'
  : s >= 50 ? 'var(--status-warning-text)'
  : 'var(--status-danger-text)';


export const DomainBadge = ({ reachable, checkedAt, loading, onCheck }) => {
  if (loading) return <span style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>⏳ Prüfe...</span>;
  const date = checkedAt ? datumKurz(checkedAt, '') : '';
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
      <span style={{ padding: '2px 8px', borderRadius: 12, fontSize: 11, fontWeight: 600, background: reachable === null ? 'var(--status-neutral-bg)' : reachable ? 'var(--status-success-bg)' : 'var(--status-danger-bg)', color: reachable === null ? 'var(--status-neutral-text)' : reachable ? 'var(--status-success-text)' : 'var(--status-danger-text)' }}>
        {reachable === null ? '● Nicht geprüft' : reachable ? '✓ Erreichbar' : '✗ Nicht erreichbar'}
      </span>
      {date && <span style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>{date}</span>}
      <button onClick={onCheck} title="Jetzt prüfen" style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: 12, color: 'var(--text-tertiary)', padding: '0 2px' }}>🔄</button>
    </span>
  );
};


export const LEVEL_COLORS = {
  'Homepage Standard Platin': 'var(--status-info-text)',
  'Homepage Standard Gold':   '#b8860b',
  'Homepage Standard Silber': 'var(--text-tertiary)',
  'Homepage Standard Bronze': '#cd7f32',
  'Nicht konform':            'var(--status-danger-text)',
};


export const GbpBadge = ({ lead }) => {
  if (!lead) return null;

  const claimed = lead.gbp_claimed;
  const rating  = lead.gbp_rating;
  const total   = lead.gbp_ratings_total;

  if (lead.gbp_checked_at === undefined || lead.gbp_checked_at === null) {
    return (
      <span style={{
        display: 'inline-flex', alignItems: 'center', gap: 5,
        padding: '3px 10px', borderRadius: 12, fontSize: 11,
        fontWeight: 500, background: '#F1EFE8', color: '#5F5E5A',
        border: '0.5px solid #D3D1C7',
      }}>
        <span>📍</span> Google Business: Nicht geprüft
      </span>
    );
  }

  if (!claimed) {
    return (
      <span
        title="Kein Google Business Profil gefunden — starkes Verkaufsargument!"
        style={{
          display: 'inline-flex', alignItems: 'center', gap: 5,
          padding: '3px 10px', borderRadius: 12, fontSize: 11,
          fontWeight: 600, background: '#FCEBEB', color: '#A32D2D',
          border: '0.5px solid #F09595', cursor: 'default',
        }}
      >
        <span>⚠</span> Google Business: Nicht eingetragen
      </span>
    );
  }

  const stars = rating ? `⭐ ${rating.toFixed(1)}` : '✓';
  const count = total  ? ` (${total} Bewertungen)` : '';

  return (
    <span
      title={`Google Place ID: ${lead.gbp_place_id || '—'}`}
      style={{
        display: 'inline-flex', alignItems: 'center', gap: 5,
        padding: '3px 10px', borderRadius: 12, fontSize: 11,
        fontWeight: 600, background: '#EAF3DE', color: '#27500A',
        border: '0.5px solid #97C459', cursor: 'default',
      }}
    >
      {stars} Google Business{count}
    </span>
  );
};



export const STATUS_MAP = {
  new: ['neutral', 'Neu'],
  contacted: ['info', 'Kontaktiert'],
  qualified: ['success', 'Qualifiziert'],
  proposal_sent: ['warning', 'Angebot gesendet'],
  won: ['success', 'Gewonnen'],
  lost: ['danger', 'Verloren'],
};


export const MAIL_STOERUNGEN = {
  hard_bounce:   { text: 'dauerhaft unzustellbar', dauerhaft: true },
  blocked:       { text: 'vom Empfänger abgewiesen', dauerhaft: true },
  invalid_email: { text: 'Adresse unbrauchbar', dauerhaft: true },
  spam:          { text: 'als Spam gemeldet', dauerhaft: true },
  soft_bounce:   { text: 'vorübergehend nicht zustellbar', dauerhaft: false },
  error:         { text: 'Fehler beim Versand', dauerhaft: false },
};


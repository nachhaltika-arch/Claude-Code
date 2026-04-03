import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

// ── Dummy data ─────────────────────────────────────────────────

const PROJECT = {
  name: 'Homepage Eisistcool.de',
  status: 'In Bearbeitung',
};

const PHASES = [
  {
    number: 1,
    label: 'Kickoff & Strategie',
    description: 'Ziele, Zielgruppe und Sitemap definiert',
    done: 5, total: 5,
    state: 'done',
  },
  {
    number: 2,
    label: 'Texterstellung',
    description: 'Alle Seiteninhalte verfasst und freigegeben',
    done: 8, total: 8,
    state: 'done',
  },
  {
    number: 3,
    label: 'Design & Mockup',
    description: 'Startseite & Unterseiten im Design-Tool',
    done: 3, total: 5,
    state: 'active',
  },
  {
    number: 4,
    label: 'Entwicklung',
    description: 'Technische Umsetzung im CMS',
    done: 0, total: 10,
    state: 'locked',
  },
  {
    number: 5,
    label: 'SEO & GEO-Optimierung',
    description: 'Meta-Tags, Ladezeit, lokale Sichtbarkeit',
    done: 0, total: 6,
    state: 'locked',
  },
  {
    number: 6,
    label: 'Review & Freigabe',
    description: 'Gemeinsame Abnahme aller Seiten',
    done: 0, total: 4,
    state: 'locked',
  },
  {
    number: 7,
    label: 'Go-live & Übergabe',
    description: 'Domain live schalten, Einweisung, Support',
    done: 0, total: 3,
    state: 'locked',
  },
];

// ── Sub-components ─────────────────────────────────────────────

function StatusBadge({ label }) {
  return (
    <span style={{
      display: 'inline-block',
      padding: '3px 10px',
      borderRadius: 99,
      fontSize: 12,
      fontWeight: 600,
      background: 'var(--status-warning-bg)',
      color: 'var(--status-warning-text)',
    }}>
      {label}
    </span>
  );
}

function PhaseCard({ phase, isLast }) {
  const isActive = phase.state === 'active';
  const isDone   = phase.state === 'done';
  const isLocked = phase.state === 'locked';
  const pct = phase.total > 0 ? Math.round((phase.done / phase.total) * 100) : 0;

  const icon = isDone ? '✅' : isActive ? '⚙️' : '🔒';

  const barColor = isDone
    ? 'var(--status-success-text)'
    : isActive
    ? 'var(--brand-primary)'
    : 'var(--border-medium)';

  return (
    <div style={{ display: 'flex', gap: 0 }}>
      {/* Timeline spine */}
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: 40, flexShrink: 0 }}>
        <div style={{
          width: 36, height: 36, borderRadius: '50%',
          background: isDone ? 'var(--status-success-bg)' : isActive ? 'var(--brand-primary-light, #e0f4f8)' : 'var(--bg-app)',
          border: isActive ? '2px solid var(--brand-primary)' : isDone ? '2px solid var(--status-success-text)' : '2px solid var(--border-light)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 16, flexShrink: 0,
          zIndex: 1,
        }}>
          {icon}
        </div>
        {!isLast && (
          <div style={{
            width: 2, flex: 1, minHeight: 24,
            background: isDone ? 'var(--status-success-text)' : 'var(--border-light)',
            margin: '4px 0',
            opacity: isDone ? 0.4 : 0.2,
          }} />
        )}
      </div>

      {/* Card body */}
      <div style={{
        flex: 1, marginLeft: 14,
        marginBottom: isLast ? 0 : 12,
        padding: '14px 16px',
        background: isActive ? 'var(--bg-surface)' : 'var(--bg-app)',
        border: isActive
          ? '2px solid var(--brand-primary)'
          : '1px solid var(--border-light)',
        borderRadius: 'var(--radius-lg)',
        boxShadow: isActive ? '0 0 0 3px var(--brand-primary-light, rgba(0,142,170,0.08))' : 'none',
        opacity: isLocked ? 0.55 : 1,
        transition: 'box-shadow 0.2s',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8, marginBottom: 4 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
              Phase {phase.number}
            </span>
            {isActive && (
              <span style={{ fontSize: 10, fontWeight: 600, background: 'var(--brand-primary)', color: '#fff', borderRadius: 99, padding: '1px 7px' }}>
                Aktiv
              </span>
            )}
          </div>
          {!isLocked && (
            <span style={{ fontSize: 12, fontWeight: 600, color: isDone ? 'var(--status-success-text)' : 'var(--brand-primary)' }}>
              {isDone ? 'Abgeschlossen' : `${pct}%`}
            </span>
          )}
        </div>

        <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 3 }}>
          {phase.label}
        </div>
        <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: isLocked ? 0 : 10 }}>
          {phase.description}
        </div>

        {!isLocked && (
          <>
            <div style={{ height: 6, background: 'var(--border-light)', borderRadius: 3, overflow: 'hidden' }}>
              <div style={{
                height: '100%', width: `${pct}%`,
                background: barColor,
                borderRadius: 3,
                transition: 'width 0.6s ease',
              }} />
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 4 }}>
              {phase.done} von {phase.total} Schritten erledigt
            </div>
          </>
        )}
      </div>
    </div>
  );
}

// ── Main page ──────────────────────────────────────────────────

export default function KundenPortal() {
  const { user } = useAuth();
  const navigate = useNavigate();

  if (user?.role !== 'kunde') {
    return (
      <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-tertiary)' }}>
        Diese Seite ist nur für Kunden zugänglich.
      </div>
    );
  }

  const activePhase = PHASES.find(p => p.state === 'active');
  const overallDone  = PHASES.filter(p => p.state === 'done').length;

  return (
    <div style={{ maxWidth: 640, margin: '0 auto', padding: '0 0 40px' }}>

      {/* ── Header ── */}
      <div style={{ marginBottom: 28 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
          <h1 style={{ fontSize: 22, fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
            Mein Projekt
          </h1>
          <StatusBadge label={PROJECT.status} />
        </div>
        <div style={{ fontSize: 14, color: 'var(--text-secondary)', marginTop: 4 }}>
          {PROJECT.name}
        </div>
        <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginTop: 8 }}>
          {overallDone} von {PHASES.length} Phasen abgeschlossen
          {activePhase && ` · Aktiv: Phase ${activePhase.number} – ${activePhase.label}`}
        </div>
      </div>

      {/* ── Overall progress bar ── */}
      <div style={{ marginBottom: 32, background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', padding: '14px 18px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, color: 'var(--text-secondary)', marginBottom: 8 }}>
          <span style={{ fontWeight: 600 }}>Gesamtfortschritt</span>
          <span style={{ fontWeight: 600, color: 'var(--brand-primary)' }}>{Math.round((overallDone / PHASES.length) * 100)}%</span>
        </div>
        <div style={{ height: 8, background: 'var(--border-light)', borderRadius: 4, overflow: 'hidden' }}>
          <div style={{
            height: '100%',
            width: `${(overallDone / PHASES.length) * 100}%`,
            background: 'var(--brand-primary)',
            borderRadius: 4,
            transition: 'width 0.8s ease',
          }} />
        </div>
        <div style={{ display: 'flex', gap: 16, marginTop: 10, flexWrap: 'wrap' }}>
          {[
            { label: 'Abgeschlossen', count: PHASES.filter(p => p.state === 'done').length,   color: 'var(--status-success-text)' },
            { label: 'In Arbeit',     count: PHASES.filter(p => p.state === 'active').length, color: 'var(--brand-primary)' },
            { label: 'Ausstehend',    count: PHASES.filter(p => p.state === 'locked').length, color: 'var(--text-tertiary)' },
          ].map(s => (
            <div key={s.label} style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 12 }}>
              <div style={{ width: 8, height: 8, borderRadius: '50%', background: s.color, flexShrink: 0 }} />
              <span style={{ color: 'var(--text-secondary)' }}>{s.label}:</span>
              <span style={{ fontWeight: 600, color: s.color }}>{s.count}</span>
            </div>
          ))}
        </div>
      </div>

      {/* ── Phase timeline ── */}
      <div>
        {PHASES.map((phase, i) => (
          <PhaseCard key={phase.number} phase={phase} isLast={i === PHASES.length - 1} />
        ))}
      </div>

      {/* ── Footer note ── */}
      <div style={{ marginTop: 28, padding: '12px 16px', background: 'var(--bg-app)', borderRadius: 'var(--radius-md)', fontSize: 12, color: 'var(--text-tertiary)', textAlign: 'center' }}>
        Bei Fragen zu deinem Projekt wende dich an dein KOMPAGNON-Team.
      </div>
    </div>
  );
}

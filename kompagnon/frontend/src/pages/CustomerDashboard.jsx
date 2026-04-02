import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import API_BASE_URL from '../config';

// ── Category score config ─────────────────────────────────────────────────────
const CATEGORIES = [
  { key: 'rc_score', label: 'Rechtliche Compliance',    max: 30, color: '#3f51b5' },
  { key: 'tp_score', label: 'Technische Performance',   max: 20, color: '#2196f3' },
  { key: 'bf_score', label: 'Barrierefreiheit',         max: 20, color: '#9c27b0' },
  { key: 'si_score', label: 'Sicherheit & Datenschutz', max: 15, color: '#f44336' },
  { key: 'se_score', label: 'SEO & Sichtbarkeit',       max: 10, color: '#ff9800' },
  { key: 'ux_score', label: 'Inhalt & Nutzererfahrung', max:  5, color: '#4caf50' },
];

// ── Project phases ────────────────────────────────────────────────────────────
const PHASES = [
  { key: 'phase_1', label: 'Strategie-Workshop' },
  { key: 'phase_2', label: 'Texterstellung'      },
  { key: 'phase_3', label: 'Umsetzung'           },
  { key: 'phase_4', label: 'Go-Live'             },
];

// ── Level colors ──────────────────────────────────────────────────────────────
const LEVEL_COLOR = {
  'Homepage Standard Platin': '#4a90d9',
  'Homepage Standard Gold':   '#b8860b',
  'Homepage Standard Silber': '#708090',
  'Homepage Standard Bronze': '#cd7f32',
  'Nicht konform':            '#dc2626',
};

function scoreBarColor(pct) {
  if (pct >= 0.7) return '#16a34a';
  if (pct >= 0.45) return '#f59e0b';
  return '#dc2626';
}

// ── Main Component ────────────────────────────────────────────────────────────

export default function CustomerDashboard() {
  const { user, token } = useAuth();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]   = useState(null);

  useEffect(() => {
    if (!user?.lead_id) { setLoading(false); return; }
    const h = { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` };
    fetch(`${API_BASE_URL}/api/usercards/${user.lead_id}/profile`, { headers: h })
      .then(r => r.ok ? r.json() : Promise.reject(r.status))
      .then(data => setProfile(data))
      .catch(() => setError('Daten konnten nicht geladen werden.'))
      .finally(() => setLoading(false));
  }, [user?.lead_id]); // eslint-disable-line

  // ── Loading / error ──────────────────────────────────────────────────────────
  if (loading) return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '60vh', flexDirection: 'column', gap: 12 }}>
      <div style={{ width: 36, height: 36, borderRadius: '50%', border: '3px solid var(--border-light)', borderTopColor: 'var(--brand-primary)', animation: 'spin 0.8s linear infinite' }} />
      <span style={{ fontSize: 13, color: 'var(--text-tertiary)' }}>Wird geladen…</span>
    </div>
  );

  if (error || !profile) return (
    <div style={{ textAlign: 'center', padding: 60, color: 'var(--text-tertiary)' }}>
      {error || 'Keine Daten verfügbar.'}
    </div>
  );

  const { lead, current_score, current_level, audits = [], projects = [] } = profile;
  const latestAudit = audits[0] || null;
  const project     = projects[0] || null;
  const levelColor  = LEVEL_COLOR[current_level] || 'var(--text-tertiary)';

  // Recommendations & issues from latest audit
  let recs   = latestAudit?.recommendations || [];
  let issues = latestAudit?.top_issues       || [];
  try { if (typeof recs   === 'string') recs   = JSON.parse(recs);   } catch { recs   = []; }
  try { if (typeof issues === 'string') issues = JSON.parse(issues); } catch { issues = []; }

  const recText  = (r) => typeof r === 'string' ? r : (r?.title || r?.text || '');
  const issText  = (i) => typeof i === 'string' ? i : (i?.title || i?.issue || i?.text || '');

  // Count open recommendations
  const openCount = recs.length + issues.length;

  // ── Phase index ──────────────────────────────────────────────────────────────
  const currentPhaseIdx = PHASES.findIndex(p => p.key === project?.status);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20, maxWidth: 1100, margin: '0 auto', width: '100%', animation: 'fadeIn 0.3s ease' }}>

      {/* ── 1. HEADER ── */}
      <div style={{ background: 'var(--brand-primary)', borderRadius: 'var(--radius-xl)', padding: '24px 28px', color: 'white' }}>
        <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.6)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 6 }}>
          Willkommen zurück
        </div>
        <h1 style={{ fontSize: 24, fontWeight: 700, color: 'white', margin: 0 }}>
          {lead.display_name || lead.company_name}
        </h1>
        {lead.website_url && (
          <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.7)', marginTop: 6 }}>
            {lead.website_url.replace(/^https?:\/\//, '')}
          </div>
        )}
      </div>

      {/* ── 2. KPIs ── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(190px, 1fr))', gap: 12 }}>
        {/* Score */}
        <KpiCard
          icon="🏆"
          label="Homepage Score"
          value={current_score != null ? `${current_score}/100` : '—'}
          sub={current_level?.replace('Homepage Standard ', '') || ''}
          accent={levelColor}
        />
        {/* Level */}
        <KpiCard
          icon="🎖️"
          label="Zertifizierungsstufe"
          value={current_level?.replace('Homepage Standard ', '') || '—'}
          sub={current_score != null ? `${current_score} Punkte` : ''}
          accent={levelColor}
        />
        {/* Last audit */}
        <KpiCard
          icon="📅"
          label="Letzter Audit"
          value={latestAudit ? new Date(latestAudit.created_at).toLocaleDateString('de-DE') : '—'}
          sub={latestAudit ? `Score: ${latestAudit.total_score}/100` : 'Noch kein Audit'}
          accent="var(--brand-primary)"
        />
        {/* Open recommendations */}
        <KpiCard
          icon="📋"
          label="Offene Empfehlungen"
          value={openCount > 0 ? openCount : '—'}
          sub={openCount > 0 ? `${issues.length} dringend, ${recs.length} wichtig` : 'Keine Empfehlungen'}
          accent={openCount > 0 ? '#f59e0b' : '#16a34a'}
        />
      </div>

      {/* ── 3. TWO COLUMNS ── */}
      {latestAudit && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 16 }}>

          {/* Left — category score bars */}
          <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', padding: 20 }}>
            <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 16 }}>
              Kategorie-Scores
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {CATEGORIES.map(cat => {
                const score = latestAudit[cat.key] ?? 0;
                const pct   = cat.max > 0 ? score / cat.max : 0;
                const color = scoreBarColor(pct);
                return (
                  <div key={cat.key}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4, fontSize: 12 }}>
                      <span style={{ color: 'var(--text-secondary)' }}>{cat.label}</span>
                      <span style={{ fontWeight: 600, color }}>{score}/{cat.max}</span>
                    </div>
                    <div style={{ height: 6, background: 'var(--border-light)', borderRadius: 3, overflow: 'hidden' }}>
                      <div style={{ height: '100%', width: `${pct * 100}%`, background: color, borderRadius: 3, transition: 'width 0.8s ease' }} />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Right — recommendations */}
          <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', padding: 20 }}>
            <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 16 }}>
              Top-Empfehlungen
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {issues.slice(0, 3).map((issue, i) => (
                <RecommendationRow
                  key={`issue-${i}`}
                  text={issText(issue)}
                  badge="Dringend"
                  badgeColor="#dc2626"
                  badgeBg="#fef2f2"
                />
              ))}
              {recs.slice(0, 4).map((rec, i) => (
                <RecommendationRow
                  key={`rec-${i}`}
                  text={recText(rec)}
                  badge="Wichtig"
                  badgeColor="#d97706"
                  badgeBg="#fffbeb"
                />
              ))}
              {issues.length === 0 && recs.length === 0 && (
                <div style={{ fontSize: 13, color: 'var(--text-tertiary)', padding: '16px 0', textAlign: 'center' }}>
                  ✅ Keine offenen Empfehlungen
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ── 4. PROJECT PHASES ── */}
      {(project || true) && (
        <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', padding: 20 }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 20 }}>
            Projektstatus
          </div>

          {/* Phase steps */}
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: 0, overflowX: 'auto' }}>
            {PHASES.map((phase, idx) => {
              const done    = currentPhaseIdx >= 0 && idx < currentPhaseIdx;
              const active  = idx === currentPhaseIdx;
              const pending = currentPhaseIdx < 0 ? idx > 0 : idx > currentPhaseIdx;
              const color   = done ? '#16a34a' : active ? '#f59e0b' : 'var(--border-medium)';
              const isLast  = idx === PHASES.length - 1;

              return (
                <div key={phase.key} style={{ display: 'flex', alignItems: 'center', flex: isLast ? '0 0 auto' : 1, minWidth: 120 }}>
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', flex: '0 0 auto' }}>
                    {/* Circle */}
                    <div style={{
                      width: 36, height: 36, borderRadius: '50%',
                      background: done ? '#16a34a' : active ? '#f59e0b' : 'var(--bg-app)',
                      border: `2px solid ${color}`,
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontSize: 14, color: (done || active) ? 'white' : 'var(--text-tertiary)',
                      fontWeight: 700, flexShrink: 0,
                      transition: 'all 0.3s ease',
                    }}>
                      {done ? '✓' : idx + 1}
                    </div>
                    {/* Label */}
                    <div style={{ fontSize: 11, marginTop: 6, textAlign: 'center', whiteSpace: 'nowrap',
                      color: done ? '#16a34a' : active ? '#f59e0b' : 'var(--text-tertiary)',
                      fontWeight: active ? 600 : 400,
                    }}>
                      {phase.label}
                    </div>
                    {active && (
                      <div style={{ fontSize: 10, color: '#f59e0b', fontWeight: 600, marginTop: 2 }}>Aktuelle Phase</div>
                    )}
                  </div>
                  {/* Connector */}
                  {!isLast && (
                    <div style={{ flex: 1, height: 2, background: done ? '#16a34a' : 'var(--border-light)', marginBottom: 28, transition: 'background 0.3s ease' }} />
                  )}
                </div>
              );
            })}
          </div>

          {/* Phase details */}
          {project && (
            <div style={{ display: 'flex', gap: 20, marginTop: 16, paddingTop: 16, borderTop: '1px solid var(--border-light)', flexWrap: 'wrap' }}>
              {project.start_date && (
                <div style={{ fontSize: 12 }}>
                  <span style={{ color: 'var(--text-tertiary)' }}>Projektstart: </span>
                  <span style={{ color: 'var(--text-primary)', fontWeight: 500 }}>{project.start_date}</span>
                </div>
              )}
              {project.target_go_live && (
                <div style={{ fontSize: 12 }}>
                  <span style={{ color: 'var(--text-tertiary)' }}>Geplantes Go-Live: </span>
                  <span style={{ color: 'var(--text-primary)', fontWeight: 500 }}>{project.target_go_live}</span>
                </div>
              )}
            </div>
          )}
          {!project && (
            <div style={{ marginTop: 12, fontSize: 12, color: 'var(--text-tertiary)', textAlign: 'center' }}>
              Noch kein Projekt angelegt — Ihr Berater wird Sie kontaktieren.
            </div>
          )}
        </div>
      )}

      {/* ── 5. CONTACT BANNER ── */}
      <div style={{
        background: 'linear-gradient(135deg, #16a34a 0%, #15803d 100%)',
        borderRadius: 'var(--radius-xl)',
        padding: '20px 24px',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 16,
      }}>
        <div>
          <div style={{ fontSize: 16, fontWeight: 700, color: 'white', marginBottom: 4 }}>
            Fragen zu Ihrem Projekt?
          </div>
          <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.85)' }}>
            Unser Team steht Ihnen gerne zur Verfügung.
          </div>
        </div>
        {lead.email ? (
          <a
            href={`mailto:${lead.email}`}
            style={{
              background: 'white', color: '#16a34a', borderRadius: 'var(--radius-md)',
              padding: '10px 20px', fontSize: 13, fontWeight: 700,
              textDecoration: 'none', flexShrink: 0, display: 'inline-block',
            }}
          >
            Kontakt aufnehmen
          </a>
        ) : (
          <div style={{
            background: 'white', color: '#16a34a', borderRadius: 'var(--radius-md)',
            padding: '10px 20px', fontSize: 13, fontWeight: 700, flexShrink: 0,
          }}>
            Kontakt aufnehmen
          </div>
        )}
      </div>

    </div>
  );
}

// ── Sub-components ────────────────────────────────────────────────────────────

function KpiCard({ icon, label, value, sub, accent }) {
  return (
    <div style={{
      background: 'var(--bg-surface)', border: '1px solid var(--border-light)',
      borderRadius: 'var(--radius-lg)', padding: '16px 18px',
      borderTop: `3px solid ${accent}`,
    }}>
      <div style={{ fontSize: 20, marginBottom: 8 }}>{icon}</div>
      <div style={{ fontSize: 11, color: 'var(--text-tertiary)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 4 }}>
        {label}
      </div>
      <div style={{ fontSize: 24, fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1 }}>
        {value}
      </div>
      {sub && (
        <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 4 }}>{sub}</div>
      )}
    </div>
  );
}

function RecommendationRow({ text, badge, badgeColor, badgeBg }) {
  if (!text) return null;
  return (
    <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10 }}>
      <span style={{
        flexShrink: 0, fontSize: 10, fontWeight: 700, padding: '2px 7px',
        borderRadius: 'var(--radius-sm)', background: badgeBg, color: badgeColor,
        border: `1px solid ${badgeColor}30`, marginTop: 1, whiteSpace: 'nowrap',
      }}>
        {badge}
      </span>
      <span style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
        {text}
      </span>
    </div>
  );
}

import React from 'react';

// ── Constants ─────────────────────────────────────────────────────────────────

const PHASES = [
  { key: 'phase_1', label: 'Onboarding',  short: '1' },
  { key: 'phase_2', label: 'Briefing',   short: '2' },
  { key: 'phase_3', label: 'Content',    short: '3' },
  { key: 'phase_4', label: 'Technik',    short: '4' },
  { key: 'phase_5', label: 'QA',         short: '5' },
  { key: 'phase_6', label: 'Go-Live',    short: '6' },
  { key: 'phase_7', label: 'Post-Launch',short: '7' },
];

const AUDIT_LEVELS = {
  bronze:   { label: 'Bronze',   bg: '#CD7F32', text: '#fff' },
  silber:   { label: 'Silber',   bg: '#9E9E9E', text: '#fff' },
  gold:     { label: 'Gold',     bg: '#D4A100', text: '#fff' },
  platin:   { label: 'Platin',   bg: '#185FA5', text: '#fff' },
  diamant:  { label: 'Diamant',  bg: '#1D9E75', text: '#fff' },
};

// ── Helpers ───────────────────────────────────────────────────────────────────

function initials(name) {
  if (!name) return '??';
  const parts = name.trim().split(/\s+/);
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

function phaseIndex(status) {
  const idx = PHASES.findIndex(p => p.key === status);
  return idx === -1 ? 0 : idx;
}

function speedColor(score) {
  if (score === null || score === undefined) return { text: 'var(--text-tertiary)', bg: 'var(--bg-muted)' };
  if (score >= 90) return { text: '#3B6D11', bg: '#EAF4E0' };
  if (score >= 50) return { text: '#BA7517', bg: '#FEF3DC' };
  return { text: '#E24B4A', bg: '#FDEAEA' };
}

function paymentColor(status) {
  if (!status) return { text: 'var(--text-tertiary)', bg: 'var(--bg-muted)' };
  const s = status.toLowerCase();
  if (s === 'bezahlt')   return { text: '#3B6D11', bg: '#EAF4E0' };
  if (s === 'überfällig') return { text: '#E24B4A', bg: '#FDEAEA' };
  return { text: '#BA7517', bg: '#FEF3DC' }; // offen
}

function problemColor(idx) {
  return idx === 0 ? { text: '#E24B4A', bg: '#FDEAEA' }
       : idx === 1 ? { text: '#BA7517', bg: '#FEF3DC' }
       :             { text: '#BA7517', bg: '#FEF3DC' };
}

// ── Sub-components ────────────────────────────────────────────────────────────

function Badge({ label, colorStyle, style }) {
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center',
      padding: '2px 8px', borderRadius: 20,
      fontSize: 11, fontWeight: 600, lineHeight: '18px',
      background: colorStyle?.bg || 'var(--bg-muted)',
      color: colorStyle?.text || 'var(--text-secondary)',
      ...style,
    }}>
      {label}
    </span>
  );
}

function InfoBlock({ label, children, style }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 3, ...style }}>
      <span style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
        {label}
      </span>
      <div style={{ fontSize: 13, color: 'var(--text-primary)' }}>
        {children}
      </div>
    </div>
  );
}

function Divider() {
  return <div style={{ width: 1, alignSelf: 'stretch', background: 'var(--border-light)', flexShrink: 0 }} />;
}

// ── Main component ────────────────────────────────────────────────────────────

export default function ProjectCard({ project }) {
  if (!project) return null;

  const activeIdx   = phaseIndex(project.status);
  const activePhase = PHASES[activeIdx];
  const progressPct = 60; // placeholder — replace with real checklist % if available

  const speedM      = project.pagespeed_mobile;
  const speedD      = project.pagespeed_desktop;
  const speedMColor = speedColor(speedM);
  const speedDColor = speedColor(speedD);

  const payColor    = paymentColor(project.payment_status);

  const auditInfo   = AUDIT_LEVELS[(project.audit_level || '').toLowerCase()];

  const desiredPages = project.desired_pages
    ? project.desired_pages.split(',').map(s => s.trim()).filter(Boolean)
    : [];

  const topProblems = project.top_problems
    ? project.top_problems.split('\n').map(s => s.trim()).filter(Boolean).slice(0, 3)
    : [];

  const card = {
    background: 'var(--bg-surface)',
    border: '1px solid var(--border-light)',
    borderRadius: 'var(--radius-lg)',
    overflow: 'hidden',
    fontFamily: 'var(--font-sans)',
  };

  const row = {
    display: 'flex',
    alignItems: 'stretch',
    gap: 0,
    borderTop: '1px solid var(--border-light)',
    padding: '14px 20px',
  };

  const col = {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    gap: 6,
    paddingRight: 16,
  };

  // ── BEREICH 1 — Header ────────────────────────────────────────────────────
  return (
    <div style={card}>
      <div style={{ background: '#E6F1FB', padding: '16px 20px', display: 'flex', alignItems: 'center', gap: 14 }}>
        {/* Avatar */}
        <div style={{
          width: 44, height: 44, borderRadius: '50%',
          background: '#185FA5', color: '#fff',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 15, fontWeight: 700, flexShrink: 0,
        }}>
          {initials(project.company_name)}
        </div>

        {/* Name + meta */}
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontSize: 15, fontWeight: 700, color: '#0D2A4E', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {project.company_name || `Projekt #${project.id}`}
          </div>
          <div style={{ fontSize: 12, color: '#4A6884', marginTop: 1 }}>
            {[project.industry, project.city].filter(Boolean).join(' · ') || '–'}
          </div>
        </div>

        {/* Badges */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexShrink: 0 }}>
          {project.package_type && (
            <Badge label={project.package_type} colorStyle={{ text: '#3B6D11', bg: '#EAF4E0' }} />
          )}
          <Badge
            label={project.payment_status || 'offen'}
            colorStyle={payColor}
          />
        </div>
      </div>

      {/* ── BEREICH 2 — Phasenleiste ──────────────────────────────────────── */}
      <div style={{ padding: '14px 20px 10px', borderTop: '1px solid var(--border-light)' }}>
        <div style={{ display: 'flex', gap: 4, marginBottom: 6 }}>
          {PHASES.map((phase, idx) => {
            const done   = idx < activeIdx;
            const active = idx === activeIdx;
            return (
              <div key={phase.key} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
                <div style={{ width: '100%', height: 8, borderRadius: 4, overflow: 'hidden', background: 'var(--border-light)' }}>
                  {done ? (
                    <div style={{ width: '100%', height: '100%', background: '#1D9E75' }} />
                  ) : active ? (
                    <div style={{ width: `${progressPct}%`, height: '100%', background: '#185FA5' }} />
                  ) : null}
                </div>
                <span style={{ fontSize: 9, color: done ? '#1D9E75' : active ? '#185FA5' : 'var(--text-tertiary)', fontWeight: active ? 700 : 400 }}>
                  {phase.short}
                </span>
              </div>
            );
          })}
        </div>
        <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
          <span style={{ fontWeight: 600, color: '#185FA5' }}>Phase {activeIdx + 1} von 7</span>
          {' · '}{activePhase?.label}
          {' · '}<span style={{ color: '#1D9E75' }}>{progressPct}% erledigt</span>
        </div>
      </div>

      {/* ── BEREICH 3 — Website / PageSpeed / Audit ───────────────────────── */}
      <div style={row}>
        <div style={col}>
          <InfoBlock label="Website">
            {project.website_url
              ? <a href={project.website_url} target="_blank" rel="noreferrer" style={{ color: '#185FA5', textDecoration: 'none', fontSize: 12, wordBreak: 'break-all' }}>{project.website_url}</a>
              : <span style={{ color: 'var(--text-tertiary)', fontSize: 12 }}>–</span>
            }
            {project.cms_type && (
              <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginTop: 2 }}>{project.cms_type}</div>
            )}
          </InfoBlock>
        </div>
        <Divider />
        <div style={{ ...col, paddingLeft: 16 }}>
          <InfoBlock label="PageSpeed">
            <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
              <Badge
                label={speedM !== null && speedM !== undefined ? `📱 ${speedM}` : '📱 –'}
                colorStyle={speedMColor}
              />
              <Badge
                label={speedD !== null && speedD !== undefined ? `🖥 ${speedD}` : '🖥 –'}
                colorStyle={speedDColor}
              />
            </div>
          </InfoBlock>
        </div>
        <Divider />
        <div style={{ ...col, paddingLeft: 16, paddingRight: 0 }}>
          <InfoBlock label="Zertifizierung">
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              {auditInfo
                ? <Badge label={auditInfo.label} colorStyle={{ bg: auditInfo.bg, text: auditInfo.text }} />
                : <span style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>–</span>
              }
              {project.audit_score !== null && project.audit_score !== undefined && (
                <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{project.audit_score} Pkt.</span>
              )}
            </div>
          </InfoBlock>
        </div>
      </div>

      {/* ── BEREICH 4 — Seiten / Assets / Termine ─────────────────────────── */}
      <div style={row}>
        <div style={col}>
          <InfoBlock label="Gewünschte Seiten">
            {desiredPages.length > 0 ? (
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginTop: 2 }}>
                {desiredPages.map(p => (
                  <span key={p} style={{
                    fontSize: 11, padding: '2px 7px', borderRadius: 12,
                    background: 'var(--bg-muted)', color: 'var(--text-secondary)',
                    border: '1px solid var(--border-light)',
                  }}>{p}</span>
                ))}
              </div>
            ) : (
              <span style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>–</span>
            )}
          </InfoBlock>
        </div>
        <Divider />
        <div style={{ ...col, paddingLeft: 16 }}>
          <InfoBlock label="Assets">
            {[
              { label: 'Logo',     val: project.has_logo },
              { label: 'Briefing', val: project.has_briefing },
              { label: 'Fotos',    val: project.has_photos },
            ].map(({ label, val }) => (
              <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12 }}>
                <span style={{ color: val ? '#1D9E75' : '#E24B4A', fontWeight: 700 }}>{val ? '✓' : '✗'}</span>
                <span style={{ color: val ? 'var(--text-primary)' : 'var(--text-tertiary)' }}>{label}</span>
              </div>
            ))}
          </InfoBlock>
        </div>
        <Divider />
        <div style={{ ...col, paddingLeft: 16, paddingRight: 0 }}>
          <InfoBlock label="Termine">
            <div style={{ fontSize: 12, display: 'flex', flexDirection: 'column', gap: 3 }}>
              <div>
                <span style={{ color: 'var(--text-tertiary)' }}>Start: </span>
                {project.start_date
                  ? new Date(project.start_date).toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' })
                  : '–'}
              </div>
              <div>
                <span style={{ color: 'var(--text-tertiary)' }}>Go-live: </span>
                {project.go_live_date
                  ? new Date(project.go_live_date).toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' })
                  : '–'}
              </div>
            </div>
          </InfoBlock>
        </div>
      </div>

      {/* ── BEREICH 5 — Probleme / Ansprechpartner ────────────────────────── */}
      <div style={row}>
        <div style={col}>
          <InfoBlock label="Top-Probleme (Audit)">
            {topProblems.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4, marginTop: 2 }}>
                {topProblems.map((p, i) => {
                  const c = problemColor(i);
                  return (
                    <div key={i} style={{
                      fontSize: 11, padding: '3px 8px', borderRadius: 6,
                      background: c.bg, color: c.text, fontWeight: 500,
                    }}>{p}</div>
                  );
                })}
              </div>
            ) : (
              <span style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>–</span>
            )}
          </InfoBlock>
        </div>
        <Divider />
        <div style={{ ...col, paddingLeft: 16, paddingRight: 0 }}>
          <InfoBlock label="Ansprechpartner">
            <div style={{ display: 'flex', flexDirection: 'column', gap: 3, fontSize: 12 }}>
              <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                {project.contact_name || '–'}
              </div>
              {project.contact_phone && (
                <a href={`tel:${project.contact_phone}`} style={{ color: 'var(--text-secondary)', textDecoration: 'none' }}>
                  📞 {project.contact_phone}
                </a>
              )}
              {project.contact_email && (
                <a href={`mailto:${project.contact_email}`} style={{ color: '#185FA5', textDecoration: 'none', wordBreak: 'break-all' }}>
                  ✉ {project.contact_email}
                </a>
              )}
              {!project.contact_phone && !project.contact_email && !project.contact_name && (
                <span style={{ color: 'var(--text-tertiary)' }}>–</span>
              )}
            </div>
          </InfoBlock>
        </div>
      </div>
    </div>
  );
}

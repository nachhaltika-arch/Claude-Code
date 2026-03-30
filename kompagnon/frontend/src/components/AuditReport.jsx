import React from 'react';
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  Radar,
  ResponsiveContainer,
  Tooltip as ReTooltip,
} from 'recharts';

const LEVEL_STYLES = {
  'Homepage Standard Platin': { bg: '#e8eaf6', color: '#283593', icon: '\uD83C\uDFC6' },
  'Homepage Standard Gold':   { bg: '#fff8e1', color: '#f57f17', icon: '\uD83E\uDD47' },
  'Homepage Standard Silber': { bg: '#f5f5f5', color: '#616161', icon: '\uD83E\uDD48' },
  'Homepage Standard Bronze': { bg: '#efebe9', color: '#4e342e', icon: '\uD83E\uDD49' },
  'Nicht konform':            { bg: '#fdecea', color: '#C8102E', icon: '\u26D4' },
};

const CATEGORIES = [
  {
    key: 'rechtliche_compliance',
    label: 'Rechtliche Compliance',
    shortLabel: 'Rechtlich',
    max: 30,
    color: '#3f51b5',
    items: [
      { key: 'rc_impressum',    label: 'Impressum (TMG/DDG)',              max: 7 },
      { key: 'rc_datenschutz',  label: 'Datenschutzerkl\u00E4rung (DSGVO)', max: 7 },
      { key: 'rc_cookie',       label: 'Cookie Consent (TDDDG)',            max: 6 },
      { key: 'rc_bfsg',         label: 'Barrierefreiheitserkl\u00E4rung (BFSG)', max: 4 },
      { key: 'rc_urheberrecht', label: 'Urheberrecht & Lizenzen',          max: 3 },
      { key: 'rc_ecommerce',    label: 'E-Commerce Pflichten',             max: 3 },
    ],
  },
  {
    key: 'technische_performance',
    label: 'Technische Performance',
    shortLabel: 'Performance',
    max: 20,
    color: '#2196f3',
    items: [
      { key: 'tp_lcp',    label: 'LCP (Ladezeit Hauptinhalt)',  max: 5 },
      { key: 'tp_cls',    label: 'CLS (Layout-Stabilit\u00E4t)', max: 4 },
      { key: 'tp_inp',    label: 'INP (Interaktionszeit)',      max: 3 },
      { key: 'tp_mobile', label: 'Mobile-First Design',         max: 4 },
      { key: 'tp_bilder', label: 'Bildoptimierung',             max: 4 },
    ],
  },
  {
    key: 'barrierefreiheit',
    label: 'Barrierefreiheit',
    shortLabel: 'Barrierefr.',
    max: 20,
    color: '#9c27b0',
    items: [
      { key: 'bf_kontrast',     label: 'Farbkontraste (WCAG AA)',           max: 5 },
      { key: 'bf_tastatur',     label: 'Tastaturzug\u00E4nglichkeit',       max: 5 },
      { key: 'bf_screenreader', label: 'Screenreader-Kompatibilit\u00E4t', max: 5 },
      { key: 'bf_lesbarkeit',   label: 'Lesbarkeit & Textgr\u00F6\u00DFe', max: 5 },
    ],
  },
  {
    key: 'sicherheit_datenschutz',
    label: 'Sicherheit & Datenschutz',
    shortLabel: 'Sicherheit',
    max: 15,
    color: '#f44336',
    items: [
      { key: 'si_ssl',          label: 'HTTPS / SSL-Zertifikat',        max: 4 },
      { key: 'si_header',       label: 'Security-Header (HSTS, CSP)',   max: 4 },
      { key: 'si_drittanbieter',label: 'DSGVO Drittanbieter',           max: 4 },
      { key: 'si_formulare',    label: 'Formularsicherheit',            max: 3 },
    ],
  },
  {
    key: 'seo_sichtbarkeit',
    label: 'SEO & Sichtbarkeit',
    shortLabel: 'SEO',
    max: 10,
    color: '#ff9800',
    items: [
      { key: 'se_seo',    label: 'Technische SEO Grundlagen',      max: 4 },
      { key: 'se_schema', label: 'Strukturierte Daten (Schema.org)', max: 3 },
      { key: 'se_lokal',  label: 'Lokale Auffindbarkeit',          max: 3 },
    ],
  },
  {
    key: 'inhalt_nutzererfahrung',
    label: 'Inhalt & Nutzererfahrung',
    shortLabel: 'Inhalt/UX',
    max: 5,
    color: '#4caf50',
    items: [
      { key: 'ux_erstindruck', label: 'Erster Eindruck',           max: 1 },
      { key: 'ux_cta',         label: 'Klare Call-to-Action',      max: 1 },
      { key: 'ux_navigation',  label: 'Navigation & Struktur',     max: 1 },
      { key: 'ux_vertrauen',   label: 'Vertrauenssignale',         max: 1 },
      { key: 'ux_content',     label: 'Content-Qualit\u00E4t',     max: 1 },
      { key: 'ux_kontakt',     label: 'Kontaktm\u00F6glichkeiten', max: 1 },
    ],
  },
];

const HOSTING_ITEMS = [
  { key: 'ho_anbieter', label: 'Anbieter identifizierbar' },
  { key: 'ho_uptime',   label: 'Erreichbarkeit' },
  { key: 'ho_http',     label: 'HTTP\u2192HTTPS Weiterleitung' },
  { key: 'ho_backup',   label: 'Backup-Hinweise' },
  { key: 'ho_cdn',      label: 'CDN aktiv' },
];

function scoreColor(score, max) {
  if (max === 0) return 'var(--kc-mittel)';
  const pct = score / max;
  if (pct >= 1.0) return 'var(--kc-success)';
  if (pct >= 0.5) return 'var(--kc-warning)';
  return 'var(--kc-rot)';
}

function scoreIcon(score, max) {
  if (max === 0) return '\u2014';
  const pct = score / max;
  if (pct >= 1.0) return '\u2713';
  if (pct >= 0.5) return '\u26A0';
  return '\u2717';
}

// ═══════════════════════════════════════════════════════════
// Main Component
// ═══════════════════════════════════════════════════════════

export default function AuditReport({ auditData }) {
  if (!auditData) return null;

  const r = auditData;
  const ls = LEVEL_STYLES[r.level] || LEVEL_STYLES['Nicht konform'];
  const items = r.items || {};
  const checks = r.checks || {};

  const radarData = CATEGORIES.map((cat) => {
    const catData = r.categories?.[cat.key] || { score: 0, max: cat.max };
    return {
      subject: cat.shortLabel,
      score: cat.max > 0 ? Math.round((catData.score / cat.max) * 100) : 0,
      fullMark: 100,
    };
  });

  const hasHostingData = HOSTING_ITEMS.some((hi) => items[hi.key] !== undefined);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--kc-space-6)' }}>
      {/* Score Hero */}
      <div
        className="kc-card"
        style={{
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          flexDirection: 'column', gap: 'var(--kc-space-4)',
          padding: 'var(--kc-space-10)',
          background: ls.bg, borderColor: ls.color,
        }}
      >
        <div style={{
          fontFamily: 'var(--kc-font-display)', fontSize: '4rem', fontWeight: 700,
          color: ls.color, lineHeight: 1,
        }}>
          {r.total_score}
          <span style={{ fontSize: 'var(--kc-text-2xl)', fontWeight: 400, color: 'var(--kc-mittel)' }}> / 100</span>
        </div>
        <div style={{
          display: 'inline-flex', alignItems: 'center', gap: 'var(--kc-space-2)',
          padding: 'var(--kc-space-2) var(--kc-space-6)',
          borderRadius: 'var(--kc-radius-md)',
          background: 'var(--kc-weiss)', border: `2px solid ${ls.color}`,
          fontWeight: 700, fontSize: 'var(--kc-text-lg)', color: ls.color,
        }}>
          {ls.icon} {r.level}
        </div>
        <p style={{ color: 'var(--kc-text-subtil)', fontSize: 'var(--kc-text-sm)', textAlign: 'center' }}>
          {r.website_url}
          {(r.city || r.trade) && (
            <span> &middot; {[r.city, r.trade].filter(Boolean).join(', ')}</span>
          )}
          {r.created_at && (
            <span> &middot; {new Date(r.created_at).toLocaleDateString('de-DE')}</span>
          )}
        </p>
      </div>

      {/* Overview: Radar + Category Bars */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 'var(--kc-space-4)' }}>
        {/* Radar Chart */}
        <div className="kc-card">
          <span className="kc-eyebrow">\u00DCbersicht</span>
          <h3 style={{ marginBottom: 'var(--kc-space-3)', fontSize: 'var(--kc-text-base)' }}>Kategorien-Profil</h3>
          <ResponsiveContainer width="100%" height={240}>
            <RadarChart data={radarData} margin={{ top: 10, right: 20, bottom: 10, left: 20 }}>
              <PolarGrid stroke="var(--kc-rand)" />
              <PolarAngleAxis
                dataKey="subject"
                tick={{ fontSize: 11, fill: '#555' }}
              />
              <Radar
                name="Score %"
                dataKey="score"
                stroke="#C8102E"
                fill="#C8102E"
                fillOpacity={0.18}
                strokeWidth={2}
              />
              <ReTooltip
                formatter={(value) => [`${value}%`, 'Score']}
                contentStyle={{ fontSize: '12px', borderRadius: '6px' }}
              />
            </RadarChart>
          </ResponsiveContainer>
        </div>

        {/* Category Score Bars */}
        <div className="kc-card">
          <span className="kc-eyebrow">Bewertung</span>
          <h3 style={{ marginBottom: 'var(--kc-space-4)', fontSize: 'var(--kc-text-base)' }}>Kategorie-Scores</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--kc-space-3)' }}>
            {CATEGORIES.map((cat) => {
              const catData = r.categories?.[cat.key] || { score: 0, max: cat.max };
              const pct = cat.max > 0 ? (catData.score / cat.max) * 100 : 0;
              const color = scoreColor(catData.score, cat.max);
              return (
                <div key={cat.key}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 'var(--kc-space-1)' }}>
                    <span style={{ fontSize: 'var(--kc-text-xs)', fontWeight: 600, color: 'var(--kc-text-sekundaer)' }}>
                      {cat.label}
                    </span>
                    <span style={{ fontSize: 'var(--kc-text-xs)', fontFamily: 'var(--kc-font-mono)', fontWeight: 700, color }}>
                      {catData.score}/{cat.max}
                    </span>
                  </div>
                  <div style={{ height: '6px', background: 'var(--kc-rand)', borderRadius: 'var(--kc-radius-full)', overflow: 'hidden' }}>
                    <div style={{
                      height: '100%', width: `${pct}%`, background: color,
                      borderRadius: 'var(--kc-radius-full)', transition: 'width 0.8s ease',
                    }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Detailed Category Breakdown */}
      <div>
        <div className="kc-section-header" style={{ marginBottom: 'var(--kc-space-4)' }}>
          <span className="kc-eyebrow">Details</span>
          <h2>Einzelkriterien</h2>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--kc-space-3)' }}>
          {CATEGORIES.map((cat) => {
            const catData = r.categories?.[cat.key] || { score: 0, max: cat.max };
            return (
              <CategorySection
                key={cat.key}
                category={cat}
                catScore={catData.score}
                items={items}
              />
            );
          })}
        </div>
      </div>

      {/* Hosting & Infrastruktur */}
      {hasHostingData && (
        <div className="kc-card">
          <span className="kc-eyebrow">Infrastruktur</span>
          <h3 style={{ marginBottom: 'var(--kc-space-4)', fontSize: 'var(--kc-text-base)' }}>Hosting & Infrastruktur</h3>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--kc-space-2)' }}>
            {HOSTING_ITEMS.map((hi) => {
              const val = items[hi.key];
              const ok = val === 1 || val === true;
              return (
                <span
                  key={hi.key}
                  style={{
                    display: 'inline-flex', alignItems: 'center', gap: '6px',
                    padding: '4px 12px',
                    borderRadius: 'var(--kc-radius-md)',
                    background: ok ? '#e8f5e9' : '#fdecea',
                    border: `1px solid ${ok ? 'var(--kc-success)' : 'var(--kc-rot)'}`,
                    fontSize: 'var(--kc-text-xs)', fontWeight: 600,
                    color: ok ? 'var(--kc-success)' : 'var(--kc-rot)',
                  }}
                >
                  {ok ? '\u2713' : '\u2717'} {hi.label}
                </span>
              );
            })}
          </div>
        </div>
      )}

      {/* Core Web Vitals */}
      {(checks.lcp_value != null || checks.cls_value != null || checks.inp_value != null || checks.mobile_score != null) && (
        <div className="kc-card">
          <span className="kc-eyebrow">Messwerte</span>
          <h3 style={{ marginBottom: 'var(--kc-space-4)', fontSize: 'var(--kc-text-base)' }}>Core Web Vitals</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: 'var(--kc-space-3)' }}>
            {checks.lcp_value != null && (
              <MetricCard
                label="LCP"
                value={`${checks.lcp_value}s`}
                hint="< 2.5s = gut"
                ok={checks.lcp_value < 2.5}
                warn={checks.lcp_value < 4.0}
              />
            )}
            {checks.cls_value != null && (
              <MetricCard
                label="CLS"
                value={String(checks.cls_value)}
                hint="< 0.1 = gut"
                ok={checks.cls_value < 0.1}
                warn={checks.cls_value < 0.25}
              />
            )}
            {checks.inp_value != null && (
              <MetricCard
                label="INP"
                value={`${checks.inp_value}ms`}
                hint="< 200ms = gut"
                ok={checks.inp_value < 200}
                warn={checks.inp_value < 500}
              />
            )}
            {checks.mobile_score != null && (
              <MetricCard
                label="Mobile Score"
                value={`${checks.mobile_score}/100`}
                hint="> 80 = gut"
                ok={checks.mobile_score >= 80}
                warn={checks.mobile_score >= 50}
              />
            )}
          </div>
        </div>
      )}

      {/* AI Summary */}
      {r.ai_summary && (
        <div className="kc-card" style={{ borderLeft: '4px solid var(--kc-info, #2196f3)' }}>
          <span className="kc-eyebrow" style={{ color: 'var(--kc-info, #2196f3)' }}>KI-Analyse</span>
          <h3 style={{ marginBottom: 'var(--kc-space-3)', fontSize: 'var(--kc-text-base)' }}>
            Was bedeutet das f\u00FCr Ihren Betrieb?
          </h3>
          <p style={{ color: 'var(--kc-text-sekundaer)', lineHeight: 'var(--kc-leading-normal)', fontSize: 'var(--kc-text-base)' }}>
            {r.ai_summary}
          </p>
        </div>
      )}

      {/* Issues + Recommendations */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 'var(--kc-space-4)' }}>
        {r.top_issues && r.top_issues.length > 0 && (
          <div className="kc-alert kc-alert--danger">
            <strong style={{ display: 'block', marginBottom: 'var(--kc-space-3)', fontFamily: 'var(--kc-font-display)' }}>
              Top-Probleme
            </strong>
            <ul style={{ margin: 0, paddingLeft: 'var(--kc-space-6)', display: 'flex', flexDirection: 'column', gap: 'var(--kc-space-2)' }}>
              {r.top_issues.map((issue, i) => (
                <li key={i} style={{ fontSize: 'var(--kc-text-sm)' }}>{issue}</li>
              ))}
            </ul>
          </div>
        )}
        {r.recommendations && r.recommendations.length > 0 && (
          <div className="kc-alert kc-alert--info" style={{ borderColor: 'var(--kc-success)', background: '#e8f5e9', color: '#1b5e20' }}>
            <strong style={{ display: 'block', marginBottom: 'var(--kc-space-3)', fontFamily: 'var(--kc-font-display)' }}>
              Empfehlungen
            </strong>
            <ol style={{ margin: 0, paddingLeft: 'var(--kc-space-6)', display: 'flex', flexDirection: 'column', gap: 'var(--kc-space-2)' }}>
              {r.recommendations.map((rec, i) => (
                <li key={i} style={{ fontSize: 'var(--kc-text-sm)' }}>{rec}</li>
              ))}
            </ol>
          </div>
        )}
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════
// Category Section (collapsible)
// ═══════════════════════════════════════════════════════════

function CategorySection({ category, catScore, items }) {
  const [expanded, setExpanded] = React.useState(true);
  const color = scoreColor(catScore, category.max);

  return (
    <div className="kc-card" style={{ overflow: 'hidden', padding: 0 }}>
      <button
        onClick={() => setExpanded((e) => !e)}
        style={{
          width: '100%', display: 'flex', alignItems: 'center',
          justifyContent: 'space-between',
          padding: 'var(--kc-space-3) var(--kc-space-4)',
          background: 'none', border: 'none', cursor: 'pointer', textAlign: 'left',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--kc-space-3)' }}>
          <div style={{ width: '4px', height: '20px', borderRadius: '2px', background: category.color, flexShrink: 0 }} />
          <span style={{ fontWeight: 700, fontSize: 'var(--kc-text-sm)', color: 'var(--kc-text-primaer)' }}>
            {category.label}
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--kc-space-3)' }}>
          <span style={{ fontSize: 'var(--kc-text-sm)', fontFamily: 'var(--kc-font-mono)', fontWeight: 700, color }}>
            {catScore}/{category.max}
          </span>
          <span style={{ fontSize: 'var(--kc-text-xs)', color: 'var(--kc-mittel)' }}>
            {expanded ? '\u25B2' : '\u25BC'}
          </span>
        </div>
      </button>

      {expanded && (
        <div style={{
          borderTop: '1px solid var(--kc-rand)',
          padding: 'var(--kc-space-3) var(--kc-space-4)',
          display: 'flex', flexDirection: 'column', gap: 'var(--kc-space-2)',
          background: 'var(--kc-hell)',
        }}>
          {category.items.map((item) => {
            const score = items[item.key] ?? 0;
            const pct = item.max > 0 ? (score / item.max) * 100 : 0;
            const icolor = scoreColor(score, item.max);
            const iicon = scoreIcon(score, item.max);

            return (
              <div
                key={item.key}
                style={{
                  display: 'grid',
                  gridTemplateColumns: '1fr 100px 48px 20px',
                  gap: 'var(--kc-space-3)',
                  alignItems: 'center',
                }}
              >
                <span style={{ fontSize: 'var(--kc-text-xs)', color: 'var(--kc-text-sekundaer)' }}>
                  {item.label}
                </span>
                <div style={{ height: '5px', background: 'var(--kc-rand)', borderRadius: 'var(--kc-radius-full)', overflow: 'hidden' }}>
                  <div style={{
                    height: '100%', width: `${pct}%`, background: icolor,
                    borderRadius: 'var(--kc-radius-full)', transition: 'width 0.5s ease',
                  }} />
                </div>
                <span style={{ fontSize: 'var(--kc-text-xs)', fontFamily: 'var(--kc-font-mono)', color: icolor, textAlign: 'right', fontWeight: 600 }}>
                  {score}/{item.max}
                </span>
                <span style={{ fontSize: 'var(--kc-text-xs)', color: icolor, fontWeight: 700, textAlign: 'center' }}>
                  {iicon}
                </span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════
// Metric Card
// ═══════════════════════════════════════════════════════════

function MetricCard({ label, value, hint, ok, warn }) {
  const color = ok ? 'var(--kc-success)' : warn ? 'var(--kc-warning)' : 'var(--kc-rot)';
  return (
    <div style={{
      padding: 'var(--kc-space-4)',
      background: 'var(--kc-hell)',
      borderRadius: 'var(--kc-radius-md)',
      border: '1px solid var(--kc-rand)',
      textAlign: 'center',
    }}>
      <div style={{ fontSize: 'var(--kc-text-xs)', color: 'var(--kc-text-subtil)', marginBottom: 'var(--kc-space-1)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
        {label}
      </div>
      <div style={{ fontSize: 'var(--kc-text-xl)', fontFamily: 'var(--kc-font-mono)', fontWeight: 700, color }}>
        {value}
      </div>
      <div style={{ fontSize: 'var(--kc-text-xs)', color: 'var(--kc-mittel)', marginTop: 'var(--kc-space-1)' }}>
        {hint}
      </div>
    </div>
  );
}

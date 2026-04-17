import React, { useEffect, useRef, useState } from 'react';
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  Radar,
  ResponsiveContainer,
  Tooltip as ReTooltip,
} from 'recharts';
import * as echarts from 'echarts';
import { useScreenSize } from '../utils/responsive';
import { useAuth } from '../context/AuthContext';
import API_BASE_URL from '../config';

const LEVEL_STYLES = {
  'Homepage Standard Platin': { bg: '#e8eaf6', color: '#283593', icon: '\uD83C\uDFC6' },
  'Homepage Standard Gold':   { bg: '#fff8e1', color: '#f57f17', icon: '\uD83E\uDD47' },
  'Homepage Standard Silber': { bg: '#f5f5f5', color: '#616161', icon: '\uD83E\uDD48' },
  'Homepage Standard Bronze': { bg: '#efebe9', color: '#4e342e', icon: '\uD83E\uDD49' },
  'Nicht konform':            { bg: '#fdecea', color: '#C8102E', icon: '⛔' },
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
      { key: 'rc_datenschutz',  label: 'Datenschutzerklärung (DSGVO)', max: 7 },
      { key: 'rc_cookie',       label: 'Cookie Consent (TDDDG)',            max: 6 },
      { key: 'rc_bfsg',         label: 'Barrierefreiheitserklärung (BFSG)', max: 4 },
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
      { key: 'tp_cls',    label: 'CLS (Layout-Stabilität)', max: 4 },
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
      { key: 'bf_tastatur',     label: 'Tastaturzugänglichkeit',       max: 5 },
      { key: 'bf_screenreader', label: 'Screenreader-Kompatibilität', max: 5 },
      { key: 'bf_lesbarkeit',   label: 'Lesbarkeit & Textgröße', max: 5 },
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
      { key: 'ux_content',     label: 'Content-Qualität',     max: 1 },
      { key: 'ux_kontakt',     label: 'Kontaktmöglichkeiten', max: 1 },
    ],
  },
];

const HOSTING_ITEMS = [
  { key: 'ho_anbieter', label: 'Anbieter identifizierbar' },
  { key: 'ho_uptime',   label: 'Erreichbarkeit' },
  { key: 'ho_http',     label: 'HTTP→HTTPS Weiterleitung' },
  { key: 'ho_backup',   label: 'Backup-Hinweise' },
  { key: 'ho_cdn',      label: 'CDN aktiv' },
];

function scoreColor(score, max) {
  if (max === 0) return 'var(--text-tertiary)';
  const pct = score / max;
  if (pct >= 1.0) return 'var(--status-success-text)';
  if (pct >= 0.5) return 'var(--status-warning-text)';
  return 'var(--brand-primary)';
}

function scoreIcon(score, max) {
  if (max === 0) return '—';
  const pct = score / max;
  if (pct >= 1.0) return '✓';
  if (pct >= 0.5) return '⚠';
  return '✗';
}

// ═══════════════════════════════════════════════════════════
// Main Component
// ═══════════════════════════════════════════════════════════

export default function AuditReport({ auditData, onClose }) {
  const { isMobile } = useScreenSize();
  const { token } = useAuth();
  const [angebotLoading, setAngebotLoading] = useState(false);

  const createAngebot = async () => {
    setAngebotLoading(true);
    try {
      const res = await fetch(
        `${API_BASE_URL}/api/audit/${auditData.id}/angebot`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (!res.ok) throw new Error("Fehler");
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `Angebot-KOMPAGNON-${auditData.company_name}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      alert("Angebot konnte nicht erstellt werden.");
    } finally { setAngebotLoading(false); }
  };

  if (!auditData) return null;

  const r = auditData;
  const ls = LEVEL_STYLES[r.level] || LEVEL_STYLES['Nicht konform'];

  // Debug: log the raw API response to verify field names
  console.log('[AuditReport] auditData:', r);

  // r.result is a fallback for response shapes that nest data one level deeper
  const res = r.result || r;

  // Support: res.items.key (from _format_audit), res.key (flat DB), r.result.key
  const itemsRaw = r.items || r.result?.items || r.result || {};
  const items = {};
  for (const cat of CATEGORIES) {
    for (const item of cat.items) {
      items[item.key] = itemsRaw[item.key] ?? res[item.key] ?? r[item.key] ?? 0;
    }
  }
  for (const hi of HOSTING_ITEMS) {
    items[hi.key] = itemsRaw[hi.key] ?? res[hi.key] ?? r[hi.key] ?? 0;
  }

  const checks = res.checks || r.checks || {
    ssl_ok: res.ssl_ok ?? r.ssl_ok,
    impressum_ok: res.impressum_ok ?? r.impressum_ok,
    datenschutz_ok: res.datenschutz_ok ?? r.datenschutz_ok,
    lcp_value: res.lcp_value ?? r.lcp_value,
    cls_value: res.cls_value ?? r.cls_value,
    inp_value: res.inp_value ?? r.inp_value,
    mobile_score: res.mobile_score ?? r.mobile_score,
    performance_score: res.performance_score ?? r.performance_score,
  };

  // Parse JSON fields if needed
  let topIssues = r.top_issues || [];
  let recommendations = r.recommendations || [];
  try {
    if (typeof topIssues === 'string') topIssues = JSON.parse(topIssues);
    if (typeof recommendations === 'string') recommendations = JSON.parse(recommendations);
  } catch (e) { /* ignore */ }

  // Mapping from CATEGORIES key → flat score field
  const CAT_SCORE_FIELD = {
    'rechtliche_compliance':  'rc_score',
    'technische_performance': 'tp_score',
    'barrierefreiheit':       'bf_score',
    'sicherheit_datenschutz': 'si_score',
    'seo_sichtbarkeit':       'se_score',
    'inhalt_nutzererfahrung': 'ux_score',
  };

  // Build category score: try direct score keys, then categories object, then sum items
  const getCatScore = (catKey, catMax) => {
    // 1. Direct score keys (multiple naming conventions)
    const directKeys = {
      rechtliche_compliance:  ['rc_score', 'rc_gesamt'],
      technische_performance: ['tp_score', 'tp_gesamt'],
      barrierefreiheit:       ['bf_score', 'bf_gesamt'],
      sicherheit_datenschutz: ['si_score', 'si_gesamt'],
      seo_sichtbarkeit:       ['se_score', 'se_gesamt'],
      inhalt_nutzererfahrung: ['ux_score', 'ux_gesamt'],
    };
    const keys = directKeys[catKey] || [];
    for (const k of keys) {
      const v = r.result?.[k] ?? r[k];
      if (v !== undefined && v !== null) return Math.round(Number(v));
    }
    // 2. categories object (from _format_audit or r.result.categories)
    const cat = r.result?.categories?.[catKey];
    if (cat?.score !== undefined) return Math.round(Number(cat.score));
    // 3. Flat score field via CAT_SCORE_FIELD map
    const field = CAT_SCORE_FIELD[catKey];
    if (field) {
      if (res[field] != null) return Math.round(Number(res[field]));
      if (r[field] != null) return Math.round(Number(r[field]));
    }
    // 4. Sum individual item scores
    const catDef = CATEGORIES.find(c => c.key === catKey);
    if (!catDef) return 0;
    return Math.min(catDef.items.reduce((sum, item) => sum + (items[item.key] || 0), 0), catMax);
  };

  const radarData = CATEGORIES.map((cat) => {
    const catScore = getCatScore(cat.key, cat.max);
    return {
      subject: cat.shortLabel,
      score: cat.max > 0 ? Math.round((Math.min(catScore, cat.max) / cat.max) * 100) : 0,
      fullMark: 100,
    };
  });

  const hasHostingData = HOSTING_ITEMS.some((hi) => items[hi.key] !== undefined && items[hi.key] !== 0);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', position: 'relative' }}>
      {/* Close button */}
      {onClose && (
        <button
          onClick={onClose}
          style={{
            position: 'absolute', top: 16, right: 16, zIndex: 200,
            background: 'rgba(0,0,0,0.15)', border: 'none', borderRadius: '50%',
            width: 36, height: 36, fontSize: 18, cursor: 'pointer', color: '#fff',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}
        >
          ×
        </button>
      )}
      {/* Angebot Button */}
      {auditData.id && auditData.status === "completed" && (
        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
          <button
            onClick={createAngebot}
            disabled={angebotLoading}
            title="Erstellt ein fertiges PDF-Angebot auf Basis dieses Audit-Ergebnisses"
            style={{
              background: '#1D9E75', color: '#fff', border: 'none',
              borderRadius: 8, padding: '8px 16px', fontSize: 13,
              fontWeight: 600, cursor: 'pointer', display: 'flex',
              alignItems: 'center', gap: 6,
            }}
          >
            {angebotLoading ? '⏳ Wird erstellt...' : '📄 Angebot erstellen'}
          </button>
        </div>
      )}

      {/* Score Hero */}
      <div
        className="kc-card"
        style={{
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          flexDirection: 'column', gap: '16px',
          padding: 'var(--kc-space-10)',
          background: ls.bg, borderColor: ls.color,
        }}
      >
        <div style={{
          fontFamily: 'var(--font-sans)', fontSize: '4rem', fontWeight: 700,
          color: ls.color, lineHeight: 1,
        }}>
          {r.total_score}
          <span style={{ fontSize: '22px', fontWeight: 400, color: 'var(--text-tertiary)' }}> / 100</span>
        </div>
        <div style={{
          display: 'inline-flex', alignItems: 'center', gap: '8px',
          padding: '8px 24px',
          borderRadius: 'var(--radius-md)',
          background: 'var(--bg-surface)', border: `2px solid ${ls.color}`,
          fontWeight: 700, fontSize: '16px', color: ls.color,
        }}>
          {ls.icon} {r.level}
        </div>
        <p style={{ color: 'var(--text-tertiary)', fontSize: '13px', textAlign: 'center' }}>
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
      <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : 'repeat(auto-fit, minmax(300px, 1fr))', gap: '16px' }}>
        {/* Radar Chart */}
        <div className="kc-card">
          <span >Übersicht</span>
          <h3 style={{ marginBottom: '12px', fontSize: '14px' }}>Kategorien-Profil</h3>
          <ResponsiveContainer width="100%" height={isMobile ? 200 : 240}>
            <RadarChart data={radarData} margin={{ top: 10, right: 20, bottom: 10, left: 20 }}>
              <PolarGrid stroke="var(--border-light)" />
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
          <span >Bewertung</span>
          <h3 style={{ marginBottom: '16px', fontSize: '14px' }}>Kategorie-Scores</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {CATEGORIES.map((cat) => {
              const catScore = getCatScore(cat.key, cat.max);
              const pct = cat.max > 0 ? (catScore / cat.max) * 100 : 0;
              const color = scoreColor(catScore, cat.max);
              return (
                <div key={cat.key}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                    <span style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-secondary)' }}>
                      {cat.label}
                    </span>
                    <span style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', fontWeight: 700, color }}>
                      {catScore}/{cat.max}
                    </span>
                  </div>
                  <div style={{ height: '6px', background: 'var(--border-light)', borderRadius: 'var(--radius-full)', overflow: 'hidden' }}>
                    <div style={{
                      height: '100%', width: `${pct}%`, background: color,
                      borderRadius: 'var(--radius-full)', transition: 'width 0.8s ease',
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
        <div  style={{ marginBottom: '16px' }}>
          <span >Details</span>
          <h2>Einzelkriterien</h2>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {CATEGORIES.map((cat) => (
              <CategorySection
                key={cat.key}
                category={cat}
                catScore={getCatScore(cat.key, cat.max)}
                items={items}
              />
          ))}
        </div>
      </div>

      {/* Hosting & Infrastruktur */}
      {hasHostingData && (
        <div className="kc-card">
          <span >Infrastruktur</span>
          <h3 style={{ marginBottom: '16px', fontSize: '14px' }}>Hosting & Infrastruktur</h3>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
            {HOSTING_ITEMS.map((hi) => {
              const val = items[hi.key];
              const ok = val === 1 || val === true;
              return (
                <span
                  key={hi.key}
                  style={{
                    display: 'inline-flex', alignItems: 'center', gap: '6px',
                    padding: '4px 12px',
                    borderRadius: 'var(--radius-md)',
                    background: ok ? 'var(--status-success-bg)' : 'var(--status-danger-bg)',
                    border: `1px solid ${ok ? 'var(--status-success-text)' : 'var(--brand-primary)'}`,
                    fontSize: '11px', fontWeight: 600,
                    color: ok ? 'var(--status-success-text)' : 'var(--brand-primary)',
                  }}
                >
                  {ok ? '✓' : '✗'} {hi.label}
                </span>
              );
            })}
          </div>
        </div>
      )}

      {/* Core Web Vitals */}
      {(checks.lcp_value != null || checks.cls_value != null || checks.inp_value != null || checks.mobile_score != null) && (
        <div className="kc-card">
          <span >Messwerte</span>
          <h3 style={{ marginBottom: '16px', fontSize: '14px' }}>Core Web Vitals</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '12px' }}>
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
          <span  style={{ color: 'var(--kc-info, #2196f3)' }}>KI-Analyse</span>
          <h3 style={{ marginBottom: '12px', fontSize: '14px' }}>
            Was bedeutet das für Ihren Betrieb?
          </h3>
          <p style={{ color: 'var(--text-secondary)', lineHeight: 'var(--kc-leading-normal)', fontSize: '14px' }}>
            {r.ai_summary}
          </p>
        </div>
      )}

      {/* Issues + Recommendations */}
      <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
        {topIssues.length > 0 && (
          <div className="kc-card" style={{ background: 'var(--color-bg-surface, var(--bg-surface))', border: '1px solid var(--border-light)' }}>
            <strong style={{ display: 'block', marginBottom: '12px', fontFamily: 'var(--font-sans)', color: 'var(--status-danger-text)' }}>
              Top-Probleme
            </strong>
            <ul style={{ margin: 0, paddingLeft: '24px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {topIssues.map((issue, i) => (
                <li key={i} style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>{typeof issue === 'string' ? issue : issue?.title || issue?.issue || ''}</li>
              ))}
            </ul>
          </div>
        )}
        {recommendations.length > 0 && (
          <div className="kc-card" style={{ background: 'var(--color-bg-surface, var(--bg-surface))', border: '1px solid var(--border-light)' }}>
            <strong style={{ display: 'block', marginBottom: '12px', fontFamily: 'var(--font-sans)', color: 'var(--status-success-text)' }}>
              Empfehlungen
            </strong>
            <ol style={{ margin: 0, paddingLeft: '24px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {recommendations.map((rec, i) => (
                <li key={i} style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>{typeof rec === 'string' ? rec : rec?.title || ''}</li>
              ))}
            </ol>
          </div>
        )}
      </div>

      {/* ── BLOCK 1: Alert Banner ── */}
      {(() => {
        const score = r.total_score || 0;
        const notOk = r.level === 'Nicht konform' || score < 40;
        const partial = !notOk && score < 70;
        if (!notOk && !partial) return null;
        const bg    = notOk ? '#FFF7ED' : '#EFF6FF';
        const border= notOk ? '#F97316' : '#3B82F6';
        const color = notOk ? '#9A3412' : '#1E40AF';
        const icon  = notOk ? '⚠️' : 'ℹ️';
        const text  = notOk
          ? 'Handlungsbedarf: Diese Website erfüllt den Homepage Standard 2025 nicht. Die wichtigsten Probleme sind unten aufgeführt.'
          : 'Gutes Fundament — gezielte Optimierungen bringen Sie auf Gold-Niveau.';
        return (
          <div style={{ display: 'flex', gap: 12, alignItems: 'flex-start', background: bg, border: `1px solid ${border}`, borderRadius: 10, padding: '14px 18px' }}>
            <span style={{ fontSize: 22, flexShrink: 0 }}>{icon}</span>
            <p style={{ margin: 0, fontSize: 14, color, lineHeight: 1.6 }}>{text}</p>
          </div>
        );
      })()}

      {/* ── BLOCK 3: GEO / KI Readiness ── */}
      {(() => {
        const llmsTxt    = !!(r.llms_txt ?? false);
        const robotsOk   = !!(r.robots_ai_friendly ?? false);
        const schemaOk   = !!(r.structured_data ?? (r.se_schema > 0));
        const aiMentions = r.ai_mentions ?? 0;
        const aiOverview = (r.se_score || 0) >= 7;
        const rows = [
          { label: 'llms.txt vorhanden',      ok: llmsTxt,    rec: llmsTxt    ? 'Vorhanden ✓'                      : 'Datei unter /llms.txt anlegen' },
          { label: 'robots.txt KI-freundlich', ok: robotsOk,   rec: robotsOk   ? 'KI-Crawler erlaubt ✓'             : 'GPTBot nicht blockieren' },
          { label: 'Strukturierte Daten',      ok: schemaOk,   rec: schemaOk   ? 'Schema.org vorhanden ✓'           : 'Schema.org LocalBusiness ergänzen' },
          { label: 'KI-Erwähnungen',           ok: aiMentions > 0, rec: aiMentions > 0 ? `${aiMentions} gefunden ✓` : 'Content-Authority aufbauen' },
          { label: 'Google AI Overview',       ok: aiOverview, rec: aiOverview  ? 'Gut aufgestellt ✓'               : 'Featured Snippets optimieren' },
        ];
        return (
          <div className="kc-card">
            <strong style={{ display: 'block', marginBottom: 12, fontSize: 14 }}>🤖 GEO & KI-Sichtbarkeit</strong>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <thead>
                <tr style={{ background: 'var(--bg-elevated, #F9FAFB)' }}>
                  <th style={{ padding: '8px 10px', textAlign: 'left', fontWeight: 600, color: 'var(--text-secondary, #374151)', borderBottom: '1px solid var(--border-light, #E5E7EB)' }}>Prüfpunkt</th>
                  <th style={{ padding: '8px 10px', textAlign: 'center', fontWeight: 600, color: 'var(--text-secondary, #374151)', borderBottom: '1px solid var(--border-light, #E5E7EB)', width: 70 }}>Status</th>
                  <th style={{ padding: '8px 10px', textAlign: 'left', fontWeight: 600, color: 'var(--text-secondary, #374151)', borderBottom: '1px solid var(--border-light, #E5E7EB)' }}>Empfehlung</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row, i) => (
                  <tr key={i} style={{ background: i % 2 === 0 ? 'var(--bg-surface, #fff)' : 'var(--bg-elevated, #F9FAFB)' }}>
                    <td style={{ padding: '8px 10px', color: 'var(--text-secondary, #374151)', borderBottom: '1px solid var(--border-light, #F3F4F6)' }}>{row.label}</td>
                    <td style={{ padding: '8px 10px', textAlign: 'center', fontSize: 18, borderBottom: '1px solid var(--border-light, #F3F4F6)' }}>
                      <span style={{ color: row.ok ? 'var(--status-success-text, #16a34a)' : 'var(--status-danger-text, #DC2626)' }}>{row.ok ? '✓' : '✗'}</span>
                    </td>
                    <td style={{ padding: '8px 10px', color: 'var(--text-tertiary, #6B7280)', borderBottom: '1px solid var(--border-light, #F3F4F6)' }}>{row.rec}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );
      })()}

      {/* ── BLOCK 4: Roadmap ── */}
      {(() => {
        const score = r.total_score || 0;
        const llmsTxt  = !!(r.llms_txt ?? false);
        const schemaOk = !!(r.structured_data ?? (r.se_schema > 0));
        const robotsOk = !!(r.robots_ai_friendly ?? false);
        const mobilePs = r.mobile_score || 0;

        const phase1 = [];
        if (!llmsTxt)   phase1.push('llms.txt anlegen (ca. 1 Tag)');
        if (!schemaOk)  phase1.push('Schema.org LocalBusiness einbauen');
        if (mobilePs < 50) phase1.push('Bilder komprimieren & Lazy Load aktivieren');
        if (!robotsOk)  phase1.push('robots.txt: GPTBot-Blockierung entfernen');
        if (!phase1.length) phase1.push('Audit-Score weiter optimieren & Inhalte aktualisieren');

        const phase2 = ['Regelmäßige Blog-Inhalte für SEO-Autorität aufbauen'];
        if (r.level === 'Nicht konform') phase2.push('SSL, Datenschutz & Impressum prüfen und korrigieren');
        if (!schemaOk) phase2.push('Weitere Schema.org-Typen (FAQPage, Review) ergänzen');

        const phase3 = [
          'Backlink-Aufbau über lokale Verzeichnisse und Branchenportale',
          'Google Business Profil optimieren und regelmäßig pflegen',
          'KI-Sichtbarkeit: Erwähnungen in Fachartikeln & Podcasts aufbauen',
        ];

        const phases = [
          { label: 'Phase 1', title: 'Quick Wins', period: 'Woche 1–2', items: phase1, bg: '#F0FDF4', border: '#16a34a', headerBg: '#16a34a' },
          { label: 'Phase 2', title: 'Mittelfristig', period: 'Monat 1–3', items: phase2, bg: '#EFF6FF', border: '#2563EB', headerBg: '#2563EB' },
          { label: 'Phase 3', title: 'Langfristig', period: 'Monat 3–6', items: phase3, bg: '#FAF5FF', border: '#7C3AED', headerBg: '#7C3AED' },
        ];
        return (
          <div>
            <strong style={{ display: 'block', marginBottom: 12, fontSize: 14 }}>📋 Maßnahmen-Roadmap</strong>
            <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : 'repeat(3, 1fr)', gap: 12 }}>
              {phases.map(ph => (
                <div key={ph.label} style={{ borderRadius: 10, overflow: 'hidden', border: `1px solid ${ph.border}` }}>
                  <div style={{ background: ph.headerBg, padding: '10px 14px' }}>
                    <div style={{ color: 'white', fontWeight: 700, fontSize: 13 }}>{ph.label} — {ph.title}</div>
                    <div style={{ color: 'rgba(255,255,255,0.75)', fontSize: 11 }}>{ph.period}</div>
                  </div>
                  <div style={{ background: ph.bg, padding: '12px 14px' }}>
                    <ul style={{ margin: 0, paddingLeft: 18, display: 'flex', flexDirection: 'column', gap: 6 }}>
                      {ph.items.map((item, i) => (
                        <li key={i} style={{ fontSize: 12, color: 'var(--text-secondary, #374151)', lineHeight: 1.5 }}>{item}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              ))}
            </div>
          </div>
        );
      })()}

      {/* Certification */}
      {r.level && r.total_score != null && (
        <div className="kc-card" style={{
          textAlign: 'center', padding: '32px',
          borderTop: `3px solid ${ls.color}`,
        }}>
          <h3 style={{ fontFamily: 'var(--font-sans)', fontSize: '16px', marginBottom: '16px' }}>
            Zertifizierungsaussage
          </h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '13px', lineHeight: 'var(--kc-leading-normal)', maxWidth: '600px', margin: '0 auto' }}>
            Hiermit wird bestätigt, dass die geprüfte Website <strong>{r.website_url}</strong> zum Zeitpunkt des Audits
            den Anforderungen des <strong>{r.level}</strong> entspricht
            und eine Gesamtbewertung von <strong>{r.total_score} / 100 Punkten</strong> erzielt hat.
          </p>
          <p style={{ color: 'var(--text-tertiary)', fontSize: '11px', marginTop: '16px' }}>
            Auditor: KOMPAGNON Communications
          </p>
        </div>
      )}
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
          padding: '12px 16px',
          background: 'none', border: 'none', cursor: 'pointer', textAlign: 'left',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ width: '4px', height: '20px', borderRadius: '2px', background: category.color, flexShrink: 0 }} />
          <span style={{ fontWeight: 700, fontSize: '13px', color: 'var(--text-primary)' }}>
            {category.label}
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontSize: '13px', fontFamily: 'var(--font-mono)', fontWeight: 700, color }}>
            {catScore}/{category.max}
          </span>
          <span style={{ fontSize: '11px', color: 'var(--text-tertiary)' }}>
            {expanded ? '▲' : '▼'}
          </span>
        </div>
      </button>

      {expanded && (
        <div style={{
          borderTop: '1px solid var(--border-light)',
          padding: '12px 16px',
          display: 'flex', flexDirection: 'column', gap: '8px',
          background: 'var(--bg-app)',
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
                  gap: '12px',
                  alignItems: 'center',
                }}
              >
                <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
                  {item.label}
                </span>
                <div style={{ height: '5px', background: 'var(--border-light)', borderRadius: 'var(--radius-full)', overflow: 'hidden' }}>
                  <div style={{
                    height: '100%', width: `${pct}%`, background: icolor,
                    borderRadius: 'var(--radius-full)', transition: 'width 0.5s ease',
                  }} />
                </div>
                <span style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: icolor, textAlign: 'right', fontWeight: 600 }}>
                  {score}/{item.max}
                </span>
                <span style={{ fontSize: '11px', color: icolor, fontWeight: 700, textAlign: 'center' }}>
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
// ECharts Radar (Block 2)
// ═══════════════════════════════════════════════════════════

const RADAR_INDICATORS = [
  { name: 'SEO & Keywords', max: 10 },
  { name: 'Performance',    max: 10 },
  { name: 'Sicherheit',     max: 10 },
  { name: 'Inhalt & UX',    max: 10 },
  { name: 'Rechtliches',    max: 10 },
  { name: 'GEO / KI',       max: 10 },
];

function EChartsRadar({ auditData: r, getCatScore }) {
  const radarRef = useRef(null);

  const vals = [
    Math.round((Math.min(getCatScore('seo_sichtbarkeit', 10),   10)  / 10)  * 10),
    Math.round((Math.min(getCatScore('technische_performance',20),20) / 20)  * 10),
    Math.round((Math.min(getCatScore('sicherheit_datenschutz',15),15)/ 15)  * 10),
    Math.round((Math.min(getCatScore('inhalt_nutzererfahrung', 5),  5)  / 5)  * 10),
    Math.round((Math.min(getCatScore('rechtliche_compliance',  30), 30) / 30) * 10),
    Math.round(((r.geo_score || 0) / 10) * 10),
  ];

  useEffect(() => {
    if (!radarRef.current) return;
    const chart = echarts.init(radarRef.current);
    chart.setOption({
      backgroundColor: 'transparent',
      radar: {
        indicator: RADAR_INDICATORS,
        splitNumber: 5,
        axisName: { color: 'var(--text-secondary, #374151)', fontSize: 11 },
        splitLine: { lineStyle: { color: '#E5E7EB' } },
        splitArea: { show: false },
        axisLine: { lineStyle: { color: '#E5E7EB' } },
      },
      series: [{
        type: 'radar',
        data: [{ value: vals, name: 'Score (0–10)' }],
        lineStyle: { color: '#0d6efd', width: 2 },
        areaStyle: { color: 'rgba(13,110,253,0.18)' },
        symbol: 'circle',
        symbolSize: 5,
        itemStyle: { color: '#0d6efd' },
      }],
      tooltip: { trigger: 'item' },
    });
    const onResize = () => chart.resize();
    window.addEventListener('resize', onResize);
    return () => { window.removeEventListener('resize', onResize); chart.dispose(); };
  }, [r.id]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="kc-card">
      <strong style={{ display: 'block', marginBottom: 8, fontSize: 14 }}>Kategorien-Radar (interaktiv)</strong>
      <div ref={radarRef} style={{ width: '100%', height: 320 }} />
    </div>
  );
}

// ═══════════════════════════════════════════════════════════
// Metric Card
// ═══════════════════════════════════════════════════════════

function MetricCard({ label, value, hint, ok, warn }) {
  const color = ok ? 'var(--status-success-text)' : warn ? 'var(--status-warning-text)' : 'var(--brand-primary)';
  return (
    <div style={{
      padding: '16px',
      background: 'var(--bg-app)',
      borderRadius: 'var(--radius-md)',
      border: '1px solid var(--border-light)',
      textAlign: 'center',
    }}>
      <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', marginBottom: '4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
        {label}
      </div>
      <div style={{ fontSize: '18px', fontFamily: 'var(--font-mono)', fontWeight: 700, color }}>
        {value}
      </div>
      <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', marginTop: '4px' }}>
        {hint}
      </div>
    </div>
  );
}

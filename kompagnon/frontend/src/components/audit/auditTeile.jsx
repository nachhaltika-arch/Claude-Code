/**
 * Kategorieabschnitt und Netzdiagramm des Auditberichts (L-25).
 *
 * Am 2026-08-30 aus `AuditReport.jsx` herausgeloest — 180 Zeilen. Beide waren
 * dort schon eigene Funktionen.
 */
import React, { useEffect, useRef, useState } from 'react';
import * as echarts from 'echarts';

import { SOURCE_BADGES, scoreColor, scoreIcon } from './auditDaten';

export function CategorySection({ category }) {
  const [expanded, setExpanded] = React.useState(true);
  const catScore = category.score;
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
          {category.criteria.map((item) => {
            const score = item.score ?? 0;
            const notCollected = item.collected === false;
            const pct = item.max > 0 ? (score / item.max) * 100 : 0;
            const icolor = notCollected ? 'var(--text-tertiary)' : scoreColor(score, item.max);
            const badge = SOURCE_BADGES[item.source] || null;

            return (
              <div
                key={item.key}
                style={{
                  display: 'grid',
                  gridTemplateColumns: '16px 1fr 100px 48px 20px',
                  gap: '12px',
                  alignItems: 'center',
                  opacity: notCollected ? 0.55 : 1,
                }}
              >
                <span
                  title={badge ? badge.title : ''}
                  style={{ fontSize: '11px', color: badge ? badge.color : 'transparent' }}
                >
                  {badge ? badge.icon : ''}
                </span>
                <span
                  title={item.hint || ''}
                  style={{ fontSize: '11px', color: 'var(--text-secondary)' }}
                >
                  {item.label}
                </span>
                <div style={{ height: '5px', background: 'var(--border-light)', borderRadius: 'var(--radius-full)', overflow: 'hidden' }}>
                  {!notCollected && (
                    <div style={{
                      height: '100%', width: `${pct}%`, background: icolor,
                      borderRadius: 'var(--radius-full)', transition: 'width 0.5s ease',
                    }} />
                  )}
                </div>
                <span style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: icolor, textAlign: 'right', fontWeight: 600 }}>
                  {notCollected ? '–' : `${score}/${item.max}`}
                </span>
                <span style={{ fontSize: '11px', color: icolor, fontWeight: 700, textAlign: 'center' }}>
                  {notCollected ? '○' : scoreIcon(score, item.max)}
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

export const RADAR_INDICATORS = [
  { name: 'SEO & Keywords', max: 10 },
  { name: 'Performance',    max: 10 },
  { name: 'Sicherheit',     max: 10 },
  { name: 'Inhalt & UX',    max: 10 },
  { name: 'Rechtliches',    max: 10 },
  { name: 'GEO / KI',       max: 10 },
];

export function EChartsRadar({ auditData: r, getCatScore }) {
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
        axisName: { color: '#374151', fontSize: 11 },
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

export function MetricCard({ label, value, hint, ok, warn }) {
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

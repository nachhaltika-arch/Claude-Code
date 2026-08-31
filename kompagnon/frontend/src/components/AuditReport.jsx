import React, { useState } from 'react';
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  Radar,
  ResponsiveContainer,
  Tooltip as ReTooltip,
} from 'recharts';
import { useScreenSize } from '../utils/responsive';
import { useAuth } from '../context/AuthContext';
import API_BASE_URL from '../config';
import { datumKurz } from '../utils/datum';
import { fassungText } from '../utils/fassung';
import {
  CATEGORIES, COLLECTION_REASONS, HOSTING_ITEMS, LEVEL_STYLES,
  SOURCE_BADGES, buildViewCategories, scoreColor,
} from './audit/auditDaten';
import { CategorySection, MetricCard } from './audit/auditTeile';

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

  // Ab 2026-08-11 liefert die API den Kriterienkatalog mit (Labels, Punkte,
  // Quellen). Ältere Audits haben das nicht — für die bleibt die frühere
  // Darstellung aus der fest verdrahteten Liste erhalten.
  const viewCategories = buildViewCategories(r) || CATEGORIES.map((cat) => ({
    ...cat,
    score: getCatScore(cat.key, cat.max),
    criteria: cat.items.map((item) => ({
      ...item,
      score: items[item.key] ?? 0,
      collected: true,
    })),
  }));

  const blockers = Array.isArray(r.blockers) ? r.blockers : [];
  const coverage = typeof r.coverage === 'number' ? r.coverage : null;
  // Über wie viele Seiten geurteilt wurde. Ergebnisse von vor dem 21.08.2026
  // kannten nur die Startseite; ohne diese Angabe liest jemand eine alte Note
  // wie eine neue.
  const seitenGeprueft = typeof r.seiten_geprueft === 'number' ? r.seiten_geprueft : 1;
  const seitenGefunden = typeof r.seiten_gefunden === 'number' ? r.seiten_gefunden : null;
  const collectionNotes = r.collection_notes && typeof r.collection_notes === 'object'
    ? r.collection_notes
    : {};

  const radarData = viewCategories.map((cat) => ({
    subject: cat.shortLabel || cat.label,
    score: cat.max > 0 ? Math.round((Math.min(cat.score, cat.max) / cat.max) * 100) : 0,
    fullMark: 100,
  }));

  const hasHostingData = HOSTING_ITEMS.some((hi) => items[hi.key] !== undefined && items[hi.key] !== 0);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', position: 'relative' }}>
      {/* Close button */}
      {onClose && (
        <button aria-label="Schließen"
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
              background: 'var(--success)', color: 'var(--text-inverse)', border: 'none',
              borderRadius: 8, padding: '8px 16px', fontSize: 13,
              fontWeight: 600, cursor: 'pointer', display: 'flex',
              alignItems: 'center', gap: 6,
            }}
          >
            {angebotLoading ? '⏳ Wird erstellt...' : '📄 Angebot erstellen'}
          </button>
        </div>
      )}

      {/* EINORDNUNG — steht vor der Punktzahl. Wer eine Zahl über seine
          eigene Arbeit liest, muss vorher sehen, dass sein Geschäft
          verstanden wurde; sonst liest er sie als Urteil eines Fremden. */}
      {(r.erkannte_branche || r.branchenklasse) && (
        <div style={{
          fontSize: 13, lineHeight: 1.6, color: 'var(--text-secondary)',
          background: 'var(--bg-hover)', border: '1px solid var(--border-light)',
          borderRadius: 'var(--radius-md)', padding: '10px 14px',
        }}>
          {r.branchenklasse === 'K6' ? (
            <>Eingeordnet als <strong>{r.erkannte_branche || r.branchenklasse_bezeichnung}</strong>.
              {' '}Der Homepage Standard ist auf Betriebe zugeschnitten — die
              angebotsbezogenen Kriterien gelten hier nicht und zählen nicht mit.</>
          ) : (
            <>Bewertet als <strong>{r.erkannte_branche || r.branchenklasse_bezeichnung}</strong>
              {r.branchenklasse_bezeichnung && <> — Maßstab: {r.branchenklasse_bezeichnung}</>}.</>
          )}
        </div>
      )}

      {/* Die Fassung, gegen die bewertet wurde (S6.2). Das Backend setzt sie
          seit 2026.2 und liefert sie aus; gelesen hat sie bis zum 24.08.2026
          niemand. Ein Ergebnis ohne Massstab ist keine Aussage — und zwei
          Ergebnisse aus zwei Fassungen sind nicht dasselbe Ergebnis. */}
      <div style={{
        fontSize: 12, color: 'var(--text-tertiary)',
        fontFamily: 'var(--font-mono)', textAlign: 'right',
      }}>
        Homepage Standard · {fassungText(r.standard_version)}
      </div>

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
            <span> &middot; {datumKurz(r.created_at)}</span>
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
                tick={{ fontSize: 12, fill: '#555' }}
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
            {viewCategories.map((cat) => {
              const catScore = cat.score;
              const pct = cat.max > 0 ? (catScore / cat.max) * 100 : 0;
              const color = scoreColor(catScore, cat.max);
              const partial = cat.nominalMax != null && cat.max < cat.nominalMax;
              return (
                <div key={cat.key}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                    <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)' }}>
                      {cat.label}
                      {partial && (
                        <span
                          title={`Nur ${cat.max} von ${cat.nominalMax} Punkten konnten geprüft werden`}
                          style={{ marginLeft: 6, color: 'var(--text-tertiary)', fontWeight: 500 }}
                        >
                          (teilweise geprüft)
                        </span>
                      )}
                    </span>
                    <span style={{ fontSize: 12, fontFamily: 'var(--font-mono)', fontWeight: 700, color }}>
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

      {/* K.-o.-Kriterien: rechtliche Totalausfälle deckeln das Level */}
      {blockers.length > 0 && (
        <div
          className="kc-card"
          style={{ borderLeft: '4px solid var(--brand-primary)', background: '#FDECEA' }}
        >
          <span>Kritisch</span>
          <h3 style={{ marginBottom: '8px', fontSize: '14px' }}>
            Rechtliche Ausschlusskriterien
          </h3>
          <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '10px' }}>
            Diese Punkte begrenzen die Bewertung unabhängig vom erreichten Score.
          </p>
          <ul style={{ margin: 0, paddingLeft: '18px' }}>
            {blockers.map((b) => (
              <li key={b.key} style={{ fontSize: '12px', color: 'var(--text-primary)', marginBottom: 4 }}>
                {b.label}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Detailed Category Breakdown */}
      <div>
        <div  style={{ marginBottom: '16px' }}>
          <span >Details</span>
          <h2>Einzelkriterien</h2>
        </div>

        {coverage != null && (
          <div style={{
            display: 'flex', flexWrap: 'wrap', gap: '14px', alignItems: 'center',
            marginBottom: '12px', fontSize: 12, color: 'var(--text-tertiary)',
          }}>
            <span>{coverage}% der Kriterien konnten geprüft werden.</span>
            {seitenGeprueft > 1 && (
              <span>
                Bewertet wurden {seitenGeprueft} Seiten dieser Website
                {seitenGefunden && seitenGefunden > seitenGeprueft
                  ? ` von ${seitenGefunden} gefundenen`
                  : ''}.
              </span>
            )}
            {Object.entries(collectionNotes).map(([area, note]) => (
              <span
                key={area}
                title={note.detail || ''}
                style={{ color: 'var(--brand-primary)', fontWeight: 600 }}
              >
                {area}: {COLLECTION_REASONS[note.reason] || note.reason}
              </span>
            ))}
            {Object.entries(SOURCE_BADGES).map(([key, badge]) => (
              <span key={key} style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                <span style={{ color: badge.color }}>{badge.icon}</span>
                {badge.title}
              </span>
            ))}
          </div>
        )}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {viewCategories.map((cat) => (
            <CategorySection key={cat.key} category={cat} />
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
                    background: ok ? '#e8f5e9' : '#fdecea',
                    border: `1px solid ${ok ? 'var(--status-success-text)' : 'var(--brand-primary)'}`,
                    fontSize: 12, fontWeight: 600,
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
        <div className="kc-card" style={{ borderLeft: '4px solid var(--status-info-text, #2196f3)' }}>
          <span  style={{ color: 'var(--status-info-text, #2196f3)' }}>KI-Analyse</span>
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
          ? `Handlungsbedarf: Diese Website erfüllt den Homepage Standard ${fassungText(r.standard_version)} nicht. Die wichtigsten Probleme sind unten aufgeführt.`
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
                <tr style={{ background: 'var(--bg-app)' }}>
                  <th style={{ padding: '8px 10px', textAlign: 'left', fontWeight: 600, color: 'var(--text-secondary)', borderBottom: '1px solid var(--border-light)' }}>Prüfpunkt</th>
                  <th style={{ padding: '8px 10px', textAlign: 'center', fontWeight: 600, color: 'var(--text-secondary)', borderBottom: '1px solid var(--border-light)', width: 70 }}>Status</th>
                  <th style={{ padding: '8px 10px', textAlign: 'left', fontWeight: 600, color: 'var(--text-secondary)', borderBottom: '1px solid var(--border-light)' }}>Empfehlung</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row, i) => (
                  <tr key={i} style={{ background: i % 2 === 0 ? 'var(--bg-surface)' : 'var(--bg-app)' }}>
                    <td style={{ padding: '8px 10px', color: 'var(--text-primary)', borderBottom: '1px solid var(--border-light)' }}>{row.label}</td>
                    <td style={{ padding: '8px 10px', textAlign: 'center', fontSize: 18, borderBottom: '1px solid var(--border-light)' }}>
                      <span style={{ color: row.ok ? 'var(--status-success-text)' : 'var(--status-danger-text)' }}>{row.ok ? '✓' : '✗'}</span>
                    </td>
                    <td style={{ padding: '8px 10px', color: 'var(--text-tertiary)', borderBottom: '1px solid var(--border-light)' }}>{row.rec}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );
      })()}

      {/* ── BLOCK 4: Roadmap ── */}
      {(() => {
        // Kriterienwerte liegen unter r.items, Messwerte unter r.checks —
        // die frühere flache Form (r.se_schema) gibt es nicht mehr.
        const llmsTxt  = !!(r.llms_txt ?? false);
        const schemaOk = !!(r.structured_data ?? ((r.items?.se_schema ?? 0) > 0));
        const robotsOk = !!(r.robots_ai_friendly ?? false);
        const mobilePs = r.checks?.mobile_score ?? r.mobile_score ?? 0;

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
                    <div style={{ color: 'rgba(255,255,255,0.75)', fontSize: 12 }}>{ph.period}</div>
                  </div>
                  <div style={{ background: ph.bg, padding: '12px 14px' }}>
                    <ul style={{ margin: 0, paddingLeft: 18, display: 'flex', flexDirection: 'column', gap: 6 }}>
                      {ph.items.map((item, i) => (
                        <li key={i} style={{ fontSize: 12, color: 'var(--text-primary)', lineHeight: 1.5 }}>{item}</li>
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
          <p style={{ color: 'var(--text-tertiary)', fontSize: 12, marginTop: '16px' }}>
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


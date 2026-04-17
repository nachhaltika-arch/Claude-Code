import { useState, useEffect } from 'react';
import API_BASE_URL from '../config';

const scoreColor = (s) => s >= 70 ? '#00875A' : s >= 50 ? '#B8860B' : '#C0392B';

export default function LeadSeoSummary({ projectId, leadId, token }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!projectId && !leadId) { setLoading(false); return; }
    const url = projectId
      ? `${API_BASE_URL}/api/seo/result/${projectId}`
      : `${API_BASE_URL}/api/seo/result/by-lead/${leadId}`;
    fetch(url, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => r.ok ? r.json() : null)
      .then(d => { if (d) setData(d); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [projectId, leadId]); // eslint-disable-line

  if (loading || !data || data.status === 'not_found') return null;

  const hasData = data.status === 'completed';
  const kws = (data.top_keywords || []).filter(k => k.priority === 'hoch');
  const errors = (data.onpage_issues || []).filter(i => i.status === 'err');
  const topActions = (data.action_plan || []).slice(0, 3);

  return (
    <div style={{
      border: '0.5px solid var(--border, #D5E0E2)',
      borderRadius: 10, marginBottom: 16,
      overflow: 'hidden', background: 'var(--paper, #FAFAFA)',
    }}>
      {/* Header */}
      <div
        onClick={() => setOpen(!open)}
        style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '12px 16px', cursor: 'pointer',
          background: 'var(--surface, #F0F4F5)',
          borderBottom: open ? '0.5px solid var(--border, #D5E0E2)' : 'none',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{
            background: '#004F59', color: '#FAE600', fontSize: 10, fontWeight: 900,
            padding: '3px 8px', borderRadius: 4,
            textTransform: 'uppercase', letterSpacing: '.06em',
          }}>SEO</span>
          <span style={{ fontSize: 13, fontWeight: 700, color: 'var(--text, #000)' }}>SEO-Positionierung</span>
          {hasData && (
            <span style={{
              fontSize: 10, fontWeight: 700, padding: '2px 8px', borderRadius: 10,
              background: '#E3F6EF', color: '#00875A',
            }}>Analysiert</span>
          )}
          {data.status === 'running' && (
            <span style={{
              fontSize: 10, fontWeight: 700, padding: '2px 8px', borderRadius: 10,
              background: '#FFFBE0', color: '#B8860B',
            }}>Laeuft…</span>
          )}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          {hasData && (
            <span style={{
              fontSize: 14, fontWeight: 700,
              color: scoreColor(data.overall_score),
              fontFamily: "var(--font-display, 'Barlow Condensed')",
            }}>{data.overall_score}/100</span>
          )}
          <span style={{ fontSize: 12, color: 'var(--text-30, #9AACAE)' }}>{open ? '▲' : '▼'}</span>
        </div>
      </div>

      {/* Body */}
      {open && (
        <div style={{ padding: 16, fontFamily: 'var(--font-sans)' }}>
          {!hasData ? (
            <div style={{ fontSize: 12, color: 'var(--text-60, #4A5A5C)' }}>
              Analyse noch nicht abgeschlossen (Status: {data.status})
            </div>
          ) : (
            <>
              {/* Scores */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 8, marginBottom: 16 }}>
                {[
                  { v: data.overall_score, l: 'Gesamt' },
                  { v: data.keyword_score, l: 'Keywords' },
                  { v: data.onpage_score, l: 'On-Page' },
                  { v: data.competitor_score, l: 'Wettbewerb' },
                ].map(({ v, l }) => (
                  <div key={l} style={{
                    background: 'var(--surface, #F0F4F5)', borderRadius: 8,
                    padding: '10px 8px', textAlign: 'center',
                  }}>
                    <div style={{
                      fontSize: 22, fontWeight: 700, color: scoreColor(v),
                      fontFamily: "var(--font-display, 'Barlow Condensed')",
                    }}>{v ?? '–'}</div>
                    <div style={{ fontSize: 10, color: 'var(--text-30, #9AACAE)', marginTop: 3, textTransform: 'uppercase', letterSpacing: '.06em', fontWeight: 700 }}>{l}</div>
                  </div>
                ))}
              </div>

              {/* Top-Keywords */}
              {kws.length > 0 && (
                <div style={{ marginBottom: 12 }}>
                  <div style={{ fontSize: 10, fontWeight: 900, color: 'var(--text-30, #9AACAE)', textTransform: 'uppercase', letterSpacing: '.08em', marginBottom: 6 }}>Top-Keywords</div>
                  <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap' }}>
                    {kws.map((k, i) => (
                      <span key={i} style={{
                        fontSize: 11, fontWeight: 700,
                        padding: '3px 9px', borderRadius: 4,
                        background: '#FDECEA', color: '#C0392B',
                      }}>{k.keyword}</span>
                    ))}
                  </div>
                </div>
              )}

              {/* Kritische Probleme */}
              {errors.length > 0 && (
                <div style={{ marginBottom: 12 }}>
                  <div style={{ fontSize: 10, fontWeight: 900, color: 'var(--text-30, #9AACAE)', textTransform: 'uppercase', letterSpacing: '.08em', marginBottom: 6 }}>Kritische Probleme</div>
                  {errors.map((e, i) => (
                    <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                      <div style={{ width: 7, height: 7, borderRadius: '50%', background: '#E24B4A', flexShrink: 0 }} />
                      <span style={{ fontSize: 12, color: 'var(--text, #000)' }}>{e.label}</span>
                    </div>
                  ))}
                </div>
              )}

              {/* Top-3 Massnahmen */}
              {topActions.length > 0 && (
                <div>
                  <div style={{ fontSize: 10, fontWeight: 900, color: 'var(--text-30, #9AACAE)', textTransform: 'uppercase', letterSpacing: '.08em', marginBottom: 6 }}>Sofortmassnahmen</div>
                  <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap' }}>
                    {topActions.map((a, i) => (
                      <span key={i} style={{
                        background: '#004F59', color: '#FAE600',
                        borderRadius: 4, fontSize: 10, fontWeight: 700,
                        padding: '3px 8px',
                      }}>{i + 1}. {a.title}</span>
                    ))}
                  </div>
                </div>
              )}

              <div style={{ fontSize: 10, color: 'var(--text-30, #9AACAE)', marginTop: 14 }}>
                Analysiert am {new Date(data.updated_at).toLocaleDateString('de-DE')}
                {data.city && ` · ${data.trade || 'Handwerk'} in ${data.city}`}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}

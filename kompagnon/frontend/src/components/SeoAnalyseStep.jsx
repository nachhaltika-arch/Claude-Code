import { useState, useEffect, useCallback } from 'react';
import toast from 'react-hot-toast';
import API_BASE_URL from '../config';
import { useConfirmStep } from '../hooks/useConfirmStep';

const STATUS_COLORS = {
  ok:   { dot: '#1D9E75', bg: '#E3F6EF' },
  warn: { dot: '#EF9F27', bg: '#FFFBE0' },
  err:  { dot: '#E24B4A', bg: '#FDECEA' },
};

const PRIO_COLORS = {
  hoch:    { bg: '#FDECEA', text: '#A32D2D' },
  mittel:  { bg: '#FFFBE0', text: '#854F0B' },
  niedrig: { bg: '#E3F6EF', text: '#3B6D11' },
};

export default function SeoAnalyseStep({ projectId, token, onStepConfirmed }) {
  const [data, setData]           = useState(null);
  const [loading, setLoading]     = useState(true);
  const [triggering, setTriggering] = useState(false);
  const [activeTab, setActiveTab] = useState('keywords');

  const { confirm: confirmStep, confirming: confirmingStep } = useConfirmStep({
    projectId, stepId: 'seo-analyse', token, onConfirmed: onStepConfirmed,
  });
  const [error, setError]         = useState(null);

  const headers = { Authorization: `Bearer ${token}` };

  const fetchResult = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/seo/result/${projectId}`, { headers });
      if (res.ok) setData(await res.json());
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  }, [projectId]); // eslint-disable-line

  useEffect(() => { fetchResult(); }, [fetchResult]);

  // Auto-poll wenn running/pending
  useEffect(() => {
    if (data?.status !== 'running' && data?.status !== 'pending') return;
    const iv = setInterval(fetchResult, 5000);
    return () => clearInterval(iv);
  }, [data?.status, fetchResult]);

  const triggerAnalysis = async () => {
    setTriggering(true);
    setError(null);
    try {
      await fetch(`${API_BASE_URL}/api/seo/trigger/${projectId}`, { method: 'POST', headers });
      setTimeout(fetchResult, 2000);
    } catch (e) { setError(e.message); setTriggering(false); }
  };

  const scoreColor = (s) => s >= 70 ? '#00875A' : s >= 50 ? '#B8860B' : '#C0392B';

  if (loading) return <div style={{ padding: 20, textAlign: 'center', color: 'var(--text-tertiary)', fontSize: 13 }}>SEO-Daten werden geladen…</div>;

  if (error) return (
    <div style={{ padding: 20 }}>
      <div style={{ color: '#C0392B', fontSize: 13, marginBottom: 12 }}>Fehler: {error}</div>
      <button onClick={fetchResult} style={btnStyle}>Erneut versuchen</button>
    </div>
  );

  if (!data || data.status === 'not_found' || data.status === 'pending') return (
    <div style={{ padding: 20, textAlign: 'center' }}>
      <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 16 }}>Noch keine SEO-Analyse vorhanden.</div>
      <button onClick={triggerAnalysis} disabled={triggering} style={btnStyle}>
        {triggering ? 'Wird gestartet…' : 'SEO-Analyse jetzt starten'}
      </button>
    </div>
  );

  if (data.status === 'running') return (
    <div style={{ padding: 20, textAlign: 'center' }}>
      <div style={{ fontSize: 13, color: 'var(--kc-dark, #004F59)', marginBottom: 10 }}>Analyse laeuft — ca. 30–60 Sekunden…</div>
      <div style={{ height: 4, background: 'var(--border, #D5E0E2)', borderRadius: 2, overflow: 'hidden' }}>
        <div style={{ height: '100%', width: '60%', background: '#FAE600', borderRadius: 2, animation: 'pulse 1.5s infinite' }} />
      </div>
    </div>
  );

  if (data.status === 'failed') return (
    <div style={{ padding: 20 }}>
      <div style={{ color: '#C0392B', fontSize: 13, marginBottom: 12 }}>Analyse fehlgeschlagen: {data.error_message || 'Unbekannt'}</div>
      <button onClick={triggerAnalysis} style={btnStyle}>Erneut versuchen</button>
    </div>
  );

  const kws = data.top_keywords || [];
  const issues = data.onpage_issues || [];
  const comps = data.competitors || [];
  const actions = data.action_plan || [];
  const maxComp = Math.max(...comps.map(c => c.score), 1);

  return (
    <div style={{ fontFamily: 'var(--font-sans)' }}>

      {/* Score-Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 10, marginBottom: 20 }}>
        {[
          { v: data.overall_score, l: 'Gesamt' },
          { v: data.keyword_score, l: 'Keywords' },
          { v: data.onpage_score, l: 'On-Page' },
          { v: data.competitor_score, l: 'Wettbewerb' },
        ].map(({ v, l }) => (
          <div key={l} style={{ background: 'var(--paper, #FAFAFA)', border: '0.5px solid var(--border, #D5E0E2)', borderRadius: 8, padding: '12px 10px', textAlign: 'center' }}>
            <div style={{ fontSize: 26, fontWeight: 700, color: scoreColor(v), fontFamily: "var(--font-display, 'Barlow Condensed')" }}>{v ?? '–'}</div>
            <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-30, #9AACAE)', textTransform: 'uppercase', letterSpacing: '.08em', marginTop: 4 }}>{l}</div>
          </div>
        ))}
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', borderBottom: '0.5px solid var(--border-light)', marginBottom: 16 }}>
        {[['keywords','Keywords'],['onpage','On-Page'],['competitors','Wettbewerb'],['actions','Massnahmen']].map(([k, lbl]) => (
          <button key={k} onClick={() => setActiveTab(k)} style={{
            padding: '8px 14px', fontSize: 11, fontWeight: 700,
            color: activeTab === k ? 'var(--kc-dark, #004F59)' : 'var(--text-30, #9AACAE)',
            background: 'none', border: 'none',
            borderBottom: activeTab === k ? '2px solid #FAE600' : '2px solid transparent',
            cursor: 'pointer', fontFamily: 'var(--font-sans)',
            textTransform: 'uppercase', letterSpacing: '.06em',
          }}>{lbl}</button>
        ))}
      </div>

      {/* Keywords */}
      {activeTab === 'keywords' && kws.map((kw, i) => (
        <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '8px 0', borderBottom: '0.5px solid var(--surface, #F0F4F5)', fontSize: 13 }}>
          <div style={{ flex: 1, fontWeight: 600, color: 'var(--text, #000)' }}>{kw.keyword}</div>
          <div style={{ fontSize: 11, color: 'var(--text-60, #4A5A5C)', minWidth: 80 }}>{kw.type}</div>
          <span style={{ fontSize: 10, fontWeight: 700, padding: '2px 8px', borderRadius: 3, background: PRIO_COLORS[kw.priority]?.bg || '#F0F4F5', color: PRIO_COLORS[kw.priority]?.text || '#555' }}>{kw.priority}</span>
          <div style={{ width: 60, height: 4, background: 'var(--border, #D5E0E2)', borderRadius: 2, overflow: 'hidden' }}>
            <div style={{ height: '100%', width: `${kw.volume}%`, background: 'var(--kc-mid, #008EAA)', borderRadius: 2 }} />
          </div>
        </div>
      ))}

      {/* On-Page */}
      {activeTab === 'onpage' && issues.map((iss, i) => (
        <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: 10, padding: '8px 0', borderBottom: '0.5px solid var(--surface, #F0F4F5)' }}>
          <div style={{ width: 8, height: 8, borderRadius: '50%', marginTop: 5, flexShrink: 0, background: STATUS_COLORS[iss.status]?.dot || '#ccc' }} />
          <div>
            <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text, #000)' }}>{iss.label}</div>
            <div style={{ fontSize: 12, color: 'var(--text-60, #4A5A5C)', marginTop: 2 }}>{iss.description}</div>
          </div>
        </div>
      ))}

      {/* Wettbewerber */}
      {activeTab === 'competitors' && [...comps].sort((a, b) => b.score - a.score).map((c, i) => (
        <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '8px 0', borderBottom: '0.5px solid var(--surface, #F0F4F5)', fontSize: 13 }}>
          <div style={{ flex: 1, color: 'var(--text, #000)', fontWeight: 500 }}>{c.name}</div>
          <div style={{ width: 80, height: 4, background: 'var(--border, #D5E0E2)', borderRadius: 2, overflow: 'hidden' }}>
            <div style={{ height: '100%', width: `${Math.round(c.score / maxComp * 100)}%`, background: 'var(--kc-dark, #004F59)', borderRadius: 2 }} />
          </div>
          <div style={{ minWidth: 28, fontWeight: 700, color: 'var(--kc-dark, #004F59)' }}>{c.score}</div>
        </div>
      ))}

      {/* Massnahmen */}
      {activeTab === 'actions' && actions.map((a, i) => (
        <div key={i} style={{ display: 'flex', gap: 10, padding: '10px 0', borderBottom: '0.5px solid var(--surface, #F0F4F5)' }}>
          <div style={{ width: 22, height: 22, borderRadius: '50%', background: 'var(--kc-dark, #004F59)', color: '#fff', fontSize: 11, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, fontWeight: 700 }}>{i + 1}</div>
          <div>
            <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text, #000)' }}>{a.title}</div>
            <div style={{ fontSize: 12, color: 'var(--text-60, #4A5A5C)', marginTop: 3 }}>{a.time} · {a.effect}</div>
          </div>
        </div>
      ))}

      {/* Schritt abschliessen */}
      <button
        onClick={confirmStep}
        disabled={confirmingStep}
        style={{
          width: '100%', marginTop: 20, padding: '12px',
          background: confirmingStep ? 'var(--border-light)' : '#FAE600',
          color: '#000', border: 'none', borderRadius: 8,
          fontSize: 13, fontWeight: 900,
          cursor: confirmingStep ? 'not-allowed' : 'pointer',
          fontFamily: 'var(--font-sans)',
          textTransform: 'uppercase', letterSpacing: '.05em',
        }}
      >
        {confirmingStep ? 'Wird gespeichert…' : 'SEO-Analyse abschliessen & weiter'}
      </button>

      {/* Footer */}
      <div style={{ marginTop: 12, display: 'flex', gap: 10, alignItems: 'center' }}>
        <button onClick={triggerAnalysis} disabled={triggering} style={{
          background: 'transparent', color: 'var(--kc-dark, #004F59)',
          border: '1px solid var(--kc-dark, #004F59)', borderRadius: 6,
          padding: '8px 18px', fontSize: 12, fontWeight: 700, cursor: 'pointer',
          fontFamily: 'var(--font-sans)',
        }}>
          {triggering ? 'Laeuft…' : 'Neu analysieren'}
        </button>
        <span style={{ fontSize: 11, color: 'var(--text-30, #9AACAE)' }}>
          Letzte Analyse: {data.updated_at ? new Date(data.updated_at).toLocaleDateString('de-DE') : '–'}
        </span>
      </div>
    </div>
  );
}

const btnStyle = {
  background: '#FAE600', color: '#004F59', border: 'none', borderRadius: 6,
  padding: '9px 18px', fontSize: 12, fontWeight: 900, cursor: 'pointer',
  fontFamily: 'var(--font-sans)', textTransform: 'uppercase', letterSpacing: '.04em',
};

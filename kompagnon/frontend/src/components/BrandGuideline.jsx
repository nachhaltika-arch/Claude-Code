import { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import API_BASE_URL from '../config';

const TABS = ['Farben', 'Typografie', 'Komponenten', 'CSS Variables'];

function CopyButton({ text, label = 'Kopieren' }) {
  const [copied, setCopied] = useState(false);
  const copy = () => {
    navigator.clipboard?.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    });
  };
  return (
    <button onClick={copy} style={{
      background: copied ? '#00875A' : 'var(--bg-app, #F5F5F0)',
      color: copied ? '#fff' : 'var(--text-secondary)',
      border: '0.5px solid var(--border-light)',
      borderRadius: 5, padding: '3px 9px', fontSize: 10, fontWeight: 700,
      cursor: 'pointer', fontFamily: 'var(--font-sans)', transition: 'all .15s',
    }}>
      {copied ? '✓ Kopiert' : label}
    </button>
  );
}

function TabBar({ active, onChange }) {
  return (
    <div style={{ display: 'flex', gap: 2, borderBottom: '1px solid var(--border-light)', marginBottom: 16 }}>
      {TABS.map(t => (
        <button
          key={t}
          onClick={() => onChange(t)}
          style={{
            background: 'none', border: 'none', borderBottom: active === t ? '2px solid var(--brand-primary, #004F59)' : '2px solid transparent',
            padding: '8px 14px', fontSize: 12, fontWeight: active === t ? 700 : 400,
            color: active === t ? 'var(--brand-primary, #004F59)' : 'var(--text-tertiary)',
            cursor: 'pointer', fontFamily: 'var(--font-sans)', transition: 'all .15s',
            marginBottom: -1,
          }}
        >
          {t}
        </button>
      ))}
    </div>
  );
}

function FarbenTab({ colors }) {
  if (!colors || Object.keys(colors).length === 0) {
    return <div style={{ fontSize: 12, color: 'var(--text-tertiary)', padding: '16px 0' }}>Keine Farb-Tokens vorhanden.</div>;
  }
  return (
    <div>
      <div style={{ fontSize: 9, fontWeight: 900, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.1em', marginBottom: 10 }}>
        Farb-Tokens — Klick kopiert
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(90px, 1fr))', gap: 10 }}>
        {Object.entries(colors).map(([tk, hex]) => (
          <div
            key={tk}
            onClick={() => navigator.clipboard?.writeText(hex).then(() => toast.success(`${hex} kopiert`))}
            title={`${tk}: ${hex} — klicken zum Kopieren`}
            style={{ textAlign: 'center', cursor: 'pointer' }}
          >
            <div style={{
              height: 52, borderRadius: 8, background: hex,
              border: '0.5px solid rgba(0,0,0,.08)',
              transition: 'transform .12s',
              ':hover': { transform: 'scale(1.05)' },
            }}
              onMouseEnter={e => e.currentTarget.style.transform = 'scale(1.05)'}
              onMouseLeave={e => e.currentTarget.style.transform = 'scale(1)'}
            />
            <div style={{ fontSize: 8, color: 'var(--text-tertiary)', fontFamily: 'monospace', marginTop: 3 }}>{hex}</div>
            <div style={{ fontSize: 8, textTransform: 'uppercase', letterSpacing: '.03em', color: 'var(--text-tertiary)' }}>
              {tk.replace(/_/g, ' ')}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function TypografieTab({ typography, colors }) {
  const heading = typography?.heading || 'Georgia';
  const body    = typography?.body    || 'Arial';
  const accent  = typography?.accent  || heading;
  const hColor  = colors?.h1_color || colors?.primary || '#1A1A1A';
  const bColor  = colors?.body_color || '#333333';
  const aColor  = colors?.accent || '#004F59';

  return (
    <div>
      {[
        { label: 'Überschrift (H1)', font: heading, size: 22, weight: 800, color: hColor,
          sample: 'Ihr Handwerksbetrieb — Qualität seit Jahrzehnten' },
        { label: 'Unterüberschrift (H2)', font: heading, size: 16, weight: 600, color: hColor,
          sample: 'Unsere Leistungen im Überblick' },
        { label: 'Fließtext', font: body, size: 13, weight: 400, color: bColor,
          sample: 'Professionelle Handwerksarbeit mit Erfahrung und Leidenschaft. Wir stehen für Qualität, Zuverlässigkeit und persönliche Beratung.' },
        { label: 'Akzent / Buttons', font: accent, size: 12, weight: 700, color: aColor,
          sample: 'Jetzt Angebot anfordern →' },
      ].map(({ label, font, size, weight, color, sample }) => (
        <div key={label} style={{ marginBottom: 16, paddingBottom: 16, borderBottom: '0.5px solid var(--border-light)' }}>
          <div style={{ fontSize: 9, color: 'var(--text-tertiary)', marginBottom: 4 }}>
            {label} — <span style={{ fontFamily: 'monospace' }}>{font}</span>
          </div>
          <div style={{ fontFamily: font, fontSize: size, fontWeight: weight, color, lineHeight: 1.4 }}>
            {sample}
          </div>
        </div>
      ))}

      {typography?.scale && (
        <div>
          <div style={{ fontSize: 9, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.08em', marginBottom: 8 }}>
            Typografische Skala
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {Object.entries(typography.scale).map(([step, val]) => (
              <div key={step} style={{ background: 'var(--bg-app)', borderRadius: 6, padding: '4px 8px', fontSize: 10 }}>
                <span style={{ color: 'var(--text-tertiary)' }}>{step}: </span>
                <strong>{val}</strong>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function KomponentenTab({ guideline, colors }) {
  const primary   = colors?.primary   || '#004F59';
  const accent    = colors?.accent    || '#FAE600';
  const surface   = colors?.surface   || '#F5F5F0';
  const hColor    = colors?.h1_color  || '#1A1A1A';
  const bodyColor = colors?.body_color|| '#444444';
  const font      = guideline?.typography?.body || 'Arial';

  return (
    <div>
      {/* Buttons */}
      <div style={{ marginBottom: 16 }}>
        <div style={{ fontSize: 9, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.08em', marginBottom: 8 }}>
          Button-Varianten
        </div>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          <button style={{ background: primary, color: '#fff', border: 'none', borderRadius: 7, padding: '10px 20px', fontSize: 12, fontWeight: 700, fontFamily: font, cursor: 'default' }}>
            Primär-Button
          </button>
          <button style={{ background: accent, color: '#000', border: 'none', borderRadius: 7, padding: '10px 20px', fontSize: 12, fontWeight: 700, fontFamily: font, cursor: 'default' }}>
            Akzent-Button
          </button>
          <button style={{ background: 'transparent', color: primary, border: `1.5px solid ${primary}`, borderRadius: 7, padding: '10px 20px', fontSize: 12, fontWeight: 700, fontFamily: font, cursor: 'default' }}>
            Outline-Button
          </button>
        </div>
      </div>

      {/* Card preview */}
      <div style={{ marginBottom: 16 }}>
        <div style={{ fontSize: 9, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.08em', marginBottom: 8 }}>
          Karten-Komponente
        </div>
        <div style={{ background: surface, borderRadius: 10, padding: '16px 18px', maxWidth: 300, border: '0.5px solid rgba(0,0,0,.06)' }}>
          <div style={{ fontSize: 14, fontWeight: 700, color: hColor, fontFamily: guideline?.typography?.heading || 'Georgia', marginBottom: 6 }}>
            Leistung XY
          </div>
          <div style={{ fontSize: 12, color: bodyColor, fontFamily: font, lineHeight: 1.5, marginBottom: 12 }}>
            Professionelle Durchführung mit langjähriger Erfahrung und modernsten Methoden.
          </div>
          <div style={{ display: 'inline-block', background: accent, color: '#000', borderRadius: 5, padding: '6px 14px', fontSize: 11, fontWeight: 700, fontFamily: font }}>
            Mehr erfahren →
          </div>
        </div>
      </div>

      {/* Voice & Tone */}
      {guideline?.voice && (
        <div>
          <div style={{ fontSize: 9, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.08em', marginBottom: 8 }}>
            Voice & Tone
          </div>
          <div style={{ background: 'var(--bg-app)', borderRadius: 8, padding: '10px 14px', fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.7 }}>
            {typeof guideline.voice === 'string' ? guideline.voice : JSON.stringify(guideline.voice, null, 2)}
          </div>
        </div>
      )}
    </div>
  );
}

function CssVariablesTab({ guideline, colors }) {
  const lines = [];
  if (colors) {
    Object.entries(colors).forEach(([k, v]) => {
      lines.push(`  --color-${k.replace(/_/g, '-')}: ${v};`);
    });
  }
  if (guideline?.typography) {
    const t = guideline.typography;
    if (t.heading) lines.push(`  --font-heading: "${t.heading}", serif;`);
    if (t.body)    lines.push(`  --font-body: "${t.body}", sans-serif;`);
    if (t.accent)  lines.push(`  --font-accent: "${t.accent}", sans-serif;`);
  }
  if (guideline?.spacing) {
    Object.entries(guideline.spacing).forEach(([k, v]) => {
      lines.push(`  --spacing-${k}: ${v};`);
    });
  }
  const cssText = `:root {\n${lines.join('\n')}\n}`;

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
        <div style={{ fontSize: 9, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.08em' }}>
          CSS Custom Properties
        </div>
        <CopyButton text={cssText} label="CSS kopieren" />
      </div>
      <pre style={{
        background: '#1A1A2E', color: '#A8D8A8', borderRadius: 8,
        padding: '14px 16px', fontSize: 11, fontFamily: 'monospace',
        lineHeight: 1.6, overflowX: 'auto', margin: 0,
        border: '0.5px solid rgba(255,255,255,.06)',
      }}>
        {cssText}
      </pre>
    </div>
  );
}

export default function BrandGuideline({ leadId, token, projectId, onStepConfirmed }) {
  const [guideline,   setGuideline]   = useState(null);
  const [loading,     setLoading]     = useState(true);
  const [generating,  setGenerating]  = useState(false);
  const [confirming,  setConfirming]  = useState(false);
  const [confirmed,   setConfirmed]   = useState(false);
  const [savedAt,     setSavedAt]     = useState(null);
  const [activeTab,   setActiveTab]   = useState('Farben');
  const [error,       setError]       = useState('');

  useEffect(() => {
    if (!leadId) return;
    setLoading(true);
    setGuideline(null);
    setError('');

    fetch(
      `${API_BASE_URL}/api/branddesign/${leadId}/guideline`,
      { headers: { Authorization: `Bearer ${token}` } }
    )
      .then(r => r.ok ? r.json() : null)
      .then(d => {
        if (d?.generated && d?.guideline) {
          setGuideline(d.guideline);
          if (d.generated_at) setSavedAt(new Date(d.generated_at));
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [leadId, token]); // eslint-disable-line

  const generate = async () => {
    setGenerating(true);
    setError('');
    try {
      const res = await fetch(
        `${API_BASE_URL}/api/branddesign/${leadId}/guideline/generate`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        }
      );
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }
      const d = await res.json();
      setGuideline(d.guideline);
      setSavedAt(new Date());
      toast.success('Brand Guideline gespeichert ✓');
    } catch (e) {
      const msg = e.message || 'Generierung fehlgeschlagen';
      setError(msg);
      toast.error(msg);
    } finally {
      setGenerating(false);
    }
  };

  const confirm = async () => {
    if (!projectId || !onStepConfirmed) {
      setConfirmed(true);
      if (onStepConfirmed) onStepConfirmed('brand-guideline');
      return;
    }
    setConfirming(true);
    try {
      await fetch(`${API_BASE_URL}/api/projects/${projectId}/confirm-step`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ step: 'brand-guideline' }),
      });
      setConfirmed(true);
      toast.success('Schritt abgeschlossen ✓');
      onStepConfirmed('brand-guideline');
    } catch {
      setConfirmed(true);
      if (onStepConfirmed) onStepConfirmed('brand-guideline');
    } finally {
      setConfirming(false);
    }
  };

  // ── Loading ───────────────────────────────────────────────────────────────
  if (loading) {
    return (
      <div style={{ padding: '32px 24px', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12, color: 'var(--text-tertiary)' }}>
        <div style={{
          width: 32, height: 32, borderRadius: '50%',
          border: '3px solid var(--border-light)',
          borderTopColor: 'var(--brand-primary, #004F59)',
          animation: 'spin .8s linear infinite',
        }} />
        <style>{`@keyframes spin{to{transform:rotate(360deg)}}`}</style>
        <div style={{ fontSize: 12 }}>Brand Guideline wird geladen…</div>
        {leadId && (
          <div style={{ fontSize: 10, color: 'var(--text-tertiary)', fontFamily: 'monospace' }}>Lead-ID: {leadId}</div>
        )}
      </div>
    );
  }

  // ── Kein leadId ───────────────────────────────────────────────────────────
  if (!leadId) {
    return (
      <div style={{ padding: '20px 24px', background: '#FEF3DC', borderRadius: 10, fontSize: 13, color: '#8A5C00' }}>
        Fehler: Keine Lead-ID verfügbar. Bitte Seite neu laden.
      </div>
    );
  }

  // ── Noch keine Guideline → Generate-Banner ────────────────────────────────
  if (!guideline) {
    return (
      <div>
        <div style={{
          background: 'linear-gradient(135deg, #004F59, #008EAA)',
          borderRadius: 12, padding: '18px 20px',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 16,
        }}>
          <div>
            <div style={{ fontSize: 14, fontWeight: 900, color: '#FAE600', marginBottom: 4 }}>
              Brand Guideline noch nicht generiert
            </div>
            <div style={{ fontSize: 12, color: 'rgba(255,255,255,.7)', lineHeight: 1.5 }}>
              Claude liest Brand Design, Briefing und Stil-Daten — ca. 15 Sekunden.
            </div>
          </div>
          <button
            onClick={generate}
            disabled={generating}
            style={{
              background: '#FAE600', color: '#004F59',
              border: 'none', borderRadius: 8,
              padding: '11px 22px', fontSize: 12, fontWeight: 900,
              cursor: generating ? 'not-allowed' : 'pointer',
              whiteSpace: 'nowrap', flexShrink: 0,
              fontFamily: 'var(--font-sans)',
              opacity: generating ? 0.7 : 1,
            }}
          >
            {generating ? 'Generiert…' : 'Guideline generieren →'}
          </button>
        </div>
        {error && (
          <div style={{ marginTop: 10, padding: '10px 14px', background: '#FEE2E2', borderRadius: 8, fontSize: 12, color: '#991B1B' }}>
            Fehler: {error}
          </div>
        )}
      </div>
    );
  }

  // ── Guideline vorhanden ───────────────────────────────────────────────────
  const g = guideline;
  const colors = g.colors || {};

  return (
    <div style={{ fontFamily: 'var(--font-sans)' }}>

      {/* Status-Bar */}
      <div style={{
        background: 'var(--status-success-bg, #E3F6EF)',
        border: '0.5px solid #00875A33',
        borderRadius: 8, padding: '10px 14px', marginBottom: 16,
        display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 14 }}>✓</span>
          <div>
            <div style={{ fontSize: 12, fontWeight: 700, color: '#00875A' }}>Automatisch gespeichert</div>
            {savedAt && (
              <div style={{ fontSize: 10, color: '#4A7A5C', marginTop: 1 }}>
                {savedAt.toLocaleString('de-DE', { dateStyle: 'medium', timeStyle: 'short' })}
                {g.meta?.style_keyword ? ` · ${g.meta.style_keyword}` : ''}
                {g.meta?.farb_stimmung ? ` · ${g.meta.farb_stimmung}` : ''}
              </div>
            )}
          </div>
        </div>
        <button
          onClick={generate}
          disabled={generating}
          style={{
            background: 'transparent', color: '#00875A',
            border: '1px solid #00875A44', borderRadius: 6,
            padding: '5px 12px', fontSize: 11, fontWeight: 700,
            cursor: generating ? 'not-allowed' : 'pointer',
            fontFamily: 'var(--font-sans)', flexShrink: 0,
          }}
        >
          {generating ? '⏳ Generiert…' : '↻ Neu generieren'}
        </button>
      </div>

      {/* Tabs */}
      <TabBar active={activeTab} onChange={setActiveTab} />

      {/* Tab-Inhalt */}
      <div style={{ minHeight: 200 }}>
        {activeTab === 'Farben'       && <FarbenTab colors={colors} />}
        {activeTab === 'Typografie'   && <TypografieTab typography={g.typography} colors={colors} />}
        {activeTab === 'Komponenten'  && <KomponentenTab guideline={g} colors={colors} />}
        {activeTab === 'CSS Variables'&& <CssVariablesTab guideline={g} colors={colors} />}
      </div>

      {/* Abschließen-Button */}
      <div style={{ marginTop: 24, paddingTop: 16, borderTop: '0.5px solid var(--border-light)' }}>
        <button
          onClick={confirm}
          disabled={confirming || confirmed}
          style={{
            width: '100%', padding: '13px 20px',
            background: confirmed ? '#00875A' : 'var(--brand-accent, #FAE600)',
            color: confirmed ? '#fff' : '#000',
            border: 'none', borderRadius: 9,
            fontSize: 13, fontWeight: 900, cursor: confirming || confirmed ? 'default' : 'pointer',
            fontFamily: 'var(--font-sans)',
            opacity: confirming ? 0.7 : 1,
            transition: 'background .2s, color .2s',
          }}
        >
          {confirmed ? '✓ Guideline abgeschlossen' : confirming ? 'Wird gespeichert…' : '✓ Guideline abschließen & weiter →'}
        </button>
      </div>
    </div>
  );
}

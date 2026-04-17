import { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import API_BASE_URL from '../config';

const TABS = ['Farben', 'Typografie', 'Komponenten', 'CSS Variables'];

export default function BrandGuideline({ leadId, token, projectId, onStepConfirmed }) {
  const [guideline, setGuideline]     = useState(null);
  const [loading, setLoading]         = useState(true);
  const [generating, setGenerating]   = useState(false);
  const [confirming, setConfirming]   = useState(false);
  const [confirmed, setConfirmed]     = useState(false);
  const [savedAt, setSavedAt]         = useState(null);
  const [activeTab, setActiveTab]     = useState('Farben');
  const [error, setError]             = useState('');

  const h = { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` };

  useEffect(() => {
    if (!leadId || !token) { setLoading(false); return; }
    setLoading(true);
    setError('');
    setGuideline(null);
    fetch(`${API_BASE_URL}/api/branddesign/${leadId}/guideline`, { headers: h })
      .then(r => r.ok ? r.json() : Promise.reject(r.status))
      .then(d => {
        if (d?.generated && d?.guideline) {
          setGuideline(d.guideline);
          if (d.generated_at) setSavedAt(new Date(d.generated_at));
        }
      })
      .catch(err => { if (err !== 404) setError('Guideline konnte nicht geladen werden.'); })
      .finally(() => setLoading(false));
  }, [leadId, token]); // eslint-disable-line

  const generate = async () => {
    if (!leadId) return;
    setGenerating(true);
    setError('');
    try {
      const res = await fetch(`${API_BASE_URL}/api/branddesign/${leadId}/guideline/generate`, { method: 'POST', headers: h });
      if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.detail || `HTTP ${res.status}`); }
      const d = await res.json();
      if (d?.guideline) { setGuideline(d.guideline); setSavedAt(new Date()); toast.success('Brand Guideline gespeichert'); }
    } catch (e) { setError(e.message || 'Generierung fehlgeschlagen'); toast.error(e.message || 'Generierung fehlgeschlagen'); }
    finally { setGenerating(false); }
  };

  const confirm = async () => {
    if (!projectId || confirming || confirmed) return;
    setConfirming(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/projects/${projectId}/confirm-step`, {
        method: 'POST', headers: h, body: JSON.stringify({ step_id: 'brand-guideline' }),
      });
      if (!res.ok) throw new Error();
      setConfirmed(true);
      if (onStepConfirmed) onStepConfirmed();
    } catch { toast.error('Fehler beim Bestaetigen'); }
    finally { setConfirming(false); }
  };

  const copy = (text) => { navigator.clipboard?.writeText(text).then(() => toast.success('Kopiert')).catch(() => {}); };

  if (loading) return (
    <div style={{ padding: '32px 0', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 10, color: 'var(--text-tertiary)' }}>
      <style>{`@keyframes spin{to{transform:rotate(360deg)}}`}</style>
      <div style={{ width: 28, height: 28, borderRadius: '50%', border: '3px solid var(--border-light)', borderTopColor: 'var(--brand-primary,#004F59)', animation: 'spin .8s linear infinite' }} />
      <div style={{ fontSize: 12 }}>Brand Guideline wird geladen…</div>
    </div>
  );

  if (error && !guideline) return (
    <div style={{ padding: 16, background: '#FDEAEA', borderRadius: 8, fontSize: 13, color: '#C0392B' }}>
      {error}
      <button onClick={generate} style={{ marginLeft: 12, fontSize: 11, fontWeight: 700, background: '#C0392B', color: '#fff', border: 'none', borderRadius: 5, padding: '3px 10px', cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>Erneut versuchen</button>
    </div>
  );

  if (!guideline) return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      <div style={{ background: 'linear-gradient(135deg,#004F59,#008EAA)', borderRadius: 12, padding: '18px 20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 16 }}>
        <div>
          <div style={{ fontSize: 14, fontWeight: 900, color: '#FAE600', marginBottom: 4 }}>Brand Guideline noch nicht generiert</div>
          <div style={{ fontSize: 12, color: 'rgba(255,255,255,.7)', lineHeight: 1.5 }}>Claude liest Brand Design, Briefing und Stil-Daten — ca. 15 Sekunden.</div>
        </div>
        <button onClick={generate} disabled={generating} style={{ background: '#FAE600', color: '#004F59', border: 'none', borderRadius: 8, padding: '11px 22px', fontSize: 12, fontWeight: 900, cursor: generating ? 'not-allowed' : 'pointer', whiteSpace: 'nowrap', flexShrink: 0, fontFamily: 'var(--font-sans)', opacity: generating ? 0.7 : 1 }}>
          {generating ? 'Generiert…' : 'Guideline generieren'}
        </button>
      </div>
    </div>
  );

  const g = guideline;
  const tokens = g.tokens || g.colors || {};
  const typo = g.typography || {};
  const comps = g.components || {};
  const cssVars = g.css_variables || '';

  return (
    <div style={{ fontFamily: 'var(--font-sans)', display: 'flex', flexDirection: 'column', gap: 12 }}>

      <div style={{ background: '#E3F6EF', border: '0.5px solid #00875A33', borderRadius: 8, padding: '10px 14px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12 }}>
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
        <button onClick={generate} disabled={generating} style={{ background: 'transparent', color: '#00875A', border: '1px solid #00875A44', borderRadius: 6, padding: '5px 12px', fontSize: 11, fontWeight: 700, cursor: 'pointer', fontFamily: 'var(--font-sans)', flexShrink: 0 }}>
          {generating ? 'Generiert…' : 'Neu generieren'}
        </button>
      </div>

      <div style={{ display: 'flex', borderBottom: '0.5px solid var(--border-light)' }}>
        {TABS.map(tab => (
          <button key={tab} onClick={() => setActiveTab(tab)} style={{
            padding: '8px 14px', fontSize: 11, fontWeight: 700,
            color: activeTab === tab ? 'var(--brand-primary,#004F59)' : 'var(--text-tertiary)',
            background: 'none', border: 'none',
            borderBottom: activeTab === tab ? '2px solid #FAE600' : '2px solid transparent',
            cursor: 'pointer', fontFamily: 'var(--font-sans)', textTransform: 'uppercase', letterSpacing: '.06em',
          }}>{tab}</button>
        ))}
      </div>

      {activeTab === 'Farben' && (
        <div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(90px,1fr))', gap: 8, marginBottom: 14 }}>
            {Object.entries(tokens).map(([key, hex]) => (
              <div key={key} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
                <div onClick={() => copy(hex)} title={`${key}: ${hex}`}
                  style={{ width: '100%', height: 48, borderRadius: 8, background: hex, cursor: 'pointer', border: '0.5px solid rgba(0,0,0,.08)' }} />
                <div style={{ fontSize: 8, fontFamily: 'monospace', color: 'var(--text-tertiary)', textAlign: 'center' }}>{hex}</div>
                <div style={{ fontSize: 8, fontWeight: 700, textAlign: 'center', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '.04em' }}>{key.replace(/_/g, ' ')}</div>
              </div>
            ))}
          </div>
          <div style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>Klick auf Farbfeld kopiert den Hex-Code</div>
        </div>
      )}

      {activeTab === 'Typografie' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {typo.fonts && (
            <div style={{ background: 'var(--surface,#F0F4F5)', borderRadius: 8, padding: '12px 14px', marginBottom: 8 }}>
              <div style={{ fontSize: 9, fontWeight: 900, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.1em', marginBottom: 10 }}>Schrift-Rollen</div>
              {[
                { lbl: 'Ueberschriften', font: typo.fonts.heading, color: typo.colors?.heading },
                { lbl: 'Fliesstext', font: typo.fonts.body, color: typo.colors?.body },
                { lbl: 'Akzent / CTA', font: typo.fonts.accent, color: typo.colors?.cta },
              ].map(({ lbl, font, color }) => font && (
                <div key={lbl} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '7px 0', borderBottom: '0.5px solid var(--border-light)' }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 9, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.06em', marginBottom: 2 }}>{lbl}</div>
                    <div style={{ fontFamily: font, fontSize: 15, color: 'var(--text-primary)' }}>{font}</div>
                  </div>
                  {color && <>
                    <div style={{ width: 20, height: 20, borderRadius: 4, background: color, flexShrink: 0, border: '0.5px solid rgba(0,0,0,.1)' }} />
                    <div style={{ fontSize: 9, fontFamily: 'monospace', color: 'var(--text-tertiary)' }}>{color}</div>
                  </>}
                </div>
              ))}
            </div>
          )}
          {typo.scale && Object.entries(typo.scale).map(([level, spec]) => (
            <div key={level} style={{ display: 'flex', alignItems: 'baseline', gap: 12, padding: '8px 0', borderBottom: '0.5px solid var(--surface,#F0F4F5)' }}>
              <div style={{ width: 48, flexShrink: 0, fontSize: 9, fontWeight: 900, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.08em', background: 'var(--surface,#F0F4F5)', padding: '2px 6px', borderRadius: 3, textAlign: 'center' }}>{level.toUpperCase()}</div>
              <div style={{
                flex: 1, fontFamily: spec.family || (level.startsWith('h') ? typo.fonts?.heading : typo.fonts?.body),
                fontSize: Math.min(parseInt(spec.size) || 14, 28), fontWeight: spec.weight || 400,
                letterSpacing: spec.letter_spacing || 'normal', textTransform: spec.text_transform || 'none',
                color: 'var(--text-primary)', lineHeight: 1.3,
              }}>
                {level.startsWith('h') ? 'Beispiel-Ueberschrift' : level === 'button' ? 'JETZT ANFRAGEN' : level === 'label' ? 'LABEL' : 'Beispieltext'}
              </div>
              <div style={{ fontSize: 9, color: 'var(--text-tertiary)', textAlign: 'right', flexShrink: 0, fontFamily: 'monospace' }}>{spec.size}{spec.weight ? ` · ${spec.weight}` : ''}</div>
            </div>
          ))}
        </div>
      )}

      {activeTab === 'Komponenten' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {(comps.button_primary || comps.button_secondary || comps.button_accent) && (
            <div style={{ background: 'var(--surface,#F0F4F5)', borderRadius: 8, padding: '12px 14px' }}>
              <div style={{ fontSize: 9, fontWeight: 900, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.1em', marginBottom: 10 }}>Buttons</div>
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                {['button_primary', 'button_secondary', 'button_accent'].map(key => {
                  const s = comps[key]; if (!s) return null;
                  return (
                    <button key={key} style={{
                      background: s.background || 'transparent', color: s.color || '#000',
                      border: s.border || 'none', borderRadius: s.border_radius || '6px',
                      padding: s.padding || '10px 20px', fontSize: 13, fontWeight: 700,
                      cursor: 'default', fontFamily: s.font_family || 'var(--font-sans)',
                      textTransform: s.text_transform || 'none', letterSpacing: s.letter_spacing || 'normal',
                    }}>
                      {key === 'button_primary' ? 'Primaer' : key === 'button_secondary' ? 'Sekundaer' : 'Akzent'}
                    </button>
                  );
                })}
              </div>
            </div>
          )}
          {comps.card && (() => { const s = comps.card; return (
            <div style={{ background: 'var(--surface,#F0F4F5)', borderRadius: 8, padding: '12px 14px' }}>
              <div style={{ fontSize: 9, fontWeight: 900, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.1em', marginBottom: 10 }}>Karte</div>
              <div style={{ background: s.background || '#fff', border: s.border || '0.5px solid #D5E0E2', borderRadius: s.border_radius || '8px', boxShadow: s.shadow || 'none', padding: s.padding || '20px', maxWidth: 280 }}>
                <div style={{ fontFamily: s.title_font || 'inherit', fontSize: 14, fontWeight: 700, color: s.title_color || 'var(--text-primary)', marginBottom: 6 }}>{g.meta?.company || 'Muster GmbH'}</div>
                <div style={{ fontFamily: s.body_font || 'inherit', fontSize: 12, color: s.body_color || '#555', lineHeight: 1.6 }}>{g.meta?.gewerk || 'Handwerk'} · Beispieltext</div>
              </div>
            </div>
          ); })()}
          {g.voice_tone && (
            <div style={{ background: 'var(--surface,#F0F4F5)', borderRadius: 8, padding: '12px 14px' }}>
              <div style={{ fontSize: 9, fontWeight: 900, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.1em', marginBottom: 8 }}>Voice & Tone</div>
              <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 4 }}>{g.voice_tone.charakter}</div>
              <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginBottom: 8 }}>Ansprache: <strong>{g.voice_tone.ansprache}</strong></div>
              {g.voice_tone.cta_beispiele?.length > 0 && (
                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                  {g.voice_tone.cta_beispiele.map((cta, i) => (
                    <span key={i} style={{ background: tokens?.primary || '#004F59', color: '#fff', fontSize: 11, fontWeight: 700, padding: '4px 12px', borderRadius: 5 }}>{cta}</span>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {activeTab === 'CSS Variables' && cssVars && (
        <div>
          <div style={{ background: '#1a1a2e', borderRadius: 8, padding: '12px 14px', fontFamily: 'monospace', fontSize: 11, color: '#a8b2d8', lineHeight: 1.8, whiteSpace: 'pre-wrap', maxHeight: 300, overflowY: 'auto' }}>{cssVars}</div>
          <button onClick={() => copy(cssVars)} style={{ marginTop: 8, padding: '7px 14px', fontSize: 11, fontWeight: 700, background: 'var(--surface,#F0F4F5)', border: '0.5px solid var(--border-light)', borderRadius: 6, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>CSS kopieren</button>
        </div>
      )}

      <div style={{ marginTop: 8, paddingTop: 14, borderTop: '0.5px solid var(--border-light)' }}>
        <button onClick={confirm} disabled={confirming || confirmed} style={{
          width: '100%', padding: '12px',
          background: confirmed ? '#E3F6EF' : (confirming ? 'var(--border-light)' : '#FAE600'),
          color: confirmed ? '#00875A' : '#000',
          border: confirmed ? '0.5px solid #00875A33' : 'none',
          borderRadius: 8, fontSize: 13, fontWeight: 900,
          cursor: (confirming || confirmed) ? 'default' : 'pointer',
          fontFamily: 'var(--font-sans)', textTransform: 'uppercase', letterSpacing: '.05em',
        }}>
          {confirmed ? 'Brand Guideline abgeschlossen' : confirming ? 'Wird gespeichert…' : 'Guideline abschliessen & weiter'}
        </button>
      </div>
    </div>
  );
}

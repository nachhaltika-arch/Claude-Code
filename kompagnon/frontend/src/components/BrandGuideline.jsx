import { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import API_BASE_URL from '../config';
import { useConfirmStep } from '../hooks/useConfirmStep';

const TABS = ['Farben', 'Typografie', 'Komponenten', 'Vorschau', 'Export'];

export default function BrandGuideline({ project, lead, token, leadId, brandData, projectId, onStepConfirmed }) {
  const [activeTab, setActiveTab] = useState('Farben');
  const [guideline, setGuideline] = useState(null);
  const [loading, setLoading]     = useState(true);
  const [generating, setGenerating] = useState(false);
  const [editingToken, setEditingToken] = useState(null);
  const [editedColors, setEditedColors] = useState({});
  const [savedAt, setSavedAt] = useState(null);

  const headers = { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` };

  const { confirm: confirmStep, confirming: confirmingStep } = useConfirmStep({
    projectId: projectId || project?.id,
    stepId: 'brand-guideline',
    token,
    onConfirmed: onStepConfirmed,
  });

  useEffect(() => {
    if (!leadId) { setLoading(false); return; }
    setLoading(true);
    setGuideline(null);
    fetch(`${API_BASE_URL}/api/branddesign/${leadId}/guideline`, {
      headers: { Authorization: `Bearer ${token}` },
    })
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

  const reload = async () => {
    if (!leadId) return;
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/branddesign/${leadId}/guideline`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const d = await res.json();
        if (d?.generated && d?.guideline) {
          setGuideline(d.guideline);
          if (d.generated_at) setSavedAt(new Date(d.generated_at));
        }
      }
    } catch { /* silent */ }
    finally { setLoading(false); }
  };

  const generate = async () => {
    setGenerating(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/branddesign/${leadId}/guideline/generate`, { method: 'POST', headers });
      if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || 'Fehler');
      const d = await res.json();
      setGuideline(d.guideline);
      setSavedAt(new Date());
      toast.success('Brand Guideline gespeichert');
    } catch (e) { toast.error(e.message || 'Generierung fehlgeschlagen'); }
    finally { setGenerating(false); }
  };

  const g = guideline;

  if (!leadId) return (
    <div style={{ padding: '20px 24px', background: '#FEF3DC', borderRadius: 10, fontSize: 13, color: '#8A5C00' }}>
      Keine Lead-ID verfuegbar. Bitte Seite neu laden.
    </div>
  );

  if (loading) return (
    <div style={{ padding: '32px 24px', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12, color: 'var(--text-tertiary)' }}>
      <div style={{ width: 32, height: 32, borderRadius: '50%', border: '3px solid var(--border-light)', borderTopColor: 'var(--brand-primary, #004F59)', animation: 'spin .8s linear infinite' }} />
      <style>{`@keyframes spin{to{transform:rotate(360deg)}}`}</style>
      <div style={{ fontSize: 12 }}>Brand Guideline wird geladen…</div>
    </div>
  );

  return (
    <div style={{ fontFamily: 'var(--font-sans)' }}>

      {/* KI-Generator oder Status */}
      {!g ? (
        <div style={{
          background: 'linear-gradient(135deg, #004F59, #008EAA)',
          borderRadius: 12, padding: '18px 20px', margin: '16px 0',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 16, flexWrap: 'wrap',
        }}>
          <div>
            <div style={{ fontSize: 14, fontWeight: 900, color: '#FAE600', marginBottom: 4 }}>Brand Guideline generieren</div>
            <div style={{ fontSize: 12, color: 'rgba(255,255,255,.7)', lineHeight: 1.5 }}>
              Claude liest Brand Design, Briefing und Stil-Daten und erstellt ein vollstaendiges Design-Token-System.
            </div>
          </div>
          <button onClick={generate} disabled={generating} style={{
            background: '#FAE600', color: '#004F59', border: 'none', borderRadius: 8,
            padding: '11px 22px', fontSize: 12, fontWeight: 900,
            cursor: generating ? 'not-allowed' : 'pointer', whiteSpace: 'nowrap', flexShrink: 0,
            fontFamily: 'var(--font-sans)', opacity: generating ? 0.7 : 1,
          }}>
            {generating ? 'Generiert…' : 'Guideline generieren'}
          </button>
        </div>
      ) : (
        <div style={{
          background: '#E3F6EF', border: '0.5px solid #00875A33',
          borderRadius: 8, padding: '10px 14px', margin: '12px 0',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ fontSize: 14 }}>✓</span>
            <div>
              <div style={{ fontSize: 12, fontWeight: 700, color: '#00875A' }}>
                Automatisch gespeichert
              </div>
              <div style={{ fontSize: 10, color: '#4A7A5C', marginTop: 1 }}>
                {savedAt ? savedAt.toLocaleString('de-DE', { dateStyle: 'medium', timeStyle: 'short' }) : ''}
                {g?.meta?.style_keyword ? ` · ${g.meta.style_keyword}` : ''}
                {g?.meta?.farb_stimmung ? ` · ${g.meta.farb_stimmung}` : ''}
              </div>
            </div>
          </div>
          <button onClick={generate} disabled={generating} style={{
            background: 'transparent', color: '#00875A', border: '1px solid #00875A44',
            borderRadius: 6, padding: '5px 12px', fontSize: 11, fontWeight: 700,
            cursor: 'pointer', fontFamily: 'var(--font-sans)', flexShrink: 0,
          }}>{generating ? 'Generiert…' : 'Neu generieren'}</button>
        </div>
      )}

      {/* Schritt abschliessen */}
      {g && (projectId || project?.id) && (
        <button
          onClick={confirmStep}
          disabled={confirmingStep}
          style={{
            width: '100%', margin: '0 0 12px', padding: '12px',
            background: confirmingStep ? 'var(--border-light)' : '#FAE600',
            color: '#000', border: 'none', borderRadius: 8,
            fontSize: 13, fontWeight: 900,
            cursor: confirmingStep ? 'not-allowed' : 'pointer',
            fontFamily: 'var(--font-sans)',
            textTransform: 'uppercase', letterSpacing: '.05em',
          }}
        >
          {confirmingStep ? 'Wird gespeichert…' : 'Guideline abschliessen & weiter'}
        </button>
      )}

      {/* Tabs + Content */}
      {g && (
        <>
          <div style={{ display: 'flex', borderBottom: '0.5px solid var(--border-light)', marginBottom: 16 }}>
            {TABS.map(tab => (
              <button key={tab} onClick={() => setActiveTab(tab)} style={{
                padding: '8px 14px', fontSize: 11, fontWeight: 700,
                color: activeTab === tab ? 'var(--brand-primary)' : 'var(--text-tertiary)',
                background: 'none', border: 'none',
                borderBottom: activeTab === tab ? '2px solid #FAE600' : '2px solid transparent',
                cursor: 'pointer', fontFamily: 'var(--font-sans)',
                textTransform: 'uppercase', letterSpacing: '.06em',
              }}>{tab}</button>
            ))}
          </div>

          {/* FARBEN — klickbar zum Inline-Editieren */}
          {activeTab === 'Farben' && (
            <div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(100px, 1fr))', gap: 10, marginBottom: 16 }}>
                {Object.entries(g.colors || {}).map(([tokenKey, hex]) => {
                  const isEditing = editingToken === tokenKey;
                  const isDerived = ['primary_dark','primary_light','primary_subtle'].includes(tokenKey);
                  const displayHex = editedColors[tokenKey] || hex;
                  return (
                    <div key={tokenKey}>
                      <div
                        onClick={() => isDerived ? navigator.clipboard?.writeText(displayHex) : setEditingToken(isEditing ? null : tokenKey)}
                        style={{
                          width: '100%', height: 52, borderRadius: 8,
                          background: displayHex,
                          border: isEditing ? '2px solid var(--brand-primary)' : '0.5px solid rgba(0,0,0,.08)',
                          cursor: 'pointer', position: 'relative',
                        }}
                        title={isDerived ? `${displayHex} (auto — klick kopiert)` : `${tokenKey} bearbeiten`}
                      >
                        {!isDerived && <div style={{ position: 'absolute', top: 3, right: 4, fontSize: 9, color: 'rgba(255,255,255,.7)' }}>✎</div>}
                        {isDerived && <div style={{ position: 'absolute', top: 3, right: 4, fontSize: 8, color: 'rgba(255,255,255,.5)' }}>auto</div>}
                      </div>
                      {isEditing && !isDerived && (
                        <div style={{ border: '1.5px solid var(--brand-primary)', borderRadius: 8, padding: 10, background: 'var(--bg-surface)', marginTop: 4 }}>
                          <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                            <div style={{ width: 28, height: 28, borderRadius: 5, background: displayHex, border: '0.5px solid rgba(0,0,0,.1)' }} />
                            <input value={displayHex} onChange={e => setEditedColors(prev => ({ ...prev, [tokenKey]: e.target.value }))}
                              style={{ width: 90, padding: '4px 8px', border: '0.5px solid var(--border-light)', borderRadius: 5, fontSize: 12, fontFamily: 'monospace', background: 'var(--bg-surface)', color: 'var(--text-primary)' }} />
                            <input type="color" value={displayHex.length === 7 ? displayHex : '#000000'} onChange={e => setEditedColors(prev => ({ ...prev, [tokenKey]: e.target.value }))}
                              style={{ width: 28, height: 28, cursor: 'pointer', border: 'none' }} />
                            <button onClick={() => setEditingToken(null)} style={{ marginLeft: 'auto', padding: '4px 10px', fontSize: 10, background: 'var(--brand-primary)', color: '#fff', border: 'none', borderRadius: 5, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>OK</button>
                          </div>
                        </div>
                      )}
                      <div style={{ fontSize: 8, color: 'var(--text-tertiary)', fontFamily: 'monospace', textAlign: 'center', marginTop: 3 }}>{displayHex}</div>
                      <div style={{ fontSize: 8, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.04em', textAlign: 'center' }}>{tokenKey.replace(/_/g, ' ')}</div>
                    </div>
                  );
                })}
              </div>
              {Object.keys(editedColors).length > 0 && (
                <button
                  onClick={async () => {
                    const updated = { ...g, colors: { ...g.colors, ...editedColors } };
                    try {
                      await fetch(`${API_BASE_URL}/api/branddesign/${leadId}/guideline`, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
                        body: JSON.stringify({ guideline: updated }),
                      });
                      setGuideline(updated);
                      setEditedColors({});
                      setEditingToken(null);
                      setSavedAt(new Date());
                      toast.success('Aenderungen gespeichert');
                    } catch { toast.error('Speichern fehlgeschlagen'); }
                  }}
                  style={{ marginBottom: 12, padding: '9px 18px', background: '#FAE600', color: '#000', border: 'none', borderRadius: 7, fontSize: 11, fontWeight: 900, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}
                >
                  Aenderungen speichern
                </button>
              )}
              {g.css_variables && (
                <div>
                  <div style={{ fontSize: 10, fontWeight: 900, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.1em', marginBottom: 6 }}>CSS Variables</div>
                  <div style={{ background: '#1a1a2e', borderRadius: 8, padding: '12px 14px', fontFamily: 'monospace', fontSize: 11, color: '#a8b2d8', lineHeight: 1.8, whiteSpace: 'pre-wrap', maxHeight: 200, overflowY: 'auto' }}>{g.css_variables}</div>
                  <button onClick={() => { navigator.clipboard?.writeText(g.css_variables); toast.success('CSS kopiert'); }}
                    style={{ marginTop: 6, padding: '6px 14px', fontSize: 11, fontWeight: 700, background: 'var(--bg-surface)', border: '0.5px solid var(--border-light)', borderRadius: 6, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>Kopieren</button>
                </div>
              )}
            </div>
          )}

          {/* TYPOGRAFIE */}
          {activeTab === 'Typografie' && (
            <div>
              <div style={{ marginBottom: 12, fontSize: 12, color: 'var(--text-secondary)' }}>
                <strong>{g.typography?.font_heading}</strong> (Ueberschriften) · <strong>{g.typography?.font_body}</strong> (Fliesstext)
              </div>
              {Object.entries(g.typography?.scale || {}).map(([level, spec]) => (
                <div key={level} style={{ display: 'flex', alignItems: 'baseline', gap: 14, padding: '10px 0', borderBottom: '0.5px solid var(--surface)' }}>
                  <div style={{ width: 52, flexShrink: 0, fontSize: 9, fontWeight: 900, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.08em', background: 'var(--surface)', padding: '2px 6px', borderRadius: 3, textAlign: 'center' }}>{level.toUpperCase()}</div>
                  <div style={{
                    flex: 1,
                    fontFamily: level.startsWith('h') ? g.typography.font_heading : g.typography.font_body,
                    fontSize: Math.min(parseInt(spec.size) || 16, 28),
                    fontWeight: spec.weight || 400,
                    letterSpacing: spec.letter_spacing || 'normal',
                    textTransform: spec.text_transform || 'none',
                    color: 'var(--text-primary)', lineHeight: 1.3,
                  }}>
                    {level.startsWith('h') ? 'Beispiel-Ueberschrift' : level === 'button' ? 'JETZT ANFRAGEN' : level === 'label' ? 'LABEL' : 'Beispieltext fuer diese Groesse.'}
                  </div>
                  <div style={{ fontSize: 9, color: 'var(--text-tertiary)', textAlign: 'right', flexShrink: 0, fontFamily: 'monospace' }}>{spec.size} · {spec.weight}</div>
                </div>
              ))}
            </div>
          )}

          {/* KOMPONENTEN */}
          {activeTab === 'Komponenten' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              <div>
                <div style={{ fontSize: 10, fontWeight: 900, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.1em', marginBottom: 8 }}>Buttons</div>
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                  {['button_primary', 'button_secondary', 'button_accent'].map(key => {
                    const s = g.components?.[key] || {};
                    return (
                      <button key={key} style={{
                        background: s.background || 'transparent', color: s.color || '#000',
                        border: s.border || 'none', borderRadius: s.border_radius || '6px',
                        padding: s.padding || '10px 20px', fontSize: 13, fontWeight: 700, cursor: 'pointer', fontFamily: 'var(--font-sans)',
                      }}>
                        {key === 'button_primary' ? 'Primaer' : key === 'button_secondary' ? 'Sekundaer' : 'Akzent'}
                      </button>
                    );
                  })}
                </div>
              </div>
              {g.voice_tone && (
                <div>
                  <div style={{ fontSize: 10, fontWeight: 900, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.1em', marginBottom: 8 }}>Voice & Tone</div>
                  <div style={{ background: 'var(--surface)', borderRadius: 8, padding: '12px 14px' }}>
                    <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 4 }}>{g.voice_tone.charakter}</div>
                    <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginBottom: 8 }}>Ansprache: <strong>{g.voice_tone.ansprache}</strong></div>
                    <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                      {(g.voice_tone.cta_beispiele || []).map((cta, i) => (
                        <span key={i} style={{ background: g.colors?.primary || '#004F59', color: '#fff', fontSize: 11, fontWeight: 700, padding: '4px 12px', borderRadius: 5 }}>{cta}</span>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* VORSCHAU */}
          {activeTab === 'Vorschau' && (
            <div style={{ border: '0.5px solid var(--border-light)', borderRadius: 10, overflow: 'hidden' }}>
              <div style={{ background: g.colors?.primary || '#004F59', padding: '0 24px', height: 64, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span style={{ fontFamily: g.typography?.font_heading, fontSize: 18, fontWeight: 700, color: '#fff' }}>{g.meta?.company || 'Unternehmen'}</span>
                <button style={{ background: g.colors?.accent || '#F39C12', color: '#fff', border: 'none', borderRadius: g.border_radius?.md || '6px', padding: '8px 18px', fontSize: 13, fontWeight: 700, cursor: 'pointer' }}>
                  {g.voice_tone?.cta_beispiele?.[0] || 'Jetzt anfragen'}
                </button>
              </div>
              <div style={{ background: g.colors?.primary || '#004F59', padding: '40px 24px' }}>
                <div style={{ fontFamily: g.typography?.font_heading, fontSize: 32, fontWeight: 700, color: '#fff', marginBottom: 12, lineHeight: 1.15 }}>
                  {g.meta?.gewerk || 'Handwerk'} in Ihrer Region
                </div>
                <div style={{ fontSize: 15, color: 'rgba(255,255,255,.75)', marginBottom: 20, lineHeight: 1.6 }}>
                  Professionell · Zuverlaessig · {g.voice_tone?.charakter?.split(',')[0] || 'Modern'}
                </div>
              </div>
              <div style={{ background: g.colors?.surface || '#F5F5F5', padding: 24 }}>
                <div style={{ fontFamily: g.typography?.font_heading, fontSize: 20, fontWeight: 700, color: g.colors?.text_primary || '#1A1A1A', marginBottom: 8 }}>Unsere Leistungen</div>
                <div style={{ fontFamily: g.typography?.font_body, fontSize: 14, color: g.colors?.text_secondary || '#555', lineHeight: 1.7 }}>Professionelle Leistungen fuer Privat- und Gewerbekunden.</div>
              </div>
            </div>
          )}

          {/* EXPORT */}
          {activeTab === 'Export' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                <button onClick={() => { navigator.clipboard?.writeText(JSON.stringify(g, null, 2)); toast.success('JSON kopiert'); }}
                  style={{ padding: '9px 16px', borderRadius: 7, background: 'var(--bg-surface)', border: '0.5px solid var(--border-light)', fontSize: 12, fontWeight: 700, cursor: 'pointer', fontFamily: 'var(--font-sans)', display: 'flex', alignItems: 'center', gap: 6 }}>
                  JSON kopieren
                </button>
                <button onClick={() => { navigator.clipboard?.writeText(g.css_variables || ''); toast.success('CSS kopiert'); }}
                  style={{ padding: '9px 16px', borderRadius: 7, background: 'var(--bg-surface)', border: '0.5px solid var(--border-light)', fontSize: 12, fontWeight: 700, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
                  CSS Variables
                </button>
              </div>
              <div style={{ background: 'var(--surface)', borderRadius: 8, padding: '12px 14px', fontSize: 11, color: 'var(--text-secondary)', lineHeight: 1.7 }}>
                Die Brand Guideline wird beim GrapesJS-Editor automatisch als Design-Tokens uebergeben.
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

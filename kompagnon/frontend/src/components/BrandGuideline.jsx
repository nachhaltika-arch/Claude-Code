import { useState, useEffect, useCallback } from 'react';
import toast from 'react-hot-toast';
import API_BASE_URL from '../config';

const TABS = ['Farben', 'Typografie', 'Abstände', 'Komponenten', 'Vorschau', 'Export'];

export default function BrandGuideline({ project, lead, token, leadId, brandData }) {
  const [activeTab, setActiveTab] = useState('Farben');
  const [guideline, setGuideline]   = useState(null);
  const [loading, setLoading]       = useState(true);
  const [generating, setGenerating] = useState(false);

  const headers = {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${token}`,
  };

  const resolvedLeadId = leadId || project?.lead_id || lead?.id;

  const load = useCallback(async () => {
    if (!resolvedLeadId) return;
    setLoading(true);
    try {
      const res = await fetch(
        `${API_BASE_URL}/api/branddesign/${resolvedLeadId}/guideline`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (res.ok) {
        const d = await res.json();
        if (d.generated && d.guideline) setGuideline(d.guideline);
      }
    } catch { /* silent */ }
    finally { setLoading(false); }
  }, [resolvedLeadId]); // eslint-disable-line

  useEffect(() => { load(); }, [load]);

  const generate = async () => {
    setGenerating(true);
    try {
      const res = await fetch(
        `${API_BASE_URL}/api/branddesign/${resolvedLeadId}/guideline/generate`,
        { method: 'POST', headers }
      );
      if (!res.ok) throw new Error((await res.json()).detail || 'Fehler');
      const d = await res.json();
      setGuideline(d.guideline);
      toast.success('Brand Guideline generiert!');
    } catch (e) {
      toast.error(e.message || 'Generierung fehlgeschlagen');
    } finally {
      setGenerating(false);
    }
  };

  const g = guideline;

  if (loading) return (
    <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-tertiary)' }}>
      <div style={{ fontSize: 24, marginBottom: 8 }}>⏳</div>
      Wird geladen…
    </div>
  );

  return (
    <div style={{ fontFamily: 'var(--font-sans)' }}>

      {/* ── KI-Generator-Bar ── */}
      {!guideline ? (
        <div style={{
          background: 'linear-gradient(135deg, #004F59, #008EAA)',
          borderRadius: 12, padding: '18px 20px', margin: '4px 0 16px',
          display: 'flex', alignItems: 'center',
          justifyContent: 'space-between', gap: 16,
        }}>
          <div>
            <div style={{ fontSize: 14, fontWeight: 900, color: '#FAE600', marginBottom: 4 }}>
              Brand Guideline noch nicht generiert
            </div>
            <div style={{ fontSize: 12, color: 'rgba(255,255,255,.7)', lineHeight: 1.5 }}>
              Claude liest Brand Design, Briefing und Stil-Daten
              und erstellt ein vollständiges Design-Token-System — ca. 15 Sekunden.
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
      ) : (
        <div style={{
          background: 'var(--status-success-bg, #E3F6EF)',
          border: '0.5px solid #00875A33',
          borderRadius: 8, padding: '10px 14px', marginBottom: 12,
          display: 'flex', alignItems: 'center',
          justifyContent: 'space-between', gap: 12,
        }}>
          <div style={{ fontSize: 12, color: '#00875A', fontWeight: 700 }}>
            ✓ Brand Guideline generiert
            {g?.meta?.style_keyword ? ` — ${g.meta.style_keyword}` : ''}
            {g?.meta?.farb_stimmung ? ` · ${g.meta.farb_stimmung}` : ''}
          </div>
          <button
            onClick={generate}
            disabled={generating}
            style={{
              background: 'transparent', color: '#00875A',
              border: '1px solid #00875A44', borderRadius: 6,
              padding: '5px 12px', fontSize: 11, fontWeight: 700,
              cursor: 'pointer', fontFamily: 'var(--font-sans)',
            }}
          >
            {generating ? '⏳' : '↻ Neu generieren'}
          </button>
        </div>
      )}

      {/* ── Tab-Navigation ── */}
      {guideline && (
        <>
          <div style={{
            display: 'flex', borderBottom: '0.5px solid var(--border-light)',
            marginBottom: 16, gap: 0,
          }}>
            {TABS.map(tab => (
              <button key={tab} onClick={() => setActiveTab(tab)} style={{
                padding: '8px 14px', fontSize: 11, fontWeight: 700,
                color: activeTab === tab ? 'var(--brand-primary, #004F59)' : 'var(--text-tertiary)',
                background: 'none', border: 'none',
                borderBottom: activeTab === tab
                  ? '2px solid var(--brand-accent, #FAE600)'
                  : '2px solid transparent',
                cursor: 'pointer', fontFamily: 'var(--font-sans)',
                textTransform: 'uppercase', letterSpacing: '.06em',
                marginBottom: -1,
              }}>
                {tab}
              </button>
            ))}
          </div>

          {/* ── TAB: FARBEN ── */}
          {activeTab === 'Farben' && (
            <div>
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fill, minmax(96px, 1fr))',
                gap: 10, marginBottom: 16,
              }}>
                {Object.entries(g.colors || {}).map(([tk, hex]) => (
                  <div key={tk} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 5 }}>
                    <div
                      style={{
                        width: '100%', height: 52, borderRadius: 8, background: hex,
                        border: '0.5px solid rgba(0,0,0,.08)', cursor: 'pointer',
                        transition: 'transform .12s',
                      }}
                      onMouseEnter={e => e.currentTarget.style.transform = 'scale(1.05)'}
                      onMouseLeave={e => e.currentTarget.style.transform = 'scale(1)'}
                      onClick={() => {
                        navigator.clipboard?.writeText(hex);
                        toast.success(`${hex} kopiert`);
                      }}
                      title="Klick = kopieren"
                    />
                    <div style={{ fontSize: 9, fontWeight: 900, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '.04em', textAlign: 'center' }}>
                      {tk.replace(/_/g, ' ')}
                    </div>
                    <div style={{ fontSize: 8, color: 'var(--text-tertiary)', fontFamily: 'monospace' }}>
                      {hex}
                    </div>
                  </div>
                ))}
              </div>

              {g.css_variables && (
                <div>
                  <div style={{ fontSize: 10, fontWeight: 900, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.1em', marginBottom: 6 }}>
                    CSS Variables
                  </div>
                  <div style={{
                    background: '#1a1a2e', borderRadius: 8, padding: '12px 14px',
                    fontFamily: 'monospace', fontSize: 11, color: '#a8b2d8',
                    lineHeight: 1.8, whiteSpace: 'pre-wrap', maxHeight: 200, overflowY: 'auto',
                  }}>
                    {g.css_variables}
                  </div>
                  <button
                    onClick={() => { navigator.clipboard?.writeText(g.css_variables); toast.success('CSS Variables kopiert'); }}
                    style={{
                      marginTop: 6, padding: '6px 14px', fontSize: 11, fontWeight: 700,
                      background: 'var(--bg-app)', border: '0.5px solid var(--border-light)',
                      borderRadius: 6, cursor: 'pointer', fontFamily: 'var(--font-sans)',
                    }}
                  >
                    Kopieren
                  </button>
                </div>
              )}
            </div>
          )}

          {/* ── TAB: TYPOGRAFIE ── */}
          {activeTab === 'Typografie' && (
            <div>
              <div style={{ marginBottom: 12, fontSize: 12, color: 'var(--text-secondary)' }}>
                <strong>{g.typography?.font_heading}</strong> (Überschriften) ·{' '}
                <strong>{g.typography?.font_body}</strong> (Fließtext)
              </div>
              {Object.entries(g.typography?.scale || {}).map(([level, spec]) => (
                <div key={level} style={{
                  display: 'flex', alignItems: 'baseline', gap: 14,
                  padding: '10px 0', borderBottom: '0.5px solid var(--border-light)',
                }}>
                  <div style={{
                    width: 52, flexShrink: 0, fontSize: 9, fontWeight: 900,
                    color: 'var(--text-tertiary)', textTransform: 'uppercase',
                    letterSpacing: '.08em', background: 'var(--bg-app)',
                    padding: '2px 6px', borderRadius: 3, textAlign: 'center',
                  }}>
                    {level.toUpperCase()}
                  </div>
                  <div style={{
                    flex: 1,
                    fontFamily: level.startsWith('h') ? g.typography.font_heading : g.typography.font_body,
                    fontSize: parseInt(spec.size) > 32 ? 26 : parseInt(spec.size) > 20 ? 20 : parseInt(spec.size) > 16 ? 16 : 13,
                    fontWeight: spec.weight || 400,
                    letterSpacing: spec.letter_spacing || 'normal',
                    textTransform: spec.text_transform || 'none',
                    color: 'var(--text-primary)', lineHeight: 1.3,
                  }}>
                    {level === 'h1' ? 'Hauptüberschrift der Website'
                      : level === 'h2' ? 'Abschnittsüberschrift'
                      : level === 'h3' ? 'Karten-Überschrift'
                      : level === 'h4' ? 'Unterüberschrift'
                      : level === 'body_lg' ? 'Fließtext groß — Einleitungstext für wichtige Abschnitte.'
                      : level === 'body' ? 'Standard-Fließtext für Absätze und Beschreibungen.'
                      : level === 'body_sm' ? 'Kleiner Fließtext für Details und Hinweise.'
                      : level === 'label' ? 'LABEL · KATEGORIE'
                      : level === 'button' ? 'JETZT ANFRAGEN'
                      : 'Bildunterschrift · 22. April 2026'}
                  </div>
                  <div style={{ fontSize: 9, color: 'var(--text-tertiary)', textAlign: 'right', flexShrink: 0, fontFamily: 'monospace' }}>
                    {spec.size} · {spec.weight}
                    {spec.line_height ? ` · lh ${spec.line_height}` : ''}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* ── TAB: ABSTÄNDE ── */}
          {activeTab === 'Abstände' && (
            <div>
              <div style={{ display: 'flex', gap: 12, alignItems: 'flex-end', flexWrap: 'wrap', marginBottom: 24 }}>
                {Object.entries(g.spacing || {}).map(([tk, value]) => {
                  const px = parseInt(value) || 8;
                  return (
                    <div key={tk} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 5 }}>
                      <div style={{
                        width: Math.min(px, 96), height: Math.min(px, 96),
                        background: 'var(--brand-primary, #004F59)',
                        opacity: 0.15 + Math.min(px / 120, 0.75),
                        borderRadius: 4,
                      }} />
                      <div style={{ fontSize: 9, fontWeight: 900, color: 'var(--text-secondary)', fontFamily: 'monospace' }}>
                        --space-{tk}
                      </div>
                      <div style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>{value}</div>
                    </div>
                  );
                })}
              </div>

              <div style={{ marginBottom: 8, fontSize: 9, fontWeight: 900, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.08em' }}>
                Border Radius
              </div>
              <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'center' }}>
                {Object.entries(g.border_radius || {}).map(([tk, value]) => (
                  <div key={tk} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
                    <div style={{
                      width: 44, height: 44, background: 'var(--bg-app)',
                      border: '2px solid var(--brand-primary, #004F59)',
                      borderRadius: value === '9999px' ? '50%' : value,
                    }} />
                    <div style={{ fontSize: 8, color: 'var(--text-tertiary)', fontFamily: 'monospace' }}>{tk}</div>
                    <div style={{ fontSize: 8, color: 'var(--text-tertiary)' }}>{value}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ── TAB: KOMPONENTEN ── */}
          {activeTab === 'Komponenten' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
              {/* Buttons */}
              <div>
                <div style={{ fontSize: 10, fontWeight: 900, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.1em', marginBottom: 8 }}>Buttons</div>
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                  {['button_primary', 'button_secondary', 'button_accent'].map(key => {
                    const s = g.components?.[key] || {};
                    return (
                      <button key={key} style={{
                        background: s.background || 'transparent',
                        color: s.color || '#000',
                        border: s.border || 'none',
                        borderRadius: s.border_radius || '6px',
                        padding: s.padding || '10px 20px',
                        fontSize: 13, fontWeight: 700,
                        cursor: 'default', fontFamily: 'var(--font-sans)',
                      }}>
                        {key === 'button_primary' ? 'Primär Button'
                          : key === 'button_secondary' ? 'Sekundär Button'
                          : 'Akzent Button'}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Card */}
              <div>
                <div style={{ fontSize: 10, fontWeight: 900, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.1em', marginBottom: 8 }}>Karte</div>
                {(() => {
                  const s = g.components?.card || {};
                  return (
                    <div style={{
                      background: s.background || 'var(--bg-app)',
                      border: s.border || '0.5px solid var(--border-light)',
                      borderRadius: s.border_radius || '8px',
                      boxShadow: s.shadow || 'none',
                      padding: s.padding || '20px',
                      maxWidth: 320,
                    }}>
                      <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 6 }}>
                        {g.meta?.company || 'Muster GmbH'}
                      </div>
                      <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                        {g.meta?.gewerk || 'Handwerk'} · {g.meta?.farb_stimmung || 'Modern'}
                      </div>
                    </div>
                  );
                })()}
              </div>

              {/* Voice & Tone */}
              {g.voice_tone && (
                <div>
                  <div style={{ fontSize: 10, fontWeight: 900, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.1em', marginBottom: 8 }}>Voice & Tone</div>
                  <div style={{ background: 'var(--bg-app)', borderRadius: 8, padding: '12px 14px' }}>
                    <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 4 }}>{g.voice_tone.charakter}</div>
                    <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginBottom: 8 }}>Ansprache: <strong>{g.voice_tone.ansprache}</strong></div>
                    {(g.voice_tone.cta_beispiele || []).length > 0 && (
                      <>
                        <div style={{ fontSize: 9, fontWeight: 900, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.08em', marginBottom: 5 }}>CTA-Beispiele</div>
                        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                          {g.voice_tone.cta_beispiele.map((cta, i) => (
                            <span key={i} style={{
                              background: g.colors?.primary || 'var(--brand-primary)',
                              color: '#fff', fontSize: 11, fontWeight: 700,
                              padding: '4px 12px', borderRadius: 5,
                            }}>
                              {cta}
                            </span>
                          ))}
                        </div>
                      </>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* ── TAB: VORSCHAU ── */}
          {activeTab === 'Vorschau' && (
            <div style={{ border: '0.5px solid var(--border-light)', borderRadius: 10, overflow: 'hidden' }}>
              {/* Nav */}
              <div style={{
                background: g.colors?.primary || '#004F59', padding: '0 24px',
                height: g.components?.nav?.height || '64px',
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              }}>
                <span style={{ fontFamily: g.typography?.font_heading, fontSize: 18, fontWeight: 700, color: '#fff' }}>
                  {g.meta?.company || 'Unternehmen'}
                </span>
                <button style={{
                  background: g.colors?.accent || '#FAE600', color: '#000',
                  border: 'none', borderRadius: g.border_radius?.md || '6px',
                  padding: '8px 18px', fontSize: 13, fontWeight: 700, cursor: 'default',
                }}>
                  {g.voice_tone?.cta_beispiele?.[0] || 'Jetzt anfragen'}
                </button>
              </div>
              {/* Hero */}
              <div style={{ background: g.colors?.primary || '#004F59', padding: '40px 24px' }}>
                <div style={{
                  fontFamily: g.typography?.font_heading,
                  fontSize: 28, fontWeight: 700, color: '#fff', marginBottom: 10, lineHeight: 1.2,
                }}>
                  {g.meta?.gewerk || 'Handwerk'} in {g.meta?.company ? 'Ihrer Region' : 'Deutschland'}
                </div>
                <div style={{ fontSize: 14, color: 'rgba(255,255,255,.75)', marginBottom: 18, lineHeight: 1.6 }}>
                  Professionell · Zuverlässig · {g.voice_tone?.charakter?.split(',')[0] || 'Modern'}
                </div>
                <div style={{ display: 'flex', gap: 10 }}>
                  <button style={{
                    background: g.colors?.accent || '#FAE600', color: '#000',
                    border: 'none', borderRadius: g.border_radius?.md || '6px',
                    padding: '11px 22px', fontSize: 13, fontWeight: 700, cursor: 'default',
                  }}>
                    {g.voice_tone?.cta_beispiele?.[0] || 'Anfragen'}
                  </button>
                  <button style={{
                    background: 'transparent', color: '#fff',
                    border: '1.5px solid rgba(255,255,255,.5)',
                    borderRadius: g.border_radius?.md || '6px',
                    padding: '11px 22px', fontSize: 13, fontWeight: 700, cursor: 'default',
                  }}>
                    Mehr erfahren
                  </button>
                </div>
              </div>
              {/* Content */}
              <div style={{ background: g.colors?.surface || '#F5F5F5', padding: '24px' }}>
                <div style={{
                  fontFamily: g.typography?.font_heading, fontSize: 18, fontWeight: 700,
                  color: g.colors?.text_primary || '#1A1A1A', marginBottom: 8,
                }}>
                  Unsere Leistungen
                </div>
                <div style={{
                  fontFamily: g.typography?.font_body, fontSize: 14,
                  color: g.colors?.text_secondary || '#555', lineHeight: 1.7,
                }}>
                  Professionelle Leistungen für Privat- und Gewerbekunden.
                </div>
              </div>
              {/* Footer */}
              <div style={{
                background: g.colors?.secondary || '#2C3E50',
                padding: '16px 24px', display: 'flex', justifyContent: 'space-between',
              }}>
                <span style={{ fontSize: 11, color: 'rgba(255,255,255,.6)', fontFamily: g.typography?.font_body }}>
                  © {g.meta?.company || 'Unternehmen'}
                </span>
                <span style={{ fontSize: 11, color: 'rgba(255,255,255,.6)', fontFamily: g.typography?.font_body }}>
                  Impressum · Datenschutz
                </span>
              </div>
            </div>
          )}

          {/* ── TAB: EXPORT ── */}
          {activeTab === 'Export' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                <button
                  onClick={() => { navigator.clipboard?.writeText(JSON.stringify(g, null, 2)); toast.success('JSON kopiert'); }}
                  style={{
                    padding: '9px 16px', borderRadius: 7, background: 'var(--bg-app)',
                    border: '0.5px solid var(--border-light)', fontSize: 12, fontWeight: 700,
                    cursor: 'pointer', fontFamily: 'var(--font-sans)',
                  }}
                >
                  JSON kopieren
                </button>
                <button
                  onClick={() => { navigator.clipboard?.writeText(g.css_variables || ''); toast.success('CSS Variables kopiert'); }}
                  style={{
                    padding: '9px 16px', borderRadius: 7, background: 'var(--bg-app)',
                    border: '0.5px solid var(--border-light)', fontSize: 12, fontWeight: 700,
                    cursor: 'pointer', fontFamily: 'var(--font-sans)',
                  }}
                >
                  CSS Variables
                </button>
              </div>
              <pre style={{
                background: '#1a1a2e', color: '#a8b2d8', borderRadius: 8,
                padding: '12px 14px', fontFamily: 'monospace', fontSize: 10,
                lineHeight: 1.7, overflowX: 'auto', maxHeight: 320, margin: 0,
              }}>
                {JSON.stringify(g, null, 2)}
              </pre>
              <div style={{
                background: 'var(--bg-app)', borderRadius: 8, padding: '12px 14px',
                fontSize: 11, color: 'var(--text-secondary)', lineHeight: 1.7,
              }}>
                Die Brand Guideline wird beim GrapesJS-Editor automatisch als Design-Tokens übergeben —
                Farben, Fonts und Abstände sind im Editor sofort richtig gesetzt.
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

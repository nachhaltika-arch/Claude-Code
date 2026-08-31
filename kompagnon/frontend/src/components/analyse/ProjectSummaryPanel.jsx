/**
 * Die Projektzusammenfassung neben der Analyse-Zentrale (L-25).
 *
 * Am 2026-08-30 aus `AnalyseCentrale.jsx` herausgeloest — 164 Zeilen.
 */
import { useEffect, useState } from 'react';
import { aufTaste } from '../../utils/tastaturBedienung';

export function ProjectSummaryPanel({ leadId, headers, stepResults, savedPagespeed, savedBrand }) {
  const [pagespeed, setPagespeed] = useState(savedPagespeed || null);
  const [brand, setBrand]         = useState(savedBrand || null);
  const [designData, setDesignData] = useState(savedBrand?.design_data || null);

  // Sync from parent when saved data arrives
  useEffect(() => { if (savedPagespeed) setPagespeed(savedPagespeed); }, [savedPagespeed]);
  useEffect(() => {
    if (savedBrand) { setBrand(savedBrand); if (savedBrand.design_data) setDesignData(savedBrand.design_data); }
  }, [savedBrand]);

  const gaResult = stepResults?.analytics;

  const scoreColor = (s) => {
    if (s == null) return { bg: 'var(--bg-elevated)', text: 'var(--text-tertiary)' };
    if (s >= 90) return { bg: '#EAF4E0', text: '#2D6A0A' };
    if (s >= 50) return { bg: '#FEF3DC', text: '#8A5C00' };
    return { bg: '#FDEAEA', text: '#C0392B' };
  };

  return (
    <div style={{
      borderTop: '1px solid var(--border-light)',
      background: 'var(--bg-surface)',
      padding: '12px 14px',
      flexShrink: 0,
      display: 'flex',
      flexDirection: 'column',
      gap: 10,
    }}>
      {/* PageSpeed */}
      <div>
        <div style={{ fontSize: 9, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.08em', marginBottom: 6 }}>
          PageSpeed
        </div>
        {pagespeed ? (
          <div style={{ display: 'flex', gap: 6 }}>
            {[
              { label: 'Mobil',   score: pagespeed.mobile_score },
              { label: 'Desktop', score: pagespeed.desktop_score },
            ].map(({ label, score }) => {
              const c = scoreColor(score);
              return (
                <div key={label} style={{ flex: 1, borderRadius: 6, padding: '6px 8px', textAlign: 'center', background: c.bg }}>
                  <div style={{ fontSize: 18, fontWeight: 900, color: c.text, lineHeight: 1 }}>{score ?? '\u2014'}</div>
                  <div style={{ fontSize: 9, color: c.text, opacity: 0.7, marginTop: 2 }}>{label}</div>
                </div>
              );
            })}
          </div>
        ) : (
          <div style={{ fontSize: 12, color: 'var(--text-tertiary)', fontStyle: 'italic' }}>Noch nicht gemessen</div>
        )}
      </div>

      {/* Google Analytics */}
      <div>
        <div style={{ fontSize: 9, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.08em', marginBottom: 6 }}>Google Analytics</div>
        {gaResult != null ? (
          <div style={{ fontSize: 12, fontWeight: 600, padding: '5px 10px', borderRadius: 6, background: gaResult.ga_found ? '#EAF4E0' : '#FEF3DC', color: gaResult.ga_found ? '#2D6A0A' : '#8A5C00' }}>
            {gaResult.ga_found ? 'GA4 erkannt' : 'Kein GA4 gefunden'}
          </div>
        ) : (
          <div style={{ fontSize: 12, color: 'var(--text-tertiary)', fontStyle: 'italic' }}>Analyse ausstehend</div>
        )}
      </div>

      {/* Brand Design Board */}
      <div>
        <div style={{ fontSize: 9, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.08em', marginBottom: 8 }}>
          Brand Design
          {designData?.style_keyword && (
            <span style={{ marginLeft: 8, fontWeight: 600, color: 'var(--brand-primary-mid)', textTransform: 'none', letterSpacing: 0 }}>
              {designData.style_keyword}
            </span>
          )}
        </div>

        {designData ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>

            {/* Farb-Palette */}
            <div>
              <div style={{ fontSize: 9, color: 'var(--text-tertiary)', marginBottom: 4 }}>Farben</div>
              <div style={{ display: 'flex', gap: 4, overflowX: 'auto', paddingBottom: 4 }}>
                {[
                  { color: designData.colors?.primary,    label: 'P' },
                  { color: designData.colors?.secondary,  label: 'S' },
                  { color: designData.colors?.accent,     label: 'A' },
                  { color: designData.colors?.background, label: 'BG' },
                  { color: designData.colors?.text,       label: 'T' },
                  ...(designData.colors?.all || [])
                    .filter(c => ![designData.colors?.primary, designData.colors?.secondary, designData.colors?.accent, designData.colors?.background, designData.colors?.text].includes(c))
                    .slice(0, 6).map(c => ({ color: c, label: '' })),
                ].filter(e => e.color).map(({ color, label }, i) => (
                  <div role="button" tabIndex={0} onKeyDown={aufTaste(() => navigator.clipboard?.writeText(color))} key={i} title={`${label ? label + ': ' : ''}${color}`} onClick={() => navigator.clipboard?.writeText(color)} style={{ flexShrink: 0, cursor: 'pointer' }}>
                    <div style={{ width: label ? 28 : 20, height: label ? 28 : 20, borderRadius: 4, background: color, border: '1px solid var(--border-light)' }} />
                    {label && <div style={{ fontSize: 8, color: 'var(--text-tertiary)', textAlign: 'center', marginTop: 2 }}>{label}</div>}
                  </div>
                ))}
              </div>
            </div>

            {/* Schrift-Vorschau */}
            {designData.fonts?.length > 0 && (
              <div>
                <div style={{ fontSize: 9, color: 'var(--text-tertiary)', marginBottom: 4 }}>Schriften</div>
                {designData.fonts.slice(0, 2).map((font, i) => (
                  <div key={i} style={{ fontSize: i === 0 ? 13 : 11, fontWeight: i === 0 ? 700 : 400, color: 'var(--text-primary)', lineHeight: 1.3, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', marginBottom: 2 }}>
                    {font}
                  </div>
                ))}
              </div>
            )}

            {/* Design-DNA Chips */}
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
              {[
                designData.border_radius_style && designData.border_radius_style !== 'unbekannt' && `${designData.border_radius_style}`,
                designData.shadow_label && `${designData.shadow_label}`,
                designData.button_style && `btn: ${designData.button_style}`,
                designData.spacing_density && `${designData.spacing_density}`,
                designData.farb_stimmung && `${designData.farb_stimmung}`,
              ].filter(Boolean).map((chip, i) => (
                <span key={i} style={{ fontSize: 9, padding: '2px 6px', background: 'var(--bg-elevated)', border: '1px solid var(--border-light)', borderRadius: 4, color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>
                  {chip}
                </span>
              ))}
            </div>

            {/* KI Design Brief */}
            {designData.design_brief?.fuer_ki_prompt && (
              <details style={{ fontSize: 10 }}>
                <summary style={{ cursor: 'pointer', color: 'var(--brand-primary-mid)', fontWeight: 600, fontSize: 10 }}>
                  KI-Design-Brief
                </summary>
                <div style={{ marginTop: 6, padding: '8px 10px', background: 'var(--bg-app)', borderRadius: 6, fontSize: 10, color: 'var(--text-secondary)', lineHeight: 1.6, border: '1px solid var(--border-light)' }}>
                  {designData.design_brief.fuer_ki_prompt}
                </div>
                <button onClick={() => navigator.clipboard?.writeText(designData.design_brief.fuer_ki_prompt)}
                  style={{ marginTop: 4, fontSize: 10, padding: '3px 8px', background: 'none', border: '1px solid var(--border-light)', borderRadius: 4, cursor: 'pointer', color: 'var(--brand-primary-mid)', fontFamily: 'var(--font-sans)' }}>
                  Kopieren
                </button>
              </details>
            )}

            {!designData.design_brief && designData.style_beschreibung && (
              <div style={{ fontSize: 10, color: 'var(--text-tertiary)', lineHeight: 1.5, fontStyle: 'italic' }}>{designData.style_beschreibung}</div>
            )}
          </div>
        ) : brand?.primary_color ? (
          <div style={{ display: 'flex', gap: 4 }}>
            {[brand.primary_color, brand.secondary_color].filter(Boolean).map((c, i) => (
              <div key={i} style={{ width: 20, height: 20, borderRadius: 4, background: c, border: '1px solid var(--border-light)' }} />
            ))}
            {brand.font_primary && <span style={{ fontSize: 10, color: 'var(--text-secondary)', marginLeft: 4 }}>{brand.font_primary}</span>}
          </div>
        ) : (
          <div style={{ fontSize: 12, color: 'var(--text-tertiary)', fontStyle: 'italic' }}>Brand-Scan starten</div>
        )}
      </div>
    </div>
  );
}

import { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import API_BASE_URL from '../config';

const STILE = ['Klassisch', 'Modern', 'Minimalistisch', 'Verspielt', 'Industriell', 'Natuerlich'];
const RADIEN = [
  { label: 'Eckig', value: '0px', preview: 0 },
  { label: 'Rund',  value: '8px', preview: 8 },
  { label: 'Pill',  value: '24px', preview: 24 },
];

export default function BrandDesignWerkstatt({ project, lead, token, onBrandSaved }) {
  const leadId  = project?.lead_id || lead?.id;
  const headers = { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` };

  const [brand, setBrand]         = useState(null);
  const [loading, setLoading]     = useState(true);
  const [scanning, setScanning]   = useState(false);
  const [saving, setSaving]       = useState(false);
  const [suggesting, setSuggesting] = useState(false);
  const [fontSuggestions, setFontSuggestions] = useState([]);

  const [primaryColor, setPrimaryColor]     = useState('#004F59');
  const [secondaryColor, setSecondaryColor] = useState('#008EAA');
  const [accentColor, setAccentColor]       = useState('#FAE600');
  const [allColors, setAllColors]           = useState([]);
  const [fontPrimary, setFontPrimary]       = useState('');
  const [fontSecondary, setFontSecondary]   = useState('');
  const [designStyle, setDesignStyle]       = useState('Modern');
  const [borderRadius, setBorderRadius]     = useState('8px');
  const [logoUrl, setLogoUrl]               = useState('');
  const [companyName, setCompanyName]       = useState('');

  useEffect(() => {
    if (!leadId) return;
    (async () => {
      setLoading(true);
      try {
        const res = await fetch(`${API_BASE_URL}/api/branddesign/${leadId}`, { headers });
        if (res.ok) {
          const d = await res.json();
          applyBrandData(d);
          setBrand(d);
        }
      } catch { /* silent */ }
      finally { setLoading(false); }
    })();
    setCompanyName(lead?.company_name || lead?.display_name || '');
  }, [leadId]); // eslint-disable-line

  const applyBrandData = (d) => {
    if (d.primary_color)      setPrimaryColor(d.primary_color);
    if (d.secondary_color)    setSecondaryColor(d.secondary_color);
    if (d.all_colors?.length > 2) setAccentColor(d.all_colors[2]);
    if (d.all_colors)         setAllColors(d.all_colors || []);
    if (d.font_primary)       setFontPrimary(d.font_primary);
    if (d.font_secondary)     setFontSecondary(d.font_secondary);
    if (d.brand_design_style) setDesignStyle(d.brand_design_style);
    if (d.logo_url)           setLogoUrl(d.logo_url);
  };

  const scanBrand = async () => {
    setScanning(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/branddesign/${leadId}/scrape`, { method: 'POST', headers });
      if (!res.ok) throw new Error('Scraping fehlgeschlagen');
      const d = await res.json();
      applyBrandData(d);
      setBrand(d);
      toast.success('Brand-Daten von Website gescannt');
    } catch (e) { toast.error(e.message || 'Scan fehlgeschlagen'); }
    finally { setScanning(false); }
  };

  const suggestFonts = async () => {
    setSuggesting(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/branddesign/${leadId}/suggest-fonts`, { method: 'POST', headers });
      if (res.ok) {
        const d = await res.json();
        setFontSuggestions(d.suggestions || []);
        toast.success('KI-Font-Vorschlaege geladen');
      }
    } catch { toast.error('Font-Vorschlaege konnten nicht geladen werden'); }
    finally { setSuggesting(false); }
  };

  const saveBrand = async () => {
    setSaving(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/branddesign/${leadId}/save`, {
        method: 'POST', headers,
        body: JSON.stringify({
          primary_color: primaryColor, secondary_color: secondaryColor,
          font_primary: fontPrimary, font_secondary: fontSecondary,
          design_style: designStyle, logo_url: logoUrl,
          brand_notes: `radius:${borderRadius}`,
        }),
      });
      if (!res.ok) throw new Error('Speichern fehlgeschlagen');
      toast.success('Brand Design gespeichert');
      if (onBrandSaved) onBrandSaved({ primary_color: primaryColor, font_primary: fontPrimary });
    } catch (e) { toast.error(e.message); }
    finally { setSaving(false); }
  };

  if (loading) return (
    <div style={{ padding: 32, textAlign: 'center', color: 'var(--text-tertiary)' }}>
      Brand-Daten werden geladen…
    </div>
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16, padding: '16px 0', fontFamily: 'var(--font-sans)' }}>

      {/* Scan-Banner */}
      <div style={{
        background: brand?.scraped_at ? '#E3F6EF' : '#F0F4F5',
        border: `0.5px solid ${brand?.scraped_at ? 'rgba(0,135,90,.2)' : 'var(--border-light)'}`,
        borderRadius: 10, padding: '12px 16px',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12,
      }}>
        <div>
          <div style={{ fontSize: 12, fontWeight: 700, color: brand?.scraped_at ? '#00875A' : 'var(--text-secondary)' }}>
            {brand?.scraped_at ? `Automatisch gescannt` : 'Noch kein Brand-Scan'}
          </div>
          <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 2 }}>
            {brand?.scraped_at
              ? 'Farben und Schriften von der alten Website uebernommen. Pruefe und passe an.'
              : 'Website scannen um Farben, Schriften und Logo automatisch zu erkennen.'}
          </div>
        </div>
        <button onClick={scanBrand} disabled={scanning} style={{
          background: 'var(--brand-primary)', color: '#fff', border: 'none', borderRadius: 7,
          padding: '8px 16px', fontSize: 11, fontWeight: 700,
          cursor: scanning ? 'not-allowed' : 'pointer', flexShrink: 0,
          fontFamily: 'var(--font-sans)', opacity: scanning ? 0.7 : 1,
        }}>
          {scanning ? 'Scannt…' : 'Website scannen'}
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>

        {/* Farben */}
        <div style={{ background: 'var(--bg-surface)', border: '0.5px solid var(--border-light)', borderRadius: 10, padding: 16 }}>
          <div style={{ fontSize: 9, fontWeight: 900, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.1em', marginBottom: 14 }}>Farbpalette</div>
          {[
            { label: 'Primaerfarbe', value: primaryColor, set: setPrimaryColor },
            { label: 'Sekundaerfarbe', value: secondaryColor, set: setSecondaryColor },
            { label: 'Akzentfarbe', value: accentColor, set: setAccentColor },
          ].map(({ label, value, set }) => (
            <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
              <input type="color" value={value} onChange={e => set(e.target.value)}
                style={{ width: 40, height: 40, borderRadius: 8, border: 'none', cursor: 'pointer', padding: 2 }} />
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-primary)' }}>{label}</div>
                <div style={{ fontFamily: 'monospace', fontSize: 11, color: 'var(--text-tertiary)' }}>{value}</div>
              </div>
            </div>
          ))}
          {allColors.length > 3 && (
            <div style={{ marginTop: 8 }}>
              <div style={{ fontSize: 9, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.08em', marginBottom: 6 }}>Weitere erkannte Farben</div>
              <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap' }}>
                {allColors.slice(3, 12).map((c, i) => (
                  <div key={i} onClick={() => setPrimaryColor(c)} title={c}
                    style={{ width: 28, height: 28, borderRadius: 6, background: c, border: '1px solid rgba(0,0,0,.08)', cursor: 'pointer' }} />
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Schriften + Stil */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div style={{ background: 'var(--bg-surface)', border: '0.5px solid var(--border-light)', borderRadius: 10, padding: 16, flex: 1 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
              <div style={{ fontSize: 9, fontWeight: 900, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.1em' }}>Schriften</div>
              <button onClick={suggestFonts} disabled={suggesting} style={{
                background: 'transparent', color: 'var(--brand-primary)',
                border: '1px solid var(--border-light)', borderRadius: 5,
                padding: '4px 10px', fontSize: 10, fontWeight: 700,
                cursor: suggesting ? 'not-allowed' : 'pointer', fontFamily: 'var(--font-sans)',
              }}>{suggesting ? '…' : 'KI-Vorschlag'}</button>
            </div>
            <div style={{ fontSize: 9, fontWeight: 900, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.1em', marginBottom: 6 }}>Ueberschriften</div>
            <input value={fontPrimary} onChange={e => setFontPrimary(e.target.value)} placeholder="z.B. Montserrat"
              style={{ width: '100%', padding: '7px 10px', fontSize: 14, fontWeight: 700, border: '1px solid var(--border-light)', borderRadius: 6, fontFamily: fontPrimary || 'inherit', boxSizing: 'border-box', color: 'var(--text-primary)', background: 'var(--bg-app)', marginBottom: 10 }} />
            <div style={{ fontSize: 9, fontWeight: 900, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.1em', marginBottom: 6 }}>Fliesstext</div>
            <input value={fontSecondary} onChange={e => setFontSecondary(e.target.value)} placeholder="z.B. Inter"
              style={{ width: '100%', padding: '7px 10px', fontSize: 13, border: '1px solid var(--border-light)', borderRadius: 6, fontFamily: fontSecondary || 'inherit', boxSizing: 'border-box', color: 'var(--text-primary)', background: 'var(--bg-app)' }} />
            {fontSuggestions.length > 0 && (
              <div style={{ marginTop: 10 }}>
                <div style={{ fontSize: 9, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.08em', marginBottom: 6 }}>KI-Empfehlungen</div>
                {fontSuggestions.map(f => (
                  <div key={f.name} onClick={() => { f.use?.toLowerCase().includes('berschrift') ? setFontPrimary(f.name) : setFontSecondary(f.name); toast.success(`${f.name} uebernommen`); }}
                    style={{ padding: '7px 10px', borderRadius: 6, border: '1px solid var(--border-light)', marginBottom: 5, cursor: 'pointer', background: 'var(--bg-app)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: 14, fontWeight: 700 }}>{f.name}</span>
                    <span style={{ fontSize: 9, color: 'var(--text-tertiary)', background: 'var(--bg-surface)', padding: '2px 6px', borderRadius: 3 }}>{f.use}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Stil */}
          <div style={{ background: 'var(--bg-surface)', border: '0.5px solid var(--border-light)', borderRadius: 10, padding: 16 }}>
            <div style={{ fontSize: 9, fontWeight: 900, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.1em', marginBottom: 10 }}>Charakter</div>
            <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap', marginBottom: 12 }}>
              {STILE.map(s => (
                <button key={s} onClick={() => setDesignStyle(s)} style={{
                  padding: '5px 10px', borderRadius: 5,
                  border: designStyle === s ? 'none' : '0.5px solid var(--border-light)',
                  background: designStyle === s ? 'var(--brand-primary)' : 'transparent',
                  color: designStyle === s ? '#fff' : 'var(--text-secondary)',
                  fontSize: 10, fontWeight: 700, cursor: 'pointer', fontFamily: 'var(--font-sans)',
                }}>{s}</button>
              ))}
            </div>
            <div style={{ fontSize: 9, fontWeight: 900, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.1em', marginBottom: 8 }}>Ecken-Radius</div>
            <div style={{ display: 'flex', gap: 8 }}>
              {RADIEN.map(r => (
                <button key={r.value} onClick={() => setBorderRadius(r.value)} style={{
                  width: 52, height: 52,
                  border: borderRadius === r.value ? '2px solid var(--brand-primary)' : '1.5px solid var(--border-light)',
                  borderRadius: r.preview, background: borderRadius === r.value ? '#E0F4F8' : '#fff',
                  cursor: 'pointer', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 3,
                  fontSize: 9, fontWeight: 700, color: borderRadius === r.value ? 'var(--brand-primary)' : 'var(--text-tertiary)', fontFamily: 'var(--font-sans)',
                }}>{r.label}</button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Live-Vorschau */}
      <div style={{ background: 'var(--bg-surface)', border: '0.5px solid var(--border-light)', borderRadius: 10, overflow: 'hidden' }}>
        <div style={{ fontSize: 9, fontWeight: 900, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.1em', padding: '10px 16px', borderBottom: '0.5px solid var(--border-light)' }}>Live-Vorschau</div>
        <div style={{ padding: 16 }}>
          <div style={{ border: '0.5px solid var(--border-light)', borderRadius: parseInt(borderRadius) > 0 ? 12 : 0, overflow: 'hidden' }}>
            <div style={{ background: primaryColor, padding: '14px 18px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ fontFamily: fontPrimary ? `'${fontPrimary}', serif` : 'serif', fontSize: 16, fontWeight: 700, color: '#fff' }}>{companyName || 'Firmenname'}</span>
              <button style={{ background: accentColor, color: '#000', border: 'none', borderRadius: borderRadius, padding: '7px 14px', fontSize: 12, fontWeight: 700, cursor: 'default' }}>Kontakt</button>
            </div>
            <div style={{ padding: '16px 18px', background: '#fff' }}>
              <h2 style={{ fontFamily: fontPrimary ? `'${fontPrimary}', serif` : 'serif', fontSize: 20, fontWeight: 700, color: secondaryColor, marginBottom: 8 }}>Headline der neuen Website</h2>
              <p style={{ fontFamily: fontSecondary ? `'${fontSecondary}', sans-serif` : 'sans-serif', fontSize: 13, color: '#555', lineHeight: 1.6, marginBottom: 14 }}>Beschreibungstext mit dem gewaehlten Fliesstext-Font. Professionell, klar und auf die Zielgruppe abgestimmt.</p>
              <button style={{ background: primaryColor, color: '#fff', border: 'none', borderRadius: borderRadius, padding: '9px 18px', fontSize: 12, fontWeight: 700, cursor: 'default' }}>Jetzt anfragen</button>
            </div>
          </div>
        </div>
      </div>

      {/* Speichern */}
      <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
        <button onClick={saveBrand} disabled={saving} style={{
          background: 'var(--brand-primary)', color: '#fff', border: 'none', borderRadius: 8,
          padding: '11px 24px', fontSize: 13, fontWeight: 700,
          cursor: saving ? 'not-allowed' : 'pointer', fontFamily: 'var(--font-sans)', opacity: saving ? 0.7 : 1,
        }}>{saving ? 'Wird gespeichert…' : 'Brand Design speichern'}</button>
      </div>
    </div>
  );
}

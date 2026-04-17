import { useState, useEffect, useRef } from 'react';
import toast from 'react-hot-toast';
import API_BASE_URL from '../config';

function adjustColor(hex, amount) {
  const num = parseInt((hex || '#000000').replace('#', ''), 16) || 0;
  const r = Math.min(255, Math.max(0, (num >> 16) + amount));
  const g = Math.min(255, Math.max(0, ((num >> 8) & 0xff) + amount));
  const b = Math.min(255, Math.max(0, (num & 0xff) + amount));
  return '#' + [r, g, b].map(x => x.toString(16).padStart(2, '0')).join('');
}

const QUICK_ACCENTS = ['#F39C12','#E67E22','#FAE600','#2ECC71','#3498DB','#9B59B6','#1ABC9C','#E74C3C'];

const GOOGLE_FONTS_CATALOG = {
  'Serif — Klassisch': [
    'Georgia','Times New Roman','Playfair Display','Merriweather',
    'Lora','Libre Baskerville','PT Serif','Crimson Text',
    'EB Garamond','Cormorant Garamond',
  ],
  'Sans-Serif — Modern': [
    'Inter','Roboto','Open Sans','Noto Sans','Source Sans 3',
    'Nunito','Mulish','DM Sans','Plus Jakarta Sans','Outfit',
    'Figtree','Albert Sans',
  ],
  'Sans-Serif — Neutral': [
    'Arial','Helvetica','Lato','Raleway','Montserrat',
    'Poppins','Urbanist','Rubik','Work Sans','Manrope',
  ],
  'Condensed / Display': [
    'Barlow Condensed','Oswald','Anton','Bebas Neue',
    'Fjalla One','Squada One','Big Shoulders Display',
    'League Gothic','Passion One',
  ],
  'Handwerk / Regional': [
    'Teko','Exo 2','Titillium Web','Asap','Cabin',
    'Josefin Sans','Prompt','Saira','IBM Plex Sans',
  ],
  'Slab Serif': [
    'Roboto Slab','Arvo','Zilla Slab','Crete Round',
    'Alfa Slab One','Tinos',
  ],
};

const ALL_FONTS_FLAT = Object.values(GOOGLE_FONTS_CATALOG).flat();

const _loadedFonts = new Set();
function loadGoogleFont(fontName) {
  if (!fontName) return;
  const systemFonts = ['Arial','Helvetica','Georgia','Times New Roman','Courier New','Verdana','Trebuchet MS'];
  if (systemFonts.includes(fontName)) return;
  if (_loadedFonts.has(fontName)) return;
  const encoded = fontName.replace(/ /g, '+');
  if (document.querySelector(`link[href*="${encoded}"]`)) { _loadedFonts.add(fontName); return; }
  const link = document.createElement('link');
  link.rel = 'stylesheet';
  link.href = `https://fonts.googleapis.com/css2?family=${encoded}:wght@400;600;700;900&display=swap`;
  document.head.appendChild(link);
  _loadedFonts.add(fontName);
}

export default function BrandDesignEditor({ leadId, token, brandData, onSaved }) {
  const [primary, setPrimary]       = useState(brandData?.primary_color || '#004F59');
  const [secondary, setSecondary]   = useState(brandData?.secondary_color || '#2C3E50');
  const [accent, setAccent]         = useState('#F39C12');

  const [fontH1, setFontH1]         = useState(brandData?.font_heading || brandData?.font_primary || 'Georgia');
  const [fontBody, setFontBody]     = useState(brandData?.font_body || brandData?.font_secondary || 'Arial');
  const [fontAkzent, setFontAkzent] = useState(brandData?.font_accent || 'Barlow Condensed');

  const [colorH1, setColorH1]       = useState('#FFFFFF');
  const [colorBody, setColorBody]   = useState('#CCCCCC');
  const [colorAkzent, setColorAkzent] = useState('#FAE600');
  const [colorBg, setColorBg]       = useState('#1A1A1A');
  const [colorField, setColorField] = useState('#F5F5F0');

  const [radius, setRadius]         = useState(6);
  const [shadow, setShadow]         = useState('leicht');
  const [activeToken, setActiveToken] = useState(null);
  const [saving, setSaving]         = useState(false);
  const editorRef = useRef(null);

  useEffect(() => {
    const close = (e) => { if (editorRef.current && !editorRef.current.contains(e.target)) setActiveToken(null); };
    document.addEventListener('mousedown', close);
    return () => document.removeEventListener('mousedown', close);
  }, []);

  useEffect(() => {
    if (!leadId || !token) return;
    fetch(`${API_BASE_URL}/api/branddesign/${leadId}`, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => r.ok ? r.json() : null)
      .then(d => {
        if (!d) return;
        if (d.primary_color) setPrimary(d.primary_color);
        if (d.secondary_color) setSecondary(d.secondary_color);
        if (d.font_heading || d.font_primary) setFontH1(d.font_heading || d.font_primary);
        if (d.font_body || d.font_secondary) setFontBody(d.font_body || d.font_secondary);
        if (d.font_accent) setFontAkzent(d.font_accent);
        const dd = d.design_data;
        if (dd?.border_radius_px) setRadius(dd.border_radius_px);
        if (dd?.shadow_label) setShadow(dd.shadow_label);
        const ac = dd?.design_brief?.akzentfarbe || dd?.colors?.accent;
        if (ac) setAccent(ac);
      }).catch(() => {});
  }, [leadId, token]); // eslint-disable-line

  useEffect(() => {
    const detected = [
      brandData?.font_heading, brandData?.font_body, brandData?.font_accent,
      brandData?.font_primary, brandData?.font_secondary,
      ...(brandData?.all_fonts || []),
      ...(brandData?.fonts_detail?.google_fonts || []),
    ].filter(Boolean);
    detected.forEach(loadGoogleFont);

    if (brandData?.font_heading || brandData?.font_primary) {
      const f = brandData.font_heading || brandData.font_primary;
      setFontH1(f); loadGoogleFont(f);
    }
    if (brandData?.font_body || brandData?.font_secondary) {
      const f = brandData.font_body || brandData.font_secondary;
      setFontBody(f); loadGoogleFont(f);
    }
    if (brandData?.font_accent) { setFontAkzent(brandData.font_accent); loadGoogleFont(brandData.font_accent); }
    if (brandData?.secondary_color) setColorBg(brandData.secondary_color);
    if (brandData?.all_colors?.[2]) setColorField(brandData.all_colors[2]);
  }, [brandData]); // eslint-disable-line

  const save = async () => {
    setSaving(true);
    try {
      await fetch(`${API_BASE_URL}/api/branddesign/${leadId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          primary_color: primary,
          secondary_color: secondary,
          font_primary: fontH1,
          font_secondary: fontBody,
          font_heading: fontH1,
          font_body: fontBody,
          font_accent: fontAkzent,
        }),
      });
      toast.success('Brand Design gespeichert');
      if (onSaved) onSaved({ primary, secondary, accent, fontH1, fontBody, fontAkzent, radius });
    } catch { toast.error('Speichern fehlgeschlagen'); }
    finally { setSaving(false); }
  };

  const tokens = [
    { id: 'primary',   label: 'Primaer',      color: primary,    type: 'color',   setter: setPrimary },
    { id: 'primary_d', label: 'Primaer Dark', color: adjustColor(primary, -30), type: 'derived', setter: null },
    { id: 'secondary', label: 'Sekundaer',    color: secondary,  type: 'color',   setter: setSecondary },
    { id: 'accent',    label: 'Akzent',       color: accent,     type: 'color',   setter: setAccent },
    { id: 'surface',   label: 'Surface',      color: '#F5F5F0',  type: 'color',   setter: null },
    { id: 'bg',        label: 'Hintergrund',  color: colorBg,    type: 'color',   setter: setColorBg },
    { id: 'field',     label: 'Felder',       color: colorField, type: 'color',   setter: setColorField },
    { id: 'h1_color',  label: 'Ueberschrift', color: colorH1,    type: 'color',   setter: setColorH1 },
  ];

  const detectedFonts = [
    ...(brandData?.fonts_detail?.google_fonts || []),
    brandData?.font_heading, brandData?.font_body, brandData?.font_accent,
    brandData?.font_primary, brandData?.font_secondary,
    ...(brandData?.all_fonts || []),
  ].filter(Boolean).filter((v, i, a) => a.indexOf(v) === i);

  const fontRoles = [
    {
      role: 'h1', label: 'Ueberschriften (H1 · H2 · H3)',
      font: fontH1, setFont: (f) => { setFontH1(f); loadGoogleFont(f); },
      color: colorH1, setColor: setColorH1,
      sample: 'Ueberschrift — Ihr Handwerksbetrieb',
      sampleStyle: { fontSize: 16, fontWeight: 700 },
    },
    {
      role: 'body', label: 'Fliesstext',
      font: fontBody, setFont: (f) => { setFontBody(f); loadGoogleFont(f); },
      color: colorBody, setColor: setColorBody,
      sample: 'Fliesstext — professionell und gut lesbar.',
      sampleStyle: { fontSize: 12, fontWeight: 400, lineHeight: 1.6 },
    },
    {
      role: 'akzent', label: 'Akzent (Buttons · CTA)',
      font: fontAkzent, setFont: (f) => { setFontAkzent(f); loadGoogleFont(f); },
      color: colorAkzent, setColor: setColorAkzent,
      sample: 'JETZT ANFRAGEN',
      sampleStyle: { fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '.06em' },
    },
  ];

  return (
    <div ref={editorRef} style={{ fontFamily: 'var(--font-sans)' }}>

      {/* Mini-Vorschau */}
      <div style={{ border: '0.5px solid var(--border-light)', borderRadius: 10, overflow: 'hidden', marginBottom: 16 }}>
        <div style={{ background: primary, padding: '10px 16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <span style={{ fontFamily: fontH1, fontSize: 15, fontWeight: 700, color: colorH1 }}>Firmenname</span>
          <button style={{ background: accent, color: colorAkzent, border: 'none', borderRadius: radius, padding: '6px 14px', fontSize: 12, fontWeight: 700, fontFamily: fontAkzent, cursor: 'default' }}>Anfragen</button>
        </div>
        <div style={{ background: adjustColor(primary, -20), padding: 16 }}>
          <div style={{ fontFamily: fontH1, fontSize: 20, fontWeight: 700, color: colorH1, marginBottom: 4 }}>
            Ueberschrift H1 — Ihr Handwerksbetrieb
          </div>
          <div style={{ fontFamily: fontH1, fontSize: 15, fontWeight: 600, color: colorH1, opacity: 0.8, marginBottom: 8 }}>
            Ueberschrift H2 — Unsere Leistungen
          </div>
          <div style={{ fontFamily: fontBody, fontSize: 13, color: colorBody, lineHeight: 1.6, marginBottom: 10 }}>
            Fliesstext mit dem gewaehlten Body-Font — klar, lesbar und professionell.
          </div>
          <button style={{ background: accent, color: colorAkzent, border: 'none', borderRadius: radius, padding: '8px 16px', fontFamily: fontAkzent, fontSize: 12, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '.05em', cursor: 'default' }}>
            Akzent-Button
          </button>
        </div>
        <div style={{ background: colorBg, padding: '12px 16px' }}>
          <div style={{
            background: colorField,
            border: `0.5px solid ${adjustColor(colorField, -20)}`,
            borderRadius: radius, padding: 12,
            boxShadow: shadow === 'stark' ? '0 4px 16px rgba(0,0,0,.12)' : '0 2px 6px rgba(0,0,0,.06)',
          }}>
            <div style={{ fontFamily: fontH1, fontSize: 14, fontWeight: 700, color: colorH1, marginBottom: 4 }}>
              Leistungs-Karte
            </div>
            <div style={{ fontFamily: fontBody, fontSize: 12, color: colorBody, lineHeight: 1.5 }}>
              Karteninhalt mit Fliesstext-Font.
            </div>
          </div>
        </div>
      </div>

      {/* Token-Chips */}
      <div style={{ fontSize: 10, fontWeight: 900, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.1em', marginBottom: 8 }}>Klick auf Token zum Bearbeiten</div>
      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 12 }}>
        {tokens.map(t => (
          <button key={t.id} onClick={() => t.setter && setActiveToken(activeToken === t.id ? null : t.id)} style={{
            display: 'flex', alignItems: 'center', gap: 6, padding: '5px 10px',
            border: activeToken === t.id ? '1.5px solid var(--brand-primary)' : '0.5px solid var(--border-light)',
            borderRadius: 6, background: activeToken === t.id ? '#E0F4F8' : 'var(--bg-surface)',
            cursor: t.setter ? 'pointer' : 'default', fontFamily: 'var(--font-sans)', opacity: t.setter ? 1 : 0.5,
          }}>
            <div style={{ width: 14, height: 14, borderRadius: 3, background: t.color, border: '0.5px solid rgba(0,0,0,.1)', flexShrink: 0 }} />
            <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-primary)' }}>{t.label}</span>
            {t.type === 'derived' && <span style={{ fontSize: 9, color: 'var(--text-tertiary)' }}>auto</span>}
          </button>
        ))}
      </div>

      {/* Inline-Editor for tokens */}
      {activeToken && (() => {
        const t = tokens.find(x => x.id === activeToken);
        if (!t?.setter) return null;
        return (
          <div style={{ border: '1.5px solid var(--brand-primary)', borderRadius: 10, padding: 14, marginBottom: 12, background: 'var(--bg-surface)' }}>
            <div style={{ fontSize: 11, fontWeight: 900, color: 'var(--brand-primary)', textTransform: 'uppercase', letterSpacing: '.08em', marginBottom: 10 }}>{t.label} bearbeiten</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
              <div style={{ width: 36, height: 36, borderRadius: 6, background: t.color, border: '0.5px solid rgba(0,0,0,.1)', flexShrink: 0 }} />
              <input value={t.color} onChange={e => t.setter(e.target.value)} placeholder="#000000" style={{ width: 100, padding: '6px 10px', border: '1px solid var(--border-light)', borderRadius: 6, fontSize: 13, fontFamily: 'monospace', color: 'var(--text-primary)', background: 'var(--bg-surface)' }} />
              <input type="color" value={t.color.length === 7 ? t.color : '#000000'} onChange={e => t.setter(e.target.value)} style={{ width: 36, height: 36, cursor: 'pointer', border: 'none', background: 'none' }} />
            </div>
            {brandData?.all_colors?.length > 0 && (
              <div>
                <div style={{ fontSize: 9, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.08em', marginBottom: 5 }}>Von der Website erkannt</div>
                <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap', marginBottom: 8 }}>
                  {(brandData.all_colors || []).slice(0, 10).map((c, i) => (
                    <div key={i} onClick={() => t.setter(c)} title={c} style={{ width: 22, height: 22, borderRadius: 4, background: c, border: c === t.color ? '2px solid var(--brand-primary)' : '0.5px solid rgba(0,0,0,.1)', cursor: 'pointer' }} />
                  ))}
                </div>
              </div>
            )}
            {t.id === 'accent' && (
              <div>
                <div style={{ fontSize: 9, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.08em', marginBottom: 5 }}>Schnell-Palette</div>
                <div style={{ display: 'flex', gap: 4 }}>
                  {QUICK_ACCENTS.map(c => (
                    <div key={c} onClick={() => t.setter(c)} style={{ width: 22, height: 22, borderRadius: 4, background: c, border: c === t.color ? '2px solid var(--brand-primary)' : '0.5px solid rgba(0,0,0,.1)', cursor: 'pointer' }} />
                  ))}
                </div>
              </div>
            )}
          </div>
        );
      })()}

      {/* Schriften — 3 Rollen */}
      <div style={{ marginBottom: 16 }}>
        <div style={{ fontSize: 9, fontWeight: 900, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.1em', marginBottom: 10 }}>
          Schriften & Textfarben
        </div>

        {fontRoles.map(({ role, label, font, setFont, color, setColor, sample, sampleStyle }) => (
          <div key={role} style={{ border: '0.5px solid var(--border-light)', borderRadius: 8, marginBottom: 8, overflow: 'hidden' }}>
            <div style={{
              padding: '7px 12px', background: 'var(--bg-surface)',
              borderBottom: '0.5px solid var(--border-light)',
              fontSize: 10, fontWeight: 700, color: 'var(--text-secondary)',
              textTransform: 'uppercase', letterSpacing: '.06em',
            }}>
              {label}
            </div>
            <div style={{ padding: '10px 12px', display: 'flex', gap: 10, alignItems: 'flex-start' }}>
              <div style={{ flex: 1 }}>
                <FontPicker
                  value={font}
                  onChange={setFont}
                  detectedFonts={detectedFonts}
                />
                <div style={{
                  marginTop: 5, padding: '5px 8px',
                  background: 'var(--surface)', borderRadius: 5,
                  fontFamily: font, color: 'var(--text-primary)',
                  ...sampleStyle,
                }}>
                  {sample}
                </div>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 5, alignItems: 'center', flexShrink: 0 }}>
                <div style={{ fontSize: 9, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Farbe</div>
                <div style={{ position: 'relative' }}>
                  <div
                    style={{
                      width: 36, height: 36, borderRadius: 6,
                      background: color,
                      border: '0.5px solid rgba(0,0,0,.15)',
                      cursor: 'pointer',
                    }}
                    onClick={() => setActiveToken(activeToken === role + '_color' ? null : role + '_color')}
                  />
                  {activeToken === role + '_color' && (
                    <div style={{
                      position: 'absolute', right: 0, top: 42, zIndex: 10,
                      border: '1.5px solid var(--brand-primary)',
                      borderRadius: 8, padding: 10, background: 'var(--bg-surface)',
                      boxShadow: '0 4px 16px rgba(0,0,0,.12)',
                      width: 160,
                    }}>
                      <div style={{ display: 'flex', gap: 6, alignItems: 'center', marginBottom: 6 }}>
                        <div style={{ width: 24, height: 24, borderRadius: 4, background: color, border: '0.5px solid rgba(0,0,0,.1)' }} />
                        <input
                          value={color}
                          onChange={e => setColor(e.target.value)}
                          style={{ flex: 1, padding: '3px 6px', border: '0.5px solid var(--border-light)', borderRadius: 4, fontSize: 11, fontFamily: 'monospace', background: 'var(--bg-surface)', color: 'var(--text-primary)' }}
                        />
                        <input
                          type="color"
                          value={color.length === 7 ? color : '#ffffff'}
                          onChange={e => setColor(e.target.value)}
                          style={{ width: 24, height: 24, cursor: 'pointer', border: 'none', background: 'none' }}
                        />
                      </div>
                      <div style={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
                        {['#FFFFFF', '#000000', '#FAE600', primary, secondary, accent].map(c => (
                          <div key={c} onClick={() => setColor(c)}
                            style={{ width: 18, height: 18, borderRadius: 3, background: c, cursor: 'pointer',
                                     border: c === color ? '2px solid var(--brand-primary)' : '0.5px solid rgba(0,0,0,.15)' }}
                          />
                        ))}
                        {(brandData?.all_colors || []).slice(0, 6).map((c, i) => (
                          <div key={i} onClick={() => setColor(c)}
                            style={{ width: 18, height: 18, borderRadius: 3, background: c, cursor: 'pointer',
                                     border: c === color ? '2px solid var(--brand-primary)' : '0.5px solid rgba(0,0,0,.15)' }}
                          />
                        ))}
                      </div>
                    </div>
                  )}
                </div>
                <div style={{ fontSize: 8, fontFamily: 'monospace', color: 'var(--text-tertiary)' }}>{color}</div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Stil */}
      <div style={{ marginBottom: 16 }}>
        <div style={{ fontSize: 9, fontWeight: 900, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.1em', marginBottom: 6 }}>Stil</div>
        <div style={{ fontSize: 10, color: 'var(--text-tertiary)', marginBottom: 5 }}>Ecken-Radius</div>
        <div style={{ display: 'flex', gap: 6, marginBottom: 12 }}>
          {[{ label: 'Eckig', v: 0 }, { label: 'Rund', v: 6 }, { label: 'Weich', v: 14 }, { label: 'Pill', v: 99 }].map(r => (
            <button key={r.v} onClick={() => setRadius(r.v)} style={{
              flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4, padding: '8px 0',
              border: radius === r.v ? '1.5px solid var(--brand-primary)' : '0.5px solid var(--border-light)',
              borderRadius: 6, background: radius === r.v ? '#E0F4F8' : 'var(--bg-surface)', cursor: 'pointer', fontFamily: 'var(--font-sans)',
            }}>
              <div style={{ width: 24, height: 24, border: `2px solid ${radius === r.v ? 'var(--brand-primary)' : 'var(--border-medium)'}`, borderRadius: r.v === 99 ? 12 : r.v, background: radius === r.v ? '#E0F4F8' : 'transparent' }} />
              <span style={{ fontSize: 9, fontWeight: 700, color: radius === r.v ? 'var(--brand-primary)' : 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.04em' }}>{r.label}</span>
            </button>
          ))}
        </div>
        <div style={{ fontSize: 10, color: 'var(--text-tertiary)', marginBottom: 5 }}>Schatten</div>
        <div style={{ display: 'flex', gap: 5 }}>
          {['ohne', 'leicht', 'mittel', 'stark'].map(s => (
            <button key={s} onClick={() => setShadow(s)} style={{
              flex: 1, padding: '5px 0', fontSize: 9, fontWeight: shadow === s ? 900 : 400,
              border: shadow === s ? '1.5px solid var(--brand-primary)' : '0.5px solid var(--border-light)',
              borderRadius: 5, background: shadow === s ? '#E0F4F8' : 'transparent',
              color: shadow === s ? 'var(--brand-primary)' : 'var(--text-tertiary)',
              cursor: 'pointer', fontFamily: 'var(--font-sans)', textTransform: 'uppercase', letterSpacing: '.04em',
            }}>{s}</button>
          ))}
        </div>
      </div>

      {/* Speichern */}
      <button onClick={save} disabled={saving} style={{
        width: '100%', padding: 11, background: saving ? 'var(--border-light)' : '#FAE600',
        color: '#000', border: 'none', borderRadius: 8, fontSize: 12, fontWeight: 900,
        cursor: saving ? 'not-allowed' : 'pointer', fontFamily: 'var(--font-sans)',
        textTransform: 'uppercase', letterSpacing: '.05em',
      }}>{saving ? 'Wird gespeichert…' : 'Brand Design speichern'}</button>
    </div>
  );
}

function FontPicker({ value, onChange, detectedFonts = [] }) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState('');
  const ref = useRef(null);

  useEffect(() => {
    if (!open) return;
    const close = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
    document.addEventListener('mousedown', close);
    return () => document.removeEventListener('mousedown', close);
  }, [open]);

  const handleSelect = (font) => {
    loadGoogleFont(font);
    onChange(font);
    setOpen(false);
    setSearch('');
  };

  const searchLower = search.toLowerCase();
  const filteredCatalog = search
    ? { 'Suchergebnisse': ALL_FONTS_FLAT.filter(f => f.toLowerCase().includes(searchLower)) }
    : GOOGLE_FONTS_CATALOG;

  return (
    <div ref={ref} style={{ position: 'relative', width: '100%' }}>
      <button
        onClick={() => setOpen(o => !o)}
        style={{
          width: '100%', padding: '7px 10px',
          border: '0.5px solid var(--border-light)',
          borderRadius: 6, fontSize: 12,
          background: 'var(--bg-surface)', color: 'var(--text-primary)',
          fontFamily: value, cursor: 'pointer',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          gap: 6, textAlign: 'left',
        }}
      >
        <span style={{ fontFamily: value }}>{value}</span>
        <span style={{ color: 'var(--text-tertiary)', fontSize: 10 }}>&#9662;</span>
      </button>

      {open && (
        <div style={{
          position: 'absolute', top: 'calc(100% + 4px)',
          left: 0, right: 0,
          background: 'var(--bg-surface)',
          border: '1.5px solid var(--brand-primary)',
          borderRadius: 8, boxShadow: '0 8px 24px rgba(0,0,0,.15)',
          zIndex: 200, maxHeight: 340,
          display: 'flex', flexDirection: 'column', overflow: 'hidden',
        }}>
          <div style={{ padding: '8px 10px', borderBottom: '0.5px solid var(--border-light)', flexShrink: 0 }}>
            <input
              autoFocus
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Font suchen…"
              style={{
                width: '100%', padding: '5px 8px',
                border: '0.5px solid var(--border-light)',
                borderRadius: 5, fontSize: 12,
                background: 'var(--bg-surface)', color: 'var(--text-primary)',
                fontFamily: 'var(--font-sans)', boxSizing: 'border-box',
              }}
            />
          </div>

          {!search && detectedFonts.length > 0 && (
            <div style={{ flexShrink: 0 }}>
              <div style={{
                padding: '5px 10px', fontSize: 9, fontWeight: 900,
                color: '#00875A', textTransform: 'uppercase', letterSpacing: '.08em',
                background: '#F0FDF4', borderBottom: '0.5px solid var(--border-light)',
              }}>
                Von Website erkannt
              </div>
              {detectedFonts.map(font => (
                <FontOption key={font} font={font} selected={value === font} onSelect={handleSelect} detected />
              ))}
              <div style={{ height: '0.5px', background: 'var(--border-light)' }} />
            </div>
          )}

          <div style={{ overflowY: 'auto', flex: 1 }}>
            {Object.entries(filteredCatalog).map(([category, fonts]) => (
              <div key={category}>
                {!search && (
                  <div style={{
                    padding: '5px 10px', fontSize: 9, fontWeight: 900,
                    color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.08em',
                    background: 'var(--surface)', position: 'sticky', top: 0,
                  }}>
                    {category}
                  </div>
                )}
                {fonts
                  .filter(f => !detectedFonts.includes(f) || search)
                  .map(font => (
                    <FontOption key={font} font={font} selected={value === font} onSelect={handleSelect} detected={false} />
                  ))
                }
              </div>
            ))}
            {search && Object.values(filteredCatalog)[0]?.length === 0 && (
              <div style={{ padding: 20, textAlign: 'center', fontSize: 12, color: 'var(--text-tertiary)' }}>
                Kein Font gefunden
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function FontOption({ font, selected, onSelect, detected }) {
  const [hovered, setHovered] = useState(false);

  useEffect(() => {
    if (hovered) loadGoogleFont(font);
  }, [hovered, font]);

  return (
    <div
      onClick={() => onSelect(font)}
      onMouseEnter={() => setHovered(true)}
      style={{
        padding: '7px 10px',
        background: selected ? 'var(--info-bg, #E0F4F8)' : 'transparent',
        cursor: 'pointer',
        display: 'flex', alignItems: 'baseline', gap: 8,
        borderLeft: selected ? '3px solid var(--brand-primary)' : '3px solid transparent',
      }}
    >
      <span style={{
        fontFamily: hovered || selected ? font : 'var(--font-sans)',
        fontSize: 14, color: 'var(--text-primary)',
        flex: 1, lineHeight: 1.4,
      }}>
        {font}
      </span>
      <span style={{
        fontFamily: hovered || selected ? font : 'var(--font-sans)',
        fontSize: 11, color: 'var(--text-tertiary)', flexShrink: 0,
      }}>
        Aa Bb 123
      </span>
      {detected && (
        <span style={{
          fontSize: 8, fontWeight: 900, padding: '1px 5px',
          borderRadius: 3, background: '#E3F6EF', color: '#00875A', flexShrink: 0,
        }}>
          erkannt
        </span>
      )}
    </div>
  );
}

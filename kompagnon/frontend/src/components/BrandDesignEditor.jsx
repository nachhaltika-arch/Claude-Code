import { useState, useEffect, useRef } from 'react';
import API_BASE_URL from '../config';

// ── Breiter Google Fonts Katalog ─────────────────────────────────────────────
const GOOGLE_FONTS_CATALOG = {
  'Serif — Klassisch': [
    'Georgia', 'Times New Roman', 'Playfair Display', 'Merriweather',
    'Lora', 'Libre Baskerville', 'PT Serif', 'Crimson Text',
    'EB Garamond', 'Cormorant Garamond',
  ],
  'Sans-Serif — Modern': [
    'Inter', 'Roboto', 'Open Sans', 'Noto Sans', 'Source Sans 3',
    'Nunito', 'Mulish', 'DM Sans', 'Plus Jakarta Sans', 'Outfit',
    'Figtree', 'Geist', 'Albert Sans',
  ],
  'Sans-Serif — Neutral': [
    'Arial', 'Helvetica', 'Lato', 'Raleway', 'Montserrat',
    'Poppins', 'Urbanist', 'Rubik', 'Work Sans', 'Manrope',
  ],
  'Condensed / Display': [
    'Barlow Condensed', 'Oswald', 'Anton', 'Bebas Neue',
    'Fjalla One', 'Squada One', 'Big Shoulders Display',
    'League Gothic', 'Passion One',
  ],
  'Handwerk / Regional': [
    'Teko', 'Exo 2', 'Titillium Web', 'Asap', 'Cabin',
    'Josefin Sans', 'Prompt', 'Saira', 'IBM Plex Sans',
  ],
  'Slab Serif': [
    'Roboto Slab', 'Arvo', 'Zilla Slab', 'Crete Round',
    'Alfa Slab One', 'Tinos',
  ],
};

const ALL_FONTS_FLAT = Object.values(GOOGLE_FONTS_CATALOG).flat();

// ── Dynamic font loading ──────────────────────────────────────────────────────
const loadedFonts = new Set();

function loadGoogleFont(fontName) {
  if (!fontName) return;
  const systemFonts = ['Arial', 'Helvetica', 'Georgia', 'Times New Roman',
                       'Courier New', 'Verdana', 'Trebuchet MS'];
  if (systemFonts.includes(fontName)) return;
  if (loadedFonts.has(fontName)) return;
  const encoded = fontName.replace(/ /g, '+');
  const href = `https://fonts.googleapis.com/css2?family=${encoded}:wght@400;600;700;900&display=swap`;
  if (document.querySelector(`link[href*="${encoded}"]`)) {
    loadedFonts.add(fontName);
    return;
  }
  const link = document.createElement('link');
  link.rel  = 'stylesheet';
  link.href = href;
  document.head.appendChild(link);
  loadedFonts.add(fontName);
}

// ── FontOption ────────────────────────────────────────────────────────────────
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
        transition: 'font-family .1s',
      }}>
        {font}
      </span>
      <span style={{
        fontFamily: hovered || selected ? font : 'var(--font-sans)',
        fontSize: 11, color: 'var(--text-tertiary)',
        flexShrink: 0,
      }}>
        Aa Bb 123
      </span>
      {detected && (
        <span style={{
          fontSize: 8, fontWeight: 900, padding: '1px 5px',
          borderRadius: 3, background: '#E3F6EF', color: '#00875A',
          flexShrink: 0,
        }}>
          erkannt
        </span>
      )}
    </div>
  );
}

// ── FontPicker ────────────────────────────────────────────────────────────────
function FontPicker({ value, onChange, detectedFonts = [] }) {
  const [open,   setOpen]   = useState(false);
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
          background: 'var(--bg-surface)',
          color: 'var(--text-primary)',
          cursor: 'pointer',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          gap: 6, textAlign: 'left',
        }}
      >
        <span style={{ fontFamily: value }}>{value}</span>
        <span style={{ color: 'var(--text-tertiary)', fontSize: 10 }}>▾</span>
      </button>

      {open && (
        <div style={{
          position: 'absolute', top: 'calc(100% + 4px)',
          left: 0, right: 0,
          background: 'var(--bg-surface)',
          border: '1.5px solid var(--brand-primary)',
          borderRadius: 8,
          boxShadow: '0 8px 24px rgba(0,0,0,.15)',
          zIndex: 200,
          maxHeight: 340,
          display: 'flex', flexDirection: 'column',
          overflow: 'hidden',
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
                background: 'var(--bg-surface)',
                color: 'var(--text-primary)',
                fontFamily: 'var(--font-sans)',
                outline: 'none',
              }}
            />
          </div>

          {!search && detectedFonts.length > 0 && (
            <div style={{ flexShrink: 0 }}>
              <div style={{
                padding: '5px 10px',
                fontSize: 9, fontWeight: 900, color: '#00875A',
                textTransform: 'uppercase', letterSpacing: '.08em',
                background: '#F0FDF4',
                borderBottom: '0.5px solid var(--border-light)',
              }}>
                ✓ Von Website erkannt
              </div>
              {detectedFonts.map(font => (
                <FontOption
                  key={font} font={font} selected={value === font}
                  onSelect={handleSelect} detected={true}
                />
              ))}
              <div style={{ height: '0.5px', background: 'var(--border-light)' }} />
            </div>
          )}

          <div style={{ overflowY: 'auto', flex: 1 }}>
            {Object.entries(filteredCatalog).map(([category, fonts]) => (
              <div key={category}>
                {!search && (
                  <div style={{
                    padding: '5px 10px',
                    fontSize: 9, fontWeight: 900, color: 'var(--text-tertiary)',
                    textTransform: 'uppercase', letterSpacing: '.08em',
                    background: 'var(--bg-app)',
                    position: 'sticky', top: 0,
                  }}>
                    {category}
                  </div>
                )}
                {fonts
                  .filter(f => !detectedFonts.includes(f) || search)
                  .map(font => (
                    <FontOption
                      key={font} font={font} selected={value === font}
                      onSelect={handleSelect} detected={false}
                    />
                  ))
                }
              </div>
            ))}
            {search && Object.values(filteredCatalog)[0]?.length === 0 && (
              <div style={{ padding: '20px', textAlign: 'center', fontSize: 12, color: 'var(--text-tertiary)' }}>
                Kein Font gefunden
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// ── BrandDesignEditor ─────────────────────────────────────────────────────────
export default function BrandDesignEditor({ brandData, leadId, token, headers, onSaved }) {
  const [primary,    setPrimary]    = useState('#004F59');
  const [secondary,  setSecondary]  = useState('#2C3E50');
  const [accent,     setAccent]     = useState('#FAE600');
  const [fontH1,     setFontH1]     = useState('Georgia');
  const [fontBody,   setFontBody]   = useState('Arial');
  const [fontAkzent, setFontAkzent] = useState('Barlow Condensed');
  const [colorH1,    setColorH1]    = useState('#004F59');
  const [colorBody,  setColorBody]  = useState('#333333');
  const [colorAkzent, setColorAkzent] = useState('#000000');
  const [saving, setSaving] = useState(false);
  const [savedOk, setSavedOk] = useState(false);

  useEffect(() => {
    if (!brandData) {
      setPrimary('#004F59'); setSecondary('#2C3E50'); setAccent('#FAE600');
      setFontH1('Georgia'); setFontBody('Arial'); setFontAkzent('Barlow Condensed');
      return;
    }

    const detected = [
      brandData.font_heading, brandData.font_body, brandData.font_accent,
      brandData.font_primary, brandData.font_secondary,
      ...(brandData.all_fonts || []),
      ...(brandData.fonts_detail?.google_fonts || []),
    ].filter(Boolean);
    detected.forEach(loadGoogleFont);

    if (brandData.primary_color)   setPrimary(brandData.primary_color);
    if (brandData.secondary_color) setSecondary(brandData.secondary_color);

    const h1f = brandData.font_heading || brandData.font_primary;
    if (h1f) { setFontH1(h1f); loadGoogleFont(h1f); }

    const bf = brandData.font_body || brandData.font_secondary;
    if (bf) { setFontBody(bf); loadGoogleFont(bf); }

    if (brandData.font_accent) { setFontAkzent(brandData.font_accent); loadGoogleFont(brandData.font_accent); }
  }, [brandData]); // eslint-disable-line

  const detectedFonts = [
    ...(brandData?.fonts_detail?.google_fonts || []),
    brandData?.font_heading, brandData?.font_body, brandData?.font_accent,
    brandData?.font_primary, brandData?.font_secondary,
    ...(brandData?.all_fonts || []),
  ].filter(Boolean).filter((v, i, a) => a.indexOf(v) === i);

  const save = async () => {
    if (!leadId) return;
    setSaving(true);
    try {
      const h = { 'Content-Type': 'application/json', ...(headers || {}) };
      const res = await fetch(`${API_BASE_URL}/api/branddesign/${leadId}`, {
        method: 'PUT', headers: h,
        body: JSON.stringify({
          primary_color:   primary,
          secondary_color: secondary,
          font_primary:    fontH1,
          font_secondary:  fontBody,
        }),
      });
      if (!res.ok) throw new Error('Fehler');
      setSavedOk(true);
      setTimeout(() => setSavedOk(false), 2500);
      if (onSaved) onSaved({ primary_color: primary, secondary_color: secondary, font_primary: fontH1, font_secondary: fontBody });
    } catch { /* silent */ } finally { setSaving(false); }
  };

  const FONT_ROLES = [
    {
      role: 'h1', label: 'Überschriften (H1 · H2 · H3)',
      font: fontH1, setFont: (f) => { setFontH1(f); loadGoogleFont(f); },
      color: colorH1, setColor: setColorH1,
      sample: 'Überschrift — Ihr Handwerksbetrieb',
      sampleStyle: { fontSize: 16, fontWeight: 700 },
    },
    {
      role: 'body', label: 'Fließtext',
      font: fontBody, setFont: (f) => { setFontBody(f); loadGoogleFont(f); },
      color: colorBody, setColor: setColorBody,
      sample: 'Fließtext — professionell und gut lesbar.',
      sampleStyle: { fontSize: 12, fontWeight: 400 },
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
    <div style={{ padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: 24 }}>

      {/* ── Farben ──────────────────────────────────────────────────────────── */}
      <div>
        <div style={{ fontSize: 10, fontWeight: 900, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.08em', marginBottom: 12 }}>
          Brand-Farben
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12 }}>
          {[
            { label: 'Primärfarbe',   value: primary,   onChange: setPrimary,   desc: 'Hauptfarbe · Nav · Buttons' },
            { label: 'Sekundärfarbe', value: secondary, onChange: setSecondary, desc: 'Akzente · Highlights' },
            { label: 'Akzentfarbe',   value: accent,    onChange: setAccent,    desc: 'CTA · Hover · Highlights' },
          ].map(({ label, value, onChange, desc }) => (
            <div key={label} style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.06em' }}>
                {label}
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <input
                  type="color" value={value}
                  onChange={e => onChange(e.target.value)}
                  style={{ width: 36, height: 36, padding: 2, border: '0.5px solid var(--border-light)', borderRadius: 6, cursor: 'pointer', background: 'none', flexShrink: 0 }}
                />
                <input
                  type="text" value={value}
                  onChange={e => { if (/^#[0-9A-Fa-f]{0,6}$/.test(e.target.value)) onChange(e.target.value); }}
                  style={{ flex: 1, padding: '5px 8px', border: '0.5px solid var(--border-light)', borderRadius: 6, fontSize: 11, fontFamily: 'monospace', background: 'var(--bg-surface)', color: 'var(--text-primary)', outline: 'none' }}
                />
              </div>
              <div style={{ fontSize: 9, color: 'var(--text-tertiary)' }}>{desc}</div>
            </div>
          ))}
        </div>
      </div>

      {/* ── Schriften ───────────────────────────────────────────────────────── */}
      <div>
        <div style={{ fontSize: 10, fontWeight: 900, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.08em', marginBottom: 12 }}>
          Schriften
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {FONT_ROLES.map(({ role, label, font, setFont, color, setColor, sample, sampleStyle }) => (
            <div key={role} style={{ background: 'var(--bg-surface)', border: '0.5px solid var(--border-light)', borderRadius: 8, padding: 12 }}>
              <div style={{ fontSize: 10, fontWeight: 900, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.06em', marginBottom: 8 }}>
                {label}
              </div>
              <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 8 }}>
                <div style={{ flex: 1 }}>
                  <FontPicker value={font} onChange={setFont} detectedFonts={detectedFonts} />
                </div>
                <input
                  type="color" value={color}
                  onChange={e => setColor(e.target.value)}
                  title="Textfarbe"
                  style={{ width: 28, height: 28, padding: 2, border: '0.5px solid var(--border-light)', borderRadius: 4, cursor: 'pointer', background: 'none', flexShrink: 0 }}
                />
              </div>
              <div style={{
                padding: '6px 8px', background: 'var(--bg-app)', borderRadius: 5,
                fontFamily: font, color: color, ...sampleStyle,
              }}>
                {sample}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ── Live-Vorschau ────────────────────────────────────────────────────── */}
      <div>
        <div style={{ fontSize: 10, fontWeight: 900, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.08em', marginBottom: 12 }}>
          Live-Vorschau
        </div>
        <div style={{ border: '0.5px solid var(--border-light)', borderRadius: 10, overflow: 'hidden' }}>
          <div style={{ background: primary, padding: '10px 16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontFamily: fontH1, fontSize: 15, fontWeight: 700, color: '#fff' }}>Firmenname</span>
            <button style={{ fontFamily: fontAkzent, background: accent, color: colorAkzent, border: 'none', borderRadius: 5, padding: '5px 12px', fontSize: 10, fontWeight: 700, cursor: 'default', letterSpacing: '.04em' }}>
              Kontakt
            </button>
          </div>
          <div style={{ padding: '16px 16px 12px' }}>
            <div style={{ fontFamily: fontH1, fontSize: 20, fontWeight: 700, color: colorH1, marginBottom: 4 }}>Überschrift H1</div>
            <div style={{ fontFamily: fontH1, fontSize: 14, fontWeight: 600, color: colorH1, opacity: 0.8, marginBottom: 10 }}>Überschrift H2</div>
            <div style={{ fontFamily: fontBody, fontSize: 12, color: colorBody, lineHeight: 1.6, marginBottom: 12 }}>
              Fließtext mit dem gewählten Body-Font. Professionell, gut lesbar, überzeugend.
            </div>
            <div style={{ display: 'flex', gap: 10, marginBottom: 12 }}>
              <button style={{ fontFamily: fontAkzent, background: primary, color: '#fff', border: 'none', borderRadius: 6, padding: '8px 16px', fontSize: 12, fontWeight: 700, cursor: 'default', textTransform: 'uppercase', letterSpacing: '.04em' }}>
                Jetzt anfragen
              </button>
              <button style={{ fontFamily: fontAkzent, background: accent, color: colorAkzent, border: 'none', borderRadius: 6, padding: '8px 16px', fontSize: 12, fontWeight: 700, cursor: 'default' }}>
                Mehr erfahren
              </button>
            </div>
            <div style={{ border: `1px solid ${primary}30`, borderRadius: 8, padding: '10px 12px', background: `${primary}08` }}>
              <div style={{ fontFamily: fontH1, fontWeight: 700, color: colorH1, fontSize: 12, marginBottom: 4 }}>Leistungs-Karte</div>
              <div style={{ fontFamily: fontBody, fontSize: 11, color: colorBody, lineHeight: 1.5 }}>Karteninhalt mit Fließtext-Font. Klar und lesbar.</div>
            </div>
          </div>
        </div>
      </div>

      {/* ── Speichern ─────────────────────────────────────────────────────────── */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <button
          onClick={save}
          disabled={saving}
          style={{
            padding: '10px 24px', borderRadius: 8, border: 'none',
            background: savedOk ? '#1D9E75' : saving ? 'var(--border-medium)' : 'var(--kc-dark, #004F59)',
            color: '#fff', fontSize: 13, fontWeight: 700,
            cursor: saving ? 'not-allowed' : 'pointer',
            fontFamily: 'var(--font-sans)', textTransform: 'uppercase',
            transition: 'background .2s',
          }}
        >
          {savedOk ? '✓ Gespeichert' : saving ? 'Speichert…' : 'Brand Design speichern'}
        </button>
        {detectedFonts.length > 0 && (
          <span style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>
            {detectedFonts.length} erkannte Font(s) im Dropdown hervorgehoben
          </span>
        )}
      </div>
    </div>
  );
}

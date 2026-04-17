import { useState, useEffect, useRef } from 'react';
import toast from 'react-hot-toast';
import API_BASE_URL from '../config';

const FONT_CATALOG = {
  'Erkannt': [],
  'Serif': ['Georgia','Playfair Display','Merriweather','Lora',
             'Libre Baskerville','EB Garamond','Cormorant Garamond','PT Serif'],
  'Sans-Serif Modern': ['Inter','DM Sans','Plus Jakarta Sans','Outfit',
                         'Figtree','Albert Sans','Manrope'],
  'Sans-Serif Neutral': ['Roboto','Open Sans','Noto Sans','Lato','Raleway',
                          'Montserrat','Poppins','Nunito','Rubik','Work Sans'],
  'Condensed / Display': ['Barlow Condensed','Oswald','Bebas Neue','Anton',
                            'Fjalla One','Big Shoulders Display','League Gothic'],
  'Handwerk': ['Teko','Exo 2','Titillium Web','Cabin','Asap',
                'Saira','IBM Plex Sans','Josefin Sans'],
  'Slab Serif': ['Roboto Slab','Arvo','Zilla Slab','Alfa Slab One','Crete Round'],
};

const ALL_FONTS_FLAT = Object.values(FONT_CATALOG).flat();

const _loadedFonts = new Set();
function loadFont(name) {
  if (!name) return;
  const sys = ['Arial','Helvetica','Georgia','Times New Roman','Verdana','Courier New'];
  if (sys.includes(name) || _loadedFonts.has(name)) return;
  if (document.querySelector(`link[href*="${name.replace(/ /g,'+')}"]`)) {
    _loadedFonts.add(name); return;
  }
  const l = document.createElement('link');
  l.rel = 'stylesheet';
  l.href = `https://fonts.googleapis.com/css2?family=${name.replace(/ /g,'+')}:wght@400;600;700;900&display=swap`;
  document.head.appendChild(l);
  _loadedFonts.add(name);
}

function adjustHex(hex, amt) {
  const n = parseInt((hex || '#000000').replace('#',''), 16);
  const r = Math.min(255, Math.max(0, (n >> 16) + amt));
  const g = Math.min(255, Math.max(0, ((n >> 8) & 0xff) + amt));
  const b = Math.min(255, Math.max(0, (n & 0xff) + amt));
  return '#' + [r,g,b].map(x => x.toString(16).padStart(2,'0')).join('');
}

function FontPicker({ value, onChange, detectedFonts = [] }) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState('');
  const ref = useRef(null);

  useEffect(() => {
    if (!open) return;
    const close = e => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
    document.addEventListener('mousedown', close);
    return () => document.removeEventListener('mousedown', close);
  }, [open]);

  const select = f => { loadFont(f); onChange(f); setOpen(false); setSearch(''); };

  const catalog = search
    ? { 'Suchergebnisse': ALL_FONTS_FLAT.filter(f =>
        f.toLowerCase().includes(search.toLowerCase())) }
    : { ...(detectedFonts.length ? { 'Von Website erkannt': detectedFonts } : {}),
        ...Object.fromEntries(
          Object.entries(FONT_CATALOG).filter(([k]) => k !== 'Erkannt')
        ) };

  return (
    <div ref={ref} style={{ position: 'relative' }}>
      <button onClick={() => setOpen(o => !o)} style={{
        width: '100%', padding: '7px 10px', textAlign: 'left',
        border: '0.5px solid var(--border-light)', borderRadius: 6,
        background: 'var(--bg-surface)', cursor: 'pointer',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        fontFamily: value, fontSize: 13, color: 'var(--text-primary)',
      }}>
        <span style={{ fontFamily: value }}>{value}</span>
        <span style={{ color: 'var(--text-tertiary)', fontSize: 10, fontFamily: 'var(--font-sans)' }}>&#9662;</span>
      </button>

      {open && (
        <div style={{
          position: 'absolute', top: 'calc(100% + 4px)', left: 0, right: 0,
          background: 'var(--bg-surface)',
          border: '1.5px solid var(--brand-primary, #004F59)',
          borderRadius: 8, zIndex: 300,
          boxShadow: '0 8px 24px rgba(0,0,0,.18)',
          maxHeight: 320, display: 'flex', flexDirection: 'column', overflow: 'hidden',
        }}>
          <div style={{ padding: '6px 8px', borderBottom: '0.5px solid var(--border-light)', flexShrink: 0 }}>
            <input autoFocus value={search} onChange={e => setSearch(e.target.value)}
              placeholder="Font suchen…" style={{
                width: '100%', padding: '5px 8px', fontSize: 12,
                border: '0.5px solid var(--border-light)', borderRadius: 5,
                background: 'var(--bg-surface)', color: 'var(--text-primary)',
                fontFamily: 'var(--font-sans)', boxSizing: 'border-box',
              }} />
          </div>
          <div style={{ overflowY: 'auto', flex: 1 }}>
            {Object.entries(catalog).map(([cat, fonts]) => (
              <div key={cat}>
                <div style={{
                  padding: '4px 10px', fontSize: 9, fontWeight: 900,
                  textTransform: 'uppercase', letterSpacing: '.08em',
                  color: cat.includes('erkannt') ? '#00875A' : 'var(--text-tertiary)',
                  background: cat.includes('erkannt') ? '#F0FDF4' : 'var(--surface)',
                  position: 'sticky', top: 0,
                }}>
                  {cat}
                </div>
                {fonts
                  .filter(f => !cat.includes('erkannt') && detectedFonts.includes(f) ? false : true)
                  .map(font => (
                    <FontRow key={font} font={font} selected={value===font}
                      onSelect={select}
                      detected={detectedFonts.includes(font) && !cat.includes('erkannt')} />
                  ))
                }
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function FontRow({ font, selected, onSelect, detected }) {
  const [hov, setHov] = useState(false);
  useEffect(() => { if (hov) loadFont(font); }, [hov, font]);
  return (
    <div onClick={() => onSelect(font)}
      onMouseEnter={() => setHov(true)}
      style={{
        padding: '6px 10px', cursor: 'pointer',
        background: selected ? '#E0F4F8' : 'transparent',
        borderLeft: selected ? '3px solid var(--brand-primary,#004F59)' : '3px solid transparent',
        display: 'flex', alignItems: 'baseline', gap: 8,
      }}>
      <span style={{ fontFamily: hov||selected ? font : 'inherit', fontSize: 14, flex: 1, color: 'var(--text-primary)' }}>{font}</span>
      <span style={{ fontFamily: hov||selected ? font : 'inherit', fontSize: 11, color: 'var(--text-tertiary)', flexShrink: 0 }}>Aa Bb 123</span>
      {detected && <span style={{ fontSize: 8, fontWeight: 900, padding: '1px 5px', borderRadius: 3, background: '#E3F6EF', color: '#00875A', flexShrink: 0 }}>erkannt</span>}
    </div>
  );
}

function ColorToken({ id, label, value, onChange, autoValue, allColors = [], activeId, setActiveId }) {
  const isActive = activeId === id;
  const isDerived = !onChange;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4, position: 'relative' }}>
      <div
        onClick={e => { e.stopPropagation(); if (!isDerived) setActiveId(isActive ? null : id); }}
        title={isDerived ? 'Automatisch berechnet' : 'Klicken zum Bearbeiten'}
        style={{
          width: '100%', height: 46, borderRadius: 8,
          background: value || autoValue || '#ccc',
          border: isActive ? '2px solid var(--brand-primary, #004F59)' : '0.5px solid rgba(0,0,0,.1)',
          cursor: isDerived ? 'default' : 'pointer',
          position: 'relative', transition: 'transform .1s',
          transform: isActive ? 'scale(1.04)' : 'scale(1)',
        }}
      >
        {isDerived && (
          <div style={{ position: 'absolute', bottom: 2, right: 4, fontSize: 7, color: 'rgba(255,255,255,.6)', fontWeight: 700 }}>AUTO</div>
        )}
      </div>
      <div style={{ fontSize: 8, fontWeight: 900, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '.04em', textAlign: 'center', lineHeight: 1.2 }}>{label}</div>
      <div style={{ fontSize: 7, color: 'var(--text-tertiary)', fontFamily: 'monospace' }}>{value || autoValue || ''}</div>

      {isActive && onChange && (
        <div style={{
          position: 'absolute', zIndex: 200, top: 58,
          background: 'var(--bg-surface)',
          border: '1.5px solid var(--brand-primary, #004F59)',
          borderRadius: 10, padding: 12,
          boxShadow: '0 8px 24px rgba(0,0,0,.2)',
          width: 180,
        }} onClick={e => e.stopPropagation()}>
          <div style={{ display: 'flex', gap: 6, alignItems: 'center', marginBottom: 8 }}>
            <div style={{ width: 28, height: 28, borderRadius: 5, background: value, border: '0.5px solid rgba(0,0,0,.1)', flexShrink: 0 }} />
            <input value={value} onChange={e => onChange(e.target.value)}
              style={{ flex: 1, padding: '4px 7px', fontSize: 12, fontFamily: 'monospace',
                       border: '0.5px solid var(--border-light)', borderRadius: 5,
                       background: 'var(--bg-surface)', color: 'var(--text-primary)' }} />
            <input type="color" value={value?.length===7 ? value : '#000000'}
              onChange={e => onChange(e.target.value)}
              style={{ width: 28, height: 28, cursor: 'pointer', border: 'none', background: 'none', flexShrink: 0 }} />
          </div>
          <div style={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
            {['#FFFFFF','#000000','#FAE600',...allColors.slice(0,9)].map((c,i) => (
              <div key={i} onClick={() => onChange(c)}
                style={{ width: 18, height: 18, borderRadius: 3, background: c, cursor: 'pointer',
                         border: c===value ? '2px solid var(--brand-primary,#004F59)' : '0.5px solid rgba(0,0,0,.1)' }} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function Section({ label, hint, children }) {
  return (
    <div style={{ background: '#fff', border: '0.5px solid var(--border-light)', borderRadius: 10, overflow: 'visible' }}>
      <div style={{
        padding: '7px 14px', background: 'var(--surface)',
        borderBottom: '0.5px solid var(--border-light)',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      }}>
        <span style={{ fontSize: 9, fontWeight: 900, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.1em' }}>{label}</span>
        {hint && <span style={{ fontSize: 9, color: 'var(--text-tertiary)' }}>{hint}</span>}
      </div>
      <div style={{ padding: '12px 14px' }}>{children}</div>
    </div>
  );
}

export default function BrandDesignEditor({ leadId, token, brandData, onSaved }) {
  const [primary, setPrimary]         = useState('#004F59');
  const [secondary, setSecondary]     = useState('#2C3E50');
  const [accent, setAccent]           = useState('#FAE600');
  const [colorBg, setColorBg]         = useState('#F5F5F0');
  const [colorField, setColorField]   = useState('#FFFFFF');
  const [colorHeading, setColorHeading] = useState('#FFFFFF');
  const [colorText, setColorText]     = useState('#333333');
  const [fontH1, setFontH1]           = useState('Georgia');
  const [fontBody, setFontBody]       = useState('Arial');
  const [fontAkzent, setFontAkzent]   = useState('Barlow Condensed');
  const [colorFontH1, setColorFontH1]   = useState('#FFFFFF');
  const [colorFontBody, setColorFontBody] = useState('rgba(255,255,255,0.75)');
  const [colorFontCta, setColorFontCta] = useState('#000000');
  const [radius, setRadius]           = useState(6);
  const [shadow, setShadow]           = useState('leicht');
  const [activeColorId, setActiveColorId] = useState(null);
  const [saving, setSaving]           = useState(false);
  const [scraping, setScraping]       = useState(false);

  const headers = { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` };

  useEffect(() => {
    if (!brandData) {
      setPrimary('#004F59');
      setSecondary('#2C3E50');
      setAccent('#FAE600');
      setColorBg('#F5F5F0');
      setColorField('#FFFFFF');
      setColorHeading('#FFFFFF');
      setColorText('#333333');
      setFontH1('Georgia');
      setFontBody('Arial');
      setFontAkzent('Barlow Condensed');
      setColorFontH1('#FFFFFF');
      setColorFontBody('rgba(255,255,255,0.75)');
      setColorFontCta('#000000');
      setRadius(6);
      setShadow('leicht');
      return;
    }
    if (brandData.primary_color)   setPrimary(brandData.primary_color);
    if (brandData.secondary_color) setSecondary(brandData.secondary_color);

    const dd = brandData.design_data;
    if (dd?.design_brief?.akzentfarbe) setAccent(dd.design_brief.akzentfarbe);
    if (dd?.design_brief?.hintergrundfarbe) setColorBg(dd.design_brief.hintergrundfarbe);
    if (dd?.border_radius_px) setRadius(dd.border_radius_px);
    if (dd?.shadow_label)     setShadow(dd.shadow_label);

    const fh = brandData.font_heading || brandData.font_primary;
    const fb = brandData.font_body    || brandData.font_secondary;
    const fa = brandData.font_accent;
    if (fh) { setFontH1(fh);     loadFont(fh); }
    if (fb) { setFontBody(fb);   loadFont(fb); }
    if (fa) { setFontAkzent(fa); loadFont(fa); }

    (brandData.all_fonts || []).forEach(loadFont);
    (brandData.fonts_detail?.google_fonts || []).forEach(loadFont);
  }, [brandData]);

  const detectedFonts = [
    brandData?.font_heading, brandData?.font_body, brandData?.font_accent,
    brandData?.font_primary, brandData?.font_secondary,
    ...(brandData?.fonts_detail?.google_fonts || []),
    ...(brandData?.all_fonts || []),
  ].filter(Boolean).filter((v,i,a) => a.indexOf(v)===i);

  const rescrape = async () => {
    setScraping(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/branddesign/${leadId}/scrape`, { method: 'POST', headers });
      if (res.ok) {
        const d = await res.json();
        if (d.primary_color)   setPrimary(d.primary_color);
        if (d.secondary_color) setSecondary(d.secondary_color);
        toast.success('Website neu gescrapt');
      }
    } catch { toast.error('Scraping fehlgeschlagen'); }
    finally { setScraping(false); }
  };

  const save = async () => {
    setSaving(true);
    try {
      await fetch(`${API_BASE_URL}/api/branddesign/${leadId}`, {
        method: 'PUT', headers,
        body: JSON.stringify({
          primary_color: primary, secondary_color: secondary,
          font_primary: fontH1, font_secondary: fontBody,
          font_heading: fontH1, font_body: fontBody, font_accent: fontAkzent,
        }),
      });
      toast.success('Brand Design gespeichert');
      if (onSaved) onSaved({ primary, secondary, accent, fontH1, fontBody, fontAkzent });
    } catch { toast.error('Speichern fehlgeschlagen'); }
    finally { setSaving(false); }
  };

  const primaryDark = adjustHex(primary, -30);
  const allColors   = brandData?.all_colors || [];

  return (
    <div style={{ fontFamily: 'var(--font-sans)', display: 'grid',
                  gridTemplateColumns: '1fr 320px', gap: 0, minHeight: 560,
                  border: '0.5px solid var(--border-light)', borderRadius: 10,
                  overflow: 'visible', background: 'var(--bg-surface)' }}
      onClick={() => setActiveColorId(null)}
    >
      {/* LINKE SPALTE: Steuerung */}
      <div style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 12,
                    borderRight: '0.5px solid var(--border-light)', overflowY: 'auto' }}
        onClick={e => e.stopPropagation()}
      >
        <Section label="Farben" hint="Klick auf Farbe zum Bearbeiten">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 8, position: 'relative' }}>
            {[
              { id:'primary',  label:'Primaer',      value:primary,      onChange:setPrimary  },
              { id:'prim_d',   label:'Primaer Dark',  value:primaryDark,  onChange:null, autoValue:primaryDark },
              { id:'secondary',label:'Sekundaer',     value:secondary,    onChange:setSecondary },
              { id:'accent',   label:'Akzent',       value:accent,       onChange:setAccent  },
              { id:'bg',       label:'Hintergrund',  value:colorBg,      onChange:setColorBg },
              { id:'field',    label:'Felder',        value:colorField,   onChange:setColorField },
              { id:'heading',  label:'Ueberschrift', value:colorHeading, onChange:setColorHeading },
              { id:'text',     label:'Text',          value:colorText,    onChange:setColorText },
            ].map(t => (
              <ColorToken key={t.id} {...t} allColors={allColors} activeId={activeColorId} setActiveId={setActiveColorId} />
            ))}
          </div>
          {allColors.length > 0 && (
            <div style={{ marginTop: 10 }}>
              <div style={{ fontSize: 9, fontWeight: 900, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.08em', marginBottom: 5 }}>
                Von Website erkannt — klick zum uebernehmen
              </div>
              <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                {allColors.slice(0,12).map((c,i) => (
                  <div key={i} onClick={() => {
                    if (!activeColorId || activeColorId === 'prim_d') return;
                    const map = { primary:setPrimary, secondary:setSecondary, accent:setAccent,
                                  bg:setColorBg, field:setColorField, heading:setColorHeading, text:setColorText };
                    if (map[activeColorId]) map[activeColorId](c);
                  }}
                    title={c}
                    style={{ width: 22, height: 22, borderRadius: 4, background: c,
                             border: '0.5px solid rgba(0,0,0,.1)', cursor: 'pointer' }}
                  />
                ))}
              </div>
              {activeColorId && activeColorId !== 'prim_d' && (
                <div style={{ fontSize: 10, color: 'var(--text-tertiary)', marginTop: 4 }}>
                  Klick auf erkannte Farbe → wird als "{activeColorId}" uebernommen
                </div>
              )}
            </div>
          )}
        </Section>

        <Section label="Schriften" hint="Je Rolle: Font + Textfarbe">
          {[
            { label:'Ueberschriften (H1 · H2 · H3)', font:fontH1, setFont:f=>{setFontH1(f);loadFont(f);},
              color:colorFontH1, setColor:setColorFontH1,
              sample:'Ueberschrift — Ihr Betrieb', sampleSize:16, sampleWeight:700 },
            { label:'Fliesstext', font:fontBody, setFont:f=>{setFontBody(f);loadFont(f);},
              color:colorFontBody, setColor:setColorFontBody,
              sample:'Fliesstext — professionell und gut lesbar.', sampleSize:12, sampleWeight:400 },
            { label:'Akzent (Buttons · CTA)', font:fontAkzent, setFont:f=>{setFontAkzent(f);loadFont(f);},
              color:colorFontCta, setColor:setColorFontCta,
              sample:'JETZT ANFRAGEN', sampleSize:11, sampleWeight:700, sampleUpper:true },
          ].map(({ label, font, setFont, color, setColor, sample, sampleSize, sampleWeight, sampleUpper }) => (
            <div key={label} style={{ padding: '9px 0', borderBottom: '0.5px solid var(--border-light)' }}>
              <div style={{ fontSize: 9, fontWeight: 900, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.06em', marginBottom: 6 }}>
                {label}
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 28px', gap: 8, alignItems: 'center', marginBottom: 6 }}>
                <FontPicker value={font} onChange={setFont} detectedFonts={detectedFonts} />
                <div style={{ position: 'relative' }}>
                  <div
                    onClick={e => { e.stopPropagation(); setActiveColorId(activeColorId===label ? null : label); }}
                    style={{ width: 28, height: 28, borderRadius: 5, background: color,
                             border: activeColorId===label ? '2px solid var(--brand-primary,#004F59)' : '0.5px solid rgba(0,0,0,.15)',
                             cursor: 'pointer' }}
                  />
                  {activeColorId === label && (
                    <div style={{
                      position: 'absolute', right: 0, top: 34, zIndex: 200,
                      background: 'var(--bg-surface)',
                      border: '1.5px solid var(--brand-primary,#004F59)',
                      borderRadius: 8, padding: 10,
                      boxShadow: '0 8px 24px rgba(0,0,0,.18)', width: 160,
                    }} onClick={e => e.stopPropagation()}>
                      <div style={{ display: 'flex', gap: 6, alignItems: 'center', marginBottom: 8 }}>
                        <div style={{ width: 24, height: 24, borderRadius: 4, background: color, border: '0.5px solid rgba(0,0,0,.1)', flexShrink: 0 }} />
                        <input value={color} onChange={e => setColor(e.target.value)}
                          style={{ flex: 1, padding: '3px 6px', fontSize: 11, fontFamily: 'monospace',
                                   border: '0.5px solid var(--border-light)', borderRadius: 4,
                                   background: 'var(--bg-surface)', color: 'var(--text-primary)' }} />
                        <input type="color" value={color?.length===7?color:'#ffffff'}
                          onChange={e => setColor(e.target.value)}
                          style={{ width: 24, height: 24, cursor: 'pointer', border: 'none' }} />
                      </div>
                      <div style={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
                        {['#FFFFFF','#000000','#FAE600',primary,secondary,accent,...allColors.slice(0,6)].map((c,i) => (
                          <div key={i} onClick={() => setColor(c)}
                            style={{ width: 18, height: 18, borderRadius: 3, background: c, cursor: 'pointer',
                                     border: c===color ? '2px solid #004F59' : '0.5px solid rgba(0,0,0,.1)' }} />
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
              <div style={{
                fontFamily: font, fontSize: sampleSize, fontWeight: sampleWeight,
                color: 'var(--text-primary)', lineHeight: 1.3,
                textTransform: sampleUpper ? 'uppercase' : 'none',
                letterSpacing: sampleUpper ? '.06em' : 'normal',
                padding: '4px 0',
              }}>
                {sample}
              </div>
            </div>
          ))}
        </Section>

        <Section label="Stil & Radius">
          <div style={{ display: 'flex', gap: 12 }}>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 9, fontWeight: 900, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.08em', marginBottom: 6 }}>Ecken</div>
              <div style={{ display: 'flex', gap: 5 }}>
                {[{l:'Eckig',v:0},{l:'Rund',v:6},{l:'Weich',v:14},{l:'Pill',v:99}].map(r => (
                  <button key={r.v} onClick={() => setRadius(r.v)} style={{
                    flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4, padding: '7px 0',
                    border: radius===r.v ? '1.5px solid var(--brand-primary,#004F59)' : '0.5px solid var(--border-light)',
                    borderRadius: 6, background: radius===r.v ? '#E0F4F8' : 'var(--bg-surface)', cursor: 'pointer', fontFamily: 'var(--font-sans)',
                  }}>
                    <div style={{ width: 22, height: 22, border: `2px solid ${radius===r.v ? '#004F59' : 'var(--border-medium)'}`, borderRadius: r.v===99 ? 11 : r.v, background: radius===r.v ? '#E0F4F8' : 'transparent' }} />
                    <span style={{ fontSize: 8, fontWeight: 700, textTransform: 'uppercase', color: radius===r.v ? '#004F59' : 'var(--text-tertiary)', letterSpacing: '.04em' }}>{r.l}</span>
                  </button>
                ))}
              </div>
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 9, fontWeight: 900, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.08em', marginBottom: 6 }}>Schatten</div>
              <div style={{ display: 'flex', gap: 5 }}>
                {['ohne','leicht','mittel','stark'].map(s => (
                  <button key={s} onClick={() => setShadow(s)} style={{
                    flex: 1, padding: '7px 0', fontSize: 9, fontWeight: 700,
                    border: shadow===s ? '1.5px solid var(--brand-primary,#004F59)' : '0.5px solid var(--border-light)',
                    borderRadius: 5, background: shadow===s ? '#E0F4F8' : 'var(--bg-surface)',
                    color: shadow===s ? '#004F59' : 'var(--text-tertiary)',
                    cursor: 'pointer', fontFamily: 'var(--font-sans)', textTransform: 'uppercase', letterSpacing: '.04em',
                  }}>{s}</button>
                ))}
              </div>
            </div>
          </div>
        </Section>

        <div style={{ display: 'flex', gap: 8, marginTop: 'auto', paddingTop: 4 }}>
          <button onClick={rescrape} disabled={scraping} style={{
            padding: '10px 14px', background: 'transparent',
            color: 'var(--text-secondary)', border: '0.5px solid var(--border-light)',
            borderRadius: 8, fontSize: 11, fontWeight: 700, cursor: 'pointer',
            fontFamily: 'var(--font-sans)', whiteSpace: 'nowrap',
          }}>
            {scraping ? 'Scannt…' : 'Website neu scannen'}
          </button>
          <button onClick={save} disabled={saving} style={{
            flex: 1, padding: '11px', background: '#FAE600', color: '#000',
            border: 'none', borderRadius: 8, fontSize: 12, fontWeight: 900,
            cursor: saving ? 'not-allowed' : 'pointer',
            fontFamily: 'var(--font-sans)', textTransform: 'uppercase', letterSpacing: '.05em',
          }}>
            {saving ? 'Wird gespeichert…' : 'Brand Design speichern'}
          </button>
        </div>
      </div>

      {/* RECHTE SPALTE: Vorschau */}
      <div style={{ background: '#fff', display: 'flex', flexDirection: 'column', borderRadius: '0 10px 10px 0' }}>
        <div style={{
          padding: '9px 14px', borderBottom: '0.5px solid var(--border-light)',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexShrink: 0,
        }}>
          <span style={{ fontSize: 9, fontWeight: 900, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.1em' }}>Vorschau</span>
          <span style={{ fontSize: 9, fontWeight: 900, padding: '2px 8px', borderRadius: 3,
                         background: '#FFFBE0', color: '#B8860B', border: '0.5px solid #B8860B33',
                         textTransform: 'uppercase', letterSpacing: '.06em' }}>
            Beispiel-Inhalt
          </span>
        </div>

        <div style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
          <div style={{ background: primary, height: 40, display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 14px', flexShrink: 0 }}>
            <span style={{ fontFamily: fontH1, fontSize: 13, fontWeight: 700, color: colorFontH1 }}>Firmenname GmbH</span>
            <div style={{ background: accent, color: colorFontCta, fontFamily: fontAkzent, fontSize: 10, fontWeight: 700, padding: '4px 10px', borderRadius: Math.min(radius, 6), textTransform: 'uppercase', letterSpacing: '.04em' }}>Anfragen</div>
          </div>

          <div style={{ background: adjustHex(primary,-20), padding: '18px 14px', flexShrink: 0 }}>
            <div style={{ fontFamily: fontH1, fontSize: 17, fontWeight: 700, color: colorFontH1, marginBottom: 3, lineHeight: 1.2 }}>
              Ueberschrift H1 — Profis fuer Ihr Projekt
            </div>
            <div style={{ fontFamily: fontH1, fontSize: 13, fontWeight: 600, color: colorFontH1, opacity: 0.75, marginBottom: 8 }}>
              Ueberschrift H2 — Seit 20 Jahren in der Region
            </div>
            <div style={{ fontFamily: fontBody, fontSize: 11, color: colorFontBody, lineHeight: 1.65, marginBottom: 10 }}>
              Fliesstext mit dem gewaehlten Body-Font — klar, lesbar und professionell gesetzt.
            </div>
            <div style={{ display: 'inline-block', background: accent, color: colorFontCta, fontFamily: fontAkzent, fontSize: 10, fontWeight: 700, padding: '7px 14px', borderRadius: radius, textTransform: 'uppercase', letterSpacing: '.05em' }}>
              Jetzt anfragen
            </div>
          </div>

          <div style={{ background: colorBg, padding: '12px 14px', flex: 1 }}>
            <div style={{ fontFamily: fontH1, fontSize: 12, fontWeight: 700, color: colorHeading, marginBottom: 8 }}>Unsere Leistungen</div>
            {['Leistung A','Leistung B'].map(l => (
              <div key={l} style={{
                background: colorField, border: `0.5px solid ${adjustHex(colorField,-15)}`,
                borderRadius: radius, padding: '9px 11px', marginBottom: 7,
                boxShadow: shadow==='ohne' ? 'none' : shadow==='leicht' ? '0 2px 6px rgba(0,0,0,.07)' : shadow==='mittel' ? '0 3px 10px rgba(0,0,0,.11)' : '0 5px 18px rgba(0,0,0,.16)',
              }}>
                <div style={{ fontFamily: fontH1, fontSize: 12, fontWeight: 700, color: colorHeading, marginBottom: 3 }}>{l}</div>
                <div style={{ fontFamily: fontBody, fontSize: 10, color: colorText, lineHeight: 1.5 }}>Kurze Leistungsbeschreibung im Fliesstext-Font.</div>
              </div>
            ))}
          </div>

          <div style={{ background: secondary, padding: '8px 14px', flexShrink: 0 }}>
            <div style={{ fontFamily: fontBody, fontSize: 9, color: 'rgba(255,255,255,.45)' }}>Firmenname · Impressum · Datenschutz</div>
          </div>
        </div>
      </div>
    </div>
  );
}

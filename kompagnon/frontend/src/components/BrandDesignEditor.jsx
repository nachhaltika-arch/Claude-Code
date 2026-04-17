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
const GOOGLE_FONTS = ['Georgia','Playfair Display','Merriweather','Lora','Inter','Roboto','Open Sans','Noto Sans','Barlow Condensed','Oswald','Raleway','Montserrat'];

export default function BrandDesignEditor({ leadId, token, brandData, onSaved }) {
  const [primary, setPrimary]     = useState(brandData?.primary_color || '#004F59');
  const [secondary, setSecondary] = useState(brandData?.secondary_color || '#2C3E50');
  const [accent, setAccent]       = useState('#F39C12');
  const [fontHead, setFontHead]   = useState(brandData?.font_primary || 'Georgia');
  const [fontBody, setFontBody]   = useState(brandData?.font_secondary || 'Arial');
  const [radius, setRadius]       = useState(6);
  const [shadow, setShadow]       = useState('leicht');
  const [activeToken, setActiveToken] = useState(null);
  const [saving, setSaving]       = useState(false);
  const [activeTab, setActiveTab] = useState('design');
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
        if (d.font_primary) setFontHead(d.font_primary);
        if (d.font_secondary) setFontBody(d.font_secondary);
        const dd = d.design_data;
        if (dd?.border_radius_px) setRadius(dd.border_radius_px);
        if (dd?.shadow_label) setShadow(dd.shadow_label);
        const ac = dd?.design_brief?.akzentfarbe || dd?.colors?.accent;
        if (ac) setAccent(ac);
      }).catch(() => {});
  }, [leadId, token]); // eslint-disable-line

  const save = async () => {
    setSaving(true);
    try {
      await fetch(`${API_BASE_URL}/api/branddesign/${leadId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ primary_color: primary, secondary_color: secondary, font_primary: fontHead, font_secondary: fontBody }),
      });
      toast.success('Brand Design gespeichert');
      if (onSaved) onSaved({ primary, secondary, accent, fontHead, fontBody, radius });
    } catch { toast.error('Speichern fehlgeschlagen'); }
    finally { setSaving(false); }
  };

  const tokens = [
    { id: 'primary', label: 'Primaer', color: primary, type: 'color', setter: setPrimary },
    { id: 'primary_d', label: 'Primaer Dark', color: adjustColor(primary, -30), type: 'derived', setter: null },
    { id: 'secondary', label: 'Sekundaer', color: secondary, type: 'color', setter: setSecondary },
    { id: 'accent', label: 'Akzent', color: accent, type: 'color', setter: setAccent },
    { id: 'surface', label: 'Surface', color: '#F5F5F0', type: 'color', setter: null },
  ];

  return (
    <div ref={editorRef} style={{ fontFamily: 'var(--font-sans)' }}>

      {/* Tabs */}
      <div style={{ display: 'flex', borderBottom: '0.5px solid var(--border-light)', marginBottom: 16 }}>
        {[['design', 'Brand Design'], ['guideline', 'Guideline']].map(([id, lbl]) => (
          <button key={id} onClick={() => setActiveTab(id)} style={{
            padding: '8px 16px', fontSize: 11, fontWeight: 700,
            color: activeTab === id ? 'var(--brand-primary)' : 'var(--text-tertiary)',
            background: 'none', border: 'none',
            borderBottom: activeTab === id ? '2px solid #FAE600' : '2px solid transparent',
            cursor: 'pointer', fontFamily: 'var(--font-sans)',
            textTransform: 'uppercase', letterSpacing: '.06em',
          }}>{lbl}</button>
        ))}
      </div>

      {activeTab === 'design' && (
        <>
          {/* Mini-Vorschau */}
          <div style={{ border: '0.5px solid var(--border-light)', borderRadius: 10, overflow: 'hidden', marginBottom: 16 }}>
            <div style={{ background: primary, padding: '10px 16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ fontFamily: fontHead, fontSize: 15, fontWeight: 700, color: '#fff' }}>Firmenname</span>
              <button style={{ background: accent, color: '#fff', border: 'none', borderRadius: radius, padding: '6px 14px', fontSize: 12, fontWeight: 700, cursor: 'default' }}>Anfragen</button>
            </div>
            <div style={{ background: adjustColor(primary, -20), padding: 16 }}>
              <div style={{ fontFamily: fontHead, fontSize: 18, fontWeight: 700, color: '#fff', marginBottom: 6 }}>Ueberschrift H1</div>
              <div style={{ fontFamily: fontBody, fontSize: 13, color: 'rgba(255,255,255,.75)', lineHeight: 1.6 }}>Fliesstext mit dem gewaehlten Body-Font.</div>
            </div>
            <div style={{ background: '#F5F5F0', padding: '12px 16px' }}>
              <div style={{ background: '#fff', border: '0.5px solid #D5D5D0', borderRadius: radius, padding: 12, boxShadow: shadow === 'stark' ? '0 4px 16px rgba(0,0,0,.12)' : '0 2px 6px rgba(0,0,0,.06)' }}>
                <div style={{ fontFamily: fontHead, fontSize: 14, fontWeight: 700, color: secondary, marginBottom: 4 }}>Leistungs-Karte</div>
                <div style={{ fontFamily: fontBody, fontSize: 12, color: '#555', lineHeight: 1.5 }}>Karteninhalt mit Sekundaerfarbe.</div>
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

          {/* Inline-Editor */}
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

          {/* Schrift + Stil */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 16 }}>
            <div>
              <div style={{ fontSize: 9, fontWeight: 900, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.1em', marginBottom: 6 }}>Schriften</div>
              <div style={{ fontSize: 10, color: 'var(--text-tertiary)', marginBottom: 3 }}>Ueberschriften</div>
              <select value={fontHead} onChange={e => setFontHead(e.target.value)} style={{ width: '100%', padding: '7px 10px', border: '0.5px solid var(--border-light)', borderRadius: 6, fontSize: 12, background: 'var(--bg-surface)', color: 'var(--text-primary)', fontFamily: fontHead, marginBottom: 6 }}>
                {GOOGLE_FONTS.map(f => <option key={f} value={f}>{f}</option>)}
              </select>
              <div style={{ fontSize: 10, color: 'var(--text-tertiary)', marginBottom: 3 }}>Fliesstext</div>
              <select value={fontBody} onChange={e => setFontBody(e.target.value)} style={{ width: '100%', padding: '7px 10px', border: '0.5px solid var(--border-light)', borderRadius: 6, fontSize: 12, background: 'var(--bg-surface)', color: 'var(--text-primary)', fontFamily: fontBody }}>
                {GOOGLE_FONTS.map(f => <option key={f} value={f}>{f}</option>)}
              </select>
            </div>
            <div>
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
          </div>

          {/* Speichern */}
          <button onClick={save} disabled={saving} style={{
            width: '100%', padding: 11, background: saving ? 'var(--border-light)' : '#FAE600',
            color: '#000', border: 'none', borderRadius: 8, fontSize: 12, fontWeight: 900,
            cursor: saving ? 'not-allowed' : 'pointer', fontFamily: 'var(--font-sans)',
            textTransform: 'uppercase', letterSpacing: '.05em',
          }}>{saving ? 'Wird gespeichert…' : 'Brand Design speichern'}</button>
        </>
      )}

      {/* Guideline Tab */}
      {activeTab === 'guideline' && (
        <GuidelineTab leadId={leadId} authToken={token} />
      )}
    </div>
  );
}

function GuidelineTab({ leadId, authToken }) {
  const [guideline, setGuideline] = useState(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/branddesign/${leadId}/guideline`, { headers: { Authorization: `Bearer ${authToken}` } })
      .then(r => r.ok ? r.json() : null)
      .then(d => { if (d?.generated) setGuideline(d.guideline); })
      .catch(() => {}).finally(() => setLoading(false));
  }, [leadId, authToken]);

  const generate = async () => {
    setGenerating(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/branddesign/${leadId}/guideline/generate`, { method: 'POST', headers: { Authorization: `Bearer ${authToken}`, 'Content-Type': 'application/json' } });
      const d = await res.json();
      setGuideline(d.guideline);
      toast.success('Guideline generiert!');
    } catch { toast.error('Fehler'); }
    finally { setGenerating(false); }
  };

  if (loading) return <div style={{ padding: 20, color: 'var(--text-tertiary)', fontSize: 13 }}>Laedt…</div>;

  if (!guideline) return (
    <div style={{ padding: '20px 0', textAlign: 'center' }}>
      <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 12 }}>Guideline noch nicht generiert.</div>
      <button onClick={generate} disabled={generating} style={{ background: 'var(--brand-primary)', color: '#fff', border: 'none', borderRadius: 8, padding: '10px 22px', fontSize: 12, fontWeight: 900, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
        {generating ? 'Generiert…' : 'Guideline generieren'}
      </button>
    </div>
  );

  return (
    <div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(80px, 1fr))', gap: 8, marginBottom: 16 }}>
        {Object.entries(guideline.colors || {}).slice(0, 12).map(([tk, hex]) => (
          <div key={tk} style={{ textAlign: 'center' }}>
            <div onClick={() => { navigator.clipboard?.writeText(hex); toast.success(`${hex} kopiert`); }} title={`${tk}: ${hex}`}
              style={{ height: 40, borderRadius: 6, background: hex, border: '0.5px solid rgba(0,0,0,.08)', cursor: 'pointer', marginBottom: 3 }} />
            <div style={{ fontSize: 8, color: 'var(--text-tertiary)', fontFamily: 'monospace' }}>{hex}</div>
            <div style={{ fontSize: 8, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.04em' }}>{tk.replace(/_/g, ' ')}</div>
          </div>
        ))}
      </div>
      <div style={{ padding: '10px 12px', background: 'var(--surface)', borderRadius: 8, fontSize: 11, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
        Vollstaendige Guideline → im naechsten Schritt "Brand Guideline" verfuegbar.
      </div>
    </div>
  );
}

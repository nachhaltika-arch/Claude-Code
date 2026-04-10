import { useState, useEffect } from 'react';
import API_BASE_URL from '../config';
import toast from 'react-hot-toast';

const TEMPLATE_PRESETS = [
  { id: 'modern-clean',   name: 'Modern Clean',    desc: 'Minimalistisch, viel Weissraum, klare Typografie',    icon: '⬜', style: { borderRadius: 8, shadows: 'leicht', density: 'luftig' },   preview_gradient: 'linear-gradient(135deg, #f8fafc, #e2e8f0)' },
  { id: 'handwerk-bold',  name: 'Handwerk Bold',   desc: 'Kraftvoll, erdige Toene, handwerkliches Gefuehl',     icon: '🔨', style: { borderRadius: 4, shadows: 'mittel', density: 'kompakt' },  preview_gradient: 'linear-gradient(135deg, #292524, #57534e)' },
  { id: 'service-trust',  name: 'Service & Trust',  desc: 'Vertrauenswuerdig, professionell, klar strukturiert', icon: '🤝', style: { borderRadius: 6, shadows: 'mittel', density: 'normal' },   preview_gradient: 'linear-gradient(135deg, #1e3a5f, #185fa5)' },
  { id: 'local-friendly', name: 'Local Friendly',   desc: 'Warm, freundlich, lokal verwurzelt',                  icon: '🏘️', style: { borderRadius: 12, shadows: 'leicht', density: 'normal' },  preview_gradient: 'linear-gradient(135deg, #065f46, #059669)' },
  { id: 'premium-dark',   name: 'Premium Dark',     desc: 'Hochwertig, dunkel, exklusives Auftreten',            icon: '\u2726', style: { borderRadius: 4, shadows: 'stark', density: 'luftig' }, preview_gradient: 'linear-gradient(135deg, #0f172a, #1e293b)' },
];

export default function DesignStudio({ project, leadId, token, brandData, sitemapPages }) {
  const [step, setStep]                         = useState(1);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [dbTemplates, setDbTemplates]           = useState([]);
  const [selectedPage, setSelectedPage]         = useState(null);
  const [generating, setGenerating]             = useState(false);
  const [designResult, setDesignResult]         = useState(null);

  const headers = { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` };

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/templates/`, { headers })
      .then(r => r.ok ? r.json() : [])
      .then(data => setDbTemplates(Array.isArray(data) ? data.slice(0, 6) : []))
      .catch(() => {});
  }, []); // eslint-disable-line

  const primaryColor   = brandData?.primary_color   || '#008EAA';
  const secondaryColor = brandData?.secondary_color || '#004F59';
  const fontPrimary    = brandData?.font_primary    || 'Inter';

  const generateDesign = async () => {
    if (!selectedPage || !selectedTemplate) {
      toast.error('Bitte Seite und Template auswaehlen');
      return;
    }
    setGenerating(true);
    try {
      const res = await fetch(
        `${API_BASE_URL}/api/agents/${project.id}/content`,
        {
          method: 'POST', headers,
          body: JSON.stringify({
            company_name:   project.company_name || '',
            page_name:      selectedPage.page_name,
            template_style: selectedTemplate.id || selectedTemplate.name,
            brand_primary:  primaryColor,
            brand_secondary: secondaryColor,
            brand_font:     fontPrimary,
            zweck:          selectedPage.zweck || '',
            ziel_keyword:   selectedPage.ziel_keyword || '',
          }),
        }
      );
      if (!res.ok) throw new Error('Generierung fehlgeschlagen');
      const { job_id } = await res.json();

      const deadline = Date.now() + 120_000;
      while (Date.now() < deadline) {
        await new Promise(r => setTimeout(r, 2000));
        const poll = await fetch(`${API_BASE_URL}/api/agents/jobs/${job_id}`, { headers }).then(r => r.json());
        if (poll.status === 'done') {
          setDesignResult(poll.result_html || poll.result);
          setStep(4);
          toast.success('Design-Entwurf fertig!');
          break;
        }
        if (poll.status === 'error') throw new Error(poll.error || 'Fehler');
      }
    } catch (e) {
      toast.error(e.message);
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>

      {/* Schritt-Anzeige */}
      <div style={{ display: 'flex', borderBottom: '1px solid var(--border-light)', background: 'var(--bg-app)', padding: '12px 20px', gap: 0 }}>
        {[
          { n: 1, label: 'Template waehlen' },
          { n: 2, label: 'Brand anwenden' },
          { n: 3, label: 'Seite waehlen' },
          { n: 4, label: 'KI generiert' },
        ].map((s, i) => (
          <div key={s.n} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            {i > 0 && <div style={{ width: 24, height: 2, background: step > i ? 'var(--brand-primary)' : 'var(--border-light)' }} />}
            <div onClick={() => step > s.n && setStep(s.n)} style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: step > s.n ? 'pointer' : 'default' }}>
              <div style={{
                width: 24, height: 24, borderRadius: '50%',
                background: step >= s.n ? 'var(--brand-primary)' : 'var(--bg-elevated)',
                color: step >= s.n ? '#fff' : 'var(--text-tertiary)',
                fontSize: 11, fontWeight: 700,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}>
                {step > s.n ? '\u2713' : s.n}
              </div>
              <span style={{ fontSize: 11, fontWeight: step === s.n ? 700 : 400, color: step >= s.n ? 'var(--text-primary)' : 'var(--text-tertiary)', whiteSpace: 'nowrap' }}>
                {s.label}
              </span>
            </div>
          </div>
        ))}
      </div>

      <div style={{ padding: '20px 24px' }}>

        {/* Schritt 1: Template waehlen */}
        {step === 1 && (
          <div>
            <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 16 }}>Template waehlen</div>

            <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.06em', marginBottom: 10 }}>Stil-Vorlagen</div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: 12, marginBottom: 24 }}>
              {TEMPLATE_PRESETS.map(t => (
                <div
                  key={t.id}
                  onClick={() => { setSelectedTemplate(t); setStep(2); }}
                  style={{
                    borderRadius: 10, overflow: 'hidden',
                    border: `2px solid ${selectedTemplate?.id === t.id ? 'var(--brand-primary)' : 'var(--border-light)'}`,
                    cursor: 'pointer', transition: 'all 0.15s',
                  }}
                  onMouseEnter={e => e.currentTarget.style.transform = 'translateY(-2px)'}
                  onMouseLeave={e => e.currentTarget.style.transform = 'translateY(0)'}
                >
                  <div style={{ height: 80, background: t.preview_gradient, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 28 }}>{t.icon}</div>
                  <div style={{ padding: '10px 12px', background: 'var(--bg-surface)' }}>
                    <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 3 }}>{t.name}</div>
                    <div style={{ fontSize: 10, color: 'var(--text-tertiary)', lineHeight: 1.4 }}>{t.desc}</div>
                  </div>
                </div>
              ))}
            </div>

            {dbTemplates.length > 0 && (
              <>
                <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.06em', marginBottom: 10 }}>Gespeicherte Templates</div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: 12 }}>
                  {dbTemplates.map(t => (
                    <div key={t.id} onClick={() => { setSelectedTemplate(t); setStep(2); }}
                      style={{ borderRadius: 10, overflow: 'hidden', border: `2px solid ${selectedTemplate?.id === t.id ? 'var(--brand-primary)' : 'var(--border-light)'}`, cursor: 'pointer' }}>
                      {t.thumbnail_url ? (
                        <img src={t.thumbnail_url} alt={t.name} style={{ width: '100%', height: 80, objectFit: 'cover' }} />
                      ) : (
                        <div style={{ height: 80, background: 'var(--bg-elevated)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 24 }}>🌐</div>
                      )}
                      <div style={{ padding: '10px 12px', background: 'var(--bg-surface)' }}>
                        <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-primary)' }}>{t.name}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>
        )}

        {/* Schritt 2: Brand anwenden */}
        {step === 2 && selectedTemplate && (
          <div>
            <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 16 }}>
              Brand Design auf "{selectedTemplate.name}" anwenden
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 24 }}>
              {/* Brand-Daten */}
              <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 10, padding: 16 }}>
                <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.06em', marginBottom: 12 }}>Erkannte Brand-Daten</div>
                <div style={{ display: 'flex', gap: 8, marginBottom: 10 }}>
                  {[primaryColor, secondaryColor].filter(Boolean).map((c, i) => (
                    <div key={i} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
                      <div style={{ width: 36, height: 36, borderRadius: 6, background: c, border: '1px solid var(--border-light)' }} />
                      <div style={{ fontSize: 9, color: 'var(--text-tertiary)', fontFamily: 'monospace' }}>{c}</div>
                    </div>
                  ))}
                </div>
                {fontPrimary && (
                  <div>
                    <div style={{ fontSize: 18, fontWeight: 700, color: primaryColor }}>{fontPrimary}</div>
                    <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>Aa Bb Cc 1 2 3</div>
                  </div>
                )}
                {!brandData?.primary_color && (
                  <div style={{ fontSize: 11, color: 'var(--status-warning-text)', background: 'var(--status-warning-bg)', padding: '8px 10px', borderRadius: 6, marginTop: 8 }}>
                    Noch kein Brand-Scan — Standardfarben werden verwendet.
                  </div>
                )}
              </div>

              {/* Template-Vorschau */}
              <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 10, overflow: 'hidden' }}>
                <div style={{ height: 8, background: primaryColor }} />
                <div style={{ padding: 16 }}>
                  <div style={{ fontSize: 16, fontWeight: 700, color: primaryColor, marginBottom: 6 }}>
                    {project?.company_name || 'Ihr Unternehmen'}
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginBottom: 12 }}>{selectedTemplate.desc}</div>
                  <div style={{ display: 'inline-block', padding: '6px 14px', background: primaryColor, color: '#fff', borderRadius: selectedTemplate.style?.borderRadius || 6, fontSize: 11, fontWeight: 600 }}>
                    Kontakt aufnehmen
                  </div>
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', gap: 10 }}>
              <button onClick={() => setStep(1)} style={{ padding: '9px 18px', borderRadius: 8, border: '1px solid var(--border-light)', background: 'var(--bg-surface)', color: 'var(--text-primary)', fontSize: 13, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
                Anderes Template
              </button>
              <button onClick={() => setStep(3)} style={{ padding: '9px 24px', borderRadius: 8, border: 'none', background: 'var(--brand-primary)', color: '#fff', fontSize: 13, fontWeight: 700, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
                Brand passt — Seite waehlen
              </button>
            </div>
          </div>
        )}

        {/* Schritt 3: Seite waehlen */}
        {step === 3 && (
          <div>
            <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 16 }}>Fuer welche Seite soll der Entwurf erstellt werden?</div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))', gap: 10, marginBottom: 20 }}>
              {sitemapPages.map(page => (
                <div key={page.id} onClick={() => setSelectedPage(page)}
                  style={{
                    padding: '12px 14px', borderRadius: 8,
                    border: `2px solid ${selectedPage?.id === page.id ? 'var(--brand-primary)' : 'var(--border-light)'}`,
                    background: selectedPage?.id === page.id ? 'var(--bg-active, var(--bg-elevated))' : 'var(--bg-surface)',
                    cursor: 'pointer',
                  }}>
                  <div style={{ fontSize: 12, fontWeight: 600, color: selectedPage?.id === page.id ? 'var(--brand-primary)' : 'var(--text-primary)', marginBottom: 3 }}>{page.page_name}</div>
                  <div style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>{page.page_type}</div>
                </div>
              ))}
            </div>
            {sitemapPages.length === 0 && (
              <div style={{ textAlign: 'center', padding: '32px 20px', color: 'var(--text-tertiary)', fontSize: 13 }}>
                Noch keine Sitemap-Seiten angelegt. Bitte zuerst im Analyse-Tab die Seitenstruktur definieren.
              </div>
            )}
            <button
              onClick={generateDesign}
              disabled={!selectedPage || generating}
              style={{
                padding: '11px 28px', borderRadius: 8, border: 'none',
                background: !selectedPage || generating ? 'var(--border-medium)' : 'linear-gradient(135deg, #008EAA, #006680)',
                color: '#fff', fontSize: 13, fontWeight: 700,
                cursor: !selectedPage || generating ? 'not-allowed' : 'pointer',
                display: 'flex', alignItems: 'center', gap: 8,
                boxShadow: !selectedPage || generating ? 'none' : '0 2px 10px rgba(0,142,170,0.35)',
                fontFamily: 'var(--font-sans)',
              }}
            >
              {generating ? (
                <><span style={{ width: 14, height: 14, border: '2px solid rgba(255,255,255,.3)', borderTopColor: '#fff', borderRadius: '50%', animation: 'spin .8s linear infinite', display: 'inline-block' }} />KI erstellt Entwurf...</>
              ) : 'Design jetzt generieren'}
            </button>
          </div>
        )}

        {/* Schritt 4: Ergebnis */}
        {step === 4 && designResult && (
          <div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
              <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' }}>
                Design-Entwurf: {selectedPage?.page_name}
              </div>
              <div style={{ display: 'flex', gap: 8 }}>
                <button onClick={() => setStep(3)} style={{ padding: '7px 14px', borderRadius: 6, border: '1px solid var(--border-light)', background: 'var(--bg-surface)', color: 'var(--text-primary)', fontSize: 12, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
                  Neue Variante
                </button>
                <button
                  onClick={() => {
                    const page = sitemapPages.find(p => p.id === selectedPage.id);
                    if (page) window.dispatchEvent(new CustomEvent('kompagnon:open-editor', { detail: { pageId: page.id, html: designResult } }));
                  }}
                  style={{ padding: '7px 14px', borderRadius: 6, border: 'none', background: 'var(--brand-primary)', color: '#fff', fontSize: 12, fontWeight: 600, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}
                >
                  Im Editor bearbeiten
                </button>
              </div>
            </div>
            <div style={{ border: '1px solid var(--border-light)', borderRadius: 10, overflow: 'hidden', height: 480 }}>
              <iframe
                srcDoc={typeof designResult === 'string' ? designResult : JSON.stringify(designResult)}
                style={{ width: '100%', height: '100%', border: 'none' }}
                title="Design-Vorschau"
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

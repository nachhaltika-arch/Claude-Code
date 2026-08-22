/**
 * Marketing-Schritte: Design-Studio, Google-Profil, Trustpilot, Upsell.
 *
 * **Warum eigene Datei (L-25, 22.08.2026).** `ProzessFlow.jsx` hatte 2.307
 * Zeilen. 493 davon waren tot — `PHASEN`, `ALLE_SCHRITTE` und die
 * Standardkomponente, die niemand importierte. Der Rest bestand aus einem
 * Verteiler (`SchrittInhalt`) und siebzehn Einbettungen, die je einen
 * Schritt des Online-Editors anzeigen.
 *
 * Geschnitten ist nach **Thema**, nicht nach Groesse: Die Einbettungen
 * teilen untereinander nichts ausser den Bibliotheks-Importen — nachgemessen
 * vor dem Schnitt. `SchrittInhalt` bleibt in `ProzessFlow.jsx` und holt sie
 * von hier.
 */
import API_BASE_URL from '../../config';
import { loadJson } from '../../utils/apiRequest';
import { aufTaste } from '../../utils/tastaturBedienung';
import { useEffect, useState } from 'react';


export function DesignStudioEmbed({ project, leadId, token, headers, brandData, sitemapPages }) {
  const [selectedPage, setSelectedPage] = useState(null);
  const [generating, setGenerating]     = useState(false);
  const [generatedHtml, setGeneratedHtml] = useState(null);
  const [error, setError]               = useState('');
  const [dbTemplates, setDbTemplates]   = useState([]);
  const [selectedTpl, setSelectedTpl]   = useState(null);

  useEffect(() => {
    loadJson(`${API_BASE_URL}/api/templates/`, { headers }, { context: 'Vorlagen', fallback: [] })
      .then(d => setDbTemplates(Array.isArray(d) ? d : []));
  }, []); // eslint-disable-line

  const PRESETS = [
    { id: 'modern', label: 'Modern Clean', color: 'var(--kc-mid)', desc: 'Minimalistisch, viel Weissraum' },
    { id: 'bold', label: 'Handwerk Bold', color: '#C0392B', desc: 'Kraftvoll, markant' },
    { id: 'trust', label: 'Service & Trust', color: '#2C3E50', desc: 'Serioes, vertrauenswuerdig' },
    { id: 'friendly', label: 'Local Friendly', color: '#27AE60', desc: 'Warm, freundlich, lokal' },
    { id: 'premium', label: 'Premium Dark', color: '#1A1A2E', desc: 'Hochwertig, dunkel' },
  ];

  const colors = brandData ? [
    { role: 'Primaer', hex: brandData.primary_color || '#008EAA' },
    { role: 'Sekundaer', hex: brandData.secondary_color || '#004F59' },
  ].filter(c => c.hex) : [];

  const fonts = brandData?.all_fonts || [];

  const generate = async () => {
    if (!selectedPage) { setError('Bitte Seite auswaehlen'); return; }
    setGenerating(true); setError('');
    try {
      const res = await fetch(`${API_BASE_URL}/api/projects/${project.id}/design-json/${selectedPage.id}`, { method: 'POST', headers });
      if (!res.ok) throw new Error((await res.json().catch(()=>({}))).detail || 'Fehler');
      const { blocks, brand } = await res.json();
      const { renderPage } = await import('../grapesjs/handwerk-blocks');
      setGeneratedHtml(renderPage(blocks, brand));
    } catch (e) { setError(e.message); }
    finally { setGenerating(false); }
  };

  return (
    <div style={{ padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: 24 }}>
      {colors.length > 0 && (
        <div>
          <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.08em', marginBottom: 10 }}>Brand-Farben</div>
          <div style={{ display: 'flex', gap: 10 }}>
            {colors.map(c => (
              <div key={c.role} style={{ textAlign: 'center' }}>
                <div style={{ width: 52, height: 52, borderRadius: 10, background: c.hex, border: '1px solid var(--border-light)', marginBottom: 4 }} />
                <div style={{ fontSize: 10, color: 'var(--text-tertiary)', fontWeight: 600 }}>{c.role}</div>
                <div style={{ fontSize: 9, color: 'var(--text-tertiary)', fontFamily: 'monospace' }}>{c.hex}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {fonts.length > 0 && (
        <div>
          <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.08em', marginBottom: 10 }}>Schriftarten</div>
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
            {fonts.slice(0,4).map((f, i) => (
              <div key={i} style={{ padding: '10px 16px', background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 8 }}>
                <div style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 2 }}>Aa</div>
                <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>{f}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div>
        <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.08em', marginBottom: 10 }}>Stil-Vorlage waehlen</div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(160px,1fr))', gap: 10 }}>
          {PRESETS.map(p => (
            <div role="button" tabIndex={0} onKeyDown={aufTaste(() => setSelectedTpl(p.id))} key={p.id} onClick={() => setSelectedTpl(p.id)}
              style={{ padding: '12px 14px', borderRadius: 10, cursor: 'pointer',
                border: `2px solid ${selectedTpl === p.id ? p.color : 'var(--border-light)'}`,
                background: selectedTpl === p.id ? `${p.color}12` : 'var(--bg-surface)', transition: 'all .15s' }}>
              <div style={{ width: '100%', height: 6, borderRadius: 3, background: p.color, marginBottom: 8 }} />
              <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 3 }}>{p.label}</div>
              <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>{p.desc}</div>
            </div>
          ))}
          {dbTemplates.map(t => (
            <div role="button" tabIndex={0} onKeyDown={aufTaste(() => setSelectedTpl(`db-${t.id}`))} key={`db-${t.id}`} onClick={() => setSelectedTpl(`db-${t.id}`)}
              style={{ padding: '12px 14px', borderRadius: 10, cursor: 'pointer',
                border: `2px solid ${selectedTpl === `db-${t.id}` ? 'var(--brand-primary)' : 'var(--border-light)'}`,
                background: selectedTpl === `db-${t.id}` ? 'var(--bg-active)' : 'var(--bg-surface)' }}>
              <div style={{ fontSize: 11, color: 'var(--brand-primary-mid)', fontWeight: 700, marginBottom: 4 }}>Gespeichert</div>
              <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-primary)' }}>{t.name}</div>
            </div>
          ))}
        </div>
      </div>

      <div style={{ borderTop: '1px solid var(--border-light)', paddingTop: 20 }}>
        <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.08em', marginBottom: 10 }}>KI-Design generieren</div>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'center' }}>
          <select aria-label="Seite fuer das KI-Design" value={selectedPage?.id || ''} onChange={e => { const p = sitemapPages.find(s => String(s.id) === e.target.value); setSelectedPage(p || null); }}
            style={{ flex: 1, minWidth: 180, padding: '9px 12px', fontSize: 13, border: '1px solid var(--border-light)', borderRadius: 8, background: 'var(--bg-app)', color: 'var(--text-primary)', fontFamily: 'var(--font-sans)' }}>
            <option value="">Seite waehlen...</option>
            {sitemapPages.map(p => <option key={p.id} value={p.id}>{p.page_name}</option>)}
          </select>
          <button onClick={generate} disabled={generating || !selectedPage || !selectedTpl}
            style={{ padding: '9px 20px', borderRadius: 8, border: 'none', background: (generating || !selectedPage || !selectedTpl) ? 'var(--border-medium)' : 'var(--brand-primary)', color: '#fff', fontSize: 13, fontWeight: 700, cursor: (generating || !selectedPage || !selectedTpl) ? 'not-allowed' : 'pointer', fontFamily: 'var(--font-sans)', display: 'flex', alignItems: 'center', gap: 8 }}>
            {generating ? (<><span style={{ width:14, height:14, border:'2px solid rgba(255,255,255,.3)', borderTopColor:'#fff', borderRadius:'50%', animation:'spin .8s linear infinite', display:'inline-block' }} />Generiert...</>) : 'Design generieren'}
          </button>
        </div>
        {!selectedTpl && <div style={{ fontSize: 11, color: 'var(--status-warning-text)', marginTop: 6 }}>Bitte zuerst eine Stil-Vorlage waehlen</div>}
        {error && <div style={{ fontSize: 12, color: 'var(--status-danger-text)', marginTop: 8 }}>{error}</div>}
      </div>

      {generatedHtml && (
        <div style={{ borderTop: '1px solid var(--border-light)', paddingTop: 20 }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.08em', marginBottom: 10 }}>Vorschau</div>
          <iframe srcDoc={generatedHtml} style={{ width: '100%', height: 500, border: '1px solid var(--border-light)', borderRadius: 8 }} title="Design-Vorschau" />
          <button onClick={() => window.dispatchEvent(new CustomEvent('kompagnon:open-editor', { detail: { html: generatedHtml } }))}
            style={{ marginTop: 10, padding: '10px 20px', borderRadius: 8, border: 'none', background: 'var(--brand-primary)', color: 'var(--text-on-brand)', fontSize: 13, fontWeight: 700, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
            Im Editor oeffnen
          </button>
        </div>
      )}
    </div>
  );
}


// ── GBP + QR-Code ─────────────────────────────────────────────────────────────
export function GbpQrEmbed({ project, headers }) {
  const [gbpData, setGbpData]     = useState(null);
  const [qrData, setQrData]       = useState(null);
  const [qrLoading, setQrLoading] = useState(false);
  const [qrError, setQrError]     = useState('');

  useEffect(() => {
    loadJson(`${API_BASE_URL}/api/projects/${project.id}/bewertungs-url`, { headers }, { context: 'Bewertungs-Link' })
      .then(d => d && setGbpData(d));
  }, [project.id]); // eslint-disable-line

  const loadQr = async () => {
    setQrLoading(true); setQrError('');
    try {
      const r = await fetch(`${API_BASE_URL}/api/projects/${project.id}/bewertungs-qrcode`, { headers });
      if (!r.ok) { setQrError('QR-Code konnte nicht geladen werden'); return; }
      const blob = await r.blob();
      const reader = new FileReader();
      reader.onloadend = () => setQrData(reader.result);
      reader.readAsDataURL(blob);
    } catch { setQrError('Verbindungsfehler'); }
    finally { setQrLoading(false); }
  };

  const downloadQr = () => {
    if (!qrData) return;
    const a = document.createElement('a');
    a.href = qrData; a.download = `bewertungs-qr-${project.company_name || project.id}.png`; a.click();
  };

  return (
    <div style={{ padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: 16 }}>
      {gbpData?.review_url && (
        <div style={{ padding: 14, background: 'var(--bg-app)', border: '1px solid var(--border-light)', borderRadius: 10 }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', marginBottom: 6 }}>Google Bewertungs-Link</div>
          <a href={gbpData.review_url} target="_blank" rel="noreferrer" style={{ fontSize: 13, color: 'var(--brand-primary-mid)', wordBreak: 'break-all' }}>{gbpData.review_url}</a>
        </div>
      )}
      {project.gbp_rating && (
        <div style={{ display: 'flex', gap: 12 }}>
          <div style={{ flex: 1, padding: 14, background: 'var(--bg-app)', border: '1px solid var(--border-light)', borderRadius: 10, textAlign: 'center' }}>
            <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginBottom: 4 }}>Google Bewertung</div>
            <div style={{ fontSize: 22, fontWeight: 800, color: '#d97706' }}>⭐ {project.gbp_rating}</div>
          </div>
          <div style={{ flex: 1, padding: 14, background: 'var(--bg-app)', border: '1px solid var(--border-light)', borderRadius: 10, textAlign: 'center' }}>
            <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginBottom: 4 }}>Anzahl Bewertungen</div>
            <div style={{ fontSize: 22, fontWeight: 800, color: 'var(--text-primary)' }}>{project.gbp_ratings_total}</div>
          </div>
        </div>
      )}
      <div style={{ display: 'flex', gap: 10 }}>
        <button onClick={loadQr} disabled={qrLoading}
          style={{ flex: 1, padding: '10px 0', background: 'var(--brand-primary)', color: 'var(--text-on-brand)', border: 'none', borderRadius: 8, fontWeight: 700, fontSize: 13, cursor: qrLoading ? 'not-allowed' : 'pointer', fontFamily: 'var(--font-sans)' }}>
          {qrLoading ? 'Laden...' : '📲 QR-Code laden'}
        </button>
        {qrData && (
          <button onClick={downloadQr}
            style={{ padding: '10px 16px', background: 'var(--bg-app)', border: '1px solid var(--border-medium)', borderRadius: 8, fontSize: 13, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
            ⬇ Herunterladen
          </button>
        )}
      </div>
      {qrError && <div style={{ fontSize: 12, color: '#dc2626' }}>{qrError}</div>}
      {qrData && <img src={qrData} alt="Bewertungs-QR" style={{ width: 160, height: 160, margin: '0 auto', display: 'block', borderRadius: 8 }} />}
    </div>
  );
}

// ── Trustpilot ────────────────────────────────────────────────────────────────


// ── Trustpilot ────────────────────────────────────────────────────────────────
export function TrustpilotEmbed({ project }) {
  return (
    <div style={{ padding: '32px 24px', textAlign: 'center', display: 'flex', flexDirection: 'column', gap: 16, alignItems: 'center' }}>
      <div style={{ fontSize: 40 }}>⭐</div>
      <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' }}>Trustpilot-Bewertung anfragen</div>
      <div style={{ fontSize: 13, color: 'var(--text-secondary)', maxWidth: 360 }}>
        Fordere {project?.company_name || 'den Kunden'} auf, eine Bewertung auf Trustpilot zu hinterlassen und stärke die Online-Reputation.
      </div>
      <a href="https://www.trustpilot.com" target="_blank" rel="noreferrer"
        style={{ padding: '10px 28px', background: 'var(--success)', color: 'var(--text-on-brand)', border: 'none', borderRadius: 8, fontWeight: 700, fontSize: 13, cursor: 'pointer', fontFamily: 'var(--font-sans)', textDecoration: 'none', display: 'inline-block' }}>
        ⭐ Zu Trustpilot
      </a>
    </div>
  );
}

// ── Website-Vergleich ─────────────────────────────────────────────────────────


// ── Upsell ────────────────────────────────────────────────────────────────────
export function UpsellEmbed() {
  const PAKETE = [
    { name: 'SEO-Retainer',     price: '129€/Monat', color: '#0d6efd', features: ['Monatliche Keyword-Analyse', 'On-Page Optimierung', 'Monatlicher Report'] },
    { name: 'Wartungspaket',    price: '49€/Monat',  color: '#7c3aed', features: ['Updates & Sicherheit', 'Backup täglich', 'Support per Chat'] },
    { name: 'Digital Rundum',   price: '249€/Monat', color: '#059669', features: ['SEO + Wartung', 'Google Ads Management', 'Monatliches Strategie-Call'] },
  ];
  return (
    <div style={{ padding: '20px 24px' }}>
      <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 16 }}>💼 Upsell-Produkte</div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16 }}>
        {PAKETE.map(pkg => (
          <div key={pkg.name} style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 10, padding: 20, display: 'flex', flexDirection: 'column', gap: 10 }}>
            <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' }}>{pkg.name}</div>
            <div style={{ fontSize: 20, fontWeight: 800, color: pkg.color }}>{pkg.price}</div>
            <ul style={{ margin: 0, paddingLeft: 18, fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.8 }}>
              {pkg.features.map(f => <li key={f}>{f}</li>)}
            </ul>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Live-Daten ────────────────────────────────────────────────────────────────

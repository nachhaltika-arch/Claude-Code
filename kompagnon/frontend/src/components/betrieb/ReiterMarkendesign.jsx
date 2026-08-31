/**
 * Der Markendesign-Reiter der Betriebsansicht (L-25).
 *
 * Am 2026-08-31 aus `CustomerDetail.jsx` herausgeloest — 283 Zeilen, der
 * groesste der drei.
 */
import API_BASE_URL from '../../config';
import toast from 'react-hot-toast';
import { loadJson } from '../../utils/apiRequest';
import { aufTaste } from '../../utils/tastaturBedienung';

export default function ReiterMarkendesign({
  customerId,
  token,
  isMobile,
  analyzing,
  brandData,
  brandLoaded,
  h,
  leadId,
  scanResults,
  scanRunning,
  scanStep,
  scraping,
  setAnalyzing,
  setBrandData,
  setBrandLoaded,
  setScanResults,
  setScanRunning,
  setScanStep,
  setScraping,
}) {

  const lid = leadId || customerId;
  const loadBrandData = () => {
    loadJson(`${API_BASE_URL}/api/branddesign/${lid}`, { headers: h }, { context: 'Markendesign' })
      .then(d => { if (d) setBrandData(d); });
  };

  if (!brandLoaded && lid) {
    setBrandLoaded(true);
    loadBrandData();
  }

  const scrapeWebsite = async () => {
    setScraping(true);
    try {
      await fetch(`${API_BASE_URL}/api/branddesign/${lid}/scrape`, { method: 'POST', headers: h });
      loadBrandData();
    } catch { toast.error('Scraping fehlgeschlagen'); }
    finally { setScraping(false); }
  };

  const analyzeScreenshot = async () => {
    setAnalyzing(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/branddesign/${lid}/analyze-screenshot`, { method: 'POST', headers: h });
      if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.detail || 'Fehler'); }
      const d = await res.json(); setBrandData(prev => ({ ...prev, ...d }));
      toast.success('Screenshot analysiert!');
    } catch (e) { toast.error(e.message || 'Analyse fehlgeschlagen'); }
    finally { setAnalyzing(false); }
  };

  const uploadPdf = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);
    try {
      const res = await fetch(`${API_BASE_URL}/api/branddesign/${lid}/upload-pdf`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });
      if (!res.ok) throw new Error('Upload fehlgeschlagen');
      toast.success('PDF hochgeladen!');
      loadBrandData();
    } catch (e) { toast.error(e.message); }
  };

  const downloadPdf = async () => {
    const res = await fetch(`${API_BASE_URL}/api/branddesign/${lid}/pdf`, { headers: h });
    if (!res.ok) { toast.error('PDF nicht verfügbar'); return; }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = brandData?.pdf_filename || 'brand.pdf'; a.click();
    URL.revokeObjectURL(url);
  };

  const primaryBtn = { padding: '9px 16px', background: 'var(--brand-primary)', color: 'var(--text-on-brand)', border: 'none', borderRadius: 'var(--radius-md)', fontSize: 13, fontWeight: 600, cursor: 'pointer', fontFamily: 'var(--font-sans)' };
  const secondaryBtn = { padding: '9px 16px', background: 'var(--bg-surface)', color: 'var(--text-primary)', border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)', fontSize: 13, fontWeight: 500, cursor: 'pointer', fontFamily: 'var(--font-sans)', display: 'inline-flex', alignItems: 'center', gap: 6 };
  const sectionLabel = { fontSize: 11, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 10 };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

      {/* Status banner */}
      <div style={{ padding: '10px 14px', borderRadius: 'var(--radius-md)', fontSize: 13,
        background: brandData?.scraped_at ? '#dcfce7' : brandData?.scrape_failed ? '#fff7ed' : 'var(--bg-elevated)',
        color:      brandData?.scraped_at ? '#166534'  : brandData?.scrape_failed ? '#92400e'  : 'var(--text-tertiary)',
        border: `1px solid ${brandData?.scraped_at ? '#86efac' : brandData?.scrape_failed ? '#fcd34d' : 'var(--border-light)'}`,
      }}>
        {brandData?.scraped_at
          ? `✅ Branddesign erfasst · ${brandData.scraped_at}`
          : brandData?.scrape_failed
            ? '⚠️ Website konnte nicht gescrapt werden — Screenshot-Analyse verfügbar'
            : 'Noch kein Branddesign erfasst'}
      </div>

      {/* Action buttons */}
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        <button onClick={scrapeWebsite} disabled={scraping} style={primaryBtn}>
          {scraping ? '⏳ Wird gescrapt…' : '🌐 Website scrapen'}
        </button>
        <button onClick={analyzeScreenshot} disabled={analyzing} style={secondaryBtn}>
          {analyzing ? '⏳ KI analysiert…' : '🤖 Screenshot analysieren'}
        </button>
        <label style={{ ...secondaryBtn, cursor: 'pointer' }}>
          📄 PDF hochladen
          <input type="file" accept=".pdf" onChange={uploadPdf} style={{ display: 'none' }} />
        </label>
      </div>

      {/* Alles scannen — sequential carousel */}
      {(() => {
        const SCAN_STEPS = [
          { key: 'scrape',    label: 'Brand Scrape',    icon: '🌐', endpoint: () => fetch(`${API_BASE_URL}/api/branddesign/${lid}/scrape`, { method: 'POST', headers: h }).then(r => { if (r.ok) return r.json(); throw new Error(); }) },
          { key: 'fonts',     label: 'Font-Recherche',  icon: '🔤', endpoint: () => fetch(`${API_BASE_URL}/api/branddesign/${lid}/suggest-fonts`, { method: 'POST', headers: h }).then(r => { if (r.ok) return r.json(); throw new Error(); }) },
          { key: 'crawler',   label: 'Website-Crawler', icon: '🕷️', endpoint: async () => {
            await fetch(`${API_BASE_URL}/api/crawler/start/${lid}`, { method: 'POST', headers: h });
            for (let i = 0; i < 30; i++) {
              await new Promise(r => setTimeout(r, 2000));
              const s = await fetch(`${API_BASE_URL}/api/crawler/status/${lid}`, { headers: h }).then(r => r.json());
              if (s.status === 'completed' || s.status === 'done') return s;
              if (s.status === 'failed' || s.status === 'error') throw new Error('Crawler failed');
            }
            return { status: 'timeout' };
          }},
          { key: 'pagespeed', label: 'PageSpeed',       icon: '⚡', endpoint: () => fetch(`${API_BASE_URL}/api/leads/${lid}/pagespeed`, { method: 'POST', headers: h }).then(r => { if (r.ok) return r.json(); throw new Error(); }) },
        ];

        const runAllScans = async () => {
          setScanRunning(true);
          setScanResults([]);
          for (let i = 0; i < SCAN_STEPS.length; i++) {
            setScanStep(i);
            try {
              const result = await SCAN_STEPS[i].endpoint();
              setScanResults(prev => [...prev, { key: SCAN_STEPS[i].key, ok: true, data: result }]);
              if (SCAN_STEPS[i].key === 'scrape' && result) setBrandData(result);
            } catch {
              setScanResults(prev => [...prev, { key: SCAN_STEPS[i].key, ok: false }]);
            }
          }
          setScanStep(-1);
          setScanRunning(false);
          toast.success('Alle Scans abgeschlossen');
          loadBrandData();
        };

        return (
          <div style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)', padding: '14px 16px', overflow: 'hidden' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: scanRunning || scanResults.length > 0 ? 14 : 0 }}>
              <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)' }}>Komplett-Scan</div>
              <button onClick={runAllScans} disabled={scanRunning} style={{
                padding: '7px 16px', fontSize: 12, fontWeight: 700,
                background: scanRunning ? 'var(--border-medium)' : 'linear-gradient(135deg, #008EAA 0%, #006B80 100%)',
                color: '#fff', border: 'none', borderRadius: 'var(--radius-md)',
                cursor: scanRunning ? 'not-allowed' : 'pointer', fontFamily: 'var(--font-sans)',
                display: 'flex', alignItems: 'center', gap: 6,
              }}>
                {scanRunning ? '⏳ Läuft…' : '🚀 Alles scannen'}
              </button>
            </div>

            {(scanRunning || scanResults.length > 0) && (
              <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                {SCAN_STEPS.map((step, i) => {
                  const result = scanResults.find(r => r.key === step.key);
                  const isActive = scanRunning && scanStep === i;
                  const isDone = !!result;
                  const isFailed = result && !result.ok;
                  const isPending = !isDone && !isActive;
                  return (
                    <div key={step.key} style={{
                      flex: '1 1 0', minWidth: isMobile ? '45%' : 120,
                      padding: '10px 12px', borderRadius: 'var(--radius-md)',
                      border: `2px solid ${isActive ? 'var(--kc-mid)' : isDone ? (isFailed ? '#e74c3c' : '#3B6D11') : 'var(--border-light)'}`,
                      background: isActive ? '#E6F6FA' : isDone ? (isFailed ? '#FEF2F2' : '#EAF4E0') : 'var(--bg-surface)',
                      transition: 'all 0.3s ease',
                      opacity: isPending && scanRunning ? 0.5 : 1,
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
                        <span style={{ fontSize: 16 }}>{isDone ? (isFailed ? '❌' : '✅') : isActive ? '⏳' : step.icon}</span>
                        <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)' }}>{step.label}</span>
                      </div>
                      {isActive && (
                        <div style={{ height: 3, borderRadius: 2, background: 'var(--border-light)', overflow: 'hidden' }}>
                          <div style={{
                            height: '100%', width: '60%', borderRadius: 2,
                            background: 'var(--kc-mid)',
                            animation: 'scanPulse 1.2s ease-in-out infinite alternate',
                          }} />
                        </div>
                      )}
                      {isDone && !isFailed && <div style={{ fontSize: 10, color: '#3B6D11', marginTop: 2 }}>Fertig</div>}
                      {isFailed && <div style={{ fontSize: 10, color: '#e74c3c', marginTop: 2 }}>Fehlgeschlagen</div>}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        );
      })()}

      {/* Color palette */}
      {brandData?.primary_color && (
        <div>
          <div style={sectionLabel}>Farben</div>
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 12 }}>
            {[
              { label: 'Primär',       color: brandData.primary_color },
              { label: 'Sekundär',     color: brandData.secondary_color },
              { label: 'Akzent',       color: brandData.accent_color },
              { label: 'Hintergrund',  color: brandData.background_color },
              { label: 'Text',         color: brandData.text_color },
            ].filter(c => c.color).map(({ label, color }) => (
              <div key={label} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6 }}>
                <div role="button" tabIndex={0} onKeyDown={aufTaste(() => { navigator.clipboard.writeText(color); toast.success(color + ' kopiert!'); })}
                  style={{ width: 52, height: 52, borderRadius: 8, background: color, border: '1px solid var(--border-light)', cursor: 'pointer' }}
                  onClick={() => { navigator.clipboard.writeText(color); toast.success(color + ' kopiert!'); }}
                />
                <div style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>{label}</div>
                <div style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-primary)' }}>{color}</div>
              </div>
            ))}
          </div>
          {brandData.all_colors?.length > 0 && (
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
              {brandData.all_colors.map((c, i) => {
                const hex = c.startsWith('#') ? c : '#' + c;
                return (
                  <div role="button" tabIndex={0} onKeyDown={aufTaste(() => navigator.clipboard.writeText(hex))} key={i} style={{ width: 24, height: 24, borderRadius: 4, background: hex, border: '1px solid var(--border-light)', cursor: 'pointer' }}
                    onClick={() => navigator.clipboard.writeText(hex)} title={hex} />
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Fonts */}
      {(brandData?.font_primary || brandData?.font_secondary) && (
        <div>
          <div style={sectionLabel}>Schriften</div>
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
            {brandData.font_primary && (
              <div style={{ background: 'var(--bg-elevated)', padding: '10px 14px', borderRadius: 8, border: '1px solid var(--border-light)' }}>
                <div style={{ fontSize: 10, color: 'var(--text-tertiary)', marginBottom: 4 }}>Primär</div>
                <div style={{ fontSize: 15, fontFamily: brandData.font_primary }}>{brandData.font_primary}</div>
              </div>
            )}
            {brandData.font_secondary && (
              <div style={{ background: 'var(--bg-elevated)', padding: '10px 14px', borderRadius: 8, border: '1px solid var(--border-light)' }}>
                <div style={{ fontSize: 10, color: 'var(--text-tertiary)', marginBottom: 4 }}>Sekundär</div>
                <div style={{ fontSize: 15, fontFamily: brandData.font_secondary }}>{brandData.font_secondary}</div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Design style + notes */}
      {brandData?.design_style && (
        <div>
          <div style={sectionLabel}>Designstil</div>
          <div style={{ display: 'flex', gap: 8, marginBottom: 10 }}>
            <span style={{ background: 'var(--bg-elevated)', padding: '4px 10px', borderRadius: 20, fontSize: 12, border: '1px solid var(--border-light)' }}>
              {brandData.design_style}
            </span>
            {brandData.font_style && (
              <span style={{ background: 'var(--bg-elevated)', padding: '4px 10px', borderRadius: 20, fontSize: 12, border: '1px solid var(--border-light)' }}>
                {brandData.font_style}
              </span>
            )}
          </div>
          {brandData.brand_notes && (
            <div style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6, background: 'var(--bg-elevated)', padding: 12, borderRadius: 8, border: '1px solid var(--border-light)' }}>
              {brandData.brand_notes}
            </div>
          )}
        </div>
      )}

      {/* PDF section */}
      {brandData?.pdf_filename && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 14px', background: 'var(--bg-elevated)', border: '1px solid var(--border-light)', borderRadius: 8 }}>
          <span style={{ fontSize: 20 }}>📄</span>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: 13, fontWeight: 500 }}>{brandData.pdf_filename}</div>
            <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>Branddesign-Dokument</div>
          </div>
          <button onClick={downloadPdf} style={{ fontSize: 12, padding: '5px 10px', background: 'var(--brand-primary)', color: 'var(--text-on-brand)', border: 'none', borderRadius: 6, cursor: 'pointer' }}>
            ⬇ Download
          </button>
        </div>
      )}

    </div>
  );
}

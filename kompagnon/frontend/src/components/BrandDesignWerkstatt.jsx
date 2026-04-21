import { useState, useEffect } from 'react';
import API_BASE_URL from '../config';
import BrandDesignEditor from './BrandDesignEditor';

export default function BrandDesignWerkstatt({ project, leadId, token, brandData: initialBrandData, onSaved }) {
  const [scanning,  setScanning]  = useState(false);
  const [brandData, setBrandData] = useState(initialBrandData || null);
  const [scanError, setScanError] = useState(null);
  const [scanDone,  setScanDone]  = useState(false);

  useEffect(() => {
    setBrandData(initialBrandData);
    if (initialBrandData?.primary_color) setScanDone(true);
  }, [initialBrandData]);

  const websiteUrl = project?.website_url;
  const headers = { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' };

  const runScan = async () => {
    if (!leadId || !websiteUrl) return;
    setScanning(true);
    setScanError(null);
    try {
      const res = await fetch(`${API_BASE_URL}/api/branddesign/${leadId}/scrape`, {
        method: 'POST', headers,
      });
      if (!res.ok) throw new Error(`Brand-Scan fehlgeschlagen (HTTP ${res.status})`);
      const data = await res.json();
      setBrandData(data);
      setScanDone(true);
      if (onSaved) onSaved(data);
    } catch (err) {
      setScanError(err.message);
    } finally {
      setScanning(false);
    }
  };

  const detectedColors = brandData?.all_colors || [];
  const detectedFonts  = [
    ...(brandData?.fonts_detail?.google_fonts || []),
    brandData?.font_heading, brandData?.font_body,
    brandData?.font_primary, brandData?.font_secondary,
    ...(brandData?.all_fonts || []),
  ].filter(Boolean).filter((v, i, a) => a.indexOf(v) === i);

  return (
    <div>
      {/* Scan-Section */}
      <div style={{
        padding: '14px 24px',
        borderBottom: '1px solid var(--border-light)',
        background: scanDone ? 'var(--bg-app)' : 'var(--info-bg, #E0F4F8)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16, flexWrap: 'wrap' }}>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 2 }}>
              {scanDone ? 'Brand gescannt — jetzt anpassen' : 'Brand von Website scannen'}
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-tertiary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {websiteUrl || 'Keine URL hinterlegt'} &mdash; Farben, Schriften &amp; Stil werden erkannt
            </div>
          </div>

          {/* Scan-Ergebnis-Preview */}
          {scanDone && brandData && (
            <div style={{ display: 'flex', gap: 5, alignItems: 'center', flexShrink: 0 }}>
              {[brandData.primary_color, brandData.secondary_color].filter(Boolean).map((c, i) => (
                <div key={i} title={c} style={{ width: 22, height: 22, borderRadius: 5, background: c, border: '1px solid var(--border-light)' }} />
              ))}
              {detectedColors.length > 2 && (
                detectedColors.slice(2, 6).map((c, i) => (
                  <div key={i} title={c} style={{ width: 16, height: 16, borderRadius: 4, background: c, border: '1px solid var(--border-light)' }} />
                ))
              )}
              {detectedFonts.length > 0 && (
                <span style={{ fontSize: 10, fontWeight: 700, color: '#00875A', background: '#E3F6EF', padding: '2px 7px', borderRadius: 4, marginLeft: 4 }}>
                  {detectedFonts.length} Fonts
                </span>
              )}
            </div>
          )}

          <button
            onClick={runScan}
            disabled={scanning || !websiteUrl}
            style={{
              padding: '9px 20px', borderRadius: 8, border: 'none',
              cursor: scanning || !websiteUrl ? 'not-allowed' : 'pointer',
              background: scanning ? 'var(--border-medium)' : scanDone ? 'var(--bg-surface)' : 'var(--kc-dark, #004F59)',
              border: scanDone ? '1px solid var(--border-light)' : 'none',
              color: scanDone ? 'var(--text-secondary)' : '#fff',
              fontSize: 12, fontWeight: 700, fontFamily: 'var(--font-sans)',
              display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0,
            }}
          >
            {scanning ? (
              <>
                <span style={{ width: 12, height: 12, border: '2px solid rgba(0,0,0,.2)', borderTopColor: 'var(--brand-primary)', borderRadius: '50%', animation: 'spin .8s linear infinite', display: 'inline-block' }} />
                Scannt&hellip;
              </>
            ) : scanDone ? 'Neu scannen' : '🎨 Brand scannen'}
          </button>
        </div>

        {scanError && (
          <div style={{ marginTop: 10, fontSize: 11, color: '#C0392B', background: '#FDEAEA', border: '1px solid rgba(192,57,43,.3)', borderRadius: 6, padding: '6px 10px' }}>
            {scanError}
          </div>
        )}

        {!scanDone && !scanning && (
          <div style={{ marginTop: 10, fontSize: 11, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
            Scannt automatisch: Primär- &amp; Sekundärfarben, erkannte Fonts, Designstil (Radius, Schatten).
            Danach kannst du alles manuell anpassen.
          </div>
        )}
      </div>

      {/* BrandDesignEditor eingebettet */}
      <div style={{ padding: '20px 24px' }}>
        <BrandDesignEditor
          leadId={leadId}
          token={token}
          brandData={brandData}
          onSaved={onSaved}
        />
      </div>
    </div>
  );
}

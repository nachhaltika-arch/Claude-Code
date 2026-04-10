import { useState, useEffect } from 'react';
import API_BASE_URL from '../config';
import toast from 'react-hot-toast';

// ── Pipeline-Schritte ────────────────────────────────────────────────────────

function buildSteps(projectId, leadId, websiteUrl, headers) {
  return [
    {
      id: 'url-crawl',
      label: 'URL-Crawler',
      icon: '🕷️',
      desc: 'Alle Seiten der Website erfassen',
      run: async (setProgress) => {
        const start = await fetch(
          `${API_BASE_URL}/api/crawler/start/${leadId}`,
          { method: 'POST', headers: { ...headers, 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: websiteUrl, max_pages: 50 }) }
        );
        if (!start.ok) throw new Error('Crawler konnte nicht gestartet werden');

        // Poll until done (max 3 min)
        const deadline = Date.now() + 180_000;
        while (Date.now() < deadline) {
          await new Promise(r => setTimeout(r, 2500));
          const status = await fetch(
            `${API_BASE_URL}/api/crawler/status/${leadId}`,
            { headers }
          ).then(r => r.json()).catch(() => ({}));
          const pct = status.total_urls
            ? Math.min(90, Math.round((status.total_urls / 50) * 90))
            : 30;
          setProgress(pct);
          if (status.status === 'completed') { setProgress(100); break; }
          if (status.status === 'failed') throw new Error('Crawler fehlgeschlagen');
        }

        const results = await fetch(
          `${API_BASE_URL}/api/crawler/results/${leadId}`,
          { headers }
        ).then(r => r.ok ? r.json() : {});
        return { urls: results.results?.length || 0 };
      },
    },
    {
      id: 'content-scrape',
      label: 'Website-Content',
      icon: '📄',
      desc: 'Texte, Assets, Links & SEO-Daten je Seite',
      run: async (setProgress) => {
        setProgress(10);
        const res = await fetch(
          `${API_BASE_URL}/api/crawler/scrape-content/${leadId}`,
          { method: 'POST', headers }
        );
        if (!res.ok) throw new Error('Content-Scraping fehlgeschlagen');
        setProgress(60);
        const data = await res.json();
        setProgress(100);
        return { pages: data.scraped || 0 };
      },
    },
    {
      id: 'hosting',
      label: 'Hosting-Analyse',
      icon: '🖥️',
      desc: 'Provider, DNS, WHOIS, WordPress-Erkennung',
      run: async (setProgress) => {
        setProgress(20);
        const res = await fetch(
          `${API_BASE_URL}/api/projects/${projectId}/hosting-scan`,
          { method: 'POST', headers }
        );
        setProgress(100);
        if (!res.ok) throw new Error('Hosting-Scan fehlgeschlagen');
        const data = await res.json();
        return { provider: data.hosting_provider || '—' };
      },
    },
    {
      id: 'pagespeed',
      label: 'PageSpeed',
      icon: '⚡',
      desc: 'Core Web Vitals, Mobil & Desktop Score',
      run: async (setProgress) => {
        setProgress(15);
        const res = await fetch(
          `${API_BASE_URL}/api/leads/${leadId}/pagespeed`,
          { method: 'POST', headers }
        );
        setProgress(100);
        if (!res.ok) throw new Error('PageSpeed-Messung fehlgeschlagen');
        const data = await res.json();
        return { mobile: data.mobile_score, desktop: data.desktop_score };
      },
    },
    {
      id: 'analytics',
      label: 'Google Analytics',
      icon: '📊',
      desc: 'GA4-Tag, GTM und Tracking-Pixel erkennen',
      run: async (setProgress) => {
        setProgress(20);
        const content = await fetch(
          `${API_BASE_URL}/api/crawler/content/${leadId}`,
          { headers }
        ).then(r => r.ok ? r.json() : []).catch(() => []);
        setProgress(70);
        const GA_PATTERNS = ['gtag/js', 'google-analytics', 'googletagmanager', 'ga4', 'gtm.js'];
        let found = false;
        for (const page of content) {
          const text = (page.full_text || '') + (page.url || '');
          if (GA_PATTERNS.some(p => text.toLowerCase().includes(p))) {
            found = true; break;
          }
        }
        setProgress(100);
        return { ga_found: found };
      },
    },
    {
      id: 'brand',
      label: 'Brand Design',
      icon: '🎨',
      desc: 'Farben, Schriften & Logo von Website',
      run: async (setProgress) => {
        setProgress(20);
        const res = await fetch(
          `${API_BASE_URL}/api/branddesign/${leadId}/scrape`,
          { method: 'POST', headers }
        );
        setProgress(80);
        if (!res.ok) throw new Error('Brand-Scraping fehlgeschlagen');
        const data = await res.json();
        setProgress(100);
        return {
          primary: data.primary_color,
          fonts: data.all_fonts?.length || 0,
        };
      },
    },
  ];
}

// Shared badge style
const badge = {
  fontSize: 10, fontWeight: 600,
  background: 'var(--bg-app)', color: 'var(--text-secondary)',
  border: '1px solid var(--border-light)',
  borderRadius: 4, padding: '2px 6px',
};

// ── Haupt-Komponente ─────────────────────────────────────────────────────────

export default function AnalyseCentrale({ projectId, leadId, websiteUrl, token }) {
  const headers = token ? { Authorization: `Bearer ${token}` } : {};

  const [running, setRunning]         = useState(false);
  const [currentStep, setCurrentStep] = useState(-1);
  const [stepProgress, setStepProgress] = useState(0);
  const [stepResults, setStepResults] = useState({});
  const [stepErrors, setStepErrors]   = useState({});
  const [pages, setPages]             = useState([]);
  const [pagesLoading, setPagesLoading] = useState(false);
  const [hostingData, setHostingData] = useState(null);
  const [expanded, setExpanded]       = useState(null);

  const steps = buildSteps(projectId, leadId, websiteUrl, headers);

  useEffect(() => {
    if (!leadId) return;
    loadResults();
  }, [leadId]); // eslint-disable-line

  const loadResults = async () => {
    setPagesLoading(true);
    try {
      const [contentRes, hostingRes] = await Promise.allSettled([
        fetch(`${API_BASE_URL}/api/crawler/content/${leadId}`, { headers }).then(r => r.ok ? r.json() : []),
        fetch(`${API_BASE_URL}/api/projects/${projectId}/hosting-info`, { headers }).then(r => r.ok ? r.json() : null),
      ]);
      if (contentRes.status === 'fulfilled') setPages(contentRes.value || []);
      if (hostingRes.status === 'fulfilled') setHostingData(hostingRes.value);
    } catch { /* silent */ }
    finally { setPagesLoading(false); }
  };

  const runPipeline = async () => {
    if (!websiteUrl) { toast.error('Keine Website-URL im Projekt'); return; }
    setRunning(true);
    setStepResults({});
    setStepErrors({});

    for (let i = 0; i < steps.length; i++) {
      const step = steps[i];
      setCurrentStep(i);
      setStepProgress(0);
      try {
        const result = await step.run((pct) => setStepProgress(pct));
        setStepResults(prev => ({ ...prev, [step.id]: result }));
      } catch (err) {
        setStepErrors(prev => ({ ...prev, [step.id]: err.message }));
      }
    }

    setCurrentStep(-1);
    setRunning(false);
    await loadResults();
    toast.success('Alle Analysen abgeschlossen!');
  };

  // ── Gesamtfortschritt ────────────────────────────────────────────────────
  const doneCount  = Object.keys(stepResults).length + Object.keys(stepErrors).length;
  const totalPct   = running
    ? Math.round(((doneCount / steps.length) + (stepProgress / 100 / steps.length)) * 100)
    : doneCount === steps.length ? 100 : 0;

  // ── Render ───────────────────────────────────────────────────────────────
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

      {/* ── Header + Start-Button ── */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 16, flexWrap: 'wrap' }}>
        <div>
          <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 4 }}>
            Analyse-Zentrale
          </div>
          <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
            {websiteUrl || 'Keine URL hinterlegt'}
          </div>
        </div>
        <button
          onClick={runPipeline}
          disabled={running || !websiteUrl}
          style={{
            padding: '11px 24px', borderRadius: 8, border: 'none',
            background: running || !websiteUrl
              ? 'var(--border-medium)'
              : 'linear-gradient(135deg, #008EAA, #006680)',
            color: 'white', fontSize: 13, fontWeight: 700,
            cursor: running || !websiteUrl ? 'not-allowed' : 'pointer',
            display: 'flex', alignItems: 'center', gap: 8,
            boxShadow: running ? 'none' : '0 2px 10px rgba(0,142,170,0.35)',
            fontFamily: 'var(--font-sans)',
          }}
        >
          {running ? (
            <><span style={{ width: 14, height: 14, border: '2px solid rgba(255,255,255,.3)', borderTopColor: '#fff', borderRadius: '50%', animation: 'spin .8s linear infinite', display: 'inline-block' }} />Analysiert...</>
          ) : 'Alle Analysen starten'}
        </button>
      </div>

      {/* ── Gesamt-Fortschrittsbalken ── */}
      {(running || doneCount > 0) && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: 'var(--text-tertiary)', marginBottom: 6 }}>
            <span>{running ? `Schritt ${doneCount + 1} von ${steps.length}` : `${doneCount} von ${steps.length} Schritten abgeschlossen`}</span>
            <span>{totalPct}%</span>
          </div>
          <div style={{ height: 8, background: 'var(--border-light)', borderRadius: 4, overflow: 'hidden' }}>
            <div style={{
              height: '100%',
              width: `${totalPct}%`,
              background: 'linear-gradient(90deg, #008EAA, #00B4D8)',
              borderRadius: 4,
              transition: 'width 0.4s ease',
            }} />
          </div>
        </div>
      )}

      {/* ── Schritt-Kacheln ── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 10 }}>
        {steps.map((step, i) => {
          const isDone    = step.id in stepResults;
          const hasError  = step.id in stepErrors;
          const isActive  = currentStep === i;
          const result    = stepResults[step.id];
          const error     = stepErrors[step.id];

          return (
            <div key={step.id} style={{
              borderRadius: 10, padding: '14px 16px',
              border: `1px solid ${isActive ? 'var(--brand-primary-mid, #008EAA)' : isDone ? 'var(--status-success-text)' : hasError ? 'var(--status-danger-text)' : 'var(--border-light)'}`,
              background: isActive ? 'var(--brand-primary-light, #E6F6FA)' : isDone ? 'var(--status-success-bg)' : hasError ? 'var(--status-danger-bg)' : 'var(--bg-surface)',
              transition: 'all 0.3s',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                <span style={{ fontSize: 18 }}>{step.icon}</span>
                <span style={{ fontSize: 12, fontWeight: 700, color: isActive ? 'var(--brand-primary-dark, #006680)' : isDone ? 'var(--status-success-text)' : hasError ? 'var(--status-danger-text)' : 'var(--text-primary)' }}>
                  {step.label}
                </span>
                {isActive && <span style={{ marginLeft: 'auto', width: 12, height: 12, border: '2px solid var(--brand-primary, #008EAA)', borderTopColor: 'transparent', borderRadius: '50%', animation: 'spin .7s linear infinite', display: 'inline-block', flexShrink: 0 }} />}
                {isDone && <span style={{ marginLeft: 'auto', fontSize: 14, color: 'var(--status-success-text)' }}>&#10003;</span>}
                {hasError && <span style={{ marginLeft: 'auto', fontSize: 14, color: 'var(--status-danger-text)' }}>&#10007;</span>}
              </div>

              {isActive && (
                <div style={{ height: 4, background: 'var(--brand-primary-light, #E6F6FA)', borderRadius: 2, overflow: 'hidden', marginBottom: 6 }}>
                  <div style={{ height: '100%', width: `${stepProgress}%`, background: 'var(--brand-primary, #008EAA)', borderRadius: 2, transition: 'width 0.4s' }} />
                </div>
              )}

              <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>{step.desc}</div>

              {isDone && result && (
                <div style={{ marginTop: 8, fontSize: 11, color: 'var(--status-success-text)', fontWeight: 600 }}>
                  {step.id === 'url-crawl'      && `${result.urls} URLs gefunden`}
                  {step.id === 'content-scrape'  && `${result.pages} Seiten gescrapt`}
                  {step.id === 'hosting'         && result.provider}
                  {step.id === 'pagespeed'       && `Mobil: ${result.mobile ?? '—'} / Desktop: ${result.desktop ?? '—'}`}
                  {step.id === 'analytics'       && (result.ga_found ? 'GA4 erkannt' : 'Kein GA4 gefunden')}
                  {step.id === 'brand'           && `${result.primary || '—'} / ${result.fonts} Schriften`}
                </div>
              )}
              {hasError && (
                <div style={{ marginTop: 6, fontSize: 10, color: 'var(--status-danger-text)' }}>{error}</div>
              )}
            </div>
          );
        })}
      </div>

      {/* ── Seiten-Board ── */}
      {pages.length > 0 && (
        <div>
          <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 12 }}>
            Seiten-Board — {pages.length} Seiten analysiert
          </div>

          <div style={{
            display: 'flex', gap: 12, overflowX: 'auto',
            paddingBottom: 12,
            scrollbarWidth: 'thin',
            WebkitOverflowScrolling: 'touch',
          }}>
            {pages.map((page, i) => {
              const isExpanded = expanded === i;
              const h2s = Array.isArray(page.h2s) ? page.h2s : [];
              const imgs = Array.isArray(page.images) ? page.images : [];
              const path = (() => { try { return new URL(page.url).pathname || '/'; } catch { return page.url; } })();

              return (
                <div
                  key={i}
                  onClick={() => setExpanded(isExpanded ? null : i)}
                  style={{
                    flexShrink: 0,
                    width: isExpanded ? 380 : 220,
                    borderRadius: 12,
                    border: `1px solid ${isExpanded ? 'var(--brand-primary-mid, #008EAA)' : 'var(--border-light)'}`,
                    background: 'var(--bg-surface)',
                    padding: 14,
                    cursor: 'pointer',
                    transition: 'all 0.25s',
                    boxShadow: isExpanded ? '0 4px 16px rgba(0,142,170,0.12)' : '0 1px 4px rgba(0,0,0,0.06)',
                  }}
                >
                  <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--brand-primary)', marginBottom: 4, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {path}
                  </div>
                  <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 8, lineHeight: 1.4, overflow: 'hidden', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical' }}>
                    {page.h1 || page.title || '(kein Titel)'}
                  </div>

                  <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap', marginBottom: 8 }}>
                    {page.word_count > 0 && (
                      <span style={badge}>{page.word_count} W</span>
                    )}
                    {imgs.length > 0 && (
                      <span style={badge}>{imgs.length} Img</span>
                    )}
                    {h2s.length > 0 && (
                      <span style={badge}>H2: {h2s.length}</span>
                    )}
                  </div>

                  {page.meta_description && (
                    <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginBottom: 8, lineHeight: 1.5, overflow: 'hidden', display: '-webkit-box', WebkitLineClamp: isExpanded ? 4 : 2, WebkitBoxOrient: 'vertical' }}>
                      {page.meta_description}
                    </div>
                  )}

                  {isExpanded && (
                    <>
                      {h2s.length > 0 && (
                        <div style={{ marginBottom: 10 }}>
                          <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.06em', marginBottom: 4 }}>H2-Headings</div>
                          {h2s.slice(0, 5).map((h, j) => (
                            <div key={j} style={{ fontSize: 11, color: 'var(--text-secondary)', padding: '2px 0', borderLeft: '2px solid var(--border-light)', paddingLeft: 8, marginBottom: 3 }}>{h}</div>
                          ))}
                        </div>
                      )}

                      {page.text_preview && (
                        <div style={{ marginBottom: 10 }}>
                          <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.06em', marginBottom: 4 }}>Text-Vorschau</div>
                          <div style={{ fontSize: 11, color: 'var(--text-secondary)', lineHeight: 1.6 }}>{page.text_preview.slice(0, 200)}...</div>
                        </div>
                      )}

                      <a href={page.url} target="_blank" rel="noreferrer" onClick={e => e.stopPropagation()} style={{ fontSize: 11, color: 'var(--brand-primary)', textDecoration: 'none' }}>
                        Seite oeffnen
                      </a>
                    </>
                  )}
                </div>
              );
            })}
          </div>
          <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 4 }}>
            Karte anklicken fuer Details. Horizontal scrollen fuer alle Seiten.
          </div>
        </div>
      )}

      {pagesLoading && (
        <div style={{ display: 'flex', justifyContent: 'center', padding: '24px 0' }}>
          <div style={{ width: 24, height: 24, borderRadius: '50%', border: '2px solid var(--border-light)', borderTopColor: 'var(--brand-primary, #008EAA)', animation: 'spin 0.8s linear infinite' }} />
        </div>
      )}

      {!running && !pagesLoading && pages.length === 0 && (
        <div style={{ textAlign: 'center', padding: '48px 20px', color: 'var(--text-tertiary)', fontSize: 13 }}>
          <div style={{ fontSize: 36, marginBottom: 12 }}>🔬</div>
          <div style={{ fontWeight: 600, marginBottom: 6 }}>Noch keine Analyse gestartet</div>
          <div>Alle Analysen starten um Daten zu erfassen.</div>
        </div>
      )}
    </div>
  );
}

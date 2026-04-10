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
  const [selectedPage, setSelectedPage] = useState(null);
  const [search, setSearch]             = useState('');
  const [sortBy, setSortBy]             = useState('url');
  const [showFullText, setShowFullText] = useState(false);

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
      if (contentRes.status === 'fulfilled') {
        setPages(contentRes.value || []);
        if (contentRes.value?.length > 0 && !selectedPage) {
          setSelectedPage(contentRes.value[0]);
        }
      }
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

      {/* ── Seiten-Board (Master-Detail) ── */}
      {pages.length > 0 && (
        <div>
          {/* Board-Header */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12, flexWrap: 'wrap' }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)' }}>
              {pages.length} Seiten analysiert
            </div>
            <input
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="URL oder Titel suchen..."
              style={{
                flex: 1, minWidth: 180, padding: '6px 10px', fontSize: 12,
                border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)',
                background: 'var(--bg-app)', color: 'var(--text-primary)',
                fontFamily: 'var(--font-sans)', outline: 'none',
              }}
            />
            <select
              value={sortBy}
              onChange={e => setSortBy(e.target.value)}
              style={{
                padding: '6px 10px', fontSize: 12,
                border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)',
                background: 'var(--bg-app)', color: 'var(--text-primary)',
                fontFamily: 'var(--font-sans)', cursor: 'pointer',
              }}
            >
              <option value="url">Sortieren: URL</option>
              <option value="words">Sortieren: Woerter</option>
              <option value="images">Sortieren: Bilder</option>
            </select>
          </div>

          {/* Master-Detail Split */}
          {(() => {
            const filtered = pages
              .filter(p => !search || p.url?.toLowerCase().includes(search.toLowerCase()) || p.title?.toLowerCase().includes(search.toLowerCase()) || p.h1?.toLowerCase().includes(search.toLowerCase()))
              .sort((a, b) => {
                if (sortBy === 'words')  return (b.word_count || 0) - (a.word_count || 0);
                if (sortBy === 'images') return ((Array.isArray(b.images) ? b.images.length : 0)) - ((Array.isArray(a.images) ? a.images.length : 0));
                return (a.url || '').localeCompare(b.url || '');
              });

            const sel = selectedPage;

            return (
              <div style={{
                display: 'grid',
                gridTemplateColumns: '280px 1fr',
                gap: 0,
                border: '1px solid var(--border-light)',
                borderRadius: 'var(--radius-lg)',
                overflow: 'hidden',
                minHeight: 480,
                maxHeight: 680,
              }}>

                {/* LINKE LISTE */}
                <div style={{
                  borderRight: '1px solid var(--border-light)',
                  overflowY: 'auto',
                  background: 'var(--bg-app)',
                }}>
                  {filtered.length === 0 ? (
                    <div style={{ padding: 20, fontSize: 12, color: 'var(--text-tertiary)', textAlign: 'center' }}>
                      Keine Seiten gefunden
                    </div>
                  ) : filtered.map((page, i) => {
                    const isSelected = sel?.url === page.url;
                    const imgCount   = Array.isArray(page.images) ? page.images.length : 0;
                    let path = page.url;
                    try { path = new URL(page.url).pathname || '/'; } catch { /* keep */ }

                    return (
                      <div
                        key={i}
                        onClick={() => { setSelectedPage(page); setShowFullText(false); }}
                        style={{
                          padding: '10px 14px',
                          borderBottom: '1px solid var(--border-light)',
                          cursor: 'pointer',
                          background: isSelected ? 'var(--bg-active, var(--bg-elevated))' : 'transparent',
                          borderLeft: `3px solid ${isSelected ? 'var(--brand-primary)' : 'transparent'}`,
                          transition: 'background 0.12s',
                        }}
                        onMouseEnter={e => { if (!isSelected) e.currentTarget.style.background = 'var(--bg-elevated)'; }}
                        onMouseLeave={e => { if (!isSelected) e.currentTarget.style.background = 'transparent'; }}
                      >
                        <div style={{
                          fontSize: 11, fontWeight: 700,
                          color: isSelected ? 'var(--brand-primary)' : 'var(--text-primary)',
                          overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                          marginBottom: 3,
                        }}>
                          {path === '/' ? 'Startseite' : path}
                        </div>
                        {(page.title || page.h1) && (
                          <div style={{
                            fontSize: 11, color: 'var(--text-secondary)',
                            overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                            marginBottom: 5,
                          }}>
                            {page.title || page.h1}
                          </div>
                        )}
                        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                          {page.word_count > 0 && (
                            <span style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>{page.word_count} W</span>
                          )}
                          {imgCount > 0 && (
                            <span style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>{imgCount} Img</span>
                          )}
                          {(Array.isArray(page.h2s) ? page.h2s.length : 0) > 0 && (
                            <span style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>H2: {page.h2s.length}</span>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* RECHTES DETAIL */}
                {sel ? (
                  <div style={{ overflowY: 'auto', padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: 18 }}>

                    {/* URL */}
                    <div>
                      <DetailLabel>URL</DetailLabel>
                      <a href={sel.url} target="_blank" rel="noreferrer"
                        style={{ fontSize: 12, color: 'var(--brand-primary)', textDecoration: 'none', wordBreak: 'break-all', lineHeight: 1.5 }}>
                        {sel.url}
                      </a>
                    </div>

                    {/* Seitentitel */}
                    {(sel.title || sel.h1) && (
                      <div>
                        <DetailLabel>Seitentitel</DetailLabel>
                        <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1.4 }}>
                          {sel.title || sel.h1}
                        </div>
                      </div>
                    )}

                    {/* Headings */}
                    <div>
                      <DetailLabel>Headings</DetailLabel>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                        {sel.h1 && <HeadingRow level="H1" text={sel.h1} color="var(--brand-primary)" indent={0} />}
                        {(Array.isArray(sel.h2s) ? sel.h2s : []).map((h, j) =>
                          <HeadingRow key={`h2${j}`} level="H2" text={h} color="var(--text-primary)" indent={16} />
                        )}
                        {(Array.isArray(sel.h3s) ? sel.h3s : []).map((h, j) =>
                          <HeadingRow key={`h3${j}`} level="H3" text={h} color="var(--text-secondary)" indent={32} />
                        )}
                        {!sel.h1 && !sel.h2s?.length && !sel.h3s?.length && (
                          <span style={{ fontSize: 12, color: 'var(--text-tertiary)', fontStyle: 'italic' }}>Keine Headings</span>
                        )}
                      </div>
                    </div>

                    {/* Meta */}
                    {sel.meta_description && (
                      <div>
                        <DetailLabel>Meta-Description</DetailLabel>
                        <div style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.65, fontStyle: 'italic' }}>
                          {sel.meta_description}
                        </div>
                      </div>
                    )}

                    {/* Volltext */}
                    {sel.full_text && (
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
                          <DetailLabel style={{ marginBottom: 0 }}>Volltext - {sel.word_count || 0} Woerter</DetailLabel>
                          <button
                            onClick={() => setShowFullText(v => !v)}
                            style={{ fontSize: 11, color: 'var(--brand-primary)', background: 'none', border: 'none', cursor: 'pointer', fontFamily: 'var(--font-sans)', padding: 0 }}
                          >
                            {showFullText ? '\u25B2 Weniger' : '\u25BC Volltext anzeigen'}
                          </button>
                        </div>
                        <div style={{
                          fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.75,
                          whiteSpace: 'pre-wrap', wordBreak: 'break-word',
                          background: 'var(--bg-app)', borderRadius: 8, padding: '12px 14px',
                          maxHeight: showFullText ? 600 : 100,
                          overflowY: showFullText ? 'auto' : 'hidden',
                          position: 'relative', transition: 'max-height 0.3s',
                        }}>
                          {sel.full_text}
                          {!showFullText && (
                            <div style={{ position: 'absolute', bottom: 0, left: 0, right: 0, height: 36, background: 'linear-gradient(transparent, var(--bg-app))', borderRadius: '0 0 8px 8px' }} />
                          )}
                        </div>
                      </div>
                    )}

                    {/* Assets */}
                    {(Array.isArray(sel.images) && sel.images.length > 0) && (
                      <div>
                        <DetailLabel>Assets - {sel.images.length} Bilder</DetailLabel>
                        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                          {sel.images.slice(0, 12).map((src, j) => {
                            const imgSrc = typeof src === 'string' ? src : src?.src || '';
                            return (
                              <div key={j} title={imgSrc} style={{ width: 56, height: 56, borderRadius: 8, border: '1px solid var(--border-light)', overflow: 'hidden', background: 'var(--bg-app)', flexShrink: 0 }}>
                                <img src={imgSrc} alt="" loading="lazy" style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                                  onError={e => { e.target.parentNode.style.display = 'none'; }} />
                              </div>
                            );
                          })}
                          {sel.images.length > 12 && (
                            <div style={{ width: 56, height: 56, borderRadius: 8, background: 'var(--bg-app)', border: '1px solid var(--border-light)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 11, color: 'var(--text-tertiary)', fontWeight: 700 }}>
                              +{sel.images.length - 12}
                            </div>
                          )}
                        </div>
                      </div>
                    )}

                    {/* Links */}
                    {((Array.isArray(sel.links_internal) && sel.links_internal.length > 0) ||
                      (Array.isArray(sel.links_external) && sel.links_external.length > 0)) && (
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
                        {sel.links_internal?.length > 0 && (
                          <div>
                            <DetailLabel>Interne Links ({sel.links_internal.length})</DetailLabel>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                              {sel.links_internal.slice(0, 15).map((link, j) => {
                                let label = link;
                                try { label = new URL(link).pathname || '/'; } catch { /* keep */ }
                                return (
                                  <a key={j} href={link} target="_blank" rel="noreferrer"
                                    style={{ fontSize: 11, color: 'var(--brand-primary)', textDecoration: 'none', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', display: 'block', padding: '1px 0' }}>
                                    {label}
                                  </a>
                                );
                              })}
                              {sel.links_internal.length > 15 && (
                                <span style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>+ {sel.links_internal.length - 15} weitere</span>
                              )}
                            </div>
                          </div>
                        )}
                        {sel.links_external?.length > 0 && (
                          <div>
                            <DetailLabel>Externe Links ({sel.links_external.length})</DetailLabel>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                              {sel.links_external.slice(0, 12).map((link, j) => {
                                let label = link;
                                try { label = new URL(link).hostname; } catch { /* keep */ }
                                return (
                                  <a key={j} href={link} target="_blank" rel="noreferrer"
                                    style={{ fontSize: 11, color: 'var(--text-secondary)', textDecoration: 'none', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', display: 'block', padding: '1px 0' }}>
                                    {label}
                                  </a>
                                );
                              })}
                              {sel.links_external.length > 12 && (
                                <span style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>+ {sel.links_external.length - 12} weitere</span>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ) : (
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-tertiary)', fontSize: 13 }}>
                    Seite aus der Liste auswaehlen
                  </div>
                )}
              </div>
            );
          })()}
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

// ── Hilfskomponenten ─────────────────────────────────────────────────────────

function DetailLabel({ children, style }) {
  return (
    <div style={{
      fontSize: 10, fontWeight: 700, color: 'var(--text-tertiary)',
      textTransform: 'uppercase', letterSpacing: '.08em',
      marginBottom: 8, ...style,
    }}>
      {children}
    </div>
  );
}

function HeadingRow({ level, text, color, indent }) {
  return (
    <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8, paddingLeft: indent }}>
      <span style={{ fontSize: 9, fontWeight: 800, color, opacity: 0.6, flexShrink: 0, marginTop: 3, letterSpacing: '.04em', minWidth: 20 }}>
        {level}
      </span>
      <span style={{ fontSize: 13, color, lineHeight: 1.5 }}>{text}</span>
    </div>
  );
}

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
        setProgress(80);
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || `PageSpeed fehlgeschlagen (HTTP ${res.status})`);
        }
        const data = await res.json();
        setProgress(100);
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

export default function AnalyseCentrale({ projectId, leadId, websiteUrl, token, onDataUpdate }) {
  const headers = token ? { Authorization: `Bearer ${token}` } : {};

  const [running, setRunning]         = useState(false);
  const [currentStep, setCurrentStep] = useState(-1);
  const [stepProgress, setStepProgress] = useState(0);
  const [stepResults, setStepResults] = useState({});
  const [stepErrors, setStepErrors]   = useState({});
  // Optimierung #1 — wenn mehrere Schritte parallel laufen, kann der einzelne
  // Integer `currentStep` das nicht abbilden. `parallelRunning` ist ein Set
  // von Step-IDs, die gerade aktiv sind (nur waehrend runParallelPipeline
  // befuellt). Das Step-Render-Template nutzt parallelRunning.has(step.id)
  // als aktiv-Erkennung neben currentStep.
  const [parallelRunning, setParallelRunning] = useState(() => new Set());
  const [pages, setPages]             = useState([]);
  const [pagesLoading, setPagesLoading] = useState(false);
  const [hostingData, setHostingData] = useState(null);
  const [savedPagespeed, setSavedPagespeed] = useState(null);
  const [savedBrand, setSavedBrand]   = useState(null);
  const [selectedPage, setSelectedPage] = useState(null);
  const [search, setSearch]             = useState('');
  const [sortBy, setSortBy]             = useState('url');
  const [showFullText, setShowFullText] = useState(false);

  const steps = buildSteps(projectId, leadId, websiteUrl, headers);

  // ── Gespeicherte Ergebnisse laden (nur lesen, nichts ausfuehren) ────────
  useEffect(() => {
    if (!leadId) return;
    loadSavedResults();
  }, [leadId]); // eslint-disable-line

  const loadSavedResults = async () => {
    setPagesLoading(true);
    const saved = {};
    try {
      const [contentRes, hostingRes, psRes, brandRes] = await Promise.allSettled([
        fetch(`${API_BASE_URL}/api/crawler/content/${leadId}`, { headers }).then(r => r.ok ? r.json() : []),
        fetch(`${API_BASE_URL}/api/projects/${projectId}/hosting-info`, { headers }).then(r => r.ok ? r.json() : null),
        fetch(`${API_BASE_URL}/api/leads/${leadId}/pagespeed`, { headers }).then(r => r.ok ? r.json() : null),
        fetch(`${API_BASE_URL}/api/branddesign/${leadId}`, { headers }).then(r => r.ok ? r.json() : null),
      ]);

      // Crawler + Content
      const content = contentRes.status === 'fulfilled' ? (contentRes.value || []) : [];
      if (content.length > 0) {
        setPages(content);
        if (!selectedPage) setSelectedPage(content[0]);
        saved['url-crawl'] = { urls: content.length };
        const scraped = content.filter(p => p.full_text || p.text_preview).length;
        if (scraped > 0) saved['content-scrape'] = { pages: scraped };
        // GA check from existing content
        const GA_PATTERNS = ['gtag/js', 'google-analytics', 'googletagmanager', 'ga4', 'gtm.js'];
        let gaFound = false;
        for (const page of content) {
          const text = (page.full_text || '') + (page.url || '');
          if (GA_PATTERNS.some(p => text.toLowerCase().includes(p))) { gaFound = true; break; }
        }
        saved['analytics'] = { ga_found: gaFound };
      }

      // Hosting
      const hosting = hostingRes.status === 'fulfilled' ? hostingRes.value : null;
      if (hosting?.hosting_provider) {
        setHostingData(hosting);
        saved['hosting'] = { provider: hosting.hosting_provider };
      }

      // PageSpeed
      const ps = psRes.status === 'fulfilled' ? psRes.value : null;
      if (ps?.mobile_score != null) {
        saved['pagespeed'] = { mobile: ps.mobile_score, desktop: ps.desktop_score };
        setSavedPagespeed(ps);
      }

      // Brand
      const brand = brandRes.status === 'fulfilled' ? brandRes.value : null;
      if (brand?.primary_color) {
        saved['brand'] = { primary: brand.primary_color, fonts: brand.all_fonts?.length || 0 };
        setSavedBrand(brand);
      }

      setStepResults(saved);
      // Notify parent (ProzessFlow) about loaded data for step completion
      if (onDataUpdate) {
        onDataUpdate({
          crawlPages: content.length,
          brandPrimaryColor: brand?.primary_color || null,
          brandData: brand,
        });
      }
    } catch { /* silent */ }
    finally { setPagesLoading(false); }
  };

  // ── Einzelnen Schritt ausfuehren ────────────────────────────────────────
  const runStep = async (stepIndex) => {
    const step = steps[stepIndex];
    if (!websiteUrl) { toast.error('Keine Website-URL im Projekt'); return; }
    setRunning(true);
    setCurrentStep(stepIndex);
    setStepProgress(0);
    setStepErrors(prev => { const n = { ...prev }; delete n[step.id]; return n; });
    try {
      const result = await step.run((pct) => setStepProgress(pct));
      setStepResults(prev => ({ ...prev, [step.id]: result }));
      toast.success(`${step.label} abgeschlossen`);
    } catch (err) {
      setStepErrors(prev => ({ ...prev, [step.id]: err.message }));
      toast.error(`${step.label} fehlgeschlagen`);
    }
    setCurrentStep(-1);
    setRunning(false);
    // Seitenliste aktualisieren nach Crawler/Content
    if (step.id === 'url-crawl' || step.id === 'content-scrape') {
      const content = await fetch(`${API_BASE_URL}/api/crawler/content/${leadId}`, { headers }).then(r => r.ok ? r.json() : []).catch(() => []);
      setPages(content);
      if (content.length > 0 && !selectedPage) setSelectedPage(content[0]);
    }
    // Panel-Daten aktualisieren nach PageSpeed/Brand
    if (step.id === 'pagespeed') {
      const ps = await fetch(`${API_BASE_URL}/api/leads/${leadId}/pagespeed`, { headers }).then(r => r.ok ? r.json() : null).catch(() => null);
      if (ps) setSavedPagespeed(ps);
    }
    if (step.id === 'brand') {
      const bd = await fetch(`${API_BASE_URL}/api/branddesign/${leadId}`, { headers }).then(r => r.ok ? r.json() : null).catch(() => null);
      if (bd) {
        setSavedBrand(bd);
        if (onDataUpdate) onDataUpdate({ brandPrimaryColor: bd.primary_color, brandData: bd });
      }
    }
    // Crawl-Daten nach oben melden
    if (step.id === 'url-crawl' || step.id === 'content-scrape') {
      if (onDataUpdate) onDataUpdate({ crawlPages: pages.length });
    }
  };

  // ── Alle Schritte sequenziell (Fallback, alter Pfad) ───────────────────
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
    // Gespeicherte Ergebnisse nachladen (Seiten-Board + Panel-Daten aktualisieren)
    await loadSavedResults();
    toast.success('Alle Analysen abgeschlossen — Ergebnisse gespeichert!');
  };

  // ── Vollanalyse parallel (Optimierung #1) ──────────────────────────────
  //
  // Abhaengigkeits-Graph:
  //   Gruppe A (unabhaengig, sofort parallel): url-crawl, pagespeed, brand, hosting
  //   Gruppe B (sequentiell, startet sobald url-crawl fertig):
  //     url-crawl -> content-scrape -> analytics
  //
  // Statt `await Promise.allSettled(phase1)` nutzen wir Promise-Chaining:
  // content-scrape startet genau in dem Moment, in dem url-crawl fertig ist —
  // unabhaengig davon, ob pagespeed/brand/hosting noch laufen. Das ist
  // der Speedup gegenueber einem zweistufigen "phase1 dann phase2"-Ansatz.
  const runParallelPipeline = async () => {
    if (!websiteUrl) { toast.error('Keine Website-URL im Projekt'); return; }
    setRunning(true);
    setCurrentStep(-1);  // Bei parallelem Lauf kein einzelner "aktueller" Step
    setStepResults({});
    setStepErrors({});
    setParallelRunning(new Set());

    const stepMap = Object.fromEntries(steps.map(s => [s.id, s]));

    // Hilfsfunktion: einen Schritt ausfuehren und pro Schritt im
    // parallelRunning-Set tracken. Fehler werden nicht bubbled — stattdessen
    // in stepErrors gespeichert, damit Promise.allSettled weiterlaufen kann
    // und der Nutzer danach sieht welcher Schritt fehlschlug.
    const execStep = async (stepId) => {
      const step = stepMap[stepId];
      if (!step) return null;
      setParallelRunning(prev => {
        const next = new Set(prev);
        next.add(stepId);
        return next;
      });
      try {
        // In der parallelen Pipeline kein per-step-Progress — das wuerde
        // sonst die stepProgress-Anzeige springen lassen, weil mehrere
        // Schritte gleichzeitig schreiben.
        const result = await step.run(() => {});
        setStepResults(prev => ({ ...prev, [stepId]: result }));
        return result;
      } catch (err) {
        setStepErrors(prev => ({ ...prev, [stepId]: err.message || String(err) }));
        return null;
      } finally {
        setParallelRunning(prev => {
          const next = new Set(prev);
          next.delete(stepId);
          return next;
        });
      }
    };

    try {
      // ── Gruppe A: 4 Schritte sofort parallel starten ───────────────────
      const pCrawl     = execStep('url-crawl');
      const pPagespeed = execStep('pagespeed');
      const pBrand     = execStep('brand');
      const pHosting   = execStep('hosting');

      // ── Gruppe B: Promise-Chain, startet sobald url-crawl fertig ──────
      const pContentScrape = pCrawl.then(async (crawlResult) => {
        if (!crawlResult) return null;
        // Seitenliste nach dem Crawl sofort nachladen, damit das Seiten-
        // Board schon gefuellt ist, waehrend content-scrape noch laeuft.
        try {
          const content = await fetch(
            `${API_BASE_URL}/api/crawler/content/${leadId}`,
            { headers },
          ).then(r => r.ok ? r.json() : []).catch(() => []);
          setPages(content);
          if (Array.isArray(content) && content.length > 0 && !selectedPage) {
            setSelectedPage(content[0]);
          }
        } catch { /* nicht fatal */ }
        return execStep('content-scrape');
      });
      const pAnalytics = pContentScrape.then((contentResult) => {
        if (!contentResult) return null;
        return execStep('analytics');
      });

      // Auf alle Pfade warten — Gruppe A + Gruppe B (via Chain)
      await Promise.allSettled([pPagespeed, pBrand, pHosting, pContentScrape, pAnalytics]);

      // Panel-Daten abschliessend nachladen (SavedBrand, SavedPagespeed, Pages)
      await loadSavedResults();

      const doneIds = Object.keys(stepResults).length + Object.keys(stepErrors).length;
      toast.success(
        'Vollanalyse abgeschlossen — alle Daten gespeichert!',
        { duration: 4000 },
      );
    } catch (err) {
      toast.error('Vollanalyse unterbrochen: ' + (err?.message || 'unbekannter Fehler'));
    } finally {
      setParallelRunning(new Set());
      setRunning(false);
    }
  };

  const [saveStatus, setSaveStatus] = useState(''); // '', 'saving', 'saved'

  // ── Gesamtfortschritt ────────────────────────────────────────────────────
  const doneCount  = Object.keys(stepResults).length + Object.keys(stepErrors).length;
  const totalPct   = running
    ? Math.round(((doneCount / steps.length) + (stepProgress / 100 / steps.length)) * 100)
    : doneCount === steps.length ? 100 : 0;

  // ── Manuell speichern / verifizieren ─────────────────────────────────────
  const saveResults = async () => {
    setSaveStatus('saving');
    try {
      await loadSavedResults();
      setSaveStatus('saved');
      toast.success('Ergebnisse gespeichert');
      setTimeout(() => setSaveStatus(''), 3000);
    } catch {
      setSaveStatus('');
      toast.error('Speichern fehlgeschlagen');
    }
  };

  // ── Gesamt-Status fuer Hero-Panel ────────────────────────────────────────
  const parallelDoneCount = Object.keys(stepResults).length + Object.keys(stepErrors).length;

  // ── Render ───────────────────────────────────────────────────────────────
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

      {/* ── Optimierung #1: Prominenter Vollanalyse-Hero ── */}
      <div style={{
        background: running ? 'var(--bg-surface)' : 'linear-gradient(135deg, #008EAA 0%, #006680 100%)',
        border: running ? '1px solid var(--border-light)' : 'none',
        borderRadius: 12,
        padding: '18px 22px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: 14,
        flexWrap: 'wrap',
        boxShadow: running ? 'none' : '0 4px 18px rgba(0, 142, 170, 0.28)',
      }}>
        <div style={{ flex: 1, minWidth: 220 }}>
          <div style={{
            fontSize: 15, fontWeight: 700,
            color: running ? 'var(--text-primary)' : '#fff',
            marginBottom: 3,
          }}>
            {running ? 'Vollanalyse laeuft …' : 'Vollanalyse starten'}
          </div>
          <div style={{
            fontSize: 12,
            color: running ? 'var(--text-secondary)' : 'rgba(255,255,255,.85)',
          }}>
            {running
              ? `Schritt ${parallelDoneCount}/${steps.length} abgeschlossen${parallelRunning.size > 0 ? ` · ${parallelRunning.size} parallel aktiv` : ''}`
              : 'Crawler · Brand · PageSpeed · Analytics — alle unabhaengigen Schritte laufen gleichzeitig'}
          </div>
        </div>
        <button
          onClick={runParallelPipeline}
          disabled={running || !websiteUrl}
          style={{
            padding: '11px 26px',
            borderRadius: 10,
            border: 'none',
            background: running
              ? 'var(--border-light)'
              : (!websiteUrl ? 'rgba(255,255,255,.25)' : 'rgba(255,255,255,.22)'),
            color: running ? 'var(--text-secondary)' : '#fff',
            fontSize: 14,
            fontWeight: 700,
            cursor: (running || !websiteUrl) ? 'not-allowed' : 'pointer',
            flexShrink: 0,
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            fontFamily: 'var(--font-sans)',
            backdropFilter: running ? 'none' : 'blur(4px)',
          }}
        >
          {running ? (
            <>
              <span style={{
                width: 14, height: 14, borderRadius: '50%',
                border: '2px solid rgba(0,0,0,.2)',
                borderTopColor: 'var(--text-secondary)',
                animation: 'spin 0.8s linear infinite',
                display: 'inline-block',
              }} />
              Laeuft …
            </>
          ) : (
            <>\u25B6 Vollanalyse starten</>
          )}
        </button>
      </div>

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
        <div style={{ display: 'flex', gap: 8, flexShrink: 0 }}>
          <button
            onClick={runParallelPipeline}
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
          {doneCount > 0 && !running && (
            <button
              onClick={saveResults}
              disabled={saveStatus === 'saving'}
              style={{
                padding: '11px 20px', borderRadius: 8,
                border: saveStatus === 'saved' ? '1px solid var(--status-success-text)' : '1px solid var(--brand-primary, #008EAA)',
                background: saveStatus === 'saved' ? 'var(--status-success-bg)' : 'transparent',
                color: saveStatus === 'saved' ? 'var(--status-success-text)' : 'var(--brand-primary, #008EAA)',
                fontSize: 13, fontWeight: 700,
                cursor: saveStatus === 'saving' ? 'not-allowed' : 'pointer',
                fontFamily: 'var(--font-sans)',
                display: 'flex', alignItems: 'center', gap: 6,
                transition: 'all .2s',
              }}
            >
              {saveStatus === 'saving' ? (
                <><span style={{ width: 12, height: 12, border: '2px solid var(--border-medium)', borderTopColor: 'var(--brand-primary)', borderRadius: '50%', animation: 'spin .8s linear infinite', display: 'inline-block' }} />Speichert...</>
              ) : saveStatus === 'saved' ? '\u2713 Gespeichert' : 'Ergebnisse speichern'}
            </button>
          )}
        </div>
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
          // isActive erkennt beide Modi: sequenzieller runPipeline (currentStep === i)
          // und paralleler runParallelPipeline (parallelRunning.has(step.id)).
          const isActive  = currentStep === i || parallelRunning.has(step.id);
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
                {isDone && !isActive && <span style={{ marginLeft: 'auto', fontSize: 14, color: 'var(--status-success-text)' }}>&#10003;</span>}
                {hasError && !isActive && <span style={{ marginLeft: 'auto', fontSize: 14, color: 'var(--status-danger-text)' }}>&#10007;</span>}
              </div>

              {isActive && stepProgress > 0 && !parallelRunning.has(step.id) && (
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

              {/* Einzelner Start-Button pro Schritt */}
              {!isActive && !running && (
                <button
                  onClick={() => runStep(i)}
                  disabled={!websiteUrl}
                  style={{
                    marginTop: 10, width: '100%', padding: '6px 0', borderRadius: 6,
                    border: isDone ? '1px solid var(--status-success-text)' : '1px solid var(--brand-primary, #008EAA)',
                    background: isDone ? 'transparent' : 'var(--brand-primary, #008EAA)',
                    color: isDone ? 'var(--status-success-text)' : '#fff',
                    fontSize: 11, fontWeight: 700, cursor: websiteUrl ? 'pointer' : 'not-allowed',
                    fontFamily: 'var(--font-sans)',
                  }}
                >
                  {isDone ? 'Erneut ausfuehren' : 'Starten'}
                </button>
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
                height: 680,
              }}>

                {/* LINKE SPALTE */}
                <div style={{
                  borderRight: '1px solid var(--border-light)',
                  background: 'var(--bg-app)',
                  display: 'flex',
                  flexDirection: 'column',
                  overflow: 'hidden',
                  borderRadius: 'var(--radius-lg) 0 0 var(--radius-lg)',
                }}>
                  {/* Scrollbare Seiten-Liste */}
                  <div style={{ flex: 1, overflowY: 'auto' }}>
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
                  {/* Zusammenfassung */}
                  <ProjectSummaryPanel
                    leadId={leadId}
                    headers={headers}
                    stepResults={stepResults}
                    savedPagespeed={savedPagespeed}
                    savedBrand={savedBrand}
                  />
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

// ── Projekt-Zusammenfassung (linke Spalte unten) ─────────────────────────────

function ProjectSummaryPanel({ leadId, headers, stepResults, savedPagespeed, savedBrand }) {
  const [pagespeed, setPagespeed] = useState(savedPagespeed || null);
  const [brand, setBrand]         = useState(savedBrand || null);
  const [designData, setDesignData] = useState(savedBrand?.design_data || null);

  // Sync from parent when saved data arrives
  useEffect(() => { if (savedPagespeed) setPagespeed(savedPagespeed); }, [savedPagespeed]);
  useEffect(() => {
    if (savedBrand) { setBrand(savedBrand); if (savedBrand.design_data) setDesignData(savedBrand.design_data); }
  }, [savedBrand]);

  const gaResult = stepResults?.analytics;

  const scoreColor = (s) => {
    if (s == null) return { bg: 'var(--bg-elevated)', text: 'var(--text-tertiary)' };
    if (s >= 90) return { bg: '#EAF4E0', text: '#2D6A0A' };
    if (s >= 50) return { bg: '#FEF3DC', text: '#8A5C00' };
    return { bg: '#FDEAEA', text: '#C0392B' };
  };

  return (
    <div style={{
      borderTop: '1px solid var(--border-light)',
      background: 'var(--bg-surface)',
      padding: '12px 14px',
      flexShrink: 0,
      display: 'flex',
      flexDirection: 'column',
      gap: 10,
    }}>
      {/* PageSpeed */}
      <div>
        <div style={{ fontSize: 9, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.08em', marginBottom: 6 }}>
          PageSpeed
        </div>
        {pagespeed ? (
          <div style={{ display: 'flex', gap: 6 }}>
            {[
              { label: 'Mobil',   score: pagespeed.mobile_score },
              { label: 'Desktop', score: pagespeed.desktop_score },
            ].map(({ label, score }) => {
              const c = scoreColor(score);
              return (
                <div key={label} style={{ flex: 1, borderRadius: 6, padding: '6px 8px', textAlign: 'center', background: c.bg }}>
                  <div style={{ fontSize: 18, fontWeight: 900, color: c.text, lineHeight: 1 }}>{score ?? '\u2014'}</div>
                  <div style={{ fontSize: 9, color: c.text, opacity: 0.7, marginTop: 2 }}>{label}</div>
                </div>
              );
            })}
          </div>
        ) : (
          <div style={{ fontSize: 11, color: 'var(--text-tertiary)', fontStyle: 'italic' }}>Noch nicht gemessen</div>
        )}
      </div>

      {/* Google Analytics */}
      <div>
        <div style={{ fontSize: 9, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.08em', marginBottom: 6 }}>Google Analytics</div>
        {gaResult != null ? (
          <div style={{ fontSize: 11, fontWeight: 600, padding: '5px 10px', borderRadius: 6, background: gaResult.ga_found ? '#EAF4E0' : '#FEF3DC', color: gaResult.ga_found ? '#2D6A0A' : '#8A5C00' }}>
            {gaResult.ga_found ? 'GA4 erkannt' : 'Kein GA4 gefunden'}
          </div>
        ) : (
          <div style={{ fontSize: 11, color: 'var(--text-tertiary)', fontStyle: 'italic' }}>Analyse ausstehend</div>
        )}
      </div>

      {/* Brand Design Board */}
      <div>
        <div style={{ fontSize: 9, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.08em', marginBottom: 8 }}>
          Brand Design
          {designData?.style_keyword && (
            <span style={{ marginLeft: 8, fontWeight: 600, color: 'var(--brand-primary)', textTransform: 'none', letterSpacing: 0 }}>
              {designData.style_keyword}
            </span>
          )}
        </div>

        {/* SSL-Status Badge (vom branddesign-Scrape gesetzt) */}
        {brand?.ssl_ok === false && (
          <div style={{
            display: 'flex',
            alignItems: 'flex-start',
            gap: 8,
            padding: '10px 14px',
            background: '#FFFBE0',
            border: '1px solid #FAE600',
            borderRadius: 8,
            marginBottom: 10,
          }}>
            <span style={{ fontSize: 18, lineHeight: 1 }} aria-hidden="true">⚠️</span>
            <div>
              <div style={{
                fontWeight: 900, fontSize: 11,
                color: '#004F59',
                textTransform: 'uppercase',
                letterSpacing: '.06em',
              }}>
                SSL-Zertifikat fehlerhaft
              </div>
              <div style={{ fontSize: 11, color: '#4A5A5C', marginTop: 3, lineHeight: 1.5 }}>
                Die Kunden-Website hat ein ungueltiges Zertifikat. Inhalte wurden trotzdem geladen.
                Nach dem Launch auf Netlify wird SSL automatisch korrekt eingerichtet.
              </div>
              {brand?.ssl_error && (
                <div style={{ fontSize: 10, color: '#9AACAE', marginTop: 4, fontFamily: 'monospace' }}>
                  {brand.ssl_error}
                </div>
              )}
            </div>
          </div>
        )}
        {brand?.ssl_ok === true && (
          <div style={{
            display: 'inline-flex', alignItems: 'center', gap: 5,
            padding: '3px 9px',
            background: '#E3F6EF',
            border: '1px solid rgba(0,135,90,0.3)',
            borderRadius: 20,
            fontSize: 10, fontWeight: 700,
            color: '#00875A',
            textTransform: 'uppercase',
            letterSpacing: '.06em',
            marginBottom: 10,
          }}>
            🔒 SSL OK
          </div>
        )}

        {designData ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>

            {/* Farb-Palette */}
            <div>
              <div style={{ fontSize: 9, color: 'var(--text-tertiary)', marginBottom: 4 }}>Farben</div>
              <div style={{ display: 'flex', gap: 4, overflowX: 'auto', paddingBottom: 4 }}>
                {[
                  { color: designData.colors?.primary,    label: 'P' },
                  { color: designData.colors?.secondary,  label: 'S' },
                  { color: designData.colors?.accent,     label: 'A' },
                  { color: designData.colors?.background, label: 'BG' },
                  { color: designData.colors?.text,       label: 'T' },
                  ...(designData.colors?.all || [])
                    .filter(c => ![designData.colors?.primary, designData.colors?.secondary, designData.colors?.accent, designData.colors?.background, designData.colors?.text].includes(c))
                    .slice(0, 6).map(c => ({ color: c, label: '' })),
                ].filter(e => e.color).map(({ color, label }, i) => (
                  <div key={i} title={`${label ? label + ': ' : ''}${color}`} onClick={() => navigator.clipboard?.writeText(color)} style={{ flexShrink: 0, cursor: 'pointer' }}>
                    <div style={{ width: label ? 28 : 20, height: label ? 28 : 20, borderRadius: 4, background: color, border: '1px solid var(--border-light)' }} />
                    {label && <div style={{ fontSize: 8, color: 'var(--text-tertiary)', textAlign: 'center', marginTop: 2 }}>{label}</div>}
                  </div>
                ))}
              </div>
            </div>

            {/* Schrift-Vorschau */}
            {designData.fonts?.length > 0 && (
              <div>
                <div style={{ fontSize: 9, color: 'var(--text-tertiary)', marginBottom: 4 }}>Schriften</div>
                {designData.fonts.slice(0, 2).map((font, i) => (
                  <div key={i} style={{ fontSize: i === 0 ? 13 : 11, fontWeight: i === 0 ? 700 : 400, color: 'var(--text-primary)', lineHeight: 1.3, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', marginBottom: 2 }}>
                    {font}
                  </div>
                ))}
              </div>
            )}

            {/* Design-DNA Chips */}
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
              {[
                designData.border_radius_style && designData.border_radius_style !== 'unbekannt' && `${designData.border_radius_style}`,
                designData.shadow_label && `${designData.shadow_label}`,
                designData.button_style && `btn: ${designData.button_style}`,
                designData.spacing_density && `${designData.spacing_density}`,
                designData.farb_stimmung && `${designData.farb_stimmung}`,
              ].filter(Boolean).map((chip, i) => (
                <span key={i} style={{ fontSize: 9, padding: '2px 6px', background: 'var(--bg-elevated)', border: '1px solid var(--border-light)', borderRadius: 4, color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>
                  {chip}
                </span>
              ))}
            </div>

            {/* KI Design Brief */}
            {designData.design_brief?.fuer_ki_prompt && (
              <details style={{ fontSize: 10 }}>
                <summary style={{ cursor: 'pointer', color: 'var(--brand-primary)', fontWeight: 600, fontSize: 10 }}>
                  KI-Design-Brief
                </summary>
                <div style={{ marginTop: 6, padding: '8px 10px', background: 'var(--bg-app)', borderRadius: 6, fontSize: 10, color: 'var(--text-secondary)', lineHeight: 1.6, border: '1px solid var(--border-light)' }}>
                  {designData.design_brief.fuer_ki_prompt}
                </div>
                <button onClick={() => navigator.clipboard?.writeText(designData.design_brief.fuer_ki_prompt)}
                  style={{ marginTop: 4, fontSize: 10, padding: '3px 8px', background: 'none', border: '1px solid var(--border-light)', borderRadius: 4, cursor: 'pointer', color: 'var(--brand-primary)', fontFamily: 'var(--font-sans)' }}>
                  Kopieren
                </button>
              </details>
            )}

            {!designData.design_brief && designData.style_beschreibung && (
              <div style={{ fontSize: 10, color: 'var(--text-tertiary)', lineHeight: 1.5, fontStyle: 'italic' }}>{designData.style_beschreibung}</div>
            )}
          </div>
        ) : brand?.primary_color ? (
          <div style={{ display: 'flex', gap: 4 }}>
            {[brand.primary_color, brand.secondary_color].filter(Boolean).map((c, i) => (
              <div key={i} style={{ width: 20, height: 20, borderRadius: 4, background: c, border: '1px solid var(--border-light)' }} />
            ))}
            {brand.font_primary && <span style={{ fontSize: 10, color: 'var(--text-secondary)', marginLeft: 4 }}>{brand.font_primary}</span>}
          </div>
        ) : (
          <div style={{ fontSize: 11, color: 'var(--text-tertiary)', fontStyle: 'italic' }}>Brand-Scan starten</div>
        )}
      </div>
    </div>
  );
}

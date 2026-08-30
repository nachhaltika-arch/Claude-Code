/**
 * Die Schrittliste der Analyse-Zentrale (L-25).
 *
 * Am 2026-08-30 aus `AnalyseCentrale.jsx` herausgeloest — 123 Zeilen. Sie
 * beschreibt, **was** gemessen wird; die Zentrale daneben, wie.
 */
import API_BASE_URL from '../../config';

export function buildSteps(projectId, leadId, websiteUrl, headers) {
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
  ];
}

// ── Haupt-Komponente ─────────────────────────────────────────────────────────


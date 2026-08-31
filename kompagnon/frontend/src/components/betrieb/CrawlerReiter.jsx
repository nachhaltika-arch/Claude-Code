import { useEffect, useRef, useState } from 'react';
import API_BASE_URL from '../../config';
import { loadJson } from '../../utils/apiRequest';
import { aufTaste } from '../../utils/tastaturBedienung';

/**
 * Der Crawler-Reiter des Betriebsprofils (L-25).
 *
 * **Warum eigene Datei, 22.08.2026.** `pages/LeadProfile.jsx` hatte 2.846
 * Zeilen, davon rund 1.650 in vierzehn Reiter-Zweigen. Die meisten davon
 * lassen sich **nicht** einfach herausloesen: `overview` greift auf 38
 * Namen des Seitenzustands zu, und die muesste man alle durchreichen.
 *
 * Dieser Zweig ist die Ausnahme. Er bringt seinen **gesamten** Zustand
 * selbst mit — sieben Namen, die nur er benutzt — und braucht von aussen
 * nur den Betrieb und das Anmeldemerkmal. Deshalb faellt er heraus, ohne
 * dass eine Requisitenkette entsteht.
 *
 * Die Zeilenzahl war nicht der Grund, sondern die Gelegenheit: Ein Reiter,
 * der seinen Zustand selbst haelt, ist eine Komponente — er stand nur
 * zufaellig mitten in einer Seite.
 */
// Nur der Crawler-Zweig zeigte diese Galerie — sie ist mitgewandert.
function CrawledImagesGallery({ leadId, headers }) {
  const [images, setImages] = useState([]);
  const [showAll, setShowAll] = useState(false);
  useEffect(() => {
    if (!leadId) return;
    loadJson(
      `${API_BASE_URL}/api/files/${leadId}/grapesjs-assets?include_crawled=true`,
      { headers },
      { context: 'Bilder der Website', fallback: [] }
    ).then(assets => setImages((Array.isArray(assets) ? assets : []).filter(a => a.category?.startsWith('Website:'))));
  }, [leadId]); // eslint-disable-line
  if (images.length === 0) return null;
  const visible = showAll ? images : images.slice(0, 12);
  return (
    <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', padding: 16, marginTop: 8 }}>
      <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 12, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <span>{images.length} Bilder von der Website gecrawlt</span>
        {images.length > 12 && <button onClick={() => setShowAll(v => !v)} style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: 12, color: 'var(--brand-primary-mid)', fontFamily: 'var(--font-sans)' }}>{showAll ? 'Weniger' : `Alle ${images.length}`}</button>}
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(80px, 1fr))', gap: 6 }}>
        {visible.map((img, i) => (
          <div key={i} title={img.name} style={{ position: 'relative', paddingBottom: '75%', background: 'var(--bg-app)', borderRadius: 'var(--radius-sm)', overflow: 'hidden', border: '1px solid var(--border-light)' }}>
            <img src={img.src} alt={img.name} loading="lazy" style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover' }} onError={e => { e.target.parentNode.style.display = 'none'; }} />
          </div>
        ))}
      </div>
      <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginTop: 10 }}>Diese Bilder sind im GrapesJS-Editor unter „Website: ..." verfügbar.</div>
    </div>
  );
}

export default function CrawlerReiter({ leadId, lead, token }) {
  const [crawlJob, setCrawlJob] = useState(null);
  const [crawlResults, setCrawlResults] = useState([]);
  const [crawlLoading, setCrawlLoading] = useState(false);
  const [crawlElapsed, setCrawlElapsed] = useState(0);
  const crawlIntervalRef = useRef(null);
  const [crawlSort, setCrawlSort] = useState({ col: 'crawled_at', asc: true });
  const [crawlExpandedRow, setCrawlExpandedRow] = useState(null);

  const h = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };

  return (() => {
        const loadCrawlStatus = () => {
          fetch(`${API_BASE_URL}/api/crawler/status/${leadId}`, { headers: h })
            .then(r => r.json()).then(d => {
              setCrawlJob(d);
              if (d.status === 'completed') {
                fetch(`${API_BASE_URL}/api/crawler/results/${leadId}`, { headers: h })
                  .then(r => r.json()).then(res => setCrawlResults(res.results || []));
              }
            }).catch(console.error);
        };
        const startCrawl = () => {
          const url = lead?.website_url;
          if (!url || crawlLoading || crawlJob?.status === 'running') return;
          setCrawlLoading(true);
          setCrawlElapsed(0);
          let elapsed = 0;
          if (crawlIntervalRef.current) clearInterval(crawlIntervalRef.current);
          crawlIntervalRef.current = setInterval(() => { elapsed += 1; setCrawlElapsed(elapsed); }, 1000);
          fetch(`${API_BASE_URL}/api/crawler/start/${leadId}`, {
            method: 'POST', headers: h,
            body: JSON.stringify({ url, max_pages: 50 }),
          }).then(r => r.json()).then(d => {
            setCrawlJob(d);
            setCrawlResults([]);
            const interval = setInterval(() => {
              fetch(`${API_BASE_URL}/api/crawler/status/${leadId}`, { headers: h })
                .then(r => r.json()).then(status => {
                  setCrawlJob(status);
                  if (status.status === 'completed' || status.status === 'failed') {
                    clearInterval(interval);
                    clearInterval(crawlIntervalRef.current);
                    setCrawlLoading(false);
                    if (status.status === 'completed') {
                      fetch(`${API_BASE_URL}/api/crawler/results/${leadId}`, { headers: h })
                        .then(r => r.json()).then(res => setCrawlResults(res.results || []));
                    }
                  }
                });
            }, 3000);
          }).catch(e => { console.error(e); setCrawlLoading(false); clearInterval(crawlIntervalRef.current); });
        };

        if (!crawlJob && !crawlLoading) loadCrawlStatus();

        const statusColor = { running: '#f59e0b', completed: '#16a34a', failed: '#dc2626', pending: '#64748b', none: '#94a3b8' };
        const statusLabel = { running: 'Läuft', completed: 'Abgeschlossen', failed: 'Fehler', pending: 'Wartend', none: 'Kein Job' };

        const sorted = [...crawlResults].sort((a, b) => {
          const va = a[crawlSort.col] ?? '';
          const vb = b[crawlSort.col] ?? '';
          return crawlSort.asc ? (va > vb ? 1 : -1) : (va < vb ? 1 : -1);
        });

        const statusGroups = { '2xx': 0, '3xx': 0, '4xx+': 0 };
        crawlResults.forEach(r => {
          if (!r.status_code) return;
          if (r.status_code < 300) statusGroups['2xx']++;
          else if (r.status_code < 400) statusGroups['3xx']++;
          else statusGroups['4xx+']++;
        });
        const totalForBar = Object.values(statusGroups).reduce((a, b) => a + b, 0) || 1;

        const ThSort = ({ col, label }) => (
          <th onClick={() => setCrawlSort(p => ({ col, asc: p.col === col ? !p.asc : true }))} style={{ padding: '8px 12px', fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', textAlign: 'left', cursor: 'pointer', borderBottom: '1px solid var(--border-light)', userSelect: 'none', whiteSpace: 'nowrap' }}>
            {label} {crawlSort.col === col ? (crawlSort.asc ? '↑' : '↓') : ''}
          </th>
        );

        return (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {/* Header */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
              <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' }}>🕷️ Website-Crawler</div>
              <button onClick={startCrawl} disabled={crawlLoading || crawlJob?.status === 'running'} style={{
                padding: '8px 18px', background: (crawlLoading || crawlJob?.status === 'running') ? 'var(--border-medium)' : 'var(--success)', color: 'var(--text-on-brand)',
                border: 'none', borderRadius: 'var(--radius-md)', fontSize: 12, fontWeight: 700,
                cursor: (crawlLoading || crawlJob?.status === 'running') ? 'not-allowed' : 'pointer',
                fontFamily: 'var(--font-sans)', display: 'flex', alignItems: 'center', gap: 6,
              }}>
                {(crawlLoading || crawlJob?.status === 'running') ? (
                  <><div style={{ width: 12, height: 12, borderRadius: '50%', border: '2px solid rgba(255,255,255,0.3)', borderTopColor: 'white', animation: 'spin 0.7s linear infinite' }} />Analysiert…</>
                ) : '▶ Crawler starten'}
              </button>
            </div>

            {/* Progress Box — nur während Crawler läuft */}
            {(crawlJob?.status === 'running' || (crawlLoading && !crawlJob)) && (() => {
              const elapsed = crawlJob?.duration_seconds ?? crawlElapsed;
              const found = crawlJob?.total_urls || 0;
              const phase = elapsed < 5 ? { icon: '🔌', text: 'Verbindung wird aufgebaut…' }
                : elapsed < 15 ? { icon: '🏠', text: 'Startseite wird analysiert…' }
                : elapsed < 30 ? { icon: '🔗', text: `Links werden entdeckt — ${found} URLs bisher` }
                : elapsed < 45 ? { icon: '📄', text: `Unterseiten durchsucht — ${found} URLs gecrawlt` }
                : { icon: '⚡', text: `Tiefe Analyse — ${found} URLs, Abschluss in Kürze` };
              return (
                <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--brand-primary-mid, var(--border-light))', borderRadius: 'var(--radius-lg)', padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: 14 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <div style={{ width: 36, height: 36, borderRadius: '50%', border: '3px solid var(--brand-primary-light)', borderTopColor: 'var(--brand-primary)', animation: 'spin 0.8s linear infinite', flexShrink: 0 }} />
                    <div>
                      <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' }}>Crawler analysiert {lead?.website_url?.replace(/^https?:\/\//, '').split('/')[0]}</div>
                      <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 2 }}>Seiten werden automatisch entdeckt und analysiert</div>
                    </div>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 14px', background: 'var(--brand-primary-light)', borderRadius: 'var(--radius-md)', fontSize: 13, color: 'var(--brand-primary-dark)', fontWeight: 500 }}>
                    <span style={{ fontSize: 18 }}>{phase.icon}</span><span>{phase.text}</span>
                  </div>
                  <div>
                    <div style={{ height: 6, background: 'var(--border-light)', borderRadius: 3, overflow: 'hidden' }}>
                      <div style={{ height: '100%', width: `${Math.min(95, (elapsed / 44) * 100)}%`, background: 'var(--brand-primary)', borderRadius: 3, transition: 'width 1s linear' }} />
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, color: 'var(--text-tertiary)', marginTop: 5 }}>
                      <span>{found > 0 ? `${found} URLs gefunden` : 'Suche läuft…'}</span>
                      <span>{elapsed < 60 ? `${elapsed}s` : `${Math.floor(elapsed / 60)}m ${elapsed % 60}s`}</span>
                    </div>
                  </div>
                  {elapsed > 35 && (
                    <div style={{ fontSize: 12, color: 'var(--text-tertiary)', padding: '8px 12px', background: 'var(--bg-app)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-light)' }}>
                      Große Websites dauern bis zu 60 Sekunden. Die Analyse läuft im Hintergrund — kein erneuter Klick nötig.
                    </div>
                  )}
                </div>
              );
            })()}

            {/* Status cards */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
              {[
                { label: 'Status', value: statusLabel[crawlJob?.status || 'none'], color: statusColor[crawlJob?.status || 'none'] },
                { label: 'Laufzeit', value: crawlJob?.duration_seconds != null ? `${Math.floor(crawlJob.duration_seconds / 60)}m ${crawlJob.duration_seconds % 60}s` : '—' },
                { label: 'Gecrawlte URLs', value: crawlJob?.total_urls || crawlResults.length || 0 },
                { label: 'URL-Limit', value: 50 },
              ].map(c => (
                <div key={c.label} style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', padding: '14px 16px' }}>
                  <div style={{ fontSize: 10, color: 'var(--text-tertiary)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 6 }}>{c.label}</div>
                  <div style={{ fontSize: 18, fontWeight: 700, color: c.color || 'var(--text-primary)' }}>{c.value}</div>
                </div>
              ))}
            </div>

            {/* Status bar chart */}
            {/* Gecrawlte Bilder Galerie */}
            <CrawledImagesGallery leadId={leadId} headers={h} />

            {crawlResults.length > 0 && (
              <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', padding: 16 }}>
                <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 12 }}>URLs nach Status-Code</div>
                <div style={{ display: 'flex', height: 28, borderRadius: 6, overflow: 'hidden', marginBottom: 10 }}>
                  {statusGroups['2xx'] > 0 && <div style={{ flex: statusGroups['2xx'], background: '#16a34a', minWidth: 2 }} title={`${statusGroups['2xx']} × 2xx`} />}
                  {statusGroups['3xx'] > 0 && <div style={{ flex: statusGroups['3xx'], background: '#f59e0b', minWidth: 2 }} title={`${statusGroups['3xx']} × 3xx`} />}
                  {statusGroups['4xx+'] > 0 && <div style={{ flex: statusGroups['4xx+'], background: '#dc2626', minWidth: 2 }} title={`${statusGroups['4xx+']} × 4xx+`} />}
                </div>
                <div style={{ display: 'flex', gap: 20, fontSize: 12, color: 'var(--text-secondary)' }}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: 5 }}><span style={{ width: 10, height: 10, borderRadius: 2, background: '#16a34a', display: 'inline-block' }} />{statusGroups['2xx']} OK</span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: 5 }}><span style={{ width: 10, height: 10, borderRadius: 2, background: '#f59e0b', display: 'inline-block' }} />{statusGroups['3xx']} Redirect</span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: 5 }}><span style={{ width: 10, height: 10, borderRadius: 2, background: '#dc2626', display: 'inline-block' }} />{statusGroups['4xx+']} Fehler</span>
                </div>
              </div>
            )}

            {/* Results table */}
            {sorted.length > 0 ? (
              <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', overflow: 'hidden', overflowX: 'auto' }}>
                <table style={{ width: '100%', minWidth: 480, borderCollapse: 'collapse', fontSize: 12 }}>
                  <thead>
                    <tr style={{ background: 'var(--bg-app)' }}>
                      <ThSort col="crawled_at" label="Zeitpunkt" />
                      <ThSort col="status_code" label="Status" />
                      <ThSort col="load_time" label="Ladezeit" />
                      <ThSort col="url" label="URL" />
                    </tr>
                  </thead>
                  <tbody>
                    {sorted.map((r, i) => {
                      const sc = r.status_code;
                      const scColor = !sc ? '#94a3b8' : sc < 300 ? '#16a34a' : sc < 400 ? '#f59e0b' : '#dc2626';
                      const scBg = !sc ? 'var(--bg-app)' : sc < 300 ? 'var(--status-success-bg)' : sc < 400 ? 'var(--status-warning-bg)' : 'var(--status-danger-bg)';
                      const lt = r.load_time;
                      const rowKey = r.url + '_' + i;
                      const isExpanded = crawlExpandedRow === rowKey;

                      // ── Build hints ──────────────────────────────
                      const hints = [];
                      if (sc === 301 || sc === 302) {
                        hints.push({ bg: 'var(--status-warning-bg)', border: '#fde68a', text: '⚠️ Weiterleitung erkannt. Prüfe ob die Ziel-URL direkt verlinkt werden kann, um Ladezeit zu sparen.' });
                      } else if (sc === 404) {
                        hints.push({ bg: 'var(--status-danger-bg)', border: '#fecaca', text: '🔴 Seite nicht gefunden. Dieser Link sollte entfernt oder korrigiert werden.' });
                      } else if (sc === 500) {
                        hints.push({ bg: 'var(--status-danger-bg)', border: '#fecaca', text: '🔴 Serverfehler. Diese Seite hat ein technisches Problem und muss geprüft werden.' });
                      } else if (!sc || sc === 0) {
                        hints.push({ bg: 'var(--status-danger-bg)', border: '#fecaca', text: '🔴 Seite nicht erreichbar. Timeout nach 10 Sekunden.' });
                      }
                      if (lt != null && lt > 3.0) {
                        hints.push({ bg: '#fff7ed', border: '#fed7aa', text: '🟠 Ladezeit über 3 Sekunden. Bilder komprimieren oder Caching aktivieren.' });
                      } else if (lt != null && lt > 1.5) {
                        hints.push({ bg: 'var(--status-warning-bg)', border: '#fde68a', text: '🟡 Ladezeit erhöht. Performance-Optimierung empfohlen.' });
                      }
                      if (hints.length === 0 && sc >= 200 && sc < 300 && lt != null && lt <= 1.5) {
                        hints.push({ bg: 'var(--status-success-bg)', border: '#bbf7d0', text: '✅ Alles in Ordnung.' });
                      }

                      return (
                        <>
                          <tr role="button" tabIndex={0} onKeyDown={aufTaste(() => setCrawlExpandedRow(isExpanded ? null : rowKey))}
                            key={rowKey}
                            onClick={() => setCrawlExpandedRow(isExpanded ? null : rowKey)}
                            style={{
                              borderTop: '1px solid var(--border-light)',
                              cursor: 'pointer',
                              background: isExpanded ? 'var(--bg-app)' : 'transparent',
                              transition: 'background 0.15s',
                            }}
                            onMouseEnter={e => { if (!isExpanded) e.currentTarget.style.background = 'var(--bg-hover)'; }}
                            onMouseLeave={e => { if (!isExpanded) e.currentTarget.style.background = 'transparent'; }}
                          >
                            <td style={{ padding: '7px 12px', color: 'var(--text-tertiary)', whiteSpace: 'nowrap' }}>{r.crawled_at || '—'}</td>
                            <td style={{ padding: '7px 12px' }}>
                              <span style={{ background: scBg, color: scColor, fontWeight: 700, borderRadius: 4, padding: '2px 7px' }}>{sc || '—'}</span>
                            </td>
                            <td style={{ padding: '7px 12px', color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>
                              {lt != null ? `${lt}s` : '—'}
                            </td>
                            <td style={{ padding: '7px 12px', maxWidth: 400 }}>
                              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
                                <a href={r.url} target="_blank" rel="noreferrer" onClick={e => e.stopPropagation()} style={{ color: 'var(--brand-primary-mid)', textDecoration: 'none', fontSize: 12, wordBreak: 'break-all' }}>{r.url}</a>
                                <span style={{ flexShrink: 0, fontSize: 10, color: 'var(--text-tertiary)', transform: isExpanded ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }}>▼</span>
                              </div>
                            </td>
                          </tr>
                          {isExpanded && (
                            <tr key={rowKey + '_hint'} style={{ background: 'var(--bg-app)' }}>
                              <td colSpan={4} style={{ padding: '0 12px 10px 12px' }}>
                                <div style={{
                                  display: 'flex', flexDirection: 'column', gap: 6,
                                  animation: 'crawlHintIn 0.18s ease',
                                }}>
                                  {hints.length === 0 ? (
                                    <div style={{ padding: '8px 12px', background: 'var(--bg-app)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)', fontSize: 12, color: 'var(--text-secondary)' }}>
                                      Keine Empfehlung verfügbar.
                                    </div>
                                  ) : hints.map((hint, hi) => (
                                    <div key={hi} style={{
                                      padding: '9px 13px',
                                      background: hint.bg,
                                      border: `1px solid ${hint.border}`,
                                      borderRadius: 'var(--radius-md)',
                                      fontSize: 12, lineHeight: 1.5,
                                      color: 'var(--text-primary)',
                                    }}>
                                      {hint.text}
                                    </div>
                                  ))}
                                </div>
                              </td>
                            </tr>
                          )}
                        </>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            ) : crawlJob?.status !== 'running' && (
              <div style={{ textAlign: 'center', padding: '40px 20px', color: 'var(--text-tertiary)', background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)' }}>
                <div style={{ fontSize: 40, marginBottom: 10, opacity: 0.3 }}>🕷️</div>
                <div style={{ fontSize: 13 }}>Noch kein Crawl durchgeführt</div>
                <div style={{ fontSize: 12, marginTop: 4 }}>Klicke auf "Crawler starten" um die Website zu analysieren.</div>
              </div>
            )}
          </div>
        );
  })();
}

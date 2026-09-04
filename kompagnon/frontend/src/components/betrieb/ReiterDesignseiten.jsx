/**
 * Der Design-Reiter der Betriebsansicht (L-25).
 *
 * Am 2026-08-31 aus `CustomerDetail.jsx` herausgeloest — ebenfalls eine
 * sofort aufgerufene Funktion.
 */
import API_BASE_URL from '../../config';

export default function ReiterDesignseiten({
  activeDesignPage,
  designError,
  designResult,
  designRunning,
  designSlow,
  generateDesign,
  h,
  loadSitemapPages,
  loadVersionsForPage,
  pageVersions,
  projectId,
  setActiveDesignPage,
  setActiveTab,
  setDesignResult,
  setPageVersions,
  sitemapLoaded,
  sitemapLoading,
  sitemapPages,
}) {

  if (!sitemapLoaded && !sitemapLoading) loadSitemapPages();
  const PAGE_ICONS = { startseite: '🏠', leistung: '🔧', info: 'ℹ️', vertrauen: '⭐', conversion: '📞', kontakt: '✉️' };
  const contentPages = sitemapPages.filter(p => !p.ist_pflichtseite);

  // Auto-set first page if not set yet
  if (contentPages.length > 0 && !activeDesignPage) {
    const first = contentPages.find(p => p.page_type === 'startseite') || contentPages[0];
    setActiveDesignPage(first);
    if (!pageVersions[first.id]) loadVersionsForPage(first.id);
  }

  if (sitemapLoaded && contentPages.length === 0) {
    return (
      <div style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', padding: 24, textAlign: 'center' }}>
        <div style={{ fontSize: 24, marginBottom: 12 }}>🗺️</div>
        <div style={{ fontSize: 14, fontWeight: 500, color: 'var(--text-primary)', marginBottom: 8 }}>Noch keine Sitemap-Seiten angelegt</div>
        <div style={{ fontSize: 13, color: 'var(--text-tertiary)', marginBottom: 16 }}>Bitte zuerst im Sitemap-Tab die Website-Struktur planen.</div>
        <button onClick={() => setActiveTab('sitemap')} style={{ padding: '8px 16px', background: 'var(--brand-primary)', color: 'var(--text-on-brand)', border: 'none', borderRadius: 'var(--radius-md)', cursor: 'pointer', fontSize: 13, fontWeight: 600 }}>
          Zur Sitemap →
        </button>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

      {/* ── Page tab strip ── */}
      {contentPages.length > 0 && (
        <div style={{ display: 'flex', gap: 0, overflowX: 'auto', WebkitOverflowScrolling: 'touch', scrollbarWidth: 'none', borderBottom: '1px solid var(--border-light)', marginBottom: 4 }}>
          {contentPages.map(page => (
            <button key={page.id}
              onClick={() => {
                setActiveDesignPage(page);
                setDesignResult(null);
                if (!pageVersions[page.id]) loadVersionsForPage(page.id);
              }}
              style={{
                flexShrink: 0, padding: '8px 16px', border: 'none',
                borderBottom: activeDesignPage?.id === page.id ? '2px solid var(--brand-primary)' : '2px solid transparent',
                background: 'none', cursor: 'pointer', fontSize: 13,
                fontWeight: activeDesignPage?.id === page.id ? 600 : 400,
                color: activeDesignPage?.id === page.id ? 'var(--brand-primary)' : 'var(--text-secondary)',
                whiteSpace: 'nowrap', marginBottom: -1, display: 'flex', alignItems: 'center', gap: 5,
              }}>
              {PAGE_ICONS[page.page_type] || '📄'} {page.page_name}
              {(pageVersions[page.id]?.length || 0) > 0 && (
                <span style={{ background: 'var(--brand-primary)', color: 'var(--text-on-brand)', borderRadius: 99, padding: '1px 6px', fontSize: 12 }}>
                  {pageVersions[page.id].length}
                </span>
              )}
            </button>
          ))}
        </div>
      )}

      {/* ── Active page info + generator ── */}
      {activeDesignPage && (
        <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', padding: 20 }}>
          <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 12 }}>🎨 KI-Entwurf generieren</div>

          {/* Active page info box */}
          <div style={{ background: 'var(--bg-app)', border: '1px solid var(--border-light)', borderRadius: 8, padding: '10px 14px', marginBottom: 14, fontSize: 13 }}>
            <div style={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: 4 }}>
              {PAGE_ICONS[activeDesignPage.page_type] || '📄'} {activeDesignPage.page_name}
            </div>
            {activeDesignPage.ziel_keyword && <div style={{ color: 'var(--text-secondary)' }}>🔑 Keyword: <strong>{activeDesignPage.ziel_keyword}</strong></div>}
            {activeDesignPage.zweck && <div style={{ color: 'var(--text-secondary)', marginTop: 2 }}>🎯 Zweck: {activeDesignPage.zweck}</div>}
          </div>

          {!projectId && (
            <div style={{ background: '#FFF9E6', border: '1px solid #F5D87A', borderRadius: 8, padding: '10px 14px', fontSize: 13, color: '#92660A', marginBottom: 12 }}>
              Noch kein verknüpftes Projekt gefunden — bitte zuerst ein Projekt anlegen.
            </div>
          )}
          <button onClick={generateDesign} disabled={designRunning || !projectId}
            style={{ padding: '10px 22px', borderRadius: 8, border: 'none', background: designRunning || !projectId ? 'var(--bg-muted)' : 'var(--brand-primary)', color: designRunning || !projectId ? 'var(--text-tertiary)' : '#fff', fontSize: 14, fontWeight: 600, cursor: designRunning || !projectId ? 'not-allowed' : 'pointer', fontFamily: 'var(--font-sans)', display: 'flex', alignItems: 'center', gap: 8 }}>
            {designRunning && <span style={{ width: 12, height: 12, borderRadius: '50%', border: '2px solid rgba(255,255,255,0.3)', borderTopColor: 'white', animation: 'spin 0.8s linear infinite', display: 'inline-block' }} />}
            {designRunning ? 'Generiere Entwurf…' : '🎨 KI-Entwurf generieren'}
          </button>
          {designSlow && <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginTop: 8 }}>⏳ Claude denkt gründlich nach — das kann bis zu 55 Sekunden dauern…</div>}
          {designError && <div style={{ background: 'var(--status-danger-bg)', border: '1px solid var(--status-danger-text)', borderRadius: 8, padding: '10px 14px', fontSize: 13, color: 'var(--status-danger-text)', marginTop: 12 }}>{designError}</div>}
        </div>
      )}

      {/* ── Result preview ── */}
      {designResult && (
        <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', padding: 20 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
            <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' }}>Generierter Entwurf</div>
            {typeof designResult === 'string' && designResult.startsWith('<') && (
              <button onClick={() => window.open('data:text/html;charset=utf-8,' + encodeURIComponent(designResult), '_blank')}
                style={{ padding: '5px 12px', background: 'var(--bg-app)', border: '1px solid var(--border-medium)', borderRadius: 6, fontSize: 12, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
                👁 Im Browser öffnen
              </button>
            )}
          </div>
          {typeof designResult === 'string' && designResult.trim().startsWith('<') ? (
            <iframe srcDoc={designResult} style={{ width: '100%', height: 600, border: '1px solid var(--border-light)', borderRadius: 8 }} title="Vorschau" />
          ) : (
            <pre style={{ whiteSpace: 'pre-wrap', fontSize: 13, color: 'var(--text-primary)', fontFamily: 'inherit', lineHeight: 1.7, margin: 0 }}>{typeof designResult === 'string' ? designResult : JSON.stringify(designResult, null, 2)}</pre>
          )}
        </div>
      )}

      {/* ── Version history for active page ── */}
      {activeDesignPage && (pageVersions[activeDesignPage.id]?.length || 0) > 0 && (
        <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', padding: 20 }}>
          <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 12 }}>🕓 Versionen — {activeDesignPage.page_name}</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {(pageVersions[activeDesignPage.id] || []).map(v => (
              <div key={v.id} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 12px', background: 'var(--bg-app)', borderRadius: 8, border: '1px solid var(--border-light)', fontSize: 13 }}>
                <div>
                  <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{v.version_name}</span>
                  <span style={{ color: 'var(--text-tertiary)', marginLeft: 10, fontSize: 12 }}>{v.created_at}</span>
                </div>
                <div style={{ display: 'flex', gap: 6 }}>
                  <button onClick={async () => {
                    const res = await fetch(`${API_BASE_URL}/api/designs/version/${v.id}`, { headers: h });
                    if (res.ok) { const d = await res.json(); setDesignResult(d.html_content); }
                  }} style={{ padding: '4px 10px', fontSize: 12, borderRadius: 5, border: '1px solid var(--border-medium)', background: 'var(--bg-surface)', cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
                    👁 Laden
                  </button>
                  <button onClick={async () => {
                    if (!window.confirm('Version löschen?')) return;
                    await fetch(`${API_BASE_URL}/api/designs/version/${v.id}`, { method: 'DELETE', headers: h });
                    setPageVersions(prev => ({ ...prev, [activeDesignPage.id]: prev[activeDesignPage.id].filter(x => x.id !== v.id) }));
                  }} style={{ padding: '4px 10px', fontSize: 12, borderRadius: 5, border: '1px solid var(--status-danger-text)', background: 'transparent', color: 'var(--status-danger-text)', cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
                    🗑
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

    </div>
  );
}

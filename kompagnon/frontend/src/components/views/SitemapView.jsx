/**
 * SitemapView — Übersichts-Karten aller Sitemap-Seiten mit den vom Wireframe-
 * Generator (oder manuell) zugewiesenen Bibliotheks-Blöcken.
 *
 * Props:
 *   projectId            — Project.id
 *   leadId               — für /api/sitemap/{leadId}/pages
 *   wireframeData        — aktueller Wireframe ({pages: [...]}); kann leer sein
 *   onGenerateWireframe  — Callback: startet KI-Wireframe-Job (Schritt D POST)
 *   onNavigateToWireframe — Callback: View-Switcher → Wireframe
 *   onRegenerateSitemap  — Callback: Sitemap neu erzeugen (existing API)
 *
 * Datenquelle:
 *   - Sitemap-Pages aus /api/sitemap/{leadId}/pages
 *   - Block-Zuweisungen aus props.wireframeData (Schritt D Endpoint)
 */
import { useEffect, useMemo, useState } from 'react';
import API_BASE_URL from '../../config';
import { useAuth } from '../../context/AuthContext';

const KC_DARK = '#004F59';
const KC_MID = '#008EAA';
const KC_YELLOW = '#FAE600';

export default function SitemapView({
  projectId,
  leadId,
  wireframeData,
  onGenerateWireframe,
  onNavigateToWireframe,
  onRegenerateSitemap,
}) {
  const { token } = useAuth();
  const headers = useMemo(
    () => ({ Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }),
    [token],
  );

  const [pages, setPages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!leadId) return;
    let cancelled = false;
    setLoading(true);
    // Backend liefert die Pages unter GET /api/sitemap/{lead_id} (returnt
    // direkt ein Array). Den falschen Pfad /pages gibt es nur für POST.
    fetch(`${API_BASE_URL}/api/sitemap/${leadId}`, { headers })
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))))
      .then((data) => {
        if (!cancelled) setPages(Array.isArray(data) ? data : data.pages || []);
      })
      .catch((e) => !cancelled && setError(e.message || 'Sitemap konnte nicht geladen werden'))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [leadId, headers]);

  // Wireframe-Daten pro page_id indexieren für schnellen Lookup
  const blocksByPageId = useMemo(() => {
    const map = new Map();
    (wireframeData?.pages || []).forEach((p) => {
      map.set(p.page_id, (p.blocks || []).slice().sort((a, b) => (a.order ?? 0) - (b.order ?? 0)));
    });
    return map;
  }, [wireframeData]);

  const totalBlocks = (wireframeData?.pages || []).reduce(
    (sum, p) => sum + (p.blocks?.length || 0),
    0,
  );

  return (
    <div style={{ padding: 24, fontFamily: 'var(--font-sans, "Noto Sans", sans-serif)' }}>
      {/* Topbar */}
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: 12,
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: 24,
        }}
      >
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 900, color: KC_DARK, margin: 0, textTransform: 'uppercase', letterSpacing: '-0.02em' }}>
            Sitemap
          </h1>
          <p style={{ fontSize: 13, color: '#64748b', marginTop: 4 }}>
            {pages.length} Seite{pages.length === 1 ? '' : 'n'} · {totalBlocks} Block-Zuweisung{totalBlocks === 1 ? '' : 'en'}
          </p>
        </div>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          <button
            type="button"
            onClick={onRegenerateSitemap}
            style={{
              background: 'transparent',
              color: KC_DARK,
              border: `1.5px solid ${KC_DARK}`,
              borderRadius: 8,
              padding: '9px 16px',
              fontSize: 13,
              fontWeight: 700,
              cursor: 'pointer',
            }}
          >
            Sitemap neu generieren
          </button>
          <button
            type="button"
            onClick={onGenerateWireframe}
            disabled={pages.length === 0}
            style={{
              background: KC_YELLOW,
              color: '#000',
              border: 'none',
              borderRadius: 8,
              padding: '10px 18px',
              fontSize: 13,
              fontWeight: 800,
              cursor: pages.length === 0 ? 'not-allowed' : 'pointer',
              opacity: pages.length === 0 ? 0.5 : 1,
              textTransform: 'uppercase',
              letterSpacing: '0.04em',
            }}
          >
            KI-Wireframe erzeugen
          </button>
          <button
            type="button"
            onClick={onNavigateToWireframe}
            disabled={totalBlocks === 0}
            style={{
              background: KC_MID,
              color: '#fff',
              border: 'none',
              borderRadius: 8,
              padding: '10px 18px',
              fontSize: 13,
              fontWeight: 700,
              cursor: totalBlocks === 0 ? 'not-allowed' : 'pointer',
              opacity: totalBlocks === 0 ? 0.5 : 1,
            }}
          >
            Zu Wireframe →
          </button>
        </div>
      </div>

      {/* Body */}
      {loading && <div style={{ color: '#64748b', fontSize: 14 }}>Sitemap wird geladen…</div>}
      {error && (
        <div style={{ background: '#FEF2F2', color: '#991B1B', padding: 12, borderRadius: 8, fontSize: 13 }}>
          {error}
        </div>
      )}

      {!loading && !error && pages.length === 0 && (
        <div
          style={{
            border: '2px dashed #cbd5e1',
            borderRadius: 16,
            padding: 40,
            textAlign: 'center',
            color: '#64748b',
          }}
        >
          <div style={{ fontSize: 32, marginBottom: 8 }}>🗺</div>
          <div style={{ fontSize: 15, fontWeight: 600, color: KC_DARK, marginBottom: 6 }}>
            Noch keine Sitemap-Seiten
          </div>
          <div style={{ fontSize: 13, marginBottom: 16 }}>
            Generiere eine Sitemap auf Basis von Briefing und Crawl-Ergebnis.
          </div>
          <button
            type="button"
            onClick={onRegenerateSitemap}
            style={{
              background: KC_MID,
              color: '#fff',
              border: 'none',
              borderRadius: 8,
              padding: '10px 18px',
              fontSize: 13,
              fontWeight: 700,
              cursor: 'pointer',
            }}
          >
            Sitemap jetzt generieren
          </button>
        </div>
      )}

      {/* Pages-Grid */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
          gap: 16,
        }}
      >
        {pages.map((page) => {
          const blocks = blocksByPageId.get(page.id) || [];
          const hasBlocks = blocks.length > 0;
          return (
            <article
              key={page.id}
              style={{
                background: '#fff',
                border: '1px solid #e2e8f0',
                borderRadius: 12,
                padding: 18,
                boxShadow: '0 1px 2px rgba(0,0,0,0.03)',
              }}
            >
              <header style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14 }}>
                <span
                  aria-hidden
                  style={{
                    width: 10,
                    height: 10,
                    borderRadius: '50%',
                    background: hasBlocks ? '#1D9E75' : '#cbd5e1',
                    flexShrink: 0,
                  }}
                />
                <h3
                  style={{
                    fontSize: 15,
                    fontWeight: 800,
                    color: KC_DARK,
                    margin: 0,
                    textTransform: 'uppercase',
                    letterSpacing: '-0.01em',
                  }}
                >
                  {page.page_name}
                </h3>
                <span style={{ marginLeft: 'auto', fontSize: 11, color: '#94a3b8' }}>
                  {blocks.length} Block{blocks.length === 1 ? '' : 's'}
                </span>
              </header>

              {hasBlocks ? (
                <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: 6 }}>
                  {blocks.map((b, idx) => (
                    <li
                      key={`${b.slug}-${idx}`}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 8,
                        background: '#f8fafc',
                        border: '1px solid #e2e8f0',
                        borderRadius: 6,
                        padding: '6px 8px',
                        fontSize: 12,
                        color: '#334155',
                      }}
                    >
                      <span
                        style={{
                          fontFamily: 'ui-monospace, SFMono-Regular, monospace',
                          fontSize: 11,
                          background: '#fff',
                          color: KC_MID,
                          border: `1px solid ${KC_MID}`,
                          borderRadius: 4,
                          padding: '2px 6px',
                          fontWeight: 700,
                          flexShrink: 0,
                        }}
                      >
                        {b.slug}
                      </span>
                      <span style={{ color: '#94a3b8', fontSize: 10, marginLeft: 'auto' }}>#{b.order ?? idx}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <div
                  style={{
                    textAlign: 'center',
                    padding: 14,
                    color: '#94a3b8',
                    fontSize: 12,
                    fontStyle: 'italic',
                    background: '#f8fafc',
                    borderRadius: 6,
                    border: '1px dashed #e2e8f0',
                  }}
                >
                  Keine Blöcke — KI-Wireframe erzeugen oder im Wireframe-View hinzufügen.
                </div>
              )}
            </article>
          );
        })}
      </div>
    </div>
  );
}

/**
 * DesignView — Live-Vorschau der Wireframe-Pages mit Style-Guide-Override.
 *
 * Fuehrt drei Datenquellen zusammen:
 *   - Sitemap (sitemapPages): Page-Hierarchie + Pflichtseiten + Page-Type
 *   - Wireframe (wireframeData): Block-Slugs + Slot-Werte pro Page
 *   - Style-Guide (styleGuide): alle Tokens (Farben/Typo/Spacing/UI/Forms/...)
 *
 * Rendert pro aktiver Page das HTML aus der Library-Templates mit Slot-
 * Werten. CSS-Override-Block mappt die neutralen Tailwind-Gray-Klassen
 * (Phase B) auf die Style-Guide-Tokens — die Library bleibt Wireframe-only,
 * das Brand-Design entsteht erst hier zur Render-Zeit.
 *
 * Props:
 *   projectId
 *   sitemapPages          — [{id, page_name, parent_id, page_type, ist_pflichtseite, ...}]
 *   wireframeData         — { pages: [{page_id, page_name, blocks: [...]}] }
 *   styleGuide            — Style-Tokens aus StyleGuideView
 *   approved              — Style-Guide muss freigegeben sein, sonst Lock
 *   onOpenGrapesJS        — Callback (Container öffnet Editor-Modal/Tab)
 *   onNetlifyDeploy       — Callback (Container ruft Deploy-Endpoint)
 */
import { useEffect, useMemo, useState } from 'react';
import API_BASE_URL from '../../config';
import { useAuth } from '../../context/AuthContext';

const KC_DARK = '#004F59';
const KC_MID = '#008EAA';
const KC_YELLOW = '#FAE600';

export default function DesignView({
  projectId,
  sitemapPages = [],
  wireframeData,
  styleGuide,
  approved,
  onOpenGrapesJS,
  onNetlifyDeploy,
}) {
  const { token } = useAuth();
  const headers = useMemo(
    () => ({ Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }),
    [token],
  );

  const wfPages = wireframeData?.pages || [];
  const [activePageId, setActivePageId] = useState(wfPages[0]?.page_id || null);
  const [library, setLibrary] = useState({});
  const [libraryLoading, setLibraryLoading] = useState(false);

  useEffect(() => {
    if (!activePageId && wfPages.length > 0) {
      setActivePageId(wfPages[0].page_id);
    }
  }, [wfPages, activePageId]);

  // Bibliothek laden — nur slugs aus dem aktiven Wireframe
  useEffect(() => {
    const slugs = new Set();
    wfPages.forEach((p) => (p.blocks || []).forEach((b) => slugs.add(b.slug)));
    const missing = [...slugs].filter((s) => !library[s]);
    if (missing.length === 0) return;

    setLibraryLoading(true);
    Promise.all(
      missing.map((slug) =>
        fetch(`${API_BASE_URL}/api/components/${slug}`, { headers })
          .then((r) => (r.ok ? r.json() : null))
          .then((data) => [slug, data])
          .catch(() => [slug, null]),
      ),
    )
      .then((results) => {
        setLibrary((prev) => {
          const next = { ...prev };
          results.forEach(([slug, data]) => {
            if (data) next[slug] = data;
          });
          return next;
        });
      })
      .finally(() => setLibraryLoading(false));
  }, [wfPages, headers, library]);

  // ── Sitemap-Tree: Pages nach parent_id gruppieren ────────────────────────
  const sitemapTree = useMemo(() => {
    const byParent = new Map();
    sitemapPages.forEach((p) => {
      const k = p.parent_id ?? 'root';
      if (!byParent.has(k)) byParent.set(k, []);
      byParent.get(k).push(p);
    });
    byParent.forEach((arr) => arr.sort((a, b) => (a.position ?? 0) - (b.position ?? 0)));
    return byParent;
  }, [sitemapPages]);

  // ── Aggregat-Stats für die Status-Bar oben ───────────────────────────────
  const totalBlocks = wfPages.reduce((s, p) => s + (p.blocks?.length || 0), 0);
  const styleHasOverrides =
    Object.keys(styleGuide?.palette_overrides?.light || {}).length +
    Object.keys(styleGuide?.palette_overrides?.dark || {}).length +
    Object.keys(styleGuide?.semantic_overrides?.light || {}).length +
    Object.keys(styleGuide?.semantic_overrides?.dark || {}).length > 0;

  const activePage = wfPages.find((p) => p.page_id === activePageId) || null;
  const activeSitemapPage = sitemapPages.find((p) => p.id === activePageId) || null;

  // ── Style-CSS-Override-Generator ─────────────────────────────────────────
  // Mapped die Tailwind-Gray-Klassen aus der neutralisierten Library
  // (Phase B) auf die aktuellen Style-Guide-Tokens.
  const overrideCSS = useMemo(() => buildOverrideCSS(styleGuide), [styleGuide]);

  const renderedHTML = useMemo(() => {
    if (!activePage) return '';
    const blocks = (activePage.blocks || []).slice().sort((a, b) => (a.order ?? 0) - (b.order ?? 0));
    const html = blocks
      .map((b) => {
        const tpl = library[b.slug]?.html_template;
        if (!tpl) return `<!-- block ${b.slug} not loaded -->`;
        return fillTemplate(tpl, b.slots || {});
      })
      .join('\n');
    // CSS-Override + Tailwind-CDN ins Vorschau-HTML einbetten
    return `<style>${overrideCSS}</style>${html}`;
  }, [activePage, library, overrideCSS]);

  const exportHTML = () => {
    const fontFamily = styleGuide?.typography?.font_family || 'Noto Sans';
    const blocksHtml = (activePage?.blocks || [])
      .slice().sort((a, b) => (a.order ?? 0) - (b.order ?? 0))
      .map((b) => {
        const tpl = library[b.slug]?.html_template;
        return tpl ? fillTemplate(tpl, b.slots || {}) : '';
      })
      .join('\n');

    const fullHTML = `<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>${activePage?.page_name || 'Seite'}</title>
<script src="https://cdn.tailwindcss.com"></script>
<style>
body { font-family: '${fontFamily}', sans-serif; margin: 0; padding: 0; }
${overrideCSS}
</style>
</head>
<body>
${blocksHtml}
</body>
</html>`;
    const blob = new Blob([fullHTML], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${activePage?.page_name || 'seite'}.html`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // ── Lock-Screen wenn StyleGuide noch nicht freigegeben ────────────────────
  if (!approved) {
    return (
      <div style={{ padding: 60, textAlign: 'center', fontFamily: 'var(--font-sans, "Noto Sans", sans-serif)' }}>
        <div style={{ fontSize: 48, marginBottom: 12 }}>🔒</div>
        <h1 style={{ fontSize: 20, fontWeight: 900, color: KC_DARK, textTransform: 'uppercase', marginBottom: 8 }}>
          Design gesperrt
        </h1>
        <p style={{ fontSize: 14, color: 'var(--text-secondary)', maxWidth: 480, margin: '0 auto', lineHeight: 1.6 }}>
          Bitte zunächst den Style Guide an den Kunden zur Freigabe senden.
          Sobald die Freigabe vorliegt, wird diese Ansicht automatisch entsperrt.
        </p>
      </div>
    );
  }

  if (wfPages.length === 0) {
    return (
      <div style={{ padding: 24, textAlign: 'center', color: 'var(--text-secondary)', fontFamily: 'var(--font-sans, "Noto Sans", sans-serif)' }}>
        <div style={{ fontSize: 32, marginBottom: 8 }}>🖼</div>
        <div style={{ fontSize: 14, color: KC_DARK, fontWeight: 600 }}>
          Noch kein Wireframe — bitte zuerst die Sitemap- und Wireframe-Schritte abschließen.
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', fontFamily: 'var(--font-sans, "Noto Sans", sans-serif)' }}>
      {/* Status-Bar oben — zeigt was aus den 3 Quellen einfließt */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 16, flexWrap: 'wrap',
        padding: '10px 18px',
        background: 'var(--bg-app)', borderBottom: '1px solid var(--border-light)',
        fontSize: 11,
      }}>
        <SourceBadge label="Sitemap" value={`${sitemapPages.length} Page${sitemapPages.length === 1 ? '' : 's'}`} icon="🗺" />
        <SourceBadge label="Wireframe" value={`${totalBlocks} Block${totalBlocks === 1 ? '' : 's'}`} icon="🧱" />
        <SourceBadge label="Style-Guide" value={styleHasOverrides ? 'Custom' : 'Default'} icon="🎨" />
        <div style={{ flex: 1 }} />
        <span style={{ color: 'var(--text-tertiary)', fontSize: 10 }}>
          {libraryLoading ? '⟳ Templates werden geladen…' : 'Live-Vorschau aktualisiert sich automatisch'}
        </span>
      </div>

      <div style={{ flex: 1, display: 'flex', minHeight: 0, overflow: 'hidden' }}>
        {/* Linke Spalte: Sitemap-Tree + Aktionen */}
        <aside style={{
          width: 240, flexShrink: 0,
          background: 'var(--bg-app)', borderRight: '1px solid var(--border-light)',
          padding: 16, overflowY: 'auto',
        }}>
          <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 8 }}>
            Sitemap
          </div>
          {sitemapPages.length === 0 ? (
            // Fallback: flache Liste aus wireframeData wenn keine sitemapPages
            <ul style={{ listStyle: 'none', padding: 0, margin: '0 0 18px 0', display: 'flex', flexDirection: 'column', gap: 2 }}>
              {wfPages.map((p) => (
                <li key={p.page_id}>
                  <PageButton
                    label={p.page_name || `Seite ${p.page_id}`}
                    isActive={p.page_id === activePageId}
                    onClick={() => setActivePageId(p.page_id)}
                  />
                </li>
              ))}
            </ul>
          ) : (
            <div style={{ marginBottom: 18 }}>
              <SitemapTreeNodes
                nodes={sitemapTree.get('root') || []}
                tree={sitemapTree}
                activePageId={activePageId}
                onSelect={setActivePageId}
                wfPagesIds={new Set(wfPages.map((p) => p.page_id))}
                level={0}
              />
            </div>
          )}

          <div style={{
            fontSize: 10, fontWeight: 700, color: 'var(--text-secondary)',
            textTransform: 'uppercase', letterSpacing: '0.1em',
            marginBottom: 8, paddingTop: 16, borderTop: '1px solid var(--border-light)',
          }}>
            Aktionen
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            <button type="button" onClick={() => onOpenGrapesJS?.(activePageId)} style={btnPrimary}>
              In GrapesJS öffnen
            </button>
            <button type="button" onClick={exportHTML} disabled={!renderedHTML}
              style={{ ...btnSecondary, opacity: renderedHTML ? 1 : 0.5, cursor: renderedHTML ? 'pointer' : 'not-allowed' }}>
              HTML exportieren
            </button>
            <button type="button" onClick={() => onNetlifyDeploy?.(projectId)} style={btnAccent}>
              Netlify Deploy
            </button>
          </div>
        </aside>

        {/* Rechte Spalte: Live-Vorschau */}
        <main style={{ flex: 1, overflow: 'auto', background: 'var(--surface)' }}>
          {/* Page-Header in der Vorschau (Breadcrumb aus Sitemap) */}
          {activeSitemapPage && (
            <div style={{
              padding: '10px 18px',
              background: '#fff', borderBottom: '1px solid var(--border-light)',
              fontSize: 11, color: 'var(--text-secondary)',
              display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap',
            }}>
              <Breadcrumb page={activeSitemapPage} sitemapPages={sitemapPages} />
              {activeSitemapPage.ist_pflichtseite && (
                <span title="Pflichtseite" style={{ marginLeft: 4 }}>🔒</span>
              )}
              <span style={{ flex: 1 }} />
              <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: 10, color: 'var(--text-tertiary)' }}>
                /{slugify(activeSitemapPage.page_name)}
              </span>
            </div>
          )}

          <div style={{
            margin: '20px auto',
            background: styleGuide?.colors?.background || styleGuide?.palette?.bg_primary || '#fff',
            color: styleGuide?.colors?.text || '#0a0a0a',
            maxWidth: styleGuide?.spacing?.container || 1200,
            minHeight: '85%',
            boxShadow: '0 4px 16px rgba(0,0,0,0.08)',
            borderRadius: 8, overflow: 'hidden',
            fontFamily: styleGuide?.typography?.font_family || 'Noto Sans',
          }}>
            {renderedHTML ? (
              // eslint-disable-next-line react/no-danger
              <div dangerouslySetInnerHTML={{ __html: renderedHTML }} />
            ) : (
              <div style={{ padding: 60, textAlign: 'center', color: 'var(--text-secondary)' }}>
                {libraryLoading ? 'Vorschau wird gerendert…' : 'Diese Seite hat keine Blöcke.'}
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Source-Badge (Status-Bar oben)
// ─────────────────────────────────────────────────────────────────────────────

function SourceBadge({ label, value, icon }) {
  return (
    <div style={{
      display: 'inline-flex', alignItems: 'center', gap: 6,
      padding: '4px 10px',
      background: '#fff', border: '1px solid var(--border-light)', borderRadius: 6,
    }}>
      <span aria-hidden style={{ fontSize: 12 }}>{icon}</span>
      <span style={{ fontSize: 9, fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
        {label}
      </span>
      <span style={{ fontSize: 11, fontWeight: 700, color: KC_DARK }}>{value}</span>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Sitemap-Tree-Renderer (rekursiv)
// ─────────────────────────────────────────────────────────────────────────────

function SitemapTreeNodes({ nodes, tree, activePageId, onSelect, wfPagesIds, level }) {
  return (
    <ul style={{
      listStyle: 'none', padding: 0, margin: 0,
      display: 'flex', flexDirection: 'column', gap: 2,
    }}>
      {nodes.map((p) => {
        const children = tree.get(p.id) || [];
        const hasWireframe = wfPagesIds.has(p.id);
        return (
          <li key={p.id}>
            <PageButton
              label={p.page_name || `Seite ${p.id}`}
              isActive={p.id === activePageId}
              onClick={() => onSelect(p.id)}
              isPflicht={p.ist_pflichtseite}
              hasWireframe={hasWireframe}
              indent={level}
            />
            {children.length > 0 && (
              <SitemapTreeNodes
                nodes={children} tree={tree}
                activePageId={activePageId} onSelect={onSelect}
                wfPagesIds={wfPagesIds} level={level + 1}
              />
            )}
          </li>
        );
      })}
    </ul>
  );
}

function PageButton({ label, isActive, onClick, isPflicht, hasWireframe = true, indent = 0 }) {
  return (
    <button
      type="button" onClick={onClick}
      title={!hasWireframe ? `${label} — kein Wireframe vorhanden` : label}
      style={{
        width: '100%', textAlign: 'left',
        padding: '6px 10px', paddingLeft: 10 + indent * 14,
        borderRadius: 6, border: 'none',
        background: isActive ? KC_DARK : 'transparent',
        color: isActive ? '#fff' : 'var(--text-secondary)',
        fontSize: 12, fontWeight: isActive ? 700 : 500,
        cursor: 'pointer', fontFamily: 'inherit',
        display: 'flex', alignItems: 'center', gap: 6,
        opacity: hasWireframe ? 1 : 0.55,
      }}
    >
      <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
        {label}
      </span>
      {isPflicht && <span aria-label="Pflichtseite" style={{ fontSize: 10 }}>🔒</span>}
      {!hasWireframe && (
        <span title="Kein Wireframe" style={{ fontSize: 9, opacity: 0.7 }}>—</span>
      )}
    </button>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Breadcrumb in der Vorschau-Topbar
// ─────────────────────────────────────────────────────────────────────────────

function Breadcrumb({ page, sitemapPages }) {
  const path = [];
  let current = page;
  let safety = 10;
  const byId = new Map(sitemapPages.map((p) => [p.id, p]));
  while (current && safety-- > 0) {
    path.unshift(current);
    current = current.parent_id ? byId.get(current.parent_id) : null;
  }
  return (
    <span>
      {path.map((p, i) => (
        <span key={p.id}>
          {i > 0 && <span style={{ color: 'var(--border-medium)', margin: '0 6px' }}>›</span>}
          <span style={{ color: i === path.length - 1 ? KC_DARK : 'var(--text-secondary)', fontWeight: i === path.length - 1 ? 700 : 500 }}>
            {p.page_name}
          </span>
        </span>
      ))}
    </span>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Style-CSS-Override-Generator
// ─────────────────────────────────────────────────────────────────────────────
//
// Mapped die neutralen Tailwind-Gray-Klassen aus der Phase-B-Library auf
// Style-Guide-Tokens (palette + button_variants + card + spacing + typo +
// semantic). Wird zur Render-Zeit als <style>-Block ins Preview-HTML
// eingebettet — die Library bleibt Wireframe-only.

function buildOverrideCSS(styleGuide) {
  if (!styleGuide) return '';
  const palette  = styleGuide.palette  || {};
  const colors   = styleGuide.colors   || {};
  const typo     = styleGuide.typography || {};
  const buttons  = styleGuide.buttons  || {};
  const spacing  = styleGuide.spacing  || {};
  const card     = styleGuide.card     || {};
  const semantic = styleGuide.semantic || {};
  const variants = styleGuide.button_variants || {};

  // Effektive Werte mit Fallback auf legacy colors-Object
  const bg     = palette.bg_primary  || colors.background || '#fff';
  const surf   = palette.bg_surface  || '#f8fafc';
  const text   = palette.text_primary|| colors.text       || '#0a0a0a';
  const muted  = palette.text_muted  || 'var(--text-secondary)';
  const border = palette.border      || '#e2e8f0';
  const acc1   = palette.accent_1    || colors.primary    || '#0a0a0a';
  const acc2   = palette.accent_2    || colors.accent     || '#FAE600';

  const fontBody = typo.font_family  || 'Noto Sans';
  const radiusBtn = buttons.radius   || '8px';
  const radiusCard = (card.radius || spacing.radius || '8px');

  // Primary-Button: bevorzugt button_variants.primary, sonst accent_1
  const btnPrimaryBg = variants.primary?.bg     || acc1;
  const btnPrimaryFg = variants.primary?.fg     || bg;
  const btnPrimaryBorder = variants.primary?.border || acc1;

  return `
/* ─── DesignView Style-Override ─── */
body { font-family: '${fontBody}', sans-serif; color: ${text}; background: ${bg}; }
h1, h2, h3, h4 { color: ${text}; }
p { color: ${text}; }

/* Backgrounds */
.bg-white      { background-color: ${bg} !important; }
.bg-gray-50    { background-color: ${surf} !important; }
.bg-gray-100   { background-color: ${surf} !important; }
.bg-gray-200   { background-color: ${border} !important; }
.bg-gray-700,
.bg-gray-800,
.bg-gray-900   { background-color: ${btnPrimaryBg} !important; }

/* Text-Colors */
.text-gray-900 { color: ${text} !important; }
.text-gray-700 { color: ${text} !important; }
.text-gray-600 { color: ${muted} !important; }
.text-gray-500 { color: ${muted} !important; }
.text-gray-400 { color: ${muted} !important; }

/* Borders */
.border-gray-200, .border-gray-300 { border-color: ${border} !important; }
.divide-gray-200 > :not(:last-child),
.divide-gray-300 > :not(:last-child) { border-color: ${border} !important; }

/* Primary-Buttons (gray-900 bg + white text) */
.bg-gray-900.text-white,
button.bg-gray-900,
.bg-gray-800.text-white {
  background-color: ${btnPrimaryBg} !important;
  color: ${btnPrimaryFg} !important;
  border-color: ${btnPrimaryBorder} !important;
}

/* Akzent-2 (z.B. fuer kleinere CTA-Pills, "Mehr erfahren →") */
.bg-gray-300 { background-color: ${acc2} !important; }

/* Border-Radius */
.rounded, .rounded-md, .rounded-lg { border-radius: ${radiusBtn} !important; }
.rounded-xl, .rounded-2xl { border-radius: ${radiusCard} !important; }
button { border-radius: ${radiusBtn}; }

/* Status-Bedeutungen — ueberlappend mit gray-Klassen sind selten in der
   Library. Wir setzen Custom-Klassen direkt verwendbar. */
.status-success { background: ${semantic.success?.bg}; color: ${semantic.success?.fg}; border: 1px solid ${semantic.success?.border}; }
.status-warn    { background: ${semantic.warn?.bg};    color: ${semantic.warn?.fg};    border: 1px solid ${semantic.warn?.border}; }
.status-error   { background: ${semantic.error?.bg};   color: ${semantic.error?.fg};   border: 1px solid ${semantic.error?.border}; }
.status-info    { background: ${semantic.info?.bg};    color: ${semantic.info?.fg};    border: 1px solid ${semantic.info?.border}; }
`.trim();
}

// ─────────────────────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────────────────────

function fillTemplate(template, slots) {
  return template.replace(/\{\{(\w+)\}\}/g, (match, key) => {
    const val = slots[key];
    if (val === undefined || val === null) return '';
    if (typeof val === 'string' || typeof val === 'number') return escapeHTML(String(val));
    return '';
  });
}

function escapeHTML(s) {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function slugify(s) {
  if (!s) return '';
  return String(s).toLowerCase()
    .replace(/ä/g, 'ae').replace(/ö/g, 'oe').replace(/ü/g, 'ue').replace(/ß/g, 'ss')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

const btnBase = {
  width: '100%',
  border: 'none',
  borderRadius: 8,
  padding: '8px 12px',
  fontSize: 12,
  fontWeight: 700,
  cursor: 'pointer',
  textAlign: 'center',
  fontFamily: 'inherit',
};
const btnPrimary = { ...btnBase, background: KC_DARK, color: '#fff' };
const btnSecondary = { ...btnBase, background: 'transparent', color: KC_DARK, border: `1.5px solid ${KC_DARK}` };
const btnAccent = { ...btnBase, background: KC_YELLOW, color: '#000', textTransform: 'uppercase', letterSpacing: '0.04em' };

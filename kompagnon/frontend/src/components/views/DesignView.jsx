/**
 * DesignView — Live-Vorschau der Wireframe-Seiten mit Style-Guide-Override
 * + Aktionen: GrapesJS öffnen, HTML exportieren, Netlify deployen.
 *
 * Rendert pro aktiver Seite das zusammengesetzte HTML aus den Bibliotheks-
 * Templates mit den slot-Werten aus wireframe_data.
 *
 * Props:
 *   projectId
 *   wireframeData         — { pages: [{page_id, page_name, blocks: [...]}] }
 *   styleGuide            — Style-Tokens aus StyleGuideView
 *   approved              — Style Guide muss freigegeben sein, sonst Lock
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

  const pages = wireframeData?.pages || [];
  const [activePageId, setActivePageId] = useState(pages[0]?.page_id || null);
  const [library, setLibrary] = useState({});  // { slug: { html_template, slots, ... } }
  const [libraryLoading, setLibraryLoading] = useState(false);

  useEffect(() => {
    if (!activePageId && pages.length > 0) {
      setActivePageId(pages[0].page_id);
    }
  }, [pages, activePageId]);

  // Bibliothek laden — nur die slugs die im wireframe_data vorkommen
  useEffect(() => {
    const slugs = new Set();
    pages.forEach((p) => (p.blocks || []).forEach((b) => slugs.add(b.slug)));
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
  }, [pages, headers, library]);

  const activePage = pages.find((p) => p.page_id === activePageId) || null;

  const renderedHTML = useMemo(() => {
    if (!activePage) return '';
    const blocks = (activePage.blocks || []).slice().sort((a, b) => (a.order ?? 0) - (b.order ?? 0));
    return blocks
      .map((b) => {
        const tpl = library[b.slug]?.html_template;
        if (!tpl) {
          return `<!-- block ${b.slug} not loaded -->`;
        }
        return fillTemplate(tpl, b.slots || {});
      })
      .join('\n');
  }, [activePage, library]);

  const exportHTML = () => {
    const fullHTML = `<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>${activePage?.page_name || 'Seite'}</title>
<script src="https://cdn.tailwindcss.com"></script>
<style>body{font-family:'${styleGuide?.typography?.font_family || 'Noto Sans'}',sans-serif;margin:0;padding:0;}</style>
</head>
<body>
${renderedHTML}
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
      <div
        style={{
          padding: 60,
          textAlign: 'center',
          fontFamily: 'var(--font-sans, "Noto Sans", sans-serif)',
        }}
      >
        <div style={{ fontSize: 48, marginBottom: 12 }}>🔒</div>
        <h1 style={{ fontSize: 20, fontWeight: 900, color: KC_DARK, textTransform: 'uppercase', marginBottom: 8 }}>
          Design gesperrt
        </h1>
        <p style={{ fontSize: 14, color: '#64748b', maxWidth: 480, margin: '0 auto', lineHeight: 1.6 }}>
          Bitte zunächst den Style Guide an den Kunden zur Freigabe senden. Sobald die Freigabe vorliegt, wird diese Ansicht automatisch entsperrt.
        </p>
      </div>
    );
  }

  if (pages.length === 0) {
    return (
      <div style={{ padding: 24, textAlign: 'center', color: '#64748b', fontFamily: 'var(--font-sans, "Noto Sans", sans-serif)' }}>
        <div style={{ fontSize: 32, marginBottom: 8 }}>🖼</div>
        <div style={{ fontSize: 14, color: KC_DARK, fontWeight: 600 }}>
          Noch kein Wireframe — bitte zuerst die Sitemap- und Wireframe-Schritte abschließen.
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', height: '100%', fontFamily: 'var(--font-sans, "Noto Sans", sans-serif)' }}>
      {/* Linke Spalte: Steuerung */}
      <aside
        style={{
          width: 200,
          flexShrink: 0,
          background: '#f8fafc',
          borderRight: '1px solid #e2e8f0',
          padding: 16,
          overflowY: 'auto',
        }}
      >
        <div style={{ fontSize: 10, fontWeight: 700, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 8 }}>
          Seiten
        </div>
        <ul style={{ listStyle: 'none', padding: 0, margin: '0 0 18px 0', display: 'flex', flexDirection: 'column', gap: 2 }}>
          {pages.map((p) => (
            <li key={p.page_id}>
              <button
                type="button"
                onClick={() => setActivePageId(p.page_id)}
                style={{
                  width: '100%',
                  textAlign: 'left',
                  padding: '7px 10px',
                  borderRadius: 6,
                  border: 'none',
                  background: p.page_id === activePageId ? KC_DARK : 'transparent',
                  color: p.page_id === activePageId ? '#fff' : '#334155',
                  fontSize: 12,
                  fontWeight: p.page_id === activePageId ? 700 : 500,
                  cursor: 'pointer',
                }}
              >
                {p.page_name || `Seite ${p.page_id}`}
              </button>
            </li>
          ))}
        </ul>

        <div style={{ fontSize: 10, fontWeight: 700, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 8, paddingTop: 14, borderTop: '1px solid #e2e8f0' }}>
          Aktionen
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          <button
            type="button"
            onClick={() => onOpenGrapesJS?.(activePageId)}
            style={btnPrimary}
          >
            In GrapesJS öffnen
          </button>
          <button
            type="button"
            onClick={exportHTML}
            disabled={!renderedHTML}
            style={{ ...btnSecondary, opacity: renderedHTML ? 1 : 0.5, cursor: renderedHTML ? 'pointer' : 'not-allowed' }}
          >
            HTML exportieren
          </button>
          <button
            type="button"
            onClick={() => onNetlifyDeploy?.(projectId)}
            style={btnAccent}
          >
            Netlify Deploy
          </button>
        </div>

        {libraryLoading && (
          <div style={{ marginTop: 14, fontSize: 10, color: '#94a3b8' }}>
            Templates werden geladen…
          </div>
        )}
      </aside>

      {/* Rechte Spalte: Live-Vorschau */}
      <main style={{ flex: 1, overflow: 'auto', background: '#e2e8f0' }}>
        <div
          style={{
            margin: '20px auto',
            background: styleGuide?.colors?.background || '#fff',
            maxWidth: 1200,
            minHeight: '90%',
            boxShadow: '0 4px 16px rgba(0,0,0,0.08)',
            borderRadius: 8,
            overflow: 'hidden',
            fontFamily: styleGuide?.typography?.font_family || 'Noto Sans',
          }}
        >
          {renderedHTML ? (
            // eslint-disable-next-line react/no-danger
            <div dangerouslySetInnerHTML={{ __html: renderedHTML }} />
          ) : (
            <div style={{ padding: 60, textAlign: 'center', color: '#64748b' }}>
              {libraryLoading ? 'Vorschau wird gerendert…' : 'Diese Seite hat keine Blöcke.'}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

// ── Helpers ───────────────────────────────────────────────────────────────────

/**
 * Ersetzt {{key}}-Platzhalter im Template mit slot-Werten.
 * Sicherheit: nur primitive Typen (string/number) werden ersetzt — Objekte
 * würden [object Object] erzeugen, das wäre ein Bug-Signal.
 */
function fillTemplate(template, slots) {
  return template.replace(/\{\{(\w+)\}\}/g, (match, key) => {
    const val = slots[key];
    if (val === undefined || val === null) return '';
    if (typeof val === 'string' || typeof val === 'number') {
      return escapeHTML(String(val));
    }
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

const btnBase = {
  width: '100%',
  border: 'none',
  borderRadius: 8,
  padding: '9px 12px',
  fontSize: 12,
  fontWeight: 700,
  cursor: 'pointer',
  textAlign: 'center',
};
const btnPrimary = { ...btnBase, background: KC_MID, color: '#fff' };
const btnSecondary = { ...btnBase, background: 'transparent', color: KC_DARK, border: `1.5px solid ${KC_DARK}` };
const btnAccent = { ...btnBase, background: KC_YELLOW, color: '#000', textTransform: 'uppercase', letterSpacing: '0.04em' };

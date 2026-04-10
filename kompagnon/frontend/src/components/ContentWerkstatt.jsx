import { useState } from 'react';
import API_BASE_URL from '../config';
import toast from 'react-hot-toast';

export default function ContentWerkstatt({ project, sitemapPages, token, leadId, websiteContent }) {
  const [selectedPage, setSelectedPage] = useState(null);
  const [generating, setGenerating]     = useState(false);
  const [pageContent, setPageContent]   = useState({});
  const [editedContent, setEditedContent] = useState({});

  const headers = {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${token}`,
  };

  const generateContent = async (page) => {
    setGenerating(true);
    try {
      const res = await fetch(
        `${API_BASE_URL}/api/projects/${project.id}/content-workshop/${page.id}`,
        { method: 'POST', headers }
      );
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || 'Generierung fehlgeschlagen');
      }
      const data = await res.json();
      setPageContent(prev => ({ ...prev, [page.id]: data }));
      setSelectedPage(page);
      toast.success(`Content fuer "${page.page_name}" generiert`);
    } catch (e) {
      toast.error(e.message);
    } finally {
      setGenerating(false);
    }
  };

  const setEdit = (pageId, field, value) => {
    setEditedContent(prev => ({
      ...prev,
      [pageId]: { ...(prev[pageId] || {}), [field]: value },
    }));
  };

  const getField = (pageId, field) => {
    return editedContent[pageId]?.[field] ?? pageContent[pageId]?.[field] ?? '';
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '260px 1fr', height: 680, border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', overflow: 'hidden' }}>

      {/* Linke Seiten-Liste */}
      <div style={{ borderRight: '1px solid var(--border-light)', display: 'flex', flexDirection: 'column', overflow: 'hidden', background: 'var(--bg-app)' }}>
        <div style={{ padding: '12px 14px', borderBottom: '1px solid var(--border-light)', fontSize: 11, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.06em' }}>
          Sitemap — {sitemapPages.length} Seiten
        </div>

        <div style={{ flex: 1, overflowY: 'auto' }}>
          {sitemapPages.length === 0 ? (
            <div style={{ padding: 20, fontSize: 12, color: 'var(--text-tertiary)', textAlign: 'center' }}>
              Noch keine Sitemap angelegt.<br />
              Bitte zuerst im Analyse-Tab die Seitenstruktur definieren.
            </div>
          ) : sitemapPages.map(page => {
            const hasContent = !!pageContent[page.id];
            const isSelected = selectedPage?.id === page.id;
            return (
              <div
                key={page.id}
                onClick={() => setSelectedPage(page)}
                style={{
                  padding: '10px 14px',
                  borderBottom: '1px solid var(--border-light)',
                  cursor: 'pointer',
                  background: isSelected ? 'var(--bg-active, var(--bg-elevated))' : 'transparent',
                  borderLeft: `3px solid ${isSelected ? 'var(--brand-primary)' : 'transparent'}`,
                }}
                onMouseEnter={e => { if (!isSelected) e.currentTarget.style.background = 'var(--bg-elevated)'; }}
                onMouseLeave={e => { if (!isSelected) e.currentTarget.style.background = 'transparent'; }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 3 }}>
                  <span style={{ fontSize: 12, fontWeight: 600, color: isSelected ? 'var(--brand-primary)' : 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {page.page_name}
                  </span>
                  {hasContent && <span style={{ fontSize: 10, color: 'var(--status-success-text)', flexShrink: 0 }}>{'\u2713'}</span>}
                </div>
                <span style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>{page.page_type}</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Rechter Content-Bereich */}
      {selectedPage ? (
        <div style={{ overflowY: 'auto', display: 'flex', flexDirection: 'column' }}>

          {/* Header */}
          <div style={{ padding: '14px 20px', borderBottom: '1px solid var(--border-light)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: 'var(--bg-surface)', position: 'sticky', top: 0, zIndex: 1 }}>
            <div>
              <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' }}>{selectedPage.page_name}</div>
              <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>{selectedPage.page_type}{selectedPage.ziel_keyword ? ` · Keyword: ${selectedPage.ziel_keyword}` : ''}</div>
            </div>
            <button
              onClick={() => generateContent(selectedPage)}
              disabled={generating}
              style={{
                padding: '8px 18px', borderRadius: 8, border: 'none',
                background: generating ? 'var(--border-medium)' : 'var(--brand-primary)',
                color: 'white', fontSize: 12, fontWeight: 700,
                cursor: generating ? 'not-allowed' : 'pointer',
                display: 'flex', alignItems: 'center', gap: 6,
                fontFamily: 'var(--font-sans)',
              }}
            >
              {generating ? (
                <><span style={{ width: 12, height: 12, border: '2px solid rgba(255,255,255,.3)', borderTopColor: '#fff', borderRadius: '50%', animation: 'spin .8s linear infinite', display: 'inline-block' }} />Generiert...</>
              ) : pageContent[selectedPage.id] ? 'Neu generieren' : 'KI-Content generieren'}
            </button>
          </div>

          <div style={{ padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: 20 }}>

            {pageContent[selectedPage.id] && (
              <>
                {/* Alter Content */}
                {pageContent[selectedPage.id].old_content && (
                  <div>
                    <CLabel>Alter Content (von bestehender Website)</CLabel>
                    <div style={{ fontSize: 12, color: 'var(--text-secondary)', background: 'var(--bg-app)', borderRadius: 8, padding: '12px 14px', lineHeight: 1.7, maxHeight: 120, overflowY: 'auto', whiteSpace: 'pre-wrap' }}>
                      {pageContent[selectedPage.id].old_content}
                    </div>
                  </div>
                )}

                {/* KI Content — editierbar */}
                <div>
                  <CLabel>KI-Content</CLabel>
                  {[
                    { field: 'headline',    label: 'H1', rows: 1 },
                    { field: 'subheadline', label: 'Unterzeile', rows: 1 },
                    { field: 'intro',       label: 'Einleitung', rows: 3 },
                  ].map(({ field, label, rows }) => (
                    <div key={field} style={{ marginBottom: 12 }}>
                      <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.06em', marginBottom: 4 }}>{label}</div>
                      <textarea
                        value={getField(selectedPage.id, field)}
                        onChange={e => setEdit(selectedPage.id, field, e.target.value)}
                        rows={rows}
                        style={{ width: '100%', padding: '8px 10px', fontSize: 13, border: '1px solid var(--border-light)', borderRadius: 6, background: 'var(--bg-surface)', color: 'var(--text-primary)', fontFamily: 'var(--font-sans)', resize: 'vertical', boxSizing: 'border-box', lineHeight: 1.6 }}
                      />
                    </div>
                  ))}

                  {/* Abschnitte */}
                  {(pageContent[selectedPage.id].sections || []).map((section, i) => (
                    <div key={i} style={{ background: 'var(--bg-app)', borderRadius: 8, padding: '12px 14px', marginBottom: 10 }}>
                      <input
                        value={editedContent[selectedPage.id]?.sections?.[i]?.titel ?? section.titel}
                        onChange={e => {
                          const sections = [...(editedContent[selectedPage.id]?.sections || pageContent[selectedPage.id].sections.map(s => ({...s})))];
                          sections[i] = { ...sections[i], titel: e.target.value };
                          setEdit(selectedPage.id, 'sections', sections);
                        }}
                        style={{ width: '100%', fontSize: 13, fontWeight: 700, border: 'none', background: 'transparent', color: 'var(--text-primary)', fontFamily: 'var(--font-sans)', marginBottom: 8, outline: 'none', boxSizing: 'border-box' }}
                        placeholder="Abschnitt-Titel"
                      />
                      <textarea
                        value={editedContent[selectedPage.id]?.sections?.[i]?.text ?? section.text}
                        onChange={e => {
                          const sections = [...(editedContent[selectedPage.id]?.sections || pageContent[selectedPage.id].sections.map(s => ({...s})))];
                          sections[i] = { ...sections[i], text: e.target.value };
                          setEdit(selectedPage.id, 'sections', sections);
                        }}
                        rows={3}
                        style={{ width: '100%', fontSize: 12, border: 'none', background: 'transparent', color: 'var(--text-secondary)', fontFamily: 'var(--font-sans)', resize: 'vertical', outline: 'none', lineHeight: 1.7, boxSizing: 'border-box' }}
                      />
                    </div>
                  ))}
                </div>

                {/* SEO */}
                <div>
                  <CLabel>SEO-Daten</CLabel>
                  {[
                    { field: 'meta_title',       label: 'Meta-Titel (max. 60 Zeichen)' },
                    { field: 'meta_description', label: 'Meta-Description (max. 155 Zeichen)' },
                    { field: 'cta',              label: 'Call-to-Action Text' },
                  ].map(({ field, label }) => (
                    <div key={field} style={{ marginBottom: 10 }}>
                      <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.06em', marginBottom: 4 }}>{label}</div>
                      <input
                        value={getField(selectedPage.id, field)}
                        onChange={e => setEdit(selectedPage.id, field, e.target.value)}
                        style={{ width: '100%', padding: '7px 10px', fontSize: 12, border: '1px solid var(--border-light)', borderRadius: 6, background: 'var(--bg-surface)', color: 'var(--text-primary)', fontFamily: 'var(--font-sans)', boxSizing: 'border-box' }}
                      />
                    </div>
                  ))}
                </div>
              </>
            )}

            {!pageContent[selectedPage.id] && !generating && (
              <div style={{ textAlign: 'center', padding: '48px 20px', color: 'var(--text-tertiary)' }}>
                <div style={{ fontSize: 40, marginBottom: 12 }}>🤖</div>
                <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 6 }}>Noch kein Content generiert</div>
                <div style={{ fontSize: 13 }}>
                  KI-Content generieren — Claude analysiert den bestehenden
                  Website-Content und schreibt ihn neu.
                </div>
              </div>
            )}
          </div>
        </div>
      ) : (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-tertiary)', fontSize: 13 }}>
          Seite aus der Liste auswaehlen
        </div>
      )}
    </div>
  );
}

function CLabel({ children }) {
  return (
    <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.08em', marginBottom: 8 }}>
      {children}
    </div>
  );
}

import { useState } from 'react';
import API_BASE_URL from '../config';
import toast from 'react-hot-toast';

const CONTENT_TABS = [
  { id: 'sitemap',    label: 'Sitemap',        icon: '🗺️', desc: 'Seitenstruktur' },
  { id: 'inhalte',    label: 'Seiteninhalte',   icon: '📄', desc: 'Texte & KI' },
  { id: 'assets',     label: 'Bilder & Assets', icon: '🖼️', desc: 'Medien je Seite' },
  { id: 'freigaben',  label: 'Freigaben',       icon: '✅', desc: 'Kunden-Freigaben' },
];

export default function ContentWerkstatt({ project, sitemapPages, sitemapLoading, token, leadId, websiteContent }) {
  const [activeTab, setActiveTab]       = useState('sitemap');
  const [selectedPage, setSelectedPage] = useState(null);
  const [generating, setGenerating]     = useState(false);
  const [pageContent, setPageContent]   = useState({});
  const [editedContent, setEditedContent] = useState({});
  const [newContent, setNewContent]     = useState({});

  const headers = { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` };

  const generateContent = async (page) => {
    setGenerating(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/projects/${project.id}/content-workshop/${page.id}`, { method: 'POST', headers });
      if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || 'Fehler');
      const data = await res.json();
      setPageContent(prev => ({ ...prev, [page.id]: data }));
      setSelectedPage(page);
      setActiveTab('inhalte');
      toast.success(`Content fuer "${page.page_name}" generiert`);
    } catch (e) { toast.error(e.message); }
    finally { setGenerating(false); }
  };

  const getField = (pageId, field) => editedContent[pageId]?.[field] ?? pageContent[pageId]?.[field] ?? '';
  const setEdit = (pageId, field, value) => setEditedContent(prev => ({ ...prev, [pageId]: { ...(prev[pageId] || {}), [field]: value } }));

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>

      {/* Unter-Tab-Navigation */}
      <div style={{ display: 'flex', background: 'var(--bg-app)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', overflow: 'hidden', marginBottom: 12 }}>
        {CONTENT_TABS.map((tab, i) => {
          const isActive = activeTab === tab.id;
          return (
            <button key={tab.id} onClick={() => setActiveTab(tab.id)} style={{
              flex: 1, padding: '10px 8px 8px', border: 'none',
              borderRight: i < CONTENT_TABS.length - 1 ? '1px solid var(--border-light)' : 'none',
              borderBottom: isActive ? '3px solid var(--brand-primary)' : '3px solid transparent',
              background: isActive ? 'var(--bg-active, var(--bg-elevated))' : 'transparent',
              cursor: 'pointer', fontFamily: 'var(--font-sans)',
              display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2,
            }}>
              <span style={{ fontSize: 18 }}>{tab.icon}</span>
              <span style={{ fontSize: 12, fontWeight: isActive ? 700 : 500, color: isActive ? 'var(--brand-primary)' : 'var(--text-primary)' }}>{tab.label}</span>
              <span style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>{tab.desc}</span>
            </button>
          );
        })}
      </div>

      {/* TAB 1: SITEMAP */}
      {activeTab === 'sitemap' && (
        <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', overflow: 'hidden' }}>
          <div style={{ padding: '14px 18px', borderBottom: '1px solid var(--border-light)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)' }}>Seitenstruktur — {sitemapPages.length} Seiten</div>
            <button onClick={() => setActiveTab('inhalte')} disabled={sitemapPages.length === 0}
              style={{ padding: '6px 14px', borderRadius: 6, border: 'none', background: sitemapPages.length > 0 ? 'var(--brand-primary)' : 'var(--border-medium)', color: '#fff', fontSize: 12, fontWeight: 600, cursor: sitemapPages.length > 0 ? 'pointer' : 'not-allowed', fontFamily: 'var(--font-sans)' }}>
              Zu Seiteninhalten
            </button>
          </div>

          {sitemapLoading ? (
            <div style={{ display: 'flex', justifyContent: 'center', padding: 32 }}>
              <div style={{ width: 24, height: 24, borderRadius: '50%', border: '2px solid var(--border-light)', borderTopColor: 'var(--brand-primary)', animation: 'spin .8s linear infinite' }} />
            </div>
          ) : sitemapPages.length === 0 ? (
            <div style={{ padding: 32, textAlign: 'center', color: 'var(--text-tertiary)' }}>
              <div style={{ fontSize: 32, marginBottom: 10 }}>🗺️</div>
              <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 6 }}>Noch keine Sitemap angelegt</div>
              <div style={{ fontSize: 12, marginBottom: 16 }}>Definiere zuerst die Seitenstruktur der neuen Website.</div>
            </div>
          ) : (
            <div>
              <div style={{ display: 'grid', gridTemplateColumns: '40px 1fr 120px 140px 100px', gap: 0, padding: '8px 16px', background: 'var(--bg-app)', fontSize: 10, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.06em', borderBottom: '1px solid var(--border-light)' }}>
                <div>#</div><div>Seite</div><div>Typ</div><div>Content-Status</div><div>Aktion</div>
              </div>
              {sitemapPages.map((page, idx) => {
                const hasContent = !!pageContent[page.id];
                return (
                  <div key={page.id} style={{ display: 'grid', gridTemplateColumns: '40px 1fr 120px 140px 100px', gap: 0, padding: '10px 16px', borderBottom: '1px solid var(--border-light)', alignItems: 'center' }}>
                    <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>{idx + 1}</div>
                    <div>
                      <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)' }}>{page.page_name}</div>
                      {page.ziel_keyword && <div style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>Keyword: {page.ziel_keyword}</div>}
                    </div>
                    <div><span style={{ fontSize: 10, padding: '2px 8px', borderRadius: 99, background: 'var(--bg-elevated)', color: 'var(--text-secondary)', fontWeight: 600 }}>{page.page_type || 'info'}</span></div>
                    <div><span style={{ fontSize: 10, padding: '2px 8px', borderRadius: 99, fontWeight: 600, background: hasContent ? 'var(--status-success-bg)' : 'var(--bg-elevated)', color: hasContent ? 'var(--status-success-text)' : 'var(--text-tertiary)' }}>{hasContent ? 'Generiert' : 'Ausstehend'}</span></div>
                    <div>
                      <button onClick={() => { setSelectedPage(page); generateContent(page); }} disabled={generating}
                        style={{ fontSize: 11, padding: '4px 10px', borderRadius: 6, border: '1px solid var(--border-light)', background: 'var(--bg-surface)', color: 'var(--brand-primary)', cursor: generating ? 'not-allowed' : 'pointer', fontFamily: 'var(--font-sans)', fontWeight: 600 }}>
                        {hasContent ? 'Neu' : 'KI'}
                      </button>
                    </div>
                  </div>
                );
              })}
              <div style={{ padding: '12px 16px', borderTop: '1px solid var(--border-light)', display: 'flex', gap: 10 }}>
                <button onClick={async () => { for (const page of sitemapPages) { await generateContent(page); await new Promise(r => setTimeout(r, 500)); } }}
                  disabled={generating || sitemapPages.length === 0}
                  style={{ padding: '8px 18px', borderRadius: 8, border: 'none', background: 'var(--brand-primary)', color: '#fff', fontSize: 12, fontWeight: 700, cursor: generating ? 'not-allowed' : 'pointer', fontFamily: 'var(--font-sans)', display: 'flex', alignItems: 'center', gap: 6 }}>
                  {generating ? (<><span style={{ width: 12, height: 12, border: '2px solid rgba(255,255,255,.3)', borderTopColor: '#fff', borderRadius: '50%', animation: 'spin .8s linear infinite', display: 'inline-block' }} />Generiert...</>) : `Alle ${sitemapPages.length} Seiten generieren`}
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* TAB 2: SEITENINHALTE — Master-Detail */}
      {activeTab === 'inhalte' && (
        <div style={{ display: 'grid', gridTemplateColumns: '240px 1fr', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', overflow: 'hidden', height: 640 }}>
          <div style={{ borderRight: '1px solid var(--border-light)', display: 'flex', flexDirection: 'column', background: 'var(--bg-app)' }}>
            <div style={{ padding: '10px 14px', borderBottom: '1px solid var(--border-light)', fontSize: 10, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.06em' }}>{sitemapPages.length} Seiten</div>
            <div style={{ flex: 1, overflowY: 'auto' }}>
              {sitemapPages.map(page => {
                const hasContent = !!pageContent[page.id];
                const isSelected = selectedPage?.id === page.id;
                return (
                  <div key={page.id} onClick={() => setSelectedPage(page)}
                    style={{ padding: '10px 14px', borderBottom: '1px solid var(--border-light)', cursor: 'pointer', background: isSelected ? 'var(--bg-active, var(--bg-elevated))' : 'transparent', borderLeft: `3px solid ${isSelected ? 'var(--brand-primary)' : 'transparent'}` }}
                    onMouseEnter={e => { if (!isSelected) e.currentTarget.style.background = 'var(--bg-elevated)'; }}
                    onMouseLeave={e => { if (!isSelected) e.currentTarget.style.background = 'transparent'; }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontSize: 12, fontWeight: 600, color: isSelected ? 'var(--brand-primary)' : 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{page.page_name}</span>
                      {hasContent && <span style={{ fontSize: 10, color: 'var(--status-success-text)', flexShrink: 0, marginLeft: 4 }}>{'\u2713'}</span>}
                    </div>
                    <div style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>{page.page_type}</div>
                  </div>
                );
              })}
            </div>
          </div>

          {selectedPage ? (
            <div style={{ overflowY: 'auto', display: 'flex', flexDirection: 'column' }}>
              <div style={{ padding: '12px 18px', borderBottom: '1px solid var(--border-light)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: 'var(--bg-surface)', position: 'sticky', top: 0, zIndex: 1 }}>
                <div>
                  <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' }}>{selectedPage.page_name}</div>
                  <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>{selectedPage.page_type}{selectedPage.ziel_keyword ? ` · ${selectedPage.ziel_keyword}` : ''}</div>
                </div>
                <button onClick={() => generateContent(selectedPage)} disabled={generating}
                  style={{ padding: '7px 16px', borderRadius: 8, border: 'none', background: generating ? 'var(--border-medium)' : 'var(--brand-primary)', color: '#fff', fontSize: 12, fontWeight: 700, cursor: generating ? 'not-allowed' : 'pointer', fontFamily: 'var(--font-sans)', display: 'flex', alignItems: 'center', gap: 6 }}>
                  {generating ? (<><span style={{ width: 11, height: 11, border: '2px solid rgba(255,255,255,.3)', borderTopColor: '#fff', borderRadius: '50%', animation: 'spin .8s linear infinite', display: 'inline-block' }} />Generiert...</>) : pageContent[selectedPage.id] ? 'Neu generieren' : 'KI generieren'}
                </button>
              </div>

              <div style={{ padding: '18px 20px', display: 'flex', flexDirection: 'column', gap: 18 }}>
                {pageContent[selectedPage.id]?.old_content && (
                  <div>
                    <FieldLabel>Alter Content (von bestehender Website)</FieldLabel>
                    <div style={{ fontSize: 12, color: 'var(--text-secondary)', background: 'var(--bg-app)', borderRadius: 8, padding: '10px 12px', lineHeight: 1.7, maxHeight: 100, overflowY: 'auto', whiteSpace: 'pre-wrap', borderLeft: '3px solid var(--border-medium)' }}>
                      {pageContent[selectedPage.id].old_content}
                    </div>
                  </div>
                )}

                {pageContent[selectedPage.id] && (
                  <div>
                    <FieldLabel>KI-Content</FieldLabel>
                    {[
                      { field: 'headline', label: 'H1', rows: 1 },
                      { field: 'subheadline', label: 'Unterzeile', rows: 1 },
                      { field: 'intro', label: 'Einleitung', rows: 3 },
                    ].map(({ field, label, rows }) => (
                      <div key={field} style={{ marginBottom: 10 }}>
                        <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.06em', marginBottom: 4 }}>{label}</div>
                        <textarea value={getField(selectedPage.id, field)} onChange={e => setEdit(selectedPage.id, field, e.target.value)} rows={rows}
                          style={{ width: '100%', padding: '7px 10px', fontSize: 13, border: '1px solid var(--border-light)', borderRadius: 6, background: 'var(--bg-surface)', color: 'var(--text-primary)', fontFamily: 'var(--font-sans)', resize: 'vertical', boxSizing: 'border-box', lineHeight: 1.6 }} />
                      </div>
                    ))}
                    {(pageContent[selectedPage.id].sections || []).map((section, i) => (
                      <div key={i} style={{ background: 'var(--bg-app)', borderRadius: 8, padding: '10px 12px', marginBottom: 8, borderLeft: '3px solid var(--brand-primary-mid, var(--border-medium))' }}>
                        <input value={editedContent[selectedPage.id]?.sections?.[i]?.titel ?? section.titel}
                          onChange={e => { const secs = [...(editedContent[selectedPage.id]?.sections || pageContent[selectedPage.id].sections.map(s => ({...s})))]; secs[i] = { ...secs[i], titel: e.target.value }; setEdit(selectedPage.id, 'sections', secs); }}
                          style={{ width: '100%', fontSize: 13, fontWeight: 700, border: 'none', background: 'transparent', color: 'var(--text-primary)', fontFamily: 'var(--font-sans)', marginBottom: 6, outline: 'none', boxSizing: 'border-box' }} placeholder="Abschnitt-Titel" />
                        <textarea value={editedContent[selectedPage.id]?.sections?.[i]?.text ?? section.text}
                          onChange={e => { const secs = [...(editedContent[selectedPage.id]?.sections || pageContent[selectedPage.id].sections.map(s => ({...s})))]; secs[i] = { ...secs[i], text: e.target.value }; setEdit(selectedPage.id, 'sections', secs); }}
                          rows={3} style={{ width: '100%', fontSize: 12, border: 'none', background: 'transparent', color: 'var(--text-secondary)', fontFamily: 'var(--font-sans)', resize: 'vertical', outline: 'none', lineHeight: 1.7, boxSizing: 'border-box' }} />
                      </div>
                    ))}
                  </div>
                )}

                <div>
                  <FieldLabel>Eigene Ergaenzungen</FieldLabel>
                  <textarea value={newContent[selectedPage.id] || ''} onChange={e => setNewContent(prev => ({ ...prev, [selectedPage.id]: e.target.value }))}
                    rows={4} placeholder="Eigene Texte, Ergaenzungen oder Hinweise fuer diese Seite"
                    style={{ width: '100%', padding: '10px 12px', fontSize: 12, border: '1px dashed var(--border-medium)', borderRadius: 8, background: 'var(--bg-app)', color: 'var(--text-primary)', fontFamily: 'var(--font-sans)', resize: 'vertical', boxSizing: 'border-box', lineHeight: 1.7 }} />
                </div>

                {pageContent[selectedPage.id] && (
                  <div>
                    <FieldLabel>SEO</FieldLabel>
                    {[{ field: 'meta_title', label: 'Meta-Titel (max. 60 Z.)' }, { field: 'meta_description', label: 'Meta-Description (max. 155 Z.)' }, { field: 'cta', label: 'Call-to-Action' }].map(({ field, label }) => (
                      <div key={field} style={{ marginBottom: 8 }}>
                        <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.06em', marginBottom: 4 }}>{label}</div>
                        <input value={getField(selectedPage.id, field)} onChange={e => setEdit(selectedPage.id, field, e.target.value)}
                          style={{ width: '100%', padding: '7px 10px', fontSize: 12, border: '1px solid var(--border-light)', borderRadius: 6, background: 'var(--bg-surface)', color: 'var(--text-primary)', fontFamily: 'var(--font-sans)', boxSizing: 'border-box' }} />
                      </div>
                    ))}
                  </div>
                )}

                {!pageContent[selectedPage.id] && !generating && (
                  <div style={{ textAlign: 'center', padding: '32px 20px', color: 'var(--text-tertiary)' }}>
                    <div style={{ fontSize: 36, marginBottom: 10 }}>🤖</div>
                    <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 6 }}>Noch kein KI-Content generiert</div>
                    <div style={{ fontSize: 12 }}>KI generieren klicken — Claude nimmt den alten Content und schreibt ihn neu.</div>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-tertiary)', fontSize: 13 }}>Seite aus der Liste waehlen</div>
          )}
        </div>
      )}

      {/* TAB 3: BILDER & ASSETS */}
      {activeTab === 'assets' && (
        <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', overflow: 'hidden' }}>
          <div style={{ padding: '14px 18px', borderBottom: '1px solid var(--border-light)', fontSize: 13, fontWeight: 700, color: 'var(--text-primary)' }}>Bilder & Assets — Zuordnung zu Seiten</div>
          {sitemapPages.length === 0 ? (
            <div style={{ padding: 32, textAlign: 'center', color: 'var(--text-tertiary)', fontSize: 13 }}>Erst Sitemap anlegen</div>
          ) : sitemapPages.map(page => (
            <details key={page.id} style={{ borderBottom: '1px solid var(--border-light)' }}>
              <summary style={{ padding: '12px 18px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 10, listStyle: 'none', userSelect: 'none' }}>
                <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>{page.page_name}</span>
                <span style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>{page.page_type}</span>
              </summary>
              <div style={{ padding: '0 18px 16px', display: 'flex', flexDirection: 'column', gap: 10 }}>
                {(() => {
                  const pageData = (websiteContent || []).find(p => p.url?.includes(page.page_name?.toLowerCase().replace(/ /g, '-')) || p.h1?.toLowerCase().includes(page.page_name?.toLowerCase()));
                  const imgs = Array.isArray(pageData?.images) ? pageData.images : [];
                  return imgs.length > 0 ? (
                    <div>
                      <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.06em', marginBottom: 8 }}>Gecrawlte Bilder ({imgs.length})</div>
                      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                        {imgs.slice(0, 8).map((src, j) => {
                          const imgSrc = typeof src === 'string' ? src : src?.src || '';
                          return (
                            <div key={j} style={{ width: 64, height: 64, borderRadius: 8, border: '1px solid var(--border-light)', overflow: 'hidden', background: 'var(--bg-app)' }}>
                              <img src={imgSrc} alt="" loading="lazy" style={{ width: '100%', height: '100%', objectFit: 'cover' }} onError={e => { e.target.parentNode.style.display = 'none'; }} />
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  ) : (
                    <div style={{ fontSize: 12, color: 'var(--text-tertiary)', fontStyle: 'italic' }}>Keine Bilder aus Crawler fuer diese Seite gefunden</div>
                  );
                })()}
                <div style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>Eigene Bilder hochladen: im Analyse-Tab unter Zugangsdaten / Dateien</div>
              </div>
            </details>
          ))}
        </div>
      )}

      {/* TAB 4: FREIGABEN */}
      {activeTab === 'freigaben' && (
        <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', overflow: 'hidden' }}>
          <div style={{ padding: '14px 18px', borderBottom: '1px solid var(--border-light)', fontSize: 13, fontWeight: 700, color: 'var(--text-primary)' }}>Content-Freigaben je Seite</div>
          {sitemapPages.length === 0 ? (
            <div style={{ padding: 32, textAlign: 'center', color: 'var(--text-tertiary)', fontSize: 13 }}>Erst Sitemap anlegen</div>
          ) : sitemapPages.map(page => {
            const hasContent = !!pageContent[page.id];
            return (
              <div key={page.id} style={{ padding: '12px 18px', borderBottom: '1px solid var(--border-light)', display: 'flex', alignItems: 'center', gap: 14 }}>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)' }}>{page.page_name}</div>
                  <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>{page.page_type}</div>
                </div>
                <span style={{ fontSize: 11, fontWeight: 600, padding: '3px 10px', borderRadius: 99, background: hasContent ? 'var(--status-warning-bg)' : 'var(--bg-elevated)', color: hasContent ? 'var(--status-warning-text)' : 'var(--text-tertiary)' }}>
                  {hasContent ? 'Freigabe ausstehend' : 'Content fehlt'}
                </span>
                {hasContent && (
                  <button style={{ padding: '5px 12px', borderRadius: 6, border: '1px solid var(--border-light)', background: 'var(--bg-surface)', color: 'var(--brand-primary)', fontSize: 11, fontWeight: 600, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
                    Freigabe anfordern
                  </button>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function FieldLabel({ children }) {
  return <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.08em', marginBottom: 8 }}>{children}</div>;
}

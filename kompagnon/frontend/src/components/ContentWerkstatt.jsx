import { useState, useRef, useEffect } from 'react';
import API_BASE_URL from '../config';
import toast from 'react-hot-toast';

const CONTENT_TABS = [
  { id: 'inhalte',    label: 'Seiteninhalte',   icon: '📄', desc: 'Texte & KI' },
  { id: 'assets',     label: 'Bilder & Assets', icon: '🖼️', desc: 'Medien je Seite' },
  { id: 'freigaben',  label: 'Freigaben',       icon: '✅', desc: 'Kunden-Freigaben' },
];

export default function ContentWerkstatt({ project, sitemapPages, sitemapLoading, token, leadId, websiteContent }) {
  const [activeTab, setActiveTab]       = useState('inhalte');
  const [selectedPage, setSelectedPage] = useState(null);
  const [generating, setGenerating]     = useState(false);
  const [pageContent, setPageContent]   = useState({});
  const [editedContent, setEditedContent] = useState({});
  const [newContent, setNewContent]     = useState({});
  const [queueRunning, setQueueRunning]         = useState(false);
  const [queueDone, setQueueDone]               = useState(0);
  const [queueStop, setQueueStop]               = useState(false);
  const [saveStatus, setSaveStatus]             = useState('idle');
  const [queueCurrentPage, setQueueCurrentPage] = useState('');
  // Optimierung #3 — Batch-Generierung aller Seiten in einem Claude-Call
  const [generatingAll, setGeneratingAll]     = useState(false);
  const [allGenProgress, setAllGenProgress]   = useState({ done: 0, total: 0 });
  const queueStopRef = useRef(false);

  useEffect(() => {
    if (queueStop) { queueStopRef.current = true; setQueueStop(false); }
  }, [queueStop]);

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

  const generateAllContent = async () => {
    if (sitemapPages.length === 0) return;
    setQueueRunning(true);
    setQueueDone(0);
    queueStopRef.current = false;
    for (let i = 0; i < sitemapPages.length; i++) {
      if (queueStopRef.current) { toast('Generierung gestoppt', { icon: '\u25A0' }); break; }
      const page = sitemapPages[i];
      setQueueCurrentPage(page.page_name);
      try { await generateContent(page); } catch { /* weiter */ }
      setQueueDone(i + 1);
      if (i < sitemapPages.length - 1 && !queueStopRef.current) {
        await new Promise(r => setTimeout(r, 1000));
      }
    }
    setQueueRunning(false);
    setQueueCurrentPage('');
    if (!queueStopRef.current) toast.success('Alle Seiten generiert!');
  };

  const saveCurrentContent = async (pageId) => {
    if (!pageId) return;
    const edited = editedContent[pageId];
    const base = pageContent[pageId];
    if (!edited && !newContent[pageId]) return;
    setSaveStatus('saving');
    try {
      await fetch(`${API_BASE_URL}/api/projects/${project.id}/page-content/${pageId}`, {
        method: 'PUT', headers,
        body: JSON.stringify({ content: { ...(base || {}), ...(edited || {}) }, new_content: newContent[pageId] || '' }),
      });
      setSaveStatus('saved');
      setTimeout(() => setSaveStatus('idle'), 2500);
    } catch {
      setSaveStatus('error');
      setTimeout(() => setSaveStatus('idle'), 3000);
    }
  };

  const handlePageSelect = async (page) => {
    if (selectedPage && selectedPage.id !== page.id) {
      await saveCurrentContent(selectedPage.id);
    }
    setSelectedPage(page);
  };

  // Auto-save every 30s
  useEffect(() => {
    if (!selectedPage) return;
    const interval = setInterval(() => saveCurrentContent(selectedPage.id), 30000);
    return () => clearInterval(interval);
  }, [selectedPage?.id, editedContent, newContent]); // eslint-disable-line

  // Hydrate pageContent from sitemap pages' ki_* columns on mount/update.
  // Wenn der Batch-Endpoint vorher gelaufen ist, kommen ki_h1/ki_hero_text/
  // ki_abschnitt_text via GET /api/sitemap/{leadId} zurueck. Wir mappen sie
  // in das Schema, das die bestehende Detail-Ansicht erwartet (headline,
  // intro, sections[0].text, cta, meta_*). Nur Seiten, fuer die noch kein
  // pageContent existiert, werden hydriert — das schuetzt gerade frisch
  // generierten Content aus dem Einzelseiten-Endpoint.
  useEffect(() => {
    if (!Array.isArray(sitemapPages) || sitemapPages.length === 0) return;
    setPageContent(prev => {
      let changed = false;
      const next = { ...prev };
      for (const p of sitemapPages) {
        if (next[p.id]) continue;
        if (!p.content_generated && !p.ki_h1 && !p.ki_hero_text) continue;
        next[p.id] = {
          headline:         p.ki_h1 || '',
          subheadline:      '',
          intro:            p.ki_hero_text || '',
          sections:         p.ki_abschnitt_text
            ? [{ titel: 'Details', text: p.ki_abschnitt_text }]
            : [],
          cta:              p.ki_cta || '',
          meta_title:       p.ki_meta_title || '',
          meta_description: p.ki_meta_description || '',
        };
        changed = true;
      }
      return changed ? next : prev;
    });
  }, [sitemapPages]);

  // Optimierung #3 — Alle Seiten in einem einzigen Claude-Call generieren.
  const handleGenerateAll = async () => {
    if (!sitemapPages || sitemapPages.length === 0) {
      toast.error('Keine Sitemap-Seiten vorhanden. Zuerst Sitemap anlegen.');
      return;
    }
    if (!window.confirm(
      `Alle ${sitemapPages.length} Seiten mit KI-Texten befüllen? ` +
      'Bestehende KI-Texte werden überschrieben.'
    )) return;

    setGeneratingAll(true);
    setAllGenProgress({ done: 0, total: sitemapPages.length });
    try {
      const res = await fetch(
        `${API_BASE_URL}/api/projects/${project.id}/content-workshop/generate-all`,
        { method: 'POST', headers },
      );
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.detail || 'Fehler beim Generieren');

      setAllGenProgress({ done: data.pages_generated || 0, total: sitemapPages.length });
      toast.success(`${data.pages_generated || 0} Seiten erfolgreich generiert!`);

      // Lokalen pageContent-State im bestehenden Schema aktualisieren,
      // damit die Detail-Ansicht die neuen Texte sofort anzeigt — ohne
      // auf einen Sitemap-Reload zu warten.
      if (data.results && Array.isArray(data.results)) {
        setPageContent(prev => {
          const next = { ...prev };
          for (const item of data.results) {
            if (!item?.page_id) continue;
            next[item.page_id] = {
              headline:         item.h1 || '',
              subheadline:      '',
              intro:            item.hero_text || '',
              sections:         item.abschnitt_text
                ? [{ titel: 'Details', text: item.abschnitt_text }]
                : [],
              cta:              item.cta || '',
              meta_title:       item.meta_title || '',
              meta_description: item.meta_description || '',
            };
          }
          return next;
        });
        // Edits zu bereits gerenderten Seiten verwerfen — die neuen KI-Texte
        // sind der frische Stand, alte Edits wuerden sonst wieder darueber-
        // gestuelpt via getField().
        setEditedContent({});
      }
    } catch (err) {
      toast.error(err.message || 'Generierung fehlgeschlagen');
    } finally {
      setGeneratingAll(false);
    }
  };

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


      {/* TAB 2: SEITENINHALTE — Master-Detail */}
      {activeTab === 'inhalte' && (
        <>
          {/* Batch-Generierung-Toolbar (Optimierung #3) */}
          <div style={{
            display: 'flex', alignItems: 'center', gap: 12,
            padding: '10px 14px', marginBottom: 10,
            background: 'var(--bg-surface)',
            border: '1px solid var(--border-light)',
            borderRadius: 'var(--radius-lg)',
            flexWrap: 'wrap',
          }}>
            <div style={{ flex: 1, minWidth: 180 }}>
              <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-primary)' }}>
                Alle Seiten auf einmal generieren
              </div>
              <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 2 }}>
                Ein Claude-Call schreibt Texte für alle {sitemapPages?.length || 0} Seiten — spart 30–45 Min. manuelle Klicks.
              </div>
            </div>
            <button
              onClick={handleGenerateAll}
              disabled={generatingAll || !sitemapPages?.length}
              style={{
                padding: '8px 16px',
                borderRadius: 8,
                border: 'none',
                background: generatingAll ? '#6B7280' : (!sitemapPages?.length ? 'var(--border-medium)' : '#7c3aed'),
                color: '#fff',
                fontSize: 13,
                fontWeight: 700,
                cursor: generatingAll || !sitemapPages?.length ? 'not-allowed' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                fontFamily: 'var(--font-sans)',
                flexShrink: 0,
              }}
            >
              {generatingAll ? (
                <>
                  <span style={{
                    width: 11, height: 11,
                    border: '2px solid rgba(255,255,255,.3)',
                    borderTopColor: '#fff', borderRadius: '50%',
                    animation: 'spin .8s linear infinite',
                    display: 'inline-block',
                  }} />
                  Generiere… {allGenProgress.total > 0 && `(${allGenProgress.total} Seiten)`}
                </>
              ) : (
                <>
                  🤖 Alle {sitemapPages?.length || 0} Seiten generieren
                </>
              )}
            </button>
          </div>

        <div style={{ display: 'grid', gridTemplateColumns: '240px 1fr', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', overflow: 'hidden', height: 640 }}>
          <div style={{ borderRight: '1px solid var(--border-light)', display: 'flex', flexDirection: 'column', background: 'var(--bg-app)' }}>
            <div style={{ padding: '10px 14px', borderBottom: '1px solid var(--border-light)', fontSize: 10, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.06em' }}>{sitemapPages.length} Seiten</div>
            <div style={{ flex: 1, overflowY: 'auto' }}>
              {sitemapPages.map(page => {
                const hasContent = !!pageContent[page.id];
                const isSelected = selectedPage?.id === page.id;
                return (
                  <div key={page.id} onClick={() => handlePageSelect(page)}
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
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11, minWidth: 90 }}>
                  {saveStatus === 'saving' && (<><span style={{ width: 10, height: 10, border: '1.5px solid var(--border-medium)', borderTopColor: 'var(--brand-primary)', borderRadius: '50%', animation: 'spin .7s linear infinite', display: 'inline-block', flexShrink: 0 }} /><span style={{ color: 'var(--text-tertiary)' }}>Speichert...</span></>)}
                  {saveStatus === 'saved' && <span style={{ color: 'var(--status-success-text)', fontWeight: 600 }}>Gespeichert</span>}
                  {saveStatus === 'error' && <span style={{ color: 'var(--status-danger-text)' }}>Speicherfehler</span>}
                </div>
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
        </>
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

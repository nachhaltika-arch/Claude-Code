/**
 * Der Sitemap-Reiter der Betriebsansicht (L-25).
 *
 * Am 2026-08-31 aus `CustomerDetail.jsx` herausgeloest. Er stand dort als
 * **sofort aufgerufene Funktion** — die Form, an der der erste Anlauf am
 * 30.08. gescheitert ist: Ihr Vorspann (`if (!geladen) lade()`, die drei
 * Tabellen) gehoert vor das `return`, nicht daneben.
 */
import toast from 'react-hot-toast';

export default function ReiterSitemap({
  isMobile,
  addPageForm,
  addPageOpen,
  addPageSaving,
  createPage,
  downloadSitemapPdf,
  editPageForm,
  editPageModal,
  editPageSaving,
  generateKI,
  kiConfirm,
  kiGenerating,
  leadId,
  loadSitemapPages,
  saveEditPage,
  setActiveDesignPage,
  setActiveTab,
  setAddPageForm,
  setAddPageOpen,
  setEditPageForm,
  setEditPageModal,
  setEditingPage,
  setKiConfirm,
  sitemapLoaded,
  sitemapLoading,
  sitemapPages,
}) {

  if (!sitemapLoaded && !sitemapLoading) loadSitemapPages();
  const ST = {
    geplant:        { bg: '#EFF6FF', text: '#1D4ED8', label: 'Geplant' },
    in_bearbeitung: { bg: '#FEF9C3', text: '#92400E', label: 'In Bearb.' },
    freigegeben:    { bg: '#FEF3C7', text: '#B45309', label: 'Freigegeben' },
    live:           { bg: '#DCFCE7', text: '#166534', label: 'Live' },
  };
  const TI = { startseite: '🏠', leistung: '🔧', info: 'ℹ️', vertrauen: '⭐', conversion: '📞', sonstige: '📄' };
  const PAGE_TYPES = [
    { v: 'startseite', l: 'Startseite' }, { v: 'leistung', l: 'Leistung' },
    { v: 'info', l: 'Info' }, { v: 'vertrauen', l: 'Vertrauen' },
    { v: 'conversion', l: 'Conversion' }, { v: 'sonstige', l: 'Sonstige' },
  ];
  const inp = { width: '100%', padding: '7px 10px', fontSize: 13, border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)', background: 'var(--bg-surface)', color: 'var(--text-primary)', fontFamily: 'var(--font-sans)', boxSizing: 'border-box' };
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
      {/* Action buttons */}
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        <button onClick={() => setAddPageOpen(o => !o)}
          style={{ padding: '8px 16px', background: 'var(--brand-primary)', color: 'var(--text-on-brand)', border: 'none', borderRadius: 'var(--radius-md)', fontSize: 13, fontWeight: 600, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
          ➕ Seite hinzufügen
        </button>
        <button onClick={() => setKiConfirm(true)} disabled={kiGenerating || !leadId}
          style={{ padding: '8px 16px', background: 'var(--bg-surface)', color: 'var(--text-primary)', border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)', fontSize: 13, cursor: 'pointer', fontFamily: 'var(--font-sans)', opacity: kiGenerating ? 0.6 : 1 }}>
          {kiGenerating ? '⏳ Generiere…' : '🤖 KI-Vorlage laden'}
        </button>
        <button onClick={downloadSitemapPdf} disabled={!leadId}
          style={{ padding: '8px 16px', background: 'var(--bg-surface)', color: 'var(--text-primary)', border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)', fontSize: 13, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
          📄 PDF herunterladen
        </button>
      </div>

      {/* KI Confirm */}
      {kiConfirm && (
        <div style={{ background: '#FFF9E6', border: '1px solid #F5D87A', borderRadius: 'var(--radius-md)', padding: '12px 16px', fontSize: 13, color: '#92660A', display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
          <span style={{ flex: 1 }}>⚠️ KI-Vorlage überschreibt alle vorhandenen (Nicht-Pflicht-)Seiten.</span>
          <button onClick={generateKI} style={{ padding: '6px 14px', background: 'var(--warn)', color: 'var(--kc-black)', border: 'none', borderRadius: 6, fontSize: 12, fontWeight: 600, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>Ja, generieren</button>
          <button onClick={() => setKiConfirm(false)} style={{ padding: '6px 14px', background: 'var(--bg-surface)', color: 'var(--text-secondary)', border: '1px solid var(--border-medium)', borderRadius: 6, fontSize: 12, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>Abbrechen</button>
        </div>
      )}

      {/* Add page form */}
      {addPageOpen && (
        <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-lg)', padding: 16, display: 'flex', flexDirection: 'column', gap: 10 }}>
          <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 2 }}>Neue Seite anlegen</div>
          <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr 1fr', gap: 10 }}>
            <div>
              <label style={{ fontSize: 11, color: 'var(--text-tertiary)', display: 'block', marginBottom: 4 }}>Seitenname *</label>
              <input aria-label="Seitenname" value={addPageForm.page_name} onChange={e => setAddPageForm(f => ({ ...f, page_name: e.target.value }))} placeholder="z.B. Leistungen" style={inp} />
            </div>
            <div>
              <label style={{ fontSize: 11, color: 'var(--text-tertiary)', display: 'block', marginBottom: 4 }}>Typ</label>
              <select aria-label="Typ" value={addPageForm.page_type} onChange={e => setAddPageForm(f => ({ ...f, page_type: e.target.value }))} style={inp}>
                {PAGE_TYPES.map(t => <option key={t.v} value={t.v}>{t.l}</option>)}
              </select>
            </div>
            <div>
              <label style={{ fontSize: 11, color: 'var(--text-tertiary)', display: 'block', marginBottom: 4 }}>Übergeordnete Seite</label>
              <select aria-label="Übergeordnete Seite" value={addPageForm.parent_id} onChange={e => setAddPageForm(f => ({ ...f, parent_id: e.target.value }))} style={inp}>
                <option value="">– Keine –</option>
                {sitemapPages.filter(p => !p.ist_pflichtseite).map(p => <option key={p.id} value={p.id}>{p.page_name}</option>)}
              </select>
            </div>
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button onClick={createPage} disabled={addPageSaving || !addPageForm.page_name.trim()}
              style={{ padding: '7px 16px', background: 'var(--brand-primary)', color: 'var(--text-on-brand)', border: 'none', borderRadius: 6, fontSize: 13, fontWeight: 600, cursor: 'pointer', fontFamily: 'var(--font-sans)', opacity: addPageSaving ? 0.6 : 1 }}>
              {addPageSaving ? 'Speichert…' : '💾 Anlegen'}
            </button>
            <button onClick={() => setAddPageOpen(false)}
              style={{ padding: '7px 14px', background: 'var(--bg-app)', color: 'var(--text-secondary)', border: '1px solid var(--border-medium)', borderRadius: 6, fontSize: 13, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
              Abbrechen
            </button>
          </div>
        </div>
      )}

      {/* Page list */}
      <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', overflow: 'hidden' }}>
        {sitemapLoading ? (
          <div style={{ padding: 32, textAlign: 'center' }}>
            <div style={{ width: 28, height: 28, borderRadius: '50%', border: '3px solid var(--border-light)', borderTopColor: 'var(--brand-primary)', animation: 'spin 0.8s linear infinite', margin: '0 auto' }} />
          </div>
        ) : sitemapPages.filter(p => !p.ist_pflichtseite).length === 0 ? (
          <div style={{ padding: '40px 20px', textAlign: 'center', color: 'var(--text-tertiary)' }}>
            <div style={{ fontSize: 36, marginBottom: 8, opacity: 0.3 }}>🗺️</div>
            <div style={{ fontSize: 13 }}>Noch keine Seiten geplant.</div>
          </div>
        ) : (
          <>
            {sitemapPages.filter(p => !p.ist_pflichtseite).map(page => {
              const st = ST[page.status] || ST.geplant;
              return (
                <div key={page.id} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '10px 14px', borderBottom: '1px solid var(--border-light)', flexWrap: 'wrap' }}>
                  <span style={{ fontSize: 17, flexShrink: 0 }}>{TI[page.page_type] || '📄'}</span>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{page.page_name}</div>
                    {page.ziel_keyword && <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 1 }}>{page.ziel_keyword}</div>}
                  </div>
                  <span style={{ fontSize: 11, fontWeight: 600, padding: '2px 7px', borderRadius: 10, background: st.bg, color: st.text, whiteSpace: 'nowrap', flexShrink: 0 }}>{st.label}</span>
                  {/* Action buttons */}
                  {(() => {
                    const aBtn = (bg, color) => ({
                      padding: '5px 11px', fontSize: 12, fontWeight: 500,
                      background: bg, color, border: 'none',
                      borderRadius: 'var(--radius-md)', cursor: 'pointer',
                      fontFamily: 'var(--font-sans)', whiteSpace: 'nowrap',
                    });
                    return (
                      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                        <button
                          onClick={() => { setEditPageModal(page); setEditPageForm({ page_name: page.page_name, page_type: page.page_type, ziel_keyword: page.ziel_keyword || '', zweck: page.zweck || '', cta_text: page.cta_text || '', status: page.status || 'geplant' }); }}
                          style={aBtn('#1a2332', '#fff')}>
                          ✏️ Bearbeiten
                        </button>
                        <button
                          onClick={() => { setActiveDesignPage(page); setActiveTab('design'); }}
                          style={aBtn('var(--brand-primary)', '#fff')}>
                          🎨 Design
                        </button>
                        <button
                          onClick={() => { setActiveDesignPage(page); setActiveTab('design'); }}
                          style={aBtn('#059669', '#fff')}>
                          📝 Content
                        </button>
                        <button
                          onClick={() => {
                            if (page.mockup_html) {
                              const w = window.open('', '_blank');
                              w.document.write(page.mockup_html);
                              w.document.close();
                            } else {
                              toast.error('Noch kein Design für diese Seite');
                            }
                          }}
                          style={aBtn('var(--bg-elevated)', 'var(--text-primary)')}>
                          👁 Vorschau
                        </button>
                        <button
                          onClick={() => setEditingPage(page)}
                          style={aBtn('#7c3aed', '#fff')}>
                          🖊️ Editor
                        </button>
                      </div>
                    );
                  })()}
                </div>
              );
            })}
            {sitemapPages.filter(p => p.ist_pflichtseite).map((page, idx, arr) => {
              const st = ST[page.status] || ST.geplant;
              return (
                <div key={page.id} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 14px', borderBottom: idx < arr.length - 1 ? '1px solid var(--border-light)' : 'none', background: 'var(--bg-app)' }}>
                  <span style={{ fontSize: 15, flexShrink: 0, color: 'var(--text-tertiary)' }}>🔒</span>
                  <span style={{ flex: 1, fontSize: 13, fontWeight: 600, color: 'var(--text-tertiary)' }}>{page.page_name}</span>
                  <span style={{ fontSize: 10, fontWeight: 700, padding: '2px 7px', borderRadius: 10, background: '#F3F4F6', color: '#6B7280' }}>⚖️ Pflicht</span>
                  <span style={{ fontSize: 11, fontWeight: 600, padding: '2px 7px', borderRadius: 10, background: st.bg, color: st.text }}>{st.label}</span>
                </div>
              );
            })}
            <div style={{ padding: '8px 14px', fontSize: 11, color: 'var(--text-tertiary)', borderTop: '1px solid var(--border-light)' }}>
              4 Pflichtseiten werden von KOMPAGNON rechtskonform befüllt.
            </div>
          </>
        )}
      </div>

      {/* Edit page modal */}
      {editPageModal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', zIndex: 1000, display: 'flex', alignItems: isMobile ? 'flex-end' : 'center', justifyContent: 'center', padding: isMobile ? 0 : 20 }}
          onClick={e => e.target === e.currentTarget && setEditPageModal(null)}>
          <div style={{ background: 'var(--bg-surface)', borderRadius: isMobile ? '16px 16px 0 0' : 'var(--radius-xl)', padding: 24, width: '100%', maxWidth: 480, maxHeight: isMobile ? '92vh' : '85vh', overflowY: 'auto' }}
            onClick={e => e.stopPropagation()}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
              <span style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' }}>Seite bearbeiten</span>
              <button onClick={() => setEditPageModal(null)} style={{ background: 'none', border: 'none', fontSize: 20, cursor: 'pointer', color: 'var(--text-tertiary)' }}>×</button>
            </div>
            {[
              { k: 'page_name', label: 'Seitenname', type: 'text' },
              { k: 'ziel_keyword', label: 'Ziel-Keyword', type: 'text' },
              { k: 'zweck', label: 'Zweck / Beschreibung', type: 'textarea' },
              { k: 'cta_text', label: 'CTA-Text', type: 'text' },
            ].map(f => (
              <div key={f.k} style={{ marginBottom: 12 }}>
                <label style={{ fontSize: 11, color: 'var(--text-tertiary)', display: 'block', marginBottom: 4 }}>{f.label}</label>
                {f.type === 'textarea'
                  ? <textarea aria-label={f.label} value={editPageForm[f.k] || ''} onChange={e => setEditPageForm(p => ({ ...p, [f.k]: e.target.value }))} rows={3} style={{ ...inp, resize: 'vertical' }} />
                  : <input aria-label={f.label} type="text" value={editPageForm[f.k] || ''} onChange={e => setEditPageForm(p => ({ ...p, [f.k]: e.target.value }))} style={inp} />
                }
              </div>
            ))}
            <div style={{ marginBottom: 16 }}>
              <label style={{ fontSize: 11, color: 'var(--text-tertiary)', display: 'block', marginBottom: 4 }}>Typ</label>
              <select aria-label="Typ" value={editPageForm.page_type || 'info'} onChange={e => setEditPageForm(p => ({ ...p, page_type: e.target.value }))} style={inp}>
                {PAGE_TYPES.map(t => <option key={t.v} value={t.v}>{t.l}</option>)}
              </select>
            </div>
            <div style={{ marginBottom: 20 }}>
              <label style={{ fontSize: 11, color: 'var(--text-tertiary)', display: 'block', marginBottom: 4 }}>Status</label>
              <select aria-label="Status" value={editPageForm.status || 'geplant'} onChange={e => setEditPageForm(p => ({ ...p, status: e.target.value }))} style={inp}>
                <option value="geplant">Geplant</option>
                <option value="in_bearbeitung">In Bearbeitung</option>
                <option value="freigegeben">Freigegeben</option>
                <option value="live">Live</option>
              </select>
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
              <button onClick={saveEditPage} disabled={editPageSaving}
                style={{ flex: 1, padding: '10px', background: 'var(--brand-primary)', color: 'var(--text-on-brand)', border: 'none', borderRadius: 'var(--radius-md)', fontSize: 13, fontWeight: 600, cursor: 'pointer', fontFamily: 'var(--font-sans)', opacity: editPageSaving ? 0.6 : 1 }}>
                {editPageSaving ? 'Speichert…' : '💾 Speichern'}
              </button>
              <button onClick={() => setEditPageModal(null)}
                style={{ flex: 1, padding: '10px', background: 'var(--bg-app)', color: 'var(--text-secondary)', border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)', fontSize: 13, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
                Abbrechen
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

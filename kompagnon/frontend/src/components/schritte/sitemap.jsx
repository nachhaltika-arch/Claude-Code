/**
 * Die Sitemap-Schritte des Online-Editors.
 *
 * **Warum eigene Datei (L-25, 22.08.2026).** `ProzessFlow.jsx` hatte 2.307
 * Zeilen. 493 davon waren tot — `PHASEN`, `ALLE_SCHRITTE` und die
 * Standardkomponente, die niemand importierte. Der Rest bestand aus einem
 * Verteiler (`SchrittInhalt`) und siebzehn Einbettungen, die je einen
 * Schritt des Online-Editors anzeigen.
 *
 * Geschnitten ist nach **Thema**, nicht nach Groesse: Die Einbettungen
 * teilen untereinander nichts ausser den Bibliotheks-Importen — nachgemessen
 * vor dem Schnitt. `SchrittInhalt` bleibt in `ProzessFlow.jsx` und holt sie
 * von hier.
 */
import API_BASE_URL from '../../config';
import { aufTaste } from '../../utils/tastaturBedienung';
import { useState } from 'react';


export function SitemapEditorEmbed({ pages, leadId, headers, onReload }) {
  const [selectedId, setSelectedId] = useState(null);
  const [addOpen, setAddOpen]       = useState(false);
  const [addName, setAddName]       = useState('');
  const [addType, setAddType]       = useState('info');
  const [addParent, setAddParent]   = useState('');
  const [saving, setSaving]         = useState(false);
  const [editField, setEditField]   = useState(null); // { field, value }

  const contentPages = pages.filter(p => !p.ist_pflichtseite);
  const pflichtPages = pages.filter(p => p.ist_pflichtseite);
  const allPages     = [...contentPages, ...pflichtPages];
  const selected     = allPages.find(p => p.id === selectedId);

  const PAGE_TYPES = ['startseite', 'leistung', 'info', 'vertrauen', 'conversion', 'rechtlich'];
  const STATUSES = [
    { value: 'geplant',      label: 'Geplant',       color: 'var(--text-tertiary)',       bg: 'var(--bg-elevated)' },
    { value: 'in_arbeit',    label: 'In Arbeit',     color: '#854D0E',                    bg: '#FEF9C3' },
    { value: 'entwurf',      label: 'Entwurf',       color: '#7c3aed',                    bg: '#f3e8ff' },
    { value: 'review',       label: 'Zur Pruefung',  color: 'var(--text-brand)',                    bg: '#E6F6FA' },
    { value: 'freigegeben',  label: 'Freigegeben',   color: 'var(--success)',                    bg: '#dcfce7' },
  ];

  const makeSlug = (name) => name.toLowerCase().replace(/[äa]/g,'ae').replace(/[öo]/g,'oe').replace(/[üu]/g,'ue').replace(/ß/g,'ss').replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'');
  const pagePath = (p) => {
    if (!p) return '/';
    const slug = makeSlug(p.page_name);
    if (p.page_type === 'startseite') return '/';
    if (p.parent_id) {
      const parent = allPages.find(pp => pp.id === p.parent_id);
      return parent ? `/${makeSlug(parent.page_name)}/${slug}` : `/${slug}`;
    }
    return `/${slug}`;
  };

  const jsonHeaders = { ...headers, 'Content-Type': 'application/json' };

  const savePage = async (id, data) => {
    setSaving(true);
    await fetch(`${API_BASE_URL}/api/sitemap/pages/${id}`, { method: 'PUT', headers: jsonHeaders, body: JSON.stringify(data) });
    setSaving(false);
    setEditField(null);
    onReload();
  };

  const deletePage = async (id) => {
    if (selectedId === id) setSelectedId(null);
    await fetch(`${API_BASE_URL}/api/sitemap/pages/${id}`, { method: 'DELETE', headers });
    onReload();
  };

  const addPage = async () => {
    if (!addName.trim()) return;
    setSaving(true);
    await fetch(`${API_BASE_URL}/api/sitemap/${leadId}/pages`, {
      method: 'POST', headers: jsonHeaders,
      body: JSON.stringify({ page_name: addName.trim(), page_type: addType, parent_id: addParent ? Number(addParent) : null, position: contentPages.length }),
    });
    setAddName(''); setAddType('info'); setAddParent(''); setAddOpen(false);
    setSaving(false);
    onReload();
  };

  const moveUp = async (idx) => {
    if (idx === 0) return;
    const reordered = [...contentPages];
    [reordered[idx - 1], reordered[idx]] = [reordered[idx], reordered[idx - 1]];
    await fetch(`${API_BASE_URL}/api/sitemap/${leadId}/reorder`, {
      method: 'PUT', headers: jsonHeaders,
      body: JSON.stringify(reordered.map((p, i) => ({ id: p.id, position: i, parent_id: p.parent_id || null }))),
    });
    onReload();
  };

  const moveDown = async (idx) => {
    if (idx >= contentPages.length - 1) return;
    const reordered = [...contentPages];
    [reordered[idx], reordered[idx + 1]] = [reordered[idx + 1], reordered[idx]];
    await fetch(`${API_BASE_URL}/api/sitemap/${leadId}/reorder`, {
      method: 'PUT', headers: jsonHeaders,
      body: JSON.stringify(reordered.map((p, i) => ({ id: p.id, position: i, parent_id: p.parent_id || null }))),
    });
    onReload();
  };

  const uploadTemplate = async (pageId, file) => {
    const text = await file.text();
    await savePage(pageId, { mockup_html: text });
  };

  const statusOf = (s) => STATUSES.find(st => st.value === s) || STATUSES[0];
  const inputStyle = { width: '100%', padding: '7px 10px', fontSize: 12, border: '1px solid var(--border-light)', borderRadius: 6, background: 'var(--bg-app)', color: 'var(--text-primary)', fontFamily: 'var(--font-sans)', outline: 'none', boxSizing: 'border-box' };
  const btnSm = { padding: '4px 8px', fontSize: 12, border: 'none', borderRadius: 4, cursor: 'pointer', fontFamily: 'var(--font-sans)' };

  return (
    <div style={{ display: 'flex', minHeight: 480 }}>

      {/* ── Linke Spalte: Seitenliste ── */}
      <div style={{ width: 300, borderRight: '1px solid var(--border-light)', display: 'flex', flexDirection: 'column', flexShrink: 0 }}>
        <div style={{ padding: '14px 16px', borderBottom: '1px solid var(--border-light)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-primary)' }}>{allPages.length} Seiten</span>
          <button onClick={() => setAddOpen(!addOpen)} style={{ ...btnSm, background: 'var(--brand-primary)', color: 'var(--text-on-brand)', fontWeight: 700, padding: '5px 12px' }}>+ Neu</button>
        </div>

        {addOpen && (
          <div style={{ padding: 12, borderBottom: '1px solid var(--border-light)', background: 'var(--bg-app)', display: 'flex', flexDirection: 'column', gap: 8 }}>
            <input aria-label="Seitenname..." value={addName} onChange={e => setAddName(e.target.value)} placeholder="Seitenname..." style={inputStyle} autoFocus onKeyDown={e => e.key === 'Enter' && addPage()} />
            <div style={{ display: 'flex', gap: 6 }}>
              <select aria-label="Seitentyp" value={addType} onChange={e => setAddType(e.target.value)} style={{ ...inputStyle, flex: 1 }}>
                {PAGE_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
              </select>
              <select aria-label="Uebergeordnete Seite" value={addParent} onChange={e => setAddParent(e.target.value)} style={{ ...inputStyle, flex: 1 }}>
                <option value="">Hauptseite</option>
                {contentPages.map(p => <option key={p.id} value={p.id}>↳ {p.page_name}</option>)}
              </select>
            </div>
            <div style={{ display: 'flex', gap: 6 }}>
              <button onClick={addPage} disabled={saving || !addName.trim()} style={{ ...btnSm, background: 'var(--success)', color: 'var(--text-on-brand)', fontWeight: 700, padding: '5px 14px' }}>Anlegen</button>
              <button onClick={() => setAddOpen(false)} style={{ ...btnSm, background: 'var(--border-light)', color: 'var(--text-secondary)' }}>Abb.</button>
            </div>
          </div>
        )}

        <div style={{ flex: 1, overflowY: 'auto' }}>
          {contentPages.map((p, idx) => {
            const st = statusOf(p.status);
            const isSel = selectedId === p.id;
            return (
              <div key={p.id} onClick={() => setSelectedId(p.id)} style={{
                padding: '10px 14px', cursor: 'pointer', borderBottom: '1px solid var(--border-light)',
                background: isSel ? `${st.bg}` : 'transparent',
                borderLeft: isSel ? `3px solid ${st.color}` : '3px solid transparent',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 3 }}>
                  {p.parent_id && <span style={{ fontSize: 9, color: 'var(--text-tertiary)' }}>↳</span>}
                  <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{p.page_name}</span>
                  <div style={{ display: 'flex', gap: 2, flexShrink: 0 }}>
                    <button onClick={e => { e.stopPropagation(); moveUp(idx); }} disabled={idx === 0} style={{ ...btnSm, background: 'transparent', color: idx === 0 ? 'var(--border-light)' : 'var(--text-tertiary)', fontSize: 12, padding: '2px 4px' }}>↑</button>
                    <button onClick={e => { e.stopPropagation(); moveDown(idx); }} disabled={idx >= contentPages.length - 1} style={{ ...btnSm, background: 'transparent', color: idx >= contentPages.length - 1 ? 'var(--border-light)' : 'var(--text-tertiary)', fontSize: 12, padding: '2px 4px' }}>↓</button>
                  </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <span style={{ fontSize: 12, color: 'var(--text-tertiary)', fontFamily: 'monospace' }}>{pagePath(p)}</span>
                  <span style={{ marginLeft: 'auto', fontSize: 9, padding: '1px 6px', borderRadius: 99, background: st.bg, color: st.color, fontWeight: 600, flexShrink: 0 }}>{st.label}</span>
                </div>
              </div>
            );
          })}

          {pflichtPages.length > 0 && (
            <>
              <div style={{ padding: '8px 14px', fontSize: 9, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.06em', borderBottom: '1px solid var(--border-light)', background: 'var(--bg-app)' }}>Pflichtseiten</div>
              {pflichtPages.map(p => (
                <div role="button" tabIndex={0} onKeyDown={aufTaste(() => setSelectedId(p.id))} key={p.id} onClick={() => setSelectedId(p.id)} style={{
                  padding: '8px 14px', cursor: 'pointer', borderBottom: '1px solid var(--border-light)',
                  background: selectedId === p.id ? 'var(--bg-app)' : 'transparent', opacity: 0.7,
                }}>
                  <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{p.page_name} 🔒</div>
                  <div style={{ fontSize: 12, color: 'var(--text-tertiary)', fontFamily: 'monospace' }}>{pagePath(p)}</div>
                </div>
              ))}
            </>
          )}
        </div>
      </div>

      {/* ── Rechte Spalte: Detail-Panel ── */}
      <div style={{ flex: 1, overflow: 'auto' }}>
        {selected ? (
          <div style={{ padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: 16 }}>
            {/* Header */}
            <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12 }}>
              <div>
                <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)' }}>{selected.page_name}</div>
                <div style={{ fontSize: 12, color: 'var(--text-tertiary)', fontFamily: 'monospace', marginTop: 2 }}>{pagePath(selected)}</div>
              </div>
              {!selected.ist_pflichtseite && (
                <button onClick={() => deletePage(selected.id)} style={{ ...btnSm, color: 'var(--status-danger-text)', background: 'var(--status-danger-bg)', padding: '5px 12px' }}>Loeschen</button>
              )}
            </div>

            {/* Status */}
            <div>
              <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.06em', marginBottom: 6 }}>Status</div>
              <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                {STATUSES.map(st => (
                  <button key={st.value} onClick={() => savePage(selected.id, { status: st.value })}
                    style={{
                      padding: '6px 14px', borderRadius: 99, fontSize: 12, fontWeight: 600, cursor: 'pointer', fontFamily: 'var(--font-sans)',
                      background: selected.status === st.value ? st.color : st.bg,
                      color: selected.status === st.value ? '#fff' : st.color,
                      border: `1px solid ${st.color}`, transition: 'all .15s',
                    }}>
                    {st.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Felder-Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px 20px' }}>
              {/* Seitenname */}
              <div>
                <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.06em', marginBottom: 4 }}>Seitenname</div>
                {editField?.field === 'page_name' ? (
                  <div style={{ display: 'flex', gap: 4 }}>
                    <input aria-label="Seitenname" value={editField.value} onChange={e => setEditField({ ...editField, value: e.target.value })} style={inputStyle} autoFocus onKeyDown={e => e.key === 'Enter' && savePage(selected.id, { page_name: editField.value })} />
                    <button onClick={() => savePage(selected.id, { page_name: editField.value })} style={{ ...btnSm, background: 'var(--success)', color: 'var(--text-on-brand)' }}>✓</button>
                  </div>
                ) : (
                  <div role="button" tabIndex={0} onKeyDown={aufTaste(() => !selected.ist_pflichtseite && setEditField({ field: 'page_name', value: selected.page_name }))} onClick={() => !selected.ist_pflichtseite && setEditField({ field: 'page_name', value: selected.page_name })} style={{ fontSize: 13, color: 'var(--text-primary)', cursor: selected.ist_pflichtseite ? 'default' : 'pointer', padding: '4px 0' }}>{selected.page_name}</div>
                )}
              </div>

              {/* Seitentyp */}
              <div>
                <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.06em', marginBottom: 4 }}>Typ</div>
                <select aria-label="Typ" value={selected.page_type} onChange={e => savePage(selected.id, { page_type: e.target.value })} disabled={selected.ist_pflichtseite} style={inputStyle}>
                  {PAGE_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
                </select>
              </div>

              {/* Keyword */}
              <div>
                <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.06em', marginBottom: 4 }}>Ziel-Keyword</div>
                {editField?.field === 'ziel_keyword' ? (
                  <div style={{ display: 'flex', gap: 4 }}>
                    <input aria-label="Ziel-Keyword" value={editField.value} onChange={e => setEditField({ ...editField, value: e.target.value })} style={inputStyle} autoFocus onKeyDown={e => e.key === 'Enter' && savePage(selected.id, { ziel_keyword: editField.value })} />
                    <button onClick={() => savePage(selected.id, { ziel_keyword: editField.value })} style={{ ...btnSm, background: 'var(--success)', color: 'var(--text-on-brand)' }}>✓</button>
                  </div>
                ) : (
                  <div role="button" tabIndex={0} onKeyDown={aufTaste(() => setEditField({ field: 'ziel_keyword', value: selected.ziel_keyword || '' }))} onClick={() => setEditField({ field: 'ziel_keyword', value: selected.ziel_keyword || '' })} style={{ fontSize: 12, color: selected.ziel_keyword ? 'var(--text-primary)' : 'var(--text-tertiary)', cursor: 'pointer', padding: '4px 0', fontStyle: selected.ziel_keyword ? 'normal' : 'italic' }}>{selected.ziel_keyword || 'Klicken zum Setzen...'}</div>
                )}
              </div>

              {/* CTA */}
              <div>
                <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.06em', marginBottom: 4 }}>CTA</div>
                {editField?.field === 'cta_text' ? (
                  <div style={{ display: 'flex', gap: 4 }}>
                    <input aria-label="Text der Handlungsaufforderung" value={editField.value} onChange={e => setEditField({ ...editField, value: e.target.value })} style={inputStyle} autoFocus onKeyDown={e => e.key === 'Enter' && savePage(selected.id, { cta_text: editField.value })} />
                    <button onClick={() => savePage(selected.id, { cta_text: editField.value })} style={{ ...btnSm, background: 'var(--success)', color: 'var(--text-on-brand)' }}>✓</button>
                  </div>
                ) : (
                  <div role="button" tabIndex={0} onKeyDown={aufTaste(() => setEditField({ field: 'cta_text', value: selected.cta_text || '' }))} onClick={() => setEditField({ field: 'cta_text', value: selected.cta_text || '' })} style={{ fontSize: 12, color: selected.cta_text ? 'var(--text-primary)' : 'var(--text-tertiary)', cursor: 'pointer', padding: '4px 0', fontStyle: selected.cta_text ? 'normal' : 'italic' }}>{selected.cta_text || 'Klicken zum Setzen...'}</div>
                )}
              </div>
            </div>

            {/* Zweck */}
            <div>
              <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.06em', marginBottom: 4 }}>Zweck / Beschreibung</div>
              {editField?.field === 'zweck' ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                  <textarea aria-label="Zweck der Seite" value={editField.value} onChange={e => setEditField({ ...editField, value: e.target.value })} rows={3} style={{ ...inputStyle, resize: 'vertical' }} autoFocus />
                  <div style={{ display: 'flex', gap: 4 }}>
                    <button onClick={() => savePage(selected.id, { zweck: editField.value })} style={{ ...btnSm, background: 'var(--success)', color: 'var(--text-on-brand)', fontWeight: 700 }}>Speichern</button>
                    <button onClick={() => setEditField(null)} style={{ ...btnSm, background: 'var(--border-light)', color: 'var(--text-secondary)' }}>Abb.</button>
                  </div>
                </div>
              ) : (
                <div role="button" tabIndex={0} onKeyDown={aufTaste(() => setEditField({ field: 'zweck', value: selected.zweck || '' }))} onClick={() => setEditField({ field: 'zweck', value: selected.zweck || '' })} style={{ fontSize: 12, color: selected.zweck ? 'var(--text-secondary)' : 'var(--text-tertiary)', cursor: 'pointer', lineHeight: 1.5, padding: '4px 0', fontStyle: selected.zweck ? 'normal' : 'italic' }}>{selected.zweck || 'Klicken zum Beschreiben...'}</div>
              )}
            </div>

            {/* Notizen */}
            <div>
              <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.06em', marginBottom: 4 }}>Notizen</div>
              {editField?.field === 'notizen' ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                  <textarea aria-label="Notizen" value={editField.value} onChange={e => setEditField({ ...editField, value: e.target.value })} rows={2} style={{ ...inputStyle, resize: 'vertical' }} autoFocus />
                  <div style={{ display: 'flex', gap: 4 }}>
                    <button onClick={() => savePage(selected.id, { notizen: editField.value })} style={{ ...btnSm, background: 'var(--success)', color: 'var(--text-on-brand)', fontWeight: 700 }}>Speichern</button>
                    <button onClick={() => setEditField(null)} style={{ ...btnSm, background: 'var(--border-light)', color: 'var(--text-secondary)' }}>Abb.</button>
                  </div>
                </div>
              ) : (
                <div role="button" tabIndex={0} onKeyDown={aufTaste(() => setEditField({ field: 'notizen', value: selected.notizen || '' }))} onClick={() => setEditField({ field: 'notizen', value: selected.notizen || '' })} style={{ fontSize: 12, color: selected.notizen ? 'var(--text-secondary)' : 'var(--text-tertiary)', cursor: 'pointer', lineHeight: 1.5, padding: '4px 0', fontStyle: selected.notizen ? 'normal' : 'italic' }}>{selected.notizen || 'Klicken fuer Notizen...'}</div>
              )}
            </div>

            {/* Template Upload */}
            <div>
              <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.06em', marginBottom: 6 }}>HTML-Template</div>
              {selected.mockup_html ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  <div style={{ fontSize: 12, color: 'var(--status-success-text)', background: 'var(--status-success-bg)', padding: '6px 10px', borderRadius: 6, display: 'flex', alignItems: 'center', gap: 6 }}>
                    <span>✓</span> Template vorhanden ({Math.round(selected.mockup_html.length / 1024)} KB)
                  </div>
                  <div style={{ display: 'flex', gap: 6 }}>
                    <label style={{ ...btnSm, background: 'var(--brand-primary)', color: 'var(--text-on-brand)', fontWeight: 600, padding: '5px 14px', cursor: 'pointer', display: 'inline-block' }}>
                      Ersetzen
                      <input type="file" accept=".html,.htm" style={{ display: 'none' }} onChange={e => e.target.files[0] && uploadTemplate(selected.id, e.target.files[0])} />
                    </label>
                    <button onClick={() => savePage(selected.id, { mockup_html: '' })} style={{ ...btnSm, color: 'var(--status-danger-text)', background: 'var(--status-danger-bg)', padding: '5px 12px' }}>Entfernen</button>
                  </div>
                </div>
              ) : (
                <label style={{
                  display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
                  padding: '16px 20px', border: '2px dashed var(--border-light)', borderRadius: 8,
                  cursor: 'pointer', background: 'var(--bg-app)', color: 'var(--text-tertiary)', fontSize: 12,
                  transition: 'border-color .2s',
                }}>
                  <span style={{ fontSize: 20 }}>📄</span>
                  HTML-Template hochladen (.html)
                  <input type="file" accept=".html,.htm" style={{ display: 'none' }} onChange={e => e.target.files[0] && uploadTemplate(selected.id, e.target.files[0])} />
                </label>
              )}
            </div>
          </div>
        ) : (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', padding: 40 }}>
            <div style={{ textAlign: 'center', color: 'var(--text-tertiary)' }}>
              <div style={{ fontSize: 32, marginBottom: 8 }}>🗺️</div>
              <div style={{ fontSize: 13 }}>Seite auswaehlen zum Bearbeiten</div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}


export function SitemapKiVorschlag({ project, leadId, headers, onGenerated, hasExistingPages, existingCount }) {
  const [loading, setLoading]         = useState(false);
  const [done, setDone]               = useState(false);
  const [error, setError]             = useState(null);
  const [gateBlocked, setGateBlocked] = useState(false);

  const generate = async () => {
    if (!leadId) { setError('Keine Lead-ID verfügbar.'); return; }

    if (hasExistingPages && existingCount > 0) {
      const ok = window.confirm(
        `Es gibt bereits ${existingCount} Inhaltsseiten in der Sitemap.\n\n` +
        `Neu generieren? Die bestehenden Seiten (ohne Impressum/Datenschutz) ` +
        `werden durch KI-Vorschläge aus dem aktuellen Briefing ersetzt.`
      );
      if (!ok) return;
    }

    setLoading(true); setError(null); setGateBlocked(false);
    try {
      const res = await fetch(`${API_BASE_URL}/api/sitemap/${leadId}/generate`, { method: 'POST', headers });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        const detail = errData.detail;
        if (detail?.code === 'BRIEFING_NOT_APPROVED') { setGateBlocked(true); return; }
        throw new Error(typeof detail === 'string' ? detail : detail?.message || `HTTP ${res.status}`);
      }
      setDone(true);
      if (onGenerated) onGenerated();
      setTimeout(() => setDone(false), 3000);
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };

  if (gateBlocked) return (
    <div style={{ margin: '0 20px 16px', padding: '14px 18px', background: 'rgba(217,119,6,.06)', border: '1px solid rgba(217,119,6,.3)', borderRadius: 10, display: 'flex', alignItems: 'center', gap: 14 }}>
      <span style={{ fontSize: 28, flexShrink: 0 }}>🔒</span>
      <div style={{ flex: 1 }}>
        <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 3 }}>Briefing noch nicht freigegeben</div>
        <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>Der Kunde hat das Briefing noch nicht freigegeben. Sobald die Freigabe erteilt wurde, kann die KI-Sitemap erstellt werden.</div>
      </div>
      <button onClick={generate} disabled={loading}
        style={{ padding: '9px 18px', borderRadius: 8, border: '1px solid rgba(217,119,6,.4)', background: 'transparent', color: 'var(--warn)', fontSize: 12, fontWeight: 700, cursor: 'pointer', fontFamily: 'var(--font-sans)', flexShrink: 0 }}>
        Erneut prüfen
      </button>
    </div>
  );

  return (
    <div style={{
      margin: '0 20px 16px',
      padding: '14px 18px',
      background: done
        ? 'var(--status-success-bg)'
        : hasExistingPages
          ? 'rgba(124,58,237,.05)'
          : 'var(--kc-mid-a-08)',
      border: done
        ? '1px solid var(--status-success-text)'
        : hasExistingPages
          ? '1px solid rgba(124,58,237,.25)'
          : '1px solid var(--kc-mid-a-25)',
      borderRadius: 10,
      display: 'flex',
      alignItems: 'center',
      gap: 14,
    }}>
      <span style={{ fontSize: 22, flexShrink: 0 }}>{done ? '✓' : '🤖'}</span>
      <div style={{ flex: 1 }}>
        <div style={{ fontSize: 13, fontWeight: 700, color: done ? 'var(--status-success-text)' : 'var(--text-primary)', marginBottom: 3 }}>
          {done
            ? 'Sitemap wurde generiert!'
            : hasExistingPages
              ? 'Sitemap neu aus Briefing generieren'
              : 'Noch keine Sitemap — KI-Vorschlag erstellen?'
          }
        </div>
        <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
          {done
            ? 'Wird gleich angezeigt …'
            : hasExistingPages
              ? `${existingCount} bestehende Seiten werden durch KI-Vorschlag ersetzt · Briefing + Crawler-Daten + USP`
              : 'Claude analysiert Briefing, USP, Zielgruppe und gecrawlte Seiten'
          }
        </div>
        {error && <div style={{ fontSize: 12, color: 'var(--status-danger-text)', marginTop: 6 }}>{error}</div>}
      </div>
      {!done && (
        <button
          onClick={generate}
          disabled={loading}
          style={{
            padding: '9px 18px', borderRadius: 8, border: 'none',
            background: loading
              ? 'var(--border-medium)'
              : hasExistingPages ? '#7c3aed' : 'var(--brand-primary)',
            color: '#fff', fontSize: 12, fontWeight: 700,
            cursor: loading ? 'not-allowed' : 'pointer',
            fontFamily: 'var(--font-sans)', flexShrink: 0,
            display: 'flex', alignItems: 'center', gap: 6, whiteSpace: 'nowrap',
          }}
        >
          {loading ? (
            <><span style={{ width: 12, height: 12, border: '2px solid rgba(255,255,255,.3)', borderTopColor: '#fff', borderRadius: '50%', animation: 'spin .8s linear infinite', display: 'inline-block' }} />Wird erstellt …</>
          ) : hasExistingPages ? 'Neu generieren' : 'KI-Sitemap erstellen'}
        </button>
      )}
    </div>
  );
}

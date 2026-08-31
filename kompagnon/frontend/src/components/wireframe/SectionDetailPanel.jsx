/**
 * Das Detailfeld eines Wireframe-Abschnitts (L-25).
 *
 * Am 2026-08-30 aus `WireframeView.jsx` herausgeloest — 567 Zeilen, der
 * groesste Einzelteil der Ansicht.
 */
import { useEffect, useState } from 'react';
import API_BASE_URL from '../../config';
import { KC_DARK, KC_MID, renderSlots } from './wireframeDaten';

export default function SectionDetailPanel({ block, libraryEntry, headers, projectId, pageId,
                             onClose, onSaveSlots, onSaveAsCustom,
                             onVarianteUebernehmen }) {
  const slots = libraryEntry?.slots || [];
  const html  = libraryEntry?.html_template || '';

  const [values, setValues] = useState(() => {
    const init = {};
    slots.forEach((s) => {
      init[s.key] = (block?.slots && block.slots[s.key]) ?? s.default ?? '';
    });
    return init;
  });
  // Phase-B-Felder — transient, nicht persistiert. Bei Bedarf spaeter
  // auf den Block schreiben.
  const [aiPrompt, setAiPrompt]     = useState('');
  const [assetType, setAssetType]   = useState('none');
  const [elementType, setElementType] = useState('none');
  const [generating, setGenerating] = useState(false);
  const [generateError, setGenerateError] = useState('');

  // Erweiterte Bereiche (eingeklappt)
  const [showAdvanced, setShowAdvanced]   = useState(false);
  const [showCustomForm, setShowCustomForm] = useState(false);
  const [customError, setCustomError] = useState('');
  // Stufe B: eigene Fassung für diesen Kunden
  const [variante, setVariante] = useState({ status: 'idle', ergebnis: null, fehler: '' });
  const [variantenWunsch, setVariantenWunsch] = useState('');
  const [showRawHtml, setShowRawHtml]     = useState(false);
  const [rawHtml, setRawHtml]             = useState(html);
  const [customSlug, setCustomSlug]       = useState(`${block.slug}-custom`);
  const [customName, setCustomName]       = useState(
    libraryEntry?.name ? `${libraryEntry.name} (Custom)` : 'Custom Section',
  );
  const [saving, setSaving] = useState(false);

  // Beim Wechsel der Section (anderer Block angeklickt ohne Unmount): re-init
  useEffect(() => {
    const init = {};
    slots.forEach((s) => {
      init[s.key] = (block?.slots && block.slots[s.key]) ?? s.default ?? '';
    });
    setValues(init);
    setAiPrompt('');
    setAssetType('none');
    setElementType('none');
    setGenerateError('');
    setRawHtml(html);
    setCustomSlug(`${block.slug}-custom`);
    setCustomName(libraryEntry?.name ? `${libraryEntry.name} (Custom)` : 'Custom Section');
    setShowAdvanced(false);
    setShowCustomForm(false);
    setCustomError('');
    setVariante({ status: 'idle', ergebnis: null, fehler: '' });
    setVariantenWunsch('');
    setShowRawHtml(false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [block?.slug]);

  const hasSlots = slots.length > 0;

  const handleGenerateCopy = async () => {
    if (generating || !aiPrompt.trim() || !hasSlots) return;
    setGenerating(true);
    setGenerateError('');
    try {
      const res = await fetch(`${API_BASE_URL}/api/components/generate-copy`, {
        method: 'POST', headers,
        body: JSON.stringify({
          slug:          block.slug,
          ai_prompt:     aiPrompt,
          asset_type:    assetType === 'none' ? null : assetType,
          element_type:  elementType === 'none' ? null : elementType,
          current_slots: values,
        }),
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        const detail = body?.detail;
        const msg = typeof detail === 'string' ? detail : detail?.message || `Fehler ${res.status}`;
        throw new Error(msg);
      }
      // Generierte Werte ueber bestehende mergen — User-Edits nicht ueberschreiben
      // wenn KI fuer den Key nichts liefert.
      setValues((prev) => ({ ...prev, ...(body.slots || {}) }));
    } catch (e) {
      setGenerateError(e.message || 'KI-Aufruf fehlgeschlagen');
    } finally {
      setGenerating(false);
    }
  };

  const handleSlotSave = () => {
    if (saving) return;
    setSaving(true);
    onSaveSlots(values);
  };

  const eigeneFassung = (block?.html_override || '').trim();

  const umschreiben = async () => {
    setVariante({ status: 'laeuft', ergebnis: null, fehler: '' });
    try {
      const start = await fetch(`${API_BASE_URL}/api/projects/${projectId}/wireframe/variant`, {
        method: 'POST', headers,
        body: JSON.stringify({ page_id: pageId, slug: block.slug, wunsch: variantenWunsch }),
      });
      const gestartet = await start.json().catch(() => ({}));
      if (!start.ok) {
        const detail = gestartet?.detail;
        throw new Error(typeof detail === 'string' ? detail : `Fehler ${start.status}`);
      }

      // Polling wie beim Blockautor — der Auftrag läuft im Hintergrund.
      const frist = Date.now() + 180_000;
      while (Date.now() < frist) {
        // eslint-disable-next-line no-await-in-loop
        await new Promise((r) => setTimeout(r, 2000));
        // eslint-disable-next-line no-await-in-loop
        const res = await fetch(
          `${API_BASE_URL}/api/projects/wireframe-variant-jobs/${gestartet.job_id}`,
          { headers },
        );
        if (res.status === 404) throw new Error('Auftrag nicht gefunden');
        // eslint-disable-next-line no-await-in-loop
        const job = await res.json();
        if (job.status === 'done') {
          setVariante({ status: 'fertig', ergebnis: job.result, fehler: '' });
          return;
        }
        if (job.status === 'error') throw new Error(job.error || 'Unbekannter Fehler');
      }
      throw new Error('Zeitüberschreitung — bitte erneut versuchen');
    } catch (e) {
      setVariante({ status: 'fehler', ergebnis: null, fehler: e.message || 'Fehlgeschlagen' });
    }
  };

  const uebernehmen = async () => {
    const html = variante.ergebnis?.html_override;
    if (!html) return;
    const ok = await onVarianteUebernehmen?.(html);
    if (ok !== false) setVariante({ status: 'idle', ergebnis: null, fehler: '' });
  };

  const handleCustomSave = async () => {
    if (saving) return;
    setSaving(true);
    setCustomError('');
    try {
      await onSaveAsCustom({
        new_slug:       customSlug.trim().toLowerCase(),
        new_name:       customName.trim(),
        html_template:  showRawHtml ? rawHtml : renderSlots(html, values),
        category:       libraryEntry?.category || 'CUSTOM',
        source_slug:    block.slug,
        slots:          showRawHtml ? [] : (libraryEntry?.slots || []),
        ki_prompt_hint: libraryEntry?.ki_prompt_hint || '',
        preview_note:   `Custom-Variante von ${libraryEntry?.name || block.slug}`,
      });
    } catch (e) {
      setCustomError(e.message || 'Speichern fehlgeschlagen');
    } finally {
      setSaving(false);
    }
  };

  const lblStyle = {
    display: 'block', fontSize: 12, fontWeight: 700,
    color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.04em',
    marginBottom: 4,
  };
  const inpStyle = {
    width: '100%', boxSizing: 'border-box',
    padding: '7px 10px',
    border: '1px solid var(--border-medium)', borderRadius: 6,
    fontSize: 12, fontFamily: 'inherit', outline: 'none',
    background: '#fff',
  };

  return (
    <aside style={{
      width: 380, flexShrink: 0,
      background: '#fff', borderLeft: '1px solid var(--border-light)',
      display: 'flex', flexDirection: 'column',
      boxShadow: '-4px 0 12px rgba(0,0,0,0.04)',
      fontFamily: 'var(--font-sans, system-ui)',
    }}>
      {/* Header */}
      <div style={{
        padding: '12px 14px', borderBottom: '1px solid var(--border-light)',
        background: 'var(--bg-app)',
        display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 10,
      }}>
        <div style={{ minWidth: 0, flex: 1 }}>
          <div style={{
            fontSize: 13, fontWeight: 800, color: KC_DARK,
            overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
          }}>
            {libraryEntry?.name || block.slug}
          </div>
          <div style={{ fontSize: 12, color: 'var(--text-secondary)', fontFamily: 'ui-monospace, monospace', marginTop: 2 }}>
            {block.slug}
          </div>
          {libraryEntry?.preview_note && (
            <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 4, lineHeight: 1.4 }}>
              {libraryEntry.preview_note}
            </div>
          )}
        </div>
        <button type="button" onClick={onClose} aria-label="Schließen"
          style={{ background: 'none', border: 'none', fontSize: 18, cursor: 'pointer', color: 'var(--text-secondary)', lineHeight: 1, padding: 0, flexShrink: 0 }}>
          ×
        </button>
      </div>

      {/* Body — scrollbar */}
      <div style={{ flex: 1, overflowY: 'auto', padding: 14, display: 'flex', flexDirection: 'column', gap: 14 }}>
        {/* Stufe B: für diesen Kunden umschreiben */}
        <div style={{
          padding: 10, borderRadius: 8, background: '#faf5ff',
          border: '1px solid #d8b4fe', display: 'flex',
          flexDirection: 'column', gap: 6,
        }}>
          <div style={{ ...lblStyle, color: '#6b21a8', marginBottom: 0 }}>
            Für diesen Kunden umschreiben
          </div>
          <p style={{ fontSize: 12, color: '#6b21a8', margin: 0, lineHeight: 1.4 }}>
            Claude baut die Section anders auf — passend zu Gewerk, Leistungen
            und Einzugsgebiet aus dem Briefing. Slots und Block bleiben
            dieselben, nur das Layout ändert sich.
          </p>
          {eigeneFassung && (
            <div style={{ fontSize: 12, color: '#6b21a8', fontWeight: 700 }}>
              Dieser Block hat bereits eine eigene Fassung.
            </div>
          )}
          <textarea aria-label="Optional: was soll anders sein? z.B. „Notdienst nach oben, Bild links"
            value={variantenWunsch}
            onChange={(e) => setVariantenWunsch(e.target.value)}
            rows={2}
            placeholder="Optional: was soll anders sein? z.B. „Notdienst nach oben, Bild links"
            style={{ ...inpStyle, padding: '6px 8px', fontSize: 12, resize: 'vertical' }}
            disabled={variante.status === 'laeuft'}
          />
          <button
            type="button" onClick={umschreiben}
            disabled={variante.status === 'laeuft'}
            style={{
              padding: '7px 10px',
              background: '#7c3aed', opacity: variante.status === 'laeuft' ? 0.5 : 1,
              color: '#fff', border: 'none', borderRadius: 6,
              fontSize: 12, fontWeight: 700, fontFamily: 'inherit',
              cursor: variante.status === 'laeuft' ? 'wait' : 'pointer',
            }}
          >
            {variante.status === 'laeuft'
              ? 'Claude schreibt um… (30–90 s)'
              : (eigeneFassung ? '✨ Neu umschreiben' : '✨ Umschreiben lassen')}
          </button>

          {variante.status === 'fehler' && (
            <div style={{
              padding: 8, background: '#fef2f2', border: '1px solid #fca5a5',
              borderRadius: 4, color: '#991b1b', fontSize: 12,
            }}>{variante.fehler}</div>
          )}

          {variante.status === 'fertig' && variante.ergebnis && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {variante.ergebnis.begruendung && (
                <div style={{ fontSize: 12, color: '#4c1d95', fontStyle: 'italic' }}>
                  „{variante.ergebnis.begruendung}"
                </div>
              )}
              {!variante.ergebnis.contract?.konform && (
                <div style={{
                  padding: 8, background: '#fef2f2', border: '1px solid #fca5a5',
                  borderRadius: 4, color: '#991b1b', fontSize: 12,
                }}>
                  <strong>Der Vertrag ist verletzt — Übernehmen wird abgelehnt:</strong>
                  <ul style={{ margin: '4px 0 0', paddingLeft: 16 }}>
                    {(variante.ergebnis.contract?.verstoesse || []).map((v, i) => (
                      <li key={`${v.regel}-${i}`}>{v.regel}: {v.text}</li>
                    ))}
                  </ul>
                </div>
              )}
              <div style={{
                border: '1px solid var(--border-light)', borderRadius: 6,
                overflow: 'hidden', background: '#fff', pointerEvents: 'none',
                maxHeight: 240, overflowY: 'auto',
              }}>
                {/* eslint-disable-next-line react/no-danger */}
                <div dangerouslySetInnerHTML={{
                  __html: renderSlots(variante.ergebnis.html_override, values),
                }} />
              </div>
              <div style={{ display: 'flex', gap: 6 }}>
                <button
                  type="button" onClick={uebernehmen}
                  disabled={!variante.ergebnis.contract?.konform}
                  style={{
                    flex: 1, padding: '6px 10px',
                    background: variante.ergebnis.contract?.konform ? 'var(--success)' : 'var(--text-tertiary)',
                    color: 'var(--text-on-brand)', border: 'none', borderRadius: 4,
                    fontSize: 12, fontWeight: 700, fontFamily: 'inherit',
                    cursor: variante.ergebnis.contract?.konform ? 'pointer' : 'not-allowed',
                  }}
                >✓ Übernehmen</button>
                <button
                  type="button"
                  onClick={() => setVariante({ status: 'idle', ergebnis: null, fehler: '' })}
                  style={{
                    padding: '6px 10px', background: '#fff',
                    border: '1px solid var(--border-medium)', borderRadius: 4,
                    fontSize: 12, fontWeight: 700, fontFamily: 'inherit',
                    cursor: 'pointer',
                  }}
                >Verwerfen</button>
              </div>
            </div>
          )}

          {eigeneFassung && variante.status !== 'fertig' && (
            <button
              type="button" onClick={() => onVarianteUebernehmen?.(null)}
              style={{
                padding: '6px 10px', background: '#fff', color: '#6b21a8',
                border: '1px solid #d8b4fe', borderRadius: 4,
                fontSize: 12, fontWeight: 700, fontFamily: 'inherit',
                cursor: 'pointer',
              }}
            >↩︎ Zurück zur Bibliotheksvorlage</button>
          )}
        </div>

        {/* AI-Generate-Block (Phase B Hauptfeature) */}
        {hasSlots && (
          <div style={{
            padding: 10,
            background: '#f0f9ff', border: '1px solid #bae6fd', borderRadius: 8,
          }}>
            <label style={lblStyle}>✨ KI-Anweisung</label>
            <textarea aria-label="✨ KI-Anweisung"
              value={aiPrompt}
              onChange={(e) => setAiPrompt(e.target.value)}
              placeholder='z.B. "Fokus auf Wallbox-Installation, sympathisch, lokal verankert"'
              rows={3}
              style={{ ...inpStyle, resize: 'vertical', minHeight: 60, marginBottom: 8 }}
            />
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginBottom: 8 }}>
              <div>
                <label style={lblStyle}>Asset</label>
                <select aria-label="Asset"
                  value={assetType}
                  onChange={(e) => setAssetType(e.target.value)}
                  style={{ ...inpStyle, cursor: 'pointer', padding: '6px 8px' }}
                >
                  <option value="none">Kein Asset</option>
                  <option value="image">Bild</option>
                  <option value="video">Video</option>
                </select>
              </div>
              <div>
                <label style={lblStyle}>Element</label>
                <select aria-label="Element"
                  value={elementType}
                  onChange={(e) => setElementType(e.target.value)}
                  style={{ ...inpStyle, cursor: 'pointer', padding: '6px 8px' }}
                >
                  <option value="none">Standard</option>
                  <option value="form">Formular</option>
                  <option value="button">Button</option>
                </select>
              </div>
            </div>
            <button
              type="button"
              onClick={handleGenerateCopy}
              disabled={generating || !aiPrompt.trim()}
              style={{
                width: '100%', padding: '8px 12px',
                background: KC_MID,
                color: '#fff', border: 'none', borderRadius: 6,
                fontSize: 12, fontWeight: 700,
                cursor: generating || !aiPrompt.trim() ? 'not-allowed' : 'pointer',
                opacity: generating || !aiPrompt.trim() ? 0.4 : 1,
                fontFamily: 'inherit',
              }}
            >
              {generating ? 'KI generiert…' : '✨ Generate copy'}
            </button>
            {generateError && (
              <div style={{
                marginTop: 8, padding: '6px 8px',
                background: '#FEF2F2', border: '1px solid #FCA5A5', borderRadius: 4,
                fontSize: 12, color: '#991B1B',
              }}>
                {generateError}
              </div>
            )}
          </div>
        )}

        {/* Slots */}
        {hasSlots ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
              Slots ({slots.length})
            </div>
            {slots.map((s) => (
              <div key={s.key}>
                <label style={lblStyle}>{s.label || s.key}</label>
                <input aria-label={s.default || ''}
                  type="text"
                  value={values[s.key] ?? ''}
                  onChange={(e) => setValues((v) => ({ ...v, [s.key]: e.target.value }))}
                  placeholder={s.default || ''}
                  style={inpStyle}
                />
                <div style={{ fontSize: 9, color: 'var(--text-tertiary)', marginTop: 2, fontFamily: 'ui-monospace, monospace' }}>
                  {`{{${s.key}}}`}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div style={{
            padding: 10, fontSize: 12, color: '#92400e',
            background: '#FEF3C7', border: '1px solid #FCD34D', borderRadius: 6,
          }}>
            Diese Section hat keine definierten Slots. Nutze „HTML direkt bearbeiten" unten für volle Kontrolle.
          </div>
        )}

        {/* Erweiterter Bereich — eingeklappt */}
        <div style={{ borderTop: '1px solid var(--border-light)', paddingTop: 10 }}>
          <button
            type="button"
            onClick={() => setShowAdvanced((v) => !v)}
            style={{
              background: 'none', border: 'none',
              color: KC_MID, fontSize: 12, fontWeight: 700,
              cursor: 'pointer', padding: 0, fontFamily: 'inherit',
            }}
          >
            {showAdvanced ? '▼ Erweitert' : '▶ Erweitert (HTML / Custom speichern)'}
          </button>

          {showAdvanced && (
            <div style={{ marginTop: 10, display: 'flex', flexDirection: 'column', gap: 8 }}>
              <button
                type="button" onClick={() => setShowRawHtml((v) => !v)}
                style={{
                  background: '#fff', border: '1px solid var(--border-medium)',
                  color: 'var(--text-secondary)', fontSize: 12, fontWeight: 600,
                  padding: '6px 10px', borderRadius: 6,
                  cursor: 'pointer', fontFamily: 'inherit',
                  textAlign: 'left',
                }}
              >
                {showRawHtml ? '← Slot-Modus' : 'HTML direkt bearbeiten →'}
              </button>
              {showRawHtml && (
                <>
                  <textarea aria-label="HTML-Quelltext"
                    value={rawHtml}
                    onChange={(e) => setRawHtml(e.target.value)}
                    rows={12}
                    style={{ ...inpStyle, fontFamily: 'ui-monospace, monospace', fontSize: 12, resize: 'vertical' }}
                  />
                  <div style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>
                    Wird nur sichtbar wenn du als Custom-Section speicherst.
                  </div>
                </>
              )}

              <button
                type="button" onClick={() => setShowCustomForm((v) => !v)}
                style={{
                  background: '#fff', border: `1px solid ${KC_MID}`,
                  color: KC_MID, fontSize: 12, fontWeight: 700,
                  padding: '6px 10px', borderRadius: 6,
                  cursor: 'pointer', fontFamily: 'inherit',
                  textAlign: 'left',
                }}
              >
                {showCustomForm ? '× Custom abbrechen' : '💾 Als Custom-Section speichern'}
              </button>

              {showCustomForm && (
                <div style={{
                  padding: 8, background: '#FEF3C7', border: '1px solid #FCD34D', borderRadius: 6,
                  display: 'flex', flexDirection: 'column', gap: 6,
                }}>
                  <div>
                    <label style={{ ...lblStyle, color: '#92400e' }}>Slug</label>
                    <input aria-label="Slug" value={customSlug} onChange={(e) => setCustomSlug(e.target.value)}
                      style={{ ...inpStyle, padding: '6px 8px', fontFamily: 'ui-monospace, monospace', borderColor: '#FCD34D' }} />
                  </div>
                  <div>
                    <label style={{ ...lblStyle, color: '#92400e' }}>Name</label>
                    <input aria-label="Name" value={customName} onChange={(e) => setCustomName(e.target.value)}
                      style={{ ...inpStyle, padding: '6px 8px', borderColor: '#FCD34D' }} />
                  </div>
                  <button
                    type="button" onClick={handleCustomSave}
                    disabled={saving || !customSlug.trim() || !customName.trim()}
                    style={{
                      padding: '6px 10px', marginTop: 2,
                      background: KC_MID, opacity: saving ? 0.5 : 1, color: '#fff',
                      border: 'none', borderRadius: 4,
                      fontSize: 12, fontWeight: 700,
                      cursor: saving ? 'wait' : 'pointer',
                      fontFamily: 'inherit',
                    }}
                  >
                    {saving ? 'Speichert…' : '✓ Custom speichern + anwenden'}
                  </button>
                  {customError && (
                    <div style={{
                      padding: 8, background: '#fef2f2', border: '1px solid #fca5a5',
                      borderRadius: 4, color: '#991b1b', fontSize: 12,
                    }}>{customError}</div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Footer */}
      <div style={{
        padding: '10px 14px', borderTop: '1px solid var(--border-light)',
        display: 'flex', gap: 8, background: 'var(--bg-app)',
      }}>
        <button
          type="button" onClick={onClose}
          style={{
            flex: 1, padding: '8px 12px',
            background: '#fff', border: '1px solid var(--border-light)',
            borderRadius: 8, fontSize: 12, cursor: 'pointer',
            color: 'var(--text-secondary)', fontFamily: 'inherit',
          }}
        >
          Schließen
        </button>
        <button
          type="button" onClick={handleSlotSave}
          disabled={saving || !hasSlots}
          style={{
            flex: 1, padding: '8px 12px',
            background: KC_DARK, opacity: saving || !hasSlots ? 0.5 : 1,
            color: '#fff', border: 'none',
            borderRadius: 8, fontSize: 12, fontWeight: 700,
            cursor: saving || !hasSlots ? 'not-allowed' : 'pointer',
            fontFamily: 'inherit',
          }}
        >
          {saving ? 'Speichert…' : '✓ Slots speichern'}
        </button>
      </div>
    </aside>
  );
}

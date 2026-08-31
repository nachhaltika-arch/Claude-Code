/**
 * Der Bausteineditor der Komponentenbibliothek (L-25).
 *
 * Am 2026-08-30 aus `ComponentLibrary.jsx` herausgeloest — 215 Zeilen.
 */
import { useState } from 'react';

import { ContractPanel, StatusBadge } from '../BlockContract';
import { CATEGORY_OPTIONS, KC_DARK } from './katalog';
import { Field, Hint, inputStyle } from './felder';

export default function Editor({
  form, updateForm, isNew, dirty,
  saving, deleting, approving, previewHtml,
  onSave, onDelete, onApprove,
}) {
  const [tagInput, setTagInput] = useState('');

  const addTag = () => {
    const t = tagInput.trim().toLowerCase();
    if (!t) return;
    if (form.tags.includes(t)) { setTagInput(''); return; }
    updateForm({ tags: [...form.tags, t] });
    setTagInput('');
  };
  const removeTag = (t) => updateForm({ tags: form.tags.filter((x) => x !== t) });

  const updateSlot = (idx, patch) => {
    const next = form.slots.map((s, i) => (i === idx ? { ...s, ...patch } : s));
    updateForm({ slots: next });
  };
  const addSlot = () => updateForm({ slots: [...form.slots, { key: '', label: '', default: '' }] });
  const removeSlot = (idx) => updateForm({ slots: form.slots.filter((_, i) => i !== idx) });

  return (
    <>
      {/* Top: header bar */}
      <div style={{
        padding: '10px 14px', borderBottom: '1px solid #e2e8f0',
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        background: '#f8fafc',
      }}>
        <div style={{ fontSize: 13, fontWeight: 800, color: KC_DARK, display: 'flex', alignItems: 'center', gap: 8 }}>
          {isNew ? 'Neue Komponente' : form.name || form.slug}
          {!isNew && <StatusBadge status={form.status} />}
          {dirty && <span style={{ fontSize: 10, color: '#92400e', background: '#FEF3C7', padding: '2px 6px', borderRadius: 4 }}>UNGESPEICHERT</span>}
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          {!isNew && (
            <button
              type="button" onClick={onDelete} disabled={deleting || saving}
              style={{
                padding: '6px 12px', fontSize: 12, fontWeight: 700,
                background: '#fff', color: '#dc2626',
                border: '1px solid #fca5a5', borderRadius: 6,
                cursor: deleting ? 'wait' : 'pointer', fontFamily: 'inherit',
              }}
            >{deleting ? 'Loescht…' : 'Loeschen'}</button>
          )}
          <button
            type="button" onClick={onSave} disabled={saving || (!dirty && !isNew)}
            style={{
              padding: '6px 14px', fontSize: 12, fontWeight: 700,
              background: KC_DARK, opacity: saving || (!dirty && !isNew) ? 0.5 : 1,
              color: '#fff', border: 'none', borderRadius: 6,
              cursor: saving ? 'wait' : 'pointer', fontFamily: 'inherit',
            }}
          >{saving ? 'Speichert…' : (isNew ? 'Anlegen' : 'Speichern')}</button>
        </div>
      </div>

      {/* Body: 2-column form + preview */}
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        {/* Form column */}
        <div style={{ flex: '0 0 380px', padding: 14, overflowY: 'auto', borderRight: '1px solid #e2e8f0' }}>
          <ContractPanel
            contract={form.contract}
            status={form.status}
            stale={dirty}
            onApprove={isNew ? undefined : onApprove}
            approving={approving}
          />

          <Field label="Slug">
            <input
              type="text" value={form.slug} disabled={!isNew} aria-label="Slug"
              onChange={(e) => updateForm({ slug: e.target.value.toLowerCase() })}
              placeholder={isNew ? 'leer lassen → wird aus Name erzeugt' : ''}
              style={inputStyle(!isNew)}
            />
            <Hint>{isNew ? 'Kleinbuchstaben, Ziffern, Bindestriche. Leer lassen → automatisch aus Name (z.B. „SHK Hero Premium" → „shk-hero-premium").' : 'Slug ist nicht editierbar.'}</Hint>
          </Field>

          <Field label="Name">
            <input
              type="text" value={form.name} aria-label="Name"
              onChange={(e) => updateForm({ name: e.target.value })}
              style={inputStyle(false)}
            />
          </Field>

          <Field label="Kategorie">
            <select
              value={form.category} onChange={(e) => updateForm({ category: e.target.value })}
              style={inputStyle(false)}
            >
              {CATEGORY_OPTIONS.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
          </Field>

          <Field label="Tags">
            <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap', marginBottom: 6 }}>
              {form.tags.map((t) => (
                <span key={t} style={{
                  display: 'inline-flex', alignItems: 'center', gap: 4,
                  background: '#e2e8f0', color: '#334155',
                  padding: '2px 8px', borderRadius: 12, fontSize: 12,
                }}>
                  {t}
                  <button type="button" onClick={() => removeTag(t)}
                    style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#64748b', fontSize: 13, padding: 0, lineHeight: 1 }}>×</button>
                </span>
              ))}
            </div>
            <div style={{ display: 'flex', gap: 6 }}>
              <input
                type="text" value={tagInput}
                onChange={(e) => setTagInput(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); addTag(); } }}
                placeholder="Tag eingeben + Enter"
                style={{ ...inputStyle(false), flex: 1 }}
              />
              <button aria-label="Hinzufügen" type="button" onClick={addTag}
                style={{ padding: '6px 10px', fontSize: 12, background: '#fff', border: '1px solid #cbd5e1', borderRadius: 6, cursor: 'pointer' }}>+</button>
            </div>
          </Field>

          <Field label={`Slots (${form.slots.length})`}>
            {form.slots.map((s, idx) => (
              <div key={idx} style={{
                marginBottom: 6, padding: 8,
                border: '1px solid #e2e8f0', borderRadius: 6, background: '#f8fafc',
              }}>
                <div style={{ display: 'flex', gap: 4, marginBottom: 4 }}>
                  <input
                    type="text" placeholder="key"
                    value={s.key || ''} onChange={(e) => updateSlot(idx, { key: e.target.value })}
                    style={{ ...inputStyle(false), flex: 1, fontFamily: 'ui-monospace, monospace', fontSize: 12 }}
                  />
                  <button type="button" onClick={() => removeSlot(idx)}
                    style={{ padding: '4px 8px', fontSize: 12, background: '#fff', color: '#dc2626', border: '1px solid #fca5a5', borderRadius: 4, cursor: 'pointer' }}>×</button>
                </div>
                <input
                  type="text" placeholder="Label"
                  value={s.label || ''} onChange={(e) => updateSlot(idx, { label: e.target.value })}
                  style={{ ...inputStyle(false), marginBottom: 4 }}
                />
                <input
                  type="text" placeholder="Default-Wert"
                  value={s.default || ''} onChange={(e) => updateSlot(idx, { default: e.target.value })}
                  style={inputStyle(false)}
                />
              </div>
            ))}
            <button type="button" onClick={addSlot}
              style={{ padding: '6px 10px', fontSize: 12, background: '#fff', border: '1px dashed #cbd5e1', borderRadius: 6, cursor: 'pointer', width: '100%' }}>
              + Slot hinzufuegen
            </button>
          </Field>

          <Field label="HTML-Template">
            <textarea
              value={form.html_template} aria-label="HTML-Template"
              onChange={(e) => updateForm({ html_template: e.target.value })}
              rows={14}
              style={{
                width: '100%', boxSizing: 'border-box',
                padding: 8, border: '1px solid #cbd5e1', borderRadius: 6,
                fontSize: 12, fontFamily: 'ui-monospace, monospace', resize: 'vertical',
              }}
            />
          </Field>

          <Field label="KI-Prompt-Hint">
            <textarea
              value={form.ki_prompt_hint}
              onChange={(e) => updateForm({ ki_prompt_hint: e.target.value })}
              rows={3}
              style={{ ...inputStyle(false), resize: 'vertical' }}
            />
          </Field>

          <Field label="Preview-Note">
            <textarea
              value={form.preview_note}
              onChange={(e) => updateForm({ preview_note: e.target.value })}
              rows={2}
              style={{ ...inputStyle(false), resize: 'vertical' }}
            />
          </Field>
        </div>

        {/* Preview column */}
        <div style={{ flex: 1, overflowY: 'auto', background: '#f8fafc', padding: 14 }}>
          <div style={{ fontSize: 10, fontWeight: 800, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 8 }}>
            Live-Preview (mit Default-Slots)
          </div>
          <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: 8, overflow: 'hidden', pointerEvents: 'none' }}>
            {previewHtml ? (
              <div dangerouslySetInnerHTML={{ __html: previewHtml }} />
            ) : (
              <div style={{ padding: 32, textAlign: 'center', color: '#94a3b8', fontSize: 12 }}>
                Kein HTML eingegeben
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}

// ── Tiny helpers ─────────────────────────────────────────────────────────────

// Beschriftung und Feld waren hier Geschwister ohne `htmlFor` — dieselbe
// Form wie in sieben weiteren Dateien (L-17). Der Baustein verknüpft beide.

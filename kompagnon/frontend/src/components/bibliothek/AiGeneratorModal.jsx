/**
 * Der KI-Erzeuger der Komponentenbibliothek (L-25).
 *
 * Am 2026-08-30 aus `ComponentLibrary.jsx` herausgeloest — 304 der damals
 * 1.264 Zeilen. Er hat am selben Tag seinen Escape-Weg bekommen (L-17).
 */
import React, { useMemo } from 'react';

import { ContractPanel } from '../BlockContract';
import { useEscapeKey } from '../../hooks/useKeyboardShortcuts';
import { aufTaste } from '../../utils/tastaturBedienung';
import { BOOL_ELEMENTS, CATEGORY_OPTIONS, COUNT_ELEMENTS, INDUSTRIES, renderSlots } from './katalog';
import { Field, Hint, inputStyle } from './felder';

export default function AiGeneratorModal({ form, setForm, status, result, error, onGenerate, onUseResult, onClose, presets = [] }) {
  // **Escape schliesst — WCAG 2.1.1 (30.08.2026, L-17).** Der Hintergrund
  // reagiert auf einen Klick; mit der Tastatur gab es keinen Weg heraus.
  // `role="button"` waere hier falsch: Eine Ueberlagerung ist keine
  // Schaltflaeche, sie ist der Weg zurueck.
  useEscapeKey(onClose);

  const previewHtml = useMemo(() => {
    if (!result?.html_template) return '';
    const defaults = (result.slots || []).reduce((acc, s) => {
      if (s.key) acc[s.key] = s.default ?? '';
      return acc;
    }, {});
    return renderSlots(result.html_template, defaults);
  }, [result]);

  return (
    <div role="button" tabIndex={0} onKeyDown={aufTaste((e) => e.target === e.currentTarget && onClose())} onClick={(e) => e.target === e.currentTarget && onClose()} style={{
      position: 'fixed', inset: 0, zIndex: 2000,
      background: 'rgba(0,0,0,0.55)',
      display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 16,
    }}>
      <div style={{
        background: '#fff', borderRadius: 12,
        width: '100%', maxWidth: 1100, maxHeight: 'calc(100vh - 32px)',
        display: 'flex', flexDirection: 'column', overflow: 'hidden',
        boxShadow: '0 20px 60px rgba(0,0,0,0.3)',
        fontFamily: 'inherit',
      }}>
        {/* Header */}
        <div style={{
          padding: '14px 18px', borderBottom: '1px solid #e2e8f0',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          background: 'linear-gradient(135deg, #7c3aed 0%, #a855f7 100%)', color: '#fff',
        }}>
          <div>
            <div style={{ fontSize: 14, fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              ✨ Komponenten-Designer (KI)
            </div>
            <div style={{ fontSize: 12, opacity: 0.9, marginTop: 2 }}>
              Opus 5 · Wireframe-Stil (neutral grau) · CI-Design folgt im Projekt-Prozess
            </div>
          </div>
          <button aria-label="Schließen" type="button" onClick={onClose} disabled={status === 'running'}
            style={{ background: 'none', border: 'none', fontSize: 22, cursor: 'pointer', color: '#fff', lineHeight: 1, opacity: status === 'running' ? 0.4 : 1 }}>×</button>
        </div>

        {/* Body: 2 Spalten — Form links, Preview/Result rechts */}
        <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
          {/* Form */}
          <div style={{ flex: '0 0 360px', padding: 16, overflowY: 'auto', borderRight: '1px solid #e2e8f0', background: '#f8fafc' }}>
            <Field label="Kategorie">
              <select
                value={form.category}
                onChange={(e) => setForm({
                  ...form,
                  category: e.target.value,
                  // Layout-Preset zuruecksetzen wenn Kategorie wechselt — die alten
                  // Presets passen nicht zur neuen Kategorie
                  layout_preset: '',
                })}
                disabled={status === 'running'}
                style={inputStyle(false)}
              >
                {CATEGORY_OPTIONS.map((c) => <option key={c} value={c}>{c}</option>)}
              </select>
            </Field>

            {/* Phase A (Weg 1): Layout-Preset — vordefinierte Pattern pro Kategorie */}
            <Field label={`Layout-Preset${presets.length ? ` (${presets.length})` : ''}`}>
              <select
                value={form.layout_preset || ''}
                onChange={(e) => setForm({ ...form, layout_preset: e.target.value })}
                disabled={status === 'running' || presets.length === 0}
                style={inputStyle(presets.length === 0)}
              >
                <option value="">Beliebig (KI entscheidet)</option>
                {presets.map((p) => (
                  <option key={p.id} value={p.id}>{p.label}</option>
                ))}
              </select>
              {form.layout_preset && (() => {
                const preset = presets.find((p) => p.id === form.layout_preset);
                return preset ? (
                  <Hint>
                    <span style={{ color: '#475569' }}>{preset.guidance}</span>
                  </Hint>
                ) : null;
              })()}
            </Field>

            <Field label="Layout-Dichte">
              <div style={{ display: 'flex', gap: 4 }}>
                {[
                  { id: 'minimal', label: 'Sparsam' },
                  { id: 'elegant', label: 'Ausgewogen' },
                  { id: 'bold', label: 'Dicht' },
                ].map((s) => {
                  const active = form.style_vibe === s.id;
                  return (
                    <button
                      key={s.id} type="button"
                      onClick={() => setForm({ ...form, style_vibe: s.id })}
                      disabled={status === 'running'}
                      style={{
                        flex: 1, padding: '7px 10px',
                        background: active ? '#7c3aed' : '#fff',
                        color: active ? '#fff' : '#475569',
                        border: '1px solid ' + (active ? '#7c3aed' : '#cbd5e1'),
                        borderRadius: 6, fontSize: 12, fontWeight: 700,
                        cursor: status === 'running' ? 'not-allowed' : 'pointer',
                        textTransform: 'uppercase',
                      }}
                    >{s.label}</button>
                  );
                })}
              </div>
            </Field>

            <Field label="Branche">
              <select
                value={form.industry}
                onChange={(e) => setForm({ ...form, industry: e.target.value })}
                disabled={status === 'running'}
                style={inputStyle(false)}
              >
                {INDUSTRIES.map((i) => (
                  <option key={i.id} value={i.id}>{i.label}</option>
                ))}
              </select>
              {form.industry === 'custom' && (
                <textarea
                  value={form.industry_custom}
                  onChange={(e) => setForm({ ...form, industry_custom: e.target.value })}
                  disabled={status === 'running'}
                  rows={3}
                  placeholder="Beschreibe die Branche: typische Themen, Vokabular, Trust-Marker, Pain-Points. Z.B.: 'IT-Beratung fuer Mittelstand — Cloud-Migration, Cyber-Security, DSGVO-Compliance, ITIL-Zertifizierung, On-Site + Remote.'"
                  style={{ ...inputStyle(false), marginTop: 6, resize: 'vertical', fontSize: 12 }}
                />
              )}
            </Field>

            <Field label="Pflicht-Elemente (optional — leer = KI entscheidet)">
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 70px', gap: '4px 8px', fontSize: 12, marginBottom: 8 }}>
                {COUNT_ELEMENTS.map((el) => (
                  <React.Fragment key={el.key}>
                    <label htmlFor={`el-${el.key}`} style={{ alignSelf: 'center', color: '#475569' }}>{el.label}</label>
                    <input
                      id={`el-${el.key}`}
                      type="number" min={0} max={el.max}
                      value={form.elements[el.key] ?? 0}
                      onChange={(e) => {
                        const v = parseInt(e.target.value, 10) || 0;
                        const next = { ...form.elements };
                        if (v > 0) next[el.key] = v; else delete next[el.key];
                        setForm({ ...form, elements: next });
                      }}
                      disabled={status === 'running'}
                      style={{
                        padding: '4px 6px', border: '1px solid #cbd5e1',
                        borderRadius: 4, fontSize: 12, fontFamily: 'inherit',
                        textAlign: 'center', boxSizing: 'border-box', width: '100%',
                      }}
                    />
                  </React.Fragment>
                ))}
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px 8px', marginTop: 4 }}>
                {BOOL_ELEMENTS.map((el) => {
                  const checked = !!form.elements[el.key];
                  return (
                    <label
                      key={el.key}
                      style={{
                        display: 'inline-flex', alignItems: 'center', gap: 4,
                        fontSize: 12, color: '#475569', cursor: 'pointer',
                        background: checked ? '#ede9fe' : '#f1f5f9',
                        border: '1px solid ' + (checked ? '#a78bfa' : '#e2e8f0'),
                        padding: '3px 8px', borderRadius: 12,
                      }}
                    >
                      <input
                        type="checkbox" checked={checked}
                        onChange={(e) => {
                          const next = { ...form.elements };
                          if (e.target.checked) next[el.key] = true; else delete next[el.key];
                          setForm({ ...form, elements: next });
                        }}
                        disabled={status === 'running'}
                        style={{ margin: 0 }}
                      />
                      {el.label}
                    </label>
                  );
                })}
              </div>
            </Field>

            <Field label="Free-Form-Wunsch (optional)">
              <textarea
                value={form.user_prompt}
                onChange={(e) => setForm({ ...form, user_prompt: e.target.value })}
                disabled={status === 'running'}
                rows={4}
                placeholder="z.B.: Hero mit Foerder-Badge oben links, grosse Headline, Subtext, primaerer CTA + Telefonnummer als sekundaere Aktion"
                style={{ ...inputStyle(false), resize: 'vertical' }}
              />
            </Field>

            <button
              type="button" onClick={onGenerate}
              disabled={status === 'running'}
              style={{
                width: '100%', marginTop: 8,
                padding: '10px 14px',
                background: '#7c3aed', opacity: status === 'running' ? 0.5 : 1,
                color: '#fff', border: 'none', borderRadius: 8,
                fontSize: 12, fontWeight: 700,
                cursor: status === 'running' ? 'wait' : 'pointer',
                textTransform: 'uppercase', letterSpacing: '0.04em',
              }}
            >
              {status === 'running' ? 'Generiert…' : (status === 'done' ? '🔄 Nochmal generieren' : '✨ Generieren')}
            </button>
          </div>

          {/* Preview / Status */}
          <div style={{ flex: 1, overflowY: 'auto', background: '#fff', padding: 16 }}>
            {status === 'idle' && (
              <div style={{ padding: 32, textAlign: 'center', color: '#94a3b8', fontSize: 13 }}>
                Form ausfuellen und „Generieren" klicken.<br/>Erwartete Wartezeit: 8–15 Sekunden.
              </div>
            )}
            {status === 'running' && (
              <div style={{ padding: 32, textAlign: 'center', color: '#64748b', fontSize: 13 }}>
                <div style={{ fontSize: 32, marginBottom: 12 }}>⏳</div>
                Opus 5 schreibt deine Komponente…<br/>
                <div style={{ fontSize: 12, marginTop: 8, color: '#94a3b8' }}>Polling alle 2s · Background-Job</div>
              </div>
            )}
            {status === 'error' && (
              <div style={{ padding: 16, background: '#fee2e2', border: '1px solid #fca5a5', borderRadius: 8, color: '#991b1b', fontSize: 12 }}>
                <div style={{ fontWeight: 700, marginBottom: 4 }}>Fehler:</div>
                {error || 'Unbekannter Fehler'}
              </div>
            )}
            {status === 'done' && result && (
              <div>
                <div style={{ marginBottom: 12 }}>
                  <div style={{ fontSize: 14, fontWeight: 800, color: '#0f172a', marginBottom: 4 }}>{result.name}</div>
                  <div style={{ fontSize: 12, color: '#64748b' }}>{result.preview_note}</div>
                  <div style={{ fontSize: 12, color: '#94a3b8', marginTop: 4 }}>
                    {(result.slots || []).length} Slots · {(result.tags || []).join(' · ')}
                  </div>
                </div>

                {/* Der Vertragsbefund faehrt aus dem Job mit. Er gehoert hierher,
                    nicht erst hinter das Speichern — sonst uebernimmt man einen
                    Block und wundert sich, warum er als Entwurf landet. */}
                <ContractPanel
                  contract={result.contract}
                  status={result.contract?.konform ? 'approved' : 'draft'}
                  hinweis={'Uebernehmen und speichern geht trotzdem — der Block landet '
                    + 'dann als Entwurf und wartet dort auf die Reparatur.'}
                />
                <div style={{
                  border: '1px solid #e2e8f0', borderRadius: 8, overflow: 'hidden',
                  background: '#fff', pointerEvents: 'none', marginBottom: 12,
                }}>
                  {previewHtml ? (
                    <div dangerouslySetInnerHTML={{ __html: previewHtml }} />
                  ) : (
                    <div style={{ padding: 16, textAlign: 'center', color: '#94a3b8', fontSize: 12 }}>Keine Preview</div>
                  )}
                </div>
                <div style={{
                  background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 6,
                  padding: 10, fontSize: 12, color: '#475569', marginBottom: 12,
                }}>
                  <div style={{ fontWeight: 700, fontSize: 12, textTransform: 'uppercase', color: '#64748b', marginBottom: 4 }}>
                    KI-Prompt-Hint:
                  </div>
                  {result.ki_prompt_hint || '(leer)'}
                </div>
                <button
                  type="button" onClick={onUseResult}
                  style={{
                    width: '100%', padding: '10px 14px',
                    background: 'var(--success)', color: 'var(--text-on-brand)', border: 'none', borderRadius: 8,
                    fontSize: 12, fontWeight: 700, cursor: 'pointer',
                    textTransform: 'uppercase', letterSpacing: '0.04em',
                  }}
                >✓ In Editor uebernehmen (Slug eingeben + speichern)</button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Editor sub-component ─────────────────────────────────────────────────────


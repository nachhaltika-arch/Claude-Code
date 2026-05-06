/**
 * ComponentLibrary — UI Phase 1 fuer den Component-Manager.
 *
 * Liste aller Library-Eintraege links, Editor rechts. Ueber Quelle (KAS /
 * HyperUI / Custom) und Kategorie filterbar. Live-Preview rendert
 * `{{slot}}`-Marker mit Default-Werten — gleiche Logik wie WireframeView.
 *
 * Backend: GET/POST/PUT/DELETE auf /api/components.
 */
import { useCallback, useEffect, useMemo, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import API_BASE_URL from '../config';
import toast from 'react-hot-toast';

const KC_DARK = '#004F59';
const KC_MID = '#008EAA';

const CATEGORY_OPTIONS = [
  'NAV', 'HERO', 'LEIST', 'TRUST', 'SEO', 'CTA', 'HW', 'FOOT', 'CUSTOM',
];

const SOURCES = [
  { id: 'all',    label: 'Alle' },
  { id: 'kas',    label: 'KAS' },
  { id: 'hyperui', label: 'HyperUI' },
  { id: 'custom', label: 'Custom' },
];

function detectSource(tags) {
  const t = (tags || []).map((x) => String(x).toLowerCase());
  if (t.includes('hyperui')) return 'hyperui';
  if (t.includes('custom') || t.includes('user-saved')) return 'custom';
  return 'kas';
}

function renderSlots(html, slotValues) {
  if (!html) return '';
  if (!slotValues || typeof slotValues !== 'object') return html;
  const escape = (s) => String(s).replace(/[<>&"']/g, (c) => (
    { '<': '&lt;', '>': '&gt;', '&': '&amp;', '"': '&quot;', "'": '&#39;' }[c]
  ));
  let result = html;
  Object.entries(slotValues).forEach(([key, value]) => {
    if (value == null) return;
    const re = new RegExp(`\\{\\{\\s*${key.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\s*\\}\\}`, 'g');
    result = result.replace(re, escape(value));
  });
  return result;
}

const SLUG_REGEX = /^[a-z0-9][a-z0-9-]*$/;

function emptyForm() {
  return {
    slug: '',
    name: '',
    category: 'CUSTOM',
    tags: [],
    html_template: '',
    slots: [],
    ki_prompt_hint: '',
    preview_note: '',
  };
}

export default function ComponentLibrary() {
  const { token } = useAuth();
  const headers = useMemo(
    () => ({ Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }),
    [token],
  );

  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [sourceFilter, setSourceFilter] = useState('all');
  const [categoryFilter, setCategoryFilter] = useState('all');

  const [selectedSlug, setSelectedSlug] = useState(null);
  const [form, setForm] = useState(emptyForm());
  const [isNew, setIsNew] = useState(false);
  const [dirty, setDirty] = useState(false);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/components?include_html=true`, { headers });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setItems(Array.isArray(data) ? data : []);
    } catch (e) {
      toast.error(`Laden fehlgeschlagen: ${e.message}`);
    } finally {
      setLoading(false);
    }
  }, [headers]);

  useEffect(() => { reload(); }, [reload]);

  const filtered = useMemo(() => {
    let list = items;
    if (sourceFilter !== 'all') {
      list = list.filter((c) => detectSource(c.tags) === sourceFilter);
    }
    if (categoryFilter !== 'all') {
      list = list.filter((c) => c.category === categoryFilter);
    }
    if (searchQuery.trim()) {
      const q = searchQuery.trim().toLowerCase();
      list = list.filter(
        (c) =>
          c.slug.toLowerCase().includes(q)
          || c.name.toLowerCase().includes(q)
          || (c.tags || []).some((t) => String(t).toLowerCase().includes(q)),
      );
    }
    return list;
  }, [items, sourceFilter, categoryFilter, searchQuery]);

  const counts = useMemo(() => {
    const c = { all: items.length, kas: 0, hyperui: 0, custom: 0 };
    items.forEach((it) => { c[detectSource(it.tags)] += 1; });
    return c;
  }, [items]);

  const openItem = (item) => {
    if (dirty && !window.confirm('Ungespeicherte Aenderungen verwerfen?')) return;
    setSelectedSlug(item.slug);
    setIsNew(false);
    setForm({
      slug:           item.slug,
      name:           item.name || '',
      category:       item.category || 'CUSTOM',
      tags:           item.tags || [],
      html_template:  item.html_template || '',
      slots:          item.slots || [],
      ki_prompt_hint: item.ki_prompt_hint || '',
      preview_note:   item.preview_note || '',
    });
    setDirty(false);
  };

  const openNew = () => {
    if (dirty && !window.confirm('Ungespeicherte Aenderungen verwerfen?')) return;
    setSelectedSlug(null);
    setIsNew(true);
    setForm(emptyForm());
    setDirty(false);
  };

  const updateForm = (patch) => {
    setForm((f) => ({ ...f, ...patch }));
    setDirty(true);
  };

  const previewHtml = useMemo(() => {
    const defaults = (form.slots || []).reduce((acc, s) => {
      if (s.key) acc[s.key] = s.default ?? '';
      return acc;
    }, {});
    return renderSlots(form.html_template, defaults);
  }, [form.html_template, form.slots]);

  const validate = () => {
    if (!form.slug || !SLUG_REGEX.test(form.slug)) {
      return 'Slug muss kleinbuchstaben, ziffern, bindestriche enthalten';
    }
    if (!form.name.trim()) return 'Name darf nicht leer sein';
    if (!form.html_template || form.html_template.trim().length < 20) {
      return 'HTML-Template fehlt oder zu kurz';
    }
    if (!form.category.trim()) return 'Kategorie waehlen';
    return null;
  };

  const save = async () => {
    const err = validate();
    if (err) { toast.error(err); return; }
    setSaving(true);
    try {
      if (isNew) {
        const res = await fetch(`${API_BASE_URL}/api/components`, {
          method: 'POST', headers,
          body: JSON.stringify({
            slug:           form.slug,
            name:           form.name,
            category:       form.category,
            tags:           form.tags,
            html_template:  form.html_template,
            slots:          form.slots,
            ki_prompt_hint: form.ki_prompt_hint,
            preview_note:   form.preview_note,
          }),
        });
        const body = await res.json().catch(() => ({}));
        if (!res.ok) throw new Error(body?.detail || `HTTP ${res.status}`);
        toast.success(`Angelegt: ${body.slug}`);
        await reload();
        setSelectedSlug(body.slug);
        setIsNew(false);
        setDirty(false);
      } else {
        const res = await fetch(`${API_BASE_URL}/api/components/${form.slug}`, {
          method: 'PUT', headers,
          body: JSON.stringify({
            name:           form.name,
            category:       form.category,
            tags:           form.tags,
            html_template:  form.html_template,
            slots:          form.slots,
            ki_prompt_hint: form.ki_prompt_hint,
            preview_note:   form.preview_note,
          }),
        });
        const body = await res.json().catch(() => ({}));
        if (!res.ok) throw new Error(body?.detail || `HTTP ${res.status}`);
        toast.success('Gespeichert');
        await reload();
        setDirty(false);
      }
    } catch (e) {
      toast.error(`Speichern fehlgeschlagen: ${e.message}`);
    } finally {
      setSaving(false);
    }
  };

  const remove = async () => {
    if (isNew || !form.slug) return;
    if (!window.confirm(`Komponente "${form.name}" (${form.slug}) wirklich loeschen?`)) return;
    setDeleting(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/components/${form.slug}`, {
        method: 'DELETE', headers,
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(body?.detail || `HTTP ${res.status}`);
      toast.success('Geloescht');
      await reload();
      setSelectedSlug(null);
      setForm(emptyForm());
      setIsNew(false);
      setDirty(false);
    } catch (e) {
      toast.error(`Loeschen fehlgeschlagen: ${e.message}`);
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16, fontFamily: 'var(--font-sans)' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 900, color: KC_DARK, margin: 0, textTransform: 'uppercase' }}>
            Komponenten-Bibliothek
          </h1>
          <p style={{ fontSize: 12, color: '#64748b', marginTop: 4 }}>
            {loading ? 'Laedt…' : `${items.length} Eintraege · ${filtered.length} sichtbar`}
          </p>
        </div>
        <button
          type="button" onClick={openNew}
          style={{
            background: KC_DARK, color: '#fff', border: 'none',
            borderRadius: 8, padding: '9px 16px', fontSize: 12, fontWeight: 700,
            cursor: 'pointer', textTransform: 'uppercase', letterSpacing: '0.04em',
          }}
        >+ Neue Komponente</button>
      </div>

      {/* Filters */}
      <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
        <input
          type="text" placeholder="Suchen (Slug / Name / Tag)…"
          value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)}
          style={{
            flex: '1 1 220px', minWidth: 0, padding: '7px 12px',
            border: '1px solid #cbd5e1', borderRadius: 6, fontSize: 13, outline: 'none',
          }}
        />
        <div style={{ display: 'inline-flex', gap: 0, border: '1px solid #e2e8f0', borderRadius: 8, overflow: 'hidden' }}>
          {SOURCES.map((s) => {
            const active = sourceFilter === s.id;
            return (
              <button
                key={s.id} type="button" onClick={() => setSourceFilter(s.id)}
                style={{
                  background: active ? KC_DARK : 'transparent',
                  color: active ? '#fff' : '#475569',
                  border: 'none', cursor: 'pointer',
                  padding: '6px 10px', fontSize: 11, fontWeight: 700,
                  textTransform: 'uppercase', letterSpacing: '0.04em',
                  fontFamily: 'inherit',
                }}
              >{s.label} <span style={{ opacity: 0.6 }}>({counts[s.id] ?? 0})</span></button>
            );
          })}
        </div>
        <select
          value={categoryFilter} onChange={(e) => setCategoryFilter(e.target.value)}
          style={{ padding: '7px 10px', border: '1px solid #cbd5e1', borderRadius: 6, fontSize: 12, background: '#fff' }}
        >
          <option value="all">Alle Kategorien</option>
          {CATEGORY_OPTIONS.map((c) => <option key={c} value={c}>{c}</option>)}
        </select>
      </div>

      {/* Body: 2-column list + editor */}
      <div style={{ display: 'flex', gap: 16, minHeight: 600 }}>
        {/* List */}
        <aside style={{
          width: 320, flexShrink: 0,
          background: '#fff', border: '1px solid #e2e8f0', borderRadius: 8,
          overflowY: 'auto', maxHeight: 'calc(100vh - 260px)',
        }}>
          {loading && <div style={{ padding: 16, color: '#64748b', fontSize: 12 }}>Laedt…</div>}
          {!loading && filtered.length === 0 && (
            <div style={{ padding: 16, color: '#94a3b8', fontSize: 12, textAlign: 'center' }}>
              Keine Treffer.
            </div>
          )}
          {!loading && filtered.map((it) => {
            const active = selectedSlug === it.slug && !isNew;
            const src = detectSource(it.tags);
            return (
              <button
                key={it.slug} type="button" onClick={() => openItem(it)}
                style={{
                  display: 'block', width: '100%', textAlign: 'left',
                  padding: '10px 12px',
                  border: 'none', borderBottom: '1px solid #f1f5f9',
                  borderLeft: active ? `3px solid ${KC_MID}` : '3px solid transparent',
                  background: active ? '#f0f9fb' : '#fff',
                  cursor: 'pointer', fontFamily: 'inherit',
                }}
              >
                <div style={{ display: 'flex', gap: 8, alignItems: 'baseline' }}>
                  <span style={{
                    background: '#e2e8f0', color: '#475569',
                    fontSize: 9, fontWeight: 700, padding: '1px 5px', borderRadius: 3,
                    textTransform: 'uppercase', letterSpacing: '0.04em',
                  }}>{it.category}</span>
                  <span style={{ fontSize: 12, fontWeight: 700, color: KC_DARK, flex: 1, minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {it.name}
                  </span>
                  <span style={{
                    fontSize: 9, fontWeight: 700, color: '#64748b',
                    textTransform: 'uppercase', letterSpacing: '0.04em',
                  }}>{src}</span>
                </div>
                <div style={{ fontSize: 10, color: '#94a3b8', fontFamily: 'ui-monospace, monospace', marginTop: 2 }}>
                  {it.slug}
                </div>
              </button>
            );
          })}
        </aside>

        {/* Editor */}
        <main style={{
          flex: 1, minWidth: 0,
          background: '#fff', border: '1px solid #e2e8f0', borderRadius: 8,
          display: 'flex', flexDirection: 'column',
          maxHeight: 'calc(100vh - 260px)',
        }}>
          {!isNew && !selectedSlug ? (
            <div style={{ padding: 32, textAlign: 'center', color: '#94a3b8', fontSize: 13 }}>
              Waehle links eine Komponente oder lege eine neue an.
            </div>
          ) : (
            <Editor
              form={form} updateForm={updateForm}
              isNew={isNew} dirty={dirty}
              saving={saving} deleting={deleting}
              previewHtml={previewHtml}
              onSave={save} onDelete={remove}
            />
          )}
        </main>
      </div>
    </div>
  );
}

// ── Editor sub-component ─────────────────────────────────────────────────────

function Editor({
  form, updateForm, isNew, dirty,
  saving, deleting, previewHtml,
  onSave, onDelete,
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
        <div style={{ fontSize: 13, fontWeight: 800, color: KC_DARK }}>
          {isNew ? 'Neue Komponente' : form.name || form.slug}
          {dirty && <span style={{ marginLeft: 8, fontSize: 10, color: '#92400e', background: '#FEF3C7', padding: '2px 6px', borderRadius: 4 }}>UNGESPEICHERT</span>}
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          {!isNew && (
            <button
              type="button" onClick={onDelete} disabled={deleting || saving}
              style={{
                padding: '6px 12px', fontSize: 11, fontWeight: 700,
                background: '#fff', color: '#dc2626',
                border: '1px solid #fca5a5', borderRadius: 6,
                cursor: deleting ? 'wait' : 'pointer', fontFamily: 'inherit',
              }}
            >{deleting ? 'Loescht…' : 'Loeschen'}</button>
          )}
          <button
            type="button" onClick={onSave} disabled={saving || (!dirty && !isNew)}
            style={{
              padding: '6px 14px', fontSize: 11, fontWeight: 700,
              background: saving || (!dirty && !isNew) ? '#94a3b8' : KC_DARK,
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
          <Field label="Slug">
            <input
              type="text" value={form.slug} disabled={!isNew}
              onChange={(e) => updateForm({ slug: e.target.value.toLowerCase() })}
              placeholder="z.b. my-hero-1"
              style={inputStyle(!isNew)}
            />
            <Hint>{isNew ? 'Kleinbuchstaben, Ziffern, Bindestriche.' : 'Slug ist nicht editierbar.'}</Hint>
          </Field>

          <Field label="Name">
            <input
              type="text" value={form.name}
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
                  padding: '2px 8px', borderRadius: 12, fontSize: 11,
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
              <button type="button" onClick={addTag}
                style={{ padding: '6px 10px', fontSize: 11, background: '#fff', border: '1px solid #cbd5e1', borderRadius: 6, cursor: 'pointer' }}>+</button>
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
                    style={{ ...inputStyle(false), flex: 1, fontFamily: 'ui-monospace, monospace', fontSize: 11 }}
                  />
                  <button type="button" onClick={() => removeSlot(idx)}
                    style={{ padding: '4px 8px', fontSize: 11, background: '#fff', color: '#dc2626', border: '1px solid #fca5a5', borderRadius: 4, cursor: 'pointer' }}>×</button>
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
              style={{ padding: '6px 10px', fontSize: 11, background: '#fff', border: '1px dashed #cbd5e1', borderRadius: 6, cursor: 'pointer', width: '100%' }}>
              + Slot hinzufuegen
            </button>
          </Field>

          <Field label="HTML-Template">
            <textarea
              value={form.html_template}
              onChange={(e) => updateForm({ html_template: e.target.value })}
              rows={14}
              style={{
                width: '100%', boxSizing: 'border-box',
                padding: 8, border: '1px solid #cbd5e1', borderRadius: 6,
                fontSize: 11, fontFamily: 'ui-monospace, monospace', resize: 'vertical',
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

function Field({ label, children }) {
  return (
    <div style={{ marginBottom: 12 }}>
      <label style={{
        display: 'block', fontSize: 10, fontWeight: 700, color: '#475569',
        textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 4,
      }}>{label}</label>
      {children}
    </div>
  );
}

function Hint({ children }) {
  return (
    <div style={{ fontSize: 10, color: '#94a3b8', marginTop: 3 }}>{children}</div>
  );
}

function inputStyle(disabled) {
  return {
    width: '100%', boxSizing: 'border-box',
    padding: '7px 10px',
    border: '1px solid #cbd5e1', borderRadius: 6,
    fontSize: 12, fontFamily: 'inherit',
    background: disabled ? '#f1f5f9' : '#fff',
    color: disabled ? '#64748b' : 'inherit',
    outline: 'none',
  };
}

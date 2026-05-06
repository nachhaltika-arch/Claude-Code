/**
 * ComponentLibrary — UI Phase 1 fuer den Component-Manager.
 *
 * Liste aller Library-Eintraege links, Editor rechts. Ueber Quelle (KAS /
 * HyperUI / Custom) und Kategorie filterbar. Live-Preview rendert
 * `{{slot}}`-Marker mit Default-Werten — gleiche Logik wie WireframeView.
 *
 * Backend: GET/POST/PUT/DELETE auf /api/components.
 */
import React, { useCallback, useEffect, useMemo, useState } from 'react';
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

// Element-Picker im KI-Generator. Counts: User legt Anzahl fest (0 = KI entscheidet).
// Bools: User aktiviert/deaktiviert ein Element (false/leer = KI entscheidet).
const COUNT_ELEMENTS = [
  { key: 'headline',    label: 'Headlines',    max: 4 },
  { key: 'subtext',     label: 'Subtexte',     max: 5 },
  { key: 'buttons',     label: 'Buttons / CTAs', max: 4 },
  { key: 'links',       label: 'Links',        max: 12 },
  { key: 'images',      label: 'Bilder',       max: 12 },
  { key: 'icons',       label: 'Icons',        max: 12 },
  { key: 'cards',       label: 'Karten',       max: 12 },
  { key: 'avatars',     label: 'Avatare',      max: 6 },
  { key: 'stats',       label: 'Stat-Counter', max: 6 },
  { key: 'form_fields', label: 'Formular-Felder', max: 8 },
];
const BOOL_ELEMENTS = [
  { key: 'logo',     label: 'Logo' },
  { key: 'dropdown', label: 'Dropdown' },
  { key: 'search',   label: 'Such-Feld' },
  { key: 'rating',   label: 'Star-Rating' },
  { key: 'video',    label: 'Video / iframe' },
  { key: 'list',     label: 'Liste (bullet)' },
];

// Branchen-Dropdown im KI-Generator. Default 'shk' = aktuelle KAS-Niche.
// Backend kennt 'shk' / 'bauhandwerk' / 'gala' / 'maler' / 'kfz' /
// 'steuer-anwalt' / 'medizin' / 'gastro' / 'kosmetik' / 'fitness' /
// 'custom' / 'none'.
const INDUSTRIES = [
  { id: 'shk',           label: 'SHK (Heizung/Sanitaer/Elektrik)' },
  { id: 'bauhandwerk',   label: 'Bauhandwerk (Maurer, Dachdecker, Trockenbau)' },
  { id: 'gala',          label: 'Garten- und Landschaftsbau' },
  { id: 'maler',         label: 'Maler & Stuckateur' },
  { id: 'kfz',           label: 'KFZ-Werkstatt / Auto-Service' },
  { id: 'steuer-anwalt', label: 'Steuerberater / Anwalt / Versicherung' },
  { id: 'medizin',       label: 'Arzt / Zahnarzt / Praxis' },
  { id: 'gastro',        label: 'Gastronomie / Hotel / Restaurant' },
  { id: 'kosmetik',      label: 'Friseur / Kosmetik / Wellness' },
  { id: 'fitness',       label: 'Fitness / Sport / Yoga' },
  { id: 'custom',        label: 'Custom (selbst beschreiben)…' },
  { id: 'none',          label: 'Keine — generisch' },
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

// Slugify mit deutschen Sonderzeichen-Mapping (vor normalize damit ae/oe/ue/ss
// nicht durch NFD-Decomposition zu a/o/u/s reduziert werden).
function slugify(text) {
  return (text || '')
    .toLowerCase()
    .replace(/ä/g, 'ae')
    .replace(/ö/g, 'oe')
    .replace(/ü/g, 'ue')
    .replace(/ß/g, 'ss')
    .normalize('NFD').replace(/[̀-ͯ]/g, '')
    .replace(/[^a-z0-9-]+/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-+|-+$/g, '');
}

// Macht slug eindeutig gegen die aktuelle Library — haengt -2/-3/... an wenn noetig.
function generateUniqueSlug(base, existingSlugs) {
  if (!base) return '';
  const existing = new Set(existingSlugs);
  if (!existing.has(base)) return base;
  let n = 2;
  while (existing.has(`${base}-${n}`)) n++;
  return `${base}-${n}`;
}

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

  // AI-Generator (Component-Designer)
  const [aiOpen, setAiOpen] = useState(false);
  const [aiForm, setAiForm] = useState({
    category: 'HERO', style_vibe: 'elegant', user_prompt: '',
    industry: 'shk', industry_custom: '',
    elements: {}, // { headline: 2, buttons: 2, logo: true, ... }
  });
  const [aiStatus, setAiStatus] = useState('idle'); // idle | running | done | error
  const [aiJobId, setAiJobId] = useState(null);
  const [aiResult, setAiResult] = useState(null);
  const [aiError, setAiError] = useState(null);

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

  const save = async () => {
    // Bei NEU + leerem Slug: Auto-Generation aus Name. Sonst: Slug muss valide sein.
    let effectiveSlug = form.slug.trim();
    if (isNew && !effectiveSlug && form.name.trim()) {
      const base = slugify(form.name);
      effectiveSlug = generateUniqueSlug(base, items.map((i) => i.slug));
      setForm((f) => ({ ...f, slug: effectiveSlug }));
    }

    if (!effectiveSlug || !SLUG_REGEX.test(effectiveSlug)) {
      toast.error('Slug muss kleinbuchstaben, ziffern, bindestriche enthalten');
      return;
    }
    if (!form.name.trim()) { toast.error('Name darf nicht leer sein'); return; }
    if (!form.html_template || form.html_template.trim().length < 20) {
      toast.error('HTML-Template fehlt oder zu kurz');
      return;
    }
    if (!form.category.trim()) { toast.error('Kategorie waehlen'); return; }

    setSaving(true);
    try {
      if (isNew) {
        const res = await fetch(`${API_BASE_URL}/api/components`, {
          method: 'POST', headers,
          body: JSON.stringify({
            slug:           effectiveSlug,
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

  // ── AI-Generator-Logik ────────────────────────────────────────────────────

  const startAiGenerate = async () => {
    setAiStatus('running');
    setAiError(null);
    setAiResult(null);
    try {
      const res = await fetch(`${API_BASE_URL}/api/components/generate`, {
        method: 'POST', headers,
        body: JSON.stringify(aiForm),
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(body?.detail || `HTTP ${res.status}`);
      setAiJobId(body.job_id);
    } catch (e) {
      setAiStatus('error');
      setAiError(e.message);
    }
  };

  // Poll job-status every 2 sec while running
  useEffect(() => {
    if (!aiJobId || aiStatus !== 'running') return;
    let cancelled = false;
    const tick = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/api/components/generate/${aiJobId}`, { headers });
        if (cancelled) return;
        if (res.status === 404) {
          // Job verschwunden — als Fehler behandeln
          setAiStatus('error');
          setAiError('Job nicht gefunden');
          setAiJobId(null);
          return;
        }
        const body = await res.json();
        if (body.status === 'done') {
          setAiResult(body.result);
          setAiStatus('done');
          setAiJobId(null);
        } else if (body.status === 'error') {
          setAiStatus('error');
          setAiError(body.error || 'Unbekannter Fehler');
          setAiJobId(null);
        }
      } catch (e) {
        if (!cancelled) {
          setAiStatus('error');
          setAiError(e.message);
          setAiJobId(null);
        }
      }
    };
    const t = setInterval(tick, 2000);
    tick(); // sofort einmal pollen
    return () => { cancelled = true; clearInterval(t); };
  }, [aiJobId, aiStatus, headers]);

  const closeAiModal = () => {
    setAiOpen(false);
    setAiStatus('idle');
    setAiJobId(null);
    setAiResult(null);
    setAiError(null);
  };

  // Uebernimmt das KI-Resultat in den Editor (als neue Komponente).
  // Slug wird automatisch aus Name slugifiziert + eindeutig gemacht.
  const useAiResult = () => {
    if (!aiResult) return;
    if (dirty && !window.confirm('Ungespeicherte Aenderungen verwerfen?')) return;
    const baseSlug = slugify(aiResult.name || `${aiForm.category.toLowerCase()}-ai`);
    const uniqueSlug = generateUniqueSlug(baseSlug, items.map((i) => i.slug));
    setSelectedSlug(null);
    setIsNew(true);
    setForm({
      slug: uniqueSlug,
      name: aiResult.name || '',
      category: aiResult.category || aiForm.category,
      tags: aiResult.tags || [],
      html_template: aiResult.html_template || '',
      slots: aiResult.slots || [],
      ki_prompt_hint: aiResult.ki_prompt_hint || '',
      preview_note: aiResult.preview_note || '',
    });
    setDirty(true);
    closeAiModal();
    toast.success(`KI-Komponente uebernommen — Slug: ${uniqueSlug}`);
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
        <div style={{ display: 'flex', gap: 8 }}>
          <button
            type="button" onClick={() => { setAiOpen(true); setAiStatus('idle'); }}
            style={{
              background: '#7c3aed', color: '#fff', border: 'none',
              borderRadius: 8, padding: '9px 16px', fontSize: 12, fontWeight: 700,
              cursor: 'pointer', textTransform: 'uppercase', letterSpacing: '0.04em',
            }}
          >✨ Mit KI generieren</button>
          <button
            type="button" onClick={openNew}
            style={{
              background: KC_DARK, color: '#fff', border: 'none',
              borderRadius: 8, padding: '9px 16px', fontSize: 12, fontWeight: 700,
              cursor: 'pointer', textTransform: 'uppercase', letterSpacing: '0.04em',
            }}
          >+ Neue Komponente</button>
        </div>
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

      {/* AI-Generator-Modal */}
      {aiOpen && (
        <AiGeneratorModal
          form={aiForm} setForm={setAiForm}
          status={aiStatus} result={aiResult} error={aiError}
          onGenerate={startAiGenerate}
          onUseResult={useAiResult}
          onClose={closeAiModal}
        />
      )}
    </div>
  );
}

// ── AI-Generator-Modal ───────────────────────────────────────────────────────

function AiGeneratorModal({ form, setForm, status, result, error, onGenerate, onUseResult, onClose }) {
  const previewHtml = useMemo(() => {
    if (!result?.html_template) return '';
    const defaults = (result.slots || []).reduce((acc, s) => {
      if (s.key) acc[s.key] = s.default ?? '';
      return acc;
    }, {});
    return renderSlots(result.html_template, defaults);
  }, [result]);

  return (
    <div onClick={(e) => e.target === e.currentTarget && onClose()} style={{
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
            <div style={{ fontSize: 11, opacity: 0.9, marginTop: 2 }}>
              Sonnet 4.6 · Wireframe-Stil (neutral grau) · CI-Design folgt im Projekt-Prozess
            </div>
          </div>
          <button type="button" onClick={onClose} disabled={status === 'running'}
            style={{ background: 'none', border: 'none', fontSize: 22, cursor: 'pointer', color: '#fff', lineHeight: 1, opacity: status === 'running' ? 0.4 : 1 }}>×</button>
        </div>

        {/* Body: 2 Spalten — Form links, Preview/Result rechts */}
        <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
          {/* Form */}
          <div style={{ flex: '0 0 360px', padding: 16, overflowY: 'auto', borderRight: '1px solid #e2e8f0', background: '#f8fafc' }}>
            <Field label="Kategorie">
              <select
                value={form.category}
                onChange={(e) => setForm({ ...form, category: e.target.value })}
                disabled={status === 'running'}
                style={inputStyle(false)}
              >
                {CATEGORY_OPTIONS.map((c) => <option key={c} value={c}>{c}</option>)}
              </select>
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
                        borderRadius: 6, fontSize: 11, fontWeight: 700,
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
                  style={{ ...inputStyle(false), marginTop: 6, resize: 'vertical', fontSize: 11 }}
                />
              )}
            </Field>

            <Field label="Pflicht-Elemente (optional — leer = KI entscheidet)">
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 70px', gap: '4px 8px', fontSize: 11, marginBottom: 8 }}>
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
                        borderRadius: 4, fontSize: 11, fontFamily: 'inherit',
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
                        fontSize: 11, color: '#475569', cursor: 'pointer',
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
                background: status === 'running' ? '#94a3b8' : '#7c3aed',
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
                Sonnet 4.6 schreibt deine Komponente…<br/>
                <div style={{ fontSize: 11, marginTop: 8, color: '#94a3b8' }}>Polling alle 2s · Background-Job</div>
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
                  <div style={{ fontSize: 11, color: '#64748b' }}>{result.preview_note}</div>
                  <div style={{ fontSize: 10, color: '#94a3b8', marginTop: 4 }}>
                    {(result.slots || []).length} Slots · {(result.tags || []).join(' · ')}
                  </div>
                </div>
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
                  padding: 10, fontSize: 11, color: '#475569', marginBottom: 12,
                }}>
                  <div style={{ fontWeight: 700, fontSize: 10, textTransform: 'uppercase', color: '#64748b', marginBottom: 4 }}>
                    KI-Prompt-Hint:
                  </div>
                  {result.ki_prompt_hint || '(leer)'}
                </div>
                <button
                  type="button" onClick={onUseResult}
                  style={{
                    width: '100%', padding: '10px 14px',
                    background: '#10b981', color: '#fff', border: 'none', borderRadius: 8,
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
              placeholder={isNew ? 'leer lassen → wird aus Name erzeugt' : ''}
              style={inputStyle(!isNew)}
            />
            <Hint>{isNew ? 'Kleinbuchstaben, Ziffern, Bindestriche. Leer lassen → automatisch aus Name (z.B. „SHK Hero Premium" → „shk-hero-premium").' : 'Slug ist nicht editierbar.'}</Hint>
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

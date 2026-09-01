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
import { StatusBadge, anzahlVerstoesse } from '../components/BlockContract';
import { mitBlockMarkierung } from '../utils/blockMarkup';
// Am 30.08.2026 herausgeloest (L-25): `ComponentLibrary.jsx` trug 1.264
// Zeilen und darin zwei eigenstaendige Komponenten samt Feldbausteinen und
// Wortschatz.
import { CATEGORY_OPTIONS, KC_DARK, KC_MID, SLUG_REGEX, SOURCES, STATES, detectSource, emptyForm, generateUniqueSlug, renderSlots, slugify } from '../components/bibliothek/katalog';
import AiGeneratorModal from '../components/bibliothek/AiGeneratorModal';
import Editor from '../components/bibliothek/Editor';

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
  const [stateFilter, setStateFilter] = useState('all');

  const [selectedSlug, setSelectedSlug] = useState(null);
  const [form, setForm] = useState(emptyForm());
  const [isNew, setIsNew] = useState(false);
  const [dirty, setDirty] = useState(false);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [approving, setApproving] = useState(false);

  // AI-Generator (Component-Designer)
  const [aiOpen, setAiOpen] = useState(false);
  const [aiForm, setAiForm] = useState({
    category: 'HERO', style_vibe: 'elegant', user_prompt: '',
    industry: 'shk', industry_custom: '',
    elements: {}, // { headline: 2, buttons: 2, logo: true, ... }
    layout_preset: '', // Phase A (Weg 1): vordefiniertes Layout-Muster
  });
  const [aiStatus, setAiStatus] = useState('idle'); // idle | running | done | error
  const [aiJobId, setAiJobId] = useState(null);
  const [aiResult, setAiResult] = useState(null);
  const [aiError, setAiError] = useState(null);
  // Phase A (Weg 1): Layout-Presets vom Backend
  const [layoutPresets, setLayoutPresets] = useState([]);

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/components/layout-presets`, { headers })
      .then((r) => (r.ok ? r.json() : []))
      .then((data) => setLayoutPresets(Array.isArray(data) ? data : []))
      .catch(() => setLayoutPresets([]));
  }, [headers]);

  // Presets zur aktuellen Kategorie
  const presetsForCategory = useMemo(
    () => layoutPresets.filter((p) => p.category === aiForm.category),
    [layoutPresets, aiForm.category],
  );

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      // Der Manager ist der Ort, an dem Entwuerfe bearbeitet und freigegeben
      // werden — hier muessen sie sichtbar sein, samt Vertragsbefund.
      const res = await fetch(
        `${API_BASE_URL}/api/components?include_html=true&include_drafts=true`,
        { headers },
      );
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
    if (stateFilter !== 'all') {
      list = list.filter((c) => (c.status || 'approved') === stateFilter);
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
  }, [items, sourceFilter, categoryFilter, stateFilter, searchQuery]);

  const counts = useMemo(() => {
    const c = { all: items.length, kas: 0, hyperui: 0, custom: 0 };
    items.forEach((it) => { c[detectSource(it.tags)] += 1; });
    return c;
  }, [items]);

  const stateCounts = useMemo(() => {
    const c = { all: items.length, approved: 0, draft: 0 };
    items.forEach((it) => { c[(it.status || 'approved') === 'draft' ? 'draft' : 'approved'] += 1; });
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
      status:         item.status || 'approved',
      contract:       item.contract || null,
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

  // Ein Block, der auf Entwurf faellt, darf das nicht stillschweigend tun —
  // sonst sieht der Nutzer nur, dass sein Block aus dem Wireframe-Editor
  // verschwindet, und haelt es fuer einen Fehler.
  const meldeVertrag = (body, erfolgstext) => {
    const offen = anzahlVerstoesse(body?.contract);
    if (body?.status === 'draft') {
      toast(`${erfolgstext} — als Entwurf: ${offen} ${offen === 1 ? 'Punkt' : 'Punkte'} `
            + 'aus dem Vertrag offen. Details stehen im Editor.',
      { icon: '⚠️', duration: 6000 });
      return;
    }
    toast.success(erfolgstext);
  };

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
        meldeVertrag(body, `Angelegt: ${body.slug}`);
        setForm((f) => ({ ...f, status: body.status, contract: body.contract || null }));
        setSelectedSlug(body.slug);
        setIsNew(false);
        // Erst den Zustand setzen, dann nachladen. Andersherum wuerde eine
        // Eingabe, die waehrend des Nachladens passiert, wieder als
        // „gespeichert" gelten — und der Speichern-Knopf bliebe grau.
        setDirty(false);
        await reload();
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
        meldeVertrag(body, 'Gespeichert');
        setForm((f) => ({ ...f, status: body.status, contract: body.contract || null }));
        setDirty(false);
        await reload();
      }
    } catch (e) {
      toast.error(`Speichern fehlgeschlagen: ${e.message}`);
    } finally {
      setSaving(false);
    }
  };

  // Freigabe: der Punkt, an dem ein Block auf Kundenseiten landen kann. Das
  // Backend verweigert sie bei Vertragsbruch mit 422 — die Verstoesse stecken
  // dann in detail.contract und gehoeren angezeigt, nicht verschluckt.
  const approve = async () => {
    if (!form.slug || isNew) return;
    setApproving(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/components/${form.slug}/approve`, {
        method: 'POST', headers,
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        const detail = body?.detail;
        if (detail?.contract) {
          setForm((f) => ({ ...f, contract: detail.contract }));
        }
        throw new Error(typeof detail === 'string' ? detail
          : detail?.message || `HTTP ${res.status}`);
      }
      setForm((f) => ({ ...f, status: body.status, contract: body.contract || null }));
      toast.success('Freigegeben — der Block steht jetzt im Wireframe-Editor.');
      await reload();
    } catch (e) {
      toast.error(`Freigabe abgelehnt: ${e.message}`);
    } finally {
      setApproving(false);
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
  // Slug: der von der KI vergebene, notfalls eindeutig gemacht — und dann
  // wandert er auch ins Markup. Regel R2 verlangt, dass `data-block` zum Slug
  // passt; benennt die Oberflaeche nur den Eintrag um, faellt der eben noch
  // saubere Block beim Speichern auf Entwurf zurueck.
  const useAiResult = () => {
    if (!aiResult) return;
    if (dirty && !window.confirm('Ungespeicherte Aenderungen verwerfen?')) return;
    const baseSlug = slugify(aiResult.slug || aiResult.name || `${aiForm.category.toLowerCase()}-ai`);
    const uniqueSlug = generateUniqueSlug(baseSlug, items.map((i) => i.slug));
    setSelectedSlug(null);
    setIsNew(true);
    setForm({
      slug: uniqueSlug,
      name: aiResult.name || '',
      category: aiResult.category || aiForm.category,
      tags: aiResult.tags || [],
      html_template: mitBlockMarkierung(aiResult.html_template || '', uniqueSlug),
      slots: aiResult.slots || [],
      ki_prompt_hint: aiResult.ki_prompt_hint || '',
      preview_note: aiResult.preview_note || '',
      // Der Befund aus dem Job bleibt sichtbar, bis das Speichern ihn ersetzt.
      status: aiResult.contract?.konform === false ? 'draft' : 'approved',
      contract: aiResult.contract || null,
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
        <input aria-label="Suchen (Slug / Name / Tag)…"
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
                  padding: '6px 10px', fontSize: 12, fontWeight: 700,
                  textTransform: 'uppercase', letterSpacing: '0.04em',
                  fontFamily: 'inherit',
                }}
              >{s.label} <span style={{ opacity: 0.6 }}>({counts[s.id] ?? 0})</span></button>
            );
          })}
        </div>
        <div style={{ display: 'inline-flex', gap: 0, border: '1px solid #e2e8f0', borderRadius: 8, overflow: 'hidden' }}>
          {STATES.map((s) => {
            const active = stateFilter === s.id;
            return (
              <button
                key={s.id} type="button" onClick={() => setStateFilter(s.id)}
                style={{
                  background: active ? '#92400e' : 'transparent',
                  color: active ? '#fff' : '#475569',
                  border: 'none', cursor: 'pointer',
                  padding: '6px 10px', fontSize: 12, fontWeight: 700,
                  textTransform: 'uppercase', letterSpacing: '0.04em',
                  fontFamily: 'inherit',
                }}
              >{s.label} <span style={{ opacity: 0.6 }}>({stateCounts[s.id] ?? 0})</span></button>
            );
          })}
        </div>
        <select aria-label="Nach Kategorie filtern"
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
            const entwurf = (it.status || 'approved') === 'draft';
            // Freigegeben und trotzdem verletzt: die Altlast (hw-karte,
            // seo-lokal). Nicht verstecken — sonst faellt sie erst beim Kunden auf.
            const altlast = !entwurf && anzahlVerstoesse(it.contract) > 0;
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
                    fontSize: 12, fontWeight: 700, padding: '1px 5px', borderRadius: 3,
                    textTransform: 'uppercase', letterSpacing: '0.04em',
                  }}>{it.category}</span>
                  <span style={{ fontSize: 12, fontWeight: 700, color: KC_DARK, flex: 1, minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {it.name}
                  </span>
                  <span style={{
                    fontSize: 12, fontWeight: 700, color: '#64748b',
                    textTransform: 'uppercase', letterSpacing: '0.04em',
                  }}>{src}</span>
                </div>
                <div style={{ display: 'flex', gap: 6, alignItems: 'center', marginTop: 2 }}>
                  <span style={{ fontSize: 12, color: '#94a3b8', fontFamily: 'ui-monospace, monospace', flex: 1, minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {it.slug}
                  </span>
                  {entwurf && <StatusBadge status="draft" />}
                  {altlast && (
                    <span
                      title={`Freigegeben, verletzt aber den Vertrag (${anzahlVerstoesse(it.contract)} Punkte)`}
                      style={{ fontSize: 12, color: '#b45309' }}
                    >⚠️</span>
                  )}
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
              saving={saving} deleting={deleting} approving={approving}
              previewHtml={previewHtml}
              onSave={save} onDelete={remove} onApprove={approve}
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
          presets={presetsForCategory}
        />
      )}
    </div>
  );
}

// ── AI-Generator-Modal ───────────────────────────────────────────────────────

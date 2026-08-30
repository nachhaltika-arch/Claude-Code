import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useScreenSize } from '../utils/responsive';
import API_BASE_URL from '../config';
import { schreibe } from '../utils/schreiben';
import { loeschfrage } from '../utils/loeschfrage';
import Feld from '../components/ui/Feld';
import SeitenTitel from '../components/ui/SeitenTitel';
import { aufTaste } from '../utils/tastaturBedienung';
import { ModuleBlock, PreviewCard, ThumbnailUpload } from '../components/akademie/kursBausteine';
import { S, useDragSort } from '../components/akademie/kursDaten';

// ── Shared styles ──────────────────────────────────────────────

// ── Drag helpers ───────────────────────────────────────────────

// ── Field component ────────────────────────────────────────────

// Verknüpft statt nur danebengestellt (L-17).
function Field({ label, children }) {
  return <Feld label={label} labelStyle={S.label}>{children}</Feld>;
}

// ── Thumbnail upload area ──────────────────────────────────────

export default function AcademyAdminCourse() {
  const { courseId } = useParams();
  const isNew = !courseId || courseId === 'new';
  const navigate = useNavigate();
  const { token, user, hasRole } = useAuth();
  const { isMobile, isTablet } = useScreenSize();
  const h = { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) };

  const [loading, setLoading] = useState(!isNew);
  const [saving,  setSaving]  = useState(false);
  const [savedId, setSavedId] = useState(isNew ? null : Number(courseId));

  const [form, setForm] = useState({
    title:           '',
    description:     '',
    thumbnail_url:   '',
    target_audience: 'both',
    audience:        'employee',
    is_published:    false,
    linear_progress: false,
    is_locked:       false,
  });

  const [modules, setModules]       = useState([]);
  const [addingModule, setAddingModule] = useState(false);
  const [newModTitle,  setNewModTitle]  = useState('');

  const setF = (key) => (val) => setForm(prev => ({ ...prev, [key]: val }));
  // Eine Stelle fuer alle Meldungen dieses Bildschirms. Leer heisst: alles gut.
  const [fehler, setFehler] = useState('');

  // ── Load existing course ──────────────────────────────────────

  useEffect(() => {
    if (isNew) return;
    fetch(`${API_BASE_URL}/api/academy/courses/${courseId}`, { headers: h })
      .then(r => r.json())
      .then(data => {
        setForm({
          title:           data.title           || '',
          description:     data.description     || '',
          thumbnail_url:   data.thumbnail_url   || '',
          target_audience: data.target_audience || 'both',
          audience:        data.audience        || 'employee',
          is_published:    Boolean(data.is_published),
          linear_progress: Boolean(data.linear_progress),
          is_locked:       Boolean(data.is_locked),
        });
        setModules(Array.isArray(data.modules) ? data.modules : []);
      })
      .catch(() => navigate('/app/akademie/admin'))
      .finally(() => setLoading(false));
  }, [courseId]); // eslint-disable-line

  // ── Save course ───────────────────────────────────────────────

  const save = async () => {
    if (!form.title.trim()) return;
    setSaving(true);
    const anlegen = isNew || !savedId;
    const { ok, antwort, fehler: meldung } = await schreibe(() => fetch(
      anlegen
        ? `${API_BASE_URL}/api/academy/courses`
        : `${API_BASE_URL}/api/academy/courses/${savedId}`,
      { method: anlegen ? 'POST' : 'PUT', headers: h, body: JSON.stringify({ ...form }) },
    ), 'Der Kurs');
    setFehler(ok ? '' : meldung);
    if (ok) {
      const data = await antwort.json();
      setSavedId(data.id);
      if (isNew) navigate(`/app/academy/admin/course/${data.id}`, { replace: true });
    }
    setSaving(false);
  };

  // ── Module CRUD ───────────────────────────────────────────────

  const reorderModules = async (next) => {
    if (!savedId) return;
    const { ok, fehler: meldung } = await schreibe(() => fetch(
      `${API_BASE_URL}/api/academy/courses/${savedId}/modules/reorder`, {
        method: 'PUT', headers: h,
        body: JSON.stringify({ order: next.map((m, i) => ({ id: m.id, sort_order: i })) }),
      }), 'Die Reihenfolge');
    setFehler(ok ? '' : meldung);
  };

  const { handlers: modHandlers, overIdx: modOver } = useDragSort(modules, setModules, reorderModules);

  const addModule = async () => {
    if (!newModTitle.trim() || addingModule || !savedId) return;
    setAddingModule(true);
    const { ok, antwort, fehler: meldung } = await schreibe(() => fetch(
      `${API_BASE_URL}/api/academy/courses/${savedId}/modules`, {
        method: 'POST', headers: h,
        body: JSON.stringify({ title: newModTitle.trim(), sort_order: modules.length }),
      }), 'Das Modul');
    setFehler(ok ? '' : meldung);
    if (ok) {
      const mod = await antwort.json();
      setModules(prev => [...prev, { ...mod, lessons: [] }]);
      setNewModTitle('');
    }
    setAddingModule(false);
  };

  // Ein Weg fuer alle Modulfelder statt einer Funktion je Feld. Vorher gab es
  // zwei fast gleiche, und mit Beschreibung und Vorschaubild waeren es vier
  // geworden — genau die Bauart, an der im Backend die zwei Anlegewege
  // auseinandergelaufen waeren.
  const FELDNAME = {
    title: 'Der Modulname',
    is_locked: 'Der Zugang',
    description: 'Die Modulbeschreibung',
    thumbnail_url: 'Das Vorschaubild',
  };

  const updateModulFeld = async (id, feld, wert) => {
    setModules(prev => prev.map(m => m.id === id ? { ...m, [feld]: wert } : m));
    const { ok, fehler: meldung } = await schreibe(() => fetch(
      `${API_BASE_URL}/api/academy/modules/${id}`,
      { method: 'PUT', headers: h, body: JSON.stringify({ [feld]: wert }) }),
      FELDNAME[feld] || 'Das Feld');
    setFehler(ok ? '' : meldung);
  };

  const deleteModule = async (id) => {
    // Die Frage nennt, was mitgeht: Ein Modul zieht seine Lektionen mit, und
    // „Modul und alle Lektionen darin löschen?" sagt nicht, wie viele das sind.
    const modul = modules.find(m => m.id === id);
    if (!window.confirm(loeschfrage('Modul', modul?.title, [
      [(modul?.lessons || []).length, 'Lektion', 'Lektionen'],
    ]))) return;
    const { ok, fehler: meldung } = await schreibe(() => fetch(
      `${API_BASE_URL}/api/academy/modules/${id}`, { method: 'DELETE', headers: h }), 'Das Modul');
    setFehler(ok ? '' : meldung);
    if (ok) setModules(prev => prev.filter(m => m.id !== id));
  };

  // ── Access guard ──────────────────────────────────────────────

  if (!hasRole('admin')) return (
    <div style={{ textAlign: 'center', padding: 60, color: 'var(--text-tertiary)' }}>
      <div style={{ fontSize: 48, marginBottom: 12 }}>🔒</div>
      <div style={{ fontSize: 14 }}>Nur für Administratoren</div>
    </div>
  );

  if (loading) return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '40vh' }}>
      <div style={{ width: 28, height: 28, borderRadius: '50%', border: '3px solid var(--border-light)', borderTopColor: 'var(--brand-primary)', animation: 'spin 0.8s linear infinite' }} />
    </div>
  );

  const lessonCount = modules.reduce((sum, m) => sum + (m.lessons?.length || 0), 0);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20, width: '100%' }}>
      <SeitenTitel>Kurs bearbeiten</SeitenTitel>

      {/* ── Topbar / Breadcrumb ───────────────────────────────── */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        flexWrap: 'wrap', gap: 12,
        paddingBottom: 20, borderBottom: '1px solid var(--border-light)',
      }}>
        {/* Breadcrumb */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13 }}>
          <button onClick={() => navigate('/app/akademie/admin')} style={{ background: 'none', border: 'none', color: 'var(--text-tertiary)', cursor: 'pointer', padding: 0, fontFamily: 'var(--font-sans)' }}>
            Kurse verwalten
          </button>
          <span style={{ color: 'var(--border-medium)' }}>›</span>
          <span style={{ color: 'var(--text-primary)', fontWeight: 500 }}>
            {isNew ? 'Neuer Kurs' : form.title || `Kurs #${courseId}`}
          </span>
        </div>

        {/* Action buttons */}
        <div style={{ display: 'flex', gap: 8 }}>
          <button
            onClick={() => savedId && navigate(`/app/academy/${savedId}`)}
            disabled={!savedId}
            style={{
              padding: '7px 14px',
              background: 'transparent', color: 'var(--text-secondary)',
              border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)',
              fontSize: 12, cursor: savedId ? 'pointer' : 'not-allowed',
              fontFamily: 'var(--font-sans)', opacity: savedId ? 1 : 0.5,
            }}
          >👁 Vorschau</button>
          <button
            onClick={save}
            disabled={saving || !form.title.trim()}
            style={{
              padding: '7px 20px',
              background: 'var(--brand-primary)', color: 'var(--text-on-brand)',
              border: 'none', borderRadius: 'var(--radius-md)',
              fontSize: 12, fontWeight: 600, cursor: saving || !form.title.trim() ? 'not-allowed' : 'pointer',
              fontFamily: 'var(--font-sans)', opacity: saving || !form.title.trim() ? 0.6 : 1,
              display: 'flex', alignItems: 'center', gap: 6,
            }}
            onMouseEnter={e => { if (!saving) e.currentTarget.style.opacity = '0.85'; }}
            onMouseLeave={e => { e.currentTarget.style.opacity = saving ? '0.6' : '1'; }}
          >
            {saving && (
              <span style={{ display: 'inline-block', width: 11, height: 11, borderRadius: '50%', border: '2px solid rgba(255,255,255,0.4)', borderTopColor: '#fff', animation: 'spin 0.8s linear infinite' }} />
            )}
            {saving ? 'Speichert…' : 'Speichern'}
          </button>
        </div>
      </div>

      {/* Was schiefging, steht hier — und nicht mehr nur in der Konsole.
        * Bis zum 18.08.2026 hoerte der Knopf einfach auf zu drehen; dass sich
        * keine Lektion anlegen liess, ist deshalb nie jemandem aufgefallen. */}
      {fehler && (
        <div
          role="alert"
          style={{
            margin: '0 0 16px', padding: '10px 14px',
            background: 'var(--status-danger-bg)', color: 'var(--status-danger-text)',
            border: '1px solid var(--status-danger-text)',
            borderRadius: 'var(--radius-md)', fontSize: 13, lineHeight: 1.5,
            display: 'flex', alignItems: 'flex-start', gap: 10,
          }}
        >
          <span aria-hidden="true">⚠️</span>
          <span style={{ flex: 1 }}>{fehler}</span>
          <button
            type="button" onClick={() => setFehler('')}
            aria-label="Meldung schliessen"
            style={{
              background: 'none', border: 'none', cursor: 'pointer',
              color: 'inherit', fontSize: 14, lineHeight: 1, padding: 2,
            }}
          >✕</button>
        </div>
      )}

      {/* ── 2-column layout ───────────────────────────────────── */}
      <div style={{ display: 'grid', gridTemplateColumns: (isMobile || isTablet) ? '1fr' : '1fr 340px', gap: 20, alignItems: 'start' }}>

        {/* ── LEFT COLUMN ─────────────────────────────────────── */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

          {/* CARD 1 — Course details */}
          <div style={S.card}>
            <div style={S.cardHeader}>
              <span style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>Kursdetails</span>
            </div>
            <div style={S.cardBody}>

              <Field label="Kurstitel *">
                <input
                  value={form.title}
                  onChange={e => setF('title')(e.target.value)}
                  placeholder="z.B. SEO-Grundlagen für Einsteiger"
                  style={S.input}
                  onFocus={e => e.target.style.borderColor = 'var(--brand-primary-mid)'}
                  onBlur={e => e.target.style.borderColor = 'var(--border-medium)'}
                />
              </Field>

              <Field label="Kurzbeschreibung">
                <textarea
                  value={form.description}
                  onChange={e => setF('description')(e.target.value)}
                  rows={3}
                  placeholder="Worum geht es in diesem Kurs?"
                  style={{ ...S.input, resize: 'vertical' }}
                  onFocus={e => e.target.style.borderColor = 'var(--brand-primary-mid)'}
                  onBlur={e => e.target.style.borderColor = 'var(--border-medium)'}
                />
              </Field>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                <Field label="Zielgruppe">
                  <select
                    value={form.target_audience}
                    onChange={e => { setF('target_audience')(e.target.value); setF('audience')(e.target.value === 'both' ? 'employee' : e.target.value); }}
                    style={S.input}
                  >
                    <option value="customer">Für Kunden</option>
                    <option value="employee">Für Mitarbeiter</option>
                    <option value="both">Für alle</option>
                  </select>
                </Field>

                <Field label="Status">
                  <select
                    value={form.is_published ? 'published' : 'draft'}
                    onChange={e => setF('is_published')(e.target.value === 'published')}
                    style={S.input}
                  >
                    <option value="published">✅ Veröffentlicht</option>
                    <option value="draft">📝 Entwurf</option>
                  </select>
                </Field>
              </div>

              <ThumbnailUpload url={form.thumbnail_url} onUrlChange={setF('thumbnail_url')} />

              <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', fontSize: 13, color: 'var(--text-secondary)' }}>
                <input
                  type="checkbox"
                  checked={form.linear_progress}
                  onChange={e => setF('linear_progress')(e.target.checked)}
                  style={{ accentColor: 'var(--brand-primary)', width: 16, height: 16 }}
                />
                Lineare Freischaltung (Lektionen müssen der Reihe nach abgeschlossen werden)
              </label>

              {/* Zugang: „Veröffentlicht" ist der redaktionelle Zustand,
                  „nur für Zugewiesene" der Zugang. Zwei Fragen, zwei Felder —
                  aus dem Memberspot-Vergleich. */}
              <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', fontSize: 13, color: 'var(--text-secondary)' }}>
                <input
                  type="checkbox"
                  checked={form.is_locked}
                  onChange={e => setF('is_locked')(e.target.checked)}
                  style={{ accentColor: 'var(--brand-primary)', width: 16, height: 16 }}
                />
                Nur für zugewiesene Kunden (sonst für alle der Zielgruppe sichtbar)
              </label>
            </div>
          </div>

          {/* CARD 2 — Modules & Lessons */}
          <div style={S.card}>
            <div style={S.cardHeader}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>Module & Lektionen</span>
                {modules.length > 0 && (
                  <span style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>
                    {modules.length} {modules.length === 1 ? 'Modul' : 'Module'} · {lessonCount} {lessonCount === 1 ? 'Lektion' : 'Lektionen'}
                  </span>
                )}
              </div>
            </div>
            <div style={{ padding: 20, display: 'flex', flexDirection: 'column', gap: 10 }}>
              {!savedId && (
                <div style={{
                  fontSize: 12, color: 'var(--text-tertiary)', background: 'var(--bg-app)',
                  borderRadius: 'var(--radius-md)', padding: '10px 14px', textAlign: 'center',
                }}>
                  Speichere den Kurs zuerst, um Module hinzuzufügen.
                </div>
              )}

              {modules.length === 0 && savedId && (
                <div style={{ fontSize: 12, color: 'var(--text-tertiary)', textAlign: 'center', padding: '16px 0' }}>
                  Noch keine Module. Füge unten ein Modul hinzu.
                </div>
              )}

              {modules.map((mod, mIdx) => (
                <ModuleBlock
                  key={mod.id}
                  mod={mod}
                  modIdx={mIdx}
                  isDragTarget={modOver.current === mIdx}
                  modDragHandlers={modHandlers}
                  courseId={savedId}
                  token={token}
                  h={h}
                  onUpdateFeld={updateModulFeld}
                  onDeleteModule={deleteModule}
                  onFehler={setFehler}
                />
              ))}

              {savedId && (
                <div style={{ display: 'flex', gap: 8, marginTop: 4 }}>
                  <input aria-label="Modulname…"
                    value={newModTitle}
                    onChange={e => setNewModTitle(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && addModule()}
                    placeholder="Modulname…"
                    style={{ ...S.input, flex: 1 }}
                    onFocus={e => e.target.style.borderColor = 'var(--brand-primary-mid)'}
                    onBlur={e => e.target.style.borderColor = 'var(--border-medium)'}
                  />
                  <button
                    onClick={addModule}
                    disabled={addingModule || !newModTitle.trim()}
                    style={{
                      padding: '9px 16px', background: 'var(--brand-primary)', color: 'var(--text-on-brand)',
                      border: 'none', borderRadius: 'var(--radius-md)',
                      fontSize: 12, fontWeight: 600, cursor: 'pointer',
                      fontFamily: 'var(--font-sans)',
                      opacity: !newModTitle.trim() ? 0.5 : 1, whiteSpace: 'nowrap',
                    }}
                  >+ Modul hinzufügen</button>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* ── RIGHT COLUMN ──────────────────────────────────────── */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16, position: 'sticky', top: 20 }}>

          {/* Preview card */}
          <div>
            <div style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 8 }}>
              Vorschau
            </div>
            <PreviewCard form={form} />
          </div>

          {/* Info card */}
          <div style={S.card}>
            <div style={{ padding: '14px 20px', borderBottom: '1px solid var(--border-light)' }}>
              <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>Kursinfo</span>
            </div>
            <div style={{ padding: '14px 20px', display: 'flex', flexDirection: 'column', gap: 10 }}>
              {[
                { label: 'Module',    value: modules.length },
                { label: 'Lektionen', value: lessonCount },
                { label: 'Zertifikat', value: 'Automatisch bei 100%' },
                ...(savedId ? [{ label: 'Kurs-ID', value: `#${savedId}` }] : []),
              ].map(({ label, value }) => (
                <div key={label} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>{label}</span>
                  <span style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-primary)' }}>{value}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Status toggle shortcut */}
          <div style={{
            ...S.card, padding: '14px 20px',
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          }}>
            <div>
              <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 2 }}>
                {form.is_published ? 'Veröffentlicht' : 'Entwurf'}
              </div>
              <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>
                {form.is_published ? 'Für Nutzer sichtbar' : 'Nicht öffentlich'}
              </div>
            </div>
            <div role="button" tabIndex={0} onKeyDown={aufTaste(() => setF('is_published')(!form.is_published))}
              onClick={() => setF('is_published')(!form.is_published)}
              style={{
                width: 40, height: 22, borderRadius: 11, cursor: 'pointer',
                background: form.is_published ? 'var(--status-success-text)' : 'var(--border-medium)',
                position: 'relative', transition: 'background 0.2s',
              }}
            >
              <div style={{
                position: 'absolute', top: 3, width: 16, height: 16, borderRadius: '50%',
                background: 'var(--bg-surface)', transition: 'left 0.2s',
                left: form.is_published ? 21 : 3,
                boxShadow: '0 1px 3px rgba(0,0,0,0.2)',
              }} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

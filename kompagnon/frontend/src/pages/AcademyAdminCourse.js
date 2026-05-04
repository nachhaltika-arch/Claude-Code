import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useScreenSize } from '../utils/responsive';
import API_BASE_URL from '../config';

// ── Shared styles ──────────────────────────────────────────────

const S = {
  input: {
    width: '100%', padding: '9px 12px',
    border: '1px solid var(--border-medium)',
    borderRadius: 'var(--radius-md)', fontSize: 13,
    fontFamily: 'var(--font-sans)', color: 'var(--text-primary)',
    background: 'var(--bg-surface)', outline: 'none', boxSizing: 'border-box',
    transition: 'border-color 0.15s',
  },
  label: {
    display: 'block', fontSize: 10, fontWeight: 600,
    color: 'var(--text-tertiary)', textTransform: 'uppercase',
    letterSpacing: '0.06em', marginBottom: 5,
  },
  card: {
    background: 'var(--bg-surface)', border: '1px solid var(--border-light)',
    borderRadius: 'var(--radius-lg)', overflow: 'hidden',
  },
  cardHeader: {
    padding: '14px 20px', borderBottom: '1px solid var(--border-light)',
    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
  },
  cardBody: { padding: '20px', display: 'flex', flexDirection: 'column', gap: 16 },
};

const TYPE_BADGE = {
  video:     { bg: 'var(--status-info-bg)',    color: 'var(--status-info-text)',    label: 'VIDEO' },
  text:      { bg: 'var(--status-neutral-bg)', color: 'var(--status-neutral-text)', label: 'TEXT' },
  quiz:      { bg: 'var(--status-warning-bg)', color: 'var(--status-warning-text)', label: 'QUIZ' },
  checklist: { bg: 'var(--status-success-bg)', color: 'var(--status-success-text)', label: 'LISTE' },
};

const AUDIENCE_LABEL = {
  employee: 'Für Mitarbeiter',
  customer: 'Für Kunden',
  both:     'Für alle',
};

// ── Drag helpers ───────────────────────────────────────────────

function useDragSort(items, setItems, onReorder) {
  const from = useRef(null);
  const over = useRef(null);
  const [active, setActive] = useState(false);

  const handlers = (idx) => ({
    draggable: true,
    onDragStart: () => { from.current = idx; setActive(true); },
    onDragEnter: () => { over.current = idx; },
    onDragOver:  (e) => e.preventDefault(),
    onDragEnd:   async () => {
      setActive(false);
      const f = from.current; const t = over.current;
      from.current = null; over.current = null;
      if (f === null || t === null || f === t) return;
      const next = [...items];
      const [moved] = next.splice(f, 1);
      next.splice(t, 0, moved);
      setItems(next);
      if (onReorder) await onReorder(next);
    },
  });

  return { handlers, active, overIdx: over };
}

// ── Field component ────────────────────────────────────────────

function Field({ label, children }) {
  return (
    <div>
      <label style={S.label}>{label}</label>
      {children}
    </div>
  );
}

// ── Thumbnail upload area ──────────────────────────────────────

function ThumbnailUpload({ url, onUrlChange }) {
  const [draggingOver, setDraggingOver] = useState(false);

  return (
    <div>
      <label style={S.label}>Thumbnail (URL oder Drag & Drop)</label>
      <input
        value={url}
        onChange={e => onUrlChange(e.target.value)}
        placeholder="https://…/bild.jpg"
        style={S.input}
      />
      <div
        onDragOver={e => { e.preventDefault(); setDraggingOver(true); }}
        onDragLeave={() => setDraggingOver(false)}
        onDrop={e => {
          e.preventDefault();
          setDraggingOver(false);
          const text = e.dataTransfer.getData('text');
          if (text) onUrlChange(text);
        }}
        style={{
          marginTop: 8,
          height: url ? 'auto' : 80,
          minHeight: url ? 0 : 80,
          border: `1.5px dashed ${draggingOver ? 'var(--brand-primary)' : 'var(--border-medium)'}`,
          borderRadius: 'var(--radius-md)',
          background: draggingOver ? 'var(--bg-active)' : 'var(--bg-app)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          transition: 'border-color 0.15s, background 0.15s',
          overflow: 'hidden',
        }}
      >
        {url ? (
          <div style={{ position: 'relative', width: '100%', paddingTop: '56.25%' }}>
            <img
              src={url}
              alt="Thumbnail"
              style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover', borderRadius: 'var(--radius-md)' }}
              onError={e => e.target.style.display = 'none'}
            />
            <button
              onClick={() => onUrlChange('')}
              style={{
                position: 'absolute', top: 8, right: 8,
                background: 'rgba(15,28,32,0.6)', color: '#fff',
                border: 'none', borderRadius: 'var(--radius-full)',
                width: 24, height: 24, fontSize: 13, cursor: 'pointer', lineHeight: 1,
              }}
            >×</button>
          </div>
        ) : (
          <span style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>
            🖼 URL per Drag & Drop ablegen
          </span>
        )}
      </div>
    </div>
  );
}

// ── Lesson row ─────────────────────────────────────────────────

function LessonRow({ lesson, dragHandlers, isDragTarget, onEdit, onDelete }) {
  const badge = TYPE_BADGE[lesson.type] || TYPE_BADGE.text;
  const dur   = lesson.duration_minutes ? `${lesson.duration_minutes} min` : null;

  return (
    <div
      {...dragHandlers}
      style={{
        display: 'flex', alignItems: 'center', gap: 8,
        padding: '8px 10px',
        background: isDragTarget ? 'var(--bg-active)' : 'var(--bg-app)',
        borderRadius: 'var(--radius-md)', border: '1px solid var(--border-light)',
        transition: 'background 0.1s', cursor: 'default',
      }}
    >
      <span style={{ fontSize: 14, color: 'var(--text-tertiary)', opacity: 0.5, cursor: 'grab', flexShrink: 0 }}>⠿</span>
      <span style={{
        fontSize: 9, fontWeight: 700, padding: '2px 6px',
        borderRadius: 'var(--radius-full)', flexShrink: 0,
        background: badge.bg, color: badge.color,
        letterSpacing: '0.06em',
      }}>{badge.label}</span>
      <span style={{ fontSize: 13, color: 'var(--text-primary)', flex: 1, minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
        {lesson.title || <span style={{ color: 'var(--text-tertiary)', fontStyle: 'italic' }}>Ohne Titel</span>}
      </span>
      {dur && <span style={{ fontSize: 11, color: 'var(--text-tertiary)', flexShrink: 0 }}>{dur}</span>}
      <button
        onClick={onEdit}
        style={{
          padding: '3px 8px', background: 'var(--bg-surface)', color: 'var(--text-secondary)',
          border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-sm)',
          fontSize: 11, cursor: 'pointer', flexShrink: 0,
        }}
      >✏️</button>
      <button
        onClick={onDelete}
        style={{
          padding: '3px 8px', background: 'var(--status-danger-bg)', color: 'var(--status-danger-text)',
          border: 'none', borderRadius: 'var(--radius-sm)',
          fontSize: 11, cursor: 'pointer', flexShrink: 0,
        }}
      >🗑</button>
    </div>
  );
}

// ── Module block ───────────────────────────────────────────────

function ModuleBlock({
  mod, modIdx, isDragTarget, modDragHandlers,
  courseId, token, h,
  onUpdateTitle, onToggleLock, onDeleteModule,
}) {
  const navigate = useNavigate();
  const [lessons, setLessons]       = useState(mod.lessons || []);
  const [collapsed, setCollapsed]   = useState(false);
  const [addingLesson, setAddingLesson] = useState(false);

  const lessonOverRef = useRef(null);

  const reorderLessons = async (next) => {
    try {
      await fetch(`${API_BASE_URL}/api/academy/modules/${mod.id}/lessons/reorder`, {
        method: 'PUT', headers: h,
        body: JSON.stringify({ order: next.map((l, i) => ({ id: l.id, sort_order: i })) }),
      });
    } catch (e) { console.error(e); }
  };

  const { handlers: lsnHandlers, overIdx: lsnOver } = useDragSort(lessons, setLessons, reorderLessons);

  const addLesson = async () => {
    if (addingLesson) return;
    setAddingLesson(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/academy/modules/${mod.id}/lessons`, {
        method: 'POST', headers: h,
        body: JSON.stringify({ title: 'Neue Lektion', type: 'text', sort_order: lessons.length }),
      });
      if (res.ok) {
        const lesson = await res.json();
        setLessons(prev => [...prev, lesson]);
      }
    } catch (e) { console.error(e); }
    finally { setAddingLesson(false); }
  };

  const deleteLesson = async (lessonId) => {
    if (!window.confirm('Lektion löschen?')) return;
    try {
      await fetch(`${API_BASE_URL}/api/academy/lessons/${lessonId}`, { method: 'DELETE', headers: h });
      setLessons(prev => prev.filter(l => l.id !== lessonId));
    } catch (e) { console.error(e); }
  };

  return (
    <div
      {...modDragHandlers(modIdx)}
      style={{
        border: `1px solid ${isDragTarget ? 'var(--brand-primary)' : 'var(--border-light)'}`,
        borderRadius: 'var(--radius-md)', overflow: 'hidden',
        background: isDragTarget ? 'var(--bg-active)' : 'var(--bg-surface)',
        transition: 'border-color 0.15s, background 0.1s',
      }}
    >
      {/* Module header */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 8,
        padding: '10px 12px', background: 'var(--bg-app)',
        borderBottom: collapsed ? 'none' : '1px solid var(--border-light)',
      }}>
        <span style={{ fontSize: 14, color: 'var(--text-tertiary)', opacity: 0.5, cursor: 'grab', flexShrink: 0 }}>⠿</span>

        <input
          value={mod.title}
          onChange={e => onUpdateTitle(mod.id, e.target.value)}
          onClick={e => e.stopPropagation()}
          style={{
            ...S.input, flex: 1, padding: '5px 8px', fontSize: 13,
            fontWeight: 600, background: 'transparent', border: '1px solid transparent',
          }}
          onFocus={e => e.target.style.borderColor = 'var(--border-medium)'}
          onBlur={e => e.target.style.borderColor = 'transparent'}
        />

        {/* Locked toggle */}
        <label
          title={mod.is_locked ? 'Gesperrt' : 'Freigeschaltet'}
          style={{ display: 'flex', alignItems: 'center', gap: 4, cursor: 'pointer', flexShrink: 0 }}
          onClick={e => e.stopPropagation()}
        >
          <input
            type="checkbox"
            checked={mod.is_locked || false}
            onChange={() => onToggleLock(mod.id, !mod.is_locked)}
            style={{ accentColor: 'var(--brand-primary)', width: 14, height: 14 }}
          />
          <span style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>Gesperrt</span>
        </label>

        <button
          onClick={() => navigate(`/app/akademie/admin/modul/${mod.id}`)}
          style={{
            padding: '3px 8px', background: 'var(--bg-surface)', color: 'var(--text-secondary)',
            border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-sm)',
            fontSize: 11, cursor: 'pointer',
          }}
        >✏️</button>

        <button
          onClick={() => onDeleteModule(mod.id)}
          style={{
            padding: '3px 8px', background: 'var(--status-danger-bg)', color: 'var(--status-danger-text)',
            border: 'none', borderRadius: 'var(--radius-sm)',
            fontSize: 11, cursor: 'pointer',
          }}
        >🗑</button>

        <button
          onClick={() => setCollapsed(c => !c)}
          style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-tertiary)', fontSize: 12, padding: '0 2px' }}
        >{collapsed ? '▼' : '▲'}</button>
      </div>

      {/* Lesson list */}
      {!collapsed && (
        <div style={{ padding: '10px 12px', display: 'flex', flexDirection: 'column', gap: 6 }}>
          {lessons.length === 0 && (
            <div style={{ fontSize: 12, color: 'var(--text-tertiary)', textAlign: 'center', padding: '8px 0' }}>
              Noch keine Lektionen
            </div>
          )}
          {lessons.map((lesson, lIdx) => (
            <LessonRow
              key={lesson.id}
              lesson={lesson}
              dragHandlers={lsnHandlers(lIdx)}
              isDragTarget={lsnOver.current === lIdx}
              onEdit={() => navigate(`/app/akademie/admin/modul/${mod.id}`)}
              onDelete={() => deleteLesson(lesson.id)}
            />
          ))}
          <button
            onClick={addLesson}
            disabled={addingLesson}
            style={{
              alignSelf: 'flex-start', padding: '5px 12px',
              background: 'transparent', color: 'var(--brand-primary)',
              border: '1px dashed var(--border-medium)', borderRadius: 'var(--radius-md)',
              fontSize: 12, cursor: 'pointer', fontFamily: 'var(--font-sans)',
              opacity: addingLesson ? 0.6 : 1,
            }}
          >{addingLesson ? '…' : '+ Lektion hinzufügen'}</button>
        </div>
      )}
    </div>
  );
}

// ── Preview card ───────────────────────────────────────────────

function PreviewCard({ form }) {
  const pct  = 0;
  const done = false;
  const aud  = form.target_audience || form.audience;

  return (
    <div style={{
      background: 'var(--bg-surface)', border: '1px solid var(--border-light)',
      borderRadius: 'var(--radius-lg)', overflow: 'hidden',
      boxShadow: 'var(--shadow-card)',
    }}>
      {/* Thumbnail */}
      <div style={{
        paddingTop: '56.25%', position: 'relative',
        background: form.thumbnail_url
          ? `url(${form.thumbnail_url}) center/cover`
          : 'linear-gradient(135deg, var(--brand-primary) 0%, var(--brand-primary-deeper) 100%)',
        borderRadius: 'var(--radius-lg) var(--radius-lg) 0 0',
      }}>
        <div style={{
          position: 'absolute', top: 10, left: 10,
          background: 'var(--brand-primary)', color: '#fff',
          borderRadius: 'var(--radius-full)', fontSize: 10, fontWeight: 600, padding: '2px 9px',
        }}>{AUDIENCE_LABEL[aud] || aud || '—'}</div>
        {!form.thumbnail_url && (
          <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 36, opacity: 0.25 }}>🎓</div>
        )}
      </div>

      {/* Body */}
      <div style={{ padding: '14px 16px 16px', display: 'flex', flexDirection: 'column', gap: 8 }}>
        <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)', lineHeight: 1.35 }}>
          {form.title || <span style={{ color: 'var(--text-tertiary)', fontStyle: 'italic' }}>Kein Titel</span>}
        </div>
        <div style={{
          fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.5,
          display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden',
        }}>
          {form.description || <span style={{ color: 'var(--text-tertiary)' }}>Keine Beschreibung</span>}
        </div>
        {/* Progress bar mock */}
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
            <span style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>Noch nicht gestartet</span>
            <span style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>0%</span>
          </div>
          <div style={{ height: 5, background: 'var(--brand-primary-light)', borderRadius: 3 }}>
            <div style={{ width: '0%', height: '100%', background: 'var(--brand-primary)', borderRadius: 3 }} />
          </div>
        </div>
        <div style={{
          marginTop: 2, padding: '8px 14px', background: 'var(--brand-primary)', color: '#fff',
          border: 'none', borderRadius: 'var(--radius-md)', fontSize: 12, fontWeight: 600,
          textAlign: 'center',
        }}>Starten →</div>
      </div>
    </div>
  );
}

// ── Main component ─────────────────────────────────────────────

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
  });

  const [modules, setModules]       = useState([]);
  const [addingModule, setAddingModule] = useState(false);
  const [newModTitle,  setNewModTitle]  = useState('');

  const setF = (key) => (val) => setForm(prev => ({ ...prev, [key]: val }));

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
    try {
      const body = { ...form };
      let res;
      if (isNew || !savedId) {
        res = await fetch(`${API_BASE_URL}/api/academy/courses`, { method: 'POST', headers: h, body: JSON.stringify(body) });
      } else {
        res = await fetch(`${API_BASE_URL}/api/academy/courses/${savedId}`, { method: 'PUT', headers: h, body: JSON.stringify(body) });
      }
      if (res.ok) {
        const data = await res.json();
        setSavedId(data.id);
        if (isNew) navigate(`/app/akademie/admin/course/${data.id}`, { replace: true });
      }
    } catch (e) { console.error(e); }
    finally { setSaving(false); }
  };

  // ── Module CRUD ───────────────────────────────────────────────

  const reorderModules = async (next) => {
    if (!savedId) return;
    try {
      await fetch(`${API_BASE_URL}/api/academy/courses/${savedId}/modules/reorder`, {
        method: 'PUT', headers: h,
        body: JSON.stringify({ order: next.map((m, i) => ({ id: m.id, sort_order: i })) }),
      });
    } catch (e) { console.error(e); }
  };

  const { handlers: modHandlers, overIdx: modOver } = useDragSort(modules, setModules, reorderModules);

  const addModule = async () => {
    if (!newModTitle.trim() || addingModule || !savedId) return;
    setAddingModule(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/academy/courses/${savedId}/modules`, {
        method: 'POST', headers: h,
        body: JSON.stringify({ title: newModTitle.trim(), sort_order: modules.length }),
      });
      if (res.ok) {
        const mod = await res.json();
        setModules(prev => [...prev, { ...mod, lessons: [] }]);
        setNewModTitle('');
      }
    } catch (e) { console.error(e); }
    finally { setAddingModule(false); }
  };

  const updateModuleTitle = async (id, title) => {
    setModules(prev => prev.map(m => m.id === id ? { ...m, title } : m));
    try {
      await fetch(`${API_BASE_URL}/api/academy/modules/${id}`, { method: 'PUT', headers: h, body: JSON.stringify({ title }) });
    } catch (e) { console.error(e); }
  };

  const toggleModuleLock = async (id, locked) => {
    setModules(prev => prev.map(m => m.id === id ? { ...m, is_locked: locked } : m));
    try {
      await fetch(`${API_BASE_URL}/api/academy/modules/${id}`, { method: 'PUT', headers: h, body: JSON.stringify({ is_locked: locked }) });
    } catch (e) { console.error(e); }
  };

  const deleteModule = async (id) => {
    if (!window.confirm('Modul und alle Lektionen darin löschen?')) return;
    try {
      await fetch(`${API_BASE_URL}/api/academy/modules/${id}`, { method: 'DELETE', headers: h });
      setModules(prev => prev.filter(m => m.id !== id));
    } catch (e) { console.error(e); }
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

      {/* ── Topbar / Breadcrumb ───────────────────────────────── */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        flexWrap: 'wrap', gap: 12,
        paddingBottom: 20, borderBottom: '1px solid var(--border-light)',
      }}>
        {/* Breadcrumb */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13 }}>
          <button onClick={() => navigate('/app/akademie/admin')} style={{ background: 'none', border: 'none', color: 'var(--text-tertiary)', cursor: 'pointer', padding: 0, fontFamily: 'var(--font-sans)' }}>
            Kursverwaltung
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
              background: 'var(--brand-primary)', color: '#fff',
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
                  onFocus={e => e.target.style.borderColor = 'var(--brand-primary)'}
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
                  onFocus={e => e.target.style.borderColor = 'var(--brand-primary)'}
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
                  onUpdateTitle={updateModuleTitle}
                  onToggleLock={toggleModuleLock}
                  onDeleteModule={deleteModule}
                />
              ))}

              {savedId && (
                <div style={{ display: 'flex', gap: 8, marginTop: 4 }}>
                  <input
                    value={newModTitle}
                    onChange={e => setNewModTitle(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && addModule()}
                    placeholder="Modulname…"
                    style={{ ...S.input, flex: 1 }}
                    onFocus={e => e.target.style.borderColor = 'var(--brand-primary)'}
                    onBlur={e => e.target.style.borderColor = 'var(--border-medium)'}
                  />
                  <button
                    onClick={addModule}
                    disabled={addingModule || !newModTitle.trim()}
                    style={{
                      padding: '9px 16px', background: 'var(--brand-primary)', color: '#fff',
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
            <div
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

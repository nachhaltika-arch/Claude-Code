/**
 * Die Bausteine der Kursverwaltung (L-25).
 *
 * Vorschaubild, Lektionszeile, Modulblock und die Vorschaukarte. Am
 * 2026-08-30 aus `AcademyAdminCourse.jsx` herausgeloest — 384 der damals 936
 * Zeilen. Alle vier waren dort schon eigene Funktionen.
 */
import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import API_BASE_URL from '../../config';
import { schreibe } from '../../utils/schreiben';
import { loeschfrage } from '../../utils/loeschfrage';
import { AUDIENCE_LABEL, S, TYPE_BADGE, useDragSort } from './kursDaten';

export function ThumbnailUpload({ url, onUrlChange }) {
  const [draggingOver, setDraggingOver] = useState(false);

  return (
    <div>
      <label style={S.label}>Thumbnail (URL oder Drag & Drop)</label>
      <input aria-label="Thumbnail (URL oder Drag & Drop)"
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

export function LessonRow({ lesson, dragHandlers, isDragTarget, onEdit, onDelete }) {
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
        fontSize: 12, fontWeight: 700, padding: '2px 6px',
        borderRadius: 'var(--radius-full)', flexShrink: 0,
        background: badge.bg, color: badge.color,
        letterSpacing: '0.06em',
      }}>{badge.label}</span>
      <span style={{ fontSize: 13, color: 'var(--text-primary)', flex: 1, minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
        {lesson.title || <span style={{ color: 'var(--text-tertiary)', fontStyle: 'italic' }}>Ohne Titel</span>}
      </span>
      {dur && <span style={{ fontSize: 12, color: 'var(--text-tertiary)', flexShrink: 0 }}>{dur}</span>}
      <button aria-label="Bearbeiten"
        onClick={onEdit}
        style={{
          padding: '3px 8px', background: 'var(--bg-surface)', color: 'var(--text-secondary)',
          border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-sm)',
          fontSize: 12, cursor: 'pointer', flexShrink: 0,
        }}
      >✏️</button>
      <button aria-label="Löschen"
        onClick={onDelete}
        style={{
          padding: '3px 8px', background: 'var(--status-danger-bg)', color: 'var(--status-danger-text)',
          border: 'none', borderRadius: 'var(--radius-sm)',
          fontSize: 12, cursor: 'pointer', flexShrink: 0,
        }}
      >🗑</button>
    </div>
  );
}

// Ein Feld, das beim Verlassen speichert statt bei jedem Tastendruck.
// Der Modulname darueber tut Letzteres seit jeher — bei einem ganzen Satz
// waere das eine Schreibanfrage je Buchstabe.
export function BlurFeld({ wert, platzhalter, onSpeichern, stil }) {
  const [text, setText] = useState(wert || '');

  useEffect(() => { setText(wert || ''); }, [wert]);

  return (
    <input aria-label={platzhalter}
      value={text}
      placeholder={platzhalter}
      onChange={e => setText(e.target.value)}
      onClick={e => e.stopPropagation()}
      onBlur={() => { if (text !== (wert || '')) onSpeichern(text); }}
      onKeyDown={e => { if (e.key === 'Enter') e.target.blur(); }}
      onFocus={e => { e.target.style.borderColor = 'var(--border-medium)'; }}
      style={{
        ...S.input, padding: '4px 8px', fontSize: 12,
        background: 'transparent', border: '1px solid transparent',
        color: 'var(--text-secondary)', ...stil,
      }}
    />
  );
}


// ── Module block ───────────────────────────────────────────────

export function ModuleBlock({
  mod, modIdx, isDragTarget, modDragHandlers,
  courseId, token, h,
  onUpdateFeld, onDeleteModule, onFehler,
}) {
  const navigate = useNavigate();
  const [lessons, setLessons]       = useState(mod.lessons || []);
  const [collapsed, setCollapsed]   = useState(false);
  const [addingLesson, setAddingLesson] = useState(false);

  const lessonOverRef = useRef(null);

  const reorderLessons = async (next) => {
    const { ok, fehler } = await schreibe(() => fetch(
      `${API_BASE_URL}/api/academy/modules/${mod.id}/lessons/reorder`, {
        method: 'PUT', headers: h,
        body: JSON.stringify({ order: next.map((l, i) => ({ id: l.id, sort_order: i })) }),
      }), 'Die Reihenfolge');
    onFehler(ok ? '' : fehler);
  };

  const { handlers: lsnHandlers, overIdx: lsnOver } = useDragSort(lessons, setLessons, reorderLessons);

  const addLesson = async () => {
    if (addingLesson) return;
    setAddingLesson(true);
    // Genau dieser Aufruf antwortete seit jeher mit 500, ohne dass es jemand
    // sah — siehe utils/schreiben.js.
    const { ok, antwort, fehler } = await schreibe(() => fetch(
      `${API_BASE_URL}/api/academy/modules/${mod.id}/lessons`, {
        method: 'POST', headers: h,
        body: JSON.stringify({ title: 'Neue Lektion', type: 'text', sort_order: lessons.length }),
      }), 'Die Lektion');
    onFehler(ok ? '' : fehler);
    if (ok) {
      const lesson = await antwort.json();
      setLessons(prev => [...prev, lesson]);
    }
    setAddingLesson(false);
  };

  const deleteLesson = async (lessonId) => {
    const lektion = lessons.find(l => l.id === lessonId);
    if (!window.confirm(loeschfrage('Lektion', lektion?.title))) return;
    const { ok, fehler } = await schreibe(() => fetch(
      `${API_BASE_URL}/api/academy/lessons/${lessonId}`, { method: 'DELETE', headers: h }),
      'Die Lektion');
    onFehler(ok ? '' : fehler);
    if (ok) setLessons(prev => prev.filter(l => l.id !== lessonId));
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

        <input aria-label="Modultitel"
          value={mod.title}
          onChange={e => onUpdateFeld(mod.id, 'title', e.target.value)}
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
          title={mod.is_locked ? 'Nur für zugewiesene Kunden' : 'Für alle im Kurs sichtbar'}
          style={{ display: 'flex', alignItems: 'center', gap: 4, cursor: 'pointer', flexShrink: 0 }}
          onClick={e => e.stopPropagation()}
        >
          <input
            type="checkbox"
            checked={mod.is_locked || false}
            onChange={() => onUpdateFeld(mod.id, 'is_locked', !mod.is_locked)}
            style={{ accentColor: 'var(--brand-primary)', width: 14, height: 14 }}
          />
          <span style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>Nur Zugewiesene</span>
        </label>

        <button
          onClick={() => onDeleteModule(mod.id)}
          style={{
            padding: '3px 8px', background: 'var(--status-danger-bg)', color: 'var(--status-danger-text)',
            border: 'none', borderRadius: 'var(--radius-sm)',
            fontSize: 12, cursor: 'pointer',
          }}
        >🗑</button>

        <button
          onClick={() => setCollapsed(c => !c)}
          style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-tertiary)', fontSize: 12, padding: '0 2px' }}
        >{collapsed ? '▼' : '▲'}</button>
      </div>

      {/* Zweite Zeile: worum es geht, und ein Bild dazu.
          Aus dem Memberspot-Vergleich (docs/akademie-vorbild-memberspot.md) —
          dort traegt jedes Modul beides, und genau deshalb ist die Modulliste
          dort lesbar, waehrend unsere eine Aufzaehlung von Ueberschriften war. */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 8,
        padding: '0 12px 8px 30px', background: 'var(--bg-app)',
        borderBottom: collapsed ? 'none' : '1px solid var(--border-light)',
      }}>
        {mod.thumbnail_url ? (
          <img
            src={mod.thumbnail_url}
            alt=""
            style={{
              width: 44, height: 28, objectFit: 'cover', flexShrink: 0,
              borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-light)',
            }}
            onError={e => { e.target.style.display = 'none'; }}
          />
        ) : null}

        <BlurFeld
          wert={mod.description}
          platzhalter="Worum geht es in diesem Modul?"
          onSpeichern={wert => onUpdateFeld(mod.id, 'description', wert)}
          stil={{ flex: 1 }}
        />

        <BlurFeld
          wert={mod.thumbnail_url}
          platzhalter="Bildadresse"
          onSpeichern={wert => onUpdateFeld(mod.id, 'thumbnail_url', wert)}
          stil={{ width: 150, fontSize: 12 }}
        />
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
              onEdit={() => navigate(`/app/academy/admin/lesson/${lesson.id}`)}
              onDelete={() => deleteLesson(lesson.id)}
            />
          ))}
          <button
            onClick={addLesson}
            disabled={addingLesson}
            style={{
              alignSelf: 'flex-start', padding: '5px 12px',
              background: 'transparent', color: 'var(--brand-primary-mid)',
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

export function PreviewCard({ form }) {
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
          background: 'var(--brand-primary)', color: 'var(--text-on-brand)',
          borderRadius: 'var(--radius-full)', fontSize: 12, fontWeight: 600, padding: '2px 9px',
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
            <span style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>Noch nicht gestartet</span>
            <span style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>0%</span>
          </div>
          <div style={{ height: 5, background: 'var(--brand-primary-light)', borderRadius: 3 }}>
            <div style={{ width: '0%', height: '100%', background: 'var(--brand-primary)', borderRadius: 3 }} />
          </div>
        </div>
        <div style={{
          marginTop: 2, padding: '8px 14px', background: 'var(--brand-primary)', color: 'var(--text-on-brand)',
          border: 'none', borderRadius: 'var(--radius-md)', fontSize: 12, fontWeight: 600,
          textAlign: 'center',
        }}>Starten →</div>
      </div>
    </div>
  );
}

// ── Main component ─────────────────────────────────────────────


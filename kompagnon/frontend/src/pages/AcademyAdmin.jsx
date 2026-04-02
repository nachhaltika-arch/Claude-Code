import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import API_BASE_URL from '../config';

const AUDIENCE_LABEL = {
  employee: 'Intern',
  customer: 'Kunden',
  both:     'Alle',
};

export default function AcademyAdmin() {
  const navigate = useNavigate();
  const { token, user } = useAuth();
  const h = { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) };

  const [courses, setCourses] = useState([]);
  const [loading, setLoading]   = useState(true);
  const [deleteId, setDeleteId] = useState(null);

  // Drag-and-drop state
  const dragIdx  = useRef(null);
  const overIdx  = useRef(null);
  const [dragging, setDragging] = useState(false);

  useEffect(() => { loadCourses(); }, []); // eslint-disable-line

  const loadCourses = async () => {
    setLoading(true);
    try {
      const res  = await fetch(`${API_BASE_URL}/api/academy/courses`, { headers: h });
      const data = await res.json();
      setCourses(Array.isArray(data) ? data : []);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  };

  const deleteCourse = async (id) => {
    try {
      await fetch(`${API_BASE_URL}/api/academy/courses/${id}`, { method: 'DELETE', headers: h });
      setCourses(prev => prev.filter(c => c.id !== id));
      setDeleteId(null);
    } catch (e) { console.error(e); }
  };

  // ── Drag handlers ──────────────────────────────────────────────

  const onDragStart = (idx) => {
    dragIdx.current = idx;
    setDragging(true);
  };

  const onDragEnter = (idx) => {
    overIdx.current = idx;
  };

  const onDragEnd = async () => {
    setDragging(false);
    const from = dragIdx.current;
    const to   = overIdx.current;
    dragIdx.current = null;
    overIdx.current = null;
    if (from === null || to === null || from === to) return;

    const reordered = [...courses];
    const [moved]   = reordered.splice(from, 1);
    reordered.splice(to, 0, moved);
    setCourses(reordered);

    try {
      await fetch(`${API_BASE_URL}/api/academy/courses/reorder`, {
        method: 'PUT', headers: h,
        body: JSON.stringify({ order: reordered.map((c, i) => ({ id: c.id, sort_order: i })) }),
      });
    } catch (e) { console.error(e); }
  };

  if (user?.role !== 'admin') {
    return (
      <div style={{ textAlign: 'center', padding: 60, color: 'var(--text-tertiary)' }}>
        <div style={{ fontSize: 48, marginBottom: 12 }}>🔒</div>
        <div style={{ fontSize: 14 }}>Nur für Administratoren</div>
      </div>
    );
  }

  const deletingCourse = courses.find(c => c.id === deleteId);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20, width: '100%' }}>

      {/* ── Topbar ─────────────────────────────────────────────── */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        flexWrap: 'wrap', gap: 12,
        paddingBottom: 20, borderBottom: '1px solid var(--border-light)',
      }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 700, color: 'var(--text-primary)', margin: '0 0 2px' }}>
            Kursverwaltung
          </h1>
          <p style={{ fontSize: 12, color: 'var(--text-tertiary)', margin: 0 }}>
            {courses.length} {courses.length === 1 ? 'Kurs' : 'Kurse'} · Reihenfolge per Drag & Drop ändern
          </p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button
            onClick={() => navigate('/app/akademie')}
            style={{
              padding: '7px 14px', background: 'transparent', color: 'var(--text-secondary)',
              border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)',
              fontSize: 12, cursor: 'pointer', fontFamily: 'var(--font-sans)',
            }}
          >← Zurück</button>
          <button
            onClick={() => navigate('/app/akademie/admin/course/new')}
            style={{
              padding: '7px 16px', background: 'var(--brand-primary)', color: 'white',
              border: 'none', borderRadius: 'var(--radius-md)',
              fontSize: 12, fontWeight: 600, cursor: 'pointer', fontFamily: 'var(--font-sans)',
            }}
          >+ Neuer Kurs</button>
        </div>
      </div>

      {/* ── Course list ─────────────────────────────────────────── */}
      {loading ? (
        <div style={{ display: 'flex', justifyContent: 'center', padding: '80px 0' }}>
          <div style={{ width: 28, height: 28, borderRadius: '50%', border: '3px solid var(--border-light)', borderTopColor: 'var(--brand-primary)', animation: 'spin 0.8s linear infinite' }} />
        </div>

      ) : courses.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '80px 20px', color: 'var(--text-tertiary)' }}>
          <div style={{ fontSize: 44, marginBottom: 12, opacity: 0.25 }}>🎓</div>
          <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 6 }}>Noch keine Kurse</div>
          <div style={{ fontSize: 12 }}>Klicke auf „+ Neuer Kurs" um loszulegen.</div>
        </div>

      ) : (
        <div style={{
          background: 'var(--bg-surface)', border: '1px solid var(--border-light)',
          borderRadius: 'var(--radius-lg)', overflow: 'hidden',
        }}>
          {/* Column header */}
          <div style={{
            display: 'grid', gridTemplateColumns: '28px 44px 1fr auto',
            gap: 12, padding: '8px 16px',
            background: 'var(--bg-app)', borderBottom: '1px solid var(--border-light)',
            fontSize: 10, fontWeight: 600, color: 'var(--text-tertiary)',
            textTransform: 'uppercase', letterSpacing: '0.06em',
          }}>
            <span />
            <span />
            <span>Kurs</span>
            <span>Aktionen</span>
          </div>

          {courses.map((course, idx) => {
            const aud        = course.target_audience || course.audience;
            const published  = course.is_published !== false; // default true if field absent
            const moduleCount = course.module_count  ?? course.modules?.length  ?? null;
            const lessonCount = course.lesson_count  ?? course.lessons?.length  ?? null;

            return (
              <div
                key={course.id}
                draggable
                onDragStart={() => onDragStart(idx)}
                onDragEnter={() => onDragEnter(idx)}
                onDragOver={e => e.preventDefault()}
                onDragEnd={onDragEnd}
                style={{
                  display: 'grid', gridTemplateColumns: '28px 44px 1fr auto',
                  gap: 12, padding: '12px 16px', alignItems: 'center',
                  borderBottom: idx < courses.length - 1 ? '1px solid var(--border-light)' : 'none',
                  background: dragging && overIdx.current === idx ? 'var(--bg-active)' : 'transparent',
                  transition: 'background 0.1s',
                  cursor: 'default',
                }}
                onMouseEnter={e => { if (e.currentTarget.style.background === 'transparent') e.currentTarget.style.background = 'var(--bg-hover)'; }}
                onMouseLeave={e => e.currentTarget.style.background = dragging && overIdx.current === idx ? 'var(--bg-active)' : 'transparent'}
              >
                {/* Drag handle */}
                <span style={{
                  fontSize: 16, color: 'var(--text-tertiary)', cursor: 'grab',
                  userSelect: 'none', lineHeight: 1, opacity: 0.5,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                }}>⠿</span>

                {/* Thumbnail */}
                <div style={{
                  width: 40, height: 40, borderRadius: 'var(--radius-md)', flexShrink: 0,
                  background: course.thumbnail_url
                    ? `url(${course.thumbnail_url}) center/cover`
                    : 'linear-gradient(135deg, var(--brand-primary) 0%, var(--brand-primary-deeper) 100%)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 18,
                }}>
                  {!course.thumbnail_url && '🎓'}
                </div>

                {/* Course info */}
                <div style={{ minWidth: 0 }}>
                  <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 4, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {course.title}
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>

                    {/* Status dot */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                      <div style={{
                        width: 7, height: 7, borderRadius: '50%',
                        background: published ? 'var(--status-success-text)' : 'var(--status-warning-text)',
                        flexShrink: 0,
                      }} />
                      <span style={{ fontSize: 11, color: published ? 'var(--status-success-text)' : 'var(--status-warning-text)', fontWeight: 500 }}>
                        {published ? 'Veröffentlicht' : 'Entwurf'}
                      </span>
                    </div>

                    {/* Module / lesson count */}
                    {(moduleCount !== null || lessonCount !== null) && (
                      <span style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>
                        {moduleCount !== null && `${moduleCount} ${moduleCount === 1 ? 'Modul' : 'Module'}`}
                        {moduleCount !== null && lessonCount !== null && ' · '}
                        {lessonCount !== null && `${lessonCount} ${lessonCount === 1 ? 'Lektion' : 'Lektionen'}`}
                      </span>
                    )}

                    {/* Audience badge */}
                    {aud && (
                      <span style={{
                        fontSize: 10, fontWeight: 600, padding: '2px 8px',
                        borderRadius: 'var(--radius-full)',
                        background: 'var(--brand-primary-light)', color: 'var(--brand-primary)',
                        letterSpacing: '0.02em',
                      }}>
                        {AUDIENCE_LABEL[aud] || aud}
                      </span>
                    )}
                  </div>
                </div>

                {/* Actions */}
                <div style={{ display: 'flex', gap: 6, flexShrink: 0 }}>
                  <button
                    onClick={() => navigate(`/app/akademie/admin/course/${course.id}`)}
                    style={{
                      padding: '5px 10px', background: 'var(--bg-app)', color: 'var(--text-secondary)',
                      border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)',
                      fontSize: 12, cursor: 'pointer', fontFamily: 'var(--font-sans)',
                      display: 'flex', alignItems: 'center', gap: 4,
                      transition: 'background 0.1s, color 0.1s',
                    }}
                    onMouseEnter={e => { e.currentTarget.style.background = 'var(--bg-hover)'; e.currentTarget.style.color = 'var(--text-primary)'; }}
                    onMouseLeave={e => { e.currentTarget.style.background = 'var(--bg-app)'; e.currentTarget.style.color = 'var(--text-secondary)'; }}
                  >
                    ✏️ Bearbeiten
                  </button>
                  <button
                    onClick={() => setDeleteId(course.id)}
                    style={{
                      padding: '5px 10px',
                      background: 'var(--status-danger-bg)', color: 'var(--status-danger-text)',
                      border: '1px solid transparent', borderRadius: 'var(--radius-md)',
                      fontSize: 12, cursor: 'pointer', fontFamily: 'var(--font-sans)',
                      transition: 'opacity 0.15s',
                    }}
                    onMouseEnter={e => e.currentTarget.style.opacity = '0.75'}
                    onMouseLeave={e => e.currentTarget.style.opacity = '1'}
                  >
                    Löschen
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* ── Delete confirm modal ────────────────────────────────── */}
      {deleteId && (
        <>
          <div
            style={{ position: 'fixed', inset: 0, background: 'rgba(15,28,32,0.5)', backdropFilter: 'blur(4px)', zIndex: 1000 }}
            onClick={() => setDeleteId(null)}
          />
          <div
            onClick={e => e.stopPropagation()}
            style={{
              position: 'fixed', top: '50%', left: '50%', transform: 'translate(-50%,-50%)',
              background: 'var(--bg-surface)', borderRadius: 'var(--radius-xl)',
              padding: '28px 32px', maxWidth: 380, width: '90vw',
              textAlign: 'center', boxShadow: 'var(--shadow-elevated)', zIndex: 1001,
            }}
          >
            <div style={{
              width: 48, height: 48, borderRadius: '50%',
              background: 'var(--status-danger-bg)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 22, margin: '0 auto 14px',
            }}>🗑️</div>
            <h3 style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)', margin: '0 0 8px' }}>
              Kurs löschen?
            </h3>
            <p style={{ fontSize: 13, color: 'var(--text-secondary)', margin: '0 0 20px', lineHeight: 1.55 }}>
              <strong>{deletingCourse?.title}</strong> wird dauerhaft gelöscht.<br />
              Diese Aktion kann nicht rückgängig gemacht werden.
            </p>
            <div style={{ display: 'flex', gap: 10 }}>
              <button
                onClick={() => setDeleteId(null)}
                style={{
                  flex: 1, padding: '9px 0',
                  background: 'var(--bg-app)', color: 'var(--text-primary)',
                  border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)',
                  fontSize: 13, cursor: 'pointer', fontFamily: 'var(--font-sans)',
                }}
              >Abbrechen</button>
              <button
                onClick={() => deleteCourse(deleteId)}
                style={{
                  flex: 1, padding: '9px 0',
                  background: 'var(--status-danger-bg)', color: 'var(--status-danger-text)',
                  border: 'none', borderRadius: 'var(--radius-md)',
                  fontSize: 13, fontWeight: 700, cursor: 'pointer', fontFamily: 'var(--font-sans)',
                }}
              >Löschen</button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import API_BASE_URL from '../config';

export default function AcademyLesson() {
  const { lessonId } = useParams();
  const { token, user } = useAuth();
  const h = { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) };

  const [lesson, setLesson] = useState(null);
  const [module, setModule] = useState(null);
  const [course, setCourse] = useState(null);
  const [allLessons, setAllLessons] = useState([]);
  const [completed, setCompleted] = useState(false);
  const [completing, setCompleting] = useState(false);
  const [checked, setChecked] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    setChecked({});
    fetch(`${API_BASE_URL}/api/academy/lessons/${lessonId}`, { headers: h })
      .then(r => r.json())
      .then(async lessonData => {
        setLesson(lessonData);

        const modData = await fetch(`${API_BASE_URL}/api/academy/modules/${lessonData.module_id}`, { headers: h }).then(r => r.json());
        setModule(modData);

        const [courseData, modulesData] = await Promise.all([
          fetch(`${API_BASE_URL}/api/academy/courses/${modData.course_id}`, { headers: h }).then(r => r.json()),
          fetch(`${API_BASE_URL}/api/academy/courses/${modData.course_id}/modules`, { headers: h }).then(r => r.json()),
        ]);
        setCourse(courseData);

        const lessonArrays = await Promise.all(
          (Array.isArray(modulesData) ? modulesData : []).map(m =>
            fetch(`${API_BASE_URL}/api/academy/modules/${m.id}/lessons`, { headers: h })
              .then(r => r.json())
              .then(ls => Array.isArray(ls) ? ls : [])
          )
        );
        setAllLessons(lessonArrays.flat());

        if (user?.id) {
          const progData = await fetch(
            `${API_BASE_URL}/api/academy/courses/${modData.course_id}/progress?user_id=${user.id}`,
            { headers: h }
          ).then(r => r.json());
          const lessonProg = (progData.lessons || []).find(p => p.lesson_id === parseInt(lessonId));
          setCompleted(lessonProg?.completed || false);
        }
      })
      .catch(e => console.error(e))
      .finally(() => setLoading(false));
  }, [lessonId]); // eslint-disable-line

  const handleComplete = async () => {
    if (!user?.id || completing) return;
    setCompleting(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/academy/lessons/${lessonId}/complete`, {
        method: 'POST', headers: h,
        body: JSON.stringify({ user_id: user.id }),
      });
      const data = await res.json();
      setCompleted(data.completed);
    } catch (e) { console.error(e); }
    finally { setCompleting(false); }
  };

  if (loading) return (
    <div className="d-flex justify-content-center align-items-center" style={{ height: '40vh' }}>
      <div className="spinner-border" role="status"><span className="visually-hidden">Laden...</span></div>
    </div>
  );

  if (!lesson) return (
    <div className="text-center py-5">
      <div style={{ fontSize: 48, opacity: 0.4 }}>📖</div>
      <h2 className="mt-3 h5">Lektion nicht gefunden</h2>
      <Link to="/app/akademie" className="btn btn-primary mt-3">← Zur Akademie</Link>
    </div>
  );

  const currentIdx = allLessons.findIndex(l => l.id === parseInt(lessonId));
  const prevLesson = currentIdx > 0 ? allLessons[currentIdx - 1] : null;
  const nextLesson = currentIdx < allLessons.length - 1 ? allLessons[currentIdx + 1] : null;
  const checklistItems = lesson.checklist_items || [];
  const checkedCount = Object.values(checked).filter(Boolean).length;

  return (
    <div style={{ maxWidth: 860, margin: '0 auto' }}>
      {/* Breadcrumb */}
      <nav aria-label="breadcrumb" className="mb-3">
        <ol className="breadcrumb">
          <li className="breadcrumb-item"><Link to="/app/akademie">Akademie</Link></li>
          {course && (
            <li className="breadcrumb-item">
              <Link to={`/app/akademie/kurs/${course.id}`}>{course.title}</Link>
            </li>
          )}
          {module && <li className="breadcrumb-item text-muted">{module.title}</li>}
          <li className="breadcrumb-item active" aria-current="page">{lesson.title}</li>
        </ol>
      </nav>

      <h2 className="mb-4" style={{ fontSize: 22, fontWeight: 700, color: 'var(--text-primary)' }}>{lesson.title}</h2>

      {/* Video */}
      {lesson.video_url && (
        <div className="ratio ratio-16x9 mb-4 rounded overflow-hidden shadow-sm">
          <iframe
            src={lesson.video_url}
            title={lesson.title}
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowFullScreen
          />
        </div>
      )}

      {/* Text content */}
      {lesson.content_text && (
        <div
          className="mb-4 p-4 rounded border"
          style={{ background: 'var(--bg-surface)', fontSize: 14, color: 'var(--text-primary)', lineHeight: 1.8 }}
          dangerouslySetInnerHTML={{ __html: lesson.content_text }}
        />
      )}

      {/* Checklist */}
      {checklistItems.length > 0 && (
        <div className="card mb-4" style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)' }}>
          <div className="card-header d-flex justify-content-between align-items-center"
            style={{ background: 'var(--bg-surface)', borderBottom: '1px solid var(--border-light)' }}>
            <span className="fw-semibold" style={{ color: 'var(--text-primary)' }}>
              <i className="fa-solid fa-list-check me-2" />Checkliste
            </span>
            <small className="text-muted">{checkedCount}/{checklistItems.length}</small>
          </div>
          <div className="progress" style={{ height: 4, borderRadius: 0 }}>
            <div
              className="progress-bar bg-success"
              style={{ width: checklistItems.length ? `${(checkedCount / checklistItems.length) * 100}%` : '0%' }}
            />
          </div>
          <ul className="list-group list-group-flush">
            {checklistItems.map((item, i) => {
              const isDone = checked[i];
              const label = typeof item === 'string' ? item : item.label;
              return (
                <li key={i} className="list-group-item" style={{ background: isDone ? 'var(--status-success-bg, #f0fdf4)' : 'var(--bg-surface)' }}>
                  <label className="d-flex align-items-center gap-3 mb-0" style={{ cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      className="form-check-input mt-0"
                      checked={!!isDone}
                      onChange={() => setChecked(prev => ({ ...prev, [i]: !prev[i] }))}
                    />
                    <span style={{ fontSize: 14, textDecoration: isDone ? 'line-through' : 'none', color: isDone ? 'var(--text-tertiary)' : 'var(--text-primary)' }}>
                      {label}
                    </span>
                  </label>
                </li>
              );
            })}
          </ul>
        </div>
      )}

      {/* Download */}
      {lesson.file_url && (
        <div className="mb-4">
          <a href={lesson.file_url} className="btn btn-outline-secondary" target="_blank" rel="noreferrer">
            <i className="fa-solid fa-download me-2" />Datei herunterladen
          </a>
        </div>
      )}

      {/* Complete button */}
      <div className="mb-4">
        <button
          className={`btn ${completed ? 'btn-success' : 'btn-outline-success'}`}
          onClick={handleComplete}
          disabled={completing || !user}
        >
          {completing ? (
            <><span className="spinner-border spinner-border-sm me-2" />Wird gespeichert...</>
          ) : completed ? (
            <><i className="fa-solid fa-circle-check me-2" />Abgeschlossen</>
          ) : (
            <><i className="fa-regular fa-circle me-2" />Lektion abschließen</>
          )}
        </button>
      </div>

      {/* Prev / Next navigation */}
      <div className="d-flex justify-content-between align-items-center border-top pt-3">
        <div>
          {prevLesson && (
            <Link to={`/app/akademie/lektion/${prevLesson.id}`} className="btn btn-outline-secondary btn-sm">
              <i className="fa-solid fa-chevron-left me-1" />Vorherige Lektion
            </Link>
          )}
        </div>
        {course && (
          <Link to={`/app/akademie/kurs/${course.id}`} className="btn btn-link btn-sm text-muted text-decoration-none">
            Zur Kursübersicht
          </Link>
        )}
        <div>
          {nextLesson && (
            <Link to={`/app/akademie/lektion/${nextLesson.id}`} className="btn btn-outline-primary btn-sm">
              Nächste Lektion<i className="fa-solid fa-chevron-right ms-1" />
            </Link>
          )}
        </div>
      </div>
    </div>
  );
}

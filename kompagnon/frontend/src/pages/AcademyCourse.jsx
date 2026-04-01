import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Badge from '../components/ui/Badge';
import API_BASE_URL from '../config';

const BADGE_MAP = {
  primary: 'info', warning: 'warning', success: 'success', danger: 'danger', info: 'info', secondary: 'neutral',
};

function getLessonIcon(lesson) {
  if (lesson.video_url) return 'fa-video';
  if (lesson.file_url) return 'fa-download';
  if (lesson.content_text) return 'fa-file-lines';
  return 'fa-question';
}

export default function AcademyCourse() {
  const { kursId } = useParams();
  const { token, user } = useAuth();
  const h = { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) };

  const [course, setCourse] = useState(null);
  const [modules, setModules] = useState([]);
  const [lessonsByModule, setLessonsByModule] = useState({});
  const [progress, setProgress] = useState({ total_lessons: 0, completed: 0, progress_pct: 0, lessons: [] });
  const [loading, setLoading] = useState(true);
  const [openModuleId, setOpenModuleId] = useState(null);

  useEffect(() => {
    const uid = user?.id;
    Promise.all([
      fetch(`${API_BASE_URL}/api/academy/courses/${kursId}`, { headers: h }).then(r => r.json()),
      fetch(`${API_BASE_URL}/api/academy/courses/${kursId}/modules`, { headers: h }).then(r => r.json()),
      uid
        ? fetch(`${API_BASE_URL}/api/academy/courses/${kursId}/progress?user_id=${uid}`, { headers: h }).then(r => r.json())
        : Promise.resolve({ total_lessons: 0, completed: 0, progress_pct: 0, lessons: [] }),
    ]).then(async ([courseData, modulesData, progressData]) => {
      setCourse(courseData);
      const mods = Array.isArray(modulesData) ? modulesData : [];
      setModules(mods);
      setProgress(progressData || { total_lessons: 0, completed: 0, progress_pct: 0, lessons: [] });
      if (mods.length > 0) setOpenModuleId(mods[0].id);

      const lessonResults = await Promise.all(
        mods.map(m =>
          fetch(`${API_BASE_URL}/api/academy/modules/${m.id}/lessons`, { headers: h })
            .then(r => r.json())
            .then(ls => [m.id, Array.isArray(ls) ? ls : []])
        )
      );
      const byModule = {};
      lessonResults.forEach(([mid, ls]) => { byModule[mid] = ls; });
      setLessonsByModule(byModule);
    }).catch(() => {}).finally(() => setLoading(false));
  }, [kursId]); // eslint-disable-line

  if (loading) return (
    <div className="d-flex justify-content-center align-items-center" style={{ height: '40vh' }}>
      <div className="spinner-border" role="status"><span className="visually-hidden">Laden...</span></div>
    </div>
  );

  if (!course) return (
    <div className="text-center py-5">
      <div style={{ fontSize: 48, opacity: 0.4 }}>📚</div>
      <h2 className="mt-3 h5">Kurs nicht gefunden</h2>
      <Link to="/app/akademie" className="btn btn-primary mt-3">← Zurück zur Akademie</Link>
    </div>
  );

  const progressMap = {};
  (progress.lessons || []).forEach(p => { progressMap[p.lesson_id] = p; });

  // Build flat ordered lesson list for linear locking across modules
  const allLessons = modules.flatMap(m => lessonsByModule[m.id] || []);
  const unlockedIds = new Set();
  if (course.linear_progress) {
    for (let i = 0; i < allLessons.length; i++) {
      unlockedIds.add(allLessons[i].id);
      if (!progressMap[allLessons[i].id]?.completed) break;
    }
  } else {
    allLessons.forEach(l => unlockedIds.add(l.id));
  }

  return (
    <div style={{ maxWidth: 900, margin: '0 auto' }}>
      {/* Breadcrumb */}
      <nav aria-label="breadcrumb" className="mb-3">
        <ol className="breadcrumb">
          <li className="breadcrumb-item"><Link to="/app/akademie">Akademie</Link></li>
          <li className="breadcrumb-item active" aria-current="page">{course.title}</li>
        </ol>
      </nav>

      {/* Header */}
      <div className="mb-4">
        <div className="d-flex align-items-center gap-2 mb-2 flex-wrap">
          <h2 className="mb-0" style={{ fontSize: 20, fontWeight: 700, color: 'var(--text-primary)' }}>{course.title}</h2>
          <Badge variant={BADGE_MAP[course.category_color] || 'neutral'}>{course.category}</Badge>
          {course.linear_progress && (
            <span className="badge bg-warning text-dark">
              <i className="fa-solid fa-list-ol me-1" />Lineare Freischaltung
            </span>
          )}
        </div>
        <p style={{ fontSize: 13, color: 'var(--text-secondary)', margin: '0 0 16px' }}>{course.description}</p>

        {/* Overall progress bar */}
        <div className="d-flex justify-content-between mb-1">
          <small className="text-muted">Gesamtfortschritt</small>
          <small className="text-muted">{progress.completed} von {progress.total_lessons} Lektionen</small>
        </div>
        <div className="progress" style={{ height: 10 }}>
          <div
            className="progress-bar bg-success"
            role="progressbar"
            style={{ width: `${progress.progress_pct}%` }}
            aria-valuenow={progress.progress_pct}
            aria-valuemin={0}
            aria-valuemax={100}
          />
        </div>
      </div>

      {/* Modules accordion */}
      {modules.length === 0 ? (
        <div className="text-center py-5 text-muted">
          <i className="fa-solid fa-book-open fa-2x mb-3 d-block opacity-25" />
          <p>Dieser Kurs hat noch keine Module.</p>
        </div>
      ) : (
        <div className="accordion">
          {modules.map(mod => {
            const lessons = lessonsByModule[mod.id] || [];
            const modCompleted = lessons.filter(l => progressMap[l.id]?.completed).length;
            const isOpen = openModuleId === mod.id;

            return (
              <div className="accordion-item" key={mod.id}>
                <h2 className="accordion-header">
                  <button
                    className={`accordion-button${isOpen ? '' : ' collapsed'}`}
                    type="button"
                    onClick={() => setOpenModuleId(isOpen ? null : mod.id)}
                    style={{ background: 'var(--bg-surface)', color: 'var(--text-primary)' }}
                  >
                    <span className="me-auto fw-semibold">{mod.title}</span>
                    <div className="d-flex align-items-center gap-2 me-3">
                      <small className="text-muted">{modCompleted}/{lessons.length}</small>
                      <div className="progress" style={{ width: 80, height: 6 }}>
                        <div
                          className="progress-bar bg-success"
                          style={{ width: lessons.length ? `${(modCompleted / lessons.length) * 100}%` : '0%' }}
                        />
                      </div>
                    </div>
                  </button>
                </h2>
                <div className={`accordion-collapse collapse${isOpen ? ' show' : ''}`}>
                  <div className="accordion-body p-0">
                    {lessons.length === 0 ? (
                      <p className="text-center text-muted py-3 mb-0 small">Keine Lektionen</p>
                    ) : (
                      <ul className="list-group list-group-flush">
                        {lessons.map(lesson => {
                          const done = progressMap[lesson.id]?.completed;
                          const locked = !unlockedIds.has(lesson.id);
                          const icon = getLessonIcon(lesson);

                          return (
                            <li
                              key={lesson.id}
                              className={`list-group-item d-flex align-items-center gap-3 py-3${locked ? ' opacity-50' : ''}`}
                              style={{ background: 'var(--bg-surface)' }}
                            >
                              {locked
                                ? <i className="fa-solid fa-lock text-secondary" style={{ width: 16 }} />
                                : done
                                  ? <i className="fa-solid fa-circle-check text-success" style={{ width: 16 }} />
                                  : <i className="fa-regular fa-circle text-muted" style={{ width: 16 }} />
                              }
                              <i className={`fa-solid ${icon} text-muted`} style={{ fontSize: 13, width: 16 }} />
                              {locked ? (
                                <span style={{ fontSize: 14, color: 'var(--text-muted)' }}>{lesson.title}</span>
                              ) : (
                                <Link
                                  to={`/app/akademie/lektion/${lesson.id}`}
                                  className="text-decoration-none flex-grow-1"
                                  style={{ fontSize: 14, color: 'var(--text-primary)' }}
                                >
                                  {lesson.title}
                                </Link>
                              )}
                            </li>
                          );
                        })}
                      </ul>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      <div className="mt-4">
        <Link to="/app/akademie" className="btn btn-outline-secondary btn-sm">← Zurück zur Übersicht</Link>
      </div>
    </div>
  );
}

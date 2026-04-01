import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import API_BASE_URL from '../config';

const TYPE_ICON  = { video: '🎬', text: '📄', quiz: '❓', checklist: '✅' };
const TYPE_LABEL = { video: 'Video', text: 'Text', quiz: 'Quiz', checklist: 'Checkliste' };

export default function AcademyCourse() {
  const { id, kursId } = useParams();
  // Unterstütze beide Routen: /academy/:id und /akademie/kurs/:kursId
  // eslint-disable-next-line no-unused-vars
  const courseId = id || kursId;
  const navigate = useNavigate();
  const { user, token } = useAuth();
  const h = useCallback(
    () => ({ 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) }),
    [token],
  );

  const [course, setCourse] = useState(null);
  const [modules, setModules] = useState([]);
  const [progressMap, setProgressMap] = useState({});     // lesson_id → {completed, score}
  const [activeLessonId, setActiveLessonId] = useState(null);
  const [activeLesson, setActiveLesson] = useState(null);
  const [loading, setLoading] = useState(true);
  const [completing, setCompleting] = useState(false);
  const [openModules, setOpenModules] = useState({});
  const [sidebarOpen, setSidebarOpen] = useState(false);  // mobile drawer

  // Quiz state
  const [quizQuestions, setQuizQuestions] = useState([]);
  const [quizAnswers, setQuizAnswers] = useState({});
  const [quizResult, setQuizResult] = useState(null);
  const [quizLoading, setQuizLoading] = useState(false);

  // ── Load course + progress ──────────────────────────────
  useEffect(() => {
    setLoading(true);
    Promise.all([
      fetch(`${API_BASE_URL}/api/academy/courses/${courseId}`, { headers: h() }).then(r => r.json()),
      fetch(`${API_BASE_URL}/api/academy/courses/${courseId}/progress`, { headers: h() }).then(r => r.json()),
    ]).then(([courseData, progressData]) => {
      setCourse(courseData);
      const mods = courseData.modules || [];
      setModules(mods);
      const pMap = {};
      (progressData.lessons || []).forEach(l => { pMap[l.lesson_id] = l; });
      setProgressMap(pMap);
      if (mods.length > 0) {
        setOpenModules({ [mods[0].id]: true });
        const first = mods[0].lessons?.[0];
        if (first) setActiveLessonId(first.id);
      }
    }).catch(console.error).finally(() => setLoading(false));
  }, [id]); // eslint-disable-line

  // ── Load lesson detail ──────────────────────────────────
  useEffect(() => {
    if (!activeLessonId) return;
    fetch(`${API_BASE_URL}/api/academy/lessons/${activeLessonId}`, { headers: h() })
      .then(r => r.json())
      .then(data => {
        setActiveLesson(data);
        setQuizQuestions([]);
        setQuizAnswers({});
        setQuizResult(null);
        if (data.type === 'quiz') {
          fetch(`${API_BASE_URL}/api/academy/lessons/${activeLessonId}/quiz`, { headers: h() })
            .then(r => r.json()).then(setQuizQuestions).catch(console.error);
        }
      }).catch(console.error);
  }, [activeLessonId]); // eslint-disable-line

  // ── Derived values ──────────────────────────────────────
  const allLessons = modules.flatMap(m => m.lessons || []);
  const currentIdx = allLessons.findIndex(l => l.id === activeLessonId);
  const prevLesson = currentIdx > 0 ? allLessons[currentIdx - 1] : null;
  const nextLesson = currentIdx < allLessons.length - 1 ? allLessons[currentIdx + 1] : null;
  const completedCount = allLessons.filter(l => progressMap[l.id]?.completed).length;
  const overallPct = allLessons.length > 0 ? Math.round((completedCount / allLessons.length) * 100) : 0;
  const isDone = id => Boolean(progressMap[id]?.completed);

  const isLocked = (lessonId) => {
    if (!course?.linear_progress) return false;
    const idx = allLessons.findIndex(l => l.id === lessonId);
    for (let i = 0; i < idx; i++) {
      if (!isDone(allLessons[i].id)) return true;
    }
    return false;
  };

  // ── Actions ─────────────────────────────────────────────
  const selectLesson = (lesson) => {
    if (isLocked(lesson.id)) return;
    setActiveLessonId(lesson.id);
    setSidebarOpen(false);
  };

  const handleComplete = async () => {
    if (!activeLessonId || completing) return;
    setCompleting(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/academy/lessons/${activeLessonId}/complete`, {
        method: 'POST', headers: h(), body: JSON.stringify({}),
      });
      const data = await res.json();
      setProgressMap(p => ({ ...p, [activeLessonId]: { ...p[activeLessonId], completed: data.completed } }));
      if (data.completed && nextLesson) setTimeout(() => setActiveLessonId(nextLesson.id), 350);
    } catch (e) { console.error(e); }
    setCompleting(false);
  };

  const handleSubmitQuiz = async () => {
    setQuizLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/academy/lessons/${activeLessonId}/quiz`, {
        method: 'POST', headers: h(), body: JSON.stringify({ answers: quizAnswers }),
      });
      const data = await res.json();
      setQuizResult(data);
      if (data.passed) {
        setProgressMap(p => ({ ...p, [activeLessonId]: { ...p[activeLessonId], completed: true, score: data.score } }));
      }
    } catch (e) { console.error(e); }
    setQuizLoading(false);
  };

  // ── Certificate ─────────────────────────────────────────
  const handleCertificate = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/academy/courses/${courseId}/certificate`, {
        method: 'POST', headers: h(),
      });
      const data = await res.json();
      if (data.certificate_code) navigate(`/academy/certificate/${data.certificate_code}`);
    } catch (e) { console.error(e); }
  };

  // ── Render ───────────────────────────────────────────────
  if (loading) return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '60vh' }}>
      <div style={{ width: 32, height: 32, borderRadius: '50%', border: '3px solid var(--border-light)', borderTopColor: 'var(--brand-primary)', animation: 'spin 0.8s linear infinite' }} />
    </div>
  );
  if (!course) return (
    <div style={{ textAlign: 'center', padding: 60, color: 'var(--text-tertiary)' }}>Kurs nicht gefunden.</div>
  );

  const isActive = (lid) => lid === activeLessonId;

  return (
    <>
      {/* Mobile: sidebar drawer overlay */}
      {sidebarOpen && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.45)', zIndex: 40 }}
          onClick={() => setSidebarOpen(false)} />
      )}

      {/* Mobile: top bar */}
      <div style={{ display: 'none', marginBottom: 12, '@media (max-width: 768px)': { display: 'flex' } }}>
        <button onClick={() => setSidebarOpen(true)} style={{
          padding: '8px 14px', background: 'var(--bg-surface)',
          border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)',
          fontSize: 12, cursor: 'pointer', fontFamily: 'var(--font-sans)',
        }}>☰ Kursinhalt</button>
      </div>

      <div style={{ display: 'flex', gap: 20, alignItems: 'flex-start' }}>

        {/* ── Sidebar ────────────────────────────────────── */}
        <aside style={{
          width: 280, flexShrink: 0,
          background: 'var(--bg-surface)', border: '1px solid var(--border-light)',
          borderRadius: 'var(--radius-lg)', display: 'flex', flexDirection: 'column',
          overflow: 'hidden', position: 'sticky', top: 16,
          // mobile: absolute panel
          ...(sidebarOpen ? {
            position: 'fixed', top: 0, left: 0, bottom: 0, zIndex: 50,
            width: 300, borderRadius: 0, overflowY: 'auto',
          } : {}),
        }}>
          {/* Course header */}
          <div style={{ padding: '14px 16px 12px', borderBottom: '1px solid var(--border-light)' }}>
            <button onClick={() => navigate('/app/akademie')} style={{
              background: 'none', border: 'none', color: 'var(--text-tertiary)',
              fontSize: 11, cursor: 'pointer', padding: 0, marginBottom: 10,
              fontFamily: 'var(--font-sans)',
            }}>← Zur Übersicht</button>
            <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1.4, marginBottom: 10 }}>
              {course.title}
            </div>
            {/* Overall progress bar */}
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
              <span style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>{completedCount} / {allLessons.length}</span>
              <span style={{ fontSize: 10, fontWeight: 700, color: overallPct === 100 ? '#16a34a' : 'var(--brand-primary)' }}>{overallPct}%</span>
            </div>
            <div style={{ height: 5, background: 'var(--border-light)', borderRadius: 3, overflow: 'hidden' }}>
              <div style={{ width: `${overallPct}%`, height: '100%', background: overallPct === 100 ? '#16a34a' : 'var(--brand-primary)', borderRadius: 3, transition: 'width 0.4s' }} />
            </div>
          </div>

          {/* Module accordion */}
          <div style={{ flex: 1, overflowY: 'auto', padding: 8 }}>
            {modules.map(mod => {
              const mLessons = mod.lessons || [];
              const mDone = mLessons.filter(l => isDone(l.id)).length;
              const open = openModules[mod.id];
              return (
                <div key={mod.id} style={{ marginBottom: 4 }}>
                  <button
                    onClick={() => setOpenModules(p => ({ ...p, [mod.id]: !p[mod.id] }))}
                    style={{
                      width: '100%', display: 'flex', alignItems: 'center',
                      justifyContent: 'space-between', padding: '9px 10px',
                      background: open ? 'var(--bg-app)' : 'transparent',
                      border: 'none', borderRadius: 'var(--radius-md)',
                      cursor: 'pointer', color: 'var(--text-primary)', textAlign: 'left',
                    }}
                  >
                    <span style={{ fontSize: 12, fontWeight: 600, flex: 1, lineHeight: 1.3 }}>{mod.title}</span>
                    <span style={{ fontSize: 10, color: 'var(--text-tertiary)', marginRight: 6, flexShrink: 0 }}>
                      {mDone}/{mLessons.length}
                    </span>
                    <span style={{ fontSize: 10, color: 'var(--text-tertiary)', transform: open ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s', flexShrink: 0 }}>▼</span>
                  </button>

                  {open && (
                    <div style={{ paddingLeft: 8 }}>
                      {mLessons.map(lesson => {
                        const active = isActive(lesson.id);
                        const done   = isDone(lesson.id);
                        const locked = isLocked(lesson.id);
                        return (
                          <button
                            key={lesson.id}
                            onClick={() => selectLesson(lesson)}
                            disabled={locked}
                            style={{
                              width: '100%', display: 'flex', alignItems: 'center',
                              gap: 8, padding: '7px 10px',
                              background: active ? 'var(--brand-primary)' : 'transparent',
                              border: 'none', borderRadius: 'var(--radius-md)',
                              cursor: locked ? 'not-allowed' : 'pointer',
                              color: active ? 'white' : locked ? 'var(--text-tertiary)' : 'var(--text-secondary)',
                              textAlign: 'left', opacity: locked ? 0.5 : 1,
                            }}
                          >
                            {/* Icon */}
                            <span style={{ fontSize: 13, flexShrink: 0, width: 16, textAlign: 'center' }}>
                              {locked ? '🔒' : done ? '✓' : active ? '▶' : '○'}
                            </span>
                            <span style={{ fontSize: 12, lineHeight: 1.3, flex: 1 }}>{lesson.title}</span>
                            <span style={{ fontSize: 11, flexShrink: 0, opacity: 0.65 }}>
                              {TYPE_ICON[lesson.type] || '📄'}
                            </span>
                          </button>
                        );
                      })}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </aside>

        {/* ── Main content ───────────────────────────────── */}
        <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', gap: 16 }}>

          {/* Mobile: open sidebar button */}
          <button onClick={() => setSidebarOpen(true)} style={{
            display: 'none', /* shown via @media in index.css if needed */
            padding: '8px 14px', background: 'var(--bg-surface)',
            border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)',
            fontSize: 12, cursor: 'pointer', fontFamily: 'var(--font-sans)',
            alignSelf: 'flex-start',
          }}>☰ Kursinhalt anzeigen</button>

          {activeLesson ? (
            <>
              {/* Lesson header */}
              <div style={{
                background: 'var(--bg-surface)', border: '1px solid var(--border-light)',
                borderRadius: 'var(--radius-lg)', padding: '20px 24px',
                display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 16,
              }}>
                <div>
                  <div style={{
                    display: 'inline-flex', alignItems: 'center', gap: 5,
                    background: 'var(--bg-app)', border: '1px solid var(--border-light)',
                    borderRadius: 'var(--radius-full)', padding: '3px 10px',
                    fontSize: 11, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 10,
                  }}>
                    {TYPE_ICON[activeLesson.type]} {TYPE_LABEL[activeLesson.type] || 'Lektion'}
                  </div>
                  <h2 style={{ fontSize: 20, fontWeight: 700, color: 'var(--text-primary)', margin: 0, letterSpacing: '-0.01em' }}>
                    {activeLesson.title}
                  </h2>
                  {activeLesson.duration_minutes > 0 && (
                    <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginTop: 6 }}>
                      ⏱ {activeLesson.duration_minutes} Min.
                    </div>
                  )}
                </div>
                {isDone(activeLessonId) && (
                  <div style={{ background: '#dcfce7', color: '#16a34a', borderRadius: 'var(--radius-full)', padding: '5px 12px', fontSize: 12, fontWeight: 700, flexShrink: 0 }}>
                    ✓ Erledigt
                  </div>
                )}
              </div>

              {/* Video player */}
              {activeLesson.type === 'video' && activeLesson.content_url && (
                <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', overflow: 'hidden' }}>
                  <div style={{ position: 'relative', paddingTop: '56.25%' }}>
                    <iframe
                      src={activeLesson.content_url}
                      style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', border: 'none' }}
                      allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                      allowFullScreen
                      title={activeLesson.title}
                    />
                  </div>
                </div>
              )}

              {/* Text content */}
              {activeLesson.type === 'text' && activeLesson.content_text && (
                <div
                  style={{
                    background: 'var(--bg-surface)', border: '1px solid var(--border-light)',
                    borderRadius: 'var(--radius-lg)', padding: '24px',
                    fontSize: 14, lineHeight: 1.75, color: 'var(--text-primary)',
                  }}
                  dangerouslySetInnerHTML={{ __html: activeLesson.content_text }}
                />
              )}

              {/* Quiz */}
              {activeLesson.type === 'quiz' && (
                <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', padding: 24 }}>
                  <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 20 }}>
                    ❓ Quiz — {quizQuestions.length} {quizQuestions.length === 1 ? 'Frage' : 'Fragen'}
                  </div>

                  {quizQuestions.length === 0 ? (
                    <div style={{ color: 'var(--text-tertiary)', fontSize: 13 }}>Noch keine Fragen hinterlegt.</div>
                  ) : quizResult ? (
                    /* Result */
                    <div style={{ textAlign: 'center', padding: '20px 0' }}>
                      <div style={{ fontSize: 52, marginBottom: 12 }}>{quizResult.passed ? '🏆' : '😞'}</div>
                      <div style={{ fontSize: 28, fontWeight: 800, color: quizResult.passed ? '#16a34a' : '#dc2626', marginBottom: 6 }}>
                        {quizResult.score}%
                      </div>
                      <div style={{ fontSize: 14, color: 'var(--text-secondary)', marginBottom: 4 }}>
                        {quizResult.correct} von {quizResult.total} richtig
                      </div>
                      <div style={{ fontSize: 13, fontWeight: 600, color: quizResult.passed ? '#16a34a' : '#dc2626', marginBottom: 24 }}>
                        {quizResult.passed ? '✓ Bestanden' : '✗ Nicht bestanden — mind. 70% benötigt'}
                      </div>
                      {!quizResult.passed && (
                        <button onClick={() => { setQuizResult(null); setQuizAnswers({}); }} style={{
                          padding: '9px 20px', background: 'var(--brand-primary)', color: 'white',
                          border: 'none', borderRadius: 'var(--radius-md)', fontSize: 13,
                          fontWeight: 600, cursor: 'pointer', fontFamily: 'var(--font-sans)',
                        }}>Nochmal versuchen</button>
                      )}
                    </div>
                  ) : (
                    /* Questions */
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
                      {quizQuestions.map((q, qi) => (
                        <div key={q.id} style={{ padding: 16, background: 'var(--bg-app)', borderRadius: 'var(--radius-md)' }}>
                          <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 12 }}>
                            {qi + 1}. {q.question}
                          </div>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                            {q.answers.map(ans => (
                              <label key={ans.id} style={{
                                display: 'flex', alignItems: 'center', gap: 10,
                                cursor: 'pointer', padding: '8px 12px',
                                borderRadius: 'var(--radius-md)',
                                background: quizAnswers[q.id] === ans.id ? 'rgba(var(--brand-primary-rgb,30,73,132),0.08)' : 'transparent',
                                border: `1px solid ${quizAnswers[q.id] === ans.id ? 'var(--brand-primary)' : 'var(--border-light)'}`,
                                transition: 'all 0.15s',
                              }}>
                                <input
                                  type="radio" name={`q_${q.id}`} value={ans.id}
                                  checked={quizAnswers[q.id] === ans.id}
                                  onChange={() => setQuizAnswers(p => ({ ...p, [q.id]: ans.id }))}
                                  style={{ accentColor: 'var(--brand-primary)', flexShrink: 0 }}
                                />
                                <span style={{ fontSize: 13, color: 'var(--text-primary)' }}>{ans.text}</span>
                              </label>
                            ))}
                          </div>
                        </div>
                      ))}
                      <button
                        onClick={handleSubmitQuiz}
                        disabled={quizLoading || Object.keys(quizAnswers).length < quizQuestions.length}
                        style={{
                          padding: '10px 24px', background: 'var(--brand-primary)', color: 'white',
                          border: 'none', borderRadius: 'var(--radius-md)', fontSize: 13,
                          fontWeight: 700, cursor: 'pointer', fontFamily: 'var(--font-sans)',
                          opacity: Object.keys(quizAnswers).length < quizQuestions.length ? 0.45 : 1,
                          alignSelf: 'flex-start',
                        }}
                      >
                        {quizLoading ? 'Wird geprüft…' : 'Antworten prüfen →'}
                      </button>
                    </div>
                  )}
                </div>
              )}

              {/* Download */}
              {activeLesson.file_url && (
                <a href={activeLesson.file_url} download target="_blank" rel="noreferrer" style={{
                  display: 'flex', alignItems: 'center', gap: 10, padding: '12px 16px',
                  background: 'var(--bg-surface)', border: '1px solid var(--border-light)',
                  borderRadius: 'var(--radius-lg)', textDecoration: 'none',
                  color: 'var(--text-primary)', fontSize: 13, fontWeight: 500,
                }}>
                  📎 Datei herunterladen
                </a>
              )}

              {/* Navigation bar */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <button
                  onClick={() => prevLesson && setActiveLessonId(prevLesson.id)}
                  disabled={!prevLesson}
                  style={{
                    padding: '9px 18px', background: 'var(--bg-surface)',
                    color: 'var(--text-secondary)',
                    border: '1px solid var(--border-medium)',
                    borderRadius: 'var(--radius-md)', fontSize: 12, fontWeight: 600,
                    cursor: prevLesson ? 'pointer' : 'default',
                    fontFamily: 'var(--font-sans)', opacity: prevLesson ? 1 : 0.4,
                  }}
                >← Zurück</button>

                {activeLesson.type !== 'quiz' && (
                  <button
                    onClick={handleComplete}
                    disabled={completing}
                    style={{
                      padding: '9px 20px',
                      background: isDone(activeLessonId) ? '#f0fdf4' : 'var(--brand-primary)',
                      color: isDone(activeLessonId) ? '#16a34a' : 'white',
                      border: isDone(activeLessonId) ? '1px solid #bbf7d0' : 'none',
                      borderRadius: 'var(--radius-md)', fontSize: 12, fontWeight: 700,
                      cursor: 'pointer', fontFamily: 'var(--font-sans)',
                    }}
                  >
                    {isDone(activeLessonId)
                      ? '✓ Als offen markieren'
                      : completing ? 'Speichern…' : 'Als erledigt markieren →'}
                  </button>
                )}

                <button
                  onClick={() => nextLesson && setActiveLessonId(nextLesson.id)}
                  disabled={!nextLesson}
                  style={{
                    padding: '9px 18px',
                    background: nextLesson ? 'var(--brand-primary)' : 'var(--bg-surface)',
                    color: nextLesson ? 'white' : 'var(--text-secondary)',
                    border: nextLesson ? 'none' : '1px solid var(--border-medium)',
                    borderRadius: 'var(--radius-md)', fontSize: 12, fontWeight: 600,
                    cursor: nextLesson ? 'pointer' : 'default',
                    fontFamily: 'var(--font-sans)', opacity: nextLesson ? 1 : 0.4,
                  }}
                >Weiter →</button>
              </div>

              {/* Certificate banner at 100% */}
              {overallPct === 100 && (
                <div style={{
                  background: 'linear-gradient(135deg, #f0fdf4, #dcfce7)',
                  border: '1px solid #bbf7d0', borderRadius: 'var(--radius-lg)',
                  padding: '20px 24px', display: 'flex',
                  alignItems: 'center', justifyContent: 'space-between', gap: 16,
                }}>
                  <div>
                    <div style={{ fontSize: 14, fontWeight: 700, color: '#166534', marginBottom: 4 }}>
                      🏆 Kurs abgeschlossen!
                    </div>
                    <div style={{ fontSize: 12, color: '#15803d' }}>Du kannst jetzt dein Zertifikat erstellen.</div>
                  </div>
                  <button onClick={handleCertificate} style={{
                    padding: '9px 18px', background: '#16a34a', color: 'white',
                    border: 'none', borderRadius: 'var(--radius-md)', fontSize: 12,
                    fontWeight: 700, cursor: 'pointer', fontFamily: 'var(--font-sans)', flexShrink: 0,
                  }}>Zertifikat erstellen →</button>
                </div>
              )}
            </>
          ) : (
            <div style={{ textAlign: 'center', padding: '60px 20px', color: 'var(--text-tertiary)' }}>
              <div style={{ fontSize: 48, marginBottom: 12, opacity: 0.3 }}>📚</div>
              <div style={{ fontSize: 14 }}>Wähle eine Lektion in der Sidebar aus.</div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}

import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import API_BASE_URL from '../config';

const TYPE_ICON  = { video: '🎬', text: '📄', quiz: '❓', checklist: '✅' };
const TYPE_LABEL = { video: 'VIDEO', text: 'TEXT', quiz: 'QUIZ', checklist: 'CHECKLISTE' };
const TYPE_COLOR = { video: '#7c3aed', text: '#0891b2', quiz: '#d97706', checklist: '#059669' };

export default function AcademyCourse() {
  const { id, kursId } = useParams();
  const courseId = id || kursId;
  const navigate = useNavigate();
  const { user, token } = useAuth();
  const h = useCallback(
    () => ({ 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) }),
    [token],
  );

  const [course, setCourse] = useState(null);
  const [modules, setModules] = useState([]);
  const [progressMap, setProgressMap] = useState({});
  const [activeLessonId, setActiveLessonId] = useState(null);
  const [activeLesson, setActiveLesson] = useState(null);
  const [loading, setLoading] = useState(true);
  const [completing, setCompleting] = useState(false);
  const [openModules, setOpenModules] = useState({});
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // Quiz state — step-by-step
  const [quizQuestions, setQuizQuestions] = useState([]);
  const [quizStep, setQuizStep] = useState(0);
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
        setQuizStep(0);
        setQuizAnswers({});
        setQuizResult(null);
        if (data.type === 'quiz') {
          setQuizLoading(true);
          fetch(`${API_BASE_URL}/api/academy/lessons/${activeLessonId}/quiz`, { headers: h() })
            .then(r => r.json())
            .then(qs => { setQuizQuestions(Array.isArray(qs) ? qs : []); })
            .catch(console.error)
            .finally(() => setQuizLoading(false));
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
  const isDone = lid => Boolean(progressMap[lid]?.completed);

  // Current module of active lesson
  const activeModule = modules.find(m => m.lessons?.some(l => l.id === activeLessonId));

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
  const currentQ = quizQuestions[quizStep] || null;
  const quizAnswered = currentQ ? quizAnswers[currentQ.id] !== undefined : false;
  const allAnswered = quizQuestions.length > 0 && quizQuestions.every(q => quizAnswers[q.id] !== undefined);

  return (
    <>
      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.45)', zIndex: 40 }}
          onClick={() => setSidebarOpen(false)} />
      )}

      {/* Mobile: open sidebar button */}
      <button onClick={() => setSidebarOpen(true)} style={{
        display: 'none',
        padding: '7px 14px', background: 'var(--bg-surface)',
        border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)',
        fontSize: 12, cursor: 'pointer', fontFamily: 'var(--font-sans)',
        marginBottom: 12,
      }} className="academy-mobile-toggle">☰ Inhaltsverzeichnis ▼</button>

      <div style={{ display: 'flex', gap: 20, alignItems: 'flex-start' }}>

        {/* ── Sidebar (260px, fixed scroll) ─────────────── */}
        <aside style={{
          width: 260, flexShrink: 0,
          background: 'var(--bg-surface)', border: '1px solid var(--border-light)',
          borderRadius: 'var(--radius-lg)', display: 'flex', flexDirection: 'column',
          overflow: 'hidden', position: 'sticky', top: 16, maxHeight: 'calc(100vh - 100px)',
          ...(sidebarOpen ? {
            position: 'fixed', top: 0, left: 0, bottom: 0, zIndex: 50,
            width: 300, borderRadius: 0,
          } : {}),
        }}>
          {/* Back + course title + progress */}
          <div style={{ padding: '14px 16px 12px', borderBottom: '1px solid var(--border-light)', flexShrink: 0 }}>
            <button onClick={() => navigate('/app/academy')} style={{
              background: 'none', border: 'none', color: 'var(--text-tertiary)',
              fontSize: 11, cursor: 'pointer', padding: 0, marginBottom: 10,
              fontFamily: 'var(--font-sans)', display: 'flex', alignItems: 'center', gap: 4,
            }}>← Zur Übersicht</button>
            <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1.4, marginBottom: 10 }}>
              {course.title}
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
              <span style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>{completedCount} / {allLessons.length} Lektionen</span>
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
                    <span style={{ fontSize: 10, color: 'var(--text-tertiary)', marginRight: 6, flexShrink: 0 }}>{mDone}/{mLessons.length}</span>
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
                            <span style={{ fontSize: 12, flexShrink: 0, width: 16, textAlign: 'center', color: done && !active ? '#16a34a' : 'inherit' }}>
                              {locked ? '🔒' : done ? '✓' : active ? '▶' : '○'}
                            </span>
                            <span style={{ fontSize: 12, lineHeight: 1.3, flex: 1 }}>{lesson.title}</span>
                            <span style={{ fontSize: 11, flexShrink: 0, opacity: 0.65 }}>{TYPE_ICON[lesson.type] || '📄'}</span>
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

          {activeLesson ? (
            <>
              {/* Breadcrumb */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: 'var(--text-tertiary)', flexWrap: 'wrap' }}>
                <button onClick={() => navigate('/app/academy')} style={{ background: 'none', border: 'none', color: 'var(--text-tertiary)', cursor: 'pointer', fontSize: 12, fontFamily: 'var(--font-sans)', padding: 0 }}>
                  Akademy
                </button>
                <span>›</span>
                <button onClick={() => navigate('/app/academy')} style={{ background: 'none', border: 'none', color: 'var(--text-tertiary)', cursor: 'pointer', fontSize: 12, fontFamily: 'var(--font-sans)', padding: 0, maxWidth: 160, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {course.title}
                </button>
                {activeModule && (<><span>›</span><span style={{ color: 'var(--text-secondary)', fontWeight: 500 }}>{activeModule.title}</span></>)}
              </div>

              {/* Lesson header */}
              <div style={{
                background: 'var(--bg-surface)', border: '1px solid var(--border-light)',
                borderRadius: 'var(--radius-lg)', padding: '20px 24px',
                display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 16,
              }}>
                <div>
                  {/* Type badge */}
                  <div style={{
                    display: 'inline-flex', alignItems: 'center', gap: 5,
                    background: TYPE_COLOR[activeLesson.type] || 'var(--brand-primary)',
                    color: 'white',
                    borderRadius: 'var(--radius-full)', padding: '3px 10px',
                    fontSize: 10, fontWeight: 700, letterSpacing: '0.08em',
                    marginBottom: 10,
                  }}>
                    {TYPE_ICON[activeLesson.type]} {TYPE_LABEL[activeLesson.type] || 'LEKTION'}
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

              {/* ── Quiz (step-by-step) ─────────────────────── */}
              {activeLesson.type === 'quiz' && (
                <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', padding: 24 }}>

                  {quizLoading ? (
                    <div style={{ display: 'flex', justifyContent: 'center', padding: 40 }}>
                      <div style={{ width: 28, height: 28, borderRadius: '50%', border: '3px solid var(--border-light)', borderTopColor: 'var(--brand-primary)', animation: 'spin 0.8s linear infinite' }} />
                    </div>
                  ) : quizQuestions.length === 0 ? (
                    <div style={{ color: 'var(--text-tertiary)', fontSize: 13 }}>Noch keine Fragen hinterlegt.</div>

                  ) : quizResult ? (
                    /* ── Result screen ── */
                    <div style={{ textAlign: 'center', padding: '24px 0' }}>
                      <div style={{
                        display: 'inline-block', borderRadius: 'var(--radius-lg)', padding: '24px 40px',
                        background: quizResult.passed ? '#f0fdf4' : '#fef2f2',
                        border: `1px solid ${quizResult.passed ? '#bbf7d0' : '#fecaca'}`,
                        marginBottom: 24,
                      }}>
                        <div style={{ fontSize: 48, marginBottom: 8 }}>{quizResult.passed ? '🏆' : '😞'}</div>
                        <div style={{ fontSize: 26, fontWeight: 800, color: quizResult.passed ? '#16a34a' : '#dc2626', marginBottom: 4 }}>
                          {quizResult.passed ? 'Bestanden' : 'Nicht bestanden'}
                        </div>
                        <div style={{ fontSize: 15, color: quizResult.passed ? '#15803d' : '#b91c1c' }}>
                          {quizResult.correct} von {quizResult.total} richtig ✓
                        </div>
                        {!quizResult.passed && (
                          <div style={{ fontSize: 12, color: '#b91c1c', marginTop: 4 }}>Bitte erneut versuchen.</div>
                        )}
                      </div>
                      {!quizResult.passed && (
                        <button onClick={() => { setQuizResult(null); setQuizAnswers({}); setQuizStep(0); }} style={{
                          padding: '9px 22px', background: 'var(--brand-primary)', color: 'white',
                          border: 'none', borderRadius: 'var(--radius-md)', fontSize: 13,
                          fontWeight: 600, cursor: 'pointer', fontFamily: 'var(--font-sans)',
                        }}>Nochmal versuchen</button>
                      )}
                    </div>

                  ) : (
                    /* ── Step-by-step questions ── */
                    <>
                      {/* Quiz progress bar */}
                      <div style={{ marginBottom: 20 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                          <span style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-secondary)' }}>
                            Frage {quizStep + 1} von {quizQuestions.length}
                          </span>
                          <span style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>
                            {Object.keys(quizAnswers).length} beantwortet
                          </span>
                        </div>
                        <div style={{ height: 5, background: 'var(--border-light)', borderRadius: 3, overflow: 'hidden' }}>
                          <div style={{
                            width: `${((quizStep + 1) / quizQuestions.length) * 100}%`,
                            height: '100%', background: 'var(--brand-primary)',
                            borderRadius: 3, transition: 'width 0.3s',
                          }} />
                        </div>
                      </div>

                      {/* Question */}
                      {currentQ && (
                        <div>
                          <div style={{ fontSize: 15, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 16, lineHeight: 1.4 }}>
                            {currentQ.question}
                          </div>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginBottom: 20 }}>
                            {currentQ.answers.map(ans => {
                              const selected = quizAnswers[currentQ.id] === ans.id;
                              return (
                                <label key={ans.id} style={{
                                  display: 'flex', alignItems: 'center', gap: 12,
                                  cursor: 'pointer', padding: '12px 16px',
                                  borderRadius: 'var(--radius-md)',
                                  background: selected ? 'var(--brand-primary-light)' : 'var(--bg-app)',
                                  border: `1.5px solid ${selected ? 'var(--brand-primary)' : 'var(--border-light)'}`,
                                  transition: 'all 0.15s',
                                }}>
                                  <input
                                    type="radio" name={`q_${currentQ.id}`} value={ans.id}
                                    checked={selected}
                                    onChange={() => setQuizAnswers(p => ({ ...p, [currentQ.id]: ans.id }))}
                                    style={{ accentColor: 'var(--brand-primary)', flexShrink: 0, width: 16, height: 16 }}
                                  />
                                  <span style={{ fontSize: 13, color: 'var(--text-primary)', lineHeight: 1.4 }}>{ans.text}</span>
                                </label>
                              );
                            })}
                          </div>

                          {/* Step navigation */}
                          <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
                            {quizStep > 0 && (
                              <button onClick={() => setQuizStep(s => s - 1)} style={{
                                padding: '8px 18px', background: 'var(--bg-app)',
                                color: 'var(--text-secondary)', border: '1px solid var(--border-medium)',
                                borderRadius: 'var(--radius-md)', fontSize: 13, cursor: 'pointer',
                                fontFamily: 'var(--font-sans)',
                              }}>← Zurück</button>
                            )}
                            {quizStep < quizQuestions.length - 1 ? (
                              <button
                                onClick={() => setQuizStep(s => s + 1)}
                                disabled={!quizAnswered}
                                style={{
                                  padding: '8px 18px', background: quizAnswered ? 'var(--brand-primary)' : 'var(--border-light)',
                                  color: quizAnswered ? 'white' : 'var(--text-tertiary)',
                                  border: 'none', borderRadius: 'var(--radius-md)',
                                  fontSize: 13, fontWeight: 600, cursor: quizAnswered ? 'pointer' : 'not-allowed',
                                  fontFamily: 'var(--font-sans)',
                                }}
                              >Weiter →</button>
                            ) : (
                              <button
                                onClick={handleSubmitQuiz}
                                disabled={!allAnswered || quizLoading}
                                style={{
                                  padding: '8px 20px',
                                  background: allAnswered ? 'var(--brand-primary)' : 'var(--border-light)',
                                  color: allAnswered ? 'white' : 'var(--text-tertiary)',
                                  border: 'none', borderRadius: 'var(--radius-md)',
                                  fontSize: 13, fontWeight: 700, cursor: allAnswered ? 'pointer' : 'not-allowed',
                                  fontFamily: 'var(--font-sans)',
                                }}
                              >{quizLoading ? 'Wird geprüft…' : 'Antworten absenden →'}</button>
                            )}
                          </div>
                        </div>
                      )}
                    </>
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
              <div style={{
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                padding: '14px 0', borderTop: '1px solid var(--border-light)',
              }}>
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
                >← Vorherige Lektion</button>

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
                      ? '✓ Erledigt'
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
                >Nächste Lektion →</button>
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
              <div style={{ fontSize: 14 }}>Wähle eine Lektion im Inhaltsverzeichnis aus.</div>
            </div>
          )}
        </div>
      </div>

      <style>{`
        @media (max-width: 768px) {
          .academy-mobile-toggle { display: flex !important; }
        }
      `}</style>
    </>
  );
}

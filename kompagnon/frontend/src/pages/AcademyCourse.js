import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import API_BASE_URL from '../config';

// ── Design tokens ──────────────────────────────────────────────
const T = {
  primary:     '#008eaa',
  primaryBg:   '#e0f4f8',
  primaryDark: '#006880',
  appBg:       '#f4f6f8',
  surface:     '#ffffff',
  border:      'rgba(0,142,170,0.12)',
  borderMed:   'rgba(0,142,170,0.25)',
  text:        '#0f1c20',
  textSub:     '#4a6470',
  textMuted:   '#8fa8b0',
  radiusLg:    '12px',
  radiusFull:  '9999px',
  shadow:      '0 1px 3px rgba(0,0,0,0.06)',
  font:        "'DM Sans', system-ui, sans-serif",
  successBg:   '#eaf5ee',
  successText: '#1a7a3a',
  errorBg:     '#fef0f0',
  errorText:   '#b02020',
  neutralBg:   '#f0f2f4',
  quizBg:      '#fff8e6',
  quizText:    '#a06800',
};

// Lesson-type badge tokens
const TYPE_BADGE = {
  video:     { bg: T.primaryBg,  color: T.primaryDark, label: 'VIDEO',      icon: '🎬' },
  text:      { bg: T.neutralBg,  color: T.textSub,     label: 'TEXT',       icon: '📄' },
  quiz:      { bg: T.quizBg,     color: T.quizText,    label: 'QUIZ',       icon: '❓' },
  checklist: { bg: T.successBg,  color: T.successText, label: 'CHECKLISTE', icon: '✅' },
};

export default function AcademyCourse() {
  const { id, kursId } = useParams();
  const courseId = id || kursId;
  const navigate = useNavigate();
  const { token } = useAuth();
  const h = useCallback(
    () => ({ 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) }),
    [token],
  );

  const [course,         setCourse]         = useState(null);
  const [modules,        setModules]        = useState([]);
  const [progressMap,    setProgressMap]    = useState({});
  const [activeLessonId, setActiveLessonId] = useState(null);
  const [activeLesson,   setActiveLesson]   = useState(null);
  const [loading,        setLoading]        = useState(true);
  const [completing,     setCompleting]     = useState(false);
  const [openModules,    setOpenModules]    = useState({});
  const [sidebarOpen,    setSidebarOpen]    = useState(false);

  // Quiz — step-by-step
  const [quizQuestions, setQuizQuestions] = useState([]);
  const [quizStep,      setQuizStep]      = useState(0);
  const [quizAnswers,   setQuizAnswers]   = useState({});
  const [quizResult,    setQuizResult]    = useState(null);
  const [quizLoading,   setQuizLoading]   = useState(false);

  // ── Load course + progress ──────────────────────────────────
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

  // ── Load lesson detail ──────────────────────────────────────
  useEffect(() => {
    if (!activeLessonId) return;
    fetch(`${API_BASE_URL}/api/academy/lessons/${activeLessonId}`, { headers: h() })
      .then(r => r.json())
      .then(data => {
        setActiveLesson(data);
        setQuizQuestions([]); setQuizStep(0); setQuizAnswers({}); setQuizResult(null);
        if (data.type === 'quiz') {
          setQuizLoading(true);
          fetch(`${API_BASE_URL}/api/academy/lessons/${activeLessonId}/quiz`, { headers: h() })
            .then(r => r.json())
            .then(qs => setQuizQuestions(Array.isArray(qs) ? qs : []))
            .catch(console.error)
            .finally(() => setQuizLoading(false));
        }
      }).catch(console.error);
  }, [activeLessonId]); // eslint-disable-line

  // ── Derived ─────────────────────────────────────────────────
  const allLessons    = modules.flatMap(m => m.lessons || []);
  const currentIdx    = allLessons.findIndex(l => l.id === activeLessonId);
  const prevLesson    = currentIdx > 0 ? allLessons[currentIdx - 1] : null;
  const nextLesson    = currentIdx < allLessons.length - 1 ? allLessons[currentIdx + 1] : null;
  const completedCount = allLessons.filter(l => progressMap[l.id]?.completed).length;
  const overallPct    = allLessons.length > 0 ? Math.round((completedCount / allLessons.length) * 100) : 0;
  const isDone        = lid => Boolean(progressMap[lid]?.completed);
  const activeModule  = modules.find(m => m.lessons?.some(l => l.id === activeLessonId));

  const isLocked = lessonId => {
    if (!course?.linear_progress) return false;
    const idx = allLessons.findIndex(l => l.id === lessonId);
    for (let i = 0; i < idx; i++) if (!isDone(allLessons[i].id)) return true;
    return false;
  };

  // ── Actions ──────────────────────────────────────────────────
  const selectLesson = lesson => {
    if (isLocked(lesson.id)) return;
    setActiveLessonId(lesson.id);
    setSidebarOpen(false);
  };

  const handleComplete = async () => {
    if (!activeLessonId || completing) return;
    setCompleting(true);
    try {
      const res  = await fetch(`${API_BASE_URL}/api/academy/lessons/${activeLessonId}/complete`, {
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
      const res  = await fetch(`${API_BASE_URL}/api/academy/lessons/${activeLessonId}/quiz`, {
        method: 'POST', headers: h(), body: JSON.stringify({ answers: quizAnswers }),
      });
      const data = await res.json();
      setQuizResult(data);
      if (data.passed)
        setProgressMap(p => ({ ...p, [activeLessonId]: { ...p[activeLessonId], completed: true, score: data.score } }));
    } catch (e) { console.error(e); }
    setQuizLoading(false);
  };

  const handleCertificate = async () => {
    try {
      const res  = await fetch(`${API_BASE_URL}/api/academy/courses/${courseId}/certificate`, { method: 'POST', headers: h() });
      const data = await res.json();
      if (data.certificate_code) navigate(`/academy/certificate/${data.certificate_code}`);
    } catch (e) { console.error(e); }
  };

  // ── Loading / not found ──────────────────────────────────────
  if (loading) return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '60vh' }}>
      <div style={{ width: 32, height: 32, borderRadius: '50%', border: `3px solid ${T.primaryBg}`, borderTopColor: T.primary, animation: 'spin 0.8s linear infinite' }} />
    </div>
  );
  if (!course) return (
    <div style={{ textAlign: 'center', padding: 60, color: T.textMuted, fontFamily: T.font }}>Kurs nicht gefunden.</div>
  );

  const currentQ   = quizQuestions[quizStep] || null;
  const qAnswered  = currentQ ? quizAnswers[currentQ.id] !== undefined : false;
  const allAnswered = quizQuestions.length > 0 && quizQuestions.every(q => quizAnswers[q.id] !== undefined);
  const lessonDone  = isDone(activeLessonId);
  const badge       = activeLesson ? (TYPE_BADGE[activeLesson.type] || TYPE_BADGE.text) : null;

  return (
    <>
      {/* ── Mobile overlay ─────────────────────────────────── */}
      {sidebarOpen && (
        <div
          style={{ position: 'fixed', inset: 0, background: 'rgba(15,28,32,0.5)', zIndex: 40 }}
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* ── Mobile toggle button ────────────────────────────── */}
      <button
        onClick={() => setSidebarOpen(true)}
        className="ac-mobile-toggle"
        style={{
          display: 'none', marginBottom: 12,
          padding: '8px 16px', background: T.surface,
          border: `1px solid ${T.border}`, borderRadius: T.radiusLg,
          fontSize: 13, fontWeight: 500, color: T.textSub,
          cursor: 'pointer', fontFamily: T.font,
          boxShadow: T.shadow,
        }}
      >☰ Inhaltsverzeichnis ▼</button>

      {/* ── Two-column layout ───────────────────────────────── */}
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 0, minHeight: '70vh' }}>

        {/* ════════════════════════════════════════════════════
            SIDEBAR
        ════════════════════════════════════════════════════ */}
        <aside
          className={`ac-sidebar${sidebarOpen ? ' open' : ''}`}
          style={{
            width: 260, flexShrink: 0,
            background: T.surface,
            borderRight: `1px solid ${T.border}`,
            display: 'flex', flexDirection: 'column',
            position: 'sticky', top: 0,
            maxHeight: 'calc(100vh - 76px)',
            overflowY: 'auto',
            // Mobile: slide-in panel
            ...(sidebarOpen ? {
              position: 'fixed', top: 0, left: 0, bottom: 0, zIndex: 50,
              width: 300, borderRight: `1px solid ${T.border}`,
              boxShadow: '4px 0 24px rgba(0,0,0,0.12)',
              overflowY: 'auto',
            } : {}),
          }}
        >

          {/* Back link + course title + overall progress */}
          <div style={{ padding: '16px 16px 14px', borderBottom: `1px solid ${T.border}`, flexShrink: 0 }}>
            <button
              onClick={() => navigate('/app/academy')}
              style={{
                background: 'none', border: 'none', padding: 0, marginBottom: 12,
                fontSize: 12, color: T.textMuted, cursor: 'pointer',
                fontFamily: T.font, display: 'flex', alignItems: 'center', gap: 4,
              }}
            >← Zur Übersicht</button>

            <div style={{ fontSize: 14, fontWeight: 700, color: T.text, lineHeight: 1.4, marginBottom: 12, fontFamily: T.font }}>
              {course.title}
            </div>

            {/* Overall progress bar */}
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}>
              <span style={{ fontSize: 11, color: T.textMuted, fontFamily: T.font }}>
                {completedCount} / {allLessons.length} Lektionen
              </span>
              <span style={{ fontSize: 11, fontWeight: 600, color: overallPct === 100 ? T.successText : T.primary, fontFamily: T.font }}>
                {overallPct}%
              </span>
            </div>
            <div style={{ height: 6, background: T.primaryBg, borderRadius: 3, overflow: 'hidden' }}>
              <div style={{
                width: `${overallPct}%`, height: '100%',
                background: overallPct === 100 ? T.successText : T.primary,
                borderRadius: 3, transition: 'width 0.4s ease',
              }} />
            </div>
          </div>

          {/* Module accordion */}
          <nav style={{ flex: 1, overflowY: 'auto', padding: '8px 0' }}>
            {modules.map(mod => {
              const mLessons = mod.lessons || [];
              const mDone    = mLessons.filter(l => isDone(l.id)).length;
              const open     = Boolean(openModules[mod.id]);

              return (
                <div key={mod.id} style={{ marginBottom: 2 }}>
                  {/* Module header */}
                  <button
                    onClick={() => setOpenModules(p => ({ ...p, [mod.id]: !p[mod.id] }))}
                    style={{
                      width: '100%', display: 'flex', alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '9px 16px',
                      background: T.appBg,
                      borderLeft: open ? `3px solid ${T.primary}` : '3px solid transparent',
                      border: 'none', borderTop: `1px solid ${T.border}`,
                      cursor: 'pointer', textAlign: 'left',
                      transition: 'border-left-color 0.15s',
                    }}
                  >
                    <span style={{ fontSize: 12, fontWeight: 600, color: T.text, lineHeight: 1.3, flex: 1, fontFamily: T.font }}>
                      {mod.title}
                    </span>
                    <span style={{ fontSize: 10, color: T.textMuted, marginRight: 8, fontFamily: T.font, flexShrink: 0 }}>
                      {mDone}/{mLessons.length}
                    </span>
                    <span style={{
                      fontSize: 9, color: T.textMuted, flexShrink: 0,
                      transform: open ? 'rotate(180deg)' : 'none',
                      transition: 'transform 0.2s',
                    }}>▼</span>
                  </button>

                  {/* Lessons list */}
                  {open && (
                    <div>
                      {mLessons.map(lesson => {
                        const active = lesson.id === activeLessonId;
                        const done   = isDone(lesson.id);
                        const locked = isLocked(lesson.id);

                        // State-based styles
                        let bg      = 'transparent';
                        let color   = T.textMuted;
                        let weight  = 400;
                        let opacity = 1;
                        let marker  = '○';

                        if (locked) { opacity = 0.5; marker = '🔒'; color = T.textMuted; }
                        else if (active) { bg = T.primaryBg; color = T.primary; weight = 600; marker = '▶'; }
                        else if (done)   { bg = T.successBg; color = T.successText; marker = '✓'; }

                        return (
                          <button
                            key={lesson.id}
                            onClick={() => selectLesson(lesson)}
                            disabled={locked}
                            style={{
                              width: '100%', display: 'flex', alignItems: 'center',
                              gap: 8, padding: '8px 16px 8px 20px',
                              background: bg, border: 'none',
                              cursor: locked ? 'not-allowed' : 'pointer',
                              textAlign: 'left', opacity,
                              transition: 'background 0.15s',
                            }}
                            onMouseEnter={e => { if (!active && !locked) e.currentTarget.style.background = T.primaryBg; }}
                            onMouseLeave={e => { if (!active && !locked) e.currentTarget.style.background = bg; }}
                          >
                            <span style={{ fontSize: done ? 11 : 12, color, flexShrink: 0, width: 14, textAlign: 'center' }}>
                              {marker}
                            </span>
                            <span style={{ fontSize: 12, color, fontWeight: weight, lineHeight: 1.35, flex: 1, fontFamily: T.font }}>
                              {lesson.title}
                            </span>
                            <span style={{ fontSize: 10, color: T.textMuted, flexShrink: 0, opacity: 0.7 }}>
                              {(TYPE_BADGE[lesson.type] || TYPE_BADGE.text).icon}
                            </span>
                          </button>
                        );
                      })}
                    </div>
                  )}
                </div>
              );
            })}
          </nav>
        </aside>

        {/* ════════════════════════════════════════════════════
            MAIN CONTENT
        ════════════════════════════════════════════════════ */}
        <div className="ac-content" style={{
          flex: 1, minWidth: 0,
          background: T.appBg,
          padding: '32px 32px 48px',
          display: 'flex', flexDirection: 'column', gap: 20,
        }}>

          {activeLesson ? (
            <>
              {/* ── Breadcrumb ── */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
                <button
                  onClick={() => navigate('/app/academy')}
                  style={{ background: 'none', border: 'none', padding: 0, fontSize: 12, color: T.textMuted, cursor: 'pointer', fontFamily: T.font }}
                >Akademy</button>
                <span style={{ fontSize: 12, color: T.textMuted }}>›</span>
                <button
                  onClick={() => navigate('/app/academy')}
                  style={{
                    background: 'none', border: 'none', padding: 0, fontSize: 12,
                    color: T.textMuted, cursor: 'pointer', fontFamily: T.font,
                    maxWidth: 180, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                  }}
                >{course.title}</button>
                {activeModule && (
                  <>
                    <span style={{ fontSize: 12, color: T.textMuted }}>›</span>
                    <span style={{ fontSize: 12, color: T.textSub, fontFamily: T.font, fontWeight: 500 }}>
                      {activeModule.title}
                    </span>
                  </>
                )}
              </div>

              {/* ── Lesson header (badge + title) ── */}
              <div>
                {/* Type badge */}
                <div style={{
                  display: 'inline-flex', alignItems: 'center', gap: 5,
                  background: badge.bg, color: badge.color,
                  borderRadius: T.radiusFull, padding: '4px 12px',
                  fontSize: 11, fontWeight: 700, letterSpacing: '0.06em',
                  fontFamily: T.font, marginBottom: 10,
                }}>
                  {badge.icon} {badge.label}
                </div>

                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 16 }}>
                  <div>
                    <h1 style={{
                      fontSize: 22, fontWeight: 700, color: T.text,
                      margin: 0, letterSpacing: '-0.01em', lineHeight: 1.3,
                      fontFamily: T.font,
                    }}>
                      {activeLesson.title}
                    </h1>
                    {activeLesson.duration_minutes > 0 && (
                      <div style={{ fontSize: 12, color: T.textMuted, marginTop: 6, fontFamily: T.font }}>
                        ⏱ {activeLesson.duration_minutes} Min.
                      </div>
                    )}
                  </div>
                  {lessonDone && (
                    <div style={{
                      background: T.successBg, color: T.successText,
                      borderRadius: T.radiusFull, padding: '5px 14px',
                      fontSize: 12, fontWeight: 600, flexShrink: 0, fontFamily: T.font,
                    }}>✓ Erledigt</div>
                  )}
                </div>
              </div>

              {/* ── Content box ── */}
              <div style={{
                background: T.surface, borderRadius: T.radiusLg,
                padding: 28, boxShadow: T.shadow,
              }}>

                {/* Video */}
                {activeLesson.type === 'video' && activeLesson.content_url && (
                  <div style={{ position: 'relative', paddingTop: '56.25%', borderRadius: 8, overflow: 'hidden' }}>
                    <iframe
                      src={activeLesson.content_url}
                      style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', border: 'none' }}
                      allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                      allowFullScreen title={activeLesson.title}
                    />
                  </div>
                )}

                {/* Text */}
                {activeLesson.type === 'text' && activeLesson.content_text && (
                  <div
                    style={{ fontSize: 15, lineHeight: 1.75, color: T.text, fontFamily: T.font }}
                    dangerouslySetInnerHTML={{ __html: activeLesson.content_text }}
                  />
                )}

                {/* Quiz — step-by-step */}
                {activeLesson.type === 'quiz' && (
                  <div>
                    {quizLoading && !quizResult ? (
                      <div style={{ display: 'flex', justifyContent: 'center', padding: 40 }}>
                        <div style={{ width: 28, height: 28, borderRadius: '50%', border: `3px solid ${T.primaryBg}`, borderTopColor: T.primary, animation: 'spin 0.8s linear infinite' }} />
                      </div>

                    ) : quizQuestions.length === 0 ? (
                      <div style={{ color: T.textMuted, fontSize: 13, fontFamily: T.font }}>Noch keine Fragen hinterlegt.</div>

                    ) : quizResult ? (
                      /* Result screen */
                      <div style={{ textAlign: 'center', padding: '16px 0' }}>
                        <div style={{
                          display: 'inline-block', borderRadius: T.radiusLg,
                          padding: '28px 44px',
                          background: quizResult.passed ? T.successBg : T.errorBg,
                          border: `1px solid ${quizResult.passed ? '#bbf7d0' : '#fecaca'}`,
                          marginBottom: 24,
                        }}>
                          <div style={{ fontSize: 44, marginBottom: 10 }}>{quizResult.passed ? '🏆' : '😞'}</div>
                          <div style={{ fontSize: 24, fontWeight: 700, color: quizResult.passed ? T.successText : T.errorText, marginBottom: 4, fontFamily: T.font }}>
                            {quizResult.passed ? 'Bestanden' : 'Nicht bestanden'}
                          </div>
                          <div style={{ fontSize: 14, color: quizResult.passed ? T.successText : T.errorText, fontFamily: T.font }}>
                            {quizResult.correct} von {quizResult.total} richtig
                          </div>
                        </div>
                        {!quizResult.passed && (
                          <div>
                            <button
                              onClick={() => { setQuizResult(null); setQuizAnswers({}); setQuizStep(0); }}
                              style={{
                                padding: '10px 24px', background: T.primary, color: '#fff',
                                border: 'none', borderRadius: '8px', fontSize: 13, fontWeight: 600,
                                cursor: 'pointer', fontFamily: T.font,
                              }}
                            >Nochmal versuchen</button>
                          </div>
                        )}
                      </div>

                    ) : (
                      /* Step-by-step questions */
                      <div>
                        {/* Quiz progress */}
                        <div style={{ marginBottom: 24 }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                            <span style={{ fontSize: 12, fontWeight: 600, color: T.textSub, fontFamily: T.font }}>
                              Frage {quizStep + 1} von {quizQuestions.length}
                            </span>
                            <span style={{ fontSize: 12, color: T.textMuted, fontFamily: T.font }}>
                              {Object.keys(quizAnswers).length} beantwortet
                            </span>
                          </div>
                          <div style={{ height: 6, background: T.primaryBg, borderRadius: 3, overflow: 'hidden' }}>
                            <div style={{
                              width: `${((quizStep + 1) / quizQuestions.length) * 100}%`,
                              height: '100%', background: T.primary, borderRadius: 3,
                              transition: 'width 0.3s ease',
                            }} />
                          </div>
                        </div>

                        {/* Question */}
                        {currentQ && (
                          <div>
                            <div style={{ fontSize: 15, fontWeight: 600, color: T.text, marginBottom: 16, lineHeight: 1.45, fontFamily: T.font }}>
                              {currentQ.question}
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginBottom: 24 }}>
                              {currentQ.answers.map(ans => {
                                const selected = quizAnswers[currentQ.id] === ans.id;
                                return (
                                  <label key={ans.id} style={{
                                    display: 'flex', alignItems: 'center', gap: 12,
                                    cursor: 'pointer', padding: '12px 16px',
                                    borderRadius: '8px',
                                    background: selected ? T.primaryBg : T.appBg,
                                    border: selected ? `2px solid ${T.primary}` : `1.5px solid ${T.borderMed}`,
                                    transition: 'all 0.15s',
                                  }}>
                                    <input
                                      type="radio" name={`q_${currentQ.id}`} value={ans.id}
                                      checked={selected}
                                      onChange={() => setQuizAnswers(p => ({ ...p, [currentQ.id]: ans.id }))}
                                      style={{ accentColor: T.primary, flexShrink: 0, width: 16, height: 16 }}
                                    />
                                    <span style={{ fontSize: 13, color: T.text, lineHeight: 1.4, fontFamily: T.font }}>
                                      {ans.text}
                                    </span>
                                  </label>
                                );
                              })}
                            </div>

                            {/* Step nav */}
                            <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
                              {quizStep > 0 && (
                                <button
                                  onClick={() => setQuizStep(s => s - 1)}
                                  style={{
                                    padding: '9px 18px', background: 'transparent',
                                    color: T.textSub, border: `1px solid ${T.border}`,
                                    borderRadius: '8px', fontSize: 13, cursor: 'pointer', fontFamily: T.font,
                                  }}
                                >← Zurück</button>
                              )}
                              {quizStep < quizQuestions.length - 1 ? (
                                <button
                                  onClick={() => setQuizStep(s => s + 1)}
                                  disabled={!qAnswered}
                                  style={{
                                    padding: '9px 18px',
                                    background: qAnswered ? T.primary : T.primaryBg,
                                    color: qAnswered ? '#fff' : T.textMuted,
                                    border: 'none', borderRadius: '8px',
                                    fontSize: 13, fontWeight: 600,
                                    cursor: qAnswered ? 'pointer' : 'not-allowed',
                                    fontFamily: T.font,
                                  }}
                                >Weiter →</button>
                              ) : (
                                <button
                                  onClick={handleSubmitQuiz}
                                  disabled={!allAnswered || quizLoading}
                                  style={{
                                    padding: '9px 20px',
                                    background: allAnswered ? T.primary : T.primaryBg,
                                    color: allAnswered ? '#fff' : T.textMuted,
                                    border: 'none', borderRadius: '8px',
                                    fontSize: 13, fontWeight: 700,
                                    cursor: allAnswered ? 'pointer' : 'not-allowed',
                                    fontFamily: T.font,
                                  }}
                                >{quizLoading ? 'Wird geprüft…' : 'Antworten absenden →'}</button>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}

                {/* Empty video placeholder */}
                {activeLesson.type === 'video' && !activeLesson.content_url && (
                  <div style={{ textAlign: 'center', padding: '40px 0', color: T.textMuted, fontFamily: T.font, fontSize: 13 }}>
                    🎬 Kein Video hinterlegt.
                  </div>
                )}

                {/* File download */}
                {activeLesson.file_url && (
                  <a
                    href={activeLesson.file_url} download target="_blank" rel="noreferrer"
                    style={{
                      display: 'flex', alignItems: 'center', gap: 10, marginTop: 20,
                      padding: '12px 16px', background: T.appBg,
                      border: `1px solid ${T.border}`, borderRadius: '8px',
                      textDecoration: 'none', color: T.textSub, fontSize: 13, fontFamily: T.font,
                    }}
                  >📎 Datei herunterladen</a>
                )}
              </div>

              {/* ── Navigation bar ── */}
              <div style={{
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                paddingTop: 16, borderTop: `1px solid ${T.border}`,
              }}>
                {/* ← Zurück (ghost) */}
                <button
                  onClick={() => prevLesson && setActiveLessonId(prevLesson.id)}
                  disabled={!prevLesson}
                  style={{
                    padding: '9px 18px',
                    background: 'transparent',
                    color: T.textSub,
                    border: `1px solid ${T.border}`,
                    borderRadius: '8px', fontSize: 13, fontWeight: 500,
                    cursor: prevLesson ? 'pointer' : 'default',
                    fontFamily: T.font, opacity: prevLesson ? 1 : 0.35,
                  }}
                >← Zurück</button>

                {/* Complete / done toggle */}
                {activeLesson.type !== 'quiz' && (
                  <button
                    onClick={handleComplete}
                    disabled={completing}
                    style={{
                      padding: '9px 20px',
                      background: lessonDone ? T.successBg : T.primary,
                      color:      lessonDone ? T.successText : '#fff',
                      border: 'none', borderRadius: '8px',
                      fontSize: 13, fontWeight: 600,
                      cursor: 'pointer', fontFamily: T.font,
                      transition: 'opacity 0.15s',
                    }}
                    onMouseEnter={e => e.currentTarget.style.opacity = '0.85'}
                    onMouseLeave={e => e.currentTarget.style.opacity = '1'}
                  >
                    {lessonDone ? '✓ Erledigt' : completing ? 'Speichern…' : 'Als erledigt markieren →'}
                  </button>
                )}

                {/* Weiter → */}
                <button
                  onClick={() => nextLesson && setActiveLessonId(nextLesson.id)}
                  disabled={!nextLesson}
                  style={{
                    padding: '9px 18px',
                    background: nextLesson ? T.primary : 'transparent',
                    color:      nextLesson ? '#fff' : T.textSub,
                    border: nextLesson ? 'none' : `1px solid ${T.border}`,
                    borderRadius: '8px', fontSize: 13, fontWeight: 500,
                    cursor: nextLesson ? 'pointer' : 'default',
                    fontFamily: T.font, opacity: nextLesson ? 1 : 0.35,
                  }}
                >Weiter →</button>
              </div>

              {/* ── Certificate banner (100%) ── */}
              {overallPct === 100 && (
                <div style={{
                  background: T.successBg,
                  border: `1px solid #bbf7d0`,
                  borderRadius: T.radiusLg,
                  padding: '20px 24px',
                  display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 16,
                }}>
                  <div>
                    <div style={{ fontSize: 14, fontWeight: 700, color: T.successText, marginBottom: 3, fontFamily: T.font }}>
                      🏆 Kurs abgeschlossen!
                    </div>
                    <div style={{ fontSize: 12, color: T.successText, fontFamily: T.font }}>
                      Du kannst jetzt dein Zertifikat erstellen.
                    </div>
                  </div>
                  <button
                    onClick={handleCertificate}
                    style={{
                      padding: '9px 20px', background: T.successText, color: '#fff',
                      border: 'none', borderRadius: '8px', fontSize: 13, fontWeight: 600,
                      cursor: 'pointer', fontFamily: T.font, flexShrink: 0,
                    }}
                  >Zertifikat erstellen →</button>
                </div>
              )}
            </>

          ) : (
            /* No lesson selected */
            <div style={{ textAlign: 'center', padding: '80px 20px' }}>
              <div style={{ fontSize: 48, marginBottom: 14, opacity: 0.2 }}>📚</div>
              <div style={{ fontSize: 14, color: T.textSub, fontFamily: T.font }}>
                Wähle eine Lektion im Inhaltsverzeichnis aus.
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Responsive styles */}
      <style>{`
        @media (max-width: 768px) {
          .ac-mobile-toggle { display: flex !important; }
          .ac-sidebar:not(.open) { display: none !important; }
          .ac-content { width: 100% !important; }
        }
      `}</style>
    </>
  );
}

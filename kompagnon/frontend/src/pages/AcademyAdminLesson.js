import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import API_BASE_URL from '../config';

// ── Shared styles ──────────────────────────────────────────────

const S = {
  input: {
    width: '100%', padding: '9px 12px',
    border: '1px solid var(--border-medium)',
    borderRadius: 'var(--radius-md)', fontSize: 13,
    fontFamily: 'var(--font-sans)', color: 'var(--text-primary)',
    background: 'var(--bg-surface)', outline: 'none', boxSizing: 'border-box',
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
    fontSize: 14, fontWeight: 600, color: 'var(--text-primary)',
  },
  cardBody: { padding: '20px', display: 'flex', flexDirection: 'column', gap: 16 },
};

function focusOn(e)  { e.target.style.borderColor = 'var(--brand-primary)'; }
function focusOff(e) { e.target.style.borderColor = 'var(--border-medium)'; }

function Field({ label, children }) {
  return (
    <div>
      <label style={S.label}>{label}</label>
      {children}
    </div>
  );
}

// ── Quiz editor ────────────────────────────────────────────────

const EMPTY_QUESTION = () => ({
  _key:    Math.random(),
  question: '',
  answers: [
    { text: '', is_correct: true  },
    { text: '', is_correct: false },
    { text: '', is_correct: false },
    { text: '', is_correct: false },
  ],
});

function QuizEditor({ questions, setQuestions }) {
  const [modal, setModal] = useState(null); // null | { idx, data }

  const openNew = () => setModal({ idx: null, data: EMPTY_QUESTION() });
  const openEdit = (idx) => setModal({ idx, data: JSON.parse(JSON.stringify(questions[idx])) });

  const closeModal = () => setModal(null);

  const saveModal = () => {
    if (!modal) return;
    const q = modal.data;
    setQuestions(prev => {
      const next = [...prev];
      if (modal.idx === null) next.push(q);
      else next[modal.idx] = q;
      return next;
    });
    closeModal();
  };

  const deleteQuestion = (idx) => setQuestions(prev => prev.filter((_, i) => i !== idx));

  const setModalAnswer = (aIdx, field, value) => {
    setModal(prev => {
      const data = { ...prev.data };
      const answers = data.answers.map((a, i) => {
        if (field === 'is_correct') return { ...a, is_correct: i === aIdx };
        if (i === aIdx) return { ...a, [field]: value };
        return a;
      });
      return { ...prev, data: { ...data, answers } };
    });
  };

  return (
    <>
      <div style={S.card}>
        <div style={{ ...S.cardHeader, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <span>Quiz-Fragen</span>
          <span style={{ fontSize: 11, color: 'var(--text-tertiary)', fontWeight: 400 }}>
            {questions.length} {questions.length === 1 ? 'Frage' : 'Fragen'}
          </span>
        </div>
        <div style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 10 }}>
          {questions.length === 0 && (
            <div style={{ fontSize: 12, color: 'var(--text-tertiary)', textAlign: 'center', padding: '16px 0' }}>
              Noch keine Fragen. Klicke auf „+ Frage hinzufügen".
            </div>
          )}

          {questions.map((q, idx) => {
            const correct = q.answers.find(a => a.is_correct);
            return (
              <div key={q._key ?? idx} style={{
                border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)',
                overflow: 'hidden',
              }}>
                {/* Question header */}
                <div style={{
                  padding: '10px 14px', background: 'var(--bg-app)',
                  display: 'flex', alignItems: 'flex-start', gap: 10,
                }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 4 }}>
                      {idx + 1}. {q.question || <span style={{ color: 'var(--text-tertiary)', fontStyle: 'italic' }}>Kein Fragetext</span>}
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                      {q.answers.map((a, ai) => (
                        <div key={ai} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12 }}>
                          {a.is_correct
                            ? <span style={{ color: 'var(--status-success-text)', fontSize: 13 }}>✓</span>
                            : <span style={{ color: 'var(--border-medium)', fontSize: 11 }}>○</span>}
                          <span style={{ color: a.is_correct ? 'var(--status-success-text)' : 'var(--text-secondary)', fontWeight: a.is_correct ? 600 : 400 }}>
                            {a.text || <span style={{ color: 'var(--text-tertiary)', fontStyle: 'italic' }}>Leer</span>}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: 6, flexShrink: 0 }}>
                    <button
                      onClick={() => openEdit(idx)}
                      style={{
                        padding: '4px 9px', background: 'var(--bg-surface)', color: 'var(--text-secondary)',
                        border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-sm)',
                        fontSize: 11, cursor: 'pointer',
                      }}
                    >✏️ Bearbeiten</button>
                    <button
                      onClick={() => deleteQuestion(idx)}
                      style={{
                        padding: '4px 9px', background: 'var(--status-danger-bg)', color: 'var(--status-danger-text)',
                        border: 'none', borderRadius: 'var(--radius-sm)',
                        fontSize: 11, cursor: 'pointer',
                      }}
                    >🗑 Löschen</button>
                  </div>
                </div>
              </div>
            );
          })}

          <button
            onClick={openNew}
            style={{
              alignSelf: 'flex-start', padding: '7px 16px',
              background: 'var(--brand-primary)', color: '#fff',
              border: 'none', borderRadius: 'var(--radius-md)',
              fontSize: 12, fontWeight: 600, cursor: 'pointer', fontFamily: 'var(--font-sans)',
            }}
          >+ Weitere Frage hinzufügen</button>
        </div>
      </div>

      {/* ── Question edit modal ──────────────────────────── */}
      {modal && (
        <>
          <div
            style={{ position: 'fixed', inset: 0, background: 'rgba(15,28,32,0.55)', backdropFilter: 'blur(4px)', zIndex: 1000 }}
            onClick={closeModal}
          />
          <div
            onClick={e => e.stopPropagation()}
            style={{
              position: 'fixed', top: '50%', left: '50%', transform: 'translate(-50%,-50%)',
              background: 'var(--bg-surface)', borderRadius: 'var(--radius-xl)',
              width: 520, maxWidth: '92vw', maxHeight: '90vh', overflowY: 'auto',
              boxShadow: 'var(--shadow-elevated)', zIndex: 1001,
            }}
          >
            {/* Modal header */}
            <div style={{
              padding: '16px 20px', borderBottom: '1px solid var(--border-light)',
              display: 'flex', alignItems: 'center', justifyContent: 'space-between', position: 'sticky', top: 0, background: 'var(--bg-surface)', zIndex: 1,
            }}>
              <span style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' }}>
                {modal.idx === null ? 'Neue Frage' : 'Frage bearbeiten'}
              </span>
              <button onClick={closeModal} style={{ background: 'none', border: 'none', fontSize: 20, cursor: 'pointer', color: 'var(--text-tertiary)', lineHeight: 1, padding: '0 4px' }}>×</button>
            </div>

            <div style={{ padding: 20, display: 'flex', flexDirection: 'column', gap: 16 }}>
              {/* Question text */}
              <Field label="Fragetext">
                <textarea
                  value={modal.data.question}
                  onChange={e => setModal(prev => ({ ...prev, data: { ...prev.data, question: e.target.value } }))}
                  rows={3}
                  placeholder="Wie lautet die Frage?"
                  style={{ ...S.input, resize: 'vertical' }}
                  onFocus={focusOn} onBlur={focusOff}
                />
              </Field>

              {/* Answer options */}
              <div>
                <label style={S.label}>Antwortoptionen — wähle die richtige</label>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {modal.data.answers.map((ans, ai) => (
                    <div key={ai} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      {/* Radio = correct */}
                      <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer', flexShrink: 0 }}>
                        <input
                          type="radio"
                          name="correct-answer"
                          checked={ans.is_correct}
                          onChange={() => setModalAnswer(ai, 'is_correct', true)}
                          style={{ accentColor: 'var(--status-success-text)', width: 16, height: 16 }}
                        />
                      </label>
                      <input
                        value={ans.text}
                        onChange={e => setModalAnswer(ai, 'text', e.target.value)}
                        placeholder={`Antwort ${ai + 1}…`}
                        style={{
                          ...S.input, flex: 1,
                          borderColor: ans.is_correct ? 'var(--status-success-text)' : 'var(--border-medium)',
                          background: ans.is_correct ? 'var(--status-success-bg)' : 'var(--bg-surface)',
                        }}
                        onFocus={focusOn}
                        onBlur={e => { e.target.style.borderColor = ans.is_correct ? 'var(--status-success-text)' : 'var(--border-medium)'; }}
                      />
                      {ans.is_correct && <span style={{ color: 'var(--status-success-text)', fontSize: 16, flexShrink: 0 }}>✓</span>}
                    </div>
                  ))}
                </div>
              </div>

              {/* Modal actions */}
              <div style={{ display: 'flex', gap: 10, paddingTop: 4 }}>
                <button
                  onClick={closeModal}
                  style={{
                    flex: 1, padding: '9px', background: 'var(--bg-app)', color: 'var(--text-primary)',
                    border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)',
                    fontSize: 13, cursor: 'pointer', fontFamily: 'var(--font-sans)',
                  }}
                >Abbrechen</button>
                <button
                  onClick={saveModal}
                  style={{
                    flex: 1, padding: '9px', background: 'var(--brand-primary)', color: '#fff',
                    border: 'none', borderRadius: 'var(--radius-md)',
                    fontSize: 13, fontWeight: 600, cursor: 'pointer', fontFamily: 'var(--font-sans)',
                  }}
                >{modal.idx === null ? 'Hinzufügen' : 'Speichern'}</button>
              </div>
            </div>
          </div>
        </>
      )}
    </>
  );
}

// ── Help card (non-quiz types) ─────────────────────────────────

const TIPS = {
  video: {
    icon: '🎬',
    title: 'Tipps für Video-Lektionen',
    items: [
      'Nutze YouTube-Embed-URLs (youtube.com/embed/…) oder Vimeo.',
      'Halte Videos unter 10 Minuten für bessere Completion-Rates.',
      'Ergänze das Video mit einer kurzen Textbeschreibung.',
      'Empfohlene Auflösung: mindestens 1080p.',
    ],
  },
  text: {
    icon: '📄',
    title: 'Tipps für Text-Lektionen',
    items: [
      'Verwende Überschriften (<h2>, <h3>) für Struktur.',
      'Halte Absätze kurz — 3–5 Sätze pro Block.',
      'Füge Bilder mit <img>-Tags ein.',
      'Fettdruck (<strong>) für wichtige Begriffe.',
    ],
  },
};

function HelpCard({ type }) {
  const tip = TIPS[type] || TIPS.text;
  return (
    <div style={S.card}>
      <div style={S.cardHeader}>{tip.icon} {tip.title}</div>
      <div style={{ padding: '16px 20px' }}>
        <ul style={{ margin: 0, padding: '0 0 0 18px', display: 'flex', flexDirection: 'column', gap: 8 }}>
          {tip.items.map((item, i) => (
            <li key={i} style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.55 }}>{item}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}

// ── Main component ─────────────────────────────────────────────

export default function AcademyAdminLesson() {
  const { lessonId }  = useParams();
  const [search]      = useSearchParams();
  const navigate      = useNavigate();
  const { token, user } = useAuth();
  const h = { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) };

  const isNew     = !lessonId || lessonId === 'new';
  const moduleId  = search.get('moduleId');

  const [loading, setLoading]   = useState(!isNew);
  const [saving,  setSaving]    = useState(false);

  // Breadcrumb context
  const [courseId,   setCourseId]   = useState(null);
  const [courseTitle, setCourseTitle] = useState('');

  // Lesson form
  const [form, setForm] = useState({
    title:            '',
    type:             'text',
    duration_minutes: '',
    content_text:     '',
    video_url:        '',
    file_url:         '',
  });

  // Quiz
  const [questions, setQuestions] = useState([]);

  const setF = (key) => (val) => setForm(prev => ({ ...prev, [key]: val }));

  // ── Load lesson + context ─────────────────────────────────────

  const loadContext = useCallback(async (modId) => {
    try {
      const mod = await fetch(`${API_BASE_URL}/api/academy/modules/${modId}`, { headers: h }).then(r => r.json());
      if (mod.course_id) {
        setCourseId(mod.course_id);
        const course = await fetch(`${API_BASE_URL}/api/academy/courses/${mod.course_id}`, { headers: h }).then(r => r.json());
        setCourseTitle(course.title || `Kurs #${mod.course_id}`);
      }
    } catch (e) { /* breadcrumb optional */ }
  }, []); // eslint-disable-line

  useEffect(() => {
    if (isNew) {
      if (moduleId) loadContext(moduleId);
      return;
    }
    Promise.all([
      fetch(`${API_BASE_URL}/api/academy/lessons/${lessonId}`, { headers: h }).then(r => r.json()),
    ])
      .then(async ([lesson]) => {
        setForm({
          title:            lesson.title            || '',
          type:             lesson.type             || 'text',
          duration_minutes: lesson.duration_minutes || '',
          content_text:     lesson.content_text     || '',
          video_url:        lesson.video_url        || '',
          file_url:         lesson.file_url         || '',
        });
        if (lesson.module_id) await loadContext(lesson.module_id);
        // Load quiz if applicable
        if (lesson.type === 'quiz') {
          try {
            const qData = await fetch(`${API_BASE_URL}/api/academy/lessons/${lessonId}/quiz`, { headers: h }).then(r => r.json());
            if (Array.isArray(qData)) {
              setQuestions(qData.map(q => ({
                _key: Math.random(),
                question: q.question || '',
                answers: (q.answers || []).map(a => ({ text: a.text || '', is_correct: false })),
              })));
            }
          } catch (e) { /* quiz optional */ }
        }
      })
      .catch(() => navigate('/app/akademie/admin'))
      .finally(() => setLoading(false));
  }, [lessonId]); // eslint-disable-line

  // ── Save ──────────────────────────────────────────────────────

  const save = async () => {
    if (!form.title.trim()) return;
    setSaving(true);
    try {
      const body = {
        title:            form.title.trim(),
        type:             form.type,
        duration_minutes: Number(form.duration_minutes) || 0,
        content_text:     form.content_text,
        video_url:        form.video_url,
        file_url:         form.file_url,
      };

      let savedLessonId = isNew ? null : Number(lessonId);

      if (isNew) {
        if (!moduleId) return;
        const res = await fetch(`${API_BASE_URL}/api/academy/modules/${moduleId}/lessons`, {
          method: 'POST', headers: h, body: JSON.stringify(body),
        });
        if (!res.ok) throw new Error();
        const data = await res.json();
        savedLessonId = data.id;
      } else {
        await fetch(`${API_BASE_URL}/api/academy/lessons/${savedLessonId}`, {
          method: 'PUT', headers: h, body: JSON.stringify(body),
        });
      }

      // Save quiz questions
      if (form.type === 'quiz' && savedLessonId) {
        await fetch(`${API_BASE_URL}/api/academy/lessons/${savedLessonId}/quiz/admin`, {
          method: 'POST', headers: h,
          body: JSON.stringify({
            questions: questions.map(q => ({
              question: q.question,
              answers:  q.answers.map(a => ({ text: a.text, is_correct: a.is_correct })),
            })),
          }),
        });
      }

      // Navigate back
      if (courseId) navigate(`/app/akademie/admin/course/${courseId}`);
      else navigate('/app/akademie/admin');

    } catch (e) { console.error(e); }
    finally { setSaving(false); }
  };

  // ── Guard ─────────────────────────────────────────────────────

  if (user?.role !== 'admin') return (
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

  const isQuiz = form.type === 'quiz';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20, maxWidth: 1100, margin: '0 auto', width: '100%' }}>

      {/* ── Topbar ───────────────────────────────────────────── */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        flexWrap: 'wrap', gap: 12,
        paddingBottom: 20, borderBottom: '1px solid var(--border-light)',
      }}>
        {/* Breadcrumb */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13 }}>
          <button
            onClick={() => courseId ? navigate(`/app/akademie/admin/course/${courseId}`) : navigate('/app/akademie/admin')}
            style={{ background: 'none', border: 'none', color: 'var(--text-tertiary)', cursor: 'pointer', padding: 0, fontFamily: 'var(--font-sans)', display: 'flex', alignItems: 'center', gap: 4 }}
          >
            ← {courseTitle ? `${courseTitle} bearbeiten` : 'Kurs bearbeiten'}
          </button>
          <span style={{ color: 'var(--border-medium)' }}>›</span>
          <span style={{ color: 'var(--text-primary)', fontWeight: 500 }}>
            {isNew ? 'Neue Lektion' : form.title || `Lektion #${lessonId}`}
          </span>
        </div>

        {/* Actions */}
        <div style={{ display: 'flex', gap: 8 }}>
          <button
            onClick={() => courseId ? navigate(`/app/akademie/admin/course/${courseId}`) : navigate('/app/akademie/admin')}
            style={{
              padding: '7px 14px', background: 'transparent', color: 'var(--text-secondary)',
              border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)',
              fontSize: 12, cursor: 'pointer', fontFamily: 'var(--font-sans)',
            }}
          >Abbrechen</button>
          <button
            onClick={save}
            disabled={saving || !form.title.trim()}
            style={{
              padding: '7px 20px', background: 'var(--brand-primary)', color: '#fff',
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

      {/* ── 2-column layout ──────────────────────────────────── */}
      <div style={{ display: 'grid', gridTemplateColumns: isQuiz ? '380px 1fr' : '1fr 340px', gap: 20, alignItems: 'start' }}>

        {/* ── LEFT ─────────────────────────────────────────── */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

          {/* KARTE 1 — Lektionsdetails */}
          <div style={S.card}>
            <div style={S.cardHeader}>Lektionsdetails</div>
            <div style={S.cardBody}>
              <Field label="Titel *">
                <input
                  value={form.title}
                  onChange={e => setF('title')(e.target.value)}
                  placeholder="z.B. Einführung in SEO"
                  style={S.input}
                  onFocus={focusOn} onBlur={focusOff}
                />
              </Field>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                <Field label="Typ">
                  <select
                    value={form.type}
                    onChange={e => setF('type')(e.target.value)}
                    style={S.input}
                  >
                    <option value="video">🎬 Video</option>
                    <option value="text">📄 Text</option>
                    <option value="quiz">🧠 Quiz</option>
                  </select>
                </Field>

                <Field label="Dauer (Minuten)">
                  <input
                    type="number"
                    min="0"
                    value={form.duration_minutes}
                    onChange={e => setF('duration_minutes')(e.target.value)}
                    placeholder="z.B. 5"
                    style={S.input}
                    onFocus={focusOn} onBlur={focusOff}
                  />
                </Field>
              </div>
            </div>
          </div>

          {/* KARTE 2 — Typ-spezifischer Inhalt (nur wenn nicht Quiz) */}
          {!isQuiz && (
            <div style={S.card}>
              {form.type === 'video' && (
                <>
                  <div style={S.cardHeader}>🎬 Video-Inhalt</div>
                  <div style={S.cardBody}>
                    <Field label="Video-URL (YouTube/Vimeo Embed)">
                      <input
                        value={form.video_url}
                        onChange={e => setF('video_url')(e.target.value)}
                        placeholder="https://www.youtube.com/embed/…"
                        style={S.input}
                        onFocus={focusOn} onBlur={focusOff}
                      />
                    </Field>

                    {form.video_url && (
                      <div>
                        <label style={S.label}>Vorschau</label>
                        <div style={{ position: 'relative', paddingTop: '56.25%', borderRadius: 'var(--radius-md)', overflow: 'hidden', background: 'var(--bg-app)' }}>
                          <iframe
                            src={form.video_url}
                            title="Video preview"
                            style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', border: 'none' }}
                            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                            allowFullScreen
                          />
                        </div>
                      </div>
                    )}

                    <Field label="Datei-URL (optionaler Download)">
                      <input
                        value={form.file_url}
                        onChange={e => setF('file_url')(e.target.value)}
                        placeholder="https://…/handout.pdf"
                        style={S.input}
                        onFocus={focusOn} onBlur={focusOff}
                      />
                    </Field>
                  </div>
                </>
              )}

              {form.type === 'text' && (
                <>
                  <div style={S.cardHeader}>📄 Textinhalt</div>
                  <div style={S.cardBody}>
                    <Field label="Inhalt (HTML erlaubt)">
                      <textarea
                        value={form.content_text}
                        onChange={e => setF('content_text')(e.target.value)}
                        rows={14}
                        placeholder={'<h2>Einleitung</h2>\n<p>Text hier…</p>'}
                        style={{ ...S.input, resize: 'vertical', fontFamily: 'var(--font-mono)', fontSize: 12, lineHeight: 1.65 }}
                        onFocus={focusOn} onBlur={focusOff}
                      />
                    </Field>

                    {form.content_text && (
                      <div>
                        <label style={S.label}>Vorschau</label>
                        <div
                          style={{
                            padding: '14px 16px',
                            background: 'var(--bg-app)', borderRadius: 'var(--radius-md)',
                            border: '1px solid var(--border-light)',
                            fontSize: 13, color: 'var(--text-primary)', lineHeight: 1.65,
                          }}
                          dangerouslySetInnerHTML={{ __html: form.content_text }}
                        />
                      </div>
                    )}
                  </div>
                </>
              )}
            </div>
          )}
        </div>

        {/* ── RIGHT ────────────────────────────────────────── */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16, position: 'sticky', top: 20 }}>
          {isQuiz
            ? <QuizEditor questions={questions} setQuestions={setQuestions} />
            : <HelpCard type={form.type} />
          }
        </div>
      </div>
    </div>
  );
}

import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import API_BASE_URL from '../config';

const inputStyle = {
  width: '100%', padding: '9px 12px', border: '1px solid var(--border-medium)',
  borderRadius: 'var(--radius-md)', fontSize: 13, fontFamily: 'var(--font-sans)',
  color: 'var(--text-primary)', background: 'var(--bg-surface)', outline: 'none', boxSizing: 'border-box',
};

const labelStyle = {
  display: 'block', fontSize: 10, fontWeight: 600, color: 'var(--text-tertiary)',
  textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 5,
};

function LessonForm({ lesson, onSave, onDelete, onMove, isFirst, isLast }) {
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({
    title: lesson.title || '',
    content_text: lesson.content_text || '',
    video_url: lesson.video_url || '',
    file_url: lesson.file_url || '',
    checklist_items: lesson.checklist_items || [],
  });
  const [saving, setSaving] = useState(false);

  const save = async () => {
    setSaving(true);
    try {
      await onSave(lesson.id, form);
    } finally { setSaving(false); }
  };

  const addChecklistItem = () => setForm(p => ({ ...p, checklist_items: [...p.checklist_items, ''] }));
  const removeChecklistItem = (i) => setForm(p => ({ ...p, checklist_items: p.checklist_items.filter((_, j) => j !== i) }));
  const updateChecklistItem = (i, val) => setForm(p => ({ ...p, checklist_items: p.checklist_items.map((v, j) => j === i ? val : v) }));

  return (
    <div style={{ border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)', overflow: 'hidden', background: 'var(--bg-surface)' }}>
      {/* Lesson header row */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '10px 12px', background: 'var(--bg-app)', cursor: 'pointer' }}
        onClick={() => setOpen(o => !o)}>
        {/* Sort arrows */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 2, flexShrink: 0 }} onClick={e => e.stopPropagation()}>
          <button onClick={() => onMove(-1)} disabled={isFirst} style={{ padding: '1px 5px', background: 'none', border: '1px solid var(--border-medium)', borderRadius: 3, fontSize: 10, cursor: 'pointer', opacity: isFirst ? 0.3 : 1 }}>▲</button>
          <button onClick={() => onMove(1)} disabled={isLast} style={{ padding: '1px 5px', background: 'none', border: '1px solid var(--border-medium)', borderRadius: 3, fontSize: 10, cursor: 'pointer', opacity: isLast ? 0.3 : 1 }}>▼</button>
        </div>
        <span style={{ flex: 1, fontSize: 13, fontWeight: 500, color: 'var(--text-primary)' }}>
          {form.title || <span style={{ color: 'var(--text-tertiary)' }}>Ohne Titel</span>}
        </span>
        <span style={{ fontSize: 11, color: 'var(--text-tertiary)', marginRight: 4 }}>{open ? '▲' : '▼'}</span>
        <button
          onClick={e => { e.stopPropagation(); onDelete(lesson.id); }}
          style={{ padding: '4px 8px', background: 'var(--status-danger-bg)', color: 'var(--status-danger-text)', border: 'none', borderRadius: 'var(--radius-sm)', fontSize: 11, cursor: 'pointer', flexShrink: 0 }}
        >✕</button>
      </div>

      {/* Collapsible form */}
      {open && (
        <div style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div>
            <label style={labelStyle}>Titel</label>
            <input value={form.title} onChange={e => setForm(p => ({ ...p, title: e.target.value }))} placeholder="Lektionstitel..." style={inputStyle} />
          </div>

          <div>
            <label style={labelStyle}>Textinhalt (HTML erlaubt)</label>
            <textarea
              value={form.content_text}
              onChange={e => setForm(p => ({ ...p, content_text: e.target.value }))}
              rows={6}
              placeholder="<p>Einleitung...</p>"
              style={{ ...inputStyle, resize: 'vertical', fontFamily: 'var(--font-mono)', fontSize: 12, lineHeight: 1.6 }}
            />
          </div>

          <div>
            <label style={labelStyle}>Video-URL (YouTube/Vimeo Embed)</label>
            <input value={form.video_url} onChange={e => setForm(p => ({ ...p, video_url: e.target.value }))} placeholder="https://www.youtube.com/embed/..." style={inputStyle} />
          </div>

          <div>
            <label style={labelStyle}>Datei-URL (Download)</label>
            <input value={form.file_url} onChange={e => setForm(p => ({ ...p, file_url: e.target.value }))} placeholder="https://..." style={inputStyle} />
          </div>

          {/* Checklist items */}
          <div>
            <label style={labelStyle}>Checklisten-Punkte</label>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {form.checklist_items.map((item, i) => (
                <div key={i} style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                  <span style={{ fontSize: 11, color: 'var(--text-tertiary)', width: 20, textAlign: 'center', flexShrink: 0 }}>{i + 1}</span>
                  <input value={item} onChange={e => updateChecklistItem(i, e.target.value)} placeholder={`Punkt ${i + 1}...`} style={{ ...inputStyle, flex: 1 }} />
                  <button onClick={() => removeChecklistItem(i)} style={{ padding: '6px 8px', background: 'var(--status-danger-bg)', color: 'var(--status-danger-text)', border: 'none', borderRadius: 'var(--radius-sm)', fontSize: 11, cursor: 'pointer', flexShrink: 0 }}>✕</button>
                </div>
              ))}
              <button onClick={addChecklistItem} style={{
                padding: '6px 12px', background: 'var(--bg-app)', color: 'var(--brand-primary)',
                border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)',
                fontSize: 12, cursor: 'pointer', fontFamily: 'var(--font-sans)', alignSelf: 'flex-start',
              }}>+ Punkt hinzufügen</button>
            </div>
          </div>

          <div>
            <button onClick={save} disabled={saving} style={{
              padding: '8px 20px', background: 'var(--brand-primary)', color: 'white', border: 'none',
              borderRadius: 'var(--radius-md)', fontSize: 12, fontWeight: 600, cursor: 'pointer',
              fontFamily: 'var(--font-sans)', opacity: saving ? 0.6 : 1,
            }}>{saving ? 'Speichert...' : 'Lektion speichern'}</button>
          </div>
        </div>
      )}
    </div>
  );
}

export default function AcademyModuleEdit() {
  const { moduleId } = useParams();
  const { token, user, hasRole } = useAuth();
  const navigate = useNavigate();
  const h = { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) };

  const [module, setModule] = useState(null);
  const [course, setCourse] = useState(null);
  const [lessons, setLessons] = useState([]);
  const [loading, setLoading] = useState(true);
  const [moduleTitle, setModuleTitle] = useState('');
  const [savingTitle, setSavingTitle] = useState(false);

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/academy/modules/${moduleId}`, { headers: h })
      .then(r => r.json())
      .then(async modData => {
        setModule(modData);
        setModuleTitle(modData.title || '');
        const [courseData, lessonsData] = await Promise.all([
          fetch(`${API_BASE_URL}/api/academy/courses/${modData.course_id}`, { headers: h }).then(r => r.json()),
          fetch(`${API_BASE_URL}/api/academy/modules/${moduleId}/lessons`, { headers: h }).then(r => r.json()),
        ]);
        setCourse(courseData);
        setLessons(Array.isArray(lessonsData) ? lessonsData : []);
      })
      .catch(() => navigate('/app/akademie/admin'))
      .finally(() => setLoading(false));
  }, [moduleId]); // eslint-disable-line

  const saveModuleTitle = async () => {
    if (!moduleTitle.trim()) return;
    setSavingTitle(true);
    try {
      await fetch(`${API_BASE_URL}/api/academy/modules/${moduleId}`, {
        method: 'PUT', headers: h, body: JSON.stringify({ title: moduleTitle }),
      });
      setModule(p => ({ ...p, title: moduleTitle }));
    } catch (e) { console.error(e); }
    finally { setSavingTitle(false); }
  };

  const addLesson = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/academy/modules/${moduleId}/lessons`, {
        method: 'POST', headers: h,
        body: JSON.stringify({ title: 'Neue Lektion', sort_order: lessons.length }),
      });
      const newLesson = await res.json();
      setLessons(prev => [...prev, newLesson]);
    } catch (e) { console.error(e); }
  };

  const saveLesson = async (lessonId, data) => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/academy/lessons/${lessonId}`, {
        method: 'PUT', headers: h, body: JSON.stringify(data),
      });
      const updated = await res.json();
      setLessons(prev => prev.map(l => l.id === lessonId ? updated : l));
    } catch (e) { console.error(e); }
  };

  const deleteLesson = async (lessonId) => {
    if (!window.confirm('Lektion löschen?')) return;
    try {
      await fetch(`${API_BASE_URL}/api/academy/lessons/${lessonId}`, { method: 'DELETE', headers: h });
      setLessons(prev => prev.filter(l => l.id !== lessonId));
    } catch (e) { console.error(e); }
  };

  const moveLesson = async (idx, dir) => {
    const newLessons = [...lessons];
    const target = idx + dir;
    if (target < 0 || target >= newLessons.length) return;
    [newLessons[idx], newLessons[target]] = [newLessons[target], newLessons[idx]];
    const updated = newLessons.map((l, i) => ({ ...l, sort_order: i }));
    setLessons(updated);
    try {
      await Promise.all(updated.map(l =>
        fetch(`${API_BASE_URL}/api/academy/lessons/${l.id}`, {
          method: 'PUT', headers: h, body: JSON.stringify({ sort_order: l.sort_order }),
        })
      ));
    } catch (e) { console.error(e); }
  };

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

  return (
    <div style={{ maxWidth: 800, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 16 }}>
      {/* Breadcrumb */}
      <nav style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>
        <Link to="/app/akademie" style={{ color: 'var(--brand-primary)', textDecoration: 'none' }}>Akademie</Link>
        {' › '}
        <Link to="/app/akademie/admin" style={{ color: 'var(--brand-primary)', textDecoration: 'none' }}>Kurse verwalten</Link>
        {course && <>{' › '}<Link to={`/app/akademie/admin/${course.id}`} style={{ color: 'var(--brand-primary)', textDecoration: 'none' }}>{course.title}</Link></>}
        {' › '}
        <span style={{ color: 'var(--text-secondary)' }}>{module?.title}</span>
      </nav>

      {/* Module title */}
      <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', padding: 20 }}>
        <label style={labelStyle}>Modultitel</label>
        <div style={{ display: 'flex', gap: 8 }}>
          <input value={moduleTitle} onChange={e => setModuleTitle(e.target.value)} style={{ ...inputStyle, flex: 1 }} />
          <button onClick={saveModuleTitle} disabled={savingTitle} style={{
            padding: '9px 16px', background: 'var(--brand-primary)', color: 'white', border: 'none',
            borderRadius: 'var(--radius-md)', fontSize: 12, fontWeight: 500, cursor: 'pointer',
            fontFamily: 'var(--font-sans)', opacity: savingTitle ? 0.6 : 1,
          }}>{savingTitle ? '...' : 'Speichern'}</button>
        </div>
      </div>

      {/* Lessons list */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <h3 style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)', margin: 0 }}>Lektionen ({lessons.length})</h3>
        <button onClick={addLesson} style={{
          padding: '7px 14px', background: 'var(--brand-primary)', color: 'white', border: 'none',
          borderRadius: 'var(--radius-md)', fontSize: 12, fontWeight: 500, cursor: 'pointer', fontFamily: 'var(--font-sans)',
        }}>+ Neue Lektion</button>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {lessons.length === 0 && (
          <div style={{ textAlign: 'center', padding: '24px', color: 'var(--text-tertiary)', fontSize: 13, background: 'var(--bg-surface)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-light)' }}>
            Noch keine Lektionen. Klicke auf "+ Neue Lektion".
          </div>
        )}
        {lessons.map((lesson, idx) => (
          <LessonForm
            key={lesson.id}
            lesson={lesson}
            onSave={saveLesson}
            onDelete={deleteLesson}
            onMove={(dir) => moveLesson(idx, dir)}
            isFirst={idx === 0}
            isLast={idx === lessons.length - 1}
          />
        ))}
      </div>
    </div>
  );
}

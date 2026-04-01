import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Badge from '../components/ui/Badge';
import API_BASE_URL from '../config';

const BADGE_MAP = {
  primary: 'info', warning: 'warning', success: 'success', danger: 'danger', info: 'info', secondary: 'neutral',
};

export default function AcademyAdmin() {
  const navigate = useNavigate();
  const { token, user } = useAuth();
  const h = { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) };

  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [deleteId, setDeleteId] = useState(null);

  useEffect(() => { loadCourses(); }, []); // eslint-disable-line

  const loadCourses = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/academy/courses`, { headers: h });
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

  const moveCourse = async (id, direction) => {
    const idx = courses.findIndex(c => c.id === id);
    if (idx < 0) return;
    const targetIdx = direction === 'up' ? idx - 1 : idx + 1;
    if (targetIdx < 0 || targetIdx >= courses.length) return;

    const reordered = [...courses];
    [reordered[idx], reordered[targetIdx]] = [reordered[targetIdx], reordered[idx]];
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

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16, maxWidth: 900, margin: '0 auto', width: '100%' }}>

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 10 }}>
        <div>
          <h2 style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-primary)', margin: '0 0 4px' }}>Kurse verwalten</h2>
          <div style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>{courses.length} Kurse · Reihenfolge mit Pfeilen ändern</div>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button onClick={() => navigate('/app/akademie')} style={{
            padding: '7px 14px', background: 'transparent', color: 'var(--text-secondary)',
            border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)',
            fontSize: 12, cursor: 'pointer', fontFamily: 'var(--font-sans)',
          }}>← Zurück</button>
          <button onClick={() => navigate('/app/akademie/admin/neu')} style={{
            padding: '7px 14px', background: 'var(--brand-primary)', color: 'white',
            border: 'none', borderRadius: 'var(--radius-md)',
            fontSize: 12, fontWeight: 600, cursor: 'pointer', fontFamily: 'var(--font-sans)',
          }}>+ Neuer Kurs</button>
        </div>
      </div>

      {/* Table */}
      {loading ? (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: 200 }}>
          <div style={{ width: 28, height: 28, borderRadius: '50%', border: '3px solid var(--border-light)', borderTopColor: 'var(--brand-primary)', animation: 'spin 0.8s linear infinite' }} />
        </div>
      ) : (
        <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', overflow: 'hidden' }}>
          {/* Header Row */}
          <div style={{
            display: 'grid', gridTemplateColumns: '40px 1fr 100px 80px 80px 100px',
            gap: 8, padding: '10px 16px', background: 'var(--bg-app)',
            borderBottom: '1px solid var(--border-light)', fontSize: 10, fontWeight: 600,
            color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em',
          }}>
            <span>#</span><span>Kurs</span><span>Kategorie</span><span>Zielgruppe</span><span>Formate</span><span>Aktionen</span>
          </div>

          {courses.length === 0 ? (
            <div style={{ textAlign: 'center', padding: 40, color: 'var(--text-tertiary)', fontSize: 13 }}>Keine Kurse vorhanden</div>
          ) : courses.map((course, idx) => (
            <div key={course.id} style={{
              display: 'grid', gridTemplateColumns: '40px 1fr 100px 80px 80px 100px',
              gap: 8, padding: '10px 16px', alignItems: 'center',
              borderBottom: idx < courses.length - 1 ? '1px solid var(--border-light)' : 'none',
              transition: 'background 0.1s',
            }}
            onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-hover)'}
            onMouseLeave={e => e.currentTarget.style.background = 'transparent'}>

              {/* Sort Arrows */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <button onClick={() => moveCourse(course.id, 'up')} disabled={idx === 0}
                  style={{ background: 'none', border: 'none', cursor: idx === 0 ? 'default' : 'pointer', color: idx === 0 ? 'var(--border-light)' : 'var(--text-tertiary)', fontSize: 10, padding: 0, lineHeight: 1 }}>▲</button>
                <button onClick={() => moveCourse(course.id, 'down')} disabled={idx === courses.length - 1}
                  style={{ background: 'none', border: 'none', cursor: idx === courses.length - 1 ? 'default' : 'pointer', color: idx === courses.length - 1 ? 'var(--border-light)' : 'var(--text-tertiary)', fontSize: 10, padding: 0, lineHeight: 1 }}>▼</button>
              </div>

              {/* Title */}
              <div>
                <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)' }}>{course.title}</div>
                <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {course.description?.substring(0, 60)}{(course.description?.length || 0) > 60 ? '...' : ''}
                </div>
              </div>

              {/* Category */}
              <Badge variant={BADGE_MAP[course.category_color] || 'neutral'}>{course.category}</Badge>

              {/* Audience */}
              <span style={{ fontSize: 11, color: 'var(--text-secondary)' }}>
                {course.audience === 'employee' ? 'Intern' : 'Kunde'}
              </span>

              {/* Formats */}
              <div style={{ display: 'flex', gap: 4, fontSize: 12 }}>
                {(course.formats || []).includes('text') && <span title="Text">📄</span>}
                {(course.formats || []).includes('video') && <span title="Video">🎬</span>}
                {(course.formats || []).includes('checklist') && <span title="Checkliste">✅</span>}
              </div>

              {/* Actions */}
              <div style={{ display: 'flex', gap: 4 }}>
                <button onClick={() => navigate(`/app/akademie/admin/${course.id}`)} style={{
                  padding: '4px 8px', background: 'var(--bg-app)', color: 'var(--text-secondary)',
                  border: '1px solid var(--border-light)', borderRadius: 'var(--radius-sm)',
                  fontSize: 11, cursor: 'pointer', fontFamily: 'var(--font-sans)',
                }}>✏️</button>
                <button onClick={() => setDeleteId(course.id)} style={{
                  padding: '4px 8px', background: 'var(--status-danger-bg)', color: 'var(--status-danger-text)',
                  border: '1px solid var(--status-danger-bg)', borderRadius: 'var(--radius-sm)',
                  fontSize: 11, cursor: 'pointer', fontFamily: 'var(--font-sans)',
                }}>🗑️</button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Delete Modal */}
      {deleteId && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(15,28,32,0.5)', backdropFilter: 'blur(4px)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}
          onClick={() => setDeleteId(null)}>
          <div onClick={e => e.stopPropagation()} style={{
            background: 'var(--bg-surface)', borderRadius: 'var(--radius-xl)', padding: 28,
            maxWidth: 380, width: '100%', textAlign: 'center', boxShadow: '0 20px 60px rgba(0,0,0,0.15)',
          }}>
            <div style={{ width: 48, height: 48, borderRadius: '50%', background: 'var(--status-danger-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 22, margin: '0 auto 14px' }}>🗑️</div>
            <h3 style={{ fontSize: 16, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 8 }}>Kurs löschen?</h3>
            <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 20, lineHeight: 1.5 }}>
              <strong>{courses.find(c => c.id === deleteId)?.title}</strong> wird dauerhaft gelöscht.
            </p>
            <div style={{ display: 'flex', gap: 10 }}>
              <button onClick={() => setDeleteId(null)} style={{
                flex: 1, padding: '9px', background: 'var(--bg-app)', color: 'var(--text-primary)',
                border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)',
                fontSize: 13, cursor: 'pointer', fontFamily: 'var(--font-sans)',
              }}>Abbrechen</button>
              <button onClick={() => deleteCourse(deleteId)} style={{
                flex: 1, padding: '9px', background: 'var(--status-danger-bg)', color: 'var(--status-danger-text)',
                border: '1px solid var(--status-danger-bg)', borderRadius: 'var(--radius-md)',
                fontSize: 13, fontWeight: 600, cursor: 'pointer', fontFamily: 'var(--font-sans)',
              }}>Löschen</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

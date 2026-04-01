import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Badge from '../components/ui/Badge';
import API_BASE_URL from '../config';

const BADGE_MAP = {
  primary: 'info', warning: 'warning', success: 'success', danger: 'danger', info: 'info', secondary: 'neutral',
};

export default function AcademyCourse() {
  const { kursId } = useParams();
  const navigate = useNavigate();
  const { token } = useAuth();
  const h = { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) };

  const [course, setCourse] = useState(null);
  const [loading, setLoading] = useState(true);
  const [checked, setChecked] = useState({});
  const [activeTab, setActiveTab] = useState('text');

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/academy/courses/${kursId}`, { headers: h })
      .then(r => { if (!r.ok) throw new Error(); return r.json(); })
      .then(data => {
        setCourse(data);
        const fmts = data.formats || [];
        setActiveTab(fmts[0] || 'text');
      })
      .catch(() => setCourse(null))
      .finally(() => setLoading(false));
  }, [kursId]); // eslint-disable-line

  if (loading) return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '40vh' }}>
      <div style={{ width: 28, height: 28, borderRadius: '50%', border: '3px solid var(--border-light)', borderTopColor: 'var(--brand-primary)', animation: 'spin 0.8s linear infinite' }} />
    </div>
  );

  if (!course) return (
    <div style={{ textAlign: 'center', padding: '60px 20px' }}>
      <div style={{ fontSize: 48, marginBottom: 16, opacity: 0.4 }}>📚</div>
      <h2 style={{ fontSize: 18, color: 'var(--text-primary)', marginBottom: 8 }}>Kurs nicht gefunden</h2>
      <p style={{ fontSize: 13, color: 'var(--text-tertiary)', marginBottom: 20 }}>Der angeforderte Kurs existiert nicht.</p>
      <button onClick={() => navigate('/app/akademie')} style={{
        padding: '9px 20px', background: 'var(--brand-primary)', color: 'white', border: 'none',
        borderRadius: 'var(--radius-md)', fontSize: 13, fontWeight: 500, cursor: 'pointer', fontFamily: 'var(--font-sans)',
      }}>← Zurück zur Akademie</button>
    </div>
  );

  const formats = course.formats || [];
  const items = course.checklist_items || [];
  const checkedCount = Object.values(checked).filter(Boolean).length;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16, maxWidth: 900, margin: '0 auto', width: '100%' }}>

      {/* Breadcrumb */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: 'var(--text-tertiary)' }}>
        <Link to="/app/akademie" style={{ color: 'var(--brand-primary)', textDecoration: 'none' }}>Akademie</Link>
        <span>›</span>
        <span style={{ color: 'var(--text-secondary)' }}>{course.title}</span>
      </div>

      {/* Header */}
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6, flexWrap: 'wrap' }}>
          <h2 style={{ fontSize: 20, fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>{course.title}</h2>
          <Badge variant={BADGE_MAP[course.category_color] || 'neutral'}>{course.category}</Badge>
        </div>
        <p style={{ fontSize: 13, color: 'var(--text-secondary)', margin: 0, lineHeight: 1.5 }}>{course.description}</p>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 4, background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', padding: 4 }}>
        {formats.includes('text') && (
          <button onClick={() => setActiveTab('text')} style={{
            flex: 1, padding: '8px 12px', borderRadius: 'var(--radius-md)', border: 'none',
            background: activeTab === 'text' ? 'var(--bg-active)' : 'transparent',
            color: activeTab === 'text' ? 'var(--brand-primary)' : 'var(--text-tertiary)',
            fontSize: 12, fontWeight: activeTab === 'text' ? 500 : 400, cursor: 'pointer',
            fontFamily: 'var(--font-sans)', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6,
          }}>📄 Anleitung</button>
        )}
        {formats.includes('video') && (
          <button onClick={() => setActiveTab('video')} style={{
            flex: 1, padding: '8px 12px', borderRadius: 'var(--radius-md)', border: 'none',
            background: activeTab === 'video' ? 'var(--bg-active)' : 'transparent',
            color: activeTab === 'video' ? 'var(--brand-primary)' : 'var(--text-tertiary)',
            fontSize: 12, fontWeight: activeTab === 'video' ? 500 : 400, cursor: 'pointer',
            fontFamily: 'var(--font-sans)', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6,
          }}>🎬 Video</button>
        )}
        {formats.includes('checklist') && (
          <button onClick={() => setActiveTab('checklist')} style={{
            flex: 1, padding: '8px 12px', borderRadius: 'var(--radius-md)', border: 'none',
            background: activeTab === 'checklist' ? 'var(--bg-active)' : 'transparent',
            color: activeTab === 'checklist' ? 'var(--brand-primary)' : 'var(--text-tertiary)',
            fontSize: 12, fontWeight: activeTab === 'checklist' ? 500 : 400, cursor: 'pointer',
            fontFamily: 'var(--font-sans)', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6,
          }}>✅ Checkliste</button>
        )}
      </div>

      {/* Tab Content */}
      <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', overflow: 'hidden' }}>

        {activeTab === 'text' && (
          course.content_text ? (
            <div style={{ padding: '24px', fontSize: 14, color: 'var(--text-primary)', lineHeight: 1.7 }}
              dangerouslySetInnerHTML={{ __html: course.content_text }} />
          ) : (
            <div style={{ padding: '48px 24px', textAlign: 'center', maxWidth: 600, margin: '0 auto' }}>
              <div style={{ fontSize: 48, marginBottom: 16, opacity: 0.3 }}>🔨</div>
              <h3 style={{ fontSize: 16, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 8 }}>Dieser Inhalt wird gerade erstellt</h3>
              <p style={{ fontSize: 13, color: 'var(--text-tertiary)', lineHeight: 1.6 }}>
                Die Anleitung für „{course.title}" wird aktuell vorbereitet und in Kürze hier verfügbar sein.
              </p>
            </div>
          )
        )}

        {activeTab === 'video' && (
          <div style={{ padding: 16 }}>
            {course.video_url ? (
              <div style={{ position: 'relative', paddingBottom: '56.25%', height: 0, borderRadius: 'var(--radius-md)', overflow: 'hidden' }}>
                <iframe src={course.video_url} style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', border: 'none' }}
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowFullScreen title={course.title} />
              </div>
            ) : (
              <div style={{ position: 'relative', paddingBottom: '56.25%', height: 0, background: 'var(--bg-app)', borderRadius: 'var(--radius-md)', overflow: 'hidden' }}>
                <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 12 }}>
                  <div style={{ fontSize: 48, opacity: 0.3 }}>🎬</div>
                  <div style={{ fontSize: 14, color: 'var(--text-tertiary)' }}>Video folgt in Kürze</div>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'checklist' && (
          <div style={{ padding: 16 }}>
            <div style={{ marginBottom: 16 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                <span style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)' }}>{checkedCount} von {items.length} erledigt</span>
                <span style={{ fontSize: 12, color: checkedCount === items.length ? 'var(--status-success-text)' : 'var(--text-tertiary)' }}>
                  {items.length > 0 ? Math.round((checkedCount / items.length) * 100) : 0}%
                </span>
              </div>
              <div style={{ height: 6, background: 'var(--border-light)', borderRadius: 3, overflow: 'hidden' }}>
                <div style={{
                  width: items.length > 0 ? `${(checkedCount / items.length) * 100}%` : '0%', height: '100%',
                  background: checkedCount === items.length ? 'var(--status-success-text)' : 'var(--brand-primary)',
                  borderRadius: 3, transition: 'width 0.3s ease',
                }} />
              </div>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              {items.map((item, i) => {
                const isDone = checked[item.id || i];
                return (
                  <label key={item.id || i} style={{
                    display: 'flex', alignItems: 'center', gap: 12, padding: '10px 12px',
                    borderRadius: 'var(--radius-md)', cursor: 'pointer',
                    background: isDone ? 'var(--status-success-bg)' : 'transparent', transition: 'background 0.15s',
                  }}>
                    <input type="checkbox" checked={!!isDone}
                      onChange={() => setChecked(prev => ({ ...prev, [item.id || i]: !prev[item.id || i] }))}
                      style={{ width: 18, height: 18, accentColor: 'var(--brand-primary)', cursor: 'pointer', flexShrink: 0 }} />
                    <span style={{
                      fontSize: 13, color: isDone ? 'var(--text-tertiary)' : 'var(--text-primary)',
                      textDecoration: isDone ? 'line-through' : 'none', transition: 'all 0.15s',
                    }}>{item.label}</span>
                  </label>
                );
              })}
              {items.length === 0 && (
                <div style={{ textAlign: 'center', padding: 20, color: 'var(--text-tertiary)', fontSize: 13 }}>Keine Checklisten-Punkte vorhanden</div>
              )}
            </div>
          </div>
        )}
      </div>

      <div>
        <button onClick={() => navigate('/app/akademie')} style={{
          padding: '9px 20px', background: 'transparent', color: 'var(--brand-primary)',
          border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)',
          fontSize: 13, cursor: 'pointer', fontFamily: 'var(--font-sans)',
        }}>← Zurück zur Übersicht</button>
      </div>
    </div>
  );
}

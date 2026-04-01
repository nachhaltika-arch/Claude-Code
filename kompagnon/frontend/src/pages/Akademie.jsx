import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Badge from '../components/ui/Badge';
import API_BASE_URL from '../config';

const BADGE_MAP = {
  primary: 'info', warning: 'warning', success: 'success', danger: 'danger', info: 'info', secondary: 'neutral',
};

export default function Akademie() {
  const navigate = useNavigate();
  const { user, token } = useAuth();
  const isInternal = user?.role === 'admin' || user?.role === 'auditor';
  const [viewMode, setViewMode] = useState(isInternal ? 'employee' : 'customer');
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);

  const h = { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) };

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/academy/courses`, { headers: h })
      .then(r => r.json())
      .then(data => setCourses(Array.isArray(data) ? data : []))
      .catch(e => console.error(e))
      .finally(() => setLoading(false));
  }, []); // eslint-disable-line

  const filtered = courses.filter(c => c.audience === viewMode);
  const heading = viewMode === 'employee' ? 'Interne Schulungen' : 'Ihr Projekt verstehen';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

      {/* Hero Banner */}
      <div style={{
        background: 'var(--brand-primary)', borderRadius: 'var(--radius-xl)',
        padding: '40px 24px', textAlign: 'center', color: 'white',
      }}>
        <div style={{ fontSize: 40, marginBottom: 12 }}>🎓</div>
        <h1 style={{ fontSize: 28, fontWeight: 700, color: 'white', margin: '0 0 8px', letterSpacing: '-0.01em' }}>
          KOMPAGNON Akademie
        </h1>
        <p style={{ fontSize: 15, color: 'rgba(255,255,255,0.75)', margin: 0 }}>
          Ihr Wissenshub für digitale Sichtbarkeit
        </p>

        {isInternal && (
          <div style={{ marginTop: 20, display: 'flex', gap: 6, justifyContent: 'center' }}>
            {[{ id: 'employee', label: 'Interne Schulungen' }, { id: 'customer', label: 'Kundenansicht' }].map(v => (
              <button key={v.id} onClick={() => setViewMode(v.id)} style={{
                padding: '7px 16px', borderRadius: 'var(--radius-full)', border: 'none',
                background: viewMode === v.id ? 'rgba(255,255,255,0.25)' : 'rgba(255,255,255,0.08)',
                color: 'white', fontSize: 12, fontWeight: viewMode === v.id ? 600 : 400,
                cursor: 'pointer', fontFamily: 'var(--font-sans)', transition: 'all 0.15s',
              }}>{v.label}</button>
            ))}
          </div>
        )}
      </div>

      {/* Section Heading */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ fontSize: 16, fontWeight: 600, color: 'var(--text-primary)' }}>{heading}</div>
        {user?.role === 'admin' && (
          <button onClick={() => navigate('/app/akademie/admin')} style={{
            padding: '6px 14px', background: 'var(--bg-app)', color: 'var(--text-secondary)',
            border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)',
            fontSize: 11, fontWeight: 500, cursor: 'pointer', fontFamily: 'var(--font-sans)',
          }}>⚙️ Kurse verwalten</button>
        )}
      </div>

      {/* Course Grid */}
      {loading ? (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: 200 }}>
          <div style={{ width: 28, height: 28, borderRadius: '50%', border: '3px solid var(--border-light)', borderTopColor: 'var(--brand-primary)', animation: 'spin 0.8s linear infinite' }} />
        </div>
      ) : filtered.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '60px 20px', color: 'var(--text-tertiary)' }}>
          <div style={{ fontSize: 48, marginBottom: 12, opacity: 0.4 }}>🔨</div>
          <div style={{ fontSize: 14 }}>Inhalte werden vorbereitet</div>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 16 }}>
          {filtered.map(course => (
            <div key={course.id} className="academy-card" style={{
              background: 'var(--bg-surface)', border: '1px solid var(--border-light)',
              borderRadius: 'var(--radius-lg)', boxShadow: 'var(--shadow-card)',
              display: 'flex', flexDirection: 'column', overflow: 'hidden',
            }}>
              <div style={{ padding: '12px 16px', borderBottom: '1px solid var(--border-light)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: 'var(--bg-app)' }}>
                <Badge variant={BADGE_MAP[course.category_color] || 'neutral'}>{course.category}</Badge>
                <div style={{ display: 'flex', gap: 6, color: 'var(--text-tertiary)', fontSize: 13 }}>
                  {(course.formats || []).includes('text') && <span title="Text">📄</span>}
                  {(course.formats || []).includes('video') && <span title="Video">🎬</span>}
                  {(course.formats || []).includes('checklist') && <span title="Checkliste">✅</span>}
                </div>
              </div>
              <div style={{ padding: 16, flex: 1, display: 'flex', flexDirection: 'column', gap: 10 }}>
                <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>{course.title}</div>
                <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.5, flex: 1 }}>{course.description}</div>
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                    <span style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>Noch nicht gestartet</span>
                    <span style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>0%</span>
                  </div>
                  <div style={{ height: 4, background: 'var(--border-light)', borderRadius: 2, overflow: 'hidden' }}>
                    <div style={{ width: '0%', height: '100%', background: 'var(--brand-primary)', borderRadius: 2 }} />
                  </div>
                </div>
              </div>
              <div style={{ padding: '12px 16px', borderTop: '1px solid var(--border-light)' }}>
                <button onClick={() => navigate(`/app/akademie/kurs/${course.id}`)} style={{
                  width: '100%', padding: '8px 14px', background: 'var(--brand-primary)', color: 'white', border: 'none',
                  borderRadius: 'var(--radius-md)', fontSize: 12, fontWeight: 600, cursor: 'pointer', fontFamily: 'var(--font-sans)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6,
                }}>Kurs starten →</button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

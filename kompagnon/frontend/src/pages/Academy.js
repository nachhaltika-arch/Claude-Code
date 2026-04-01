import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import API_BASE_URL from '../config';

const AUDIENCE_LABEL = { employee: 'Für Mitarbeiter', customer: 'Für Kunden', both: 'Für alle' };
const AUDIENCE_COLOR = { employee: '#7c3aed', customer: '#0891b2', both: '#059669' };

export default function Academy() {
  const navigate = useNavigate();
  const { user, token } = useAuth();
  const isInternal = user?.role === 'admin' || user?.role === 'auditor';
  const h = { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) };

  const [courses, setCourses] = useState([]);
  const [progressMap, setProgressMap] = useState({});
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all'); // all | mine | done

  useEffect(() => {
    const uid = user?.id;
    Promise.all([
      fetch(`${API_BASE_URL}/api/academy/courses`, { headers: h }).then(r => r.json()),
      uid
        ? fetch(`${API_BASE_URL}/api/academy/progress/all?user_id=${uid}`, { headers: h }).then(r => r.json())
        : Promise.resolve({}),
    ])
      .then(([data, pMap]) => {
        setCourses(Array.isArray(data) ? data : []);
        setProgressMap(pMap || {});
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []); // eslint-disable-line

  const visible = courses.filter(c => {
    const aud = c.target_audience || c.audience;
    const roleMatch = isInternal
      ? aud === 'employee' || aud === 'both'
      : aud === 'customer' || aud === 'both';
    if (!roleMatch) return false;
    if (filter === 'mine') {
      const p = progressMap[c.id];
      return p && p.completed > 0;
    }
    if (filter === 'done') {
      const p = progressMap[c.id];
      return p && p.progress_pct === 100;
    }
    return true;
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>

      {/* Hero */}
      <div style={{
        background: 'linear-gradient(135deg, var(--brand-primary) 0%, #1e3a5f 100%)',
        borderRadius: 'var(--radius-xl)', padding: '48px 32px', color: 'white',
        position: 'relative', overflow: 'hidden',
      }}>
        <div style={{ position: 'absolute', top: -40, right: -40, width: 200, height: 200, borderRadius: '50%', background: 'rgba(255,255,255,0.04)' }} />
        <div style={{ position: 'absolute', bottom: -60, right: 80, width: 160, height: 160, borderRadius: '50%', background: 'rgba(255,255,255,0.03)' }} />
        <div style={{ position: 'relative' }}>
          <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.12em', textTransform: 'uppercase', color: 'rgba(255,255,255,0.55)', marginBottom: 8 }}>
            KOMPAGNON
          </div>
          <h1 style={{ fontSize: 32, fontWeight: 800, color: 'white', margin: '0 0 10px', letterSpacing: '-0.02em' }}>
            Akademy
          </h1>
          <p style={{ fontSize: 15, color: 'rgba(255,255,255,0.7)', margin: 0, maxWidth: 480 }}>
            {isInternal
              ? 'Schulungen, Prozess-Guides und internes Wissen für das KOMPAGNON-Team.'
              : 'Ihr Wissenshub für digitale Sichtbarkeit — Ihr Projekt verstehen und meistern.'}
          </p>
        </div>
      </div>

      {/* Toolbar */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
        <div style={{ display: 'flex', gap: 6 }}>
          {[
            { id: 'all', label: 'Alle Kurse' },
            { id: 'mine', label: 'Gestartet' },
            { id: 'done', label: 'Abgeschlossen' },
          ].map(f => (
            <button key={f.id} onClick={() => setFilter(f.id)} style={{
              padding: '6px 14px', borderRadius: 'var(--radius-full)',
              border: filter === f.id ? 'none' : '1px solid var(--border-medium)',
              background: filter === f.id ? 'var(--brand-primary)' : 'var(--bg-surface)',
              color: filter === f.id ? 'white' : 'var(--text-secondary)',
              fontSize: 12, fontWeight: filter === f.id ? 600 : 400, cursor: 'pointer',
              fontFamily: 'var(--font-sans)', transition: 'all 0.15s',
            }}>{f.label}</button>
          ))}
        </div>
        {user?.role === 'admin' && (
          <button onClick={() => navigate('/app/akademie/admin')} style={{
            padding: '6px 14px', background: 'var(--bg-app)', color: 'var(--text-secondary)',
            border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)',
            fontSize: 11, fontWeight: 500, cursor: 'pointer', fontFamily: 'var(--font-sans)',
          }}>⚙️ Kurse verwalten</button>
        )}
      </div>

      {/* Grid */}
      {loading ? (
        <div style={{ display: 'flex', justifyContent: 'center', padding: '80px 0' }}>
          <div style={{ width: 32, height: 32, borderRadius: '50%', border: '3px solid var(--border-light)', borderTopColor: 'var(--brand-primary)', animation: 'spin 0.8s linear infinite' }} />
        </div>
      ) : visible.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '80px 20px', color: 'var(--text-tertiary)' }}>
          <div style={{ fontSize: 56, marginBottom: 16, opacity: 0.3 }}>🎓</div>
          <div style={{ fontSize: 15, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 6 }}>
            {filter === 'done' ? 'Noch kein Kurs abgeschlossen' : filter === 'mine' ? 'Noch kein Kurs gestartet' : 'Keine Kurse verfügbar'}
          </div>
          <div style={{ fontSize: 13 }}>Inhalte werden vorbereitet</div>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 20 }}>
          {visible.map(course => {
            const p = progressMap[course.id];
            const pct = p?.progress_pct || 0;
            const started = p && p.completed > 0;
            const done = pct === 100;
            const aud = course.target_audience || course.audience;
            return (
              <div key={course.id} style={{
                background: 'var(--bg-surface)', border: '1px solid var(--border-light)',
                borderRadius: 'var(--radius-lg)', boxShadow: 'var(--shadow-card)',
                display: 'flex', flexDirection: 'column', overflow: 'hidden',
                transition: 'box-shadow 0.2s, transform 0.2s',
                cursor: 'pointer',
              }}
                onClick={() => navigate(`/app/akademie/kurs/${course.id}`)}
                onMouseEnter={e => { e.currentTarget.style.boxShadow = 'var(--shadow-lg, 0 8px 24px rgba(0,0,0,0.12))'; e.currentTarget.style.transform = 'translateY(-2px)'; }}
                onMouseLeave={e => { e.currentTarget.style.boxShadow = 'var(--shadow-card)'; e.currentTarget.style.transform = 'none'; }}
              >
                {/* Thumbnail */}
                <div style={{
                  height: 140, background: course.thumbnail_url
                    ? `url(${course.thumbnail_url}) center/cover`
                    : 'linear-gradient(135deg, var(--brand-primary) 0%, #1e3a5f 100%)',
                  position: 'relative', flexShrink: 0,
                }}>
                  {done && (
                    <div style={{
                      position: 'absolute', top: 10, right: 10,
                      background: '#16a34a', color: 'white', borderRadius: 'var(--radius-full)',
                      fontSize: 11, fontWeight: 700, padding: '4px 10px',
                    }}>✓ Abgeschlossen</div>
                  )}
                  {!done && started && (
                    <div style={{
                      position: 'absolute', top: 10, right: 10,
                      background: 'rgba(0,0,0,0.55)', color: 'white', borderRadius: 'var(--radius-full)',
                      fontSize: 11, fontWeight: 600, padding: '4px 10px',
                    }}>{pct}% erledigt</div>
                  )}
                  {/* Audience badge */}
                  <div style={{
                    position: 'absolute', bottom: 10, left: 10,
                    background: AUDIENCE_COLOR[aud] || '#64748b', color: 'white',
                    borderRadius: 'var(--radius-full)', fontSize: 10, fontWeight: 700,
                    padding: '3px 8px', letterSpacing: '0.04em',
                  }}>{AUDIENCE_LABEL[aud] || aud}</div>
                  {!course.thumbnail_url && (
                    <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 48, opacity: 0.3 }}>🎓</div>
                  )}
                </div>

                {/* Body */}
                <div style={{ padding: 18, flex: 1, display: 'flex', flexDirection: 'column', gap: 8 }}>
                  <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1.4 }}>{course.title}</div>
                  <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.5, flex: 1 }}>{course.description}</div>

                  {/* Format icons */}
                  <div style={{ display: 'flex', gap: 8, color: 'var(--text-tertiary)', fontSize: 12 }}>
                    {(course.formats || []).includes('text') && <span title="Text">📄 Text</span>}
                    {(course.formats || []).includes('video') && <span title="Video">🎬 Video</span>}
                    {(course.formats || []).includes('checklist') && <span title="Checkliste">✅ Checkliste</span>}
                  </div>

                  {/* Progress bar */}
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                      <span style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>
                        {!p || p.total_lessons === 0 ? 'Noch nicht gestartet' : done ? 'Abgeschlossen' : `${p.completed} von ${p.total_lessons} Lektionen`}
                      </span>
                      <span style={{ fontSize: 10, fontWeight: 600, color: done ? '#16a34a' : 'var(--text-tertiary)' }}>{pct}%</span>
                    </div>
                    <div style={{ height: 5, background: 'var(--border-light)', borderRadius: 3, overflow: 'hidden' }}>
                      <div style={{ width: `${pct}%`, height: '100%', background: done ? '#16a34a' : 'var(--brand-primary)', borderRadius: 3, transition: 'width 0.4s' }} />
                    </div>
                  </div>

                  {/* CTA */}
                  <button style={{
                    marginTop: 4, width: '100%', padding: '9px 14px',
                    background: done ? '#16a34a' : 'var(--brand-primary)',
                    color: 'white', border: 'none', borderRadius: 'var(--radius-md)',
                    fontSize: 12, fontWeight: 700, cursor: 'pointer', fontFamily: 'var(--font-sans)',
                  }}>
                    {done ? '🏆 Zertifikat' : started ? 'Fortsetzen →' : 'Jetzt starten →'}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

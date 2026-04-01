import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import API_BASE_URL from '../config';

// ── Design tokens ──────────────────────────────────────────────
const T = {
  primary:    '#008eaa',
  primaryBg:  '#e0f4f8',
  appBg:      '#f4f6f8',
  surface:    '#ffffff',
  border:     'rgba(0,142,170,0.12)',
  borderMed:  'rgba(0,142,170,0.25)',
  text:       '#0f1c20',
  textSub:    '#4a6470',
  textMuted:  '#8fa8b0',
  radiusLg:   '12px',
  radiusXl:   '16px',
  radiusFull: '9999px',
  shadow:     '0 1px 3px rgba(0,0,0,0.06)',
  font:       "'DM Sans', system-ui, sans-serif",
  successBg:  '#eaf5ee',
  successText:'#1a7a3a',
  certBg:     '#fff8e6',
  certText:   '#a06800',
};

const AUDIENCE_LABEL = {
  employee: 'Für Mitarbeiter',
  customer: 'Für Kunden',
  both:     'Für alle',
};

export default function Academy() {
  const navigate = useNavigate();
  const { user, token } = useAuth();
  const isInternal = user?.role === 'admin' || user?.role === 'auditor';
  const h = { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) };

  const [courses, setCourses]       = useState([]);
  const [progressMap, setProgressMap] = useState({});
  const [loading, setLoading]       = useState(true);
  const [filter, setFilter]         = useState('all'); // all | mine | done
  const [search, setSearch]         = useState('');

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
    const roleOk = isInternal
      ? aud === 'employee' || aud === 'both'
      : aud === 'customer'  || aud === 'both';
    if (!roleOk) return false;
    if (search.trim()) {
      const q = search.toLowerCase();
      if (!c.title?.toLowerCase().includes(q) && !c.description?.toLowerCase().includes(q)) return false;
    }
    if (filter === 'mine') { const p = progressMap[c.id]; return p && p.completed > 0; }
    if (filter === 'done') { const p = progressMap[c.id]; return p && p.progress_pct === 100; }
    return true;
  });

  return (
    <div style={{ fontFamily: T.font, display: 'flex', flexDirection: 'column', gap: 28 }}>

      {/* ── Header ──────────────────────────────────────────── */}
      <div style={{
        display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between',
        flexWrap: 'wrap', gap: 16,
        paddingBottom: 24, borderBottom: `1px solid ${T.border}`,
      }}>
        <div>
          <h1 style={{
            fontSize: 26, fontWeight: 700, color: T.text,
            margin: '0 0 4px', letterSpacing: '-0.01em', lineHeight: 1.2,
            fontFamily: T.font,
          }}>
            KOMPAGNON Akademy
          </h1>
          <p style={{ fontSize: 14, color: T.textMuted, margin: 0, fontFamily: T.font }}>
            {isInternal ? 'Schulungen & internes Wissen für das Team' : 'Dein Lernbereich — Wissen & Kurse'}
          </p>
        </div>

        {/* Search */}
        <div style={{ position: 'relative', flexShrink: 0 }}>
          <svg width="14" height="14" viewBox="0 0 16 16" fill="none"
            stroke={T.textMuted} strokeWidth="1.6"
            style={{ position: 'absolute', left: 11, top: '50%', transform: 'translateY(-50%)', pointerEvents: 'none' }}>
            <circle cx="6.5" cy="6.5" r="4.5" /><path d="M10.5 10.5L14 14" strokeLinecap="round" />
          </svg>
          <input
            type="text"
            placeholder="Kurse suchen…"
            value={search}
            onChange={e => setSearch(e.target.value)}
            style={{
              paddingLeft: 33, paddingRight: 14, paddingTop: 9, paddingBottom: 9,
              background: T.surface, border: `1px solid ${T.borderMed}`,
              borderRadius: T.radiusLg, fontSize: 13, color: T.text,
              fontFamily: T.font, outline: 'none', width: 224,
              boxShadow: T.shadow, transition: 'border-color 0.15s',
            }}
            onFocus={e => e.target.style.borderColor = T.primary}
            onBlur={e => e.target.style.borderColor = T.borderMed}
          />
        </div>
      </div>

      {/* ── Filter tabs ─────────────────────────────────────── */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
        <div style={{ display: 'flex', borderBottom: `1px solid ${T.border}` }}>
          {[
            { id: 'all',  label: 'Alle' },
            { id: 'mine', label: 'In Bearbeitung' },
            { id: 'done', label: 'Abgeschlossen' },
          ].map(f => {
            const active = filter === f.id;
            return (
              <button
                key={f.id}
                onClick={() => setFilter(f.id)}
                style={{
                  padding: '9px 18px',
                  background: 'none', border: 'none',
                  borderBottom: active ? `2px solid ${T.primary}` : '2px solid transparent',
                  marginBottom: -1,
                  color: active ? T.primary : T.textSub,
                  fontSize: 13, fontWeight: active ? 600 : 400,
                  cursor: 'pointer', fontFamily: T.font,
                  transition: 'color 0.15s',
                }}
              >{f.label}</button>
            );
          })}
        </div>

        {user?.role === 'admin' && (
          <button
            onClick={() => navigate('/app/akademie/admin')}
            style={{
              padding: '7px 14px',
              background: T.appBg, color: T.textSub,
              border: `1px solid ${T.borderMed}`, borderRadius: T.radiusLg,
              fontSize: 12, fontWeight: 500, cursor: 'pointer', fontFamily: T.font,
            }}
          >⚙️ Kurse verwalten</button>
        )}
      </div>

      {/* ── Grid ────────────────────────────────────────────── */}
      {loading ? (
        <div style={{ display: 'flex', justifyContent: 'center', padding: '80px 0' }}>
          <div style={{
            width: 32, height: 32, borderRadius: '50%',
            border: `3px solid ${T.primaryBg}`,
            borderTopColor: T.primary,
            animation: 'spin 0.8s linear infinite',
          }} />
        </div>

      ) : visible.length === 0 ? (
        /* ── Empty state ── */
        <div style={{ textAlign: 'center', padding: '80px 20px' }}>
          <div style={{ fontSize: 52, marginBottom: 14, opacity: 0.25 }}>🎓</div>
          <div style={{ fontSize: 15, fontWeight: 600, color: T.textSub, marginBottom: 6, fontFamily: T.font }}>
            {search
              ? 'Keine Kurse gefunden'
              : filter === 'done' ? 'Noch kein Kurs abgeschlossen'
              : filter === 'mine' ? 'Noch kein Kurs gestartet'
              : 'Noch keine Kurse verfügbar'}
          </div>
          <div style={{ fontSize: 13, color: T.textMuted, fontFamily: T.font }}>
            {search ? `Keine Ergebnisse für „${search}"` : 'Inhalte werden vorbereitet.'}
          </div>
        </div>

      ) : (
        /* ── Course grid ── */
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
          gap: 20,
        }}>
          {visible.map(course => {
            const p        = progressMap[course.id];
            const pct      = p?.progress_pct || 0;
            const started  = p && p.completed > 0;
            const done     = pct === 100;
            const aud      = course.target_audience || course.audience;
            const certCode = p?.certificate_code;

            return (
              <div
                key={course.id}
                onClick={() => navigate(`/app/academy/${course.id}`)}
                style={{
                  background: T.surface,
                  border: `1px solid ${T.border}`,
                  borderRadius: T.radiusLg,
                  boxShadow: T.shadow,
                  display: 'flex', flexDirection: 'column',
                  overflow: 'hidden',
                  cursor: 'pointer',
                  transition: 'box-shadow 0.2s, transform 0.18s',
                }}
                onMouseEnter={e => {
                  e.currentTarget.style.boxShadow = '0 6px 20px rgba(0,142,170,0.12)';
                  e.currentTarget.style.transform = 'translateY(-2px)';
                }}
                onMouseLeave={e => {
                  e.currentTarget.style.boxShadow = T.shadow;
                  e.currentTarget.style.transform = 'none';
                }}
              >
                {/* ── Thumbnail (16:9) ── */}
                <div style={{
                  paddingTop: '56.25%',
                  position: 'relative',
                  background: course.thumbnail_url
                    ? `url(${course.thumbnail_url}) center/cover`
                    : `linear-gradient(135deg, ${T.primary} 0%, #005f74 100%)`,
                  borderRadius: `${T.radiusLg} ${T.radiusLg} 0 0`,
                  flexShrink: 0,
                }}>
                  {/* Audience badge — top left */}
                  <div style={{
                    position: 'absolute', top: 10, left: 10,
                    background: T.primary, color: '#fff',
                    borderRadius: T.radiusFull,
                    fontSize: 11, fontWeight: 600,
                    padding: '3px 10px',
                    fontFamily: T.font,
                    letterSpacing: '0.02em',
                  }}>
                    {AUDIENCE_LABEL[aud] || aud}
                  </div>

                  {/* Status badge — top right */}
                  {done && (
                    <div style={{
                      position: 'absolute', top: 10, right: 10,
                      background: T.certBg, color: T.certText,
                      borderRadius: T.radiusFull,
                      fontSize: 11, fontWeight: 600, padding: '3px 10px',
                      fontFamily: T.font,
                    }}>🏆 Zertifikat</div>
                  )}
                  {!done && started && (
                    <div style={{
                      position: 'absolute', top: 10, right: 10,
                      background: 'rgba(0,0,0,0.5)', color: '#fff',
                      borderRadius: T.radiusFull,
                      fontSize: 11, fontWeight: 500, padding: '3px 10px',
                      fontFamily: T.font,
                    }}>{pct}% erledigt</div>
                  )}

                  {!course.thumbnail_url && (
                    <div style={{
                      position: 'absolute', inset: 0,
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontSize: 44, opacity: 0.25,
                    }}>🎓</div>
                  )}
                </div>

                {/* ── Card body ── */}
                <div style={{
                  padding: '16px 18px 18px',
                  flex: 1, display: 'flex', flexDirection: 'column', gap: 10,
                }}>
                  {/* Title */}
                  <div style={{
                    fontSize: 15, fontWeight: 600, color: T.text,
                    lineHeight: 1.35, fontFamily: T.font,
                  }}>{course.title}</div>

                  {/* Description — 2 lines max */}
                  <div style={{
                    fontSize: 14, color: T.textSub, lineHeight: 1.55,
                    flex: 1, fontFamily: T.font,
                    display: '-webkit-box',
                    WebkitLineClamp: 2,
                    WebkitBoxOrient: 'vertical',
                    overflow: 'hidden',
                  }}>{course.description}</div>

                  {/* Progress bar + percent */}
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                      <span style={{ fontSize: 12, color: T.textMuted, fontFamily: T.font }}>
                        {!p || p.total_lessons === 0
                          ? 'Noch nicht gestartet'
                          : done ? 'Abgeschlossen'
                          : `${p.completed} von ${p.total_lessons} Lektionen`}
                      </span>
                      <span style={{ fontSize: 12, fontWeight: 500, color: T.textMuted, fontFamily: T.font }}>
                        {pct}%
                      </span>
                    </div>
                    <div style={{
                      height: 6, background: T.primaryBg,
                      borderRadius: 3, overflow: 'hidden',
                    }}>
                      <div style={{
                        width: `${pct}%`, height: '100%',
                        background: done ? T.successText : T.primary,
                        borderRadius: 3, transition: 'width 0.4s ease',
                      }} />
                    </div>
                  </div>

                  {/* CTA button */}
                  <button
                    onClick={e => {
                      e.stopPropagation();
                      if (done && certCode) navigate(`/academy/certificate/${certCode}`);
                      else navigate(`/app/academy/${course.id}`);
                    }}
                    style={{
                      marginTop: 2, width: '100%', padding: '10px 16px',
                      background: done ? T.certBg : T.primary,
                      color:      done ? T.certText : '#fff',
                      border: 'none', borderRadius: '8px',
                      fontSize: 13, fontWeight: 600,
                      cursor: 'pointer', fontFamily: T.font,
                      transition: 'opacity 0.15s',
                      letterSpacing: '0.01em',
                    }}
                    onMouseEnter={e => e.currentTarget.style.opacity = '0.85'}
                    onMouseLeave={e => e.currentTarget.style.opacity = '1'}
                  >
                    {done
                      ? (certCode ? 'Zertifikat anzeigen →' : '✓ Abgeschlossen')
                      : started ? 'Fortsetzen →' : 'Starten →'}
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

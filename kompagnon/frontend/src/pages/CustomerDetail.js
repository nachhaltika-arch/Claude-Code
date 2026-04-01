import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import API_BASE_URL from '../config';

export default function CustomerDetail() {
  const { customerId } = useParams();
  const navigate = useNavigate();
  const { token } = useAuth();
  const h = { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) };

  const [customer, setCustomer] = useState(null);
  const [loadingCustomer, setLoadingCustomer] = useState(true);

  // Academy state
  const [assigned, setAssigned] = useState([]);
  const [allCourses, setAllCourses] = useState([]);
  const [loadingAcademy, setLoadingAcademy] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [assigning, setAssigning] = useState(null); // course_id being assigned
  const [removing, setRemoving] = useState(null);

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/leads/${customerId}`, { headers: h })
      .then(r => r.json())
      .then(setCustomer)
      .catch(console.error)
      .finally(() => setLoadingCustomer(false));
  }, [customerId]); // eslint-disable-line

  useEffect(() => {
    Promise.all([
      fetch(`${API_BASE_URL}/api/academy/customer/${customerId}/courses`, { headers: h }).then(r => r.json()),
      fetch(`${API_BASE_URL}/api/academy/courses`, { headers: h }).then(r => r.json()),
    ])
      .then(([assignedData, coursesData]) => {
        setAssigned(Array.isArray(assignedData) ? assignedData : []);
        setAllCourses(Array.isArray(coursesData) ? coursesData : []);
      })
      .catch(console.error)
      .finally(() => setLoadingAcademy(false));
  }, [customerId]); // eslint-disable-line

  const handleAssign = async (courseId) => {
    setAssigning(courseId);
    try {
      const res = await fetch(`${API_BASE_URL}/api/academy/customer/${customerId}/courses/${courseId}/assign`, {
        method: 'POST', headers: h,
      });
      if (res.ok) {
        const data = await res.json();
        setAssigned(prev => [...prev, { ...data, progress_pct: 0, total_lessons: 0, completed: 0, certificate_code: null }]);
      }
    } catch (e) { console.error(e); }
    setAssigning(null);
    setShowModal(false);
  };

  const handleRemove = async (courseId) => {
    setRemoving(courseId);
    try {
      const res = await fetch(`${API_BASE_URL}/api/academy/customer/${customerId}/courses/${courseId}`, {
        method: 'DELETE', headers: h,
      });
      if (res.ok) {
        setAssigned(prev => prev.filter(a => a.course_id !== courseId));
      }
    } catch (e) { console.error(e); }
    setRemoving(null);
  };

  // Courses not yet assigned and relevant for customers
  const assignedIds = new Set(assigned.map(a => a.course_id));
  const available = allCourses.filter(c => {
    const aud = c.target_audience || c.audience;
    return !assignedIds.has(c.id) && (aud === 'customer' || aud === 'both');
  });

  if (loadingCustomer) return (
    <div style={{ display: 'flex', justifyContent: 'center', padding: '80px 0' }}>
      <div style={{ width: 28, height: 28, borderRadius: '50%', border: '3px solid var(--border-light)', borderTopColor: 'var(--brand-primary)', animation: 'spin 0.8s linear infinite' }} />
    </div>
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>

      {/* ── Header ── */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <button onClick={() => navigate(-1)} style={{
          background: 'none', border: 'none', color: 'var(--text-tertiary)',
          cursor: 'pointer', fontSize: 13, fontFamily: 'var(--font-sans)', padding: 0,
          display: 'flex', alignItems: 'center', gap: 4,
        }}>← Zurück</button>
        <span style={{ color: 'var(--border-medium)' }}>·</span>
        <h1 style={{ fontSize: 20, fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
          {customer?.contact_name || customer?.company_name || `Kunde #${customerId}`}
        </h1>
      </div>

      {/* ── Akademy Section ── */}
      <div style={{
        background: 'var(--bg-surface)', border: '1px solid var(--border-light)',
        borderRadius: 'var(--radius-lg)', overflow: 'hidden',
      }}>
        {/* Section header */}
        <div style={{
          padding: '16px 20px', borderBottom: '1px solid var(--border-light)',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ fontSize: 16 }}>🎓</span>
            <span style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>Akademy</span>
            {!loadingAcademy && assigned.length > 0 && (
              <span style={{
                background: 'var(--brand-primary-light)', color: 'var(--brand-primary)',
                borderRadius: 'var(--radius-full)', fontSize: 11, fontWeight: 600,
                padding: '2px 8px',
              }}>{assigned.length}</span>
            )}
          </div>
          <button
            onClick={() => setShowModal(true)}
            style={{
              padding: '6px 14px', background: 'var(--brand-primary)', color: 'white',
              border: 'none', borderRadius: 'var(--radius-md)', fontSize: 12,
              fontWeight: 600, cursor: 'pointer', fontFamily: 'var(--font-sans)',
              display: 'flex', alignItems: 'center', gap: 6,
            }}
          >+ Kurs zuweisen</button>
        </div>

        {/* Course table */}
        <div style={{ padding: '4px 0' }}>
          {loadingAcademy ? (
            <div style={{ padding: '32px 20px', display: 'flex', justifyContent: 'center' }}>
              <div style={{ width: 24, height: 24, borderRadius: '50%', border: '2px solid var(--border-light)', borderTopColor: 'var(--brand-primary)', animation: 'spin 0.8s linear infinite' }} />
            </div>
          ) : assigned.length === 0 ? (
            <div style={{ padding: '32px 20px', textAlign: 'center', color: 'var(--text-tertiary)' }}>
              <div style={{ fontSize: 36, marginBottom: 8, opacity: 0.3 }}>📚</div>
              <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 4 }}>Noch keine Kurse zugewiesen</div>
              <div style={{ fontSize: 12 }}>Klicke auf „+ Kurs zuweisen" um diesem Kunden Zugriff zu geben.</div>
            </div>
          ) : (
            <>
              {/* Table header */}
              <div style={{
                display: 'grid', gridTemplateColumns: '1fr 180px 120px 40px',
                gap: 12, padding: '8px 20px',
                fontSize: 11, fontWeight: 600, color: 'var(--text-tertiary)',
                textTransform: 'uppercase', letterSpacing: '0.06em',
                borderBottom: '1px solid var(--border-light)',
              }}>
                <span>Kurs</span>
                <span>Fortschritt</span>
                <span>Zertifikat</span>
                <span />
              </div>

              {assigned.map(row => (
                <div key={row.course_id} style={{
                  display: 'grid', gridTemplateColumns: '1fr 180px 120px 40px',
                  gap: 12, padding: '12px 20px', alignItems: 'center',
                  borderBottom: '1px solid var(--border-light)',
                  transition: 'background 0.1s',
                }}
                  onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-app)'}
                  onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                >
                  {/* Course name */}
                  <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)', lineHeight: 1.3 }}>
                    {row.course_title}
                    {row.assigned_at && (
                      <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 2 }}>
                        Zugewiesen: {row.assigned_at}
                      </div>
                    )}
                  </div>

                  {/* Progress bar */}
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                      <span style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>
                        {row.total_lessons > 0 ? `${row.completed}/${row.total_lessons}` : '—'}
                      </span>
                      <span style={{ fontSize: 10, fontWeight: 600, color: row.progress_pct === 100 ? '#16a34a' : 'var(--text-tertiary)' }}>
                        {row.progress_pct}%
                      </span>
                    </div>
                    <div style={{ height: 5, background: 'var(--border-light)', borderRadius: 3, overflow: 'hidden' }}>
                      <div style={{
                        width: `${row.progress_pct}%`, height: '100%',
                        background: row.progress_pct === 100 ? '#16a34a' : 'var(--brand-primary)',
                        borderRadius: 3, transition: 'width 0.4s',
                      }} />
                    </div>
                  </div>

                  {/* Certificate */}
                  <div>
                    {row.certificate_code ? (
                      <a
                        href={`/academy/certificate/${row.certificate_code}`}
                        target="_blank"
                        rel="noreferrer"
                        style={{
                          display: 'inline-flex', alignItems: 'center', gap: 4,
                          padding: '3px 10px', background: '#dcfce7', color: '#16a34a',
                          borderRadius: 'var(--radius-full)', fontSize: 11, fontWeight: 700,
                          textDecoration: 'none',
                        }}
                      >🏆 Zertifikat</a>
                    ) : (
                      <span style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>—</span>
                    )}
                  </div>

                  {/* Remove button */}
                  <button
                    onClick={() => handleRemove(row.course_id)}
                    disabled={removing === row.course_id}
                    title="Kurs entfernen"
                    style={{
                      background: 'none', border: 'none', cursor: 'pointer',
                      color: 'var(--status-danger-text)', padding: 4, borderRadius: 'var(--radius-sm)',
                      opacity: removing === row.course_id ? 0.4 : 0.6, display: 'flex', alignItems: 'center',
                      transition: 'opacity 0.15s',
                    }}
                    onMouseEnter={e => e.currentTarget.style.opacity = '1'}
                    onMouseLeave={e => e.currentTarget.style.opacity = removing === row.course_id ? '0.4' : '0.6'}
                  >
                    <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
                      <path d="M2.5 4h11M6 4V2.5h4V4M4 4l.8 9.5h6.4L12 4"/>
                    </svg>
                  </button>
                </div>
              ))}
            </>
          )}
        </div>
      </div>

      {/* ── Assign Modal ── */}
      {showModal && (
        <>
          <div
            style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)', zIndex: 100 }}
            onClick={() => setShowModal(false)}
          />
          <div style={{
            position: 'fixed', top: '50%', left: '50%', transform: 'translate(-50%,-50%)',
            background: 'var(--bg-surface)', borderRadius: 'var(--radius-xl)',
            boxShadow: '0 20px 60px rgba(0,0,0,0.18)',
            width: 480, maxWidth: '90vw', maxHeight: '70vh',
            display: 'flex', flexDirection: 'column', zIndex: 101,
          }}>
            <div style={{ padding: '18px 20px', borderBottom: '1px solid var(--border-light)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' }}>Kurs zuweisen</span>
              <button onClick={() => setShowModal(false)} style={{ background: 'none', border: 'none', fontSize: 18, cursor: 'pointer', color: 'var(--text-tertiary)', lineHeight: 1 }}>×</button>
            </div>

            <div style={{ flex: 1, overflowY: 'auto', padding: 8 }}>
              {available.length === 0 ? (
                <div style={{ padding: '32px 20px', textAlign: 'center', color: 'var(--text-tertiary)', fontSize: 13 }}>
                  Alle verfügbaren Kurse wurden bereits zugewiesen.
                </div>
              ) : available.map(course => (
                <button
                  key={course.id}
                  onClick={() => handleAssign(course.id)}
                  disabled={assigning === course.id}
                  style={{
                    width: '100%', display: 'flex', alignItems: 'center', gap: 12,
                    padding: '12px 14px', background: 'transparent',
                    border: 'none', borderRadius: 'var(--radius-md)',
                    cursor: 'pointer', textAlign: 'left',
                    transition: 'background 0.1s',
                    opacity: assigning === course.id ? 0.6 : 1,
                  }}
                  onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-app)'}
                  onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                >
                  <div style={{
                    width: 40, height: 40, borderRadius: 'var(--radius-md)', flexShrink: 0,
                    background: course.thumbnail_url
                      ? `url(${course.thumbnail_url}) center/cover`
                      : 'linear-gradient(135deg, var(--brand-primary), #1e3a5f)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: 18,
                  }}>
                    {!course.thumbnail_url && '🎓'}
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 2 }}>{course.title}</div>
                    <div style={{ fontSize: 11, color: 'var(--text-tertiary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{course.description}</div>
                  </div>
                  <span style={{ fontSize: 12, color: 'var(--brand-primary)', fontWeight: 600, flexShrink: 0 }}>
                    {assigning === course.id ? '…' : '+ Zuweisen'}
                  </span>
                </button>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

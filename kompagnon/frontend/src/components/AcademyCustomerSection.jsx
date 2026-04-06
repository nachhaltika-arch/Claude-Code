import { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { useAuth } from '../context/AuthContext';
import { useScreenSize } from '../utils/responsive';
import API_BASE_URL from '../config';

export default function AcademyCustomerSection({ leadId }) {
  const { token } = useAuth();
  const { isMobile } = useScreenSize();
  const h = { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) };

  const [assigned, setAssigned]     = useState([]);
  const [allCourses, setAllCourses] = useState([]);
  const [loading, setLoading]       = useState(true);
  const [showModal, setShowModal]   = useState(false);
  const [assigning, setAssigning]   = useState(null);
  const [removing, setRemoving]     = useState(null);

  useEffect(() => {
    Promise.all([
      fetch(`${API_BASE_URL}/api/academy/customer/${leadId}/courses`, { headers: h }).then(r => r.json()),
      fetch(`${API_BASE_URL}/api/academy/courses`, { headers: h }).then(r => r.json()),
    ])
      .then(([assignedData, coursesData]) => {
        setAssigned(Array.isArray(assignedData) ? assignedData : []);
        setAllCourses(Array.isArray(coursesData) ? coursesData : []);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [leadId]); // eslint-disable-line

  const handleAssign = async (courseId) => {
    setAssigning(courseId);
    try {
      const res = await fetch(`${API_BASE_URL}/api/academy/customer/${leadId}/courses/${courseId}/assign`, { method: 'POST', headers: h });
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
      const res = await fetch(`${API_BASE_URL}/api/academy/customer/${leadId}/courses/${courseId}`, { method: 'DELETE', headers: h });
      if (res.ok) setAssigned(prev => prev.filter(a => a.course_id !== courseId));
    } catch (e) { console.error(e); }
    setRemoving(null);
  };

  const assignedIds = new Set(assigned.map(a => a.course_id));
  const available = allCourses.filter(c => {
    const aud = c.target_audience || c.audience;
    return !assignedIds.has(c.id) && (aud === 'customer' || aud === 'both');
  });

  return (
    <>
      <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', overflow: 'hidden' }}>
        {/* Header */}
        <div style={{ padding: isMobile ? '12px 16px' : '16px 20px', borderBottom: '1px solid var(--border-light)', display: 'flex', flexDirection: isMobile ? 'column' : 'row', alignItems: isMobile ? 'stretch' : 'center', justifyContent: 'space-between', gap: isMobile ? 10 : 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ fontSize: 16 }}>🎓</span>
            <span style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>Akademy</span>
            {!loading && assigned.length > 0 && (
              <span style={{ background: 'var(--brand-primary-light)', color: 'var(--brand-primary)', borderRadius: 'var(--radius-full)', fontSize: 11, fontWeight: 600, padding: '2px 8px' }}>{assigned.length}</span>
            )}
          </div>
          <button onClick={() => setShowModal(true)} style={{ padding: '8px 14px', background: 'var(--brand-primary)', color: 'var(--text-inverse)', border: 'none', borderRadius: 'var(--radius-md)', fontSize: 12, fontWeight: 600, cursor: 'pointer', fontFamily: 'var(--font-sans)', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6, ...(isMobile ? { width: '100%' } : {}) }}>
            + Kurs zuweisen
          </button>
        </div>

        {/* Course list */}
        <div style={{ padding: '4px 0' }}>
          {loading ? (
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
            <div style={{ overflowX: 'auto' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 180px 120px 40px', minWidth: 520, gap: 12, padding: '8px 20px', fontSize: 11, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', borderBottom: '1px solid var(--border-light)' }}>
                <span>Kurs</span><span>Fortschritt</span><span>Zertifikat</span><span />
              </div>
              {assigned.map(row => (
                <div key={row.course_id} style={{ display: 'grid', gridTemplateColumns: '1fr 180px 120px 40px', minWidth: 520, gap: 12, padding: '12px 20px', alignItems: 'center', borderBottom: '1px solid var(--border-light)', transition: 'background 0.1s' }} onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-app)'} onMouseLeave={e => e.currentTarget.style.background = 'transparent'}>
                  <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)', lineHeight: 1.3 }}>
                    {row.course_title}
                    {row.assigned_at && <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 2 }}>Zugewiesen: {row.assigned_at}</div>}
                  </div>
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                      <span style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>{row.total_lessons > 0 ? `${row.completed}/${row.total_lessons}` : '—'}</span>
                      <span style={{ fontSize: 10, fontWeight: 600, color: row.progress_pct === 100 ? 'var(--status-success-text)' : 'var(--text-tertiary)' }}>{row.progress_pct}%</span>
                    </div>
                    <div style={{ height: 5, background: 'var(--border-light)', borderRadius: 3, overflow: 'hidden' }}>
                      <div style={{ width: `${row.progress_pct}%`, height: '100%', background: row.progress_pct === 100 ? 'var(--status-success-text)' : 'var(--brand-primary)', borderRadius: 3, transition: 'width 0.4s' }} />
                    </div>
                  </div>
                  <div>
                    {row.certificate_code ? (
                      <a href={`/academy/certificate/${row.certificate_code}`} target="_blank" rel="noreferrer" style={{ display: 'inline-flex', alignItems: 'center', gap: 4, padding: '3px 10px', background: 'var(--status-success-bg)', color: 'var(--status-success-text)', borderRadius: 'var(--radius-full)', fontSize: 11, fontWeight: 700, textDecoration: 'none' }}>🏆 Zertifikat</a>
                    ) : (
                      <span style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>—</span>
                    )}
                  </div>
                  <button onClick={() => handleRemove(row.course_id)} disabled={removing === row.course_id} title="Kurs entfernen" style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--status-danger-text)', padding: 4, borderRadius: 'var(--radius-sm)', opacity: removing === row.course_id ? 0.4 : 0.6, display: 'flex', alignItems: 'center', transition: 'opacity 0.15s' }} onMouseEnter={e => e.currentTarget.style.opacity = '1'} onMouseLeave={e => e.currentTarget.style.opacity = removing === row.course_id ? '0.4' : '0.6'}>
                    <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"><path d="M2.5 4h11M6 4V2.5h4V4M4 4l.8 9.5h6.4L12 4"/></svg>
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Assign Modal */}
      {showModal && createPortal(
        <>
          <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', zIndex: 100 }} onClick={() => setShowModal(false)} />
          <div style={isMobile ? {
            position: 'fixed', bottom: 0, left: 0, right: 0,
            background: 'var(--bg-surface)', borderRadius: '16px 16px 0 0',
            padding: '20px 16px 32px', zIndex: 101, maxHeight: '80vh', overflowY: 'auto',
          } : {
            position: 'fixed', top: '50%', left: '50%', transform: 'translate(-50%,-50%)',
            background: 'var(--bg-surface)', borderRadius: 'var(--radius-xl)',
            padding: 28, zIndex: 101, width: 480, maxHeight: '80vh', overflowY: 'auto',
            boxShadow: 'var(--shadow-xl)',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <span style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' }}>Kurs zuweisen</span>
              <button onClick={() => setShowModal(false)} style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: 20, color: 'var(--text-tertiary)', lineHeight: 1 }}>×</button>
            </div>
            {available.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '24px 0', color: 'var(--text-tertiary)', fontSize: 13 }}>Alle verfügbaren Kurse wurden bereits zugewiesen.</div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {available.map(c => (
                  <div key={c.id} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 14px', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)', background: 'var(--bg-app)' }}>
                    <div>
                      <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>{c.title}</div>
                      {c.description && <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 2 }}>{c.description}</div>}
                    </div>
                    <button onClick={() => handleAssign(c.id)} disabled={assigning === c.id} style={{ padding: '6px 14px', background: assigning === c.id ? 'var(--bg-elevated)' : 'var(--brand-primary)', color: assigning === c.id ? 'var(--text-tertiary)' : 'var(--text-inverse)', border: 'none', borderRadius: 'var(--radius-md)', fontSize: 12, fontWeight: 600, cursor: assigning === c.id ? 'not-allowed' : 'pointer', fontFamily: 'var(--font-sans)', flexShrink: 0, marginLeft: 12 }}>
                      {assigning === c.id ? '…' : 'Zuweisen'}
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </>,
        document.body
      )}
    </>
  );
}

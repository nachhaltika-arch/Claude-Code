/**
 * Der Akademie-Reiter der Betriebsansicht (L-25).
 *
 * Am 2026-08-31 aus `CustomerDetail.jsx` herausgeloest — 251 Zeilen. Er stand
 * dort als **nacktes JSX** hinter dem `&&`, ohne Klammern: `{activeTab ===
 * 'akademy' && <div …>}`. Das ist die dritte Form neben dem geklammerten
 * Ausdruck und der sofort aufgerufenen Funktion — und der Grund, warum ein
 * Schnitt hier jedes Mal gelesen werden will statt gemustert.
 */


export default function ReiterAkademie({
  isMobile,
  activeTab,
  assigned,
  handleRemove,
  loadingAcademy,
  removing,
  setShowModal,
}) {
  return (
  <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', overflow: 'hidden' }}>

    {/* Section header — stacked on mobile */}
    <div style={{
      padding: isMobile ? '12px 16px' : '16px 20px',
      borderBottom: '1px solid var(--border-light)',
      display: 'flex',
      flexDirection: isMobile ? 'column' : 'row',
      alignItems: isMobile ? 'stretch' : 'center',
      justifyContent: 'space-between',
      gap: isMobile ? 10 : 0,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <span style={{ fontSize: 16 }}>🎓</span>
        <span style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>Akademie</span>
        {!loadingAcademy && assigned.length > 0 && (
          <span style={{ background: 'var(--brand-primary-light)', color: 'var(--brand-primary-mid)', borderRadius: 'var(--radius-full)', fontSize: 12, fontWeight: 600, padding: '2px 8px' }}>
            {assigned.length}
          </span>
        )}
      </div>
      {/* Full-width button on mobile */}
      <button
        onClick={() => setShowModal(true)}
        style={{
          padding: '8px 14px',
          background: 'var(--brand-primary)',
          color: 'var(--text-inverse)',
          border: 'none', borderRadius: 'var(--radius-md)',
          fontSize: 12, fontWeight: 600, cursor: 'pointer',
          fontFamily: 'var(--font-sans)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6,
          ...(isMobile ? { width: '100%' } : {}),
        }}
      >+ Kurs zuweisen</button>
    </div>

    {/* SCHRITT 4 — Course table with horizontal scroll */}
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
        <div style={{ overflowX: 'auto' }}>
          {/* Table header */}
          <div style={{
            display: 'grid', gridTemplateColumns: '1fr 180px 120px 40px',
            minWidth: 520, gap: 12, padding: '8px 20px',
            fontSize: 12, fontWeight: 600, color: 'var(--text-tertiary)',
            textTransform: 'uppercase', letterSpacing: '0.06em',
            borderBottom: '1px solid var(--border-light)',
          }}>
            <span>Kurs</span><span>Fortschritt</span><span>Zertifikat</span><span />
          </div>

          {assigned.map(row => (
            <div
              key={row.course_id}
              style={{
                display: 'grid', gridTemplateColumns: '1fr 180px 120px 40px',
                minWidth: 520, gap: 12, padding: '12px 20px',
                alignItems: 'center', borderBottom: '1px solid var(--border-light)',
                transition: 'background 0.1s',
              }}
              onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-app)'}
              onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
            >
              {/* Course name */}
              <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)', lineHeight: 1.3 }}>
                {row.course_title}
                {row.assigned_at && (
                  <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginTop: 2 }}>Zugewiesen: {row.assigned_at}</div>
                )}
              </div>

              {/* Progress bar */}
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                  <span style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>
                    {row.total_lessons > 0 ? `${row.completed}/${row.total_lessons}` : '—'}
                  </span>
                  <span style={{ fontSize: 12, fontWeight: 600, color: row.progress_pct === 100 ? 'var(--status-success-text)' : 'var(--text-tertiary)' }}>
                    {row.progress_pct}%
                  </span>
                </div>
                <div style={{ height: 5, background: 'var(--border-light)', borderRadius: 3, overflow: 'hidden' }}>
                  <div style={{ width: `${row.progress_pct}%`, height: '100%', background: row.progress_pct === 100 ? 'var(--status-success-text)' : 'var(--brand-primary)', borderRadius: 3, transition: 'width 0.4s' }} />
                </div>
              </div>

              {/* Certificate */}
              <div>
                {row.certificate_code ? (
                  <a
                    href={`/academy/certificate/${row.certificate_code}`}
                    target="_blank" rel="noreferrer"
                    style={{
                      display: 'inline-flex', alignItems: 'center', gap: 4,
                      padding: '3px 10px',
                      background: 'var(--status-success-bg)',
                      color: 'var(--status-success-text)',
                      borderRadius: 'var(--radius-full)', fontSize: 12, fontWeight: 700,
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
                  color: 'var(--status-danger-text)', padding: 4,
                  borderRadius: 'var(--radius-sm)',
                  opacity: removing === row.course_id ? 0.4 : 0.6,
                  display: 'flex', alignItems: 'center', transition: 'opacity 0.15s',
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
        </div>
      )}
    </div>
        </div>
  );
}

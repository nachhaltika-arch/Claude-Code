/**
 * Das verknuepfte Projekt eines Betriebs (L-25).
 *
 * Am 2026-08-30 aus `CustomerDetail.jsx` herausgeloest — 78 Zeilen.
 */
import { useState, useEffect } from 'react';
import API_BASE_URL from '../../config';

export default function LinkedProjectSection({ leadId, headers, navigate }) {
  const [project, setProject]   = useState(null);
  const [loading, setLoading]   = useState(true);
  const [creating, setCreating] = useState(false);
  const [error, setError]       = useState(null);

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/projects/?limit=200`, { headers })
      .then(r => r.json())
      .then(data => {
        const list = Array.isArray(data) ? data : [];
        setProject(list.find(p => String(p.lead_id) === String(leadId)) || null);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [leadId]); // eslint-disable-line

  const createProject = async () => {
    setCreating(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE_URL}/api/projects/from-lead/${leadId}`, { method: 'POST', headers });
      const data = await res.json();
      if (res.ok) { setProject(data); }
      else { setError(data?.detail?.message || data.detail || 'Fehler beim Anlegen des Projekts'); }
    } catch (e) { setError(String(e)); }
    setCreating(false);
  };

  const phaseLabel = (status) => {
    const m = String(status || '').match(/phase_(\d)/);
    return m ? `Phase ${m[1]} von 7` : (status === 'completed' ? 'Abgeschlossen' : status || '–');
  };

  const card = { background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', padding: '14px 16px' };

  if (loading) return null;

  return (
    <div style={card}>
      <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 10 }}>🗂 Verknüpftes Projekt</div>
      {project ? (
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 2 }}>
              {project.project_name || project.company_name || `Projekt #${project.id}`}
            </div>
            <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{phaseLabel(project.status)}</div>
          </div>
          <button onClick={() => navigate(`/app/projects/${project.id}`)} style={{
            padding: '7px 14px', background: 'var(--brand-primary)', color: 'var(--text-on-brand)',
            border: 'none', borderRadius: 'var(--radius-md)', fontSize: 12, fontWeight: 600,
            cursor: 'pointer', fontFamily: 'var(--font-sans)', flexShrink: 0,
          }}>
            Zum Projekt →
          </button>
        </div>
      ) : (
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
          <div style={{ flex: 1, fontSize: 12, color: 'var(--text-tertiary)' }}>Noch kein Projekt angelegt.</div>
          <button onClick={createProject} disabled={creating} style={{
            padding: '7px 14px', background: 'var(--bg-hover)', color: 'var(--text-secondary)',
            border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)',
            fontSize: 12, fontWeight: 500, cursor: creating ? 'wait' : 'pointer',
            fontFamily: 'var(--font-sans)', flexShrink: 0,
          }}>
            {creating ? 'Wird angelegt…' : '+ Projekt anlegen'}
          </button>
        </div>
      )}
      {error && <div style={{ marginTop: 8, fontSize: 12, color: 'var(--status-danger-text)' }}>❌ {error}</div>}
    </div>
  );
}


// ── CMS Connection section ─────────────────────────────────────


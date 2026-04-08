import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import API_BASE_URL from '../config';

export default function Abnahme() {
  const { projectId } = useParams();
  const [project, setProject] = useState(null);
  const [loading, setLoading] = useState(true);
  const [name, setName] = useState('');
  const [confirmed, setConfirmed] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/projects/${projectId}`)
      .then(r => r.ok ? r.json() : null)
      .then(d => { if (d) setProject(d); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [projectId]);

  const handleSubmit = async () => {
    if (!name.trim() || !confirmed) return;
    setSubmitting(true);
    setError('');
    try {
      const r = await fetch(`${API_BASE_URL}/api/projects/${projectId}/abnahme`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: name.trim() }),
      });
      if (r.ok) {
        const data = await r.json();
        setDone(true);
        setProject(prev => prev ? { ...prev, abnahme_datum: data.abnahme_datum, abnahme_durch: data.abnahme_durch } : prev);
      } else {
        setError('Abnahme konnte nicht gespeichert werden.');
      }
    } catch {
      setError('Verbindungsfehler. Bitte erneut versuchen.');
    }
    setSubmitting(false);
  };

  const fmtDate = (d) => {
    const dt = new Date(d);
    return dt.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' })
      + ' um ' + dt.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' }) + ' Uhr';
  };

  const card = { background: '#fff', borderRadius: 12, border: '1px solid #e5e7eb', padding: 32, maxWidth: 520, width: '100%' };

  if (loading) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#f4f6f8', fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif" }}>
        <div style={{ color: '#94a3b8', fontSize: 14 }}>Laden...</div>
      </div>
    );
  }

  if (!project) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#f4f6f8', fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif" }}>
        <div style={card}>
          <div style={{ textAlign: 'center', color: '#64748b', fontSize: 14 }}>Projekt nicht gefunden.</div>
        </div>
      </div>
    );
  }

  const alreadyDone = project.abnahme_datum && !done;

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#f4f6f8', padding: 20, fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif" }}>
      <div style={card}>
        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          <div style={{ fontSize: 24, fontWeight: 700, color: '#008eaa', marginBottom: 4 }}>KOMPAGNON</div>
          <div style={{ fontSize: 18, fontWeight: 600, color: '#1a1a1a' }}>Digitale Abnahme</div>
          {project.company_name && (
            <div style={{ fontSize: 13, color: '#94a3b8', marginTop: 4 }}>{project.company_name}</div>
          )}
        </div>

        {/* Already approved */}
        {alreadyDone && (
          <div style={{ background: '#D1FAE5', border: '1px solid #bbf7d0', borderRadius: 8, padding: '16px 20px', textAlign: 'center' }}>
            <div style={{ fontSize: 28, marginBottom: 8 }}>&#10003;</div>
            <div style={{ fontSize: 14, fontWeight: 600, color: '#065F46' }}>
              Abgenommen am {fmtDate(project.abnahme_datum)}
            </div>
            <div style={{ fontSize: 13, color: '#065F46', marginTop: 4 }}>
              von {project.abnahme_durch || 'Kunde'}
            </div>
          </div>
        )}

        {/* Success after submit */}
        {done && (
          <div style={{ background: '#D1FAE5', border: '1px solid #bbf7d0', borderRadius: 8, padding: '24px 20px', textAlign: 'center' }}>
            <div style={{ fontSize: 36, marginBottom: 12 }}>&#10003;</div>
            <div style={{ fontSize: 16, fontWeight: 600, color: '#065F46', marginBottom: 6 }}>
              Vielen Dank, {name}!
            </div>
            <div style={{ fontSize: 13, color: '#065F46' }}>
              Ihre Website wurde offiziell abgenommen.
            </div>
          </div>
        )}

        {/* Form */}
        {!alreadyDone && !done && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <p style={{ fontSize: 14, color: '#555', lineHeight: 1.6, margin: 0 }}>
              Bitte bestaetigen Sie die Abnahme Ihrer Website.
            </p>

            <div>
              <label style={{ fontSize: 12, fontWeight: 500, color: '#64748b', display: 'block', marginBottom: 4 }}>Ihr Name</label>
              <input
                value={name}
                onChange={e => setName(e.target.value)}
                placeholder="Max Mustermann"
                required
                style={{ width: '100%', padding: '10px 14px', border: '1px solid #e5e7eb', borderRadius: 8, fontSize: 14, fontFamily: 'inherit', color: '#1a1a1a', boxSizing: 'border-box' }}
              />
            </div>

            <label style={{ display: 'flex', alignItems: 'flex-start', gap: 10, cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={confirmed}
                onChange={e => setConfirmed(e.target.checked)}
                style={{ marginTop: 3, width: 18, height: 18, accentColor: '#008eaa', cursor: 'pointer' }}
              />
              <span style={{ fontSize: 13, color: '#555', lineHeight: 1.5 }}>
                Ich bestaetige die Abnahme der fertiggestellten Website.
              </span>
            </label>

            {error && (
              <div style={{ padding: '8px 12px', borderRadius: 6, background: '#fef2f2', border: '1px solid #fca5a5', color: '#dc2626', fontSize: 12 }}>{error}</div>
            )}

            <button
              onClick={handleSubmit}
              disabled={!name.trim() || !confirmed || submitting}
              style={{
                width: '100%', padding: '12px', border: 'none', borderRadius: 8,
                background: (!name.trim() || !confirmed || submitting) ? '#e5e7eb' : '#008eaa',
                color: (!name.trim() || !confirmed || submitting) ? '#94a3b8' : '#fff',
                fontSize: 14, fontWeight: 600, cursor: (!name.trim() || !confirmed || submitting) ? 'not-allowed' : 'pointer',
                fontFamily: 'inherit',
              }}
            >
              {submitting ? 'Wird gespeichert...' : 'Jetzt abnehmen'}
            </button>
          </div>
        )}

        {/* Footer */}
        <div style={{ textAlign: 'center', marginTop: 24, fontSize: 11, color: '#c0c0c0' }}>
          KOMPAGNON Communications BP GmbH &bull; kompagnon.eu
        </div>
      </div>
    </div>
  );
}

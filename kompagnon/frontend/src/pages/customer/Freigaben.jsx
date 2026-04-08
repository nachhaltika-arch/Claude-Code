import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import API_BASE_URL from '../../config';

export default function Freigaben() {
  const { token, user } = useAuth();
  const [project, setProject] = useState(null);
  const [freigaben, setFreigaben] = useState({});
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState({});
  const [comments, setComments] = useState({});

  useEffect(() => {
    loadProject();
  }, [token]); // eslint-disable-line

  const loadProject = async () => {
    try {
      // Finde das eigene Projekt über portal/me
      const res = await fetch(`${API_BASE_URL}/api/portal/me`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) { setLoading(false); return; }
      const portalData = await res.json();
      if (!portalData.project_id) { setLoading(false); return; }

      // Lade Projekt-Details für content_freigaben
      const pRes = await fetch(`${API_BASE_URL}/api/projects/${portalData.project_id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (pRes.ok) {
        const p = await pRes.json();
        setProject(p);
        try {
          const cf = typeof p.content_freigaben === 'string' ? JSON.parse(p.content_freigaben) : (p.content_freigaben || {});
          setFreigaben(cf);
        } catch { setFreigaben({}); }
      }
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  const handleDecision = async (seiteId, confirmed) => {
    if (!project) return;
    setSending(s => ({ ...s, [seiteId]: true }));
    try {
      await fetch(`${API_BASE_URL}/api/projects/${project.id}/confirm-approval`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          seite_id: seiteId,
          bestaetigt: confirmed,
          kommentar: comments[seiteId] || '',
        }),
      });
      // Reload
      await loadProject();
    } catch (e) { console.error(e); }
    setSending(s => ({ ...s, [seiteId]: false }));
  };

  const cardStyle = {
    background: 'var(--bg-surface)', borderRadius: 'var(--radius-lg)',
    border: '1px solid var(--border-light)', padding: '20px 22px', marginBottom: 14,
  };

  const items = Object.entries(freigaben);
  const pending = items.filter(([, v]) => v.status === 'ausstehend' || !v.status);
  const decided = items.filter(([, v]) => v.status && v.status !== 'ausstehend');

  return (
    <div style={{ maxWidth: 720, margin: '0 auto', padding: '0 0 40px' }}>
      <div style={{ fontSize: 20, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 20 }}>
        ✅ Freigaben
      </div>

      {loading && <div style={{ color: 'var(--text-tertiary)', fontSize: 13 }}>Wird geladen…</div>}

      {!loading && items.length === 0 && (
        <div style={{ ...cardStyle, textAlign: 'center', color: 'var(--text-tertiary)', fontSize: 13, padding: 40 }}>
          Keine offenen Freigaben vorhanden.
          <div style={{ fontSize: 12, marginTop: 8, color: 'var(--text-tertiary)' }}>
            Ihr KOMPAGNON-Team sendet Ihnen Freigabeanfragen, sobald Inhalte bereit sind.
          </div>
        </div>
      )}

      {/* Offene Freigaben */}
      {pending.length > 0 && (
        <div style={{ marginBottom: 24 }}>
          <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-tertiary)', letterSpacing: '0.06em', marginBottom: 10 }}>
            OFFEN ({pending.length})
          </div>
          {pending.map(([seiteId, item]) => (
            <div key={seiteId} style={{ ...cardStyle, borderLeft: '3px solid var(--brand-primary)' }}>
              <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 6 }}>
                {item.topic || item.label || `Seite ${seiteId}`}
              </div>
              {item.beschreibung && (
                <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 10, lineHeight: 1.5 }}>
                  {item.beschreibung}
                </div>
              )}
              {item.preview_url && (
                <a href={item.preview_url} target="_blank" rel="noopener noreferrer"
                  style={{ display: 'inline-block', fontSize: 12, color: 'var(--brand-primary)', marginBottom: 10 }}>
                  Vorschau öffnen →
                </a>
              )}
              <textarea
                placeholder="Kommentar (optional)…"
                value={comments[seiteId] || ''}
                onChange={e => setComments(c => ({ ...c, [seiteId]: e.target.value }))}
                rows={2}
                style={{
                  width: '100%', boxSizing: 'border-box', padding: '8px 12px', borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border-light)', background: 'var(--bg-app)',
                  color: 'var(--text-primary)', fontSize: 12, fontFamily: 'var(--font-sans)', resize: 'vertical', outline: 'none',
                  marginBottom: 10,
                }}
              />
              <div style={{ display: 'flex', gap: 10 }}>
                <button onClick={() => handleDecision(seiteId, true)} disabled={sending[seiteId]}
                  style={{
                    padding: '8px 18px', background: '#1D9E75', color: '#fff', border: 'none',
                    borderRadius: 'var(--radius-md)', fontSize: 13, fontWeight: 600, cursor: 'pointer',
                    fontFamily: 'var(--font-sans)', opacity: sending[seiteId] ? 0.6 : 1,
                  }}>Freigeben</button>
                <button onClick={() => handleDecision(seiteId, false)} disabled={sending[seiteId]}
                  style={{
                    padding: '8px 18px', background: 'var(--status-danger-bg)', color: 'var(--status-danger-text)',
                    border: '1px solid var(--status-danger-text)', borderRadius: 'var(--radius-md)',
                    fontSize: 13, fontWeight: 600, cursor: 'pointer', fontFamily: 'var(--font-sans)',
                    opacity: sending[seiteId] ? 0.6 : 1,
                  }}>Ablehnen</button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Erledigte Freigaben */}
      {decided.length > 0 && (
        <div>
          <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-tertiary)', letterSpacing: '0.06em', marginBottom: 10 }}>
            ERLEDIGT ({decided.length})
          </div>
          {decided.map(([seiteId, item]) => (
            <div key={seiteId} style={{ ...cardStyle, opacity: 0.7 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>
                  {item.topic || item.label || `Seite ${seiteId}`}
                </div>
                <span style={{
                  padding: '2px 8px', borderRadius: 4, fontSize: 11, fontWeight: 600,
                  background: item.status === 'freigegeben' ? 'var(--status-success-bg)' : 'var(--status-danger-bg)',
                  color: item.status === 'freigegeben' ? 'var(--status-success-text)' : 'var(--status-danger-text)',
                }}>
                  {item.status === 'freigegeben' ? 'Freigegeben' : 'Abgelehnt'}
                </span>
              </div>
              {item.freigegeben_am && (
                <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 4 }}>
                  am {item.freigegeben_am}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

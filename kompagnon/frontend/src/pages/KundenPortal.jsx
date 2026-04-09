import { useState, useEffect, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import API_BASE_URL from '../config';

// ── Phase card ────────────────────────────────────────────────

function PhaseCard({ phase, isLast }) {
  const isDone   = phase.state === 'done';
  const isActive = phase.state === 'active';
  const isLocked = phase.state === 'locked';
  const pct = phase.total > 0 ? Math.round((phase.done / phase.total) * 100) : 0;

  const icon = isDone ? '✅' : isActive ? '⚙️' : '🔒';
  const barColor = isDone
    ? 'var(--status-success-text)'
    : isActive ? 'var(--brand-primary)' : 'var(--border-medium)';

  return (
    <div style={{ display: 'flex', gap: 0 }}>
      {/* Spine */}
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: 40, flexShrink: 0 }}>
        <div style={{
          width: 36, height: 36, borderRadius: '50%', fontSize: 16,
          background: isDone ? 'var(--status-success-bg)' : isActive ? 'rgba(0,142,170,0.12)' : 'var(--bg-app)',
          border: isDone ? '2px solid var(--status-success-text)' : isActive ? '2px solid var(--brand-primary)' : '2px solid var(--border-light)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1,
        }}>{icon}</div>
        {!isLast && (
          <div style={{ width: 2, flex: 1, minHeight: 24, background: isDone ? 'var(--status-success-text)' : 'var(--border-light)', margin: '4px 0', opacity: isDone ? 0.35 : 0.2 }} />
        )}
      </div>

      {/* Body */}
      <div style={{
        flex: 1, marginLeft: 14, marginBottom: isLast ? 0 : 12,
        padding: '14px 16px',
        background: isActive ? 'var(--bg-surface)' : 'var(--bg-app)',
        border: isActive ? '2px solid var(--brand-primary)' : '1px solid var(--border-light)',
        borderRadius: 'var(--radius-lg)',
        boxShadow: isActive ? '0 0 0 3px rgba(0,142,170,0.08)' : 'none',
        opacity: isLocked ? 0.55 : 1,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8, marginBottom: 4 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>Phase {phase.number}</span>
            {isActive && <span style={{ fontSize: 10, fontWeight: 600, background: 'var(--brand-primary)', color: '#fff', borderRadius: 99, padding: '1px 7px' }}>Aktiv</span>}
          </div>
          {!isLocked && (
            <span style={{ fontSize: 12, fontWeight: 600, color: isDone ? 'var(--status-success-text)' : 'var(--brand-primary)' }}>
              {isDone ? 'Abgeschlossen' : `${pct}%`}
            </span>
          )}
        </div>
        <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 3 }}>{phase.label}</div>
        <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: isLocked ? 0 : 10 }}>{phase.description}</div>
        {!isLocked && (
          <>
            <div style={{ height: 6, background: 'var(--border-light)', borderRadius: 3, overflow: 'hidden' }}>
              <div style={{ height: '100%', width: `${pct}%`, background: barColor, borderRadius: 3, transition: 'width 0.6s ease' }} />
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 4 }}>
              {phase.done} von {phase.total} Schritten erledigt
            </div>
          </>
        )}
      </div>
    </div>
  );
}

// ── Spinner ───────────────────────────────────────────────────

function Spinner() {
  return (
    <div style={{ display: 'flex', justifyContent: 'center', padding: '48px 0' }}>
      <div style={{ width: 28, height: 28, borderRadius: '50%', border: '3px solid var(--border-light)', borderTopColor: 'var(--brand-primary)', animation: 'spin 0.8s linear infinite' }} />
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────

export default function KundenPortal() {
  const { user, token } = useAuth();
  const h = { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) };

  const [project, setProject]     = useState(null);
  const [messages, setMessages]   = useState([]);
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading]     = useState(true);
  const [msgText, setMsgText]     = useState('');
  const [sending, setSending]     = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError]         = useState(null);
  const fileRef = useRef();
  const msgsEndRef = useRef();

  useEffect(() => {
    if (user?.role !== 'kunde') return;
    const load = async () => {
      try {
        const [projRes, msgRes, docRes] = await Promise.all([
          fetch(`${API_BASE_URL}/api/portal/me`,        { headers: h }),
          fetch(`${API_BASE_URL}/api/portal/messages`,  { headers: h }),
          fetch(`${API_BASE_URL}/api/portal/documents`, { headers: h }),
        ]);
        if (!projRes.ok) throw new Error(`Portal: ${projRes.status}`);
        const [proj, msgs, docs] = await Promise.all([projRes.json(), msgRes.json(), docRes.json()]);
        setProject(proj);
        setMessages(Array.isArray(msgs) ? msgs : []);
        setDocuments(Array.isArray(docs) ? docs : []);
      } catch (e) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []); // eslint-disable-line

  useEffect(() => {
    msgsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  if (user?.role !== 'kunde') return (
    <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-tertiary)' }}>Diese Seite ist nur für Kunden zugänglich.</div>
  );

  const sendMessage = async () => {
    if (!msgText.trim() || sending) return;
    setSending(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/portal/messages`, {
        method: 'POST', headers: h, body: JSON.stringify({ text: msgText.trim() }),
      });
      if (res.ok) {
        setMessages(prev => [...prev, { id: Date.now(), sender_role: 'kunde', text: msgText.trim(), created_at: new Date().toISOString() }]);
        setMsgText('');
      }
    } catch (e) { console.error(e); }
    setSending(false);
  };

  const uploadFile = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    const fd = new FormData();
    fd.append('file', file);
    try {
      const res = await fetch(`${API_BASE_URL}/api/portal/documents/upload`, {
        method: 'POST',
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: fd,
      });
      if (res.ok) {
        const data = await res.json();
        setDocuments(prev => [{ id: Date.now(), filename: data.filename, created_at: new Date().toISOString() }, ...prev]);
      }
    } catch (e) { console.error(e); }
    setUploading(false);
    e.target.value = '';
  };

  if (loading) return <Spinner />;

  if (error) return (
    <div style={{ padding: 32, textAlign: 'center' }}>
      <div style={{ fontSize: 13, color: 'var(--status-danger-text)', marginBottom: 12 }}>❌ {error}</div>
      <button onClick={() => { setError(null); setLoading(true); }} style={{ fontSize: 13, color: 'var(--brand-primary)', background: 'none', border: 'none', cursor: 'pointer' }}>Erneut versuchen</button>
    </div>
  );

  const phases      = project?.phases || [];
  const activePhase = phases.find(p => p.state === 'active');
  const donePhaseCnt = phases.filter(p => p.state === 'done').length;

  const sectionCard = { background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', padding: '16px 18px', marginTop: 24 };
  const sectionHead = { fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 14 };

  return (
    <div style={{ maxWidth: 660, margin: '0 auto', paddingBottom: 48 }}>

      {/* ── Header ── */}
      <div style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
          <h1 style={{ fontSize: 22, fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>Mein Projekt</h1>
          <span style={{ display: 'inline-block', padding: '3px 10px', borderRadius: 99, fontSize: 12, fontWeight: 600, background: 'var(--status-warning-bg)', color: 'var(--status-warning-text)' }}>
            {project?.project_status || 'In Bearbeitung'}
          </span>
        </div>
        <div style={{ fontSize: 14, color: 'var(--text-secondary)', marginTop: 4 }}>{project?.project_name || 'Mein Projekt'}</div>
        <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginTop: 6 }}>
          {donePhaseCnt} von {phases.length} Phasen abgeschlossen
          {activePhase && ` · Aktiv: Phase ${activePhase.number} – ${activePhase.label}`}
        </div>
      </div>

      {/* ── Overall progress ── */}
      <div style={{ ...sectionCard, marginTop: 0 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, color: 'var(--text-secondary)', marginBottom: 8 }}>
          <span style={{ fontWeight: 600 }}>Gesamtfortschritt</span>
          <span style={{ fontWeight: 600, color: 'var(--brand-primary)' }}>{phases.length ? Math.round((donePhaseCnt / phases.length) * 100) : 0}%</span>
        </div>
        <div style={{ height: 8, background: 'var(--border-light)', borderRadius: 4, overflow: 'hidden' }}>
          <div style={{ height: '100%', width: `${phases.length ? (donePhaseCnt / phases.length) * 100 : 0}%`, background: 'var(--brand-primary)', borderRadius: 4, transition: 'width 0.8s ease' }} />
        </div>
        <div style={{ display: 'flex', gap: 16, marginTop: 10, flexWrap: 'wrap' }}>
          {[
            { label: 'Abgeschlossen', count: phases.filter(p => p.state === 'done').length,   color: 'var(--status-success-text)' },
            { label: 'In Arbeit',     count: phases.filter(p => p.state === 'active').length, color: 'var(--brand-primary)' },
            { label: 'Ausstehend',    count: phases.filter(p => p.state === 'locked').length, color: 'var(--text-tertiary)' },
          ].map(s => (
            <div key={s.label} style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 12 }}>
              <div style={{ width: 8, height: 8, borderRadius: '50%', background: s.color, flexShrink: 0 }} />
              <span style={{ color: 'var(--text-secondary)' }}>{s.label}:</span>
              <span style={{ fontWeight: 600, color: s.color }}>{s.count}</span>
            </div>
          ))}
        </div>
      </div>

      {/* ── Phase timeline ── */}
      <div style={{ marginTop: 24 }}>
        {phases.map((phase, i) => (
          <PhaseCard key={phase.number} phase={phase} isLast={i === phases.length - 1} />
        ))}
      </div>

      {/* ── DNS-Guide (nur wenn Netlify-Domain gesetzt) ── */}
      {project?.netlify && project.netlify.domain && (
        <div style={{
          ...sectionCard,
          background: project.netlify.ssl_active
            ? 'var(--status-success-bg)'
            : 'var(--status-warning-bg)',
          border: `1px solid ${project.netlify.ssl_active ? 'var(--status-success-text)' : 'var(--status-warning-text)'}`,
        }}>
          {project.netlify.ssl_active ? (
            <>
              <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--status-success-text)', marginBottom: 6 }}>
                🎉 Ihre Website ist jetzt live!
              </div>
              <a
                href={`https://${project.netlify.domain}`}
                target="_blank"
                rel="noopener noreferrer"
                style={{ fontSize: 13, color: 'var(--brand-primary)', fontWeight: 600, textDecoration: 'none' }}
              >
                {project.netlify.domain} öffnen →
              </a>
            </>
          ) : (
            <>
              <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--status-warning-text)', marginBottom: 6 }}>
                ⚡ Letzter Schritt: Domain verbinden
              </div>
              <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 14, lineHeight: 1.6 }}>
                Tragen Sie bitte folgende DNS-Einstellungen bei Ihrem Domain-Anbieter
                (z.B. IONOS, Strato, united-domains) für <strong>{project.netlify.domain}</strong> ein.
                Sie haben diese Anleitung auch per E-Mail erhalten.
              </p>
              <div style={{ background: 'var(--bg-surface)', borderRadius: 8, overflow: 'hidden', border: '1px solid var(--border-light)' }}>
                <div style={{ display: 'grid', gridTemplateColumns: '70px 70px 1fr', padding: '8px 12px', background: 'var(--bg-app)', fontSize: 10, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  <span>Typ</span><span>Name</span><span>Wert</span>
                </div>
                {(project.netlify.guide?.records || []).map((r, i) => (
                  <div key={i} style={{ display: 'grid', gridTemplateColumns: '70px 70px 1fr', padding: '10px 12px', borderTop: '1px solid var(--border-light)', fontSize: 12, alignItems: 'center' }}>
                    <span style={{ fontWeight: 700, color: 'var(--brand-primary)' }}>{r.type}</span>
                    <span style={{ fontFamily: 'monospace', color: 'var(--text-primary)' }}>{r.name}</span>
                    <span style={{ fontFamily: 'monospace', color: 'var(--text-primary)', wordBreak: 'break-all' }}>{r.value}</span>
                  </div>
                ))}
              </div>
              <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 10, lineHeight: 1.5 }}>
                DNS-Änderungen werden innerhalb von 1–48 Stunden aktiv. Wir benachrichtigen Sie automatisch, sobald Ihre Website live ist.
              </div>
            </>
          )}
        </div>
      )}

      {/* ── Nachrichten ── */}
      <div style={sectionCard}>
        <div style={sectionHead}>💬 Nachrichten</div>
        <div style={{ maxHeight: 280, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 8, marginBottom: 12 }}>
          {messages.length === 0 && (
            <div style={{ fontSize: 12, color: 'var(--text-tertiary)', textAlign: 'center', padding: '20px 0' }}>Noch keine Nachrichten</div>
          )}
          {messages.map(m => (
            <div key={m.id} style={{
              alignSelf: m.sender_role === 'kunde' ? 'flex-end' : 'flex-start',
              maxWidth: '80%', padding: '8px 12px', borderRadius: 12,
              background: m.sender_role === 'kunde' ? 'var(--brand-primary)' : 'var(--bg-app)',
              color: m.sender_role === 'kunde' ? '#fff' : 'var(--text-primary)',
              fontSize: 13,
            }}>
              {m.sender_role !== 'kunde' && (
                <div style={{ fontSize: 10, fontWeight: 600, marginBottom: 3, color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Team</div>
              )}
              {m.text}
              <div style={{ fontSize: 10, opacity: 0.6, marginTop: 3, textAlign: 'right' }}>
                {new Date(m.created_at).toLocaleString('de-DE', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })}
              </div>
            </div>
          ))}
          <div ref={msgsEndRef} />
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <input
            value={msgText}
            onChange={e => setMsgText(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && !e.shiftKey && sendMessage()}
            placeholder="Nachricht schreiben…"
            style={{ flex: 1, padding: '8px 12px', fontSize: 13, border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)', background: 'var(--bg-app)', color: 'var(--text-primary)', fontFamily: 'var(--font-sans)' }}
          />
          <button onClick={sendMessage} disabled={sending || !msgText.trim()} style={{
            padding: '8px 14px', background: 'var(--brand-primary)', color: '#fff',
            border: 'none', borderRadius: 'var(--radius-md)', fontSize: 13, fontWeight: 600,
            cursor: sending ? 'wait' : 'pointer', opacity: !msgText.trim() ? 0.5 : 1,
            fontFamily: 'var(--font-sans)',
          }}>
            {sending ? '…' : '→'}
          </button>
        </div>
      </div>

      {/* ── Dokumente ── */}
      <div style={sectionCard}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
          <div style={sectionHead}>📎 Dokumente</div>
          <button onClick={() => fileRef.current?.click()} disabled={uploading} style={{
            padding: '6px 12px', background: 'var(--brand-primary)', color: '#fff',
            border: 'none', borderRadius: 'var(--radius-md)', fontSize: 12, fontWeight: 600,
            cursor: uploading ? 'wait' : 'pointer', fontFamily: 'var(--font-sans)',
          }}>
            {uploading ? 'Lädt…' : '+ Hochladen'}
          </button>
          <input ref={fileRef} type="file" style={{ display: 'none' }} onChange={uploadFile} />
        </div>
        {documents.length === 0 ? (
          <div style={{ fontSize: 12, color: 'var(--text-tertiary)', textAlign: 'center', padding: '16px 0' }}>Noch keine Dokumente hochgeladen</div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {documents.map(d => (
              <div key={d.id} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '8px 10px', background: 'var(--bg-app)', borderRadius: 'var(--radius-md)' }}>
                <span style={{ fontSize: 18, flexShrink: 0 }}>📄</span>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: 13, color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{d.filename}</div>
                  <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>
                    {d.created_at ? new Date(d.created_at).toLocaleDateString('de-DE') : ''}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div style={{ marginTop: 24, fontSize: 12, color: 'var(--text-tertiary)', textAlign: 'center' }}>
        Bei Fragen wende dich an dein KOMPAGNON-Team.
      </div>
    </div>
  );
}

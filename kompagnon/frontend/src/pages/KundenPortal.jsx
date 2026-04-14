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

      {/* ── Tor 2: Content-Freigabe-Karte (Baustein 3) ── */}
      <ContentApprovalCard project={project} token={token} onApproved={(data) => {
        setProject(prev => prev ? {
          ...prev,
          content_approved_at: data?.content_approved_at || new Date().toISOString(),
          content_approved_by: data?.content_approved_by || 'Sie',
        } : prev);
      }} />

      {/* ── Phase timeline ── */}
      <div style={{ marginTop: 24 }}>
        {phases.map((phase, i) => (
          <PhaseCard key={phase.number} phase={phase} isLast={i === phases.length - 1} />
        ))}
      </div>

      {/* ── Website-Versionen zur Auswahl ── */}
      <WebsiteVersionsSection
        project={project}
        token={token}
        onReload={async () => {
          try {
            const res = await fetch(`${API_BASE_URL}/api/portal/me`, { headers: { Authorization: `Bearer ${token}` } });
            if (res.ok) setProject(await res.json());
          } catch (_) {}
        }}
      />

      {/* ── Inspirations-URLs ── */}
      <InspirationsSection project={project} token={token} onSaved={() => {}} />

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


function WebsiteVersionsSection({ project, token, onReload }) {
  const [selecting, setSelecting] = useState(false);
  const versions = Array.isArray(project?.versions) ? project.versions : [];
  if (versions.length === 0) return null;

  const selected = versions.find(v => v.selected);

  const selectVersion = async (versionId) => {
    setSelecting(true);
    try {
      await fetch(`${API_BASE_URL}/api/portal/versions/${versionId}/select`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      });
      if (onReload) await onReload();
    } catch (_) {}
    setSelecting(false);
  };

  // Wenn bereits eine ausgewählt ist → Bestätigungs-Banner
  if (selected) {
    return (
      <div style={{
        background: 'var(--status-success-bg)',
        border: '1px solid var(--status-success-text)',
        borderRadius: 'var(--radius-lg)',
        padding: '18px 20px',
        marginTop: 24,
      }}>
        <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--status-success-text)', marginBottom: 6 }}>
          ✓ Ihre Auswahl ist gespeichert — Version {selected.version_label}
        </div>
        <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
          Wir beginnen jetzt mit der Umsetzung Ihrer gewählten Version.
        </div>
      </div>
    );
  }

  return (
    <div style={{
      background: 'var(--bg-surface)',
      border: '2px solid var(--brand-primary)',
      borderRadius: 'var(--radius-lg)',
      padding: '20px 22px',
      marginTop: 24,
    }}>
      <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--brand-primary)', marginBottom: 4 }}>
        🎨 Ihre 3 Website-Entwürfe sind bereit!
      </div>
      <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 16, lineHeight: 1.5 }}>
        Wählen Sie Ihren Favoriten — wir setzen ihn dann für Sie um.
      </p>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
        {versions.map(v => {
          let reasoning = {};
          try { reasoning = JSON.parse(v.ki_reasoning || '{}'); } catch {}
          return (
            <div key={v.id} style={{
              border: '1px solid var(--border-light)',
              borderRadius: 'var(--radius-md)',
              overflow: 'hidden',
              background: 'var(--bg-app)',
            }}>
              <div style={{ height: 200, overflow: 'hidden', position: 'relative', background: 'var(--bg-surface)' }}>
                <iframe
                  title={`preview-v${v.id}`}
                  src={`${API_BASE_URL}/api/portal/versions/${v.id}/preview`}
                  style={{
                    width: '200%', height: '400px',
                    transform: 'scale(0.5)', transformOrigin: 'top left',
                    border: 'none', pointerEvents: 'none',
                  }}
                />
              </div>
              <div style={{ padding: '14px 16px' }}>
                <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--brand-primary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 4 }}>
                  Version {v.version_label}
                </div>
                <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 6 }}>
                  {reasoning.titel || `Entwurf ${v.version_label}`}
                </div>
                {reasoning.beschreibung && (
                  <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 12, lineHeight: 1.5 }}>
                    {reasoning.beschreibung}
                  </div>
                )}
                <button
                  onClick={() => selectVersion(v.id)}
                  disabled={selecting}
                  style={{
                    width: '100%', padding: '11px',
                    background: 'var(--brand-primary)', color: '#fff',
                    border: 'none', borderRadius: 'var(--radius-md)',
                    fontSize: 13, fontWeight: 600,
                    cursor: selecting ? 'wait' : 'pointer',
                    fontFamily: 'var(--font-sans)',
                  }}
                >
                  {selecting ? 'Wird gespeichert…' : 'Diese Version auswählen →'}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}


function InspirationsSection({ project, token }) {
  const [urls, setUrls] = useState({ 1: '', 2: '', 3: '' });
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (project?.inspirations) {
      setUrls({
        1: project.inspirations.url_1 || '',
        2: project.inspirations.url_2 || '',
        3: project.inspirations.url_3 || '',
      });
    }
  }, [project?.inspirations]);

  const save = async () => {
    if (!project?.lead_id) return;
    setSaving(true);
    try {
      await fetch(`${API_BASE_URL}/api/leads/${project.lead_id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          inspiration_url_1: urls[1] || null,
          inspiration_url_2: urls[2] || null,
          inspiration_url_3: urls[3] || null,
        }),
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch (e) { /* ignore */ }
    setSaving(false);
  };

  return (
    <div style={{
      background: 'var(--bg-surface)', border: '1px solid var(--border-light)',
      borderRadius: 'var(--radius-lg)', padding: '18px 20px', marginTop: 24,
    }}>
      <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 4 }}>
        Ihre Inspirationen
      </div>
      <p style={{ fontSize: 12, color: 'var(--text-tertiary)', marginBottom: 14, lineHeight: 1.5 }}>
        Welche Websites gefallen Ihnen? (bis zu 3 URLs — optional). Wir nutzen sie als Referenz für Ihren Entwurf.
      </p>
      {[1, 2, 3].map(n => (
        <div key={n} style={{ marginBottom: 10 }}>
          <label style={{ fontSize: 11, color: 'var(--text-tertiary)', display: 'block', marginBottom: 4 }}>
            Website {n}
          </label>
          <input
            value={urls[n]}
            onChange={e => setUrls(p => ({ ...p, [n]: e.target.value }))}
            placeholder="https://www.beispiel.de"
            style={{
              width: '100%', boxSizing: 'border-box', padding: '9px 12px',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border-light)',
              background: 'var(--bg-app)', color: 'var(--text-primary)',
              fontSize: 13, fontFamily: 'var(--font-sans)', outline: 'none',
            }}
          />
        </div>
      ))}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginTop: 10 }}>
        <button onClick={save} disabled={saving} style={{
          padding: '8px 20px', borderRadius: 'var(--radius-md)',
          background: 'var(--brand-primary)', color: 'white',
          border: 'none', fontSize: 13, fontWeight: 600,
          cursor: saving ? 'wait' : 'pointer', fontFamily: 'var(--font-sans)',
        }}>
          {saving ? 'Speichern…' : 'Speichern'}
        </button>
        {saved && <span style={{ fontSize: 12, color: 'var(--status-success-text)' }}>✓ Gespeichert</span>}
      </div>
    </div>
  );
}

// ── Tor 2: Content-Freigabe-Karte (Baustein 3) ────────────────────────────────
//
// Sichtbar genau dann, wenn der Admin die Freigabe angefragt hat
// (content_approval_sent_at gesetzt) und der Kunde noch nicht
// freigegeben hat (content_approved_at NULL). Zeigt optional eine
// Sitemap-Vorschau. Nach erfolgreicher Freigabe schwenkt die Karte
// auf einen gruenen Bestaetigungs-Screen um.

function ContentApprovalCard({ project, token, onApproved }) {
  const sentAt = project?.content_approval_sent_at || null;
  const approvedAt = project?.content_approved_at || null;
  const sitemap = Array.isArray(project?.sitemap_preview) ? project.sitemap_preview : [];

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  // Wenn noch gar keine Freigabe angefragt wurde: Karte unsichtbar.
  if (!sentAt && !approvedAt) return null;

  // Bereits freigegeben → Bestaetigung
  if (approvedAt) {
    return (
      <div style={{
        marginTop: 24,
        padding: '18px 22px',
        background: '#EAF3DE',
        border: '1px solid #1D9E75',
        borderRadius: 'var(--radius-lg, 10px)',
        display: 'flex', alignItems: 'center', gap: 14,
      }}>
        <div style={{ fontSize: 26, lineHeight: 1, color: '#1D9E75' }}>✓</div>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 14, fontWeight: 700, color: '#0F5C43' }}>
            Freigabe erteilt — Ihr Design wird erstellt.
          </div>
          <div style={{ fontSize: 12, color: '#27500A', marginTop: 2 }}>
            Freigegeben am {new Date(approvedAt).toLocaleString('de-DE', { dateStyle: 'medium', timeStyle: 'short' })}
          </div>
        </div>
      </div>
    );
  }

  // sentAt gesetzt, approvedAt noch nicht → Freigabe-Aufforderung
  const approve = async () => {
    if (!project?.project_id || submitting) return;
    setSubmitting(true);
    setError('');
    try {
      const res = await fetch(
        `${API_BASE_URL}/api/projects/${project.project_id}/approve-content-portal`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
        },
      );
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(data?.detail || `Freigabe fehlgeschlagen (${res.status})`);
      }
      if (onApproved) onApproved(data);
    } catch (e) {
      setError(e?.message || 'Freigabe fehlgeschlagen');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={{
      marginTop: 24,
      padding: '20px 22px',
      background: '#FFF7E6',
      border: '1px solid #F5A623',
      borderRadius: 'var(--radius-lg, 10px)',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
        <div style={{ fontSize: 22, lineHeight: 1 }}>📋</div>
        <div style={{ fontSize: 15, fontWeight: 700, color: '#7A4E00' }}>
          Ihre Inhalte warten auf Freigabe
        </div>
      </div>
      <div style={{ fontSize: 13, color: '#5A4800', lineHeight: 1.55, marginBottom: 14 }}>
        Wir haben Sitemap und Texte für Ihre neue Website erstellt. Bitte
        prüfen Sie diese und erteilen Sie die Freigabe — danach starten wir
        mit dem Design.
      </div>

      {sitemap.length > 0 && (
        <div style={{
          background: '#FFFFFFDD',
          border: '1px solid #E8D7A8',
          borderRadius: 8,
          padding: '10px 14px',
          marginBottom: 14,
        }}>
          <div style={{
            fontSize: 10, fontWeight: 700, color: '#7A6500',
            textTransform: 'uppercase', letterSpacing: '0.06em',
            marginBottom: 6,
          }}>
            Vorschau · {sitemap.length} {sitemap.length === 1 ? 'Seite' : 'Seiten'}
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            {sitemap.map((p, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, color: '#5A4800' }}>
                <span style={{ fontWeight: 600 }}>{p.page_name}</span>
                <span style={{ fontSize: 10, color: '#94803D', textTransform: 'uppercase' }}>{p.page_type}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {error && (
        <div style={{
          background: '#FEE2E2',
          border: '1px solid #DC2626',
          borderRadius: 6,
          padding: '8px 12px',
          fontSize: 12,
          color: '#991B1B',
          marginBottom: 12,
          fontWeight: 600,
        }}>
          Fehler: {error}
        </div>
      )}

      <button
        onClick={approve}
        disabled={submitting}
        style={{
          padding: '11px 26px', borderRadius: 10, border: 'none',
          background: submitting ? '#94a3b8' : '#1D9E75',
          color: '#fff', fontSize: 14, fontWeight: 700,
          cursor: submitting ? 'not-allowed' : 'pointer',
          fontFamily: 'var(--font-sans, system-ui)',
          boxShadow: submitting ? 'none' : '0 1px 3px rgba(0,0,0,0.12)',
        }}
      >
        {submitting ? 'Wird übermittelt…' : '✓ Inhalte freigeben'}
      </button>
      <div style={{ fontSize: 11, color: '#94803D', marginTop: 8 }}>
        Freigabe angefragt am {new Date(sentAt).toLocaleString('de-DE', { dateStyle: 'medium', timeStyle: 'short' })}
      </div>
    </div>
  );
}

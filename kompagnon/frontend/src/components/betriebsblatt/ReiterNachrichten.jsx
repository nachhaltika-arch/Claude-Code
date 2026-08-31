/**
 * Der Nachrichten-Reiter des Betriebsblatts (L-25).
 *
 * Am 2026-08-31 aus `LeadProfile.jsx` herausgeloest — 137 Zeilen, eine sofort
 * aufgerufene Funktion. Ihr Vorspann laedt den Verlauf beim ersten Anzeigen.
 */
import EmptyState from '../ui/EmptyState';

export default function ReiterNachrichten({
  lead,
  messages,
  msgChannel,
  msgLoading,
  msgSending,
  msgSubject,
  msgText,
  sendMessage,
  setMsgChannel,
  setMsgSubject,
  setMsgText,
  setShowNewsletter,
}) {

  const fmtTime = (iso) => {
    if (!iso) return '';
    const d = new Date(iso);
    return d.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' });
  };
  const fmtDay = (iso) => {
    if (!iso) return '';
    const d = new Date(iso);
    const today = new Date();
    const yesterday = new Date(today); yesterday.setDate(today.getDate() - 1);
    if (d.toDateString() === today.toDateString()) return 'Heute';
    if (d.toDateString() === yesterday.toDateString()) return 'Gestern';
    return d.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' });
  };

  // Group messages by day for separators
  const grouped = [];
  let lastDay = null;
  for (const m of messages) {
    const day = fmtDay(m.created_at);
    if (day !== lastDay) { grouped.push({ type: 'sep', day }); lastDay = day; }
    grouped.push({ type: 'msg', msg: m });
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 0, border: '1px solid var(--border-light)', borderRadius: 12, overflow: 'hidden', background: 'var(--bg-app)' }}>

      {/* Newsletter Button */}
      <div style={{ padding: '10px 16px', borderBottom: '1px solid var(--border-light)', display: 'flex', justifyContent: 'flex-end' }}>
        <button onClick={() => setShowNewsletter(true)}
          style={{ padding: '6px 14px', border: 'none', borderRadius: 6,
                   background: 'var(--brand-primary)', color: 'var(--text-on-brand)', cursor: 'pointer',
                   fontSize: 13, fontWeight: 600 }}>
          Newsletter erstellen
        </button>
      </div>

      {/* Nachrichtenverlauf */}
      <div style={{ maxHeight: 500, overflowY: 'auto', padding: '16px 16px 8px', display: 'flex', flexDirection: 'column', gap: 12 }}>
        {msgLoading && messages.length === 0 && (
          <div style={{ textAlign: 'center', color: 'var(--text-tertiary)', fontSize: 13, padding: 32 }}>Nachrichten werden geladen…</div>
        )}
        {!msgLoading && messages.length === 0 && (
          <EmptyState icon="💬" title="Noch keine Nachrichten" description="Schreibe die erste Nachricht an den Kunden — sie erscheint direkt im Kundenportal. Nutze das Eingabefeld unten." compact />
        )}
        {grouped.map((item, i) => {
          if (item.type === 'sep') return (
            <div key={`sep-${i}`} style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--text-tertiary)', fontSize: 11 }}>
              <div style={{ flex: 1, height: 1, background: 'var(--border-light)' }} />
              {item.day}
              <div style={{ flex: 1, height: 1, background: 'var(--border-light)' }} />
            </div>
          );
          const m = item.msg;
          const isAdmin = m.sender_role === 'admin';
          return (
            <div key={m.id} style={{ display: 'flex', flexDirection: 'column', alignItems: isAdmin ? 'flex-end' : 'flex-start' }}>
              <div style={{ fontSize: 10, color: 'var(--text-tertiary)', marginBottom: 3, display: 'flex', alignItems: 'center', gap: 6 }}>
                <span style={{ fontWeight: 600 }}>{m.sender_name || (isAdmin ? 'Admin' : lead.company_name)}</span>
                <span>{fmtTime(m.created_at)}</span>
                {isAdmin && (
                  <span style={{ background: m.channel === 'email' ? 'var(--status-warning-bg)' : 'var(--status-success-bg)', color: m.channel === 'email' ? 'var(--status-warning-text)' : 'var(--status-success-text)', borderRadius: 4, padding: '1px 6px', fontSize: 10, fontWeight: 600 }}>
                    {m.channel === 'email' ? '✉️ E-Mail' : '💬 In-App'}
                  </span>
                )}
                {!isAdmin && !m.is_read && (
                  <span style={{ color: 'var(--status-info-text)', fontSize: 10 }}>🔵 Ungelesen</span>
                )}
              </div>
              <div style={{ maxWidth: '75%', padding: '10px 14px', borderRadius: isAdmin ? '14px 14px 4px 14px' : '14px 14px 14px 4px', background: isAdmin ? 'var(--brand-primary-light)' : 'var(--bg-surface)', border: '1px solid var(--border-light)', fontSize: 13, lineHeight: 1.6, color: 'var(--text-primary)', whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                {m.content}
              </div>
            </div>
          );
        })}
      </div>

      {/* Eingabebereich */}
      <div style={{ borderTop: '1px solid var(--border-light)', padding: '12px 16px', background: 'var(--bg-surface)', display: 'flex', flexDirection: 'column', gap: 10 }}>
        {msgChannel === 'email' && (
          <input aria-label="Betreff der E-Mail…"
            value={msgSubject}
            onChange={e => setMsgSubject(e.target.value)}
            placeholder="Betreff der E-Mail…"
            style={{ padding: '7px 12px', borderRadius: 8, border: '1px solid var(--border-light)', fontSize: 13, fontFamily: 'var(--font-sans)', background: 'var(--bg-app)', color: 'var(--text-primary)', outline: 'none' }}
          />
        )}
        <textarea aria-label="Nachricht schreiben… (Ctrl+Enter zum Senden)"
          value={msgText}
          onChange={e => setMsgText(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) sendMessage(); }}
          placeholder="Nachricht schreiben… (Ctrl+Enter zum Senden)"
          rows={3}
          style={{ padding: '10px 12px', borderRadius: 8, border: '1px solid var(--border-light)', fontSize: 13, fontFamily: 'var(--font-sans)', resize: 'vertical', background: 'var(--bg-app)', color: 'var(--text-primary)', outline: 'none', width: '100%', boxSizing: 'border-box' }}
        />
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 8 }}>
          <div style={{ display: 'flex', gap: 4 }}>
            {[{ id: 'in_app', label: '💬 In-App' }, { id: 'email', label: '✉️ + E-Mail' }].map(ch => (
              <button key={ch.id} onClick={() => setMsgChannel(ch.id)}
                style={{ padding: '6px 12px', borderRadius: 6, border: '1px solid var(--border-light)', fontSize: 12, fontWeight: msgChannel === ch.id ? 700 : 400, background: msgChannel === ch.id ? 'var(--brand-primary)' : 'var(--bg-app)', color: msgChannel === ch.id ? '#fff' : 'var(--text-secondary)', cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
                {ch.label}
              </button>
            ))}
          </div>
          <button onClick={sendMessage} disabled={msgSending || !msgText.trim()}
            style={{ padding: '8px 20px', background: 'var(--brand-primary)', color: 'var(--text-on-brand)', border: 'none', borderRadius: 8, fontWeight: 700, fontSize: 13, cursor: msgSending || !msgText.trim() ? 'not-allowed' : 'pointer', opacity: msgSending || !msgText.trim() ? 0.6 : 1, fontFamily: 'var(--font-sans)' }}>
            {msgSending ? 'Senden…' : 'Senden →'}
          </button>
        </div>
      </div>
    </div>
  );
}

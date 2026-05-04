import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import API_BASE_URL from '../../config';

const statusLabels = { open: 'Offen', in_progress: 'In Bearbeitung', resolved: 'Gelöst' };
const prioLabels  = { low: 'Niedrig', medium: 'Normal', high: 'Dringend' };

export default function SupportTickets() {
  const { token, user } = useAuth();
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState({ title: '', description: '', priority: 'medium', type: 'feedback' });
  const [sending, setSending] = useState(false);
  const [msg, setMsg] = useState('');

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/tickets/my`, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => r.json())
      .then(d => { setTickets(Array.isArray(d) ? d : []); setLoading(false); })
      .catch(() => setLoading(false));
  }, [token]);

  const submit = async () => {
    if (!form.title.trim() || !form.description.trim()) return;
    setSending(true);
    setMsg('');
    try {
      const res = await fetch(`${API_BASE_URL}/api/tickets/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ ...form, user_email: user?.email || '', user_name: user?.first_name || '' }),
      });
      if (res.ok) {
        const data = await res.json();
        setMsg(`Ticket ${data.ticket_number} erstellt`);
        setForm({ title: '', description: '', priority: 'medium', type: 'feedback' });
        // Reload list
        const r2 = await fetch(`${API_BASE_URL}/api/tickets/my`, { headers: { Authorization: `Bearer ${token}` } });
        if (r2.ok) setTickets(await r2.json());
      }
    } catch { setMsg('Fehler beim Erstellen'); }
    setSending(false);
  };

  const cardStyle = {
    background: 'var(--bg-surface)', borderRadius: 'var(--radius-lg)',
    border: '1px solid var(--border-light)', padding: '20px 22px', marginBottom: 14,
  };
  const inputStyle = {
    width: '100%', boxSizing: 'border-box', padding: '10px 12px', borderRadius: 'var(--radius-md)',
    border: '1px solid var(--border-light)', background: 'var(--bg-app)',
    color: 'var(--text-primary)', fontSize: 13, fontFamily: 'var(--font-sans)', outline: 'none',
  };
  const badgeStyle = (bg, color) => ({
    display: 'inline-block', padding: '2px 8px', borderRadius: 4,
    fontSize: 11, fontWeight: 600, background: bg, color,
  });

  return (
    <div style={{ maxWidth: 720, margin: '0 auto', padding: '0 0 40px' }}>
      <div style={{ fontSize: 20, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 20 }}>
        🎫 Support-Tickets
      </div>

      {/* Neues Ticket */}
      <div style={cardStyle}>
        <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 12 }}>Neues Ticket</div>
        <input style={{ ...inputStyle, marginBottom: 10 }} placeholder="Titel des Problems"
          value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} />
        <textarea style={{ ...inputStyle, marginBottom: 10, minHeight: 80, resize: 'vertical' }}
          placeholder="Beschreibung…" value={form.description}
          onChange={e => setForm({ ...form, description: e.target.value })} />
        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          <select style={{ ...inputStyle, width: 'auto' }} value={form.priority}
            onChange={e => setForm({ ...form, priority: e.target.value })}>
            <option value="low">Niedrig</option>
            <option value="medium">Normal</option>
            <option value="high">Dringend</option>
          </select>
          <button onClick={submit} disabled={sending} style={{
            padding: '9px 20px', background: 'var(--brand-primary)', color: '#fff', border: 'none',
            borderRadius: 'var(--radius-md)', fontSize: 13, fontWeight: 600, cursor: 'pointer',
            fontFamily: 'var(--font-sans)', opacity: sending ? 0.6 : 1,
          }}>{sending ? 'Wird gesendet…' : 'Ticket senden'}</button>
        </div>
        {msg && <div style={{ marginTop: 8, fontSize: 12, color: msg.includes('Fehler') ? 'var(--status-danger-text)' : 'var(--status-success-text)' }}>{msg}</div>}
      </div>

      {/* Liste */}
      {loading && <div style={{ color: 'var(--text-tertiary)', fontSize: 13 }}>Wird geladen…</div>}
      {!loading && tickets.length === 0 && (
        <div style={{ ...cardStyle, textAlign: 'center', color: 'var(--text-tertiary)', fontSize: 13 }}>
          Noch keine Tickets. Erstellen Sie oben ein neues Ticket.
        </div>
      )}
      {tickets.map(t => (
        <div key={t.id} style={cardStyle}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12 }}>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>{t.title}</div>
              <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 4, lineHeight: 1.5 }}>{t.description}</div>
              <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 6 }}>
                {t.ticket_number} · {t.created_at ? new Date(t.created_at).toLocaleDateString('de-DE') : ''}
              </div>
            </div>
            <div style={{ display: 'flex', gap: 6, flexShrink: 0 }}>
              <span style={badgeStyle(
                t.priority === 'high' ? 'var(--status-danger-bg)' : 'var(--status-warning-bg)',
                t.priority === 'high' ? 'var(--status-danger-text)' : 'var(--status-warning-text)',
              )}>{prioLabels[t.priority] || t.priority}</span>
              <span style={badgeStyle(
                t.status === 'resolved' ? 'var(--status-success-bg)' : 'var(--status-info-bg)',
                t.status === 'resolved' ? 'var(--status-success-text)' : 'var(--status-info-text)',
              )}>{statusLabels[t.status] || t.status || 'Offen'}</span>
            </div>
          </div>
          {t.admin_notes && (
            <div style={{ marginTop: 10, padding: '8px 12px', background: 'var(--bg-app)', borderRadius: 'var(--radius-md)', fontSize: 12, color: 'var(--text-secondary)' }}>
              <strong>Antwort:</strong> {t.admin_notes}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

import React, { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import { apiCall } from '../context/AuthContext';

const N = '#0F1E3A';
const TYPE_B = { bug: { label: 'Fehler', color: '#dc2626', bg: '#fee2e2' }, feature: { label: 'Idee', color: '#7c3aed', bg: '#faf5ff' }, feedback: { label: 'Feedback', color: '#008EAA', bg: '#f0fafa' }, question: { label: 'Frage', color: '#d97706', bg: '#fffbeb' } };
const STATUS_B = { open: { label: 'Offen', color: '#2563eb', bg: '#eff6ff' }, in_progress: { label: 'In Bearbeitung', color: '#d97706', bg: '#fffbeb' }, resolved: { label: 'Geloest', color: '#059669', bg: '#f0fdf4' }, closed: { label: 'Geschlossen', color: '#64748b', bg: '#f1f5f9' } };
const PRIO_B = { low: { label: 'Niedrig', color: '#64748b' }, medium: { label: 'Mittel', color: '#d97706' }, high: { label: 'Hoch', color: '#dc2626' }, critical: { label: 'Kritisch', color: '#7c3aed' } };

export default function Tickets() {
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(null);
  const [notes, setNotes] = useState('');
  const [newStatus, setNewStatus] = useState('');
  const [saving, setSaving] = useState(false);
  const [filter, setFilter] = useState('');

  useEffect(() => { load(); }, []);
  const load = async () => {
    setLoading(true);
    try { const r = await apiCall('/api/tickets/' + (filter ? `?status=${filter}` : '')); if (r.ok) setTickets(await r.json()); }
    catch { /* */ } finally { setLoading(false); }
  };

  useEffect(() => { load(); }, [filter]); // eslint-disable-line

  const openDetail = (t) => { setSelected(t); setNotes(t.admin_notes || ''); setNewStatus(t.status); };

  const saveTicket = async () => {
    if (!selected) return;
    setSaving(true);
    try {
      const r = await apiCall(`/api/tickets/${selected.id}`, { method: 'PATCH', body: JSON.stringify({ status: newStatus, admin_notes: notes }) });
      if (r.ok) { toast.success('Ticket aktualisiert'); setSelected(null); load(); }
    } finally { setSaving(false); }
  };

  if (loading) return <div style={{ padding: 40, textAlign: 'center', color: '#64748b' }}>Laden...</div>;

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20, flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 800, color: N, margin: 0 }}>Support Tickets</h1>
          <p style={{ fontSize: 13, color: '#64748b', margin: '4px 0 0' }}>{tickets.length} Tickets</p>
        </div>
        <div style={{ display: 'flex', gap: 6 }}>
          {['', 'open', 'in_progress', 'resolved', 'closed'].map((f) => (
            <button key={f} onClick={() => setFilter(f)} style={{
              padding: '6px 12px', borderRadius: 20, border: 'none', fontSize: 12, fontWeight: 600, cursor: 'pointer',
              background: filter === f ? N : '#f1f5f9', color: filter === f ? '#fff' : '#475569',
            }}>{f ? (STATUS_B[f]?.label || f) : 'Alle'}</button>
          ))}
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {tickets.map((t) => {
          const tb = TYPE_B[t.type] || TYPE_B.feedback;
          const sb = STATUS_B[t.status] || STATUS_B.open;
          const pb = PRIO_B[t.priority] || PRIO_B.medium;
          return (
            <div key={t.id} onClick={() => openDetail(t)} style={{
              background: '#fff', border: '1px solid #eef0f8', borderRadius: 10, padding: '14px 18px', cursor: 'pointer',
              display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap', transition: 'border-color 0.15s',
            }}>
              <span style={{ fontSize: 12, fontFamily: 'monospace', color: '#64748b', minWidth: 110 }}>{t.ticket_number}</span>
              <span style={{ background: tb.bg, color: tb.color, fontSize: 11, fontWeight: 700, padding: '2px 8px', borderRadius: 6 }}>{tb.label}</span>
              <span style={{ fontSize: 13, fontWeight: 700, color: N, flex: 1, minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{t.title}</span>
              <span style={{ fontSize: 11, color: '#64748b' }}>{t.user_name || t.user_email || 'Anonym'}</span>
              <span style={{ fontSize: 11, color: pb.color, fontWeight: 700 }}>{pb.label}</span>
              <span style={{ background: sb.bg, color: sb.color, fontSize: 11, fontWeight: 700, padding: '2px 8px', borderRadius: 6 }}>{sb.label}</span>
              <span style={{ fontSize: 11, color: '#94a3b8' }}>{t.created_at ? String(t.created_at).slice(0, 10) : ''}</span>
            </div>
          );
        })}
        {tickets.length === 0 && <div style={{ textAlign: 'center', padding: 40, color: '#64748b' }}>Keine Tickets gefunden</div>}
      </div>

      {/* Detail Modal */}
      {selected && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}
          onClick={(e) => { if (e.target === e.currentTarget) setSelected(null); }}>
          <div onClick={(e) => e.stopPropagation()} style={{ background: '#fff', borderRadius: 16, padding: 28, maxWidth: 560, width: '100%', maxHeight: '85vh', overflowY: 'auto', boxShadow: '0 20px 60px rgba(0,0,0,0.2)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
              <div>
                <div style={{ fontSize: 12, fontFamily: 'monospace', color: '#64748b', marginBottom: 4 }}>{selected.ticket_number}</div>
                <h3 style={{ fontSize: 18, fontWeight: 800, color: N, margin: 0 }}>{selected.title}</h3>
              </div>
              <button onClick={() => setSelected(null)} style={{ background: '#f1f5f9', border: 'none', borderRadius: '50%', width: 32, height: 32, cursor: 'pointer', fontSize: 16 }}>✕</button>
            </div>
            <div style={{ background: '#f8fafc', borderRadius: 10, padding: 16, marginBottom: 16, fontSize: 14, color: '#475569', lineHeight: 1.6, whiteSpace: 'pre-wrap' }}>{selected.description}</div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 10, marginBottom: 16, fontSize: 12 }}>
              <div><span style={{ color: '#64748b' }}>Von:</span> <strong>{selected.user_name || selected.user_email || 'Anonym'}</strong></div>
              <div><span style={{ color: '#64748b' }}>Typ:</span> <strong>{TYPE_B[selected.type]?.label}</strong></div>
              <div><span style={{ color: '#64748b' }}>Seite:</span> <span style={{ color: '#008EAA', wordBreak: 'break-all' }}>{selected.page_url}</span></div>
            </div>
            <div style={{ marginBottom: 12 }}>
              <label style={{ fontSize: 11, fontWeight: 700, color: '#64748b', display: 'block', marginBottom: 6, textTransform: 'uppercase' }}>Status</label>
              <select value={newStatus} onChange={(e) => setNewStatus(e.target.value)} style={{ width: '100%', padding: '8px 12px', border: '1.5px solid #e2e8f0', borderRadius: 8, fontSize: 14 }}>
                <option value="open">Offen</option>
                <option value="in_progress">In Bearbeitung</option>
                <option value="resolved">Geloest</option>
                <option value="closed">Geschlossen</option>
              </select>
            </div>
            <div style={{ marginBottom: 16 }}>
              <label style={{ fontSize: 11, fontWeight: 700, color: '#64748b', display: 'block', marginBottom: 6, textTransform: 'uppercase' }}>Admin-Notizen</label>
              <textarea value={notes} onChange={(e) => setNotes(e.target.value)} rows={3} style={{ width: '100%', padding: '8px 12px', border: '1.5px solid #e2e8f0', borderRadius: 8, fontSize: 14, resize: 'vertical', boxSizing: 'border-box' }} placeholder="Interne Notizen..." />
            </div>
            <div style={{ display: 'flex', gap: 10 }}>
              <button onClick={() => setSelected(null)} style={{ flex: 1, padding: 11, background: '#f1f5f9', color: N, border: 'none', borderRadius: 8, fontSize: 14, fontWeight: 600, cursor: 'pointer', minHeight: 44 }}>Abbrechen</button>
              <button onClick={saveTicket} disabled={saving} style={{ flex: 1, padding: 11, background: N, color: '#fff', border: 'none', borderRadius: 8, fontSize: 14, fontWeight: 700, cursor: 'pointer', minHeight: 44, opacity: saving ? 0.6 : 1 }}>{saving ? 'Speichern...' : 'Speichern'}</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useScreenSize } from '../utils/responsive';
import API_BASE_URL from '../config';

const N = '#0F1E3A';
const TC = { bug: { label: 'Fehler', icon: '🐛', color: '#dc2626', bg: '#fee2e2' }, feature: { label: 'Idee', icon: '💡', color: '#7c3aed', bg: '#f5f3ff' }, feedback: { label: 'Feedback', icon: '💬', color: '#008EAA', bg: '#f0fafa' }, question: { label: 'Frage', icon: '❓', color: '#d97706', bg: '#fffbeb' } };
const SC = { open: { label: 'Offen', icon: '🔵', color: '#2563eb', bg: '#dbeafe' }, in_progress: { label: 'In Bearbeitung', icon: '🟡', color: '#d97706', bg: '#fef3c7' }, resolved: { label: 'Geloest', icon: '🟢', color: '#059669', bg: '#d1fae5' }, closed: { label: 'Geschlossen', icon: '⚫', color: '#64748b', bg: '#f1f5f9' } };
const PC = { low: { label: 'Niedrig', color: '#64748b', bg: '#f1f5f9' }, medium: { label: 'Mittel', color: '#d97706', bg: '#fef3c7' }, high: { label: 'Hoch', color: '#dc2626', bg: '#fee2e2' }, critical: { label: 'Kritisch', color: '#7c3aed', bg: '#f5f3ff' } };

export default function Tickets() {
  const { token } = useAuth();
  const { isMobile } = useScreenSize();
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(null);
  const [fStatus, setFStatus] = useState('open');
  const [fType, setFType] = useState('');
  const [search, setSearch] = useState('');
  const [saving, setSaving] = useState(false);
  const [note, setNote] = useState('');
  const [nStatus, setNStatus] = useState('');

  const hdr = () => ({ 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) });

  useEffect(() => { load(); }, []); // eslint-disable-line
  const load = async () => { try { const r = await fetch(`${API_BASE_URL}/api/tickets/`, { headers: hdr() }); setTickets(await r.json()); } catch { /**/ } finally { setLoading(false); } };

  const openT = (t) => { setSelected(t); setNote(t.admin_notes || ''); setNStatus(t.status); };
  const save = async () => {
    if (!selected) return; setSaving(true);
    try { await fetch(`${API_BASE_URL}/api/tickets/${selected.id}`, { method: 'PATCH', headers: hdr(), body: JSON.stringify({ status: nStatus, admin_notes: note }) }); setSelected(null); load(); }
    finally { setSaving(false); }
  };

  const filtered = tickets.filter((t) => {
    if (fStatus && t.status !== fStatus) return false;
    if (fType && t.type !== fType) return false;
    if (search && ![t.title, t.ticket_number, t.user_name, t.user_email].some((f) => f?.toLowerCase().includes(search.toLowerCase()))) return false;
    return true;
  }).sort((a, b) => ({ critical: 0, high: 1, medium: 2, low: 3 }[a.priority] || 2) - ({ critical: 0, high: 1, medium: 2, low: 3 }[b.priority] || 2));

  const kpis = { open: tickets.filter((t) => t.status === 'open').length, wip: tickets.filter((t) => t.status === 'in_progress').length, crit: tickets.filter((t) => t.priority === 'critical' && t.status === 'open').length, done: tickets.filter((t) => t.status === 'resolved').length };

  if (loading) return <div style={{ padding: 40, textAlign: 'center', color: '#64748b' }}>Laden...</div>;

  return (
    <div>
      <div style={{ marginBottom: 20 }}>
        <h1 style={{ fontSize: 22, fontWeight: 800, color: N, margin: '0 0 4px' }}>Support Tickets</h1>
        <p style={{ fontSize: 13, color: '#64748b', margin: 0 }}>{filtered.length} Tickets{tickets.length !== filtered.length ? ` von ${tickets.length}` : ''}</p>
      </div>

      {/* KPIs */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: 10, marginBottom: 20 }}>
        {[{ l: 'Offen', v: kpis.open, c: '#2563eb', i: '📬', f: () => setFStatus('open') }, { l: 'In Bearbeitung', v: kpis.wip, c: '#d97706', i: '⚙️', f: () => setFStatus('in_progress') }, { l: 'Kritisch', v: kpis.crit, c: '#dc2626', i: '🚨', f: () => setFStatus('open') }, { l: 'Geloest', v: kpis.done, c: '#059669', i: '✅', f: () => setFStatus('resolved') }].map((k) => (
          <div key={k.l} onClick={k.f} style={{ background: '#fff', borderRadius: 10, padding: '14px 16px', border: '1px solid #e2e8f0', cursor: 'pointer' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
              <span style={{ fontSize: 20 }}>{k.i}</span>
              <span style={{ fontSize: 22, fontWeight: 900, color: k.c }}>{k.v}</span>
            </div>
            <div style={{ fontSize: 11, fontWeight: 600, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.06em' }}>{k.l}</div>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 16, flexWrap: 'wrap' }}>
        <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Suche..." style={{ flex: '1 1 200px', padding: '8px 12px', border: '1.5px solid #e2e8f0', borderRadius: 8, fontSize: 13, outline: 'none', boxSizing: 'border-box' }} />
        {[{ v: '', l: 'Alle' }, { v: 'open', l: 'Offen' }, { v: 'in_progress', l: 'Bearbeitung' }, { v: 'resolved', l: 'Geloest' }, { v: 'closed', l: 'Geschlossen' }].map((s) => (
          <button key={s.v} onClick={() => setFStatus(s.v)} style={{
            padding: '8px 14px', borderRadius: 8, border: `1.5px solid ${fStatus === s.v ? '#008EAA' : '#e2e8f0'}`,
            background: fStatus === s.v ? '#f0fafa' : '#fff', color: fStatus === s.v ? '#008EAA' : '#64748b',
            fontSize: 12, fontWeight: fStatus === s.v ? 700 : 400, cursor: 'pointer', whiteSpace: 'nowrap', minHeight: 36,
          }}>{s.l}</button>
        ))}
        <select value={fType} onChange={(e) => setFType(e.target.value)} style={{ padding: '8px 12px', border: '1.5px solid #e2e8f0', borderRadius: 8, fontSize: 13, outline: 'none', cursor: 'pointer' }}>
          <option value="">Alle Typen</option>
          {Object.entries(TC).map(([k, v]) => <option key={k} value={k}>{v.icon} {v.label}</option>)}
        </select>
      </div>

      {/* Two-column: List + Detail */}
      <div style={{ display: 'grid', gridTemplateColumns: selected && !isMobile ? '1fr 400px' : '1fr', gap: 16, alignItems: 'flex-start' }}>
        {/* List */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {filtered.length === 0 && <div style={{ textAlign: 'center', padding: 40, color: '#94a3b8', background: '#fff', borderRadius: 12, border: '1px solid #e2e8f0' }}>Keine Tickets</div>}
          {filtered.map((t) => {
            const tc = TC[t.type] || TC.feedback;
            const sc = SC[t.status] || SC.open;
            const pc = PC[t.priority] || PC.medium;
            const sel = selected?.id === t.id;
            return (
              <div key={t.id} onClick={() => openT(t)} style={{
                background: sel ? '#f0fafa' : '#fff', borderRadius: 10, border: `1.5px solid ${sel ? '#008EAA' : '#e2e8f0'}`,
                padding: '14px 16px', cursor: 'pointer', transition: 'all 0.15s',
              }}>
                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 10, marginBottom: 6 }}>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4, flexWrap: 'wrap' }}>
                      <span style={{ fontSize: 11, fontWeight: 700, color: '#94a3b8' }}>{t.ticket_number}</span>
                      <span style={{ fontSize: 11, fontWeight: 700, color: tc.color, background: tc.bg, padding: '2px 7px', borderRadius: 4 }}>{tc.icon} {tc.label}</span>
                      <span style={{ fontSize: 11, fontWeight: 700, color: pc.color, background: pc.bg, padding: '2px 7px', borderRadius: 4 }}>{pc.label}</span>
                    </div>
                    <div style={{ fontSize: 14, fontWeight: 700, color: N, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{t.title}</div>
                    <div style={{ fontSize: 12, color: '#64748b', display: 'flex', gap: 10, flexWrap: 'wrap', marginTop: 4 }}>
                      {t.user_name && <span>👤 {t.user_name}</span>}
                      <span>{String(t.created_at || '').slice(0, 10)}</span>
                    </div>
                  </div>
                  <span style={{ fontSize: 11, fontWeight: 700, color: sc.color, background: sc.bg, padding: '4px 10px', borderRadius: 6, flexShrink: 0 }}>{sc.label}</span>
                </div>
                <div style={{ fontSize: 12, color: '#64748b', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', paddingTop: 6, borderTop: '1px solid #f1f5f9' }}>{t.description}</div>
              </div>
            );
          })}
        </div>

        {/* Detail */}
        {selected && (
          <div style={{ background: '#fff', borderRadius: 12, border: '1px solid #e2e8f0', overflow: 'hidden', position: isMobile ? 'fixed' : 'sticky', top: isMobile ? 0 : 20, left: isMobile ? 0 : 'auto', right: isMobile ? 0 : 'auto', bottom: isMobile ? 0 : 'auto', zIndex: isMobile ? 200 : 1, maxHeight: isMobile ? '100vh' : 'auto', overflowY: 'auto' }}>
            <div style={{ background: N, padding: '14px 18px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div>
                <div style={{ color: 'rgba(255,255,255,0.75)', fontSize: 11, marginBottom: 2 }}>{selected.ticket_number}</div>
                <div style={{ color: '#fff', fontWeight: 700, fontSize: 14 }}>Ticket bearbeiten</div>
              </div>
              <button onClick={() => setSelected(null)} style={{ background: 'rgba(255,255,255,0.1)', border: 'none', borderRadius: '50%', width: 28, height: 28, color: '#fff', cursor: 'pointer', fontSize: 14, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>✕</button>
            </div>
            <div style={{ padding: 18 }}>
              <div style={{ display: 'flex', gap: 8, marginBottom: 14, flexWrap: 'wrap' }}>
                {(() => { const c = TC[selected.type] || TC.feedback; return <span style={{ fontSize: 12, fontWeight: 700, color: c.color, background: c.bg, padding: '4px 10px', borderRadius: 6 }}>{c.icon} {c.label}</span>; })()}
                {(() => { const c = PC[selected.priority] || PC.medium; return <span style={{ fontSize: 12, fontWeight: 700, color: c.color, background: c.bg, padding: '4px 10px', borderRadius: 6 }}>{c.label}</span>; })()}
              </div>
              <div style={{ fontSize: 16, fontWeight: 800, color: N, marginBottom: 8 }}>{selected.title}</div>
              <div style={{ fontSize: 12, color: '#64748b', marginBottom: 14, display: 'flex', flexDirection: 'column', gap: 4 }}>
                {selected.user_name && <span>👤 {selected.user_name}</span>}
                {selected.user_email && <span>✉️ {selected.user_email}</span>}
                <span>{String(selected.created_at || '').slice(0, 16).replace('T', ' ')}</span>
                {selected.page_url && <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>🔗 {selected.page_url}</span>}
              </div>
              <Lbl>Beschreibung</Lbl>
              <div style={{ background: '#f8fafc', borderRadius: 8, padding: '12px 14px', fontSize: 13, color: '#334155', lineHeight: 1.6, marginBottom: 16, whiteSpace: 'pre-wrap' }}>{selected.description}</div>
              {selected.browser_info && (<><Lbl>Browser</Lbl><div style={{ background: '#f8fafc', borderRadius: 8, padding: '8px 12px', fontSize: 11, color: '#64748b', marginBottom: 16, wordBreak: 'break-all' }}>{selected.browser_info}</div></>)}
              <Lbl>Status</Lbl>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6, marginBottom: 16 }}>
                {Object.entries(SC).map(([id, c]) => (
                  <button key={id} onClick={() => setNStatus(id)} style={{
                    padding: '8px 10px', borderRadius: 8, border: `1.5px solid ${nStatus === id ? c.color : '#e2e8f0'}`,
                    background: nStatus === id ? c.bg : '#fff', color: nStatus === id ? c.color : '#64748b',
                    fontSize: 12, fontWeight: nStatus === id ? 700 : 400, cursor: 'pointer', textAlign: 'left', minHeight: 36,
                  }}>{c.icon} {c.label}</button>
                ))}
              </div>
              <Lbl>Entwickler-Notiz</Lbl>
              <textarea value={note} onChange={(e) => setNote(e.target.value)} placeholder="Interne Notiz..." rows={3} style={{ width: '100%', padding: '10px 12px', border: '1.5px solid #e2e8f0', borderRadius: 8, fontSize: 13, resize: 'vertical', boxSizing: 'border-box', outline: 'none', marginBottom: 14 }} />
              <button onClick={save} disabled={saving} style={{ width: '100%', padding: 11, background: saving ? '#64748b' : '#059669', color: '#fff', border: 'none', borderRadius: 8, fontSize: 14, fontWeight: 700, cursor: saving ? 'not-allowed' : 'pointer', minHeight: 44, opacity: saving ? 0.6 : 1 }}>
                {saving ? 'Speichern...' : 'Speichern'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function Lbl({ children }) { return <div style={{ fontSize: 11, fontWeight: 700, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 6 }}>{children}</div>; }

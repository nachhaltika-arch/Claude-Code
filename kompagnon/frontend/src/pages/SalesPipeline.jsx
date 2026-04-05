import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Badge from '../components/ui/Badge';
import Button from '../components/ui/Button';
import API_BASE_URL from '../config';

const COLUMNS = [
  { id: 'new', label: 'Neue Leads', icon: '🆕', color: '#008EAA', desc: 'Frisch importiert oder auditiert' },
  { id: 'contacted', label: 'Kontaktiert', icon: '📞', color: '#7c3aed', desc: 'Erste Kontaktaufnahme erfolgt' },
  { id: 'qualified', label: 'Qualifiziert', icon: '✅', color: '#059669', desc: 'Bedarf bestätigt' },
  { id: 'proposal_sent', label: 'Angebot gesendet', icon: '📄', color: '#d97706', desc: 'Angebot liegt beim Kunden' },
  { id: 'won', label: 'Gewonnen', icon: '🏆', color: '#16a34a', desc: 'Auftrag erhalten' },
  { id: 'lost', label: 'Verloren', icon: '❌', color: '#dc2626', desc: 'Kein Abschluss' },
];

export default function SalesPipeline() {
  const navigate = useNavigate();
  const { token, user } = useAuth();
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dragging, setDragging] = useState(null);
  const [dragOver, setDragOver] = useState(null);
  const [deleteConfirm, setDeleteConfirm] = useState(null);
  const [search, setSearch] = useState('');
  const [filterTrade, setFilterTrade] = useState('');

  const h = { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) };

  const fetchedRef = useRef(false);

  useEffect(() => {
    if (fetchedRef.current) return;
    fetchedRef.current = true;
    loadLeads();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const loadLeads = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/leads/`, { headers: h });
      const data = await res.json();
      const salesLeads = Array.isArray(data)
        ? data.filter(l => !(l.status === 'won' && l.lead_source === 'stripe_checkout'))
        : [];
      setLeads(salesLeads);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  };

  const updateStatus = async (leadId, status) => {
    try {
      await fetch(`${API_BASE_URL}/api/leads/${leadId}`, { method: 'PATCH', headers: h, body: JSON.stringify({ status }) });
      setLeads(prev => prev.map(l => l.id === leadId ? { ...l, status } : l));
    } catch {}
  };

  const deleteLead = async (leadId) => {
    try {
      await fetch(`${API_BASE_URL}/api/leads/${leadId}`, { method: 'DELETE', headers: h });
      setLeads(prev => prev.filter(l => l.id !== leadId));
      setDeleteConfirm(null);
    } catch {}
  };

  const handleDragStart = (e, lead) => { setDragging(lead); e.dataTransfer.effectAllowed = 'move'; };
  const handleDrop = (e, colId) => { e.preventDefault(); if (dragging && dragging.status !== colId) updateStatus(dragging.id, colId); setDragging(null); setDragOver(null); };

  const trades = [...new Set(leads.map(l => l.trade).filter(Boolean))];

  const getColLeads = (colId) =>
    leads.filter(l => {
      if (l.status !== colId) return false;
      if (search && !(l.company_name || '').toLowerCase().includes(search.toLowerCase()) && !(l.city || '').toLowerCase().includes(search.toLowerCase())) return false;
      if (filterTrade && l.trade !== filterTrade) return false;
      return true;
    }).sort((a, b) => (b.analysis_score || 0) - (a.analysis_score || 0));

  const convRate = leads.length ? Math.round(leads.filter(l => l.status === 'won').length / leads.length * 100) : 0;

  if (loading) return (
    <div style={{ display: 'flex', gap: 10 }}>
      {[1,2,3,4,5].map(i => <div key={i} className="skeleton" style={{ flex: 1, height: 300, borderRadius: 'var(--radius-lg)' }} />)}
    </div>
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16, animation: 'fadeIn 0.3s ease' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
        <div>
          <p style={{ fontSize: 12, color: 'var(--text-tertiary)', margin: 0 }}>
            {leads.length} Leads · {convRate}% Abschlussrate · {leads.filter(l => l.status === 'won').length} gewonnen
          </p>
        </div>
        <Button variant="primary" size="sm" onClick={() => navigate('/app/import')}>+ Leads importieren</Button>
      </div>

      {/* KPI Leiste */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: 10 }}>
        {COLUMNS.map(col => {
          const count = leads.filter(l => l.status === col.id).length;
          return (
            <div key={col.id} style={{
              background: 'var(--bg-surface)', border: '1px solid var(--border-light)',
              borderRadius: 'var(--radius-lg)', padding: '12px 14px', borderTop: `3px solid ${col.color}`,
            }}>
              <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginBottom: 4 }}>{col.icon} {col.label}</div>
              <div style={{ fontSize: 22, fontWeight: 600, color: col.color }}>{count}</div>
            </div>
          );
        })}
      </div>

      {/* Filter */}
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        <div style={{ position: 'relative', flex: '1 1 180px' }}>
          <span style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-tertiary)', fontSize: 13 }}>🔍</span>
          <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Firma oder Stadt suchen..."
            style={{ width: '100%', padding: '8px 12px 8px 30px', border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)', fontSize: 13, fontFamily: 'var(--font-sans)', outline: 'none', boxSizing: 'border-box', color: 'var(--text-primary)', background: 'var(--bg-surface)' }} />
        </div>
        {trades.length > 0 && (
          <select value={filterTrade} onChange={e => setFilterTrade(e.target.value)}
            style={{ padding: '8px 12px', border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)', fontSize: 13, fontFamily: 'var(--font-sans)', background: 'var(--bg-surface)', color: 'var(--text-primary)', cursor: 'pointer', outline: 'none' }}>
            <option value="">Alle Gewerke</option>
            {trades.map(t => <option key={t} value={t}>{t}</option>)}
          </select>
        )}
        {(search || filterTrade) && (
          <button onClick={() => { setSearch(''); setFilterTrade(''); }}
            style={{ padding: '8px 12px', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)', background: 'var(--bg-surface)', color: 'var(--status-danger-text)', fontSize: 12, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
            ✕ Filter
          </button>
        )}
      </div>

      {/* Kanban */}
      <div style={{ display: 'flex', gap: 10, width: '100%', alignItems: 'flex-start', overflowX: 'auto' }}>
        {COLUMNS.map(col => {
          const colLeads = getColLeads(col.id);
          const isOver = dragOver === col.id;
          return (
            <div key={col.id}
              onDragOver={e => { e.preventDefault(); setDragOver(col.id); }}
              onDrop={e => handleDrop(e, col.id)}
              onDragLeave={() => setDragOver(null)}
              style={{
                flex: '1 1 0', minWidth: 170,
                background: isOver ? `${col.color}08` : 'var(--bg-app)',
                borderRadius: 'var(--radius-lg)',
                border: `1.5px ${isOver ? 'dashed' : 'solid'} ${isOver ? col.color : 'var(--border-light)'}`,
                transition: 'all 0.15s',
              }}>
              <div style={{ padding: '10px 12px 0', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 5, minWidth: 0 }}>
                  <span style={{ fontSize: 13 }}>{col.icon}</span>
                  <span style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.04em', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{col.label}</span>
                </div>
                <span style={{ background: `${col.color}20`, color: col.color, borderRadius: 'var(--radius-full)', padding: '1px 7px', fontSize: 11, fontWeight: 600, flexShrink: 0 }}>{colLeads.length}</span>
              </div>
              <div style={{ height: 2, background: col.color, margin: '8px 12px', borderRadius: 2 }} />
              <div style={{ padding: '0 8px 8px', display: 'flex', flexDirection: 'column', gap: 6 }}>
                {colLeads.map(lead => (
                  <SalesCard key={lead.id} lead={lead} col={col} columns={COLUMNS} onDragStart={handleDragStart}
                    onOpen={() => navigate(`/app/leads/${lead.id}`)}
                    onAudit={() => navigate(`/app/audit?url=${encodeURIComponent(lead.website_url || '')}&lead_id=${lead.id}`)}
                    onDelete={() => setDeleteConfirm(lead.id)} onStatusChange={updateStatus} isAdmin={user?.role === 'admin'} />
                ))}
                {colLeads.length === 0 && (
                  <div style={{ padding: '14px 8px', textAlign: 'center', color: 'var(--text-tertiary)', fontSize: 11, border: '1px dashed var(--border-light)', borderRadius: 'var(--radius-md)' }}>Leer</div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Lösch Modal */}
      {deleteConfirm && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(15,28,32,0.5)', backdropFilter: 'blur(4px)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}
          onClick={() => setDeleteConfirm(null)}>
          <div onClick={e => e.stopPropagation()} style={{ background: 'var(--bg-surface)', borderRadius: 'var(--radius-xl)', padding: 28, maxWidth: 360, width: '100%', textAlign: 'center' }}>
            <div style={{ fontSize: 36, marginBottom: 12 }}>🗑️</div>
            <h3 style={{ fontSize: 16, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 8 }}>Lead löschen?</h3>
            <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 20 }}>
              <strong>{leads.find(l => l.id === deleteConfirm)?.company_name}</strong> wird dauerhaft gelöscht.
            </p>
            <div style={{ display: 'flex', gap: 10 }}>
              <Button variant="secondary" fullWidth onClick={() => setDeleteConfirm(null)}>Abbrechen</Button>
              <Button variant="danger" fullWidth onClick={() => deleteLead(deleteConfirm)}>Löschen</Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Helpers ────────────────────────────────────────────────────────────────

function getDomain(url) {
  if (!url) return null;
  try { return new URL(url.startsWith('http') ? url : 'https://' + url).hostname.replace('www.', ''); } catch { return url; }
}

function scoreStyle(score) {
  if (!score || score === 0) return null;
  if (score >= 70) return { bg: '#EAF4E0', text: '#3B6D11' };
  if (score >= 50) return { bg: '#FEF3DC', text: '#BA7517' };
  return { bg: '#FDEAEA', text: '#E24B4A' };
}

const CERT_STYLES = {
  bronze:  { bg: '#F5E6D3', text: '#7D4A1A' },
  silber:  { bg: '#EFEFEF', text: '#5A5A5A' },
  gold:    { bg: '#FEF3DC', text: '#BA7517' },
  platin:  { bg: '#E6F1FB', text: '#185FA5' },
  diamant: { bg: '#EAF4E0', text: '#1D9E75' },
};

function fmtDate(iso) {
  if (!iso) return null;
  return new Date(iso).toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: '2-digit' });
}

// ── Sales Card ──

function SalesCard({ lead, col, columns, onDragStart, onOpen, onAudit, onDelete, onStatusChange, isAdmin }) {
  const [menuOpen, setMenuOpen] = useState(false);
  const domain    = getDomain(lead.website_url);
  const sc        = scoreStyle(lead.analysis_score);
  const certKey   = (lead.audit_level || '').toLowerCase();
  const certStyle = CERT_STYLES[certKey];

  return (
    <div
      draggable
      onDragStart={e => onDragStart(e, lead)}
      onClick={onOpen}
      style={{
        background: 'var(--bg-surface)', borderRadius: 'var(--radius-md)',
        border: '1px solid var(--border-light)', padding: '11px 12px',
        cursor: 'grab', boxShadow: 'var(--shadow-card)', transition: 'all 0.15s',
        position: 'relative', display: 'flex', flexDirection: 'column', gap: 7,
      }}
      onMouseEnter={e => { e.currentTarget.style.borderColor = col.color; e.currentTarget.style.boxShadow = 'var(--shadow-elevated)'; }}
      onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--border-light)'; e.currentTarget.style.boxShadow = 'var(--shadow-card)'; }}
    >
      {/* ── Row 1: avatar + name + menu ── */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 6 }}>
        {/* Favicon / Initialen-Kreis */}
        <div style={{ flexShrink: 0, marginTop: 1 }}>
          {lead.favicon_url ? (
            <img
              src={lead.favicon_url}
              alt=""
              style={{ width: 28, height: 28, borderRadius: 4, objectFit: 'contain', background: '#fff', padding: 2, display: 'block' }}
              onError={e => { e.target.style.display = 'none'; e.target.nextSibling.style.display = 'flex'; }}
            />
          ) : null}
          <div style={{
            width: 28, height: 28, borderRadius: 4,
            background: col.color + '22', color: col.color,
            fontSize: 12, fontWeight: 700,
            display: lead.favicon_url ? 'none' : 'flex',
            alignItems: 'center', justifyContent: 'center',
            flexShrink: 0,
          }}>
            {(lead.company_name || '?')[0].toUpperCase()}
          </div>
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {lead.company_name || 'Unbekannt'}
          </div>
          {domain && (
            <div style={{ fontSize: 10, color: 'var(--brand-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', marginTop: 1 }}>
              {domain}
            </div>
          )}
        </div>
        {/* Context menu */}
        <div style={{ position: 'relative', flexShrink: 0 }} onClick={e => e.stopPropagation()}>
          <button
            onClick={e => { e.stopPropagation(); setMenuOpen(!menuOpen); }}
            style={{ background: 'none', border: 'none', color: 'var(--text-tertiary)', cursor: 'pointer', fontSize: 15, padding: '0 2px', lineHeight: 1 }}
          >⋯</button>
          {menuOpen && (
            <>
              <div style={{ position: 'fixed', inset: 0, zIndex: 49 }} onClick={() => setMenuOpen(false)} />
              <div style={{ position: 'absolute', top: '100%', right: 0, background: 'var(--bg-surface)', borderRadius: 'var(--radius-md)', boxShadow: 'var(--shadow-elevated)', border: '1px solid var(--border-light)', zIndex: 50, minWidth: 160, maxWidth: 'calc(100vw - 24px)', overflow: 'hidden' }}
                onClick={e => e.stopPropagation()}>
                <MItem onClick={() => { onOpen(); setMenuOpen(false); }}>👤 Kundenkartei</MItem>
                <MItem onClick={() => { onAudit(); setMenuOpen(false); }}>🔍 Audit starten</MItem>
                <div style={{ borderTop: '1px solid var(--border-light)', padding: '4px 0' }}>
                  <div style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', padding: '4px 12px', letterSpacing: '0.06em' }}>Status ändern</div>
                  {columns.filter(c => c.id !== lead.status).map(c => (
                    <MItem key={c.id} onClick={() => { onStatusChange(lead.id, c.id); setMenuOpen(false); }} style={{ color: c.color }}>{c.icon} {c.label}</MItem>
                  ))}
                </div>
                {isAdmin && (
                  <div style={{ borderTop: '1px solid var(--status-danger-bg)' }}>
                    <MItem onClick={() => { onDelete(); setMenuOpen(false); }} danger>🗑️ Löschen</MItem>
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </div>

      {/* ── Row 2: Stadt + Gewerk tags ── */}
      {(lead.city || lead.trade) && (
        <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
          {lead.city  && <span style={{ fontSize: 10, color: 'var(--text-secondary)', background: 'var(--bg-app)', border: '1px solid var(--border-light)', padding: '1px 6px', borderRadius: 10 }}>📍 {lead.city}</span>}
          {lead.trade && <span style={{ fontSize: 10, color: 'var(--text-secondary)', background: 'var(--bg-app)', border: '1px solid var(--border-light)', padding: '1px 6px', borderRadius: 10 }}>🔧 {lead.trade}</span>}
        </div>
      )}

      {/* ── Row 3: Score badge + Zertifizierung ── */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 5, flexWrap: 'wrap' }}>
        {sc ? (
          <span style={{ fontSize: 11, fontWeight: 700, padding: '2px 7px', borderRadius: 10, background: sc.bg, color: sc.text }}>
            ⭐ {lead.analysis_score}
          </span>
        ) : (
          <span style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>Kein Audit</span>
        )}
        {certStyle && (
          <span style={{ fontSize: 10, fontWeight: 600, padding: '2px 7px', borderRadius: 10, background: certStyle.bg, color: certStyle.text }}>
            🏅 {lead.audit_level}
          </span>
        )}
      </div>

      {/* ── Row 4: Erstellungsdatum ── */}
      {lead.created_at && (
        <div style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>
          📅 {fmtDate(lead.created_at)}
        </div>
      )}
    </div>
  );
}

function MItem({ children, onClick, danger, style }) {
  return (
    <button onClick={onClick} style={{
      width: '100%', display: 'flex', alignItems: 'center', gap: 6,
      padding: '6px 12px', background: 'transparent', border: 'none',
      borderRadius: 'var(--radius-sm)', cursor: 'pointer', fontSize: 12, textAlign: 'left',
      color: danger ? 'var(--status-danger-text)' : 'var(--text-secondary)',
      fontFamily: 'var(--font-sans)', transition: 'background 0.1s', ...style,
    }}
    onMouseEnter={e => e.currentTarget.style.background = danger ? 'var(--status-danger-bg)' : 'var(--bg-hover)'}
    onMouseLeave={e => e.currentTarget.style.background = 'transparent'}>
      {children}
    </button>
  );
}

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useScreenSize } from '../utils/responsive';
import API_BASE_URL from '../config';

const NAVY = '#0F1E3A';

const COLUMNS = [
  { id: 'new', label: 'Neu / Auditiert', icon: '🆕', color: '#008EAA', bg: '#f0fafa' },
  { id: 'contacted', label: 'Kontaktiert', icon: '📞', color: '#7c3aed', bg: '#faf5ff' },
  { id: 'qualified', label: 'Qualifiziert', icon: '✅', color: '#059669', bg: '#f0fdf4' },
  { id: 'proposal_sent', label: 'Angebot', icon: '📄', color: '#d97706', bg: '#fffbeb' },
  { id: 'won', label: 'Gewonnen', icon: '🏆', color: '#16a34a', bg: '#f0fdf4' },
  { id: 'lost', label: 'Verloren', icon: '❌', color: '#dc2626', bg: '#fff5f5' },
];

const LEVEL_CFG = {
  'Homepage Standard Platin': { label: 'Platin', icon: '💎', color: '#4a90d9', bg: '#e8f4fd' },
  'Homepage Standard Gold': { label: 'Gold', icon: '🥇', color: '#b8860b', bg: '#fef9e7' },
  'Homepage Standard Silber': { label: 'Silber', icon: '🥈', color: '#708090', bg: '#f4f6f7' },
  'Homepage Standard Bronze': { label: 'Bronze', icon: '🥉', color: '#cd7f32', bg: '#fdf2e9' },
  'Nicht konform': { label: 'Nicht konform', icon: '⚠️', color: '#dc2626', bg: '#fee2e2' },
};

export default function LeadPipeline() {
  const navigate = useNavigate();
  const { user, token } = useAuth();
  const { isMobile } = useScreenSize();
  const [activeTab, setActiveTab] = useState(0);
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [deleteConfirm, setDeleteConfirm] = useState(null);
  const [dragOver, setDragOver] = useState(null);
  const [dragging, setDragging] = useState(null);

  const headers = () => ({ 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) });

  useEffect(() => { loadLeads(); }, []); // eslint-disable-line

  const loadLeads = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/leads/`, { headers: headers() });
      const data = await res.json();
      setLeads(Array.isArray(data) ? data : []);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  };

  const getColumnLeads = (colId) =>
    leads.filter((l) => l.status === colId).sort((a, b) => (b.analysis_score || 0) - (a.analysis_score || 0));

  const updateStatus = async (leadId, newStatus) => {
    try {
      await fetch(`${API_BASE_URL}/api/leads/${leadId}`, { method: 'PATCH', headers: headers(), body: JSON.stringify({ status: newStatus }) });
      setLeads((prev) => prev.map((l) => (l.id === leadId ? { ...l, status: newStatus } : l)));
    } catch (e) { console.error(e); }
  };

  const handleDragStart = (e, lead) => { setDragging(lead); e.dataTransfer.effectAllowed = 'move'; };
  const handleDragOver = (e, colId) => { e.preventDefault(); setDragOver(colId); };
  const handleDrop = (e, colId) => { e.preventDefault(); if (dragging && dragging.status !== colId) updateStatus(dragging.id, colId); setDragging(null); setDragOver(null); };

  const deleteLead = async (id) => {
    try {
      await fetch(`${API_BASE_URL}/api/leads/${id}`, { method: 'DELETE', headers: headers() });
      setLeads((prev) => prev.filter((l) => l.id !== id));
      setDeleteConfirm(null);
    } catch (e) { console.error(e); }
  };

  if (loading) return <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: 200, color: '#64748b', fontSize: 14 }}>Leads werden geladen...</div>;

  return (
    <div>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24, flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 800, color: NAVY, margin: 0 }}>Lead Pipeline</h1>
          <p style={{ fontSize: 13, color: '#64748b', margin: '4px 0 0' }}>{leads.length} Leads · Drag & Drop zum Verschieben</p>
        </div>
        <button onClick={() => navigate('/app/import')} style={{ background: NAVY, color: '#fff', border: 'none', borderRadius: 8, padding: '9px 18px', fontSize: 13, fontWeight: 700, cursor: 'pointer' }}>
          + Lead hinzufuegen
        </button>
      </div>

      {/* Kanban */}
      {isMobile ? (
        /* Mobile: Tab-based view */
        <div style={{ width: '100%' }}>
          <div style={{ display: 'flex', gap: 6, overflowX: 'auto', paddingBottom: 4, marginBottom: 16, scrollbarWidth: 'none' }}>
            {COLUMNS.map((col, idx) => {
              const count = leads.filter((l) => l.status === col.id).length;
              return (
                <button key={col.id} onClick={() => setActiveTab(idx)} style={{
                  flexShrink: 0, padding: '8px 14px', borderRadius: 20, border: 'none',
                  background: activeTab === idx ? col.color : '#f1f5f9', color: activeTab === idx ? '#fff' : '#475569',
                  fontSize: 13, fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6, minHeight: 36, whiteSpace: 'nowrap',
                }}>
                  {col.icon} {col.label}
                  <span style={{ background: activeTab === idx ? 'rgba(255,255,255,0.3)' : col.color + '20', color: activeTab === idx ? '#fff' : col.color, borderRadius: 10, padding: '0 6px', fontSize: 11, fontWeight: 700 }}>{count}</span>
                </button>
              );
            })}
          </div>
          <div style={{ width: '100%' }}>
            {getColumnLeads(COLUMNS[activeTab].id).map((lead) => (
              <div key={lead.id} style={{ marginBottom: 8 }}>
                <LeadCard lead={lead} onDragStart={() => {}} onOpenProfile={() => navigate(`/app/leads/${lead.id}`)}
                  onStartAudit={() => navigate(`/app/audit?url=${encodeURIComponent(lead.website_url || '')}&lead_id=${lead.id}`)}
                  onDelete={() => setDeleteConfirm(lead.id)} isAdmin={user?.role === 'admin'} columns={COLUMNS} onStatusChange={updateStatus} />
              </div>
            ))}
            {getColumnLeads(COLUMNS[activeTab].id).length === 0 && (
              <div style={{ textAlign: 'center', padding: '40px 20px', color: '#94a3b8', fontSize: 14, border: '2px dashed #e2e8f0', borderRadius: 12 }}>Keine Leads in dieser Spalte</div>
            )}
          </div>
        </div>
      ) : (
        /* Desktop: Flex columns */
        <div style={{ display: 'flex', gap: 12, width: '100%', alignItems: 'flex-start' }}>
          {COLUMNS.map((col) => {
            const colLeads = getColumnLeads(col.id);
            const over = dragOver === col.id;
            return (
              <div key={col.id} onDragOver={(e) => handleDragOver(e, col.id)} onDrop={(e) => handleDrop(e, col.id)} onDragLeave={() => setDragOver(null)}
                style={{ flex: '1 1 0', minWidth: 160, background: over ? col.bg : '#f8fafc', borderRadius: 12, border: over ? `2px dashed ${col.color}` : '2px solid transparent', transition: 'all 0.15s', minHeight: 200 }}>
                <div style={{ padding: '12px 14px 0', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, minWidth: 0 }}>
                    <span style={{ fontSize: 14, flexShrink: 0 }}>{col.icon}</span>
                    <span style={{ fontSize: 12, fontWeight: 700, color: NAVY, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{col.label}</span>
                  </div>
                  <div style={{ background: col.color + '20', color: col.color, borderRadius: 20, padding: '2px 7px', fontSize: 11, fontWeight: 700, flexShrink: 0 }}>{colLeads.length}</div>
                </div>
                <div style={{ height: 3, background: col.color, margin: '8px 14px', borderRadius: 2 }} />
                <div style={{ padding: '0 8px 8px', display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {colLeads.map((lead) => (
                    <LeadCard key={lead.id} lead={lead} onDragStart={handleDragStart}
                      onOpenProfile={() => navigate(`/app/leads/${lead.id}`)}
                      onStartAudit={() => navigate(`/app/audit?url=${encodeURIComponent(lead.website_url || '')}&lead_id=${lead.id}`)}
                      onDelete={() => setDeleteConfirm(lead.id)} isAdmin={user?.role === 'admin'} columns={COLUMNS} onStatusChange={updateStatus} />
                  ))}
                  {colLeads.length === 0 && (
                    <div style={{ padding: '16px 8px', textAlign: 'center', color: '#94a3b8', fontSize: 11, border: '1.5px dashed #e2e8f0', borderRadius: 8 }}>Keine Leads</div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Delete Modal */}
      {deleteConfirm && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }} onClick={() => setDeleteConfirm(null)}>
          <div onClick={(e) => e.stopPropagation()} style={{ background: '#fff', borderRadius: 16, padding: 28, maxWidth: 380, width: '100%', textAlign: 'center', boxShadow: '0 20px 60px rgba(0,0,0,0.2)' }}>
            <div style={{ fontSize: 40, marginBottom: 12 }}>🗑️</div>
            <h3 style={{ fontSize: 18, fontWeight: 800, color: NAVY, marginBottom: 8 }}>Lead loeschen?</h3>
            <p style={{ fontSize: 13, color: '#64748b', marginBottom: 24 }}>
              <strong>{leads.find((l) => l.id === deleteConfirm)?.company_name}</strong> und alle Audits werden geloescht.
            </p>
            <div style={{ display: 'flex', gap: 10 }}>
              <button onClick={() => setDeleteConfirm(null)} style={{ flex: 1, padding: 11, background: '#f1f5f9', color: NAVY, border: 'none', borderRadius: 8, fontSize: 14, fontWeight: 600, cursor: 'pointer', minHeight: 44 }}>Abbrechen</button>
              <button onClick={() => deleteLead(deleteConfirm)} style={{ flex: 1, padding: 11, background: '#ef4444', color: '#fff', border: 'none', borderRadius: 8, fontSize: 14, fontWeight: 700, cursor: 'pointer', minHeight: 44 }}>Loeschen</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Lead Card ──

function LeadCard({ lead, onDragStart, onOpenProfile, onStartAudit, onDelete, isAdmin, columns, onStatusChange }) {
  const [menuOpen, setMenuOpen] = useState(false);
  const hasAudit = lead.analysis_score > 0;
  const lcfg = LEVEL_CFG[lead.current_level] || null;
  const scoreColor = (s) => s >= 85 ? '#16a34a' : s >= 70 ? '#2563eb' : s >= 50 ? '#d97706' : '#dc2626';

  const domain = (url) => {
    if (!url) return null;
    try { return new URL(url.startsWith('http') ? url : 'https://' + url).hostname.replace('www.', ''); } catch { return url; }
  };

  return (
    <div draggable onDragStart={(e) => onDragStart(e, lead)} style={{
      background: '#fff', borderRadius: 10, border: '1px solid #e2e8f0', padding: 12, cursor: 'grab',
      boxShadow: '0 1px 4px rgba(0,0,0,0.06)', transition: 'all 0.15s', position: 'relative',
    }}>
      {/* Name + menu */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 6, gap: 6 }}>
        <div onClick={onOpenProfile} style={{ fontSize: 13, fontWeight: 700, color: NAVY, cursor: 'pointer', flex: 1, minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={lead.company_name}>
          {lead.company_name || 'Unbekannt'}
        </div>
        <div style={{ position: 'relative' }}>
          <button onClick={(e) => { e.stopPropagation(); setMenuOpen(!menuOpen); }} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8', fontSize: 16, padding: '0 2px' }}>⋯</button>
          {menuOpen && (
            <div style={{ position: 'absolute', top: '100%', right: 0, background: '#fff', borderRadius: 8, boxShadow: '0 8px 24px rgba(0,0,0,0.15)', border: '1px solid #e2e8f0', zIndex: 50, minWidth: 160, overflow: 'hidden' }}
              onClick={(e) => e.stopPropagation()}>
              <button onClick={() => { onOpenProfile(); setMenuOpen(false); }} style={MI}>👤 Kundenkartei</button>
              <button onClick={() => { onStartAudit(); setMenuOpen(false); }} style={MI}>🔍 Audit starten</button>
              <div style={{ borderTop: '1px solid #f1f5f9', padding: '4px 0' }}>
                <div style={{ fontSize: 10, fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', padding: '4px 12px', letterSpacing: '0.08em' }}>Status aendern</div>
                {columns.filter((c) => c.id !== lead.status).map((col) => (
                  <button key={col.id} onClick={() => { onStatusChange(lead.id, col.id); setMenuOpen(false); }} style={{ ...MI, color: col.color }}>{col.icon} {col.label}</button>
                ))}
              </div>
              {isAdmin && (
                <div style={{ borderTop: '1px solid #fee2e2' }}>
                  <button onClick={() => { onDelete(); setMenuOpen(false); }} style={{ ...MI, color: '#ef4444' }}>🗑️ Loeschen</button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Domain */}
      {lead.website_url && (
        <div style={{ fontSize: 11, color: '#008EAA', marginBottom: 8, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', display: 'flex', alignItems: 'center', gap: 4 }}>
          <span>🌐</span>
          <a href={lead.website_url.startsWith('http') ? lead.website_url : 'https://' + lead.website_url} target="_blank" rel="noopener noreferrer"
            onClick={(e) => e.stopPropagation()} style={{ color: '#008EAA', textDecoration: 'none', overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {domain(lead.website_url)}
          </a>
        </div>
      )}

      {/* Score */}
      {hasAudit ? (
        <div style={{ marginBottom: 8 }}>
          {lcfg && (
            <div style={{ display: 'inline-flex', alignItems: 'center', gap: 4, background: lcfg.bg, color: lcfg.color, borderRadius: 6, padding: '2px 8px', fontSize: 11, fontWeight: 700, marginBottom: 6 }}>
              {lcfg.icon} {lcfg.label}
            </div>
          )}
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div style={{ flex: 1, height: 5, background: '#e2e8f0', borderRadius: 3, overflow: 'hidden' }}>
              <div style={{ width: `${lead.analysis_score}%`, height: '100%', background: scoreColor(lead.analysis_score), borderRadius: 3, transition: 'width 0.6s ease' }} />
            </div>
            <span style={{ fontSize: 12, fontWeight: 700, color: scoreColor(lead.analysis_score), flexShrink: 0 }}>{lead.analysis_score}/100</span>
          </div>
        </div>
      ) : (
        <div style={{ fontSize: 11, color: '#94a3b8', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 4 }}>⚪ Noch kein Audit</div>
      )}

      {/* Tags */}
      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
        {lead.city && <span style={{ fontSize: 10, color: '#64748b', background: '#f1f5f9', padding: '2px 7px', borderRadius: 4 }}>📍 {lead.city}</span>}
        {lead.trade && <span style={{ fontSize: 10, color: '#64748b', background: '#f1f5f9', padding: '2px 7px', borderRadius: 4 }}>🔧 {lead.trade}</span>}
      </div>
    </div>
  );
}

const MI = { width: '100%', display: 'flex', alignItems: 'center', gap: 8, padding: '8px 12px', background: 'none', border: 'none', cursor: 'pointer', fontSize: 13, color: '#0F1E3A', textAlign: 'left', whiteSpace: 'nowrap' };

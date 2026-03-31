import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useScreenSize } from '../utils/responsive';
import API_BASE_URL from '../config';
import Badge from '../components/ui/Badge';

const COLUMNS = [
  { id: 'won', label: 'Auftrag erhalten', icon: '✅', color: '#059669' },
  { id: 'onboarding', label: 'Onboarding', icon: '🚀', color: '#008EAA' },
  { id: 'in_progress', label: 'In Umsetzung', icon: '⚙️', color: '#d97706' },
  { id: 'review', label: 'Abnahme', icon: '👁️', color: '#7c3aed' },
  { id: 'live', label: 'Live', icon: '🌐', color: '#16a34a' },
];

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
      const projectLeads = Array.isArray(data)
        ? data.filter(l => l.status === 'won' || l.lead_source === 'stripe_checkout' || l.lead_source === 'llm_landing')
        : [];
      setLeads(projectLeads);
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

  if (loading) return (
    <div style={{ display: 'flex', gap: 12 }}>
      {[1,2,3,4,5].map(i => <div key={i} className="skeleton" style={{ flex: 1, height: 300, borderRadius: 'var(--radius-lg)' }} />)}
    </div>
  );

  return (
    <div style={{ animation: 'fadeIn 0.3s ease' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
        <div>
          <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginBottom: 2 }}>
            {leads.length} aktive Kundenprojekte · Drag & Drop zum Verschieben
          </div>
        </div>
      </div>

      {/* Kanban Board */}
      {isMobile ? (
        <div>
          <div style={{ display: 'flex', gap: 4, overflowX: 'auto', paddingBottom: 8, marginBottom: 12 }}>
            {COLUMNS.map((col, idx) => {
              const count = getColumnLeads(col.id).length;
              return (
                <button key={col.id} onClick={() => setActiveTab(idx)} style={{
                  flexShrink: 0, padding: '6px 12px', borderRadius: 'var(--radius-full)', border: 'none',
                  background: activeTab === idx ? 'var(--bg-active)' : 'transparent',
                  color: activeTab === idx ? 'var(--brand-primary)' : 'var(--text-secondary)',
                  fontSize: 12, fontWeight: activeTab === idx ? 500 : 400, cursor: 'pointer',
                  fontFamily: 'var(--font-sans)',
                }}>
                  {col.label} <span style={{ marginLeft: 4, opacity: 0.6 }}>{count}</span>
                </button>
              );
            })}
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {getColumnLeads(COLUMNS[activeTab].id).map(lead => (
              <LeadCard key={lead.id} lead={lead} onDragStart={() => {}} onOpenProfile={() => navigate(`/app/leads/${lead.id}`)}
                onStartAudit={() => navigate(`/app/audit?url=${encodeURIComponent(lead.website_url || '')}&lead_id=${lead.id}`)}
                onDelete={() => setDeleteConfirm(lead.id)} isAdmin={user?.role === 'admin'} columns={COLUMNS} onStatusChange={updateStatus}
                isInProgress={COLUMNS[activeTab].id === 'won'} />
            ))}
            {getColumnLeads(COLUMNS[activeTab].id).length === 0 && (
              <div style={{ textAlign: 'center', padding: 40, color: 'var(--text-tertiary)', fontSize: 12, border: '1.5px dashed var(--border-medium)', borderRadius: 'var(--radius-lg)' }}>
                Keine Leads
              </div>
            )}
          </div>
        </div>
      ) : (
        <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
          {COLUMNS.map((col) => {
            const colLeads = getColumnLeads(col.id);
            const over = dragOver === col.id;
            return (
              <div key={col.id}
                onDragOver={(e) => handleDragOver(e, col.id)}
                onDrop={(e) => handleDrop(e, col.id)}
                onDragLeave={() => setDragOver(null)}
                style={{
                  flex: '1 1 0', minWidth: 160,
                  background: over ? 'var(--bg-hover)' : 'var(--bg-app)',
                  borderRadius: 'var(--radius-lg)',
                  border: over ? '1.5px dashed var(--brand-primary)' : '1.5px solid transparent',
                  transition: 'all 0.15s', minHeight: 200, padding: 6,
                }}>
                {/* Column header */}
                <div style={{ padding: '8px 8px 4px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span style={{ fontSize: 11, fontWeight: 500, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                    {col.label}
                  </span>
                  <span style={{
                    fontSize: 10, padding: '1px 6px', borderRadius: 10,
                    background: 'var(--status-neutral-bg)', color: 'var(--status-neutral-text)', fontWeight: 600,
                  }}>
                    {colLeads.length}
                  </span>
                </div>

                {/* Cards */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginTop: 6 }}>
                  {colLeads.map(lead => (
                    <LeadCard key={lead.id} lead={lead} onDragStart={handleDragStart}
                      onOpenProfile={() => navigate(`/app/leads/${lead.id}`)}
                      onStartAudit={() => navigate(`/app/audit?url=${encodeURIComponent(lead.website_url || '')}&lead_id=${lead.id}`)}
                      onDelete={() => setDeleteConfirm(lead.id)} isAdmin={user?.role === 'admin'} columns={COLUMNS} onStatusChange={updateStatus}
                      isInProgress={col.id === 'won'} />
                  ))}
                  {colLeads.length === 0 && (
                    <div style={{ padding: 16, textAlign: 'center', color: 'var(--text-tertiary)', fontSize: 11, border: '1.5px dashed var(--border-light)', borderRadius: 'var(--radius-md)' }}>
                      Keine Leads
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Delete Modal */}
      {deleteConfirm && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }} onClick={() => setDeleteConfirm(null)}>
          <div onClick={(e) => e.stopPropagation()} style={{
            background: 'var(--bg-surface)', borderRadius: 'var(--radius-xl)', padding: 28, maxWidth: 380, width: '100%',
            textAlign: 'center', boxShadow: 'var(--shadow-elevated)',
          }}>
            <h3 style={{ fontSize: 16, fontWeight: 500, color: 'var(--text-primary)', marginBottom: 8 }}>Lead löschen?</h3>
            <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 20 }}>
              <strong>{leads.find((l) => l.id === deleteConfirm)?.company_name}</strong> und alle Audits werden gelöscht.
            </p>
            <div style={{ display: 'flex', gap: 8 }}>
              <button onClick={() => setDeleteConfirm(null)} style={{
                flex: 1, padding: 10, background: 'var(--bg-hover)', color: 'var(--text-primary)',
                border: 'none', borderRadius: 'var(--radius-md)', fontSize: 13, fontWeight: 500, cursor: 'pointer',
              }}>Abbrechen</button>
              <button onClick={() => deleteLead(deleteConfirm)} style={{
                flex: 1, padding: 10, background: 'var(--status-danger-bg)', color: 'var(--status-danger-text)',
                border: 'none', borderRadius: 'var(--radius-md)', fontSize: 13, fontWeight: 500, cursor: 'pointer',
              }}>Löschen</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Lead Card ──

function LeadCard({ lead, onDragStart, onOpenProfile, onStartAudit, onDelete, isAdmin, columns, onStatusChange, isInProgress }) {
  const [menuOpen, setMenuOpen] = useState(false);
  const hasAudit = lead.analysis_score > 0;
  const scoreColor = (s) => s >= 70 ? 'var(--status-success-text)' : s >= 40 ? 'var(--status-warning-text)' : 'var(--status-danger-text)';

  const domain = (url) => {
    if (!url) return null;
    try { return new URL(url.startsWith('http') ? url : 'https://' + url).hostname.replace('www.', ''); } catch { return url; }
  };

  const daysSinceCreated = lead.created_at ? Math.floor((Date.now() - new Date(lead.created_at).getTime()) / 86400000) : null;

  return (
    <div draggable onDragStart={(e) => onDragStart(e, lead)} style={{
      background: 'var(--bg-surface)', borderRadius: 'var(--radius-md)',
      border: '1px solid var(--border-light)', padding: 10, cursor: 'grab',
      boxShadow: 'var(--shadow-card)', transition: 'border-color 0.15s',
      borderLeft: isInProgress ? '3px solid var(--brand-primary)' : undefined,
    }}
    onMouseEnter={e => e.currentTarget.style.borderColor = 'var(--border-medium)'}
    onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--border-light)'}
    >
      {/* Name */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 4, marginBottom: 4 }}>
        <div onClick={onOpenProfile} style={{
          fontSize: 12, fontWeight: 500, color: 'var(--text-primary)', cursor: 'pointer',
          overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', flex: 1,
        }}>
          {lead.company_name || 'Unbekannt'}
        </div>
        <div style={{ position: 'relative' }}>
          <button onClick={(e) => { e.stopPropagation(); setMenuOpen(!menuOpen); }} style={{
            background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-tertiary)',
            fontSize: 14, padding: '0 2px', lineHeight: 1,
          }}>···</button>
          {menuOpen && (
            <>
              <div style={{ position: 'fixed', inset: 0, zIndex: 49 }} onClick={() => setMenuOpen(false)} />
              <div style={{
                position: 'absolute', top: '100%', right: 0,
                background: 'var(--bg-elevated)', borderRadius: 'var(--radius-md)',
                boxShadow: 'var(--shadow-elevated)', border: '1px solid var(--border-light)',
                zIndex: 50, minWidth: 150, overflow: 'hidden', padding: 4,
              }}>
                <MItem onClick={() => { onOpenProfile(); setMenuOpen(false); }}>Kundenkartei</MItem>
                <MItem onClick={() => { onStartAudit(); setMenuOpen(false); }}>Audit starten</MItem>
                <div style={{ height: 1, background: 'var(--border-light)', margin: '4px 0' }} />
                <div style={{ fontSize: 9, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', padding: '4px 10px', letterSpacing: '0.06em' }}>Status</div>
                {columns.filter(c => c.id !== lead.status).map(col => (
                  <MItem key={col.id} onClick={() => { onStatusChange(lead.id, col.id); setMenuOpen(false); }}>{col.label}</MItem>
                ))}
                {isAdmin && (
                  <>
                    <div style={{ height: 1, background: 'var(--status-danger-bg)', margin: '4px 0' }} />
                    <MItem onClick={() => { onDelete(); setMenuOpen(false); }} danger>Löschen</MItem>
                  </>
                )}
              </div>
            </>
          )}
        </div>
      </div>

      {/* Meta: city, trade */}
      <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginBottom: 6 }}>
        {[lead.city, lead.trade].filter(Boolean).join(' · ') || (domain(lead.website_url) || '')}
      </div>

      {/* Score bar */}
      {hasAudit && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6 }}>
          <div style={{ flex: 1, height: 3, background: 'var(--border-light)', borderRadius: 2 }}>
            <div style={{ width: `${lead.analysis_score}%`, height: '100%', background: scoreColor(lead.analysis_score), borderRadius: 2 }} />
          </div>
          <span style={{ fontSize: 10, fontWeight: 600, color: scoreColor(lead.analysis_score) }}>{lead.analysis_score}</span>
        </div>
      )}

      {/* Footer */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Badge variant={lead.status === 'won' ? 'success' : lead.status === 'lost' ? 'danger' : lead.status === 'proposal_sent' ? 'warning' : 'neutral'}>
          {columns.find(c => c.id === lead.status)?.label || lead.status}
        </Badge>
        {daysSinceCreated !== null && (
          <span style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>Tag {daysSinceCreated}</span>
        )}
      </div>
    </div>
  );
}

function MItem({ children, onClick, danger }) {
  return (
    <button onClick={onClick} style={{
      width: '100%', display: 'flex', alignItems: 'center', gap: 6,
      padding: '6px 10px', background: 'transparent', border: 'none',
      borderRadius: 'var(--radius-sm)', cursor: 'pointer', fontSize: 12, textAlign: 'left',
      color: danger ? 'var(--status-danger-text)' : 'var(--text-secondary)',
      fontFamily: 'var(--font-sans)', transition: 'background 0.1s',
    }}
    onMouseEnter={e => e.currentTarget.style.background = danger ? 'var(--status-danger-bg)' : 'var(--bg-hover)'}
    onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
    >
      {children}
    </button>
  );
}

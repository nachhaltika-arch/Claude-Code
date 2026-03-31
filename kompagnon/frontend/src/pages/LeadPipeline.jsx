import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import API_BASE_URL from '../config';

const COLUMNS = [
  { id: 'won', label: 'Auftrag erhalten', color: 'success' },
  { id: 'onboarding', label: 'Onboarding', color: 'primary' },
  { id: 'in_progress', label: 'In Umsetzung', color: 'warning' },
  { id: 'review', label: 'Abnahme', color: 'info' },
  { id: 'live', label: 'Live', color: 'success' },
];

export default function LeadPipeline() {
  const navigate = useNavigate();
  const { token } = useAuth();
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dragging, setDragging] = useState(null);
  const [dragOver, setDragOver] = useState(null);

  const headers = () => ({ 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) });

  useEffect(() => { loadLeads(); }, []); // eslint-disable-line

  const loadLeads = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/leads/`, { headers: headers() });
      const data = await res.json();
      const projectLeads = Array.isArray(data) ? data.filter(l => l.status === 'won' || l.lead_source === 'stripe_checkout' || l.lead_source === 'llm_landing') : [];
      setLeads(projectLeads);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  };

  const getColumnLeads = (colId) => leads.filter(l => l.status === colId).sort((a, b) => (b.analysis_score || 0) - (a.analysis_score || 0));

  const updateStatus = async (leadId, newStatus) => {
    try {
      await fetch(`${API_BASE_URL}/api/leads/${leadId}`, { method: 'PATCH', headers: headers(), body: JSON.stringify({ status: newStatus }) });
      setLeads(prev => prev.map(l => l.id === leadId ? { ...l, status: newStatus } : l));
    } catch {}
  };

  const handleDragStart = (e, lead) => { setDragging(lead); e.dataTransfer.effectAllowed = 'move'; };
  const handleDrop = (e, colId) => { e.preventDefault(); if (dragging && dragging.status !== colId) updateStatus(dragging.id, colId); setDragging(null); setDragOver(null); };

  if (loading) return <div className="d-flex justify-content-center py-5"><div className="spinner-border text-primary"></div></div>;

  return (
    <div>
      <h2 className="mb-1"><i className="fas fa-diagram-project me-2"></i>Projektpipeline</h2>
      <small className="text-muted d-block mb-3">{leads.length} aktive Kundenprojekte · Drag & Drop zum Verschieben</small>

      <div className="d-flex gap-2 overflow-auto pb-3" style={{ minHeight: 400 }}>
        {COLUMNS.map(col => {
          const colLeads = getColumnLeads(col.id);
          const isOver = dragOver === col.id;
          return (
            <div key={col.id} className="kanban-col flex-shrink-0"
              onDragOver={e => { e.preventDefault(); setDragOver(col.id); }}
              onDrop={e => handleDrop(e, col.id)}
              onDragLeave={() => setDragOver(null)}
              style={{ borderTop: isOver ? `3px dashed var(--bs-${col.color})` : '3px solid transparent' }}>
              <div className={`card h-100 border-0 ${isOver ? 'bg-light' : 'bg-body-tertiary'}`}>
                <div className="card-header bg-transparent border-bottom d-flex justify-content-between align-items-center py-2">
                  <span className="fw-bold small text-uppercase">{col.label}</span>
                  <span className={`badge bg-${col.color}`}>{colLeads.length}</span>
                </div>
                <div className="card-body p-2 d-flex flex-column gap-2" style={{ minHeight: 200 }}>
                  {colLeads.map(lead => (
                    <div key={lead.id} draggable onDragStart={e => handleDragStart(e, lead)} className="card shadow-sm kanban-card">
                      <div className="card-body p-2">
                        <div className="fw-semibold small mb-1" style={{ cursor: 'pointer' }} onClick={() => navigate(`/app/leads/${lead.id}`)}>
                          {lead.company_name || 'Unbekannt'}
                        </div>
                        {lead.city && <small className="text-muted"><i className="fas fa-location-dot me-1"></i>{lead.city}</small>}
                      </div>
                    </div>
                  ))}
                  {colLeads.length === 0 && <div className="text-muted text-center small py-3 border border-dashed rounded">Leer</div>}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

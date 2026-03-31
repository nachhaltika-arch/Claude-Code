import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import API_BASE_URL from '../config';

const COLUMNS = [
  { id: 'new', label: 'Neue Leads', color: 'primary' },
  { id: 'contacted', label: 'Kontaktiert', color: 'info' },
  { id: 'qualified', label: 'Qualifiziert', color: 'success' },
  { id: 'proposal_sent', label: 'Angebot', color: 'warning' },
  { id: 'won', label: 'Gewonnen', color: 'success' },
  { id: 'lost', label: 'Verloren', color: 'danger' },
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

  const h = { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) };

  useEffect(() => { loadLeads(); }, []); // eslint-disable-line

  const loadLeads = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/leads/?limit=500`, { headers: h });
      const data = await res.json();
      setLeads(Array.isArray(data) ? data : []);
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

  const getColLeads = (colId) =>
    leads.filter(l => l.status === colId && (!search || (l.company_name || '').toLowerCase().includes(search.toLowerCase()) || (l.city || '').toLowerCase().includes(search.toLowerCase())))
      .sort((a, b) => (b.analysis_score || 0) - (a.analysis_score || 0));

  const scoreColor = (s) => s >= 70 ? 'text-success' : s >= 50 ? 'text-warning' : 'text-danger';
  const scoreBg = (s) => s >= 70 ? 'bg-success' : s >= 50 ? 'bg-warning' : 'bg-danger';

  if (loading) return (
    <div className="d-flex justify-content-center py-5"><div className="spinner-border text-primary"></div></div>
  );

  return (
    <div>
      <div className="d-flex justify-content-between align-items-start flex-wrap gap-2 mb-3">
        <div>
          <h2 className="mb-1"><i className="fas fa-bars-progress me-2"></i>Vertriebspipeline</h2>
          <small className="text-muted">{leads.length} Leads · Drag & Drop zum Verschieben</small>
        </div>
        <button className="btn btn-primary btn-sm" onClick={() => navigate('/app/import')}>
          <i className="fas fa-circle-plus me-1"></i> Leads importieren
        </button>
      </div>

      {/* Search */}
      <div className="input-group mb-3" style={{ maxWidth: 300 }}>
        <span className="input-group-text"><i className="fas fa-magnifying-glass"></i></span>
        <input className="form-control form-control-sm" placeholder="Firma oder Stadt..." value={search} onChange={e => setSearch(e.target.value)} />
      </div>

      {/* Kanban */}
      <div className="d-flex gap-2 overflow-auto pb-3" style={{ minHeight: 400 }}>
        {COLUMNS.map(col => {
          const colLeads = getColLeads(col.id);
          const isOver = dragOver === col.id;
          return (
            <div key={col.id} className={`kanban-col flex-shrink-0 ${isOver ? 'bg-light' : ''}`}
              onDragOver={e => { e.preventDefault(); setDragOver(col.id); }}
              onDrop={e => handleDrop(e, col.id)}
              onDragLeave={() => setDragOver(null)}
              style={{ borderTop: isOver ? `3px dashed var(--bs-${col.color})` : '3px solid transparent' }}>
              <div className="card h-100 border-0 bg-body-tertiary">
                <div className="card-header bg-transparent border-bottom d-flex justify-content-between align-items-center py-2">
                  <span className="fw-bold small text-uppercase">{col.label}</span>
                  <span className={`badge bg-${col.color}`}>{colLeads.length}</span>
                </div>
                <div className="card-body p-2 d-flex flex-column gap-2" style={{ minHeight: 200 }}>
                  {colLeads.map(lead => (
                    <div key={lead.id} draggable onDragStart={e => handleDragStart(e, lead)}
                      className="card shadow-sm kanban-card">
                      <div className="card-body p-2">
                        <div className="d-flex justify-content-between align-items-start mb-1">
                          <span className="fw-semibold small text-truncate" style={{ cursor: 'pointer' }} onClick={() => navigate(`/app/leads/${lead.id}`)}>
                            {lead.company_name || 'Unbekannt'}
                          </span>
                          <div className="dropdown">
                            <button className="btn btn-link btn-sm text-muted p-0" data-bs-toggle="dropdown"><i className="fas fa-ellipsis"></i></button>
                            <ul className="dropdown-menu dropdown-menu-end">
                              <li><button className="dropdown-item small" onClick={() => navigate(`/app/leads/${lead.id}`)}><i className="fas fa-address-book me-2"></i>Kundenkartei</button></li>
                              <li><button className="dropdown-item small" onClick={() => navigate(`/app/audit?url=${encodeURIComponent(lead.website_url || '')}&lead_id=${lead.id}`)}><i className="fas fa-magnifying-glass me-2"></i>Audit</button></li>
                              <li><hr className="dropdown-divider" /></li>
                              <li><span className="dropdown-header">Status ändern</span></li>
                              {COLUMNS.filter(c => c.id !== lead.status).map(c => (
                                <li key={c.id}><button className="dropdown-item small" onClick={() => updateStatus(lead.id, c.id)}>{c.label}</button></li>
                              ))}
                              {user?.role === 'admin' && (
                                <>
                                  <li><hr className="dropdown-divider" /></li>
                                  <li><button className="dropdown-item small text-danger" onClick={() => setDeleteConfirm(lead.id)}><i className="fas fa-trash-can me-2"></i>Löschen</button></li>
                                </>
                              )}
                            </ul>
                          </div>
                        </div>
                        {lead.website_url && <div className="small text-primary text-truncate mb-1">{lead.website_url.replace(/^https?:\/\/(www\.)?/, '')}</div>}
                        {lead.analysis_score > 0 && (
                          <div className="d-flex align-items-center gap-1 mb-1">
                            <div className="progress flex-grow-1" style={{ height: 3 }}>
                              <div className={`progress-bar ${scoreBg(lead.analysis_score)}`} style={{ width: `${lead.analysis_score}%` }}></div>
                            </div>
                            <small className={`fw-bold ${scoreColor(lead.analysis_score)}`}>{lead.analysis_score}</small>
                          </div>
                        )}
                        <div className="d-flex gap-1 flex-wrap">
                          {lead.city && <span className="badge bg-light text-dark border"><i className="fas fa-location-dot me-1"></i>{lead.city}</span>}
                          {lead.trade && <span className="badge bg-light text-dark border">{lead.trade}</span>}
                        </div>
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

      {/* Delete Modal */}
      {deleteConfirm && (
        <div className="modal show d-block" style={{ background: 'rgba(0,0,0,0.5)' }} onClick={() => setDeleteConfirm(null)}>
          <div className="modal-dialog modal-sm modal-dialog-centered" onClick={e => e.stopPropagation()}>
            <div className="modal-content">
              <div className="modal-body text-center p-4">
                <i className="fas fa-trash-can text-danger fs-1 mb-3"></i>
                <h5>Lead löschen?</h5>
                <p className="text-muted small"><strong>{leads.find(l => l.id === deleteConfirm)?.company_name}</strong> wird dauerhaft gelöscht.</p>
                <div className="d-flex gap-2">
                  <button className="btn btn-secondary flex-fill" onClick={() => setDeleteConfirm(null)}>Abbrechen</button>
                  <button className="btn btn-danger flex-fill" onClick={() => deleteLead(deleteConfirm)}>Löschen</button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

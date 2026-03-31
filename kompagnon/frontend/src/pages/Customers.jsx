import { useEffect, useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import API_BASE_URL from '../config';

const STATUS = {
  new: ['secondary', 'Neu'], contacted: ['info', 'Kontaktiert'], qualified: ['success', 'Qualifiziert'],
  proposal_sent: ['warning', 'Angebot'], won: ['success', 'Gewonnen'], lost: ['danger', 'Verloren'],
};

export default function Customers() {
  const navigate = useNavigate();
  const { token } = useAuth();
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [sortBy, setSortBy] = useState('name');

  const h = { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) };

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/leads/`, { headers: h })
      .then(r => r.json()).then(d => setLeads(Array.isArray(d) ? d : []))
      .catch(() => {}).finally(() => setLoading(false));
  }, []); // eslint-disable-line

  const filtered = useMemo(() => {
    let list = leads;
    if (search) { const q = search.toLowerCase(); list = list.filter(l => [l.company_name, l.city, l.trade, l.email, l.website_url].some(v => (v || '').toLowerCase().includes(q))); }
    if (statusFilter !== 'all') list = list.filter(l => l.status === statusFilter);
    list = [...list].sort((a, b) => {
      if (sortBy === 'score') return (b.analysis_score || 0) - (a.analysis_score || 0);
      if (sortBy === 'date') return new Date(b.created_at || 0) - new Date(a.created_at || 0);
      return (a.company_name || '').localeCompare(b.company_name || '');
    });
    return list;
  }, [leads, search, statusFilter, sortBy]);

  const scoreColor = (s) => s >= 70 ? 'text-success' : s >= 50 ? 'text-warning' : 'text-danger';
  const scoreBg = (s) => s >= 70 ? 'bg-success' : s >= 50 ? 'bg-warning' : 'bg-danger';

  if (loading) return (
    <div className="d-flex justify-content-center py-5"><div className="spinner-border text-primary"></div></div>
  );

  return (
    <div>
      <h2 className="mb-3"><i className="fas fa-address-book me-2"></i>Kontaktkartei</h2>

      {/* Filter Bar */}
      <div className="row g-2 mb-3">
        <div className="col-md-5">
          <div className="input-group">
            <span className="input-group-text"><i className="fas fa-magnifying-glass"></i></span>
            <input type="text" className="form-control" placeholder="Suchen nach Name, Ort, Gewerk..." value={search} onChange={e => setSearch(e.target.value)} />
          </div>
        </div>
        <div className="col-md-4">
          <div className="btn-group w-100 flex-wrap" role="group">
            {['all', ...Object.keys(STATUS)].map(key => {
              const label = key === 'all' ? 'Alle' : STATUS[key][1];
              const count = key === 'all' ? leads.length : leads.filter(l => l.status === key).length;
              if (key !== 'all' && count === 0) return null;
              return (
                <button key={key} className={`btn btn-sm ${statusFilter === key ? 'btn-primary' : 'btn-outline-secondary'}`} onClick={() => setStatusFilter(key)}>
                  {label} <span className="badge bg-light text-dark ms-1">{count}</span>
                </button>
              );
            })}
          </div>
        </div>
        <div className="col-md-3">
          <select className="form-select" value={sortBy} onChange={e => setSortBy(e.target.value)}>
            <option value="name">A → Z</option>
            <option value="score">Score ↓</option>
            <option value="date">Neueste</option>
          </select>
        </div>
      </div>

      <p className="text-muted small mb-2">{filtered.length} Ergebnisse{search && ` für „${search}"`}</p>

      {/* Table */}
      <div className="card shadow-sm">
        <div className="table-responsive">
          <table className="table table-hover table-striped mb-0">
            <thead className="table-light">
              <tr>
                <th>Unternehmen</th>
                <th>Ort</th>
                <th>Status</th>
                <th>Score</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {filtered.length === 0 ? (
                <tr><td colSpan={5} className="text-center text-muted py-4">Keine Ergebnisse</td></tr>
              ) : filtered.map(lead => {
                const [c, l] = STATUS[lead.status] || ['secondary', lead.status];
                return (
                  <tr key={lead.id} style={{ cursor: 'pointer' }} onClick={() => navigate(`/app/leads/${lead.id}`)}>
                    <td>
                      <div className="fw-semibold">{lead.display_name || lead.company_name || 'Unbekannt'}</div>
                      <small className="text-muted">{lead.trade}{lead.trade && lead.website_url ? ' · ' : ''}{lead.website_url?.replace(/^https?:\/\/(www\.)?/, '').replace(/\/$/, '')}</small>
                    </td>
                    <td>{lead.city || '—'}</td>
                    <td><span className={`badge bg-${c}`}>{l}</span></td>
                    <td>
                      {lead.analysis_score > 0 ? (
                        <div className="d-flex align-items-center gap-2">
                          <span className={`fw-bold ${scoreColor(lead.analysis_score)}`}>{lead.analysis_score}</span>
                          <div className="progress flex-grow-1" style={{ height: 4, maxWidth: 60 }}>
                            <div className={`progress-bar ${scoreBg(lead.analysis_score)}`} style={{ width: `${lead.analysis_score}%` }}></div>
                          </div>
                        </div>
                      ) : <span className="text-muted">—</span>}
                    </td>
                    <td><i className="fas fa-chevron-right text-muted"></i></td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

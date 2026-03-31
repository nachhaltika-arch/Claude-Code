import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import API_BASE_URL from '../config';

export default function Dashboard() {
  const { token } = useAuth();
  const navigate = useNavigate();
  const [kpis, setKpis] = useState(null);
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);

  const h = { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) };

  useEffect(() => {
    Promise.all([
      fetch(`${API_BASE_URL}/api/dashboard/kpis`, { headers: h }).then(r => r.json()),
      fetch(`${API_BASE_URL}/api/leads/`, { headers: h }).then(r => r.json()),
    ]).then(([kpiData, leadsData]) => {
      setKpis(kpiData);
      setLeads(Array.isArray(leadsData) ? leadsData.slice(0, 8) : []);
    }).finally(() => setLoading(false));
  }, []); // eslint-disable-line

  const scoreColor = (s) => s >= 70 ? 'text-success' : s >= 50 ? 'text-warning' : 'text-danger';
  const statusBadge = (status) => {
    const map = { new: ['secondary', 'Neu'], contacted: ['info', 'Kontaktiert'], qualified: ['success', 'Qualifiziert'], proposal_sent: ['warning', 'Angebot'], won: ['success', 'Gewonnen'], lost: ['danger', 'Verloren'] };
    const [c, l] = map[status] || ['secondary', status];
    return <span className={`badge bg-${c}`}>{l}</span>;
  };

  if (loading) return (
    <div className="d-flex justify-content-center align-items-center" style={{ height: '50vh' }}>
      <div className="spinner-border text-primary" role="status"><span className="visually-hidden">Laden...</span></div>
    </div>
  );

  const kpiCards = [
    { label: 'Leads gesamt', value: leads.length, icon: 'fas fa-users', border: 'border-primary' },
    { label: 'Audits heute', value: kpis?.audits_today ?? 0, icon: 'fas fa-clipboard-list', border: 'border-warning' },
    { label: 'Ø Score', value: kpis?.audits_avg_score ? `${kpis.audits_avg_score}/100` : '—', icon: 'fas fa-chart-line', border: 'border-success' },
    { label: 'Gewonnen', value: leads.filter(l => l.status === 'won').length, icon: 'fas fa-circle-check', border: 'border-info' },
  ];

  return (
    <div>
      <h2 className="mb-4"><i className="fas fa-gauge-high me-2"></i>Dashboard</h2>

      {/* KPI Cards */}
      <div className="row g-3 mb-4">
        {kpiCards.map((kpi, i) => (
          <div className="col-6 col-md-3" key={i}>
            <div className={`card shadow-sm h-100 ${kpi.border}`} style={{ borderTopWidth: 3 }}>
              <div className="card-body text-center">
                <i className={`${kpi.icon} fs-4 text-muted mb-2`}></i>
                <div className="display-6 fw-bold">{kpi.value}</div>
                <small className="text-muted text-uppercase">{kpi.label}</small>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Leads List */}
      <div className="row g-3">
        <div className="col-lg-8">
          <div className="card shadow-sm">
            <div className="card-header d-flex justify-content-between align-items-center">
              <span className="fw-semibold">Aktuelle Leads</span>
              <button className="btn btn-link btn-sm text-decoration-none p-0" onClick={() => navigate('/app/leads')}>
                Alle anzeigen <i className="fas fa-arrow-right ms-1"></i>
              </button>
            </div>
            <div className="card-body p-0">
              {leads.length === 0 ? (
                <p className="text-muted text-center py-4 mb-0">Noch keine Leads vorhanden</p>
              ) : (
                <div className="list-group list-group-flush">
                  {leads.map(lead => (
                    <button key={lead.id} className="list-group-item list-group-item-action d-flex align-items-center gap-3 py-2" onClick={() => navigate(`/app/leads/${lead.id}`)}>
                      <div className="rounded-circle bg-primary bg-opacity-10 text-primary d-flex align-items-center justify-content-center fw-bold" style={{ width: 36, height: 36, flexShrink: 0 }}>
                        {lead.company_name?.[0] || '?'}
                      </div>
                      <div className="flex-grow-1 min-w-0">
                        <div className="fw-semibold text-truncate">{lead.company_name}</div>
                        <small className="text-muted">{[lead.city, lead.trade].filter(Boolean).join(' · ')}</small>
                      </div>
                      {lead.analysis_score > 0 && (
                        <span className={`fw-bold ${scoreColor(lead.analysis_score)}`}>{lead.analysis_score}</span>
                      )}
                      {statusBadge(lead.status)}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="col-lg-4">
          <div className="card shadow-sm">
            <div className="card-header fw-semibold">Schnellaktionen</div>
            <div className="card-body d-grid gap-2">
              <button className="btn btn-primary" onClick={() => navigate('/app/import')}>
                <i className="fas fa-cloud-arrow-up me-2"></i>Domains importieren
              </button>
              <button className="btn btn-outline-primary" onClick={() => navigate('/app/audit')}>
                <i className="fas fa-magnifying-glass-chart me-2"></i>Audit starten
              </button>
              <button className="btn btn-outline-secondary" onClick={() => navigate('/app/sales')}>
                <i className="fas fa-bars-progress me-2"></i>Vertriebspipeline
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

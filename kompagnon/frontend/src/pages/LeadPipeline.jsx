import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import toast from 'react-hot-toast';
import API_BASE_URL from '../config';
import AuditHistory from '../components/AuditHistory';
import { useScreenSize } from '../utils/responsive';
import { useAuth } from '../context/AuthContext';

const statusConfig = {
  new:           { label: 'Neu',           className: 'kc-badge kc-badge--info' },
  contacted:     { label: 'Kontaktiert',   className: 'kc-badge kc-badge--neutral' },
  qualified:     { label: 'Qualifiziert',  className: 'kc-badge kc-badge--success' },
  proposal_sent: { label: 'Angebot',       className: 'kc-badge kc-badge--warning' },
  won:           { label: 'Gewonnen',      className: 'kc-badge kc-badge--success' },
  lost:          { label: 'Verloren',      className: 'kc-badge kc-badge--danger' },
};

export default function LeadPipeline() {
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expandedLead, setExpandedLead] = useState(null);
  const [enriching, setEnriching] = useState(null);
  const [deleteConfirm, setDeleteConfirm] = useState(null);
  const { user } = useAuth();
  const navigate = useNavigate();
  const { isMobile } = useScreenSize();

  useEffect(() => {
    loadLeads();
  }, []);

  const loadLeads = async () => {
    try {
      setLoading(true);
      const res = await axios.get(`${API_BASE_URL}/api/leads/`);
      setLeads(res.data);
    } catch (error) {
      toast.error('Leads konnten nicht geladen werden.');
    } finally {
      setLoading(false);
    }
  };

  const enrichLead = async (leadId) => {
    setEnriching(leadId);
    try {
      const res = await fetch(`${API_BASE_URL}/api/leads/${leadId}/enrich`, { method: 'POST' });
      const data = await res.json();
      if (data.status === 'success') {
        toast.success(`Angereichert: ${data.enriched_fields.length} Felder`);
        loadLeads();
      } else {
        toast.error(data.reason || 'Anreicherung fehlgeschlagen');
      }
    } catch (e) { toast.error('Fehler bei Anreicherung'); }
    finally { setEnriching(null); }
  };

  const deleteLead = async (leadId) => {
    try {
      const res = await axios.delete(`${API_BASE_URL}/api/leads/${leadId}`);
      if (res.data.success) {
        setLeads((prev) => prev.filter((l) => l.id !== leadId));
        setDeleteConfirm(null);
        toast.success('Lead geloescht');
      }
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Loeschen fehlgeschlagen');
    }
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--kc-space-4)' }}>
        <div className="kc-skeleton" style={{ height: '40px', width: '200px' }} />
        {[1, 2, 3].map((i) => (
          <div key={i} className="kc-skeleton" style={{ height: '48px' }} />
        ))}
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--kc-space-6)' }}>
      <div className="kc-section-header">
        <span className="kc-eyebrow">Vertrieb</span>
        <h1>Lead Pipeline</h1>
      </div>

      <div className="kc-card" style={{ padding: 0, overflow: 'hidden' }}>
        <div style={{ overflowX: isMobile ? 'auto' : undefined }}>
        <table className="kc-table">
          <thead>
            <tr>
              <th></th>
              <th>Unternehmen</th>
              <th style={{ display: isMobile ? 'none' : undefined }}>Kontakt</th>
              <th style={{ display: isMobile ? 'none' : undefined }}>Stadt</th>
              <th>Gewerk</th>
              <th>Status</th>
              <th style={{ textAlign: 'right', display: isMobile ? 'none' : undefined }}>Score</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {leads.length === 0 ? (
              <tr>
                <td colSpan={8} style={{ textAlign: 'center', color: 'var(--kc-mittel)', padding: 'var(--kc-space-8)' }}>
                  Keine Leads vorhanden.
                </td>
              </tr>
            ) : (
              leads.map((lead) => {
                const cfg = statusConfig[lead.status] || statusConfig.new;
                const isExpanded = expandedLead === lead.id;
                return (
                  <React.Fragment key={lead.id}>
                    <tr
                      style={{ cursor: 'pointer' }}
                      onClick={() => setExpandedLead(isExpanded ? null : lead.id)}
                    >
                      <td style={{ width: '24px', textAlign: 'center', color: 'var(--kc-mittel)', fontSize: 'var(--kc-text-xs)' }}>
                        {isExpanded ? '▼' : '▶'}
                      </td>
                      <td style={{ fontWeight: 600 }}>
                        <span
                          style={{ cursor: 'pointer', color: 'var(--kc-text-primaer)', textDecoration: 'none' }}
                          onClick={(e) => { e.stopPropagation(); navigate(`/app/leads/${lead.id}`); }}
                          onMouseEnter={(e) => { e.target.style.textDecoration = 'underline'; }}
                          onMouseLeave={(e) => { e.target.style.textDecoration = 'none'; }}
                        >
                          {lead.company_name}
                        </span>
                      </td>
                      <td style={{ color: 'var(--kc-text-sekundaer)', display: isMobile ? 'none' : undefined }}>{lead.contact_name}</td>
                      <td style={{ color: 'var(--kc-text-sekundaer)', display: isMobile ? 'none' : undefined }}>{lead.city}</td>
                      <td style={{ color: 'var(--kc-text-sekundaer)' }}>{lead.trade}</td>
                      <td><span className={cfg.className}>{cfg.label}</span></td>
                      <td style={{ textAlign: 'right', display: isMobile ? 'none' : undefined }}>
                        <span
                          style={{
                            fontFamily: 'var(--kc-font-mono)',
                            fontWeight: 700,
                            fontSize: 'var(--kc-text-sm)',
                            color: lead.analysis_score >= 70 ? 'var(--kc-success)' :
                                   lead.analysis_score >= 40 ? 'var(--kc-warning)' :
                                   'var(--kc-text-subtil)',
                          }}
                        >
                          {lead.analysis_score}/100
                        </span>
                      </td>
                      <td style={{ textAlign: 'right' }} onClick={(e) => e.stopPropagation()}>
                        <button
                          className="kc-btn-ghost"
                          style={{ fontSize: 'var(--kc-text-xs)', padding: 'var(--kc-space-1) var(--kc-space-3)' }}
                          onClick={() => navigate(`/app/audit?url=${encodeURIComponent(lead.website_url || '')}&company=${encodeURIComponent(lead.company_name)}&contact=${encodeURIComponent(lead.contact_name)}&city=${encodeURIComponent(lead.city)}&trade=${encodeURIComponent(lead.trade)}&lead_id=${lead.id}`)}
                        >
                          Audit
                        </button>
                        <button
                          className="kc-btn-ghost"
                          style={{ fontSize: 'var(--kc-text-xs)', padding: 'var(--kc-space-1) var(--kc-space-3)' }}
                          onClick={(e) => { e.stopPropagation(); enrichLead(lead.id); }}
                          disabled={enriching === lead.id}
                          title="Daten anreichern"
                        >
                          {enriching === lead.id ? '...' : 'Anreichern'}
                        </button>
                        {user?.role === 'admin' && (
                          <button
                            className="kc-btn-ghost"
                            style={{ fontSize: 'var(--kc-text-xs)', padding: 'var(--kc-space-1) var(--kc-space-2)', color: '#94a3b8' }}
                            onClick={(e) => { e.stopPropagation(); setDeleteConfirm(lead.id); }}
                            title="Lead loeschen"
                          >
                            🗑️
                          </button>
                        )}
                      </td>
                    </tr>
                    {isExpanded && (
                      <tr>
                        <td colSpan={8} style={{ padding: 'var(--kc-space-4) var(--kc-space-6)', background: 'var(--kc-hell)' }}>
                          <AuditHistory leadId={lead.id} />
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                );
              })
            )}
          </tbody>
        </table>
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      {deleteConfirm && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}
          onClick={() => setDeleteConfirm(null)}>
          <div onClick={(e) => e.stopPropagation()} style={{ background: '#fff', borderRadius: 16, padding: 28, maxWidth: 400, width: '100%', boxShadow: '0 20px 60px rgba(0,0,0,0.2)' }}>
            <div style={{ width: 52, height: 52, borderRadius: '50%', background: '#fee2e2', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 24, margin: '0 auto 16px' }}>🗑️</div>
            <h3 style={{ fontSize: 18, fontWeight: 800, color: '#0F1E3A', textAlign: 'center', marginBottom: 8 }}>Lead loeschen?</h3>
            <p style={{ fontSize: 14, color: '#64748b', textAlign: 'center', marginBottom: 8, lineHeight: 1.5 }}>
              <strong>{leads.find((l) => l.id === deleteConfirm)?.company_name}</strong> wird dauerhaft geloescht.
            </p>
            <p style={{ fontSize: 12, color: '#ef4444', textAlign: 'center', marginBottom: 24 }}>
              Alle zugehoerigen Audits werden ebenfalls geloescht. Diese Aktion kann nicht rueckgaengig gemacht werden.
            </p>
            <div style={{ display: 'flex', gap: 10 }}>
              <button onClick={() => setDeleteConfirm(null)} style={{ flex: 1, padding: 11, background: '#f1f5f9', color: '#0F1E3A', border: 'none', borderRadius: 8, fontSize: 14, fontWeight: 600, cursor: 'pointer', minHeight: 44 }}>
                Abbrechen
              </button>
              <button onClick={() => deleteLead(deleteConfirm)} style={{ flex: 1, padding: 11, background: '#ef4444', color: '#fff', border: 'none', borderRadius: 8, fontSize: 14, fontWeight: 700, cursor: 'pointer', minHeight: 44 }}>
                Endgueltig loeschen
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

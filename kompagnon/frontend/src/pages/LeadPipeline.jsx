import React, { useEffect, useState } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';
import API_BASE_URL from '../config';

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
        <table className="kc-table">
          <thead>
            <tr>
              <th>Unternehmen</th>
              <th>Kontakt</th>
              <th>Stadt</th>
              <th>Gewerk</th>
              <th>Status</th>
              <th style={{ textAlign: 'right' }}>Score</th>
            </tr>
          </thead>
          <tbody>
            {leads.length === 0 ? (
              <tr>
                <td colSpan={6} style={{ textAlign: 'center', color: 'var(--kc-mittel)', padding: 'var(--kc-space-8)' }}>
                  Keine Leads vorhanden.
                </td>
              </tr>
            ) : (
              leads.map((lead) => {
                const cfg = statusConfig[lead.status] || statusConfig.new;
                return (
                  <tr key={lead.id}>
                    <td style={{ fontWeight: 600 }}>{lead.company_name}</td>
                    <td style={{ color: 'var(--kc-text-sekundaer)' }}>{lead.contact_name}</td>
                    <td style={{ color: 'var(--kc-text-sekundaer)' }}>{lead.city}</td>
                    <td style={{ color: 'var(--kc-text-sekundaer)' }}>{lead.trade}</td>
                    <td><span className={cfg.className}>{cfg.label}</span></td>
                    <td style={{ textAlign: 'right' }}>
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
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

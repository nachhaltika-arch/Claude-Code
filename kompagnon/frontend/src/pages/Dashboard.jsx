import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useScreenSize } from '../utils/responsive';
import Card from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import Skeleton from '../components/ui/Skeleton';
import API_BASE_URL from '../config';

export default function Dashboard() {
  const { token } = useAuth();
  const navigate = useNavigate();
  const { isMobile } = useScreenSize();
  const [kpis, setKpis] = useState(null);
  const [leads, setLeads] = useState([]);
  const [audits, setAudits] = useState([]);
  const [loading, setLoading] = useState(true);
  const fetchedRef = useRef(false);

  useEffect(() => {
    if (fetchedRef.current) return;
    fetchedRef.current = true;
    const h = { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) };
    Promise.all([
      fetch(`${API_BASE_URL}/api/dashboard/kpis`, { headers: h }).then(r => r.json()),
      fetch(`${API_BASE_URL}/api/leads/`, { headers: h }).then(r => r.json()).catch(() => []),
      fetch(`${API_BASE_URL}/api/audit/recent`, { headers: h }).then(r => r.json().catch(() => [])),
    ]).then(async ([kpiData, leadsData, auditData]) => {
      setKpis(kpiData);
      let rows = Array.isArray(leadsData) ? leadsData : [];
      // Fallback: if leads table is empty, try usercards
      if (rows.length === 0) {
        try {
          const uc = await fetch(`${API_BASE_URL}/api/usercards/`, { headers: h }).then(r => r.json());
          if (Array.isArray(uc) && uc.length > 0) rows = uc;
        } catch (_) {}
      }
      setLeads(rows.slice(0, 8));
      setAudits(Array.isArray(auditData) ? auditData.slice(0, 5) : []);
    }).finally(() => setLoading(false));
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const KpiCard = ({ label, value, icon, delta, color }) => (
    <Card>
      <div style={{
        display: 'flex', alignItems: 'flex-start',
        justifyContent: 'space-between', marginBottom: 12,
      }}>
        <span style={{
          fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.04em',
          color: 'var(--text-tertiary)', fontWeight: 500,
        }}>
          {label}
        </span>
        <span style={{ fontSize: 18, opacity: 0.6 }}>{icon}</span>
      </div>
      {loading ? (
        <Skeleton height={32} width={80} />
      ) : (
        <div style={{
          fontSize: 28, fontWeight: 500,
          color: color || 'var(--text-primary)',
          lineHeight: 1, marginBottom: delta ? 8 : 0,
        }}>
          {value ?? '—'}
        </div>
      )}
      {delta && !loading && (
        <div style={{
          fontSize: 11,
          color: delta > 0 ? 'var(--status-success-text)' : 'var(--status-danger-text)',
        }}>
          {delta > 0 ? '↑' : '↓'} {Math.abs(delta)} diese Woche
        </div>
      )}
    </Card>
  );

  const avgScore = audits.length
    ? Math.round(audits.reduce((s, a) => s + (a.total_score || 0), 0) / audits.length)
    : null;

  const statusBadge = (status) => {
    const map = {
      new: ['neutral', 'Neu'],
      contacted: ['info', 'Kontaktiert'],
      qualified: ['success', 'Qualifiziert'],
      proposal_sent: ['warning', 'Angebot'],
      won: ['success', 'Gewonnen'],
      lost: ['danger', 'Verloren'],
    };
    const [v, l] = map[status] || ['neutral', status];
    return <Badge variant={v}>{l}</Badge>;
  };

  const scoreColor = (s) =>
    s >= 70 ? 'var(--status-success-text)'
    : s >= 50 ? 'var(--status-warning-text)'
    : 'var(--status-danger-text)';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20, animation: 'fadeIn 0.3s ease' }}>

      {/* KPI Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
        gap: 12,
      }}>
        <KpiCard label="Leads gesamt" value={kpis?.leads_total ?? leads.length} icon="👥" />
        <KpiCard label="Audits heute" value={kpis?.audits_today ?? 0} icon="✓" color="var(--brand-primary)" />
        <KpiCard
          label="Ø Homepage-Score"
          value={avgScore !== null ? `${avgScore}/100` : '—'}
          icon="◎"
          color={avgScore ? scoreColor(avgScore) : undefined}
        />
        <KpiCard
          label="Gewonnene Leads"
          value={kpis?.leads_won ?? leads.filter(l => l.status === 'won').length}
          icon="🏆"
          color="var(--status-success-text)"
        />
      </div>

      {/* Zwei-Spalten */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: isMobile ? '1fr' : 'minmax(0, 1.6fr) minmax(0, 1fr)',
        gap: 16,
      }}>

        {/* Leads */}
        <Card padding="sm">
          <div style={{
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            padding: '4px 4px 12px', borderBottom: '1px solid var(--border-light)', marginBottom: 4,
          }}>
            <span style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)' }}>
              Aktuelle Leads
            </span>
            <button
              onClick={() => navigate('/app/sales')}
              style={{
                fontSize: 11, color: 'var(--brand-primary)', background: 'none',
                border: 'none', cursor: 'pointer', fontFamily: 'var(--font-sans)',
              }}
            >
              Alle anzeigen →
            </button>
          </div>

          {loading ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10, padding: '8px 4px' }}>
              {[1,2,3,4].map(i => <Skeleton key={i} height={40} />)}
            </div>
          ) : leads.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '32px 16px', color: 'var(--text-tertiary)', fontSize: 13 }}>
              Noch keine Leads vorhanden
            </div>
          ) : (
            leads.map((lead, i) => (
              <div
                key={lead.id}
                onClick={() => navigate(`/app/leads/${lead.id}`)}
                style={{
                  display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                  padding: '10px 4px',
                  borderBottom: i < leads.length - 1 ? '1px solid var(--border-light)' : 'none',
                  cursor: 'pointer', transition: 'background 0.1s',
                  borderRadius: 'var(--radius-sm)', gap: 12,
                }}
                onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-hover)'}
                onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
              >
                <div style={{
                  width: 32, height: 32, borderRadius: '50%',
                  background: 'var(--brand-primary-light)', color: 'var(--brand-primary)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 11, fontWeight: 600, flexShrink: 0,
                }}>
                  {lead.company_name?.[0] || '?'}
                </div>

                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{
                    fontSize: 13, fontWeight: 500, color: 'var(--text-primary)',
                    overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                  }}>
                    {lead.company_name}
                  </div>
                  <div style={{
                    fontSize: 11, color: 'var(--text-tertiary)',
                    overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                  }}>
                    {lead.city}{lead.city && lead.trade ? ' · ' : ''}{lead.trade}
                  </div>
                </div>

                {lead.analysis_score > 0 && (
                  <div style={{ textAlign: 'right', flexShrink: 0 }}>
                    <div style={{ fontSize: 13, fontWeight: 500, color: scoreColor(lead.analysis_score) }}>
                      {lead.analysis_score}
                    </div>
                    <div style={{ width: 40, height: 3, background: 'var(--border-light)', borderRadius: 2, overflow: 'hidden', marginTop: 3 }}>
                      <div style={{ width: `${lead.analysis_score}%`, height: '100%', background: scoreColor(lead.analysis_score), borderRadius: 2 }} />
                    </div>
                  </div>
                )}

                {statusBadge(lead.status)}
              </div>
            ))
          )}
        </Card>

        {/* Letzte Audits */}
        <Card padding="sm">
          <div style={{
            fontSize: 13, fontWeight: 500, color: 'var(--text-primary)',
            padding: '4px 4px 12px', borderBottom: '1px solid var(--border-light)', marginBottom: 8,
          }}>
            Letzte Audits
          </div>

          {loading ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10, padding: '4px' }}>
              {[1,2,3].map(i => <Skeleton key={i} height={48} />)}
            </div>
          ) : audits.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '32px 12px', color: 'var(--text-tertiary)', fontSize: 13 }}>
              Noch keine Audits
            </div>
          ) : (
            audits.map((audit, i) => {
              const score = audit.total_score || 0;
              const level = score >= 85 ? 'Pt' : score >= 70 ? 'Go' : score >= 50 ? 'Si' : score >= 30 ? 'Br' : 'NC';
              const levelColor =
                score >= 85 ? 'var(--brand-primary)'
                : score >= 70 ? 'var(--status-warning-text)'
                : score >= 50 ? 'var(--text-secondary)'
                : score >= 30 ? '#a06820'
                : 'var(--status-danger-text)';

              return (
                <div key={audit.id} style={{
                  display: 'flex', alignItems: 'center', gap: 10, padding: '8px 4px',
                  borderBottom: i < audits.length - 1 ? '1px solid var(--border-light)' : 'none',
                }}>
                  <div style={{
                    width: 32, height: 32, borderRadius: 'var(--radius-sm)',
                    background: `${levelColor}18`, color: levelColor,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: 10, fontWeight: 700, flexShrink: 0,
                  }}>
                    {level}
                  </div>

                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{
                      fontSize: 12, fontWeight: 500, color: 'var(--text-primary)',
                      overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                    }}>
                      {audit.company_name || audit.website_url}
                    </div>
                    <div style={{ fontSize: 10, color: 'var(--text-tertiary)', marginTop: 2 }}>
                      {new Date(audit.created_at).toLocaleDateString('de-DE')}
                    </div>
                  </div>

                  <div style={{ fontSize: 14, fontWeight: 600, color: levelColor, flexShrink: 0 }}>
                    {score}
                  </div>
                </div>
              );
            })
          )}

          {!loading && audits.length > 0 && (
            <div style={{
              display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8,
              marginTop: 12, paddingTop: 12, borderTop: '1px solid var(--border-light)',
            }}>
              {[
                { label: 'Ø Score', value: avgScore || '—' },
                { label: 'Audits', value: audits.length },
              ].map(stat => (
                <div key={stat.label} style={{
                  textAlign: 'center', padding: '8px',
                  background: 'var(--bg-app)', borderRadius: 'var(--radius-sm)',
                }}>
                  <div style={{ fontSize: 16, fontWeight: 500, color: 'var(--brand-primary)' }}>
                    {stat.value}
                  </div>
                  <div style={{ fontSize: 10, color: 'var(--text-tertiary)', marginTop: 2 }}>
                    {stat.label}
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}

import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useScreenSize } from '../utils/responsive';
import Card from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import Skeleton from '../components/ui/Skeleton';
import API_BASE_URL from '../config';
import OnboardingWizard from '../components/OnboardingWizard';

export default function Dashboard() {
  const { token, user } = useAuth();
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [onboardingChecked, setOnboardingChecked] = useState(false);
  const navigate = useNavigate();
  const { isMobile } = useScreenSize();
  const [kpis, setKpis] = useState(null);
  const [dealStats, setDealStats] = useState(null);
  const [campaignStats, setCampaignStats] = useState([]);
  const [leads, setLeads] = useState([]);
  const [audits, setAudits] = useState([]);
  const [loading, setLoading] = useState(true);
  const fetchedRef = useRef(false);

  useEffect(() => {
    if (fetchedRef.current) return;
    fetchedRef.current = true;
    const h = { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) };
    Promise.all([
      fetch(`${API_BASE_URL}/api/dashboard/kpis`, { headers: h }).then(r => r.json()).catch(() => null),
      fetch(`${API_BASE_URL}/api/leads/`, { headers: h }).then(r => r.json()).catch(() => []),
      fetch(`${API_BASE_URL}/api/audit/recent`, { headers: h }).then(r => r.json()).catch(() => []),
      fetch(`${API_BASE_URL}/api/deals/stats`, { headers: h }).then(r => r.json()).catch(() => null),
      fetch(`${API_BASE_URL}/api/campaigns/stats`, { headers: h }).then(r => r.json()).catch(() => []),
    ]).then(async ([kpiData, leadsData, auditData, dealsData, campaignData]) => {
      setKpis(kpiData);
      setDealStats(dealsData);
      setCampaignStats(Array.isArray(campaignData) ? campaignData : []);
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

  useEffect(() => {
    if (!user || onboardingChecked) return;
    setOnboardingChecked(true);

    // Nur für Kunden mit verknüpftem Lead
    if (user.role !== 'kunde' || !user.lead_id) return;

    // Onboarding-Status vom Server prüfen
    const checkOnboarding = async () => {
      try {
        const res = await fetch(
          `${API_BASE_URL}/api/auth/me`,
          {
            headers: {
              Authorization: `Bearer ${localStorage.getItem('kompagnon_token')}`,
            },
          }
        );
        if (res.ok) {
          const me = await res.json();
          if (me.onboarding_completed === false) {
            setShowOnboarding(true);
          }
        }
      } catch {}
    };
    checkOnboarding();
  }, [user, onboardingChecked]); // eslint-disable-line react-hooks/exhaustive-deps

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
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20, animation: 'fadeIn 0.3s ease', width: '100%', minWidth: 0, overflowX: 'hidden' }}>

      {showOnboarding && (
        <OnboardingWizard
          user={user}
          onComplete={() => {
            setShowOnboarding(false);
            // onboarding_completed Flag lokal aktualisieren
            // damit kein zweiter Check den Wizard nochmal zeigt
            setOnboardingChecked(true);
          }}
        />
      )}

      {/* Deal-Metriken */}
      {dealStats && (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: 12,
          minWidth: 0, width: '100%',
        }}>
          <div style={{ background: 'var(--bg-surface)', borderRadius: 'var(--radius-lg)', padding: '18px 22px', border: '1px solid var(--border-light)' }}>
            <div style={{ fontSize: 11, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 6 }}>
              💰 Heute gewonnen
            </div>
            <div style={{ fontSize: 24, fontWeight: 700, color: 'var(--status-success-text)' }}>
              {Number(dealStats.won_today).toLocaleString('de-DE', { style: 'currency', currency: 'EUR' })}
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 4 }}>
              {dealStats.deals_won_today} Deal{dealStats.deals_won_today !== 1 ? 's' : ''}
            </div>
          </div>
          <div style={{ background: 'var(--bg-surface)', borderRadius: 'var(--radius-lg)', padding: '18px 22px', border: '1px solid var(--border-light)' }}>
            <div style={{ fontSize: 11, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 6 }}>
              📅 Diesen Monat
            </div>
            <div style={{ fontSize: 24, fontWeight: 700, color: 'var(--status-success-text)' }}>
              {Number(dealStats.won_this_month).toLocaleString('de-DE', { style: 'currency', currency: 'EUR' })}
            </div>
          </div>
          <div style={{ background: 'var(--bg-surface)', borderRadius: 'var(--radius-lg)', padding: '18px 22px', border: '1px solid var(--border-light)' }}>
            <div style={{ fontSize: 11, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 6 }}>
              💼 Pipeline offen
            </div>
            <div style={{ fontSize: 24, fontWeight: 700, color: 'var(--brand-primary)' }}>
              {Number(dealStats.pipeline_value).toLocaleString('de-DE', { style: 'currency', currency: 'EUR' })}
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 4 }}>
              {dealStats.deals_open} offene Deal{dealStats.deals_open !== 1 ? 's' : ''}
            </div>
          </div>
        </div>
      )}

      {/* KPI Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
        gap: 12,
        minWidth: 0, width: '100%',
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

      {/* Leads nach Herkunft */}
      {campaignStats.length > 0 && (() => {
        const SRC = {
          facebook:   { icon: '📘', label: 'Facebook' },
          linkedin:   { icon: '💼', label: 'LinkedIn' },
          google_ads: { icon: '🔍', label: 'Google Ads' },
          briefkarte: { icon: '📬', label: 'Briefkarte' },
          instagram:  { icon: '📸', label: 'Instagram' },
          email:      { icon: '✉️', label: 'E-Mail' },
          postkarte:  { icon: '📬', label: 'Postkarte' },
          sonstige:   { icon: '📌', label: 'Sonstige' },
          direkt:     { icon: '🔗', label: 'Direkt' },
        };
        const maxCount = Math.max(...campaignStats.map(s => s.lead_count || 0), 1);
        return (
          <div style={{
            background: 'var(--bg-surface)', borderRadius: 'var(--radius-lg)',
            padding: '18px 22px', border: '1px solid var(--border-light)',
            width: '100%', boxSizing: 'border-box',
          }}>
            <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 14, color: 'var(--text-primary)' }}>
              📊 Leads nach Herkunft
            </div>
            {campaignStats.map(stat => {
              const cfg = SRC[stat.source] || { icon: stat.source_icon || '📌', label: stat.source_label || stat.source };
              const cnt = stat.lead_count || 0;
              const won = stat.won_count || 0;
              const pct = cnt > 0 ? Math.round((won / cnt) * 100) : 0;
              const widthPct = Math.round((cnt / maxCount) * 100);
              return (
                <div key={stat.source} style={{
                  display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10,
                }}>
                  <span style={{ fontSize: 16, width: 24, flexShrink: 0 }}>{cfg.icon}</span>
                  <span style={{ fontSize: 12, width: 100, color: 'var(--text-secondary)', flexShrink: 0 }}>{cfg.label}</span>
                  <div style={{ flex: 1, height: 8, background: 'var(--bg-app)', borderRadius: 4, overflow: 'hidden', minWidth: 50 }}>
                    <div style={{
                      width: `${widthPct}%`, height: '100%',
                      background: 'var(--brand-primary)',
                      borderRadius: 4, transition: 'width 0.5s ease',
                    }} />
                  </div>
                  <span style={{ fontSize: 12, color: 'var(--text-tertiary)', minWidth: 70, textAlign: 'right', flexShrink: 0 }}>
                    {cnt} Lead{cnt !== 1 ? 's' : ''}
                  </span>
                  <span style={{
                    fontSize: 11,
                    color: pct > 30 ? 'var(--status-success-text)' : 'var(--text-tertiary)',
                    minWidth: 42, textAlign: 'right', flexShrink: 0, fontWeight: 600,
                  }}>
                    {pct}% ✓
                  </span>
                </div>
              );
            })}
          </div>
        );
      })()}

      {/* Zwei-Spalten */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: isMobile ? '1fr' : 'minmax(0, 1.6fr) minmax(0, 1fr)',
        gap: 16,
        minWidth: 0, width: '100%', overflowX: 'hidden',
      }}>

        {/* Leads */}
        <Card padding="sm" style={{ width: '100%', boxSizing: 'border-box', minWidth: 0 }}>
          <div style={{
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            padding: '4px 4px 12px', borderBottom: '1px solid var(--border-light)', marginBottom: 4,
          }}>
            <span style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)' }}>
              Aktuelle Leads
            </span>
            <button
              onClick={() => navigate('/app/deals')}
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
            <div style={{ textAlign: 'center', padding: '32px 16px', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 10 }}>
              <div style={{ fontSize: 28 }}>📋</div>
              <div style={{ fontSize: 13, color: 'var(--text-tertiary)' }}>Noch keine Leads vorhanden</div>
              <button onClick={() => navigate('/app/import')} style={{ marginTop: 4, padding: '8px 18px', borderRadius: 8, border: 'none', background: 'var(--brand-primary)', color: '#fff', fontSize: 13, fontWeight: 600, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
                + Leads importieren
              </button>
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

                <span style={{ flexShrink: 0 }}>{statusBadge(lead.status)}</span>
              </div>
            ))
          )}
        </Card>

        {/* Letzte Audits */}
        <Card padding="sm" style={{ width: '100%', boxSizing: 'border-box', minWidth: 0 }}>
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

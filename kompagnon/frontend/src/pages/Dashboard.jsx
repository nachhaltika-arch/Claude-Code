import React, { useEffect, useState } from 'react';
import {
  FolderIcon,
  BanknotesIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  StarIcon,
  MagnifyingGlassCircleIcon,
  ChartBarIcon,
  ArrowTrendingUpIcon,
} from '@heroicons/react/24/outline';
import MarginBadge from '../components/MarginBadge';
import AlertBanner from '../components/AlertBanner';
import axios from 'axios';
import toast from 'react-hot-toast';
import API_BASE_URL from '../config';
import { useScreenSize } from '../utils/responsive';

const phaseNames = {
  phase_1_akquisition: 'Phase 1 — Akquisition',
  phase_2_briefing: 'Phase 2 — Briefing',
  phase_3_content: 'Phase 3 — Content',
  phase_4_technik: 'Phase 4 — Technik',
  phase_5_qa: 'Phase 5 — QA',
  phase_6_golive: 'Phase 6 — Go-Live',
  phase_7_postlaunch: 'Phase 7 — Post-Launch',
  completed: 'Abgeschlossen',
};

export default function Dashboard() {
  const { isMobile } = useScreenSize();
  const [kpis, setKpis] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [projectsByPhase, setProjectsByPhase] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
    const interval = setInterval(loadDashboardData, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const [kpiRes, alertRes, projectRes] = await Promise.all([
        axios.get(`${API_BASE_URL}/api/dashboard/kpis`),
        axios.get(`${API_BASE_URL}/api/dashboard/alerts`),
        axios.get(`${API_BASE_URL}/api/dashboard/projects-by-phase`),
      ]);
      setKpis(kpiRes.data);
      setAlerts(alertRes.data);
      setProjectsByPhase(projectRes.data);
    } catch (error) {
      toast.error('Dashboard-Daten konnten nicht geladen werden.');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--kc-space-4)' }}>
        {[1, 2, 3].map((i) => (
          <div key={i} className="kc-skeleton" style={{ height: '80px' }} />
        ))}
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--kc-space-8)' }}>
      {/* Header */}
      <div className="kc-section-header">
        <span className="kc-eyebrow">Automation System</span>
        <h1>Dashboard</h1>
      </div>

      {/* KPI Cards */}
      {kpis && (
        <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr 1fr' : 'repeat(auto-fit, minmax(200px, 1fr))', gap: 'var(--kc-space-4)' }}>
          <KpiCard
            icon={FolderIcon}
            label="Aktive Projekte"
            value={kpis.active_projects}
          />
          <KpiCard
            icon={BanknotesIcon}
            label="Durchschn. Marge"
            value={
              <MarginBadge
                marginPercent={kpis.average_margin_percent}
                status={kpis.average_margin_percent >= 70 ? 'green' : kpis.average_margin_percent >= 60 ? 'yellow' : 'red'}
              />
            }
            raw
          />
          <KpiCard
            icon={CheckCircleIcon}
            label="Im Ziel (>70%)"
            value={kpis.projects_in_target}
            valueColor="var(--kc-success)"
          />
          <KpiCard
            icon={ExclamationTriangleIcon}
            label="Risiko (<60%)"
            value={kpis.projects_at_risk}
            valueColor={kpis.projects_at_risk > 0 ? 'var(--kc-rot)' : 'var(--kc-text-primaer)'}
          />
          <KpiCard
            icon={StarIcon}
            label="Offene Reviews"
            value={kpis.pending_reviews}
            valueColor={kpis.pending_reviews > 0 ? 'var(--kc-warning)' : 'var(--kc-text-primaer)'}
          />
        </div>
      )}

      {/* Audit KPIs */}
      {kpis && (kpis.audits_today > 0 || kpis.audits_avg_score > 0) && (
        <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr 1fr' : 'repeat(auto-fit, minmax(200px, 1fr))', gap: 'var(--kc-space-4)' }}>
          <KpiCard icon={MagnifyingGlassCircleIcon} label="Audits heute" value={kpis.audits_today} />
          <KpiCard
            icon={ChartBarIcon}
            label="Ø Audit-Score"
            value={`${kpis.audits_avg_score}/100`}
            valueColor={kpis.audits_avg_score >= 70 ? 'var(--kc-success)' : kpis.audits_avg_score >= 50 ? 'var(--kc-warning)' : 'var(--kc-rot)'}
          />
          <KpiCard
            icon={ArrowTrendingUpIcon}
            label="Verbesserungen"
            value={kpis.audits_improved}
            valueColor="var(--kc-success)"
          />
        </div>
      )}

      {/* Alerts */}
      <AlertBanner alerts={alerts} />

      {/* Kanban View */}
      <div>
        <div className="kc-section-header" style={{ marginBottom: 'var(--kc-space-4)' }}>
          <span className="kc-eyebrow">Pipeline</span>
          <h2>Projekte nach Phase</h2>
        </div>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: isMobile ? '1fr' : 'repeat(auto-fill, minmax(240px, 1fr))',
            gap: 'var(--kc-space-4)',
          }}
        >
          {Object.entries(projectsByPhase).map(([phaseKey, projects]) => (
            <div
              key={phaseKey}
              style={{
                background: 'var(--kc-weiss)',
                border: '1px solid var(--kc-rand)',
                borderRadius: 'var(--kc-radius-lg)',
                overflow: 'hidden',
              }}
            >
              {/* Phase Header */}
              <div
                style={{
                  padding: 'var(--kc-space-3) var(--kc-space-4)',
                  borderBottom: '1px solid var(--kc-rand)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                }}
              >
                <span
                  style={{
                    fontSize: 'var(--kc-text-xs)',
                    fontWeight: 700,
                    textTransform: 'uppercase',
                    letterSpacing: 'var(--kc-tracking-wide)',
                    color: 'var(--kc-text-subtil)',
                  }}
                >
                  {phaseNames[phaseKey] || phaseKey}
                </span>
                <span
                  className="kc-badge kc-badge--neutral"
                  style={{ fontSize: '0.65rem' }}
                >
                  {projects.length}
                </span>
              </div>

              {/* Phase Cards */}
              <div style={{ padding: 'var(--kc-space-3)', display: 'flex', flexDirection: 'column', gap: 'var(--kc-space-2)', minHeight: '60px' }}>
                {projects.length === 0 ? (
                  <p style={{ fontSize: 'var(--kc-text-xs)', color: 'var(--kc-mittel)', textAlign: 'center', padding: 'var(--kc-space-2)' }}>
                    Keine Projekte
                  </p>
                ) : (
                  projects.map((p) => (
                    <div
                      key={p.id}
                      style={{
                        padding: 'var(--kc-space-2) var(--kc-space-3)',
                        background: 'var(--kc-hell)',
                        borderRadius: 'var(--kc-radius-md)',
                        borderLeft: `3px solid ${
                          p.margin_status === 'green' ? 'var(--kc-success)' :
                          p.margin_status === 'yellow' ? 'var(--kc-warning)' :
                          p.margin_status === 'red' ? 'var(--kc-rot)' : 'var(--kc-rand)'
                        }`,
                      }}
                    >
                      <div
                        style={{
                          fontWeight: 600,
                          fontSize: 'var(--kc-text-sm)',
                          color: 'var(--kc-text-primaer)',
                          marginBottom: 'var(--kc-space-1)',
                        }}
                      >
                        {p.company_name}
                      </div>
                      <MarginBadge marginPercent={p.margin_percent} status={p.margin_status} />
                    </div>
                  ))
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function KpiCard({ icon: Icon, label, value, valueColor, raw = false }) {
  return (
    <div className="kc-kpi">
      <div className="kc-kpi__label">
        <Icon style={{ width: '16px', height: '16px' }} />
        {label}
      </div>
      <div
        className={raw ? '' : 'kc-kpi__value'}
        style={valueColor ? { color: valueColor } : undefined}
      >
        {value}
      </div>
    </div>
  );
}

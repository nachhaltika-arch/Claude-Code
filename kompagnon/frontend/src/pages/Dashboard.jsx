import React, { useEffect, useState } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';
import { useNavigate } from 'react-router-dom';
import API_BASE_URL from '../config';
import Card from '../components/ui/Card';
import Badge from '../components/ui/Badge';

const phaseNames = {
  phase_1_akquisition: 'Akquisition',
  phase_2_briefing: 'Briefing',
  phase_3_content: 'Content',
  phase_4_technik: 'Technik',
  phase_5_qa: 'QA',
  phase_6_golive: 'Go-Live',
  phase_7_postlaunch: 'Post-Launch',
  completed: 'Abgeschlossen',
};

const phaseIndex = {
  phase_1_akquisition: 1, phase_2_briefing: 2, phase_3_content: 3,
  phase_4_technik: 4, phase_5_qa: 5, phase_6_golive: 6,
  phase_7_postlaunch: 7, completed: 7,
};

const phaseColors = ['#008eaa', '#0284c7', '#7c3aed', '#059669', '#d97706', '#ea580c', '#16a34a'];

export default function Dashboard() {
  const navigate = useNavigate();
  const [kpis, setKpis] = useState(null);
  const [projectsByPhase, setProjectsByPhase] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [kpiRes, projectRes] = await Promise.all([
        axios.get(`${API_BASE_URL}/api/dashboard/kpis`),
        axios.get(`${API_BASE_URL}/api/dashboard/projects-by-phase`),
      ]);
      setKpis(kpiRes.data);
      setProjectsByPhase(projectRes.data);
    } catch {
      toast.error('Dashboard-Daten konnten nicht geladen werden.');
    } finally {
      setLoading(false);
    }
  };

  if (loading && !kpis) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        {[1, 2, 3, 4].map(i => (
          <div key={i} className="skeleton" style={{ height: 80 }} />
        ))}
      </div>
    );
  }

  const kpiCards = kpis ? [
    { label: 'Aktive Projekte', value: kpis.active_projects, delta: null },
    { label: 'Leads Pipeline', value: Object.values(projectsByPhase).flat().length || '—' },
    { label: 'Audits heute', value: kpis.audits_today },
    { label: 'Ø Homepage-Score', value: kpis.audits_avg_score ? `${kpis.audits_avg_score}` : '—' },
  ] : [];

  // Flatten projects for left card
  const allProjects = Object.entries(projectsByPhase).flatMap(([phase, projects]) =>
    projects.map(p => ({ ...p, phase }))
  ).filter(p => p.phase !== 'completed').slice(0, 8);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20, animation: 'fadeIn 0.3s ease' }}>
      {/* KPI Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 12 }}>
        {kpiCards.map((kpi, i) => (
          <Card key={i} padding="md">
            <div style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-tertiary)', marginBottom: 6 }}>
              {kpi.label}
            </div>
            <div style={{ fontSize: 28, fontWeight: 500, color: 'var(--text-primary)', lineHeight: 1 }}>
              {kpi.value}
            </div>
            {kpi.delta && (
              <div style={{ fontSize: 11, color: kpi.delta > 0 ? 'var(--status-success-text)' : 'var(--status-danger-text)', marginTop: 4 }}>
                {kpi.delta > 0 ? '+' : ''}{kpi.delta}%
              </div>
            )}
          </Card>
        ))}
      </div>

      {/* Two-column layout */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.6fr 1fr', gap: 16 }}>

        {/* Left: Active Projects */}
        <Card padding="lg">
          <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)', marginBottom: 12 }}>
            Aktive Projekte
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {allProjects.length === 0 && (
              <div style={{ fontSize: 12, color: 'var(--text-tertiary)', padding: 16, textAlign: 'center' }}>
                Keine aktiven Projekte
              </div>
            )}
            {allProjects.map((p) => {
              const pi = phaseIndex[p.phase] || 1;
              const progress = (pi / 7) * 100;
              const color = phaseColors[(pi - 1) % phaseColors.length];
              return (
                <div
                  key={p.id}
                  style={{
                    display: 'flex', alignItems: 'center', gap: 10,
                    padding: '8px 0', borderBottom: '1px solid var(--border-light)',
                    cursor: 'pointer',
                  }}
                  onClick={() => navigate(`/app/projects/${p.id}`)}
                >
                  <div style={{
                    width: 28, height: 28, borderRadius: 'var(--radius-md)',
                    background: `${color}18`, display: 'flex', alignItems: 'center',
                    justifyContent: 'center', flexShrink: 0,
                  }}>
                    <div style={{ width: 8, height: 8, borderRadius: '50%', background: color }} />
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {p.company_name}
                    </div>
                    <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>
                      {phaseNames[p.phase] || p.phase}
                    </div>
                  </div>
                  {/* Progress bar */}
                  <div style={{ width: 60, height: 3, background: 'var(--border-light)', borderRadius: 2, flexShrink: 0 }}>
                    <div style={{ width: `${progress}%`, height: '100%', background: color, borderRadius: 2, transition: 'width 0.5s ease' }} />
                  </div>
                  <Badge variant={p.margin_status === 'green' ? 'success' : p.margin_status === 'yellow' ? 'warning' : 'danger'}>
                    {p.margin_status === 'green' ? 'Im Ziel' : p.margin_status === 'yellow' ? 'Risiko' : 'Kritisch'}
                  </Badge>
                </div>
              );
            })}
          </div>
        </Card>

        {/* Right: Activity feed + stats */}
        <Card padding="lg">
          <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)', marginBottom: 12 }}>
            Aktivitäten
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {/* Generate activity items from projects */}
            {allProjects.slice(0, 5).map((p, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
                <div style={{
                  width: 6, height: 6, borderRadius: '50%', marginTop: 5, flexShrink: 0,
                  background: i === 0 ? 'var(--brand-primary)' : i < 3 ? 'var(--status-success-text)' : 'var(--text-tertiary)',
                }} />
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 12, color: 'var(--text-primary)' }}>
                    <strong>{p.company_name}</strong> — {phaseNames[p.phase] || 'In Bearbeitung'}
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>
                    Projekt aktiv
                  </div>
                </div>
              </div>
            ))}
            {allProjects.length === 0 && (
              <div style={{ fontSize: 12, color: 'var(--text-tertiary)', textAlign: 'center', padding: 20 }}>
                Keine aktuellen Aktivitäten
              </div>
            )}
          </div>

          {/* Mini stats at bottom */}
          {kpis && (
            <div style={{
              display: 'flex', gap: 12, marginTop: 'auto', paddingTop: 16,
              borderTop: '1px solid var(--border-light)',
            }}>
              {[
                { label: 'Im Ziel', value: kpis.projects_in_target },
                { label: 'Ø Score', value: kpis.audits_avg_score || '—' },
                { label: 'Abgeschlossen', value: projectsByPhase.completed?.length || 0 },
              ].map((stat, i) => (
                <div key={i} style={{ flex: 1, textAlign: 'center' }}>
                  <div style={{ fontSize: 16, fontWeight: 500, color: 'var(--text-primary)' }}>{stat.value}</div>
                  <div style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>{stat.label}</div>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}

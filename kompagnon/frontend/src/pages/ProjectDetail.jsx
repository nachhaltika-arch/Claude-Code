import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import toast from 'react-hot-toast';
import PhaseTracker from '../components/PhaseTracker';
import MarginBadge from '../components/MarginBadge';

import API_BASE_URL from '../config';

export default function ProjectDetail() {
  const { id } = useParams();
  const [project, setProject] = useState(null);
  const [margin, setMargin] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    loadProject();
  }, [id]);

  const loadProject = async () => {
    try {
      setLoading(true);
      const [projectRes, marginRes] = await Promise.all([
        axios.get(`${API_BASE_URL}/api/projects/${id}`),
        axios.get(`${API_BASE_URL}/api/projects/${id}/margin`),
      ]);
      setProject(projectRes.data);
      setMargin(marginRes.data);
    } catch (error) {
      toast.error('Projekt konnte nicht geladen werden.');
    } finally {
      setLoading(false);
    }
  };

  if (loading || !project) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <div className="skeleton" style={{ height: '40px', width: '300px' }} />
        <div className="skeleton" style={{ height: '60px' }} />
        <div className="skeleton" style={{ height: '200px' }} />
      </div>
    );
  }

  const tabs = ['overview', 'checklists', 'zeit', 'kommunikation'];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div  style={{ marginBottom: 0 }}>
          <span >Projekt #{project.id}</span>
          <h1 style={{ fontSize: 'var(--kc-text-3xl)' }}>{project.company_name}</h1>
        </div>
        {margin && <MarginBadge marginPercent={margin.margin_percent} status={margin.status} />}
      </div>

      {/* Phase Tracker */}
      <div className="kc-card">
        <PhaseTracker currentPhase={project.status} />
      </div>

      {/* Tabs */}
      <div className="kc-tabs">
        {tabs.map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`kc-tab ${activeTab === tab ? 'kc-tab--active' : ''}`}
          >
            {tab === 'overview' ? 'Übersicht' :
             tab === 'checklists' ? 'Checklisten' :
             tab === 'zeit' ? 'Zeiterfassung' : 'Kommunikation'}
          </button>
        ))}
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* Project Info Grid */}
          <div
            className="kc-card"
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
              gap: '24px',
            }}
          >
            <InfoBlock label="Status" value={project.status.replace('phase_', 'Phase ')} />
            <InfoBlock label="Festpreis" value={`€${project.fixed_price.toFixed(2)}`} mono />
            <InfoBlock label="Stunden geloggt" value={`${project.actual_hours.toFixed(1)}h`} mono />
            {margin && <InfoBlock label="Gesamtkosten" value={`€${margin.total_costs.toFixed(2)}`} mono />}
          </div>

          {/* Margin Detail */}
          {margin && (
            <div
              className="kc-card"
              style={{
                background: margin.status === 'red' ? 'var(--kc-rot-subtle)' : 'var(--bg-app)',
                border: margin.status === 'red' ? '1px solid var(--brand-primary)' : '1px solid var(--border-light)',
              }}
            >
              <div style={{ marginBottom: '16px' }}>
                <span >Marge</span>
                <h2 style={{ fontSize: '22px', margin: 0 }}>
                  Profitabilität
                </h2>
              </div>
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
                  gap: '24px',
                }}
              >
                <InfoBlock
                  label="Personenstunden"
                  value={`${margin.human_hours.toFixed(1)}h × €${project.hourly_rate}/h`}
                  mono
                />
                <InfoBlock label="KI-Kosten" value={`€${margin.ai_tool_costs.toFixed(2)}`} mono />
                <InfoBlock
                  label="Verbleibend bis 70%"
                  value={`${margin.hours_remaining_at_target.toFixed(1)}h`}
                  mono
                />
                <InfoBlock
                  label="Marge"
                  value={
                    <MarginBadge marginPercent={margin.margin_percent} status={margin.status} />
                  }
                  raw
                />
              </div>
            </div>
          )}
        </div>
      )}

      {/* Placeholder tabs */}
      {activeTab !== 'overview' && (
        <div
          className="kc-card"
          style={{ textAlign: 'center', padding: 'var(--kc-space-16)', color: 'var(--text-tertiary)' }}
        >
          <p style={{ fontSize: '16px', fontWeight: 600 }}>
            {activeTab === 'checklists' ? 'Checklisten' :
             activeTab === 'zeit' ? 'Zeiterfassung' : 'Kommunikation'}
          </p>
          <p style={{ fontSize: '13px' }}>In Entwicklung</p>
        </div>
      )}
    </div>
  );
}

function InfoBlock({ label, value, mono = false, raw = false }) {
  return (
    <div>
      <p
        style={{
          fontSize: '11px',
          fontWeight: 600,
          textTransform: 'uppercase',
          letterSpacing: 'var(--kc-tracking-wide)',
          color: 'var(--text-tertiary)',
          marginBottom: '4px',
        }}
      >
        {label}
      </p>
      {raw ? (
        <div>{value}</div>
      ) : (
        <p
          style={{
            fontSize: '16px',
            fontWeight: 700,
            fontFamily: mono ? 'var(--font-mono)' : 'var(--font-sans)',
            color: 'var(--text-primary)',
            margin: 0,
          }}
        >
          {value}
        </p>
      )}
    </div>
  );
}

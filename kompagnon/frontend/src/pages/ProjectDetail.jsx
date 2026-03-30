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
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--kc-space-4)' }}>
        <div className="kc-skeleton" style={{ height: '40px', width: '300px' }} />
        <div className="kc-skeleton" style={{ height: '60px' }} />
        <div className="kc-skeleton" style={{ height: '200px' }} />
      </div>
    );
  }

  const tabs = ['overview', 'checklists', 'zeit', 'kommunikation'];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--kc-space-6)' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div className="kc-section-header" style={{ marginBottom: 0 }}>
          <span className="kc-eyebrow">Projekt #{project.id}</span>
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
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--kc-space-6)' }}>
          {/* Project Info Grid */}
          <div
            className="kc-card"
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
              gap: 'var(--kc-space-6)',
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
                background: margin.status === 'red' ? 'var(--kc-rot-subtle)' : 'var(--kc-hell)',
                border: margin.status === 'red' ? '1px solid var(--kc-rot)' : '1px solid var(--kc-rand)',
              }}
            >
              <div style={{ marginBottom: 'var(--kc-space-4)' }}>
                <span className="kc-eyebrow">Marge</span>
                <h2 style={{ fontSize: 'var(--kc-text-2xl)', margin: 0 }}>
                  Profitabilität
                </h2>
              </div>
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
                  gap: 'var(--kc-space-6)',
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
          style={{ textAlign: 'center', padding: 'var(--kc-space-16)', color: 'var(--kc-mittel)' }}
        >
          <p style={{ fontSize: 'var(--kc-text-lg)', fontWeight: 600 }}>
            {activeTab === 'checklists' ? 'Checklisten' :
             activeTab === 'zeit' ? 'Zeiterfassung' : 'Kommunikation'}
          </p>
          <p style={{ fontSize: 'var(--kc-text-sm)' }}>In Entwicklung</p>
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
          fontSize: 'var(--kc-text-xs)',
          fontWeight: 600,
          textTransform: 'uppercase',
          letterSpacing: 'var(--kc-tracking-wide)',
          color: 'var(--kc-text-subtil)',
          marginBottom: 'var(--kc-space-1)',
        }}
      >
        {label}
      </p>
      {raw ? (
        <div>{value}</div>
      ) : (
        <p
          style={{
            fontSize: 'var(--kc-text-lg)',
            fontWeight: 700,
            fontFamily: mono ? 'var(--kc-font-mono)' : 'var(--kc-font-display)',
            color: 'var(--kc-text-primaer)',
            margin: 0,
          }}
        >
          {value}
        </p>
      )}
    </div>
  );
}

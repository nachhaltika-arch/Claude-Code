import React, { useEffect, useState } from 'react';
import {
  FolderIcon,
  BanknotesIcon,
  CheckCircleIcon,
  ExclamationIcon,
  UserGroupIcon,
} from '@heroicons/react/24/outline';
import MarginBadge from '../components/MarginBadge';
import axios from 'axios';
import toast from 'react-hot-toast';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export default function Dashboard() {
  const [kpis, setKpis] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [projectsByPhase, setProjectsByPhase] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
    // Refresh every 30 seconds
    const interval = setInterval(loadDashboardData, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);

      // Fetch KPIs
      const kpiRes = await axios.get(`${API_URL}/api/dashboard/kpis`);
      setKpis(kpiRes.data);

      // Fetch Alerts
      const alertRes = await axios.get(`${API_URL}/api/dashboard/alerts`);
      setAlerts(alertRes.data);

      // Fetch Projects by Phase
      const projectRes = await axios.get(`${API_URL}/api/dashboard/projects-by-phase`);
      setProjectsByPhase(projectRes.data);
    } catch (error) {
      toast.error('Failed to load dashboard data');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="bg-gray-200 h-24 rounded-lg animate-pulse" />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>

      {/* KPI Cards */}
      {kpis && (
        <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
          <div className="bg-white p-4 rounded-lg shadow">
            <div className="flex items-center gap-2">
              <FolderIcon className="w-5 h-5 text-kompagnon-600" />
              <span className="text-gray-600 text-sm">Aktive Projekte</span>
            </div>
            <div className="text-3xl font-bold mt-2 text-gray-900">
              {kpis.active_projects}
            </div>
          </div>

          <div className="bg-white p-4 rounded-lg shadow">
            <div className="flex items-center gap-2">
              <BanknotesIcon className="w-5 h-5 text-success" />
              <span className="text-gray-600 text-sm">Ø Marge</span>
            </div>
            <div className="text-3xl font-bold mt-2">
              <MarginBadge
                marginPercent={kpis.average_margin_percent}
                status={kpis.average_margin_percent >= 70 ? 'green' : 'yellow'}
              />
            </div>
          </div>

          <div className="bg-white p-4 rounded-lg shadow">
            <div className="flex items-center gap-2">
              <CheckCircleIcon className="w-5 h-5 text-success" />
              <span className="text-gray-600 text-sm">Target (≥70%)</span>
            </div>
            <div className="text-3xl font-bold mt-2 text-success">
              {kpis.projects_in_target}
            </div>
          </div>

          <div className="bg-white p-4 rounded-lg shadow">
            <div className="flex items-center gap-2">
              <ExclamationIcon className="w-5 h-5 text-danger" />
              <span className="text-gray-600 text-sm">Risiko (&lt;60%)</span>
            </div>
            <div className="text-3xl font-bold mt-2 text-danger">
              {kpis.projects_at_risk}
            </div>
          </div>

          <div className="bg-white p-4 rounded-lg shadow">
            <div className="flex items-center gap-2">
              <UserGroupIcon className="w-5 h-5 text-warning" />
              <span className="text-gray-600 text-sm">Ausstehende Reviews</span>
            </div>
            <div className="text-3xl font-bold mt-2 text-warning">
              {kpis.pending_reviews}
            </div>
          </div>
        </div>
      )}

      {/* Alerts */}
      {alerts.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <h2 className="font-bold text-red-900 mb-3 flex items-center gap-2">
            <ExclamationIcon className="w-5 h-5" />
            Aktive Warnungen ({alerts.length})
          </h2>
          <div className="space-y-2">
            {alerts.slice(0, 5).map((alert, idx) => (
              <div key={idx} className="text-sm text-red-800 bg-white p-2 rounded border border-red-200">
                <strong>Projekt #{alert.project_id}</strong> — {alert.message}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Kanban View */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-bold mb-4">Projekte nach Phase</h2>
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
          {Object.entries(projectsByPhase).slice(0, 4).map(([phase, projects]) => (
            <div key={phase} className="bg-gray-50 rounded p-3">
              <h3 className="font-bold text-sm text-gray-700 mb-2">
                {phase.replace('phase_1_akquisition', 'Phase 1: Akquisition')
                  .replace(/_/g, ' ')
                  .toUpperCase()}
              </h3>
              <div className="space-y-2">
                {projects.length === 0 ? (
                  <p className="text-xs text-gray-500">Keine Projekte</p>
                ) : (
                  projects.map((p) => (
                    <div key={p.id} className="bg-white p-2 rounded border border-gray-200 text-xs">
                      <div className="font-semibold text-gray-900">{p.company_name}</div>
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

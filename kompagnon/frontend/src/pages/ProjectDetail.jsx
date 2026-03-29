import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import toast from 'react-hot-toast';
import PhaseTracker from '../components/PhaseTracker';
import MarginBadge from '../components/MarginBadge';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

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
        axios.get(`${API_URL}/api/projects/${id}`),
        axios.get(`${API_URL}/api/projects/${id}/margin`),
      ]);
      setProject(projectRes.data);
      setMargin(marginRes.data);
    } catch (error) {
      toast.error('Failed to load project');
    } finally {
      setLoading(false);
    }
  };

  if (loading || !project) return <div>Loading...</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">{project.company_name}</h1>
        {margin && (
          <MarginBadge
            marginPercent={margin.margin_percent}
            status={margin.status}
          />
        )}
      </div>

      <PhaseTracker currentPhase={project.status} />

      {/* Tabs */}
      <div className="flex border-b border-gray-200">
        {['overview', 'checklists', 'time', 'communications'].map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 font-medium text-sm border-b-2 transition-colors ${
              activeTab === tab
                ? 'border-kompagnon-600 text-kompagnon-600'
                : 'border-transparent text-gray-600 hover:text-gray-900'
            }`}
          >
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </button>
        ))}
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-2 gap-4 bg-white p-6 rounded-lg shadow">
          <div>
            <p className="text-sm text-gray-600">Status</p>
            <p className="text-lg font-bold text-gray-900">{project.status}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Fixed Price</p>
            <p className="text-lg font-bold text-gray-900">€{project.fixed_price.toFixed(2)}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Stunden geloggt</p>
            <p className="text-lg font-bold text-gray-900">{project.actual_hours.toFixed(1)}h</p>
          </div>
          {margin && (
            <div>
              <p className="text-sm text-gray-600">Gesamtkosten</p>
              <p className="text-lg font-bold text-gray-900">€{margin.total_costs.toFixed(2)}</p>
            </div>
          )}
        </div>
      )}

      {/* Margin Details */}
      {margin && activeTab === 'overview' && (
        <div className="bg-blue-50 border border-blue-200 p-6 rounded-lg">
          <h3 className="font-bold text-blue-900 mb-3">Margin Details</h3>
          <div className="grid grid-cols-3 gap-4 text-sm">
            <div>
              <p className="text-blue-700">Personenstunden</p>
              <p className="font-bold text-blue-900">{margin.human_hours.toFixed(1)}h × €{project.hourly_rate}/h</p>
            </div>
            <div>
              <p className="text-blue-700">KI-Kosten</p>
              <p className="font-bold text-blue-900">€{margin.ai_tool_costs.toFixed(2)}</p>
            </div>
            <div>
              <p className="text-blue-700">Verbleibend bis 70%</p>
              <p className="font-bold text-blue-900">{margin.hours_remaining_at_target.toFixed(1)}h</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

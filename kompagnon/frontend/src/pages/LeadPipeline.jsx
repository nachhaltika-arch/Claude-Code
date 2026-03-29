import React, { useEffect, useState } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export default function LeadPipeline() {
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadLeads();
  }, []);

  const loadLeads = async () => {
    try {
      setLoading(true);
      const res = await axios.get(`${API_URL}/api/leads/`);
      setLeads(res.data);
    } catch (error) {
      toast.error('Failed to load leads');
    } finally {
      setLoading(false);
    }
  };

  const statusColors = {
    new: 'bg-blue-100 text-blue-800',
    contacted: 'bg-yellow-100 text-yellow-800',
    qualified: 'bg-green-100 text-green-800',
    proposal_sent: 'bg-purple-100 text-purple-800',
    won: 'bg-green-500 text-white',
    lost: 'bg-red-100 text-red-800',
  };

  return (
    <div className="space-y-4">
      <h1 className="text-3xl font-bold text-gray-900">Lead Pipeline</h1>

      {loading ? (
        <div className="text-gray-500">Loading...</div>
      ) : (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-100 border-b">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-bold text-gray-700">Unternehmen</th>
                <th className="px-4 py-3 text-left text-sm font-bold text-gray-700">Kontakt</th>
                <th className="px-4 py-3 text-left text-sm font-bold text-gray-700">Stadt</th>
                <th className="px-4 py-3 text-left text-sm font-bold text-gray-700">Status</th>
                <th className="px-4 py-3 text-left text-sm font-bold text-gray-700">Score</th>
              </tr>
            </thead>
            <tbody>
              {leads.map((lead) => (
                <tr key={lead.id} className="border-b hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm font-medium text-gray-900">{lead.company_name}</td>
                  <td className="px-4 py-3 text-sm text-gray-600">{lead.contact_name}</td>
                  <td className="px-4 py-3 text-sm text-gray-600">{lead.city}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`inline-block px-2 py-1 rounded text-xs font-bold ${
                        statusColors[lead.status] || 'bg-gray-100'
                      }`}
                    >
                      {lead.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm font-bold text-gray-900">{lead.analysis_score}/100</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

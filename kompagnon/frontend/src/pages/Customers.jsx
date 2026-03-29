import React, { useEffect, useState } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export default function Customers() {
  const [customers, setCustomers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadCustomers();
  }, []);

  const loadCustomers = async () => {
    try {
      setLoading(true);
      const res = await axios.get(`${API_URL}/api/customers/`);
      setCustomers(res.data);
    } catch (error) {
      toast.error('Failed to load customers');
    } finally {
      setLoading(false);
    }
  };

  const upsellStatusColors = {
    none: 'bg-gray-100 text-gray-800',
    offered: 'bg-yellow-100 text-yellow-800',
    accepted: 'bg-green-100 text-green-800',
  };

  return (
    <div className="space-y-4">
      <h1 className="text-3xl font-bold text-gray-900">Customers</h1>

      {loading ? (
        <div className="text-gray-500">Loading...</div>
      ) : (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-100 border-b">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-bold">Projekt ID</th>
                <th className="px-4 py-3 text-left text-sm font-bold">Upsell Status</th>
                <th className="px-4 py-3 text-left text-sm font-bold">Paket</th>
                <th className="px-4 py-3 text-left text-sm font-bold">Monatlich</th>
              </tr>
            </thead>
            <tbody>
              {customers.map((customer) => (
                <tr key={customer.id} className="border-b hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm font-medium">#{customer.project_id}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`px-2 py-1 rounded text-xs font-bold ${
                        upsellStatusColors[customer.upsell_status]
                      }`}
                    >
                      {customer.upsell_status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm">{customer.upsell_package || '—'}</td>
                  <td className="px-4 py-3 text-sm font-bold">
                    €{customer.recurring_revenue.toFixed(2)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

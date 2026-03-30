import React, { useEffect, useState } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';

import API_BASE_URL from '../config';

const upsellConfig = {
  none:     { label: 'Kein Upsell',  className: 'kc-badge kc-badge--neutral' },
  offered:  { label: 'Angeboten',    className: 'kc-badge kc-badge--warning' },
  accepted: { label: 'Akzeptiert',   className: 'kc-badge kc-badge--success' },
};

export default function Customers() {
  const [customers, setCustomers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadCustomers();
  }, []);

  const loadCustomers = async () => {
    try {
      setLoading(true);
      const res = await axios.get(`${API_BASE_URL}/api/customers/`);
      setCustomers(res.data);
    } catch (error) {
      toast.error('Kunden konnten nicht geladen werden.');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--kc-space-4)' }}>
        <div className="kc-skeleton" style={{ height: '40px', width: '200px' }} />
        {[1, 2, 3].map((i) => (
          <div key={i} className="kc-skeleton" style={{ height: '48px' }} />
        ))}
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--kc-space-6)' }}>
      <div className="kc-section-header">
        <span className="kc-eyebrow">After Sales</span>
        <h1>Bestandskunden</h1>
      </div>

      <div className="kc-card" style={{ padding: 0, overflow: 'hidden' }}>
        <table className="kc-table">
          <thead>
            <tr>
              <th>Projekt</th>
              <th>Upsell Status</th>
              <th>Paket</th>
              <th style={{ textAlign: 'right' }}>Monatlich</th>
            </tr>
          </thead>
          <tbody>
            {customers.length === 0 ? (
              <tr>
                <td colSpan={4} style={{ textAlign: 'center', color: 'var(--kc-mittel)', padding: 'var(--kc-space-8)' }}>
                  Keine Kunden vorhanden.
                </td>
              </tr>
            ) : (
              customers.map((customer) => {
                const cfg = upsellConfig[customer.upsell_status] || upsellConfig.none;
                return (
                  <tr key={customer.id}>
                    <td style={{ fontWeight: 600, fontFamily: 'var(--kc-font-mono)' }}>
                      #{customer.project_id}
                    </td>
                    <td><span className={cfg.className}>{cfg.label}</span></td>
                    <td style={{ color: 'var(--kc-text-sekundaer)' }}>
                      {customer.upsell_package || '\u2014'}
                    </td>
                    <td
                      style={{
                        textAlign: 'right',
                        fontFamily: 'var(--kc-font-mono)',
                        fontWeight: 700,
                        color: customer.recurring_revenue > 0 ? 'var(--kc-success)' : 'var(--kc-text-subtil)',
                      }}
                    >
                      {'\u20AC'}{customer.recurring_revenue.toFixed(2)}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import API_BASE_URL from '../../config';

const statusLabels = { offen: 'Offen', bezahlt: 'Bezahlt', paid: 'Bezahlt', overdue: 'Überfällig' };

export default function MeineRechnungen() {
  const { token } = useAuth();
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/invoices/my`, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => r.json())
      .then(d => { setInvoices(Array.isArray(d) ? d : []); setLoading(false); })
      .catch(() => setLoading(false));
  }, [token]);

  const cardStyle = {
    background: 'var(--bg-surface)', borderRadius: 'var(--radius-lg)',
    border: '1px solid var(--border-light)', padding: '16px 20px', marginBottom: 10,
  };
  const badgeStyle = (type) => ({
    display: 'inline-block', padding: '2px 8px', borderRadius: 4, fontSize: 11, fontWeight: 600,
    background: type === 'bezahlt' || type === 'paid' ? 'var(--status-success-bg)' : type === 'overdue' ? 'var(--status-danger-bg)' : 'var(--status-warning-bg)',
    color: type === 'bezahlt' || type === 'paid' ? 'var(--status-success-text)' : type === 'overdue' ? 'var(--status-danger-text)' : 'var(--status-warning-text)',
  });

  return (
    <div style={{ maxWidth: 720, margin: '0 auto', padding: '0 0 40px' }}>
      <div style={{ fontSize: 20, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 20 }}>
        💳 Rechnungen
      </div>

      {loading && <div style={{ color: 'var(--text-tertiary)', fontSize: 13 }}>Wird geladen…</div>}
      {!loading && invoices.length === 0 && (
        <div style={{ ...cardStyle, textAlign: 'center', color: 'var(--text-tertiary)', fontSize: 13, padding: 40 }}>
          Noch keine Rechnungen vorhanden.
        </div>
      )}
      {invoices.map(inv => (
        <div key={inv.id} style={{ ...cardStyle, display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12 }}>
          <div>
            <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>
              {inv.line_item || inv.invoice_number || `Rechnung #${inv.id}`}
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 3 }}>
              {inv.invoice_number} · {inv.created_at ? new Date(inv.created_at).toLocaleDateString('de-DE') : ''}
              {inv.due_date && ` · Fällig: ${new Date(inv.due_date).toLocaleDateString('de-DE')}`}
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexShrink: 0 }}>
            <span style={badgeStyle(inv.status)}>{statusLabels[inv.status] || inv.status || 'Offen'}</span>
            <span style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)' }}>
              {Number(inv.amount_gross || 0).toLocaleString('de-DE', { style: 'currency', currency: 'EUR' })}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}

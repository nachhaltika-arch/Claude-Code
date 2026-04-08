import React, { useState, useEffect, useRef } from 'react';
import toast from 'react-hot-toast';
import { useAuth } from '../context/AuthContext';
import API_BASE_URL from '../config';

export default function RetainerDashboard() {
  const { token } = useAuth();
  const fetchedRef = useRef(false);

  const [retainers, setRetainers] = useState([]);
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showNewRetainer, setShowNewRetainer] = useState(false);
  const [showNewInvoice, setShowNewInvoice] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const [retainerForm, setRetainerForm] = useState({ customer_name: '', customer_email: '', package_name: 'SEO-Pflege', price_net: 89, start_date: new Date().toISOString().slice(0, 10) });
  const [invoiceForm, setInvoiceForm] = useState({ customer_name: '', customer_email: '', amount_net: 89, line_item: 'Website-Pflege & SEO-Paket' });

  const mkH = () => ({ 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) });

  const fetchRetainers = () => fetch(`${API_BASE_URL}/api/retainer`, { headers: mkH() }).then(r => r.json()).then(d => setRetainers(Array.isArray(d) ? d : [])).catch(() => toast.error('Vertraege konnten nicht geladen werden'));
  const fetchInvoices = () => fetch(`${API_BASE_URL}/api/invoices`, { headers: mkH() }).then(r => r.json()).then(d => setInvoices(Array.isArray(d) ? d : [])).catch(() => toast.error('Rechnungen konnten nicht geladen werden'));

  useEffect(() => {
    if (fetchedRef.current) return;
    fetchedRef.current = true;
    Promise.all([fetchRetainers(), fetchInvoices()]).finally(() => setLoading(false));
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const createRetainer = async () => {
    if (!retainerForm.customer_name.trim()) { toast.error('Kundenname erforderlich'); return; }
    setSubmitting(true);
    try {
      const r = await fetch(`${API_BASE_URL}/api/retainer`, { method: 'POST', headers: mkH(), body: JSON.stringify(retainerForm) });
      if (r.ok) { toast.success('Vertrag erstellt'); setShowNewRetainer(false); setRetainerForm({ customer_name: '', customer_email: '', package_name: 'SEO-Pflege', price_net: 89, start_date: new Date().toISOString().slice(0, 10) }); fetchRetainers(); }
      else toast.error((await r.json()).detail || 'Fehler');
    } catch { toast.error('Erstellen fehlgeschlagen'); }
    setSubmitting(false);
  };

  const createInvoice = async () => {
    if (!invoiceForm.customer_name.trim()) { toast.error('Kundenname erforderlich'); return; }
    setSubmitting(true);
    try {
      const r = await fetch(`${API_BASE_URL}/api/invoices`, { method: 'POST', headers: mkH(), body: JSON.stringify(invoiceForm) });
      if (r.ok) { const d = await r.json(); toast.success(`Rechnung ${d.invoice_number} erstellt`); setShowNewInvoice(false); setInvoiceForm({ customer_name: '', customer_email: '', amount_net: 89, line_item: 'Website-Pflege & SEO-Paket' }); fetchInvoices(); }
      else toast.error((await r.json()).detail || 'Fehler');
    } catch { toast.error('Erstellen fehlgeschlagen'); }
    setSubmitting(false);
  };

  const downloadPdf = async (invId, invNum) => {
    try {
      const r = await fetch(`${API_BASE_URL}/api/invoices/${invId}/pdf`, { headers: mkH() });
      if (!r.ok) { toast.error('PDF konnte nicht geladen werden'); return; }
      const blob = await r.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url; a.download = `Rechnung-${invNum}.pdf`; a.click();
      URL.revokeObjectURL(url);
    } catch { toast.error('Download fehlgeschlagen'); }
  };

  const fmtDate = (d) => d ? new Date(d).toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' }) : '-';
  const fmtCurrency = (v) => v != null ? `${Number(v).toFixed(2)} \u20ac` : '-';

  const statusBadge = (status, map) => {
    const s = map[status] || map._default || { label: status, bg: 'var(--bg-app)', color: 'var(--text-secondary)' };
    return <span style={{ display: 'inline-block', padding: '2px 10px', borderRadius: 999, fontSize: 11, fontWeight: 500, background: s.bg, color: s.color }}>{s.label}</span>;
  };

  const retainerStatusMap = {
    aktiv: { label: 'Aktiv', bg: 'var(--status-success-bg)', color: 'var(--status-success-text)' },
    pausiert: { label: 'Pausiert', bg: 'var(--status-warning-bg)', color: '#92600a' },
    gekuendigt: { label: 'Gekuendigt', bg: 'var(--status-danger-bg)', color: 'var(--status-danger-text)' },
    _default: { label: 'Unbekannt', bg: 'var(--bg-app)', color: 'var(--text-secondary)' },
  };

  const invoiceStatusMap = {
    offen: { label: 'Offen', bg: 'var(--status-warning-bg)', color: '#92600a' },
    bezahlt: { label: 'Bezahlt', bg: 'var(--status-success-bg)', color: 'var(--status-success-text)' },
    ueberfaellig: { label: 'Ueberfaellig', bg: 'var(--status-danger-bg)', color: 'var(--status-danger-text)' },
    _default: { label: 'Offen', bg: 'var(--status-warning-bg)', color: '#92600a' },
  };

  const card = { background: 'var(--bg-surface)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-light)' };
  const btnPrimary = { background: 'var(--brand-primary)', color: '#fff', border: 'none', padding: '8px 16px', borderRadius: 'var(--radius-md)', fontSize: 13, fontWeight: 500, cursor: 'pointer', fontFamily: 'var(--font-sans)' };
  const btnSecondary = { background: 'transparent', color: 'var(--text-secondary)', border: '1px solid var(--border-light)', padding: '6px 12px', borderRadius: 'var(--radius-md)', fontSize: 12, fontWeight: 500, cursor: 'pointer', fontFamily: 'var(--font-sans)' };
  const overlay = { position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', zIndex: 9999, display: 'flex', alignItems: 'center', justifyContent: 'center' };
  const modal = { background: 'var(--bg-surface)', borderRadius: 12, padding: 28, width: '100%', maxWidth: 480, display: 'flex', flexDirection: 'column', gap: 14 };
  const input = { width: '100%', padding: '8px 12px', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)', fontSize: 13, fontFamily: 'var(--font-sans)', background: 'var(--bg-surface)', color: 'var(--text-primary)', boxSizing: 'border-box' };
  const label = { fontSize: 12, fontWeight: 500, color: 'var(--text-secondary)', display: 'block', marginBottom: 4 };
  const thStyle = { fontSize: 10, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-tertiary)' };

  if (loading) return <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '40vh', color: 'var(--text-tertiary)', fontSize: 14 }}>Laden...</div>;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <h1 style={{ fontSize: 22, fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>Retainer & Rechnungen</h1>

      {/* ── Aktive Vertraege ─────────────────────────────────────── */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <h2 style={{ fontSize: 16, fontWeight: 600, color: 'var(--text-primary)', margin: 0 }}>Aktive Vertraege</h2>
          <button style={btnPrimary} onClick={() => setShowNewRetainer(true)}>+ Neuer Vertrag</button>
        </div>
        <div style={card}>
          <div style={{ display: 'grid', gridTemplateColumns: '1.5fr 1fr 100px 100px 120px 80px', gap: 12, padding: '10px 20px', borderBottom: '1px solid var(--border-light)', background: 'var(--bg-app)', borderRadius: '8px 8px 0 0' }}>
            {['Kunde', 'Paket', 'Preis/Monat', 'Start', 'Naechste Rechnung', 'Status'].map(h => <span key={h} style={thStyle}>{h}</span>)}
          </div>
          {retainers.length === 0 && <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-tertiary)', fontSize: 13 }}>Noch keine Vertraege vorhanden.</div>}
          {retainers.map((r, idx) => (
            <div key={r.id} style={{ display: 'grid', gridTemplateColumns: '1.5fr 1fr 100px 100px 120px 80px', gap: 12, padding: '12px 20px', alignItems: 'center', borderBottom: idx < retainers.length - 1 ? '1px solid var(--border-light)' : 'none', transition: 'background 0.1s' }} onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-hover)'} onMouseLeave={e => e.currentTarget.style.background = 'transparent'}>
              <div>
                <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)' }}>{r.customer_name || '-'}</div>
                <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>{r.customer_email}</div>
              </div>
              <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{r.package_name}</div>
              <div style={{ fontSize: 12, color: 'var(--text-primary)', fontWeight: 600 }}>{fmtCurrency(r.price_net)}</div>
              <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{fmtDate(r.start_date)}</div>
              <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{fmtDate(r.next_billing_date)}</div>
              <div>{statusBadge(r.status, retainerStatusMap)}</div>
            </div>
          ))}
        </div>
      </div>

      {/* ── Rechnungen ───────────────────────────────────────────── */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <h2 style={{ fontSize: 16, fontWeight: 600, color: 'var(--text-primary)', margin: 0 }}>Rechnungen</h2>
          <button style={btnPrimary} onClick={() => setShowNewInvoice(true)}>+ Rechnung erstellen</button>
        </div>
        <div style={card}>
          <div style={{ display: 'grid', gridTemplateColumns: '140px 1.5fr 100px 100px 80px 60px', gap: 12, padding: '10px 20px', borderBottom: '1px solid var(--border-light)', background: 'var(--bg-app)', borderRadius: '8px 8px 0 0' }}>
            {['Rechnungsnr.', 'Kunde', 'Betrag', 'Faellig', 'Status', ''].map(h => <span key={h} style={thStyle}>{h}</span>)}
          </div>
          {invoices.length === 0 && <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-tertiary)', fontSize: 13 }}>Noch keine Rechnungen vorhanden.</div>}
          {invoices.map((inv, idx) => (
            <div key={inv.id} style={{ display: 'grid', gridTemplateColumns: '140px 1.5fr 100px 100px 80px 60px', gap: 12, padding: '12px 20px', alignItems: 'center', borderBottom: idx < invoices.length - 1 ? '1px solid var(--border-light)' : 'none', transition: 'background 0.1s' }} onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-hover)'} onMouseLeave={e => e.currentTarget.style.background = 'transparent'}>
              <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--brand-primary)', fontFamily: 'var(--font-mono)' }}>{inv.invoice_number}</div>
              <div>
                <div style={{ fontSize: 13, color: 'var(--text-primary)' }}>{inv.customer_name || '-'}</div>
                <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>{inv.customer_email}</div>
              </div>
              <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)' }}>{fmtCurrency(inv.amount_gross)}</div>
              <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{fmtDate(inv.due_date)}</div>
              <div>{statusBadge(inv.status, invoiceStatusMap)}</div>
              <div>
                <button onClick={() => downloadPdf(inv.id, inv.invoice_number)} style={{ ...btnSecondary, padding: '4px 10px', fontSize: 11 }} title="PDF herunterladen">
                  <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M4 12h8M8 2v8M5 7l3 3 3-3"/></svg>
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ── Modal: Neuer Vertrag ─────────────────────────────────── */}
      {showNewRetainer && (
        <div style={overlay} onClick={e => e.target === e.currentTarget && setShowNewRetainer(false)}>
          <div style={modal}>
            <h3 style={{ fontSize: 16, fontWeight: 600, color: 'var(--text-primary)', margin: 0 }}>Neuer Retainer-Vertrag</h3>
            <div><label style={label}>Kundenname</label><input style={input} value={retainerForm.customer_name} onChange={e => setRetainerForm(f => ({ ...f, customer_name: e.target.value }))} /></div>
            <div><label style={label}>E-Mail</label><input style={input} value={retainerForm.customer_email} onChange={e => setRetainerForm(f => ({ ...f, customer_email: e.target.value }))} /></div>
            <div><label style={label}>Paket</label><input style={input} value={retainerForm.package_name} onChange={e => setRetainerForm(f => ({ ...f, package_name: e.target.value }))} /></div>
            <div><label style={label}>Preis netto</label><input style={input} type="number" value={retainerForm.price_net} onChange={e => setRetainerForm(f => ({ ...f, price_net: e.target.value }))} /></div>
            <div><label style={label}>Startdatum</label><input style={input} type="date" value={retainerForm.start_date} onChange={e => setRetainerForm(f => ({ ...f, start_date: e.target.value }))} /></div>
            <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
              <button style={btnSecondary} onClick={() => setShowNewRetainer(false)}>Abbrechen</button>
              <button style={btnPrimary} onClick={createRetainer} disabled={submitting}>{submitting ? 'Erstellen...' : 'Erstellen'}</button>
            </div>
          </div>
        </div>
      )}

      {/* ── Modal: Neue Rechnung ─────────────────────────────────── */}
      {showNewInvoice && (
        <div style={overlay} onClick={e => e.target === e.currentTarget && setShowNewInvoice(false)}>
          <div style={modal}>
            <h3 style={{ fontSize: 16, fontWeight: 600, color: 'var(--text-primary)', margin: 0 }}>Neue Rechnung</h3>
            <div><label style={label}>Kundenname</label><input style={input} value={invoiceForm.customer_name} onChange={e => setInvoiceForm(f => ({ ...f, customer_name: e.target.value }))} /></div>
            <div><label style={label}>E-Mail</label><input style={input} value={invoiceForm.customer_email} onChange={e => setInvoiceForm(f => ({ ...f, customer_email: e.target.value }))} /></div>
            <div><label style={label}>Betrag netto</label><input style={input} type="number" value={invoiceForm.amount_net} onChange={e => setInvoiceForm(f => ({ ...f, amount_net: e.target.value }))} /></div>
            <div><label style={label}>Leistung</label><input style={input} value={invoiceForm.line_item} onChange={e => setInvoiceForm(f => ({ ...f, line_item: e.target.value }))} /></div>
            <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
              <button style={btnSecondary} onClick={() => setShowNewInvoice(false)}>Abbrechen</button>
              <button style={btnPrimary} onClick={createInvoice} disabled={submitting}>{submitting ? 'Erstellen...' : 'Erstellen'}</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

import React, { useState } from 'react';
import toast from 'react-hot-toast';
import API_BASE_URL from '../config';



export default function MassExport() {
  const [exporting, setExporting] = useState(false);

  const exportCSV = async () => {
    setExporting(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/leads/export/csv`);
      if (!res.ok) throw new Error('Export fehlgeschlagen');
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `leads-export-${new Date().toISOString().slice(0, 10)}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      toast.success('CSV-Export heruntergeladen');
    } catch (e) {
      toast.error(e.message);
    } finally {
      setExporting(false);
    }
  };

  return (
    <div style={{ maxWidth: 600 }}>
      <h1 style={{ fontSize: 22, fontWeight: 800, color: 'var(--text-primary)', marginBottom: 8 }}>Massen-Export</h1>
      <p style={{ color: 'var(--text-secondary)', fontSize: 14, marginBottom: 24 }}>Alle Leads als CSV-Datei exportieren.</p>

      <div style={{ background: 'var(--bg-surface)', borderRadius: 'var(--radius-lg)', border: '1px solid var(--border-light)', padding: 24 }}>
        <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 8 }}>Lead-Export (CSV)</div>
        <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 16 }}>
          Exportiert alle Leads mit Firmenname, Kontakt, Telefon, E-Mail, Website, Stadt, Gewerk, Status, Score und Quelle.
          Semikolon-getrennt, UTF-8 mit BOM.
        </p>
        <button onClick={exportCSV} disabled={exporting} style={{
          background: 'var(--brand-primary)', color: '#fff', border: 'none', borderRadius: 'var(--radius-md)', padding: '10px 24px',
          fontSize: 14, fontWeight: 700, cursor: exporting ? 'not-allowed' : 'pointer', minHeight: 44, opacity: exporting ? 0.6 : 1,
        }}>
          {exporting ? 'Wird exportiert...' : 'CSV herunterladen'}
        </button>
      </div>
    </div>
  );
}
